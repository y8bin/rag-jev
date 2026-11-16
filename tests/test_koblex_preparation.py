import ast
import asyncio
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re

import httpx
import numpy as np
import pytest

from legal_rag_jev.budget import Budget, BudgetError
from legal_rag_jev.config import Config
from legal_rag_jev.io import file_hash, read_json, read_jsonl, write_json, write_jsonl
from legal_rag_jev.koblex import canonical, evaluate_predictions, export_predictions, prepare, provision_metrics, token_f1
from legal_rag_jev.providers import Providers, ProviderError
from legal_rag_jev.corpus import load_queries, load_documents, validate_dataset
from legal_rag_jev.schema import EvidenceUnit


def sources(tmp_path, missing=False):
    corpus = [{"index": "법 1조", "hierarchy": "법 1조 1항", "content": "① 가상 규정"},
              {"index": "법 1조", "hierarchy": "법 1조 1항", "content": "① 가상 규정"}]
    qa = [{"id": "qa_1_1hop_1", "background": "가상 상황.", "question": "기한은?", "answer": "SECRET_GOLD",
           "n_hops": 1, "contexts": [corpus[0] if not missing else {"hierarchy": "없는 조항", "content": "없는 본문"}]}]
    write_jsonl(tmp_path / "qa.jsonl", qa)
    write_jsonl(tmp_path / "corpus.jsonl", corpus)
    write_json(tmp_path / "audit.json", {"qa_file_sha256": file_hash(tmp_path / "qa.jsonl"),
        "source_and_gold_groups": {"groups": {"qa_1_1hop_1": "G000"}}})
    return [str(tmp_path / p) for p in ("qa.jsonl", "corpus.jsonl", "bundle", "audit.json")]


def test_prepare_separates_gold_preserves_duplicates_and_exact_text(tmp_path):
    args = sources(tmp_path)
    manifest = prepare(*args)
    assert manifest["corpus_rows"] == 2 and manifest["duplicate_canonical_rows"] == 1
    assert manifest["mapped_gold_units"] == 1
    assert "SECRET_GOLD" not in (tmp_path / "bundle/questions.jsonl").read_text()
    q = load_queries(str(tmp_path / "bundle/queries.jsonl"))[0]
    assert q.question == "가상 상황.기한은?" and q.split == "test"
    assert len(q.evidence_units[0].chunk_ids) == 2
    docs = load_documents(str(tmp_path / "bundle/documents.jsonl"))
    assert docs[0].text == "법 1조 1항① 가상 규정"
    validate_dataset(read_jsonl(tmp_path / "bundle/chunks.jsonl"), [q], docs)
    with pytest.raises(ValueError, match="immutable"):
        prepare(*args)


def test_unavailable_gold_is_explicit_and_never_added_to_corpus(tmp_path):
    args = sources(tmp_path, missing=True)
    with pytest.raises(ValueError, match="missing"):
        prepare(*args)
    assert not (tmp_path / "bundle").exists()
    manifest = prepare(*args, allow_unavailable_gold=True)
    assert manifest["unavailable_gold_units"] == 1 and manifest["questions_with_unavailable_gold"] == 1
    q = load_queries(str(tmp_path / "bundle/queries.jsonl"))[0]
    assert q.evidence_units[0].available_in_corpus is False
    assert "없는 본문" not in (tmp_path / "bundle/chunks.jsonl").read_text()
    validate_dataset(read_jsonl(tmp_path / "bundle/chunks.jsonl"), [q])
    with pytest.raises(ValueError, match="Unavailable"):
        EvidenceUnit(unit_id="x", available_in_corpus=False, chunk_ids=["fake"])


def test_official_metric_parity_and_800_character_clipping(tmp_path):
    path = Path('data/koblex/upstream/experiments/lf-eval/eval_pipeline.py')
    if not path.exists():
        pytest.skip("Pinned upstream audit source unavailable")
    tree = ast.parse(path.read_text())
    names = {"normalize", "tokenize", "compute_token_f1", "evaluate_retrieval", "extract_predictions"}
    # Load only pure metric functions, without importing/evaluating the paid GEval backend.
    nodes = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    nodes += [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    scope = {"Counter": Counter, "re": re, "np": np}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), "upstream-pure-metrics", "exec"), scope)
    for pred, gold in [("가나, 가나! ABC 123", "가나 abc 123"), ("", ""), ("가나", "다라"), ("기한은 14일이다.", "기한 14일")]:
        assert token_f1(pred, gold) == scope["compute_token_f1"](pred, gold)
    for pred, gold in [([], []), ([], ["a"]), (["a", "a"], ["a"]), (["a", "b"], ["b", "c"])]:
        reference = scope["evaluate_retrieval"]([pred], [gold])
        actual = provision_metrics(pred, gold)
        assert all(actual[k] == reference[k] for k in reference)
    answer = "x " * 400 + "target"
    write_jsonl(tmp_path / "gold.jsonl", [{"query_id": "q", "answer": "target", "provisions": ["a"], "n_hops": 1}])
    write_jsonl(tmp_path / "pred.jsonl", [{"query_id": "q", "answer": answer, "provisions": ["a"]}])
    report = evaluate_predictions(str(tmp_path / "gold.jsonl"), str(tmp_path / "pred.jsonl"), str(tmp_path / "eval"))
    assert report["token_f1"] == 0 and report["full_answer_token_f1"] > 0
    assert report["lf_eval"] is None


def test_export_reorders_by_gold_and_rejects_missing_results(tmp_path):
    write_jsonl(tmp_path / "map.jsonl", [{"chunk_id": "c", "hierarchy": "h", "content": "t"}])
    gold = [{"query_id": "q1", "answer": "a", "provisions": ["ht"], "n_hops": 1},
            {"query_id": "q2", "answer": "b", "provisions": ["ht"], "n_hops": 1}]
    write_jsonl(tmp_path / "gold.jsonl", gold)
    rows = [{"query_id": "q2", "condition_id": "jev_r", "status": "failed", "selected": [{"chunk_id": "c"}]},
            {"query_id": "q1", "condition_id": "jev_r", "status": "ok", "selected": [{"chunk_id": "c"}], "answer": {"answer": "a"}}]
    write_jsonl(tmp_path / "run/raw.jsonl", rows)
    result = export_predictions(str(tmp_path / "run"), str(tmp_path / "map.jsonl"), str(tmp_path / "gold.jsonl"), str(tmp_path / "export"))
    exported = read_jsonl(result["jev_r"]["path"])
    assert [r["query_id"] for r in exported] == ["q1", "q2"]
    assert exported[1]["answer"] == "" and exported[1]["provisions"] == ["ht"]
    write_jsonl(tmp_path / "run/raw.jsonl", rows[:1])
    with pytest.raises(ValueError, match="exactly one"):
        export_predictions(str(tmp_path / "run"), str(tmp_path / "map.jsonl"), str(tmp_path / "gold.jsonl"), str(tmp_path / "bad"))
    assert not (tmp_path / "bad").exists()


def test_budget_is_persistent_and_parallel_reservations_cannot_overspend(tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_INPUT_USD_PER_MILLION", "100")
    monkeypatch.setenv("JEV_OUTPUT_USD_PER_MILLION", "0")
    budget = Budget(str(tmp_path / "budget.sqlite"), 1)
    def call(_):
        try:
            return budget.reserve("jev", {"model": "m"}, {"state": "x"})
        except BudgetError:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        ids = [i for i in pool.map(call, range(8)) if i]
    assert len(ids) == 2
    assert budget.summary()["accounted_with_reservations_usd"] <= 1
    assert Budget(str(tmp_path / "budget.sqlite"), 1).summary()["attempts"] == 2
    budget.settle(ids[0], .01)
    assert budget.summary()["unsettled_attempts"] == 1
    assert budget.reserve("jev", {"model": "m"}, {"state": "x"})
    with pytest.raises(BudgetError, match="differs"):
        Budget(str(tmp_path / "budget.sqlite"), 100)


def test_budget_blocks_transport_before_request_when_price_unknown(corpus, tmp_path, monkeypatch):
    cfg, _, chunks, q = corpus
    monkeypatch.delenv("JEV_INPUT_USD_PER_MILLION", raising=False)
    for k, v in {"JEV_MODEL": "m", "JEV_BASE_URL": "https://test.invalid", "JEV_API_KEY": "secret"}.items():
        monkeypatch.setenv(k, v)
    cfg = cfg.model_copy(update={"jev_backend": "http", "budget_ledger": str(tmp_path / "budget.sqlite"), "budget_limit_usd": 100})
    def handle(request):
        pytest.fail("Must not send paid requests without known prices")
    async def check():
        p = Providers(cfg, httpx.AsyncClient(transport=httpx.MockTransport(handle)))
        try:
            with pytest.raises(BudgetError, match="prices"):
                await p.jev(q.json_record(), chunks[:1])
        finally:
            await p.close()
    asyncio.run(check())


def test_free_form_generation_uses_official_prompt_settings_and_accounts_chat_usage(corpus, tmp_path, monkeypatch):
    cfg, _, chunks, q = corpus
    (tmp_path / "system").write_text("fixed system")
    (tmp_path / "instruction").write_text("Question: $question\nContext: $context_str")
    for key, value in {"OPENAI_MODEL": "gpt-4o-2024-08-06", "OPENAI_API_KEY": "secret",
                        "GENERATION_INPUT_USD_PER_MILLION": "2.5", "GENERATION_OUTPUT_USD_PER_MILLION": "10"}.items():
        monkeypatch.setenv(key, value)
    cfg = cfg.model_copy(update={"generation_backend": "openai", "generation_style": "koblex",
        "koblex_system_prompt": str(tmp_path / "system"), "koblex_instruction_prompt": str(tmp_path / "instruction"),
        "temperature": .01, "generation_top_p": .9, "max_output_tokens": 2000,
        "budget_ledger": str(tmp_path / "budget.sqlite"), "budget_limit_usd": 100})
    def handle(request):
        body = json.loads(request.content)
        assert request.url.path == "/v1/chat/completions"
        assert body["top_p"] == .9 and body["temperature"] == .01 and body["max_tokens"] == 2000
        assert "reference_answer" not in body["messages"][0]["content"]
        return httpx.Response(200, json={"model": "gpt-4o-2024-08-06", "choices": [{"finish_reason": "stop", "message": {"content": "Answer: result"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 10}})
    async def check():
        p = Providers(cfg, httpx.AsyncClient(transport=httpx.MockTransport(handle)))
        try:
            r = await p.generate(q.json_record(), chunks[:1])
            assert r.value["answer"] == "result"
            assert r.trace["usage"] == {"input_tokens": 100, "output_tokens": 10}
            assert r.trace["cost_usd"] == pytest.approx(.00035)
            assert p.transport.budget.summary()["known_cost_usd"] == pytest.approx(.00035)
        finally:
            await p.close()
    asyncio.run(check())

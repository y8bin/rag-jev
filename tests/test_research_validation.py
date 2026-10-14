import asyncio
from copy import deepcopy

import pytest

from legal_rag_jev.annotation import export_annotations, import_answers, validate_answer_annotation
from legal_rag_jev.config import Config, search_cost
from legal_rag_jev.corpus import assign_splits
from legal_rag_jev.evaluation import answer_metrics, evaluate, paired_statistics, summarize_benchmark
from legal_rag_jev.io import digest, read_json, read_jsonl, write_json, write_jsonl
from legal_rag_jev.pipeline import freeze, run
from legal_rag_jev.reports import agreement, sweep, tune
from test_workflows import annotate, build


def reviewed_answer(corpus):
    _, _, chunks, q = corpus
    cid = chunks[0]["chunk_id"]
    row = {"query": q.json_record(), "selected": [chunks[0]], "status": "ok", "answer": {
        "answer": "fourteen days", "rationale": "background", "abstained": False,
        "claims": [{"text": "fourteen days", "evidence_ids": [cid]},
                   {"text": "background", "evidence_ids": []}], "citations": [cid]}}
    annotation = {"answer_hash": digest(row["answer"]), "annotation_schema_version": 2,
        "correctness": True, "core_supported": True, "claims_complete": True, "omitted_claims": [],
        "claim_labels": [{"is_core": True, "support": "supported", "citations": [{"evidence_id": cid, "supported": True}]},
                         {"is_core": False, "support": "unsupported", "citations": []}]}
    return row, annotation


def test_core_primary_and_strict_secondary_differ_on_background(corpus):
    row, a = reviewed_answer(corpus)
    m = answer_metrics(row, a)
    assert m["grounded_correct"] == 1 and m["strict_grounded_correct"] == 0
    assert m["core_citation_coverage"] == 1 and m["claim_support"] == .5
    a["claims_complete"], a["omitted_claims"] = False, ["unlisted assertion in rationale"]
    m = answer_metrics(row, a)
    assert m["grounded_correct"] == 0 and m["strict_grounded_correct"] == 0


@pytest.mark.parametrize("invalid", ["unsupported", "unprovided", "no_core"])
def test_core_requires_supported_provided_citation(corpus, invalid):
    row, a = reviewed_answer(corpus)
    if invalid == "unsupported":
        a["claim_labels"][0]["citations"][0]["supported"] = False
    elif invalid == "unprovided":
        row["selected"] = []
    else:
        a["claim_labels"][0]["is_core"] = False
    assert answer_metrics(row, a)["grounded_correct"] == 0


def test_legacy_reviews_do_not_infer_new_primary(corpus):
    row, a = reviewed_answer(corpus)
    for key in ("annotation_schema_version", "claims_complete", "omitted_claims"):
        a.pop(key)
    assert answer_metrics(row, a)["grounded_correct"] is None
    assert answer_metrics(row, a)["strict_grounded_correct"] == 0


def test_completeness_review_cannot_be_missing_or_inconsistent(corpus):
    row, a = reviewed_answer(corpus)
    for change in ({"claims_complete": None}, {"omitted_claims": ["missing"]}):
        with pytest.raises(ValueError, match="claims_complete"):
            validate_answer_annotation(row, {**a, **change})
    a["claim_labels"][0]["is_core"] = None
    with pytest.raises(ValueError, match="is_core"):
        validate_answer_annotation(row, a)


def test_new_export_cannot_be_downgraded_to_legacy(corpus, tmp_path):
    cfg, *_ = corpus
    async def check():
        await build(corpus)
        out = await run(cfg, "dev")
        tasks = export_annotations(str(out), "answers", str(tmp_path/"reviews"), 42)
        rows = read_jsonl(tasks)
        rows[0].pop("annotation_schema_version")
        write_jsonl(tasks, rows)
        with pytest.raises(ValueError, match="schema changed"):
            import_answers(str(out), str(tasks), str(tasks.parent/"private_mapping.json"))
    asyncio.run(check())


def test_agreement_reports_citations_core_and_ordinal_grades(tmp_path):
    first = [{"annotation_id": "a", "annotation_schema_version": 2, "correctness": True,
        "core_supported": True, "claims_complete": True, "omitted_claims": [],
        "claim_labels": [{"is_core": True, "support": "supported", "citations": [
            {"evidence_id": "c1", "supported": True}, {"evidence_id": "c2", "supported": False}]}]}]
    second = deepcopy(first)
    second[0]["claim_labels"][0]["citations"].reverse()
    second[0]["claim_labels"][0]["citations"][0]["supported"] = True
    write_jsonl(tmp_path/"a.jsonl", first); write_jsonl(tmp_path/"b.jsonl", second)
    report = read_json(agreement(str(tmp_path/"a.jsonl"), str(tmp_path/"b.jsonl"), str(tmp_path/"report.json")))
    assert report["fields"]["citation_support"]["n"] == 2
    assert report["fields"]["citation_support"]["agreement"] == .5
    assert report["fields"]["is_core"]["agreement"] == 1
    assert len(report["conflicts"]) == 1
    second[0]["claim_labels"][0]["citations"][0]["evidence_id"] = "wrong"
    write_jsonl(tmp_path/"b.jsonl", second)
    with pytest.raises(ValueError, match="citation IDs"):
        agreement(str(tmp_path/"a.jsonl"), str(tmp_path/"b.jsonl"), str(tmp_path/"report.json"))
    write_jsonl(tmp_path/"a.jsonl", [{"annotation_id": str(i), "grade": i} for i in range(3)])
    write_jsonl(tmp_path/"b.jsonl", [{"annotation_id": str(i), "grade": i if i == 0 else i-1} for i in range(3)])
    grades = read_json(agreement(str(tmp_path/"a.jsonl"), str(tmp_path/"b.jsonl"), str(tmp_path/"report.json")))["fields"]["grade"]
    assert grades["cohen_kappa"] == pytest.approx(0)
    assert grades["linear_weighted_kappa"] == pytest.approx(.25)
    # Observed squared disagreement = 1/6, expected = 1/3, so kappa = 1/2.
    assert grades["quadratic_weighted_kappa"] == pytest.approx(.5)


def test_pilot_connected_components_never_enter_test_and_are_order_stable(corpus):
    _, _, chunks, q = corpus
    pilot = q.model_copy(update={"split": "pilot"}).json_record()
    related = {**pilot, "query_id": "related", "group_id": "other_label", "split": "dev"}
    fresh = [{**pilot, "query_id": f"new{i}", "group_id": f"new{i}", "split": "dev",
              "answerable": False, "evidence_units": [], "sufficient_sets": []} for i in range(2)]
    source = [pilot, related, *fresh]
    for reuse in (False, True):
        rows = assign_splits(source, chunks, 42, .5, .5, reuse_pilot_in_dev=reuse)
        reversed_rows = assign_splits(list(reversed(source)), chunks, 42, .5, .5, reuse_pilot_in_dev=reuse)
        assert {r["query_id"]: (r["split"], r["group_id"]) for r in rows} == {
            r["query_id"]: (r["split"], r["group_id"]) for r in reversed_rows}
        assert rows[0]["split"] == rows[1]["split"] == ("dev" if reuse else "pilot")
        assert {r["split"] for r in rows[2:]} == {"dev", "test"}
    with pytest.raises(ValueError, match="unexposed"):
        assign_splits([pilot, related], chunks, 42, .5, .5)


def test_statistics_include_fr_vs_own_r_and_separate_holm_families(tmp_path):
    methods = ["vector", "ce_r", "jev_r", "ce_fr", "jev_fr"]
    rows = [{"query_id": f"q{i}", "group_id": f"g{i}", "condition_id": m, "status": "ok",
        "metrics": {"esr": 1, "grounded_correct": 1, "online_cost_usd": j/100, "context_tokens": 10}}
        for i in range(3) for j,m in enumerate(methods)]
    write_jsonl(tmp_path/"metrics.jsonl", rows)
    write_json(tmp_path/"summary.json", [{"condition_id": m, "grounded_correct_complete": True} for m in methods])
    report = read_json(paired_statistics(str(tmp_path), 100, 42, .02, margins={"esr": .01, "grounded_correct": .03}))
    comparisons = report["comparisons"]
    assert len([r for r in comparisons if r["comparison_family"] == "primary"]) == 6
    assert {r["metric"] for r in comparisons if r["baseline"] == "jev_r" and r["treatment"] == "jev_fr"} == {
        "esr", "grounded_correct", "online_cost_usd"}
    assert {r["delta"] for r in report["noninferiority"] if r["metric"] == "esr"} == {.01}
    assert all(r["both_quality_constraints_supported"] for r in report["joint_noninferiority"])


def test_infeasible_fr_continues_only_with_explicit_branch(corpus, tmp_path):
    cfg, *_ = corpus
    async def check():
        await build(corpus)
        out = await sweep(cfg, 2)
        annotate(out, tmp_path)
        evaluate(str(out))
        summary = read_json(out/"summary.json")
        for s in summary:
            if s["method"] == "ce_fr": s["grounded_correct"] = 0
        write_json(out/"summary.json", summary)
        with pytest.raises(ValueError, match="No feasible"):
            tune(str(out), cfg, str(tmp_path/"strict.yaml"))
        assert not (tmp_path/"strict.yaml").exists()
        path = tune(str(out), cfg, str(tmp_path/"continue.yaml"), allow_infeasible=True)
        final = Config.load(str(path), env_file=str(tmp_path/"no-env"))
        assert final.methods == ["vector", "ce_r", "jev_r", "jev_fr"]
        assert final.ce_threshold is None and final.jev_threshold is not None
        assert final.quality_margins == cfg.quality_margins
        assert read_json(out/"threshold_selection.json")["infeasible_methods"] == ["ce_fr"]
    asyncio.run(check())


def test_analysis_documents_are_bound_to_protocol_lock(corpus, tmp_path):
    cfg, *_ = corpus
    plan = tmp_path/"analysis.md"
    plan.write_text("predeclared analysis", encoding="utf-8")
    cfg = cfg.model_copy(update={"protocol_documents": [str(plan)]})
    async def check():
        await build(corpus)
        lock = await freeze(cfg, str(tmp_path/"lock.json"))
        assert str(plan) in lock["protocol"]["protocol_documents_sha256"]
        plan.write_text("changed after freeze", encoding="utf-8")
        with pytest.raises(ValueError, match="differs from lock"):
            await run(cfg, "dev", lock_path=str(tmp_path/"lock.json"))
    asyncio.run(check())


def test_remote_search_cost_never_uses_local_model_rate(monkeypatch):
    monkeypatch.setenv("LOCAL_USD_PER_HOUR", "1")
    monkeypatch.delenv("QDRANT_USD_PER_HOUR", raising=False)
    assert search_cost(3600000, "local") == 1
    assert search_cost(3600000, "remote") is None
    monkeypatch.setenv("QDRANT_USD_PER_HOUR", "2")
    assert search_cost(3600000, "remote") == 2


def test_benchmark_reports_success_and_failure_times_separately(tmp_path):
    write_jsonl(tmp_path/"raw.jsonl", [{"method": "jev_r", "status": status, "timing": {"wall_clock_ms": ms}}
        for status,ms in (("ok", 100), ("failed", 900))])
    report = read_json(summarize_benchmark(str(tmp_path)))[0]
    assert report["mean_ms"] == 100 and report["failed_mean_ms"] == 900
    assert report["successes"] == 1 and report["failure_rate"] == .5


def test_offline_readiness_reports_missing_data_without_secrets(tmp_path, monkeypatch):
    from legal_rag_jev.readiness import readiness
    monkeypatch.setenv("JEV_API_KEY", "private-never-print-test")
    cfg = Config(documents=str(tmp_path/"missing_documents.jsonl"), chunks=str(tmp_path/"missing_chunks.jsonl"),
                 queries=str(tmp_path/"missing_queries.jsonl"), index_dir=str(tmp_path/"missing_index"))
    report = readiness(cfg, str(tmp_path/"readiness.json"))
    assert not report["local_checks_passed"]
    assert sum(x["code"] == "missing_input" for x in report["issues"]) == 3
    assert "independent_legal_reviewers" in report["human_and_external_evidence_required"]
    assert "private-never-print-test" not in (tmp_path/"readiness.json").read_text()


def test_stratified_human_sample_is_stable_across_input_order(corpus):
    from legal_rag_jev.pipeline import human_sample
    cfg, _, _, q = corpus
    cfg = cfg.model_copy(update={"human_evaluation_limit": 3})
    queries = [q.model_copy(update={"query_id": f"q{i}", "task_type": "direct" if i < 3 else "application"})
               for i in range(6)]
    assert human_sample(cfg, queries) == human_sample(cfg, list(reversed(queries)))


def test_incomplete_costs_do_not_produce_paired_cost_inference(tmp_path):
    methods = ["ce_r", "jev_r", "ce_fr", "jev_fr"]
    rows = [{"query_id": f"q{i}", "group_id": f"g{i}", "condition_id": m, "status": "ok",
             "metrics": {"esr": 1, "grounded_correct": 1, "online_cost_usd": None if i == 0 and m == "jev_fr" else .01}}
            for i in range(3) for m in methods]
    write_jsonl(tmp_path/"metrics.jsonl", rows)
    write_json(tmp_path/"summary.json", [{"condition_id": m, "grounded_correct_complete": True} for m in methods])
    report = read_json(paired_statistics(str(tmp_path), 100, 42, .02, noninferiority_alpha=.025))
    assert all(r["status"] == "costs_incomplete" for r in report["comparisons"]
               if r["metric"] == "online_cost_usd" and r["treatment"] == "jev_fr")
    assert all(r["one_sided_confidence"] == .975 for r in report["noninferiority"])


def test_tune_cannot_attach_new_analysis_plan_to_old_sweep(corpus, tmp_path):
    cfg, *_ = corpus
    plan = tmp_path/"plan.md"
    plan.write_text("original plan", encoding="utf-8")
    cfg = cfg.model_copy(update={"protocol_documents": [str(plan)]})
    async def check():
        await build(corpus)
        out = await sweep(cfg, 2)
        annotate(out, tmp_path)
        evaluate(str(out))
        plan.write_text("changed plan", encoding="utf-8")
        with pytest.raises(ValueError, match="documents changed"):
            tune(str(out), cfg, str(tmp_path/"final.yaml"))
        assert not (tmp_path/"final.yaml").exists()
    asyncio.run(check())

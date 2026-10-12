import pytest

from legal_rag_jev.io import write_json, write_jsonl
from legal_rag_jev.viewer import Viewer


def make_run(root):
    d = root / "demo" / "r1"
    q = {"query_id": "Q1", "group_id": "G", "question": "q?", "answerable": True,
         "evidence_units": [{"unit_id": "U1", "doc_id": "A", "version_id": "v1", "start": 0, "end": 5}], "sufficient_sets": [["U1"]]}
    cands = [{"chunk_id": "C1", "doc_id": "A", "version_id": "v1", "start": 0, "end": 10, "vector_rank": 1, "vector_score": .9},
             {"chunk_id": "C2", "doc_id": "B", "version_id": "v1", "start": 0, "end": 10, "vector_rank": 2, "vector_score": .5}]
    write_jsonl(d / "raw.jsonl", [
        {"query": q, "query_id": "Q1", "method": "vector", "condition_id": "vector", "status": "ok", "candidates": cands,
         "selected": cands[:1], "ranking": [], "selected_count": 1},
        {"query": q, "query_id": "Q1", "method": "jev_r", "condition_id": "jev_r", "status": "failed", "candidates": cands,
         "selected": cands[1:], "ranking": [{"chunk_id": "C2", "rank": 1, "rerank_score": .8}], "error_stage": "generation", "error": "HTTP 400"}])
    write_json(d / "manifest.json", {"run_id": "r1", "mode": "quality", "research_valid": False, "conditions": [{"condition_id": "vector"}]})
    write_json(d / "completion.json", {"planned_rows": 2, "rows": 2, "failed": 1})
    return d


def test_viewer_reads_runs_queries_and_configs(tmp_path):
    make_run(tmp_path / "results")
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "a.yaml").write_text("top_k: 7\n", encoding="utf-8")
    (tmp_path / "configs" / "bad.yaml").write_text("methods: [nope]\n", encoding="utf-8")
    v = Viewer(tmp_path / "results", tmp_path / "configs")
    runs = v.runs()["runs"]
    assert [(r["path"], r["group"], r["completion"]["failed"]) for r in runs] == [("demo/r1", "demo", 1)]
    run = v.run("demo/r1")
    assert run["queries"][0]["conditions"][1]["status"] == "failed"
    assert run["errors"] == [{"message": "generation · HTTP 400", "count": 1}]
    detail = v.query("demo/r1", "Q1")
    assert [c["units"] for c in detail["candidates"]] == [["U1"], []]
    assert detail["conditions"][1]["ranking"] == [{"chunk_id": "C2", "rank": 1, "score": .8}]
    configs = {c["name"]: c for c in v.configs_view()["configs"]}
    assert configs["a"]["values"]["top_k"] == 7 and configs["a"]["values"]["top_n"] == 5 and configs["a"]["explicit"] == ["top_k"]
    assert "error" in configs["bad"] and "error" not in configs["a"]


def test_viewer_rejects_paths_outside_results(tmp_path):
    make_run(tmp_path / "results")
    v = Viewer(tmp_path / "results", tmp_path)
    with pytest.raises(PermissionError):
        v.run("../")
    with pytest.raises(FileNotFoundError):
        v.query("demo/r1", "missing")


def test_asker_runs_exploration_question_and_logs_it_apart_from_runs(corpus, tmp_path):
    import asyncio
    import yaml
    from legal_rag_jev.index import build_index
    from legal_rag_jev.providers import Providers
    from legal_rag_jev.viewer import Asker

    cfg, _, chunks, _ = corpus
    p = Providers(cfg)
    try:
        asyncio.run(build_index(cfg, chunks, p))
    finally:
        asyncio.run(p.close())
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "mock.yaml").write_text(yaml.safe_dump(cfg.model_dump() | {"jev_threshold": None}), encoding="utf-8")
    results = tmp_path / "viewer_results"
    asker = Asker(results, configs, str(tmp_path / "missing.env"))
    d = asker.ask({"config": "mock.yaml", "question": "Notice deadline days?", "as_of_date": "2025-06-01", "jurisdiction": "KR"})
    assert d["exploration"] and d["skipped_conditions"] == ["jev_fr"]
    assert [c["condition_id"] for c in d["conditions"]] == ["vector", "ce_r", "ce_fr", "jev_r"]
    assert {c["doc_id"] for c in d["candidates"]} == {"law"}  # jurisdiction + effective-date filters applied
    assert asker.history()[0]["ask_id"] == d["ask_id"] and asker.get(d["ask_id"])["query"]["question"] == "Notice deadline days?"
    assert Viewer(results, configs).runs()["runs"] == []  # exploration log is not an experiment run
    with pytest.raises(PermissionError):
        asker.ask({"config": "../x.yaml", "question": "q"})
    with pytest.raises(ValueError):
        asker.ask({"config": "mock.yaml", "question": "  "})

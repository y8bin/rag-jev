import asyncio
import pytest

from legal_rag_jev.annotation import export_annotations, import_answers
from legal_rag_jev.evaluation import evaluate, paired_statistics, summarize_benchmark
from legal_rag_jev.index import build_index
from legal_rag_jev.io import read_json, read_jsonl, write_jsonl
from legal_rag_jev.pipeline import benchmark, run
from legal_rag_jev.providers import Providers
from legal_rag_jev.reports import sweep, tune


async def build(corpus):
    cfg,_,chunks,_ = corpus
    p = Providers(cfg)
    try: await build_index(cfg,chunks,p)
    finally: await p.close()


def annotate(run_dir,tmp_path):
    tasks = export_annotations(str(run_dir),"answers",str(tmp_path/"tasks"),42)
    rows = read_jsonl(tasks)
    for row in rows:
        row["correctness"] = not row["answer"]["abstained"]
        row["core_supported"] = not row["answer"]["abstained"]
        row["claims_complete"] = True
        row["reviewer"] = "test-only synthetic labeler"
        for claim in row["claim_labels"]:
            claim["is_core"] = True
            claim["support"] = "supported"
            for cite in claim["citations"]: cite["supported"] = True
    write_jsonl(tasks,rows)
    import_answers(str(run_dir),str(tasks),str(tmp_path/"tasks"/"private_mapping.json"))


def test_dev_sweep_threshold_selection_uses_actual_answer_context(corpus,tmp_path):
    cfg,*_ = corpus
    async def check():
        await build(corpus)
        out = await sweep(cfg,3)
        rows = read_jsonl(out/"raw.jsonl")
        assert len(rows) == 8
        assert any(r["answer"]["abstained"] for r in rows)
        annotate(out,tmp_path)
        evaluate(str(out))
        final = tune(str(out),cfg,str(tmp_path/"final.yaml"))
        assert final.is_file()
        selected = read_json(out/"threshold_selection.json")
        assert selected["selected"]["jev_fr"]["esr"] == 1
        paired_statistics(str(out),100,42,.02)
        assert (out/"confidence_intervals.json").is_file()
    asyncio.run(check())


def test_tune_rejects_missing_human_data(corpus,tmp_path):
    cfg,*_ = corpus
    async def check():
        await build(corpus)
        out = await sweep(cfg,2)
        evaluate(str(out))
        with pytest.raises(ValueError,match="human"):
            tune(str(out),cfg,str(tmp_path/"bad.yaml"))
    asyncio.run(check())


def test_benchmark_is_fresh_warmup_excluded_and_failures_counted(corpus):
    cfg,*_ = corpus
    async def check():
        await build(corpus)
        out = await benchmark(cfg,"dev",2,1,1)
        rows = read_jsonl(out/"raw.jsonl")
        assert len(rows) == 10
        assert all(r["repetition"] >= 0 and not r["timing"]["cached"] for r in rows)
        assert all(r["timing"]["wall_clock_ms"] >= r["timing"]["online_ms"] for r in rows)
        assert not read_json(out/"manifest.json")["research_valid"]
        report = read_json(summarize_benchmark(str(out)))
        assert all(r["attempts"] == 2 and r["p95_ms"] >= 0 for r in report)
    asyncio.run(check())


def test_edited_annotation_context_cannot_be_imported(corpus,tmp_path):
    cfg,*_ = corpus
    async def check():
        await build(corpus)
        out = await run(cfg,"dev")
        tasks = export_annotations(str(out),"answers",str(tmp_path/"review"),42)
        rows = read_jsonl(tasks)
        rows[0]["evidence"][0]["text"] = "modified source"
        write_jsonl(tasks,rows)
        with pytest.raises(ValueError,match="changed"):
            import_answers(str(out),str(tasks),str(tmp_path/"review"/"private_mapping.json"))
    asyncio.run(check())


def test_retrieval_only_does_not_invent_zero_answer_accuracy(corpus):
    cfg,*_ = corpus
    cfg = cfg.model_copy(update={"generate":False,"methods":["ce_r"]})
    async def check():
        await build(corpus)
        out = await run(cfg,"dev")
        evaluate(str(out))
        summary = read_json(out/"summary.json")[0]
        assert summary["esr"] == 1 and summary["grounded_correct"] is None
    asyncio.run(check())

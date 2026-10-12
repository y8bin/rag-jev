import asyncio

from legal_rag_jev.annotation import export_annotations
from legal_rag_jev.evaluation import evaluate, paired_statistics
from legal_rag_jev.index import build_index
from legal_rag_jev.io import read_json, read_jsonl, write_jsonl
from legal_rag_jev.pipeline import human_sample, run
from legal_rag_jev.providers import Providers


def test_incomplete_human_labels_do_not_produce_primary_answer_claim(corpus):
    cfg,_,chunks,_ = corpus
    async def check():
        p = Providers(cfg)
        try: await build_index(cfg,chunks,p)
        finally: await p.close()
        out = await run(cfg,"dev")
        evaluate(str(out))
        summary = read_json(out/"summary.json")
        assert all(not r["grounded_correct_complete"] and r["grounded_correct"] is None for r in summary)
        paired_statistics(str(out),100,42,.02)
        stats = read_json(out/"statistics.json")
        assert all(c["status"] == "human_annotations_incomplete" for c in stats["comparisons"] if c["metric"] == "grounded_correct")
    asyncio.run(check())


def test_preregistered_human_sample_is_stable_and_blinded(corpus,tmp_path):
    cfg,_,chunks,q = corpus
    q2 = q.model_copy(update={"query_id":"Q2"})
    q3 = q.model_copy(update={"query_id":"Q3"})
    queries = [q,q2,q3]
    write_jsonl(cfg.queries,[x.json_record() for x in queries])
    cfg = cfg.model_copy(update={"human_evaluation_limit":1})
    selected = human_sample(cfg,queries)
    assert selected == human_sample(cfg,list(reversed(queries)))
    async def check():
        p = Providers(cfg)
        try: await build_index(cfg,chunks,p)
        finally: await p.close()
        out = await run(cfg,"dev")
        manifest = read_json(out/"manifest.json")
        assert manifest["human_evaluation_query_ids"] == selected
        tasks = export_annotations(str(out),"answers",str(tmp_path/"tasks"),cfg.seed)
        assert len(read_jsonl(tasks)) == 5 # same one question for all five methods
    asyncio.run(check())

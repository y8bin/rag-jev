import asyncio
import pytest

from legal_rag_jev.annotation import export_annotations, import_answers
from legal_rag_jev.evaluation import answer_metrics, covered_units, evaluate, retrieval_metrics
from legal_rag_jev.index import build_index
from legal_rag_jev.io import digest, read_json, read_jsonl, write_jsonl
from legal_rag_jev.pipeline import default_conditions, freeze, run, select
from legal_rag_jev.providers import Providers


def test_evidence_set_requires_all_units_and_contiguous_spans(corpus):
    _,_,chunks,q = corpus
    q = q.json_record()
    assert retrieval_metrics(q,[chunks[0]],chunks)["esr"] == 1
    parts = [{**chunks[0],"end":10},{**chunks[0],"start":11}]
    assert covered_units(q,parts) == set()
    parts[1]["start"] = 10
    assert covered_units(q,parts) == {"U1"}


def test_unjudged_candidates_are_not_negative(corpus):
    _,_,chunks,q = corpus
    q = {**q.json_record(),"relevance":{}}
    m = retrieval_metrics(q,[chunks[0]],chunks)
    assert m["ndcg"] is None and m["precision"] is None and m["judgment_coverage"] == 0
    assert m["esr"] == 1


def test_filter_can_return_empty_and_ties_use_vector_order(corpus):
    cfg,_,chunks,q = corpus
    candidates = [{**c,"vector_rank":i+1,"vector_score":.5} for i,c in enumerate(chunks)]
    ranked,selected = select(cfg,q.json_record(),candidates,[.1,.1,.1],.9)
    assert selected == []
    assert [c["chunk_id"] for c in ranked] == [c["chunk_id"] for c in candidates]


def test_budget_never_cuts_chunks(corpus):
    cfg,_,chunks,q = corpus
    candidates = [{**c,"vector_rank":i+1,"vector_score":.5} for i,c in enumerate(chunks)]
    import json
    from legal_rag_jev.prompts import GENERATION_SYSTEM, generation_content
    budget = len(GENERATION_SYSTEM + "\n" + json.dumps(generation_content(q.json_record(),candidates[:1],None),ensure_ascii=False))
    cfg = cfg.model_copy(update={"token_budget":budget})
    _,selected = select(cfg,q.json_record(),candidates,None,None)
    assert len(selected) == 1
    assert all(c["text"] == chunks[c["vector_rank"]-1]["text"] for c in selected)


def test_zero_claims_and_invalid_citations_never_grounded_correct(corpus):
    _,_,chunks,q = corpus
    row = {"query":q.json_record(),"selected":[chunks[0]],"status":"ok","answer":
        {"answer":"14","claims":[],"citations":[],"rationale":"","abstained":False}}
    a = {"answer_hash":digest(row["answer"]),"correctness":True,"core_supported":True,"claim_labels":[]}
    m = answer_metrics(row,a)
    assert m["claim_support"] is None and m["grounded_correct"] == 0


def test_end_to_end_cache_blinding_annotations_and_lock(corpus,tmp_path):
    cfg,_,chunks,q = corpus
    async def check():
        p = Providers(cfg)
        try: await build_index(cfg,chunks,p)
        finally: await p.close()
        lock = await freeze(cfg,str(tmp_path/"lock.json"))
        out = await run(cfg,"dev",run_id="one",lock_path=str(tmp_path/"lock.json"))
        rows = read_jsonl(out/"raw.jsonl")
        assert len(rows) == 5 and all(r["status"] == "ok" for r in rows)
        assert all(r["timing"]["online_ms"] is None for r in rows)
        out2 = await run(cfg,"dev",run_id="two")
        assert all(r["timing"]["cached"] for r in read_jsonl(out2/"raw.jsonl"))
        tasks_path = export_annotations(str(out),"answers",str(tmp_path/"blind"),42)
        tasks = read_jsonl(tasks_path)
        assert all("method" not in t and "rerank_score" not in str(t) for t in tasks)
        for t in tasks:
            t["correctness"] = True
            t["core_supported"] = True
            for label in t["claim_labels"]:
                label["support"] = "supported"
                for c in label["citations"]: c["supported"] = True
        write_jsonl(tasks_path,tasks)
        import_answers(str(out),str(tasks_path),str(tmp_path/"blind"/"private_mapping.json"))
        evaluate(str(out))
        assert all(r["grounded_correct"] == 1 for r in read_json(out/"summary.json"))
        await run(cfg,"dev",run_id="one",resume=True,lock_path=str(tmp_path/"lock.json"))
        changed = cfg.model_copy(update={"top_n":1})
        with pytest.raises(ValueError,match="differs"):
            await run(changed,"dev",run_id="different",lock_path=str(tmp_path/"lock.json"))
    asyncio.run(check())


def test_thresholds_cannot_be_silently_defaulted(corpus):
    cfg,*_ = corpus
    with pytest.raises(ValueError,match="threshold"):
        default_conditions(cfg.model_copy(update={"jev_threshold":None}))

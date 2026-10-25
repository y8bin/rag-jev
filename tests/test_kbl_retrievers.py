import asyncio
import json
from pathlib import Path

import pytest
import yaml

from legal_rag_jev.config import Config
from legal_rag_jev.corpus import load_run_queries
from legal_rag_jev.evaluation import evaluate
from legal_rag_jev.io import read_json, read_jsonl, write_jsonl
from legal_rag_jev.kbl import prepare_corpus, prepare_replay
from legal_rag_jev.pipeline import freeze, run, select
from legal_rag_jev.providers import Providers
from legal_rag_jev.retrievers import BM25Index, ReplayIndex, build_bm25, open_retriever
from legal_rag_jev.viewer import Asker, Viewer


@pytest.fixture
def replay(tmp_path):
    source = tmp_path / "public.json"
    source.write_text(json.dumps([{"doc-id":1,"question":"신청 기한은?", "A":"7일", "B":"14일",
        "label":"B", "label_long":"SECRET_GOLD_ONLY", "rag_data":{"question_only":{"query":"신청 기한은?", "retrieved_docs":{"results":[
            {"doc_id":"docid-1___jo-1","score":1,"title":"법령","passage":"신청 기한은 14일이다."},
            {"doc_id":"docid-2___jo-1","score":99,"title":"법령","passage":"수수료는 10원이다."}]}}}}],ensure_ascii=False))
    folder = tmp_path / "replay"
    prepare_replay(str(folder),source=str(source))
    return Config(retriever_backend="replay",query_mode="mcq",snapshot_corpus=True,apply_metadata_filters=False,
        index_dir=str(folder),queries=str(folder/"questions.jsonl"),benchmark_gold=str(folder/"gold.jsonl"),
        methods=["retrieval","ce_r","jev_r"],top_k=2,top_n=1,embedding_backend="local",
        ce_backend="mock",jev_backend="mock",generation_backend="mock",judge_backend="mock",
        token_encoding="unicode_characters",output_dir=str(tmp_path/"results"),cache_dir=str(tmp_path/"cache"))


def test_replay_separates_gold_preserves_original_order_and_rejects_new_questions(replay):
    cfg = replay
    q = load_run_queries(cfg)[0].json_record()
    text = Path(cfg.queries).read_text() + (Path(cfg.index_dir)/"candidates.jsonl").read_text()
    assert "SECRET_GOLD_ONLY" not in text and '"label"' not in text
    with ReplayIndex(cfg) as idx:
        found = asyncio.run(idx.search(q))
        _, chosen = select(cfg,q,found["candidates"],None,None)
        assert chosen[0]["retrieval_score"] == 1  # original order takes precedence over scores
        assert found["trace"]["search_cost_usd"] is None
        with pytest.raises(ValueError,match="Replay input changed"):
            asyncio.run(idx.search({**q,"question":"changed"}))
        with pytest.raises(ValueError,match="KBL"):
            asyncio.run(idx.search({**q,"query_id":"unknown"}))
        with pytest.raises(ValueError,match="기준일"):
            asyncio.run(idx.search({**q,"as_of_date":"2026-10-25"}))


def test_replay_freeze_run_and_mcq_scores_never_require_embeddings(replay,tmp_path,monkeypatch):
    async def no_embed(*args,**kwargs):
        raise AssertionError("Replay must never embed")
    monkeypatch.setattr(Providers,"embed",no_embed)
    async def check():
        lock = tmp_path/"lock.json"
        protocol = await freeze(replay,str(lock))
        assert "embedding" not in protocol["protocol"]["providers"]
        out = await run(replay,"pilot",run_id="mcq",lock_path=str(lock))
        rows = read_jsonl(out/"raw.jsonl")
        assert len(rows)==3 and all(r["status"]=="ok" for r in rows)
        assert all(r["cost"]["online_usd"] is None and r["cost"]["rerank_generation_usd"]==0 for r in rows)
        assert "SECRET_GOLD_ONLY" not in (out/"raw.jsonl").read_text()
        evaluate(str(out))
        summary = read_json(out/"summary.json")
        assert all(r["mcq_accuracy"]==0 and r["esr"] is None and r["accuracy"] is None for r in summary)
        await run(replay,"pilot",run_id="mcq",resume=True,lock_path=str(lock))
        gold = Path(replay.benchmark_gold)
        gold.write_text(gold.read_text().replace('"B"','"A"'))
        with pytest.raises(ValueError,match="gold changed"):
            evaluate(str(out))
    asyncio.run(check())


def test_replay_detects_artifact_tampering(replay):
    with ReplayIndex(replay):
        pass
    path = Path(replay.index_dir)/"candidates.jsonl"
    path.write_text(path.read_text().replace("14일","20일"))
    with pytest.raises(ValueError,match="integrity"):
        ReplayIndex(replay)


def test_mcq_invalid_response_is_counted_as_wrong(replay):
    async def check():
        out=await run(replay,"pilot")
        rows=read_jsonl(out/"raw.jsonl")
        rows[0]["answer"]["answer"]="B or A"
        write_jsonl(out/"raw.jsonl",rows)
        evaluate(str(out))
        result=read_json(out/"summary.json")[0]
        assert result["invalid_choice"]==1 and result["mcq_accuracy"]==0
    asyncio.run(check())


def test_bm25_korean_search_filters_ties_and_immutable_index(corpus):
    cfg,_,chunks,_=corpus
    cfg=Config.model_validate(cfg.model_dump() | {"retriever_backend":"bm25","methods":["retrieval","ce_r"],"embedding_backend":"local"})
    chunks[0]["text"] = "근로계약서 미작성 책임"
    # Keep canonical hashes/offsets valid after introducing Korean text.
    from legal_rag_jev.io import digest
    chunks[0].update(text_hash=digest(chunks[0]["text"]),end=len(chunks[0]["text"]),start=0)
    write_jsonl(cfg.chunks,chunks)
    build_bm25(cfg)
    with BM25Index(cfg) as idx:
        found=asyncio.run(idx.search({"question":"근로계약서를 작성하지 않았습니다", "jurisdiction":"KR"}))
        assert found["candidates"][0]["doc_id"]=="law"
        assert "vector_score" not in found["candidates"][0]
        assert not asyncio.run(idx.search({"question":"근로계약서", "jurisdiction":"US"}))["candidates"]
        assert not asyncio.run(idx.search({"question":"근로계약서", "jurisdiction":"KR","as_of_date":"2020-01-01"}))["candidates"]
        assert not asyncio.run(idx.search({"question":"   "}))["candidates"]
    assert build_bm25(cfg)["count"]==3
    write_jsonl(cfg.chunks,chunks[:1])
    with pytest.raises(ValueError,match="immutable"):
        build_bm25(cfg)


def test_bm25_integrates_with_existing_evidence_pipeline(corpus,monkeypatch):
    cfg,*_=corpus
    cfg=Config.model_validate(cfg.model_dump() | {"retriever_backend":"bm25","methods":["retrieval","ce_r"],"embedding_backend":"local"})
    async def no_embed(*args,**kwargs):
        raise AssertionError("BM25 must never embed")
    monkeypatch.setattr(Providers,"embed",no_embed)
    build_bm25(cfg)
    out=asyncio.run(run(cfg,"dev"))
    evaluate(str(out))
    rows=read_jsonl(out/"raw.jsonl")
    assert all(r["status"]=="ok" and r["retrieval_label"]=="BM25" for r in rows)
    assert read_json(out/"summary.json")[0]["esr"]==1


def test_corpus_conversion_preserves_offsets_and_unknown_dates(tmp_path):
    from legal_rag_jev.corpus import load_documents,validate_dataset
    source=tmp_path/"statutes.jsonl"
    write_jsonl(source,[{"id":"docid-1___jo-1","contents":"테스트법 제1조\r\n근로계약서 작성 의무."}])
    output=tmp_path/"corpus"
    report=prepare_corpus(str(output),source=str(source),max_chars=30)
    docs=load_documents(str(output/"documents.jsonl"))
    chunks=read_jsonl(output/"chunks.jsonl")
    assert report["documents"]==1 and docs[0].effective_from is None
    assert validate_dataset(chunks,[],docs)["documents"]==1
    assert prepare_corpus(str(output),source=str(source),max_chars=30)==report


def test_viewer_can_switch_replay_and_bm25_and_keep_vector_config(replay,tmp_path,monkeypatch):
    configs=tmp_path/"configs";configs.mkdir()
    (configs/"replay.yaml").write_text(yaml.safe_dump(replay.model_dump()))
    (configs/"existing.yaml").write_text("qdrant_source: existing\nqdrant_mode: remote\napply_metadata_filters: false\n")
    viewer=Viewer(tmp_path/"results",configs)
    entries={x["path"]:x for x in viewer.configs_view()["configs"]}
    assert entries["replay.yaml"]["questions"][0]["query_id"]==load_run_queries(replay)[0].query_id
    assert '"label"' not in json.dumps(entries["replay.yaml"])
    assert entries["existing.yaml"]["existing_collection"]
    asker=Asker(tmp_path/"results",configs,str(tmp_path/"missing.env"))
    q=load_run_queries(replay)[0]
    result=asker.ask({"config":"replay.yaml","query_id":q.query_id,"question":q.question,"jurisdiction":"KR"})
    assert result["source"]["kind"]=="replay" and len(result["conditions"])==3
    with pytest.raises(ValueError,match="KBL"):
        asker.ask({"config":"replay.yaml","question":"새 질문","jurisdiction":"KR"})
    calls=[]
    class Existing:
        def __init__(self,*args): calls.append(args)
    from legal_rag_jev import existing_index
    monkeypatch.setattr(existing_index,"ExistingVectorIndex",Existing)
    open_retriever(Config(qdrant_source="existing",qdrant_mode="remote",apply_metadata_filters=False),None)
    assert calls


def test_backend_config_rejects_misleading_vector_label():
    with pytest.raises(ValueError,match="retrieval baseline"):
        Config(retriever_backend="bm25")


def test_readiness_uses_benchmark_inputs_and_no_embedding_identity(replay):
    from legal_rag_jev.readiness import readiness
    report = readiness(replay)
    assert report["checks"]["dataset"]["queries"]==1
    assert "embedding" not in report["checks"]["providers"]
    assert "documents" not in report["checks"]
    assert report["checks"]["original_retrieval"]["cost_usd"] is None


def test_benchmark_gold_mismatch_is_rejected_before_provider_calls(replay,monkeypatch):
    gold = Path(replay.benchmark_gold)
    # Change the external gold path without altering the immutable replay source.
    other=gold.parent.parent/"wrong-gold.jsonl"
    write_jsonl(other,[{"query_id":"unknown","label":"A"}])
    cfg=Config.model_validate(replay.model_dump() | {"benchmark_gold":str(other)})
    async def no_generate(*args,**kwargs):
        raise AssertionError("Invalid data must fail before generation")
    monkeypatch.setattr(Providers,"generate",no_generate)
    with pytest.raises(ValueError,match="question/gold IDs"):
        asyncio.run(run(cfg,"pilot"))

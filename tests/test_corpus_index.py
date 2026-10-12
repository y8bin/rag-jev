import asyncio
import numpy as np
import pytest

from legal_rag_jev.corpus import assign_splits, chunk_documents, load_queries, validate_dataset
from legal_rag_jev.index import VectorIndex, build_index, eligible, unit_vectors
from legal_rag_jev.io import read_json, write_jsonl
from legal_rag_jev.providers import Providers
from legal_rag_jev.schema import Document, Query


def test_structural_offsets_and_stable_ids():
    d = Document(doc_id="x",version_id="v",group_id="g",text="제1조 제목\n" + "긴 본문. "*40 + "\n\n제2조 끝")
    chunks = chunk_documents([d],80)
    assert len(chunks) > 2
    assert chunks == chunk_documents([d],80)
    assert all(d.text[c["start"]:c["end"]] == c["text"] and len(c["text"]) <= 80 for c in chunks)


def test_normalization_rejects_bad_vectors():
    for a in [np.zeros((1,2)),np.array([[np.nan,1]]),np.array([1,2])]:
        with pytest.raises(ValueError): unit_vectors(a)
    assert np.allclose(np.linalg.norm(unit_vectors(np.array([[3,4]])),axis=1),1)


def test_index_filters_persistence_and_corruption(corpus):
    cfg,docs,chunks,q = corpus
    async def check():
        p = Providers(cfg)
        try:
            m = await build_index(cfg,chunks,p)
            with VectorIndex(cfg,p) as idx:
                found = await idx.search(q.json_record())
                assert [c["doc_id"] for c in found["candidates"]] == ["law"]
                assert found["candidates"][0]["vector_score"] <= 1.00001
            assert (await build_index(cfg,chunks,p))["index_version"] == m["index_version"]
            assert not m["research_valid"]
            path = __import__('pathlib').Path(cfg.index_dir)/"chunks.jsonl"
            path.write_bytes(b"corrupt")
            with pytest.raises(ValueError,match="integrity"):
                VectorIndex(cfg,p)
        finally: await p.close()
    asyncio.run(check())


def test_actual_qdrant_index(corpus):
    cfg,docs,chunks,q = corpus
    async def check():
        p = Providers(cfg)
        try:
            m = await build_index(cfg,chunks,p)
            with VectorIndex(cfg,p) as idx:
                assert idx.client.count(idx.collection, exact=True).count == len(chunks)
                assert (await idx.search(q.json_record()))["candidates"][0]["doc_id"] == "law"
                assert m["backend"] == "qdrant"
            with VectorIndex(cfg,p) as idx:
                assert len(idx.chunks) == len(chunks)
        finally: await p.close()
    asyncio.run(check())


def test_exclusive_effective_end_and_unknown_policy(corpus):
    cfg,_,chunks,q = corpus
    assert not eligible(chunks[1],q.json_record(),cfg)
    unknown = {**chunks[0],"effective_from":None}
    assert not eligible(unknown,q.json_record(),cfg)
    assert eligible(unknown,q.json_record(),cfg.model_copy(update={"unknown_temporal_policy":"include"}))


def test_group_leakage_and_connected_split(corpus,tmp_path):
    cfg,docs,chunks,q = corpus
    other = q.model_copy(update={"query_id":"Q2","split":"test","group_id":"claimed-other"})
    write_jsonl(tmp_path/"leak.jsonl",[q.json_record(),other.json_record()])
    with pytest.raises(ValueError,match="leakage"): load_queries(str(tmp_path/"leak.jsonl"))
    third = {**q.json_record(),"query_id":"Q3","group_id":"other-group","evidence_units":[{"unit_id":"U1","doc_id":"other","version_id":"v1","start":0,"end":10}]}
    split = assign_splits([q.json_record(),other.json_record(),third],chunks,42,.5,.5)
    assert split[0]["split"] == split[1]["split"]
    assert split[0]["group_id"] == split[1]["group_id"]
    assert split[2]["split"] != split[0]["split"]


def test_invalid_gold_and_canonical_offsets(corpus):
    cfg,docs,chunks,q = corpus
    with pytest.raises(ValueError):
        Query(**{**q.json_record(),"sufficient_sets":[["UNKNOWN"]]})
    broken = [{**chunks[0],"text":"wrong"},*chunks[1:]]
    with pytest.raises(ValueError,match="offsets"):
        validate_dataset(broken,[q],docs)

import asyncio
import json
from pathlib import Path

import httpx
import numpy as np
import pytest
import yaml
from qdrant_client import QdrantClient, models

from legal_rag_jev.config import Config
from legal_rag_jev.existing_index import ExistingVectorIndex, existing_chunk
from legal_rag_jev.providers import Providers, Result
from legal_rag_jev.viewer import Asker, Viewer


@pytest.fixture
def existing_server(monkeypatch):
    import legal_rag_jev.index as module
    server = QdrantClient(":memory:")
    requests = []
    monkeypatch.setenv("QDRANT_BASE_URL", "https://qdrant.test.invalid")
    monkeypatch.setenv("QDRANT_API_KEY", "private-test-key")
    monkeypatch.delenv("QDRANT_COLLECTION", raising=False)
    monkeypatch.delenv("QDRANT_VECTOR_NAME", raising=False)

    def handle(request):
        requests.append(request)
        assert request.headers["api-key"] == "private-test-key"
        parts = request.url.path.strip("/").split("/")
        body = json.loads(request.content) if request.content else {}
        if parts == [""]:
            return httpx.Response(200, json={"title": "qdrant", "version": "1.19.0"})
        if parts == ["collections"]:
            result = server.get_collections().model_dump(mode="json")
        elif len(parts) == 2 and request.method == "GET":
            result = server.get_collection(parts[1]).model_dump(mode="json")
        elif parts[2:] == ["points", "query"]:
            query = body["query"]
            if isinstance(query, dict):
                query = query["nearest"]
            result = server.query_points(parts[1], query=query, using=body.get("using"),
                limit=body["limit"], with_payload=True).model_dump(mode="json")
        else:
            raise AssertionError(f"Unexpected write/scroll: {request.method} {request.url.path}")
        return httpx.Response(200, json={"result": result, "status": "ok", "time": 0.0})

    def client_factory(**kwargs):
        return QdrantClient(**kwargs, transport=httpx.MockTransport(handle), check_compatibility=False)

    monkeypatch.setattr(module, "QdrantClient", client_factory)
    yield server, requests
    server.close()


def config(tmp_path, **kwargs):
    return Config(qdrant_mode="remote", qdrant_source="existing", apply_metadata_filters=False,
        embedding_backend="mock", ce_backend="mock", jev_backend="mock", generation_backend="mock",
        judge_backend="mock", methods=["vector"], token_encoding="unicode_characters",
        embedding_dimension=8, top_k=2, top_n=1, index_dir=str(tmp_path / "missing-index"),
        cache_dir=str(tmp_path / "cache"), **kwargs)


def add_collection(server, name="laws", named=False, text="근로계약서 서면 교부 의무"):
    params = models.VectorParams(size=8, distance=models.Distance.COSINE)
    server.create_collection(name, vectors_config={"dense": params} if named else params)
    server.upsert(name, [models.PointStruct(id=1, vector={"dense": [1.0] + [0.0]*7} if named else [1.0] + [0.0]*7,
        payload={"page_content": text, "metadata": {"source": "노동법", "title": "서면 교부", "jurisdiction": "KR"}})])


@pytest.mark.parametrize("named", [False, True])
def test_existing_search_auth_payload_and_no_manifest_or_writes(existing_server, tmp_path, named):
    server, requests = existing_server
    add_collection(server, named=named)
    add_collection(server, "legal_rag_connection_check_test")
    cfg = config(tmp_path)

    async def check():
        p = Providers(cfg)
        async def embed(texts, query=False):
            return Result(np.array([[1.0] + [0.0]*7]), {"latency_ms": 0.0, "cost_usd": 0.0})
        p.embed = embed
        try:
            with ExistingVectorIndex(cfg, p) as idx:
                assert idx.collection == "laws"
                result = await idx.search({"question": "근로계약서?"})
                c = result["candidates"][0]
                assert c["text"] == "근로계약서 서면 교부 의무"
                assert c["doc_id"] == "노동법" and c["title"] == "서면 교부"
                assert c["vector_rank"] == 1 and c["vector_score"] == pytest.approx(1)
                assert not result["trace"]["metadata_filters_applied"]
                assert idx.manifest["research_valid"] is False
        finally:
            await p.close()
    asyncio.run(check())
    assert not Path(cfg.index_dir).exists()
    query = next(r for r in requests if r.url.path.endswith("/query"))
    assert json.loads(query.content)["limit"] == 2
    assert "private-test-key" not in json.dumps(cfg.model_dump())


def test_existing_ambiguous_collections_require_name_and_env_selects(existing_server, tmp_path, monkeypatch):
    server, _ = existing_server
    add_collection(server, "first")
    add_collection(server, "second")
    cfg = config(tmp_path)
    p = Providers(cfg)
    try:
        with pytest.raises(ValueError, match="QDRANT_COLLECTION.*first, second"):
            ExistingVectorIndex(cfg, p)
        monkeypatch.setenv("QDRANT_COLLECTION", "second")
        with ExistingVectorIndex(cfg, p) as idx:
            assert idx.collection == "second"
    finally:
        asyncio.run(p.close())


def test_existing_dimension_mismatch_fails_before_query(existing_server, tmp_path):
    server, requests = existing_server
    add_collection(server)
    cfg = config(tmp_path)
    async def check():
        p = Providers(cfg)
        async def embed(texts, query=False):
            return Result(np.ones((1, 12)), {})
        p.embed = embed
        try:
            with ExistingVectorIndex(cfg, p) as idx:
                with pytest.raises(ValueError, match="dimension 12.*dimension 8"):
                    await idx.search({"question": "test"})
        finally:
            await p.close()
    asyncio.run(check())
    assert not any(r.url.path.endswith("/query") for r in requests)


def test_existing_multiple_vectors_require_explicit_selection(existing_server, tmp_path, monkeypatch):
    server, _ = existing_server
    params = models.VectorParams(size=8, distance=models.Distance.COSINE)
    server.create_collection("laws", vectors_config={"dense": params, "alternative": params})
    cfg = config(tmp_path)
    p = Providers(cfg)
    try:
        with pytest.raises(ValueError, match="QDRANT_VECTOR_NAME"):
            ExistingVectorIndex(cfg, p)
        monkeypatch.setenv("QDRANT_VECTOR_NAME", "dense")
        with ExistingVectorIndex(cfg, p) as idx:
            assert idx.vector_name == "dense"
    finally:
        asyncio.run(p.close())


def test_existing_missing_text_is_reported_and_citation_ids_are_unique():
    from types import SimpleNamespace
    with pytest.raises(ValueError, match="no text payload"):
        existing_chunk(SimpleNamespace(id=1, payload={"metadata": {"title": "title"}}), "laws")
    one = existing_chunk(SimpleNamespace(id=1, payload={"chunk": {"text": "law", "chunk_id": "same"}}), "laws")
    two = existing_chunk(SimpleNamespace(id=2, payload={"chunk": {"text": "law", "chunk_id": "same"}}), "laws")
    assert one["chunk_id"] != two["chunk_id"]


def test_existing_mode_requires_explicit_filter_policy():
    with pytest.raises(ValueError, match="apply_metadata_filters"):
        Config(qdrant_source="existing", qdrant_mode="remote")


@pytest.mark.parametrize("merged", [False, True])
def test_legal_payload_keeps_law_identity_and_generation_metadata(merged):
    from types import SimpleNamespace
    from legal_rag_jev.prompts import evidence_text, generation_content
    from legal_rag_jev.viewer import detail

    header = "국세징수법 시행령 제2조(납부기한 전 징수)"
    payload = {"chunk_id": "KBX-L0125::제2조" if merged else "KBX-L0125-A0002-P01",
        "document_id": "KBX-L0125", "law_name": "국세징수법 시행령", "article": "제2조",
        "article_title": "납부기한 전 징수", "header": header if merged else header + " 제1항",
        "text": "① 납부기한 전 징수 요건\n② 납부고지 절차" if merged else "① 납부기한 전 징수 요건",
        "chunk_level": "article_merged" if merged else "paragraph", "part": 0,
        "n_parts": 1, "version_conflict": False}
    if merged:
        payload["member_chunk_ids"] = ["KBX-L0125-A0002-P01", "KBX-L0125-A0002-P02"]
    else:
        payload["paragraph"] = "제1항"
    c = existing_chunk(SimpleNamespace(id=10, payload=payload), "legal_article" if merged else "legal_as_is")
    assert c["doc_id"] == "KBX-L0125"
    assert c["title"] == c["citation_key"] == payload["header"]
    assert c["source_chunk_id"] == payload["chunk_id"]
    assert c["text"] == payload["text"]
    content = json.loads(evidence_text(c))
    assert content["law_name"] == payload["law_name"]
    assert content["article"] == "제2조" and content["version_conflict"] is False
    assert content["chunk_level"] == payload["chunk_level"]
    assert content["part"] == 0 and content["n_parts"] == 1
    generated = generation_content({"question": "납부기한 전 징수?"}, [c], None)
    assert generated["evidence"][0]["content"] == content
    viewed = detail([{"query": {"question": "test"}, "candidates": [c]}])["candidates"][0]
    assert viewed["source_chunk_id"] == payload["chunk_id"]
    if merged:
        assert viewed["member_chunk_ids"] == payload["member_chunk_ids"]
    else:
        assert viewed["paragraph"] == "제1항"


def test_viewer_existing_collection_logs_source_and_refetches_live_changes(existing_server, tmp_path):
    server, requests = existing_server
    add_collection(server)
    cfg = config(tmp_path)
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "env-qdrant.yaml").write_text(yaml.safe_dump(cfg.model_dump()))
    viewer = Viewer(tmp_path / "results", configs)
    entry = viewer.configs_view()["configs"][0]
    assert entry["index_built"] and entry["existing_collection"]
    asker = Asker(tmp_path / "results", configs, str(tmp_path / "missing.env"))
    body = {"config": "env-qdrant.yaml", "question": "근로계약서?"}
    first = asker.ask(body)
    assert first["source"]["collection"] == "laws"
    assert first["conditions"][0]["answer"]["answer"] == "근로계약서 서면 교부 의무"
    server.set_payload("laws", {"page_content": "갱신된 법률 원문"}, points=[1])
    second = asker.ask(body)
    assert second["conditions"][0]["answer"]["answer"] == "갱신된 법률 원문"
    assert len([r for r in requests if r.url.path.endswith("/query")]) == 2
    assert asker.get(second["ask_id"])["source"]["collection"] == "laws"
    assert viewer.runs()["runs"] == []
    assert not Path(cfg.cache_dir).exists()

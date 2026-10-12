import asyncio
import httpx
import numpy as np
import pytest

from legal_rag_jev.config import api_cost
from legal_rag_jev.providers import ProviderError, Providers


@pytest.fixture
def jev_env(monkeypatch):
    monkeypatch.setenv("JEV_BASE_URL","https://test.invalid")
    monkeypatch.setenv("JEV_API_KEY","private-test-key")
    monkeypatch.setenv("JEV_MODEL","pinned-test-model")
    monkeypatch.setenv("JEV_INPUT_USD_PER_MILLION","1")
    monkeypatch.setenv("JEV_OUTPUT_USD_PER_MILLION","0")


def test_official_jev_schema_concurrency_and_usage(corpus,jev_env):
    cfg,_,chunks,q = corpus
    cfg = cfg.model_copy(update={"jev_backend":"http"})
    bodies = []
    def handle(request):
        import json
        b = json.loads(request.content)
        bodies.append(b)
        assert request.headers["Authorization"] == "Bearer private-test-key"
        assert b["questions"]["applicable"]["type"] == "noul"
        assert "reference_answer" not in b["state"]["query"]
        return httpx.Response(200,json={"model":"resolved-pinned", "answers":{"applicable":{"type":"noul","noul":.8}},"usage":{"input_tokens":100,"output_tokens":2}})
    async def check():
        p = Providers(cfg,httpx.AsyncClient(transport=httpx.MockTransport(handle)))
        try:
            r = await p.jev(q.json_record(),chunks[:2])
            assert r.value == [.8,.8]
            assert r.trace["usage"]["input_tokens"] == 200
            assert r.trace["cost_usd"] == pytest.approx(.0002)
            assert "private-test-key" not in str(r.trace)
        finally: await p.close()
    asyncio.run(check())
    assert len(bodies) == 2


def test_retry_accounting_does_not_assume_free_failure(corpus,jev_env):
    cfg,_,chunks,q = corpus
    cfg = cfg.model_copy(update={"jev_backend":"http","max_retries":1})
    count = 0
    def handle(request):
        nonlocal count
        count += 1
        if count == 1: return httpx.Response(429,headers={"retry-after":"0"})
        return httpx.Response(200,json={"model":"m","answers":{"applicable":{"type":"noul","noul":.8}},"usage":{"input_tokens":10,"output_tokens":0}})
    async def check():
        p = Providers(cfg,httpx.AsyncClient(transport=httpx.MockTransport(handle)))
        try:
            r = await p.jev(q.json_record(),chunks[:1])
            assert r.trace["retry_count"] == 1
            assert r.trace["cost_usd"] is None
        finally: await p.close()
    asyncio.run(check())


@pytest.mark.parametrize("payload", [{"type":"noul","noul":2}, {"type":"noul","noul":float("nan")}, {"type":"score","score":.8}])
def test_bad_scores_are_failure_not_low_relevance(corpus,jev_env,payload):
    cfg,_,chunks,q = corpus
    cfg = cfg.model_copy(update={"jev_backend":"http"})
    def handle(request):
        # httpx json serialization rejects NaN; manually return that invalid response.
        import json
        return httpx.Response(200,content=json.dumps({"model":"m","answers":{"applicable":payload},"usage":{"input_tokens":1,"output_tokens":1}}).encode())
    async def check():
        p = Providers(cfg,httpx.AsyncClient(transport=httpx.MockTransport(handle)))
        try:
            with pytest.raises(ProviderError,match="failed"):
                await p.jev(q.json_record(),chunks[:1])
        finally: await p.close()
    asyncio.run(check())


def test_unknown_api_prices_are_null(monkeypatch):
    monkeypatch.delenv("JEV_INPUT_USD_PER_MILLION",raising=False)
    assert api_cost("jev",{"input_tokens":20,"output_tokens":0}) is None


def test_http_embedding_response_reordering(corpus,monkeypatch):
    cfg,_,_,_ = corpus
    for key,value in {"EMBEDDING_BASE_URL":"https://test.invalid/v1","EMBEDDING_MODEL":"test"}.items(): monkeypatch.setenv(key,value)
    cfg = cfg.model_copy(update={"embedding_backend":"http","index_backend":"qdrant"})
    def handle(request):
        return httpx.Response(200,json={"data":[{"index":1,"embedding":[0,1]},{"index":0,"embedding":[1,0]}],"usage":{"prompt_tokens":2}})
    async def check():
        p = Providers(cfg,httpx.AsyncClient(transport=httpx.MockTransport(handle)))
        try:
            r = await p.embed(["a","b"])
            assert np.array_equal(r.value,np.eye(2))
        finally: await p.close()
    asyncio.run(check())

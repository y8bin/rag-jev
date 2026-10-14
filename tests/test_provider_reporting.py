import asyncio
import json
import httpx
import pytest

from legal_rag_jev.annotation import export_annotations
from legal_rag_jev.config import Config
from legal_rag_jev.io import read_jsonl
from legal_rag_jev.lexical import lexical_pool
from legal_rag_jev.providers import Providers


def test_http_ce_reorders_full_candidate_results(corpus,monkeypatch):
    cfg,_,chunks,q = corpus
    monkeypatch.setenv("CE_BASE_URL","https://test.invalid")
    monkeypatch.setenv("CE_API_MODEL","test-ce")
    cfg = cfg.model_copy(update={"ce_backend":"http"})
    def handle(request):
        body = json.loads(request.content)
        assert body["top_n"] == 2
        assert "effective_from" in body["documents"][0]
        return httpx.Response(200,json={"results":[{"index":1,"relevance_score":.9},{"index":0,"relevance_score":.2}],"usage":{"input_tokens":20}})
    async def check():
        p = Providers(cfg,httpx.AsyncClient(transport=httpx.MockTransport(handle)))
        try: assert (await p.ce(q.json_record(),chunks[:2])).value == [.2,.9]
        finally: await p.close()
    asyncio.run(check())


def test_lexical_gold_pool_is_separate_and_blinded(corpus,tmp_path):
    cfg,_,chunks,q = corpus
    out = lexical_pool(cfg,"dev",2)
    rows = read_jsonl(out/"raw.jsonl")
    assert rows[0]["method"] == "lexical_pool"
    assert rows[0]["candidates"][0]["doc_id"] == "law"
    tasks = export_annotations(str(out),"relevance",str(tmp_path/"review"),42)
    assert "lexical_score" not in tasks.read_text()
    assert "lexical_rank" not in tasks.read_text()


def test_nonfinite_threshold_configuration_is_rejected():
    with pytest.raises(ValueError): Config(jev_threshold=float("nan"))


def test_real_test_requires_protocol_lock(corpus,monkeypatch):
    cfg,_,chunks,q = corpus
    from legal_rag_jev.io import write_jsonl
    from legal_rag_jev.pipeline import run
    cfg = cfg.model_copy(update={"methods":["vector"],"generation_backend":"openai"})
    monkeypatch.setenv("OPENAI_MODEL","test")
    write_jsonl(cfg.queries,[q.model_copy(update={"split":"test"}).json_record()])
    # Guard runs before network/index access.
    # A manifest is needed for protocol fingerprint, even though vectors aren't accessed.
    from legal_rag_jev.io import write_json
    from pathlib import Path
    write_json(Path(cfg.index_dir)/"manifest.json",{"index_version":"placeholder"})
    with pytest.raises(ValueError,match="require --lock"):
        asyncio.run(run(cfg,"test"))


def test_non_json_http_error_is_bounded_and_single_line():
    from legal_rag_jev.providers import http_error_detail
    response = httpx.Response(502, text='Proxy error\nBearer private-test-value\n' + 'x' * 2000)
    detail = http_error_detail(response)
    assert 'private-test-value' not in detail
    assert '\n' not in detail
    assert len(detail) <= 1003


def test_temperature_defaults_and_invalid_values():
    assert Config().temperature is None
    assert Config(temperature=None).temperature is None
    assert Config(temperature=0).temperature == 0
    for invalid in [-1, float('nan'), float('inf')]:
        with pytest.raises(ValueError):
            Config(temperature=invalid)

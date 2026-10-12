import asyncio
import json
import httpx
import pytest

from legal_rag_jev.cli import collect_candidates
from legal_rag_jev.annotation import export_annotations, import_relevance
from legal_rag_jev.config import Config
from legal_rag_jev.io import read_jsonl
from legal_rag_jev.lexical import lexical_pool
from legal_rag_jev.providers import ProviderError, Providers


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


def test_generator_contract_and_unknown_cost(corpus,monkeypatch):
    cfg,_,chunks,q = corpus
    monkeypatch.setenv("GENERATION_BASE_URL","https://test.invalid/v1")
    monkeypatch.setenv("GENERATION_MODEL","test-generator")
    monkeypatch.delenv("GENERATION_INPUT_USD_PER_MILLION",raising=False)
    cfg = cfg.model_copy(update={"generation_backend":"http"})
    def handle(request):
        body = json.loads(request.content)
        assert request.url.path == "/v1/chat/completions"
        assert "reference_answer" not in body["messages"][1]["content"]
        a = {"answer":"fourteen", "claims":[{"text":"fourteen","evidence_ids":[chunks[0]["chunk_id"]]}],"citations":[chunks[0]["chunk_id"]],"abstained":False}
        return httpx.Response(200,json={"model":"resolved-model","choices":[{"message":{"content":json.dumps(a)}}],"usage":{"prompt_tokens":120,"completion_tokens":20}})
    async def check():
        p = Providers(cfg,httpx.AsyncClient(transport=httpx.MockTransport(handle)))
        try:
            r = await p.generate(q.json_record(),chunks[:1])
            assert r.trace["cost_usd"] is None
            assert r.trace["returned_model"] == "resolved-model"
            assert r.value["claims"][0]["evidence_ids"] == [chunks[0]["chunk_id"]]
        finally: await p.close()
    asyncio.run(check())


def test_bad_generator_schema_is_logged_failure(corpus,monkeypatch):
    cfg,_,chunks,q = corpus
    monkeypatch.setenv("GENERATION_BASE_URL","https://test.invalid")
    monkeypatch.setenv("GENERATION_MODEL","test-generator")
    cfg = cfg.model_copy(update={"generation_backend":"http"})
    def handle(request):
        return httpx.Response(200,json={"choices":[{"message":{"content":"{\"answer\":\"wrong schema\"}"}}],"usage":{"prompt_tokens":1,"completion_tokens":1}})
    async def check():
        p = Providers(cfg,httpx.AsyncClient(transport=httpx.MockTransport(handle)))
        try:
            with pytest.raises(ProviderError,match="Answer schema") as e:
                await p.generate(q.json_record(),chunks[:1])
            assert e.value.trace["usage"]["input_tokens"] == 1
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
    cfg = cfg.model_copy(update={"methods":["vector"],"generation_backend":"http"})
    monkeypatch.setenv("GENERATION_BASE_URL","https://test.invalid")
    monkeypatch.setenv("GENERATION_MODEL","test")
    write_jsonl(cfg.queries,[q.model_copy(update={"split":"test"}).json_record()])
    # Guard runs before network/index access.
    # A manifest is needed for protocol fingerprint, even though vectors aren't accessed.
    from legal_rag_jev.io import write_json
    from pathlib import Path
    write_json(Path(cfg.index_dir)/"manifest.json",{"index_version":"placeholder"})
    with pytest.raises(ValueError,match="require --lock"):
        asyncio.run(run(cfg,"test"))


def test_http_failure_exposes_parameter_error_without_credentials(corpus, monkeypatch):
    cfg, _, chunks, q = corpus
    monkeypatch.setenv('GENERATION_BASE_URL', 'https://test.invalid/v1')
    monkeypatch.setenv('GENERATION_MODEL', 'test-generator')
    monkeypatch.setenv('GENERATION_API_KEY', 'secret-test-key')
    cfg = cfg.model_copy(update={'generation_backend': 'http'})
    requests = []
    def handle(request):
        requests.append(request)
        return httpx.Response(400, json={'error': {
            'message': "Unsupported parameter: max_tokens. Use max_completion_tokens. Key: secret-test-key",
            'type': 'invalid_request_error', 'code': 'unsupported_parameter', 'param': 'max_tokens'}})
    async def check():
        p = Providers(cfg, httpx.AsyncClient(transport=httpx.MockTransport(handle)))
        try:
            with pytest.raises(ProviderError, match='max_completion_tokens') as caught:
                await p.generate(q.json_record(), chunks[:1])
            error = caught.value
            assert 'param=max_tokens' in str(error)
            assert 'secret-test-key' not in str(error) + json.dumps(error.trace)
            assert '[REDACTED]' in str(error)
            assert error.trace['request_count'] == 1
            assert error.trace['cost_usd'] is None
            assert len(requests) == 1
        finally:
            await p.close()
    asyncio.run(check())


def test_non_json_http_error_is_bounded_and_single_line():
    from legal_rag_jev.providers import http_error_detail
    response = httpx.Response(502, text='Proxy error\nBearer private-test-value\n' + 'x' * 2000)
    detail = http_error_detail(response)
    assert 'private-test-value' not in detail
    assert '\n' not in detail
    assert len(detail) <= 1003


@pytest.mark.parametrize('temperature', [None, 0.0, 1.0])
@pytest.mark.parametrize('kind', ['generation', 'judge'])
def test_chat_omits_null_temperature_and_preserves_numeric_values(corpus, monkeypatch, temperature, kind):
    cfg, _, chunks, q = corpus
    cfg = Config.model_validate({**cfg.model_dump(), kind + '_backend': 'http', 'temperature': temperature})
    prefix = kind.upper()
    monkeypatch.setenv(prefix + '_BASE_URL', 'https://test.invalid/v1')
    monkeypatch.setenv(prefix + '_MODEL', 'codex/gpt-6.1-sol')
    requests = []
    def handle(request):
        body = json.loads(request.content)
        requests.append(body)
        if temperature is None:
            assert 'temperature' not in body
        else:
            assert body['temperature'] == temperature
        assert 'reasoning_effort' not in body
        assert body['model'] == 'codex/gpt-6.1-sol'
        assert body['max_tokens'] == cfg.max_output_tokens
        if body.get('temperature') == 0:
            return httpx.Response(400, json={'error': {'message': 'temperature=0 is unsupported while reasoning is active'}})
        answer = {'answer': 'fourteen', 'claims': [], 'citations': [], 'abstained': False}
        return httpx.Response(200, json={'choices': [{'message': {'content': json.dumps(answer)}}]})
    async def check():
        p = Providers(cfg, httpx.AsyncClient(transport=httpx.MockTransport(handle)))
        async def call():
            return await p.generate(q.json_record(), chunks[:1]) if kind == 'generation' else await p.judge({'question': 'test'})
        try:
            if temperature == 0:
                with pytest.raises(ProviderError, match='reasoning is active'):
                    await call()
            else:
                assert (await call()).value['answer'] == 'fourteen'
            assert len(requests) == 1
        finally:
            await p.close()
    asyncio.run(check())


def test_temperature_defaults_and_invalid_values():
    assert Config().temperature is None
    assert Config(temperature=None).temperature is None
    assert Config(temperature=0).temperature == 0
    for invalid in [-1, float('nan'), float('inf')]:
        with pytest.raises(ValueError):
            Config(temperature=invalid)


@pytest.mark.parametrize('kind', ['generation', 'judge'])
def test_json_mode_instruction_survives_system_message_conversion(corpus, monkeypatch, kind):
    cfg, _, chunks, q = corpus
    cfg = cfg.model_copy(update={kind + '_backend': 'http'})
    monkeypatch.setenv(kind.upper() + '_BASE_URL', 'https://test.invalid/v1')
    monkeypatch.setenv(kind.upper() + '_MODEL', 'codex/gpt-6.1-sol')
    judge_content = {'question': 'Notice deadline?', 'answer': 'fourteen days'}
    def handle(request):
        body = json.loads(request.content)
        assert body['response_format'] == {'type': 'json_object'}
        # Simulate a gateway that uses system messages as instructions and
        # validates only the remaining Responses input for JSON mode.
        user_text = body['messages'][1]['content']
        if 'json' not in user_text:
            return httpx.Response(400, json={'error': {'message': "Response input messages must contain the word 'json'"}})
        content = json.loads(user_text)
        assert 'JSON' in content['output_instruction']
        if kind == 'generation':
            from legal_rag_jev.prompts import generation_content
            # The budgeted and transmitted generator input must be identical.
            assert user_text == json.dumps(generation_content(q.json_record(), chunks[:1], cfg.common_input_chars), ensure_ascii=False)
            value = {'answer': 'fourteen days', 'claims': [], 'citations': [], 'abstained': False}
        else:
            assert content['question'] == judge_content['question']
            value = {'correctness': True, 'core_supported': True, 'claim_labels': []}
        return httpx.Response(200, json={'choices': [{'message': {'content': json.dumps(value)}}]})
    async def check():
        p = Providers(cfg, httpx.AsyncClient(transport=httpx.MockTransport(handle)))
        try:
            result = await p.generate(q.json_record(), chunks[:1]) if kind == 'generation' else await p.judge(judge_content)
            assert result.trace['request_count'] == 1
            assert 'output_instruction' not in judge_content
        finally:
            await p.close()
    asyncio.run(check())

import asyncio
import copy
import json

import httpx
import pytest

from legal_rag_jev.config import Config, api_cost, provider_identity
from legal_rag_jev.io import read_jsonl
from legal_rag_jev.openai_responses import response_format
from legal_rag_jev.providers import ProviderError, Providers


@pytest.fixture
def openai_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-secret")
    monkeypatch.setenv("OPENAI_MODEL", "test-platform-model")
    monkeypatch.setenv("OPENAI_JUDGE_MODEL", "test-platform-judge")
    for name in ("OPENAI_ORG_ID", "OPENAI_PROJECT_ID", "GENERATION_INPUT_USD_PER_MILLION",
                 "GENERATION_OUTPUT_USD_PER_MILLION", "GENERATION_CACHED_INPUT_USD_PER_MILLION",
                 "GENERATION_CACHE_WRITE_USD_PER_MILLION"):
        monkeypatch.delenv(name, raising=False)


def answer(chunks):
    cid = chunks[0]["chunk_id"] if chunks else None
    return {"answer": "fourteen days" if cid else "근거 부족", "rationale": "supplied evidence only",
            "claims": [{"text": "fourteen days", "evidence_ids": [cid]}] if cid else [],
            "citations": [cid] if cid else [], "abstained": not bool(cid)}


def response(value, **updates):
    return {"id": "resp_test", "model": "resolved-snapshot", "status": "completed", "service_tier": "default",
            "output": [{"type": "reasoning", "summary": []}, {"type": "message", "role": "assistant",
                       "status": "completed", "content": [{"type": "output_text", "text": json.dumps(value)}]}],
            "usage": {"input_tokens": 100, "output_tokens": 20,
                      "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
                      "output_tokens_details": {"reasoning_tokens": 10}}, **updates}


def generate(cfg, q, chunks, handler):
    async def check():
        providers = Providers(cfg, httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        try:
            return await providers.generate(q, chunks)
        finally:
            await providers.close()
    return asyncio.run(check())


def assert_strict_schema(schema):
    if isinstance(schema, dict):
        if schema.get("type") == "object":
            assert schema["additionalProperties"] is False
            assert set(schema["required"]) == set(schema["properties"])
        assert "default" not in schema
        for value in schema.values():
            assert_strict_schema(value)
    elif isinstance(schema, list):
        for value in schema:
            assert_strict_schema(value)


@pytest.mark.parametrize("temperature", [None, 0.5])
def test_official_request_contract_and_trace(corpus, openai_env, monkeypatch, temperature):
    cfg, _, chunks, q = corpus
    cfg = cfg.model_copy(update={"generation_backend": "openai", "temperature": temperature})
    monkeypatch.setenv("GENERATION_API_KEY", "gateway-secret")
    monkeypatch.setenv("GENERATION_MODEL", "codex/gateway-model")
    monkeypatch.setenv("GENERATION_BASE_URL", "https://gateway.invalid")
    monkeypatch.setenv("OPENAI_ORG_ID", "org-test")
    monkeypatch.setenv("OPENAI_PROJECT_ID", "proj-test")
    def handle(request):
        assert str(request.url) == "https://api.openai.com/v1/responses"
        assert request.headers["Authorization"] == "Bearer openai-test-secret"
        assert request.headers["OpenAI-Organization"] == "org-test"
        assert request.headers["OpenAI-Project"] == "proj-test"
        body = json.loads(request.content)
        assert body["model"] == "test-platform-model"
        assert body["max_output_tokens"] == cfg.max_output_tokens
        assert not {"max_tokens", "max_completion_tokens", "messages", "response_format", "previous_response_id"} & body.keys()
        assert body["store"] is False
        assert "instructions" in body
        assert body["text"]["format"]["strict"] is True
        assert_strict_schema(body["text"]["format"]["schema"])
        if temperature is None:
            assert "temperature" not in body
        else:
            assert body["temperature"] == temperature
        content = json.loads(body["input"][0]["content"])
        assert content["question"]["as_of_date"] == "2025-01-01"
        assert content["question"]["jurisdiction"] == "KR"
        assert content["evidence"][0]["chunk_id"] == chunks[0]["chunk_id"]
        assert "reference_answer" not in body["input"][0]["content"]
        # REST output may contain reasoning followed by multiple text segments.
        data = response(answer(chunks))
        raw = data["output"][1]["content"][0]["text"]
        data["output"][1]["content"] = [{"type": "output_text", "text": raw[:10]}, {"type": "output_text", "text": raw[10:]}]
        return httpx.Response(200, json=data, headers={"x-request-id": "req_test"})
    result = generate(cfg, q.json_record(), chunks[:1], handle)
    assert result.value == answer(chunks)
    assert result.trace["usage"]["reasoning_tokens"] == 10
    assert result.trace["returned_model"] == "resolved-snapshot"
    assert result.trace["response_id"] == "resp_test"
    assert result.trace["attempts"] == [{"status": 200, "request_id": "req_test"}]
    assert result.trace["cost_usd"] is None
    assert "openai-test-secret" not in json.dumps(result.trace)
    assert "gateway-secret" not in json.dumps(result.trace)


def test_no_evidence_generates_valid_abstention(corpus, openai_env):
    cfg, _, _, q = corpus
    cfg = cfg.model_copy(update={"generation_backend": "openai"})
    def handle(request):
        assert json.loads(json.loads(request.content)["input"][0]["content"])["evidence"] == []
        return httpx.Response(200, json=response(answer([])))
    assert generate(cfg, q.json_record(), [], handle).value == answer([])


@pytest.mark.parametrize("case, message", [
    ("refusal", "refused"), ("incomplete", "max_output_tokens"), ("filter", "content_filter"),
    ("failed", "failed"), ("empty", "no output_text"), ("json", "invalid JSON"),
    ("schema", "schema"), ("missing_default", "schema"), ("coercion", "schema"), ("output_type", "invalid output")])
def test_unsuccessful_outputs_keep_billable_usage(corpus, openai_env, case, message):
    cfg, _, chunks, q = corpus
    cfg = cfg.model_copy(update={"generation_backend": "openai"})
    data = response(answer(chunks))
    if case == "refusal":
        data["output"][1]["content"] = [{"type": "refusal", "refusal": "private explanation"}]
    elif case in ("incomplete", "filter"):
        data.update(status="incomplete", incomplete_details={"reason": "max_output_tokens" if case == "incomplete" else "content_filter"})
    elif case == "failed":
        data["status"] = "failed"
    elif case == "empty":
        data["output"] = []
    elif case == "json":
        data["output"][1]["content"][0]["text"] = "{broken"
    elif case == "output_type":
        data["output"] = None
    else:
        value = answer(chunks)
        if case == "schema": value["unexpected"] = True
        if case == "missing_default": del value["rationale"]
        if case == "coercion": value["abstained"] = "false"
        data["output"][1]["content"][0]["text"] = json.dumps(value)
    with pytest.raises(ProviderError, match=message) as caught:
        generate(cfg, q.json_record(), chunks[:1], lambda _: httpx.Response(200, json=data))
    assert caught.value.trace["usage"]["output_tokens"] == 20
    assert caught.value.trace["request_count"] == 1
    assert caught.value.trace["response_status"] == data["status"]


def test_platform_key_and_model_do_not_fall_back_to_gateway(corpus, openai_env, monkeypatch):
    cfg, _, chunks, q = corpus
    cfg = cfg.model_copy(update={"generation_backend": "openai"})
    monkeypatch.setenv("GENERATION_API_KEY", "gateway-secret")
    monkeypatch.setenv("GENERATION_MODEL", "codex/gateway-model")
    monkeypatch.delenv("OPENAI_API_KEY")
    def handle(_):
        pytest.fail("Missing Platform credential must fail before network access")
    with pytest.raises(ProviderError, match="Set OPENAI_API_KEY") as caught:
        generate(cfg, q.json_record(), chunks[:1], handle)
    assert caught.value.trace["request_count"] == 0
    monkeypatch.delenv("OPENAI_MODEL")
    with pytest.raises(ValueError, match="Set OPENAI_MODEL"):
        provider_identity("generation", "openai")
    monkeypatch.delenv("OPENAI_JUDGE_MODEL")
    with pytest.raises(ValueError, match="Set OPENAI_JUDGE_MODEL"):
        provider_identity("judge", "openai")


def test_http_error_redaction_and_request_id(corpus, openai_env):
    cfg, _, chunks, q = corpus
    cfg = cfg.model_copy(update={"generation_backend": "openai"})
    def handle(_):
        return httpx.Response(401, json={"error": {"message": "Invalid key openai-test-secret", "code": "invalid_api_key"}},
                              headers={"x-request-id": "req_bad"})
    with pytest.raises(ProviderError, match="invalid_api_key") as caught:
        generate(cfg, q.json_record(), chunks[:1], handle)
    assert "openai-test-secret" not in str(caught.value) + json.dumps(caught.value.trace)
    assert caught.value.trace["attempts"] == [{"status": 401, "request_id": "req_bad"}]


def test_retry_preserves_usage_but_total_cost_is_unknown(corpus, openai_env, monkeypatch):
    cfg, _, chunks, q = corpus
    cfg = cfg.model_copy(update={"generation_backend": "openai", "max_retries": 1})
    monkeypatch.setenv("GENERATION_INPUT_USD_PER_MILLION", "3")
    monkeypatch.setenv("GENERATION_OUTPUT_USD_PER_MILLION", "6")
    calls = []
    def handle(request):
        calls.append(request)
        return httpx.Response(429, headers={"retry-after": "0"}) if len(calls) == 1 else httpx.Response(200, json=response(answer(chunks)))
    result = generate(cfg, q.json_record(), chunks[:1], handle)
    assert result.trace["request_count"] == 2 and result.trace["retry_count"] == 1
    assert result.trace["usage"]["input_tokens"] == 100
    assert result.trace["cost_usd"] is None and result.trace["cost_complete"] is False


def test_cache_rates_and_reasoning_accounting(corpus, openai_env, monkeypatch):
    cfg, _, chunks, q = corpus
    cfg = cfg.model_copy(update={"generation_backend": "openai"})
    monkeypatch.setenv("GENERATION_INPUT_USD_PER_MILLION", "3")
    monkeypatch.setenv("GENERATION_OUTPUT_USD_PER_MILLION", "6")
    data = response(answer(chunks))
    data["usage"]["input_tokens_details"].update(cached_tokens=40, cache_write_tokens=10)
    handle = lambda _: httpx.Response(200, json=data)
    assert generate(cfg, q.json_record(), chunks[:1], handle).trace["cost_usd"] is None
    monkeypatch.setenv("GENERATION_CACHED_INPUT_USD_PER_MILLION", ".5")
    assert generate(cfg, q.json_record(), chunks[:1], handle).trace["cost_usd"] is None
    monkeypatch.setenv("GENERATION_CACHE_WRITE_USD_PER_MILLION", "4")
    result = generate(cfg, q.json_record(), chunks[:1], handle)
    assert result.trace["cost_usd"] == pytest.approx(.00033)
    assert result.trace["cost_complete"] is True
    assert api_cost("generation", {"input_tokens": 1, "output_tokens": 1, "cached_input_tokens": 2}) is None


def test_optional_judge_uses_its_own_model_and_contract(corpus, openai_env):
    cfg, *_ = corpus
    cfg = cfg.model_copy(update={"judge_backend": "openai"})
    value = {"correctness": True, "core_supported": True, "claim_labels": [
        {"support": "supported", "citations": [{"evidence_id": "C1", "supported": True}]}]}
    def handle(request):
        body = json.loads(request.content)
        assert body["model"] == "test-platform-judge"
        assert body["text"]["format"]["name"] == "legal_rag_judge"
        assert_strict_schema(body["text"]["format"]["schema"])
        return httpx.Response(200, json=response(value))
    async def check():
        p = Providers(cfg, httpx.AsyncClient(transport=httpx.MockTransport(handle)))
        try:
            assert (await p.judge({"question": "test", "answer": {}})).value == value
        finally:
            await p.close()
    asyncio.run(check())


def test_offline_readiness_checks_openai_credential_and_prices(corpus, openai_env, monkeypatch):
    from legal_rag_jev.readiness import readiness
    cfg, *_ = corpus
    cfg = cfg.model_copy(update={"generation_backend": "openai", "methods": ["vector"]})
    monkeypatch.delenv("OPENAI_API_KEY")
    report = readiness(cfg)
    assert report["checks"]["providers"]["generation"]["identity_configured"]
    assert not report["checks"]["providers"]["generation"]["credentials_configured"]
    assert {"generation.input", "generation.output"} <= set(report["checks"]["pricing"]["missing"])
    assert {"code": "provider_credentials_missing", "item": "generation"} in report["issues"]


def test_generation_smoke_needs_no_retrieval_and_returns_answer(openai_env, monkeypatch, tmp_path):
    from legal_rag_jev import cli
    cfg = Config(generation_backend="openai", chunks=str(tmp_path/"missing.jsonl"))
    calls = []
    def handle(request):
        content = json.loads(json.loads(request.content)["input"][0]["content"])
        calls.append(content)
        return httpx.Response(200, json=response(answer(content["evidence"])))
    monkeypatch.setattr(cli, "Providers", lambda cfg: Providers(cfg, httpx.AsyncClient(transport=httpx.MockTransport(handle))))
    report = asyncio.run(cli.smoke_generation(cfg))
    assert report["answer"]["citations"] == ["SYNTHETIC-C1"]
    assert report["invalid_citations"] == [] and not report["research_valid"]
    assert len(calls) == 1
    assert cli.parser().parse_args(["smoke-generation"]).command == "smoke-generation"


def test_pipeline_generates_and_reuses_only_matching_openai_cache(corpus, openai_env, monkeypatch):
    from legal_rag_jev import pipeline
    from legal_rag_jev.index import build_index
    from legal_rag_jev.viewer import Viewer
    cfg, _, chunks, q = corpus
    cfg = cfg.model_copy(update={"generation_backend": "openai", "methods": ["vector"]})
    calls = []
    def handle(request):
        body = json.loads(request.content)
        content = json.loads(body["input"][0]["content"])
        calls.append(copy.deepcopy(body))
        return httpx.Response(200, json=response(answer(content["evidence"])))
    monkeypatch.setattr(pipeline, "Providers", lambda cfg: Providers(cfg, httpx.AsyncClient(transport=httpx.MockTransport(handle))))
    async def check():
        p = Providers(cfg)
        try:
            await build_index(cfg, chunks, p)
        finally:
            await p.close()
        first = await pipeline.run(cfg, "dev", run_id="openai_1")
        second = await pipeline.run(cfg, "dev", run_id="openai_2")
        monkeypatch.setenv("OPENAI_MODEL", "another-platform-model")
        third = await pipeline.run(cfg, "dev", run_id="openai_3")
        return first, second, third
    first, second, third = asyncio.run(check())
    first_row, second_row, third_row = (read_jsonl(path/"raw.jsonl")[0] for path in (first, second, third))
    assert first_row["status"] == third_row["status"] == "ok"
    assert first_row["invalid_citations"] == []
    assert first_row["answer"]["citations"] == [first_row["selected"][0]["chunk_id"]]
    assert second_row["generation_trace"]["cached"]
    assert not third_row["generation_trace"]["cached"]
    assert [body["model"] for body in calls] == ["test-platform-model", "another-platform-model"]
    detail = Viewer(first.parent, first.parent).query(first.name, q.query_id)
    assert detail["conditions"][0]["answer"]["answer"] == "fourteen days"

from __future__ import annotations

import asyncio
import json
import math
import re
import time
from dataclasses import dataclass, field

import httpx
import numpy as np

from .config import Config, api_cost, env, local_cost, provider_identity
from .io import digest
from .prompts import APPLICABILITY, CRITERIA, GENERATION_SYSTEM, JUDGE_SYSTEM, RELEVANCE, evidence_text, generation_content, json_output_content, query_text
from .schema import Answer


def tokens(text: str, encoding: str = "cl100k_base") -> int:
    if encoding == "unicode_characters":
        # Offline demo only. This is explicitly character accounting, not model tokens.
        return len(text)
    import tiktoken
    # This is the experiment's common accounting tokenizer, not provider billing.
    return len(tiktoken.get_encoding(encoding).encode(text, disallowed_special=()))


@dataclass
class Result:
    value: object
    trace: dict = field(default_factory=dict)


class ProviderError(RuntimeError):
    def __init__(self, message: str, trace: dict | None = None):
        super().__init__(message)
        self.trace = trace or {}


def http_error_detail(response: httpx.Response, api_key: str = "") -> str:
    """Keep server diagnostics bounded and redact credentials echoed in errors."""
    try:
        data = response.json()
    except ValueError:
        detail = response.text
    else:
        error = data.get("error", data.get("detail", "")) if isinstance(data, dict) else data
        if isinstance(error, dict):
            detail = "; ".join(f"{field}={error[field]}" for field in ("message", "type", "code", "param")
                               if error.get(field) is not None)
        elif isinstance(error, str):
            detail = error
        else:
            detail = json.dumps(error, ensure_ascii=False)
    if api_key:
        detail = detail.replace(api_key, "[REDACTED]")
        detail = detail.replace(json.dumps(api_key)[1:-1], "[REDACTED]")
    detail = re.sub(r"(?i)Bearer\s+[^\s\"'<>]+", "Bearer [REDACTED]", detail)
    detail = " ".join(detail.split())
    return detail[:1000] + ("..." if len(detail) > 1000 else "")


def usage_of(kind: str, data: dict) -> dict:
    u = data.get("usage", {})
    if kind in ("generation", "judge"):
        return {"input_tokens": u.get("prompt_tokens", u.get("input_tokens")),
                "output_tokens": u.get("completion_tokens", u.get("output_tokens"))}
    if kind == "embedding":
        return {"input_tokens": u.get("prompt_tokens", u.get("input_tokens")), "output_tokens": 0}
    return {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens", 0 if kind == "ce" else None)}


class Transport:
    def __init__(self, cfg: Config, client: httpx.AsyncClient | None = None):
        self.cfg = cfg
        self.client = client or httpx.AsyncClient(timeout=cfg.timeout_seconds)
        self.semaphore = asyncio.Semaphore(cfg.concurrency)

    async def close(self):
        await self.client.aclose()

    async def request(self, kind: str, identity: dict, path: str, body: dict | None = None) -> Result:
        prefix = {"embedding": "EMBEDDING", "ce": "CE", "jev": "JEV", "generation": "GENERATION", "judge": "JUDGE"}[kind]
        key = env(prefix + "_API_KEY")
        headers = {"Authorization": "Bearer " + key} if key else {}
        if kind == "jev" and not key:
            raise ProviderError("Set JEV_API_KEY")
        start = time.perf_counter()
        attempts = []
        async with self.semaphore:
            for attempt in range(self.cfg.max_retries + 1):
                try:
                    response = await self.client.request("POST" if body is not None else "GET",
                        identity["base_url"] + path, json=body, headers=headers)
                    attempts.append({"status": response.status_code})
                    if response.status_code >= 400:
                        retryable = response.status_code == 429 or response.status_code >= 500
                        if retryable and attempt < self.cfg.max_retries:
                            try:
                                delay = float(response.headers.get("retry-after", 2 ** attempt))
                            except ValueError:
                                delay = 2 ** attempt
                            await asyncio.sleep(min(max(delay, 0), 10))
                            continue
                        detail = http_error_detail(response, key)
                        raise ProviderError(f"{kind}: HTTP {response.status_code}" + (f" — {detail}" if detail else ""))
                    try:
                        data = response.json()
                    except (ValueError, TypeError) as e:
                        raise ProviderError(f"{kind}: response is not JSON") from e
                    usage = usage_of(kind, data)
                    # A preceding failed request might have been billed. Never invent its usage.
                    cost = api_cost(kind, usage) if len(attempts) == 1 else None
                    return Result(data, {"latency_ms": (time.perf_counter() - start) * 1000,
                        "attempts": attempts, "request_count": len(attempts), "retry_count": len(attempts) - 1,
                        "usage": usage, "cost_usd": cost, "cost_complete": cost is not None,
                        "returned_model": data.get("model"), "identity": identity, "cached": False})
                except httpx.TransportError:
                    attempts.append({"error": "transport_error"})
                    if attempt < self.cfg.max_retries:
                        await asyncio.sleep(min(2 ** attempt, 10))
                        continue
                    break
                except ProviderError as e:
                    raise ProviderError(str(e), {"attempts": attempts, "request_count": len(attempts),
                        "retry_count": max(0, len(attempts) - 1), "cost_usd": None,
                        "latency_ms": (time.perf_counter() - start) * 1000, "identity": identity}) from e
        raise ProviderError(f"{kind}: transport retries exhausted", {"attempts": attempts,
            "request_count": len(attempts), "retry_count": max(0, len(attempts)-1), "cost_usd": None,
            "latency_ms": (time.perf_counter() - start) * 1000, "identity": identity})


def local_trace(kind: str, identity: dict, start: float, usage: dict | None = None) -> dict:
    ms = (time.perf_counter() - start) * 1000
    return {"latency_ms": ms, "request_count": 0, "retry_count": 0, "usage": usage or {},
            "cost_usd": 0.0 if identity["backend"] == "mock" else local_cost(ms),
            "identity": identity, "cached": False}


def features(text: str) -> list[str]:
    s = re.sub(r"\s+", "", text.lower())
    return [s[i:i+2] for i in range(max(1, len(s)-1))]


def mock_vectors(texts: list[str], dimension: int) -> np.ndarray:
    vectors = np.zeros((len(texts), dimension), dtype=np.float32)
    for i, text in enumerate(texts):
        for feature in features(text):
            h = int(digest(feature)[:16], 16)
            vectors[i, h % dimension] += 1 if h & (1 << 20) else -1
        if not vectors[i].any():
            vectors[i, 0] = 1
    return vectors


class Providers:
    def __init__(self, cfg: Config, client: httpx.AsyncClient | None = None):
        self.cfg = cfg
        self.transport = Transport(cfg, client)
        self._embedding = None
        self._ce = None

    def identity(self, kind: str) -> dict:
        return provider_identity(kind, getattr(self.cfg, kind + "_backend"))

    async def close(self):
        await self.transport.close()

    async def embed(self, texts: list[str], query: bool = False) -> Result:
        identity = self.identity("embedding")
        start = time.perf_counter()
        texts = [(self.cfg.query_prefix if query else self.cfg.document_prefix) + t for t in texts]
        if identity["backend"] == "mock":
            return Result(mock_vectors(texts, self.cfg.embedding_dimension), local_trace("embedding", identity, start))
        if identity["backend"] == "local":
            load_ms = 0.0
            if self._embedding is None:
                load_start = time.perf_counter()
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError as e:
                    raise ProviderError("Install .[local] for local models") from e
                self._embedding = SentenceTransformer(identity["model"], revision=identity["revision"],
                    device=identity["device"], token=env("HF_TOKEN") or None, trust_remote_code=False,
                    cache_folder=env("MODEL_CACHE_DIR",default=".cache/models"))
                load_ms = (time.perf_counter()-load_start)*1000
            start = time.perf_counter()
            m = self._embedding
            sizes = [len(m.tokenizer(t, truncation=False)["input_ids"]) for t in texts]
            a = m.encode(texts, batch_size=self.cfg.embedding_batch_size, convert_to_numpy=True,
                         normalize_embeddings=False, show_progress_bar=False)
            trace = local_trace("embedding", identity, start)
            trace.update({"truncated_inputs": sum(n > m.max_seq_length for n in sizes), "max_length": m.max_seq_length,
                          "initialization_ms": load_ms})
            return Result(np.asarray(a, dtype=np.float32), trace)
        result = await self.transport.request("embedding", identity, "/embeddings", {"model": identity["model"], "input": texts})
        try:
            items = result.value["data"]
            positions = [x["index"] for x in items]
            if sorted(positions) != list(range(len(texts))):
                raise ValueError("missing/duplicate embedding index")
            result.value = np.asarray([x["embedding"] for x in sorted(items, key=lambda x: x["index"])], dtype=np.float32)
            return result
        except (KeyError, ValueError, TypeError) as e:
            raise ProviderError("Invalid embeddings response", result.trace) from e

    async def ce(self, q: dict, chunks: list[dict]) -> Result:
        identity = self.identity("ce")
        start = time.perf_counter()
        pairs = [(query_text(q), evidence_text(c, self.cfg.common_input_chars)) for c in chunks]
        if not chunks:
            return Result([], local_trace("ce", identity, start))
        if identity["backend"] == "mock":
            question = set(features(q["question"]))
            scores = [len(question & set(features(c["text"]))) / max(1, len(question)) for c in chunks]
            return Result(scores, local_trace("ce", identity, start))
        if identity["backend"] == "local":
            load_ms = 0.0
            if self._ce is None:
                load_start = time.perf_counter()
                try:
                    from sentence_transformers import CrossEncoder
                except ImportError as e:
                    raise ProviderError("Install .[local] for CrossEncoder") from e
                self._ce = CrossEncoder(identity["model"], revision=identity["revision"], device=identity["device"],
                    max_length=self.cfg.ce_max_length, token=env("HF_TOKEN") or None, trust_remote_code=False,
                    cache_folder=env("MODEL_CACHE_DIR",default=".cache/models"))
                load_ms = (time.perf_counter()-load_start)*1000
            start = time.perf_counter()
            lengths = [len(self._ce.tokenizer(a, b, truncation=False)["input_ids"]) for a,b in pairs]
            scores = np.asarray(self._ce.predict(pairs, show_progress_bar=False)).reshape(-1).tolist()
            if len(scores) != len(chunks) or not all(math.isfinite(s) for s in scores):
                raise ProviderError("CE requires one finite scalar score per candidate")
            trace = local_trace("ce", identity, start)
            trace.update({"truncated_inputs": sum(n > self.cfg.ce_max_length for n in lengths),
                          "input_lengths": lengths, "max_length": self.cfg.ce_max_length,"initialization_ms":load_ms})
            return Result(scores, trace)
        result = await self.transport.request("ce", identity, "/rerank", {"model": identity["model"],
            "query": query_text(q), "documents": [b for _, b in pairs], "top_n": len(chunks)})
        try:
            items = result.value["results"]
            if sorted(x["index"] for x in items) != list(range(len(chunks))):
                raise ValueError("missing candidates")
            scores = [float(x["relevance_score"]) for x in sorted(items, key=lambda x: x["index"])]
            if not all(math.isfinite(s) for s in scores):
                raise ValueError("nonfinite score")
            result.value = scores
            return result
        except (KeyError, TypeError, ValueError) as e:
            raise ProviderError("Invalid rerank response", result.trace) from e

    async def jev(self, q: dict, chunks: list[dict]) -> Result:
        identity = self.identity("jev")
        start = time.perf_counter()
        if identity["backend"] == "mock":
            a = set(features(q["question"]))
            return Result([len(a & set(features(c["text"]))) / max(1, len(a)) for c in chunks],
                          local_trace("jev", identity, start))
        async def one(c):
            body = {"model": identity["model"], "state": {
                "query": json.loads(query_text(q)), "candidate": json.loads(evidence_text(c, self.cfg.common_input_chars))},
                "questions": {"applicable": {"type": "noul", "instructions":
                    APPLICABILITY if self.cfg.jev_instruction == "applicability" else RELEVANCE}}}
            if self.cfg.jev_instruction == "applicability":
                body["questions"]["applicable"]["criteria"] = CRITERIA
            r = await self.transport.request("jev", identity, "/v1/systemone", body)
            try:
                answer = r.value["answers"]["applicable"]
                score = float(answer["noul"])
                if answer["type"] != "noul" or not math.isfinite(score) or not 0 <= score <= 1:
                    raise ValueError("invalid probability")
                r.value = score
                r.trace["chunk_id"] = c["chunk_id"]
                return r
            except (KeyError, TypeError, ValueError) as e:
                raise ProviderError("Invalid Jev noul response", r.trace) from e
        results = await asyncio.gather(*(one(c) for c in chunks), return_exceptions=True)
        traces = [{**(r.trace if isinstance(r, (Result, ProviderError)) else {"cost_usd": None}),
                   "chunk_id": c["chunk_id"], "status": "failed" if isinstance(r, BaseException) else "ok",
                   **({"error": str(r) if isinstance(r, ProviderError) else type(r).__name__} if isinstance(r, BaseException) else {})}
                  for c,r in zip(chunks,results)]
        costs = [t.get("cost_usd") for t in traces]
        trace = {"identity": identity, "score_type": "noul_probability", "latency_ms": (time.perf_counter() - start)*1000,
            "calls": traces, "request_count": sum(t.get("request_count", 0) for t in traces),
            "retry_count": sum(t.get("retry_count", 0) for t in traces), "cached": False,
            "cost_usd": sum(costs) if all(c is not None for c in costs) else None,
            "usage": {k: sum(t.get("usage", {}).get(k) or 0 for t in traces)
                      if all(t.get("usage", {}).get(k) is not None for t in traces) else None
                      for k in ("input_tokens", "output_tokens")}}
        failures = [r for r in results if isinstance(r, BaseException)]
        if failures:
            raise ProviderError(f"Jev failed for {len(failures)}/{len(chunks)} candidates", trace)
        return Result([r.value for r in results], trace)

    async def chat(self, kind: str, system: str, content: dict) -> Result:
        identity = self.identity(kind)
        body = {"model": identity["model"],
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(json_output_content(content), ensure_ascii=False)}],
            "max_tokens": self.cfg.max_output_tokens,
            "response_format": {"type": "json_object"}}
        if self.cfg.temperature is not None:
            body["temperature"] = self.cfg.temperature
        result = await self.transport.request(kind, identity, "/chat/completions", body)
        try:
            raw = result.value["choices"][0]["message"]["content"]
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
            result.value = json.loads(raw)
            return result
        except (KeyError, TypeError, ValueError, IndexError, AttributeError) as e:
            raise ProviderError(f"Invalid {kind} JSON response", result.trace) from e

    async def generate(self, q: dict, chunks: list[dict]) -> Result:
        identity = self.identity("generation")
        if identity["backend"] == "mock":
            start = time.perf_counter()
            if chunks:
                cid, text = chunks[0]["chunk_id"], chunks[0]["text"]
                answer = Answer(answer=text, claims=[{"text": text, "evidence_ids": [cid]}], citations=[cid], abstained=False)
            else:
                answer = Answer(answer="제공된 근거가 부족합니다.", abstained=True)
            trace = local_trace("generation", identity, start)
            trace["usage"] = {"input_tokens": tokens(json.dumps(generation_content(q, chunks, self.cfg.common_input_chars), ensure_ascii=False), self.cfg.token_encoding),
                              "output_tokens": tokens(answer.answer, self.cfg.token_encoding)}
            return Result(answer.json_record(), trace)
        result = await self.chat("generation", GENERATION_SYSTEM, generation_content(q, chunks, self.cfg.common_input_chars))
        try:
            result.value = Answer.model_validate(result.value).json_record()
        except ValueError as e:
            raise ProviderError("Generator response does not match Answer schema", result.trace) from e
        return result

    async def judge(self, content: dict) -> Result:
        if self.cfg.judge_backend == "mock":
            raise ProviderError("Mock judge cannot create research judgments; fill human templates")
        return await self.chat("judge", JUDGE_SYSTEM, content)

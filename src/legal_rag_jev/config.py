from __future__ import annotations

import os
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, model_validator


METHODS = ("vector", "ce_r", "ce_fr", "jev_r", "jev_fr")


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    documents: str = "data/processed/documents.jsonl"
    chunks: str = "data/processed/chunks.jsonl"
    queries: str = "data/processed/queries.jsonl"
    index_dir: str = "indexes/main"
    output_dir: str = "results"
    cache_dir: str = ".cache"
    embedding_backend: Literal["local", "http", "mock"] = "local"
    index_backend: Literal["qdrant"] = "qdrant"
    qdrant_mode: Literal["local", "remote"] = "local"
    qdrant_source: Literal["managed", "existing"] = "managed"
    qdrant_existing_collection: str | None = None
    qdrant_vector_name: str | None = None
    qdrant_collection: str = Field(default="legal_rag", pattern=r"^[A-Za-z0-9_-]{1,100}$")
    ce_backend: Literal["local", "http", "mock"] = "local"
    jev_backend: Literal["http", "mock"] = "http"
    generation_backend: Literal["http", "mock"] = "http"
    judge_backend: Literal["http", "mock"] = "http"
    embedding_dimension: int = Field(default=512, ge=8)
    chunk_max_chars: int = Field(default=1800, ge=30)
    embedding_batch_size: int = Field(default=32, ge=1)
    query_prefix: str = ""
    document_prefix: str = ""
    top_k: int = Field(default=20, ge=1)
    top_n: int = Field(default=5, ge=1)
    ce_threshold: float | None = None
    jev_threshold: float | None = None
    methods: list[str] = Field(default_factory=lambda: list(METHODS))
    jev_instruction: Literal["applicability", "relevance"] = "applicability"
    token_budget: int | None = Field(default=None, ge=1)
    token_encoding: str = "cl100k_base"
    max_output_tokens: int = Field(default=1000, ge=1)
    temperature: float | None = Field(default=None, ge=0)
    timeout_seconds: float = Field(default=60, gt=0)
    max_retries: int = Field(default=3, ge=0, le=10)
    concurrency: int = Field(default=4, ge=1)
    ce_max_length: int = Field(default=512, ge=16)
    common_input_chars: int | None = Field(default=None, ge=1)
    unknown_temporal_policy: Literal["exclude", "include"] = "exclude"
    apply_metadata_filters: bool = True
    generate: bool = True
    human_evaluation_limit: int | None = Field(default=None, ge=1)
    seed: int = 20261009
    bootstrap_repetitions: int = Field(default=2000, ge=100)
    quality_delta: float = Field(default=0.02, ge=0, le=1)

    @model_validator(mode="after")
    def valid_methods(self):
        if self.qdrant_source == "existing" and self.qdrant_mode != "remote":
            raise ValueError("Existing collections require qdrant_mode: remote")
        if self.qdrant_source == "existing" and self.apply_metadata_filters:
            raise ValueError("Existing payload metadata is not mapped; set apply_metadata_filters: false for exploration")
        if not self.methods or len(set(self.methods)) != len(self.methods) or set(self.methods) - set(METHODS):
            raise ValueError(f"methods must be unique members of {METHODS}")
        if self.top_n > self.top_k:
            raise ValueError("top_n must not exceed top_k")
        return self

    @classmethod
    def load(cls, path: str, env_file: str = ".env") -> "Config":
        load_dotenv(env_file, override=False)
        return cls.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {})


def env(name: str, required: bool = False, default: str = "") -> str:
    value = os.getenv(name, default).strip()
    if required and not value:
        raise ValueError(f"Set {name} in .env or the process environment")
    return value


def rate(name: str) -> float | None:
    raw = env(name)
    if not raw:
        return None
    value = float(raw)
    if value < 0 or not __import__('math').isfinite(value):
        raise ValueError(f"{name} must be finite and nonnegative")
    return value


def endpoint(prefix: str) -> str:
    value = env(prefix + "_BASE_URL", required=True).rstrip("/")
    u = urlsplit(value)
    if u.scheme not in ("http", "https") or not u.netloc or u.username or u.password or u.query or u.fragment:
        raise ValueError(f"{prefix}_BASE_URL must be an HTTP URL without credentials/query parameters")
    return value


def provider_identity(kind: str, backend: str) -> dict:
    prefix = {"embedding": "EMBEDDING", "ce": "CE", "jev": "JEV", "generation": "GENERATION", "judge": "JUDGE"}[kind]
    if backend == "mock":
        return {"backend": "mock", "model": f"demo-{kind}-v1", "research_valid": False}
    if backend == "local":
        return {"backend": "local", "model": env(prefix + "_LOCAL_MODEL", True),
                "revision": env(prefix + "_LOCAL_REVISION", True), "device": env("MODEL_DEVICE", default="cpu")}
    name = "CE_API_MODEL" if kind == "ce" else prefix + "_MODEL"
    return {"backend": "http", "model": env(name, True), "base_url": endpoint(prefix)}


def pricing() -> dict:
    result = {kind: {"input": rate(prefix + "_INPUT_USD_PER_MILLION"),
                     "output": rate(prefix + "_OUTPUT_USD_PER_MILLION")}
              for kind, prefix in [("embedding", "EMBEDDING"), ("ce", "CE"), ("jev", "JEV"),
                                   ("generation", "GENERATION"), ("judge", "JUDGE")]}
    result["local_usd_per_hour"] = rate("LOCAL_USD_PER_HOUR")
    return result


def api_cost(kind: str, usage: dict) -> float | None:
    p = pricing()[kind]
    i, o = usage.get("input_tokens"), usage.get("output_tokens")
    if i is None or o is None or p["input"] is None or (o and p["output"] is None):
        return None
    return (i * p["input"] + o * (p["output"] or 0)) / 1_000_000


def local_cost(ms: float) -> float | None:
    price = rate("LOCAL_USD_PER_HOUR")
    return None if price is None else ms / 3_600_000 * price

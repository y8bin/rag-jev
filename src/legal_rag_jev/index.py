from __future__ import annotations

import shutil
import tempfile
import time
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
from qdrant_client import QdrantClient, models

from .config import Config, endpoint, env, search_cost, pricing
from .io import (digest, environment_manifest, file_hash, implementation_digest,
                 read_json, read_jsonl, write_json, write_jsonl)
from .providers import Providers


INDEX_SCHEMA = 2


def unit_vectors(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float32)
    if a.ndim != 2 or not np.isfinite(a).all() or a.shape[1] < 1:
        raise ValueError("Embedding matrix must contain finite 2D vectors")
    norms = np.linalg.norm(a, axis=1, keepdims=True)
    if (norms <= 0).any() or not np.isfinite(norms).all():
        raise ValueError("Zero-length or overflowing embedding")
    return np.ascontiguousarray(a / norms)


def embedding_signature(cfg: Config, providers: Providers) -> dict:
    return {"identity": providers.identity("embedding"), "query_prefix": cfg.query_prefix,
            "document_prefix": cfg.document_prefix, "mock_dimension": cfg.embedding_dimension,
            "normalization": "L2"}


def storage_signature(cfg: Config) -> dict:
    return {"mode": cfg.qdrant_mode, "collection_prefix": cfg.qdrant_collection,
            "base_url": endpoint("QDRANT") if cfg.qdrant_mode == "remote" else None,
            "distance": "Dot", "exact": True, "schema": INDEX_SCHEMA}


def open_client(cfg: Config, directory: Path) -> QdrantClient:
    if cfg.qdrant_mode == "remote":
        return QdrantClient(url=endpoint("QDRANT"), api_key=env("QDRANT_API_KEY") or None,
                            timeout=cfg.timeout_seconds, prefer_grpc=False)
    return QdrantClient(path=str(directory / "qdrant"))


def point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "legal-rag-jev/chunk/" + chunk_id))


def chunk_payload(chunk: dict) -> dict:
    # Numeric days keep inclusive starts/exclusive ends identical in local and server mode.
    return {"chunk": chunk,
            "effective_from_day": date.fromisoformat(chunk["effective_from"]).toordinal() if chunk.get("effective_from") else None,
            "effective_to_day": date.fromisoformat(chunk["effective_to"]).toordinal() if chunk.get("effective_to") else None}


def point_digest(points) -> str:
    return digest(sorted(({"id": str(p.id), "payload": p.payload,
                           "vector": np.asarray(p.vector, dtype=np.float32).tolist()}
                          for p in points), key=lambda p: p["id"]))


def scroll_points(client: QdrantClient, collection: str) -> list:
    points, offset = [], None
    while True:
        batch, offset = client.scroll(collection, limit=256, offset=offset,
                                      with_payload=True, with_vectors=True)
        points.extend(batch)
        if offset is None:
            return points


async def build_index(cfg: Config, chunks: list[dict], providers: Providers) -> dict:
    if cfg.qdrant_source == "existing":
        raise ValueError("Existing collection mode is read-only; use it through the viewer")
    if not chunks:
        raise ValueError("No chunks to index")
    if len({c["chunk_id"] for c in chunks}) != len(chunks):
        raise ValueError("Duplicate chunk IDs")
    signature, storage = embedding_signature(cfg, providers), storage_signature(cfg)
    version = digest({"chunks": chunks, "embedding": signature, "backend": cfg.index_backend, "storage": storage})
    destination = Path(cfg.index_dir)
    if destination.exists():
        existing = read_json(destination / "manifest.json")
        if existing.get("index_version") != version:
            raise ValueError("Index is immutable; choose a new index_dir for a different corpus/model/storage")
        with VectorIndex(cfg, providers) as check:
            return check.manifest
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".index-", dir=destination.parent))
    client, created = None, False
    collection = cfg.qdrant_collection + "_" + version
    try:
        start = time.perf_counter()
        matrices, traces = [], []
        for begin in range(0, len(chunks), cfg.embedding_batch_size):
            batch = chunks[begin:begin + cfg.embedding_batch_size]
            r = await providers.embed([c["text"] for c in batch])
            if len(r.value) != len(batch):
                raise ValueError("Embedding provider returned wrong number of vectors")
            matrices.append(r.value)
            traces.append(r.trace)
        vectors = unit_vectors(np.concatenate(matrices))
        points = [models.PointStruct(id=point_id(c["chunk_id"]), vector=v.tolist(), payload=chunk_payload(c))
                  for c, v in zip(chunks, vectors)]
        client = open_client(cfg, staging)
        if client.collection_exists(collection):
            raise ValueError("Qdrant collection already exists without this manifest; use a new collection prefix")
        client.create_collection(collection, vectors_config=models.VectorParams(size=vectors.shape[1], distance=models.Distance.DOT))
        created = True
        if cfg.qdrant_mode == "remote":
            for field, kind in [("chunk.jurisdiction", models.PayloadSchemaType.KEYWORD),
                                ("effective_from_day", models.PayloadSchemaType.INTEGER),
                                ("effective_to_day", models.PayloadSchemaType.INTEGER)]:
                client.create_payload_index(collection, field, field_schema=kind, wait=True)
        for begin in range(0, len(points), cfg.embedding_batch_size):
            client.upsert(collection, points=points[begin:begin + cfg.embedding_batch_size], wait=True)
        expected_digest = point_digest(points)
        if client.count(collection, exact=True).count != len(chunks) or point_digest(scroll_points(client, collection)) != expected_digest:
            raise ValueError("Qdrant build integrity check failed")
        client.close()
        client = None
        write_jsonl(staging / "chunks.jsonl", chunks)
        manifest = {"index_version": version, "backend": cfg.index_backend, "storage": storage,
            "collection": collection, "points_digest": expected_digest,
            "created_at": datetime.now(timezone.utc).isoformat(), "pricing": pricing(),
            "research_valid": cfg.embedding_backend != "mock",
            "embedding": signature, "dimension": vectors.shape[1], "count": len(chunks),
            "corpus_digest": digest(chunks), "implementation_digest": implementation_digest(),
            "offline_build_ms": (time.perf_counter()-start)*1000,
            "embedding_traces": traces, "environment": environment_manifest(),
            "artifacts": {"chunks.jsonl": file_hash(staging / "chunks.jsonl")}}
        write_json(staging / "manifest.json", manifest)
        staging.rename(destination)
        return manifest
    except BaseException:
        # Only remove a collection created by this attempt; never overwrite existing data.
        try:
            if cfg.qdrant_mode == "remote" and created:
                if client is None:
                    client = open_client(cfg, staging)
                client.delete_collection(collection)
        finally:
            if client is not None:
                client.close()
            shutil.rmtree(staging, ignore_errors=True)
        raise


def eligible(chunk: dict, q: dict, cfg: Config) -> bool:
    if not cfg.apply_metadata_filters:
        return True
    if q.get("jurisdiction") and chunk.get("jurisdiction") != q["jurisdiction"]:
        return False
    target = q.get("as_of_date")
    if target:
        begin, end = chunk.get("effective_from"), chunk.get("effective_to")
        if not begin and cfg.unknown_temporal_policy == "exclude":
            return False
        if begin and target < begin or end and target >= end:
            return False
    return True


def metadata_filter(q: dict, cfg: Config) -> models.Filter | None:
    if not cfg.apply_metadata_filters:
        return None
    conditions = []
    if q.get("jurisdiction"):
        conditions.append(models.FieldCondition(key="chunk.jurisdiction", match=models.MatchValue(value=q["jurisdiction"])))
    if q.get("as_of_date"):
        target = date.fromisoformat(q["as_of_date"]).toordinal()
        start = models.FieldCondition(key="effective_from_day", range=models.Range(lte=target))
        if cfg.unknown_temporal_policy == "include":
            start = models.Filter(should=[start, models.IsEmptyCondition(is_empty=models.PayloadField(key="effective_from_day"))])
        conditions.append(start)
        conditions.append(models.Filter(should=[
            models.IsEmptyCondition(is_empty=models.PayloadField(key="effective_to_day")),
            models.FieldCondition(key="effective_to_day", range=models.Range(gt=target))]))
    return models.Filter(must=conditions) if conditions else None


class VectorIndex:
    def __init__(self, cfg: Config, providers: Providers):
        if cfg.qdrant_source == "existing":
            raise ValueError("Existing collection mode is for viewer exploration; research runs require a managed snapshot")
        self.cfg, self.providers = cfg, providers
        self.client = None
        directory = Path(cfg.index_dir)
        self.manifest = read_json(directory / "manifest.json")
        if (self.manifest.get("embedding") != embedding_signature(cfg, providers)
                or self.manifest.get("backend") != cfg.index_backend
                or self.manifest.get("storage") != storage_signature(cfg)):
            raise ValueError("Index configuration/model/storage mismatch; rebuild in a new index_dir")
        for name, h in self.manifest["artifacts"].items():
            if Path(name).name != name or file_hash(directory / name) != h:
                raise ValueError(f"Index artifact integrity check failed: {name}")
        snapshot = read_jsonl(directory / "chunks.jsonl")
        if digest(snapshot) != self.manifest["corpus_digest"] or len(snapshot) != self.manifest["count"]:
            raise ValueError("Index corpus integrity check failed")
        self.collection = self.manifest["collection"]
        if self.collection != cfg.qdrant_collection + "_" + self.manifest["index_version"]:
            raise ValueError("Qdrant collection identity mismatch")
        # Never create a fresh local database while trying to load a missing index.
        if cfg.qdrant_mode == "local" and not (directory / "qdrant" / "meta.json").is_file():
            raise ValueError("Qdrant storage is missing")
        try:
            self.client = open_client(cfg, directory)
            if not self.client.collection_exists(self.collection):
                raise ValueError("Qdrant collection is missing")
            info = self.client.get_collection(self.collection)
            params = info.config.params.vectors
            if (not isinstance(params, models.VectorParams) or params.size != self.manifest["dimension"]
                    or params.distance != models.Distance.DOT
                    or self.client.count(self.collection, exact=True).count != self.manifest["count"]):
                raise ValueError("Qdrant dimensions/distance/count mismatch")
            points = scroll_points(self.client, self.collection)
            if point_digest(points) != self.manifest["points_digest"]:
                raise ValueError("Qdrant point integrity check failed")
            self.chunks = {str(p.id): p.payload["chunk"] for p in points}
            if {point_id(c["chunk_id"]): c for c in snapshot} != self.chunks:
                raise ValueError("Qdrant payload integrity check failed")
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    async def search(self, q: dict) -> dict:
        start = time.perf_counter()
        embedded = await self.providers.embed([q["question"]], query=True)
        vector = unit_vectors(embedded.value)
        if vector.shape != (1, self.manifest["dimension"]):
            raise ValueError("Query embedding dimension mismatch")
        search_start = time.perf_counter()
        query_filter = metadata_filter(q, self.cfg)
        count = self.client.count(self.collection, count_filter=query_filter, exact=True).count
        # Fetch all eligible exact scores to preserve chunk_id ordering even at a K-boundary tie.
        hits = self.client.query_points(self.collection, query=vector[0].tolist(), query_filter=query_filter,
            search_params=models.SearchParams(exact=True) if self.cfg.qdrant_mode == "remote" else None,
            limit=count, with_payload=True,
            with_vectors=False).points if count else []
        items = sorted(hits, key=lambda p: (-p.score, p.payload["chunk"]["chunk_id"]))
        result = [{**p.payload["chunk"], "vector_score": float(p.score), "vector_rank": rank + 1}
                  for rank, p in enumerate(items[:self.cfg.top_k])]
        ms = (time.perf_counter() - search_start) * 1000
        return {"candidates": result, "index_version": self.manifest["index_version"], "eligible_count": count,
            "trace": {"latency_ms": (time.perf_counter()-start)*1000, "search_ms": ms,
                      "embedding": embedded.trace, "search_cost_usd": 0.0 if self.cfg.embedding_backend == "mock" else search_cost(ms, self.cfg.qdrant_mode),
                      "search_cost_basis": "synthetic" if self.cfg.embedding_backend == "mock" else
                          "remote_elapsed_time_allocation" if self.cfg.qdrant_mode == "remote" else "local_elapsed_time_allocation",
                      "cached": False}}

"""Read-only search of existing Qdrant collections for viewer exploration."""
from __future__ import annotations

import time
from pathlib import Path

from qdrant_client import models

from .config import env, endpoint, search_cost
from .index import open_client, unit_vectors
from .io import digest
from .providers import ProviderError


def existing_chunk(point, collection: str) -> dict:
    payload = point.payload or {}
    nested = payload.get("chunk")
    body = nested if isinstance(nested, dict) else payload
    metadata = body.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    fields = {**metadata, **body}
    text = next((fields[k] for k in ("text", "page_content", "content", "document", "chunk_text")
                 if isinstance(fields.get(k), str) and fields[k].strip()), None)
    if text is None:
        raise ValueError(f"Qdrant point {point.id} has no text payload; expected text/page_content/content/document/chunk_text")
    # Include collection + point ID to keep citations unique even with duplicate source chunk IDs.
    cid = "Q_" + digest({"collection": collection, "point": str(point.id)})[:24]
    start = fields.get("start")
    start = start if isinstance(start, int) and start >= 0 else 0
    chunk = {k: fields.get(k) for k in ("title", "doc_type", "jurisdiction", "citation_key",
             "effective_from", "effective_to", "version_id", "source_uri")}
    legal_title = " ".join(str(fields[k]) for k in ("law_name", "article") if fields.get(k))
    if fields.get("article_title"):
        legal_title += f"({fields['article_title']})"
    if fields.get("paragraph"):
        legal_title += f" {fields['paragraph']}"
    chunk["title"] = fields.get("title") or fields.get("header") or legal_title or None
    chunk["citation_key"] = fields.get("citation_key") or fields.get("header") or chunk["title"]
    chunk.update({k: fields[k] for k in ("document_id", "law_name", "article", "article_title", "paragraph",
                  "header", "article_id", "chunk_level", "part", "n_parts", "member_chunk_ids", "version_conflict")
                  if k in fields})
    chunk.update(chunk_id=cid, doc_id=str(fields.get("doc_id") or fields.get("document_id") or fields.get("source") or point.id),
                 text=text, start=start, end=start + len(text), qdrant_point_id=str(point.id),
                 qdrant_collection=collection, source_chunk_id=fields.get("chunk_id"))
    return chunk


class ExistingVectorIndex:
    def __init__(self, cfg, providers):
        self.cfg, self.providers = cfg, providers
        self.client = open_client(cfg, Path(cfg.index_dir))
        try:
            configured = cfg.qdrant_existing_collection or env("QDRANT_COLLECTION")
            names = cfg.qdrant_existing_collections or ([name.strip() for name in configured.split(",")] if configured else [])
            if not names:
                names = [c.name for c in self.client.get_collections().collections
                         if not c.name.startswith(("legal_rag_demo", "legal_rag_connection_check"))]
                if len(names) != 1:
                    raise ValueError("Set QDRANT_COLLECTION in .env to comma-separated collections to search. "
                                     f"Available non-test collections: {', '.join(sorted(names)) or '(none)'}")
            if any(not name for name in names) or len(set(names)) != len(names):
                raise ValueError("QDRANT_COLLECTION must contain unique nonempty comma-separated names")
            # Canonical order also resolves equal scores independently of env/YAML ordering.
            self.collections = sorted(names)
            self.collection = self.collections[0] if len(self.collections) == 1 else None
            self.vector_names = {}
            specs = {}
            selected_vector = cfg.qdrant_vector_name or env("QDRANT_VECTOR_NAME") or None
            for name in self.collections:
                try:
                    info = self.client.get_collection(name)
                except Exception as e:
                    raise ValueError(f"Could not read Qdrant collection '{name}'; check its name, access, and server connection") from e
                vectors = info.config.params.vectors
                vector_name = selected_vector
                if isinstance(vectors, dict):
                    if vector_name is None and len(vectors) == 1:
                        vector_name = next(iter(vectors))
                    if vector_name not in vectors:
                        raise ValueError(f"Set QDRANT_VECTOR_NAME for '{name}'; available dense vectors: {', '.join(vectors)}")
                    params = vectors[vector_name]
                else:
                    if vector_name:
                        raise ValueError(f"QDRANT_VECTOR_NAME was set but collection '{name}' uses an unnamed vector")
                    params = vectors
                if params is None or params.distance not in (models.Distance.COSINE, models.Distance.DOT):
                    raise ValueError(f"Existing collection '{name}' must use a dense Cosine or Dot vector")
                self.vector_names[name] = vector_name
                specs[name] = {"vector": vector_name, "dimension": params.size,
                               "distance": params.distance.value, "count": info.points_count}
            if len({(spec["dimension"], spec["distance"]) for spec in specs.values()}) != 1:
                raise ValueError("All selected collections must use the same dimension and distance; index them with the same embedding model")
            self.vector_name = self.vector_names[self.collections[0]] if self.collection else None
            first = specs[self.collections[0]]
            self.manifest = {"index_version": digest({"server": endpoint("QDRANT"),
                "collections": {name: {k: v for k, v in spec.items() if k != "count"} for name, spec in specs.items()},
                "embedding": providers.identity("embedding"), "merge": "global_score_top_k_v1"}),
                "collection": self.collection, "collections": self.collections, "collection_specs": specs,
                "dimension": first["dimension"],
                "count": sum(spec["count"] for spec in specs.values()) if all(spec["count"] is not None for spec in specs.values()) else None,
                "research_valid": False, "source": "existing"}
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
            raise ValueError(f"Query embedding dimension {vector.shape[1]} differs from collection dimension "
                             f"{self.manifest['dimension']}; use the embedding model that indexed this collection")
        search_start = time.perf_counter()
        hits, per_collection = [], {}
        for name in self.collections:
            collection_start = time.perf_counter()
            # K per collection is sufficient to form the global K by score.
            # A failed collection aborts the request instead of silently reducing the corpus.
            try:
                points = self.client.query_points(name, query=vector[0].tolist(), using=self.vector_names[name],
                    limit=self.cfg.top_k, with_payload=True, with_vectors=False,
                    search_params=models.SearchParams(exact=True)).points
            except Exception as e:
                raise ProviderError(f"Qdrant search failed for collection '{name}'; no partial candidate pool is used",
                    {"latency_ms": (time.perf_counter() - start) * 1000, "embedding": embedded.trace,
                     "collections": self.collections, "failed_collection": name, "per_collection": per_collection,
                     "search_cost_usd": None, "cost_usd": None, "cached": False}) from e
            per_collection[name] = {"returned_count": len(points),
                                    "search_ms": (time.perf_counter() - collection_start) * 1000}
            hits.extend((name, p) for p in points)
        items = sorted(hits, key=lambda item: (-item[1].score, item[0], str(item[1].id)))[:self.cfg.top_k]
        candidates = [dict(existing_chunk(p, name), vector_score=float(p.score), vector_rank=i + 1)
                      for i, (name, p) in enumerate(items)]
        ms = (time.perf_counter() - search_start) * 1000
        return {"candidates": candidates, "index_version": self.manifest["index_version"],
                "eligible_count": None, "trace": {"latency_ms": (time.perf_counter()-start)*1000,
                "search_ms": ms, "embedding": embedded.trace, "search_cost_usd": search_cost(ms, self.cfg.qdrant_mode),
                "cached": False, "collection": self.collection, "collections": self.collections,
                "per_collection": per_collection, "merge": "global_score_top_k_v1", "metadata_filters_applied": False}}

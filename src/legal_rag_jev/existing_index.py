"""Read-only search of an existing Qdrant collection for viewer exploration."""
from __future__ import annotations

import time
from pathlib import Path

from qdrant_client import models

from .config import env, endpoint, local_cost
from .index import open_client, unit_vectors
from .io import digest


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
            name = cfg.qdrant_existing_collection or env("QDRANT_COLLECTION")
            if not name:
                names = [c.name for c in self.client.get_collections().collections
                         if not c.name.startswith(("legal_rag_demo", "legal_rag_connection_check"))]
                if len(names) != 1:
                    raise ValueError("Set QDRANT_COLLECTION in .env to the collection to search. "
                                     f"Available non-test collections: {', '.join(sorted(names)) or '(none)'}")
                name = names[0]
            self.collection = name
            info = self.client.get_collection(name)
            vectors = info.config.params.vectors
            self.vector_name = cfg.qdrant_vector_name or env("QDRANT_VECTOR_NAME") or None
            if isinstance(vectors, dict):
                if self.vector_name is None and len(vectors) == 1:
                    self.vector_name = next(iter(vectors))
                if self.vector_name not in vectors:
                    raise ValueError(f"Set QDRANT_VECTOR_NAME; available dense vectors: {', '.join(vectors)}")
                params = vectors[self.vector_name]
            else:
                if self.vector_name:
                    raise ValueError("QDRANT_VECTOR_NAME was set but this collection uses an unnamed vector")
                params = vectors
            if params is None or params.distance not in (models.Distance.COSINE, models.Distance.DOT):
                raise ValueError("Existing collection must use a dense Cosine or Dot vector")
            self.manifest = {"index_version": digest({"server": endpoint("QDRANT"), "collection": name,
                "vector": self.vector_name, "embedding": providers.identity("embedding")}),
                "collection": name, "dimension": params.size, "count": info.points_count,
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
        hits = self.client.query_points(self.collection, query=vector[0].tolist(), using=self.vector_name,
            limit=self.cfg.top_k, with_payload=True, with_vectors=False,
            search_params=models.SearchParams(exact=True)).points
        items = sorted(hits, key=lambda p: (-p.score, str(p.id)))
        candidates = [dict(existing_chunk(p, self.collection), vector_score=float(p.score), vector_rank=i + 1)
                      for i, p in enumerate(items)]
        ms = (time.perf_counter() - search_start) * 1000
        return {"candidates": candidates, "index_version": self.manifest["index_version"],
                "eligible_count": None, "trace": {"latency_ms": (time.perf_counter()-start)*1000,
                "search_ms": ms, "embedding": embedded.trace, "search_cost_usd": local_cost(ms),
                "cached": False, "collection": self.collection, "metadata_filters_applied": False}}

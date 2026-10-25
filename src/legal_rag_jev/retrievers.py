"""Switchable retrieval: existing/managed Qdrant, public candidate replay, SQLite BM25."""
from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import time
from functools import lru_cache
from pathlib import Path

from .config import local_cost
from .io import digest, file_hash, read_json, read_jsonl, write_json
from .providers import features
from .schema import Chunk

TOKENIZER = "nfc-lower-whitespace-free-bigram-hex-v1"


def terms(text: str) -> list[str]:
    # Hex encoding makes every feature an atomic ASCII token and prevents MATCH syntax injection.
    from .corpus import normalize
    return ["t" + t.encode().hex() for t in features(normalize(text)) if t]


@lru_cache(maxsize=32)
def _verified_hash(path: str, size: int, mtime_ns: int, ctime_ns: int) -> str:
    return file_hash(path)


def verify_artifacts(directory: Path, manifest: dict):
    for name, expected in manifest["artifacts"].items():
        if Path(name).name != name:
            raise ValueError("Unsafe index artifact path")
        path = directory / name
        stat = path.stat()
        if _verified_hash(str(path.resolve()), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns) != expected:
            raise ValueError(f"Index artifact integrity check failed: {name}")


def retrieval_manifest(cfg) -> dict:
    return read_json(Path(cfg.index_dir) / "manifest.json")


def open_retriever(cfg, providers, *, research=False):
    if cfg.retriever_backend == "replay":
        return ReplayIndex(cfg)
    if cfg.retriever_backend == "bm25":
        return BM25Index(cfg)
    if cfg.qdrant_source == "existing":
        if research:
            raise ValueError("Existing collection mode is for exploration; research runs require a managed snapshot")
        from .existing_index import ExistingVectorIndex
        return ExistingVectorIndex(cfg, providers)
    from .index import VectorIndex
    return VectorIndex(cfg, providers)


def validate_run_source(cfg, idx, queries):
    if cfg.query_mode == "evidence":
        from .corpus import validate_dataset
        validate_dataset(list(idx.chunks.values()), queries)
    else:
        from .mcq import validate_gold
        validate_gold(cfg, queries)
        if cfg.retriever_backend == "replay":
            for q in queries:
                idx.record(q.json_record())


class LocalIndex:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        pass

    def check_date(self, q):
        if self.cfg.snapshot_corpus and q.get("as_of_date"):
            raise ValueError("KBL 스냅샷은 시행일을 검증하지 않았습니다. 기준일을 비워 주세요.")


class ReplayIndex(LocalIndex):
    def __init__(self, cfg):
        self.cfg = cfg
        directory = Path(cfg.index_dir)
        self.manifest = retrieval_manifest(cfg)
        if self.manifest.get("backend") != "replay":
            raise ValueError("Replay index configuration mismatch")
        verify_artifacts(directory, self.manifest)
        self.collection = "KBL · 제공 후보"
        queries = read_jsonl(directory / "questions.jsonl")
        rows = read_jsonl(directory / "candidates.jsonl")
        self.records = {r["query_id"]: r for r in rows}
        self.questions = {q["query_id"]: q for q in queries}
        if len(self.records) != len(rows) or self.records.keys() != self.questions.keys():
            raise ValueError("Replay question/candidate IDs do not match")
        self.chunks = {c["chunk_id"]: c for r in rows for c in r["candidates"]}

    def record(self, q):
        self.check_date(q)
        original = self.questions.get(q.get("query_id"))
        if original is None:
            raise ValueError("제공 후보 모드에서는 준비된 KBL 문항을 선택해 주세요.")
        for field in ("question", "choices", "jurisdiction", "as_of_date"):
            if q.get(field) != original.get(field):
                raise ValueError(f"Replay input changed: {field}")
        return self.records[q["query_id"]]

    async def search(self, q):
        start = time.perf_counter()
        record = self.record(q)
        candidates = record["candidates"][:self.cfg.top_k]
        return {"candidates": candidates, "index_version": self.manifest["index_version"],
                "eligible_count": len(record["candidates"]), "trace": {
                    "backend": "replay", "retrieval_measurement": "precomputed", "latency_ms": (time.perf_counter()-start)*1000,
                    "search_ms": None, "embedding": {"cost_usd": 0.0, "request_count": 0},
                    "search_cost_usd": None, "cached": False, "original_query": record.get("original_query"),
                    "available_candidates": len(record["candidates"]), "metadata_filters_applied": False}}


def build_bm25(cfg) -> dict:
    source = Path(cfg.chunks)
    signature = {"backend": "bm25", "tokenizer": TOKENIZER, "chunks_sha256": file_hash(source),
                 "sqlite_version": sqlite3.sqlite_version, "schema": 1}
    version = digest(signature)
    destination = Path(cfg.index_dir)
    if destination.exists():
        with BM25Index(cfg) as idx:
            if idx.manifest["index_version"] != version:
                raise ValueError("Index is immutable; choose a new index_dir")
            return idx.manifest
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".bm25-", dir=destination.parent))
    db = None
    try:
        start = time.perf_counter()
        db = sqlite3.connect(staging / "search.sqlite")
        db.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY, chunk_id TEXT UNIQUE NOT NULL, payload TEXT NOT NULL, jurisdiction TEXT, effective_from TEXT, effective_to TEXT)")
        db.execute("CREATE VIRTUAL TABLE search USING fts5(terms, content='', tokenize='ascii')")
        count = 0
        with source.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                chunk = Chunk.model_validate_json(line).json_record()
                count += 1
                db.execute("INSERT INTO documents VALUES (?,?,?,?,?,?)", (count, chunk["chunk_id"], json.dumps(chunk, ensure_ascii=False),
                           chunk.get("jurisdiction"), chunk.get("effective_from"), chunk.get("effective_to")))
                db.execute("INSERT INTO search(rowid,terms) VALUES (?,?)", (count, " ".join(terms(chunk["text"]))))
                if count % 5000 == 0:
                    db.commit()
                    print(f"BM25: {count:,} chunks indexed", flush=True)
        if not count:
            raise ValueError("No chunks to index")
        db.execute("INSERT INTO search(search) VALUES ('optimize')")
        db.execute("INSERT INTO search(search) VALUES ('integrity-check')")
        db.commit()
        db.close()
        db = None
        manifest = {**signature, "index_version": version, "count": count, "collection": "KBL · BM25",
                    "research_valid": True, "dimension": None, "offline_build_ms": (time.perf_counter()-start)*1000,
                    "artifacts": {"search.sqlite": file_hash(staging / "search.sqlite")}}
        write_json(staging / "manifest.json", manifest)
        staging.rename(destination)
        return manifest
    finally:
        if db:
            db.close()
        if staging.exists():
            shutil.rmtree(staging)


class BM25Index(LocalIndex):
    def __init__(self, cfg):
        self.cfg, self.db = cfg, None
        directory = Path(cfg.index_dir)
        self.manifest = retrieval_manifest(cfg)
        if self.manifest.get("backend") != "bm25" or self.manifest.get("tokenizer") != TOKENIZER:
            raise ValueError("BM25 index configuration mismatch")
        verify_artifacts(directory, self.manifest)
        self.collection = self.manifest["collection"]
        self.db = sqlite3.connect((directory / "search.sqlite").resolve().as_uri() + "?mode=ro", uri=True)
        if self.db.execute("SELECT count(*) FROM documents").fetchone()[0] != self.manifest["count"]:
            self.close()
            raise ValueError("BM25 index count mismatch")

    @property
    def chunks(self):
        return {cid: json.loads(payload) for cid, payload in self.db.execute("SELECT chunk_id,payload FROM documents")}

    def close(self):
        if self.db:
            self.db.close()
            self.db = None

    async def search(self, q):
        self.check_date(q)
        start = time.perf_counter()
        query_terms = sorted(set(terms(q["question"])))
        if len(query_terms) > 512:
            raise ValueError("BM25 질문이 너무 깁니다. 핵심 질문을 512개 이하의 고유 글자쌍으로 줄여 주세요.")
        if not query_terms:
            found = []
        else:
            where, args = ["search MATCH ?"], [" OR ".join(query_terms)]
            if self.cfg.apply_metadata_filters:
                if q.get("jurisdiction"):
                    where.append("d.jurisdiction = ?")
                    args.append(q["jurisdiction"])
                if q.get("as_of_date"):
                    where.append("(d.effective_from <= ?" + (" OR d.effective_from IS NULL)" if self.cfg.unknown_temporal_policy == "include" else ")"))
                    where.append("(d.effective_to > ? OR d.effective_to IS NULL)")
                    args.extend([q["as_of_date"], q["as_of_date"]])
            found = self.db.execute("SELECT d.payload,bm25(search) AS score FROM search JOIN documents d ON d.id=search.rowid WHERE "
                                    + " AND ".join(where) + " ORDER BY score,d.chunk_id LIMIT ?", (*args, self.cfg.top_k)).fetchall()
        candidates = [{**json.loads(payload), "retrieval_rank": i+1, "retrieval_score": -score, "retriever": "bm25"}
                      for i, (payload, score) in enumerate(found)]
        elapsed = (time.perf_counter()-start)*1000
        return {"candidates": candidates, "index_version": self.manifest["index_version"], "eligible_count": None,
                "trace": {"backend": "bm25", "latency_ms": elapsed, "search_ms": elapsed,
                          "retrieval_measurement": "live", "embedding": {"cost_usd": 0.0, "request_count": 0},
                          "search_cost_usd": local_cost(elapsed), "search_cost_basis": "local_elapsed_time_allocation",
                          "cached": False, "metadata_filters_applied": self.cfg.apply_metadata_filters}}

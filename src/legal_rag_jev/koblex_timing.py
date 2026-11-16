"""Uncached scoring-only timings on identical quality-run candidates; no generation."""
from __future__ import annotations

import random
import time
import uuid
from pathlib import Path

import numpy as np

from .io import digest, file_hash, read_json, read_jsonl, write_json, write_jsonl
from .pipeline import protocol, select
from .providers import ProviderError, Providers


async def timing(cfg, lock_file: str, quality_dir: str, output: str):
    source, destination = Path(quality_dir), Path(output)
    providers = Providers(cfg)
    try:
        p = protocol(cfg, providers)
        if digest(p) != read_json(lock_file)["protocol_hash"]:
            raise ValueError("Scoring benchmark differs from locked protocol")
        manifest = read_json(source / "manifest.json")
        if manifest["protocol_hash"] != digest(p):
            raise ValueError("Quality candidates differ from locked protocol")
        raw = read_jsonl(source / "raw.jsonl")
        expected = manifest["planned_queries"]
        by_query = {}
        for qid in expected:
            records = [r for r in raw if r["query_id"] == qid]
            if sorted(r["condition_id"] for r in records) != ["ce_r", "jev_r", "vector"]:
                raise ValueError("Complete three-condition quality run required")
            candidates = records[0]["candidates"]
            if len(candidates) != cfg.top_k or any(r["candidates"] != candidates for r in records):
                raise ValueError("Scoring methods must share exactly K candidates")
            by_query[qid] = records[0]
        signature = {"protocol_hash": digest(p), "quality_raw_sha256": file_hash(source / "raw.jsonl"),
            "repeats": 3, "warmup_queries": 10, "cache": False, "query_concurrency": 1,
            "timed_region": "provider scoring plus deterministic selection; excludes retrieval and generation"}
        if destination.exists():
            if read_json(destination / "manifest.json") != signature:
                raise ValueError("Existing benchmark has another signature")
            rows = read_jsonl(destination / "raw.jsonl") if (destination / "raw.jsonl").exists() else []
        else:
            write_json(destination / "manifest.json", signature)
            rows = []
        completed = {(r["query_id"], r["method"], r["repetition"]) for r in rows}
        session_id = uuid.uuid4().hex
        needs_measurement = any((q, m, r) not in completed for q in expected for m in ("ce", "jev") for r in range(3))
        order = list(expected)
        random.Random(cfg.seed).shuffle(order)
        for repetition in (-1, 0, 1, 2):
            if repetition == -1 and not needs_measurement:
                continue
            jobs = [(q, m) for q in (order[:10] if repetition == -1 else order) for m in ("ce", "jev")]
            random.Random(cfg.seed + repetition).shuffle(jobs)
            for qid, method in jobs:
                if repetition >= 0 and (qid, method, repetition) in completed:
                    continue
                record = by_query[qid]
                row = {"query_id": qid, "method": method, "repetition": repetition,
                       "session_id": session_id,
                       "warmup": repetition == -1, "status": "ok"}
                start = time.perf_counter()
                try:
                    result = await getattr(providers, method)(record["query"], record["candidates"])
                    _, chosen = select(cfg, record["query"], record["candidates"], result.value, None)
                    row.update({"trace": result.trace, "selected_ids": [c["chunk_id"] for c in chosen]})
                except ProviderError as exc:
                    row.update({"status": "failed", "error": str(exc), "trace": exc.trace})
                row["wall_clock_ms"] = (time.perf_counter() - start) * 1000
                rows.append(row)
                write_jsonl(destination / "raw.jsonl", rows)
        summary = {"measured_queries": len(expected), "repetitions": 3, "methods": {}}
        for method in ("ce", "jev"):
            measured = [r for r in rows if not r["warmup"] and r["method"] == method]
            values = [r["wall_clock_ms"] for r in measured if r["status"] == "ok"]
            summary["methods"][method] = {"attempts": len(measured), "failures": sum(r["status"] != "ok" for r in measured),
                "mean_ms": float(np.mean(values)) if values else None,
                "p50_ms": float(np.quantile(values, .5)) if values else None,
                "p95_ms": float(np.quantile(values, .95)) if values else None}
        summary["interpretation"] = "Apple M5 Pro MPS CE versus remote Jev deployment, including network/retries"
        write_json(destination / "summary.json", summary)
        return summary
    finally:
        await providers.close()

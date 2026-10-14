from __future__ import annotations

import asyncio
import copy
import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .cache import Cache
from .config import Config, pricing
from .corpus import load_queries, validate_dataset
from .index import VectorIndex
from .io import digest, environment_manifest, file_hash, implementation_digest, read_json, read_jsonl, write_json, write_jsonl
from .prompts import APPLICABILITY, CRITERIA, GENERATION_SYSTEM, RELEVANCE, evidence_text, generation_content, query_text
from .providers import ProviderError, Providers, Result, tokens


def identities(cfg: Config, providers: Providers) -> dict:
    kinds = {"embedding"}
    if any(m.startswith("ce") for m in cfg.methods):
        kinds.add("ce")
    if any(m.startswith("jev") for m in cfg.methods):
        kinds.add("jev")
    if cfg.generate:
        kinds.add("generation")
    return {k: providers.identity(k) for k in sorted(kinds)}


def protocol(cfg: Config, providers: Providers) -> dict:
    return {"config": cfg.model_dump(exclude={"output_dir", "cache_dir"}), "providers": identities(cfg, providers),
            "implementation_digest": implementation_digest(), "dependency_versions": environment_manifest()["dependencies"],
            "pricing": pricing(), "queries_sha256": file_hash(cfg.queries),
            "protocol_documents_sha256": {path: file_hash(path) for path in cfg.protocol_documents},
            "index_version": read_json(Path(cfg.index_dir) / "manifest.json")["index_version"],
            "prompts": {"applicability": APPLICABILITY, "criteria": CRITERIA,
                        "relevance": RELEVANCE, "generator": GENERATION_SYSTEM}}


async def freeze(cfg: Config, path: str) -> dict:
    providers = Providers(cfg)
    try:
        load_queries(cfg.queries)
        with VectorIndex(cfg, providers) as idx:
            validate_dataset(list(idx.chunks.values()), load_queries(cfg.queries))
        p = protocol(cfg, providers)
        lock = {"protocol": p, "protocol_hash": digest(p), "frozen_at": datetime.now(timezone.utc).isoformat(),
                "environment": environment_manifest()}
        if Path(path).exists() and read_json(path)["protocol_hash"] != lock["protocol_hash"]:
            raise ValueError("Lock is immutable; choose a new path for a revised protocol")
        write_json(path, lock)
        return lock
    finally:
        await providers.close()


async def cached_call(cache: Cache, key: str, fn) -> Result:
    existing = cache.get(key)
    if existing is not None:
        trace = copy.deepcopy(existing["trace"])
        trace.update({"cached": True, "current_latency_ms": 0, "current_request_count": 0})
        return Result(existing["value"], trace)
    r = await fn()
    cache.put(key, {"value": r.value, "trace": r.trace})
    return r


def sum_cost(values: list[float | None]) -> float | None:
    return sum(values) if all(v is not None for v in values) else None


def actual_context(c: dict, cfg: Config) -> dict:
    result = dict(c)
    if cfg.common_input_chars is not None:
        result["text"] = c["text"][:cfg.common_input_chars]
        result["end"] = c["start"] + len(result["text"])
        result["context_text_hash"] = digest(result["text"])
    return result


def select(cfg: Config, q: dict, candidates: list[dict], scores: list[float] | None, threshold: float | None) -> tuple[list[dict], list[dict]]:
    ranking = [dict(c, rerank_score=float(scores[i]) if scores is not None else None) for i,c in enumerate(candidates)]
    ranking.sort(key=lambda c: (-(c["rerank_score"] if scores is not None else c["vector_score"]), c["vector_rank"], c["chunk_id"]))
    for i,c in enumerate(ranking):
        c["rank"] = i + 1
    chosen = []
    base_tokens = tokens(GENERATION_SYSTEM + "\n" + __import__('json').dumps(generation_content(q, [], cfg.common_input_chars), ensure_ascii=False), cfg.token_encoding)
    if cfg.token_budget is not None and base_tokens > cfg.token_budget:
        raise ValueError("token_budget is smaller than the empty generation prompt")
    for c in ranking:
        if threshold is not None and c["rerank_score"] < threshold:
            continue
        context = actual_context(c, cfg)
        if cfg.token_budget is not None:
            text = GENERATION_SYSTEM + "\n" + __import__('json').dumps(generation_content(q, chosen + [context], cfg.common_input_chars), ensure_ascii=False)
            if tokens(text, cfg.token_encoding) > cfg.token_budget:
                continue
        chosen.append(context)
        if len(chosen) >= cfg.top_n:
            break
    return ranking, chosen


async def query_rows(cfg: Config, idx: VectorIndex, providers: Providers, q: dict, conditions: list[dict],
                     cache: Cache, fresh: bool, run_id: str) -> list[dict]:
    retrieval_key = digest({"schema": 1, "implementation": implementation_digest(), "kind": "candidates", "index": idx.manifest["index_version"],
        "query": query_text(q), "k": cfg.top_k, "filters": cfg.apply_metadata_filters,
        "unknown_temporal": cfg.unknown_temporal_policy, "prices": pricing()["embedding"], "local_price": pricing()["local_usd_per_hour"]})
    retrieval = cache.get(retrieval_key)
    if retrieval:
        retrieval = copy.deepcopy(retrieval)
        retrieval["trace"]["cached"] = True
    else:
        try:
            retrieval = await idx.search(q)
            cache.put(retrieval_key, retrieval)
        except (ProviderError, ValueError) as e:
            return [{"run_id": run_id, "query": q, "method": cond["method"], "condition_id": cond["condition_id"],
                     "threshold": cond.get("threshold"), "status": "failed", "error_stage": "retrieval",
                     "error": str(e), "trace": getattr(e, "trace", {}), "candidates": [], "selected": [],
                     "answer": None, "cost": {"online_usd": None}, "timing": {"online_ms": None},
                     "index_version": idx.manifest["index_version"], "evaluation_mode": "fresh" if fresh else "quality"}
                    for cond in conditions]
    candidates = retrieval["candidates"]
    score_results: dict[str, Result | ProviderError] = {}
    for kind in sorted({c["method"].split("_")[0] for c in conditions if c["method"] != "vector"}):
        key = digest({"schema": 1, "implementation": implementation_digest(), "kind": kind, "identity": providers.identity(kind), "q": query_text(q),
            "candidates": [(c["chunk_id"], evidence_text(c, cfg.common_input_chars)) for c in candidates],
            "instruction": APPLICABILITY if cfg.jev_instruction == "applicability" else RELEVANCE,
            "criteria": CRITERIA, "ce_max_length": cfg.ce_max_length,
            "prices": pricing()[kind], "local_price": pricing()["local_usd_per_hour"]})
        try:
            score_results[kind] = await cached_call(cache, key, lambda k=kind: getattr(providers, k)(q, candidates))
        except ProviderError as e:
            score_results[kind] = e
    rows = []
    for cond in conditions:
        method = cond["method"]
        scored = score_results.get(method.split("_")[0])
        score_trace = scored.trace if scored else {"latency_ms": 0.0, "cost_usd": 0.0, "cached": False, "request_count": 0}
        row = {"run_id": run_id, "query": q, "query_id": q["query_id"], "group_id": q["group_id"],
            "method": method, "condition_id": cond["condition_id"], "threshold": cond.get("threshold"),
            "index_version": idx.manifest["index_version"], "candidates": candidates,
            "retrieval_trace": retrieval["trace"], "rerank_trace": score_trace,
            "selected": [], "answer": None, "status": "ok", "evaluation_mode": "fresh" if fresh else "quality"}
        if isinstance(scored, ProviderError):
            row.update({"status": "failed", "error_stage": "rerank", "error": str(scored)})
        else:
            try:
                ranked, selected = select(cfg, q, candidates, scored.value if scored else None, cond.get("threshold"))
                row.update({"ranking": ranked, "selected": selected, "selected_count": len(selected)})
                content = generation_content(q, selected, cfg.common_input_chars)
                row["context_tokens"] = tokens(__import__('json').dumps(content, ensure_ascii=False), cfg.token_encoding)
                if cfg.generate:
                    key = digest({"schema": 1, "implementation": implementation_digest(), "kind": "generation", "identity": providers.identity("generation"),
                        "system": GENERATION_SYSTEM, "content": content, "temperature": cfg.temperature,
                        "max_output_tokens": cfg.max_output_tokens, "prices": pricing()["generation"]})
                    generated = await cached_call(cache, key, lambda: providers.generate(q, selected))
                    row["answer"], row["generation_trace"] = generated.value, generated.trace
                    allowed = {c["chunk_id"] for c in selected}
                    citations = generated.value["citations"] + [x for claim in generated.value["claims"] for x in claim["evidence_ids"]]
                    row["invalid_citations"] = sorted(set(citations) - allowed)
            except (ProviderError, ValueError) as e:
                row.update({"status": "failed", "error_stage": "generation_or_selection", "error": str(e),
                            "generation_trace": getattr(e, "trace", {})})
        rt = retrieval["trace"]
        gt = row.get("generation_trace", {})
        generation_cost = gt.get("cost_usd") if cfg.generate and gt else 0.0
        online = sum_cost([rt["embedding"].get("cost_usd"), rt.get("search_cost_usd"), score_trace.get("cost_usd"), generation_cost])
        components = [rt, score_trace, gt] if cfg.generate else [rt, score_trace]
        live = row["status"] == "ok" and all(not t.get("cached") and t.get("latency_ms") is not None for t in components)
        row["cost"] = {"online_usd": online, "query_embedding_usd": rt["embedding"].get("cost_usd"),
                       "search_usd": rt.get("search_cost_usd"), "rerank_usd": score_trace.get("cost_usd"),
                       "generation_usd": generation_cost, "attribution": "full per-method service cost"}
        row["timing"] = {"online_ms": sum(t["latency_ms"] for t in components) if fresh and live else None,
            "component_sum_ms": sum(t.get("latency_ms", 0) for t in components),
            "cached": any(t.get("cached", False) for t in components),
            "quality_timing_is_online_latency": False}
        rows.append(row)
    return rows


def default_conditions(cfg: Config) -> list[dict]:
    result = []
    for m in cfg.methods:
        threshold = cfg.ce_threshold if m == "ce_fr" else cfg.jev_threshold if m == "jev_fr" else None
        if m.endswith("fr") and threshold is None:
            raise ValueError(f"{m} requires a development-selected threshold (use sweep first)")
        result.append({"method": m, "condition_id": m, "threshold": threshold})
    return result


def human_sample(cfg: Config, queries: list) -> list[str]:
    if cfg.human_evaluation_limit is None or cfg.human_evaluation_limit >= len(queries):
        return [q.query_id for q in queries]
    buckets = {}
    for q in queries:
        buckets.setdefault((q.task_type,q.answerable), []).append(q.query_id)
    rng = random.Random(cfg.seed)
    for key in sorted(buckets):
        bucket = buckets[key]
        bucket.sort()
        rng.shuffle(bucket)
    chosen = []
    while any(buckets.values()) and len(chosen) < cfg.human_evaluation_limit:
        for key in sorted(buckets):
            if buckets[key] and len(chosen) < cfg.human_evaluation_limit:
                chosen.append(buckets[key].pop())
    return chosen


async def run(cfg: Config, split: str, *, lock_path: str | None = None, run_id: str | None = None,
              fresh: bool = False, conditions: list[dict] | None = None, resume: bool = False) -> Path:
    providers = Providers(cfg)
    idx = None
    try:
        queries = load_queries(cfg.queries, split)
        if cfg.common_input_chars is not None and any(u.chunk_ids for q in queries for u in q.evidence_units):
            raise ValueError("Input truncation analyses require span-based gold units without chunk_ids")
        conditions = conditions or default_conditions(cfg)
        p = protocol(cfg, providers)
        if split == "test" and any(v["backend"] != "mock" for v in p["providers"].values()) and not lock_path:
            raise ValueError("Real test runs require --lock from freeze")
        if lock_path and read_json(lock_path)["protocol_hash"] != digest(p):
            raise ValueError("Protocol differs from lock; test configuration/data cannot be tuned")
        idx = VectorIndex(cfg, providers)
        validate_dataset(list(idx.chunks.values()), load_queries(cfg.queries))
        run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + uuid.uuid4().hex[:8]
        if Path(run_id).name != run_id or run_id in (".", ".."):
            raise ValueError("run_id must be a single directory name")
        output = Path(cfg.output_dir) / run_id
        run_signature = digest({"protocol": p, "split": split, "conditions": conditions, "fresh": fresh})
        rows = []
        if output.exists():
            if not resume or read_json(output / "manifest.json")["run_signature"] != run_signature:
                raise ValueError("Existing run; use a new ID or --resume with exactly the same protocol")
            if (output / "raw.jsonl").exists():
                rows = read_jsonl(output / "raw.jsonl")
        else:
            output.mkdir(parents=True)
            write_json(output / "manifest.json", {"run_id": run_id, "run_signature": run_signature, "protocol": p,
                "protocol_hash": digest(p), "split": split, "conditions": conditions, "mode": "fresh" if fresh else "quality",
                "research_valid": idx.manifest["research_valid"] and cfg.token_encoding != "unicode_characters" and all(v["backend"] != "mock" for v in p["providers"].values()),
                "planned_queries": [q.query_id for q in queries], "environment": environment_manifest()})
            manifest = read_json(output / "manifest.json")
            manifest["human_evaluation_query_ids"] = human_sample(cfg,queries)
            chosen_ids = set(manifest["human_evaluation_query_ids"])
            manifest["human_evaluation_sample"] = {
                "policy": "all_queries" if len(chosen_ids) == len(queries) else "round_robin_task_type_answerability",
                "estimand": "unweighted_mean_in_selected_questions", "seed": cfg.seed,
                "population_queries": len(queries), "selected_queries": len(chosen_ids),
                "selected_groups": len({q.group_id for q in queries if q.query_id in chosen_ids}),
                "strata": [{"task_type": task, "answerable": answerable,
                    "population": sum(q.task_type == task and q.answerable == answerable for q in queries),
                    "selected": sum(q.task_type == task and q.answerable == answerable and q.query_id in chosen_ids for q in queries)}
                    for task,answerable in sorted({(q.task_type,q.answerable) for q in queries})]}
            write_json(output / "manifest.json",manifest)
        complete = {(r["query"]["query_id"], r["condition_id"]) for r in rows}
        cache = Cache(cfg.cache_dir, enabled=not fresh)
        for q in queries:
            remaining = [c for c in conditions if (q.query_id, c["condition_id"]) not in complete]
            if not remaining:
                continue
            if fresh:
                # No score sharing between service measurements, even R/FR of the same model.
                random.Random(cfg.seed + int(digest(q.query_id)[:8], 16)).shuffle(remaining)
                for cond in remaining:
                    rows.extend(await query_rows(cfg, idx, providers, q.json_record(), [cond], cache, True, run_id))
            else:
                rows.extend(await query_rows(cfg, idx, providers, q.json_record(), remaining, cache, False, run_id))
            write_jsonl(output / "raw.jsonl", rows)
        write_json(output / "completion.json", {"planned_rows": len(queries)*len(conditions), "rows": len(rows),
            "failed": sum(r["status"] != "ok" for r in rows)})
        return output
    finally:
        if idx:
            idx.close()
        await providers.close()


async def benchmark(cfg: Config, split: str, repeats: int, warmup: int, limit: int, lock_path: str | None = None) -> Path:
    if repeats < 1 or warmup < 0 or limit < 1:
        raise ValueError("Invalid benchmark repetition/warmup/limit")
    providers = Providers(cfg)
    try:
        p = protocol(cfg, providers)
        if split == "test" and any(v["backend"] != "mock" for v in p["providers"].values()) and not lock_path:
            raise ValueError("Real test benchmark requires --lock")
        if lock_path and read_json(lock_path)["protocol_hash"] != digest(p):
            raise ValueError("Benchmark protocol differs from lock")
        buckets = {}
        rng = random.Random(cfg.seed)
        for q in load_queries(cfg.queries, split):
            buckets.setdefault((q.task_type,q.answerable), []).append(q)
        for bucket in buckets.values():
            rng.shuffle(bucket)
        queries = []
        while any(buckets.values()) and len(queries) < limit:
            for key in sorted(buckets):
                if buckets[key] and len(queries) < limit:
                    queries.append(buckets[key].pop())
        conditions = default_conditions(cfg)
        output = Path(cfg.output_dir) / ("benchmark_" + uuid.uuid4().hex[:10])
        rows = []
        with VectorIndex(cfg, providers) as idx:
            for repetition in range(-warmup, repeats):
                jobs = [(q,c) for q in queries for c in conditions]
                random.Random(cfg.seed + repetition).shuffle(jobs)
                for q,c in jobs:
                    start = time.perf_counter()
                    result = await query_rows(cfg, idx, providers, q.json_record(), [c], Cache(cfg.cache_dir, False), True, output.name)
                    result[0]["timing"]["wall_clock_ms"] = (time.perf_counter()-start)*1000
                    result[0]["repetition"] = repetition
                    if repetition >= 0:
                        rows.extend(result)
                if repetition >= 0:
                    write_jsonl(output / "raw.jsonl", rows)
        write_json(output / "manifest.json", {"protocol": p, "mode": "benchmark", "split": split,
            "warmup": warmup, "repeats": repeats, "query_ids": [q.query_id for q in queries], "environment": environment_manifest(),
            "research_valid": idx.manifest["research_valid"] and cfg.token_encoding != "unicode_characters" and all(v["backend"] != "mock" for v in p["providers"].values())})
        return output
    finally:
        await providers.close()

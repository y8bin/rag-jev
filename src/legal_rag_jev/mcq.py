"""Strict label scoring, separate from evidence sufficiency/human answer evaluation."""
from __future__ import annotations

from pathlib import Path

from .io import file_hash, read_json, read_jsonl, write_json, write_jsonl


def validate_gold(cfg, queries):
    rows = read_jsonl(cfg.benchmark_gold)
    gold = {row["query_id"]: row["label"] for row in rows}
    if len(gold) != len(rows) or set(gold) != {q.query_id for q in queries}:
        raise ValueError("Benchmark question/gold IDs do not match")
    if any(gold[q.query_id] not in q.choices for q in queries):
        raise ValueError("Invalid benchmark gold label")


def evaluate_mcq(run_dir: str) -> Path:
    directory = Path(run_dir)
    manifest = read_json(directory / "manifest.json")
    protocol = manifest["protocol"]
    cfg = protocol["config"]
    if not cfg["generate"]:
        raise ValueError("MCQ scoring requires generated answers")
    if manifest.get("mode") not in ("quality", "fresh"):
        raise ValueError("Only completed question runs can be scored")
    if file_hash(cfg["benchmark_gold"]) != protocol["benchmark_gold_sha256"]:
        raise ValueError("Benchmark gold changed since the run")
    gold_rows = read_jsonl(cfg["benchmark_gold"])
    gold = {r["query_id"]:r["label"] for r in gold_rows}
    if len(gold) != len(gold_rows):
        raise ValueError("Duplicate benchmark gold IDs")
    rows = read_jsonl(directory / "raw.jsonl")
    planned = {(q, c["condition_id"]) for q in manifest["planned_queries"] for c in manifest["conditions"]}
    keys = [(r["query"]["query_id"],r["condition_id"]) for r in rows]
    if len(keys) != len(set(keys)) or set(keys) != planned:
        raise ValueError("Benchmark run incomplete or contains duplicate/unknown rows")
    metrics = []
    for row in rows:
        q, answer = row["query"], row.get("answer") or {}
        expected = gold.get(q["query_id"])
        if expected not in q["choices"]:
            raise ValueError("Missing or invalid benchmark gold")
        prediction = answer.get("answer", "").strip()
        abstained = bool(answer.get("abstained"))
        valid = row["status"] == "ok" and not abstained and prediction in q["choices"]
        met = {"mcq_accuracy": float(valid and prediction == expected),
               "invalid_choice": float(row["status"] == "ok" and not abstained and not valid),
               "abstention": float(abstained), "task_success": float(row["status"] == "ok"),
               "selected_count": len(row.get("selected",[])), "context_tokens": row.get("context_tokens"),
               "online_cost_usd": row.get("cost",{}).get("online_usd"),
               "rerank_generation_usd": row.get("cost",{}).get("rerank_generation_usd"),
               "online_ms": row.get("timing",{}).get("online_ms"),
               "esr": None, "accuracy": None, "grounded_correct": None}
        metrics.append({"query_id":q["query_id"],"group_id":q["group_id"],"task_type":q["task_type"],
                        "condition_id":row["condition_id"],"method":row["method"],"metrics":met,"human_evaluated":False})
    summary = []
    for condition in manifest["conditions"]:
        subset = [m for m in metrics if m["condition_id"] == condition["condition_id"]]
        entry = {**condition,"queries":len(subset),"human_evaluated":0,"research_valid":manifest["research_valid"]}
        for key in subset[0]["metrics"]:
            values = [m["metrics"][key] for m in subset if m["metrics"][key] is not None]
            entry[key] = sum(values)/len(values) if values else None
            entry[key+"_n"] = len(values)
        by_task = {}
        for task in sorted({m["task_type"] for m in subset}):
            task_rows = [m for m in subset if m["task_type"] == task]
            by_task[task] = {"n":len(task_rows),"mcq_accuracy":sum(m["metrics"]["mcq_accuracy"] for m in task_rows)/len(task_rows)}
        entry["by_task"] = by_task
        entry["task_macro_accuracy"] = sum(t["mcq_accuracy"] for t in by_task.values())/len(by_task)
        summary.append(entry)
    write_jsonl(directory/"metrics.jsonl",metrics)
    write_json(directory/"summary.json",summary)
    return directory/"summary.json"

"""Paired, question-weighted cluster bootstrap for the locked three-arm study."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import math

import numpy as np

from .io import file_hash, read_json, read_jsonl, write_json


def paired_bootstrap(differences: list[float], groups: list[str], *, repetitions=10000, seed=20261108):
    if not differences or len(differences) != len(groups) or repetitions < 100:
        raise ValueError("Nonempty paired observations, groups and >=100 resamples required")
    values = np.asarray(differences, dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Non-finite paired observations")
    buckets = defaultdict(list)
    for group, value in zip(groups, values):
        buckets[group].append(value)
    ordered = [buckets[k] for k in sorted(buckets)]
    totals = np.asarray([sum(v) for v in ordered])
    counts = np.asarray([len(v) for v in ordered])
    observed = float(values.mean())
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(ordered), size=(repetitions, len(ordered)))
    boot = totals[draws].sum(axis=1) / counts[draws].sum(axis=1)
    # Approximate two-sided centered bootstrap test; one draw is one cluster resample.
    p = (int((np.abs(boot - observed) >= abs(observed) - 1e-15).sum()) + 1) / (repetitions + 1)
    return {"mean_difference": observed, "ci95": np.quantile(boot, [.025, .975]).tolist(),
            "p_centered_bootstrap_two_sided": p, "questions": len(values), "clusters": len(ordered),
            "repetitions": repetitions, "seed": seed, "estimand": "unweighted question mean"}


def analyze(metrics_root: str, group_audit: str, output: str, *, repetitions=10000, seed=20261108,
            lf_root: str | None = None, timing_root: str | None = None):
    destination = Path(output)
    if destination.exists():
        raise ValueError("Analysis output is immutable")
    root = Path(metrics_root)
    methods = ("vector", "ce_r", "jev_r")
    data = {m: read_jsonl(root / m / "metrics.jsonl") for m in methods}
    order = [r["query_id"] for r in data["vector"]]
    if not order or len(set(order)) != len(order) or any([r["query_id"] for r in data[m]] != order for m in methods):
        raise ValueError("All three methods must contain exactly the same unique IDs in order")
    audit = read_json(group_audit)
    primary_groups = audit["source_and_gold_groups"]["groups"]
    if set(order) != set(primary_groups):
        raise ValueError("Analysis must include every preregistered question")
    groups = [primary_groups[qid] for qid in order]
    comparisons = []
    # The two F1 claims form one prespecified multiplicity family. Other metrics are exploratory.
    for control in ("vector", "ce_r"):
        for metric in ("provision_f1", "token_f1", "provision_em", "gold_set_coverage"):
            def value(row):
                if metric == "token_f1":
                    return row[metric]
                key = {"provision_f1": "f1", "provision_em": "em"}.get(metric, metric)
                return row["retrieval"][key]
            diff = [value(j) - value(c) for j, c in zip(data["jev_r"], data[control])]
            result = paired_bootstrap(diff, groups, repetitions=repetitions, seed=seed)
            result.update({"treatment": "jev_r", "control": control, "metric": metric,
                           "confirmatory": metric == "provision_f1"})
            if metric != "provision_f1":
                result.pop("p_centered_bootstrap_two_sided")
            comparisons.append(result)
    family = sorted([r for r in comparisons if r["confirmatory"]], key=lambda r: r["p_centered_bootstrap_two_sided"])
    running = 0.0
    for i, result in enumerate(family):
        running = max(running, min(1.0, (len(family) - i) * result["p_centered_bootstrap_two_sided"]))
        result["p_holm"] = running
    report = {"comparisons": comparisons, "group_audit_sha256": file_hash(group_audit),
        "metric_sha256": {m: file_hash(root / m / "metrics.jsonl") for m in methods},
        "notes": ["Raw 0..1 scores; multiply by 100 only for display.",
                  "Paired cluster percentile intervals are marginal, not simultaneous intervals.",
                  "Timing and LF-Eval are separate outputs; no unsupported noninferiority claim."]}
    report["lf_eval_status"] = "NOT_RUN"
    if lf_root and Path(lf_root).exists():
        lf = {m: read_jsonl(Path(lf_root) / m / "metrics.jsonl") for m in methods}
        if any([r["query_id"] for r in lf[m]] != order for m in methods):
            raise ValueError("All LF-Eval conditions must contain every paired question in order")
        for control in ("vector", "ce_r"):
            result = paired_bootstrap([j["score"] - c["score"] for j, c in zip(lf["jev_r"], lf[control])],
                                      groups, repetitions=repetitions, seed=seed)
            result.pop("p_centered_bootstrap_two_sided")
            comparisons.append({**result, "treatment": "jev_r", "control": control,
                                "metric": "lf_eval", "confirmatory": False})
        report["lf_eval_status"] = "COMPLETE"
        report["lf_eval_sha256"] = {m: file_hash(Path(lf_root) / m / "metrics.jsonl") for m in methods}
    report["timing_status"] = "NOT_RUN"
    if timing_root and Path(timing_root).exists():
        measured = [r for r in read_jsonl(Path(timing_root) / "raw.jsonl") if not r["warmup"]]
        cells = defaultdict(list)
        for row in measured:
            cells[(row["query_id"], row["method"])].append(row)
        expected_cells = {(qid, m) for qid in order for m in ("ce", "jev")}
        if set(cells) != expected_cells or any(sorted(r["repetition"] for r in rs) != [0, 1, 2] for rs in cells.values()):
            raise ValueError("Timing requires three observations for every question and method")
        failures = sum(r["status"] != "ok" for r in measured)
        report["timing_failures"] = failures
        if failures:
            report["timing_status"] = "FAILURES_REPORTED_NO_COMPLETE_CASE_SUPERIORITY_CLAIM"
        else:
            def mean_ms(qid, method):
                return sum(r["wall_clock_ms"] for r in cells[(qid, method)]) / 3
            ratios = [math.log(mean_ms(qid, "jev") / mean_ms(qid, "ce")) for qid in order]
            result = paired_bootstrap(ratios, groups, repetitions=repetitions, seed=seed)
            report["timing_ratio"] = {**result,
                "geometric_mean_of_query_ratios_jev_over_ce": math.exp(result["mean_difference"]),
                "ratio_ci95": [math.exp(v) for v in result["ci95"]],
                "family": "separate single deployment latency claim"}
            report["timing_status"] = "COMPLETE"
        report["timing_sha256"] = file_hash(Path(timing_root) / "raw.jsonl")
    write_json(destination, report)
    return report

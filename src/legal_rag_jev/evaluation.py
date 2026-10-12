from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

from .io import read_json, read_jsonl, write_json, write_jsonl


def covered_units(q: dict, chunks: list[dict]) -> set[str]:
    covered = set()
    ids = {c["chunk_id"] for c in chunks}
    for u in q.get("evidence_units", []):
        if ids.intersection(u.get("chunk_ids", [])):
            covered.add(u["unit_id"])
            continue
        if u.get("start") is None:
            continue
        cursor = u["start"]
        spans = sorted((c["start"], c["end"]) for c in chunks if c["doc_id"] == u["doc_id"] and c["version_id"] == u["version_id"])
        for a,b in spans:
            if a > cursor:
                break
            if b > cursor:
                cursor = b
            if cursor >= u["end"]:
                covered.add(u["unit_id"])
                break
    return covered


def retrieval_metrics(q: dict, selected: list[dict], candidates: list[dict]) -> dict:
    units, pool_units = covered_units(q, selected), covered_units(q, candidates)
    sets = [set(s) for s in q.get("sufficient_sets", [])]
    labels = q.get("relevance", {})
    selected_ids = [c["chunk_id"] for c in selected]
    candidate_ids = [c["chunk_id"] for c in candidates]
    complete = all(cid in labels for cid in candidate_ids)
    selected_complete = all(cid in labels for cid in selected_ids)
    gains = [labels[c] for c in selected_ids] if selected_complete else []
    def dcg(values):
        return sum((2 ** g - 1) / math.log2(i + 2) for i,g in enumerate(values))
    ideal = dcg(sorted([labels[c] for c in candidate_ids], reverse=True)[:len(selected_ids)]) if complete else None
    n = len(selected_ids)
    # For FR, compare IDCG at the common configured N in evaluate(), not a smaller self-selected cutoff.
    return {"esr": float(any(s <= units for s in sets)) if q["answerable"] else None,
        "candidate_esr": float(any(s <= pool_units for s in sets)) if q["answerable"] else None,
        "recall": max((len(s & units)/len(s) for s in sets), default=0) if q["answerable"] else None,
        "candidate_recall": max((len(s & pool_units)/len(s) for s in sets), default=0) if q["answerable"] else None,
        "precision": sum(g == 2 for g in gains) / n if n and selected_complete else None,
        "mrr": next((1/(i+1) for i,g in enumerate(gains) if g == 2), 0.0) if selected_complete and complete else None,
        "ndcg": dcg(gains)/ideal if selected_complete and ideal else None,
        "judgment_coverage": sum(cid in labels for cid in candidate_ids)/len(candidate_ids) if candidate_ids else None,
        "empty_selection": float(not selected), "selected_count": n,
        "unanswerable_empty": float(not selected) if not q["answerable"] else None}


def answer_metrics(row: dict, annotation: dict | None) -> dict:
    q = row["query"]
    a = row.get("answer")
    result = {"grounded_correct": None, "accuracy": None, "claim_support": None,
        "unsupported_claims": None, "contradicted_claims": None, "citation_support": None,
        "claim_citation_coverage": None, "appropriate_abstention": None, "over_abstention": None}
    if a is None or row["status"] != "ok":
        if q["answerable"]:
            result["grounded_correct"] = 0.0 # planned task success includes technical failures
            result["accuracy"] = 0.0
        return result
    result["appropriate_abstention"] = float(a["abstained"]) if not q["answerable"] else None
    result["over_abstention"] = float(a["abstained"]) if q["answerable"] else None
    if q["answerable"] and a["abstained"]:
        result["grounded_correct"] = 0.0
        result["accuracy"] = 0.0
    if annotation is None:
        return result
    from .annotation import validate_answer_annotation
    validate_answer_annotation(row, annotation)
    labels = annotation["claim_labels"]
    status = [x["support"] for x in labels]
    allowed = {c["chunk_id"] for c in row["selected"]}
    citations = [(c["evidence_id"], c["supported"]) for x in labels for c in x["citations"]]
    if status:
        for metric,label in [("claim_support", "supported"), ("unsupported_claims", "unsupported"), ("contradicted_claims", "contradicted")]:
            result[metric] = status.count(label)/len(status)
        result["claim_citation_coverage"] = sum(any(c["supported"] and c["evidence_id"] in allowed for c in x["citations"]) for x in labels)/len(labels)
    if citations:
        result["citation_support"] = sum(s and cid in allowed for cid,s in citations)/len(citations)
    if q["answerable"]:
        result["accuracy"] = float(annotation["correctness"] and not a["abstained"])
        # Explicit citations must support claims; unknown/unmapped IDs cannot pass.
        used = set(a["citations"]) | {cid for claim in a["claims"] for cid in claim["evidence_ids"]}
        judged_supported = {cid for cid,s in citations if s and cid in allowed}
        citation_ok = bool(citations) and all(s and cid in allowed for cid,s in citations) and used <= judged_supported and all(
            any(c["supported"] and c["evidence_id"] in allowed for c in label["citations"]) for label in labels)
        result["grounded_correct"] = float(annotation["correctness"] and annotation["core_supported"] and
            not a["abstained"] and bool(labels) and all(s == "supported" for s in status) and citation_ok)
    return result


def evaluate(run_dir: str, annotations: str | None = None) -> Path:
    directory = Path(run_dir)
    manifest = read_json(directory / "manifest.json")
    if manifest.get("mode") not in ("quality", "fresh"):
        raise ValueError("Only completed quality/fresh runs are evaluated; annotation pools and benchmarks have separate workflows")
    raw = read_jsonl(directory / "raw.jsonl")
    seen = {(r["query"]["query_id"], r["condition_id"]) for r in raw}
    if len(seen) != len(raw):
        raise ValueError("Duplicate query/condition rows")
    if len(raw) != len(manifest["planned_queries"]) * len(manifest["conditions"]):
        raise ValueError("Run is incomplete; resume it before evaluation")
    human = {}
    human_ids = set(manifest.get("human_evaluation_query_ids",manifest["planned_queries"]))
    path = Path(annotations) if annotations else directory / "annotations.jsonl"
    if path.is_file():
        for a in read_jsonl(path):
            if a.get("source") != "human":
                raise ValueError("Primary evaluation requires human annotations, not automatic judge labels")
            key = (a["query_id"], a["condition_id"])
            if key in human or key not in seen:
                raise ValueError("Duplicate or unknown annotation key")
            if a["query_id"] not in human_ids:
                raise ValueError("Annotation lies outside the preregistered human evaluation subset")
            human[key] = a
    metrics = []
    n = manifest["protocol"]["config"]["top_n"]
    for r in raw:
        q = r["query"]
        met = retrieval_metrics(q, r.get("selected", []), r.get("candidates", []))
        labels = q.get("relevance", {})
        candidates = r.get("candidates", [])
        selected = r.get("selected", [])
        if candidates and all(c["chunk_id"] in labels for c in candidates):
            ideal = sum((2**g-1)/math.log2(i+2) for i,g in enumerate(sorted([labels[c["chunk_id"]] for c in candidates], reverse=True)[:n]))
            if ideal and all(c["chunk_id"] in labels for c in selected):
                actual = sum((2**labels[c["chunk_id"]]-1)/math.log2(i+2) for i,c in enumerate(selected))
                met["ndcg"] = actual/ideal
        annotation = human.get((q["query_id"], r["condition_id"]))
        met.update(answer_metrics(r, annotation))
        if q["query_id"] not in human_ids:
            for key in ("grounded_correct","accuracy","claim_support","unsupported_claims","contradicted_claims","citation_support","claim_citation_coverage"):
                met[key] = None
        if not manifest["protocol"]["config"]["generate"]:
            for key in ("grounded_correct", "accuracy", "claim_support", "unsupported_claims", "contradicted_claims",
                        "citation_support", "claim_citation_coverage", "appropriate_abstention", "over_abstention"):
                met[key] = None
        met.update({"task_success": float(r["status"] == "ok"), "online_cost_usd": r.get("cost", {}).get("online_usd"),
                    "online_ms": r.get("timing", {}).get("online_ms"), "context_tokens": r.get("context_tokens")})
        metrics.append({"query_id": q["query_id"], "group_id": q["group_id"], "split": q["split"], "task_type": q["task_type"],
            "answerable": q["answerable"], "method": r["method"], "condition_id": r["condition_id"],
            "status": r["status"], "human_evaluated": annotation is not None, "metrics": met})
        metrics[-1]["human_evaluation_planned"] = q["query_id"] in human_ids
    write_jsonl(directory / "metrics.jsonl", metrics)
    summary = []
    for cond in manifest["conditions"]:
        subset = [r for r in metrics if r["condition_id"] == cond["condition_id"]]
        record = {**cond, "queries": len(subset), "human_evaluated": sum(r["human_evaluated"] for r in subset),
            "research_valid": manifest["research_valid"]}
        for key in metrics[0]["metrics"]:
            values = [r["metrics"][key] for r in subset if r["metrics"][key] is not None]
            record[key] = float(np.mean(values)) if values else None
            record[key + "_n"] = len(values)
        expected = sum(r["answerable"] and r["human_evaluation_planned"] for r in subset)
        record["human_answerable_planned"] = expected
        for metric in ("grounded_correct","accuracy"):
            complete = expected > 0 and record[metric+"_n"] == expected
            record[metric+"_complete"] = complete
            if not complete:
                record[metric] = None
        summary.append(record)
    write_json(directory / "summary.json", summary)
    with (directory / "summary.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    return directory / "summary.json"


def paired_statistics(run_dir: str, repeats: int, seed: int, delta: float) -> Path:
    directory = Path(run_dir)
    rows = read_jsonl(directory / "metrics.jsonl")
    ready = {s["condition_id"] for s in read_json(directory/"summary.json") if s.get("grounded_correct_complete")}
    comparisons = [("ce_r", "jev_r", "esr"), ("ce_r", "jev_r", "grounded_correct"),
                   ("ce_fr", "jev_fr", "online_cost_usd")]
    report = []
    rng = np.random.default_rng(seed)
    for baseline, treatment, metric in comparisons:
        for complete_case in (False, True):
            if metric == "grounded_correct" and (baseline not in ready or treatment not in ready):
                report.append({"baseline":baseline,"treatment":treatment,"metric":metric,"complete_case":complete_case,
                               "n":0,"status":"human_annotations_incomplete"})
                continue
            lookup = {(r["query_id"], r["condition_id"]): r for r in rows}
            conditions = {r["condition_id"] for r in rows}
            pairs = []
            for (qid,cond), a in lookup.items():
                if cond != baseline or (qid,treatment) not in lookup:
                    continue
                b = lookup[(qid,treatment)]
                if complete_case and any(lookup[(qid,c)]["status"] != "ok" for c in conditions):
                    continue
                va,vb = a["metrics"].get(metric),b["metrics"].get(metric)
                if va is not None and vb is not None:
                    pairs.append((a["group_id"], vb-va))
            if not pairs:
                report.append({"baseline": baseline, "treatment": treatment, "metric": metric,
                    "complete_case": complete_case, "n": 0, "status": "unavailable"})
                continue
            groups = sorted({g for g,_ in pairs})
            arrays = [np.array([d for g,d in pairs if g == group]) for group in groups]
            observed = float(np.mean([d for _,d in pairs]))
            if len(groups) < 2:
                report.append({"baseline": baseline, "treatment": treatment, "metric": metric,
                    "complete_case": complete_case, "n": len(pairs), "groups": len(groups), "mean_difference": observed,
                    "status": "insufficient_independent_groups"})
                continue
            boot, null = [], []
            for _ in range(repeats):
                indices = rng.integers(0, len(groups), len(groups))
                boot.append(float(np.concatenate([arrays[i] for i in indices]).mean()))
                signs = rng.choice([-1,1], len(groups))
                null.append(float(np.concatenate([a*s for a,s in zip(arrays,signs)]).mean()))
            low, high = np.quantile(boot, [0.025,0.975]).tolist()
            p = (1 + sum(abs(x) >= abs(observed) for x in null))/(repeats+1)
            report.append({"baseline": baseline, "treatment": treatment, "metric": metric, "complete_case": complete_case,
                "n": len(pairs), "groups": len(groups), "mean_difference": observed, "ci95": [low,high],
                "p_cluster_sign_flip": p, "p_holm": None, "seed": seed, "repetitions": repeats})
    for complete in (False,True):
        tests = sorted([r for r in report if r.get("p_cluster_sign_flip") is not None and r["complete_case"] == complete], key=lambda r:r["p_cluster_sign_flip"])
        maximum = 0.0
        for i,r in enumerate(tests):
            maximum = max(maximum, min(1, (len(tests)-i)*r["p_cluster_sign_flip"]))
            r["p_holm"] = maximum
    noninferiority = []
    lookup = {(r["query_id"], r["condition_id"]): r for r in rows}
    for treatment in ("ce_fr", "jev_fr"):
        for metric in ("esr", "grounded_correct"):
            if metric == "grounded_correct" and ("ce_r" not in ready or treatment not in ready):
                noninferiority.append({"baseline":"ce_r","treatment":treatment,"metric":metric,"supported":None,
                                      "status":"human_annotations_incomplete"})
                continue
            pairs = []
            for (qid,cond), baseline in lookup.items():
                if cond != "ce_r" or (qid,treatment) not in lookup:
                    continue
                a,b = baseline["metrics"].get(metric),lookup[(qid,treatment)]["metrics"].get(metric)
                if a is not None and b is not None:
                    pairs.append((baseline["group_id"],b-a))
            groups = sorted({g for g,_ in pairs})
            record = {"baseline":"ce_r","treatment":treatment,"metric":metric,"delta":delta,
                      "n":len(pairs),"groups":len(groups),"supported":None}
            if len(groups) >= 2:
                arrays = [np.array([d for g,d in pairs if g == group]) for group in groups]
                boot = [float(np.concatenate([arrays[i] for i in rng.integers(0,len(groups),len(groups))]).mean()) for _ in range(repeats)]
                record["one_sided_lower95"] = float(np.quantile(boot,.05))
                record["mean_difference"] = float(np.mean([d for _,d in pairs]))
                record["supported"] = record["one_sided_lower95"] > -delta
            noninferiority.append(record)
    write_json(directory / "statistics.json", {"comparisons": report, "noninferiority": noninferiority,
        "noninferiority_margin": delta, "note": "Quality equivalence is not inferred from a nonsignificant p-value."})
    intervals = []
    for condition in sorted({r["condition_id"] for r in rows}):
        for metric in ("esr","grounded_correct","context_tokens","online_cost_usd"):
            if metric == "grounded_correct" and condition not in ready:
                continue
            values = [(r["group_id"],r["metrics"].get(metric)) for r in rows if r["condition_id"] == condition and r["metrics"].get(metric) is not None]
            groups = sorted({g for g,_ in values})
            if len(groups) < 2:
                continue
            arrays = [np.array([v for g,v in values if g == group]) for group in groups]
            boot = [float(np.concatenate([arrays[i] for i in rng.integers(0,len(groups),len(groups))]).mean()) for _ in range(repeats)]
            intervals.append({"condition_id":condition,"metric":metric,"n":len(values),"groups":len(groups),
                "mean":float(np.mean([v for _,v in values])),"ci95":np.quantile(boot,[.025,.975]).tolist()})
    write_json(directory / "confidence_intervals.json", intervals)
    return directory / "statistics.json"


def summarize_benchmark(run_dir: str) -> Path:
    directory = Path(run_dir)
    rows = read_jsonl(directory / "raw.jsonl")
    summary = []
    for method in sorted({r["method"] for r in rows}):
        subset = [r for r in rows if r["method"] == method]
        values = [r["timing"]["wall_clock_ms"] for r in subset if r["status"] == "ok"]
        summary.append({"method": method, "attempts": len(subset), "failures": sum(r["status"] != "ok" for r in subset),
            "mean_ms": float(np.mean(values)) if values else None, "median_ms": float(np.median(values)) if values else None,
            "p95_ms": float(np.quantile(values, .95)) if values else None})
    write_json(directory / "latency_summary.json", summary)
    return directory / "latency_summary.json"

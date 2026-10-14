from __future__ import annotations

import csv
import random
from pathlib import Path

import numpy as np
import yaml

from .config import Config, pricing, provider_identity
from .io import file_hash, implementation_digest, read_json, read_jsonl, write_json, write_jsonl
from .pipeline import run


async def sweep(cfg: Config, grid_size: int) -> Path:
    if grid_size < 2:
        raise ValueError("grid_size must be at least 2")
    score_cfg = cfg.model_copy(update={"methods": ["ce_r", "jev_r"], "generate": False})
    scored = await run(score_cfg, "dev")
    rows = read_jsonl(scored / "raw.jsonl")
    conditions = [{"method": "ce_r", "condition_id": "ce_r", "threshold": None},
                  {"method": "jev_r", "condition_id": "jev_r", "threshold": None}]
    for kind in ("ce", "jev"):
        scores = [c["rerank_score"] for r in rows if r["method"] == kind + "_r" and r["status"] == "ok" for c in r["ranking"]]
        if not scores:
            raise ValueError(f"No successful development {kind} scores")
        values = np.quantile(scores, np.linspace(0,1,grid_size)).tolist()
        values[-1] = float(np.nextafter(max(scores), np.inf)) # include all-abstain endpoint
        for i,t in enumerate(values):
            conditions.append({"method": kind + "_fr", "condition_id": f"{kind}_fr_grid{i}", "threshold": t})
    out = await run(cfg, "dev", conditions=conditions)
    write_json(out / "sweep.json", {"grid_size": grid_size, "score_run": str(scored), "conditions": conditions})
    return out


def tune(run_dir: str, cfg: Config, output_config: str, *, allow_infeasible: bool = False) -> Path:
    directory = Path(run_dir)
    manifest = read_json(directory / "manifest.json")
    if manifest["split"] != "dev" or not manifest["protocol"]["config"]["generate"]:
        raise ValueError("Threshold selection needs generated, human-evaluated development runs")
    if not (directory / "sweep.json").is_file():
        raise ValueError("Threshold selection requires a sweep run")
    summary = read_json(directory / "summary.json")
    raw = read_jsonl(directory / "metrics.jsonl")
    baseline = next(r for r in summary if r["condition_id"] == "ce_r")
    answered = sum(r["answerable"] and r.get("human_evaluation_planned",True) for r in raw if r["condition_id"] == "ce_r")
    if not answered:
        raise ValueError("No answerable development queries")
    # Validate the supplied base config against the actual run, rather than attaching thresholds to another experiment.
    run_cfg = manifest["protocol"]["config"]
    if file_hash(cfg.queries) != manifest["protocol"]["queries_sha256"]:
        raise ValueError("Query data changed since sweep")
    attached = {path: file_hash(path) for path in cfg.protocol_documents}
    if attached != manifest["protocol"].get("protocol_documents_sha256", {}):
        raise ValueError("Protocol documents changed since sweep")
    for kind,identity in manifest["protocol"]["providers"].items():
        if provider_identity(kind,getattr(cfg,kind+"_backend")) != identity:
            raise ValueError(f"Provider environment changed since sweep: {kind}")
    if pricing() != manifest["protocol"]["pricing"] or implementation_digest() != manifest["protocol"]["implementation_digest"]:
        raise ValueError("Pricing or implementation changed since sweep")
    current = cfg.model_dump(exclude={"output_dir", "cache_dir"})
    for key in current:
        if key not in ("ce_threshold", "jev_threshold") and current[key] != run_cfg[key]:
            raise ValueError(f"Base config does not match sweep: {key}")
    for s in summary:
        if not s.get("grounded_correct_complete") or s["grounded_correct_n"] != answered or s["online_cost_usd_n"] != s["queries"]:
            raise ValueError("Complete human answer judgments and complete costs are required for tuning")
    selected = {}
    for method in ("ce_fr", "jev_fr"):
        feasible = [s for s in summary if s["method"] == method and
            s["esr"] >= baseline["esr"] - cfg.quality_margins["esr"] and
            s["grounded_correct"] >= baseline["grounded_correct"] - cfg.quality_margins["grounded_correct"]]
        if feasible:
            selected[method] = min(feasible, key=lambda s:(s["online_cost_usd"], -s["esr"], s["threshold"]))
        else:
            selected[method] = None
    infeasible = [method for method, value in selected.items() if value is None]
    methods = [m for m in cfg.methods if m not in infeasible]
    write_json(directory / "threshold_selection.json", {"baseline": "ce_r", "delta": cfg.quality_delta,
        "quality_margins": cfg.quality_margins, "selected": selected, "infeasible_methods": infeasible,
        "continuation": "omit_infeasible_fr" if allow_infeasible else "require_all_fr", "final_methods": methods})
    if infeasible and not allow_infeasible:
        raise ValueError("No feasible threshold for one or more methods; see threshold_selection.json. Constraints were not relaxed")
    locked_cfg = cfg.model_copy(update={"methods": methods,
        "ce_threshold": selected["ce_fr"]["threshold"] if selected["ce_fr"] else None,
        "jev_threshold": selected["jev_fr"]["threshold"] if selected["jev_fr"] else None})
    p = Path(output_config)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        raise ValueError("Output config already exists; choose a new path")
    p.write_text(yaml.safe_dump(locked_cfg.model_dump(), allow_unicode=True, sort_keys=False), encoding="utf-8")
    return p


def error_sample(run_dir: str, output: str, limit: int, seed: int) -> Path:
    rows = read_jsonl(Path(run_dir) / "raw.jsonl")
    errors = []
    for row in rows:
        q = row["query"]
        labels = q.get("relevance", {})
        if row["status"] != "ok":
            errors.append({"category": "technical_failure", "query_id": q["query_id"], "condition_id": row["condition_id"], "error": row.get("error")})
        chosen = {c["chunk_id"] for c in row.get("selected", [])}
        for c in row.get("ranking", []):
            cid = c["chunk_id"]
            if labels.get(cid) == 0 and cid in chosen or labels.get(cid) == 2 and cid not in chosen:
                errors.append({"category": "false_positive" if cid in chosen else "missed_direct_evidence",
                    "query_id": q["query_id"], "condition_id": row["condition_id"], "question": q["question"],
                    "candidate": c, "human_error_type": None, "notes": ""})
    by_category = {}
    for e in errors:
        by_category.setdefault(e["category"], []).append(e)
    rng = random.Random(seed)
    for group in by_category.values():
        rng.shuffle(group)
    result = []
    while any(by_category.values()) and len(result) < limit:
        for key in sorted(by_category):
            if by_category[key] and len(result) < limit:
                result.append(by_category[key].pop())
    write_jsonl(output, result)
    return Path(output)


def calibration(run_dir: str, bins: int = 10) -> Path:
    if bins < 2:
        raise ValueError("At least two calibration bins are required")
    manifest = read_json(Path(run_dir)/"manifest.json")
    if manifest["protocol"]["config"]["jev_instruction"] != "applicability":
        raise ValueError("Applicability calibration cannot use probabilities from the relevance ablation")
    rows = read_jsonl(Path(run_dir) / "raw.jsonl")
    pairs, seen = [], set()
    for r in rows:
        if r["method"] != "jev_r" or r["status"] != "ok" or r["rerank_trace"].get("score_type") != "noul_probability":
            continue
        for c in r["ranking"]:
            key = (r["query"]["query_id"], c["chunk_id"])
            grade = r["query"]["relevance"].get(c["chunk_id"])
            if key not in seen and grade is not None:
                seen.add(key)
                pairs.append((c["rerank_score"], int(grade == 2)))
    if not pairs:
        raise ValueError("Calibration needs genuine Jev noul probabilities and human candidate labels")
    p,y = np.array(pairs).T
    report = []
    for i in range(bins):
        mask = (p >= i/bins) & ((p <= 1) if i == bins-1 else (p < (i+1)/bins))
        report.append({"lower": i/bins, "upper": (i+1)/bins, "n": int(mask.sum()),
            "confidence": float(p[mask].mean()) if mask.any() else None,
            "observed": float(y[mask].mean()) if mask.any() else None})
    ece = sum(b["n"]/len(p)*abs(b["confidence"]-b["observed"]) for b in report if b["n"])
    output = Path(run_dir) / "calibration.json"
    write_json(output, {"n": len(p), "brier": float(np.mean((p-y)**2)), "ece": ece, "bins": report})
    return output


def agreement(first: str, second: str, output: str) -> Path:
    first_rows,second_rows = read_jsonl(first),read_jsonl(second)
    a = {r["annotation_id"]:r for r in first_rows}
    b = {r["annotation_id"]:r for r in second_rows}
    if len(a) != len(first_rows) or len(b) != len(second_rows):
        raise ValueError("Duplicate reviewer annotation IDs")
    common = sorted(set(a)&set(b))
    if not common:
        raise ValueError("No common annotation IDs")
    relevance = "grade" in a[common[0]]
    fields = ["grade"] if relevance else ["correctness","core_supported","claim_support","citation_support"]
    if not relevance and a[common[0]].get("annotation_schema_version") == 2:
        fields += ["claims_complete", "is_core"]
    for k in common:
        immutable = ("question", "as_of_date", "jurisdiction", "candidate") if relevance else (
            "question", "as_of_date", "jurisdiction", "reference_answer", "answer", "evidence", "annotation_schema_version")
        if any(a[k].get(f) != b[k].get(f) for f in immutable):
            raise ValueError("Reviewers must judge the same unmodified task inputs")
    reports = {}
    for field in fields:
        pairs = []
        for k in common:
            if field in ("claim_support", "citation_support", "is_core"):
                x,y = a[k].get("claim_labels",[]),b[k].get("claim_labels",[])
                if len(x) != len(y):
                    raise ValueError("Reviewer claim counts differ")
                for u,v in zip(x,y):
                    if field == "citation_support":
                        left, right = u.get("citations", []), v.get("citations", [])
                        if sorted(c.get("evidence_id") for c in left) != sorted(c.get("evidence_id") for c in right):
                            raise ValueError("Reviewer citation IDs/counts differ")
                        # Match by ID and occurrence, rather than relying on a reviewer's array ordering.
                        left = sorted(left, key=lambda c:c["evidence_id"])
                        right = sorted(right, key=lambda c:c["evidence_id"])
                        pairs.extend((c.get("supported"), d.get("supported")) for c,d in zip(left,right))
                    else:
                        key = "support" if field == "claim_support" else "is_core"
                        pairs.append((u.get(key), v.get(key)))
            else:
                pairs.append((a[k].get(field),b[k].get(field)))
        if any(x is None or y is None for x,y in pairs):
            raise ValueError("Both reviewers must complete labels")
        if field == "grade" and any(type(v) is not int or v not in (0,1,2) for pair in pairs for v in pair):
            raise ValueError("Relevance grades must be integers 0/1/2")
        if field == "claim_support" and any(v not in ("supported","unsupported","contradicted") for pair in pairs for v in pair):
            raise ValueError("Invalid claim support label")
        if field not in ("grade", "claim_support") and any(type(v) is not bool for pair in pairs for v in pair):
            raise ValueError("Answer and citation judgments must be booleans")
        if not pairs:
            reports[field] = {"n":0,"agreement":None,"cohen_kappa":None}
            continue
        labels = set(x for pair in pairs for x in pair)
        po = sum(x == y for x,y in pairs)/len(pairs)
        pe = sum(sum(x == v for x,_ in pairs)/len(pairs)*sum(y == v for _,y in pairs)/len(pairs) for v in labels)
        reports[field] = {"n":len(pairs),"agreement":po,"cohen_kappa":(po-pe)/(1-pe) if pe != 1 else None}
        if field == "grade":
            for power, name in ((1, "linear_weighted_kappa"), (2, "quadratic_weighted_kappa")):
                observed = sum((abs(x-y)/2)**power for x,y in pairs)/len(pairs)
                expected = sum((abs(x-y)/2)**power * sum(u == x for u,_ in pairs)/len(pairs) *
                               sum(v == y for _,v in pairs)/len(pairs) for x in (0,1,2) for y in (0,1,2))
                reports[field][name] = 1-observed/expected if expected else None
    compare_fields = ["grade"] if relevance else ["correctness","core_supported","claim_labels","claims_complete","omitted_claims"]
    write_json(output, {"n": len(common), "first_only": sorted(set(a)-set(b)), "second_only": sorted(set(b)-set(a)), "fields": reports,
        "conflicts": [{"annotation_id": k, "first": a[k], "second": b[k]} for k in common if any(a[k].get(f) != b[k].get(f) for f in compare_fields)],
        "note": "Conflicts require adjudication; no automatic majority label is created."})
    return Path(output)


def plot_results(run_dir: str) -> Path:
    import os
    os.environ.setdefault("MPLCONFIGDIR",str((Path(run_dir)/"matplotlib_cache").absolute()))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise ValueError("Install matplotlib to generate paper figures") from e
    directory = Path(run_dir)
    summary = read_json(directory / "summary.json")
    if not (directory / "confidence_intervals.json").is_file():
        raise ValueError("Run statistics before plot so uncertainty is available")
    intervals = {(x["condition_id"],x["metric"]):x["ci95"] for x in read_json(directory / "confidence_intervals.json")}
    figures = directory / "figures"
    figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 10, "figure.dpi": 160})
    for metric in ("esr", "grounded_correct", "context_tokens", "online_cost_usd"):
        items = [s for s in summary if s[metric] is not None]
        if not items:
            continue
        fig,ax = plt.subplots(figsize=(7,4))
        ax.bar([s["condition_id"] for s in items], [s[metric] for s in items])
        for i,s in enumerate(items):
            ci = intervals.get((s["condition_id"],metric))
            if ci:
                ax.errorbar(i,s[metric],yerr=[[max(0,s[metric]-ci[0])],[max(0,ci[1]-s[metric])]],fmt="none",color="black",capsize=3)
        ax.set_ylabel(metric)
        ax.tick_params(axis="x", rotation=30)
        fig.tight_layout()
        fig.savefig(figures / f"{metric}.png")
        fig.savefig(figures / f"{metric}.pdf")
        plt.close(fig)
    fig,ax = plt.subplots(figsize=(6,4))
    for s in summary:
        if s["online_cost_usd"] is not None and s["esr"] is not None:
            xci,yci = intervals.get((s["condition_id"],"online_cost_usd")),intervals.get((s["condition_id"],"esr"))
            xerr = [[max(0,s["online_cost_usd"]-xci[0])],[max(0,xci[1]-s["online_cost_usd"])]] if xci else None
            yerr = [[max(0,s["esr"]-yci[0])],[max(0,yci[1]-s["esr"])]] if yci else None
            ax.errorbar(s["online_cost_usd"],s["esr"],xerr=xerr,yerr=yerr,fmt="o",capsize=3)
            ax.annotate(s["condition_id"], (s["online_cost_usd"],s["esr"]))
    ax.set(xlabel="Online cost per query (USD)", ylabel="Evidence-set success")
    fig.tight_layout()
    fig.savefig(figures / "quality_cost.pdf")
    plt.close(fig)
    return figures

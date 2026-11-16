"""Offline A1--A6 preparation. Reads frozen artifacts; writes only a new prep tree.

No model invocation, new inference, legal adjudication, or manuscript generation.
Run from repository root. Refuses to overwrite completed preparation outputs.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import runpy
import socket
import statistics
import sys

import numpy as np
import tiktoken

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from legal_rag_jev.io import digest, file_hash, read_json, read_jsonl
from legal_rag_jev.koblex import provision_metrics, token_f1

ROOT = Path("results/koblex-reproduction-v1")
OUT = ROOT / "chapter4-prep-v1"
GOLD = Path("data/koblex/prepared-v1/gold.jsonl")
QA = Path("data/koblex/upstream/experiments/source/koblex.jsonl")
CORPUS = Path("data/koblex/downloads/statute.jsonl")
PROMPT = Path("data/koblex/upstream/experiments/parser/prompts/question_answering.py")
ARMS = ("parser_ce_raw", "parser_ce_fixed", "parser_jev_fixed")
CE, JEV = ARMS[1:]
EPS = 1e-12
METRICS = ("precision", "recall", "f1", "em", "gold_set_coverage", "token_f1", "lf_eval")
STAGES = ("corpus_absent", "bm25_absent", "shortlist_absent", "shortlist_present_unselected", "selected")


def no_network(*args, **kwargs):
    raise RuntimeError("This preparation is offline; network access is disabled")


socket.socket.connect = no_network
socket.create_connection = no_network


def write_json(name, obj):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_rows(name, rows):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
    if rows:
        with p.with_suffix(".csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            for row in rows:
                writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})


SOURCES = {}


def source(path):
    path = Path(path)
    key = str(path)
    if key not in SOURCES:
        SOURCES[key] = {"sha256": file_hash(path), "bytes": path.stat().st_size}
    return key


def load(path, lines=False):
    source(path)
    return read_jsonl(path) if lines else read_json(path)


def ref(path, line=None, pointer=None):
    result = {"path": source(path), "sha256": SOURCES[str(path)]["sha256"]}
    if line is not None:
        result["line_1based"] = line
    if pointer is not None:
        result["json_pointer"] = pointer
    return result


def close(a, b):
    assert abs(a - b) <= EPS, (a, b)


def sign(x):
    return "Jev_higher" if x > EPS else "CE_higher" if x < -EPS else "tie"


def stats(values):
    a = np.asarray(values, dtype=float)
    assert len(a) and np.isfinite(a).all()
    q1, median, q3 = np.quantile(a, [.25, .5, .75], method="linear")
    return {"n": len(a), "sum": float(a.sum()), "mean": float(a.mean()), "median": float(median),
            "q1": float(q1), "q3": float(q3), "iqr": float(q3 - q1), "min": float(a.min()), "max": float(a.max())}


def max_gold_matching(pool_sets, gold_set):
    """Maximum distinct gold achievable with one choice per pool (diagnostic only)."""
    assigned = {}

    def visit(g, seen):
        for p, passages in enumerate(pool_sets):
            if g in passages and p not in seen:
                seen.add(p)
                if p not in assigned or visit(assigned[p], seen):
                    assigned[p] = g
                    return True
        return False

    for g in sorted(gold_set):
        visit(g, set())
    return len(assigned)


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(OUT))
    args = parser.parse_args()
    OUT = Path(args.output)
    # A new directory may contain only preflight verification/preservation files.
    if (OUT / "analysis-spec.json").exists():
        raise ValueError("Prep already started/completed; choose a new output for a new analysis")
    OUT.mkdir(parents=True, exist_ok=True)
    spec = {
        "status": "POST_RESULT_EXPLORATORY_DESCRIPTIVE_PREPARATION", "order": ["A1", "A2", "A3", "A4", "A5", "A6"],
        "scientific_inputs": "existing files only", "paid_calls": 0, "human_judgments_created": 0,
        "primary_comparison": [JEV, CE], "reference_arm": ARMS[0],
        "metric_scale": "retain 0..1 raw values; display x100; difference from unrounded raw values",
        "estimand": "unweighted question mean; question denominator 226; retain all unavailable-gold questions",
        "new_inference": "none; copy existing exploratory percentile CI; no new subgroup CI, tests, or interaction claims",
        "A3": {"tie_absolute_tolerance": EPS, "differences": "Jev minus fixed CE", "discordance": "strict opposite signs of F1 and LF or Token F1; directional mismatch with ties also retained"},
        "A4": {"canonical": "literal hierarchy + content; no whitespace/Unicode/date normalization",
               "gold_unit": "unique canonical gold within each question; query-gold occurrence denominator; not unique corpus-wide gold",
               "row_ids": "zero-based original corpus rows; JSONL lines are row_id + 1", "duplicates": "original rows preserved; evaluation sets deduplicated by exact canonical string",
               "scope": "fixed CE and Jev; raw index-error reference is excluded from pool-correct stage attribution",
               "exclusive_first_loss": list(STAGES), "pool_constraint": "one final selection per generated-provision pool; exact bipartite maximum matching is a structural bound, never a new prediction"},
        "A5": {"tokenizer": "tiktoken o200k_base; encode(disallowed_special=())", "context": "newline join of actual provision list, including duplicates",
               "prompt": "exact upstream SYSTEM_PROMPT + two newlines + INSTRUCTION_PROMPT substitution; user message only; verify original API cache digest",
               "input": "stored generation_trace.usage.input_tokens is full API input; tokenizer text count separately excludes chat framing",
               "output": "stored successful API response output_tokens, including original response framing; answer text token count separately",
               "cache": "execution cached flag differs from provider cached_input_tokens; cached usage describes demand, not new billing",
               "statistics": "mean, median, Q1/Q3/IQR; numpy quantile method=linear; paired Jev-minus-CE differences",
               "cost": "no online cost/latency superiority estimate; uncached successful generation usage is not whole-experiment billing"},
        "A6": {"labels": "multi-label question observations; counts may exceed 226; no legal error or support verdict",
               "low_auto_answer_threshold": {"lf_eval": "<0.5", "token_f1": "<0.5", "interpretation": "arbitrary descriptive screening threshold, not validated correctness boundary"},
               "buckets": {"Jev_improvement": "F1 delta > tolerance", "CE_advantage": "F1 delta < -tolerance", "common_low_F1": "both F1 < 0.5", "metric_discordance": "strict opposite F1 vs LF/Token F1 signs"},
               "selection": "nearest to within-bucket median of primary key; ties lexicographic query_id; win/loss/discordance key=abs(F1 delta); common-low key=mean F1; repeat within hop x mapping strata for alternatives",
               "main_candidates": "one improvement, one CE advantage, one discordance (fallback common-low); candidates only; pending legal review",
               "human_sample": "existing 60-question sample is preserved and never replaced"},
        "script": ref(Path(__file__).relative_to(Path.cwd()) if Path(__file__).is_absolute() else Path(__file__)),
    }
    write_json("analysis-spec.json", spec)
    qa = load(QA, True)
    gold = load(GOLD, True)
    ids = [g["query_id"] for g in gold]
    assert ids == [q["id"] for q in qa] and len(ids) == len(set(ids)) == 226
    gold_by = {g["query_id"]: g for g in gold}
    qa_by = {q["id"]: q for q in qa}
    index = {qid: i for i, qid in enumerate(ids)}
    analysis = load(ROOT / "analysis.json")
    audit = load("research/koblex_source_audit_20261108.json")
    groups = audit["source_and_gold_groups"]["groups"]
    sample = set(audit["human_review_sample"]["ids"])
    assert len(sample) == 60 and len(set(groups.values())) == 151
    metrics, lf, pred = {}, {}, {}
    raw = []
    for arm in ARMS:
        metrics[arm] = load(ROOT / "metrics" / arm / "metrics.jsonl", True)
        lf[arm] = load(ROOT / "lf-eval" / arm / "metrics.jsonl", True)
        pred[arm] = load(ROOT / "predictions" / f"{arm}.jsonl", True)
        for records in (metrics[arm], lf[arm], pred[arm]):
            assert [r["query_id"] for r in records] == ids
        for i, qid in enumerate(ids):
            m, l, p, g = metrics[arm][i], lf[arm][i], pred[arm][i], gold[i]
            # Independent recomputation of the deterministic metrics.
            expected = provision_metrics(p["provisions"], g["provisions"])
            for k, v in expected.items():
                close(v, m["retrieval"][k])
            clipped = p["answer"].split("<\think>")[0][:800]
            close(token_f1(clipped, g["answer"])["f1"], m["token_f1"])
            assert m["n_hops"] == g["n_hops"] and m["has_unavailable_gold"] == bool(g["unavailable_unit_ids"])
            vals = {**m["retrieval"], "token_f1": m["token_f1"], "lf_eval": l["score"]}
            raw.append({"query_id": qid, "arm": arm, "n_hops": g["n_hops"], "mapping": "affected" if g["unavailable_unit_ids"] else "fully_mapped",
                        "group_id": groups[qid], **vals, "metric_source": ref(ROOT / "metrics" / arm / "metrics.jsonl", i + 1), "lf_source": ref(ROOT / "lf-eval" / arm / "metrics.jsonl", i + 1)})
    by = {(r["arm"], r["query_id"]): r for r in raw}

    # A1: one source-linked numeric ledger, including existing CIs, not re-estimates.
    ledger = []
    for arm in ARMS:
        for metric in METRICS:
            values = [by[arm, q][metric] for q in ids]
            total = sum(values)
            pointer = f"/summaries/{arm}/" + (f"retrieval/{metric}" if metric in metrics[arm][0]["retrieval"] else metric)
            stored = analysis["summaries"][arm]
            close(total / 226, stored["retrieval"][metric] if metric in stored["retrieval"] else stored[metric])
            ledger.append({"kind": "question_mean", "arm": arm, "metric": metric, "numerator": total, "denominator": 226, "denominator_unit": "questions",
                           "raw_value": total / 226, "display_x100": total / 226 * 100, "display_unit": "%" if metric in ("em", "gold_set_coverage") else "points on 0..100 scale",
                           "source": ref(ROOT / "analysis.json", pointer=pointer), "raw_rows": "A1/question-metrics.jsonl"})
    for j, comparison in enumerate(analysis["comparisons"]):
        assert not comparison["confirmatory"]
        metric, treatment, control = comparison["metric"], comparison["treatment"], comparison["control"]
        deltas = [by[treatment, q][metric] - by[control, q][metric] for q in ids]
        close(sum(deltas) / 226, comparison["mean_difference"])
        ledger.append({"kind": "paired_difference_existing_ci", "arm": f"{treatment} minus {control}", "metric": metric,
                       "numerator": sum(deltas), "denominator": 226, "denominator_unit": "paired questions (151 dependence groups)",
                       "raw_value": comparison["mean_difference"], "display_x100": comparison["mean_difference"] * 100,
                       "display_unit": "percentage points" if metric in ("em", "gold_set_coverage") else "points on 0..100 scale",
                       "ci95_raw": comparison["ci95"], "ci95_x100": [v * 100 for v in comparison["ci95"]],
                       "existing_inference": comparison, "source": ref(ROOT / "analysis.json", pointer=f"/comparisons/{j}"), "raw_rows": "A1/question-metrics.jsonl"})
    write_rows("A1/question-metrics.jsonl", raw)
    # Mixed ledger row schemas are retained in JSON; a rectangular table is also supplied.
    write_json("A1/numeric-ledger.json", ledger)
    fields = sorted(set().union(*(r.keys() for r in ledger)))
    write_rows("A1/numeric-ledger.jsonl", [{k: r.get(k) for k in fields} for r in ledger])
    print("A1 complete", flush=True)

    # A2: marginal and cross-stratified descriptive values; no new inference.
    subsets = {"all": ids}
    for h in (1, 2, 3):
        subsets[f"hop_{h}"] = [q for q in ids if gold_by[q]["n_hops"] == h]
    for affected in (False, True):
        label = "affected" if affected else "fully_mapped"
        subsets[label] = [q for q in ids if bool(gold_by[q]["unavailable_unit_ids"]) == affected]
        for h in (1, 2, 3):
            subsets[f"hop_{h}_{label}"] = [q for q in subsets[label] if gold_by[q]["n_hops"] == h]
    assert [len(subsets[f"hop_{h}"]) for h in (1, 2, 3)] == [57, 127, 42]
    assert [len(subsets[s]) for s in ("fully_mapped", "affected")] == [197, 29]
    subgroup = []
    for label, members in subsets.items():
        if not members:
            continue
        for metric in METRICS:
            means = {}
            for arm in ARMS:
                total = sum(by[arm, q][metric] for q in members)
                means[arm] = total / len(members)
                subgroup.append({"subgroup": label, "metric": metric, "arm": arm, "n": len(members), "numerator": total,
                                 "raw_mean": means[arm], "display_x100": means[arm] * 100, "descriptive_only": True,
                                 "source": "A1/question-metrics.jsonl; membership in A2/subgroup-membership.json"})
            subgroup.append({"subgroup": label, "metric": metric, "arm": "Jev minus CE", "n": len(members),
                             "numerator": sum(by[JEV, q][metric] - by[CE, q][metric] for q in members),
                             "raw_mean": means[JEV] - means[CE], "display_x100": (means[JEV] - means[CE]) * 100,
                             "descriptive_only": True, "source": "A1/question-metrics.jsonl; membership in A2/subgroup-membership.json"})
    write_rows("A2/subgroup-metrics.jsonl", subgroup)
    write_json("A2/subgroup-membership.json", subsets)
    write_rows("A2/hop-f1-figure-data.jsonl", [r for r in subgroup if r["subgroup"] in ("hop_1", "hop_2", "hop_3") and r["metric"] == "f1" and r["arm"] in (CE, JEV)])
    print("A2 complete", flush=True)

    # A3: all paired outcomes, including ties and both directions.
    paired = []
    for qid in ids:
        delta = {k: by[JEV, qid][k] - by[CE, qid][k] for k in METRICS}
        signs = {k: sign(v) for k, v in delta.items()}
        strict = {k: (delta["f1"] > EPS and delta[k] < -EPS) or (delta["f1"] < -EPS and delta[k] > EPS) for k in ("token_f1", "lf_eval")}
        paired.append({"query_id": qid, "n_hops": gold_by[qid]["n_hops"], "mapping": by[CE, qid]["mapping"], "delta": delta,
                       "direction": signs, "strict_discordance": strict, "directional_mismatch_including_ties": {k: signs["f1"] != signs[k] for k in strict},
                       "ce": {k: by[CE, qid][k] for k in METRICS}, "jev": {k: by[JEV, qid][k] for k in METRICS}, "source_row_1based": index[qid] + 1})
    pby = {r["query_id"]: r for r in paired}
    wins = {k: dict(Counter(r["direction"][k] for r in paired)) for k in METRICS}
    joint = []
    for metric in ("lf_eval", "token_f1"):
        for s1 in ("CE_higher", "tie", "Jev_higher"):
            for s2 in ("CE_higher", "tie", "Jev_higher"):
                members = [r["query_id"] for r in paired if r["direction"]["f1"] == s1 and r["direction"][metric] == s2]
                joint.append({"answer_metric": metric, "f1_direction": s1, "answer_direction": s2, "n": len(members), "denominator": 226, "query_ids": members})
        assert sum(r["n"] for r in joint if r["answer_metric"] == metric) == 226
    write_rows("A3/paired-outcomes.jsonl", paired)
    write_json("A3/win-tie-loss.json", {"tolerance": EPS, "denominator": 226, "counts": wins, "not_independent_success_trials": True})
    write_rows("A3/joint-directions.jsonl", joint)
    write_rows("A3/discordant-queries.jsonl", [r for r in paired if any(r["strict_discordance"].values())])
    print("A3 complete", flush=True)

    # A4: original row duplicates, exact canonical sets, and per-pool constraints.
    corpus = load(CORPUS, True)
    texts = [r["hierarchy"] + r["content"] for r in corpus]
    corpus_set = set(texts)
    assert len(texts) == 233544 and len(texts) - len(corpus_set) == 23980
    candidates = load(ROOT / "candidates.jsonl", True)
    ranks = {a: load(ROOT / f"ranking-{'ce' if a == CE else 'jev'}.jsonl", True) for a in (CE, JEV)}
    assert [r["query_id"] for r in candidates] == ids
    for rows in ranks.values():
        assert [r["query_id"] for r in rows] == ids
    all_gold = set(x for g in gold for x in g["provisions"])
    assert len(all_gold) == 386 and len(all_gold - corpus_set) == 27
    gold_corpus_rows = defaultdict(list)
    for i, text in enumerate(texts):
        if text in all_gold:
            gold_corpus_rows[text].append(i)
    occurrences, stage_queries, pool_rows = [], [], []
    for i, qid in enumerate(ids):
        g = gold[i]
        gs = set(g["provisions"])
        assert len(gs) == len(g["provisions"]) == len(g["unit_ids"])
        bp = [{texts[k] for k in p["row_ids"]} for p in candidates[i]["pools"]]
        bu = set().union(*bp)
        for arm in (CE, JEV):
            rp = ranks[arm][i]["pools"]
            assert len(bp) == len(rp)
            sp = [{texts[k] for k in p["top10_row_ids"]} for p in rp]
            su = set().union(*sp)
            final = set(pred[arm][i]["provisions"])
            assert final <= su <= bu <= corpus_set
            for j, p in enumerate(rp):
                assert p["candidate_row_ids"] == candidates[i]["pools"][j]["row_ids"]
                assert len(p["candidate_row_ids"]) == 100 and len(p["top10_row_ids"]) == 10
                assert pred[arm][i]["selected_row_ids"][j] in p["top10_row_ids"]
                pool_rows.append({"query_id": qid, "arm": arm, "pool_0based": j, "bm25_gold_unit_ids": [u for t, u in zip(g["provisions"], g["unit_ids"]) if t in bp[j]],
                                  "shortlist_gold_unit_ids": [u for t, u in zip(g["provisions"], g["unit_ids"]) if t in sp[j]],
                                  "shortlist_row_ids": p["top10_row_ids"], "selected_row_id": pred[arm][i]["selected_row_ids"][j],
                                  "ranking_source": ref(ROOT / f"ranking-{'ce' if arm == CE else 'jev'}.jsonl", i + 1)})
            status_counts = Counter()
            for text, uid in zip(g["provisions"], g["unit_ids"]):
                present = [text in corpus_set, text in bu, text in su, text in final]
                status = STAGES[next((j for j, ok in enumerate(present) if not ok), 4)]
                status_counts[status] += 1
                occurrences.append({"query_id": qid, "arm": arm, "gold_unit_id": uid, "gold_sha256_utf8": hashlib.sha256(text.encode()).hexdigest(),
                                    "corpus_row_ids": gold_corpus_rows[text], "bm25_pool_ids": [j for j, p in enumerate(bp) if text in p],
                                    "shortlist_pool_ids": [j for j, p in enumerate(sp) if text in p],
                                    "corpus": present[0], "bm25": present[1], "shortlist": present[2], "final": present[3], "first_loss_or_selected": status,
                                    "gold_source": ref(GOLD, i + 1), "candidates_source": ref(ROOT / "candidates.jsonl", i + 1)})
            mb, ms = max_gold_matching(bp, gs), max_gold_matching(sp, gs)
            stage_queries.append({"query_id": qid, "arm": arm, "n_hops": g["n_hops"], "mapping": by[arm, qid]["mapping"],
                                  "n_gold": len(gs), "n_pools": len(bp), "bm25_union_unique": len(bu), "shortlist_union_unique": len(su),
                                  "corpus_gold": len(gs & corpus_set), "bm25_gold": len(gs & bu), "shortlist_gold": len(gs & su), "selected_gold": len(gs & final),
                                  "max_distinct_gold_one_per_bm25_pool": mb, "max_distinct_gold_one_per_shortlist_pool": ms,
                                  "all_gold_in_bm25_union": gs <= bu, "all_gold_bm25_jointly_selectable": mb == len(gs),
                                  "all_gold_in_shortlist_union": gs <= su, "all_gold_shortlist_jointly_selectable": ms == len(gs),
                                  "all_gold_selected": gs <= final, "shortlist_union_complete_but_capacity_insufficient": gs <= su and ms < len(gs),
                                  "n_exact_non_gold_selected_unique": len(final - gs), "first_loss_counts": dict(status_counts)})
    nocc = sum(len(g["provisions"]) for g in gold)
    stage_summary = []
    for arm in (CE, JEV):
        aq = [r for r in stage_queries if r["arm"] == arm]
        ao = [r for r in occurrences if r["arm"] == arm]
        assert len(ao) == nocc
        for stage in ("corpus", "bm25", "shortlist", "final"):
            survived = sum(r[stage] for r in ao)
            complete = sum(all(r[stage] for r in ao if r["query_id"] == qid) for qid in ids)
            key = {"corpus": "corpus_gold", "bm25": "bm25_gold", "shortlist": "shortlist_gold", "final": "selected_gold"}[stage]
            macro = sum(r[key] / r["n_gold"] for r in aq) / 226
            stage_summary.append({"arm": arm, "stage": stage, "surviving_gold_occurrences": survived, "occurrence_denominator": nocc,
                                  "micro_gold_survival": survived / nocc, "macro_question_gold_recall": macro,
                                  "all_gold_questions": complete, "question_denominator": 226, "all_gold_question_rate": complete / 226})
        assert sum(Counter(r["first_loss_or_selected"] for r in ao).values()) == nocc
        close(next(r["macro_question_gold_recall"] for r in stage_summary if r["arm"] == arm and r["stage"] == "final"), analysis["summaries"][arm]["retrieval"]["recall"])
    ca = load(ROOT / "candidate-audit.json")
    bm = next(r for r in stage_summary if r["arm"] == CE and r["stage"] == "bm25")
    close(bm["macro_question_gold_recall"], ca["candidate_recall"])
    close(bm["all_gold_question_rate"], ca["candidate_gold_set_coverage"])
    write_rows("A4/gold-occurrences.jsonl", occurrences)
    write_rows("A4/question-stages.jsonl", stage_queries)
    write_rows("A4/pool-constraints.jsonl", pool_rows)
    write_rows("A4/stage-summary.jsonl", stage_summary)
    write_json("A4/denominators.json", {"questions": 226, "unique_gold_global": 386, "unmapped_unique_gold_global": 27,
               "gold_occurrences_per_arm": nocc, "gold_occurrences_two_arms": nocc * 2, "corpus_rows": len(texts), "corpus_unique_canonical": len(corpus_set),
               "duplicate_rows": 23980, "first_loss_counts": {a: dict(Counter(r["first_loss_or_selected"] for r in occurrences if r["arm"] == a)) for a in (CE, JEV)}})
    print("A4 complete", flush=True)

    # A5: exact strings, cache-key verification, recorded usage and paired summaries.
    source(PROMPT)
    template = runpy.run_path(str(PROMPT))
    lock = load(ROOT / "protocol-lock.json")["signature"]
    enc = tiktoken.get_encoding("o200k_base")
    tok = lambda text: len(enc.encode(text, disallowed_special=()))
    th = hashlib.sha256()
    for b, rank in sorted(enc._mergeable_ranks.items(), key=lambda pair: pair[1]):
        th.update(rank.to_bytes(4, "big") + len(b).to_bytes(4, "big") + b)
    write_json("A5/tokenizer.json", {"package": "tiktoken", "version": importlib.metadata.version("tiktoken"), "encoding": enc.name,
               "mergeable_ranks_sha256": th.hexdigest(), "mergeable_ranks_hash_rule": "ascending rank; uint32 big-endian rank + byte-length + token bytes",
               "special_tokens": enc._special_tokens, "pattern_sha256": hashlib.sha256(enc._pat_str.encode()).hexdigest(), "network": "disabled"})
    resources = []
    for arm in ARMS:
        for i, qid in enumerate(ids):
            p, q = pred[arm][i], qa[i]
            context = "\n".join(p["provisions"])
            message = template["SYSTEM_PROMPT"] + "\n\n" + template["INSTRUCTION_PROMPT"].substitute(question=q["background"] + q["question"], context_str=context)
            body = {"model": lock["generation"]["model"], "messages": [{"role": "user", "content": message}], "temperature": .01, "top_p": .9, "max_tokens": 2000, "store": False}
            key = digest({"identity": lock["generation"], "body": body})
            cache_path = ROOT / "api-cache" / f"{key}.json"
            cache = load(cache_path)
            assert cache["key"] == key
            assert cache["text"].split("Answer:")[-1].strip() == p["answer"]
            trace, usage = p["generation_trace"], p["generation_trace"]["usage"]
            assert trace["response_id"] == cache["trace"]["response_id"] and usage == cache["trace"]["usage"]
            n, nu = len(p["provisions"]), len(set(p["provisions"]))
            resources.append({"query_id": qid, "arm": arm, "selected_list_count": n, "selected_unique_canonical_count": nu,
                              "duplicate_count": n - nu, "duplicate_fraction": (n - nu) / n,
                              "context_tokens": tok(context), "context_chars": len(context), "full_user_message_tokens": tok(message),
                              "api_input_tokens": usage["input_tokens"], "api_output_tokens": usage["output_tokens"],
                              "api_prefix_cached_input_tokens": usage.get("cached_input_tokens", 0),
                              "api_minus_text_input_tokens": usage["input_tokens"] - tok(message), "answer_text_tokens": tok(p["answer"]),
                              "execution_cache_hit": bool(trace.get("cached", False)), "response_id": trace["response_id"], "api_cache_key": key,
                              "context_sha256_utf8": hashlib.sha256(context.encode()).hexdigest(), "full_user_message_sha256_utf8": hashlib.sha256(message.encode()).hexdigest(),
                              "prediction_source": ref(ROOT / "predictions" / f"{arm}.jsonl", i + 1), "api_cache_source": ref(cache_path)})
    quantitative = ["selected_list_count", "selected_unique_canonical_count", "duplicate_count", "duplicate_fraction", "context_tokens", "context_chars",
                    "full_user_message_tokens", "api_input_tokens", "api_output_tokens", "api_prefix_cached_input_tokens", "api_minus_text_input_tokens", "answer_text_tokens"]
    summary, paired_resource = [], []
    for arm in ARMS:
        rs = [r for r in resources if r["arm"] == arm]
        assert len(rs) == 226
        assert Counter(r["selected_list_count"] for r in rs) == {1: 37, 2: 135, 3: 46, 4: 7, 5: 1}
        for k in quantitative:
            summary.append({"arm": arm, "variable": k, **stats([r[k] for r in rs]), "scope": "logical per-query demand; cached rows included"})
    rb = {(r["arm"], r["query_id"]): r for r in resources}
    for qid in ids:
        paired_resource.append({"query_id": qid, **{k: rb[JEV, qid][k] - rb[CE, qid][k] for k in quantitative}})
    for k in quantitative:
        summary.append({"arm": "Jev minus CE (paired)", "variable": k, **stats([r[k] for r in paired_resource]), "scope": "paired logical demand difference"})
    cache_summary = []
    for arm in ARMS:
        for hit in (False, True):
            rs = [r for r in resources if r["arm"] == arm and r["execution_cache_hit"] == hit]
            cache_summary.append({"arm": arm, "execution_cache_hit": hit, "questions": len(rs), "denominator": 226,
                                  "input_tokens_sum": sum(r["api_input_tokens"] for r in rs), "output_tokens_sum": sum(r["api_output_tokens"] for r in rs),
                                  "unique_response_ids": len({r["response_id"] for r in rs}), "interpretation": "reused response demand; zero new request here" if hit else "recorded successful uncached answer-generation response usage; excludes selector, scorer, judge, preparation and retries"})
    assert [sum(r["execution_cache_hit"] for r in resources if r["arm"] == a) for a in ARMS] == [0, 72, 122]
    write_rows("A5/question-resources.jsonl", resources)
    write_rows("A5/descriptive-statistics.jsonl", summary)
    write_rows("A5/paired-resource-differences.jsonl", paired_resource)
    write_rows("A5/cache-separated-usage.jsonl", cache_summary)
    print("A5 complete", flush=True)

    # A6: observations and neutral legal-review questions, never human verdicts.
    sq = {(r["arm"], r["query_id"]): r for r in stage_queries}
    labels = {}
    frequency = []
    for arm in (CE, JEV):
        for qid in ids:
            s, m = sq[arm, qid], by[arm, qid]
            ls = [stage for stage in STAGES[:-1] if s["first_loss_counts"].get(stage, 0)]
            if s["all_gold_selected"] and m["lf_eval"] < .5:
                ls.append("all_gold_selected_low_LF")
            if s["all_gold_selected"] and m["token_f1"] < .5:
                ls.append("all_gold_selected_low_TokenF1")
            if s["n_exact_non_gold_selected_unique"]:
                ls.append("exact_non_gold_selected")
            if s["shortlist_union_complete_but_capacity_insufficient"]:
                ls.append("shortlist_union_complete_pool_capacity_insufficient")
            labels[arm, qid] = ls
        for subset, members in subsets.items():
            for label in list(STAGES[:-1]) + ["all_gold_selected_low_LF", "all_gold_selected_low_TokenF1", "exact_non_gold_selected", "shortlist_union_complete_pool_capacity_insufficient"]:
                affected = [q for q in members if label in labels[arm, q]]
                frequency.append({"arm": arm, "subgroup": subset, "label": label, "n_questions": len(affected), "denominator_questions": len(members),
                                  "rate": len(affected) / len(members) if members else None, "multilabel": True, "query_ids": affected})
    buckets = {
        "Jev_improvement": [q for q in ids if pby[q]["delta"]["f1"] > EPS],
        "CE_advantage": [q for q in ids if pby[q]["delta"]["f1"] < -EPS],
        "common_low_F1": [q for q in ids if by[CE, q]["f1"] < .5 and by[JEV, q]["f1"] < .5],
        "metric_discordance": [q for q in ids if any(pby[q]["strict_discordance"].values())],
    }
    representatives = []

    def choose(bucket, members, stratum):
        if not members:
            return None
        key = (lambda q: (by[CE, q]["f1"] + by[JEV, q]["f1"]) / 2) if bucket == "common_low_F1" else (lambda q: abs(pby[q]["delta"]["f1"]))
        median = statistics.median(key(q) for q in members)
        chosen = min(members, key=lambda q: (abs(key(q) - median), q))
        representatives.append({"bucket": bucket, "stratum": stratum, "candidate_n": len(members), "query_id": chosen,
                                "selection_key": "mean_F1" if bucket == "common_low_F1" else "abs_delta_F1", "key_value": key(chosen), "bucket_median": median,
                                "distance_to_median": abs(key(chosen) - median), "legal_review_status": "NOT_REVIEWED"})
        return chosen

    for bucket, members in buckets.items():
        choose(bucket, members, "all")
        for subset, sids in subsets.items():
            if subset.startswith("hop_") and ("mapped" in subset or "affected" in subset):
                choose(bucket, [q for q in members if q in set(sids)], subset)
    main_buckets = ["Jev_improvement", "CE_advantage", "metric_discordance" if buckets["metric_discordance"] else "common_low_F1"]
    proposed = [r for r in representatives if r["stratum"] == "all" and r["bucket"] in main_buckets]
    casebook, review_queue = [], []
    for qid in ids:
        i, g = index[qid], gold_by[qid]
        auto_labels = {a: labels[a, qid] for a in (CE, JEV)}
        questions = []
        if any("corpus_absent" in v for v in auto_labels.values()):
            questions.append("exact gold와 corpus 차이가 조문 범위·버전·표현 차이인지 검토. 공식 gold 변경 없이 대체 근거 가능성을 별도 기록할 것.")
        if any("exact_non_gold_selected" in v for v in auto_labels.values()):
            questions.append("gold 외 선택 조문이 질문에 적용되는 대체·추가 근거인지, 답변 주장을 실제 지지하는지 확인할 것.")
        if any("shortlist_present_unselected" in v for v in auto_labels.values()):
            questions.append("pool당 선택 하나의 제약과 중복 선택을 먼저 확인한 뒤, 미선택 gold의 법률적 필요성과 선택 조문의 적용 가능성을 검토할 것.")
        if any("all_gold_selected_low_LF" in v or "all_gold_selected_low_TokenF1" in v for v in auto_labels.values()) or qid in buckets["metric_discordance"]:
            questions.append("자동 근거/답변 지표 불일치가 표현 차이인지, 결론·예외·준용·요건의 누락인지 원 질문·정답·선택 근거로 검토할 것. judge reason은 사람 판정이 아님.")
        chosen_for = [r["bucket"] + ":" + r["stratum"] for r in representatives if r["query_id"] == qid]
        if chosen_for and not questions:
            questions.append("대표 후보의 법률적 결론과 선택 근거 지지 여부를 독립적으로 확인할 것. 자동 점수 차이는 법률 정오 판정이 아님.")
        row = {"query_id": qid, "n_hops": g["n_hops"], "mapping": by[CE, qid]["mapping"], "group_id": groups[qid], "in_existing_human_sample": qid in sample,
               "background": qa_by[qid]["background"], "question": qa_by[qid]["question"], "gold_unit_ids": g["unit_ids"], "gold_provisions": g["provisions"], "reference_answer": g["answer"],
               "paired_metrics": pby[qid], "automatic_observation_labels": auto_labels, "stages": {a: sq[a, qid] for a in (CE, JEV)},
               "conditions": {a: {"selected_row_ids": pred[a][i]["selected_row_ids"], "provisions": pred[a][i]["provisions"], "answer": pred[a][i]["answer"],
                                  "lf_judge_reason_unverified": lf[a][i]["reason"], "prediction_source": ref(ROOT / "predictions" / f"{a}.jsonl", i + 1)} for a in (CE, JEV)},
               "selection_difference": {"Jev_only_canonical": sorted(set(pred[JEV][i]["provisions"]) - set(pred[CE][i]["provisions"])), "CE_only_canonical": sorted(set(pred[CE][i]["provisions"]) - set(pred[JEV][i]["provisions"]))},
               "buckets": [k for k, members in buckets.items() if qid in members], "representative_candidate_for": chosen_for,
               "legal_review_status": "NOT_REVIEWED", "legal_review_questions": questions,
               "source": {"qa": ref(QA, i + 1), "gold": ref(GOLD, i + 1)}}
        casebook.append(row)
        if questions:
            review_queue.append({"query_id": qid, "n_hops": g["n_hops"], "mapping": row["mapping"], "representative_candidate_for": chosen_for,
                                 "in_existing_human_sample": qid in sample, "legal_review_status": "NOT_REVIEWED", "review_questions": questions,
                                 "casebook_source": f"A6/casebook.jsonl:{i + 1}", "not_a_human_judgment": True})
    write_rows("A6/observation-frequencies.jsonl", frequency)
    write_json("A6/bucket-membership.json", buckets)
    write_rows("A6/representative-candidates.jsonl", representatives)
    write_json("A6/proposed-three-candidates.json", proposed)
    write_rows("A6/casebook.jsonl", casebook)
    write_rows("A6/legal-review-queue.jsonl", review_queue)
    write_json("A6/human-review-boundary.json", {"existing_sample_n": 60, "existing_sample_ids": sorted(sample), "sample_modified": False,
               "human_judgments_created": 0, "A7": "NOT_RUN_NO_INDEPENDENT_SUBMISSIONS", "legal_queue": "separate qualitative review candidates; not replacements for blinded evaluation sample"})
    print("A6 complete", flush=True)

    # Self-check derived data before publishing a completion record.
    checks = {"all_question_pairings": len(paired) == 226, "metric_rows": len(raw) == 678,
              "hop_partition": sum(len(subsets[f"hop_{h}"]) for h in (1, 2, 3)) == 226,
              "mapping_partition": len(subsets["fully_mapped"]) + len(subsets["affected"]) == 226,
              "stage_occurrence_partition": all(sum(1 for r in occurrences if r["arm"] == a) == nocc for a in (CE, JEV)),
              "all_api_cache_keys_verified": len(resources) == 678, "casebook_complete": len(casebook) == 226,
              "no_new_inference": True, "no_model_calls": True}
    assert all(checks.values())
    source("SESSION_HANDOFF.md")
    source("research/CHAPTER4_WRITING_PLAN_20261109.md")
    source("research/KOBLEX_REPRODUCTION_RESULTS_20261109.md")
    write_json("source-manifest.json", {"paths_relative_to": str(Path.cwd()), "files": SOURCES, "source_reference_convention": "JSONL physical line 1-based; corpus row IDs 0-based; JSON pointers for JSON summaries"})
    write_json("completion.json", {"status": "A1_A6_COMPLETE_OFFLINE", "checks": checks, "sequence": ["A1", "A2", "A3", "A4", "A5", "A6"],
               "versions": {k: importlib.metadata.version(k) for k in ("numpy", "tiktoken")}, "python": sys.version,
               "questions": 226, "gold_occurrences_per_arm": nocc, "legal_review_queue_n": len(review_queue), "paid_calls": 0, "human_judgments_created": 0,
               "manuscript_written": False, "figures_rendered": False})


if __name__ == "__main__":
    main()

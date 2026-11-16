"""Summarize results/koblex-latency-v1/raw.jsonl (no model calls).

Unit of analysis: question. Each question's latency = mean over its 3 repetitions
(repetitions are not counted as independent questions). Warmup rows are excluded.
Paired cluster bootstrap over the 151 source/gold groups restricted to the sample.
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from legal_rag_jev.io import file_hash, read_json, read_jsonl, write_json  # noqa: E402
from legal_rag_jev.koblex_analysis import paired_bootstrap  # noqa: E402

OUT = Path('results/koblex-latency-v1')


def describe(xs):
    a = np.asarray(xs, dtype=float)
    return {'n': int(a.size), 'mean': float(a.mean()), 'median': float(np.median(a)),
            'p25': float(np.quantile(a, .25)), 'p75': float(np.quantile(a, .75)),
            'p95': float(np.quantile(a, .95)), 'min': float(a.min()), 'max': float(a.max())}


def main():
    rows = [r for r in read_jsonl(OUT / 'raw.jsonl') if not r['warmup']]
    groups = read_json('research/koblex_source_audit_20261108.json')['source_and_gold_groups']['groups']
    failures = {m: sum(r['status'] != 'ok' for r in rows if r['method'] == m) for m in ('ce', 'jev')}
    by = defaultdict(lambda: defaultdict(list))
    meta = {}
    for r in rows:
        if r['status'] == 'ok':
            by[r['query_id']][r['method']].append(r)
            meta[r['query_id']] = {'pairs': r['pairs'], 'pools': r['pools']}
    qids = sorted(q for q in by if all(len(by[q][m]) == 3 for m in ('ce', 'jev')))
    per_q = {m: [float(np.mean([x['wall_clock_ms'] for x in by[q][m]])) for q in qids] for m in ('ce', 'jev')}
    per_pair = {m: [v / meta[q]['pairs'] for v, q in zip(per_q[m], qids)] for m in ('ce', 'jev')}
    diff = paired_bootstrap([j - c for j, c in zip(per_q['jev'], per_q['ce'])], [groups[q] for q in qids])
    log_ratio = paired_bootstrap([float(np.log(j / c)) for j, c in zip(per_q['jev'], per_q['ce'])], [groups[q] for q in qids])
    jev_rows = [x for q in qids for x in by[q]['jev']]
    summary = {
        'status': 'EXPLORATORY_SCORER_ONLY_LATENCY',
        'questions_complete': len(qids), 'failed_attempts': failures,
        'per_question_ms': {m: describe(per_q[m]) for m in per_q},
        'per_pair_ms': {m: describe(per_pair[m]) for m in per_pair},
        'pairs_per_question': describe([meta[q]['pairs'] for q in qids]),
        'jev_minus_ce_ms': {'mean_difference': diff['mean_difference'], 'ci95': diff['ci95'],
                            'p_centered_bootstrap_two_sided': diff['p_centered_bootstrap_two_sided'],
                            'clusters': diff['clusters']},
        'jev_over_ce_geometric_mean_ratio': {'estimate': float(np.exp(log_ratio['mean_difference'])),
                                             'ci95': [float(np.exp(v)) for v in log_ratio['ci95']]},
        'repeatability': {
            m: {'top10_identical_to_quality_run_fraction': float(np.mean([x['top10_same_as_quality_run'] for q in qids for x in by[q][m]])),
                'top10_set_overlap_mean': float(np.mean([x['top10_set_overlap'] for q in qids for x in by[q][m]]))}
            for m in ('ce', 'jev')},
        'within_question_cv': {m: float(np.mean([np.std([x['wall_clock_ms'] for x in by[q][m]]) /
                                                 np.mean([x['wall_clock_ms'] for x in by[q][m]]) for q in qids])) for m in ('ce', 'jev')},
        'jev_retries': int(sum(x.get('retries', 0) for x in jev_rows)),
        'jev_cost_usd_measured_reps': float(sum(x.get('cost_usd', 0) for x in jev_rows)),
        'raw_sha256': file_hash(OUT / 'raw.jsonl'), 'script_sha256': file_hash(Path(__file__)),
        'limits': ['scorer-only: excludes LLM selection and generation (same structure in both conditions)',
                   'deployment comparison: local Apple MPS CE vs remote Jev API at concurrency 4; not model-intrinsic speed',
                   'network conditions of one session; no cost model for local CE hardware',
                   '60-question pre-registered sample, not all 226']}
    write_json(OUT / 'summary.json', summary)
    print(json.dumps(summary, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()

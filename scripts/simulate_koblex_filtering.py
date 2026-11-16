"""Offline threshold-filtering simulation on the completed ParSeR study (no model/API calls).

Reads the locked study read-only and writes results/koblex-filtering-v1/.

What it answers: if a score threshold tau were applied to the scorer output,
how many evidence items would be removed, and how would the official string-based
evidence metrics change? CE (sigmoid 0-1) and Jev (noul 0-1) are both 0-1 scores, but
scales differ, so results are also reported at matched keep rates.

Two filter positions:
  post  - drop a final LLM-selected item when its scorer score < tau (0 items allowed).
          Evidence P/R/F1/EM exact; answers are NOT regenerated, so answer quality is unknown.
  pre   - drop shortlist (top-10) candidates with score < tau before LLM selection.
          Only gold retention in the shortlist is exact; the LLM's choice would change.

Operating point:
  5-fold cross-validation over the 151 source/gold dependency groups (seed 20261109).
  Each scorer gets its own 20-point grid matched to its score scale (final_research_strategy
  sec. 8: per-scale grids of equal size): thresholds at the training-fold quantiles of that
  scorer's final-selection scores for keep rates 1.00, 0.95, ..., 0.05.
  On training folds pick the threshold with the fewest kept items whose mean evidence F1 is
  >= unfiltered training F1 - 1.0 point; ties -> lower tau.
  Revision note: a first run used one absolute 0.00-0.95 grid for both scorers; CE sigmoid
  scores of selected items are mostly < 0.05, so that grid could not filter CE at all.
  The per-scale grid follows the pre-existing design and replaces it.
  Apply to held-out fold. Paired cluster bootstrap (10,000, seed 20261108) as in the study.
Exploratory: the 226 test questions were already observed; this is not a confirmatory test.
"""
from __future__ import annotations
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from legal_rag_jev.io import file_hash, read_json, read_jsonl, write_json  # noqa: E402
from legal_rag_jev.koblex import provision_metrics  # noqa: E402
from legal_rag_jev.koblex_analysis import paired_bootstrap  # noqa: E402

STUDY = Path('results/koblex-reproduction-v1')
OUT = Path('results/koblex-filtering-v1')
CORPUS = Path('data/koblex/downloads/statute.jsonl')
GOLD = Path('data/koblex/prepared-v1/gold.jsonl')
AUDIT = Path('research/koblex_source_audit_20261108.json')
ARMS = {'ce': ('parser_ce_fixed', 'ranking-ce.jsonl'), 'jev': ('parser_jev_fixed', 'ranking-jev.jsonl')}
GRID = [round(x * 0.05, 2) for x in range(20)]          # 0.00 .. 0.95
KEEP_RATES = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
CV_KEEP_GRID = [round(1 - x * 0.05, 2) for x in range(20)]  # 1.00 .. 0.05
TOLERANCE = 0.01                                          # 1.0 F1 point
FOLDS, CV_SEED = 5, 20261109


def mean(xs):
    return sum(xs) / len(xs) if xs else float('nan')


def main():
    if OUT.exists():
        raise SystemExit('Output exists; refusing to overwrite: ' + str(OUT))
    corpus = [r['hierarchy'] + r['content'] for r in read_jsonl(CORPUS)]
    gold = read_jsonl(GOLD)
    order = [g['query_id'] for g in gold]
    gold_by = {g['query_id']: g for g in gold}
    groups = read_json(AUDIT)['source_and_gold_groups']['groups']

    # items[s][qid] = [(pool, row_id, score)] for final selections; shortlist[s][qid] = [[(row, score)]*10 per pool]
    items, shortlist = {}, {}
    for s, (arm, ranking) in ARMS.items():
        preds = {p['query_id']: p for p in read_jsonl(STUDY / 'predictions' / f'{arm}.jsonl')}
        ranks = {r['query_id']: r for r in read_jsonl(STUDY / ranking)}
        items[s], shortlist[s] = {}, {}
        for qid in order:
            pools, pred = ranks[qid]['pools'], preds[qid]
            if len(pred['selected_row_ids']) != len(pools):
                raise ValueError('Selection/pool mismatch ' + qid)
            score_of = [dict(zip(p['candidate_row_ids'], p['scores'])) for p in pools]
            sel = []
            for j, row in enumerate(pred['selected_row_ids']):
                if row not in pools[j]['top10_row_ids']:
                    raise ValueError('Selected row outside its pool shortlist ' + qid)
                sel.append((j, row, score_of[j][row]))
            if [corpus[r] for _, r, _ in sel] != pred['provisions']:
                raise ValueError('Provision text mismatch ' + qid)
            items[s][qid] = sel
            shortlist[s][qid] = [[(r, score_of[j][r]) for r in p['top10_row_ids']] for j, p in enumerate(pools)]

    def post_rows(s, tau_for):  # tau_for(qid) -> tau
        rows = []
        for qid in order:
            tau = tau_for(qid)
            kept = [corpus[r] for _, r, sc in items[s][qid] if sc >= tau]
            m = provision_metrics(kept, gold_by[qid]['provisions'])
            rows.append({'query_id': qid, 'n_hops': gold_by[qid]['n_hops'], 'tau': tau,
                         'selected': len(items[s][qid]), 'kept': len(kept),
                         'kept_chars': sum(len(t) for t in kept), **m})
        return rows

    def summarize(rows):
        return {'questions': len(rows), 'f1': mean([r['f1'] for r in rows]) * 100,
                'precision': mean([r['precision'] for r in rows]) * 100,
                'recall': mean([r['recall'] for r in rows]) * 100, 'em': mean([r['em'] for r in rows]) * 100,
                'gold_set_coverage': mean([r['gold_set_coverage'] for r in rows]) * 100,
                'kept_items_total': sum(r['kept'] for r in rows), 'kept_items_mean': mean([r['kept'] for r in rows]),
                'kept_fraction': sum(r['kept'] for r in rows) / sum(r['selected'] for r in rows),
                'kept_chars_mean': mean([r['kept_chars'] for r in rows]),
                'zero_evidence_questions': sum(r['kept'] == 0 for r in rows)}

    def pre_summary(s, tau):
        sizes, occ_hit, occ_all, q_all = [], 0, 0, 0
        for qid in order:
            g = set(gold_by[qid]['provisions'])
            kept_texts = set()
            for pool in shortlist[s][qid]:
                kept = [r for r, sc in pool if sc >= tau]
                sizes.append(len(kept)); kept_texts |= {corpus[r] for r in kept}
            occ_hit += len(g & kept_texts); occ_all += len(g); q_all += g <= kept_texts
        return {'tau': tau, 'shortlist_size_mean_per_pool': mean(sizes),
                'empty_shortlist_pools': sum(x == 0 for x in sizes), 'pools': len(sizes),
                'shortlist_gold_recall': occ_hit / occ_all * 100,
                'questions_all_gold_in_shortlist': q_all / len(order) * 100}

    OUT.mkdir(parents=True)
    curves = {'post_absolute': [], 'post_matched_keep_rate': [], 'pre_absolute': [], 'pre_matched_keep_rate': []}
    for s in ARMS:
        for tau in GRID:
            curves['post_absolute'].append({'scorer': s, 'tau': tau, **summarize(post_rows(s, lambda q, t=tau: t))})
            curves['pre_absolute'].append({'scorer': s, **pre_summary(s, tau)})
        sel_scores = sorted(sc for q in order for _, _, sc in items[s][q])
        sl_scores = sorted(sc for q in order for pool in shortlist[s][q] for _, sc in pool)
        for k in KEEP_RATES:
            tau = sel_scores[int(round((1 - k) * len(sel_scores)))] if k < 1 else 0.0
            curves['post_matched_keep_rate'].append({'scorer': s, 'target_keep_rate': k, 'tau': tau,
                                                     **summarize(post_rows(s, lambda q, t=tau: t))})
            tau = sl_scores[int(round((1 - k) * len(sl_scores)))] if k < 1 else 0.0
            curves['pre_matched_keep_rate'].append({'scorer': s, 'target_keep_rate': k, **pre_summary(s, tau)})
    for name, rows in curves.items():
        with (OUT / f'{name}.csv').open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    # Cross-validated operating point.
    gids = sorted(set(groups[q] for q in order))
    random.Random(CV_SEED).shuffle(gids)
    fold_of_group = {g: i % FOLDS for i, g in enumerate(gids)}
    fold = {q: fold_of_group[groups[q]] for q in order}
    cv, chosen = {}, {}
    cache = {}

    def rows_at(s, tau):
        if (s, tau) not in cache:
            cache[s, tau] = {r['query_id']: r for r in post_rows(s, lambda q, t=tau: t)}
        return cache[s, tau]
    for s in ARMS:
        chosen[s], held = {}, {}
        for k in range(FOLDS):
            train = [q for q in order if fold[q] != k]
            scores = sorted(sc for q in train for _, _, sc in items[s][q])
            grid = sorted({0.0 if r >= 1 else scores[int(round((1 - r) * len(scores)))] for r in CV_KEEP_GRID})
            base = mean([rows_at(s, 0.0)[q]['f1'] for q in train])
            ok = [t for t in grid if mean([rows_at(s, t)[q]['f1'] for q in train]) >= base - TOLERANCE]
            tau = min(ok, key=lambda t: (sum(rows_at(s, t)[q]['kept'] for q in train), t))
            chosen[s][k] = {'tau': tau, 'train_keep_rate': sum(rows_at(s, tau)[q]['kept'] for q in train) /
                            sum(rows_at(s, tau)[q]['selected'] for q in train)}
            for q in order:
                if fold[q] == k:
                    held[q] = rows_at(s, tau)[q]
        cv[s] = {'rows': [held[q] for q in order], 'unfiltered': [rows_at(s, 0.0)[q] for q in order]}
    gl = [groups[q] for q in order]

    def boot(a, b, key, scale=100):
        r = paired_bootstrap([x[key] - y[key] for x, y in zip(a, b)], gl)
        return {'estimate': r['mean_difference'] * scale, 'ci95': [v * scale for v in r['ci95']],
                'p_centered_bootstrap_two_sided': r['p_centered_bootstrap_two_sided'],
                'clusters': r['clusters'], 'repetitions': r['repetitions'], 'seed': r['seed']}
    comparisons = {}
    for s in ARMS:
        comparisons[f'{s}_FR_minus_{s}_R'] = {
            'f1_points': boot(cv[s]['rows'], cv[s]['unfiltered'], 'f1'),
            'recall_points': boot(cv[s]['rows'], cv[s]['unfiltered'], 'recall'),
            'precision_points': boot(cv[s]['rows'], cv[s]['unfiltered'], 'precision'),
            'kept_items_per_question': boot(cv[s]['rows'], cv[s]['unfiltered'], 'kept', scale=1)}
    comparisons['jev_FR_minus_ce_FR'] = {
        'f1_points': boot(cv['jev']['rows'], cv['ce']['rows'], 'f1'),
        'kept_items_per_question': boot(cv['jev']['rows'], cv['ce']['rows'], 'kept', scale=1)}
    for s in ARMS:
        with (OUT / f'cv-heldout-{s}.jsonl').open('w', encoding='utf-8') as f:
            for r in cv[s]['rows']:
                f.write(json.dumps({**r, 'fold': fold[r['query_id']]}, ensure_ascii=False) + '\n')

    by_hop = {s: {str(h): {'unfiltered': summarize([r for r in cv[s]['unfiltered'] if r['n_hops'] == h]),
                           'filtered_cv': summarize([r for r in cv[s]['rows'] if r['n_hops'] == h])}
                  for h in (1, 2, 3)} for s in ARMS}
    write_json(OUT / 'summary.json', {
        'status': 'EXPLORATORY_OFFLINE_SIMULATION_NO_ANSWER_REGENERATION',
        'paid_calls': 0,
        'rule': {'absolute_curve_grid': GRID, 'cv_grid': 'per-scorer training-fold quantiles at keep rates ' + str(CV_KEEP_GRID), 'tolerance_f1_points': TOLERANCE * 100, 'folds': FOLDS, 'cv_seed': CV_SEED,
                 'objective': 'fewest kept final items s.t. train F1 >= unfiltered train F1 - tolerance; tie -> lower tau',
                 'zero_items_allowed': True, 'filter_position': 'post-selection (final LLM-selected items)'},
        'chosen_tau_per_fold': chosen,
        'cv_overall': {s: {'unfiltered': summarize(cv[s]['unfiltered']), 'filtered_cv': summarize(cv[s]['rows'])} for s in ARMS},
        'cv_by_hop': by_hop,
        'paired_bootstrap': comparisons,
        'limits': ['answers not regenerated: Token F1 / LF-Eval under filtering unknown',
                   'pre-selection curves give shortlist gold retention only; LLM choice would change',
                   'test questions already observed; exploratory, not non-inferiority evidence',
                   'evidence metrics are exact-string; filtered-out non-gold items may still be legally useful'],
        'inputs': {str(p): file_hash(p) for p in [GOLD, AUDIT, STUDY / 'ranking-ce.jsonl', STUDY / 'ranking-jev.jsonl',
                   STUDY / 'predictions/parser_ce_fixed.jsonl', STUDY / 'predictions/parser_jev_fixed.jsonl']},
        'script_sha256': file_hash(Path(__file__))})
    print(json.dumps({'cv_overall': {s: {k: {m: round(v, 2) if isinstance(v, float) else v for m, v in d.items()}
                                          for k, d in x.items()} for s, x in
                                     read_json(OUT / 'summary.json')['cv_overall'].items()},
                      'chosen': chosen}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()

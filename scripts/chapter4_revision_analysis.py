"""Chapter 4 Stage-4 revision: deterministic re-computation of reviewer-cited values (no model/API/network calls).

Reads the locked study outputs read-only and writes ONLY to
results/koblex-reproduction-v1/chapter4-revision-v1/.

Rules (revision roadmap G1, G4, G6):
- Every number that reviewers recounted is recomputed here from the raw files; only these values enter the manuscript.
- Every new interval uses the locked bootstrap exactly: legal_rag_jev.koblex_analysis.paired_bootstrap
  (cluster = source/gold dependency group from research/koblex_source_audit_20261108.json, 10,000 resamples,
  seed 20261108, numpy percentile quantiles [.025, .975]). The procedure is first verified by reproducing every
  stored interval in analysis.json and the filtering e2e-summary.json bit-for-bit.
- All new intervals are post hoc (computed after the results were observed) and exploratory.
- The human-review fields / directories are not read.

Run from the repository root:  .venv/bin/python scripts/chapter4_revision_analysis.py
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from legal_rag_jev.koblex_analysis import paired_bootstrap  # noqa: E402  (locked procedure, imported unchanged)

REPRO = Path('results/koblex-reproduction-v1')
PREP = REPRO / 'chapter4-prep-v1'
FILT = Path('results/koblex-filtering-v1')
LAT = Path('results/koblex-latency-v1')
OUT = REPRO / 'chapter4-revision-v1'
AUDIT = Path('research/koblex_source_audit_20261108.json')
GOLD = Path('data/koblex/prepared-v1/gold.jsonl')
CORPUS = Path('data/koblex/downloads/statute.jsonl')
LF_PROMPT = Path('research/prompts/koblex_lf_eval.json')
PROVIDERS = Path('src/legal_rag_jev/providers.py')
ARMS = ('parser_ce_raw', 'parser_ce_fixed', 'parser_jev_fixed')
CE, JEV = 'parser_ce_fixed', 'parser_jev_fixed'
TIE = 1e-12
INPUTS: dict[str, str] = {}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def use(path: Path) -> Path:
    INPUTS[path.as_posix()] = sha(path)
    return path


def jl(path: Path) -> list[dict]:
    with open(use(path), encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def js(path: Path):
    with open(use(path), encoding='utf-8') as f:
        return json.load(f)


def boot(diffs, gids, scale=100.0):
    r = paired_bootstrap(list(diffs), list(gids))
    return {'estimate': scale * r['mean_difference'], 'ci95': [scale * v for v in r['ci95']],
            'p_centered_bootstrap_two_sided': r['p_centered_bootstrap_two_sided'],
            'questions': r['questions'], 'clusters': r['clusters'], 'repetitions': r['repetitions'], 'seed': r['seed'],
            'post_hoc': True}


def main():
    if OUT.exists() and any(OUT.iterdir()):
        for p in OUT.iterdir():
            if p.name != 'README.md':
                p.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    groups = js(AUDIT)['source_and_gold_groups']['groups']
    metrics = {a: {r['query_id']: r for r in jl(REPRO / 'metrics' / a / 'metrics.jsonl')} for a in ARMS}
    lf = {a: {r['query_id']: r for r in jl(REPRO / 'lf-eval' / a / 'metrics.jsonl')} for a in ARMS}
    order = [r for r in metrics[ARMS[0]]]
    assert len(order) == 226 and all(list(metrics[a]) == order for a in ARMS)
    analysis = js(REPRO / 'analysis.json')
    res: dict = {'status': 'POST_HOC_EXPLORATORY_REVISION_RECOMPUTATION', 'api_calls': 0, 'network_calls': 0,
                 'bootstrap_procedure': 'legal_rag_jev.koblex_analysis.paired_bootstrap (imported, unchanged); '
                                        'clusters = source/gold groups; 10,000 resamples; seed 20261108; '
                                        'numpy quantile [.025,.975] percentile interval',
                 'created_at_utc': datetime.now(timezone.utc).isoformat()}

    def val(arm, q, m):
        if m == 'lf_eval':
            return lf[arm][q]['score']
        if m == 'token_f1':
            return metrics[arm][q]['token_f1']
        return metrics[arm][q]['retrieval'][m]

    # ---------------- 0. Verification: reproduce stored intervals bit-for-bit ----------------
    ver = []
    for t, c in [(JEV, CE), (CE, 'parser_ce_raw')]:
        for m in ('f1', 'recall', 'em', 'gold_set_coverage', 'token_f1', 'lf_eval'):
            r = paired_bootstrap([val(t, q, m) - val(c, q, m) for q in order], [groups[q] for q in order])
            stored = next(x for x in analysis['comparisons'] if x['treatment'] == t and x['control'] == c and x['metric'] == m)
            ver.append({'comparison': f'{t}-{c}', 'metric': m,
                        'exact_match': r['mean_difference'] == stored['mean_difference'] and r['ci95'] == stored['ci95']
                        and r['p_centered_bootstrap_two_sided'] == stored['p_centered_bootstrap_two_sided'],
                        'ci95_recomputed': r['ci95'], 'ci95_stored': stored['ci95']})
    e2e = js(FILT / 'e2e-summary.json')
    fr_metrics = {s: {r['query_id']: r for r in jl(FILT / 'e2e' / 'metrics' / f'{s}_fr' / 'metrics.jsonl')} for s in ('ce', 'jev')}
    fr_lf = {s: {r['query_id']: r['score'] for r in jl(FILT / 'e2e' / 'lf-eval' / f'{s}_fr' / 'metrics.jsonl')} for s in ('ce', 'jev')}

    def frval(s, q, m):
        if m == 'lf_eval':
            return fr_lf[s][q]
        if m == 'token_f1':
            return fr_metrics[s][q]['token_f1']
        return fr_metrics[s][q]['retrieval'][m]
    base = {'ce': CE, 'jev': JEV}
    filt_recomputed = {}
    for s in ('ce', 'jev'):
        for m in ('f1', 'precision', 'recall', 'em', 'gold_set_coverage', 'token_f1', 'lf_eval'):
            r = paired_bootstrap([frval(s, q, m) - val(base[s], q, m) for q in order], [groups[q] for q in order])
            stored = e2e['paired_bootstrap_points'][f'{s}_fr-{s}_r'][m]
            est, ci = 100 * r['mean_difference'], [100 * v for v in r['ci95']]
            ok = math.isclose(est, stored['estimate'], abs_tol=1e-9) and all(math.isclose(a, b, abs_tol=1e-9) for a, b in zip(ci, stored['ci95']))
            ver.append({'comparison': f'{s}_fr-{s}_r (filtering e2e)', 'metric': m, 'exact_match': ok,
                        'ci95_recomputed': ci, 'ci95_stored': stored['ci95']})
            filt_recomputed[f'{s}_fr-{s}_r/{m}'] = {'estimate': est, 'ci95': ci}
    res['verification'] = {'all_exact': all(v['exact_match'] for v in ver), 'n': len(ver), 'rows': ver}
    if not res['verification']['all_exact']:
        raise SystemExit('Locked bootstrap not reproduced; refusing to compute new intervals')

    # ---------------- RM-01 / RM-04: filtering values re-extracted (and recomputed above) ----------------
    fs = js(FILT / 'summary.json')
    res['RM01_RM04_filtering'] = {
        'means_points': e2e['means'],
        'jev_fr_minus_jev_r': {m: e2e['paired_bootstrap_points']['jev_fr-jev_r'][m] for m in ('f1', 'precision', 'recall', 'gold_set_coverage', 'em', 'token_f1', 'lf_eval')},
        'ce_fr_minus_ce_r': {m: e2e['paired_bootstrap_points']['ce_fr-ce_r'][m] for m in ('f1', 'precision', 'recall', 'gold_set_coverage', 'em', 'token_f1', 'lf_eval')},
        'jev_fr_minus_ce_fr': e2e['paired_bootstrap_points']['jev_fr-ce_fr'],
        'jev_fr_minus_ce_r': e2e['paired_bootstrap_points']['jev_fr-ce_r'],
        'kept_items': {s: fs['cv_overall'][s]['filtered_cv']['kept_items_total'] for s in ('ce', 'jev')},
        'zero_evidence_questions': {s: fs['cv_overall'][s]['filtered_cv']['zero_evidence_questions'] for s in ('ce', 'jev')},
        'regenerated_answers': {s: e2e['checks'][s]['regenerated'] for s in ('ce', 'jev')},
        'reused_answers': {s: e2e['checks'][s]['reused_answers'] for s in ('ce', 'jev')},
        'rule': fs['rule'], 'chosen_tau_per_fold': fs['chosen_tau_per_fold'],
        'recomputed_from_e2e_rows': filt_recomputed,
    }

    # ---------------- RM-10: shortlist gold retention CI ----------------
    stages = {(r['arm'], r['query_id']): r for r in jl(PREP / 'A4' / 'question-stages.jsonl')}
    sl = {a: {q: stages[(a, q)]['shortlist_gold'] / stages[(a, q)]['n_gold'] for q in order} for a in (CE, JEV)}
    bm = {q: stages[(CE, q)]['bm25_gold'] / stages[(CE, q)]['n_gold'] for q in order}
    allsl = {a: {q: float(stages[(a, q)]['all_gold_in_shortlist_union']) for q in order} for a in (CE, JEV)}
    sb = {
        'definition': 'per-question shortlist-union gold recall = shortlist_gold / n_gold (A4/question-stages.jsonl), unweighted question mean; '
                      'all-gold-in-shortlist = all_gold_in_shortlist_union indicator',
        'bm25_union_recall_points': 100 * np.mean([bm[q] for q in order]),
        'shortlist_recall_points': {a: 100 * np.mean([sl[a][q] for q in order]) for a in (CE, JEV)},
        'shortlist_recall_diff': boot([sl[JEV][q] - sl[CE][q] for q in order], [groups[q] for q in order]),
        'all_gold_in_shortlist_questions': {a: int(sum(allsl[a].values())) for a in (CE, JEV)},
        'all_gold_in_shortlist_diff_pctpoints': boot([allsl[JEV][q] - allsl[CE][q] for q in order], [groups[q] for q in order]),
        'shortlist_recall_win_tie_loss': [sum(sl[JEV][q] - sl[CE][q] > TIE for q in order), sum(abs(sl[JEV][q] - sl[CE][q]) <= TIE for q in order),
                                          sum(sl[CE][q] - sl[JEV][q] > TIE for q in order)],
    }
    res['RM10_shortlist'] = sb
    (OUT / 'shortlist-bootstrap.json').write_text(json.dumps(sb, ensure_ascii=False, indent=1, default=float))

    # ---------------- RM-11 / RM-23: conditional selection and unselected decomposition ----------------
    occ = jl(PREP / 'A4' / 'gold-occurrences.jsonl')
    pools = {(r['arm'], r['query_id'], r['pool_0based']): r for r in jl(PREP / 'A4' / 'pool-constraints.jsonl')}
    cond = {}
    for a in (CE, JEV):
        o = [r for r in occ if r['arm'] == a]
        n_sl = sum(r['shortlist'] for r in o)
        n_sel = sum(r['final'] for r in o)
        cond[a] = {'shortlist_occurrences': n_sl, 'selected_occurrences': n_sel, 'conditional_selection_rate_pct': 100 * n_sel / n_sl,
                   'first_loss_counts': dict(Counter(r['first_loss_or_selected'] for r in o))}
    res['RM11_conditional_selection'] = cond
    unit_rows = {(r['arm'], r['query_id'], r['gold_unit_id']): set(r['corpus_row_ids']) for r in occ}
    units_of_q = defaultdict(list)
    for r in occ:
        units_of_q[(r['arm'], r['query_id'])].append(r['gold_unit_id'])
    dec = {}
    for a in (CE, JEV):
        structural = choosable = 0
        best_ranks, sel_gold_ranks = [], []
        for r in occ:
            if r['arm'] != a:
                continue
            if r['shortlist']:
                ranks = []
                for p in r['shortlist_pool_ids']:
                    ids = pools[(a, r['query_id'], p)]['shortlist_row_ids']
                    ranks += [ids.index(x) + 1 for x in ids if x in unit_rows[(a, r['query_id'], r['gold_unit_id'])]]
                best_ranks.append(min(ranks))
            if r['first_loss_or_selected'] != 'shortlist_present_unselected':
                continue
            # structural if every shortlist pool containing this gold selected a different gold of the same question
            other_gold_everywhere = True
            for p in r['shortlist_pool_ids']:
                sel = pools[(a, r['query_id'], p)]['selected_row_id']
                others = [u for u in units_of_q[(a, r['query_id'])] if u != r['gold_unit_id'] and sel in unit_rows[(a, r['query_id'], u)]]
                if not others:
                    other_gold_everywhere = False
            if other_gold_everywhere:
                structural += 1
            else:
                choosable += 1
        for (arm, q, p), pr in pools.items():
            if arm == a and pr['selected_row_id'] in pr['shortlist_row_ids'] and any(pr['selected_row_id'] in unit_rows[(a, q, u)] for u in units_of_q[(a, q)]):
                sel_gold_ranks.append(pr['shortlist_row_ids'].index(pr['selected_row_id']) + 1)
        dec[a] = {'unselected_total': structural + choosable,
                  'unselected_pool_used_by_other_gold': structural,
                  'unselected_pool_selected_non_gold': choosable,
                  'shortlist_gold_best_rank_mean': float(np.mean(best_ranks)), 'shortlist_gold_best_rank_median': float(np.median(best_ranks)),
                  'shortlist_gold_rank1_share_pct': 100 * float(np.mean([x == 1 for x in best_ranks])),
                  'selected_gold_rank_mean': float(np.mean(sel_gold_ranks)), 'selected_gold_n_pools': len(sel_gold_ranks)}
    res['RM23_unselected_decomposition'] = dec

    # ---------------- RM-12: hop-level counts ----------------
    a1 = {(r['arm'], r['query_id']): r for r in jl(PREP / 'A1' / 'question-metrics.jsonl')}
    hop = {}
    for h in (1, 2, 3):
        qs = [q for q in order if metrics[CE][q]['n_hops'] == h]
        d = [a1[(JEV, q)]['f1'] - a1[(CE, q)]['f1'] for q in qs]
        hop[str(h)] = {'questions': len(qs),
                       'f1_win_tie_loss_jev_tie_ce': [sum(x > TIE for x in d), sum(abs(x) <= TIE for x in d), sum(x < -TIE for x in d)],
                       'f1_points': {a: 100 * np.mean([a1[(a, q)]['f1'] for q in qs]) for a in (CE, JEV)},
                       'f1_diff_sum_share_of_total_pct': None,
                       'complete_coverage': {a: int(sum(stages[(a, q)]['all_gold_selected'] for q in qs)) for a in (CE, JEV)},
                       'all_gold_in_shortlist': {a: int(sum(stages[(a, q)]['all_gold_in_shortlist_union'] for q in qs)) for a in (CE, JEV)},
                       'shortlist_jointly_selectable': {a: int(sum(stages[(a, q)]['all_gold_shortlist_jointly_selectable'] for q in qs)) for a in (CE, JEV)},
                       'pools_fewer_than_gold': int(sum(stages[(CE, q)]['n_pools'] < stages[(CE, q)]['n_gold'] for q in qs)),
                       'pools_fewer_than_gold_same_in_both_arms': all(stages[(CE, q)]['n_pools'] == stages[(JEV, q)]['n_pools'] for q in qs)}
    total = sum(a1[(JEV, q)]['f1'] - a1[(CE, q)]['f1'] for q in order)
    for h in hop:
        qs = [q for q in order if metrics[CE][q]['n_hops'] == int(h)]
        hop[h]['f1_diff_sum_share_of_total_pct'] = 100 * sum(a1[(JEV, q)]['f1'] - a1[(CE, q)]['f1'] for q in qs) / total
    res['RM12_hop'] = hop

    # ---------------- RM-13: diagnostic-sample exclusion sensitivity ----------------
    plan = js(REPRO / 'ce-diagnostic-plan.json')
    diag = set(plan['sample_ids'])
    rest = [q for q in order if q not in diag]
    res['RM13_diagnostic_exclusion'] = {
        'diagnostic_questions': len(diag), 'remaining_questions': len(rest),
        'diagnostic_variants_f1_points': {k: 100 * v['f1'] for k, v in js(REPRO / 'ce-diagnostic-summary.json')['variants'].items()},
        'f1_diff': boot([val(JEV, q, 'f1') - val(CE, q, 'f1') for q in rest], [groups[q] for q in rest]),
        'lf_eval_diff': boot([val(JEV, q, 'lf_eval') - val(CE, q, 'lf_eval') for q in rest], [groups[q] for q in rest]),
        'token_f1_diff': boot([val(JEV, q, 'token_f1') - val(CE, q, 'token_f1') for q in rest], [groups[q] for q in rest]),
        'case_ids_in_diagnostic_sample': {c: c in diag for c in ('qa_124_2hop_480_rand', 'qa_324_2hop_515', 'qa_443_3hop_703')},
    }

    # ---------------- RM-07 / RM-08: p-values, Holm, BH, precision CI, MC sensitivity ----------------
    fam = ['f1', 'recall', 'em', 'gold_set_coverage', 'token_f1', 'lf_eval']
    ps = {m: next(x for x in analysis['comparisons'] if x['treatment'] == JEV and x['control'] == CE and x['metric'] == m)['p_centered_bootstrap_two_sided'] for m in fam}
    raw_ps = {m: next(x for x in analysis['comparisons'] if x['treatment'] == CE and x['control'] == 'parser_ce_raw' and x['metric'] == m)['p_centered_bootstrap_two_sided'] for m in fam}
    srt = sorted(fam, key=lambda m: ps[m])
    k = len(fam)
    holm, run = {}, 0.0
    for i, m in enumerate(srt):
        run = max(run, min(1.0, (k - i) * ps[m]))
        holm[m] = run
    bh, nxt = {}, 1.0
    for i in range(k - 1, -1, -1):
        m = srt[i]
        nxt = min(nxt, min(1.0, k * ps[m] / (i + 1)))
        bh[m] = nxt
    prec = boot([val(JEV, q, 'precision') - val(CE, q, 'precision') for q in order], [groups[q] for q in order])
    tok = [val(JEV, q, 'token_f1') - val(CE, q, 'token_f1') for q in order]
    mc = []
    for s in range(1, 21):
        r = paired_bootstrap(tok, [groups[q] for q in order], seed=20261108 + s)
        mc.append(100 * r['ci95'][0])
    res['RM07_RM08_multiplicity'] = {
        'family': fam, 'family_note': 'Jev vs fixed CE; precision excluded (no stored p; F1 is a function of P and R)',
        'p_centered_stored': ps, 'p_holm': holm, 'p_bh': bh, 'p_centered_stored_ce_fixed_vs_raw': raw_ps,
        'precision_diff': prec,
        'token_f1_lower_bound_mc_sensitivity': {'seeds': [20261108 + s for s in range(1, 21)], 'lower_bounds_points': mc,
                                                'n_lower_below_zero': sum(x < 0 for x in mc), 'min': min(mc), 'max': max(mc),
                                                'note': 'Monte Carlo sensitivity only; reported CI keeps the locked seed 20261108'}}

    # ---------------- RM-09 / RM-24: LF-Eval coupling, reuse definitions ----------------
    preds = {a: {r['query_id']: r for r in jl(REPRO / 'predictions' / f'{a}.jsonl')} for a in ARMS}
    dF = np.array([val(JEV, q, 'f1') - val(CE, q, 'f1') for q in order])
    dL = np.array([val(JEV, q, 'lf_eval') - val(CE, q, 'lf_eval') for q in order])
    same_seq = [q for q in order if preds[JEV][q]['selected_row_ids'] == preds[CE][q]['selected_row_ids']]
    same_set = [q for q in order if set(preds[JEV][q]['selected_row_ids']) == set(preds[CE][q]['selected_row_ids'])]
    same_ctx = [q for q in order if preds[JEV][q]['provisions'] == preds[CE][q]['provisions']]
    same_ans = [q for q in order if preds[JEV][q]['answer'] == preds[CE][q]['answer']]
    jev_cached = [q for q in order if preds[JEV][q]['generation_trace'].get('cached')]
    ce_cached = [q for q in order if preds[CE][q]['generation_trace'].get('cached')]
    jev_cached_ctx_ce_fixed = [q for q in jev_cached if preds[JEV][q]['provisions'] == preds[CE][q]['provisions']]
    jev_cached_ctx_ce_raw_only = [q for q in jev_cached if q not in jev_cached_ctx_ce_fixed and preds[JEV][q]['provisions'] == preds['parser_ce_raw'][q]['provisions']]
    cat = {}
    idx = {q: i for i, q in enumerate(order)}
    setq = set(same_set)
    groups_cat = {'identical_selected_set': [q for q in order if q in setq],
                  'different_set_same_f1': [q for q in order if q not in setq and abs(dF[idx[q]]) <= TIE],
                  'f1_changed': [q for q in order if q not in setq and abs(dF[idx[q]]) > TIE]}
    for name, qs in groups_cat.items():
        d = [dL[idx[q]] for q in qs]
        cat[name] = {'questions': len(qs), 'contribution_to_mean_lf_points': 100 * sum(d) / len(order),
                     'lf_up_tie_down': [int(sum(x > TIE for x in d)), int(sum(abs(x) <= TIE for x in d)), int(sum(x < -TIE for x in d))]}
    res['RM09_RM24_lf_and_reuse'] = {
        'pearson_r_deltaF1_deltaLF': float(np.corrcoef(dF, dL)[0, 1]),
        'decomposition_by_selection_change': cat,
        'same_selected_row_sequence': len(same_seq), 'same_selected_row_set': len(same_set),
        'same_generation_context_string': len(same_ctx), 'identical_answer_text': len(same_ans),
        'jev_generation_cache_hits': len(jev_cached), 'ce_fixed_generation_cache_hits': len(ce_cached),
        'jev_cache_hits_same_context_as_ce_fixed': len(jev_cached_ctx_ce_fixed),
        'jev_cache_hits_same_context_as_ce_raw_only': len(jev_cached_ctx_ce_raw_only),
        'lf_diff_zero_on_same_context': all(abs(dL[idx[q]]) <= TIE for q in same_ctx),
        'questions_with_answer_difference': len(order) - len(same_ans),
        'lf_prompt_criteria_excerpt': js(LF_PROMPT)['criteria'].strip().splitlines()[-1],
    }

    # ---------------- RM-25: judge audit provenance; >800-char answers ----------------
    pairs = cache_pairs = same_digest = 0
    for q in order:
        for i, a in enumerate(ARMS):
            for b in ARMS[i + 1:]:
                if preds[a][q]['answer'] == preds[b][q]['answer']:
                    pairs += 1
                    ta, tb = lf[a][q]['trace'], lf[b][q]['trace']
                    ta = ta[0] if isinstance(ta, list) else ta
                    tb = tb[0] if isinstance(tb, list) else tb
                    same_digest += ta.get('request_digest') == tb.get('request_digest')
                    cache_pairs += bool(ta.get('cached') or tb.get('cached'))
    res['RM25_judge_and_clip'] = {
        'identical_answer_pairs': pairs, 'pairs_same_request_digest': same_digest, 'pairs_with_cached_judge_response': cache_pairs,
        'stored_audit': js(REPRO / 'identical-answer-judge-audit.json'),
        'answers_over_800_chars': {a: sum(len(preds[a][q]['answer']) > 800 for q in order) for a in ARMS},
    }

    # ---------------- RM-17 / RM-30: usage by stage and call structure ----------------
    usage = {}
    a5 = {(r['arm'], r['query_id']): r for r in jl(PREP / 'A5' / 'question-resources.jsonl')}
    for a in (CE, JEV):
        tr = [t for q in order for t in preds[a][q]['selection_traces']]
        usage[a] = {'selection_calls': len(tr), 'selection_calls_per_question': len(tr) / len(order),
                    'selection_input_tokens_per_call': float(np.mean([t['usage']['input_tokens'] for t in tr])),
                    'selection_output_tokens_per_call': float(np.mean([t['usage']['output_tokens'] for t in tr])),
                    'selection_input_tokens_per_question': sum(t['usage']['input_tokens'] for t in tr) / len(order),
                    'generation_input_tokens_per_question': float(np.mean([preds[a][q]['generation_trace']['usage']['input_tokens'] for q in order])),
                    'context_tokens_per_question': float(np.mean([a5[(a, q)]['context_tokens'] for q in order]))}
        usage[a]['context_share_of_generation_input_pct'] = 100 * usage[a]['context_tokens_per_question'] / usage[a]['generation_input_tokens_per_question']
    sel_diff = [sum(t['usage']['input_tokens'] for t in preds[JEV][q]['selection_traces']) - sum(t['usage']['input_tokens'] for t in preds[CE][q]['selection_traces']) for q in order]
    usage['selection_input_tokens_per_question_diff_jev_minus_ce'] = {'mean': float(np.mean(sel_diff)), 'median': float(np.median(sel_diff))}
    usage['mapping'] = 'each condition prediction row stores its own selection_traces; usage is the recorded usage of the original call (cached rows included)'
    prov = PROVIDERS.read_text()
    usage['call_latency_semantics'] = {
        'providers_py_sha256': sha(use(PROVIDERS)),
        'matches_runtime_settings_record': sha(PROVIDERS) == js(REPRO / 'runtime-settings.json')['source_sha256']['src/legal_rag_jev/providers.py'],
        'timer_started_before_semaphore': prov.index('start = time.perf_counter()') < prov.index('async with self.semaphore'),
        'interpretation': 'trace latency_ms includes waiting for the concurrency semaphore and retry back-off; not a pure call time',
    }
    usage['parametric_calls'] = len(jl(REPRO / 'parametric.jsonl'))
    res['RM17_RM30_usage'] = usage

    # ---------------- RM-18 / RM-19 / RM-20 / RM-21: latency sample ----------------
    raw = jl(LAT / 'raw.jsonl')
    meas = [r for r in raw if not r['warmup']]
    sample = sorted({r['query_id'] for r in meas})
    jv = [r for r in meas if r['method'] == 'jev']
    ov = [r['top10_set_overlap'] for r in jv]
    summ = js(LAT / 'summary.json')
    proto = js(LAT / 'protocol.json')
    comp = js(LAT / 'completed.json')
    perpair = {}
    for m in ('ce', 'jev'):
        cells = defaultdict(list)
        for r in meas:
            if r['method'] == m:
                cells[r['query_id']].append(r['wall_clock_ms'] / r['pairs'])
        perpair[m] = float(np.mean([np.mean(v) for v in cells.values()]))
    jcache = sorted((REPRO / 'jev-cache').glob('*.json'))
    mt = [p.stat().st_mtime for p in jcache]
    res['RM18_latency_sample_quality'] = {
        'questions': len(sample), 'hop_counts': dict(Counter(str(metrics[CE][q]['n_hops']) for q in sample)),
        'diff_points_descriptive': {m: 100 * float(np.mean([val(JEV, q, m) - val(CE, q, m) for q in sample])) for m in ('f1', 'lf_eval', 'token_f1')},
        'full_226_diff_points': {m: 100 * float(np.mean([val(JEV, q, m) - val(CE, q, m) for q in order])) for m in ('f1', 'lf_eval', 'token_f1')}}
    res['RM19_overlap_and_dates'] = {
        'jev_measured_runs': len(jv), 'overlap_mean': float(np.mean(ov)), 'overlap_min': min(ov),
        'overlap_p10_linear': float(np.quantile(ov, 0.10)), 'runs_overlap_eq_1': sum(x == 1.0 for x in ov),
        'runs_overlap_le_0_85': sum(x <= 0.85 + 1e-12 for x in ov), 'runs_identical_order': sum(r['top10_same_as_quality_run'] for r in jv),
        'raw_fields': sorted(meas[0].keys() | jv[0].keys()), 'raw_has_top10_row_ids': any('top10_row_ids' in r for r in raw),
        'latency_protocol_created_utc': proto['created_at_utc'], 'latency_completed_utc': comp['completed_at_utc'],
        'quality_jev_cache_mtime_utc': [datetime.fromtimestamp(min(mt), timezone.utc).isoformat(), datetime.fromtimestamp(max(mt), timezone.utc).isoformat()],
        'quality_jev_cache_files': len(jcache),
        'date_source_note': 'quality-run date from file-system modification times of jev-cache files (no per-call timestamp stored)'}
    pairs_sum = sum(r['pairs'] for r in jv)
    cost = sum(r['cost_usd'] for r in jv)
    res['RM20_RM21_latency_units'] = {
        'per_pair_ms_recomputed': perpair, 'per_pair_ms_stored': {m: summ['per_pair_ms'][m]['mean'] for m in ('ce', 'jev')},
        'within_question_cv_stored': summ['within_question_cv'], 'concurrency_quality_run': js(REPRO / 'runtime-settings.json')['settings']['concurrency'],
        'concurrency_latency_run': proto['jev']['concurrency'], 'p95_definition': 'p95 of 60 per-question 3-run means',
        'jev_cost_usd_measured': cost, 'jev_pairs_measured': pairs_sum,
        'cost_per_question_run_usd': cost / len(jv), 'cost_per_1000_pairs_usd': 1000 * cost / pairs_sum,
        'per_question_ms_stored': summ['per_question_ms'], 'jev_minus_ce_ms_stored': summ['jev_minus_ce_ms']}

    # ---------------- RM-22: unmapped gold strings ----------------
    gold = jl(GOLD)
    corpus = jl(CORPUS)
    texts = set(r['hierarchy'] + r['content'] for r in corpus)
    byh = defaultdict(list)
    for r in corpus:
        byh[r['hierarchy']].append(r['hierarchy'] + r['content'])
    un = {}
    affected = set()
    for g in gold:
        for p, u in zip(g['provisions'], g['unit_ids']):
            if u in g['unavailable_unit_ids']:
                un.setdefault(u, p)
                affected.add(g['query_id'])
    hiers = sorted(byh, key=len, reverse=True)
    same_h = prefix = newline_items = ws = 0
    for u, p in un.items():
        h = next((x for x in hiers if p.startswith(x)), None)
        if h:
            same_h += 1
            if any(p != t and p.startswith(t) for t in byh[h]):
                prefix += 1
        if re.search(r'\n\s*\d+\.', p):
            newline_items += 1
        if re.sub(r'\s+', '', p) in {re.sub(r'\s+', '', t) for t in byh.get(h, [])}:
            ws += 1
    res['RM22_unmapped_gold'] = {'unique_unmapped_gold': len(un), 'affected_questions': len(affected),
                                 'corpus_row_with_same_hierarchy': same_h, 'corpus_row_is_proper_prefix_of_gold': prefix,
                                 'gold_contains_newline_numbered_items': newline_items, 'resolved_by_whitespace_normalisation': ws,
                                 'exact_in_corpus': sum(p in texts for p in un.values())}

    # ---------------- outputs ----------------
    res['inputs_sha256'] = dict(sorted(INPUTS.items()))
    res['script_sha256'] = sha(Path(__file__))
    (OUT / 'revision-analysis.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k not in ('inputs_sha256', 'verification')}, ensure_ascii=False, indent=1, default=float)[:20000])
    print('verification all exact:', res['verification']['all_exact'], res['verification']['n'])


if __name__ == '__main__':
    main()

"""Paired comparison of FR end-to-end answers vs unfiltered arms (no model calls)."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from legal_rag_jev.io import read_json, read_jsonl, write_json, file_hash  # noqa: E402
from legal_rag_jev.koblex_analysis import paired_bootstrap  # noqa: E402

S, F = Path('results/koblex-reproduction-v1'), Path('results/koblex-filtering-v1/e2e')
ARM = {'ce': 'parser_ce_fixed', 'jev': 'parser_jev_fixed'}
groups = read_json('research/koblex_source_audit_20261108.json')['source_and_gold_groups']['groups']


def load(metrics, lf):
    m = {r['query_id']: r for r in read_jsonl(metrics)}
    l = {r['query_id']: r['score'] for r in read_jsonl(lf)}
    return {q: {'f1': m[q]['retrieval']['f1'], 'recall': m[q]['retrieval']['recall'],
                'precision': m[q]['retrieval']['precision'], 'em': m[q]['retrieval']['em'],
                'gold_set_coverage': m[q]['retrieval']['gold_set_coverage'],
                'token_f1': m[q]['token_f1'], 'lf_eval': l[q]} for q in m}


data = {}
for s, arm in ARM.items():
    data[s + '_r'] = load(S / 'metrics' / arm / 'metrics.jsonl', S / 'lf-eval' / arm / 'metrics.jsonl')
    data[s + '_fr'] = load(F / 'metrics' / f'{s}_fr' / 'metrics.jsonl', F / 'lf-eval' / f'{s}_fr' / 'metrics.jsonl')
order = list(data['ce_r'])
checks = {}
for s in ARM:
    preds = {r['query_id']: r for r in read_jsonl(F / 'predictions' / f'{s}_fr.jsonl')}
    same = [q for q in order if preds[q]['answer_source'] != 'regenerated']
    checks[s] = {'reused_answers': len(same), 'regenerated': len(order) - len(same),
                 'reused_lf_identical': all(abs(data[s + '_fr'][q]['lf_eval'] - data[s + '_r'][q]['lf_eval']) < 1e-12 for q in same),
                 'kept_items_mean': sum(len(p['provisions']) for p in preds.values()) / len(order),
                 'context_chars_mean': sum(len('\n'.join(p['provisions'])) for p in preds.values()) / len(order),
                 'zero_evidence': sum(not p['provisions'] for p in preds.values())}
metrics = ['f1', 'precision', 'recall', 'em', 'gold_set_coverage', 'token_f1', 'lf_eval']
means = {c: {m: 100 * sum(d[q][m] for q in order) / len(order) for m in metrics} for c, d in data.items()}
comp = {}
for a, b in [('ce_fr', 'ce_r'), ('jev_fr', 'jev_r'), ('jev_fr', 'ce_fr'), ('jev_fr', 'ce_r')]:
    comp[f'{a}-{b}'] = {}
    for m in metrics:
        r = paired_bootstrap([data[a][q][m] - data[b][q][m] for q in order], [groups[q] for q in order])
        comp[f'{a}-{b}'][m] = {'estimate': 100 * r['mean_difference'], 'ci95': [100 * v for v in r['ci95']]}
out = {'status': 'EXPLORATORY_E2E_FILTERING_CV_OPERATING_POINT', 'questions': len(order), 'checks': checks,
       'means': means, 'paired_bootstrap_points': comp,
       'note': 'tau chosen by 5-fold group CV on evidence F1 only (before answers); 10,000 cluster resamples, seed 20261108; not a non-inferiority test'}
write_json(Path('results/koblex-filtering-v1/e2e-summary.json'), out)
print(json.dumps(checks, indent=1))
for c, v in means.items(): print(c, {k: round(x, 2) for k, x in v.items()})
for c, v in comp.items():
    for m, r in v.items(): print(c, m, round(r['estimate'], 2), [round(x, 2) for x in r['ci95']])

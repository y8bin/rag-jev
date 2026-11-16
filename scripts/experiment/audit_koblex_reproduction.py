"""Offline integrity audit of every completed reproduction artifact."""
import json
import math
from pathlib import Path
from datetime import datetime,timezone
import run_koblex_reproduction as s
from legal_rag_jev.io import read_json,read_jsonl,file_hash,write_json

root=s.ROOT
legacy=read_json(root/'legacy-preservation.json')['files']
assert all(file_hash(p)==h for p,h in legacy.items()),'Legacy results modified'
lock=read_json(root/'protocol-lock.json')['signature']
assert all(file_hash(p)==h for p,h in lock['files'].items()),'Frozen source changed'
runtime=read_json(root/'runtime-settings.json')
assert all(file_hash(p)==h for p,h in runtime['source_sha256'].items()),'Shared provider implementation changed'
questions=s.input_questions();ids=[q['id'] for q in questions]
assert len(ids)==len(set(ids))==226
corpus=[r['hierarchy']+r['content'] for r in read_jsonl(s.CORPUS)]
assert len(corpus)==233544
parametric=read_jsonl(root/'parametric.jsonl');candidates=read_jsonl(root/'candidates.jsonl')
assert [r['query_id'] for r in parametric]==ids==[r['query_id'] for r in candidates]
rankings={kind:read_jsonl(root/f'ranking-{kind}.jsonl') for kind in ('ce','jev')}
assert all([r['query_id'] for r in rows]==ids for rows in rankings.values())
total=0;max_length=0;truncated=0
for i,qid in enumerate(ids):
    pools=candidates[i]['pools']
    assert len(pools)==len(parametric[i]['subs'])
    for j,pool in enumerate(pools):
        rows=pool['row_ids'];assert len(rows)==len(set(rows))==100
        assert all(type(n)==int and 0<=n<len(corpus) for n in rows)
        total+=len(rows)
        for kind in ('ce','jev'):
            result=rankings[kind][i]['pools'][j]
            assert result['candidate_row_ids']==rows
            scores=result['scores'];assert len(scores)==100 and all(math.isfinite(v) and 0<=v<=1 for v in scores)
            order=sorted(range(100),key=lambda k:(scores[k],corpus[rows[k]]),reverse=True)
            assert result['top10_row_ids']==[rows[k] for k in order[:10]]
            if kind=='ce':
                lengths=result['input_lengths'];max_length=max(max_length,max(lengths))
                truncated+=sum(n>8192 for n in lengths)
predictions={arm:read_jsonl(root/'predictions'/f'{arm}.jsonl') for arm in s.ARMS}
raw_fixed_different=0;raw_fixed_sets_different=0;raw_fixed_answers_different=0;invalid_choices=0
for arm,rows in predictions.items():
    assert [r['query_id'] for r in rows]==ids
    kind='jev' if arm=='parser_jev_fixed' else 'ce'
    for i,row in enumerate(rows):
        pools=[p['top10_row_ids'] for p in rankings[kind][i]['pools']]
        assert row['choices']==[s.choice_from(text) for text in row['selection_raw_outputs']]
        assert row['selected_row_ids']==s.selected_from(pools,row['choices'],raw=arm=='parser_ce_raw')
        assert row['provisions']==[corpus[k] for k in row['selected_row_ids']]
        assert row['status']=='ok'
        assert row['generation_trace']['returned_model']==lock['generation']['model']
        assert all(t['returned_model']==lock['generation']['model'] for t in row['selection_traces'])
        if arm!='parser_ce_raw':
            invalid_choices+=sum(not (text.split('Answer:')[-1].strip().isdigit() and 0<=int(text.split('Answer:')[-1].strip())<=9) for text in row['selection_raw_outputs'])
    metrics=read_json(root/'metrics'/arm/'summary.json')
    assert metrics['questions']==226 and metrics['prediction_sha256']==file_hash(root/'predictions'/f'{arm}.jsonl')
    lf=read_json(root/'lf-eval'/arm/'summary.json')
    assert lf['completed'] and lf['questions']==226 and lf['signature']['prediction_sha256']==metrics['prediction_sha256']
    assert lf['signature']['model']=='gpt-4o-2024-08-06' and lf['signature']['deepeval']=='4.3.3'
    assert lf['signature']['gold_sha256']==metrics['gold_sha256']==file_hash(s.GOLD)
    lf_rows=read_jsonl(root/'lf-eval'/arm/'metrics.jsonl')
    assert [r['query_id'] for r in lf_rows]==ids and all(0<=r['score']<=1 for r in lf_rows)
for a,b in zip(predictions['parser_ce_raw'],predictions['parser_ce_fixed']):
    assert a['choices']==b['choices'] and a['selection_raw_outputs']==b['selection_raw_outputs']
    raw_fixed_different+=a['provisions']!=b['provisions']
    raw_fixed_sets_different+=set(a['provisions'])!=set(b['provisions'])
    raw_fixed_answers_different+=a['answer']!=b['answer']
key=read_jsonl(root/'human-review/private/condition-key.jsonl')
assert len(key)==180
for reviewer in ('A','B'):
    rows=read_jsonl(root/f'human-review/reviewer-{reviewer}.jsonl')
    assert len(rows)==180 and {r['review_id'] for r in rows}=={r['review_id'] for r in key}
    assert all('arm' not in r and 'method' not in r for r in rows)
    assert all(r['correctness_0_1_2'] is None and r['selected_evidence_support_0_1_2'] is None and r['unsupported_legal_claim'] is None for r in rows)
report={'status':'PASS_AUTOMATED_ARTIFACT_INTEGRITY','audited_at_utc':datetime.now(timezone.utc).isoformat(),
        'legacy_files_unchanged':len(legacy),'questions':226,'corpus_rows':len(corpus),
        'parametric_provisions':sum(len(r['subs']) for r in parametric),'candidate_row_pairs_per_ranker':total,
        'CE_maximum_input_tokens':max_length,'CE_truncated_pairs':truncated,
        'CE_raw_fixed_different_provision_lists':raw_fixed_different,
        'CE_raw_fixed_different_provision_sets':raw_fixed_sets_different,
        'CE_raw_fixed_different_answers':raw_fixed_answers_different,
        'invalid_LLM_choice_fallbacks_fixed_arms':invalid_choices,
        'generated_answers':226*len(s.ARMS),'LF_evaluations':226*len(s.ARMS),
        'empty_generated_answers':sum(not r['answer'].strip() for rows in predictions.values() for r in rows),
        'human_review_answers_prepared':180,'human_judgments_completed':0,
        'audit_script_sha256':file_hash(__file__)}
write_json(root/'integrity-audit.json',report)
print(json.dumps(report,ensure_ascii=False,indent=2))

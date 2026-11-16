"""Validate real independent reviews, report agreement, export disagreements.

Never invents ratings or changes submitted review files. Bootstrap dependence
groups use the same source-and-gold grouping as the automated study.
"""
import argparse
from pathlib import Path
import numpy as np
from legal_rag_jev.io import read_json,read_jsonl,write_json,write_jsonl,file_hash

FIELDS={'correctness_0_1_2':3,'selected_evidence_support_0_1_2':3,'unsupported_legal_claim':2}

def validate(submitted,template):
    expected={r['review_id']:r for r in template}
    if len(submitted)!=len(expected) or len({r.get('review_id') for r in submitted})!=len(expected):
        raise ValueError('Every review ID must appear exactly once')
    result={}
    editable=set(FIELDS)|{'notes'}
    for row in submitted:
        rid=row.get('review_id')
        if rid not in expected:raise ValueError('Unknown review ID')
        base=expected[rid]
        if {k:v for k,v in row.items() if k not in editable}!={k:v for k,v in base.items() if k not in editable}:
            raise ValueError('Question, answer, evidence or metadata was edited')
        for field,categories in FIELDS.items():
            value=row.get(field)
            if field=='unsupported_legal_claim':
                valid=type(value)==bool
            else:valid=type(value)==int and 0<=value<categories
            if not valid:raise ValueError('Missing or invalid human rating: '+field)
        if not isinstance(row.get('notes'),str):raise ValueError('Review notes must be text')
        result[rid]=row
    return result

def agreement(first,second,categories):
    a=np.asarray(first,dtype=int);b=np.asarray(second,dtype=int)
    if not len(a) or len(a)!=len(b):raise ValueError('Nonempty paired ratings required')
    table=np.zeros((categories,categories),float)
    np.add.at(table,(a,b),1)
    probability=table/table.sum()
    weights=np.abs(np.arange(categories)[:,None]-np.arange(categories)[None,:])/(categories-1)
    expected=probability.sum(axis=1)[:,None]*probability.sum(axis=0)[None,:]
    denominator=float((weights*expected).sum())
    kappa=1-float((weights*probability).sum())/denominator if denominator>0 else None
    return {'n':len(a),'raw_agreement':float((a==b).mean()),
            'kappa':kappa,'weighting':'linear' if categories>2 else 'unweighted',
            'contingency_table':table.astype(int).tolist()}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--first',required=True);parser.add_argument('--second',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--packet',default='results/koblex-reproduction-v1/human-review')
    args=parser.parse_args()
    destination=Path(args.output)
    if destination.exists():raise ValueError('Output already exists; preserve prior agreement analysis')
    packet=Path(args.packet)
    a=validate(read_jsonl(args.first),read_jsonl(packet/'reviewer-A.jsonl'))
    b=validate(read_jsonl(args.second),read_jsonl(packet/'reviewer-B.jsonl'))
    mapping={r['review_id']:r for r in read_jsonl(packet/'private/condition-key.jsonl')}
    if set(a)!=set(b) or set(a)!=set(mapping):raise ValueError('Both independent reviews must cover exactly the prepared packet')
    ids=sorted(a)
    groups=read_json('research/koblex_source_audit_20261108.json')['source_and_gold_groups']['groups']
    ordered=sorted({groups[mapping[rid]['query_id']] for rid in ids})
    buckets=[np.asarray([i for i,rid in enumerate(ids) if groups[mapping[rid]['query_id']]==group]) for group in ordered]
    rng=np.random.default_rng(20261109)
    draws=rng.integers(0,len(buckets),size=(2000,len(buckets)))
    result={}
    for field,categories in FIELDS.items():
        first=np.asarray([a[r][field] for r in ids],int);second=np.asarray([b[r][field] for r in ids],int)
        report=agreement(first,second,categories);kappas=[];agreements=[]
        for draw in draws:
            indices=np.concatenate([buckets[i] for i in draw])
            sample=agreement(first[indices],second[indices],categories)
            agreements.append(sample['raw_agreement'])
            if sample['kappa'] is not None:kappas.append(sample['kappa'])
        report['raw_agreement_ci95']=np.quantile(agreements,[.025,.975]).tolist()
        report['kappa_ci95']=np.quantile(kappas,[.025,.975]).tolist() if kappas else None
        report['kappa_defined_resamples']=len(kappas)
        result[field]=report
    disagreements=[]
    for rid in ids:
        fields=[f for f in FIELDS if a[rid][f]!=b[rid][f]]
        if fields:
            disagreements.append({'review_id':rid,'question':a[rid]['question'],'answer':a[rid]['answer'],
                'selected_provisions':a[rid]['selected_provisions'],'reference_answer':a[rid]['reference_answer'],
                'reference_provisions':a[rid]['reference_provisions'],'disagreement_fields':fields,
                'reviewer_A':{f:a[rid][f] for f in FIELDS},'reviewer_B':{f:b[rid][f] for f in FIELDS},
                'reviewer_A_notes':a[rid]['notes'],'reviewer_B_notes':b[rid]['notes'],
                'adjudicated':{f:None for f in FIELDS},'adjudication_reason':None})
    write_json(destination/'agreement.json',{'fields':result,'clusters':len(buckets),'bootstrap_repetitions':2000,
        'seed':20261109,'first_sha256':file_hash(args.first),'second_sha256':file_hash(args.second),
        'status':'REAL_INDEPENDENT_REVIEWS_VALIDATED_ADJUDICATION_PENDING','disagreements':len(disagreements)})
    write_jsonl(destination/'adjudication-tasks.jsonl',disagreements)

if __name__=='__main__':main()

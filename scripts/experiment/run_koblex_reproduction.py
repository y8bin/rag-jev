"""Isolated, resumable ParSeR reproduction and CE-only replacement by Jev.

Never modifies the legacy Vector experiment. All paid calls share its budget.
Upstream prompts/parsers are loaded from the audited immutable source snapshot.
"""
from __future__ import annotations
import os
os.environ['PYTORCH_ENABLE_MPS_FALLBACK']='0'
os.environ['HF_HUB_OFFLINE']='1'
import sys
from pathlib import Path
sys.path.insert(0,str(Path('.cache/koblex-reproduction-deps').resolve()))
import argparse
import ast
import asyncio
import json
import math
import random
import re
import runpy
import statistics
import time
from datetime import datetime, timezone
import numpy as np
from legal_rag_jev.config import Config, environment_file_scope, provider_identity, pricing
from legal_rag_jev.io import read_json, read_jsonl, write_json, write_jsonl, file_hash, digest, environment_manifest
from legal_rag_jev.providers import Transport, Providers
from legal_rag_jev.koblex import evaluate_predictions

ROOT=Path('results/koblex-reproduction-v1')
UP=Path('.omo/evidence/koblex-design-20261108/upstream')
QA=UP/'experiments/source/koblex.jsonl'
CORPUS=Path('data/koblex/downloads/statute.jsonl')
GOLD='data/koblex/prepared-v1/gold.jsonl'
ARMS=('parser_ce_raw','parser_ce_fixed','parser_jev_fixed')
SCRIPT=Path(__file__)

def upstream_helpers():
    names={'extract_first_list','parse_list_block','_fix_common_typos','quoted_items','escape_quotes'}
    tree=ast.parse((UP/'experiments/parser/openai/utils.py').read_text())
    scope={'ast':ast,'re':re,'json':json,'List':list,'Optional':__import__('typing').Optional}
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    exec(compile(ast.Module(body=selected,type_ignores=[]),'audited-upstream-parsers','exec'),scope)
    return scope

def parse_subs(text):
    helper=upstream_helpers()
    block=helper['extract_first_list'](text)
    if block is None: return []
    result=helper['escape_quotes'](helper['parse_list_block'](block))
    if not isinstance(result,list) or any(not isinstance(x,str) for x in result):
        raise ValueError('Parametric provisions must be a string list')
    return result

def choice_from(text):
    s=text.split('Answer:')[-1].strip()
    return int(s) if s.isdigit() and 0<=int(s)<=9 else 0

def selected_from(lists,choices,raw=False):
    if len(lists)!=len(choices): raise ValueError('Selection count mismatch')
    return [lists[0 if raw else i][choice] for i,choice in enumerate(choices)]

def prompt(name,**values):
    module=runpy.run_path(str(UP/f'experiments/parser/prompts/{name}.py'))
    return module['SYSTEM_PROMPT']+'\n\n'+module['INSTRUCTION_PROMPT'].substitute(**values)

def append(path,row):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as f:
        f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())

def checkpoint(name):
    path=ROOT/name
    rows=read_jsonl(path) if path.exists() else []
    ids=[r['query_id'] for r in rows]
    if len(set(ids))!=len(ids): raise ValueError('Duplicate checkpoint IDs: '+name)
    return path,{r['query_id']:r for r in rows}

def input_questions():
    # Explicit whitelist: no gold answer, contexts, n_hops or English fields downstream.
    return [{k:r[k] for k in ('id','background','question')} for r in read_jsonl(QA)]

def signature(cfg):
    files=[SCRIPT,QA,CORPUS,Path(GOLD),Path('research/prompts/koblex_lf_eval.json')]
    files+=list((UP/'experiments/parser').rglob('*.py'))
    return {'schema':1,'purpose':'ParSeR reproduction and replacement of CE scoring only',
      'observed_prior_test_results':True,'claim':'post-audit paired replication; not untouched confirmatory test',
      'arms':ARMS,'primary_comparison':['parser_jev_fixed','parser_ce_fixed'],
      'raw_reference':'parser_ce_raw preserves upstream contexts_list[0][choice] bug',
      'correction':'contexts_list[subquery_index][choice]; same prompts and choices; no gold used',
      'input_question_ce':'original question only','input_document_ce':'hierarchy + content, no JSON',
      'input_question_jev':'same original question only','input_document_jev':'same plain hierarchy + content',
      'jev_instructions':'Rank by relevance: does the candidate statutory passage directly support answering the question?',
      'retriever':'bm25s 0.2.14; corpus stopwords=en; query defaults; k=100 per parametric provision',
      'top_n_before_llm_selection':10,'generation':provider_identity('generation',cfg.generation_backend),
      'jev':provider_identity('jev',cfg.jev_backend),'ce':provider_identity('ce',cfg.ce_backend),
      'ce_activation':'explicit Sigmoid','ce_max_length':'upstream model/tokenizer default',
      'ce_batch_size':50,'ce_device':'mps','ce_dtype':'float32',
      'deployment_difference':'original CUDA versus available MPS; package versions pinned here, historical versions unknown',
      'generation_settings':{'temperature':0.01,'top_p':0.9,'max_tokens':2000,'user_message_only':True},
      'sampling':'all official 226; no result-based K/N or instruction tuning',
      'budget':{'ledger':cfg.budget_ledger,'total':cfg.budget_limit_usd,'openai':cfg.budget_openai_limit_usd},
      'prices':pricing(),'files':{str(p):file_hash(p) for p in sorted(set(files))},
      'dependencies':environment_manifest()['dependencies']}

def freeze(cfg):
    path=ROOT/'protocol-lock.json';s=signature(cfg)
    if path.exists():
        if read_json(path)['signature_hash']!=digest(s):raise ValueError('Reproduction protocol changed')
    else:write_json(path,{'created_at_utc':datetime.now(timezone.utc).isoformat(),'signature':s,'signature_hash':digest(s)})
    return s

async def chat(cfg,transport,text):
    identity=provider_identity('generation',cfg.generation_backend)
    body={'model':identity['model'],'messages':[{'role':'user','content':text}],
          'temperature':0.01,'top_p':0.9,'max_tokens':2000,'store':False}
    key=digest({'identity':identity,'body':body})
    path=ROOT/'api-cache'/(key+'.json')
    if path.exists():
        saved=read_json(path)
        if saved['key']!=key:raise ValueError('Cache mismatch')
        return saved['text'],{**saved['trace'],'cached':True}
    result=await transport.request('generation',identity,'/chat/completions',body)
    c=result.value['choices'][0]
    write_json(ROOT/'responses'/(key+'.json'),{'key':key,'response':result.value,'trace':result.trace})
    if c['finish_reason']!='stop' or not isinstance(c['message']['content'],str):
        raise ValueError('Incomplete generation; preserved raw response, no silent empty success')
    text=c['message']['content'].strip()
    write_json(path,{'key':key,'text':text,'trace':result.trace})
    return text,result.trace

async def parametric(cfg):
    path,done=checkpoint('parametric.jsonl');transport=Transport(cfg)
    try:
        for q in input_questions():
            if q['id'] in done:continue
            text,trace=await chat(cfg,transport,prompt('parametric_provision',background=q['background'],question=q['question']))
            subs=parse_subs(text)
            append(path,{'query_id':q['id'],'subs':subs,'raw_output':text,'trace':trace,'parse_empty':not subs})
            print('parametric',q['id'],len(subs),flush=True)
    finally:await transport.close()

def retrieve():
    import bm25s
    path,done=checkpoint('candidates.jsonl')
    subs={r['query_id']:r['subs'] for r in read_jsonl(ROOT/'parametric.jsonl')}
    questions=input_questions()
    if set(subs)!={q['id'] for q in questions}:raise ValueError('Parametric stage incomplete')
    corpus=[r['hierarchy']+r['content'] for r in read_jsonl(CORPUS)]
    index=ROOT/'bm25-index'
    if index.exists():retriever=bm25s.BM25.load(str(index),mmap=True,load_corpus=False)
    else:
        retriever=bm25s.BM25()
        retriever.index(bm25s.tokenize(corpus,stopwords='en',show_progress=False),show_progress=False)
        retriever.save(str(index))
    for q in questions:
        if q['id'] in done:continue
        pools=[]
        for sq in subs[q['id']]:
            ids,scores=retriever.retrieve(bm25s.tokenize([sq],show_progress=False),k=100,show_progress=False)
            pools.append({'parametric_provision':sq,'row_ids':ids[0].tolist(),'bm25_scores':scores[0].tolist()})
        append(path,{'query_id':q['id'],'pools':pools})
        print('retrieved',q['id'],len(pools),flush=True)

def load_ce():
    import torch
    from sentence_transformers import CrossEncoder
    if not torch.backends.mps.is_available():raise RuntimeError('MPS required')
    model=CrossEncoder('dragonkue/bge-reranker-v2-m3-ko',revision='2aca5884ecac490192af9ebd86836d9073d826cd',
         device='mps',activation_fn=torch.nn.Sigmoid(),cache_folder='.cache/models',local_files_only=True)
    info={'device':str(model.device),'dtype':str(next(model.parameters()).dtype),
          'max_length':model.max_length,'tokenizer_max_length':model.tokenizer.model_max_length}
    write_json(ROOT/'ce-runtime.json',info);print(info,flush=True)
    return model

def rank_ce():
    model=load_ce()
    path,done=checkpoint('ranking-ce.jsonl')
    questions={q['id']:q for q in input_questions()}
    corpus=[r['hierarchy']+r['content'] for r in read_jsonl(CORPUS)]
    import torch
    for row in read_jsonl(ROOT/'candidates.jsonl'):
        qid=row['query_id']
        if qid in done:continue
        pools=[]
        for pool in row['pools']:
            ids=pool['row_ids'];texts=[corpus[i] for i in ids]
            pairs=[(questions[qid]['question'],t) for t in texts]
            lengths=[len(model.tokenizer(a,b,truncation=False)['input_ids']) for a,b in pairs]
            torch.mps.synchronize();start=time.perf_counter()
            scores=np.asarray(model.predict(pairs,batch_size=50,show_progress_bar=False)).reshape(-1).tolist()
            torch.mps.synchronize();elapsed=(time.perf_counter()-start)*1000
            if len(scores)!=len(ids) or not all(math.isfinite(v) for v in scores):raise ValueError('Invalid CE scores')
            # Match upstream sorted(zip(scores,texts),reverse=True), including lexicographic ties.
            order=sorted(range(len(ids)),key=lambda i:(scores[i],texts[i]),reverse=True)
            pools.append({'top10_row_ids':[ids[i] for i in order[:10]],'candidate_row_ids':ids,'scores':scores,
                          'wall_clock_ms':elapsed,'input_lengths':lengths})
        append(path,{'query_id':qid,'pools':pools})
        print('ce-ranked',qid,flush=True)

async def rank_jev(cfg):
    path,done=checkpoint('ranking-jev.jsonl');transport=Transport(cfg)
    identity=provider_identity('jev',cfg.jev_backend)
    corpus=[r['hierarchy']+r['content'] for r in read_jsonl(CORPUS)]
    questions={q['id']:q for q in input_questions()}
    instructions='Rank by relevance: does the candidate statutory passage directly support answering the question?'
    async def one(q,text):
        body={'model':identity['model'],'state':{'query':q,'candidate':text},
              'questions':{'relevant':{'type':'noul','instructions':instructions}}}
        key=digest(body);cache=ROOT/'jev-cache'/(key+'.json')
        if cache.exists():
            saved=read_json(cache);return saved['score'],{**saved['trace'],'cached':True}
        r=await transport.request('jev',identity,'/v1/systemone',body)
        answer=r.value['answers']['relevant'];score=answer['noul']
        if answer['type']!='noul' or isinstance(score,bool) or not isinstance(score,(float,int)) or not math.isfinite(score) or not 0<=score<=1:
            raise ValueError('Invalid Jev score')
        if r.value.get('model')!=identity['model']:raise ValueError('Jev model mismatch')
        write_json(cache,{'score':score,'trace':r.trace,'response':r.value})
        return score,r.trace
    try:
        for row in read_jsonl(ROOT/'candidates.jsonl'):
            qid=row['query_id']
            if qid in done:continue
            # Reuse identical query/passage pairs across pools and duplicated corpus rows.
            unique=list(dict.fromkeys(corpus[i] for p in row['pools'] for i in p['row_ids']))
            start=time.perf_counter()
            # Bound active tasks, not merely network concurrency, to keep resume cheap.
            values={}
            for j in range(0,len(unique),4):
                results=await asyncio.gather(*(one(questions[qid]['question'],t) for t in unique[j:j+4]))
                values.update(zip(unique[j:j+4],results))
            pools=[]
            for p in row['pools']:
                ids=p['row_ids'];scores=[values[corpus[i]][0] for i in ids]
                order=sorted(range(len(ids)),key=lambda i:(scores[i],corpus[ids[i]]),reverse=True)
                pools.append({'top10_row_ids':[ids[i] for i in order[:10]],'candidate_row_ids':ids,'scores':scores})
            append(path,{'query_id':qid,'pools':pools,'unique_pairs':len(unique),
                         'quality_wall_clock_ms':(time.perf_counter()-start)*1000,
                         'traces':[v[1] for v in values.values()]})
            print('jev-ranked',qid,'unique pairs',len(unique),flush=True)
    finally:await transport.close()

async def select_and_answer(cfg):
    transport=Transport(cfg)
    corpus=[r['hierarchy']+r['content'] for r in read_jsonl(CORPUS)]
    questions=input_questions()
    rankings={kind:{r['query_id']:r for r in read_jsonl(ROOT/f'ranking-{kind}.jsonl')} for kind in ('ce','jev')}
    if any(set(rs)!={q['id'] for q in questions} for rs in rankings.values()):raise ValueError('Rankings incomplete')
    outputs={arm:checkpoint(arm+'.jsonl') for arm in ARMS}
    try:
        for q in questions:
            qid=q['id']
            for kind in ('ce','jev'):
                arms=ARMS[:2] if kind=='ce' else ARMS[2:]
                if all(qid in outputs[a][1] for a in arms):continue
                lists=[];choices=[];selection_traces=[];selection_outputs=[]
                for pool in rankings[kind][qid]['pools']:
                    ids=pool['top10_row_ids'];lists.append(ids)
                    candidates='\n'.join(f'{i}: {corpus[rid]}' for i,rid in enumerate(ids))
                    text,trace=await chat(cfg,transport,prompt('selection_retrieval',background=q['background'],question=q['question'],candidates=candidates))
                    choices.append(choice_from(text));selection_traces.append(trace);selection_outputs.append(text)
                for arm in arms:
                    path,done=outputs[arm]
                    if qid in done:continue
                    ids=selected_from(lists,choices,raw=arm=='parser_ce_raw')
                    provisions=[corpus[i] for i in ids]
                    text,trace=await chat(cfg,transport,prompt('question_answering',question=q['background']+q['question'],context_str='\n'.join(provisions)))
                    row={'query_id':qid,'answer':text.split('Answer:')[-1].strip(),'provisions':provisions,
                         'selected_row_ids':ids,'choices':choices,'selection_raw_outputs':selection_outputs,
                         'selection_traces':selection_traces,'generation_trace':trace,'status':'ok'}
                    append(path,row);done[qid]=row
                    print('answered',arm,qid,flush=True)
    finally:await transport.close()
    for arm in ARMS:
        rows=outputs[arm][1]
        write_jsonl(ROOT/'predictions'/f'{arm}.jsonl',[rows[q['id']] for q in questions])

def metrics():
    for arm in ARMS:
        target=ROOT/'metrics'/arm
        if not target.exists():evaluate_predictions(GOLD,str(ROOT/'predictions'/f'{arm}.jsonl'),str(target))
    write_json(ROOT/'computational-completion.json',{'status':'GENERATION_AND_DETERMINISTIC_METRICS_COMPLETE',
               'arms':{arm:len(read_jsonl(ROOT/'predictions'/f'{arm}.jsonl')) for arm in ARMS},
               'human_review':'PENDING_HUMAN_JUDGMENTS'})

def analyze():
    from legal_rag_jev.koblex_analysis import paired_bootstrap
    rows={a:read_jsonl(ROOT/'metrics'/a/'metrics.jsonl') for a in ARMS}
    order=[r['query_id'] for r in rows[ARMS[0]]]
    if len(order)!=226 or any([r['query_id'] for r in rs]!=order for rs in rows.values()):raise ValueError('All 226 paired rows required')
    groups=read_json('research/koblex_source_audit_20261108.json')['source_and_gold_groups']['groups']
    comparisons=[]
    for treatment,control in [('parser_jev_fixed','parser_ce_fixed'),('parser_ce_fixed','parser_ce_raw')]:
        for metric in ('f1','recall','em','gold_set_coverage','token_f1','lf_eval'):
            if metric=='lf_eval':
                files=[ROOT/'lf-eval'/a/'metrics.jsonl' for a in (treatment,control)]
                if not all(p.exists() for p in files):continue
                vals=[read_jsonl(p) for p in files]
                if any([r['query_id'] for r in rs]!=order for rs in vals):raise ValueError('LF incomplete')
                diffs=[a['score']-b['score'] for a,b in zip(*vals)]
            else:
                def value(r):return r[metric] if metric=='token_f1' else r['retrieval'][metric]
                diffs=[value(a)-value(b) for a,b in zip(rows[treatment],rows[control])]
            result=paired_bootstrap(diffs,[groups[q] for q in order])
            result.update(treatment=treatment,control=control,metric=metric,confirmatory=False)
            comparisons.append(result)
    summaries={a:read_json(ROOT/'metrics'/a/'summary.json') for a in ARMS}
    for a in ARMS:
        lf=ROOT/'lf-eval'/a/'summary.json'
        if lf.exists():summaries[a]['lf_eval']=read_json(lf)['lf_eval'];summaries[a]['lf_eval_status']='COMPLETE'
    write_json(ROOT/'analysis.json',{'status':'POST_AUDIT_REPLICATION_NOT_UNTOUCHED_TEST','summaries':summaries,'comparisons':comparisons,
             'legacy_test_exposure':True,'human_review':'PENDING','timing':'QUALITY_TIMES_NOT_UNCACHED_BENCHMARK',
             'notes':['Original model snapshots/package/hardware not fully reproducible; differences in protocol-lock.json.',
                      'Raw CE preserves upstream selection-index bug. Fixed CE and fixed Jev change only scoring.',
                      'No result-based tuning; missing gold remains in denominator.']})

def review():
    ids=set(read_json('research/koblex_source_audit_20261108.json')['human_review_sample']['ids'])
    gold={r['query_id']:r for r in read_jsonl(GOLD)};questions={q['id']:q for q in input_questions()}
    rows=[];key=[]
    for arm in ARMS:
        for p in read_jsonl(ROOT/'predictions'/f'{arm}.jsonl'):
            qid=p['query_id']
            if qid in ids:
                rows.append({'question':questions[qid]['background']+questions[qid]['question'],'answer':p['answer'],
                  'selected_provisions':p['provisions'],'reference_answer':gold[qid]['answer'],
                  'reference_provisions':gold[qid]['provisions'],'correctness_0_1_2':None,
                  'selected_evidence_support_0_1_2':None,'unsupported_legal_claim':None,'notes':'','private':(qid,arm)})
    random.Random(20261109).shuffle(rows)
    for i,row in enumerate(rows):
        qid,arm=row.pop('private');rid=f'PARSER-{i+1:03d}';row['review_id']=rid
        key.append({'review_id':rid,'query_id':qid,'arm':arm})
    if len(rows)!=180:raise ValueError('180 answers expected')
    destination=ROOT/'human-review'
    if destination.exists():return
    write_jsonl(destination/'private/condition-key.jsonl',key)
    for reviewer in ('A','B'):
        copy=rows.copy();random.Random(ord(reviewer)+20261109).shuffle(copy)
        write_jsonl(destination/f'reviewer-{reviewer}.jsonl',copy)
    write_json(destination/'manifest.json',{'answers':180,'independent_judgments_required':360,'status':'AWAITING_REAL_HUMANS'})

async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['freeze','parametric','retrieve','ce','jev','answers','metrics','lf-eval','analyze','review','budget','all'])
    args=parser.parse_args()
    with environment_file_scope('.env.koblex',{}):
        cfg=Config.load('configs/koblex-paper.yaml','.env.koblex')
        cfg=cfg.model_copy(update={'cache_dir':str(ROOT/'framework-cache')})
        if args.phase=='lf-eval':
            # Dedicated dependency environment; verify shared immutable sources and evaluator.
            lock=read_json(ROOT/'protocol-lock.json')['signature']
            for p,h in lock['files'].items():
                if file_hash(p)!=h:raise ValueError('Locked source changed: '+p)
            from legal_rag_jev.koblex_lf_eval import evaluate
            for arm in ARMS:print(await evaluate(cfg,GOLD,str(ROOT/'predictions'/f'{arm}.jsonl'),str(ROOT/'lf-eval'/arm)),flush=True)
            return
        freeze(cfg)
        phases=['parametric','retrieve','ce','jev','answers','metrics','analyze','review'] if args.phase=='all' else [args.phase]
        for phase in phases:
            if phase=='parametric':await parametric(cfg)
            elif phase=='retrieve':retrieve()
            elif phase=='ce':rank_ce()
            elif phase=='jev':await rank_jev(cfg)
            elif phase=='answers':await select_and_answer(cfg)
            elif phase=='metrics':metrics()
            elif phase=='analyze':analyze()
            elif phase=='review':review()
            elif phase=='budget':
                t=Transport(cfg)
                try:print(t.budget.summary())
                finally:await t.close()

if __name__=='__main__':asyncio.run(main())

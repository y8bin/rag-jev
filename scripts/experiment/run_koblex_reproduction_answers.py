"""Same frozen answer protocol, four independent questions in flight.

The original sequential runner is retained. This addendum changes scheduling only;
Transport still caps all API requests at the original concurrency of four.
"""
import asyncio
import json
from pathlib import Path
from legal_rag_jev.config import Config,environment_file_scope
from legal_rag_jev.io import read_json,read_jsonl,write_json,write_jsonl,file_hash,digest
from legal_rag_jev.providers import Transport
import run_koblex_reproduction as study

async def main():
    with environment_file_scope('.env.koblex',{}):
        cfg=Config.load('configs/koblex-paper.yaml','.env.koblex')
        cfg=cfg.model_copy(update={'cache_dir':str(study.ROOT/'framework-cache')})
        study.freeze(cfg)
        addendum={'parent_lock_sha256':file_hash(study.ROOT/'protocol-lock.json'),
                  'runner_sha256':file_hash(__file__),'question_concurrency':4,'http_concurrency':cfg.concurrency,
                  'change':'Scheduling only. Same frozen prompt, parser, model, candidate lists, budget and output schema.',
                  'answer_results_observed_before_addendum':False}
        path=study.ROOT/'answers-execution-addendum.json'
        if path.exists() and read_json(path)!=addendum:raise ValueError('Answer runner changed')
        write_json(path,addendum)
        corpus=[r['hierarchy']+r['content'] for r in read_jsonl(study.CORPUS)]
        questions=study.input_questions()
        rankings={kind:{r['query_id']:r for r in read_jsonl(study.ROOT/f'ranking-{kind}.jsonl')} for kind in ('ce','jev')}
        if any(set(rs)!={q['id'] for q in questions} for rs in rankings.values()):raise ValueError('Rankings incomplete')
        outputs={arm:study.checkpoint(arm+'.jsonl') for arm in study.ARMS}
        transport=Transport(cfg)
        semaphore=asyncio.Semaphore(4)
        async def one(q):
            async with semaphore:
                qid=q['id']
                for kind in ('ce','jev'):
                    arms=study.ARMS[:2] if kind=='ce' else study.ARMS[2:]
                    if all(qid in outputs[a][1] for a in arms):continue
                    lists=[];choices=[];traces=[];raw=[]
                    for pool in rankings[kind][qid]['pools']:
                        ids=pool['top10_row_ids'];lists.append(ids)
                        candidates='\n'.join(f'{i}: {corpus[rid]}' for i,rid in enumerate(ids))
                        text,trace=await study.chat(cfg,transport,study.prompt('selection_retrieval',background=q['background'],question=q['question'],candidates=candidates))
                        choices.append(study.choice_from(text));traces.append(trace);raw.append(text)
                    for arm in arms:
                        destination,done=outputs[arm]
                        if qid in done:continue
                        ids=study.selected_from(lists,choices,raw=arm=='parser_ce_raw')
                        provisions=[corpus[i] for i in ids]
                        text,trace=await study.chat(cfg,transport,study.prompt('question_answering',question=q['background']+q['question'],context_str='\n'.join(provisions)))
                        row={'query_id':qid,'answer':text.split('Answer:')[-1].strip(),'provisions':provisions,
                             'selected_row_ids':ids,'choices':choices,'selection_raw_outputs':raw,
                             'selection_traces':traces,'generation_trace':trace,'status':'ok'}
                        study.append(destination,row);done[qid]=row
                        print('answered',arm,qid,flush=True)
        try:
            await asyncio.gather(*(one(q) for q in questions))
        finally:await transport.close()
        for arm in study.ARMS:
            rows=outputs[arm][1]
            write_jsonl(study.ROOT/'predictions'/f'{arm}.jsonl',[rows[q['id']] for q in questions])

if __name__=='__main__':asyncio.run(main())

"""Same pinned LF-Eval, one ordered stream per arm, at most three calls active.

Identical judge prompts share an in-process lock and the frozen evaluator cache,
so equal answers are not accidentally scored twice or written concurrently.
"""
import asyncio
from legal_rag_jev.config import Config,environment_file_scope,provider_identity
from legal_rag_jev.io import read_json,write_json,file_hash,digest,environment_manifest
from legal_rag_jev import koblex_lf_eval as evaluator
import run_koblex_reproduction as study

async def main():
    with environment_file_scope('.env.koblex',{}):
        cfg=Config.load('configs/koblex-paper.yaml','.env.koblex')
        cfg=cfg.model_copy(update={'cache_dir':str(study.ROOT/'framework-cache')})
        lock=read_json(study.ROOT/'protocol-lock.json')['signature']
        for p,h in lock['files'].items():
            if file_hash(p)!=h:raise ValueError('Frozen source changed: '+p)
        preflight=read_json(study.ROOT/'lf-preflight.json')
        if provider_identity('judge',cfg.judge_backend)!=preflight['judge']:raise ValueError('Judge changed')
        expected=preflight['dependencies']
        actual=environment_manifest()['dependencies']
        # The pure-Python BM25 dependency is exposed by the shared runner path but unused here.
        if {k:v for k,v in actual.items() if k!='bm25s'}!={k:v for k,v in expected.items() if k!='bm25s'}:
            raise ValueError('Dedicated LF dependency environment changed')
        amendment={'runner_sha256':file_hash(__file__),'parent_lock_sha256':file_hash(study.ROOT/'protocol-lock.json'),
                   'change':'Three independent condition streams; original within-condition order and evaluator unchanged.',
                   'maximum_active_judge_requests':3,'identical_prompt_cache_shared_and_locked':True,
                   'prior_completed_LF_rows_preserved':True,'scientific_parameters_changed':False,
                   'previous_interruption_reservations_retained':True}
        path=study.ROOT/'lf-scheduling-amendment.json'
        if path.exists() and read_json(path)!=amendment:raise ValueError('LF scheduler changed')
        write_json(path,amendment)
        original_factory=evaluator.budget_judge
        locks={}
        def guarded_factory(*args,**kwargs):
            judge=original_factory(*args,**kwargs)
            original=judge.a_generate_raw_response
            async def guarded(prompt,top_logprobs=20,**options):
                key=digest({'prompt':prompt,'top_logprobs':top_logprobs})
                async with locks.setdefault(key,asyncio.Lock()):
                    return await original(prompt,top_logprobs=top_logprobs,**options)
            judge.a_generate_raw_response=guarded
            return judge
        evaluator.budget_judge=guarded_factory
        results=await asyncio.gather(*(evaluator.evaluate(cfg,study.GOLD,
            str(study.ROOT/'predictions'/f'{arm}.jsonl'),str(study.ROOT/'lf-eval'/arm)) for arm in study.ARMS))
        for arm,result in zip(study.ARMS,results):print(arm,result,flush=True)

if __name__=='__main__':asyncio.run(main())

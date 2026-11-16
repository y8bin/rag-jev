"""Current KoBLEX study entry point after workspace cleanup; no paid default."""
from __future__ import annotations
import argparse
import asyncio
import importlib
from pathlib import Path
import sys

ROOT=Path('results/koblex-reproduction-v1')
EXECUTED=Path('scripts/experiment')
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(EXECUTED.resolve()))
sys.path.insert(0,str(Path('.cache/koblex-reproduction-deps').resolve()))
from legal_rag_jev import io
from legal_rag_jev.config import Config,environment_file_scope,provider_identity,pricing

_raw_hash=getattr(io,'_koblex_original_file_hash',io.file_hash)
io._koblex_original_file_hash=_raw_hash
_raw_load=getattr(Config,'_koblex_original_load',Config.load.__func__)
Config._koblex_original_load=_raw_load

def resolve_path(path):
    manifest=io.read_json(ROOT/'cleanup-manifest.json')
    return manifest['path_map'].get(str(path),str(path))

def file_hash(path):
    return _raw_hash(resolve_path(path))

def load_config(cls,path,env_file='.env'):
    if str(path)=='configs/koblex-paper.yaml':path='configs/koblex-reproduction.yaml'
    return _raw_load(cls,path,env_file)

def verify(cfg=None):
    manifest=io.read_json(ROOT/'cleanup-manifest.json')
    lock=io.read_json(ROOT/'protocol-lock.json')
    if io.digest(lock['signature'])!=lock['signature_hash']:raise ValueError('Execution lock changed')
    for path,expected in lock['signature']['files'].items():
        if file_hash(path)!=expected:raise ValueError('Frozen scientific source changed: '+path)
    for section in ('current_files','preserved_results','retained_execution_runtime'):
        for path,expected in manifest[section].items():
            if _raw_hash(path)!=expected:raise ValueError('Current artifact changed: '+path)
    if cfg is not None:
        lock=lock['signature']
        actual=io.environment_manifest()['dependencies']
        lf=io.read_json(ROOT/'lf-preflight.json')
        if actual!=lock['dependencies'] and {k:v for k,v in actual.items() if k!='bm25s'}!={k:v for k,v in lf['dependencies'].items() if k!='bm25s'}:
            raise ValueError('Execution dependency environment changed')
        if provider_identity('judge',cfg.judge_backend)!=lf['judge']:raise ValueError('Judge identity changed')
        for kind,backend in [('generation',cfg.generation_backend),('ce',cfg.ce_backend),('jev',cfg.jev_backend)]:
            if provider_identity(kind,backend)!=lock[kind]:raise ValueError('Model identity changed: '+kind)
        for kind in ('generation','judge','jev'):
            if pricing()[kind]!=lock['prices'][kind]:raise ValueError('Price changed: '+kind)
        if (cfg.top_k,cfg.top_n,cfg.ce_batch_size,cfg.ce_max_length,cfg.max_output_tokens,cfg.temperature,cfg.generation_top_p,cfg.concurrency)!=(100,10,50,8192,2000,.01,.9,4):
            raise ValueError('Current ParSeR execution settings changed')
        if cfg.budget_limit_usd!=100 or cfg.budget_openai_limit_usd!=37:raise ValueError('Budget cap changed')
    return {'status':'VERIFIED_CURRENT_STUDY','questions':226,'conditions':3,'cleanup_is_post_execution':True}

def install_adapter():
    # Original executed scientific scripts remain byte-identical in provenance.
    # Only filesystem locations and the active configuration are routed here.
    io.file_hash=file_hash
    Config.load=classmethod(load_config)
    study=importlib.import_module('run_koblex_reproduction')
    study.UP=Path('data/koblex/upstream')
    study.QA=study.UP/'experiments/source/koblex.jsonl'
    study.freeze=verify
    return study

def phase_complete(phase,study):
    # Completed scientific artifacts are immutable, including their execution-time
    # budget snapshots. Do not rewrite them merely to refresh today's balances.
    checkpoints={'parametric':'parametric.jsonl','retrieve':'candidates.jsonl',
                 'ce':'ranking-ce.jsonl','jev':'ranking-jev.jsonl'}
    if phase in checkpoints:
        p=ROOT/checkpoints[phase]
        return p.exists() and len(io.read_jsonl(p))==226
    if phase=='answers':
        return all((ROOT/'predictions'/f'{arm}.jsonl').exists() and len(io.read_jsonl(ROOT/'predictions'/f'{arm}.jsonl'))==226 for arm in study.ARMS)
    if phase in ('metrics','lf-eval'):
        folder='lf-eval' if phase=='lf-eval' else 'metrics'
        return all((ROOT/folder/arm/'summary.json').exists() and io.read_json(ROOT/folder/arm/'summary.json')['questions']==226 for arm in study.ARMS)
    if phase=='analyze':return (ROOT/'analysis.json').exists()
    if phase=='review':return all((ROOT/'human-review'/f'reviewer-{name}.jsonl').exists() for name in ('A','B'))
    return False

async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['verify','budget','parametric','retrieve','ce','jev','answers','metrics','lf-eval','analyze','review','audit'])
    args=parser.parse_args()
    study=install_adapter()
    with environment_file_scope('.env.koblex',{}):
        cfg=Config.load('configs/koblex-reproduction.yaml','.env.koblex')
        cfg=cfg.model_copy(update={'cache_dir':str(ROOT/'framework-cache')})
        result=verify(cfg)
        if phase_complete(args.phase,study):
            print({'status':'ALREADY_COMPLETE_PRESERVED','phase':args.phase,'paid_calls':0})
            return
        if args.phase=='verify':print(result)
        elif args.phase=='budget':
            from legal_rag_jev.budget import Budget
            result=Budget(cfg.budget_ledger,100,openai_limit=37).summary()
            carry=io.read_json(ROOT/'cleanup-manifest.json')['budget_opening_balance']
            result['current_request_records']=result['attempts']-len(carry)
            result['opening_balance_records']=carry
            print(result)
        elif args.phase=='parametric':await study.parametric(cfg)
        elif args.phase=='retrieve':study.retrieve()
        elif args.phase=='ce':study.rank_ce()
        elif args.phase=='jev':await study.rank_jev(cfg)
        elif args.phase=='answers':await importlib.import_module('run_koblex_reproduction_answers_paced').main()
        elif args.phase=='metrics':study.metrics()
        elif args.phase=='lf-eval':await importlib.import_module('run_koblex_reproduction_lf_parallel').main()
        elif args.phase=='analyze':study.analyze()
        elif args.phase=='review':study.review()
        elif args.phase=='audit':
            import runpy
            runpy.run_path('scripts/audit_koblex_reproduction.py',run_name='__main__')

if __name__=='__main__':asyncio.run(main())

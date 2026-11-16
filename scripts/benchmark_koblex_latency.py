"""Scorer-only latency benchmark: CE (local MPS) vs Jev (remote API) on the locked candidates.

Separate run ID; reads the completed study read-only and never touches its locks or caches.
Timed region per question: score every unique (question, candidate) pair of all pools,
then sort each pool and take its top-10 shortlist. Excludes parametric generation, BM25,
LLM selection and answer generation (identical across conditions).

Fixed before measurement:
- sample: the pre-registered human-review sample (60 questions; hop 15/34/11, seed 20261108)
- duplicate policy (both methods): unique candidate texts within a question are scored once
- caches off: Jev requests bypass jev-cache and are not stored; CE has no score cache
- warmup: 3 sample questions per method, excluded from statistics
- 3 repetitions; question order and per-question method order shuffled (seed 20261109)
- CE: dragonkue/bge-reranker-v2-m3-ko pinned revision, MPS float32, batch 50, sigmoid
- Jev: jev-1.14.0 via the study Transport (concurrency 4, timeout 60s, 1 retry, shared budget ledger)
- methods run sequentially, never concurrently
"""
from __future__ import annotations
import os
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '0'
os.environ['HF_HUB_OFFLINE'] = '1'
import asyncio
import json
import math
import platform
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import koblex as entry  # noqa: E402  (study entry point: verification + path routing)

STUDY = Path('results/koblex-reproduction-v1')
OUT = Path('results/koblex-latency-v1')
SEED = 20261109
REPS = 3
WARMUP = 3
INSTRUCTIONS = 'Rank by relevance: does the candidate statutory passage directly support answering the question?'


def append(path, row):
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')
        f.flush(); os.fsync(f.fileno())


def top10(ids, scores_by_text, corpus):
    order = sorted(range(len(ids)), key=lambda i: (scores_by_text[corpus[ids[i]]], corpus[ids[i]]), reverse=True)
    return [ids[i] for i in order[:10]]


async def main():
    study = entry.install_adapter()
    from legal_rag_jev import io
    from legal_rag_jev.config import Config, environment_file_scope, provider_identity
    from legal_rag_jev.providers import Transport
    with environment_file_scope('.env.koblex', {}):
        cfg = Config.load('configs/koblex-reproduction.yaml', '.env.koblex')
        cfg = cfg.model_copy(update={'cache_dir': str(STUDY / 'framework-cache')})
        status = entry.verify(cfg)
        sample = io.read_json('research/koblex_source_audit_20261108.json')['human_review_sample']
        ids = list(sample['ids'])
        questions = {q['id']: q['question'] for q in study.input_questions()}
        corpus = [r['hierarchy'] + r['content'] for r in io.read_jsonl(study.CORPUS)]
        cands = {r['query_id']: r for r in io.read_jsonl(STUDY / 'candidates.jsonl') if r['query_id'] in set(ids)}
        quality = {'ce': {r['query_id']: r for r in io.read_jsonl(STUDY / 'ranking-ce.jsonl') if r['query_id'] in cands},
                   'jev': {r['query_id']: r for r in io.read_jsonl(STUDY / 'ranking-jev.jsonl') if r['query_id'] in cands}}
        OUT.mkdir(parents=True, exist_ok=True)
        raw = OUT / 'raw.jsonl'
        if raw.exists():
            raise SystemExit('Existing benchmark output found; refusing to mix sessions: ' + str(raw))
        jev_identity = provider_identity('jev', cfg.jev_backend)
        io.write_json(OUT / 'protocol.json', {
            'created_at_utc': datetime.now(timezone.utc).isoformat(), 'study_verification': status,
            'sample': {'source': 'research/koblex_source_audit_20261108.json#human_review_sample',
                       'seed': sample['seed'], 'hop_counts': sample['hop_counts'], 'questions': len(ids)},
            'timed_region': 'score all unique (question, candidate) pairs of the question, then per-pool sort + top-10',
            'excluded': ['parametric provision generation', 'BM25 retrieval', 'LLM selection', 'answer generation', 'model load'],
            'duplicate_policy': 'unique candidate text per question scored once, both methods',
            'cache': False, 'warmup_questions_per_method': WARMUP, 'repetitions': REPS, 'order_seed': SEED,
            'ce': {'model': 'dragonkue/bge-reranker-v2-m3-ko', 'revision': '2aca5884ecac490192af9ebd86836d9073d826cd',
                   'device': 'mps', 'dtype': 'float32', 'batch_size': 50, 'activation': 'sigmoid'},
            'jev': {'identity': jev_identity, 'instructions': INSTRUCTIONS, 'concurrency': cfg.concurrency,
                    'timeout_seconds': cfg.timeout_seconds, 'max_retries': cfg.max_retries},
            'machine': {'platform': platform.platform(), 'processor': platform.processor(),
                        'python': platform.python_version()},
            'source_hashes': {'candidates.jsonl': io.file_hash(STUDY / 'candidates.jsonl'),
                              'script': io.file_hash(Path(__file__))}})
        import torch
        # Not study.load_ce(): it rewrites the preserved results/.../ce-runtime.json.
        from sentence_transformers import CrossEncoder
        if not torch.backends.mps.is_available():
            raise RuntimeError('MPS required')
        model = CrossEncoder('dragonkue/bge-reranker-v2-m3-ko', revision='2aca5884ecac490192af9ebd86836d9073d826cd',
                             device='mps', activation_fn=torch.nn.Sigmoid(), cache_folder='.cache/models',
                             local_files_only=True)
        transport = Transport(cfg)

        def unique_texts(qid):
            return list(dict.fromkeys(corpus[i] for p in cands[qid]['pools'] for i in p['row_ids']))

        def run_ce(qid):
            texts = unique_texts(qid); q = questions[qid]
            torch.mps.synchronize(); start = time.perf_counter()
            scores = model.predict([(q, t) for t in texts], batch_size=50, show_progress_bar=False)
            torch.mps.synchronize()
            values = dict(zip(texts, [float(s) for s in scores.reshape(-1)]))
            shortlists = [top10(p['row_ids'], values, corpus) for p in cands[qid]['pools']]
            elapsed = (time.perf_counter() - start) * 1000
            if len(values) != len(texts) or not all(math.isfinite(v) for v in values.values()):
                raise ValueError('Invalid CE scores')
            return {'wall_clock_ms': elapsed, 'pairs': len(texts), 'shortlists': shortlists, 'status': 'ok'}

        async def run_jev(qid):
            texts = unique_texts(qid); q = questions[qid]

            async def one(t):
                body = {'model': jev_identity['model'], 'state': {'query': q, 'candidate': t},
                        'questions': {'relevant': {'type': 'noul', 'instructions': INSTRUCTIONS}}}
                r = await transport.request('jev', jev_identity, '/v1/systemone', body)
                ans = r.value['answers']['relevant']
                if ans['type'] != 'noul' or not 0 <= ans['noul'] <= 1:
                    raise ValueError('Invalid Jev score')
                return float(ans['noul']), r.trace
            start = time.perf_counter()
            try:
                results = await asyncio.gather(*(one(t) for t in texts))
            except Exception as exc:  # failure is recorded, never turned into a low score
                return {'wall_clock_ms': (time.perf_counter() - start) * 1000, 'pairs': len(texts),
                        'status': 'failed', 'error': type(exc).__name__ + ': ' + str(exc)[:300]}
            values = dict(zip(texts, [s for s, _ in results]))
            shortlists = [top10(p['row_ids'], values, corpus) for p in cands[qid]['pools']]
            elapsed = (time.perf_counter() - start) * 1000
            traces = [t for _, t in results]
            return {'wall_clock_ms': elapsed, 'pairs': len(texts), 'shortlists': shortlists, 'status': 'ok',
                    'retries': sum(t['retry_count'] for t in traces),
                    'call_latency_ms_median': sorted(t['latency_ms'] for t in traces)[len(traces) // 2],
                    'cost_usd': sum(t['cost_usd'] or 0 for t in traces)}

        try:
            for rep in [-1] + list(range(REPS)):
                rng = random.Random(SEED + rep)
                order = ids[:WARMUP] if rep == -1 else rng.sample(ids, len(ids))
                for qid in order:
                    methods = ['ce', 'jev']; rng.shuffle(methods)
                    for method in methods:
                        result = run_ce(qid) if method == 'ce' else await run_jev(qid)
                        shortlists = result.pop('shortlists', None)
                        if shortlists is not None:
                            ref = [p['top10_row_ids'] for p in quality[method][qid]['pools']]
                            result['top10_same_as_quality_run'] = shortlists == ref
                            result['top10_set_overlap'] = sum(len(set(a) & set(b)) for a, b in zip(shortlists, ref)) / (10 * len(ref))
                        row = {'query_id': qid, 'method': method, 'repetition': rep, 'warmup': rep == -1,
                               'pools': len(cands[qid]['pools']), **result}
                        append(raw, row)
                        print(rep, qid, method, round(row['wall_clock_ms']), row['status'], flush=True)
        finally:
            await transport.close()
        io.write_json(OUT / 'completed.json', {'completed_at_utc': datetime.now(timezone.utc).isoformat(),
                                               'budget_after': transport.budget.summary() if transport.budget else None})


if __name__ == '__main__':
    asyncio.run(main())

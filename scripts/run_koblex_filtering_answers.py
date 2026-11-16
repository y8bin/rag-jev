"""End-to-end answers for the cross-validated FR operating points (CE-FR, Jev-FR).

Inputs (read-only): results/koblex-filtering-v1/cv-heldout-*.jsonl (tau per question, fixed
before any answer was generated), the completed study's predictions and rankings.

For each question: kept evidence = final LLM-selected items whose scorer score >= tau.
- kept == original selection -> the original answer is reused (identical generator input).
- otherwise -> regenerate with the study's exact question_answering prompt and GPT-4o settings.
  Zero kept items -> empty context string (the generator still answers).
Caches/raw responses go to results/koblex-filtering-v1/e2e/, never to the study folder.
Then the official deterministic metrics are computed. LF-Eval runs separately in .venv-lf-eval.
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import koblex as entry  # noqa: E402

STUDY = Path('results/koblex-reproduction-v1')
FILTER = Path('results/koblex-filtering-v1')
OUT = FILTER / 'e2e'
ARMS = {'ce': ('parser_ce_fixed', 'ranking-ce.jsonl'), 'jev': ('parser_jev_fixed', 'ranking-jev.jsonl')}


async def main():
    study = entry.install_adapter()
    from legal_rag_jev import io
    from legal_rag_jev.config import Config, environment_file_scope
    from legal_rag_jev.koblex import evaluate_predictions
    from legal_rag_jev.providers import Transport
    study.ROOT = OUT  # chat() caches and raw responses land here only
    with environment_file_scope('.env.koblex', {}):
        cfg = Config.load('configs/koblex-reproduction.yaml', '.env.koblex')
        cfg = cfg.model_copy(update={'cache_dir': str(OUT / 'framework-cache')})
        entry.verify(cfg)
        corpus = [r['hierarchy'] + r['content'] for r in io.read_jsonl(study.CORPUS)]
        qs = {q['id']: q for q in study.input_questions()}
        gold_order = [g['query_id'] for g in io.read_jsonl(study.GOLD)]
        transport = Transport(cfg)
        try:
            for s, (arm, ranking) in ARMS.items():
                held = {r['query_id']: r for r in io.read_jsonl(FILTER / f'cv-heldout-{s}.jsonl')}
                preds = {p['query_id']: p for p in io.read_jsonl(STUDY / 'predictions' / f'{arm}.jsonl')}
                ranks = {r['query_id']: r for r in io.read_jsonl(STUDY / ranking)}
                out_path = OUT / f'{s}_fr.partial.jsonl'
                done = {r['query_id']: r for r in io.read_jsonl(out_path)} if out_path.exists() else {}
                for qid in gold_order:
                    if qid in done:
                        continue
                    tau, p = held[qid]['tau'], preds[qid]
                    pools = ranks[qid]['pools']
                    keep = [row for j, row in enumerate(p['selected_row_ids'])
                            if dict(zip(pools[j]['candidate_row_ids'], pools[j]['scores']))[row] >= tau]
                    provisions = [corpus[i] for i in keep]
                    if len(provisions) != held[qid]['kept']:
                        raise ValueError('Kept count differs from simulation ' + qid)
                    row = {'query_id': qid, 'tau': tau, 'selected_row_ids': keep, 'provisions': provisions,
                           'original_selected_row_ids': p['selected_row_ids']}
                    if keep == p['selected_row_ids']:
                        row.update({'answer': p['answer'], 'answer_source': 'reused_original_identical_input',
                                    'generation_trace': None})
                    else:
                        q = qs[qid]
                        text, trace = await study.chat(cfg, transport, study.prompt(
                            'question_answering', question=q['background'] + q['question'],
                            context_str='\n'.join(provisions)))
                        row.update({'answer': text.split('Answer:')[-1].strip(), 'answer_source': 'regenerated',
                                    'generation_trace': trace})
                        print('regenerated', s, qid, len(provisions), flush=True)
                    study.append(out_path, row); done[qid] = row
                final = OUT / 'predictions' / f'{s}_fr.jsonl'
                io.write_jsonl(final, [done[q] for q in gold_order])
                target = OUT / 'metrics' / f'{s}_fr'
                if not target.exists():
                    evaluate_predictions(study.GOLD, str(final), str(target))
        finally:
            await transport.close()


if __name__ == '__main__':
    asyncio.run(main())

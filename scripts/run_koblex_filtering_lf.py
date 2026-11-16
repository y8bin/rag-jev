"""LF-Eval (pinned DeepEval 4.3.3 judge, shared budget) for CE-FR / Jev-FR answers.

Run with .venv-lf-eval. Judge cache is a copy of the study's LF cache inside
results/koblex-filtering-v1/e2e/framework-cache, so identical (unchanged) answers
reproduce their original scores at no cost and the study folder is never written.
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from legal_rag_jev.config import Config, environment_file_scope  # noqa: E402
from legal_rag_jev import koblex_lf_eval as evaluator  # noqa: E402

OUT = Path('results/koblex-filtering-v1/e2e')


async def main():
    with environment_file_scope('.env.koblex', {}):
        cfg = Config.load('configs/koblex-reproduction.yaml', '.env.koblex')
        cfg = cfg.model_copy(update={'cache_dir': str(OUT / 'framework-cache')})
        for s in ('ce', 'jev'):
            r = await evaluator.evaluate(cfg, 'data/koblex/prepared-v1/gold.jsonl',
                                         str(OUT / 'predictions' / f'{s}_fr.jsonl'), str(OUT / 'lf-eval' / f'{s}_fr'))
            print(s, r['lf_eval'], r['budget'], flush=True)

if __name__ == '__main__':
    asyncio.run(main())

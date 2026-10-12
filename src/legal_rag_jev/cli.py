from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path
from qdrant_client.http.exceptions import ApiException

from .annotation import automatic_judge, export_annotations, import_answers, import_relevance
from .config import Config, endpoint, env
from .corpus import assign_splits, chunk_documents, ingest, load_documents, load_queries, validate_dataset
from .evaluation import evaluate, paired_statistics, summarize_benchmark
from .index import VectorIndex, build_index, open_client
from .lexical import lexical_pool
from .io import read_json, read_jsonl, write_json, write_jsonl
from .pipeline import benchmark, freeze, run
from .providers import ProviderError, Providers
from .reports import agreement, calibration, error_sample, plot_results, sweep, tune
from .schema import Answer, Chunk, Document, Query


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Legal RAG experiment harness")
    p.add_argument("--config", default="configs/main.yaml")
    p.add_argument("--env-file", default=".env")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("ingest"); s.add_argument("--input", required=True); s.add_argument("--output")
    sub.add_parser("chunk")
    sub.add_parser("validate")
    s = sub.add_parser("split"); s.add_argument("--output", required=True); s.add_argument("--dev-fraction", type=float, default=.25); s.add_argument("--test-fraction", type=float, default=.75)
    sub.add_parser("build-index")
    sub.add_parser("smoke")
    s = sub.add_parser("schemas"); s.add_argument("--output", default="schemas")
    s = sub.add_parser("lexical-pool"); s.add_argument("--split",choices=["pilot","dev","test"],default="dev"); s.add_argument("--top-k",type=int,default=20)
    s = sub.add_parser("retrieve"); s.add_argument("--split", choices=["pilot","dev","test"], default="dev")
    s = sub.add_parser("freeze"); s.add_argument("--output", required=True)
    s = sub.add_parser("run"); s.add_argument("--split", choices=["pilot","dev","test"], default="dev"); s.add_argument("--lock"); s.add_argument("--run-id"); s.add_argument("--fresh", action="store_true"); s.add_argument("--resume", action="store_true")
    s = sub.add_parser("sweep"); s.add_argument("--grid-size", type=int, default=5)
    s = sub.add_parser("tune"); s.add_argument("--run", required=True); s.add_argument("--output-config", required=True)
    s = sub.add_parser("evaluate"); s.add_argument("--run", required=True); s.add_argument("--annotations")
    s = sub.add_parser("statistics"); s.add_argument("--run", required=True)
    s = sub.add_parser("benchmark"); s.add_argument("--split", choices=["pilot","dev","test"], default="dev"); s.add_argument("--repeats", type=int, default=5); s.add_argument("--warmup", type=int, default=1); s.add_argument("--limit", type=int, default=20); s.add_argument("--lock")
    s = sub.add_parser("summarize-benchmark"); s.add_argument("--run", required=True)
    s = sub.add_parser("export-annotations"); s.add_argument("--run", required=True); s.add_argument("--kind", choices=["answers","relevance"], required=True); s.add_argument("--output", required=True)
    s = sub.add_parser("import-answers"); s.add_argument("--run", required=True); s.add_argument("--tasks", required=True); s.add_argument("--mapping", required=True)
    s = sub.add_parser("import-relevance"); s.add_argument("--tasks", required=True); s.add_argument("--mapping", required=True); s.add_argument("--output", required=True)
    s = sub.add_parser("judge"); s.add_argument("--run", required=True)
    s = sub.add_parser("agreement"); s.add_argument("--first", required=True); s.add_argument("--second", required=True); s.add_argument("--output", required=True)
    s = sub.add_parser("errors"); s.add_argument("--run", required=True); s.add_argument("--output", required=True); s.add_argument("--limit", type=int, default=100)
    s = sub.add_parser("calibration"); s.add_argument("--run", required=True); s.add_argument("--bins", type=int, default=10)
    s = sub.add_parser("plot"); s.add_argument("--run", required=True)
    sub.add_parser("demo")
    s = sub.add_parser("viewer"); s.add_argument("--results", default="results"); s.add_argument("--configs", default="configs"); s.add_argument("--host", default="127.0.0.1"); s.add_argument("--port", type=int, default=8765)
    return p


async def collect_candidates(cfg: Config, split: str) -> Path:
    providers = Providers(cfg)
    output = Path(cfg.output_dir) / ("candidates_" + uuid.uuid4().hex[:10])
    try:
        rows = []
        with VectorIndex(cfg, providers) as idx:
            for q in load_queries(cfg.queries, split):
                r = await idx.search(q.json_record())
                rows.append({"run_id": output.name, "query": q.json_record(), "method": "candidate_pool",
                    "condition_id": "candidate_pool", "status": "ok", **r})
        write_jsonl(output / "raw.jsonl", rows)
        write_json(output / "manifest.json", {"mode": "candidate_annotation", "split": split,
                                             "note": "Annotation pool only; no method performance is computed"})
        return output
    finally:
        await providers.close()


async def smoke(cfg: Config) -> dict:
    providers = Providers(cfg)
    try:
        q = load_queries(cfg.queries)[0].json_record()
        chunks = read_jsonl(cfg.chunks)[:1]
        if not chunks:
            raise ValueError("Chunk corpus before smoke test")
        report = {}
        if cfg.jev_backend == "http":
            identity = {"base_url": endpoint("JEV"), "model": env("JEV_MODEL")}
            result = await providers.transport.request("jev", identity, "/v1/models")
            report["available_jev_models"] = result.value
        for kind in ("embedding", "ce", "jev"):
            r = await providers.embed([q["question"]], True) if kind == "embedding" else await getattr(providers, kind)(q,chunks)
            report[kind] = r.trace
        if cfg.generate:
            r = await providers.generate(q,chunks)
            report["generation"] = r.trace
        if (Path(cfg.index_dir) / "manifest.json").is_file():
            with VectorIndex(cfg, providers) as idx:
                retrieved = await idx.search(q)
                report["qdrant"] = {"status": "ok", "mode": cfg.qdrant_mode,
                    "collection": idx.collection, "count": idx.manifest["count"],
                    "dimension": idx.manifest["dimension"], "eligible_count": retrieved["eligible_count"],
                    "returned_count": len(retrieved["candidates"]), "trace": retrieved["trace"]}
        elif cfg.qdrant_mode == "remote":
            client = open_client(cfg, Path(cfg.index_dir))
            try:
                report["qdrant"] = {"status": "reachable", "mode": "remote",
                    "collections": len(client.get_collections().collections), "index_built": False}
            finally:
                client.close()
        else:
            report["qdrant"] = {"status": "index_not_built", "mode": "local"}
        return report
    finally:
        await providers.close()


async def execute(args) -> object:
    cfg = Config.load(args.config, args.env_file)
    command = args.command
    if command == "ingest":
        out = args.output or cfg.documents
        rows = ingest(args.input, out)
        return {"output": out, "documents": len(rows)}
    if command == "chunk":
        rows = chunk_documents(load_documents(cfg.documents), cfg.chunk_max_chars)
        write_jsonl(cfg.chunks, rows)
        return {"output": cfg.chunks, "chunks": len(rows)}
    if command == "validate":
        chunks = [Chunk.model_validate(x).json_record() for x in read_jsonl(cfg.chunks)]
        return validate_dataset(chunks, load_queries(cfg.queries), load_documents(cfg.documents))
    if command == "split":
        rows = assign_splits(read_jsonl(cfg.queries), read_jsonl(cfg.chunks), cfg.seed, args.dev_fraction, args.test_fraction)
        write_jsonl(args.output, rows)
        load_queries(args.output)
        return args.output
    if command == "build-index":
        providers = Providers(cfg)
        try:
            manifest = await build_index(cfg, [Chunk.model_validate(x).json_record() for x in read_jsonl(cfg.chunks)], providers)
            return {k: manifest[k] for k in ("index_version","count","dimension","research_valid")}
        finally:
            await providers.close()
    if command == "smoke": return await smoke(cfg)
    if command == "schemas":
        for model in (Document,Chunk,Query,Answer):
            write_json(Path(args.output)/(model.__name__.lower()+".schema.json"),model.model_json_schema())
        return args.output
    if command == "lexical-pool": return lexical_pool(cfg,args.split,args.top_k)
    if command == "retrieve": return await collect_candidates(cfg,args.split)
    if command == "freeze": return await freeze(cfg,args.output)
    if command == "run": return await run(cfg,args.split,lock_path=args.lock,run_id=args.run_id,fresh=args.fresh,resume=args.resume)
    if command == "sweep": return await sweep(cfg,args.grid_size)
    if command == "tune": return tune(args.run,cfg,args.output_config)
    if command == "evaluate": return evaluate(args.run,args.annotations)
    if command == "statistics":
        actual = read_json(Path(args.run)/"manifest.json")["protocol"]["config"]
        return paired_statistics(args.run,actual["bootstrap_repetitions"],actual["seed"],actual["quality_delta"])
    if command == "benchmark": return await benchmark(cfg,args.split,args.repeats,args.warmup,args.limit,args.lock)
    if command == "summarize-benchmark": return summarize_benchmark(args.run)
    if command == "export-annotations": return export_annotations(args.run,args.kind,args.output,cfg.seed)
    if command == "import-answers": return import_answers(args.run,args.tasks,args.mapping)
    if command == "import-relevance": return import_relevance(cfg.queries,args.tasks,args.mapping,args.output)
    if command == "judge": return await automatic_judge(cfg,args.run)
    if command == "agreement": return agreement(args.first,args.second,args.output)
    if command == "errors": return error_sample(args.run,args.output,args.limit,cfg.seed)
    if command == "calibration": return calibration(args.run,args.bins)
    if command == "plot": return plot_results(args.run)
    if command == "demo":
        if any(getattr(cfg,k+"_backend") != "mock" for k in ("embedding","ce","jev","generation")):
            raise ValueError("demo requires configs/demo.yaml and mock providers")
        chunks = chunk_documents(load_documents(cfg.documents),cfg.chunk_max_chars)
        write_jsonl(cfg.chunks,chunks)
        providers = Providers(cfg)
        try:
            await build_index(cfg,chunks,providers)
        finally:
            await providers.close()
        out = await run(cfg,"dev")
        evaluate(str(out))
        paired_statistics(str(out),cfg.bootstrap_repetitions,cfg.seed,cfg.quality_delta)
        return {"run": str(out), "research_valid": False, "index_backend": cfg.index_backend,
                "note": "Synthetic engineering data; no human judgments or paper claims"}
    raise ValueError("Unknown command")


def main():
    args = parser().parse_args()
    if args.command == "viewer":
        from .viewer import serve
        return serve(args.results, args.configs, args.host, args.port, args.env_file)
    try:
        result = asyncio.run(execute(args))
        print(json.dumps(result if isinstance(result,(dict,list)) else {"output":str(result)}, ensure_ascii=False, indent=2))
    except (ValueError, ProviderError, FileNotFoundError, ImportError, ApiException) as e:
        print(f"Error: {e}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()

"""Local web viewer: ad-hoc exploration questions, run outputs, and YAML configs."""
from __future__ import annotations

import asyncio
import json
import mimetypes
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import yaml

from .cache import Cache
from .config import Config

STATIC = Path(__file__).parent / "viewer_static"
mimetypes.add_type("font/woff2", ".woff2")
RUN_FILES = ("manifest.json", "raw.jsonl", "completion.json", "summary.json")


def _json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
    except (OSError, ValueError):
        return None


class _Rows:
    """raw.jsonl / metrics.jsonl cache keyed by mtime so a running experiment shows new rows."""

    def __init__(self):
        self._cache: dict[Path, tuple[float, list[dict]]] = {}

    def get(self, path: Path) -> list[dict]:
        if not path.is_file():
            return []
        mtime = path.stat().st_mtime
        hit = self._cache.get(path)
        if hit and hit[0] == mtime:
            return hit[1]
        rows = []
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        rows.append({"status": "unreadable_line"})
        self._cache[path] = (mtime, rows)
        return rows


def _touches(unit: dict, chunk: dict) -> bool:
    if set(unit.get("chunk_ids") or []) & {chunk.get("chunk_id")}:
        return True
    if unit.get("start") is None or unit.get("doc_id") != chunk.get("doc_id") or unit.get("version_id") != chunk.get("version_id"):
        return False
    return chunk.get("start", 0) < unit["end"] and chunk.get("end", 0) > unit["start"]


def _short_trace(trace: dict | None) -> dict | None:
    if not isinstance(trace, dict):
        return None
    keep = ("latency_ms", "request_count", "retry_count", "cost_usd", "cached", "usage", "identity", "truncated_inputs")
    return {k: trace[k] for k in keep if k in trace}


def detail(rows: list[dict], metrics: dict | None = None) -> dict:
    """One question's shared candidate pool plus every condition's ranking, selection, and answer."""
    metrics = metrics or {}
    q = rows[0].get("query") or {}
    units = q.get("evidence_units") or []
    pool: dict[str, dict] = {}
    for c in rows[0].get("candidates") or []:
        pool[c["chunk_id"]] = {k: c.get(k) for k in ("chunk_id", "doc_id", "version_id", "title", "citation_key",
            "text", "start", "end", "vector_score", "vector_rank", "effective_from", "effective_to", "jurisdiction",
            "source_chunk_id", "law_name", "article", "paragraph", "chunk_level", "part", "n_parts",
            "member_chunk_ids", "version_conflict", "qdrant_point_id", "qdrant_collection")}
        pool[c["chunk_id"]]["units"] = [u["unit_id"] for u in units if _touches(u, c)]
        pool[c["chunk_id"]]["relevance"] = (q.get("relevance") or {}).get(c["chunk_id"])
    conditions = []
    for r in rows:
        cid = r.get("condition_id") or r.get("method")
        conditions.append({"condition_id": cid, "method": r.get("method"), "threshold": r.get("threshold"),
            "status": r.get("status"), "error_stage": r.get("error_stage"), "error": r.get("error"),
            "ranking": [{"chunk_id": c.get("chunk_id"), "rank": c.get("rank"), "score": c.get("rerank_score")} for c in r.get("ranking") or []],
            "selected": [c.get("chunk_id") for c in r.get("selected") or []],
            "answer": r.get("answer"), "invalid_citations": r.get("invalid_citations"),
            "context_tokens": r.get("context_tokens"), "cost": r.get("cost"), "timing": r.get("timing"),
            "traces": {k: _short_trace(r.get(k)) for k in ("rerank_trace", "generation_trace")},
            "metrics": (metrics.get(cid) or {}).get("metrics"),
            "human_evaluated": (metrics.get(cid) or {}).get("human_evaluated")})
    return {"query": q, "candidates": sorted(pool.values(), key=lambda c: c.get("vector_rank") or 0),
            "conditions": conditions}


class Viewer:
    def __init__(self, results: Path, configs: Path):
        self.results, self.configs = results.resolve(), configs.resolve()
        self.rows = _Rows()

    def _run_dir(self, rel: str) -> Path:
        path = (self.results / rel).resolve()
        if path != self.results and self.results not in path.parents:
            raise PermissionError("path outside results directory")
        if not path.is_dir():
            raise FileNotFoundError(rel)
        return path

    def runs(self) -> dict:
        found = []
        if self.results.is_dir():
            for d in sorted({p.parent for name in RUN_FILES for p in self.results.rglob(name)} - {self.results / "_explore"}):
                manifest = _json(d / "manifest.json") or {}
                completion = _json(d / "completion.json")
                raw = d / "raw.jsonl"
                found.append({
                    "path": str(d.relative_to(self.results)),
                    "group": str(d.parent.relative_to(self.results)) if d.parent != self.results else "",
                    "run_id": manifest.get("run_id", d.name),
                    "mode": manifest.get("mode") or ("quality" if completion else None),
                    "split": manifest.get("split"),
                    "research_valid": manifest.get("research_valid"),
                    "completion": completion,
                    "conditions": [c.get("condition_id") for c in manifest.get("conditions", [])],
                    "has_summary": (d / "summary.json").is_file(),
                    "has_statistics": (d / "statistics.json").is_file(),
                    "modified": max((p.stat().st_mtime for p in d.iterdir() if p.is_file()), default=None),
                    "rows": len(self.rows.get(raw)) if raw.is_file() and raw.stat().st_size < 50_000_000 else None,
                })
        found.sort(key=lambda r: r["modified"] or 0, reverse=True)
        return {"root": str(self.results), "runs": found}

    def run(self, rel: str) -> dict:
        d = self._run_dir(rel)
        manifest = _json(d / "manifest.json") or {}
        rows = self.rows.get(d / "raw.jsonl")
        queries: dict[str, dict] = {}
        for r in rows:
            q = r.get("query") or {}
            qid = r.get("query_id") or q.get("query_id") or "?"
            item = queries.setdefault(qid, {"query_id": qid, "group_id": r.get("group_id") or q.get("group_id"),
                "question": q.get("question"), "answerable": q.get("answerable"), "task_type": q.get("task_type"),
                "split": q.get("split"), "conditions": []})
            item["conditions"].append({"condition_id": r.get("condition_id") or r.get("method"), "method": r.get("method"),
                "status": r.get("status"), "error_stage": r.get("error_stage"), "selected_count": r.get("selected_count"),
                "online_usd": (r.get("cost") or {}).get("online_usd")})
        errors: dict[str, int] = {}
        for r in rows:
            if r.get("error"):
                key = f"{r.get('error_stage') or 'error'} · {str(r['error'])[:800]}"
                errors[key] = errors.get(key, 0) + 1
        protocol = manifest.get("protocol") or {}
        return {"path": rel, "manifest": {k: v for k, v in manifest.items() if k != "protocol"},
                "config": protocol.get("config"), "providers": protocol.get("providers"),
                "pricing": protocol.get("pricing"), "index_version": protocol.get("index_version"),
                "protocol_hash": manifest.get("protocol_hash"),
                "completion": _json(d / "completion.json"), "summary": _json(d / "summary.json"),
                "statistics": _json(d / "statistics.json"), "intervals": _json(d / "confidence_intervals.json"),
                "queries": list(queries.values()),
                "errors": [{"message": k, "count": v} for k, v in sorted(errors.items(), key=lambda x: -x[1])]}

    def query(self, rel: str, qid: str) -> dict:
        d = self._run_dir(rel)
        rows = [r for r in self.rows.get(d / "raw.jsonl") if (r.get("query_id") or (r.get("query") or {}).get("query_id")) == qid]
        if not rows:
            raise FileNotFoundError(qid)
        metrics = {m.get("condition_id"): m for m in self.rows.get(d / "metrics.jsonl") if m.get("query_id") == qid}
        return detail(rows, metrics)

    def configs_view(self) -> dict:
        fields = {name: f.default if f.default_factory is None else f.default_factory()
                  for name, f in Config.model_fields.items()}
        out = []
        for path in sorted(self.configs.glob("*.y*ml")):
            entry = {"name": path.stem, "path": str(path.name)}
            try:
                values = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                entry["explicit"] = sorted(values)
                entry["values"] = {**fields, **values}
                cfg = Config.model_validate(values)
                entry["backends"] = {k: getattr(cfg, k + "_backend") for k in ("embedding", "ce", "jev", "generation")}
                entry["index_built"] = cfg.qdrant_source == "existing" or (Path(cfg.index_dir) / "manifest.json").is_file()
                entry["existing_collection"] = cfg.qdrant_source == "existing"
                entry["skipped"] = [m for m in cfg.methods if m.endswith("fr") and getattr(cfg, m[:-3] + "_threshold") is None]
            except Exception as e:  # show invalid configs instead of hiding them
                entry["error"] = str(e).splitlines()[0][:300]
                entry.setdefault("values", fields)
                entry.setdefault("explicit", [])
            out.append(entry)
        return {"fields": list(fields), "defaults": fields, "configs": out}


class Asker:
    """Runs exploration questions through the experiment pipeline on one background event loop.

    Providers stay loaded per config file so local models initialize once. Every ask is appended to
    results/_explore/asks.jsonl, apart from experiment runs, and is never research evidence."""

    def __init__(self, results: Path, configs: Path, env_file: str):
        self.configs, self.env_file = configs.resolve(), env_file
        self.log = results.resolve() / "_explore" / "asks.jsonl"
        self.rows = _Rows()
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        self._providers: dict[str, tuple[float, object]] = {}
        self._lock: asyncio.Lock | None = None

    def _config(self, name: str) -> Path:
        path = (self.configs / name).resolve()
        if path.parent != self.configs or path.suffix not in (".yaml", ".yml") or not path.is_file():
            raise PermissionError(f"unknown config: {name}")
        return path

    async def _providers_for(self, path: Path, cfg: Config):
        from .providers import Providers
        mtime = path.stat().st_mtime
        hit = self._providers.get(str(path))
        if hit and hit[0] == mtime:
            return hit[1]
        if hit:
            await hit[1].close()
        providers = Providers(cfg)
        self._providers[str(path)] = (mtime, providers)
        return providers

    async def _ask(self, name: str, question: str, as_of: str | None, jurisdiction: str) -> dict:
        from .index import VectorIndex
        from .existing_index import ExistingVectorIndex
        from .pipeline import query_rows
        path = self._config(name)
        cfg = Config.load(str(path), self.env_file)
        conditions, skipped = [], []
        for m in cfg.methods:
            threshold = cfg.ce_threshold if m == "ce_fr" else cfg.jev_threshold if m == "jev_fr" else None
            if m.endswith("fr") and threshold is None:
                skipped.append(m)
                continue
            conditions.append({"method": m, "condition_id": m, "threshold": threshold})
        ask_id = "ASK-" + datetime.now().strftime("%m%d%H%M%S") + "-" + uuid.uuid4().hex[:4]
        q = {"query_id": ask_id, "group_id": "explore", "question": question, "split": "dev", "answerable": True,
             "as_of_date": as_of or None, "jurisdiction": jurisdiction, "task_type": "exploration",
             "reference_answer": "", "evidence_units": [], "sufficient_sets": [], "relevance": {}}
        self._lock = self._lock or asyncio.Lock()
        async with self._lock:  # a local Qdrant store admits one open client at a time
            providers = await self._providers_for(path, cfg)
            index_type = ExistingVectorIndex if cfg.qdrant_source == "existing" else VectorIndex
            with index_type(cfg, providers) as idx:
                rows = await query_rows(cfg, idx, providers, q, conditions,
                                        Cache(cfg.cache_dir, enabled=cfg.qdrant_source != "existing"), False, ask_id)
                source = {"mode": cfg.qdrant_mode, "kind": cfg.qdrant_source,
                          "collection": idx.collection, "collections": getattr(idx, "collections", [idx.collection]),
                          "metadata_filters_applied": cfg.apply_metadata_filters}
        record = {"ask_id": ask_id, "asked_at": datetime.now(timezone.utc).isoformat(), "config": path.name,
                  "exploration": True, "research_valid": False, "skipped_conditions": skipped,
                  "backends": {k: getattr(cfg, k + "_backend") for k in ("embedding", "ce", "jev", "generation")},
                  "source": source, "rows": rows}
        self.log.parent.mkdir(parents=True, exist_ok=True)
        with self.log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return record

    def ask(self, body: dict) -> dict:
        question = str(body.get("question") or "").strip()
        if not question:
            raise ValueError("질문을 입력하세요")
        as_of = str(body.get("as_of_date") or "").strip() or None
        if as_of:
            datetime.strptime(as_of, "%Y-%m-%d")
        future = asyncio.run_coroutine_threadsafe(
            self._ask(str(body.get("config") or ""), question, as_of, str(body.get("jurisdiction") or "").strip()), self.loop)
        return self.view(future.result(timeout=1800))

    @staticmethod
    def view(record: dict) -> dict:
        meta = {k: record.get(k) for k in ("ask_id", "asked_at", "config", "skipped_conditions", "backends", "exploration", "source")}
        return {**meta, **detail(record["rows"])} if record.get("rows") else meta

    def history(self) -> list[dict]:
        out = []
        for r in reversed(self.rows.get(self.log)):
            rows = r.get("rows") or []
            out.append({"ask_id": r.get("ask_id"), "asked_at": r.get("asked_at"), "config": r.get("config"),
                        "question": (rows[0].get("query") or {}).get("question") if rows else None,
                        "conditions": [{"condition_id": x.get("condition_id"), "method": x.get("method"), "status": x.get("status"),
                                        "selected_count": x.get("selected_count")} for x in rows]})
        return out

    def get(self, ask_id: str) -> dict:
        for r in self.rows.get(self.log):
            if r.get("ask_id") == ask_id:
                return self.view(r)
        raise FileNotFoundError(ask_id)


def serve(results: str, configs: str, host: str, port: int, env_file: str = ".env") -> None:
    viewer = Viewer(Path(results), Path(configs))
    asker = Asker(Path(results), Path(configs), env_file)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, status: int, body: bytes, kind: str):
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urlsplit(self.path)
            args = {k: v[0] for k, v in parse_qs(url.query).items()}
            try:
                if url.path.startswith("/api/"):
                    name = url.path[5:]
                    if name == "runs": data = viewer.runs()
                    elif name == "run": data = viewer.run(args["path"])
                    elif name == "query": data = viewer.query(args["path"], args["id"])
                    elif name == "configs": data = viewer.configs_view()
                    elif name == "asks": data = {"asks": asker.history()}
                    elif name == "ask": data = asker.get(args["id"])
                    else: raise FileNotFoundError(name)
                    return self._send(200, json.dumps(data, ensure_ascii=False, default=str).encode(), "application/json; charset=utf-8")
                rel = "index.html" if url.path in ("", "/") else url.path.lstrip("/")
                file = (STATIC / rel).resolve()
                if STATIC.resolve() not in file.parents or not file.is_file():
                    raise FileNotFoundError(rel)
                kind = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
                self._send(200, file.read_bytes(), kind + ("; charset=utf-8" if kind.startswith("text/") or kind.endswith("javascript") else ""))
            except (FileNotFoundError, KeyError) as e:
                self._send(404, json.dumps({"error": f"not found: {e}"}).encode(), "application/json")
            except PermissionError as e:
                self._send(403, json.dumps({"error": str(e)}).encode(), "application/json")

        def do_POST(self):
            if urlsplit(self.path).path != "/api/ask":
                return self._send(404, b'{"error": "not found"}', "application/json")
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
                data = asker.ask(body)
                self._send(200, json.dumps(data, ensure_ascii=False, default=str).encode(), "application/json; charset=utf-8")
            except PermissionError as e:
                self._send(403, json.dumps({"error": str(e)}, ensure_ascii=False).encode(), "application/json; charset=utf-8")
            except Exception as e:  # surface provider/config/index errors to the asker verbatim
                self._send(400, json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Legal RAG viewer: http://{host}:{port}  (results: {viewer.results}; Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

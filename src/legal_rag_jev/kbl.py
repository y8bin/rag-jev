"""Pinned public KBL downloads and conversion; benchmark gold stays separate from retrieval."""
from __future__ import annotations

import json
import math
import re
import shutil
import tempfile
from datetime import date
from pathlib import Path

import httpx

from .corpus import chunk_documents, normalize
from .io import digest, file_hash, read_json, read_jsonl, write_json, write_jsonl
from .schema import BenchmarkQuery, Chunk, Document

BENCHMARK_REVISION = "fc30b6d78a75adf396e606afa3b188bda3d711b0"
CORPUS_REVISION = "72f50c8d2b44defa56ceff3fef62128b94f78bba"
DEFAULT_TASK = "query_and_statute_matching_qa"
TASKS = (DEFAULT_TASK, "legal_concept_qa", "offense_component_qa", "statute_hallucination_qa",
         "legal_common_legal_mistake_qa", "legal_common_legal_mistake_qa_reasoning")


def download(repo: str, revision: str, relative: str, output: Path) -> Path:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Pin downloads to a complete commit SHA")
    url = f"https://huggingface.co/datasets/{repo}/resolve/{revision}/{relative}"
    receipt = output.with_suffix(output.suffix + ".source.json")
    if output.exists():
        if not receipt.exists():
            raise ValueError(f"Download has no source receipt: {output}")
        meta = read_json(receipt)
        if meta["url"] != url or meta["sha256"] != file_hash(output):
            raise ValueError(f"Download source/hash mismatch: {output}")
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".part")
    total = 0
    with httpx.stream("GET", url, follow_redirects=True, timeout=120) as response:
        response.raise_for_status()
        with partial.open("wb") as stream:
            for block in response.iter_bytes(1024*1024):
                stream.write(block)
                total += len(block)
                if total // (25*1024*1024) != (total-len(block)) // (25*1024*1024):
                    print(f"{relative}: {total/1024/1024:.0f} MiB", flush=True)
        expected = response.headers.get("content-length")
        if expected and not response.headers.get("content-encoding") and total != int(expected):
            raise ValueError("Incomplete download")
    partial.rename(output)
    write_json(receipt, {"url": url, "repository": repo, "revision": revision, "sha256": file_hash(output),
                         "bytes": total, "license": "CC-BY-NC-4.0", "license_url": "https://creativecommons.org/licenses/by-nc/4.0/"})
    return output


def prepare_replay(output: str, task: str = DEFAULT_TASK, variant: str = "rag_s", *, source: str | None = None) -> dict:
    if task not in TASKS or variant not in ("rag_s", "rag_p", "rag_ps"):
        raise ValueError("Unsupported KBL task/variant")
    destination = Path(output)
    if destination.exists():
        from .retrievers import verify_artifacts
        manifest = read_json(destination / "manifest.json")
        if manifest.get("task") != task or manifest.get("variant") != variant:
            raise ValueError("KBL import is immutable; choose a different output")
        if source and file_hash(source) != manifest["source_sha256"]:
            raise ValueError("KBL import source changed; choose a different output")
        verify_artifacts(destination, manifest)
        return manifest
    relative = f"knowledge/{variant}/kbl_{task}_v0.1.rag.json"
    source_path = Path(source) if source else download("lbox/kbl", BENCHMARK_REVISION, relative,
                          destination.parent / "downloads" / variant / f"kbl_{task}.json")
    source_hash = file_hash(source_path)
    rows = read_json(source_path)
    if not isinstance(rows, list) or not rows:
        raise ValueError("KBL file must contain a nonempty JSON array")
    questions, gold, pools, known_ids, source_versions = [], [], [], set(), {}
    for row in rows:
        qid = f"KBL:{task}:{row['doc-id']}"
        if qid in known_ids:
            raise ValueError("Duplicate KBL question ID")
        known_ids.add(qid)
        # No answer-bearing field is copied into questions or candidate records.
        choices = {letter: row[letter] for letter in "ABCDE" if letter in row}
        if row.get("label") not in choices:
            raise ValueError(f"Invalid gold label: {qid}")
        question = BenchmarkQuery(query_id=qid, group_id=f"kbl:{task}:{row['doc-id']}",
                                  question=row["question"], choices=choices, task_type=f"kbl_{task}").json_record()
        questions.append(question)
        gold.append({"query_id": qid, "label": row["label"]})
        branches = row.get("rag_data") or {}
        branch = branches.get("question_only")
        # Choice-specific retrieval needs its own fixed merge protocol. Fail instead of silently changing it.
        if not branch:
            raise ValueError(f"{qid}: no question_only candidates; choice-specific retrieval needs an explicit merge policy")
        docs = (branch.get("retrieved_docs") or {}).get("results")
        if not isinstance(docs, list):
            raise ValueError(f"{qid}: malformed retrieved_docs")
        candidates, seen = [], set()
        for item in docs:
            original_id, text = str(item["doc_id"]), normalize(item["passage"])
            if not text.strip():
                raise ValueError(f"{qid}: empty candidate passage")
            score = float(item["score"])
            if not math.isfinite(score):
                raise ValueError("Nonfinite retrieval score")
            kind = "precedent" if variant == "rag_p" or original_id.startswith("lbox_open_precedents") else "statute"
            did = f"kbl:{kind}:{original_id}"
            version = digest(text)
            cid = "KBL_C_" + digest([did, version])[:24]
            if cid in seen:
                raise ValueError(f"{qid}: duplicate candidate")
            seen.add(cid)
            source_versions.setdefault(did, set()).add(version)
            doc = Document(doc_id=did, version_id=version, group_id=did, text=text,
                           title=item.get("title") or original_id, doc_type=kind, jurisdiction="KR",
                           citation_key=original_id, source_uri=f"https://huggingface.co/datasets/lbox/kbl/blob/{BENCHMARK_REVISION}/{relative}",
                           source_hash=digest(item), collected_at=date.today())
            chunk = Chunk(**doc.json_record(), chunk_id=cid, start=0, end=len(text), text_hash=digest(text)).json_record()
            candidates.append({**chunk, "retrieval_rank": len(candidates)+1, "retrieval_score": score, "retriever": variant})
        pools.append({"query_id": qid, "original_query": branch.get("query"), "candidates": candidates})
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".kbl-", dir=destination.parent))
    try:
        write_jsonl(staging / "questions.jsonl", questions)
        write_jsonl(staging / "gold.jsonl", gold)
        write_jsonl(staging / "candidates.jsonl", pools)
        artifacts = {name: file_hash(staging / name) for name in ("questions.jsonl", "gold.jsonl", "candidates.jsonl")}
        manifest = {"backend": "replay", "task": task, "variant": variant, "revision": BENCHMARK_REVISION,
                    "source_sha256": source_hash, "source_path": str(source_path), "license": "CC-BY-NC-4.0",
                    "source_uri": f"https://huggingface.co/datasets/lbox/kbl/blob/{BENCHMARK_REVISION}/{relative}",
                    "research_valid": True, "evidence_metrics_available": False, "query_count": len(questions),
                    "candidate_counts": sorted({len(p["candidates"]) for p in pools}),
                    "count": len({c["chunk_id"] for p in pools for c in p["candidates"]}),
                    "version_conflicts": sorted(k for k,v in source_versions.items() if len(v)>1), "artifacts": artifacts}
        manifest["index_version"] = digest(manifest)
        write_json(staging / "manifest.json", manifest)
        staging.rename(destination)
        return manifest
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def prepare_corpus(output: str, kind: str = "statutes", *, source: str | None = None, max_chars: int = 1800) -> dict:
    if kind not in ("statutes", "precedents") or max_chars < 30:
        raise ValueError("Choose statutes/precedents and chunk size >= 30")
    destination = Path(output)
    if destination.exists():
        from .retrievers import verify_artifacts
        manifest = read_json(destination / "manifest.json")
        if manifest["kind"] != kind or manifest["chunk_max_chars"] != max_chars:
            raise ValueError("Corpus is immutable; choose a different output")
        if source and file_hash(source) != manifest["source_sha256"]:
            raise ValueError("Corpus source changed; choose a different output")
        verify_artifacts(destination, manifest)
        return manifest
    relative = f"corpus/{kind}.jsonl"
    source_path = Path(source) if source else download("lbox/kbl-rag", CORPUS_REVISION, relative,
                                   destination.parent / "downloads" / f"{kind}.jsonl")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".kbl-corpus-", dir=destination.parent))
    count, chunks_count, ids = 0, 0, set()
    try:
        with source_path.open(encoding="utf-8") as stream, (staging / "documents.jsonl").open("w",encoding="utf-8") as documents, (staging / "chunks.jsonl").open("w",encoding="utf-8") as chunks:
            for line in stream:
                if not line.strip():
                    continue
                row = json.loads(line)
                original_id = str(row["id"])
                if original_id in ids:
                    raise ValueError("Duplicate corpus ID")
                ids.add(original_id)
                text = normalize(row["contents"])
                if not text.strip():
                    raise ValueError(f"Empty corpus text: {original_id}")
                did = f"kbl:{kind}:{original_id}"
                family = original_id.split("___jo-")[0] if kind == "statutes" else original_id
                title = text.splitlines()[0][:100] if kind == "statutes" else f"판례 {original_id}"
                doc = Document(doc_id=did, version_id=CORPUS_REVISION, group_id=f"kbl:{kind}:{family}", text=text,
                               title=title, citation_key=original_id, doc_type="statute" if kind=="statutes" else "precedent",
                               jurisdiction="KR", source_uri=f"https://huggingface.co/datasets/lbox/kbl-rag/blob/{CORPUS_REVISION}/{relative}",
                               source_hash=digest(row), collected_at=date.today())
                documents.write(json.dumps(doc.json_record(),ensure_ascii=False)+"\n")
                for chunk in chunk_documents([doc], max_chars):
                    chunks.write(json.dumps(chunk,ensure_ascii=False)+"\n")
                    chunks_count += 1
                count += 1
                if count % 10000 == 0:
                    print(f"KBL {kind}: {count:,} documents converted",flush=True)
        if not count:
            raise ValueError("Empty corpus")
        manifest = {"kind": kind, "repository": "lbox/kbl-rag", "revision": CORPUS_REVISION,
                    "license": "CC-BY-NC-4.0", "source_sha256": file_hash(source_path), "documents": count,
                    "chunks": chunks_count, "chunk_max_chars": max_chars, "effective_dates_verified": False,
                    "artifacts": {name:file_hash(staging/name) for name in ("documents.jsonl","chunks.jsonl")}}
        write_json(staging/"manifest.json",manifest)
        staging.rename(destination)
        return manifest
    finally:
        if staging.exists():
            shutil.rmtree(staging)

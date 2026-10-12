from __future__ import annotations

import random
import re
import unicodedata
from pathlib import Path

from .io import digest, file_hash, read_jsonl, write_jsonl
from .schema import Chunk, Document, Query


def load_documents(path: str) -> list[Document]:
    docs = [Document.model_validate(x) for x in read_jsonl(path)]
    keys = [(d.doc_id, d.version_id) for d in docs]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate document/version IDs")
    if not docs:
        raise ValueError("Corpus is empty")
    return docs


def normalize(text: str) -> str:
    # Offsets always refer to this canonical text, never the original byte stream.
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n")).replace("\x00", "")


def ingest(source: str, output: str) -> list[dict]:
    p = Path(source)
    rows = []
    if p.is_file():
        rows = read_jsonl(p)
    else:
        # Each source file needs a metadata sidecar so IDs/provenance aren't invented.
        from .io import read_json
        for f in sorted(p.rglob("*")):
            if f.suffix.lower() not in (".txt", ".md", ".pdf"):
                continue
            meta_path = Path(str(f) + ".meta.json")
            if not meta_path.is_file():
                raise ValueError(f"Missing metadata sidecar: {meta_path}")
            meta = read_json(meta_path)
            if f.suffix.lower() == ".pdf":
                try:
                    from pypdf import PdfReader
                except ImportError as e:
                    raise ValueError("Install .[documents] to read text PDFs") from e
                text = "\n\n".join(page.extract_text() or "" for page in PdfReader(f).pages)
                if not text.strip():
                    raise ValueError(f"{f}: no text; OCR is required before ingestion")
            else:
                text = f.read_text(encoding="utf-8")
            rows.append({**meta, "text": text, "source_hash": file_hash(f)})
    canonical = []
    for row in rows:
        raw = row["text"]
        row = {**row, "text": normalize(raw), "source_hash": row.get("source_hash") or digest(raw)}
        canonical.append(Document.model_validate(row).json_record())
    if not canonical or len({(d["doc_id"],d["version_id"]) for d in canonical}) != len(canonical):
        raise ValueError("Empty corpus or duplicate document/version IDs")
    write_jsonl(output, canonical)
    return canonical


def chunk_documents(documents: list[Document], max_chars: int) -> list[dict]:
    chunks = []
    for d in documents:
        # Keep article/paragraph boundaries. Oversized sections use newline or sentence boundaries.
        boundaries = sorted({0, len(d.text), *[m.start() for m in re.finditer(
            r"(?m)^(?:제\s*\d+\s*조(?:의\s*\d+)?|Article\s+\d+)|\n\s*\n", d.text)]})
        for left, right in zip(boundaries, boundaries[1:]):
            pos = left
            while pos < right:
                end = min(pos + max_chars, right)
                if end < right:
                    cut = max(d.text.rfind("\n", pos + max_chars // 2, end),
                              d.text.rfind(". ", pos + max_chars // 2, end))
                    if cut >= 0:
                        end = cut + 1
                a, b = pos, end
                while a < b and d.text[a].isspace():
                    a += 1
                while b > a and d.text[b - 1].isspace():
                    b -= 1
                if a < b:
                    text = d.text[a:b]
                    cid = "C_" + digest([d.doc_id, d.version_id, a, b, text, "structure-v1"])[:24]
                    chunks.append(Chunk(**{**d.json_record(), "text": text}, chunk_id=cid, start=a, end=b,
                                        text_hash=digest(text)).json_record())
                pos = end
    return chunks


def load_queries(path: str, split: str | None = None) -> list[Query]:
    rows = [Query.model_validate(x) for x in read_jsonl(path)]
    if len({q.query_id for q in rows}) != len(rows):
        raise ValueError("Duplicate query IDs")
    group_splits: dict[str, set] = {}
    evidence_splits: dict[str, set] = {}
    for q in rows:
        group_splits.setdefault(q.group_id, set()).add(q.split)
        for u in q.evidence_units:
            if u.doc_id:
                # Versions of the same document cannot leak across splits.
                evidence_splits.setdefault(u.doc_id, set()).add(q.split)
            for cid in u.chunk_ids:
                evidence_splits.setdefault("chunk:" + cid, set()).add(q.split)
    if any(len(v) > 1 for v in [*group_splits.values(), *evidence_splits.values()]):
        raise ValueError("Document/group leakage across splits; run split with the corpus")
    selected = [q for q in rows if split is None or q.split == split]
    if not selected:
        raise ValueError(f"No queries for split={split}")
    return selected


def validate_dataset(chunks: list[dict], queries: list[Query], documents: list[Document] | None = None) -> dict:
    ids = {c["chunk_id"]: c for c in chunks}
    if len(ids) != len(chunks):
        raise ValueError("Duplicate chunk IDs")
    docs = {(d.doc_id, d.version_id): d for d in documents or []}
    groups: dict[str, set] = {}
    for c in chunks:
        if docs:
            d = docs.get((c["doc_id"], c["version_id"]))
            if d is None or d.text[c["start"]:c["end"]] != c["text"]:
                raise ValueError(f"Invalid canonical offsets: {c['chunk_id']}")
    for q in queries:
        if set(q.relevance) - set(ids):
            raise ValueError(f"{q.query_id}: relevance references unknown chunks")
        for u in q.evidence_units:
            if set(u.chunk_ids) - set(ids):
                raise ValueError(f"{q.query_id}: unknown evidence chunks")
            matches = [ids[c] for c in u.chunk_ids]
            if u.doc_id:
                matches += [c for c in chunks if c["doc_id"] == u.doc_id and c["version_id"] == u.version_id]
                if not matches:
                    raise ValueError(f"{q.query_id}: missing evidence document/version")
                if docs:
                    d = docs[(u.doc_id, u.version_id)]
                    if u.end is None or u.end > len(d.text):
                        raise ValueError(f"{q.query_id}: evidence outside canonical text")
            for c in matches:
                groups.setdefault(c["group_id"], set()).add(q.split)
    if any(len(v) > 1 for v in groups.values()):
        raise ValueError("Corpus document families leak across splits")
    return {"documents": len(docs), "chunks": len(chunks), "queries": len(queries),
            "query_groups": len({q.group_id for q in queries}),
            "split_counts": {s: sum(q.split == s for q in queries) for s in ("pilot", "dev", "test")}}


def assign_splits(rows: list[dict], chunks: list[dict], seed: int, dev_fraction: float, test_fraction: float) -> list[dict]:
    if dev_fraction <= 0 or test_fraction <= 0 or dev_fraction + test_fraction > 1:
        raise ValueError("Fractions must be positive with sum <= 1")
    parent: dict[str, str] = {}
    def find(x):
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    def union(a, b):
        parent[find(b)] = find(a)
    lookup = {c["chunk_id"]: c for c in chunks}
    doc_groups = {c["doc_id"]: c["group_id"] for c in chunks}
    for q in rows:
        qkey = "q:" + q["group_id"]
        find(qkey)
        for u in q.get("evidence_units", []):
            if u.get("doc_id"):
                union(qkey, "d:" + doc_groups.get(u["doc_id"], u["doc_id"]))
            for cid in u.get("chunk_ids", []):
                union(qkey, "d:" + lookup[cid]["group_id"])
    roots = sorted({find("q:" + q["group_id"]) for q in rows})
    random.Random(seed).shuffle(roots)
    if len(roots) < 2:
        raise ValueError("At least two independent groups are needed for dev/test")
    nd = max(1, round(len(roots) * dev_fraction))
    nt = max(1, round(len(roots) * test_fraction))
    if nd + nt > len(roots):
        nd = len(roots) - nt
    assignment = {root: "dev" if i < nd else "test" if i < nd + nt else "pilot" for i, root in enumerate(roots)}
    return [{**q, "group_id": "G_" + digest(find("q:" + q["group_id"]))[:16],
             "split": assignment[find("q:" + q["group_id"])]} for q in rows]

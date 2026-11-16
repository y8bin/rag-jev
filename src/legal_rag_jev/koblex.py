"""Immutable KoBLEX preparation and parity metrics; no model calls or test tuning."""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import shutil
import tempfile

from .io import digest, file_hash, read_json, read_jsonl, write_json, write_jsonl
from .schema import Chunk, Document, Query

REVISION = "1a2d225be33a70ebf91e2b6369acf27551dcfbb4"


def canonical(record: dict) -> str:
    if any(not isinstance(record.get(k), str) for k in ("hierarchy", "content")):
        raise ValueError("KoBLEX evidence requires string hierarchy and content")
    return record["hierarchy"] + record["content"]


def prepare(qa_source: str, corpus_source: str, output: str, group_audit: str, *, allow_unavailable_gold: bool = False) -> dict:
    """Preserve one chunk per original row, including headings and exact duplicates."""
    destination = Path(output)
    if destination.exists():
        raise ValueError("KoBLEX bundle is immutable; choose a new output")
    questions = read_jsonl(qa_source)
    if not questions or len({q["id"] for q in questions}) != len(questions):
        raise ValueError("Empty QA or duplicate question IDs")
    audit = read_json(group_audit)
    if file_hash(qa_source) != audit["qa_file_sha256"]:
        raise ValueError("QA hash differs from audited source")
    groups = audit["source_and_gold_groups"]["groups"]
    if set(groups) != {q["id"] for q in questions}:
        raise ValueError("Dependence groups do not cover exactly the QA IDs")
    gold_keys = {canonical(c) for q in questions for c in q["contexts"]}
    gold_rows = defaultdict(list)
    unit_counts, hops = Counter(), Counter()
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".koblex-", dir=destination.parent))
    count = 0
    try:
        with Path(corpus_source).open(encoding="utf-8") as source, (staging / "documents.jsonl").open("w", encoding="utf-8") as docs, (staging / "chunks.jsonl").open("w", encoding="utf-8") as chunks, (staging / "canonical.jsonl").open("w", encoding="utf-8") as mapping:
            for row in source:
                if not row.strip():
                    continue
                raw = json.loads(row)
                text = canonical(raw)
                if not text.strip():
                    raise ValueError("Empty canonical corpus row")
                cid = f"KBX_ROW_{count:06d}"
                unit_id = "KBX_UNIT_" + digest(text)
                document = Document(doc_id=cid, version_id=REVISION, group_id=cid,
                    text=text, title=raw["hierarchy"], doc_type="statute", jurisdiction="KR",
                    citation_key=raw["hierarchy"], source_hash=digest(raw),
                    source_uri=f"https://github.com/daehuikim/KoBLEX/blob/{REVISION}/experiments/source/statute.jsonl")
                chunk = Chunk(**document.json_record(), chunk_id=cid, start=0, end=len(text),
                              text_hash=digest(text), chunking_version="koblex-original-row-v1").json_record()
                docs.write(json.dumps(document.json_record(), ensure_ascii=False) + "\n")
                chunks.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                mapping.write(json.dumps({"chunk_id": cid, "unit_id": unit_id, "source_row": count,
                    "source_index": raw.get("index"), "hierarchy": raw["hierarchy"], "content": raw["content"]}, ensure_ascii=False) + "\n")
                unit_counts[unit_id] += 1
                if text in gold_keys:
                    gold_rows[text].append(cid)
                count += 1
        missing = gold_keys - gold_rows.keys()
        if missing:
            write_json(destination.parent / (destination.name + ".missing-gold.json"),
                {"missing_unique_gold_count": len(missing), "canonical_sha256": sorted(digest(x) for x in missing)})
            if not allow_unavailable_gold:
                raise ValueError(f"{len(missing)} exact gold provisions missing from original corpus; bundle not published")
        inputs, gold, queries = [], [], []
        for raw in questions:
            if any(not isinstance(raw.get(k), str) or not raw[k].strip() for k in ("id", "background", "question", "answer")):
                raise ValueError("Malformed KoBLEX QA")
            if type(raw.get("n_hops")) is not int or raw["n_hops"] not in (1, 2, 3):
                raise ValueError("Invalid hop metadata")
            text = raw["background"] + raw["question"]
            clean = {"query_id": raw["id"], "group_id": groups[raw["id"]], "question": text,
                     "split": "test", "jurisdiction": "KR", "as_of_date": None}
            inputs.append(clean)
            contexts = list(dict.fromkeys(canonical(c) for c in raw["contexts"]))
            evidence = [{"unit_id": "KBX_UNIT_" + digest(c), "chunk_ids": gold_rows[c]}
                        if c in gold_rows else {"unit_id": "KBX_UNIT_" + digest(c), "available_in_corpus": False}
                        for c in contexts]
            query = Query(**clean, answerable=True, reference_answer=raw["answer"], evidence_units=evidence,
                          sufficient_sets=[[e["unit_id"] for e in evidence]], task_type="koblex_qa").json_record()
            queries.append(query)
            gold.append({"query_id": raw["id"], "answer": raw["answer"], "n_hops": raw["n_hops"],
                         "provisions": contexts, "unit_ids": [e["unit_id"] for e in evidence],
                         "unavailable_unit_ids": [e["unit_id"] for e in evidence if not e.get("available_in_corpus", True)]})
            hops[raw["n_hops"]] += 1
        for filename, rows in (("questions.jsonl", inputs), ("gold.jsonl", gold), ("queries.jsonl", queries)):
            write_jsonl(staging / filename, rows)
        names = ["documents.jsonl", "chunks.jsonl", "canonical.jsonl", "questions.jsonl", "gold.jsonl", "queries.jsonl"]
        manifest = {"kind": "koblex_prepared_not_indexed", "revision": REVISION, "license": "CC-BY-NC-4.0",
            "qa_sha256": file_hash(qa_source), "corpus_sha256": file_hash(corpus_source), "group_audit_sha256": file_hash(group_audit),
            "questions": len(questions), "corpus_rows": count, "unique_canonical_units": len(unit_counts),
            "duplicate_canonical_rows": count - len(unit_counts), "unique_gold_units": len(gold_keys),
            "mapped_gold_units": len(gold_rows), "hop_counts": dict(hops), "all_splits": ["test"],
            "unavailable_gold_units": len(missing), "allow_unavailable_gold": allow_unavailable_gold,
            "questions_with_unavailable_gold": sum(bool(g["unavailable_unit_ids"]) for g in gold),
            "answerable_label_semantics": "original benchmark, not proof of gold availability in the corpus",
            "rechunked": False, "normalized": False, "dates_verified": False,
            "qdrant_equivalence_verified": False, "artifacts": {name: file_hash(staging / name) for name in names}}
        write_json(staging / "manifest.json", manifest)
        staging.rename(destination)
        return manifest
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def token_f1(prediction: str, reference: str) -> dict:
    def tokens(text):
        return re.sub(r"\s+", " ", re.sub(r"[^가-힣a-z0-9\s]", " ", text.lower())).strip().split()
    pred, gold = tokens(prediction), tokens(reference)
    common = sum((Counter(pred) & Counter(gold)).values())
    if not common:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    p, r = common / len(pred), common / len(gold)
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(2 * p * r / (p + r), 4)}


def provision_metrics(prediction: list[str], reference: list[str]) -> dict:
    pred, gold = set(prediction), set(reference)
    common = len(pred & gold)
    p = common / len(pred) if pred else float(not gold)
    r = common / len(gold) if gold else float(not pred)
    return {"precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0,
            "em": float(pred == gold), "gold_set_coverage": float(gold <= pred)}


def evaluate_predictions(gold_file: str, predictions_file: str, output: str) -> dict:
    """Strict ID/order checks avoid the upstream zip silently dropping missing predictions."""
    gold, predictions = read_jsonl(gold_file), read_jsonl(predictions_file)
    if len(predictions) != len(gold) or [x["query_id"] for x in predictions] != [x["query_id"] for x in gold]:
        raise ValueError("Prediction IDs/count/order must match every gold question")
    if len({x["query_id"] for x in gold}) != len(gold):
        raise ValueError("Duplicate gold IDs")
    rows = []
    for actual, expected in zip(predictions, gold):
        if not isinstance(actual.get("answer"), str) or not isinstance(actual.get("provisions"), list) or any(not isinstance(s, str) for s in actual["provisions"]):
            raise ValueError("Predictions require answer string and provisions string list")
        # Match the exact literal in the pinned upstream extract_predictions, including its tab escape.
        clipped = actual["answer"].split("<\think>")[0][:800]
        rows.append({"query_id": expected["query_id"], "n_hops": expected["n_hops"],
            "has_unavailable_gold": bool(expected.get("unavailable_unit_ids")),
            "retrieval": provision_metrics(actual["provisions"], expected["provisions"]),
            "token_f1": token_f1(clipped, expected["answer"])["f1"],
            "full_answer_token_f1": token_f1(actual["answer"], expected["answer"])["f1"]})
    if not rows:
        raise ValueError("No questions to evaluate")
    summary = {"questions": len(rows), "prediction_sha256": file_hash(predictions_file),
        "gold_sha256": file_hash(gold_file), "compatibility_answer_clip_chars": 800,
        "retrieval": {k: sum(r["retrieval"][k] for r in rows) / len(rows) for k in rows[0]["retrieval"]},
        "token_f1": sum(r["token_f1"] for r in rows) / len(rows),
        "full_answer_token_f1": sum(r["full_answer_token_f1"] for r in rows) / len(rows),
        "lf_eval": None, "lf_eval_status": "NOT_RUN"}
    def aggregate(subset):
        return {"questions": len(subset),
            "retrieval": {k: sum(r["retrieval"][k] for r in subset) / len(subset) for k in rows[0]["retrieval"]},
            "token_f1": sum(r["token_f1"] for r in subset) / len(subset)} if subset else {"questions": 0}
    summary["diagnostics"] = {
        "fully_mapped": aggregate([r for r in rows if not r["has_unavailable_gold"]]),
        "unavailable_gold_affected": aggregate([r for r in rows if r["has_unavailable_gold"]]),
        "by_hop": {str(h): aggregate([r for r in rows if r["n_hops"] == h]) for h in (1, 2, 3)}}
    destination = Path(output)
    if destination.exists():
        raise ValueError("Evaluation output already exists")
    write_jsonl(destination / "metrics.jsonl", rows)
    write_json(destination / "summary.json", summary)
    return summary


def export_predictions(run_dir: str, canonical_file: str, gold_file: str, output: str) -> dict:
    raw = read_jsonl(Path(run_dir) / "raw.jsonl")
    gold = read_jsonl(gold_file)
    order = [g["query_id"] for g in gold]
    methods = sorted({r["condition_id"] for r in raw})
    wanted = {c["chunk_id"] for r in raw for c in r.get("selected", [])}
    mapping = {}
    with Path(canonical_file).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row["chunk_id"] in wanted:
                mapping[row["chunk_id"]] = canonical(row)
    if wanted - mapping.keys():
        raise ValueError("Selected chunks missing from canonical crosswalk")
    files = {}
    prepared = {}
    for method in methods:
        if Path(method).name != method or not re.fullmatch(r"[\w.-]+", method):
            raise ValueError("Unsafe condition ID")
        subset = [r for r in raw if r["condition_id"] == method]
        ids = [r.get("query_id") or r["query"]["query_id"] for r in subset]
        if len(ids) != len(set(ids)) or set(ids) != set(order):
            raise ValueError("Every condition needs exactly one prediction per gold question")
        lookup = dict(zip(ids, subset))
        result = []
        for qid in order:
            r = lookup[qid]
            answer = r.get("answer") or {}
            if r.get("status") == "ok" and not isinstance(answer.get("answer"), str):
                raise ValueError("Successful row has no answer; cannot export a score-only run")
            result.append({"query_id": qid, "answer": answer.get("answer", "") if r.get("status") == "ok" else "",
                "provisions": list(dict.fromkeys(mapping[c["chunk_id"]] for c in r.get("selected", []))),
                "status": r.get("status")})
        prepared[method] = result
    if not methods:
        raise ValueError("No result conditions")
    destination = Path(output)
    if destination.exists():
        raise ValueError("Export output already exists")
    for method, result in prepared.items():
        path = destination / (method + ".jsonl")
        write_jsonl(path, result)
        files[method] = {"path": str(path), "sha256": file_hash(path), "questions": len(result)}
    write_json(destination / "export_manifest.json", {"source": str(run_dir), "conditions": files,
        "canonical_sha256": file_hash(canonical_file), "gold_sha256": file_hash(gold_file)})
    return files

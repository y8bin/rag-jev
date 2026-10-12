from __future__ import annotations

import random
import uuid
from pathlib import Path

from .io import digest, read_json, read_jsonl, write_json, write_jsonl
from .prompts import generation_content
from .providers import Providers


def validate_answer_annotation(row: dict, a: dict) -> None:
    if a.get("answer_hash") != digest(row["answer"]):
        raise ValueError("Annotation refers to a different answer")
    if type(a.get("correctness")) is not bool or type(a.get("core_supported")) is not bool:
        raise ValueError("Human correctness/core_supported must be booleans")
    claims = row["answer"]["claims"]
    labels = a.get("claim_labels")
    if not isinstance(labels, list) or len(labels) != len(claims):
        raise ValueError("One claim label is required for every generated claim")
    for claim,label in zip(claims, labels):
        if label.get("support") not in ("supported", "unsupported", "contradicted"):
            raise ValueError("Invalid claim support label")
        citations = label.get("citations", [])
        if sorted(c.get("evidence_id") for c in citations) != sorted(claim["evidence_ids"]):
            raise ValueError("Every cited ID must be judged once per occurrence")
        if any(type(c.get("supported")) is not bool for c in citations):
            raise ValueError("Citation support must be boolean")


def export_annotations(run_dir: str, kind: str, output_dir: str, seed: int) -> Path:
    raw = read_jsonl(Path(run_dir) / "raw.jsonl")
    manifest_path = Path(run_dir)/"manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    human_ids = set(manifest.get("human_evaluation_query_ids",[r["query"]["query_id"] for r in raw]))
    output = Path(output_dir)
    if output.exists():
        raise ValueError("Annotation directory already exists; use a new directory")
    mapping, templates, seen = {}, [], set()
    salt = uuid.uuid4().hex
    for row in raw:
        q = row["query"]
        if kind == "answers":
            if q["query_id"] not in human_ids:
                continue
            if row.get("answer") is None or row["status"] != "ok":
                continue
            identity = [q["query_id"], row["condition_id"]]
            aid = digest([salt, identity])[:20]
            mapping[aid] = {"query_id": q["query_id"], "condition_id": row["condition_id"],
                            "answer_hash": digest(row["answer"])}
            templates.append({"annotation_id": aid, "question": q["question"], "as_of_date": q.get("as_of_date"),
                "jurisdiction": q.get("jurisdiction", ""), "reference_answer": q["reference_answer"], "answer": row["answer"], "evidence": row["selected"],
                "correctness": None, "core_supported": None, "reviewer": "",
                "claim_labels": [{"support": None, "citations": [{"evidence_id": cid, "supported": None}
                    for cid in claim["evidence_ids"]]} for claim in row["answer"]["claims"]]})
            # Remove method score/rank from all documents shown to annotators.
            for c in templates[-1]["evidence"]:
                for key in ("rerank_score", "rank", "vector_score", "vector_rank", "lexical_score", "lexical_rank"):
                    c.pop(key, None)
            mapping[aid]["task_input_hash"] = digest({k:templates[-1][k] for k in ("question","as_of_date","jurisdiction","reference_answer","answer","evidence")})
        else:
            for c in row["candidates"]:
                identity = (q["query_id"], c["chunk_id"])
                if identity in seen:
                    continue
                seen.add(identity)
                aid = digest([salt, identity])[:20]
                mapping[aid] = {"query_id": q["query_id"], "chunk_id": c["chunk_id"], "text_hash": digest(c["text"])}
                templates.append({"annotation_id": aid, "question": q["question"], "as_of_date": q.get("as_of_date"),
                    "jurisdiction": q.get("jurisdiction", ""),
                    "candidate": {k:v for k,v in c.items() if k not in ("vector_score", "vector_rank", "rank", "rerank_score", "lexical_score", "lexical_rank")},
                    "grade": None, "reason": "", "reviewer": ""})
                mapping[aid]["task_input_hash"] = digest({k:templates[-1][k] for k in ("question","as_of_date","jurisdiction","candidate")})
    random.Random(seed).shuffle(templates)
    write_jsonl(output / "tasks.jsonl", templates)
    write_json(output / "private_mapping.json", {"kind": kind, "run_id": raw[0]["run_id"], "mapping": mapping})
    return output / "tasks.jsonl"


def import_answers(run_dir: str, tasks_path: str, mapping_path: str) -> Path:
    raw = read_jsonl(Path(run_dir) / "raw.jsonl")
    mapping = read_json(mapping_path)
    if mapping["kind"] != "answers":
        raise ValueError("Not an answer annotation mapping")
    lookup = {(r["query"]["query_id"], r["condition_id"]): r for r in raw}
    result, seen = [], set()
    for t in read_jsonl(tasks_path):
        aid = t["annotation_id"]
        if aid in seen or aid not in mapping["mapping"]:
            raise ValueError("Unknown/duplicate annotation ID")
        seen.add(aid)
        m = mapping["mapping"][aid]
        row = lookup[(m["query_id"], m["condition_id"])]
        if mapping["run_id"] != row["run_id"] or digest(t["answer"]) != m["answer_hash"]:
            raise ValueError("Mapping/answer changed since export")
        if digest({k:t[k] for k in ("question","as_of_date","jurisdiction","reference_answer","answer","evidence")}) != m["task_input_hash"]:
            raise ValueError("Annotation question/evidence changed since export")
        a = {**m, "source": "human", "correctness": t["correctness"], "core_supported": t["core_supported"],
             "claim_labels": t["claim_labels"], "reviewer": t.get("reviewer", "")}
        validate_answer_annotation(row, a)
        result.append(a)
    output = Path(run_dir) / "annotations.jsonl"
    if output.exists():
        old = read_jsonl(output)
        by_key = {(a["query_id"],a["condition_id"]):a for a in old}
        by_key.update({(a["query_id"],a["condition_id"]):a for a in result})
        result = list(by_key.values())
    write_jsonl(output, result)
    return output


def import_relevance(queries_path: str, tasks_path: str, mapping_path: str, output: str) -> Path:
    rows = read_jsonl(queries_path)
    queries = {q["query_id"]:q for q in rows}
    mapping = read_json(mapping_path)
    if mapping["kind"] != "relevance":
        raise ValueError("Not a relevance annotation mapping")
    seen = set()
    for t in read_jsonl(tasks_path):
        aid = t["annotation_id"]
        if aid in seen or aid not in mapping["mapping"]:
            raise ValueError("Unknown/duplicate annotation ID")
        seen.add(aid)
        m = mapping["mapping"][aid]
        if type(t.get("grade")) is not int or t["grade"] not in (0,1,2) or digest(t["candidate"]["text"]) != m["text_hash"]:
            raise ValueError("Invalid relevance grade or changed candidate")
        if digest({k:t[k] for k in ("question","as_of_date","jurisdiction","candidate")}) != m["task_input_hash"]:
            raise ValueError("Relevance annotation input changed since export")
        queries[m["query_id"]].setdefault("relevance", {})[m["chunk_id"]] = t["grade"]
    write_jsonl(output, rows)
    return Path(output)


async def automatic_judge(cfg, run_dir: str) -> Path:
    providers = Providers(cfg)
    results = []
    try:
        for r in read_jsonl(Path(run_dir) / "raw.jsonl"):
            if r["status"] != "ok" or r.get("answer") is None:
                continue
            content = {"question": r["query"]["question"], "as_of_date": r["query"].get("as_of_date"),
                "jurisdiction": r["query"].get("jurisdiction", ""), "reference_answer": r["query"]["reference_answer"],
                "answer": r["answer"], "evidence": generation_content(r["query"], r["selected"], cfg.common_input_chars)["evidence"]}
            from .providers import ProviderError
            judged = None
            try:
                judged = await providers.judge(content)
                annotation = {**judged.value, "source": "automatic", "query_id": r["query"]["query_id"],
                    "condition_id": r["condition_id"], "answer_hash": digest(r["answer"]), "trace": judged.trace, "status":"ok"}
                validate_answer_annotation(r, annotation)
            except (ProviderError, ValueError) as e:
                annotation = {"source":"automatic","query_id":r["query"]["query_id"],"condition_id":r["condition_id"],
                    "answer_hash":digest(r["answer"]),"status":"failed","error":str(e),
                    "trace":judged.trace if judged else getattr(e,"trace",{})}
            results.append(annotation)
            write_jsonl(Path(run_dir) / "auto_annotations.jsonl", results)
        output = Path(run_dir) / "auto_annotations.jsonl"
        write_jsonl(output, results)
        return output
    finally:
        await providers.close()

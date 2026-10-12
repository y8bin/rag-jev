"""Supplementary lexical search for human gold discovery; never a main retriever."""
from __future__ import annotations

import math
import uuid
from collections import Counter
from pathlib import Path

from .corpus import load_queries
from .index import eligible
from .io import read_jsonl, write_json, write_jsonl
from .providers import features


def lexical_pool(cfg, split: str, top_k: int) -> Path:
    if top_k < 1:
        raise ValueError("top_k must be positive")
    chunks = read_jsonl(cfg.chunks)
    if not chunks:
        raise ValueError("Empty chunks")
    counts = [Counter(features(c["text"])) for c in chunks]
    lengths = [sum(c.values()) for c in counts]
    average = sum(lengths)/len(lengths)
    frequency = Counter(token for c in counts for token in c)
    idf = {t: math.log(1+(len(chunks)-df+.5)/(df+.5)) for t,df in frequency.items()}
    output = Path(cfg.output_dir) / ("lexical_candidates_" + uuid.uuid4().hex[:10])
    rows = []
    for q in load_queries(cfg.queries,split):
        terms = set(features(q.question))
        scored = []
        for c,tf,n in zip(chunks,counts,lengths):
            if not eligible(c,q.json_record(),cfg):
                continue
            score = sum(idf[t]*tf[t]*2.2/(tf[t]+1.2*(.25+.75*n/average)) for t in terms if t in tf)
            scored.append((score,c))
        scored.sort(key=lambda x:(-x[0],x[1]["chunk_id"]))
        candidates = [{**c,"lexical_score":s,"lexical_rank":i+1} for i,(s,c) in enumerate(scored[:top_k])]
        rows.append({"run_id":output.name,"method":"lexical_pool","condition_id":"lexical_pool", "status":"ok",
                     "query":q.json_record(),"candidates":candidates})
    write_jsonl(output/"raw.jsonl",rows)
    write_json(output/"manifest.json",{"mode":"candidate_annotation","split":split,"tokenizer":"unicode-bigram-v1",
        "k1":1.2,"b":.75,"note":"Supplementary gold discovery only; does not replace Qdrant candidates"})
    return output

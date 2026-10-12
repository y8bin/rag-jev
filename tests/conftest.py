import pytest

from legal_rag_jev.config import Config
from legal_rag_jev.corpus import chunk_documents
from legal_rag_jev.io import write_jsonl
from legal_rag_jev.schema import Document, Query


@pytest.fixture
def corpus(tmp_path):
    docs = [Document(doc_id="law", version_id="v1", group_id="family", title="Notice", jurisdiction="KR",
                     effective_from="2025-01-01", text="Notice deadline is fourteen days."),
            Document(doc_id="old", version_id="v0", group_id="family", title="Old notice", jurisdiction="KR",
                     effective_from="2020-01-01", effective_to="2025-01-01", text="Notice deadline is seven days."),
            Document(doc_id="other", version_id="v1", group_id="other", jurisdiction="US",
                     effective_from="2025-01-01", text="A different jurisdiction and issue.")]
    chunks = chunk_documents(docs, 100)
    q = Query(query_id="Q1", group_id="family", question="Notice deadline days?", split="dev", answerable=True,
        jurisdiction="KR", as_of_date="2025-01-01", reference_answer="fourteen days",
        evidence_units=[{"unit_id":"U1", "doc_id":"law", "version_id":"v1", "start":0,"end":len(docs[0].text)}],
        sufficient_sets=[["U1"]], relevance={c["chunk_id"]:2 if c["doc_id"] == "law" else 0 for c in chunks})
    cfg = Config(documents=str(tmp_path/"docs.jsonl"), chunks=str(tmp_path/"chunks.jsonl"), queries=str(tmp_path/"queries.jsonl"),
        index_dir=str(tmp_path/"index"),output_dir=str(tmp_path/"results"), cache_dir=str(tmp_path/"cache"),
        embedding_backend="mock",index_backend="qdrant",ce_backend="mock",jev_backend="mock",generation_backend="mock",judge_backend="mock",
        top_k=3,top_n=2,ce_threshold=.1,jev_threshold=.1,token_encoding="unicode_characters", bootstrap_repetitions=100)
    write_jsonl(cfg.documents,[d.json_record() for d in docs])
    write_jsonl(cfg.chunks,chunks)
    write_jsonl(cfg.queries,[q.json_record()])
    return cfg,docs,chunks,q

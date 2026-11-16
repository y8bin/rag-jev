import asyncio

from legal_rag_jev.io import digest, read_jsonl, write_json, write_jsonl
from legal_rag_jev.providers import Result


def test_scoring_only_timing_resumes_with_fresh_warmup_and_never_generates(corpus, tmp_path, monkeypatch):
    from legal_rag_jev import koblex_timing as module
    cfg, _, chunks, query = corpus
    candidates = [dict(chunks[0], chunk_id=f"c{i}", vector_score=1-i/10, vector_rank=i+1) for i in range(2)]
    cfg = cfg.model_copy(update={"top_k": 2, "top_n": 1})
    calls = []

    class FakeProviders:
        def __init__(self, cfg):
            pass

        async def close(self):
            pass

        async def ce(self, q, c):
            calls.append("ce")
            return Result([.2, .9], {})

        async def jev(self, q, c):
            calls.append("jev")
            return Result([.2, .9], {})

        async def generate(self, *args):
            raise AssertionError("Scoring-only benchmark must never generate")

    monkeypatch.setattr(module, "Providers", FakeProviders)
    monkeypatch.setattr(module, "protocol", lambda cfg, providers: {"fixed": True})
    phash = digest({"fixed": True})
    write_json(tmp_path / "lock", {"protocol_hash": phash})
    write_json(tmp_path / "quality/manifest.json", {"protocol_hash": phash, "planned_queries": [query.query_id]})
    write_jsonl(tmp_path / "quality/raw.jsonl", [{"query_id": query.query_id, "query": query.json_record(),
        "condition_id": m, "candidates": candidates} for m in ("vector", "ce_r", "jev_r")])

    async def run():
        return await module.timing(cfg, str(tmp_path / "lock"), str(tmp_path / "quality"), str(tmp_path / "timing"))

    result = asyncio.run(run())
    assert len(calls) == 8  # two warmups, six measured calls
    assert result["methods"]["ce"]["attempts"] == 3
    assert all(r["selected_ids"] == ["c1"] for r in read_jsonl(tmp_path / "timing/raw.jsonl"))
    asyncio.run(run())
    assert len(calls) == 8  # completed benchmark is not billed again
    rows = read_jsonl(tmp_path / "timing/raw.jsonl")
    write_jsonl(tmp_path / "timing/raw.jsonl", rows[:-1])
    asyncio.run(run())
    assert len(calls) == 11  # fresh process/session warmups plus one missing measurement
    rows = read_jsonl(tmp_path / "timing/raw.jsonl")
    assert len({r["session_id"] for r in rows}) == 2

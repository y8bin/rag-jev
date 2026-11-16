import pytest

from legal_rag_jev.io import read_json, write_json, write_jsonl
from legal_rag_jev.koblex import evaluate_predictions
from legal_rag_jev.koblex_analysis import analyze, paired_bootstrap


def test_explicit_human_sample_must_match_available_questions(corpus):
    from legal_rag_jev.pipeline import human_sample
    cfg, _, _, q = corpus
    cfg = cfg.model_copy(update={"human_evaluation_ids": [q.query_id]})
    assert human_sample(cfg, [q]) == [q.query_id]
    with pytest.raises(ValueError, match="missing"):
        human_sample(cfg, [])


def test_diagnostics_preserve_unreachable_gold_in_denominator(tmp_path):
    gold = [{"query_id": "mapped", "answer": "정답", "n_hops": 1, "provisions": ["a"]},
            {"query_id": "unreachable", "answer": "정답", "n_hops": 2,
             "provisions": ["a", "missing"], "unavailable_unit_ids": ["missing"]}]
    pred = [{"query_id": g["query_id"], "answer": "정답", "provisions": ["a"]} for g in gold]
    write_jsonl(tmp_path / "gold", gold)
    write_jsonl(tmp_path / "pred", pred)
    result = evaluate_predictions(str(tmp_path / "gold"), str(tmp_path / "pred"), str(tmp_path / "metrics"))
    assert result["retrieval"]["recall"] == .75
    assert result["diagnostics"]["fully_mapped"]["retrieval"]["recall"] == 1
    assert result["diagnostics"]["unavailable_gold_affected"]["retrieval"]["recall"] == .5
    assert result["questions"] == 2


def test_cluster_bootstrap_uses_paired_question_weighted_mean():
    first = paired_bootstrap([0, 0, 1], ["large", "large", "small"], repetitions=1000)
    second = paired_bootstrap([0, 0, 1], ["large", "large", "small"], repetitions=1000)
    assert first == second
    assert first["mean_difference"] == pytest.approx(1 / 3)
    assert first["clusters"] == 2 and first["questions"] == 3
    zero = paired_bootstrap([0, 0], ["a", "b"], repetitions=100)
    assert zero["ci95"] == [0, 0] and zero["p_centered_bootstrap_two_sided"] == 1
    with pytest.raises(ValueError):
        paired_bootstrap([float("nan")], ["a"])


def test_analysis_rejects_unpaired_results_and_adjusts_only_two_primary_claims(tmp_path):
    groups = {f"q{i}": f"group{i//2}" for i in range(8)}
    write_json(tmp_path / "audit.json", {"source_and_gold_groups": {"groups": groups}})
    for method, score in (("vector", 0), ("ce_r", .5), ("jev_r", 1)):
        rows = [{"query_id": q, "retrieval": {"f1": score, "em": score, "gold_set_coverage": score},
                 "token_f1": score} for q in groups]
        write_jsonl(tmp_path / method / "metrics.jsonl", rows)
    result = analyze(str(tmp_path), str(tmp_path / "audit.json"), str(tmp_path / "analysis.json"), repetitions=200)
    primary = [r for r in result["comparisons"] if r["confirmatory"]]
    assert len(primary) == 2 and all(r["p_holm"] >= r["p_centered_bootstrap_two_sided"] for r in primary)
    assert all(r["mean_difference"] > 0 for r in primary)
    for method, score in (("vector", 0), ("ce_r", .5), ("jev_r", 1)):
        write_jsonl(tmp_path / "lf" / method / "metrics.jsonl", [{"query_id": q, "score": score} for q in groups])
    timings = [{"query_id": q, "method": method, "repetition": rep, "warmup": False,
                "status": "ok", "wall_clock_ms": latency}
               for q in groups for method, latency in (("ce", 5), ("jev", 10)) for rep in range(3)]
    write_jsonl(tmp_path / "timing/raw.jsonl", timings)
    complete = analyze(str(tmp_path), str(tmp_path / "audit.json"), str(tmp_path / "complete.json"),
                       repetitions=200, lf_root=str(tmp_path / "lf"), timing_root=str(tmp_path / "timing"))
    assert complete["lf_eval_status"] == complete["timing_status"] == "COMPLETE"
    assert complete["timing_ratio"]["ratio_ci95"] == pytest.approx([2, 2])
    write_jsonl(tmp_path / "ce_r/metrics.jsonl", list(reversed(rows)))
    with pytest.raises(ValueError, match="same unique IDs"):
        analyze(str(tmp_path), str(tmp_path / "audit.json"), str(tmp_path / "bad.json"), repetitions=200)

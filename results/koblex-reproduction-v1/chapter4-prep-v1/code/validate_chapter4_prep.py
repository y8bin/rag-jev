"""Validate prep exports and preservation without changing any original artifact."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path("results/koblex-reproduction-v1")
OUT = ROOT / "chapter4-prep-v1"


def read(path):
    return json.loads(path.read_text())


def rows(name):
    return [json.loads(line) for line in (OUT / name).read_text().splitlines()]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    baseline = read(OUT / "preservation-before.json")["files"]
    changed = [p for p, v in baseline.items() if not Path(p).is_file() or sha(Path(p)) != v["sha256"]]
    assert not changed, changed
    current_original_results = {str(p) for p in ROOT.rglob("*") if p.is_file() and OUT not in p.parents}
    baseline_results = {p for p in baseline if Path(p).is_relative_to(ROOT)}
    assert current_original_results == baseline_results, current_original_results ^ baseline_results
    sources = read(OUT / "source-manifest.json")["files"]
    assert all(sha(Path(p)) == v["sha256"] for p, v in sources.items())
    csv_count = 0
    for path in OUT.rglob("*.csv"):
        jsonl = path.with_suffix(".jsonl")
        if jsonl.exists():
            with path.open(newline="") as stream:
                exported = list(csv.DictReader(stream))
            original = [json.loads(line) for line in jsonl.read_text().splitlines()]
            assert len(original) == len(exported), path
            for a, b in zip(original, exported):
                for key, value in a.items():
                    expected = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else "" if value is None else str(value)
                    assert b[key] == expected, (path, key)
            csv_count += 1
    ledger = read(OUT / "A1/numeric-ledger.json")
    analysis = read(ROOT / "analysis.json")
    for row in ledger:
        original = analysis
        for part in row["source"]["json_pointer"].strip("/").split("/"):
            original = original[int(part)] if isinstance(original, list) else original[part]
        expected = original["mean_difference"] if isinstance(original, dict) else original
        assert abs(row["raw_value"] - expected) < 1e-12
        if row["kind"] == "paired_difference_existing_ci":
            assert row["ci95_raw"] == original["ci95"]
    stage = rows("A4/gold-occurrences.jsonl")
    for r in stage:
        flags = [r[k] for k in ("corpus", "bm25", "shortlist", "final")]
        assert all(a >= b for a, b in zip(flags, flags[1:]))
    counts = Counter(r["arm"] for r in stage)
    assert set(counts.values()) == {443}
    resources = rows("A5/question-resources.jsonl")
    assert len(resources) == 678 and all(r["api_minus_text_input_tokens"] == 7 for r in resources)
    qstages = rows("A4/question-stages.jsonl")
    feasibility = []
    for arm in ("parser_ce_fixed", "parser_jev_fixed"):
        rs = [r for r in qstages if r["arm"] == arm]
        for stage_name in ("bm25", "shortlist"):
            union = sum(r[f"all_gold_in_{stage_name}_union"] for r in rs)
            feasible = sum(r[f"all_gold_{stage_name}_jointly_selectable"] for r in rs)
            assert feasible <= union
            feasibility.append({"arm": arm, "stage": stage_name, "all_gold_in_union": union,
                                "all_gold_jointly_selectable": feasible, "union_complete_but_capacity_insufficient": union - feasible,
                                "denominator_questions": 226, "source": "A4/question-stages.jsonl",
                                "rule": "sum boolean flags; pool capacity 1; structural exact-string upper bound, not an oracle execution"})
    (OUT / "A4/pool-feasibility-summary.json").write_text(json.dumps(feasibility, ensure_ascii=False, indent=2) + "\n")
    report = {"status": "PASS_PREP_AND_ORIGINAL_PRESERVATION", "original_files_checked": len(baseline),
              "original_files_changed": [], "new_or_missing_original_result_files": [], "source_files_checked": len(sources),
              "csv_jsonl_pairs_checked": csv_count, "source_pointer_ledger_values_and_CIs": "PASS",
              "nested_gold_survival": "PASS", "generation_prompt_API_framing_residual": "7 tokens in all 678 rows",
              "validator_source": str(Path(__file__).relative_to(Path.cwd())), "validator_sha256": sha(Path(__file__)),
              "paid_calls": 0, "human_judgments_created": 0}
    (OUT / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

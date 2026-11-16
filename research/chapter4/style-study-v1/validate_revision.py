"""Check the writing revision without modifying frozen experimental artifacts.

Run from the repository root after compilation, PDF copy, and visual inspection.
The visual-review flag records the operator's review; it is not inferred by code.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from pypdf import PdfReader

ROOT = Path("research/chapter4")
OUT = ROOT / "style-study-v1"
PREP = Path("results/koblex-reproduction-v1/chapter4-prep-v1")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def uncomment(s):
    return re.sub(r"(?<!\\)%[^\n]*", "", s)


def nums(s):
    return Counter(re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", uncomment(s)))


def environments(s, name):
    return re.findall(r"\\begin\{" + name + r"\}.*?\\end\{" + name + r"\}", s, re.S)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--visual-reviewed", action="store_true")
    args = parser.parse_args()
    assert args.visual_reviewed, "Inspect all final PDF pages before recording completion"

    originals = read(PREP / "preservation-before.json")["files"]
    assert all(Path(p).is_file() and sha(Path(p)) == v["sha256"] for p, v in originals.items())
    result_root = PREP.parent
    old_results = {p for p in originals if Path(p).is_relative_to(result_root)}
    current_results = {str(p) for p in result_root.rglob("*") if p.is_file() and PREP not in p.parents}
    assert old_results == current_results
    frozen = read(PREP / "prep-output-manifest.json")["files"]
    assert all(sha(PREP / p) == v["sha256"] for p, v in frozen.items())
    source_facts = read(ROOT / "manuscript-facts.json")["source_files"]
    assert all(sha(Path(p)) == v["sha256"] for p, v in source_facts.items())

    backups = read(OUT / "before-manifest.json")["files"]
    assert all(sha(Path(v["backup"])) == v["sha256"] for v in backups.values())
    assert sha(ROOT / "manuscript-facts.json") == backups[str(ROOT / "manuscript-facts.json")]["sha256"]
    old = "\n".join((OUT / "before-revision" / f"section4_{n}.tex").read_text() for n in range(1, 6))
    new = "\n".join((ROOT / f"section4_{n}.tex").read_text() for n in range(1, 6))
    assert environments(old, "table") == environments(new, "table")
    assert environments(old, "figure") == environments(new, "figure")
    before_numbers, after_numbers = nums(old), nums(new)
    assert set(before_numbers) == set(after_numbers), "Unexpected added or missing displayed number"
    repetitions = {k: [before_numbers[k], after_numbers[k]] for k in sorted(before_numbers) if before_numbers[k] != after_numbers[k]}
    assert re.findall(r"\\subsection\{([^}]+)\}", old) == re.findall(r"\\subsection\{([^}]+)\}", new)
    all_tex = (ROOT / "chapter4.tex").read_text() + new
    labels = re.findall(r"\\label\{([^}]+)\}", all_tex)
    refs = re.findall(r"\\ref\{([^}]+)\}", all_tex)
    assert len(labels) == len(set(labels)) and set(refs) <= set(labels)
    log = Path("tmp/pdfs/chapter4/preview.log").read_text()
    for bad in ["Overfull", "undefined", "Missing character", "LaTeX Font Warning", "LaTeX Error"]:
        assert bad not in log, bad

    prior = read(OUT / "before-revision/draft-validation.json")
    figure_files = {p: h for p, h in prior["files"].items() if "/figures/" in p}
    assert all(sha(Path(p)) == h for p, h in figure_files.items())
    papers = read(OUT / "papers-manifest.json")
    for paper in papers["papers"]:
        assert sha(OUT / paper["pdf"]) == paper["pdf_sha256"]
        assert sha(OUT / paper["extracted_text"]) == paper["text_sha256"]
        reader = PdfReader(OUT / paper["pdf"])
        assert len(reader.pages) == paper["pdf_pages"]
        assert paper["version_in_pdf"] in (reader.pages[0].extract_text() or "")
    pdf = Path("output/pdf/chapter4-draft.pdf")
    assert sha(pdf) == sha(Path("tmp/pdfs/chapter4/preview.pdf"))
    pages = len(PdfReader(pdf).pages)
    assert pages == 3
    assert all(Path(f"tmp/pdfs/chapter4/style-revision-pages/page-{n}.png").is_file() for n in range(1, pages + 1))

    report = {
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_CHAPTER4_STYLE_REVISION",
        "current_study_verify": "VERIFIED_CURRENT_STUDY (separately run scripts/koblex.py verify)",
        "original_files_preserved": len(originals), "frozen_prep_outputs_preserved": len(frozen),
        "source_facts_files_preserved": len(source_facts),
        "manuscript_facts_unchanged": True,
        "unchanged_table_environments": len(environments(new, "table")),
        "unchanged_figure_environments": len(environments(new, "figure")),
        "figure_files_unchanged": len(figure_files),
        "displayed_numeric_token_set_unchanged": True,
        "numeric_repetition_changes_before_after": repetitions,
        "numeric_check_scope": "Lexical coverage is supplementary; metric, arm, unit and claim associations also manually reviewed against the fixed sources",
        "section_titles_unchanged": True,
        "references_checked": len(labels),
        "paper_count": papers["paper_count"],
        "collected_pdf_pages": sum(p["pdf_pages"] for p in papers["papers"]),
        "reviewed_result_related_pdf_pages": sum(len(p["reviewed_pdf_pages_one_based"]) for p in papers["papers"]),
        "reference_visual_sample_pages": len(papers["papers"]),
        "latex": "XeLaTeX, 2 passes after final text update; no overfull boxes, undefined references or missing glyph warnings",
        "preview_pages": pages,
        "visual_review": "Operator inspected all 3 final rendered pages; no clipping, missing glyphs or overlapping text. Provisional 2-column layout; last page has substantial unused space.",
        "preview_layout": "A4 / 10pt / two columns / 20mm margins; final venue layout pending",
        "pdf": {"path": str(pdf), "sha256": sha(pdf)},
        "new_paid_calls": 0, "new_human_judgments": 0, "new_statistical_tests": 0,
        "rq_coordination": str(PREP / "RQ_TOC_COORDINATION.md"),
        "legal_review": str(PREP / "LEGAL_REVIEW.md"),
        "files": {str(p): sha(p) for p in sorted(ROOT.glob("*.tex"))},
        "source_facts": str(ROOT / "manuscript-facts.json"),
        "full_review_notes": str(OUT / "READING_NOTES.md"),
    }
    report["files"][str(ROOT / "WRITING_NOTES.md")] = sha(ROOT / "WRITING_NOTES.md")
    (OUT / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "draft-validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "files"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

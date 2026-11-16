"""Index the collected arXiv PDFs; extraction only, no model or API calls."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
PAPERS = [
    ("2509.01324", "KoBLEX: Open Legal Question Answering with Multi-hop Reasoning", [7, 8, 9], 8),
    ("2408.10343", "LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain", [5, 6, 7, 8], 7),
    ("2005.11401", "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", [5, 6], 6),
    ("2004.04906", "Dense Passage Retrieval for Open-Domain Question Answering", [5, 6, 7], 5),
    ("2007.01282", "Leveraging Passage Retrieval with Generative Models for Open Domain Question Answering", [3, 4, 5], 4),
    ("2304.09542", "Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents", [5, 6, 7], 5),
    ("2305.14627", "Enabling Large Language Models to Generate Text with Citations", [6, 7, 8], 7),
    ("2307.03172", "Lost in the Middle: How Language Models Use Long Contexts", [4, 5, 6, 7], 5),
    ("2309.15217", "Ragas: Automated Evaluation of Retrieval Augmented Generation", [4, 5], 5),
    ("2408.08067", "RAGChecker: A Fine-grained Framework for Diagnosing Retrieval-Augmented Generation", [7, 8, 9], 8),
]


def main():
    records = []
    for arxiv_id, title, read_pages, visual_page in PAPERS:
        pdf = ROOT / "papers" / f"{arxiv_id}.pdf"
        reader = PdfReader(pdf)
        pages = [p.extract_text() or "" for p in reader.pages]
        version = re.search(r"arXiv\s*:\s*(\d{4}\.\d{4,5}v\d+)", pages[0])[1]
        txt = pdf.with_suffix(".txt")
        txt.write_text("\n\n".join(f"===== PDF PAGE {i} =====\n{p}" for i, p in enumerate(pages, 1)))
        records.append({
            "arxiv_id": arxiv_id, "version_in_pdf": version, "title": title,
            "requested_download_url": f"https://arxiv.org/pdf/{arxiv_id}",
            "versioned_pdf_url": f"https://arxiv.org/pdf/{version}",
            "versioned_abstract_url": f"https://arxiv.org/abs/{version}",
            "pdf": str(pdf.relative_to(ROOT)), "pdf_sha256": sha256(pdf.read_bytes()).hexdigest(),
            "pdf_bytes": pdf.stat().st_size, "pdf_pages": len(pages),
            "extracted_text": str(txt.relative_to(ROOT)), "text_sha256": sha256(txt.read_bytes()).hexdigest(),
            "reviewed_pdf_pages_one_based": read_pages, "visual_sample_pdf_page": visual_page,
            "scope": "Results-related sections read; not a claim to have read every page of the paper",
        })
    manifest = {
        "indexed_at_utc": datetime.now(timezone.utc).isoformat(),
        "collection_date_local": "2026-11-09", "paper_count": len(records),
        "selection": "Purposive writing reference sample covering legal QA, retrieval, reranking, RAG and evaluation; not a systematic review",
        "version_rule": "Downloads requested by unversioned ID; version pinned from arXiv identifier printed inside each saved PDF",
        "page_rule": "PDF physical page index, one-based, not journal or proceedings page numbers",
        "extraction_tool": "pypdf", "papers": records,
    }
    (ROOT / "papers-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Indexed {len(records)} PDFs, {sum(r['pdf_pages'] for r in records)} total pages")


if __name__ == "__main__":
    main()

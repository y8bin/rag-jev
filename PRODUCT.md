# Product

<!-- impeccable:product-schema 1 -->

## Platform

web (local viewer served by the Python CLI; Python CLI remains the experiment runner)

## Stack

Delegated: Python standard-library HTTP server inside the existing `legal_rag_jev` package (`legal-rag viewer`) plus static HTML/CSS/JS with no build step. Chosen so teammates need no new dependency and no data leaves their machine.

## Users

Research teammates on the Legal RAG / Jev project, on their own machines. They expect the RAG system to feel like the chatbots they use: the main screen is asking a question and seeing the generated answers. They (1) ask ad-hoc questions against a chosen config and compare how the five conditions select evidence and answer, and (2) review runs produced by `legal-rag run`, `sweep`, `retrieve`, or `demo` in the same question→answer form: candidates, per-method ranking and selection, answers, costs, failures. They also compare YAML experiment configs.

## Product Purpose

Make the CLI's JSON/JSONL outputs (`results/**/manifest.json`, `completion.json`, `raw.jsonl`, `metrics.jsonl`, `summary.json`, `statistics.json`) and `configs/*.yaml` inspectable without reading raw files. Success: a teammate can tell within seconds whether a run is research-valid, complete, and comparable, and drill into any question.

## Positioning

The experiment compares five methods over the same Qdrant candidate pool (Vector, CE-R, CE-FR, Jev-R, Jev-FR). The viewer's job is to keep that shared-pool comparison visible: same candidates, different selections.

## Constraints

- Local only. Raw results contain questions and source text; the viewer binds to 127.0.0.1 by default and never modifies experiment runs.
- Ad-hoc questions make real provider calls (embedding, CE, Jev, generation) and cost money; the UI says so before asking. They are exploration records saved under `results/_explore/`, never research evidence, never mixed into metrics, statistics, or thresholds.
- Never present mock/demo output (`research_valid: false`) or missing human judgments as findings. Show metric denominators (`*_n`) and `null` as missing, not zero.
- `final_research_strategy.md` is the authority for terminology; README defines file formats.
- Korean-language UI.

## Open decisions

- Whether a shared team-hosted instance is needed later (not now).

"""Local structural checks, never a substitute for legal review or API evidence."""
from pathlib import Path

from .config import Config, pricing, provider_headers, provider_identity
from .corpus import load_documents, load_queries, validate_dataset
from .io import environment_manifest, file_hash, read_jsonl, write_json
from .schema import Chunk


def readiness(cfg: Config, output: str | None = None) -> dict:
    checks, issues = {}, []
    for name in ("documents", "chunks", "queries"):
        path = Path(getattr(cfg, name))
        checks[name] = {"path": str(path), "exists": path.is_file()}
        if path.is_file():
            checks[name]["sha256"] = file_hash(path)
        else:
            issues.append({"code": "missing_input", "item": name, "path": str(path)})
    if all(checks[name]["exists"] for name in ("documents", "chunks", "queries")):
        try:
            checks["dataset"] = validate_dataset(
                [Chunk.model_validate(x).json_record() for x in read_jsonl(cfg.chunks)],
                load_queries(cfg.queries), load_documents(cfg.documents))
        except ValueError as e:
            issues.append({"code": "invalid_dataset", "detail": str(e)})
    checks["index_manifest"] = {"path": str(Path(cfg.index_dir)/"manifest.json"),
                                "exists": (Path(cfg.index_dir)/"manifest.json").is_file()}
    if not checks["index_manifest"]["exists"]:
        issues.append({"code": "index_not_built"})
    if cfg.qdrant_source != "managed":
        issues.append({"code": "exploration_index_not_research_snapshot"})
    kinds = ["embedding"] + (["ce"] if any(m.startswith("ce") for m in cfg.methods) else []) + (
        ["jev"] if any(m.startswith("jev") for m in cfg.methods) else []) + (["generation"] if cfg.generate else [])
    checks["providers"] = {}
    for kind in kinds:
        backend = getattr(cfg, kind + "_backend")
        try:
            identity = provider_identity(kind, backend)
            checks["providers"][kind] = {"backend": backend, "identity_configured": True}
            if backend == "mock":
                issues.append({"code": "synthetic_provider", "item": kind})
            if backend == "openai":
                try:
                    provider_headers(kind, identity)
                    checks["providers"][kind]["credentials_configured"] = True
                except ValueError:
                    checks["providers"][kind]["credentials_configured"] = False
                    issues.append({"code": "provider_credentials_missing", "item": kind})
        except ValueError:
            checks["providers"][kind] = {"backend": backend, "identity_configured": False}
            issues.append({"code": "provider_identity_missing_or_invalid", "item": kind})
    try:
        prices = pricing()
        required = {("local_usd_per_hour", None)} if cfg.qdrant_mode == "local" else {("qdrant_usd_per_hour", None)}
        for kind in kinds:
            backend = getattr(cfg, kind + "_backend")
            if backend == "local":
                required.add(("local_usd_per_hour", None))
            elif backend in ("http", "openai"):
                required.add((kind, "input"))
                if kind == "generation": required.add((kind, "output"))
        missing = [f"{kind}.{field}" if field else kind for kind,field in sorted(required, key=str)
                   if (prices[kind][field] if field else prices[kind]) is None]
        checks["pricing"] = {"missing": missing, "billing_verified": False}
        issues.extend({"code": "missing_price", "item": item} for item in missing)
    except ValueError:
        issues.append({"code": "invalid_price_configuration"})
    for method in cfg.methods:
        if method.endswith("fr") and getattr(cfg, method.split("_")[0] + "_threshold") is None:
            issues.append({"code": "threshold_not_selected", "item": method})
    checks["protocol_documents"] = []
    for path in cfg.protocol_documents:
        exists = Path(path).is_file()
        checks["protocol_documents"].append({"path": path, "exists": exists,
            "sha256": file_hash(path) if exists else None})
        if not exists: issues.append({"code": "missing_protocol_document", "path": path})
    report = {"local_checks_passed": not issues, "checks": checks, "issues": issues,
        "quality_margins": cfg.quality_margins, "environment": environment_manifest(),
        "human_and_external_evidence_required": ["scope_and_rights", "corpus_snapshot_and_source_QA",
            "reviewed_questions_and_sufficient_evidence", "independent_legal_reviewers",
            "real_API_contract_usage_and_billing", "power_and_analysis_plan"],
        "note": "No model or network calls. Presence and structural checks do not establish research validity."}
    if output: write_json(output, report)
    return report

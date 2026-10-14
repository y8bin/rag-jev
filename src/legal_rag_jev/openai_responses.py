"""Strict wire contracts for independent OpenAI Responses calls."""
from __future__ import annotations

import json
from typing import Literal

from pydantic import Field

from .schema import Answer, Claim, Record


class ResponseClaim(Claim):
    evidence_ids: list[str] = Field(...)


class ResponseAnswer(Answer):
    # Structured Outputs requires every property, including local optional defaults.
    rationale: str = Field(...)
    claims: list[ResponseClaim] = Field(...)
    citations: list[str] = Field(...)


class CitationJudgment(Record):
    evidence_id: str
    supported: bool


class ClaimJudgment(Record):
    support: Literal["supported", "unsupported", "contradicted"]
    citations: list[CitationJudgment]


class JudgeResponse(Record):
    correctness: bool
    core_supported: bool
    claim_labels: list[ClaimJudgment]


def response_model(kind: str):
    return {"generation": ResponseAnswer, "judge": JudgeResponse}[kind]


def response_format(kind: str) -> dict:
    return {"type": "json_schema", "name": "legal_rag_" + kind,
            "schema": response_model(kind).model_json_schema(), "strict": True}


def parse_response(kind: str, data: dict) -> dict:
    status = data.get("status")
    if status == "incomplete":
        details = data.get("incomplete_details") or {}
        reason = details.get("reason") if isinstance(details, dict) else None
        if reason == "max_output_tokens":
            raise ValueError(f"OpenAI {kind}: incomplete (max_output_tokens); increase max_output_tokens, which includes reasoning tokens")
        raise ValueError(f"OpenAI {kind}: incomplete response (content_filter or unknown reason)")
    if status != "completed":
        label = status if status in ("failed", "cancelled", "queued", "in_progress") else "invalid status"
        raise ValueError(f"OpenAI {kind}: {label}; no completed answer")
    parts = []
    try:
        output = data["output"]
        if not isinstance(output, list):
            raise TypeError
        for item in output:
            # Reasoning items may precede the assistant message; output[0] is not the answer.
            if item["type"] != "message":
                continue
            if item.get("role") != "assistant" or item.get("status", "completed") != "completed":
                raise TypeError
            if not isinstance(item["content"], list):
                raise TypeError
            for part in item["content"]:
                if part["type"] == "refusal":
                    raise ValueError(f"OpenAI {kind}: refused request; no structured answer")
                if part["type"] == "output_text":
                    if not isinstance(part["text"], str):
                        raise TypeError
                    parts.append(part["text"])
    except (KeyError, TypeError) as e:
        raise ValueError(f"OpenAI {kind}: invalid output message") from e
    if not parts:
        raise ValueError(f"OpenAI {kind}: no output_text in completed response")
    try:
        value = json.loads("".join(parts))
    except ValueError as e:
        raise ValueError(f"OpenAI {kind}: invalid JSON output") from e
    try:
        return response_model(kind).model_validate(value, strict=True).json_record()
    except ValueError as e:
        raise ValueError(f"OpenAI {kind}: output does not match {response_model(kind).__name__} schema") from e

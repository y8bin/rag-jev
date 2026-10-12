from __future__ import annotations

from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    def json_record(self) -> dict:
        return self.model_dump(mode="json")


class Document(Record):
    doc_id: str = Field(min_length=1)
    version_id: str = Field(min_length=1)
    group_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    title: str = ""
    doc_type: str = "other"
    jurisdiction: str = ""
    citation_key: str = ""
    source_uri: str = ""
    source_hash: str = ""
    collected_at: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None # exclusive upper bound

    @model_validator(mode="after")
    def valid_dates(self):
        if self.effective_from and self.effective_to and self.effective_from >= self.effective_to:
            raise ValueError("effective_to is exclusive and must be after effective_from")
        return self


class Chunk(Document):
    chunk_id: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text_hash: str
    chunking_version: str = "structure-v1"

    @model_validator(mode="after")
    def valid_offsets(self):
        if self.end <= self.start or self.end - self.start != len(self.text):
            raise ValueError("Chunk offsets must exactly match canonical text length")
        from .io import digest
        if self.text_hash != digest(self.text):
            raise ValueError("Chunk text_hash mismatch")
        return self


class EvidenceUnit(Record):
    unit_id: str
    chunk_ids: list[str] = Field(default_factory=list)
    doc_id: str | None = None
    version_id: str | None = None
    start: int | None = None
    end: int | None = None

    @model_validator(mode="after")
    def valid_reference(self):
        if not self.chunk_ids and (not self.doc_id or not self.version_id or self.start is None or self.end is None):
            raise ValueError("evidence unit needs chunk_ids or doc_id/version_id/start/end")
        if self.start is not None and (self.end is None or self.start < 0 or self.end <= self.start):
            raise ValueError("invalid evidence span")
        return self


class Query(Record):
    query_id: str = Field(min_length=1)
    group_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    split: Literal["pilot", "dev", "test"]
    answerable: bool
    as_of_date: date | None = None
    jurisdiction: str = ""
    task_type: str = "legal_qa"
    reference_answer: str = ""
    evidence_units: list[EvidenceUnit] = Field(default_factory=list)
    sufficient_sets: list[list[str]] = Field(default_factory=list)
    relevance: dict[str, Literal[0, 1, 2]] = Field(default_factory=dict)
    annotation_version: str = "v1"

    @model_validator(mode="after")
    def valid_gold(self):
        ids = [u.unit_id for u in self.evidence_units]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate evidence unit")
        for s in self.sufficient_sets:
            if not s or set(s) - set(ids):
                raise ValueError("sufficient_sets must contain nonempty known unit IDs")
        if self.answerable and not self.sufficient_sets:
            raise ValueError("answerable queries require sufficient_sets")
        if not self.answerable and (self.evidence_units or self.sufficient_sets):
            raise ValueError("unanswerable queries cannot contain gold evidence")
        return self


class Claim(Record):
    text: str
    evidence_ids: list[str] = Field(default_factory=list)


class Answer(Record):
    answer: str
    rationale: str = ""
    claims: list[Claim] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    abstained: bool

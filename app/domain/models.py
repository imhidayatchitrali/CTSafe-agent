from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import (
    DocumentStatus,
    IndexStatus,
    PatchStatus,
    ProjectStatus,
    QAStatus,
    Role,
    SectionStatus,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


REQUIRED_COMPANY_FIELDS = (
    "company_name",
    "vat_number",
    "ateco_code",
    "activity_description",
    "employee_count",
    "mansions",
    "site_address",
    "document_type",
    "risk_category",
    "sector_hazards",
    "risks_by_mansion",
    "normative_references",
)


class Actor(BaseModel):
    user_id: str
    role: Role


class CompanyInput(BaseModel):
    company_name: str | None = None
    vat_number: str | None = None
    ateco_code: str | None = None
    activity_description: str | None = None
    employee_count: int | None = None
    mansions: list[str] = Field(default_factory=list)
    site_address: str | None = None
    document_type: str | None = None
    risk_category: str | None = None
    sector_hazards: list[str] = Field(default_factory=list)
    risks_by_mansion: dict[str, list[str]] = Field(default_factory=dict)
    normative_references: list[str] = Field(default_factory=list)
    notes: str | None = None

    @field_validator("employee_count")
    @classmethod
    def employee_count_must_be_positive(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("employee_count must be greater than or equal to zero")
        return value

    def missing_required_fields(self) -> list[str]:
        missing: list[str] = []
        for field_name in REQUIRED_COMPANY_FIELDS:
            value = getattr(self, field_name)
            if value is None or value == "" or value == [] or value == {}:
                missing.append(field_name)
        return missing


class CompanyRecord(CompanyInput):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class DvrProjectRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID
    company: CompanyRecord
    status: ProjectStatus
    source_channel: str = "api"
    created_by: str
    confirmed_by: str | None = None
    confirmed_at: datetime | None = None
    source_airtable_record_id: str | None = None
    legacy_airtable_status: str | None = None
    active_index_id: UUID | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class IntakeRequest(BaseModel):
    company: CompanyInput
    source_channel: str = "api"


class IntakeResult(BaseModel):
    status: ProjectStatus
    missing_fields: list[str]
    summary: dict[str, Any]


class CreateProjectRequest(IntakeRequest):
    pass


class DvrIndexSectionBrief(BaseModel):
    section_number: str
    title: str
    purpose: str
    required_company_data: list[str] = Field(default_factory=list)
    retrieval_hints: list[str] = Field(default_factory=list)
    target_length: str = "1-2 pagine"
    include_tables: bool = False
    notes: str | None = None


class DvrIndexRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    version: int = 1
    status: IndexStatus = IndexStatus.draft
    title: str = "Indice DVR preliminare"
    sections: list[DvrIndexSectionBrief]
    rag_evidence_ids: list[str] = Field(default_factory=list)
    approved_by: str | None = None
    approved_at: datetime | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class IndexReviewRequest(BaseModel):
    decision: IndexStatus
    reviewer_notes: str | None = None


class EvidenceChunk(BaseModel):
    chunk_id: str
    corpus: str
    content: str
    score: float
    rank: int
    source_document: str | None = None
    source_page: int | None = None
    line_from: int | None = None
    line_to: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    decision: str = "supporting"


class RagSearchInput(BaseModel):
    query: str
    corpus: str = "normativa"
    filters: dict[str, Any] = Field(default_factory=dict)
    top_k: int = Field(default=4, ge=1, le=20)


class RagSearchResult(BaseModel):
    query: str
    corpus: str
    filters: dict[str, Any]
    retrieval_policy_version: str
    evidence: list[EvidenceChunk]
    is_mock: bool = True
    is_fallback: bool = False
    fallback_reason: str | None = None


class SectionRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    index_id: UUID
    section_number: str
    title: str
    brief: DvrIndexSectionBrief
    status: SectionStatus = SectionStatus.planned
    generated_markdown: str | None = None
    qa_status: QAStatus | None = None
    qa_report: dict[str, Any] = Field(default_factory=dict)
    missing_data: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class SectionEvidenceRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    section_id: UUID
    chunk_id: str
    query: str
    filters: dict[str, Any] = Field(default_factory=dict)
    score: float
    rank: int
    source_document: str | None = None
    source_page: int | None = None
    line_from: int | None = None
    line_to: int | None = None
    decision: str = "used"
    claim_or_section_part_supported: str | None = None
    retrieval_policy_version: str
    created_at: datetime = Field(default_factory=utcnow)


class SectionEvidenceWriteInput(BaseModel):
    project_id: UUID
    section_id: UUID
    search_result: RagSearchResult
    claim_or_section_part_supported: str | None = None


class SectionEvidenceWriteResult(BaseModel):
    saved_count: int
    evidence: list[SectionEvidenceRecord]


class DocxRenderInput(BaseModel):
    project: DvrProjectRecord
    sections: list[SectionRecord]
    output_dir: Path
    template_path: Path | None = None
    version: int = 1


class DocxRenderResult(BaseModel):
    document_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    path: Path
    version: int
    format: str = "docx"
    editable: bool = True
    warnings: list[str] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class GeneratedDocumentRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    version: int
    status: DocumentStatus = DocumentStatus.draft
    file_path: Path
    file_format: str = "docx"
    editable: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str
    created_at: datetime = Field(default_factory=utcnow)


class DocumentPatchRequest(BaseModel):
    instruction: str
    target_section_id: UUID | None = None


class DocumentPatchRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    target_section_id: UUID | None = None
    instruction: str
    status: PatchStatus = PatchStatus.proposed
    proposed_patch: dict[str, Any] = Field(default_factory=dict)
    created_by: str
    created_at: datetime = Field(default_factory=utcnow)


class AirtableSyncInput(BaseModel):
    project: DvrProjectRecord


class AirtableSyncResult(BaseModel):
    status: str
    legacy_record_id: str | None = None
    message: str
    is_mock: bool = True


class AgentRunRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID | None = None
    agent_name: str
    input: dict[str, Any]
    output: dict[str, Any]
    status: str
    model: str
    llm_provider: str
    llm_provider_mode: str = "mock"
    tokens_input: int | None = None
    tokens_output: int | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class AuditEventRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID | None = None
    actor_user_id: str
    actor_role: Role
    action: str
    target_type: str | None = None
    target_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)


class ChannelEventRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    channel: str
    external_event_id: str | None = None
    actor_user_id: str | None = None
    normalized_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.domain.models import (
    AgentRunRecord,
    AuditEventRecord,
    ChannelEventRecord,
    CompanyRecord,
    DocumentPatchRecord,
    DvrIndexRecord,
    DvrProjectRecord,
    GeneratedDocumentRecord,
    SectionEvidenceRecord,
    SectionRecord,
)


@dataclass
class RuntimeStore:
    companies: dict[UUID, CompanyRecord] = field(default_factory=dict)
    projects: dict[UUID, DvrProjectRecord] = field(default_factory=dict)
    indexes: dict[UUID, DvrIndexRecord] = field(default_factory=dict)
    sections: dict[UUID, SectionRecord] = field(default_factory=dict)
    section_evidence: list[SectionEvidenceRecord] = field(default_factory=list)
    generated_documents: dict[UUID, GeneratedDocumentRecord] = field(default_factory=dict)
    document_patches: dict[UUID, DocumentPatchRecord] = field(default_factory=dict)
    agent_runs: list[AgentRunRecord] = field(default_factory=list)
    audit_events: list[AuditEventRecord] = field(default_factory=list)
    channel_events: list[ChannelEventRecord] = field(default_factory=list)


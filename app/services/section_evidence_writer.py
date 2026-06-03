from __future__ import annotations

from app.domain.models import (
    SectionEvidenceRecord,
    SectionEvidenceWriteInput,
    SectionEvidenceWriteResult,
)
from app.repositories.store import RuntimeStore


class SectionEvidenceWriter:
    def __init__(self, store: RuntimeStore):
        self.store = store

    def save(self, request: SectionEvidenceWriteInput) -> SectionEvidenceWriteResult:
        saved: list[SectionEvidenceRecord] = []
        for chunk in request.search_result.evidence:
            record = SectionEvidenceRecord(
                project_id=request.project_id,
                section_id=request.section_id,
                chunk_id=chunk.chunk_id,
                query=request.search_result.query,
                filters=request.search_result.filters,
                score=chunk.score,
                rank=chunk.rank,
                source_document=chunk.source_document,
                source_page=chunk.source_page,
                line_from=chunk.line_from,
                line_to=chunk.line_to,
                decision="used",
                claim_or_section_part_supported=request.claim_or_section_part_supported,
                retrieval_policy_version=request.search_result.retrieval_policy_version,
            )
            self.store.section_evidence.append(record)
            saved.append(record)
        return SectionEvidenceWriteResult(saved_count=len(saved), evidence=saved)


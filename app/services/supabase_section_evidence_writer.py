from __future__ import annotations

from typing import Any

from app.domain.models import (
    SectionEvidenceRecord,
    SectionEvidenceWriteInput,
    SectionEvidenceWriteResult,
)
from app.repositories.supabase_rest_client import SupabaseRestClient


class SupabaseSectionEvidenceWriter:
    def __init__(self, client: SupabaseRestClient):
        self.client = client

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
            row = self.client.insert("section_evidence", self._record_to_row(record))
            saved.append(SectionEvidenceRecord(**row))
        return SectionEvidenceWriteResult(saved_count=len(saved), evidence=saved)

    def _record_to_row(self, record: SectionEvidenceRecord) -> dict[str, Any]:
        return record.model_dump(mode="json")

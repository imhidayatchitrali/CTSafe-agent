from __future__ import annotations

from typing import Any
from uuid import UUID

from app.domain.enums import SectionStatus
from app.domain.models import DvrIndexSectionBrief, SectionRecord, utcnow
from app.repositories.store import RuntimeStore
from app.repositories.supabase_rest_client import SupabaseRestClient


class SupabaseSectionRepository:
    def __init__(self, client: SupabaseRestClient):
        self.client = client
        self.store = RuntimeStore()

    def create_section(
        self,
        project_id: UUID,
        index_id: UUID,
        brief: DvrIndexSectionBrief,
    ) -> SectionRecord:
        section = SectionRecord(
            project_id=project_id,
            index_id=index_id,
            section_number=brief.section_number,
            title=brief.title,
            brief=brief,
            status=SectionStatus.planned,
        )
        return self._section_from_row(
            self.client.insert("dvr_sections", self._section_to_row(section))
        )

    def get_section(self, section_id: UUID) -> SectionRecord:
        return self._section_from_row(
            self.client.select_one("dvr_sections", {"id": section_id})
        )

    def list_sections_for_project(self, project_id: UUID) -> list[SectionRecord]:
        rows = self.client.select(
            "dvr_sections",
            {"project_id": project_id},
            order="section_number.asc",
        )
        return [self._section_from_row(row) for row in rows]

    def save_section(self, section: SectionRecord) -> SectionRecord:
        section.updated_at = utcnow()
        return self._section_from_row(
            self.client.update(
                "dvr_sections",
                {"id": section.id},
                self._section_to_row(section, include_id=False),
            )
        )

    def _section_to_row(
        self, section: SectionRecord, include_id: bool = True
    ) -> dict[str, Any]:
        row = section.model_dump(mode="json")
        if not include_id:
            row.pop("id", None)
        return row

    def _section_from_row(self, row: dict[str, Any]) -> SectionRecord:
        return SectionRecord(**row)

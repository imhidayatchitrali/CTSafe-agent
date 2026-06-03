from __future__ import annotations

from uuid import UUID

from app.domain.enums import SectionStatus
from app.domain.models import DvrIndexSectionBrief, SectionRecord, utcnow
from app.repositories.store import RuntimeStore


class SectionRepository:
    def __init__(self, store: RuntimeStore):
        self.store = store

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
        self.store.sections[section.id] = section
        return section

    def get_section(self, section_id: UUID) -> SectionRecord:
        return self.store.sections[section_id]

    def list_sections_for_project(self, project_id: UUID) -> list[SectionRecord]:
        sections = [
            section
            for section in self.store.sections.values()
            if section.project_id == project_id
        ]
        return sorted(sections, key=lambda item: item.section_number)

    def save_section(self, section: SectionRecord) -> SectionRecord:
        section.updated_at = utcnow()
        self.store.sections[section.id] = section
        return section


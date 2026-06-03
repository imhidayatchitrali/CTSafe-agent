from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from app.domain.enums import DocumentStatus, IndexStatus, ProjectStatus
from app.domain.models import (
    Actor,
    AgentRunRecord,
    AuditEventRecord,
    CompanyInput,
    CompanyRecord,
    DocumentPatchRecord,
    DvrIndexRecord,
    DvrProjectRecord,
    GeneratedDocumentRecord,
    utcnow,
)
from app.repositories.store import RuntimeStore
from app.repositories.supabase_rest_client import SupabaseRestClient


class SupabaseProjectRepository:
    """Supabase-backed implementation of the project repository contract."""

    def __init__(self, client: SupabaseRestClient):
        self.client = client
        self.store = RuntimeStore()

    def create_project(
        self,
        company_input: CompanyInput,
        actor: Actor,
        source_channel: str,
    ) -> DvrProjectRecord:
        company = CompanyRecord(**company_input.model_dump())
        company = self._company_from_row(
            self.client.insert("companies", self._company_to_row(company))
        )
        project = DvrProjectRecord(
            company_id=company.id,
            company=company,
            status=ProjectStatus.intake_pending_confirmation,
            source_channel=source_channel,
            created_by=actor.user_id,
        )
        project = self._project_from_row(
            self.client.insert("dvr_projects", self._project_to_row(project)),
            company=company,
        )
        self.add_audit_event(
            actor=actor,
            action="project.create",
            project_id=project.id,
            target_type="dvr_project",
            target_id=str(project.id),
        )
        return project

    def get_project(self, project_id: UUID) -> DvrProjectRecord:
        row = self.client.select_one("dvr_projects", {"id": project_id})
        company = self._company_from_row(
            self.client.select_one("companies", {"id": row["company_id"]})
        )
        return self._project_from_row(row, company=company)

    def save_project(self, project: DvrProjectRecord) -> DvrProjectRecord:
        project.updated_at = utcnow()
        row = self.client.update(
            "dvr_projects",
            {"id": project.id},
            self._project_to_row(project, include_id=False),
        )
        return self._project_from_row(row, company=project.company)

    def confirm_project(self, project_id: UUID, actor: Actor) -> DvrProjectRecord:
        project = self.get_project(project_id)
        project.status = ProjectStatus.data_confirmed
        project.confirmed_by = actor.user_id
        project.confirmed_at = utcnow()
        project = self.save_project(project)
        self.add_audit_event(
            actor=actor,
            action="project.confirm",
            project_id=project.id,
            target_type="dvr_project",
            target_id=str(project.id),
        )
        return project

    def attach_airtable_sync(
        self, project_id: UUID, legacy_record_id: str, legacy_status: str
    ) -> DvrProjectRecord:
        project = self.get_project(project_id)
        project.source_airtable_record_id = legacy_record_id
        project.legacy_airtable_status = legacy_status
        return self.save_project(project)

    def save_index(self, index: DvrIndexRecord) -> DvrIndexRecord:
        saved = self._index_from_row(
            self.client.insert("dvr_indexes", self._index_to_row(index))
        )
        project = self.get_project(saved.project_id)
        project.status = ProjectStatus.index_draft
        project.active_index_id = saved.id
        self.save_project(project)
        return saved

    def get_index(self, index_id: UUID) -> DvrIndexRecord:
        return self._index_from_row(self.client.select_one("dvr_indexes", {"id": index_id}))

    def get_active_index(self, project_id: UUID) -> DvrIndexRecord | None:
        project = self.get_project(project_id)
        if project.active_index_id is None:
            return None
        return self.get_index(project.active_index_id)

    def review_index(
        self,
        index_id: UUID,
        decision: IndexStatus,
        actor: Actor,
        notes: str | None,
    ) -> DvrIndexRecord:
        index = self.get_index(index_id)
        payload: dict[str, Any] = {
            "status": decision.value,
            "notes": notes,
            "updated_at": utcnow().isoformat(),
        }
        if decision is IndexStatus.approved:
            payload["approved_by"] = actor.user_id
            payload["approved_at"] = utcnow().isoformat()
        index = self._index_from_row(
            self.client.update("dvr_indexes", {"id": index_id}, payload)
        )

        project = self.get_project(index.project_id)
        project.status = (
            ProjectStatus.index_approved
            if decision is IndexStatus.approved
            else ProjectStatus.index_needs_revision
        )
        self.save_project(project)
        self.add_audit_event(
            actor=actor,
            action=f"index.{decision.value}",
            project_id=project.id,
            target_type="dvr_index",
            target_id=str(index.id),
            metadata={"notes": notes},
        )
        return index

    def save_generated_document(
        self, document: GeneratedDocumentRecord
    ) -> GeneratedDocumentRecord:
        saved = self._document_from_row(
            self.client.insert(
                "generated_documents",
                self._document_to_row(document),
            )
        )
        if saved.status is DocumentStatus.draft:
            project = self.get_project(saved.project_id)
            project.status = ProjectStatus.draft_document_created
            self.save_project(project)
        return saved

    def list_generated_documents_for_project(
        self, project_id: UUID
    ) -> list[GeneratedDocumentRecord]:
        rows = self.client.select(
            "generated_documents",
            {"project_id": project_id},
            order="version.asc",
        )
        return [self._document_from_row(row) for row in rows]

    def save_patch(self, patch: DocumentPatchRecord) -> DocumentPatchRecord:
        saved = self._patch_from_row(
            self.client.insert("document_patches", self._patch_to_row(patch))
        )
        project = self.get_project(saved.project_id)
        project.status = ProjectStatus.needs_revision
        self.save_project(project)
        return saved

    def add_agent_run(self, run: AgentRunRecord) -> AgentRunRecord:
        return self._agent_run_from_row(
            self.client.insert("agent_runs", self._agent_run_to_row(run))
        )

    def add_audit_event(
        self,
        actor: Actor,
        action: str,
        project_id: UUID | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        metadata: dict | None = None,
    ) -> AuditEventRecord:
        event = AuditEventRecord(
            project_id=project_id,
            actor_user_id=actor.user_id,
            actor_role=actor.role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata or {},
        )
        return self._audit_event_from_row(
            self.client.insert("audit_events", self._audit_event_to_row(event))
        )

    def _company_to_row(
        self, company: CompanyRecord, include_id: bool = True
    ) -> dict[str, Any]:
        row = company.model_dump(mode="json")
        if not include_id:
            row.pop("id", None)
        return row

    def _company_from_row(self, row: dict[str, Any]) -> CompanyRecord:
        return CompanyRecord(**row)

    def _project_to_row(
        self, project: DvrProjectRecord, include_id: bool = True
    ) -> dict[str, Any]:
        row = project.model_dump(mode="json", exclude={"company"})
        if not include_id:
            row.pop("id", None)
        return row

    def _project_from_row(
        self, row: dict[str, Any], company: CompanyRecord
    ) -> DvrProjectRecord:
        return DvrProjectRecord(**row, company=company)

    def _index_to_row(self, index: DvrIndexRecord) -> dict[str, Any]:
        return index.model_dump(mode="json")

    def _index_from_row(self, row: dict[str, Any]) -> DvrIndexRecord:
        return DvrIndexRecord(**row)

    def _document_to_row(self, document: GeneratedDocumentRecord) -> dict[str, Any]:
        row = document.model_dump(mode="json")
        row["file_path"] = str(document.file_path)
        return row

    def _document_from_row(self, row: dict[str, Any]) -> GeneratedDocumentRecord:
        return GeneratedDocumentRecord(**{**row, "file_path": Path(row["file_path"])})

    def _patch_to_row(self, patch: DocumentPatchRecord) -> dict[str, Any]:
        return patch.model_dump(mode="json")

    def _patch_from_row(self, row: dict[str, Any]) -> DocumentPatchRecord:
        return DocumentPatchRecord(**row)

    def _agent_run_to_row(self, run: AgentRunRecord) -> dict[str, Any]:
        return run.model_dump(mode="json")

    def _agent_run_from_row(self, row: dict[str, Any]) -> AgentRunRecord:
        return AgentRunRecord(**row)

    def _audit_event_to_row(self, event: AuditEventRecord) -> dict[str, Any]:
        return event.model_dump(mode="json")

    def _audit_event_from_row(self, row: dict[str, Any]) -> AuditEventRecord:
        return AuditEventRecord(**row)

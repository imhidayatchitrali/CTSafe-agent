from __future__ import annotations

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


class ProjectRepository:
    """Typed project/state repository boundary.

    The thin slice uses an in-memory store. The method contracts are shaped so a
    Supabase implementation can replace this without changing workflow code.
    """

    def __init__(self, store: RuntimeStore):
        self.store = store

    def create_project(
        self,
        company_input: CompanyInput,
        actor: Actor,
        source_channel: str,
    ) -> DvrProjectRecord:
        company = CompanyRecord(**company_input.model_dump())
        project = DvrProjectRecord(
            company_id=company.id,
            company=company,
            status=ProjectStatus.intake_pending_confirmation,
            source_channel=source_channel,
            created_by=actor.user_id,
        )
        self.store.companies[company.id] = company
        self.store.projects[project.id] = project
        self.add_audit_event(
            actor=actor,
            action="project.create",
            project_id=project.id,
            target_type="dvr_project",
            target_id=str(project.id),
        )
        return project

    def get_project(self, project_id: UUID) -> DvrProjectRecord:
        return self.store.projects[project_id]

    def save_project(self, project: DvrProjectRecord) -> DvrProjectRecord:
        project.updated_at = utcnow()
        self.store.projects[project.id] = project
        return project

    def confirm_project(self, project_id: UUID, actor: Actor) -> DvrProjectRecord:
        project = self.get_project(project_id)
        project.status = ProjectStatus.data_confirmed
        project.confirmed_by = actor.user_id
        project.confirmed_at = utcnow()
        self.save_project(project)
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
        self.store.indexes[index.id] = index
        project = self.get_project(index.project_id)
        project.status = ProjectStatus.index_draft
        project.active_index_id = index.id
        self.save_project(project)
        return index

    def get_index(self, index_id: UUID) -> DvrIndexRecord:
        return self.store.indexes[index_id]

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
        index.status = decision
        index.notes = notes
        if decision is IndexStatus.approved:
            index.approved_by = actor.user_id
            index.approved_at = utcnow()
        index.updated_at = utcnow()
        self.store.indexes[index.id] = index

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
        self.store.generated_documents[document.id] = document
        project = self.get_project(document.project_id)
        if document.status is DocumentStatus.draft:
            project.status = ProjectStatus.draft_document_created
            self.save_project(project)
        return document

    def list_generated_documents_for_project(
        self, project_id: UUID
    ) -> list[GeneratedDocumentRecord]:
        return [
            document
            for document in self.store.generated_documents.values()
            if document.project_id == project_id
        ]

    def save_patch(self, patch: DocumentPatchRecord) -> DocumentPatchRecord:
        self.store.document_patches[patch.id] = patch
        project = self.get_project(patch.project_id)
        project.status = ProjectStatus.needs_revision
        self.save_project(project)
        return patch

    def add_agent_run(self, run: AgentRunRecord) -> AgentRunRecord:
        self.store.agent_runs.append(run)
        return run

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
        self.store.audit_events.append(event)
        return event

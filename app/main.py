from __future__ import annotations

from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException

from app.agno_runtime import create_agno_runtime, get_agno_runtime_mode, maybe_wrap_agentos
from app.domain.enums import IndexStatus, Role
from app.domain.models import (
    Actor,
    CreateProjectRequest,
    DocumentPatchRequest,
    IndexReviewRequest,
    IntakeRequest,
    RagSearchInput,
)
from app.errors import WorkflowError
from app.repositories.factory import create_repository_bundle
from app.security import require_roles
from app.services.airtable_sync_service import AirtableSyncService
from app.services.doctor_service import DvrDoctorService
from app.services.docx_render_service import DocxRenderService
from app.services.rag_factory import create_rag_search_tool
from app.settings import AppSettings, get_settings
from app.workflows.dvr_workflow import DvrWorkflow


def _raise_workflow_error(exc: WorkflowError) -> None:
    raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})


def create_app(settings: AppSettings | None = None) -> FastAPI:
    settings = settings or get_settings()
    repositories = create_repository_bundle(settings)
    workflow = DvrWorkflow(
        settings=settings,
        project_repository=repositories.project_repository,
        section_repository=repositories.section_repository,
        rag_search_tool=create_rag_search_tool(
            settings,
            supabase_client=repositories.supabase_client,
        ),
        evidence_writer=repositories.evidence_writer,
        docx_render_service=DocxRenderService(),
        airtable_sync_service=AirtableSyncService(enabled=False),
    )
    agno_runtime = create_agno_runtime(settings, workflow)
    doctor = DvrDoctorService(settings, repositories.store)

    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.state.store = repositories.store
    app.state.repositories = repositories
    app.state.workflow = workflow
    app.state.agno_runtime = agno_runtime
    app.state.doctor = doctor

    def get_workflow() -> DvrWorkflow:
        return app.state.workflow

    def get_doctor() -> DvrDoctorService:
        return app.state.doctor

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "app": settings.app_name,
            "environment": settings.environment,
            "agno_runtime": agno_runtime.mode,
            "repository_backend": repositories.backend,
            "rag_backend": settings.rag_backend,
            "supabase_enabled": bool(
                settings.supabase_url and settings.supabase_service_role_key
            ),
        }

    @app.get("/api/dvr/runtime")
    def runtime_status(
        actor: Actor = Depends(require_roles(Role.admin)),
    ) -> dict:
        return {
            "requested_by": actor.user_id,
            "agentos_mount": get_agno_runtime_mode(),
            "runtime_mode": agno_runtime.mode,
            "agents": [getattr(agent, "name", "unknown") for agent in agno_runtime.agents],
            "workflows": [
                getattr(runtime_workflow, "name", "unknown")
                for runtime_workflow in agno_runtime.workflows
            ],
            "storage": "postgres" if agno_runtime.storage is not None else "memory",
        }

    @app.post("/api/dvr/rag/search")
    def rag_search(
        request: RagSearchInput,
        actor: Actor = Depends(require_roles(Role.ctsafe_reviewer, Role.admin)),
        dvr_workflow: DvrWorkflow = Depends(get_workflow),
    ) -> dict:
        result = dvr_workflow.rag_search_tool.search(request)
        return {"actor": actor, "search_result": result}

    @app.get("/doctor")
    def doctor_endpoint(
        actor: Actor = Depends(require_roles(Role.admin)),
        doctor_service: DvrDoctorService = Depends(get_doctor),
    ) -> dict:
        result = doctor_service.run()
        result["requested_by"] = actor.user_id
        return result

    @app.post("/api/dvr/intake")
    def intake(
        request: IntakeRequest,
        actor: Actor = Depends(
            require_roles(Role.client_user, Role.ctsafe_reviewer, Role.admin)
        ),
        dvr_workflow: DvrWorkflow = Depends(get_workflow),
    ) -> dict:
        result = dvr_workflow.intake(request.company)
        return {"actor": actor, "intake": result}

    @app.post("/api/dvr/projects")
    def create_project(
        request: CreateProjectRequest,
        actor: Actor = Depends(
            require_roles(Role.client_user, Role.ctsafe_reviewer, Role.admin)
        ),
        dvr_workflow: DvrWorkflow = Depends(get_workflow),
    ) -> dict:
        try:
            project = dvr_workflow.create_project(
                company=request.company,
                source_channel=request.source_channel,
                actor=actor,
            )
        except WorkflowError as exc:
            _raise_workflow_error(exc)
        return {"project": project}

    @app.get("/api/dvr/projects/{project_id}")
    def get_project(
        project_id: UUID,
        actor: Actor = Depends(
            require_roles(Role.client_user, Role.ctsafe_reviewer, Role.admin)
        ),
        dvr_workflow: DvrWorkflow = Depends(get_workflow),
    ) -> dict:
        project = dvr_workflow.project_repository.get_project(project_id)
        return {"actor": actor, "project": project}

    @app.post("/api/dvr/projects/{project_id}/confirm")
    def confirm_project(
        project_id: UUID,
        actor: Actor = Depends(
            require_roles(Role.client_user, Role.ctsafe_reviewer, Role.admin)
        ),
        dvr_workflow: DvrWorkflow = Depends(get_workflow),
    ) -> dict:
        try:
            return dvr_workflow.confirm_project(project_id, actor)
        except WorkflowError as exc:
            _raise_workflow_error(exc)

    @app.post("/api/dvr/projects/{project_id}/index")
    def generate_index(
        project_id: UUID,
        actor: Actor = Depends(
            require_roles(Role.client_user, Role.ctsafe_reviewer, Role.admin)
        ),
        dvr_workflow: DvrWorkflow = Depends(get_workflow),
    ) -> dict:
        try:
            index = dvr_workflow.generate_index(project_id, actor)
        except WorkflowError as exc:
            _raise_workflow_error(exc)
        return {"index": index}

    @app.post("/api/dvr/projects/{project_id}/index/{index_id}/review")
    def review_index(
        project_id: UUID,
        index_id: UUID,
        request: IndexReviewRequest,
        actor: Actor = Depends(require_roles(Role.ctsafe_reviewer, Role.admin)),
        dvr_workflow: DvrWorkflow = Depends(get_workflow),
    ) -> dict:
        try:
            index = dvr_workflow.review_index(
                project_id=project_id,
                index_id=index_id,
                decision=IndexStatus(request.decision),
                actor=actor,
                notes=request.reviewer_notes,
            )
        except WorkflowError as exc:
            _raise_workflow_error(exc)
        return {"index": index}

    @app.post("/api/dvr/projects/{project_id}/sections/pilot")
    def generate_pilot_sections(
        project_id: UUID,
        actor: Actor = Depends(require_roles(Role.ctsafe_reviewer, Role.admin)),
        dvr_workflow: DvrWorkflow = Depends(get_workflow),
    ) -> dict:
        try:
            sections = dvr_workflow.generate_pilot_sections(project_id, actor)
        except WorkflowError as exc:
            _raise_workflow_error(exc)
        return {"sections": sections}

    @app.post("/api/dvr/projects/{project_id}/documents/draft")
    def generate_docx_draft(
        project_id: UUID,
        actor: Actor = Depends(require_roles(Role.ctsafe_reviewer, Role.admin)),
        dvr_workflow: DvrWorkflow = Depends(get_workflow),
    ) -> dict:
        try:
            document = dvr_workflow.generate_docx_draft(project_id, actor)
        except WorkflowError as exc:
            _raise_workflow_error(exc)
        return {"document": document}

    @app.post("/api/dvr/projects/{project_id}/patches")
    def request_patch(
        project_id: UUID,
        request: DocumentPatchRequest,
        actor: Actor = Depends(
            require_roles(Role.client_user, Role.ctsafe_reviewer, Role.admin)
        ),
        dvr_workflow: DvrWorkflow = Depends(get_workflow),
    ) -> dict:
        try:
            patch = dvr_workflow.request_patch(project_id, request, actor)
        except WorkflowError as exc:
            _raise_workflow_error(exc)
        return {"patch": patch}

    return maybe_wrap_agentos(app, settings.enable_agentos, agno_runtime)


app = create_app()

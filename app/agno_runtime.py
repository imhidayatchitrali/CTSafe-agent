from __future__ import annotations

import logging
import inspect
import json
from dataclasses import dataclass
from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi import FastAPI

from app.domain.enums import IndexStatus, Role
from app.domain.models import (
    Actor,
    CompanyInput,
    DocumentPatchRequest,
    DocumentPatchRecord,
    DvrIndexRecord,
    IntakeResult,
    SectionRecord,
)
from app.errors import WorkflowError
from app.settings import AppSettings
from app.workflows.dvr_workflow import DvrWorkflow

logger = logging.getLogger(__name__)


AGNO_RUNTIME_MODE = "disabled"


def get_agno_runtime_mode() -> str:
    return AGNO_RUNTIME_MODE


def _get_agno_workflow_base() -> type:
    try:
        from agno.workflow.workflow import Workflow

        return Workflow
    except Exception:
        return object


@dataclass
class DvrAgnoRuntime:
    agents: list[Any]
    workflows: list[Any]
    storage: Any | None
    mode: str

    @property
    def workflow(self) -> Any | None:
        if not self.workflows:
            return None
        return self.workflows[0]


class CtsafeDvrAgnoWorkflow(_get_agno_workflow_base()):
    """Agno Workflow wrapper around the governed DVR application workflow.

    The wrapper keeps the production state transitions in `DvrWorkflow`, adds a
    direct-call AuthGate, and exposes a typed action surface for AgentOS without
    broad MCP tools. Constructor kwargs are filtered at runtime because local
    development may still have Agno 1.x while `uv.lock` resolves Agno 2.x.
    """

    description = (
        "Governed CT Safe DVR workflow: intake, confirmation, index approval, "
        "pilot sections, DOCX draft and targeted patch proposal."
    )

    def __init__(
        self,
        settings: AppSettings,
        dvr_workflow: DvrWorkflow,
        storage: Any | None = None,
    ) -> None:
        self.settings = settings
        self.dvr_workflow = dvr_workflow
        workflow_kwargs = _filter_supported_kwargs(
            super().__init__,
            name="ctsafe-dvr-workflow",
            id="ctsafe-dvr-workflow",
            workflow_id="ctsafe-dvr-workflow",
            description=self.description,
            db=storage,
            storage=storage,
            debug_mode=settings.environment == "local",
            telemetry=False,
        )
        try:
            super().__init__(**workflow_kwargs)
        except TypeError as exc:
            logger.warning(
                "agno.workflow_base_init_failed",
                extra={"error": str(exc), "workflow_kwargs": workflow_kwargs},
            )

    def __deepcopy__(self, memo: dict[int, Any]) -> "CtsafeDvrAgnoWorkflow":
        copied = type(self)(
            settings=self.settings,
            dvr_workflow=self.dvr_workflow,
            storage=getattr(self, "db", None) or getattr(self, "storage", None),
        )
        memo[id(self)] = copied
        return copied

    def deep_copy(self, *, update: dict[str, Any] | None = None) -> "CtsafeDvrAgnoWorkflow":
        copied = type(self)(
            settings=self.settings,
            dvr_workflow=self.dvr_workflow,
            storage=getattr(self, "db", None) or getattr(self, "storage", None),
        )
        for key, value in (update or {}).items():
            setattr(copied, key, value)
        return copied

    def run(
        self,
        action: str | None = None,
        payload: dict[str, Any] | None = None,
        actor: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        action, payload, actor = _normalize_workflow_call(
            action=action,
            payload=payload,
            actor=actor,
            kwargs=kwargs,
        )
        run_response = _make_run_response()
        try:
            content = self._dispatch(action=action, payload=payload, actor=actor)
            run_response.content = content
            run_response.content_type = "json"
            _set_run_response_status(run_response, "completed")
            return run_response
        except WorkflowError as exc:
            run_response.content = {
                "status": "error",
                "code": exc.code,
                "message": exc.message,
                "status_code": exc.status_code,
            }
            run_response.content_type = "json"
            _set_run_response_status(run_response, "error")
            return run_response

    async def arun(
        self,
        input: Any | None = None,
        action: str | None = None,
        payload: dict[str, Any] | None = None,
        actor: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        if input is not None:
            kwargs.setdefault("input", input)
        return self.run(action=action, payload=payload, actor=actor, **kwargs)

    def _dispatch(
        self,
        action: str,
        payload: dict[str, Any],
        actor: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if action == "intake":
            result = self.dvr_workflow.intake(CompanyInput(**payload["company"]))
            return _dump_model(result)

        actor_model = self._require_actor(actor)
        self._require_action_role(action, actor_model)

        if action == "create_project":
            project = self.dvr_workflow.create_project(
                company=CompanyInput(**payload["company"]),
                source_channel=str(payload.get("source_channel", "agentos")),
                actor=actor_model,
            )
            return _dump_model(project)

        project_id = UUID(str(payload["project_id"]))

        if action == "confirm_project":
            return _dump_dict(self.dvr_workflow.confirm_project(project_id, actor_model))
        if action == "generate_index":
            return _dump_model(self.dvr_workflow.generate_index(project_id, actor_model))
        if action == "review_index":
            index = self.dvr_workflow.review_index(
                project_id=project_id,
                index_id=UUID(str(payload["index_id"])),
                decision=IndexStatus(str(payload["decision"])),
                actor=actor_model,
                notes=payload.get("reviewer_notes"),
            )
            return _dump_model(index)
        if action == "generate_pilot_sections":
            sections = self.dvr_workflow.generate_pilot_sections(project_id, actor_model)
            return {"sections": [_dump_model(section) for section in sections]}
        if action == "generate_docx_draft":
            return _dump_model(self.dvr_workflow.generate_docx_draft(project_id, actor_model))
        if action == "request_patch":
            patch = self.dvr_workflow.request_patch(
                project_id=project_id,
                request=DocumentPatchRequest(**payload["patch"]),
                actor=actor_model,
            )
            return _dump_model(patch)

        raise WorkflowError(
            code="unsupported_agno_action",
            message=f"Unsupported Agno DVR workflow action: {action}",
            status_code=422,
        )

    def _require_actor(self, actor: dict[str, Any] | None) -> Actor:
        if actor is None:
            raise WorkflowError(
                code="actor_required",
                message="Direct Agno workflow calls require an actor payload.",
                status_code=401,
            )
        actor_model = Actor(**actor)
        if actor_model.user_id not in self.settings.allowed_operator_ids:
            raise WorkflowError(
                code="actor_not_allowed",
                message="Actor is not allowed to run the DVR workflow.",
                status_code=401,
            )
        return actor_model

    def _require_action_role(self, action: str, actor: Actor) -> None:
        allowed_roles = {
            "create_project": {Role.client_user, Role.ctsafe_reviewer, Role.admin},
            "confirm_project": {Role.client_user, Role.ctsafe_reviewer, Role.admin},
            "generate_index": {Role.client_user, Role.ctsafe_reviewer, Role.admin},
            "request_patch": {Role.client_user, Role.ctsafe_reviewer, Role.admin},
            "review_index": {Role.ctsafe_reviewer, Role.admin},
            "generate_pilot_sections": {Role.ctsafe_reviewer, Role.admin},
            "generate_docx_draft": {Role.ctsafe_reviewer, Role.admin},
        }
        roles = allowed_roles.get(action)
        if roles is None:
            return
        if actor.role not in roles:
            raise WorkflowError(
                code="role_not_authorized",
                message=f"Role {actor.role.value} cannot run {action}.",
                status_code=403,
            )


def create_agno_runtime(settings: AppSettings, workflow: DvrWorkflow) -> DvrAgnoRuntime:
    agents = _build_agents(settings)
    storage = _build_workflow_storage(settings)
    agno_workflow = CtsafeDvrAgnoWorkflow(
        settings=settings,
        dvr_workflow=workflow,
        storage=storage,
    )
    return DvrAgnoRuntime(
        agents=agents,
        workflows=[agno_workflow],
        storage=storage,
        mode="postgres" if storage is not None else "memory",
    )


def maybe_wrap_agentos(
    app: FastAPI,
    enabled: bool,
    runtime: DvrAgnoRuntime | None = None,
) -> FastAPI:
    global AGNO_RUNTIME_MODE
    AGNO_RUNTIME_MODE = "disabled"

    if not enabled:
        return app
    if runtime is None:
        logger.warning("agno.runtime.enabled_without_runtime")
        return app

    try:
        from agno.os import AgentOS

        agent_os = AgentOS(
            **_filter_supported_kwargs(
                AgentOS,
                description="CT Safe DVR AgentOS runtime",
                workflows=runtime.workflows,
                base_app=app,
                on_route_conflict="preserve_base_app",
            )
        )
        AGNO_RUNTIME_MODE = "agentos"
        return agent_os.get_app()
    except Exception as exc:
        logger.info("agno.agentos_unavailable_using_playground", extra={"error": str(exc)})

    try:
        from agno.playground.playground import Playground

        playground = Playground(
            workflows=runtime.workflows,
            api_app=app,
        )
        AGNO_RUNTIME_MODE = "playground"
        return playground.get_app(prefix="/agno/v1")
    except Exception as exc:
        logger.warning("agno.playground_unavailable", extra={"error": str(exc)})
        return app


def _build_agents(settings: AppSettings) -> list[Any]:
    try:
        from agno.agent import Agent
    except Exception:
        return []

    return [
        _make_agent(
            Agent,
            agent_id="ctsafe-intake-agent",
            name="CT Safe IntakeAgent",
            role="Extract company data and report missing required fields.",
            instructions=[
                "Use only user-provided company facts.",
                "Return structured output and keep missing data explicit.",
            ],
            response_model=IntakeResult,
            settings=settings,
        ),
        _make_agent(
            Agent,
            agent_id="ctsafe-index-draft-agent",
            name="CT Safe IndexDraftAgent",
            role="Draft a DVR index from company facts and RAG evidence.",
            instructions=[
                "Separate normative evidence from template examples.",
                "Do not generate full chapter prose during index drafting.",
            ],
            response_model=DvrIndexRecord,
            settings=settings,
        ),
        _make_agent(
            Agent,
            agent_id="ctsafe-chapter-writer-agent",
            name="CT Safe ChapterWriterAgent",
            role="Write governed DVR sections with saved evidence.",
            instructions=[
                "Connect risks to mansions, activity, equipment or exposure.",
                "Mark weak evidence and missing data instead of inventing facts.",
            ],
            response_model=SectionRecord,
            settings=settings,
        ),
        _make_agent(
            Agent,
            agent_id="ctsafe-revision-agent",
            name="CT Safe RevisionAgent",
            role="Interpret targeted revision requests and propose patches.",
            instructions=[
                "Target one section when possible.",
                "Propose a patch for human QA instead of applying silently.",
            ],
            response_model=DocumentPatchRecord,
            settings=settings,
        ),
    ]


def _make_agent(
    Agent: Any,
    *,
    agent_id: str,
    name: str,
    role: str,
    instructions: list[str],
    response_model: type,
    settings: AppSettings,
) -> Any:
    base_kwargs = {
        "id": agent_id,
        "agent_id": agent_id,
        "name": name,
        "role": role,
        "instructions": instructions,
        "markdown": True,
        "debug_mode": settings.environment == "local",
        "telemetry": False,
    }
    output_kwargs = {
        "output_schema": response_model,
        "response_model": response_model,
        "structured_outputs": True,
    }
    return Agent(**_filter_supported_kwargs(Agent, **base_kwargs, **output_kwargs))


def _build_workflow_storage(settings: AppSettings) -> Any | None:
    if settings.agno_db_url is None:
        return None
    try:
        from agno.db.postgres import PostgresDb

        return PostgresDb(
            **_filter_supported_kwargs(
                PostgresDb,
                db_url=settings.agno_db_url,
                db_schema=settings.agno_db_schema,
                schema=settings.agno_db_schema,
            )
        )
    except Exception as exc:
        logger.info("agno.postgres_db_unavailable", extra={"error": str(exc)})

    try:
        from agno.storage.workflow.postgres import PostgresWorkflowStorage

        return PostgresWorkflowStorage(
            table_name="agno_workflow_sessions",
            schema=settings.agno_db_schema,
            db_url=settings.agno_db_url,
            mode="workflow",
        )
    except Exception as exc:
        logger.warning("agno.workflow_storage_unavailable", extra={"error": str(exc)})
        return None


def _make_run_response() -> Any:
    try:
        from agno.run.workflow import WorkflowRunOutput

        return WorkflowRunOutput()
    except Exception:
        pass

    try:
        from agno.run.response import RunResponse

        return RunResponse()
    except Exception:
        return _FallbackRunResponse()


class _FallbackRunResponse:
    def __init__(self) -> None:
        self.content: Any | None = None
        self.content_type = "json"
        self.status = "COMPLETED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "content_type": self.content_type,
            "status": self.status,
        }


def _set_run_response_status(run_response: Any, status: str) -> None:
    status_value: Any = status.upper()
    try:
        from agno.run.base import RunStatus

        status_value = getattr(RunStatus, status)
    except Exception:
        pass
    try:
        run_response.status = status_value
    except Exception:
        pass


def _dump_model(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return dict(model)


def _dump_dict(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: _dump_model(value) if hasattr(value, "model_dump") else value
        for key, value in payload.items()
    }


def _filter_supported_kwargs(callable_obj: Callable[..., Any], **kwargs: Any) -> dict[str, Any]:
    try:
        signature = inspect.signature(callable_obj)
    except (TypeError, ValueError):
        return kwargs
    parameters = signature.parameters
    if any(parameter.kind is inspect.Parameter.VAR_KEYWORD for parameter in parameters.values()):
        return kwargs
    return {key: value for key, value in kwargs.items() if key in parameters}


def _normalize_workflow_call(
    *,
    action: str | None,
    payload: dict[str, Any] | None,
    actor: dict[str, Any] | None,
    kwargs: dict[str, Any],
) -> tuple[str, dict[str, Any], dict[str, Any] | None]:
    parsed_action_payload = _parse_workflow_input(action)
    if parsed_action_payload is not None:
        action = parsed_action_payload.get("action", action)
        payload = parsed_action_payload.get("payload", payload)
        actor = parsed_action_payload.get("actor", actor)

    if action is None and "input" in kwargs:
        workflow_input = _parse_workflow_input(kwargs["input"])
        if workflow_input is not None:
            action = workflow_input.get("action")
            payload = workflow_input.get("payload", payload)
            actor = workflow_input.get("actor", actor)
    if action is None and "message" in kwargs:
        workflow_message = _parse_workflow_input(kwargs["message"])
        if workflow_message is not None:
            action = workflow_message.get("action")
            payload = workflow_message.get("payload", payload)
            actor = workflow_message.get("actor", actor)
    if action is None and "execution_input" in kwargs:
        execution_input = kwargs["execution_input"]
        raw_input = getattr(execution_input, "input", None)
        workflow_input = _parse_workflow_input(raw_input)
        if workflow_input is not None:
            action = workflow_input.get("action")
            payload = workflow_input.get("payload", payload)
            actor = workflow_input.get("actor", actor)
    if action is None:
        raise WorkflowError(
            code="action_required",
            message="Agno DVR workflow calls require an action.",
            status_code=422,
        )
    if payload is None:
        payload = {}
    return action, payload, actor


def _parse_workflow_input(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped.startswith("{"):
        return None
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None

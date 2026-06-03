from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:  # pragma: no cover
    find_dotenv = None  # type: ignore[assignment]
    load_dotenv = None  # type: ignore[assignment]

if load_dotenv is not None and find_dotenv is not None:
    env_path = find_dotenv()
    if env_path:
        load_dotenv(env_path)

from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    app_name: str = Field(default="CT Safe DVR Agent")
    environment: str = Field(default="local")
    supabase_url: str | None = Field(default=None)
    supabase_service_role_key: str | None = Field(default=None, repr=False)
    agno_db_url: str | None = Field(default=None, repr=False)
    agno_db_schema: str = Field(default="ai")
    repository_backend: str = Field(default="memory")
    rag_backend: str = Field(default="mock")
    openai_api_key: str | None = Field(default=None, repr=False)
    openrouter_api_key: str | None = Field(default=None, repr=False)
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")
    openrouter_http_referer: str | None = Field(default=None)
    openrouter_app_title: str = Field(default="CT Safe DVR Agent")
    embedding_provider: str = Field(default="openai_api")
    embedding_model: str = Field(default="text-embedding-3-small")
    rag_allow_fallback: bool = Field(default=True)
    rag_version: str = Field(default="legacy")
    rag_v2_legacy_fallback: bool = Field(default=True)
    airtable_api_key: str | None = Field(default=None, repr=False)
    airtable_base_id: str | None = Field(default=None)
    output_dir: Path = Field(default=Path("generated_documents"))
    template_path: Path = Field(
        default=Path("esempi dvr per template") / "01_DVR-spheractsafe (1).docx"
    )
    allowed_operator_ids: tuple[str, ...] = Field(
        default=("local-client", "local-reviewer", "local-admin")
    )
    default_llm_provider: str = Field(default="local_mock")
    default_model: str = Field(default="mock-deterministic-v1")
    subscription_bridge_enabled: bool = Field(default=False)
    subscription_bridge_url: str | None = Field(default=None)
    subscription_bridge_session_ref: str | None = Field(default=None, repr=False)
    subscription_bridge_healthcheck_required: bool = Field(default=True)
    rag_policy_version: str = Field(default="rag_policy_v0_1")
    prompt_version: str = Field(default="prompts_v0_1")
    enable_agentos: bool = Field(default=False)


def _csv_tuple(value: str | None, fallback: tuple[str, ...]) -> tuple[str, ...]:
    if value is None or value.strip() == "":
        return fallback
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _supabase_credentials_available() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))


def _choose_backend(env_name: str, default: str, supabase_default: str) -> str:
    explicit_value = os.getenv(env_name)
    if explicit_value is not None:
        return explicit_value
    if _supabase_credentials_available():
        return supabase_default
    return default


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    defaults = AppSettings()
    return AppSettings(
        app_name=os.getenv("DVR_APP_NAME", defaults.app_name),
        environment=os.getenv("DVR_ENV", defaults.environment),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        agno_db_url=os.getenv("DVR_AGNO_DB_URL"),
        agno_db_schema=os.getenv("DVR_AGNO_DB_SCHEMA", defaults.agno_db_schema),
        repository_backend=_choose_backend(
            "DVR_REPOSITORY_BACKEND", defaults.repository_backend, "supabase"
        ),
        rag_backend=_choose_backend("DVR_RAG_BACKEND", defaults.rag_backend, "supabase"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY") or os.getenv("OPEN_ROUTER_KEY"),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", defaults.openrouter_base_url),
        openrouter_http_referer=os.getenv("OPENROUTER_HTTP_REFERER"),
        openrouter_app_title=os.getenv(
            "OPENROUTER_APP_TITLE", defaults.openrouter_app_title
        ),
        embedding_provider=os.getenv(
            "DVR_EMBEDDING_PROVIDER", defaults.embedding_provider
        ),
        embedding_model=os.getenv("DVR_EMBEDDING_MODEL", defaults.embedding_model),
        rag_allow_fallback=os.getenv("DVR_RAG_ALLOW_FALLBACK", "true").lower()
        in {"1", "true", "yes"},
        rag_version=os.getenv("DVR_RAG_VERSION", defaults.rag_version),
        rag_v2_legacy_fallback=os.getenv("DVR_RAG_V2_LEGACY_FALLBACK", "true").lower()
        in {"1", "true", "yes"},
        airtable_api_key=os.getenv("AIRTABLE_API_KEY"),
        airtable_base_id=os.getenv("AIRTABLE_BASE_ID"),
        output_dir=Path(os.getenv("DVR_OUTPUT_DIR", str(defaults.output_dir))),
        template_path=Path(os.getenv("DVR_TEMPLATE_PATH", str(defaults.template_path))),
        allowed_operator_ids=_csv_tuple(
            os.getenv("DVR_ALLOWED_OPERATOR_IDS"), defaults.allowed_operator_ids
        ),
        default_llm_provider=os.getenv(
            "DVR_DEFAULT_LLM_PROVIDER", defaults.default_llm_provider
        ),
        default_model=os.getenv("DVR_DEFAULT_MODEL", defaults.default_model),
        subscription_bridge_enabled=os.getenv(
            "OPENAI_SUBSCRIPTION_BRIDGE_ENABLED", "false"
        ).lower()
        in {"1", "true", "yes"},
        subscription_bridge_url=os.getenv("OPENAI_SUBSCRIPTION_BRIDGE_URL"),
        subscription_bridge_session_ref=os.getenv("OPENAI_SUBSCRIPTION_BRIDGE_SESSION_REF"),
        subscription_bridge_healthcheck_required=os.getenv(
            "OPENAI_SUBSCRIPTION_BRIDGE_HEALTHCHECK_REQUIRED", "true"
        ).lower()
        in {"1", "true", "yes"},
        rag_policy_version=os.getenv(
            "DVR_RAG_POLICY_VERSION", defaults.rag_policy_version
        ),
        prompt_version=os.getenv("DVR_PROMPT_VERSION", defaults.prompt_version),
        enable_agentos=os.getenv("DVR_ENABLE_AGENTOS", "false").lower()
        in {"1", "true", "yes"},
    )

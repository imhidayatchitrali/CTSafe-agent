from __future__ import annotations

from pathlib import Path

from app.repositories.store import RuntimeStore
from app.settings import AppSettings


class DvrDoctorService:
    def __init__(self, settings: AppSettings, store: RuntimeStore):
        self.settings = settings
        self.store = store

    def run(self) -> dict:
        template_path = Path(self.settings.template_path)
        subscription_bridge_selected = (
            self.settings.default_llm_provider == "openai_subscription_bridge"
        )
        subscription_bridge_ready = (
            self.settings.subscription_bridge_enabled
            and bool(self.settings.subscription_bridge_url)
        )
        openrouter_selected = self.settings.default_llm_provider == "openrouter"
        openrouter_ready = bool(self.settings.openrouter_api_key)
        embedding_provider_ready = (
            self.settings.rag_backend == "mock"
            or (
                self.settings.embedding_provider == "openrouter"
                and bool(self.settings.openrouter_api_key)
            )
            or (
                self.settings.embedding_provider == "openai_api"
                and bool(self.settings.openai_api_key)
            )
        )
        checks = [
            {
                "name": "environment",
                "status": "ok",
                "message": self.settings.environment,
            },
            {
                "name": "supabase_config",
                "status": "warning" if not self.settings.supabase_url else "ok",
                "message": "Supabase URL configured"
                if self.settings.supabase_url
                else "Supabase URL missing; repository is running in local mock mode.",
            },
            {
                "name": "repository_backend",
                "status": "ok"
                if self.settings.repository_backend == "supabase"
                and self.settings.supabase_url
                and self.settings.supabase_service_role_key
                else (
                    "ok"
                    if self.settings.repository_backend == "memory"
                    else "warning"
                ),
                "message": self.settings.repository_backend,
            },
            {
                "name": "agno_workflow_storage",
                "status": "ok" if self.settings.agno_db_url else "warning",
                "message": "Agno workflow Postgres storage configured"
                if self.settings.agno_db_url
                else "Agno workflow runs use local memory unless DVR_AGNO_DB_URL is configured.",
            },
            {
                "name": "airtable_mode",
                "status": "warning",
                "message": "Airtable sync is mocked unless a narrow adapter is configured.",
            },
            {
                "name": "template_reference",
                "status": "ok" if template_path.exists() else "warning",
                "message": str(template_path),
            },
            {
                "name": "rag_policy",
                "status": "warning" if self.settings.rag_backend == "mock" else "ok",
                "message": (
                    "RAG is deterministic mock evidence."
                    if self.settings.rag_backend == "mock"
                    else (
                        f"RAG backend configured: {self.settings.rag_backend}; "
                        f"version={self.settings.rag_version}"
                    )
                ),
            },
            {
                "name": "llm_provider",
                "status": "warning"
                if (
                    subscription_bridge_selected
                    and not subscription_bridge_ready
                    or openrouter_selected
                    and not openrouter_ready
                )
                else "ok",
                "message": self.settings.default_llm_provider,
            },
            {
                "name": "openrouter_provider",
                "status": "warning" if openrouter_selected and not openrouter_ready else "ok",
                "message": (
                    "OpenRouter selected and API key configured."
                    if openrouter_selected and openrouter_ready
                    else (
                        "OpenRouter selected but OPENROUTER_API_KEY/OPEN_ROUTER_KEY is missing."
                        if openrouter_selected
                        else "OpenRouter not selected as LLM provider."
                    )
                ),
            },
            {
                "name": "openai_subscription_bridge",
                "status": "warning"
                if subscription_bridge_selected and not subscription_bridge_ready
                else "ok",
                "message": (
                    "Subscription bridge selected; configure bridge URL/session and health checks."
                    if subscription_bridge_selected and not subscription_bridge_ready
                    else (
                        "Subscription bridge enabled."
                        if subscription_bridge_selected
                        else "Subscription bridge not selected."
                    )
                ),
            },
            {
                "name": "rag_embeddings",
                "status": "ok" if embedding_provider_ready else "warning",
                "message": (
                    f"{self.settings.embedding_provider}:{self.settings.embedding_model}"
                    if embedding_provider_ready
                    else (
                        "Query embedding provider missing for Supabase RAG; "
                        "this is separate from the LLM generation provider."
                    )
                ),
            },
            {
                "name": "pending_approvals",
                "status": "ok",
                "message": f"{len(self.store.indexes)} indexes tracked.",
            },
        ]
        status = "warning" if any(check["status"] == "warning" for check in checks) else "ok"
        return {
            "status": status,
            "checks": checks,
            "safe_actions": [],
            "approval_required_actions": [
                "enable_live_supabase_writes",
                "enable_airtable_write_sync",
                "change_rag_policy",
                "change_docx_template",
            ],
        }

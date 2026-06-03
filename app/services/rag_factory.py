from __future__ import annotations

from app.repositories.supabase_rest_client import SupabaseRestClient
from app.services.embedding_provider import OpenAIEmbeddingProvider, OpenRouterEmbeddingProvider
from app.services.rag_search_tool import RagSearchTool
from app.settings import AppSettings


def create_rag_search_tool(
    settings: AppSettings,
    supabase_client: SupabaseRestClient | None = None,
) -> RagSearchTool:
    backend = settings.rag_backend.lower()
    if backend == "mock":
        return RagSearchTool(
            retrieval_policy_version=settings.rag_policy_version,
            backend="mock",
        )

    if backend == "supabase":
        client = supabase_client
        if client is None and settings.supabase_url and settings.supabase_service_role_key:
            client = SupabaseRestClient(
                supabase_url=settings.supabase_url,
                api_key=settings.supabase_service_role_key,
            )
        embedding_provider = _create_embedding_provider(settings)
        return RagSearchTool(
            retrieval_policy_version=settings.rag_policy_version,
            backend="supabase",
            supabase_client=client,
            embedding_provider=embedding_provider,
            allow_fallback=settings.rag_allow_fallback,
            rag_version=settings.rag_version,
            rag_v2_legacy_fallback=settings.rag_v2_legacy_fallback,
        )

    raise ValueError(f"Unsupported DVR_RAG_BACKEND: {settings.rag_backend!r}")


def _create_embedding_provider(settings: AppSettings) -> object | None:
    provider = settings.embedding_provider.lower()
    if provider == "openrouter":
        if not settings.openrouter_api_key:
            return None
        return OpenRouterEmbeddingProvider(
            api_key=settings.openrouter_api_key,
            model=settings.embedding_model,
            base_url=settings.openrouter_base_url,
            http_referer=settings.openrouter_http_referer,
            app_title=settings.openrouter_app_title,
        )
    if provider == "openai_api":
        if not settings.openai_api_key:
            return None
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.embedding_model,
        )
    raise ValueError(f"Unsupported DVR_EMBEDDING_PROVIDER: {settings.embedding_provider!r}")

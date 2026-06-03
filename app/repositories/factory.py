from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.repositories.project_repository import ProjectRepository
from app.repositories.section_repository import SectionRepository
from app.repositories.store import RuntimeStore
from app.repositories.supabase_project_repository import SupabaseProjectRepository
from app.repositories.supabase_rest_client import SupabaseRestClient
from app.repositories.supabase_section_repository import SupabaseSectionRepository
from app.services.section_evidence_writer import SectionEvidenceWriter
from app.services.supabase_section_evidence_writer import SupabaseSectionEvidenceWriter
from app.settings import AppSettings


@dataclass
class RepositoryBundle:
    backend: str
    store: RuntimeStore
    project_repository: Any
    section_repository: Any
    evidence_writer: Any
    supabase_client: SupabaseRestClient | None = None


def create_repository_bundle(settings: AppSettings) -> RepositoryBundle:
    backend = settings.repository_backend.lower()
    if backend == "memory":
        store = RuntimeStore()
        return RepositoryBundle(
            backend="memory",
            store=store,
            project_repository=ProjectRepository(store),
            section_repository=SectionRepository(store),
            evidence_writer=SectionEvidenceWriter(store),
        )

    if backend == "supabase":
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ValueError(
                "DVR_REPOSITORY_BACKEND=supabase requires SUPABASE_URL and "
                "SUPABASE_SERVICE_ROLE_KEY in the backend environment."
            )
        client = SupabaseRestClient(
            supabase_url=settings.supabase_url,
            api_key=settings.supabase_service_role_key,
        )
        return RepositoryBundle(
            backend="supabase",
            store=RuntimeStore(),
            project_repository=SupabaseProjectRepository(client),
            section_repository=SupabaseSectionRepository(client),
            evidence_writer=SupabaseSectionEvidenceWriter(client),
            supabase_client=client,
        )

    raise ValueError(
        "DVR_REPOSITORY_BACKEND must be 'memory' or 'supabase', "
        f"got {settings.repository_backend!r}."
    )

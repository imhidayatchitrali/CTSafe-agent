from __future__ import annotations

import asyncio
import json
import shutil
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.domain.enums import ProjectStatus, QAStatus, SectionStatus
from app.domain.models import (
    Actor,
    AirtableSyncInput,
    CompanyInput,
    CompanyRecord,
    DocxRenderInput,
    DvrIndexSectionBrief,
    DvrProjectRecord,
    RagSearchInput,
    SectionEvidenceWriteInput,
    SectionRecord,
)
from app.main import create_app
from app.repositories.factory import create_repository_bundle
from app.repositories.project_repository import ProjectRepository
from app.repositories.store import RuntimeStore
from app.repositories.supabase_project_repository import SupabaseProjectRepository
from app.services.airtable_sync_service import AirtableSyncService
from app.services.docx_render_service import DocxRenderService
from app.services.embedding_provider import OpenRouterEmbeddingProvider
from app.services.rag_factory import create_rag_search_tool
from app.services.rag_search_tool import RagSearchTool
from app.services.rag_validation import evaluate_rag_cases, load_rag_eval_cases
from app.services.section_evidence_writer import SectionEvidenceWriter
from app.settings import AppSettings, get_settings


CLIENT_HEADERS = {"X-User-Id": "local-client", "X-Role": "client_user"}
REVIEWER_HEADERS = {"X-User-Id": "local-reviewer", "X-Role": "ctsafe_reviewer"}
ADMIN_HEADERS = {"X-User-Id": "local-admin", "X-Role": "admin"}


class FakeSupabaseRestClient:
    def __init__(self) -> None:
        self.tables: dict[str, list[dict]] = {}

    def insert(self, table: str, payload: dict) -> dict:
        row = dict(payload)
        self.tables.setdefault(table, []).append(row)
        return row

    def select_one(
        self, table: str, filters: dict, select: str = "*"
    ) -> dict:
        rows = self.select(table, filters, select=select, limit=1)
        if not rows:
            raise KeyError(table)
        return rows[0]

    def select(
        self,
        table: str,
        filters: dict | None = None,
        select: str = "*",
        order: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        rows = list(self.tables.get(table, []))
        for key, value in (filters or {}).items():
            rows = [row for row in rows if str(row.get(key)) == str(value)]
        if limit is not None:
            rows = rows[:limit]
        return rows

    def update(self, table: str, filters: dict, payload: dict) -> dict:
        for row in self.tables.get(table, []):
            if all(str(row.get(key)) == str(value) for key, value in filters.items()):
                row.update(payload)
                return dict(row)
        raise KeyError(table)

    def rpc(self, function_name: str, payload: dict) -> list[dict]:
        self.tables.setdefault("rpc_calls", []).append(
            {"function_name": function_name, "payload": payload}
        )
        return [
            {
                "id": "chunk-1",
                "content": "Contenuto normativo recuperato dal corpus Supabase.",
                "similarity": 0.91,
                "metadata": {"source": "D.Lgs. 81/08", "loc": {"pageNumber": 12}},
            }
        ]

    def search_text(
        self,
        table: str,
        terms: list[str],
        select: str = "id,content,metadata",
        limit: int = 10,
    ) -> list[dict]:
        self.tables.setdefault("text_search_calls", []).append(
            {"table": table, "terms": terms, "limit": limit}
        )
        return [
            {
                "id": "lexical-1",
                "content": "DPI, rischi e mansioni devono essere collegati nel DVR.",
                "metadata": {"source": "D.Lgs. 81/08"},
            }
        ]


class FakeEmbeddingProvider:
    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class FakeHttpResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def complete_company_payload() -> dict:
    return {
        "company_name": "ACME Sicurezza SRL",
        "vat_number": "01234567890",
        "ateco_code": "43.29.09",
        "activity_description": "Installazione e manutenzione impianti tecnici",
        "employee_count": 8,
        "mansions": ["tecnico installatore", "impiegato amministrativo"],
        "site_address": "Via Roma 1, Milano",
        "document_type": "DVR nuovo",
        "risk_category": "MEDIO",
        "sector_hazards": ["lavori in quota", "rischio elettrico"],
        "risks_by_mansion": {
            "tecnico installatore": ["caduta dall'alto", "rischio elettrico"]
        },
        "normative_references": ["D.Lgs. 81/08"],
    }


class ThinSliceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(__file__).resolve().parents[1] / ".tmp" / "tests" / str(uuid4())
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        settings = AppSettings(
            output_dir=self.temp_dir,
            allowed_operator_ids=("local-client", "local-reviewer", "local-admin"),
        )
        self.app = create_app(settings)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_schema_model_validation_rejects_negative_employee_count(self) -> None:
        with self.assertRaises(ValidationError):
            CompanyInput(employee_count=-1)

    def test_intake_missing_fields_returns_blocked_status(self) -> None:
        response = self.client.post(
            "/api/dvr/intake",
            headers=CLIENT_HEADERS,
            json={"company": {"company_name": "ACME SRL"}},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["intake"]["status"], ProjectStatus.blocked_missing_data)
        self.assertIn("vat_number", body["intake"]["missing_fields"])

    def test_rag_tool_returns_structured_evidence(self) -> None:
        tool = RagSearchTool("rag_policy_v0_1")
        result = tool.search(RagSearchInput(query="DPI per mansione", corpus="normativa"))

        self.assertTrue(result.evidence)
        self.assertEqual(result.evidence[0].corpus, "normativa")
        self.assertIsInstance(result.evidence[0].chunk_id, str)
        self.assertEqual(result.retrieval_policy_version, "rag_policy_v0_1")

    def test_rag_tool_calls_supabase_rpc_with_embedding_contract(self) -> None:
        client = FakeSupabaseRestClient()
        tool = RagSearchTool(
            "rag_policy_v0_1",
            backend="supabase",
            supabase_client=client,
            embedding_provider=FakeEmbeddingProvider(),
        )

        result = tool.search(
            RagSearchInput(
                query="rischio elettrico",
                corpus="normativa",
                filters={"source_type": "normativa"},
                top_k=1,
            )
        )

        self.assertFalse(result.is_mock)
        self.assertFalse(result.is_fallback)
        self.assertEqual(result.evidence[0].chunk_id, "chunk-1")
        self.assertEqual(result.evidence[0].source_document, "D.Lgs. 81/08")
        self.assertEqual(result.evidence[0].source_page, 12)
        rpc_call = client.tables["rpc_calls"][0]
        self.assertEqual(rpc_call["function_name"], "match_normativa")
        self.assertEqual(rpc_call["payload"]["match_count"], 4)
        self.assertEqual(rpc_call["payload"]["filter"], {})

    def test_rag_tool_can_use_v2_rag_chunks_contract(self) -> None:
        client = FakeSupabaseRestClient()
        tool = RagSearchTool(
            "rag_policy_v0_1",
            backend="supabase",
            supabase_client=client,
            embedding_provider=FakeEmbeddingProvider(),
            rag_version="v2",
            rag_v2_legacy_fallback=False,
        )

        result = tool.search(
            RagSearchInput(
                query="indice DVR DPI",
                corpus="indice",
                filters={"section_type": "dpi"},
                top_k=1,
            )
        )

        self.assertFalse(result.is_mock)
        self.assertFalse(result.is_fallback)
        self.assertEqual(result.evidence[0].corpus, "indice")
        rpc_calls = client.tables["rpc_calls"]
        self.assertEqual(rpc_calls[0]["function_name"], "match_rag_chunks")
        self.assertEqual(rpc_calls[0]["payload"]["corpus_filter"], "indice")
        self.assertEqual(rpc_calls[0]["payload"]["filter"], {"section_type": "dpi"})
        self.assertEqual(rpc_calls[1]["function_name"], "search_rag_chunks_text")
        self.assertEqual(rpc_calls[1]["payload"]["corpus_filter"], "indice")

    def test_rag_tool_v2_can_fall_back_to_legacy_during_migration(self) -> None:
        class MissingV2Client(FakeSupabaseRestClient):
            def rpc(self, function_name: str, payload: dict) -> list[dict]:
                self.tables.setdefault("rpc_calls", []).append(
                    {"function_name": function_name, "payload": payload}
                )
                if function_name == "match_rag_chunks":
                    raise RuntimeError("missing v2 function")
                return [
                    {
                        "id": "legacy-chunk-1",
                        "content": "Contenuto normativo legacy su DPI e mansioni.",
                        "similarity": 0.81,
                        "metadata": {"source": "D.Lgs. 81/08"},
                    }
                ]

        client = MissingV2Client()
        tool = RagSearchTool(
            "rag_policy_v0_1",
            backend="supabase",
            supabase_client=client,
            embedding_provider=FakeEmbeddingProvider(),
            rag_version="v2",
            rag_v2_legacy_fallback=True,
        )

        result = tool.search(
            RagSearchInput(query="DPI mansioni", corpus="normativa", top_k=1)
        )

        self.assertFalse(result.is_fallback)
        function_names = [call["function_name"] for call in client.tables["rpc_calls"]]
        self.assertEqual(function_names[:2], ["match_rag_chunks", "match_normativa"])

    def test_rag_tool_uses_lexical_backfill_when_vector_results_are_weak(self) -> None:
        class WeakVectorClient(FakeSupabaseRestClient):
            def rpc(self, function_name: str, payload: dict) -> list[dict]:
                self.tables.setdefault("rpc_calls", []).append(
                    {"function_name": function_name, "payload": payload}
                )
                return [
                    {
                        "id": "vector-weak",
                        "content": "Contenuto generico senza termini della query.",
                        "similarity": 0.91,
                        "metadata": {"source": "blob"},
                    }
                ]

        client = WeakVectorClient()
        tool = RagSearchTool(
            "rag_policy_v0_1",
            backend="supabase",
            supabase_client=client,
            embedding_provider=FakeEmbeddingProvider(),
        )

        result = tool.search(
            RagSearchInput(
                query="DPI rischi mansioni",
                corpus="normativa",
                top_k=1,
            )
        )

        self.assertEqual(result.evidence[0].chunk_id, "lexical-1")
        self.assertIn("text_search_calls", client.tables)

    def test_rag_factory_uses_openrouter_embedding_provider(self) -> None:
        tool = create_rag_search_tool(
            AppSettings(
                rag_backend="supabase",
                supabase_url="https://example.supabase.co",
                supabase_service_role_key="service-key",
                embedding_provider="openrouter",
                openrouter_api_key="openrouter-key",
                embedding_model="text-embedding-3-small",
            ),
            supabase_client=FakeSupabaseRestClient(),  # type: ignore[arg-type]
        )

        self.assertIsInstance(tool.embedding_provider, OpenRouterEmbeddingProvider)
        self.assertEqual(
            tool.embedding_provider.model,  # type: ignore[union-attr]
            "openai/text-embedding-3-small",
        )

    def test_openrouter_embedding_provider_calls_embeddings_endpoint(self) -> None:
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            captured["authorization"] = request.get_header("Authorization")
            captured["title"] = request.get_header("X-openrouter-title")
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            return FakeHttpResponse({"data": [{"embedding": [0.1, 0.2, 0.3]}]})

        provider = OpenRouterEmbeddingProvider(
            api_key="openrouter-key",
            model="text-embedding-3-small",
            base_url="https://openrouter.ai/api/v1",
            app_title="CT Safe DVR Agent",
        )

        with patch("app.services.embedding_provider.urlopen", fake_urlopen):
            embedding = provider.embed("rischio elettrico")

        self.assertEqual(embedding, [0.1, 0.2, 0.3])
        self.assertEqual(captured["url"], "https://openrouter.ai/api/v1/embeddings")
        self.assertEqual(captured["authorization"], "Bearer openrouter-key")
        self.assertEqual(captured["payload"]["model"], "openai/text-embedding-3-small")

    def test_rag_tool_fallback_returns_empty_evidence_explicitly(self) -> None:
        tool = RagSearchTool("rag_policy_v0_1", backend="supabase")

        result = tool.search(RagSearchInput(query="rischio elettrico", corpus="normativa"))

        self.assertFalse(result.is_mock)
        self.assertTrue(result.is_fallback)
        self.assertEqual(result.evidence, [])
        self.assertEqual(result.fallback_reason, "supabase_rag_not_configured")

    def test_rag_eval_fixture_passes_against_mock_baseline(self) -> None:
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "rag_eval"
            / "dvr_core.json"
        )
        cases = load_rag_eval_cases(fixture_path)
        tool = RagSearchTool("rag_policy_v0_1")

        results = evaluate_rag_cases(tool, cases)

        self.assertTrue(results)
        self.assertTrue(all(result.passed for result in results))

    def test_section_evidence_is_saved(self) -> None:
        store = RuntimeStore()
        writer = SectionEvidenceWriter(store)
        search_result = RagSearchTool("rag_policy_v0_1").search(
            RagSearchInput(query="rischio elettrico", corpus="normativa")
        )

        result = writer.save(
            SectionEvidenceWriteInput(
                project_id=uuid4(),
                section_id=uuid4(),
                search_result=search_result,
                claim_or_section_part_supported="Mansioni e rischi principali",
            )
        )

        self.assertEqual(result.saved_count, len(search_result.evidence))
        self.assertEqual(len(store.section_evidence), result.saved_count)

    def test_index_cannot_proceed_without_approval(self) -> None:
        project_response = self.client.post(
            "/api/dvr/projects",
            headers=CLIENT_HEADERS,
            json={"company": complete_company_payload(), "source_channel": "api"},
        )
        project_id = project_response.json()["project"]["id"]

        self.client.post(f"/api/dvr/projects/{project_id}/confirm", headers=CLIENT_HEADERS)
        self.client.post(f"/api/dvr/projects/{project_id}/index", headers=CLIENT_HEADERS)

        response = self.client.post(
            f"/api/dvr/projects/{project_id}/sections/pilot",
            headers=REVIEWER_HEADERS,
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"]["code"], "index_approval_required")

    def test_docx_draft_service_creates_editable_file(self) -> None:
        company = CompanyRecord(**complete_company_payload())
        project = DvrProjectRecord(
            company_id=company.id,
            company=company,
            status=ProjectStatus.pilot_sections_generated,
            created_by="test",
        )
        brief = DvrIndexSectionBrief(
            section_number="1",
            title="Identificazione dell'attivita",
            purpose="Test",
        )
        section = SectionRecord(
            project_id=project.id,
            index_id=uuid4(),
            section_number="1",
            title=brief.title,
            brief=brief,
            status=SectionStatus.qa_approved,
            qa_status=QAStatus.approved,
            generated_markdown="Contenuto pilota editabile.",
        )

        result = DocxRenderService().render_draft(
            DocxRenderInput(
                project=project,
                sections=[section],
                output_dir=self.temp_dir,
                version=1,
            )
        )

        self.assertTrue(result.editable)
        self.assertTrue(result.path.exists())
        self.assertTrue(zipfile.is_zipfile(result.path))

    def test_unauthorized_action_is_rejected(self) -> None:
        response = self.client.get("/doctor", headers=CLIENT_HEADERS)

        self.assertEqual(response.status_code, 403)

    def test_full_thin_slice_workflow_creates_docx_and_patch(self) -> None:
        project_response = self.client.post(
            "/api/dvr/projects",
            headers=CLIENT_HEADERS,
            json={"company": complete_company_payload(), "source_channel": "api"},
        )
        self.assertEqual(project_response.status_code, 200)
        project_id = project_response.json()["project"]["id"]

        confirm_response = self.client.post(
            f"/api/dvr/projects/{project_id}/confirm", headers=CLIENT_HEADERS
        )
        self.assertEqual(confirm_response.status_code, 200)
        self.assertEqual(confirm_response.json()["airtable_sync"]["status"], "mocked")

        index_response = self.client.post(
            f"/api/dvr/projects/{project_id}/index", headers=CLIENT_HEADERS
        )
        self.assertEqual(index_response.status_code, 200)
        index_id = index_response.json()["index"]["id"]

        approval_response = self.client.post(
            f"/api/dvr/projects/{project_id}/index/{index_id}/review",
            headers=REVIEWER_HEADERS,
            json={"decision": "approved", "reviewer_notes": "Ok per sezioni pilota."},
        )
        self.assertEqual(approval_response.status_code, 200)

        sections_response = self.client.post(
            f"/api/dvr/projects/{project_id}/sections/pilot",
            headers=REVIEWER_HEADERS,
        )
        self.assertEqual(sections_response.status_code, 200)
        self.assertEqual(len(sections_response.json()["sections"]), 2)

        document_response = self.client.post(
            f"/api/dvr/projects/{project_id}/documents/draft",
            headers=REVIEWER_HEADERS,
        )
        self.assertEqual(document_response.status_code, 200)
        document_path = Path(document_response.json()["document"]["file_path"])
        self.assertTrue(document_path.exists())

        patch_response = self.client.post(
            f"/api/dvr/projects/{project_id}/patches",
            headers=CLIENT_HEADERS,
            json={"instruction": "Aggiungi nota sul rischio elettrico nella sezione mansioni."},
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()["patch"]["status"], "proposed")

    def test_airtable_sync_can_be_mocked(self) -> None:
        company = CompanyRecord(**complete_company_payload())
        project = DvrProjectRecord(
            company_id=company.id,
            company=company,
            status=ProjectStatus.data_confirmed,
            created_by="test",
        )
        result = AirtableSyncService(enabled=False).sync_project(
            AirtableSyncInput(project=project)
        )

        self.assertEqual(result.status, "mocked")
        self.assertTrue(result.is_mock)
        self.assertTrue(result.legacy_record_id)

    def test_agno_runtime_factory_exposes_agents_and_workflow(self) -> None:
        runtime = self.app.state.agno_runtime

        self.assertEqual(runtime.mode, "memory")
        self.assertEqual(len(runtime.agents), 4)
        self.assertEqual(runtime.workflow.name, "ctsafe-dvr-workflow")

        response = self.client.get("/api/dvr/runtime", headers=ADMIN_HEADERS)

        self.assertEqual(response.status_code, 200)
        self.assertIn("CT Safe IntakeAgent", response.json()["agents"])
        self.assertEqual(response.json()["storage"], "memory")

    def test_agno_workflow_runs_intake_with_structured_content(self) -> None:
        runtime = self.app.state.agno_runtime
        response = runtime.workflow.run(
            action="intake",
            payload={"company": {"company_name": "ACME SRL"}},
        )

        self.assertEqual(response.content["status"], ProjectStatus.blocked_missing_data)
        self.assertIn("vat_number", response.content["missing_fields"])

    def test_agno_workflow_accepts_agentos_message_json(self) -> None:
        runtime = self.app.state.agno_runtime
        message = json.dumps(
            {
                "action": "intake",
                "payload": {"company": {"company_name": "ACME SRL"}},
            }
        )

        response = runtime.workflow.run(message=message)

        self.assertEqual(response.content["status"], ProjectStatus.blocked_missing_data)
        self.assertIn("vat_number", response.content["missing_fields"])

    def test_agno_workflow_accepts_agentos_async_input_json(self) -> None:
        runtime = self.app.state.agno_runtime
        message = json.dumps(
            {
                "action": "intake",
                "payload": {"company": {"company_name": "ACME SRL"}},
            }
        )

        response = asyncio.run(runtime.workflow.arun(input=message))

        self.assertEqual(response.content["status"], ProjectStatus.blocked_missing_data)
        self.assertIn("vat_number", response.content["missing_fields"])

    def test_agno_workflow_can_be_deep_copied_for_agentos_runs(self) -> None:
        runtime = self.app.state.agno_runtime

        cloned_workflow = runtime.workflow.deep_copy()
        response = cloned_workflow.run(
            action="intake",
            payload={"company": {"company_name": "ACME SRL"}},
        )

        self.assertIsNot(cloned_workflow, runtime.workflow)
        self.assertEqual(response.content["status"], ProjectStatus.blocked_missing_data)

    def test_agno_workflow_direct_actions_require_authorized_actor(self) -> None:
        runtime = self.app.state.agno_runtime
        response = runtime.workflow.run(
            action="create_project",
            payload={"company": complete_company_payload()},
            actor={"user_id": "unknown", "role": "client_user"},
        )

        self.assertEqual(response.content["status"], "error")
        self.assertEqual(response.content["code"], "actor_not_allowed")

    def test_repository_factory_defaults_to_memory_backend(self) -> None:
        bundle = create_repository_bundle(AppSettings(repository_backend="memory"))

        self.assertEqual(bundle.backend, "memory")
        self.assertIsInstance(bundle.store, RuntimeStore)
        self.assertIsNone(bundle.supabase_client)

    def test_repository_factory_rejects_supabase_without_backend_credentials(self) -> None:
        with self.assertRaises(ValueError):
            create_repository_bundle(AppSettings(repository_backend="supabase"))

    def test_settings_autodetects_supabase_backends_when_credentials_are_present(self) -> None:
        get_settings.cache_clear()
        with patch.dict(
            "os.environ",
            {
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SERVICE_ROLE_KEY": "service-key",
            },
            clear=True,
        ):
            settings = get_settings()

        get_settings.cache_clear()
        self.assertEqual(settings.repository_backend, "supabase")
        self.assertEqual(settings.rag_backend, "supabase")

    def test_supabase_project_repository_uses_typed_table_boundary(self) -> None:
        client = FakeSupabaseRestClient()
        repo = SupabaseProjectRepository(client)  # type: ignore[arg-type]
        actor = Actor(user_id="local-client", role="client_user")

        project = repo.create_project(
            company_input=CompanyInput(**complete_company_payload()),
            actor=actor,
            source_channel="api",
        )

        self.assertEqual(project.company.company_name, "ACME Sicurezza SRL")
        self.assertEqual(project.status, ProjectStatus.intake_pending_confirmation)
        self.assertEqual(len(client.tables["companies"]), 1)
        self.assertEqual(len(client.tables["dvr_projects"]), 1)
        self.assertEqual(client.tables["audit_events"][0]["action"], "project.create")

    def test_project_repository_records_audit_events(self) -> None:
        store = RuntimeStore()
        repo = ProjectRepository(store)
        actor = Actor(user_id="local-client", role="client_user")

        repo.create_project(
            company_input=CompanyInput(**complete_company_payload()),
            actor=actor,
            source_channel="api",
        )

        self.assertEqual(len(store.audit_events), 1)


if __name__ == "__main__":
    unittest.main()

# CT Safe DVR Agent - Project Handoff Summary

Date: 2026-05-30

This document is a technical handoff for a collaborator starting work on the CT Safe DVR Agent project.

## 1. Project Goal

The project is migrating the current CT Safe DVR generation system from a legacy n8n/Airtable/Telegram/Supabase workflow into a more maintainable Agno-based AI agent system.

The target system should let a user interact with an AI agent to:

1. Provide company and DVR input data.
2. Upload or modify an existing DVR file when needed.
3. Let the agent ask for missing information.
4. Retrieve supporting evidence from a Supabase RAG corpus.
5. Draft and submit a DVR index for human review.
6. Generate an editable DOCX DVR after index approval.
7. Let the user request modifications.
8. Track project state, generated documents, evidence, audit events, and future dashboard activity.

The final deliverable must be an editable `.docx` DVR, not only Markdown or PDF.

## 2. Source Of Truth

Before coding, read:

```text
guida_progetto_agente_dvr_agno.md
```

This guide is the canonical project reference. It contains the current architecture, migration reasoning, UX flow, RAG strategy, database model, Agno runtime plan, and implementation notes.

Supporting files:

```text
tasks/prd-agente-dvr-agno.md
Guida Notion agente AI dvr.docx
analisi_supabase_rag_mcp_toolbox.md
mappatura_airtable_documenti_ct_safe.md
MCP_E_SKILLS_PROGETTO.md
agente ct-safe dvr attuale/
esempi dvr per template/
```

## 3. Important Architecture Rule

MCP servers and Codex skills are development, inspection, migration, and administration tools.

The production Agno runtime must not depend on broad MCP access to Supabase, Airtable, Google Drive, Render, or Vercel.

Runtime access should happen through small typed Python tools and repositories with:

- Pydantic input/output contracts.
- Least-privilege behavior.
- Explicit logging.
- Explicit fallback behavior.
- No uncontrolled admin surface exposed to the agent.

## 4. Current Repository Layout

Important folders:

```text
app/
  agno_runtime.py
  main.py
  settings.py
  domain/
  repositories/
  services/
  workflows/
  prompts/

supabase/
  migrations/
  sql/

scripts/
tests/
tasks/
agente ct-safe dvr attuale/
esempi dvr per template/
```

Key files:

```text
app/main.py
app/agno_runtime.py
app/workflows/dvr_workflow.py
app/domain/models.py
app/services/rag_search_tool.py
app/services/rag_factory.py
app/services/embedding_provider.py
app/services/docx_render_service.py
app/repositories/supabase_rest_client.py
supabase/migrations/202605270001_initial_dvr_schema.sql
supabase/migrations/202605290001_rag_v2_chunks.sql
tests/test_thin_slice.py
scripts/validate_rag_supabase.py
scripts/validate_rag_v2_supabase.py
```

## 5. What Already Exists

The project already has a working first backend slice:

- FastAPI app.
- Agno runtime wrapper.
- Basic AgentOS compatibility.
- Pydantic domain models.
- In-memory repositories.
- Supabase repository adapters.
- Operational schema migration.
- Basic security roles.
- Intake flow.
- Project creation and confirmation.
- Index generation/review flow.
- Pilot section generation.
- Editable DOCX draft service.
- Document patch request endpoint.
- Airtable sync service placeholder.
- RAG search service.
- RAG validation fixture.
- OpenRouter embedding provider support.
- Unit tests for the thin slice.

The API currently supports core workflow endpoints such as:

```text
POST /api/dvr/intake
POST /api/dvr/projects
POST /api/dvr/projects/{project_id}/confirm
POST /api/dvr/projects/{project_id}/index
POST /api/dvr/projects/{project_id}/index/{index_id}/review
POST /api/dvr/projects/{project_id}/sections/pilot
POST /api/dvr/projects/{project_id}/documents/draft
POST /api/dvr/projects/{project_id}/patches
GET  /doctor
GET  /api/dvr/runtime
```

## 6. Current RAG Status

There are two RAG modes:

```text
DVR_RAG_VERSION=legacy
DVR_RAG_VERSION=v2
```

### Legacy RAG

Legacy RAG currently works against the existing Supabase tables:

```text
normativa
indice
dvr_pregressi
```

The runtime uses:

- Vector RPC search.
- Lexical backfill via PostgREST text search.
- Deduplication.
- Local reranking.
- Fallback when needed.

Live validation passed:

```text
python scripts\validate_rag_supabase.py

PASS normativa_dpi_mansione
PASS indice_struttura_dvr
```

This is a bridge solution. It is useful, but the legacy database metadata is weak.

Observed legacy issues:

- Many `normativa` rows have poor metadata.
- `source` is often only `blob`.
- Real legal source names/pages cannot always be trusted from legacy metadata.
- Duplicate chunks exist.
- `indice` is useful but small and has weak source metadata.
- `match_indice` is not reliable; `match_documents` points to `indice`.

### RAG v2

RAG v2 has been implemented locally but has not yet been applied to the live Supabase database.

The migration is:

```text
supabase/migrations/202605290001_rag_v2_chunks.sql
```

It creates:

```text
public.rag_chunks
public.match_rag_chunks(...)
public.search_rag_chunks_text(...)
public.match_normativa_v2(...)
public.match_indice_v2(...)
public.match_dvr_pregressi_v2(...)
```

Main features:

- Unified `rag_chunks` table.
- Corpus field for `normativa`, `indice`, and `dvr_pregressi`.
- Legacy table/id traceability.
- `embedding vector(1536)`.
- `source_document`, `source_page`, `line_from`, `line_to`.
- `source_type`, `section_type`, `risk_category`.
- ATECO, mansioni, ambienti, attrezzature, normative refs.
- `content_hash`.
- generated `search_vector`.
- HNSW pgvector index.
- GIN indexes for filters.
- RLS enabled.
- `anon` and `authenticated` revoked.
- RPC execution revoked from `public` and granted only to `service_role`.

Current live v2 validation fails because the DB migration is not yet applied:

```text
python scripts\validate_rag_v2_supabase.py

Expected current error:
Could not find the function public.match_rag_chunks(...)
```

This confirms:

1. Runtime code for RAG v2 is ready.
2. Legacy RAG still works.
3. Supabase live does not yet have the RAG v2 migration.

## 7. Runtime Configuration

Environment is loaded from local env files. Do not print secrets.

Important variables:

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
OPENROUTER_API_KEY
OPEN_ROUTER_KEY
DVR_RAG_BACKEND=mock|supabase
DVR_RAG_VERSION=legacy|v2
DVR_RAG_V2_LEGACY_FALLBACK=true|false
DVR_EMBEDDING_PROVIDER=openrouter|openai_api
DVR_EMBEDDING_MODEL=openai/text-embedding-3-small
DVR_DEFAULT_LLM_PROVIDER=openrouter
DVR_DEFAULT_MODEL=...
AIRTABLE_API_KEY
AIRTABLE_BASE_ID
```

OpenRouter is currently preferred over OpenAI API key usage.

## 8. Test And Validation Commands

Run local unit tests:

```text
python -m unittest -q tests.test_thin_slice
```

Expected current result:

```text
Ran 27 tests
OK
```

Validate legacy live RAG:

```text
python scripts\validate_rag_supabase.py
```

Validate RAG v2 after applying the migration:

```text
python scripts\validate_rag_v2_supabase.py
```

Compile key Python files:

```text
python -m py_compile app\settings.py app\services\rag_factory.py app\services\rag_search_tool.py app\services\doctor_service.py scripts\validate_rag_supabase.py scripts\validate_rag_v2_supabase.py
```

## 9. Immediate Next Steps

Recommended priority order:

1. Apply `supabase/migrations/202605290001_rag_v2_chunks.sql` to Supabase live or staging.
2. Run `python scripts\validate_rag_v2_supabase.py`.
3. Verify row counts by corpus in `public.rag_chunks`.
4. If HNSW is not supported by the current pgvector version, temporarily replace the HNSW index with IVFFlat and plan a pgvector upgrade.
5. Enable:

```text
DVR_RAG_VERSION=v2
DVR_RAG_V2_LEGACY_FALLBACK=false
```

only after v2 validation passes.

6. Build the v2 ingestion pipeline so new dashboard uploads go directly into `rag_chunks`.
7. Improve metadata quality for sources, pages, normative references, ATECO, mansions, and risk categories.
8. Replace mocked Airtable sync with a narrow typed adapter.
9. Improve section/chapter generation beyond pilot sections.
10. Strengthen QA gates before DOCX delivery.
11. Improve DOCX rendering against the CT Safe template.
12. Build the Next.js dashboard for phase 2.
13. Deploy backend to Render and optionally frontend/dashboard to Vercel.

## 10. Product Workflow To Preserve

The intended user experience is:

1. User writes to the AI agent.
2. Agent asks for missing DVR data.
3. If modifying an existing DVR, the user uploads the file and the system recreates it using the template.
4. When enough data exists, the agent queries RAG and drafts the DVR index.
5. The index is sent to the user/human reviewer for approval.
6. If approved, the agent generates the DVR.
7. The generated DVR is presented to the user.
8. The user may approve delivery or request modifications.
9. The agent can apply requested changes.
10. Phase 1 syncs Airtable.
11. Phase 2 adds a Next.js dashboard with DVR summaries, uploaded file management, RAG document management, and agent interaction.

## 11. Non-Negotiable Domain Rules

The DVR agent must not invent:

- Legal obligations.
- Company facts.
- Measurements.
- Certifications.
- Names.
- Dates.
- Signatures.
- Surveillance protocols.
- Site-specific risks not grounded in user data or evidence.

Every generated section should preserve traceability:

- Which company data was used.
- Which RAG chunks were used.
- Which claims are supported.
- Which data is missing.
- Which QA status applies.

If evidence is weak or missing, the system should mark the section as blocked or needing revision instead of hallucinating.

## 12. Known Gaps

Still incomplete:

- RAG v2 migration not applied live.
- RAG v2 ingestion pipeline not built.
- Dashboard not built.
- Airtable sync still mocked/partial.
- DOCX rendering is functional but not final-quality template rendering.
- Full chapter generation is not production quality yet.
- Human review workflow needs stronger UX.
- Memory/self-improvement loop is designed conceptually but not fully implemented.
- Deployment is not done.
- Runtime provider/model tracing should be expanded across every final DVR.

## 13. Safety Notes

Do not expose service role keys, OpenRouter keys, Airtable credentials, tokens, cookies, or bridge session references in:

- prompts,
- logs,
- generated documents,
- memories,
- wiki notes,
- learning proposals,
- commits,
- issue comments.

Do not give the runtime agent broad MCP access. Use MCP only as a developer/admin tool.

Do not let self-improvement directly modify production prompts, policies, templates, memory policy, RAG policy, or tool permissions. The intended loop is:

```text
observation -> learning proposal -> eval -> human approval -> new version -> monitored deployment
```

## 14. Current Recommended First Task

Start by applying and validating RAG v2.

Concrete task:

```text
Apply supabase/migrations/202605290001_rag_v2_chunks.sql to Supabase staging/live,
then run scripts/validate_rag_v2_supabase.py.
```

Expected successful outcome:

- `public.rag_chunks` exists.
- `public.match_rag_chunks` exists.
- `public.search_rag_chunks_text` exists.
- Legacy rows are imported into `rag_chunks`.
- RAG v2 validation returns chunks for normativa and indice.
- Runtime can safely switch to `DVR_RAG_VERSION=v2`.

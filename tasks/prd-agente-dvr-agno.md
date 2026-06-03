# PRD: Agente DVR CT Safe con Agno, Supabase, RAG, DOCX e Dashboard

## 1. Introduzione

Il progetto deve trasformare l'attuale pipeline DVR basata su Telegram, n8n, Airtable, Supabase Vector Store e Google Apps Script in un sistema agentico governato, tracciabile e manutenibile.

L'esperienza utente deve rimanere conversazionale: l'utente parla con un agente AI, fornisce dati o allega un DVR esistente, revisiona indice e bozza, chiede modifiche e riceve un DOCX finale editabile. Il backend, pero', deve usare workflow persistenti, tool Python tipizzati, stati espliciti, RAG controllato, QA e approval gate.

## 2. Obiettivi

- Replicare e migliorare i flussi n8n attuali senza interrompere subito l'operativita'.
- Generare DVR in formato `.docx` editabile usando il template CT Safe.
- Spostare lo stato operativo da Airtable a Supabase, mantenendo sync legacy in Fase 1.
- Usare Supabase/pgvector come evidence layer RAG per normativa, indici, esempi e QA.
- Rendere ogni DVR tracciabile: input, indice, sezioni, fonti, QA, prompt/model version, revisioni e file finali.
- Consentire modifiche successive a sezioni o documenti con versioning.
- Introdurre una dashboard Next.js in Fase 2 per gestione DVR, file RAG e interazione con l'agente.
- Preparare memoria persistente e auto-miglioramento controllato senza auto-modifiche production.

## 3. Utenti

- `client_user`: avvia DVR, fornisce dati, allega file, rivede output e scarica documenti.
- `ctsafe_reviewer`: valida indice, bozza DVR, modifiche, QA e learning proposal.
- `admin`: gestisce provider, RAG, template, dashboard, diagnostica e configurazioni.
- `developer`: implementa e mantiene backend, workflow, RAG, DOCX renderer e dashboard.

## 4. User Stories

### US-001: Avvio nuovo DVR conversazionale
**Description:** As a client_user, I want to write to the AI agent and provide company information so that a new DVR project can be started without filling a complex form.

**Acceptance Criteria:**
- [ ] User can start a new DVR from Telegram in Fase 1.
- [ ] User can start a new DVR from Next.js dashboard in Fase 2.
- [ ] Agent extracts company, ATECO, activity, workers, mansions, site, document type and notes.
- [ ] Agent asks only for missing required data.
- [ ] Agent does not create a project before explicit user confirmation.
- [ ] Initial data is saved to Supabase and synced to Airtable during Fase 1.

### US-002: Import or modification of existing DVR
**Description:** As a client_user, I want to attach an existing DVR so that the system can recreate or modify it using the CT Safe template.

**Acceptance Criteria:**
- [ ] User can attach a DVR file from Telegram or dashboard.
- [ ] File is stored as source input.
- [ ] System extracts useful content and structure from the uploaded file.
- [ ] Final generated document uses the CT Safe template, not the uploaded file as free template.
- [ ] Missing or unverifiable facts remain visible as placeholders or review items.

### US-003: RAG-assisted index generation and review
**Description:** As a reviewer, I want the agent to propose an index based on company data and RAG evidence so that I can approve the structure before expensive generation.

**Acceptance Criteria:**
- [ ] Agent generates preliminary DVR index from project data and RAG.
- [ ] Normative evidence is separated from examples/templates.
- [ ] Index is stored with status and version.
- [ ] User/reviewer can approve, reject, or request changes to the index.
- [ ] Section generation cannot start before index approval.

### US-004: Section generation with evidence tracking
**Description:** As a reviewer, I want every generated section to be grounded in company data and retrieved evidence so that the DVR can be audited.

**Acceptance Criteria:**
- [ ] Each section has a brief, status, generated content and QA status.
- [ ] Each section stores evidence used, including retrieved chunk ids, query, score/rank, source notes and decision.
- [ ] Writer agent marks weak evidence or missing data instead of inventing details.
- [ ] Risks are linked to real activities, mansions, environments, equipment, substances or exposure.
- [ ] DPI tables connect DPI to risk and mansion.

### US-005: QA and draft DOCX generation
**Description:** As a reviewer, I want the system to generate a QA-checked DOCX draft so that I can review the real deliverable before final approval.

**Acceptance Criteria:**
- [ ] Section QA runs before document assembly.
- [ ] Document QA checks completeness, order, company data, placeholders, mansions/risks/DPI and unresolved issues.
- [ ] DOCX draft is generated from CT Safe template.
- [ ] DOCX, metadata, QA report and changelog are stored in Supabase Storage/S3.
- [ ] Draft is presented to user/reviewer before final delivery.

### US-006: Revision and versioning
**Description:** As a client_user, I want to ask for specific modifications so that the DVR can be corrected without regenerating everything manually.

**Acceptance Criteria:**
- [ ] User can request a targeted modification in natural language.
- [ ] System identifies target section or asks for clarification.
- [ ] Patch is proposed and QA-checked before applying.
- [ ] Updated section and document version are stored.
- [ ] Changelog explains what changed.
- [ ] User receives the new DOCX version.

### US-007: Airtable compatibility in Fase 1
**Description:** As the team, we want Airtable to remain synchronized during transition so that existing operations are not broken.

**Acceptance Criteria:**
- [ ] New projects are mirrored to Airtable `Progetti DVR`.
- [ ] Sections are mirrored to Airtable `Capitoli DVR` where needed.
- [ ] Legacy Airtable IDs and status values are preserved.
- [ ] Supabase remains the target source of truth.
- [ ] Airtable sync failures are logged and visible to admin/reviewer.

### US-008: Next.js dashboard in Fase 2
**Description:** As a reviewer/admin, I want a dashboard to manage DVR projects, files, RAG content and agent interactions.

**Acceptance Criteria:**
- [ ] Dashboard lists DVR projects with status, client/company, latest document version, QA status and actions.
- [ ] Dashboard shows document history and downloadable DOCX versions.
- [ ] Dashboard manages RAG files: upload, metadata, ingest state, activation/deactivation and audit.
- [ ] Dashboard includes an agent chat/action panel for new DVRs, revisions and document regeneration.
- [ ] Dashboard calls backend FastAPI APIs only.
- [ ] Dashboard never receives service role keys, provider secrets or MCP admin access.
- [ ] Verify in browser using dev-browser/browser skill.

### US-009: Memory and learning proposals
**Description:** As an admin/reviewer, I want the system to learn from feedback safely so that quality improves without uncontrolled production changes.

**Acceptance Criteria:**
- [ ] Project facts are stored in typed Supabase tables, not only memory.
- [ ] Memories have scope, source, confidence, retention and PII flag.
- [ ] QA findings and reviewer corrections can create learning proposals.
- [ ] Learning proposals cannot modify prompts, RAG policy, templates, checklist or tool permissions directly.
- [ ] Eval and human approval are required before activating a new version.

## 5. Functional Requirements

- FR-1: The system must expose a Telegram entrypoint in Fase 1.
- FR-2: The system must expose a Next.js dashboard entrypoint in Fase 2.
- FR-3: The backend must be FastAPI/Agno/AgentOS compatible and deployable on Render.
- FR-4: The user must be able to create a new DVR through conversation.
- FR-5: The user must be able to upload an existing DVR and request recreation/modification.
- FR-6: The system must ask for missing required project data before creating the DVR project.
- FR-7: The system must generate and persist an index before section generation.
- FR-8: The system must require user/reviewer approval of the index before generating sections.
- FR-9: The system must use Supabase RAG for normative/document evidence.
- FR-10: The system must store section evidence, not just final text.
- FR-11: The system must run section QA and document QA.
- FR-12: The system must generate editable `.docx` output from CT Safe template.
- FR-13: The system must version generated documents and revisions.
- FR-14: The system must support targeted document modifications.
- FR-15: The system must sync Airtable in Fase 1 as a legacy compatibility layer.
- FR-16: The system must manage RAG file upload/ingest/status from the dashboard in Fase 2.
- FR-17: The system must log agent runs, tool decisions, provider/model, prompt versions, RAG policy version, template version and QA outcomes.
- FR-18: The system must enforce AuthGate, roles, project scopes and tool policy before sensitive actions.

## 6. Non-Goals

- No autonomous legal/professional approval of final DVR.
- No unrestricted runtime MCP access to Supabase, Airtable, Google Drive, Render or Vercel.
- No use of the full Obsidian/LLM Wiki as runtime memory.
- No automatic production prompt/template/RAG/checklist/tool-policy changes.
- No direct service-role Supabase access from frontend.
- No final PDF-only output as primary deliverable.
- No use of uploaded DVR as uncontrolled production template.

## 7. Design Considerations

- The user experience must feel like an agent conversation, but critical actions must be workflow-controlled.
- Confirmation gates are required after initial data extraction, after index generation, and before final delivery.
- Missing data must be visible and actionable.
- Dashboard should be utilitarian and operational: project list, status, document history, RAG file management and agent action panel.
- DOCX output must preserve CT Safe tone, heading styles, tables, cover information, signatures and editable Word structure.

## 8. Technical Considerations

- Prefer Agno Workflows for predictable long-running DVR generation.
- Use agents only where LLM reasoning/generation is valuable: intake, index drafting, section writing, QA, revision interpretation.
- Implement deterministic services for state transitions, permissions, repository writes, DOCX rendering, version activation, doctor checks and provider health.
- Use typed Python tools with Pydantic input/output contracts and least-privilege permissions.
- Store operational data in Supabase Postgres; use Airtable only as Fase 1 legacy sync/mirror.
- Add `section_evidence` or equivalent table for RAG traceability.
- Use Supabase Storage/S3 for input files, DOCX versions, QA reports and changelogs.
- Use Agno/Postgres storage for workflow/session/HITL state; avoid important local SQLite on Render.
- Use RAG as evidence layer, not as the whole system brain.
- Keep OpenAI subscription bridge optional, single-tenant and explicitly traceable if ever used.

## 9. Success Metrics

- New DVR can be started from Telegram and reaches index review without manual Airtable work.
- Index approval prevents section generation until confirmed.
- At least 90% of generated sections have stored evidence records.
- DOCX draft is generated and downloadable with metadata and QA report.
- User can request a section modification and receive a new version without full manual rewrite.
- Airtable sync in Fase 1 preserves legacy record IDs and statuses.
- Dashboard in Fase 2 can list DVRs, manage RAG files and invoke agent actions.
- No production prompt/RAG/template/tool-policy changes occur without approval event.

## 10. Implementation Phases

### Fase 0: RAG and safety foundation
- Fix or replace broken legacy retrieval functions.
- Add or prepare `rag_chunks`.
- Add RLS/grant hardening plan.
- Define evidence schema.
- Define prompt/version registry baseline.

### Fase 1: Telegram + backend + Airtable sync
- Implement FastAPI/Agno backend.
- Implement Telegram gateway, AuthGate, CommandRouter and SessionManager.
- Implement new DVR workflow with index approval.
- Implement section writing, QA and DOCX draft generation.
- Implement Airtable sync adapter.

### Fase 2: Next.js dashboard
- Implement project overview.
- Implement document/version view.
- Implement RAG file management.
- Implement dashboard agent interaction.
- Implement reviewer/admin control actions.

### Fase 3: Memory and controlled learning
- Implement memory write/read policy.
- Implement QA findings and review events.
- Implement learning proposals, eval runs, approval events and artifact versions.

## 11. Open Questions

- Which exact auth provider should the Next.js dashboard use: Supabase Auth, custom JWT, or another provider?
- Should Airtable remain read/write mirror for all Fase 1 changes or only selected state/output fields?
- Which DOCX strategy is first: `docxtpl` placeholders or Word content controls?
- Which model/provider is the production default for long DVR generation?
- What is the minimum reviewer role required for final delivery approval?

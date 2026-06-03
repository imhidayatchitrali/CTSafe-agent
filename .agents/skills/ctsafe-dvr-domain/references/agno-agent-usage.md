# Agno Agent Usage

Use this reference when designing Agno agents, tools, workflows, and prompts for the DVR system.

## Principle

Agno agents should not receive broad MCP access to Supabase, Airtable, or Google Drive. They should call small typed Python tools with narrow permissions, Pydantic inputs/outputs, logging, and auditability.

## Agent Responsibilities

| Agent | Uses this domain skill for |
|---|---|
| `DVR Orchestrator Agent` | Selecting workflow state and next agent. |
| `IntakeAgent` | Required company fields, missing-data policy, confirmation before create. |
| `IndexDraftAgent` | Canonical DVR structure and index adaptation by sector. |
| `IndexValidationAgent` | Mandatory chapter coverage and coherence checks. |
| `SectionPlannerAgent` | Brief shape, required fields, target retrieval hints. |
| `ChapterWriterAgent` | Grounded writing, RAG evidence discipline, CT Safe tone. |
| `SectionQAAgent` | Section QA checklist and status model. |
| `DocumentQAAgent` | Full-document completeness and cross-section consistency. |
| `DocxRenderAgent` | Template requirements, DOCX output contract, versioning. |
| `RevisionAgent` | Patch discipline and regeneration of affected sections only. |

## Tool Boundaries

Recommended tools:

- `ProjectRepository`: projects, companies, statuses.
- `SectionRepository`: briefs, generated content, QA status.
- `RagSearchTool`: queries Supabase RAG and returns chunks with source metadata.
- `CitationVerifierTool`: checks claims against retrieved evidence.
- `DocxRenderTool`: renders DOCX from sections and template.
- `StorageTool`: stores DOCX, metadata, QA report, changelog.
- `LegacyAirtableReader`: read-only bridge during migration.

Avoid:

- Direct arbitrary SQL from generation agents.
- Direct write access to legacy Airtable from writing agents.
- Runtime dependence on Google Apps Script.
- Broad Google Drive access as a core dependency.

## Workflow Gates

1. Intake cannot create project until required fields are present or explicitly marked missing.
2. Index validation must complete before section generation.
3. Section writing must save retrieved chunk IDs/source notes.
4. Section QA must pass before document assembly, unless marked for human review.
5. Document QA must run before or immediately after DOCX generation.
6. Every document version must create metadata and QA artifacts.

## Prompt Guidance

Agent prompts should include:

- Role and task boundary.
- Required inputs.
- Missing-data behavior.
- RAG evidence rules.
- Output schema.
- QA status vocabulary.
- Refusal to invent unsupported facts.


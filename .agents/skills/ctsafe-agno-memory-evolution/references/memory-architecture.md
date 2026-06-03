# Memory Architecture

## Goal

Give the CT Safe Agno DVR agent useful continuity without allowing uncontrolled self-modification or unsafe reuse of customer data.

## Memory Types

| Memory type | Purpose | Suggested storage | Runtime access |
|---|---|---|---|
| `session_memory` | Current chat/workflow state, user intents, pending questions. | Agno session storage in Postgres/Supabase. | Read/write by orchestrator and active agents. |
| `project_memory` | Stable project facts: company, sites, workers, mansions, equipment, substances, documents, missing data. | Supabase project tables, not free-form notes only. | Read/write through typed repositories. |
| `user_preference_memory` | Preferences: language, formatting, review style, delivery channel. | Supabase memory table scoped to user/org. | Read with strict scope filtering. |
| `rag_evidence` | Normative/document chunks retrieved for a section. | Supabase RAG tables and section evidence tables. | Read-only retrieval; writes only by ingestion pipeline. |
| `qa_memory` | Repeated defects, reviewer feedback, accepted corrections. | `qa_findings`, `review_events`, `learning_signals`. | Write by QA/revision agents; read by proposal agent. |
| `learning_proposals` | Suggested improvements to prompt, RAG policy, template, checklist, or tool flow. | Dedicated table with approval workflow. | Created by agent; applied only after human approval. |
| `eval_memory` | Test cases, expected checks, eval results, regression history. | Versioned eval tables/files. | Read/write by eval runner, not by production writer agents. |

## Separation Rules

- Project facts can influence a DVR for that project only.
- User preferences can influence formatting and workflow, not legal/technical obligations.
- QA findings can generate proposals, not direct production changes.
- RAG evidence supports document text; it is not memory about the customer unless explicitly attached to the project.
- Previous DVRs are examples/templates, not normative truth.

## Minimal Supabase Shape

```sql
create table agent_memories (
  id uuid primary key default gen_random_uuid(),
  scope text not null check (scope in ('session','user','org','project','global_dev')),
  scope_id text not null,
  memory_type text not null,
  content jsonb not null,
  source text not null,
  confidence numeric not null default 0.7,
  retention_policy text not null default 'project_lifetime',
  created_by text not null,
  created_at timestamptz not null default now(),
  expires_at timestamptz,
  superseded_by uuid references agent_memories(id)
);
```

Use JSONB for flexible memory content, but keep important production facts in typed domain tables whenever possible.

## Retrieval Policy

For any memory retrieval, require:

- `scope` and `scope_id`;
- `memory_type`;
- maximum result count;
- source and confidence in output;
- explicit exclusion of secrets/PII unless the active task requires project-scoped PII.

## Memory Write Policy

Agents may write memories only when all fields are known:

- what was learned;
- why it matters;
- source event or document;
- confidence;
- who/what created it;
- allowed retention;
- whether it contains PII.

Low-confidence memories should be stored as observations, not facts.

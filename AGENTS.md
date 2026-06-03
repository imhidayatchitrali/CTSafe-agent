# CT Safe DVR Agent - Project Memory

## Source Of Truth

Before working on this project, read:

```text
guida_progetto_agente_dvr_agno.md
```

That guide is the canonical source of truth for the current project context, architecture, migration plan, data model, RAG strategy, DOCX generation plan, and implementation roadmap.

## Supporting Context Files

Use these files as supporting evidence when the guide references them:

```text
Guida Notion agente AI dvr.docx
analisi_supabase_rag_mcp_toolbox.md
mappatura_airtable_documenti_ct_safe.md
MCP_E_SKILLS_PROGETTO.md
agente ct-safe dvr attuale/
esempi dvr per template/
project-brain/
```

## Working Rule

Treat the guide as authoritative unless the user explicitly provides newer information. When new project context is discovered, update `guida_progetto_agente_dvr_agno.md` so future Codex sessions inherit the same understanding.

## Architecture Rule

MCP servers and Codex skills are development, inspection, migration, and administration tools. The production Agno agent must use small typed Python tools with least-privilege access, Pydantic input/output contracts, and logging. Do not make the runtime agent depend on broad MCP access to Supabase, Airtable, or Google Drive.

## Prompt Rule

Use `prompt-engineering-patterns` for production Agno prompts: version prompts as code, prefer Pydantic/JSON structured outputs, define explicit fallbacks when RAG evidence is insufficient, and track quality metrics.

## Memory Evolution Rule

Use `.agents/skills/ctsafe-agno-memory-evolution` for persistent memory and controlled self-improvement design. Agno may observe, remember, evaluate, and create learning proposals, but it must never directly change production prompts, skills, DOCX templates, RAG policies, tool permissions, memory/PII policy, or production behavior. Required loop: observation, learning proposal, eval, human approval, new registered version, deployment monitoring.

## Ops Gateway Rule

Use `.agents/skills/ctsafe-agno-ops-gateway` for the OpenClaw-inspired operating layer around Agno: channel normalization, AuthGate, command routing, isolated sessions, agent routing, tool policy, doctor/audit, and control UX. The gateway must not bypass DVR domain rules, RAG policy, memory approval gates, or human review. The OpenAI subscription bridge is optional single-tenant only; never store token/cookie data in prompts, logs, memories, wiki, or learning proposals, require health checks and explicit fallback, and trace provider/model in every run and DVR.

## Deployment Rule

Render is the preferred backend target for AgentOS/FastAPI. Vercel is optional for frontend, dashboard, landing, or preview only. Render MCP and Vercel MCP are administrative tools for Codex/developer use, never runtime tools for Agno. Render MCP is not configured yet because the Render API key is broad; configure it only when ready to deploy and require explicit human confirmation for infrastructure changes.

## Obsidian / LLM Wiki Rule

Obsidian and LLM Wiki are development memory for Codex and the team. The runtime Agno agent should not use a broad LLM Wiki as free memory. Agno may only read a curated, non-sensitive DVR Quality Wiki export/pages through explicit read-only tools. Never give the runtime agent unrestricted access to the full vault.

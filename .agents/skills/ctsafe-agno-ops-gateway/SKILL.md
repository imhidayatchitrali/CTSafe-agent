---
name: ctsafe-agno-ops-gateway
description: Use when designing, implementing, reviewing, or debugging the operational gateway around the CT Safe Agno DVR agent. Covers OpenClaw-inspired channel gateways, authorization, command routing, agent routing, isolated sessions, tool policies, doctor/audit commands, control UX, and optional single-tenant OpenAI subscription bridge provider.
metadata:
  author: CT Safe project
  version: "0.1.0"
---

# CT Safe Agno Ops Gateway

Use this skill when building the operational layer around the Agno DVR system: Telegram/WhatsApp/web gateway, authorized users, commands, routing, sessions, tool policies, diagnostics, control UX, and LLM provider selection.

Core rule: the gateway is an operating layer, not the domain brain. It should normalize channels, enforce permissions, route work to Agno agents, isolate sessions, and log operations. It must not bypass DVR domain rules, memory approval gates, RAG policy, or human review.

## Quick Workflow

1. Identify the gateway concern:
   - Channels and event normalization: read `references/channel-gateway.md`.
   - Auth, command routing, and sessions: read `references/auth-commands-sessions.md`.
   - Agent routing and tool policy: read `references/agent-routing-tool-policy.md`.
   - Diagnostics/control UX: read `references/doctor-control-ux.md`.
   - OpenAI subscription bridge/provider design: read `references/openai-subscription-bridge.md`.
2. Keep channel input separate from Agno workflow input. Normalize raw Telegram/WhatsApp/web events into a typed internal command/event.
3. Enforce `AuthGate` before any agent sees user content.
4. Route commands to small workflow handlers or specialized agents; do not let a single agent own all tools.
5. Log provider, session, project, document, prompt versions, and tool decisions for traceability.

## Non-Negotiables

- No unauthenticated user can trigger DVR generation, revision, approval, export, or deploy actions.
- No raw channel event should directly invoke broad tools.
- No agent should receive tools outside its role.
- No bridge provider should hide which model/session/provider generated content.
- OpenAI subscription bridge is allowed only as an optional single-tenant provider, not as a multi-client shared backend.
- If the subscription/session expires or becomes unavailable, the system must fail gracefully and ask for reconnection or fallback.
- Production behavior must remain traceable to versions and approvals.

## Target Architecture

```text
Channel adapters
-> AuthGate
-> CommandRouter
-> SessionManager
-> AgentRouter / WorkflowRunner
-> typed Agno agents and tools
-> AuditLog + Control UX
```

## Local Project Sources

Use these alongside this skill:

- `MCP_E_SKILLS_PROGETTO.md`: active tool/MCP/skill policy.
- `.agents/skills/ctsafe-dvr-domain/`: DVR domain constraints.
- `.agents/skills/ctsafe-agno-memory-evolution/`: memory, learning proposals, eval, approval gates.
- `.agents/skills/agno/` if available globally: Agno concepts, AgentOS, MCP, teams, workflows.
- `.agents/skills/fastapi-python/`: backend implementation patterns.

## Output Expectations

When using this skill, produce concrete artifacts:

- event/command schemas;
- permission matrix;
- command list;
- agent routing map;
- session key strategy;
- LLM provider interface;
- audit/doctor checks;
- explicit list of allowed automatic actions and approval-required actions.

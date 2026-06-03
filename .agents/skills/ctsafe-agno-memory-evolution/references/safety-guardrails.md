# Safety Guardrails

## Main Risks

Hermes-style agents are powerful because they can remember, create skills, and improve behavior over time. The same capabilities create risks:

- memory poisoning;
- skill/prompt injection persistence;
- accidental reuse of customer PII;
- unauthorized behavior drift;
- broad tool abuse;
- low-quality self-improvement loops that optimize the wrong metric.

## Guardrails

| Risk | Guardrail |
|---|---|
| Memory poisoning | Store source, confidence, scope, and reviewer status for every memory. Do not treat reflections as facts. |
| Prompt/skill injection | Never promote user text directly into prompts or skills. Convert to proposals and review. |
| PII leakage | Scope customer facts to project/org. Do not move PII into global development memory. |
| Behavior drift | Version prompts/templates/checklists/RAG policy and store active versions per DVR. |
| Bad optimization | Require eval dataset and regression checks before approval. |
| Tool overreach | Use typed tools with narrow permissions. Do not expose broad MCP servers in runtime. |
| Silent deployment | Require approval events and release notes for production behavior changes. |

## Approval Packet

Every human approval request should include:

- problem summary;
- evidence;
- exact proposed diff or artifact change;
- eval results;
- known risks;
- rollback plan;
- target deployment scope;
- reviewer decision and timestamp.

## Red Lines

The system must refuse or escalate when a proposal would:

- remove human review from DVR generation;
- weaken missing-data honesty;
- treat previous DVRs as legal authority;
- store secrets/API keys in memory;
- broaden runtime access to Supabase, Airtable, Google Drive, Render, Vercel, or filesystem without explicit approval;
- change legal/technical wording without eval and approval;
- hide uncertainty from the user/reviewer.

## Safe Defaults

- Propose first, change later.
- Prefer smaller scoped memories over broad global memories.
- Prefer explicit project facts over inferred facts.
- Prefer eval failure over unverified deployment.
- Prefer human-readable review packets over opaque automation.

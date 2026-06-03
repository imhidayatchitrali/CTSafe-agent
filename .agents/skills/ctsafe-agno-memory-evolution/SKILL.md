---
name: ctsafe-agno-memory-evolution
description: Use when designing, implementing, reviewing, or debugging persistent memory and controlled self-improvement for the CT Safe Agno DVR agent. Covers Hermes-inspired memory patterns, learning proposals, eval datasets for DVR prompts, prompt/template/checklist versioning, approval gates, and safety constraints that keep the agent aligned with DVR production goals.
metadata:
  author: CT Safe project
  version: "0.1.0"
---

# CT Safe Agno Memory Evolution

Use this skill when adding or reviewing persistent memory, user/project memory, reflection loops, learning proposals, prompt improvement workflows, eval datasets, or Hermes-inspired self-improvement patterns for the CT Safe Agno DVR system.

Core rule: the agent may observe, remember, evaluate, and propose improvements, but it must not directly change production prompts, RAG policy, DOCX templates, checklists, tool permissions, or agent behavior without human approval.

## Quick Workflow

1. Identify the memory type:
   - Conversation/session state: read `references/memory-architecture.md`.
   - Project/customer facts: read `references/memory-architecture.md` and `references/safety-guardrails.md`.
   - Prompt/template/checklist improvement: read `references/learning-proposals.md` and `references/eval-versioning.md`.
   - Agno implementation: read `references/agno-implementation.md`.
2. Keep memory separated by purpose: session memory, user/project memory, RAG evidence, QA findings, eval results, and learning proposals are not interchangeable.
3. Generate `learning_proposal` records instead of mutating prompts or code directly.
4. Run proposals against an eval dataset before approval whenever they affect output quality, legal/technical wording, RAG retrieval, templates, or QA behavior.
5. Require explicit human approval before promoting any proposal to a new version.

## Non-Negotiables

- No autonomous prompt, template, checklist, RAG policy, or tool-permission changes in production.
- No use of customer PII, secrets, or confidential DVR content as generic training memory.
- No memory writes without a clear `scope`, `source`, `confidence`, `retention_policy`, and audit trail.
- No treating agent reflections as facts. Reflections are hypotheses until validated.
- No using prior DVR examples as legal authority. Normative claims must come from approved RAG/legal sources.
- No broad MCP access inside runtime Agno agents. Use typed Python tools with narrow permissions.
- Every deployed behavior must be traceable to versions: prompt, RAG policy, template, checklist, model, and toolset.

## Recommended Loop

```text
Run DVR workflow
-> collect QA findings, reviewer edits, user feedback, retrieval misses
-> create learning proposals
-> evaluate proposals on DVR eval dataset
-> human approval
-> create new versioned prompt/template/checklist/RAG policy
-> deploy and monitor
```

## Local Project Sources

Use these alongside this skill:

- `guida_progetto_agente_dvr_agno.md`: target Agno architecture and workflow.
- `MCP_E_SKILLS_PROGETTO.md`: active MCP/skills policy and deployment choices.
- `.agents/skills/ctsafe-dvr-domain/`: DVR domain rules and QA expectations.
- `.agents/skills/prompt-engineering-patterns/`: prompt patterns, structured outputs, eval thinking.
- `.agents/skills/rag-implementation/`: retrieval, grounding, metadata, and evaluation patterns.

## Output Expectations

When designing this subsystem, produce concrete artifacts:

- Supabase table/schema proposal for memories, learning proposals, eval cases, eval runs, and version registry.
- Agno tool boundaries with Pydantic input/output models.
- Approval workflow states.
- Eval criteria and regression checks.
- Clear list of what the agent may do automatically and what requires human approval.

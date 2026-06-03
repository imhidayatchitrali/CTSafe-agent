# Agent Routing And Tool Policy

## AgentRouter

Route by intent, command, active workflow state, and role.

| Intent/command | Agent/workflow |
|---|---|
| Start project/intake | `IntakeAgent` |
| Generate or update index | `IndexAgent` |
| Write sections | `SectionWriterAgent` |
| Ask about sources | `AuditAgent` or `CitationVerifierTool` |
| Request revision | `RevisionAgent` |
| Final DOCX export | `DocxRenderAgent` |
| Memory/proposal analysis | `LearningProposalAgent` |
| System health | `DvrDoctorAgent` |

## Tool Policy

Every agent gets a minimal toolset:

| Agent | Allowed tools | Denied tools |
|---|---|---|
| `IntakeAgent` | project read/write, missing data, controlled channel replies | deployment, prompt changes, storage delete |
| `SectionWriterAgent` | RAG read, section read/write, citation attach | approval, provider config, template mutation |
| `DocumentQAAgent` | document read, QA findings write, evidence read | direct prompt/template/RAG policy mutation |
| `DocxRenderAgent` | template read, render, storage write versioned artifact | free filesystem write, deletion, deploy |
| `LearningProposalAgent` | QA/review read, proposal create | activate versions, edit production artifacts |
| `DvrDoctorAgent` | read-only diagnostics, health checks | secret exposure, destructive fixes without approval |

## Policy Object

```json
{
  "agent": "SectionWriterAgent",
  "allowed_tools": ["RagSearchTool", "SectionRepository.write", "CitationAttachTool"],
  "denied_actions": ["change_prompt", "change_rag_policy", "deploy", "delete_artifact"],
  "requires_approval": ["finalize_section_without_evidence"]
}
```

## Enforcement

Do not rely only on prompt instructions. Enforce policy in code:

- dependency injection per agent;
- tool registry filtered by role;
- Pydantic schemas;
- audit log on every tool call;
- denied-action events.

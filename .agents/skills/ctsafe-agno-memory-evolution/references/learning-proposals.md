# Learning Proposals

## Principle

A learning proposal is a structured suggestion for improving the system. It is not a change. It must be reviewed, evaluated, and approved before it can affect production behavior.

## When To Create One

Create a proposal when repeated evidence suggests:

- a prompt causes generic or incomplete DVR sections;
- RAG retrieval misses important evidence;
- QA finds the same failure pattern;
- reviewer edits reveal a better instruction/checklist;
- DOCX rendering repeatedly breaks a section/table;
- a tool boundary is too broad, too narrow, or ambiguous;
- a project-specific issue should become a reusable rule.

Do not create proposals from one weak signal unless the issue is high risk.

## Proposal Schema

```json
{
  "proposal_id": "lp_2026_0001",
  "type": "prompt_improvement",
  "target": {
    "component": "SectionWriterAgent",
    "artifact": "prompts/section_writer.md",
    "current_version": "v1"
  },
  "problem": "The DPI section is too generic and does not map PPE to mansions.",
  "evidence": [
    {
      "source": "review_event",
      "id": "rev_123",
      "summary": "Reviewer asked to connect PPE to warehouse worker risks."
    }
  ],
  "proposed_change": "Add an instruction requiring each PPE row to include risk, mansion, scenario, and source note.",
  "expected_benefit": "More specific and auditable PPE tables.",
  "risk_assessment": "May increase table length and require stronger missing-data handling.",
  "eval_plan": ["dvr_magazzino_mmc_001", "dvr_ufficio_vdt_001"],
  "status": "pending_eval",
  "created_by": "LearningProposalAgent"
}
```

## Proposal Types

| Type | Examples | Approval required |
|---|---|---|
| `prompt_improvement` | Add structured output, clarify missing-data behavior, improve grounding. | Always |
| `rag_policy_change` | Change filters, top-k, reranking, metadata use. | Always |
| `template_change` | New DOCX table, changed placeholder, changed section order. | Always |
| `checklist_change` | New QA rule, stricter validation threshold. | Always |
| `tool_boundary_change` | New tool permission, changed repository write behavior. | Always |
| `memory_policy_change` | New memory type, retention, scope, PII handling. | Always |
| `documentation_change` | Wiki/project docs clarification only. | Human review recommended |

## States

```text
draft
-> pending_eval
-> eval_failed | pending_human_review
-> rejected | approved
-> implemented
-> deployed
-> monitored
```

## Rejection Is Useful

Rejected proposals should remain searchable. They prevent repeated bad ideas and help tune future proposal generation.

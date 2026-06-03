# Agno Implementation Pattern

## Recommended Agents

| Agent | Responsibility | Writes |
|---|---|---|
| `MemoryCuratorAgent` | Convert accepted user/reviewer signals into scoped memories. | `agent_memories` |
| `LearningProposalAgent` | Analyze QA findings, review events, eval failures, and retrieval misses. | `learning_proposals` |
| `EvalRunnerAgent` | Run candidate changes against DVR eval cases. | `eval_runs`, `eval_results` |
| `ApprovalCoordinatorAgent` | Prepare human review packets and record approvals/rejections. | `approval_events`, version registry |
| `VersionRegistryAgent` | Register active prompt/template/checklist/RAG versions. | `artifact_versions` |

Keep production writer agents focused on DVR generation. Do not let them rewrite their own prompts.

## Tool Boundaries

Use narrow Python tools:

- `MemoryReadTool(scope, scope_id, memory_type, limit)`;
- `MemoryWriteTool(memory_record)`;
- `LearningProposalCreateTool(proposal)`;
- `EvalRunTool(proposal_id, eval_case_ids)`;
- `ApprovalRequestTool(proposal_id, summary)`;
- `VersionRegisterTool(artifact, version, approval_id)`.

Each tool should use Pydantic input/output and log:

- caller agent;
- project/user scope;
- timestamp;
- source evidence ids;
- write result;
- denied actions.

## What Can Be Automatic

Allowed without human approval:

- store session state;
- store project-scoped missing-data notes;
- store QA findings;
- create learning proposals;
- run eval cases;
- generate review packets;
- mark a proposal as eval failed.

## What Requires Approval

Always require human approval before:

- activating a new prompt version;
- changing RAG filters, chunking, reranking, or source priority;
- changing DOCX template structure;
- changing QA checklist thresholds;
- changing tool permissions;
- changing memory retention/PII policy;
- deploying behavior changes to production.

## Workflow Sketch

```python
class LearningProposal(BaseModel):
    type: str
    target_component: str
    problem: str
    evidence_ids: list[str]
    proposed_change: str
    expected_benefit: str
    risk_assessment: str
    eval_case_ids: list[str]

# Orchestrator flow:
# 1. QA agents write findings.
# 2. LearningProposalAgent groups findings and creates proposals.
# 3. EvalRunnerAgent tests candidate changes.
# 4. ApprovalCoordinatorAgent asks human for approval.
# 5. VersionRegistryAgent activates approved versions.
```

## Runtime Reminder

The Agno runtime should not use broad MCP servers for this loop. MCP can help Codex/developers inspect systems during development, but production agents should use typed application tools only.

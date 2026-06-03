# Doctor And Control UX

## DvrDoctorAgent

Purpose: provide a safe operational diagnostic command, inspired by OpenClaw-style doctor/audit checks.

## Checks

Run read-only checks first:

- app version and environment;
- active LLM provider;
- Supabase connectivity;
- RAG functions availability;
- RLS/grant warnings;
- template files present;
- prompt/template/checklist active versions;
- pending learning proposals;
- pending approvals;
- failed jobs;
- Render deployment health if configured;
- webhook status for Telegram.

## Doctor Output

```json
{
  "status": "warning",
  "checks": [
    {
      "name": "rag_metadata_quality",
      "status": "warning",
      "message": "RAG metadata is sparse; filtering by ATECO/risk_category is limited.",
      "action": "Run RAG metadata enrichment plan."
    }
  ],
  "safe_actions": [],
  "approval_required_actions": [
    "change_rag_policy",
    "rotate_provider_credentials"
  ]
}
```

## Control Dashboard

Future UI should show:

- DVR progress by section;
- missing data;
- generated versions;
- RAG sources;
- QA findings;
- pending approvals;
- learning proposals;
- provider status;
- audit log.

The dashboard should call backend APIs, not MCP servers directly.

## Operator UX Rules

- Show uncertainty and blockers clearly.
- Make destructive/high-impact actions two-step.
- Keep approval packets human-readable.
- Give download links only to authorized users.
- Log every approval/rejection.

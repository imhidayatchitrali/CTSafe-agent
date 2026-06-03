# Auth, Commands, And Sessions

## AuthGate

Authorize before routing.

Checks:

- user is in allowlist or belongs to approved organization;
- chat/group is approved;
- command is allowed for role;
- project/document scope exists;
- high-impact actions require confirmation.

## Roles

| Role | Examples | Capabilities |
|---|---|---|
| `client_user` | Customer operator | Start DVR, provide data, request status, request revision, download outputs. |
| `ctsafe_reviewer` | Internal reviewer | Approve learning proposals, approve final outputs, override QA blocks. |
| `admin` | Technical admin | Run doctor, configure providers, inspect logs, manage deploy/config. |

## Commands

| Command | Purpose | Approval level |
|---|---|---|
| `/nuovo_dvr` | Start a DVR project/intake. | Authorized client |
| `/stato_dvr` | Show current project/document status. | Authorized project user |
| `/mancanti` | List missing data blocking generation. | Authorized project user |
| `/fonti` | Show RAG evidence/citations for current section/document. | Authorized project user |
| `/revisioni` | List pending revision requests. | Authorized project user/reviewer |
| `/approva` | Approve a draft, proposal, or action. | Reviewer/admin depending on target |
| `/blocca` | Pause generation or deployment. | Reviewer/admin |
| `/doctor` | Run system diagnostics. | Admin |
| `/provider` | Show/change LLM provider status. | Admin |

## Session Keys

Use explicit isolation:

```text
org_id:user_id:project_id:document_id:channel
```

If `project_id` or `document_id` is missing, route to intake/context selection before continuing.

## Session State

Store:

- active project/document;
- current workflow step;
- missing data requests;
- pending approvals;
- last safe command;
- last generated artifact version;
- provider used.

Never store secrets in session state.

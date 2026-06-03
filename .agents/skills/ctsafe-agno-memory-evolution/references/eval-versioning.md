# Eval Dataset And Versioning

## Eval Dataset For DVR Prompts

An eval dataset is a collection of representative DVR tasks used to test whether prompts, RAG policy, templates, and QA checklists are improving.

Each eval case should include:

- input project facts;
- target agent/workflow;
- required checks;
- forbidden behaviors;
- optional gold/reference snippets;
- required RAG evidence categories;
- expected structured output fields.

## Example Eval Case

```json
{
  "case_id": "dvr_magazzino_mmc_001",
  "target": "SectionWriterAgent",
  "section": "Movimentazione manuale dei carichi",
  "input": {
    "sector": "logistica",
    "mansions": ["magazziniere", "impiegato amministrativo"],
    "activities": ["scarico merci", "uso videoterminale"],
    "known_risks": ["MMC", "VDT"]
  },
  "required_checks": [
    "MMC is linked to magazziniere, not impiegato amministrativo",
    "VDT is not mixed into the MMC section",
    "missing measurements are marked as missing, not invented",
    "preventive measures are specific to handling goods",
    "at least one normative evidence item is attached"
  ],
  "forbidden_behaviors": [
    "inventing load weights",
    "claiming measurements were performed if absent",
    "using previous DVR examples as legal authority"
  ]
}
```

## Eval Metrics

Track:

- parse success for structured output;
- required check pass rate;
- forbidden behavior count;
- citation/evidence coverage;
- missing-data honesty;
- reviewer acceptance rate;
- latency and token cost;
- regression against previous prompt version.

## Version Registry

Treat these artifacts as versioned production inputs:

- prompts;
- RAG policy;
- retrieval functions;
- DOCX templates;
- QA checklists;
- tool schemas;
- model configuration;
- memory policy.

## Suggested Registry Shape

```json
{
  "artifact": "prompts/section_writer.md",
  "version": "v2",
  "status": "active",
  "created_from_proposal": "lp_2026_0001",
  "approved_by": "human_reviewer",
  "approved_at": "2026-05-27T18:30:00Z",
  "eval_summary": {
    "cases_run": 24,
    "pass_rate": 0.92,
    "regressions": 0
  }
}
```

## DVR Traceability

Every generated DVR should store:

- prompt versions used by each agent;
- RAG policy version;
- template version;
- checklist version;
- model/version;
- retrieval result ids;
- QA result ids;
- human approvals and revisions.

This makes incidents debuggable and prevents silent behavior drift.

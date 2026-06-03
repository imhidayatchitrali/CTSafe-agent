# DVR Validation Checklists

Use this reference for `SectionQAAgent`, `DocumentQAAgent`, human review preparation, and Codex review tasks.

## Section QA

Return one of:

- `approved`
- `needs_revision`
- `blocked_missing_data`

Check:

- The section answers the section brief.
- Company facts match input data.
- Mansions, risks, DPI, equipment, and environments are coherent.
- Normative references are supported by retrieved sources or provided data.
- Placeholder fields are visible and intentional.
- No template company data leaked into the new DVR.
- No unsupported measurements, names, dates, or certificates.
- Content is specific enough for the company sector.
- Tables are complete and readable.
- Retrieved chunks are saved or referenced.

## Document QA

Check:

- Required sections are present.
- Section order and numbering are consistent.
- Company data is consistent across cover, anagrafica, sections, and tables.
- Risk family coverage matches activity, ATECO, mansions, sites, substances, equipment.
- DPI table is aligned with risks/mansions.
- Health surveillance section matches actual risks and missing data is visible.
- Training/addestramento section matches risk class and activities.
- Emergency section matches locations and fire/first-aid needs.
- Improvement plan has actions, priority, owner/responsible role, target date/status.
- No hallucinated legal claims or unsupported obligations.
- No unresolved placeholders unless explicitly marked for human completion.
- DOCX renders cleanly if render QA is available.

## Common Failure Modes

- Generic risks not tied to mansions.
- Missing context risks such as fire, microclimate, confined spaces, ATEX, radon when applicable.
- Missing content risks such as MMC, VDT, noise, vibration, chemical, biological, work at height.
- DPI listed without associated risk or mansion.
- Improvement plan too vague.
- Normative references listed but not used in text.
- Template company names, roles, addresses, or dates leaked into output.
- `indice` examples treated as normative evidence.
- `match_indice` used despite being broken in the live DB.

## QA Report Shape

```json
{
  "qa_status": "approved",
  "issues": [],
  "missing_data": [],
  "unsupported_claims": [],
  "retrieval_gaps": [],
  "suggested_fix": "",
  "human_review_required": true
}
```


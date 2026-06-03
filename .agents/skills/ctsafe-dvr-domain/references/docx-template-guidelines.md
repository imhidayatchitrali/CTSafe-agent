# DOCX Template Guidelines

Use this reference when rendering, validating, or planning the DVR DOCX.

## Template Source

Primary analyzed template:

`esempi dvr per template/01_DVR-spheractsafe (1).docx`

Observed structure:

- 4421 non-empty paragraphs
- 120 tables
- Main Word styles: `Titolo1`, `Titolo2`, `Paragrafoelenco`
- 12 top-level chapters
- 43 second-level sections

## Template Must Preserve

- Editable `.docx` output
- Cover page or opening metadata block
- Company data tables
- Signature/role blocks
- Real Word heading styles
- Tables for repeated structured data
- Section numbering
- Footer/header behavior where present
- Professional CT Safe tone and layout

## Template-Derived Top-Level Chapters

Use this as style and structure reference, not as a rigid universal index:

1. Gestione della prevenzione nei luoghi di lavoro
2. Identificazione dell'attivita
3. Organizzazione della sicurezza e del servizio di prevenzione e protezione
4. Criteri adottati per l'effettuazione della valutazione dei rischi
5. Valutazione preliminare dei rischi
6. Rischi connessi con il contesto di lavoro
7. Rischi connessi con il contenuto del lavoro
8. Dispositivi di protezione individuali (DPI)
9. Sorveglianza sanitaria
10. Sostanze psicotrope e alcool
11. Differenze di genere, eta e provenienza
12. Programma di miglioramento

## Common Table Types

Use tables for:

- Company key-value metadata
- Roles and safety organization
- Mansions, tasks, equipment, risks
- Risk scoring matrices
- DPI by risk/mansion
- Training/surveillance schedules
- Improvement plan
- Worker lists and emergency team data

Do not force long prose into tables. If a cell becomes a paragraph, use prose with bullets instead.

## Placeholder Discipline

Allowed placeholders when data is missing:

- `________________`
- `DA VERIFICARE`
- `DATO MANCANTE`
- `NON APPLICABILE - motivazione: ...`

Never silently invent:

- Names of RSPP, medico competente, RLS, emergency workers
- Inspection dates or certificate dates
- Measurements for noise, vibration, chemical exposure, radon, ATEX zones
- Training records
- Signatures

## Rendering Rules

When creating final documents:

- Prefer `docxtpl` for simple placeholders.
- Prefer Word content controls for a robust production template.
- Use `python-docx` or OOXML-level editing for deterministic layout and tables.
- Preserve real heading styles and numbering.
- Generate `DVR_v1.docx`, metadata, QA report, and changelog.
- Visually render and inspect DOCX when possible before delivery.


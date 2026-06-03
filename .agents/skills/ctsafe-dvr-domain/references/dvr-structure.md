# DVR Structure Reference

Use this reference when generating or validating a DVR index, section plan, or full document.

## What A DVR Is

A DVR is the Documento di Valutazione dei Rischi required for workplace health and safety management. In this project, it is a structured technical document that records company context, risk evaluation criteria, identified risks, prevention/protection measures, DPI, health surveillance, training, emergency management, and improvement planning.

AI output is a draft support artifact. It must be reviewed by qualified human/professional stakeholders before being treated as final.

## Minimum Data Before Generation

Do not generate a final-grade DVR without these fields:

- Ragione sociale
- Partita IVA
- Codice ATECO
- Descrizione attivita
- Numero dipendenti
- Mansioni
- Indirizzo sede
- Tipo documento
- Categoria rischio
- Pericoli settore
- Rischi per mansione
- Normativa riferimento or retrievable normative context

If fields are missing, ask for them or mark the affected sections as placeholders.

## Canonical Structure

The template DOCX analyzed has 12 top-level chapters and 43 second-level sections:

1. Gestione della prevenzione nei luoghi di lavoro
2. Identificazione dell'attivita
3. Organizzazione della sicurezza e del servizio di prevenzione e protezione
4. Criteri adottati per l'effettuazione della valutazione dei rischi
5. Valutazione preliminare dei rischi
6. Rischi connessi con il contesto di lavoro
7. Rischi connessi con il contenuto del lavoro
8. Dispositivi di protezione individuali (DPI)
9. Sorveglianza sanitaria
10. Problemi connessi all'utilizzo di sostanze psicotrope e alcool
11. Differenze di genere, eta e provenienza da altri paesi
12. Programma di miglioramento

## Required Section Families

Always check whether the index covers:

- Anagrafica aziendale and document metadata
- Sedi, luoghi di lavoro, ciclo produttivo, attivita
- Mansioni and worker groups
- Organization of prevention: datore di lavoro, RSPP, medico competente, RLS, emergenze
- Methodology and risk scoring criteria
- Context risks: workplace, seismic, microclimate, confined spaces, radon, fire, ATEX where applicable
- Content risks: equipment, vehicles, electrical systems, MMC, VDT, noise, vibration, CEM, ROA, chemical, carcinogenic/mutagenic, asbestos, biological, work at height, aggression, stress
- DPI by risk/mansion
- Health surveillance
- Training, information, addestramento
- Emergency management
- Appalti/DUVRI where applicable
- Improvement program
- Annexes and signatures/placeholders

## Writing Standards

- Use technical, direct, professional Italian.
- Prefer section-specific content over generic safety prose.
- Tie obligations and controls to actual operations.
- Avoid vague phrases such as "adottare tutte le misure necessarie" unless followed by concrete measures.
- If a risk is not applicable, state the reason or mark it as "non applicabile" with evidence.
- Do not copy a template company or names into a new DVR.

## Section Output Shape

For each section, preserve:

- `section_number`
- `title`
- `purpose`
- `company_data_used`
- `retrieval_query`
- `retrieved_chunk_ids`
- `draft_markdown`
- `citations_or_source_notes`
- `qa_status`
- `missing_data`


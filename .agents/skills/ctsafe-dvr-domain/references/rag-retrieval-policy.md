# Supabase RAG Retrieval Policy

Use this reference when searching Supabase RAG or designing RAG tools for Agno.

## Live Corpus State

The existing Supabase RAG, analyzed through Google MCP Toolbox on 2026-05-27, contains:

| Table | Rows | Role |
|---|---:|---|
| `normativa` | 27668 | Main normative corpus, fully vectorized |
| `indice` | 18 | Small corpus for index/template examples |
| `dvr_pregressi` | 0 | Prepared but empty |

Embeddings are 1536-dimensional for populated rows. Retrieval is based on `pgvector` cosine similarity and SQL functions.

## Existing Retrieval Functions

- `match_normativa`: searches `normativa`, supports `metadata @> filter`.
- `match_dvr_pregressi`: searches `dvr_pregressi`, supports `metadata @> filter`.
- `match_documents`: searches `indice`, but does not effectively apply metadata filtering.
- `match_indice`: legacy/broken; points to missing table `documents`.

Do not rely on `match_indice` until fixed. Treat `match_documents` as the practical legacy function for `indice`.

## Known Weaknesses

- `indice` has no vector index.
- `dvr_pregressi` is empty.
- RLS is disabled on public RAG tables.
- Grants are too broad for `anon` and `authenticated`.
- Metadata is mostly technical: `source`, `blobType`, `loc`, `pdf`.
- Semantic metadata is missing: ATECO, mansioni, risk category, section type, document type, normative refs.
- `normativa` has heavy exact duplication: 11486 duplicate rows beyond the first copy.
- 461 `normativa` chunks are under 100 characters.

## Retrieval Rules For Current Legacy Corpus

Use the corpus by task:

- Index generation: query `indice` for structure examples, then use company data to adapt. Do not use `indice` as law.
- Normative grounding: query `normativa`.
- Prior DVR examples: only use `dvr_pregressi` after it is populated with validated, anonymized DVRs.
- Template/style: use DOCX template analysis, not normative corpus.

Always save the chunks used in the section record or QA report.

## Query Planning

Build retrieval queries from:

- ATECO and activity description
- Mansions
- Equipment/vehicles
- Substances and processes
- Environment/site context
- Section objective
- Risk type
- Specific normative references requested by the brief

Run multiple targeted queries instead of one huge query when the section covers different risk families.

## Target `rag_chunks` Direction

Move toward a unified `rag_chunks` table with strong metadata:

- `corpus`
- `legacy_table`
- `legacy_id`
- `source_type`
- `risk_category`
- `section_type`
- `ateco_codes`
- `mansioni`
- `ambienti`
- `attrezzature`
- `document_type`
- `normative_refs`
- `source_document`
- `source_page`
- `line_from`
- `line_to`
- `valid_from`
- `valid_to`
- `metadata`

Target retrieval order:

1. Apply structured filters.
2. Run vector search.
3. Add keyword/hybrid search when available.
4. Rerank if evidence is broad or contradictory.
5. Save retrieved chunk IDs and source notes.

## Evidence Discipline

- Cite or reference only what was retrieved or provided.
- If retrieved chunks are generic, mark the section as needing better evidence.
- Do not fabricate article numbers, decrees, thresholds, measurements, or periodicities.
- Use low generation temperature for DVR text: about `0.1` to `0.2`.


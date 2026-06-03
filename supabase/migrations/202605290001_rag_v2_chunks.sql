-- CT Safe DVR Agent - RAG v2 unified chunks.
-- Runtime access remains through narrow RPC functions. Do not drop legacy
-- tables/functions in this migration; they remain the transition fallback.

create extension if not exists pgcrypto;
create extension if not exists vector;

create table if not exists public.rag_chunks (
  id uuid primary key default gen_random_uuid(),
  corpus text not null check (corpus in ('normativa', 'indice', 'dvr_pregressi')),
  legacy_table text,
  legacy_id text,
  content text not null check (length(trim(content)) > 0),
  embedding vector(1536) not null,
  metadata jsonb not null default '{}'::jsonb,
  source_type text not null default 'unknown',
  source_document text,
  source_page integer,
  line_from integer,
  line_to integer,
  risk_category text,
  section_type text,
  ateco_codes text[] not null default '{}',
  mansioni text[] not null default '{}',
  ambienti text[] not null default '{}',
  attrezzature text[] not null default '{}',
  document_type text,
  normative_refs text[] not null default '{}',
  valid_from date,
  valid_to date,
  is_active boolean not null default true,
  quality_flags text[] not null default '{}',
  content_hash text generated always as (encode(digest(content, 'sha256'), 'hex')) stored,
  search_vector tsvector generated always as (to_tsvector('italian', content)) stored,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint rag_chunks_source_page_positive check (source_page is null or source_page > 0),
  constraint rag_chunks_lines_ordered check (
    line_from is null
    or line_to is null
    or line_to >= line_from
  )
);

create unique index if not exists rag_chunks_legacy_identity_uidx
  on public.rag_chunks(corpus, legacy_table, legacy_id)
  where legacy_table is not null and legacy_id is not null;

do $$
begin
  if to_regclass('public.normativa') is not null then
    execute $sql$
      insert into public.rag_chunks (
        corpus,
        legacy_table,
        legacy_id,
        content,
        embedding,
        metadata,
        source_type,
        source_document,
        source_page,
        document_type,
        quality_flags
      )
      select
        'normativa',
        'normativa',
        id::text,
        content,
        embedding,
        coalesce(metadata, '{}'::jsonb)
          || jsonb_build_object(
            'corpus', 'normativa',
            'source_type', 'normativa',
            'legacy_table', 'normativa',
            'legacy_id', id::text
          ),
        'normativa',
        nullif(
          coalesce(
            metadata->>'source_document',
            metadata->>'pdf',
            metadata->>'file_name',
            case when metadata->>'source' <> 'blob' then metadata->>'source' end
          ),
          ''
        ),
        case
          when (metadata #>> '{loc,pageNumber}') ~ '^[0-9]+$'
            then (metadata #>> '{loc,pageNumber}')::integer
          when (metadata->>'source_page') ~ '^[0-9]+$'
            then (metadata->>'source_page')::integer
          else null
        end,
        'normativa',
        case
          when metadata->>'source' = 'blob' then array['legacy_metadata_weak']::text[]
          else '{}'::text[]
        end
      from public.normativa
      where content is not null
        and length(trim(content)) > 0
        and embedding is not null
      on conflict do nothing
    $sql$;
  end if;
end $$;

do $$
begin
  if to_regclass('public.indice') is not null then
    execute $sql$
      insert into public.rag_chunks (
        corpus,
        legacy_table,
        legacy_id,
        content,
        embedding,
        metadata,
        source_type,
        source_document,
        source_page,
        document_type,
        quality_flags
      )
      select
        'indice',
        'indice',
        id::text,
        content,
        embedding,
        coalesce(metadata, '{}'::jsonb)
          || jsonb_build_object(
            'corpus', 'indice',
            'source_type', 'template_structure',
            'legacy_table', 'indice',
            'legacy_id', id::text
          ),
        'template_structure',
        nullif(
          coalesce(
            metadata->>'source_document',
            metadata->>'pdf',
            metadata->>'file_name',
            case when metadata->>'source' <> 'blob' then metadata->>'source' end
          ),
          ''
        ),
        case
          when (metadata #>> '{loc,pageNumber}') ~ '^[0-9]+$'
            then (metadata #>> '{loc,pageNumber}')::integer
          when (metadata->>'source_page') ~ '^[0-9]+$'
            then (metadata->>'source_page')::integer
          else null
        end,
        'dvr_template',
        case
          when metadata->>'source' = 'blob' then array['legacy_metadata_weak']::text[]
          else '{}'::text[]
        end
      from public.indice
      where content is not null
        and length(trim(content)) > 0
        and embedding is not null
      on conflict do nothing
    $sql$;
  end if;
end $$;

do $$
begin
  if to_regclass('public.dvr_pregressi') is not null then
    execute $sql$
      insert into public.rag_chunks (
        corpus,
        legacy_table,
        legacy_id,
        content,
        embedding,
        metadata,
        source_type,
        source_document,
        source_page,
        document_type,
        quality_flags
      )
      select
        'dvr_pregressi',
        'dvr_pregressi',
        id::text,
        content,
        embedding,
        coalesce(metadata, '{}'::jsonb)
          || jsonb_build_object(
            'corpus', 'dvr_pregressi',
            'source_type', 'dvr_pregresso',
            'legacy_table', 'dvr_pregressi',
            'legacy_id', id::text
          ),
        'dvr_pregresso',
        nullif(
          coalesce(
            metadata->>'source_document',
            metadata->>'pdf',
            metadata->>'file_name',
            case when metadata->>'source' <> 'blob' then metadata->>'source' end
          ),
          ''
        ),
        case
          when (metadata #>> '{loc,pageNumber}') ~ '^[0-9]+$'
            then (metadata #>> '{loc,pageNumber}')::integer
          when (metadata->>'source_page') ~ '^[0-9]+$'
            then (metadata->>'source_page')::integer
          else null
        end,
        'dvr_pregresso',
        case
          when metadata->>'source' = 'blob' then array['legacy_metadata_weak']::text[]
          else '{}'::text[]
        end
      from public.dvr_pregressi
      where content is not null
        and length(trim(content)) > 0
        and embedding is not null
      on conflict do nothing
    $sql$;
  end if;
end $$;

create index if not exists rag_chunks_embedding_hnsw_idx
  on public.rag_chunks using hnsw (embedding vector_cosine_ops)
  with (m = 16, ef_construction = 64);

create index if not exists rag_chunks_corpus_active_idx
  on public.rag_chunks(corpus, is_active);
create index if not exists rag_chunks_source_type_idx
  on public.rag_chunks(source_type);
create index if not exists rag_chunks_risk_category_idx
  on public.rag_chunks(risk_category);
create index if not exists rag_chunks_section_type_idx
  on public.rag_chunks(section_type);
create index if not exists rag_chunks_metadata_gin_idx
  on public.rag_chunks using gin(metadata);
create index if not exists rag_chunks_ateco_gin_idx
  on public.rag_chunks using gin(ateco_codes);
create index if not exists rag_chunks_mansioni_gin_idx
  on public.rag_chunks using gin(mansioni);
create index if not exists rag_chunks_normative_refs_gin_idx
  on public.rag_chunks using gin(normative_refs);
create index if not exists rag_chunks_search_vector_gin_idx
  on public.rag_chunks using gin(search_vector);

create or replace function public.rag_jsonb_text_array(input jsonb)
returns text[]
language sql
immutable
as $$
  select coalesce(array_agg(item.value), '{}'::text[])
  from jsonb_array_elements_text(
    case
      when input is null then '[]'::jsonb
      when jsonb_typeof(input) = 'array' then input
      else jsonb_build_array(input #>> '{}')
    end
  ) as item(value);
$$;

create or replace function public.rag_chunks_filter_match(
  row_source_type text,
  row_risk_category text,
  row_section_type text,
  row_document_type text,
  row_ateco_codes text[],
  row_mansioni text[],
  row_normative_refs text[],
  row_metadata jsonb,
  filter jsonb
)
returns boolean
language sql
stable
as $$
  with f as (
    select coalesce(filter, '{}'::jsonb) as value
  )
  select
    value = '{}'::jsonb
    or (
      (not value ? 'source_type' or row_source_type = value->>'source_type')
      and (not value ? 'risk_category' or row_risk_category = value->>'risk_category')
      and (not value ? 'section_type' or row_section_type = value->>'section_type')
      and (not value ? 'document_type' or row_document_type = value->>'document_type')
      and (
        not value ? 'ateco_codes'
        or cardinality(public.rag_jsonb_text_array(value->'ateco_codes')) = 0
        or row_ateco_codes && public.rag_jsonb_text_array(value->'ateco_codes')
      )
      and (
        not value ? 'mansioni'
        or cardinality(public.rag_jsonb_text_array(value->'mansioni')) = 0
        or row_mansioni && public.rag_jsonb_text_array(value->'mansioni')
      )
      and (
        not value ? 'normative_refs'
        or cardinality(public.rag_jsonb_text_array(value->'normative_refs')) = 0
        or row_normative_refs && public.rag_jsonb_text_array(value->'normative_refs')
      )
      and row_metadata @> (
        value
          - 'source_type'
          - 'risk_category'
          - 'section_type'
          - 'document_type'
          - 'ateco_codes'
          - 'mansioni'
          - 'normative_refs'
      )
    )
  from f;
$$;

create or replace function public.match_rag_chunks(
  query_embedding vector(1536),
  match_count integer default 5,
  filter jsonb default '{}'::jsonb,
  corpus_filter text default null
)
returns table (
  id uuid,
  chunk_id text,
  corpus text,
  content text,
  metadata jsonb,
  source_type text,
  source_document text,
  source_page integer,
  line_from integer,
  line_to integer,
  similarity double precision
)
language sql
stable
as $$
  select
    rag_chunks.id,
    rag_chunks.id::text as chunk_id,
    rag_chunks.corpus,
    rag_chunks.content,
    rag_chunks.metadata,
    rag_chunks.source_type,
    rag_chunks.source_document,
    rag_chunks.source_page,
    rag_chunks.line_from,
    rag_chunks.line_to,
    1 - (rag_chunks.embedding <=> query_embedding) as similarity
  from public.rag_chunks
  where rag_chunks.is_active = true
    and (corpus_filter is null or rag_chunks.corpus = corpus_filter)
    and public.rag_chunks_filter_match(
      rag_chunks.source_type,
      rag_chunks.risk_category,
      rag_chunks.section_type,
      rag_chunks.document_type,
      rag_chunks.ateco_codes,
      rag_chunks.mansioni,
      rag_chunks.normative_refs,
      rag_chunks.metadata,
      filter
    )
  order by rag_chunks.embedding <=> query_embedding
  limit greatest(1, least(match_count, 50));
$$;

create or replace function public.search_rag_chunks_text(
  search_terms text[],
  match_count integer default 20,
  filter jsonb default '{}'::jsonb,
  corpus_filter text default null
)
returns table (
  id uuid,
  chunk_id text,
  corpus text,
  content text,
  metadata jsonb,
  source_type text,
  source_document text,
  source_page integer,
  line_from integer,
  line_to integer,
  similarity double precision
)
language sql
stable
as $$
  select
    rag_chunks.id,
    rag_chunks.id::text as chunk_id,
    rag_chunks.corpus,
    rag_chunks.content,
    rag_chunks.metadata,
    rag_chunks.source_type,
    rag_chunks.source_document,
    rag_chunks.source_page,
    rag_chunks.line_from,
    rag_chunks.line_to,
    term_hits.score as similarity
  from public.rag_chunks
  cross join lateral (
    select
      count(*)::double precision / greatest(coalesce(cardinality(search_terms), 0), 1) as score
    from unnest(search_terms) as term(value)
    where term.value <> ''
      and rag_chunks.content ilike '%' || term.value || '%'
  ) as term_hits
  where rag_chunks.is_active = true
    and term_hits.score > 0
    and (corpus_filter is null or rag_chunks.corpus = corpus_filter)
    and public.rag_chunks_filter_match(
      rag_chunks.source_type,
      rag_chunks.risk_category,
      rag_chunks.section_type,
      rag_chunks.document_type,
      rag_chunks.ateco_codes,
      rag_chunks.mansioni,
      rag_chunks.normative_refs,
      rag_chunks.metadata,
      filter
    )
  order by term_hits.score desc, rag_chunks.created_at desc
  limit greatest(1, least(match_count, 100));
$$;

create or replace function public.match_normativa_v2(
  query_embedding vector(1536),
  match_count integer default 5,
  filter jsonb default '{}'::jsonb
)
returns table (
  id uuid,
  chunk_id text,
  corpus text,
  content text,
  metadata jsonb,
  source_type text,
  source_document text,
  source_page integer,
  line_from integer,
  line_to integer,
  similarity double precision
)
language sql
stable
as $$
  select * from public.match_rag_chunks(query_embedding, match_count, filter, 'normativa');
$$;

create or replace function public.match_indice_v2(
  query_embedding vector(1536),
  match_count integer default 5,
  filter jsonb default '{}'::jsonb
)
returns table (
  id uuid,
  chunk_id text,
  corpus text,
  content text,
  metadata jsonb,
  source_type text,
  source_document text,
  source_page integer,
  line_from integer,
  line_to integer,
  similarity double precision
)
language sql
stable
as $$
  select * from public.match_rag_chunks(query_embedding, match_count, filter, 'indice');
$$;

create or replace function public.match_dvr_pregressi_v2(
  query_embedding vector(1536),
  match_count integer default 5,
  filter jsonb default '{}'::jsonb
)
returns table (
  id uuid,
  chunk_id text,
  corpus text,
  content text,
  metadata jsonb,
  source_type text,
  source_document text,
  source_page integer,
  line_from integer,
  line_to integer,
  similarity double precision
)
language sql
stable
as $$
  select * from public.match_rag_chunks(query_embedding, match_count, filter, 'dvr_pregressi');
$$;

alter table public.rag_chunks enable row level security;
revoke all on public.rag_chunks from anon, authenticated;
revoke execute on function public.rag_jsonb_text_array(jsonb) from public;
revoke execute on function public.rag_chunks_filter_match(
  text,
  text,
  text,
  text,
  text[],
  text[],
  text[],
  jsonb,
  jsonb
) from public;
revoke execute on function public.match_rag_chunks(vector, integer, jsonb, text) from public;
revoke execute on function public.search_rag_chunks_text(text[], integer, jsonb, text) from public;
revoke execute on function public.match_normativa_v2(vector, integer, jsonb) from public;
revoke execute on function public.match_indice_v2(vector, integer, jsonb) from public;
revoke execute on function public.match_dvr_pregressi_v2(vector, integer, jsonb) from public;

grant select on public.rag_chunks to service_role;
grant execute on function public.rag_jsonb_text_array(jsonb) to service_role;
grant execute on function public.rag_chunks_filter_match(
  text,
  text,
  text,
  text,
  text[],
  text[],
  text[],
  jsonb,
  jsonb
) to service_role;
grant execute on function public.match_rag_chunks(vector, integer, jsonb, text) to service_role;
grant execute on function public.search_rag_chunks_text(text[], integer, jsonb, text) to service_role;
grant execute on function public.match_normativa_v2(vector, integer, jsonb) to service_role;
grant execute on function public.match_indice_v2(vector, integer, jsonb) to service_role;
grant execute on function public.match_dvr_pregressi_v2(vector, integer, jsonb) to service_role;

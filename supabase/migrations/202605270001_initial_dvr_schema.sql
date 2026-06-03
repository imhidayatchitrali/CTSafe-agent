-- CT Safe DVR Agent - initial operational schema for Fase 1 thin slice.
-- Runtime agents must use narrow backend tools/repositories, not broad MCP access.

create extension if not exists pgcrypto;

create table if not exists public.companies (
  id uuid primary key default gen_random_uuid(),
  company_name text not null,
  vat_number text not null,
  ateco_code text not null,
  activity_description text not null,
  employee_count integer not null check (employee_count >= 0),
  mansions text[] not null default '{}',
  site_address text not null,
  document_type text not null,
  risk_category text not null,
  sector_hazards text[] not null default '{}',
  risks_by_mansion jsonb not null default '{}'::jsonb,
  normative_references text[] not null default '{}',
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.dvr_projects (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies(id) on delete restrict,
  status text not null check (status in (
    'intake_pending_confirmation',
    'blocked_missing_data',
    'data_confirmed',
    'index_draft',
    'index_approved',
    'index_needs_revision',
    'pilot_sections_generated',
    'draft_document_created',
    'needs_revision'
  )),
  source_channel text not null default 'api',
  created_by text not null,
  confirmed_by text,
  confirmed_at timestamptz,
  source_airtable_record_id text,
  legacy_airtable_status text,
  active_index_id uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.dvr_indexes (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.dvr_projects(id) on delete cascade,
  version integer not null default 1,
  status text not null check (status in ('draft', 'approved', 'rejected', 'needs_revision')),
  title text not null default 'Indice DVR preliminare',
  sections jsonb not null,
  rag_evidence_ids text[] not null default '{}',
  approved_by text,
  approved_at timestamptz,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (project_id, version)
);

alter table public.dvr_projects
  add constraint dvr_projects_active_index_fk
  foreign key (active_index_id) references public.dvr_indexes(id)
  deferrable initially deferred;

create table if not exists public.dvr_sections (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.dvr_projects(id) on delete cascade,
  index_id uuid not null references public.dvr_indexes(id) on delete restrict,
  section_number text not null,
  title text not null,
  brief jsonb not null,
  status text not null check (status in (
    'planned',
    'in_progress',
    'generated',
    'qa_approved',
    'needs_revision',
    'blocked_missing_data'
  )),
  generated_markdown text,
  qa_status text check (qa_status in ('approved', 'needs_revision', 'blocked_missing_data')),
  qa_report jsonb not null default '{}'::jsonb,
  missing_data text[] not null default '{}',
  source_airtable_record_id text,
  legacy_project_ref text,
  legacy_airtable_status text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (project_id, section_number)
);

create table if not exists public.generated_documents (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.dvr_projects(id) on delete cascade,
  version integer not null,
  status text not null check (status in ('draft', 'superseded')),
  file_path text not null,
  file_format text not null default 'docx',
  editable boolean not null default true,
  metadata jsonb not null default '{}'::jsonb,
  created_by text not null,
  created_at timestamptz not null default now(),
  unique (project_id, version)
);

create table if not exists public.document_patches (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.dvr_projects(id) on delete cascade,
  target_section_id uuid references public.dvr_sections(id) on delete set null,
  instruction text not null,
  status text not null check (status in ('proposed', 'applied', 'rejected')),
  proposed_patch jsonb not null default '{}'::jsonb,
  created_by text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.agent_runs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.dvr_projects(id) on delete set null,
  agent_name text not null,
  input jsonb not null default '{}'::jsonb,
  output jsonb not null default '{}'::jsonb,
  status text not null,
  model text not null,
  llm_provider text not null,
  llm_provider_mode text not null default 'mock',
  tokens_input integer,
  tokens_output integer,
  cost_estimate numeric,
  error text,
  channel_event_id uuid,
  session_key text,
  prompt_version text,
  rag_policy_version text,
  created_at timestamptz not null default now()
);

create table if not exists public.section_evidence (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.dvr_projects(id) on delete cascade,
  section_id uuid not null references public.dvr_sections(id) on delete cascade,
  chunk_id text not null,
  query text not null,
  filters jsonb not null default '{}'::jsonb,
  score numeric not null,
  rank integer not null,
  source_document text,
  source_page integer,
  line_from integer,
  line_to integer,
  decision text not null default 'used',
  claim_or_section_part_supported text,
  retrieval_policy_version text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.audit_events (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.dvr_projects(id) on delete set null,
  actor_user_id text not null,
  actor_role text not null check (actor_role in ('client_user', 'ctsafe_reviewer', 'admin')),
  action text not null,
  target_type text,
  target_id text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.channel_events (
  id uuid primary key default gen_random_uuid(),
  channel text not null,
  external_event_id text,
  actor_user_id text,
  normalized_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists dvr_projects_company_id_idx on public.dvr_projects(company_id);
create index if not exists dvr_indexes_project_id_idx on public.dvr_indexes(project_id);
create index if not exists dvr_sections_project_id_idx on public.dvr_sections(project_id);
create index if not exists generated_documents_project_id_idx on public.generated_documents(project_id);
create index if not exists document_patches_project_id_idx on public.document_patches(project_id);
create index if not exists agent_runs_project_id_idx on public.agent_runs(project_id);
create index if not exists section_evidence_project_section_idx on public.section_evidence(project_id, section_id);
create index if not exists audit_events_project_id_idx on public.audit_events(project_id);
create index if not exists channel_events_actor_user_id_idx on public.channel_events(actor_user_id);

alter table public.companies enable row level security;
alter table public.dvr_projects enable row level security;
alter table public.dvr_indexes enable row level security;
alter table public.dvr_sections enable row level security;
alter table public.generated_documents enable row level security;
alter table public.document_patches enable row level security;
alter table public.agent_runs enable row level security;
alter table public.section_evidence enable row level security;
alter table public.audit_events enable row level security;
alter table public.channel_events enable row level security;

revoke all on public.companies from anon, authenticated;
revoke all on public.dvr_projects from anon, authenticated;
revoke all on public.dvr_indexes from anon, authenticated;
revoke all on public.dvr_sections from anon, authenticated;
revoke all on public.generated_documents from anon, authenticated;
revoke all on public.document_patches from anon, authenticated;
revoke all on public.agent_runs from anon, authenticated;
revoke all on public.section_evidence from anon, authenticated;
revoke all on public.audit_events from anon, authenticated;
revoke all on public.channel_events from anon, authenticated;


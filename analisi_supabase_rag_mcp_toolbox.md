# Analisi Supabase RAG tramite MCP Toolbox

Data analisi: 2026-05-27

Vincolo metodologico: tutte le informazioni sul database Supabase riportate in questo file sono state lette tramite Google MCP Toolbox / `toolbox.exe`, senza usare codice applicativo locale come fonte del contenuto del DB.

## 1. Sintesi esecutiva

Il database RAG attuale vive nello schema `public` e contiene tre sole tabelle:

- `normativa`
- `indice`
- `dvr_pregressi`

Il corpus realmente popolato oggi e' `normativa`, con `27.668` righe vettorializzate. `indice` contiene `18` righe e sembra fungere da corpus piccolo di esempi o struttura indice. `dvr_pregressi` e' presente ma vuota.

Il motore di retrieval e' basato su `pgvector` con similarita' coseno, tramite funzioni SQL `match_*`. Il design e' funzionale ma ancora semplice: chunk testuali + embedding + metadata JSONB minimi. Dal solo DB non emergono metadata semantici forti come ATECO, mansioni, categoria rischio o sezione del DVR.

## 2. Struttura attuale del DB

### 2.1 Tabelle pubbliche

- `dvr_pregressi`
- `indice`
- `normativa`

### 2.2 Colonne

`dvr_pregressi`
- `id bigint not null`
- `content text`
- `metadata jsonb`
- `embedding vector`

`indice`
- `id bigint not null`
- `content text`
- `metadata jsonb`
- `embedding vector`

`normativa`
- `id bigint not null`
- `content text`
- `metadata jsonb`
- `embedding vector`
- `created_at timestamptz default now()`

### 2.3 Volume dati

- `dvr_pregressi`: `0`
- `indice`: `18`
- `normativa`: `27668`

### 2.4 Estensioni rilevanti

- `vector 0.8.0`
- `pgcrypto`
- `pg_stat_statements`
- `supabase_vault`

## 3. Stato vettoriale

### 3.1 Integrita' embedding

- `normativa`: tutte le `27.668` righe hanno embedding
- `indice`: tutte le `18` righe hanno embedding
- `dvr_pregressi`: nessun dato

### 3.2 Dimensione embedding

- `normativa`: `1536`
- `indice`: `1536`
- `dvr_pregressi`: non applicabile

Quindi il corpus attivo usa embedding coerenti a 1536 dimensioni.

## 4. Funzioni di retrieval trovate

Sono presenti quattro funzioni nello schema `public`:

- `match_documents`
- `match_dvr_pregressi`
- `match_indice`
- `match_normativa`

### 4.1 Comportamento osservabile

`match_normativa`
- cerca in `normativa`
- usa distanza vettoriale coseno
- supporta filtro `metadata @> filter`
- ordina per similarita' e limita a `match_count`

`match_dvr_pregressi`
- cerca in `dvr_pregressi`
- supporta filtro `metadata @> filter`

`match_documents`
- cerca in `indice`
- non usa davvero il filtro metadata
- applica solo retrieval per similarita'

`match_indice`
- riferisce una tabella `documents`
- nel DB attuale la tabella `documents` non esiste
- appare quindi incoerente o legacy

## 5. Indici

### 5.1 Indici vettoriali

- `normativa_embedding_idx` su `normativa` con `ivfflat` e `vector_cosine_ops`
- `dvr_pregressi_embedding_idx` su `dvr_pregressi` con `ivfflat` e `vector_cosine_ops`

### 5.2 Assenza rilevante

La tabella `indice` non ha un indice vettoriale dedicato. Ha solo la primary key.

## 6. Metadata effettivamente presenti

### 6.1 `normativa`

- `blobType`
- `loc`
- `source`

### 6.2 `indice`

- `blobType`
- `loc`
- `pdf`
- `source`

### 6.3 Osservazione

I metadata sono utili per provenienza e localizzazione del chunk, ma non per retrieval semantico avanzato. Non emergono dal DB attuale chiavi come:

- `ateco`
- `risk_category`
- `section_type`
- `mansioni`
- `document_type` semantico
- `normative_refs`

## 7. Esempi di contenuto

### 7.1 `indice`

I sample mostrano chunk provenienti da un PDF DVR/template con:

- testo di copertina
- indice dei contenuti
- sezioni del documento
- metadata PDF con titolo, pagine e righe

### 7.2 `normativa`

I sample mostrano chunk normativi testuali, apparentemente derivati da file testo o OCR, con line span nei metadata.

## 8. Sicurezza osservabile dal DB

### 8.1 RLS

Su tutte le tabelle `public`:

- `rls_enabled = false`
- `rls_forced = false`

### 8.2 Grant

Le tabelle `dvr_pregressi`, `indice` e `normativa` hanno grant molto larghi anche per:

- `anon`
- `authenticated`
- `service_role`
- `postgres`

Tra i privilegi risultano anche:

- `SELECT`
- `INSERT`
- `UPDATE`
- `DELETE`
- `TRUNCATE`

## 9. Inferenza sul funzionamento del RAG

Dal solo DB si puo' inferire che il sistema attuale e' un RAG semplice basato su:

1. chunking del contenuto in `content`
2. embedding vettoriale in `embedding`
3. metadati minimi in `metadata`
4. retrieval SQL tramite funzioni `match_*`
5. ranking per distanza vettoriale coseno

Il corpus piu' importante e' `normativa`. `indice` appare come secondo corpus piccolo e specializzato. `dvr_pregressi` sembra predisposto ma non ancora attivato.

## 10. Criticita' gia' emerse

- `match_indice` punta a una tabella non presente (`documents`)
- `match_documents` e `match_indice` suggeriscono una storia evolutiva non completamente ripulita
- `indice` non ha indice vettoriale
- `dvr_pregressi` e' vuota
- metadata troppo poveri per retrieval filtrato serio
- nessuna RLS
- permessi molto ampi

## 11. Approfondimenti richiesti

### 11.1 Punto 1 - Qualita' e distribuzione dei chunk in `normativa`

#### Distribuzione lunghezza chunk

- totale chunk: `27668`
- minimo: `2` caratteri
- massimo: `1000` caratteri
- media: `759` caratteri
- p25: `649`
- p50: `841`
- p75: `943`
- p90: `983`

#### Bucket di lunghezza

- `<100`: `461`
- `100-299`: `1445`
- `300-599`: `3953`
- `600-999`: `21808`
- `1000+`: `1`

#### Span di righe nei metadata

- chunk con span rilevabile: `27668`
- span minimo: `1` riga
- span massimo: `74` righe
- span medio: `8` righe
- p50: `7`
- p90: `17`

#### Qualita' di base

- chunk vuoti: `0`
- chunk sotto `50` caratteri: `157`
- chunk sotto `100` caratteri: `461`
- metadata nulli: `0`

#### Duplicazione esatta

- gruppi di duplicati esatti: `7691`
- righe duplicate oltre la prima copia: `11486`
- massimo numero di copie dello stesso chunk: `49`

#### Valori metadata osservati

- `source = blob` per tutte le `27668` righe
- `blobType = text/plain` per tutte le `27668` righe

#### Lettura interpretativa

Dal solo DB si puo' inferire che `normativa` e' un corpus grande, totalmente vettorializzato e con chunking abbastanza uniforme, probabilmente orientato a blocchi testuali di alcune centinaia di caratteri. La concentrazione fortissima nel bucket `600-999` e il massimo quasi bloccato a `1000` suggeriscono un chunker con target o limite alto vicino a `1000` caratteri.

La qualita' minima del testo e' nel complesso buona:

- nessun chunk vuoto
- metadata presenti ovunque
- line span coerente e sistematico

I segnali di debolezza sono:

- `461` chunk molto corti
- forte duplicazione esatta
- metadata tutti piatti e non semantici

In pratica il corpus `normativa` e' utilizzabile per semantic retrieval, ma non e' ancora pulito/normalizzato come knowledge base di produzione ad alta precisione.

### 11.2 Punto 2 - Verifica tecnica di `indice` e delle funzioni di retrieval

#### Stato di `indice`

- righe: `18`
- embedding presenti: `18/18`
- dimensione embedding: `1536`
- lunghezza media chunk: `637`
- lunghezza minima: `284`
- lunghezza massima: `997`

#### Osservazioni strutturali

- `indice` ha un naming legacy nel DB:
  - default dell'id: `nextval('documents_id_seq'::regclass)`
  - primary key index: `documents_pkey`
- non esiste un indice vettoriale sulla colonna `embedding`

#### Funzioni `match_*`

Funzioni coerenti con tabelle esistenti:

- `match_documents -> indice`
- `match_normativa -> normativa`
- `match_dvr_pregressi -> dvr_pregressi`

Funzione incoerente:

- `match_indice -> documents`
- `documents` non esiste nel DB attuale

#### Problemi tecnici osservabili

1. `match_indice` e' rotta o legacy, perche' punta a una tabella assente.
2. `match_documents` sembra essere la vera funzione attiva per `indice`, ma il nome non e' coerente con la tabella attuale.
3. `match_documents` non usa `metadata @> filter`, a differenza di `match_normativa` e `match_dvr_pregressi`.
4. `indice` non ha indice vettoriale. Oggi pesa poco perche' ha 18 righe, ma e' una fragilita' strutturale se il corpus cresce.

#### Lettura interpretativa

Dal solo DB si puo' inferire che `indice` deriva da un refactor incompleto:

- probabile nome precedente: `documents`
- nome attuale tabella: `indice`
- parte delle funzioni e degli oggetti SQL sono stati aggiornati, parte no

Questo rende il sottosistema di retrieval su `indice` funzionale solo in modo parziale e meno robusto del corpus `normativa`.

### 11.3 Punto 3 - Proposta di nuova struttura Supabase compatibile con il DB attuale

La proposta seguente nasce solo dalle evidenze del DB attuale.

#### Obiettivi

- mantenere compatibilita' con `normativa`, `indice` e `dvr_pregressi`
- ridurre inconsistenze SQL
- introdurre metadata semantici forti
- rendere il retrieval filtrabile e auditabile
- migliorare sicurezza e performance

#### Proposta minima compatibile

1. Tenere le tabelle attuali come corpus legacy.
2. Aggiungere una tabella unificata, ad esempio `rag_chunks`.
3. Migrare progressivamente i dati dai corpus legacy verso `rag_chunks`.
4. Esporre nuove funzioni `match_rag_chunks_*` senza rompere subito le funzioni esistenti.

#### Tabella suggerita

```sql
create table public.rag_chunks (
  id uuid primary key default gen_random_uuid(),
  corpus text not null,
  legacy_table text,
  legacy_id bigint,
  content text not null,
  metadata jsonb not null default '{}'::jsonb,
  embedding vector(1536) not null,
  source text,
  blob_type text,
  source_document text,
  source_page integer,
  line_from integer,
  line_to integer,
  risk_category text,
  section_type text,
  ateco_codes text[],
  mansioni text[],
  normative_refs text[],
  language text,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);
```

#### Indici suggeriti

```sql
create index rag_chunks_embedding_idx
on public.rag_chunks
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

create index rag_chunks_corpus_idx on public.rag_chunks (corpus);
create index rag_chunks_metadata_gin on public.rag_chunks using gin (metadata);
create index rag_chunks_ateco_gin on public.rag_chunks using gin (ateco_codes);
create index rag_chunks_mansioni_gin on public.rag_chunks using gin (mansioni);
create index rag_chunks_normative_refs_gin on public.rag_chunks using gin (normative_refs);
```

#### Funzioni suggerite

- una funzione generica `match_rag_chunks(query_embedding, match_count, filter jsonb, corpus text default null)`
- funzioni wrapper opzionali:
  - `match_normativa_v2`
  - `match_indice_v2`
  - `match_dvr_pregressi_v2`

#### Correzioni minime urgenti anche senza nuova tabella

1. correggere `match_indice` per farla puntare davvero a `indice`
2. decidere se rinominare `match_documents` oppure mantenerla come alias esplicito
3. aggiungere indice vettoriale a `indice.embedding`
4. attivare RLS
5. restringere i grant a ruoli realmente necessari
6. introdurre metadata semantici nei nuovi caricamenti

#### Strategia di migrazione prudente

Fase 1
- lasciare intatte le tabelle attuali
- correggere funzioni incoerenti
- aggiungere indice vettoriale a `indice`

Fase 2
- creare `rag_chunks`
- duplicare dentro `rag_chunks` i corpus `normativa` e `indice`
- arricchire i metadata durante l'ingest

Fase 3
- far puntare il retrieval nuovo a `rag_chunks`
- mantenere le funzioni legacy come compatibilita' temporanea

#### Benefici attesi

- un solo modello dati per tutto il RAG
- retrieval filtrabile per dominio e contesto
- migliore auditabilita' delle fonti
- meno debito tecnico SQL
- minore rischio operativo su naming e funzioni legacy

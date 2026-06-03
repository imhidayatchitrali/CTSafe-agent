# Maxi guida progetto — Agente AI DVR con Agno, Supabase, Telegram, DOCX e DVR Quality Wiki

## 1. Obiettivo del progetto

L’obiettivo del progetto è riprogettare l’attuale agente AI per la generazione di DVR, oggi basato su workflow n8n, Airtable, Telegram, Supabase Vector Store e Google Apps Script, trasformandolo in un sistema agentico più robusto, modulare, versionabile e mantenibile usando:

- **Agno** come framework agentico principale;
- **Supabase** come database operativo, database vettoriale e storage;
- **Telegram** come canale conversazionale principale;
- **Ops Gateway** come layer operativo per canali, autorizzazioni, comandi, sessioni, routing, tool policy e audit;
- **DOCX modificabile** come formato finale del DVR;
- **DVR Quality Wiki** come piccolo livello curato di memoria qualitativa, autocontrollo e apprendimento dagli errori;
- **Render** come target preferito per backend AgentOS/FastAPI;
- **Vercel** solo come opzione per frontend, dashboard o preview web;
- **OpenAI API / altri LLM provider** come modelli di generazione e embedding, con provider tracciato in ogni run/DVR.

Il sistema deve permettere di:

1. ricevere in input dati aziendali e un indice/categorie di rischio;
2. interrogare un database vettoriale basato su Supabase;
3. generare sezioni del DVR usando template e contenuti contestuali;
4. creare un documento Word modificabile manualmente;
5. permettere modifiche successive via agente AI;
6. versionare documenti, sezioni, revisioni e correzioni;
7. imparare dagli errori tramite feedback umano e DVR Quality Wiki curata;
8. esporre comandi operativi sicuri tramite gateway canali e autorizzazioni;
9. sostituire progressivamente i workflow n8n esistenti con agenti e tool Agno.

---

## 2. Riferimenti locali del progetto

I file di riferimento si trovano nella macchina locale nelle seguenti cartelle.

### 2.1 Workflow n8n attuali

Percorso locale:

```text
C:\Users\Amedeo Testa\Desktop\CTSafe agente dvr\agente ct-safe dvr attuale
```

Questa cartella contiene i workflow n8n esportati in JSON. I workflow analizzati sono:

```text
avvia_generazione (1).json
RAG DVR - Aggiunta Doc alla pipeline (1).json
Workflow 1 - Intake & Classificazione.json
Workflow 2 - RAG Retrieval & Generazione a Sezioni.json
Workflow 3 - Revisione + Creazione indice.json
Workflow 4 - Redattore.json
Workflow 5 - Creazione .docx DVR.json
```

I cinque `Workflow *` rappresentano la pipeline principale. `avvia_generazione (1).json` e' un workflow di supporto chiamato come tool dall'intake: crea il record in Airtable e invia il `record_id` al webhook `dvr-generation`. `RAG DVR - Aggiunta Doc alla pipeline (1).json` e' la pipeline di ingest documentale: legge file da Google Drive, usa OCR Mistral, genera embedding OpenAI, inserisce chunk in Supabase `normativa` e sposta i file processati.

Questi file rappresentano la pipeline attuale e devono essere usati come riferimento funzionale per ricostruire la logica in Agno.

---

### 2.2 Template ed esempi DVR

Percorso locale:

```text
C:\Users\Amedeo Testa\Desktop\CTSafe agente dvr\esempi dvr per template
```

Questa cartella contiene i DVR di esempio da usare come base per:

- template Word;
- struttura del documento;
- stile redazionale;
- sezioni standard;
- tabelle;
- layout;
- intestazioni;
- copertina;
- struttura rischi/mansioni/DPI;
- esempi di contenuto già validato.

Il file campione analizzato è:

```text
01_DVR-spheractsafe (1).docx
```

Questo documento deve essere considerato il riferimento principale per la struttura finale del DVR generato.

---

### 2.3 Guida funzionamento agente attuale

Percorso locale:

```text
C:\Users\Amedeo Testa\Desktop\CTSafe agente dvr\Guida Notion agente AI dvr.docx
```

Questa guida descrive il funzionamento operativo dell’agente attuale, inclusi:

- uso del bot Telegram;
- inserimento dati azienda;
- creazione riepilogo iniziale;
- conferma dati;
- passaggio su Airtable;
- controllo indice;
- validazione indice AI;
- validazione indice umana;
- generazione capitoli;
- redazione DVR;
- creazione documento;
- controllo finale.

La guida va usata per capire l’esperienza utente attuale e replicare, migliorandolo, il flusso operativo nel nuovo sistema.

---

### 2.4 Analisi Supabase RAG live

Percorso locale:

```text
C:\Users\Amedeo Testa\Desktop\CTSafe agente dvr\analisi_supabase_rag_mcp_toolbox.md
```

Questa analisi descrive lo stato reale del database Supabase usato dal RAG attuale, letto tramite Google MCP Toolbox / `toolbox.exe`.

Va usata come riferimento tecnico per:

- corpus RAG realmente esistenti;
- funzioni SQL `match_*`;
- indici vettoriali presenti o mancanti;
- qualità e duplicazione dei chunk;
- metadata disponibili;
- rischi RLS/grant;
- strategia di migrazione verso `rag_chunks`.

---

### 2.5 Mappatura Airtable "Documenti CT Safe"

Percorso locale:

```text
C:\Users\Amedeo Testa\Desktop\CTSafe agente dvr\mappatura_airtable_documenti_ct_safe.md
```

Questa analisi descrive la struttura reale della base Airtable usata dal sistema attuale:

- tabella `Progetti DVR` (`tbl2GOhTrhaE032us`);
- tabella `Capitoli DVR` (`tbl0zmvKGN4ms5ApU`);
- campi operativamente obbligatori;
- bottoni webhook;
- stati configurati;
- campi popolati da utente, AI o automazione;
- relazione progetto-capitoli oggi gestita come testo, non come linked record.

Va usata come riferimento per progettare la migrazione Airtable → Supabase senza perdere compatibilità con i workflow n8n esistenti.

---

### 2.6 MCP e skill del progetto

Percorso locale:

```text
C:\Users\Amedeo Testa\Desktop\CTSafe agente dvr\MCP_E_SKILLS_PROGETTO.md
```

Questo file definisce quali server MCP e quali skill usare per lo sviluppo del progetto e quali strumenti non devono diventare dipendenze runtime dell'agente Agno.

Principio chiave:

```text
Gli MCP servono soprattutto per sviluppo, ispezione, migrazione e amministrazione.
L'agente Agno in produzione deve usare tool Python tipizzati e con permessi stretti, non accessi MCP generici e troppo potenti.
```

Server/strumenti citati:

- Airtable MCP per leggere il sistema legacy e supportare la migrazione;
- Supabase MCP Toolbox per ispezione DB, RAG, funzioni SQL, RLS/grant e migrazioni;
- Agno MCP per sviluppo/allineamento AgentOS;
- Google Drive/Docs connector solo per recupero legacy, non come runtime core;
- Render MCP ufficiale come strumento amministrativo per Codex/sviluppatore, da configurare solo quando si decide il deploy e si dispone di API key Render;
- Vercel MCP ufficiale come strumento amministrativo opzionale per frontend, dashboard o preview web, non per il runtime Agno.

Skill locali rilevanti:

- `ctsafe-dvr-domain`;
- `ctsafe-agno-memory-evolution`;
- `ctsafe-agno-ops-gateway`;
- `supabase`;
- `supabase-postgres-best-practices`;
- `rag-implementation`;
- `ai-prompt-engineering-safety-review`;
- `prompt-engineering-patterns`;
- `systematic-debugging`;
- `docx`;
- `fastapi-python`;
- `n8n-expression-syntax`;
- `n8n-validation-expert`;
- `llm-wiki`;
- `wiki-setup`;
- `wiki-ingest` / `obsidian-wiki-ingest`;
- `wiki-capture` / `wiki-quick-chat-capture`;
- `wiki-lint`, `cross-linker`, `tag-taxonomy`, `wiki-dedup`, `wiki-synthesize`, `wiki-export`;
- `obsidian-markdown`, `obsidian-bases`, `json-canvas`.

Skill installate e poi rimosse per rischio:

```text
Ar9av/obsidian-wiki:
- daily-update
- data-ingest
- ingest-url
- wiki-agent
- wiki-query
- wiki-research

kepano/obsidian-skills:
- defuddle
- obsidian-cli
```

Motivo:

```text
Le prime sono state segnalate High/Critical Risk; `defuddle` e `obsidian-cli` sono state rimosse per prudenza perché marcate Med Risk.
```

Regola runtime:

```text
Agno deve esporre agenti/workflow via AgentOS MCP se serve, ma non deve ricevere accesso libero a Supabase MCP Toolbox, Airtable MCP o Google Drive.
Ogni tool Agno deve avere input/output Pydantic, permessi minimi e logging.
La wiki Obsidian/LLM Wiki è memoria di sviluppo per Codex. Agno può leggere solo export o pagine curate e non sensibili tramite tool read-only esplicito, mai la vault completa.
`prompt-engineering-patterns` è installata nel progetto con assessment CLI `Safe`, `0 alerts`, `Low Risk` e va usata per progettare prompt Agno versionati, structured output Pydantic/JSON, fallback, test e metriche.
Render è il target preferito per backend AgentOS/FastAPI. Vercel resta un'opzione per frontend, dashboard e preview, non per il core Agno.
Render MCP e Vercel MCP sono strumenti amministrativi per Codex/sviluppatore: non devono essere invocati dagli agenti DVR, non devono ricevere segreti nel prompt e ogni modifica infrastrutturale richiede conferma umana esplicita.
Render MCP non è ancora configurato perché la API key Render è ampia: configurarlo solo quando il progetto è pronto al deploy.
`ctsafe-agno-memory-evolution` è skill locale di progetto per memoria persistente, learning proposal, eval/versioning, implementazione Agno e guardrail. L'auto-miglioramento è ammesso solo come loop controllato: osservazione, proposta, eval, approvazione umana, nuova versione e monitoraggio.
`ctsafe-agno-ops-gateway` è skill locale di progetto per il layer operativo ispirato a OpenClaw: gateway canali, autorizzazioni, comandi operatore, routing agenti, sessioni isolate, tool policy, doctor/audit e UX di controllo.
Il bridge OpenAI subscription è ammesso solo come provider opzionale single-tenant: health check, fallback esplicito, niente token/cookie in prompt/log/memorie/wiki e provider tracciato in ogni run/DVR.
```

---

## 3. Stato attuale del sistema

L’attuale sistema è composto da:

```text
Telegram
  ↓
n8n
  ↓
AI Agent / OpenRouter / Claude
  ↓
Airtable
  ↓
Supabase Vector Store
  ↓
Google Apps Script
  ↓
Google Docs / DOCX
```

### 3.1 Componenti principali attuali

| Componente | Ruolo attuale |
|---|---|
| Telegram | Interfaccia iniziale con l’utente |
| n8n | Orchestrazione dei workflow |
| Airtable | Database operativo per progetti e capitoli |
| Supabase Vector Store | Retrieval per indice e normativa |
| OpenRouter / Claude | Modello LLM per classificazione, indice e redazione |
| Google Apps Script | Creazione finale del documento |
| Google Drive / Docs | Output finale e archiviazione documento |

---

### 3.2 Stato reale del Supabase RAG live

Analisi eseguita il 27/05/2026 tramite Google MCP Toolbox / `toolbox.exe`, senza usare codice applicativo locale come fonte del contenuto del database.

Nel database Supabase live il RAG attuale vive nello schema `public` e contiene tre corpus:

| Tabella | Righe | Stato |
|---|---:|---|
| `normativa` | 27.668 | Corpus principale, completamente vettorializzato |
| `indice` | 18 | Corpus piccolo per esempi/struttura indice |
| `dvr_pregressi` | 0 | Tabella predisposta ma non ancora popolata |

Tutte le righe presenti in `normativa` e `indice` hanno embedding a 1536 dimensioni. Il retrieval usa `pgvector` con similarità coseno e funzioni SQL `match_*`.

Funzioni trovate:

```text
match_normativa
match_dvr_pregressi
match_documents
match_indice
```

Osservazioni importanti:

- `match_normativa` e `match_dvr_pregressi` supportano filtro `metadata @> filter`;
- `match_documents` cerca nella tabella `indice`, ma non applica davvero filtro metadata;
- `match_indice` punta alla tabella legacy `documents`, che nel DB attuale non esiste;
- `indice` non ha indice vettoriale dedicato;
- `normativa` e `dvr_pregressi` hanno indice `ivfflat` su `embedding`;
- i metadata reali sono quasi solo tecnici/provenienza (`blobType`, `loc`, `source`, `pdf`) e non contengono metadata semantici forti come ATECO, mansioni, categoria rischio o tipo sezione;
- RLS risulta disattivata sulle tabelle RAG e i grant sono molto ampi anche per `anon` e `authenticated`.

Qualità osservata su `normativa`:

```text
chunk totali: 27.668
lunghezza media: 759 caratteri
p50: 841 caratteri
p90: 983 caratteri
chunk sotto 100 caratteri: 461
duplicati esatti oltre la prima copia: 11.486
massimo copie dello stesso chunk: 49
```

Lettura progettuale:

```text
Il corpus normativa è utilizzabile come base semantica, ma non è ancora una knowledge base RAG di produzione ad alta precisione.
Serve una migrazione prudente: mantenere le tabelle legacy, correggere le funzioni incoerenti, introdurre rag_chunks e arricchire i metadata nei nuovi ingest.
```

---

### 3.3 Stato reale della base Airtable operativa

Analisi eseguita sulla base Airtable `Documenti CT Safe`.

La base operativa attuale contiene due tabelle principali:

| Tabella Airtable | ID tabella | Ruolo |
|---|---|---|
| `Progetti DVR` | `tbl2GOhTrhaE032us` | Record padre del progetto DVR |
| `Capitoli DVR` | `tbl0zmvKGN4ms5ApU` | Record figli per brief e contenuti dei capitoli |

`Progetti DVR` contiene:

- anagrafica azienda;
- dati di classificazione rischio;
- bozza indice e indice validato;
- stato di avanzamento;
- bottoni webhook;
- link al documento finale.

Campi operativamente obbligatori in `Progetti DVR`:

```text
Ragione Sociale
Partita IVA
Codice ATECO
Descrizione Attività
N° Dipendenti
Mansioni
Indirizzo Sede
Tipo Documento
Categoria Rischio
Pericoli Settore
Rischi per Mansione
Normativa Riferimento
INDICE DVR
```

Stati reali configurati in `Stato DVR`:

```text
In validazione
Indice validato
In redazione
Redazione fatta - crea documento
DVR in creazione
DVR Creato
Errore
```

`Capitoli DVR` contiene:

- riferimento al progetto;
- numero, titolo e ordine capitolo;
- brief JSON/testuale;
- stato del singolo capitolo;
- contenuto generato.

Campi minimi in `Capitoli DVR`:

```text
Progetto DVR
Numero Capitolo
Titolo Capitolo
Brief
Stato
Ordine
Contenuto Generato
```

Stati reali configurati in `Stato`:

```text
Da redigere
In corso
Completato
```

Nota tecnica importante:

```text
Il campo `Progetto DVR` nella tabella `Capitoli DVR` è `singleLineText`, non `linkedRecord`.
Il collegamento padre-figlio è quindi testuale, ad esempio `rec... - Ragione Sociale`, e non una relazione normalizzata.
```

Implicazione per la migrazione:

```text
Supabase deve introdurre una relazione vera `dvr_sections.project_id -> dvr_projects.id`, ma conservare anche gli ID e i riferimenti Airtable legacy per audit, import incrementale e compatibilità temporanea.
```

---

## 4. Workflow n8n attuali

### 4.1 Workflow 1 — Intake & Classificazione

File locale:

```text
Workflow 1 - Intake & Classificazione.json
```

Questo workflow gestisce la prima interazione con l’utente.

Funzioni principali:

1. riceve messaggi Telegram;
2. estrae i dati aziendali obbligatori;
3. chiede dati mancanti;
4. classifica l’azienda;
5. identifica categoria rischio;
6. identifica pericoli del settore;
7. associa rischi alle mansioni;
8. propone un riepilogo all’utente;
9. salva il progetto dopo conferma esplicita.

Dati estratti:

```text
Ragione sociale
Partita IVA
Codice ATECO
Descrizione attività
Numero dipendenti
Mansioni principali
Indirizzo sede operativa
Tipo documento
Categoria rischio
Pericoli settore
Rischi per mansione
Normativa riferimento
```

Nel nuovo sistema questo workflow diventa:

```text
IntakeAgent
```

---

### 4.2 Workflow 2 — RAG Retrieval & Generazione a Sezioni

File locale:

```text
Workflow 2 - RAG Retrieval & Generazione a Sezioni.json
```

Questo workflow genera un indice DVR preliminare interrogando il vector store Supabase.

Funzioni principali:

1. riceve `record_id` del progetto;
2. recupera il progetto da Airtable;
3. costruisce una query basata su ATECO, attività, rischio e pericoli;
4. interroga Supabase Vector Store, tabella `indice`;
5. genera un indice potenziale;
6. aggiorna Airtable con l’indice DVR.

Nel nuovo sistema questo workflow diventa:

```text
IndexDraftAgent
```

Miglioramenti richiesti:

- usare filtri metadata;
- usare hybrid search;
- distinguere esempi di indice da normativa;
- salvare fonti recuperate;
- evitare retrieval troppo generico;
- salvare indice in tabella dedicata Supabase.

---

### 4.3 Workflow 3 — Revisione + Creazione indice

File locale:

```text
Workflow 3 - Revisione + Creazione indice.json
```

Questo workflow valida l’indice preliminare e genera i brief dei capitoli.

Funzioni principali:

1. riceve `record_id`;
2. recupera il progetto da Airtable;
3. imposta stato “In validazione”;
4. valida l’indice preliminare;
5. controlla capitoli obbligatori;
6. integra capitoli mancanti;
7. genera un JSON con:
   - validazione;
   - indice validato;
   - brief capitoli;
8. crea o aggiorna i capitoli nella tabella `Capitoli DVR`.

Nel nuovo sistema questo workflow diventa:

```text
IndexValidationAgent
SectionPlannerAgent
```

Output target:

```json
{
  "validazione": {
    "indice_originale_completo": true,
    "capitoli_aggiunti": [],
    "note": ""
  },
  "indice_validato": "...",
  "brief_capitoli": [
    {
      "numero": "1",
      "titolo": "Dati identificativi dell'azienda",
      "obiettivo": "...",
      "contenuto_richiesto": [],
      "dati_azienda_da_usare": [],
      "riferimenti_normativi_da_cercare": [],
      "mansioni_coinvolte": "tutte",
      "lunghezza_target": "1-2 pagine",
      "include_tabelle": true,
      "note_specifiche": "..."
    }
  ]
}
```

---

### 4.4 Workflow 4 — Redattore

File locale:

```text
Workflow 4 - Redattore.json
```

Questo workflow redige i capitoli del DVR.

Funzioni principali:

1. riceve `record_id`;
2. recupera il progetto da Airtable;
3. cerca capitoli con stato `Da redigere`;
4. processa i capitoli in batch;
5. interroga Supabase Vector Store, tabella `normativa`;
6. genera contenuto tecnico per ogni capitolo;
7. salva il contenuto generato;
8. aggiorna lo stato del capitolo.

Nel nuovo sistema questo workflow diventa:

```text
ChapterWriterAgent
SectionQAAgent
```

Miglioramenti richiesti:

- separare fonti normative da esempi DVR;
- associare ogni sezione ai chunk usati;
- introdurre QA automatico per ogni capitolo;
- rilevare placeholder, contraddizioni e dati mancanti;
- evitare salvataggio diretto senza validazione;
- salvare output in Markdown strutturato e in formato compatibile con DOCX.

---

### 4.5 Workflow 5 — Creazione .docx DVR

File locale:

```text
Workflow 5 - Creazione .docx DVR.json
```

Questo workflow crea il documento finale.

Funzioni principali:

1. riceve `record_id`;
2. recupera il progetto da Airtable;
3. cerca tutti i capitoli con stato `Completato`;
4. ordina i capitoli;
5. divide contenuti troppo lunghi in batch;
6. chiama Google Apps Script con:
   - `create`;
   - `add_chapters`;
   - `finalize`;
7. aggiorna Airtable con stato `DVR Creato`;
8. dovrebbe salvare il link Google Docs, ma nel workflow è indicato che questa parte manca o va completata.

Nel nuovo sistema questo workflow diventa:

```text
DocxRenderAgent
DocumentVersioningTool
StorageTool
```

Miglioramento principale:

```text
Eliminare Google Apps Script come componente core e generare DOCX direttamente in Python.
```

---

## 5. Architettura target

### 5.1 Schema generale

```text
Channel adapters
  ├── Telegram
  ├── WhatsApp futuro
  └── Web dashboard futuro
  ↓
AuthGate
  ↓
CommandRouter
  ↓
SessionManager
  ↓
AgentRouter / WorkflowRunner
  ↓
Agno AgentOS / FastAPI
  ↓
DVR Orchestrator Agent
  ├── IntakeAgent
  ├── IndexDraftAgent
  ├── IndexValidationAgent
  ├── SectionPlannerAgent
  ├── ChapterWriterAgent
  ├── SectionQAAgent
  ├── DocumentQAAgent
  ├── DocxRenderAgent
  ├── RevisionAgent
  ├── MemoryCuratorAgent
  ├── LearningProposalAgent
  ├── EvalRunnerAgent
  ├── ApprovalCoordinatorAgent
  └── VersionRegistryAgent
  ↓
Supabase
  ├── PostgreSQL
  ├── pgvector
  ├── Storage
  └── Auth opzionale
  ↓
DOCX versionato
  ↓
DVR Quality Wiki / quality feedback loop
  ↓
AuditLog + Control UX
```

---

### 5.2 Responsabilità dei componenti

| Componente | Responsabilità |
|---|---|
| Channel adapters | Normalizzano Telegram, futuri WhatsApp/web e output canale |
| AuthGate | Blocca utenti/chat non autorizzati e applica ruoli |
| CommandRouter | Instrada comandi operatore e workflow |
| SessionManager | Isola sessioni per org, utente, progetto, documento e canale |
| AgentRouter / WorkflowRunner | Mappa intenti/comandi verso agenti e workflow Agno |
| Agno | Orchestrazione agenti, tool, memoria, workflow |
| Supabase Postgres | Stato operativo, progetti, sezioni, versioni |
| Supabase pgvector | RAG su normativa, indici, sezioni esempio |
| Supabase Storage / S3 | File raw, template, DOCX, report QA |
| DOCX renderer | Generazione documento Word modificabile |
| RevisionAgent | Modifica successiva del documento |
| DVR Quality Wiki | Memoria di qualità curata, errori ricorrenti, checklist |
| Memory/Evolution subsystem | Memorie scoped, learning proposal, eval, approvazione e version registry |
| DvrDoctorAgent | Diagnostica read-only su sistema, RAG, template, provider, webhook e deploy |
| LlmProviderRouter | Seleziona provider LLM e registra provider/modello in ogni run/DVR |
| Render | Target preferito per backend Agno/AgentOS/FastAPI |
| Vercel | Opzione per frontend, dashboard e preview web |

---

### 5.3 Ops Gateway ispirato a OpenClaw

Il gateway operativo è il layer attorno ad Agno che rende sicuro e governabile l'uso reale dell'agente DVR.

Responsabilità:

- normalizzare eventi da Telegram, futuri WhatsApp e dashboard web;
- verificare autenticità webhook quando disponibile;
- autorizzare utente, chat, organizzazione, ruolo e scope progetto;
- convertire input canale in comandi/eventi interni tipizzati;
- instradare comandi verso workflow o agenti specializzati;
- isolare sessioni per `org_id:user_id:project_id:document_id:channel`;
- applicare tool policy prima di ogni chiamata tool;
- registrare audit log, provider, sessione, progetto, documento, prompt version e decisioni tool;
- esporre diagnostica read-only tramite `/doctor`.

Schema evento interno:

```json
{
  "event_id": "evt_123",
  "channel": "telegram",
  "channel_user_id": "123456",
  "channel_chat_id": "987654",
  "message_type": "text",
  "text": "/stato_dvr",
  "attachments": [],
  "received_at": "2026-05-27T18:00:00Z",
  "raw_ref": "telegram_update_id_123"
}
```

Ruoli minimi:

| Ruolo | Uso |
|---|---|
| `client_user` | Avvia DVR, fornisce dati, chiede stato/revisioni, scarica output |
| `ctsafe_reviewer` | Approva output, learning proposal e override QA motivati |
| `admin` | Esegue doctor, configura provider, ispeziona log, gestisce deploy/config |

Regole non negoziabili:

```text
Nessun utente non autenticato può generare, revisionare, approvare, esportare o cambiare configurazioni.
Nessun evento raw di canale può invocare direttamente tool ampi.
Nessun agente riceve tool fuori ruolo.
Le azioni distruttive o ad alto impatto devono essere a due passaggi e tracciate.
```

---

## 6. Agenti target in Agno

### 6.1 DVR Orchestrator Agent

Agente principale.

Coordina l’intero flusso.

Responsabilità:

- capire in che stato si trova il progetto;
- decidere quale agente chiamare;
- gestire comandi Telegram;
- creare job;
- aggiornare stato;
- notificare l’utente;
- gestire errori e retry.

Comandi gestiti:

```text
/nuovo_dvr
/stato_dvr
/mancanti
/fonti
/revisioni
/valida_indice
/redigi_dvr
/genera_documento
/modifica_documento
/scarica
/approva
/blocca
/annulla
```

---

### 6.2 IntakeAgent

Sostituisce Workflow 1.

Responsabilità:

- raccogliere dati aziendali;
- estrarre informazioni da messaggi testuali;
- analizzare eventuali allegati;
- chiedere solo dati mancanti;
- non inventare dati;
- classificare rischio;
- proporre riepilogo;
- attendere conferma utente;
- creare progetto.

Output consigliato:

```json
{
  "company": {
    "ragione_sociale": "",
    "partita_iva": "",
    "codice_ateco": "",
    "descrizione_attivita": "",
    "numero_dipendenti": "",
    "mansioni": [],
    "indirizzo_sede": "",
    "tipo_documento": ""
  },
  "classification": {
    "categoria_rischio": "",
    "pericoli_settore": [],
    "rischi_per_mansione": [],
    "normativa_riferimento": []
  },
  "missing_fields": [],
  "ready_for_confirmation": true
}
```

---

### 6.3 IndexDraftAgent

Sostituisce Workflow 2.

Responsabilità:

- generare indice preliminare;
- interrogare esempi di indice;
- usare dati azienda;
- usare categorie di rischio;
- produrre indice coerente con settore e tipo documento.

Input:

```text
company_data
risk_classification
document_type
```

Output:

```text
indice_dvr_preliminare
```

---

### 6.4 IndexValidationAgent

Sostituisce parte del Workflow 3.

Responsabilità:

- validare indice preliminare;
- verificare capitoli obbligatori;
- integrare capitoli mancanti;
- controllare coerenza con D.Lgs. 81/08;
- produrre indice validato.

Checklist minima capitoli:

```text
1. Dati identificativi dell'azienda
2. Descrizione attività e cicli lavorativi
3. Organigramma sicurezza
4. Metodologia valutazione rischi
5. Identificazione pericoli per mansione
6. Valutazione rischi
7. Misure prevenzione e protezione
8. Programma di miglioramento
9. DPI per mansione
10. Sorveglianza sanitaria
11. Informazione, formazione e addestramento
12. Gestione emergenze
13. Gestione appalti e DUVRI
14. Rischi specifici del settore
15. Planimetrie
16. Allegati
```

---

### 6.5 SectionPlannerAgent

Responsabilità:

- trasformare indice validato in sezioni operative;
- generare micro-brief per ogni capitolo;
- creare record `dvr_sections`;
- definire mansioni coinvolte;
- definire riferimenti da cercare;
- definire lunghezza target;
- indicare se servono tabelle.

Output:

```json
{
  "sections": [
    {
      "section_number": "1.1",
      "title": "Obiettivi",
      "brief": "...",
      "risk_category": null,
      "mansioni_coinvolte": ["tutte"],
      "requires_table": false,
      "target_length": "1 pagina"
    }
  ]
}
```

---

### 6.6 ChapterWriterAgent

Sostituisce Workflow 4.

Responsabilità:

- redigere ogni capitolo;
- recuperare contesto RAG;
- usare dati azienda;
- usare brief capitolo;
- mantenere stile del template;
- generare Markdown strutturato;
- salvare fonti recuperate.

Regole:

```text
- non inventare norme;
- non inventare dati aziendali;
- segnalare placeholder;
- usare solo dati disponibili;
- adattare contenuto a mansioni e rischi reali;
- non produrre contenuti generici se servono dati specifici;
- mantenere tono tecnico-professionale.
```

---

### 6.7 SectionQAAgent

Nuovo agente non presente in modo esplicito nel sistema attuale.

Responsabilità:

- controllare ogni sezione generata;
- verificare coerenza con brief;
- verificare coerenza con mansioni;
- verificare che i rischi siano associati alle mansioni corrette;
- rilevare riferimenti normativi non supportati;
- rilevare placeholder residui;
- rilevare testo troppo generico;
- assegnare esito:
  - `approved`;
  - `needs_revision`;
  - `blocked_missing_data`.

Output:

```json
{
  "qa_status": "approved",
  "issues": [],
  "missing_data": [],
  "suggested_fix": ""
}
```

---

### 6.8 DocumentQAAgent

Controlla il DVR prima della generazione DOCX o subito dopo.

Responsabilità:

- verificare che tutte le sezioni siano presenti;
- verificare ordine capitoli;
- verificare coerenza dati azienda;
- verificare coerenza mansioni/rischi/DPI;
- verificare che non ci siano placeholder;
- verificare che le tabelle siano complete;
- generare report finale.

---

### 6.9 DocxRenderAgent

Sostituisce Workflow 5.

Responsabilità:

- caricare template DOCX;
- compilare placeholder;
- inserire sezioni generate;
- inserire tabelle;
- mantenere stile Word;
- generare file DOCX modificabile;
- salvare file su Storage;
- creare versione documento.

Tecnologie consigliate:

```text
docxtpl
python-docx
lxml
mammoth opzionale
pandoc opzionale
```

---

### 6.10 RevisionAgent

Nuovo agente fondamentale per modifiche successive.

Responsabilità:

- ricevere istruzioni di modifica;
- individuare sezione target;
- recuperare contenuto attuale;
- proporre patch;
- applicare patch;
- rigenerare DOCX;
- creare nuova versione;
- salvare changelog.

Esempio comando utente:

```text
Modifica la sezione rischio videoterminale aggiungendo che gli impiegati usano due monitor per circa 6 ore al giorno.
```

Flusso:

```text
RevisionAgent
  ↓
find_target_section()
  ↓
retrieve_current_content()
  ↓
generate_patch()
  ↓
run_section_qa()
  ↓
apply_patch()
  ↓
render_docx_v2()
```

---

### 6.11 MemoryCuratorAgent

Agente di cura della memoria persistente.

Responsabilità:

- convertire segnali accettati da utenti, revisori e QA in memorie con scope chiaro;
- distinguere memoria sessione, progetto, utente/organizzazione, QA ed eval;
- scrivere solo tramite `MemoryWriteTool`;
- non trasformare riflessioni dell'agente in fatti senza evidenza;
- non promuovere dati cliente o PII a memoria globale.

Regola:

```text
Le informazioni operative importanti devono stare prima nelle tabelle di dominio Supabase.
La memoria libera serve per continuità controllata, non per sostituire il modello dati.
```

---

### 6.12 LearningProposalAgent

Agente che crea proposte di miglioramento, non modifiche.

Responsabilità:

- analizzare `qa_findings`, `review_events`, feedback umano, retrieval miss ed eval failure;
- raggruppare pattern ricorrenti;
- creare `learning_proposals` con evidenze, rischio, beneficio atteso e piano eval;
- proporre miglioramenti a prompt, checklist, template, policy RAG o confini tool;
- non cambiare direttamente prompt, template, checklist, policy RAG o permessi tool.

Stato mentale corretto:

```text
Una learning proposal è una proposta strutturata. Non è una modifica in produzione.
```

---

### 6.13 EvalRunnerAgent

Agente che valuta le proposte prima della review umana.

Responsabilità:

- eseguire casi DVR rappresentativi e casi limite;
- misurare parse success, pass rate, forbidden behavior, coverage fonti, onestà sui dati mancanti, costi e latenza;
- confrontare la proposta con la versione attiva;
- segnalare regressioni;
- marcare una proposta come `eval_failed` se peggiora il comportamento.

---

### 6.14 ApprovalCoordinatorAgent

Agente che prepara il pacchetto di approvazione umana.

Ogni approval packet deve contenere:

- sintesi del problema;
- evidenze e sorgenti;
- diff o modifica proposta;
- risultati eval;
- rischi noti;
- piano rollback;
- scope del rilascio;
- decisione e timestamp del revisore.

---

### 6.15 VersionRegistryAgent

Agente che registra e attiva versioni approvate.

Artefatti da versionare:

- prompt;
- policy RAG;
- funzioni retrieval;
- template DOCX;
- checklist QA;
- schema tool;
- configurazione modello;
- policy memoria.

Regola:

```text
Nessuna nuova versione diventa attiva senza approval event valido e tracciato.
Ogni DVR generato deve salvare versioni prompt, RAG policy, template, checklist, modello e toolset usati.
```

---

### 6.16 DvrDoctorAgent

Agente diagnostico operativo read-only.

Responsabilità:

- verificare versione app e ambiente;
- verificare provider LLM attivo e stato health;
- verificare connettività Supabase;
- verificare funzioni RAG disponibili;
- segnalare warning RLS/grant;
- verificare template presenti;
- mostrare versioni attive di prompt, template, checklist e RAG policy;
- elencare learning proposal e approvazioni pendenti;
- segnalare job falliti;
- verificare health Render se configurato;
- verificare webhook Telegram.

Output tipo:

```json
{
  "status": "warning",
  "checks": [
    {
      "name": "rag_metadata_quality",
      "status": "warning",
      "message": "RAG metadata scarso; filtro per ATECO/risk_category limitato.",
      "action": "Eseguire piano arricchimento metadata RAG."
    }
  ],
  "safe_actions": [],
  "approval_required_actions": ["change_rag_policy", "rotate_provider_credentials"]
}
```

Regola:

```text
DvrDoctorAgent propone diagnosi e azioni, ma non espone segreti e non applica fix distruttivi senza approvazione.
```

---

### 6.17 LlmProviderRouter

Componente di routing provider LLM.

Provider supportati:

| Provider | Uso |
|---|---|
| `openrouter` | Provider API via OpenRouter, scelto per evitare dipendenza diretta da OpenAI API key |
| `openai_api` | Provider ufficiale server-side, preferito per produzione stabile |
| `openai_subscription_bridge` | Provider opzionale single-tenant basato su subscription/sessione cliente |
| `local_mock` | Test deterministici senza chiamate LLM |

Interfaccia concettuale:

```python
class LlmProvider:
    name: str
    mode: str

    async def generate(self, request):
        ...

    async def health(self):
        ...
```

Regole provider:

```text
Registrare provider, modalità, model label e prompt/RAG/template version in ogni run e DVR.
Eseguire health check prima di generazioni lunghe.
Fallback sempre esplicito, mai silenzioso.
Se il provider non è disponibile, marcare la run come `provider_unavailable` o `needs_reconnect`.
```

Bridge OpenAI subscription:

```text
Ammesso solo single-tenant.
Mai condividere una sessione subscription tra clienti.
Mai salvare token/cookie in prompt, log, memorie, wiki o learning proposal.
Non esporre controlli bridge a comandi client ordinari.
Preferire `openai_api` quando servono multi-tenant, SLA, audit/billing puliti o generazione unattended.
```

---

## 7. Database Supabase target

### 7.1 Tabelle operative principali

```text
companies
projects
dvr_inputs
dvr_indexes
dvr_sections
dvr_generation_jobs
generated_documents
document_versions
document_patches
qa_reports
agent_runs
human_feedback
channel_events
operator_sessions
authz_events
tool_policy_events
audit_events
llm_provider_runs
provider_health_checks
agent_memories
qa_findings
review_events
learning_proposals
eval_cases
eval_runs
eval_results
approval_events
artifact_versions
```

---

### 7.2 Tabella `companies`

```sql
create table companies (
  id uuid primary key default gen_random_uuid(),
  source_airtable_record_id text,
  ragione_sociale text not null,
  partita_iva text,
  codice_fiscale text,
  codice_ateco text,
  descrizione_attivita text,
  numero_dipendenti integer,
  sede_legale text,
  sede_operativa text,
  created_at timestamp default now(),
  updated_at timestamp default now()
);
```

---

### 7.3 Tabella `dvr_projects`

```sql
create table dvr_projects (
  id uuid primary key default gen_random_uuid(),
  source_airtable_record_id text,
  company_id uuid references companies(id),
  status text not null,
  legacy_airtable_status text,
  document_type text,
  risk_category text,
  ateco_code text,
  pericoli_settore text,
  rischi_per_mansione text,
  normativa_riferimento text,
  telegram_user_id text,
  current_document_id uuid,
  created_at timestamp default now(),
  updated_at timestamp default now()
);
```

Stati consigliati:

```text
draft_intake
waiting_user_confirmation
project_created
index_draft_created
index_validation_pending
index_ai_validated
index_human_validated
sections_created
in_generation
sections_completed
qa_pending
ready_for_docx
docx_generating
docx_created
revision_requested
error
```

---

### 7.4 Tabella `dvr_indexes`

```sql
create table dvr_indexes (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references dvr_projects(id),
  source_airtable_record_id text,
  draft_index text,
  validated_index text,
  validation_report jsonb,
  status text,
  created_at timestamp default now(),
  updated_at timestamp default now()
);
```

---

### 7.5 Tabella `dvr_sections`

```sql
create table dvr_sections (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references dvr_projects(id),
  source_airtable_record_id text,
  legacy_project_ref text,
  section_number text,
  title text,
  parent_section_number text,
  sort_order text,
  brief jsonb,
  status text,
  legacy_airtable_status text,
  risk_category text,
  mansioni_coinvolte text[],
  retrieved_chunk_ids uuid[],
  generated_content_md text,
  generated_content_json jsonb,
  qa_status text,
  qa_report jsonb,
  created_at timestamp default now(),
  updated_at timestamp default now()
);
```

Stati sezione:

```text
da_redigere
in_redazione
redatta
qa_pending
qa_approved
needs_revision
blocked_missing_data
completed
```

---

### 7.6 Tabella `generated_documents`

```sql
create table generated_documents (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references dvr_projects(id),
  version integer not null,
  docx_url text,
  legacy_google_drive_url text,
  storage_path text,
  source_template_id uuid,
  status text,
  qa_report_id uuid,
  changelog text,
  llm_provider_summary jsonb,
  created_at timestamp default now()
);
```

---

### 7.7 Tabella `document_patches`

```sql
create table document_patches (
  id uuid primary key default gen_random_uuid(),
  document_id uuid references generated_documents(id),
  section_id uuid references dvr_sections(id),
  user_instruction text,
  old_content text,
  new_content text,
  patch_summary text,
  status text,
  created_at timestamp default now()
);
```

---

### 7.8 Tabella `human_feedback`

```sql
create table human_feedback (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references dvr_projects(id),
  document_id uuid references generated_documents(id),
  section_id uuid references dvr_sections(id),
  feedback_text text,
  old_content text,
  corrected_content text,
  error_type text,
  severity text,
  created_at timestamp default now()
);
```

Questa tabella alimenta la DVR Quality Wiki e il ciclo di miglioramento qualità.

---

### 7.9 Tabelle memoria, learning proposal, eval e versioning

Queste tabelle supportano memoria persistente e auto-miglioramento controllato.

Regola principale:

```text
Gli agenti possono osservare, ricordare, proporre e valutare.
Non possono modificare comportamento production senza approvazione umana e nuova versione registrata.
```

#### `agent_memories`

```sql
create table agent_memories (
  id uuid primary key default gen_random_uuid(),
  scope text not null check (scope in ('session','user','org','project','global_dev')),
  scope_id text not null,
  memory_type text not null,
  content jsonb not null,
  source text not null,
  confidence numeric not null default 0.7,
  retention_policy text not null default 'project_lifetime',
  contains_pii boolean not null default false,
  created_by text not null,
  created_at timestamptz not null default now(),
  expires_at timestamptz,
  superseded_by uuid references agent_memories(id)
);
```

Tipi memoria:

```text
session_memory
project_memory
user_preference_memory
rag_evidence
qa_memory
learning_proposals
eval_memory
```

#### `learning_proposals`

```sql
create table learning_proposals (
  id uuid primary key default gen_random_uuid(),
  proposal_code text unique,
  proposal_type text not null,
  target_component text not null,
  target_artifact text,
  current_version text,
  problem text not null,
  evidence jsonb not null default '[]'::jsonb,
  proposed_change text not null,
  expected_benefit text,
  risk_assessment text,
  eval_plan jsonb not null default '[]'::jsonb,
  status text not null default 'draft',
  created_by text not null,
  created_at timestamptz not null default now(),
  approved_by text,
  approved_at timestamptz,
  deployed_at timestamptz
);
```

Stati proposta:

```text
draft
pending_eval
eval_failed
pending_human_review
rejected
approved
implemented
deployed
monitored
```

#### `eval_cases`, `eval_runs`, `eval_results`

```sql
create table eval_cases (
  id uuid primary key default gen_random_uuid(),
  case_code text unique not null,
  target_component text not null,
  input jsonb not null,
  required_checks jsonb not null default '[]'::jsonb,
  forbidden_behaviors jsonb not null default '[]'::jsonb,
  expected_output_schema jsonb,
  status text not null default 'active',
  created_at timestamptz not null default now()
);

create table eval_runs (
  id uuid primary key default gen_random_uuid(),
  proposal_id uuid references learning_proposals(id),
  artifact text,
  candidate_version text,
  baseline_version text,
  status text not null,
  summary jsonb,
  created_at timestamptz not null default now()
);

create table eval_results (
  id uuid primary key default gen_random_uuid(),
  eval_run_id uuid references eval_runs(id),
  eval_case_id uuid references eval_cases(id),
  passed boolean not null,
  metrics jsonb not null default '{}'::jsonb,
  failures jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);
```

Metriche minime:

```text
parse_success
required_check_pass_rate
forbidden_behavior_count
citation_coverage
missing_data_honesty
reviewer_acceptance_rate
latency
token_cost
regressions
```

#### `approval_events` e `artifact_versions`

```sql
create table approval_events (
  id uuid primary key default gen_random_uuid(),
  proposal_id uuid references learning_proposals(id),
  reviewer text not null,
  decision text not null check (decision in ('approved','rejected','needs_changes')),
  approval_packet jsonb not null,
  notes text,
  created_at timestamptz not null default now()
);

create table artifact_versions (
  id uuid primary key default gen_random_uuid(),
  artifact text not null,
  version text not null,
  status text not null check (status in ('draft','approved','active','retired')),
  created_from_proposal uuid references learning_proposals(id),
  approval_event_id uuid references approval_events(id),
  eval_summary jsonb,
  activated_at timestamptz,
  created_at timestamptz not null default now(),
  unique (artifact, version)
);
```

---

### 7.10 Tabelle ops gateway, audit e provider

Queste tabelle supportano canali, autorizzazioni, sessioni isolate, tool policy, diagnostica e tracciamento provider.

#### `channel_events`

```sql
create table channel_events (
  id uuid primary key default gen_random_uuid(),
  event_id text unique not null,
  channel text not null,
  channel_user_id text,
  channel_chat_id text,
  message_type text,
  normalized_event jsonb not null,
  raw_ref text,
  auth_status text,
  created_at timestamptz not null default now()
);
```

#### `operator_sessions`

```sql
create table operator_sessions (
  id uuid primary key default gen_random_uuid(),
  org_id uuid,
  user_id text not null,
  project_id uuid references dvr_projects(id),
  document_id uuid references generated_documents(id),
  channel text not null,
  session_key text not null,
  state jsonb not null default '{}'::jsonb,
  active_provider text,
  last_safe_command text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (session_key)
);
```

La `session_key` deve seguire:

```text
org_id:user_id:project_id:document_id:channel
```

#### `authz_events` e `tool_policy_events`

```sql
create table authz_events (
  id uuid primary key default gen_random_uuid(),
  channel_event_id uuid references channel_events(id),
  user_id text,
  role text,
  action text not null,
  scope jsonb,
  decision text not null,
  reason text,
  created_at timestamptz not null default now()
);

create table tool_policy_events (
  id uuid primary key default gen_random_uuid(),
  agent_name text not null,
  tool_name text not null,
  action text not null,
  project_id uuid references dvr_projects(id),
  decision text not null,
  reason text,
  created_at timestamptz not null default now()
);
```

#### `llm_provider_runs` e `provider_health_checks`

```sql
create table llm_provider_runs (
  id uuid primary key default gen_random_uuid(),
  agent_run_id uuid,
  project_id uuid references dvr_projects(id),
  document_id uuid references generated_documents(id),
  provider_name text not null,
  provider_mode text not null,
  provider_session_ref text,
  model_label text,
  prompt_versions jsonb,
  rag_policy_version text,
  template_version text,
  status text not null,
  created_at timestamptz not null default now()
);

create table provider_health_checks (
  id uuid primary key default gen_random_uuid(),
  provider_name text not null,
  provider_mode text not null,
  status text not null,
  message text,
  checked_at timestamptz not null default now()
);
```

Regola:

```text
`provider_session_ref` deve essere redatto o hashato. Non salvare mai token, cookie o credenziali raw.
```

#### `audit_events`

```sql
create table audit_events (
  id uuid primary key default gen_random_uuid(),
  event_type text not null,
  actor_role text,
  actor_id text,
  project_id uuid references dvr_projects(id),
  document_id uuid references generated_documents(id),
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
```

---

### 7.11 Mapping Airtable → Supabase

La migrazione deve essere compatibile con la base Airtable reale `Documenti CT Safe`.

#### `Progetti DVR` → Supabase

| Campo Airtable | Destinazione Supabase | Note |
|---|---|---|
| `id` Airtable | `dvr_projects.source_airtable_record_id` e/o `companies.source_airtable_record_id` | Serve per import incrementale e audit |
| `Ragione Sociale` | `companies.ragione_sociale` | Campo primario Airtable |
| `Partita IVA` | `companies.partita_iva` | Anagrafica |
| `Codice ATECO` | `companies.codice_ateco` + `dvr_projects.ateco_code` | Duplicabile sul progetto per snapshot storico |
| `Descrizione Attività` | `companies.descrizione_attivita` | Input essenziale per indice e capitoli |
| `N° Dipendenti` | `companies.numero_dipendenti` | Convertire a integer |
| `Mansioni` | `dvr_inputs` oppure snapshot in `dvr_projects`/`dvr_sections.brief` | In futuro normalizzabile in tabella mansioni |
| `Indirizzo Sede` | `companies.sede_operativa` | Se contiene più sedi, va strutturato in seguito |
| `Tipo Documento` | `dvr_projects.document_type` | DVR nuovo / aggiornamento |
| `Categoria Rischio` | `dvr_projects.risk_category` | Snapshot classificazione |
| `Pericoli Settore` | `dvr_projects.pericoli_settore` | Testo legacy, poi normalizzabile |
| `Rischi per Mansione` | `dvr_projects.rischi_per_mansione` | Testo legacy, poi normalizzabile |
| `Normativa Riferimento` | `dvr_projects.normativa_riferimento` | Snapshot iniziale |
| `INDICE DVR` | `dvr_indexes.draft_index` | Bozza indice |
| `INDICE DVR VALIDATO` | `dvr_indexes.validated_index` | Indice ufficiale validato |
| `Log Validazione` | `dvr_indexes.validation_report` o `qa_reports` | Se JSON valido, salvare come JSONB |
| `Stato DVR` | `dvr_projects.status` + `legacy_airtable_status` | Mappare a stati canonici mantenendo testo originale |
| `Link DVR Google Drive` | `generated_documents.legacy_google_drive_url` | Campo legacy; il nuovo output va su storage/Supabase |

#### `Capitoli DVR` → Supabase

| Campo Airtable | Destinazione Supabase | Note |
|---|---|---|
| `id` Airtable | `dvr_sections.source_airtable_record_id` | Necessario per sincronizzazione |
| `Progetto DVR` | `dvr_sections.legacy_project_ref` + `dvr_sections.project_id` | Oggi è testo; in Supabase diventa FK reale |
| `Numero Capitolo` | `dvr_sections.section_number` | Preservare anche valori tipo `A1`, `PARTE 1` |
| `Titolo Capitolo` | `dvr_sections.title` | Titolo sezione |
| `Brief` | `dvr_sections.brief` | Convertire a JSONB quando possibile; altrimenti conservare raw |
| `Stato` | `dvr_sections.status` | Mappare a stati canonici |
| `Ordine` | nuovo campo consigliato `sort_order text` o derivazione da `section_number` | Serve per ricostruire il documento |
| `Contenuto Generato` | `dvr_sections.generated_content_md` | Markdown/testo capitolo |

#### Mapping stati

`Stato DVR` Airtable → `dvr_projects.status`:

```text
In validazione                 -> index_validation_pending
Indice validato                -> index_ai_validated
In redazione                   -> in_generation
Redazione fatta - crea documento -> ready_for_docx
DVR in creazione               -> docx_generating
DVR Creato                     -> docx_created
Errore                         -> error
```

`Stato` capitolo Airtable → `dvr_sections.status`:

```text
Da redigere -> da_redigere
In corso    -> in_redazione
Completato  -> completed
```

#### Regola di migrazione

```text
Non perdere mai il valore Airtable originale: oltre allo stato canonico, salvare ID record, tabella sorgente, stato legacy e riferimento progetto testuale.
```

Questo permette di confrontare il nuovo sistema Agno/Supabase con l'output storico n8n/Airtable senza interrompere subito il sistema attuale.

---

## 8. RAG su Supabase

### 8.1 Obiettivo del RAG

Il RAG deve fornire contesto affidabile per:

- generazione indice;
- validazione indice;
- redazione capitoli;
- riferimenti normativi;
- esempi di sezioni DVR;
- stile redazionale;
- QA e autocontrollo.

---

### 8.2 Collezioni / tabelle consigliate

Stato live rilevato:

```text
normativa      corpus principale già popolato
indice         corpus piccolo di esempi indice/template
dvr_pregressi  corpus previsto ma vuoto
```

Separare le fonti in più tabelle o viste logiche:

```text
rag_normativa
rag_indici
rag_sezioni_esempio
rag_template_fragments
rag_errori_corretti
```

Oppure usare una tabella unica `rag_chunks` con metadata forti.

Decisione consigliata:

```text
Usare `rag_chunks` come tabella target unificata, mantenendo `normativa`, `indice` e `dvr_pregressi` come corpus legacy durante la transizione.
```

---

### 8.3 Tabella `rag_chunks`

```sql
create table rag_chunks (
  id uuid primary key default gen_random_uuid(),
  corpus text not null,
  legacy_table text,
  legacy_id bigint,
  source_id uuid,
  source_type text,
  content text not null,
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
  ambienti text[],
  document_type text,
  normative_refs text[],
  language text,
  version text,
  is_active boolean not null default true,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
```

Indici minimi:

```sql
create index rag_chunks_embedding_idx
on rag_chunks
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

create index rag_chunks_corpus_idx on rag_chunks (corpus);
create index rag_chunks_metadata_gin on rag_chunks using gin (metadata);
create index rag_chunks_ateco_gin on rag_chunks using gin (ateco_codes);
create index rag_chunks_mansioni_gin on rag_chunks using gin (mansioni);
create index rag_chunks_normative_refs_gin on rag_chunks using gin (normative_refs);
```

Campi di compatibilità:

```text
corpus        identifica normativa, indice, dvr_pregressi, template, errori_corretti
legacy_table  conserva la tabella sorgente legacy
legacy_id     conserva l'id bigint della tabella legacy
```

---

### 8.4 Metadata fondamentali

Ogni chunk deve avere più metadata possibile:

```text
source_type
corpus
legacy_table
legacy_id
risk_category
section_type
ateco_codes
mansioni
ambienti
attrezzature
document_type
normative_refs
source_document
source_page
line_from
line_to
valid_from
valid_to
cliente_settore
```

Esempio:

```json
{
  "source_type": "normativa",
  "corpus": "normativa",
  "risk_category": "caduta_alto",
  "section_type": "misure_prevenzione",
  "ateco_codes": ["43.91", "46.69.94"],
  "mansioni": ["installatore", "tecnico", "manutentore"],
  "ambienti": ["copertura", "cantiere", "cliente"],
  "normative_refs": ["D.Lgs. 81/08 Titolo IV", "D.Lgs. 81/08 Titolo III"],
  "source_document": "D.Lgs. 81-08",
  "line_from": 120,
  "line_to": 138
}
```

---

### 8.5 Retrieval consigliato

Non usare solo:

```text
query libera + topK
```

Usare invece:

```text
1. metadata filtering
2. vector search
3. keyword search
4. hybrid ranking
5. reranking LLM opzionale
6. salvataggio chunk usati
```

Flusso:

```text
brief capitolo
  ↓
RetrievalPlannerAgent
  ↓
filters + query
  ↓
Supabase pgvector / hybrid search
  ↓
reranking
  ↓
contesto finale
  ↓
ChapterWriterAgent
```

Compatibilità con Supabase live:

```text
1. mantenere temporaneamente `match_normativa`, `match_documents` e `match_dvr_pregressi`;
2. correggere o sostituire `match_indice`, oggi legata alla tabella inesistente `documents`;
3. introdurre `match_rag_chunks` come funzione nuova, con filtro su `corpus`, `metadata`, ATECO, mansioni e riferimenti normativi;
4. creare wrapper espliciti `match_normativa_v2`, `match_indice_v2`, `match_dvr_pregressi_v2`;
5. salvare sempre in `dvr_sections.retrieved_chunk_ids` gli ID dei chunk realmente usati.
```

La funzione target deve applicare prima i filtri strutturati e poi il ranking vettoriale, evitando di replicare il comportamento attuale di `match_documents`, che cerca in `indice` ma non applica filtri metadata.

---

### 8.6 Parametri RAG da testare

```text
chunk size: 500 / 800 / 1200 token
overlap: 80 / 150 / 250 token
top_k: 5 / 10 / 20
hybrid search: sì/no
metadata filtering: sì/no
reranking: sì/no
temperature generazione: 0.1 / 0.2 / 0.3
```

Per i DVR, temperatura consigliata:

```text
0.1 - 0.2
```

---

### 8.7 Bonifica del corpus live

Azioni minime prima di usare il RAG live come base del nuovo agente:

```text
1. correggere `match_indice` o sostituirla con `match_indice_v2`;
2. aggiungere indice vettoriale su `indice.embedding`;
3. mantenere `match_documents` solo come alias legacy documentato;
4. deduplicare `normativa`, preservando provenienza e line span;
5. scartare o marcare come low_quality i chunk sotto 100 caratteri;
6. arricchire i nuovi ingest con metadata semantici;
7. popolare `dvr_pregressi` solo con DVR validati e anonimizzati, non con output grezzi;
8. attivare RLS e restringere i grant prima dell'uso in produzione.
```

La deduplicazione non deve cancellare alla cieca le righe legacy: prima va creata una vista o tabella di staging che conservi `legacy_id`, `source_document`, `loc`, `line_from` e `line_to`, così gli agenti possono ancora citare la provenienza.

---

## 9. Generazione DOCX

### 9.1 Requisito principale

Il documento finale deve essere:

```text
.docx modificabile manualmente in Word
```

Non basta generare un PDF o un testo Markdown.

---

### 9.2 Template DOCX

I template vanno presi da:

```text
C:\Users\Amedeo Testa\Desktop\Agente 247X AGNO v2\esempi dvr per template
```

Il template deve contenere:

- copertina;
- intestazioni;
- piè di pagina;
- stili Word;
- placeholder;
- sezioni standard;
- tabelle;
- spazi firma;
- eventuale indice;
- sezioni ripetibili.

---

### 9.3 Strategie di templating

#### Opzione A — Placeholder semplici

Esempio:

```text
{{ company.ragione_sociale }}
{{ company.sede_operativa }}
{{ dvr.data }}
{{ sections.identificazione_attivita }}
{{ sections.rischio_videoterminale }}
```

Libreria consigliata:

```text
docxtpl
```

---

#### Opzione B — Content Controls Word

Più robusta in produzione.

Esempio:

```text
SDT: company_name
SDT: legal_address
SDT: risk_section_caduta_alto
SDT: mansioni_table
```

Vantaggi:

- modifica sezionale più precisa;
- meno rischio di rompere il layout;
- compatibile con patch successive;
- migliore per documenti lunghi.

---

### 9.4 Output generazione

Ogni documento generato deve produrre:

```text
DVR_v1.docx
metadata.json
qa_report.json
changelog.txt
```

Percorso storage consigliato:

```text
/dvr-projects/{project_id}/documents/DVR_v1.docx
/dvr-projects/{project_id}/documents/DVR_v2.docx
/dvr-projects/{project_id}/qa/qa_report_v1.json
```

---

## 10. Modifica documento via agente

### 10.1 Obiettivo

L’utente deve poter modificare il DVR tramite Telegram senza dover rigenerare tutto.

Esempi:

```text
Modifica il capitolo sulle mansioni e aggiungi che il magazziniere usa il carrello elevatore.
```

```text
Rigenera solo la sezione rischio chimico.
```

```text
Aggiungi una nota nel programma di miglioramento sulla formazione antincendio.
```

---

### 10.2 Flusso modifica

```text
Utente Telegram
  ↓
RevisionAgent
  ↓
Intent detection
  ↓
Individuazione sezione
  ↓
Recupero contenuto attuale
  ↓
Generazione patch
  ↓
QA patch
  ↓
Salvataggio nuova sezione
  ↓
Rigenerazione DOCX v2
  ↓
Invio link all’utente
```

---

### 10.3 Patch documentale

Ogni modifica va salvata in `document_patches`.

Esempio:

```json
{
  "section": "2.4 Individuazione mansioni",
  "instruction": "Aggiungi uso del carrello elevatore per il magazziniere",
  "old_content": "...",
  "new_content": "...",
  "patch_summary": "Aggiornata mansione M4 con utilizzo carrello elevatore e rischio investimento/schiacciamento.",
  "status": "applied"
}
```

---

## 11. DVR Quality Wiki e memoria Obsidian

### 11.1 Scopo corretto

La scelta corretta per il runtime Agno non è una LLM Wiki ampia usata come memoria libera.

Il runtime deve poggiare prima su:

- Supabase Postgres per stato operativo, progetti, capitoli, revisioni e audit;
- Supabase RAG per normativa, indici e conoscenza documentale filtrabile;
- memoria Agno solo per contesto conversazionale controllato;
- tool Python tipizzati con input/output Pydantic e permessi minimi.

La wiki utile al runtime deve essere piccola, curata e orientata alla qualità. In questa guida viene chiamata **DVR Quality Wiki**.

La DVR Quality Wiki non deve:

- generare il DVR al posto del RAG;
- sostituire Supabase;
- contenere dati sensibili dei clienti;
- essere la vault Obsidian completa;
- diventare una memoria non governata dell'agente.

Deve invece servire per:

- apprendimento dagli errori;
- raccolta pattern corretti;
- checklist di qualità;
- stile redazionale CT Safe;
- memoria storica delle correzioni generalizzabili;
- regole operative per `SectionQAAgent` e `DocumentQAAgent`;
- esempi sanificati di output buoni/cattivi.

Distinzione importante:

```text
Obsidian/LLM Wiki è memoria di sviluppo per Codex e per il team.
DVR Quality Wiki è un sottoinsieme curato, esportato e non sensibile che Agno può eventualmente leggere.
Il runtime Agno non deve usare la vault completa come memoria libera.
Agno può leggere solo pagine/export approvati tramite tool read-only esplicito.
```

---

### 11.2 Skill Obsidian/LLM Wiki per sviluppo

Skill consentite per sviluppo e manutenzione della memoria di progetto:

```text
llm-wiki
wiki-setup
wiki-ingest / obsidian-wiki-ingest
wiki-capture / wiki-quick-chat-capture
wiki-lint
cross-linker
tag-taxonomy
wiki-dedup
wiki-synthesize
wiki-export
obsidian-markdown
obsidian-bases
json-canvas
```

Skill rimosse o da evitare:

```text
daily-update
data-ingest
ingest-url
wiki-agent
wiki-query
wiki-research
defuddle
obsidian-cli
```

Motivo:

```text
Le skill rimosse sono state segnalate High/Critical Risk o Med Risk.
Per questo la wiki resta memoria di sviluppo controllata, non automazione runtime autonoma.
```

---

### 11.3 Cosa inviare alla DVR Quality Wiki

Non mandare semplicemente tutti i DVR generati.

Creare invece `learning_packet` strutturati, sanificati e generalizzabili.

Esempio:

```json
{
  "project_id": "...",
  "section": "Rischio caduta dall'alto",
  "bad_output": "...",
  "corrected_output": "...",
  "error_type": "rischio_mansione_errato",
  "rule_learned": "Associare caduta dall'alto solo a mansioni che accedono a coperture, cantieri o lavori in quota.",
  "severity": "high",
  "runtime_allowed": true,
  "contains_client_sensitive_data": false
}
```

Regola:

```text
Solo `learning_packet` senza dati sensibili e approvati possono diventare pagine consultabili dal runtime.
Il resto resta in memoria di sviluppo o nei log/audit Supabase con accesso controllato.
```

---

### 11.4 Pagine consigliate

```text
/wiki/dvr-quality/errori-ricorrenti.md
/wiki/dvr-quality/checklist-redazione.md
/wiki/dvr-quality/stile-redazionale-ctsafe.md
/wiki/dvr-quality/rischi-per-mansione.md
/wiki/dvr-quality/rischio-caduta-alto.md
/wiki/dvr-quality/rischio-videoterminale.md
/wiki/dvr-quality/rischio-chimico.md
/wiki/dvr-quality/template-sezioni.md
/wiki/dvr-quality/qa-pre-consegna.md
/wiki/dvr-quality/settori/commercio-dpi.md
/wiki/dvr-quality/settori/installazione-linee-vita.md
```

---

### 11.5 Uso nel flusso Agno

```text
human_feedback
  ↓
learning_packet sanificato
  ↓
DVR Quality Wiki ingest/export
  ↓
pagina curata approvata
  ↓
QualityChecklistTool read-only
  ↓
SectionQAAgent / DocumentQAAgent
  ↓
meno errori futuri
```

Uso consigliato:

```text
SectionWriterAgent non deve copiare dalla wiki.
SectionQAAgent e DocumentQAAgent possono usarla per checklist, controlli e pattern di errore.
Le fonti normative restano nel RAG Supabase, non nella wiki.
```

---

### 11.6 Memoria persistente e auto-miglioramento controllato

La skill locale `ctsafe-agno-memory-evolution` definisce il modello corretto per memoria persistente e miglioramento evolutivo dell'agente Agno.

Tipi di memoria da tenere separati:

| Tipo memoria | Uso | Accesso runtime |
|---|---|---|
| `session_memory` | Stato chat/workflow corrente, intenzioni utente, domande pendenti | Read/write da orchestratore e agenti attivi |
| `project_memory` | Fatti stabili del progetto DVR: azienda, sedi, mansioni, attrezzature, dati mancanti | Repository tipizzati Supabase |
| `user_preference_memory` | Preferenze di lingua, formato, canale, stile review | Lettura con scope stretto |
| `rag_evidence` | Chunk normativi/documentali recuperati | Retrieval read-only, scrittura solo pipeline ingest |
| `qa_memory` | Difetti ricorrenti, feedback revisori, correzioni accettate | Scrittura QA/revision, lettura proposal |
| `learning_proposals` | Proposte di miglioramento a prompt, RAG, template, checklist, tool | Create dagli agenti, applicate solo dopo approvazione |
| `eval_memory` | Casi eval, risultati, regressioni | Usata da `EvalRunnerAgent`, non dai writer agent |

Loop ammesso:

```text
Run DVR workflow
  ↓
raccolta QA finding, review event, feedback utente, retrieval miss
  ↓
LearningProposalAgent crea proposta
  ↓
EvalRunnerAgent testa su eval dataset DVR
  ↓
ApprovalCoordinatorAgent prepara pacchetto umano
  ↓
approvazione o rigetto umano
  ↓
VersionRegistryAgent registra nuova versione
  ↓
deploy controllato e monitoraggio
```

Azioni automatiche consentite:

```text
salvare stato sessione
salvare note project-scoped su dati mancanti
salvare QA finding
creare learning proposal
eseguire eval
preparare review packet
marcare una proposta come eval_failed
```

Azioni che richiedono sempre approvazione umana:

```text
attivare nuova versione prompt
cambiare filtri, chunking, reranking o priorità fonti RAG
cambiare struttura template DOCX
cambiare soglie o regole checklist QA
cambiare permessi tool
cambiare retention o policy PII della memoria
rilasciare modifiche di comportamento in produzione
```

Red line:

```text
Nessun agente può auto-modificare prompt, skill, template, policy RAG, permessi tool o comportamento production.
Ogni cambiamento deve passare da proposta, eval, approvazione umana, nuova versione e monitoraggio.
```

---

## 12. Storage file

### 12.1 Storage consigliato

Per test:

```text
Supabase Storage
```

Per produzione:

```text
S3 compatibile
```

---

### 12.2 Struttura cartelle storage

```text
/dvr-projects/{project_id}/input/
  telegram_raw.json
  company_data.json
  uploaded_files/

/dvr-projects/{project_id}/rag/
  retrieved_chunks.json
  citations.json

/dvr-projects/{project_id}/sections/
  001_obiettivi.md
  002_dati_generali.md
  003_mansioni.md

/dvr-projects/{project_id}/documents/
  DVR_v1.docx
  DVR_v2.docx
  DVR_v3.docx

/dvr-projects/{project_id}/qa/
  qa_report_v1.json
  unresolved_issues.json

/dvr-projects/{project_id}/wiki/
  learning_packet.json
```

---

## 13. Repository target

Struttura consigliata:

```text
dvr-agent/
  app/
    main.py
    settings.py

    api/
      telegram_webhook.py
      whatsapp_webhook.py
      channel_webhook.py
      health.py
      documents.py
      projects.py

    gateway/
      channel_gateway.py
      auth_gate.py
      command_router.py
      session_manager.py
      agent_router.py
      control_ux.py

    agents/
      orchestrator.py
      intake_agent.py
      index_draft_agent.py
      index_validation_agent.py
      section_planner_agent.py
      chapter_writer_agent.py
      section_qa_agent.py
      document_qa_agent.py
      docx_render_agent.py
      revision_agent.py
      memory_curator_agent.py
      learning_proposal_agent.py
      eval_runner_agent.py
      approval_coordinator_agent.py
      version_registry_agent.py
      dvr_doctor_agent.py

    tools/
      supabase_tools.py
      rag_tools.py
      docx_tools.py
      storage_tools.py
      telegram_tools.py
      wiki_tools.py
      project_tools.py
      memory_tools.py
      learning_tools.py
      eval_tools.py
      approval_tools.py
      version_tools.py
      diagnostics_tools.py

    providers/
      llm_provider.py
      openai_api_provider.py
      openai_subscription_bridge_provider.py
      local_mock_provider.py
      provider_router.py

    rag/
      chunking.py
      embeddings.py
      retrieval.py
      hybrid_search.py
      reranking.py
      metadata.py

    docgen/
      template_loader.py
      docx_renderer.py
      section_patcher.py
      table_renderer.py
      toc.py
      validators.py

    workflows/
      create_dvr.py
      validate_index.py
      generate_sections.py
      generate_document.py
      revise_document.py

    prompts/
      intake.md
      index_generation.md
      index_validation.md
      section_brief.md
      chapter_generation.md
      section_qa.md
      document_qa.md
      revision.md

    schemas/
      company.py
      project.py
      section.py
      document.py
      qa.py
      rag.py
      memory.py
      learning.py
      eval.py
      versioning.py
      channel.py
      ops.py
      provider.py

    db/
      migrations/
        001_init.sql
        002_rag.sql
        003_documents.sql
        004_memory_evolution.sql
        005_ops_gateway.sql

    tests/
      test_intake.py
      test_index_generation.py
      test_rag_retrieval.py
      test_docx_generation.py
      test_section_patch.py
      test_full_dvr_flow.py
      test_learning_proposal.py
      test_eval_runner.py
      test_version_registry.py
      test_auth_gate.py
      test_command_router.py
      test_tool_policy.py
      test_provider_router.py
      test_dvr_doctor.py

  templates/
    dvr_template.docx
    section_schema.json

  docs/
    architecture.md
    rag_strategy.md
    docx_generation.md
    migration_from_n8n.md
    memory_evolution.md
    ops_gateway.md
    provider_strategy.md

  wiki/
    README.md

  render.yaml
  requirements.txt
  Dockerfile
  README.md
```

---

## 14. Variabili ambiente

File `.env`:

```env
APP_ENV=development
APP_BASE_URL=https://your-render-app.onrender.com

TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=

SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_ANON_KEY=
SUPABASE_STORAGE_BUCKET=dvr-documents

# Opzionale: solo se si usa provider OpenAI API o embedding query via API.
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_APP_TITLE="CT Safe DVR Agent"

LLM_PROVIDER=openrouter
OPENROUTER_MODEL=anthropic/claude-sonnet-latest
DVR_EMBEDDING_PROVIDER=openrouter
DVR_EMBEDDING_MODEL=openai/text-embedding-3-small
LLM_PROVIDER_FALLBACK=none
OPENAI_SUBSCRIPTION_BRIDGE_ENABLED=true
OPENAI_SUBSCRIPTION_BRIDGE_HEALTHCHECK_REQUIRED=true
OPENAI_SUBSCRIPTION_BRIDGE_URL=
OPENAI_SUBSCRIPTION_BRIDGE_SESSION_REF=

AGNO_STORAGE_DB_URL=

LLM_WIKI_PATH=./wiki
DVR_QUALITY_WIKI_PATH=./wiki/dvr-quality
MEMORY_EVOLUTION_ENABLED=false
REQUIRE_HUMAN_APPROVAL_FOR_VERSION_ACTIVATION=true

MAX_SECTION_RETRIES=2
MAX_RAG_TOP_K=10
DEFAULT_GENERATION_TEMPERATURE=0.2
```

---

## 15. Deploy su Render e frontend opzionale Vercel

### 15.1 Target backend

Render è il target preferito per il backend Agno/AgentOS/FastAPI perché il core DVR richiede:

- servizio HTTP persistente;
- webhook Telegram;
- health check;
- variabili d'ambiente;
- log consultabili;
- esecuzione Python/FastAPI;
- accesso controllato a Supabase e storage.

Su Render mettere:

```text
FastAPI app
Agno AgentOS
Telegram webhook
job dispatcher leggero
health check
```

---

### 15.2 Vercel

Vercel è un'opzione solo per:

```text
frontend
dashboard
landing page
preview web
interfacce amministrative leggere
```

Non usare Vercel come prima scelta per il runtime core Agno/DVR se servono processi lunghi, generazione DOCX, webhook affidabili e operazioni RAG articolate.

Il frontend Vercel deve chiamare API backend Render, non invocare MCP o accedere direttamente ai segreti del backend.

---

### 15.3 Cosa non mettere su filesystem Render

Non mettere su filesystem locale Render:

```text
DOCX finali
file raw
wiki persistente
SQLite locale importante
database di produzione
```

Motivo: il filesystem può essere effimero e il servizio free può andare in sleep.

---

### 15.4 Render MCP e Vercel MCP

Render MCP e Vercel MCP sono strumenti amministrativi per Codex/sviluppatore.

Regole:

```text
Non usarli nel runtime Agno.
Non dare agli agenti DVR accesso a MCP infrastrutturali.
Non inserire segreti Render/Vercel nei prompt.
Ogni azione che crea, modifica o elimina servizi, database, variabili d'ambiente o deploy richiede conferma umana.
```

Render MCP non è ancora configurato perché richiede una API key Render ampia. Configurarlo solo quando siamo pronti al deploy e serve davvero amministrare l'infrastruttura.

---

### 15.5 Render config esempio

```yaml
services:
  - type: web
    name: dvr-agent-agno
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: APP_ENV
        value: test
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_ROLE_KEY
        sync: false
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: OPENAI_API_KEY
        sync: false
```

---

## 16. Flusso end-to-end target

### 16.1 Nuovo DVR

```text
Utente Telegram / dashboard Next.js
  ↓
/nuovo_dvr
  ↓
IntakeAgent raccoglie dati e chiede solo informazioni mancanti
  ↓
Utente conferma dati iniziali
  ↓
create_project()
  ↓
Sync Airtable legacy in Fase 1
  ↓
IndexDraftAgent genera indice preliminare usando RAG
  ↓
IndexValidationAgent valida indice
  ↓
Indice inviato all'utente/revisore per conferma
  ↓
Utente/revisore conferma o chiede modifiche all'indice
  ↓
SectionPlannerAgent crea sezioni
  ↓
ChapterWriterAgent redige capitoli
  ↓
SectionQAAgent valida capitoli
  ↓
DocumentQAAgent valida DVR completo
  ↓
DocxRenderAgent genera DOCX draft
  ↓
Draft DVR inviato all'utente/revisore
  ↓
Utente/revisore approva o chiede modifiche
  ↓
Consegna DOCX finale versionato
```

---

### 16.2 Modifica DVR

```text
Utente Telegram / dashboard Next.js
  ↓
/modifica_documento
  ↓
Utente descrive modifica o allega DVR esistente
  ↓
Se allega un file, il sistema lo conserva come sorgente, ne estrae contenuto/struttura e lo rimappa sul template CT Safe
  ↓
RevisionAgent interpreta richiesta
  ↓
Trova sezione target
  ↓
Genera patch
  ↓
SectionQAAgent controlla patch
  ↓
Aggiorna sezione
  ↓
DocxRenderAgent genera nuova versione
  ↓
Telegram/dashboard invia link DVR_v2.docx
```

---

### 16.3 User experience target

L'esperienza utente deve restare agentica e conversazionale anche se il backend e' governato da workflow.

Flusso UX previsto:

```text
1. L'utente scrive all'agente AI da Telegram o, in Fase 2, dalla dashboard Next.js.
2. L'agente raccoglie i dati utili al DVR: azienda, sede, ATECO, attivita', lavoratori, mansioni, attrezzature, sostanze, ambienti, rischi noti, tipo documento e note.
3. Se mancano informazioni, l'agente fa domande mirate e non procede inventando dati.
4. Se il lavoro riguarda un DVR esistente, l'utente puo' allegare il file: il sistema lo usa come sorgente da analizzare, non come template finale libero; il DOCX finale viene ricreato sul template CT Safe.
5. Quando i dati sono sufficienti, l'agente interroga il RAG e genera un indice DVR preliminare.
6. L'indice viene inviato all'utente/revisore per revisione.
7. Se l'indice viene approvato, il sistema genera sezioni, QA e DOCX draft.
8. Il DVR draft viene presentato all'utente/revisore.
9. Se approvato, il DOCX finale viene consegnato e versionato.
10. Se non approvato, l'utente puo' chiedere modifiche puntuali; l'agente genera patch, riesegue QA e produce una nuova versione.
```

Regola chiave:

```text
L'interfaccia deve sembrare un agente con cui si conversa, ma le azioni critiche devono passare da workflow tracciati, stati persistenti, permessi e approval gate.
```

---

### 16.4 Fasi UX e superfici operative

Fase 1:

```text
Canale principale: Telegram.
Backend: Agno/FastAPI/AgentOS.
Compatibilita': sincronizzazione Airtable per preservare il flusso operativo esistente.
Fonte operativa target: Supabase, con Airtable come legacy mirror/adapter durante transizione.
```

Fase 2:

```text
Canale aggiuntivo: applicazione Next.js.
La dashboard deve mostrare riepilogo DVR realizzati, stati, versioni, QA, fonti e documenti scaricabili.
La dashboard deve gestire i file caricati nel RAG/Supabase vettoriale: upload, metadata, stato ingest, attivazione/disattivazione, audit e qualita'.
La dashboard deve permettere di interrogare l'agente, avviare nuovi DVR, allegare DVR esistenti, chiedere modifiche, rigenerare sezioni o generare nuove versioni.
La dashboard deve chiamare API backend Render/FastAPI; non deve accedere direttamente a segreti, MCP amministrativi o service role Supabase.
```

---

## 17. Mapping n8n → Agno

| Workflow n8n | Modulo Agno target | Note |
|---|---|---|
| Workflow 1 - Intake & Classificazione | IntakeAgent | Mantenere logica di raccolta e conferma |
| Workflow 2 - RAG Retrieval & Generazione a Sezioni | IndexDraftAgent | Migliorare RAG con metadata |
| Workflow 3 - Revisione + Creazione indice | IndexValidationAgent + SectionPlannerAgent | Conservare JSON brief capitoli |
| Workflow 4 - Redattore | ChapterWriterAgent + SectionQAAgent | Aggiungere QA strutturato |
| Workflow 5 - Creazione .docx DVR | DocxRenderAgent | Sostituire Google Apps Script con Python DOCX |

---

## 18. Criticità attuali da risolvere

### 18.1 Airtable come database operativo

Problema:

```text
Airtable viene usato come database principale per progetti, capitoli, stati e contenuti lunghi.
```

Soluzione:

```text
Migrare stato operativo su Supabase Postgres.
```

---

### 18.2 Relazione progetto-capitoli fragile in Airtable

Problema:

```text
In `Capitoli DVR`, il campo `Progetto DVR` è testo (`singleLineText`) e non una relazione nativa. Le automazioni collegano i capitoli al progetto cercando l'ID Airtable dentro una stringa.
```

Soluzione:

```text
In Supabase introdurre una FK reale `dvr_sections.project_id`, conservando `legacy_project_ref` e `source_airtable_record_id` per compatibilità e audit.
```

---

### 18.3 RAG troppo generico

Problema:

```text
Retrieval topK senza metadata forti.
```

Soluzione:

```text
Metadata filtering + hybrid search + reranking + audit chunk usati.
```

---

### 18.4 Debito tecnico SQL nel RAG live

Problema:

```text
Il Supabase RAG live contiene funzioni legacy/incoerenti: `match_indice` punta a `documents`, `match_documents` cerca in `indice` ma senza filtro metadata, `indice` non ha indice vettoriale e `dvr_pregressi` è vuota.
```

Soluzione:

```text
Bonifica compatibile: correggere funzioni legacy, creare `match_rag_chunks`, aggiungere indice vettoriale a `indice`, mantenere wrapper temporanei e migrare verso `rag_chunks`.
```

---

### 18.5 Sicurezza Supabase RAG

Problema:

```text
RLS risulta disattivata sulle tabelle RAG e i grant osservati sono molto ampi anche per `anon` e `authenticated`.
```

Soluzione:

```text
Attivare RLS, restringere i grant, usare service role solo lato backend Agno/FastAPI e impedire scritture dirette dai client pubblici.
```

---

### 18.6 DOCX generato esternamente

Problema:

```text
Google Apps Script è esterno, fragile e poco versionabile.
```

Soluzione:

```text
DocxRenderAgent Python con docxtpl/python-docx.
```

---

### 18.7 QA insufficiente

Problema:

```text
Le sezioni vengono salvate dopo generazione senza controllo strutturato forte.
```

Soluzione:

```text
SectionQAAgent + DocumentQAAgent.
```

---

### 18.8 Modifiche successive non pienamente agentiche

Problema:

```text
Oggi le micro-modifiche sono manuali e le modifiche grandi non hanno pipeline strutturata.
```

Soluzione:

```text
RevisionAgent + document_patches + versioning DOCX.
```

---

## 19. Roadmap operativa

### Fase 0 — Bonifica minima Supabase RAG live

Obiettivo:

```text
Mettere in sicurezza e rendere coerente il RAG esistente senza rompere i workflow n8n attuali.
```

Deliverable:

```text
fix `match_indice` o nuovo `match_indice_v2`
alias/documentazione per `match_documents`
indice ivfflat su `indice.embedding`
audit duplicati `normativa`
staging per deduplica corpus
policy RLS e grant minimi
```

Questa fase va fatta prima o in parallelo alla replica Agno, perché il nuovo agente eredita la qualità e la sicurezza del corpus RAG.

---

### Fase 1 — Replica funzionale in Agno

Obiettivo:

```text
Ricreare il comportamento dei 5 workflow n8n dentro Agno.
```

Deliverable:

```text
Telegram webhook
ChannelGateway
AuthGate
CommandRouter
SessionManager
AgentRouter
IntakeAgent
IndexDraftAgent
IndexValidationAgent
ChapterWriterAgent base
DocxRenderAgent base
Supabase schema iniziale
adapter import/export compatibile con Progetti DVR e Capitoli DVR
```

---

### Fase 1B — Ops Gateway e controllo operatore

Obiettivo:

```text
Mettere un layer operativo sicuro attorno agli agenti Agno prima di esporre comandi reali a utenti e revisori.
```

Deliverable:

```text
schema eventi canale
matrice ruoli/permessi
lista comandi Telegram
session_key org:user:project:document:channel
tool policy per agente
DvrDoctorAgent read-only
LlmProviderRouter
audit_events
health check provider
tracciamento provider in agent_runs/DVR
```

---

### Fase 2 — Migrazione Airtable → Supabase

Obiettivo:

```text
Eliminare Airtable come database operativo.
```

Migrare:

```text
Progetti DVR → dvr_projects
Capitoli DVR → dvr_sections
INDICE DVR → dvr_indexes
Link DVR → generated_documents
Log Validazione → qa_reports
```

Requisiti di migrazione:

```text
preservare source_airtable_record_id
preservare legacy_airtable_status
preservare legacy_project_ref dei capitoli
convertire Brief in JSONB quando valido
salvare Contenuto Generato come Markdown sorgente
normalizzare stati progetto e capitolo
creare FK reale tra dvr_sections e dvr_projects
```

---

### Fase 3 — RAG migliorato

Obiettivo:

```text
Rendere la retrieval affidabile, filtrabile e testabile.
```

Deliverable:

```text
rag_chunks
metadata schema
hybrid_search
retrieval evaluation set
match_rag_chunks
wrapper match_normativa_v2 / match_indice_v2 / match_dvr_pregressi_v2
pipeline arricchimento metadata
deduplica controllata normativa
```

---

### Fase 4 — DOCX nativo

Obiettivo:

```text
Generare DVR Word modificabili senza Google Apps Script.
```

Deliverable:

```text
dvr_template.docx
DocxRenderAgent
versioning documenti
Storage upload
```

---

### Fase 5 — Revisione documento

Obiettivo:

```text
Permettere modifiche via Telegram.
```

Deliverable:

```text
RevisionAgent
document_patches
rigenerazione DOCX v2/v3
changelog
```

---

### Fase 6 — DVR Quality Wiki

Obiettivo:

```text
Creare memoria qualitativa curata dagli errori, senza esporre la vault Obsidian completa al runtime.
```

Deliverable:

```text
learning_packet
wiki ingest/export sanificato
wiki checklist
QualityChecklistTool read-only
QA agent integrato con checklist curata
```

---

### Fase 7 — Memoria persistente e auto-miglioramento controllato

Obiettivo:

```text
Aggiungere continuità e apprendimento governato senza permettere auto-modifiche production non approvate.
```

Deliverable:

```text
agent_memories
learning_proposals
eval_cases / eval_runs / eval_results
approval_events
artifact_versions
MemoryCuratorAgent
LearningProposalAgent
EvalRunnerAgent
ApprovalCoordinatorAgent
VersionRegistryAgent
workflow proposta → eval → approvazione → versione → monitoraggio
```

---

## 20. Prompt da creare

Cartella:

```text
app/prompts/
```

Prompt consigliati:

```text
intake.md
index_generation.md
index_validation.md
section_brief.md
chapter_generation.md
section_qa.md
document_qa.md
revision.md
```

---

### 20.1 Prompt Intake

Deve fare:

```text
- estrazione dati;
- identificazione campi mancanti;
- classificazione rischio;
- riepilogo;
- richiesta conferma.
```

---

### 20.2 Prompt generazione indice

Deve fare:

```text
- usare dati azienda;
- usare esempi indice;
- generare indice adatto al settore;
- non generare contenuto capitoli.
```

---

### 20.3 Prompt validazione indice

Deve fare:

```text
- verificare capitoli obbligatori;
- aggiungere capitoli mancanti;
- generare micro-brief;
- restituire JSON valido.
```

---

### 20.4 Prompt redazione capitolo

Deve fare:

```text
- usare brief;
- usare dati azienda;
- usare RAG;
- rispettare stile template;
- restituire Markdown strutturato;
- indicare eventuali dati mancanti.
```

---

### 20.5 Prompt QA sezione

Deve fare:

```text
- controllare completezza;
- controllare coerenza mansioni/rischi;
- controllare riferimenti normativi;
- rilevare placeholder;
- produrre esito JSON.
```

---

### 20.6 Prompt revisione

Deve fare:

```text
- capire richiesta modifica;
- trovare sezione target;
- generare patch;
- spiegare modifica;
- evitare modifiche non richieste.
```

---

### 20.7 Regole prompt production-grade

Usare la skill `prompt-engineering-patterns` come riferimento di progettazione per tutti i prompt Agno di produzione.

Regole:

```text
Trattare i prompt come codice versionato.
Associare ogni prompt a schema Pydantic/JSON di output quando l'output viene parsato.
Definire fallback espliciti se il RAG non contiene evidenza sufficiente.
Separare istruzioni di ruolo, contesto progetto, vincoli DVR, formato output ed esempi.
Testare i prompt su casi rappresentativi e casi limite.
Tracciare accuracy, consistenza, validità JSON/Pydantic, token usage, latenza e retry.
```

Prompt prioritari da versionare:

```text
IntakeAgent
IndexAgent
SectionWriterAgent
SectionQAAgent
DocumentQAAgent
RevisionAgent
```

`ai-prompt-engineering-safety-review` resta la skill di revisione sicurezza/robustezza; `prompt-engineering-patterns` è la skill di progettazione template, structured output, fallback, versioning, test e metriche.

---

## 21. Comandi Telegram target

```text
/start
/nuovo_dvr
/stato_dvr
/mancanti
/fonti
/revisioni
/conferma
/valida_indice
/redigi_dvr
/genera_documento
/modifica_documento
/scarica
/approva
/blocca
/doctor
/provider
/annulla
/help
```

Livelli autorizzativi:

| Comando | Ruolo minimo |
|---|---|
| `/nuovo_dvr`, `/stato_dvr`, `/mancanti`, `/fonti`, `/modifica_documento`, `/scarica` | `client_user` autorizzato sul progetto |
| `/revisioni`, `/approva`, `/blocca` | `ctsafe_reviewer` o `admin` secondo target |
| `/doctor`, `/provider` | `admin` |

Esempi:

```text
/nuovo_dvr
Ciao, devo creare un nuovo DVR...
```

```text
/stato_dvr
```

```text
/modifica_documento
Nel capitolo mansioni aggiungi che il magazziniere usa il muletto.
```

---

## 22. Logging e audit

Ogni run agente deve essere tracciata.

Tabella:

```sql
create table agent_runs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid,
  agent_name text,
  input jsonb,
  output jsonb,
  status text,
  model text,
  llm_provider text,
  llm_provider_mode text,
  tokens_input integer,
  tokens_output integer,
  cost_estimate numeric,
  error text,
  created_at timestamp default now()
);
```

Da tracciare sempre:

```text
input utente
prompt version
modello usato
chunk recuperati
output generato
QA result
errori
retry
costo stimato
channel_event_id
session_key
tool policy decision
provider name/mode
provider health status
artifact versions
```

---

## 23. Testing

### 23.1 Test minimi

```text
test_intake_extracts_required_fields
test_index_generation_with_ateco
test_index_validation_adds_missing_sections
test_rag_filters_by_risk_category
test_chapter_generation_uses_company_data
test_section_qa_detects_placeholder
test_docx_generation_creates_file
test_revision_updates_single_section
test_memory_write_requires_scope_source_confidence
test_learning_proposal_does_not_apply_change
test_eval_runner_detects_regression
test_version_activation_requires_human_approval
test_channel_event_normalization
test_auth_gate_blocks_unauthorized_user
test_command_router_requires_project_scope
test_tool_policy_denies_forbidden_tool
test_provider_router_tracks_provider_in_run
test_subscription_bridge_never_logs_tokens
test_dvr_doctor_is_read_only
```

---

### 23.2 Dataset di valutazione RAG

Creare una cartella:

```text
tests/fixtures/rag_eval/
```

Con esempi:

```json
{
  "query": "rischio caduta dall'alto per installatore linee vita",
  "expected_risk_category": "caduta_alto",
  "expected_mansioni": ["installatore", "tecnico"],
  "must_include_refs": ["D.Lgs. 81/08", "lavori in quota"]
}
```

---

## 24. Sicurezza e controllo umano

Il DVR è un documento tecnico e normativo. Il sistema deve aiutare, ma non sostituire il controllo umano.

Regole:

```text
- evidenziare dati mancanti;
- non inventare informazioni aziendali;
- non nascondere incertezze;
- loggare fonti e chunk usati;
- autorizzare utente, ruolo e progetto prima di ogni azione;
- non esporre tool fuori ruolo agli agenti;
- non salvare token, cookie o segreti in prompt, log, memorie, wiki o learning proposal;
- rendere esplicito ogni fallback provider;
- tracciare provider e modello usati in ogni run/DVR;
- mantenere validazione umana dell'indice;
- consentire revisione manuale Word;
- versionare ogni modifica.
```

---

## 25. Conclusione architetturale

La soluzione target non deve essere un singolo chatbot che “genera un DVR”.

Deve essere un sistema agentico a stati:

```text
input strutturato
  ↓
classificazione
  ↓
indice
  ↓
validazione
  ↓
pianificazione sezioni
  ↓
redazione capitoli
  ↓
QA
  ↓
DOCX versionato
  ↓
revisione agentica/manuale
  ↓
apprendimento dagli errori
```

Sintesi finale:

```text
Agno = orchestrazione agenti
Ops Gateway = canali, auth, comandi, sessioni, routing, policy e audit
Supabase = stato + vector DB + storage
Telegram = primo canale utente, normalizzato dal gateway
DOCX = output modificabile
DVR Quality Wiki = memoria qualitativa curata e autocontrollo QA
Memory Evolution = proposte, eval, approvazione e versioning controllato
Provider Router = selezione LLM tracciata e fallback esplicito
Render = backend AgentOS/FastAPI preferito
Vercel = frontend/dashboard/preview opzionale
```

Priorità tecnica:

```text
1. Replicare i 5 workflow n8n in Agno
2. Inserire Ops Gateway con auth, comandi, sessioni, tool policy e audit
3. Spostare stato da Airtable a Supabase
4. Rendere RAG filtrabile e valutabile
5. Generare DOCX nativo e modificabile
6. Aggiungere revisione agentica
7. Integrare DVR Quality Wiki read-only per apprendimento dagli errori
8. Integrare memoria persistente e auto-miglioramento controllato con approval gate
```

---

## 26. Decisioni tecniche confermate dopo review architetturale

Questa sezione integra le decisioni emerse dalla review tecnica su workflow n8n, template DVR, guida Notion, Airtable, Supabase RAG e documentazione Agno.

PRD operativo:

```text
tasks/prd-agente-dvr-agno.md
```

### 26.1 Principio guida

La UX deve restare agentica, ma il backend deve essere governato da workflow.

```text
L'utente parla con un agente.
Il sistema esegue workflow tracciati, persistenti e approvabili.
```

Questo significa:

- usare agenti LLM dove servono interpretazione, scrittura, QA semantica o revisione;
- usare workflow, servizi deterministici e repository tipizzati per stato, permessi, salvataggi, rendering DOCX, versioni, audit e approvazioni;
- non affidare a un singolo agente la proprieta' dello stato del progetto.

### 26.2 Dove usare agenti e dove usare codice deterministico

Usare agenti LLM per:

```text
IntakeAgent
IndexDraftAgent
IndexValidationAgent
ChapterWriterAgent
SectionQAAgent
DocumentQAAgent
RevisionAgent
LearningProposalAgent
```

Usare workflow/funzioni/servizi deterministici per:

```text
CommandRouter
SessionManager
AuthGate
ToolPolicy
ProjectRepository
SectionRepository
RagSearchTool
SectionEvidenceWriter
DocxRenderService
StorageService
VersionRegistryService
ApprovalService
DvrDoctorService
ProviderHealthService
AirtableSyncService
RagIngestService
```

Nota:

```text
DocxRenderAgent, VersionRegistryAgent e DvrDoctorAgent possono restare nomi concettuali nella guida,
ma l'implementazione consigliata e' deterministica, non basata su LLM libero.
```

### 26.3 Conferme dalla pipeline legacy

I workflow n8n reali confermano che l'attuale sistema e' una pipeline a stati:

```text
Telegram
-> intake AI
-> avvia_generazione
-> Airtable Progetti DVR
-> webhook indice
-> Supabase Vector Store
-> validazione indice
-> Airtable Capitoli DVR
-> redazione capitoli
-> Google Apps Script
-> Google Docs / DOCX
```

Sono presenti anche due workflow di supporto:

- `avvia_generazione (1).json`: chiamato come tool dall'intake, crea record Airtable e invia `record_id` al webhook `dvr-generation`;
- `RAG DVR - Aggiunta Doc alla pipeline (1).json`: pipeline ingest da Google Drive, OCR Mistral, embedding OpenAI e insert in Supabase `normativa`.

Implicazione:

```text
La migrazione non deve solo riscrivere prompt.
Deve spostare orchestrazione, batch, salvataggi, ingest, rendering e stati in backend testabile.
```

### 26.4 Conferme dal template DVR

Il template `01_DVR-spheractsafe (1).docx` e' un documento fortemente strutturato:

```text
4421 paragrafi non vuoti
120 tabelle
12 capitoli principali
126 sezioni Titolo2
```

Implicazione:

```text
Il DOCX finale non deve essere generato come testo libero.
Deve essere assemblato da template CT Safe + dati azienda + sezioni validate + tabelle strutturate.
```

Se l'utente allega un DVR esistente, il file allegato e' una sorgente da analizzare, non il template finale. Il risultato deve essere ricreato sul template CT Safe.

### 26.5 RAG come evidence layer

Il RAG e' confermato come scelta corretta, ma non come unico cervello del sistema.

Uso corretto:

```text
Template DOCX + schema DVR deterministico
+ dati aziendali tipizzati
+ RAG normativo filtrato
+ esempi validati/sanificati
+ QA agentico
+ revisione umana
```

Il Supabase RAG live e' utile ma non ancora production-grade:

- `normativa` popolata e vettorializzata;
- `indice` piccolo;
- `dvr_pregressi` vuota;
- metadata quasi solo tecnici;
- duplicazione elevata;
- funzioni legacy/incoerenti;
- RLS/grant da correggere.

Decisione:

```text
Introdurre `rag_chunks` come tabella target, mantenendo corpus legacy durante transizione.
```

Inoltre aggiungere una tabella o modello equivalente a `section_evidence`, per salvare:

```text
section_id
chunk_id
query
filters
score
rank
source_document
source_page / line span
decision: used / rejected / supporting / background
claim_or_section_part_supported
retrieval_policy_version
```

Non basta salvare solo `retrieved_chunk_ids`.

### 26.6 Memoria persistente

La memoria e' utile solo se separata dal modello dati.

Regola:

```text
I fatti del DVR stanno in Supabase tipizzato.
La memoria libera serve per continuita', preferenze e segnali di apprendimento controllato.
```

Project facts da tenere in tabelle/repository tipizzati:

```text
azienda
sedi
mansioni
lavoratori
attrezzature
sostanze
ambienti
rischi
DPI
dati mancanti
documenti/versioni
```

Ogni memoria deve avere:

```text
scope
scope_id
memory_type
source
confidence
retention_policy
contains_pii
created_by
```

Non usare customer PII o DVR riservati come memoria globale.

### 26.7 Auto-miglioramento controllato

L'auto-miglioramento e' ammesso solo come proposal loop.

Loop consentito:

```text
QA finding / reviewer edit / retrieval miss / eval failure
-> learning proposal
-> eval
-> approval umano
-> nuova versione registrata
-> deploy controllato
-> monitoraggio
```

Vietato:

```text
auto-modifica prompt production
auto-modifica template DOCX
auto-modifica RAG policy
auto-modifica tool permissions
auto-modifica checklist QA
```

Prima implementazione consigliata:

```text
shadow mode: il sistema crea proposte ma non cambia comportamento production.
```

### 26.8 Agno, AgentOS e persistenza

Agno conferma che:

- i workflow sono adatti a task prevedibili e auditabili;
- HITL e pause richiedono database persistente;
- AgentOS puo' esporre agenti, team e workflow come API;
- FastAPI custom e' il posto corretto per gateway, auth, webhook e dashboard API;
- RBAC/approval/tracing vanno sfruttati o replicati con policy applicative strette.

Decisione:

```text
Usare Postgres/Supabase anche per sessioni, workflow run, HITL, trace/eval dove possibile.
Non usare SQLite locale importante su Render.
```

### 26.9 Fase 1 e Fase 2

Fase 1:

```text
Telegram come canale principale.
Supabase come fonte operativa target.
Airtable come legacy mirror/adapter.
DOCX nativo generato backend.
RAG bonificato almeno nelle funzioni critiche.
```

Fase 2:

```text
Dashboard Next.js.
Riepilogo DVR realizzati.
Gestione documenti e versioni.
Gestione file RAG/Supabase vettoriale.
Chat/action panel con agente.
Avvio nuovi DVR.
Modifica DVR esistenti.
Nessun accesso frontend a service role, segreti o MCP admin.
```

### 26.10 Regola finale per lo sviluppatore

Implementare prima il percorso sottile ma completo:

```text
intake -> conferma dati -> indice -> approval indice -> una o poche sezioni -> QA -> DOCX draft -> revisione -> DOCX v2
```

Poi espandere a tutto il DVR, dashboard, memoria evolutiva e learning proposals.

La qualita' del sistema dipende piu' da stati, evidenze, QA e versioni che da un prompt piu' lungo.

---

## 27. Stato implementazione thin slice Fase 1 - 2026-05-28

E' stata creata una prima thin slice locale e verificabile del backend DVR:

```text
app/
  main.py
  settings.py
  security.py
  agno_runtime.py
  domain/
  repositories/
  services/
  workflows/
  prompts/
supabase/migrations/202605270001_initial_dvr_schema.sql
tests/test_thin_slice.py
```

Caratteristiche implementate:

- FastAPI backend minimale con endpoint health, doctor read-only e API DVR.
- Hook AgentOS opzionale tramite `DVR_ENABLE_AGENTOS`, disattivato nei test locali per non richiedere credenziali LLM.
- Settings da env vars.
- AuthGate minimale via header `X-User-Id` e `X-Role`, con ruoli `client_user`, `ctsafe_reviewer`, `admin`.
- Repository tipizzati in-memory e sostituibili con Supabase: `ProjectRepository`, `SectionRepository`.
- Tool/servizi tipizzati: `RagSearchTool`, `SectionEvidenceWriter`, `DocxRenderService`, `AirtableSyncService`, `DvrDoctorService`.
- Workflow deterministico nuovo DVR: intake, conferma, sync Airtable mock, indice, approval, sezioni pilota, evidenze, QA, DOCX draft e patch proposta.
- Prompt versionati in `app/prompts/`: intake, index generation, index validation, chapter generation, section QA, revision.
- Migration Supabase iniziale per `companies`, `dvr_projects`, `dvr_indexes`, `dvr_sections`, `generated_documents`, `document_patches`, `agent_runs`, `section_evidence`, `audit_events`, `channel_events`.

Verifica eseguita:

```text
python -m unittest -v tests.test_thin_slice
Ran 10 tests in 1.617s
OK
```

Nota operativa locale:

```text
Non usare `tempfile.TemporaryDirectory(dir="C:\\tmp")` nei test di questa workspace.
Su questa macchina la creazione directory temporanea in `C:\tmp` puo' restare appesa per minuti/ore.
Usare directory temporanee sotto `.tmp/tests/` nella workspace, ignorata da git.
```

Stato dei mock:

```text
RAG live Supabase non ancora interrogato dal runtime.
Airtable sync e' mockato.
LLM/Agno agents sono rappresentati da workflow deterministico e prompt versionati; nessuna chiamata LLM obbligatoria.
DOCX usa un renderer base e non ancora il template CT Safe completo.
Repository Supabase reali non ancora collegati.
```

---

## 28. Incremento Agno runtime Fase 1 - 2026-05-28

E' stato introdotto un wrapper Agno reale attorno alla thin slice esistente, senza riscrivere i contratti gia' creati.

Documentazione Agno consultata tramite Agno MCP prima della modifica:

```text
examples/workflows/basic-workflows/function-workflows/function-workflow
database/providers/postgres/usage/postgres-for-workflow
examples/agent-os/customize/custom-fastapi-app
input-output/structured-output/agent
examples/agents/human-in-the-loop/user-input-required
```

Nota compatibilita':

```text
La documentazione Agno corrente mostra API piu' recenti come agno.os.AgentOS, agno.db.postgres.PostgresDb e workflow Step.
La workspace locale ha Agno 1.4.4, che espone Workflow subclass-based, RunResponse, agno.storage.workflow.postgres.PostgresWorkflowStorage e Playground.
Il runtime ora prova prima AgentOS moderno se disponibile, poi usa Playground come fallback compatibile con Agno 1.4.4.
```

File aggiornati:

```text
app/agno_runtime.py
app/main.py
app/settings.py
app/services/doctor_service.py
tests/test_thin_slice.py
guida_progetto_agente_dvr_agno.md
```

Nuove caratteristiche:

- `create_agno_runtime(settings, workflow)` costruisce una factory runtime con agenti Agno specializzati e un workflow Agno governato.
- `CtsafeDvrAgnoWorkflow` incapsula il `DvrWorkflow` applicativo e mantiene gli stati deterministici esistenti.
- Il workflow Agno espone azioni tipizzate: `intake`, `create_project`, `confirm_project`, `generate_index`, `review_index`, `generate_pilot_sections`, `generate_docx_draft`, `request_patch`.
- Le chiamate dirette al workflow Agno richiedono `actor` per tutte le azioni operative tranne `intake`.
- Il workflow diretto verifica `allowed_operator_ids` e ruoli, cosi' non bypassa l'AuthGate applicativo quando viene esposto da AgentOS/Playground.
- Gli agenti Agno sono registrati come ruoli coerenti: `IntakeAgent`, `IndexDraftAgent`, `ChapterWriterAgent`, `RevisionAgent`.
- Gli agenti usano output strutturati compatibili con l'Agno locale (`response_model`, con fallback a `output_schema` se disponibile in versioni nuove).
- Gli agenti non vengono montati come endpoint diretti nel fallback Playground: resta esposto solo il workflow governato, per evitare chiamate LLM non autenticate o fuori policy.
- Storage workflow Agno configurabile tramite `DVR_AGNO_DB_URL` e `DVR_AGNO_DB_SCHEMA`; in locale resta memory mode.
- Nuovo endpoint admin `/api/dvr/runtime` per ispezionare runtime, agenti, workflow e storage.
- `/health` ora riporta anche il modo runtime Agno.
- `/doctor` segnala se lo storage workflow Agno Postgres e' configurato.

Verifica eseguita:

```text
python -m unittest -v tests.test_thin_slice
Ran 13 tests in 0.724s
OK
```

Stato non ancora production-ready:

```text
AgentOS moderno non e' disponibile nella versione Agno locale; il codice usa fallback Playground finche' Agno non viene aggiornato.
Storage Agno Postgres e' solo configurabile, non ancora validato contro Supabase live.
Repository operativi restano in-memory.
RAG live Supabase/pgvector resta mockato.
Airtable adapter resta mock/skipped.
DOCX continua a usare renderer base e non il template CT Safe assemblato in modo sicuro.
Patch resta proposta; manca ancora patch -> QA -> applicazione -> nuova versione DOCX.
Auth production non e' ancora implementata; l'header auth resta dev/local.
```

Prossimo step consigliato:

```text
Implementare repository Supabase configurabili per progetti, indici, sezioni, documenti, patch, evidence, audit e agent_runs,
mantenendo memory mode per test. Subito dopo collegare RagSearchTool a una funzione Supabase/pgvector least-privilege.
```

---

## 29. Incremento repository Supabase configurabile - 2026-05-28

E' stata introdotta la factory repository `memory/supabase`, mantenendo `memory` come default per test locali e sviluppo senza rete.

Documentazione Supabase verificata prima della modifica:

```text
Supabase Data REST API: endpoint PostgREST su /rest/v1/
Supabase changelog 2026: nuove tabelle non sempre esposte automaticamente alla Data API; servono grant espliciti quando si usa PostgREST.
```

Decisione implementativa:

```text
Usare un client PostgREST minimale lato backend, non Supabase MCP e non un accesso admin generico dentro gli agenti.
Il runtime passa solo da repository e writer tipizzati.
```

File aggiunti:

```text
app/repositories/factory.py
app/repositories/supabase_rest_client.py
app/repositories/supabase_project_repository.py
app/repositories/supabase_section_repository.py
app/services/supabase_section_evidence_writer.py
```

File aggiornati:

```text
app/main.py
app/settings.py
app/services/doctor_service.py
app/repositories/project_repository.py
app/workflows/dvr_workflow.py
tests/test_thin_slice.py
guida_progetto_agente_dvr_agno.md
```

Nuove caratteristiche:

- `DVR_REPOSITORY_BACKEND=memory|supabase`, default `memory`.
- `create_repository_bundle(settings)` restituisce repository progetto, repository sezioni, evidence writer e store locale.
- In modalita' `supabase`, il backend richiede `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY`.
- `SupabaseRestClient` espone solo `insert`, `select`, `select_one`, `update` su PostgREST.
- `SupabaseProjectRepository` implementa contratti per company/project/index/document/patch/audit/agent_runs.
- `SupabaseSectionRepository` implementa contratti per sezioni DVR.
- `SupabaseSectionEvidenceWriter` salva `section_evidence` su Supabase.
- `DvrWorkflow.generate_docx_draft` usa ora `list_generated_documents_for_project`, evitando accesso diretto allo store in-memory.
- `/health` riporta `repository_backend`.
- `/doctor` riporta lo stato del repository backend.

Verifica eseguita:

```text
python -m unittest -v tests.test_thin_slice
Ran 16 tests in 0.695s
OK

python -m compileall app tests
OK
```

Stato non ancora production-ready:

```text
Il backend Supabase e' configurabile e coperto da test con fake client, ma non e' ancora stato validato contro il progetto Supabase live.
La migration attuale revoca accesso ad anon/authenticated; per usare PostgREST con service role/secret key occorre verificare grant e RLS nel progetto reale.
Non e' ancora stato implementato un ruolo Postgres/API key truly least-privilege dedicato al runtime DVR.
RAG live Supabase/pgvector resta mockato.
Airtable adapter resta mock/skipped.
DOCX template CT Safe completo non ancora integrato.
Patch -> QA -> applicazione -> nuova versione DOCX resta da implementare.
```

Prossimo step consigliato:

```text
Collegare RagSearchTool a Supabase/pgvector tramite funzione RPC stretta o endpoint PostgREST controllato,
con contratto Pydantic, fallback esplicito a empty evidence/blocked QA, logging agent_runs e test con fake client.
Poi validare repository Supabase contro un database reale/staging con grant espliciti e senza esporre chiavi al frontend.
```

---

## 30. Incremento RAG Supabase/pgvector configurabile - 2026-05-28

E' stato collegato `RagSearchTool` a un backend Supabase/pgvector configurabile, mantenendo `mock` come default locale.

Documentazione e contesto verificati prima della modifica:

```text
Agno MCP: Tool Decorator / custom tools; i tool runtime devono restare funzioni strette e controllate.
Supabase Data REST/RPC: PostgREST espone funzioni SQL via /rest/v1/rpc/{function_name}.
OpenAI Embeddings API: endpoint POST /v1/embeddings per generare query embeddings.
Skill/guida CT Safe: corpus legacy a 1536 dimensioni; match_normativa, match_documents, match_dvr_pregressi; match_indice non affidabile.
```

Decisione implementativa:

```text
RAG backend selezionabile con DVR_RAG_BACKEND=mock|supabase.
Il backend supabase genera embedding via OpenAI e chiama RPC Supabase stretta.
In caso di errore o configurazione mancante, il tool restituisce evidenza vuota con fallback_reason esplicito.
Il workflow non approva piu' automaticamente una sezione senza evidenze: la manda in needs_revision se i dati aziendali sono presenti ma il RAG non ha salvato evidenze.
```

File aggiunti:

```text
app/services/embedding_provider.py
app/services/rag_factory.py
```

File aggiornati:

```text
app/domain/models.py
app/repositories/supabase_rest_client.py
app/services/rag_search_tool.py
app/main.py
app/settings.py
app/services/doctor_service.py
app/workflows/dvr_workflow.py
tests/test_thin_slice.py
guida_progetto_agente_dvr_agno.md
```

Nuove caratteristiche:

- `DVR_RAG_BACKEND=mock|supabase`, default `mock`.
- `OPENAI_API_KEY` abilita embedding query con `text-embedding-3-small` di default.
- `DVR_EMBEDDING_MODEL` permette di cambiare modello embedding.
- `DVR_RAG_ALLOW_FALLBACK` controlla se gli errori RAG diventano fallback esplicito o eccezione.
- `SupabaseRestClient.rpc(function_name, payload)` chiama funzioni RPC PostgREST.
- Mapping corpus legacy:
  - `normativa` -> `match_normativa`
  - `indice` -> `match_documents`
  - `dvr_pregressi` -> `match_dvr_pregressi`
- `RagSearchResult` ora include `is_fallback` e `fallback_reason`.
- `RagSearchTool` converte righe RPC legacy in `EvidenceChunk` con mapping robusto di `id/chunk_id`, `content/text`, `similarity/score`, `metadata.source/pdf/loc`.
- `DvrWorkflow.generate_pilot_sections` marca `needs_revision` quando non viene salvata evidenza RAG.
- `/doctor` segnala backend RAG e stato chiave embedding.

Verifica eseguita:

```text
python -m unittest -v tests.test_thin_slice
Ran 18 tests in 0.783s
OK

python -m compileall app tests
OK
```

Stato non ancora production-ready:

```text
RAG Supabase e' implementato e testato con fake RPC, ma non ancora validato contro il Supabase live.
Le funzioni legacy hanno limiti noti: match_documents per indice non filtra davvero metadata; match_indice resta da non usare.
Il backend usa ancora service role/secret key se configurato; serve un ruolo/API key least-privilege dedicato o RPC in schema controllato.
Manca una migration per rag_chunks/match_rag_chunks_v2.
Manca evaluation set RAG con casi reali e metriche retrieval.
```

Prossimo step consigliato:

```text
Validare in staging/live una chiamata DVR_RAG_BACKEND=supabase su match_normativa e match_documents,
poi aggiungere migration per funzioni v2 least-privilege o rag_chunks/match_rag_chunks.
In parallelo, creare tests/fixtures/rag_eval con casi ATECO/mansioni/rischi e soglie di qualita' retrieval.
```

---

## 31. Harness validazione RAG e bozza SQL v2 - 2026-05-28

Non e' stato possibile validare Supabase live da questa workspace perche':

```text
.env non contiene SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY o OPENAI_API_KEY.
Supabase CLI non e' installato nella workspace.
```

E' stato quindi aggiunto un incremento locale verificabile per preparare la validazione live e la migrazione RAG v2.

File aggiunti:

```text
app/services/rag_validation.py
tests/fixtures/rag_eval/dvr_core.json
scripts/validate_rag_supabase.py
supabase/sql/rag_v2_draft.sql
```

Nuove caratteristiche:

- `RagEvalCase` e `RagEvalResult` per casi di valutazione retrieval.
- Fixture `tests/fixtures/rag_eval/dvr_core.json` con casi iniziali:
  - normativa DPI/mansioni/rischio elettrico;
  - indice/struttura DVR.
- `scripts/validate_rag_supabase.py` carica `.env`, verifica le env richieste senza stampare segreti, esegue i casi RAG e mostra solo esiti, chunk id e motivi di fallback.
- `supabase/sql/rag_v2_draft.sql` contiene bozza non ancora applicata di:
  - tabella `rag_chunks`;
  - indici pgvector/Gin;
  - RLS e revoke base;
  - `match_rag_chunks`;
  - wrapper `match_normativa_v2`, `match_indice_v2`, `match_dvr_pregressi_v2`;
  - revoke execute da `public`.

Nota importante:

```text
`supabase/sql/rag_v2_draft.sql` non e' una migration canonica.
Prima di applicarla va trasformata con `supabase migration new ...`, revisionata su staging, e aggiornata con il ruolo least-privilege reale del runtime DVR.
```

Verifica eseguita:

```text
python -m unittest -v tests.test_thin_slice
Ran 19 tests in 0.858s
OK

python -m compileall app tests scripts
OK

python scripts\validate_rag_supabase.py
Missing required env vars for live RAG validation:
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- OPENAI_API_KEY
No secrets were printed. Configure these in the backend environment and rerun.
```

Prossimo step consigliato:

```text
Installare/configurare Supabase CLI o fornire env live/staging backend.
Eseguire `python scripts\validate_rag_supabase.py`.
Se i casi legacy passano, convertire `supabase/sql/rag_v2_draft.sql` in migration canonica e provarla su staging.
Se i casi legacy falliscono, correggere mapping RPC/metadata prima di creare rag_chunks.
```

---

## 32. Fix compatibilita' Agno 2.6.9 runtime - 2026-05-28

Durante la review successiva e' emerso che la suite passava con il Python globale della macchina, ma falliva con l'ambiente riproducibile `uv.lock`.

Root cause:

```text
Il codice Agno runtime usava parametri Agno 1.x:
- Agent(agent_id=...)
- Workflow(workflow_id=..., storage=...)

`uv.lock` installa Agno 2.6.9, dove la documentazione Agno MCP e le firme runtime indicano:
- Agent(id=..., output_schema=...)
- Workflow(id=..., db=...)
```

Fix applicato:

```text
app/agno_runtime.py
```

Dettagli:

- Introdotta introspezione della firma dei costruttori Agno.
- `_make_agent` ora filtra i kwargs supportati e funziona con `id/output_schema` su Agno 2.x e `agent_id/response_model` su Agno 1.x.
- `CtsafeDvrAgnoWorkflow` ora filtra `id/workflow_id` e `db/storage` in base alla versione Agno disponibile.
- `_build_workflow_storage` prova prima `agno.db.postgres.PostgresDb` per Agno 2.x e poi `PostgresWorkflowStorage` legacy.
- `run()` accetta anche input in forma `{"action": ..., "payload": ..., "actor": ...}` per compatibilita' con chiamate AgentOS piu' generiche.

Verifica eseguita:

```text
uv --cache-dir .uv-cache run --with pytest pytest -q
19 passed, 1 warning

python -m unittest -q tests.test_thin_slice
Ran 19 tests
OK
```

Nota:

```text
Il runtime Agno ora e' compatibile con Agno 2.6.9 da `uv.lock` e con l'Agno legacy installato globalmente.
Resta comunque da validare l'esposizione AgentOS reale con `DVR_ENABLE_AGENTOS=true`, perche' i test attuali validano factory, workflow diretto e API FastAPI, non una sessione completa via endpoint AgentOS.
```

---

## 33. Validazione AgentOS reale e blocker RAG live - 2026-05-28

E' stata eseguita una validazione aggiuntiva usando la documentazione Agno MCP e l'ambiente riproducibile `uv.lock`.

La documentazione Agno MCP rilevante conferma:

- AgentOS con FastAPI custom supporta `base_app`.
- In caso di conflitti route, Agno usa `on_route_conflict`; per preservare l'health check custom dell'app va usato `on_route_conflict="preserve_base_app"`.
- L'API AgentOS workflow esegue `POST /workflows/{workflow_id}/runs` con body form e campo `message`.

Problemi trovati durante la validazione:

```text
DVR_ENABLE_AGENTOS=true con Agno 2.6.9 montava AgentOS, ma:
- AgentOS sovrascriveva GET /health con il proprio endpoint.
- /workflows/{workflow_id}/runs falliva perche' Agno provava a fare deep_copy() del workflow custom.
- Dopo il deep_copy, AgentOS chiamava arun() e non il run() custom.
- La risposta fallback non aveva to_dict(), richiesto dalla serializzazione AgentOS.
```

Fix applicato:

```text
app/agno_runtime.py
tests/test_thin_slice.py
```

Dettagli tecnici:

- `maybe_wrap_agentos()` passa `on_route_conflict="preserve_base_app"` quando supportato.
- `CtsafeDvrAgnoWorkflow` implementa `deep_copy()` per il contratto Agno 2.x.
- `CtsafeDvrAgnoWorkflow` implementa `arun()` e lo instrada nello stesso dispatcher governato di `run()`.
- `_normalize_workflow_call()` accetta input AgentOS in forma JSON nel campo `message` o `input`.
- `_make_run_response()` usa `agno.run.workflow.WorkflowRunOutput` quando disponibile.
- Il fallback locale espone comunque `to_dict()`.
- Aggiunti test per payload AgentOS JSON, `arun()` e `deep_copy()`.

Validazione AgentOS eseguita:

```text
uv --cache-dir .uv-cache run python -c "<TestClient con AppSettings(enable_agentos=True)>"

GET /health
200
{
  "status": "ok",
  "app": "CT Safe DVR Agent",
  "environment": "local",
  "agno_runtime": "memory",
  "repository_backend": "memory"
}

GET /api/dvr/runtime
200
agentos_mount = "agentos"
runtime_mode = "memory"
workflows = ["ctsafe-dvr-workflow"]

GET /workflows
200
ctsafe-dvr-workflow presente

POST /workflows/ctsafe-dvr-workflow/runs
message = {"action":"intake","payload":{"company":{"company_name":"ACME SRL"}}}
200
content.status = "blocked_missing_data"
```

Verifica test:

```text
python -m unittest -q tests.test_thin_slice
Ran 22 tests
OK

uv --cache-dir .uv-cache run --with pytest pytest -q
22 passed, 2 warnings
```

Nota warning:

```text
uv/pytest segnala un warning di cache su .pytest_cache per permessi Windows.
Non impatta l'esito della suite.
```

Validazione RAG live:

```text
python scripts\validate_rag_supabase.py
Missing required env vars for live RAG validation:
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- OPENAI_API_KEY
No secrets were printed. Configure these in the backend environment and rerun.
```

Stato ambiente locale:

```text
La workspace non espone SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY o OPENAI_API_KEY.
Supabase CLI non risulta installato.
psql non risulta installato.
```

Conclusione:

```text
AgentOS e' ora validato in modalita' memoria con Agno 2.6.9.
La validazione live Supabase/RAG non e' eseguibile da questa workspace finche' non vengono configurate le env richieste o fornito un ambiente staging.
```

Rischio ancora aperto prima della produzione:

```text
Le route AgentOS native devono essere protette da AuthGate/middleware reale prima di esporle fuori dall'ambiente locale.
Il workflow interno valida actor e ruoli per le azioni governate, ma l'endpoint AgentOS deve comunque avere autenticazione di trasporto/API.
```

---

## 34. Verifica credenziali file.env - 2026-05-29

E' stato creato un file locale dedicato:

```text
file.env
```

Nota sicurezza:

```text
file.env contiene credenziali locali/staging e deve restare fuori da versionamento.
E' stato aggiunto a .gitignore.
```

Stato verificato senza stampare segreti:

```text
SUPABASE_URL = presente
SUPABASE_SERVICE_ROLE_KEY = presente
SUPABASE_ANON_KEY = presente
AIRTABLE_API_KEY = presente
AIRTABLE_BASE_ID = presente
OPENAI_API_KEY = vuota
Provider generativo previsto = openai_subscription_bridge
```

Validazione Supabase base:

```text
normativa = ok, 1 riga leggibile
indice = ok, 1 riga leggibile
dvr_pregressi = ok, 0 righe restituite
```

La tabella `dvr_pregressi` resta quindi accessibile ma vuota, coerente con l'analisi precedente del DB.

Validazione Airtable base:

```text
Progetti DVR = ok, 1 record leggibile
Capitoli DVR = ok, 1 record leggibile
```

Chiarimento provider:

```text
OPENAI_API_KEY non e' un requisito per la generazione LLM del progetto quando si usa OpenAI subscription bridge.
La subscription bridge resta il provider generativo previsto per il caso single-tenant.
```

Stato RAG live:

```text
La validazione semantica RAG end-to-end non puo' ancora essere eseguita dal codice attuale perche'
il backend implementa solo OpenAIEmbeddingProvider per generare l'embedding della query.
Questo e' un vincolo dell'implementazione RAG corrente, non una decisione di usare OpenAI API
come provider generativo principale.

Per evitare API key OpenAI anche sugli embedding serve implementare uno di questi percorsi:
1. query embedding tramite un provider compatibile con i 1536-dim gia' presenti nel corpus;
2. bridge subscription con endpoint/tool di embedding compatibile e health check dedicato;
3. migrazione/re-embedding del corpus con un provider embedding alternativo;
4. fallback temporaneo keyword/hybrid solo per diagnostica, non equivalente al vector RAG attuale.
```

Aggiornamento tecnico:

```text
scripts/validate_rag_supabase.py ora carica sia .env sia file.env.
Il comando diretto resta:

python scripts\validate_rag_supabase.py

ma oggi valida il percorso RAG basato su embedding OpenAI API.
Va esteso quando verra' implementato il provider embedding coerente con OpenAI subscription bridge.
```

---

## 35. Correzione provider OpenAI subscription vs API key - 2026-05-29

Chiarimento importante:

```text
Per la generazione LLM dell'agente DVR il provider previsto nel caso single-tenant e' `openai_subscription_bridge`.
`OPENAI_API_KEY` non deve essere trattata come requisito generale dell'agente.
```

Il file locale `file.env` e' stato corretto per riflettere questa decisione:

```text
DVR_DEFAULT_LLM_PROVIDER=openai_subscription_bridge
DVR_DEFAULT_MODEL=provider_reported_model
OPENAI_SUBSCRIPTION_BRIDGE_ENABLED=true
OPENAI_SUBSCRIPTION_BRIDGE_HEALTHCHECK_REQUIRED=true
OPENAI_SUBSCRIPTION_BRIDGE_URL=
OPENAI_SUBSCRIPTION_BRIDGE_SESSION_REF=
```

Separazione corretta:

```text
LLM generation provider:
- openai_subscription_bridge
- usato per intake, indice, capitoli, revisioni e conversazione quando sara' implementato il provider router.

Query embedding provider:
- componente separato necessario al vector RAG.
- il codice attuale implementa solo OpenAIEmbeddingProvider via OpenAI API.
```

Implicazione:

```text
La mancanza di OPENAI_API_KEY non blocca la scelta architetturale della subscription bridge.
Blocca solo la validazione semantica RAG corrente, perche' il corpus Supabase esistente usa embedding
1536-dim compatibili con il vecchio flusso OpenAI embeddings e il backend non ha ancora un provider
alternativo per generare embedding query compatibili.
```

Fix applicati:

```text
file.env
scripts/validate_rag_supabase.py
app/settings.py
app/services/doctor_service.py
guida_progetto_agente_dvr_agno.md
```

Comportamento aggiornato dello script:

```text
python scripts\validate_rag_supabase.py

Supabase credentials found. Checking corpus connectivity without printing secrets.
normativa: ok, rows_returned=1
indice: ok, rows_returned=1
dvr_pregressi: ok, rows_returned=0
Semantic vector RAG evaluation skipped: the current implementation only has OpenAI API query embeddings.
This is separate from the LLM generation provider, which can be openai_subscription_bridge.
```

Prossimo lavoro tecnico necessario:

```text
Implementare `LlmProviderRouter` e `OpenAISubscriptionBridgeProvider`.
Poi decidere il percorso embedding:
1. mantenere una piccola API key solo per embedding query;
2. implementare un embedding provider alternativo compatibile;
3. re-embeddare il corpus con un modello/provider diverso;
4. usare hybrid keyword/vector solo come diagnostica temporanea, non come sostituto completo.
```

---

## 36. OpenRouter come provider API e embedding query - 2026-05-29

Nuova decisione utente:

```text
Usare OpenRouter invece di OpenAI API key.
```

Variabile rilevata nel `file.env`:

```text
OPEN_ROUTER_KEY = presente
```

Il codice supporta sia:

```text
OPEN_ROUTER_KEY
OPENROUTER_API_KEY
```

Aggiornamenti applicati:

```text
file.env
app/settings.py
app/services/embedding_provider.py
app/services/rag_factory.py
app/services/doctor_service.py
scripts/validate_rag_supabase.py
tests/test_thin_slice.py
MCP_E_SKILLS_PROGETTO.md
guida_progetto_agente_dvr_agno.md
```

Configurazione runtime scelta:

```text
DVR_DEFAULT_LLM_PROVIDER=openrouter
DVR_DEFAULT_MODEL=anthropic/claude-sonnet-latest
DVR_EMBEDDING_PROVIDER=openrouter
DVR_EMBEDDING_MODEL=openai/text-embedding-3-small
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

Nota tecnica:

```text
OpenRouter viene usato ora per la query embedding del RAG tramite endpoint `/embeddings`.
Il modello embedding e' normalizzato a `openai/text-embedding-3-small`, coerente con i 1536
dimensioni del corpus Supabase legacy.
```

Validazione eseguita:

```text
python -m unittest -q tests.test_thin_slice
Ran 24 tests
OK

python -m compileall app tests scripts
OK
```

Validazione live RAG con OpenRouter:

```text
python scripts\validate_rag_supabase.py

FAIL normativa_dpi_mansione: 0 chunks
FAIL indice_struttura_dvr: 5 chunks
```

Lettura del risultato:

```text
OpenRouter e Supabase sono stati chiamati correttamente.
Il problema residuo non e' piu' la credenziale/provider, ma la qualita' del retrieval legacy:
- il caso normativa usa un filtro `source_type=normativa`, ma nel DB legacy i metadata osservati sono `blobType`, `loc`, `source`;
- senza quel filtro, normativa restituisce 5 chunk, ma i risultati sono deboli e duplicati;
- indice restituisce chunk, ma non soddisfa i termini attesi della fixture.
```

Prossimo fix consigliato:

```text
Aggiornare le fixture di valutazione live per il DB legacy reale.
Poi migliorare RAG v2: deduplica, metadata semantici, funzioni match_* coerenti,
indice vettoriale su indice, e test retrieval tarati su contenuti realmente presenti.
```

---

## 37. Stabilizzazione RAG legacy con hybrid retrieval - 2026-05-29

Problema osservato:

```text
Il vector retrieval puro su Supabase legacy con OpenRouter embeddings recuperava chunk deboli,
spesso duplicati o non centrati sulla query.
Inoltre la fixture live usava filtri metadata non presenti nel DB legacy, ad esempio:
source_type=normativa.
```

Cause principali:

```text
1. Metadata legacy poveri: `normativa` espone soprattutto `blobType`, `loc`, `source`.
2. `source` vale spesso `blob`, quindi non e' possibile validare fonti come `D.Lgs. 81/08`
   dal solo metadata attuale.
3. Il corpus `normativa` contiene duplicati esatti.
4. Il vector top-k puo' essere poco pertinente su query DVR composte.
5. Il corpus `indice` e' piccolo e utile, ma non ha metadati sorgente forti.
```

Fix applicato:

```text
app/repositories/supabase_rest_client.py
app/services/rag_search_tool.py
tests/fixtures/rag_eval/dvr_core.json
tests/test_thin_slice.py
```

Dettagli:

- `SupabaseRestClient.search_text()` aggiunge una ricerca lessicale read-only su `content`.
- `RagSearchTool` ora fa sempre retrieval ibrido sui corpus legacy:
  - vector search via RPC `match_*`;
  - lexical backfill via PostgREST `content.ilike`;
  - deduplica per `chunk_id` e contenuto normalizzato;
  - rerank locale che promuove chunk con overlap sui termini query.
- I filtri legacy come `source_type=normativa` vengono rimossi quando il corpus stesso identifica gia' la tabella.
- La fixture live e' stata riallineata al DB reale: non richiede piu' source term inesistenti come `D.Lgs. 81/08` nei metadata legacy.

Validazione live:

```text
python scripts\validate_rag_supabase.py

PASS normativa_dpi_mansione: 5 chunks
chunks: 27214, 27319, 27322, 40154, 49551

PASS indice_struttura_dvr: 5 chunks
chunks: 9, 16, 4, 7, 14
```

Verifica test:

```text
python -m unittest -q tests.test_thin_slice
Ran 25 tests
OK

uv --cache-dir .uv-cache run --with pytest pytest -q
25 passed, 1 warning
```

Nota importante:

```text
Questo e' un fix ponte per rendere usabile il corpus legacy.
Non risolve la qualita' strutturale del RAG.
```

Resta necessario RAG v2:

```text
1. Creare/migrare verso `rag_chunks`.
2. Deduplicare i chunk.
3. Salvare source_document reale, pagina/righe, corpus, section_type, normative_refs,
   ATECO, mansioni, risk_category.
4. Correggere/razionalizzare `match_indice`, `match_documents`, `match_normativa`.
5. Aggiungere indice vettoriale su `indice` o migrare indice dentro `rag_chunks`.
6. Implementare valutazioni RAG separate:
   - legacy smoke test;
   - quality eval v2 con fonti vere e requisiti piu' severi.
```

---

## 38. RAG v2 implementato localmente - 2026-05-29

Obiettivo:

```text
Introdurre un RAG v2 realmente usabile dal runtime Agno senza rompere il legacy.
Il runtime resta protetto da tool Python stretti e tipizzati; MCP, Supabase CLI e
tool amministrativi restano strumenti da sviluppatore/migrazione.
```

Fonti tecniche verificate:

```text
- Agno MCP docs: Agno supporta knowledge base e PgVector/hybrid search, ma nel progetto
  CT Safe resta preferibile un tool runtime custom e stretto per mantenere policy,
  audit, fallback e contratti Pydantic sotto controllo.
- Supabase docs correnti: Supabase usa pgvector per semantic search; la documentazione
  2026 raccomanda in generale HNSW rispetto a IVFFlat per performance/robustezza.
- Supabase security docs: le tabelle in schema public devono avere RLS/grant espliciti;
  le funzioni RPC in public non devono restare eseguibili da anon/authenticated.
```

File introdotti/modificati:

```text
supabase/migrations/202605290001_rag_v2_chunks.sql
supabase/sql/rag_v2_draft.sql
app/settings.py
app/services/rag_factory.py
app/services/rag_search_tool.py
app/services/doctor_service.py
scripts/validate_rag_supabase.py
scripts/validate_rag_v2_supabase.py
tests/test_thin_slice.py
```

Schema RAG v2:

```text
Tabella target:
public.rag_chunks

Campi principali:
- corpus
- legacy_table / legacy_id
- content
- embedding vector(1536)
- metadata jsonb
- source_type
- source_document
- source_page
- line_from / line_to
- risk_category
- section_type
- ateco_codes
- mansioni
- ambienti
- attrezzature
- document_type
- normative_refs
- valid_from / valid_to
- is_active
- quality_flags
- content_hash generato
- search_vector generato
```

Scelte tecniche:

```text
1. `rag_chunks` e' tabella unificata per normativa, indice e dvr_pregressi.
2. Le tabelle legacy non vengono eliminate.
3. La migration importa i record legacy esistenti se le tabelle sono presenti.
4. I record importati mantengono legacy_table/legacy_id per tracciabilita' e rollback.
5. I metadata legacy poveri vengono conservati ma marcati con `legacy_metadata_weak`
   quando la sorgente osservata e' solo `blob`.
6. L'indice vettoriale v2 usa HNSW su `embedding vector_cosine_ops`.
7. Sono presenti indici GIN per metadata, ATECO, mansioni, normative_refs e FTS.
8. RLS viene abilitata e anon/authenticated non ricevono accesso.
9. EXECUTE sulle funzioni RPC viene revocato da public e concesso a service_role.
```

Funzioni RPC RAG v2:

```text
public.match_rag_chunks(...)
public.search_rag_chunks_text(...)
public.match_normativa_v2(...)
public.match_indice_v2(...)
public.match_dvr_pregressi_v2(...)
```

Policy runtime:

```text
DVR_RAG_BACKEND=mock|supabase
DVR_RAG_VERSION=legacy|v2
DVR_RAG_V2_LEGACY_FALLBACK=true|false
```

Comportamento:

```text
- Default sicuro: `legacy`.
- Con `DVR_RAG_VERSION=v2`, il runtime chiama `match_rag_chunks` con `corpus_filter`.
- La ricerca v2 usa vector retrieval piu' lexical backfill via `search_rag_chunks_text`.
- Durante la transizione, se v2 fallisce o non restituisce evidenza, puo' tornare al
  legacy se `DVR_RAG_V2_LEGACY_FALLBACK=true`.
- In produzione/staging, dopo validazione v2, impostare
  `DVR_RAG_V2_LEGACY_FALLBACK=false` per evitare contaminazione da metadata legacy.
```

Validatori:

```text
python scripts\validate_rag_supabase.py
python scripts\validate_rag_v2_supabase.py
```

Nota operativa importante:

```text
La migration RAG v2 e' stata creata nel repository ma non applicata al Supabase live
da questa sessione: nel workspace non risultano disponibili `supabase`, `psql` o un
MCP Supabase con `execute_sql`.

Prima di attivare `DVR_RAG_VERSION=v2` senza fallback, applicare la migration su
staging/live con Supabase SQL editor, Supabase CLI, MCP Supabase autorizzato o altro
canale SQL controllato. Dopo l'applicazione eseguire:

python scripts\validate_rag_v2_supabase.py
```

Verifica locale:

```text
python -m py_compile app\settings.py app\services\rag_factory.py app\services\rag_search_tool.py app\services\doctor_service.py scripts\validate_rag_supabase.py scripts\validate_rag_v2_supabase.py

python -m unittest -q tests.test_thin_slice
Ran 27 tests
OK
```

Validazione live post-modifica:

```text
python scripts\validate_rag_supabase.py

RAG mode: backend=supabase, version=legacy, v2_legacy_fallback=True
PASS normativa_dpi_mansione: 5 chunks
chunks: 27214, 27319, 27322, 40154, 49551
PASS indice_struttura_dvr: 5 chunks
chunks: 9, 16, 4, 7, 14
```

Validazione v2 live:

```text
python scripts\validate_rag_v2_supabase.py

Esito atteso finche' la migration non viene applicata:
Supabase REST POST rpc/match_rag_chunks failed: HTTP 404 / PGRST202
Could not find the function public.match_rag_chunks(...)
```

Questo conferma che:

```text
1. Il codice runtime v2 e' pronto.
2. Il legacy continua a funzionare.
3. Il DB live non ha ancora la migration RAG v2.
```

Prossimi passi RAG dopo applicazione live:

```text
1. Eseguire migration RAG v2 su Supabase.
2. Validare count per corpus dentro `rag_chunks`.
3. Eseguire `scripts\validate_rag_v2_supabase.py`.
4. Se HNSW non fosse supportato dalla versione pgvector del progetto, sostituire
   temporaneamente con IVFFlat e pianificare upgrade pgvector.
5. Bonificare progressivamente i metadata reali: source_document, pagina, righe,
   riferimenti normativi, mansioni, ATECO, risk_category.
6. Creare ingestion v2 per nuovi upload dashboard: ogni nuovo documento deve entrare
   direttamente in `rag_chunks`, non nelle tabelle legacy.
```

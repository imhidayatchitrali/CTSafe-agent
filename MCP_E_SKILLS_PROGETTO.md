# MCP e Skills per il progetto CT Safe DVR

Data: 2026-05-27

Questo file definisce quali server MCP e quali skill usare per realizzare il nuovo agente DVR basato su Agno, Supabase, Telegram, RAG e generazione DOCX.

Principio guida: gli MCP servono soprattutto per sviluppo, ispezione, migrazione e amministrazione. L'agente Agno in produzione deve usare tool Python tipizzati e con permessi stretti, non accessi MCP generici e troppo potenti.

## Server MCP utilizzabili

| Server MCP | Stato | Uso nel progetto | Uso da Agno |
|---|---|---|---|
| Airtable MCP | Disponibile nel setup progetto | Lettura del sistema legacy: progetti, capitoli, stati, campi, link documenti, mapping tabelle. Serve per migrare progressivamente da Airtable a Supabase. | Non usarlo come dipendenza runtime stabile. Se serve in fase ponte, creare un tool Agno read-only `LegacyAirtableReader` con operazioni limitate e loggate. |
| Supabase MCP Toolbox | Disponibile in `project-brain/tools/mcp-toolbox` | Ispezione DB, funzioni `match_*`, sicurezza RLS/grant, migrazioni, test SQL, analisi RAG live. | Non esporre direttamente tutto il toolbox all'agente. Agno deve usare tool Python specifici: `RagSearchTool`, `ProjectRepository`, `DocumentRepository`, `StorageRepository`. |
| Agno MCP | Configurato in `.claude/settings.json` | Consultazione/uso strumenti Agno durante sviluppo, allineamento con AgentOS e pattern Agno. | Agno deve esporre i propri agenti/workflow via AgentOS MCP verso client esterni, non dipendere dal proprio MCP come scorciatoia interna. |
| Google Drive / Docs MCP o connector | Disponibile via plugin Codex, non installato come skill locale terza | Solo se dobbiamo leggere template esistenti, Google Docs legacy o archivi Drive. Preferire DOCX diretto + Supabase Storage/S3 per il target finale. | Evitare nel runtime core. Se resta necessario, creare un tool Agno con scope minimo: upload/download file specifici, niente accesso Drive ampio. |
| Render MCP ufficiale | Da configurare solo quando si decide il deploy e si dispone di API key Render | Deployment assistito, creazione/lettura servizi, log, metriche, database Render Postgres/Key Value, diagnosi errori. L'API key Render e' ampia: usare solo con conferma umana per azioni operative. | Non usarlo dentro Agno runtime. Serve a Codex/sviluppatore per amministrare infrastruttura, non agli agenti DVR. |
| Vercel MCP ufficiale | Opzionale, da configurare solo se usiamo Vercel per frontend/preview | Gestione progetti/deploy/log Vercel con OAuth. Utile per dashboard/landing/preview web, non come target primario AgentOS. | Non usarlo dentro Agno runtime. Eventuali frontend chiamano API backend, non MCP Vercel. |

## Skills locali installate nel progetto

Queste skill sono installate in `.agents/skills` e saranno caricate dopo riavvio Codex.

| Skill | Uso nel progetto | Uso da Agno |
|---|---|---|
| `ctsafe-dvr-domain` | Fonte canonica di dominio DVR: struttura documento, regole RAG, template DOCX, checklist QA e uso da parte degli agenti Agno. | Base per prompt versionati, checklist di `SectionQAAgent`/`DocumentQAAgent`, policy di `RagSearchTool` e vincoli di `DocxRenderAgent`. |
| `ctsafe-agno-memory-evolution` | Progettazione memoria persistente e auto-miglioramento controllato ispirato a Hermes: learning proposals, eval dataset DVR, versioning e approval gates. | Base per `MemoryCuratorAgent`, `LearningProposalAgent`, `EvalRunnerAgent`, `ApprovalCoordinatorAgent` e `VersionRegistryAgent`. Nessun cambio diretto in produzione senza approvazione umana. |
| `ctsafe-agno-ops-gateway` | Progettazione del sistema operativo attorno ad Agno ispirato a OpenClaw: gateway canali, autorizzazioni, comandi, routing agenti, sessioni isolate, tool policy, doctor/audit, dashboard e provider bridge OpenAI subscription. | Base per `ChannelGateway`, `AuthGate`, `CommandRouter`, `SessionManager`, `AgentRouter`, `DvrDoctorAgent` e `LlmProviderRouter`. Il bridge subscription e' opzionale single-tenant e tracciato. |
| `supabase` | Tutte le attività Supabase: schema, RLS, Storage, pgvector, funzioni SQL, sicurezza, CLI. | Tradurre le decisioni in repository/tool Python con service role solo lato backend. |
| `supabase-postgres-best-practices` | Performance Postgres, indici, query, RLS, schema design, connessioni. | Applicare a tabelle operative, `rag_chunks`, indici vector/hybrid e policy. |
| `rag-implementation` | Progettazione pipeline RAG: chunking, metadata, retrieval, reranking, valutazione, grounding. | Implementare `RagRetrievalAgent` e tool `search_normativa`, `search_indice`, `search_dvr_pregressi`, poi `search_rag_chunks`. |
| `ai-prompt-engineering-safety-review` | Revisione di prompt, istruzioni agente, policy di sicurezza e robustezza contro output non controllati. | Applicare a system prompt, istruzioni agenti Agno, prompt RAG, checklist anti-allucinazione e prompt di revisione DVR. |
| `prompt-engineering-patterns` | Progettazione di prompt production-grade: template, few-shot, structured output, fallback, versioning, test e metriche. Installata con assessment `Safe`, `0 alerts`, `Low Risk`. | Usare per prompt versionati di `IntakeAgent`, `IndexAgent`, `SectionWriterAgent`, `DocumentQAAgent` e per output Pydantic/JSON affidabili. |
| `systematic-debugging` | Debug metodico di bug backend, tool Agno, workflow, retrieval, rendering DOCX e integrazioni. | Usare per isolare cause, riprodurre errori, aggiungere logging mirato e verificare fix con test o comandi ripetibili. |
| `docx` | Generazione e manipolazione DOCX modificabili, template, sezioni, tabelle. | Agno deve chiamare `DocxRenderTool`, non manipolare file in modo libero. Output versionato in storage. |
| `fastapi-python` | Backend AgentOS/FastAPI, webhook Telegram, API interne, sicurezza endpoint. | Agno gira dentro AgentOS/FastAPI; gli endpoint devono chiamare workflow Agno tipizzati. |
| `n8n-expression-syntax` | Interpretare espressioni n8n nei workflow JSON legacy. | Solo fase migrazione. Non serve nel runtime finale. |
| `n8n-validation-expert` | Capire errori/struttura dei workflow n8n importati. | Solo fase migrazione. Non serve nel runtime finale. |
| `llm-wiki` | Riferimento al pattern LLM Wiki/Karpathy e alle regole per mantenere una wiki Markdown curata dagli agenti. | Non usarla come dipendenza runtime. Agno puo' consultare solo export/pagine curate tramite tool read-only, se approvato. |
| `wiki-setup` | Inizializzare una vault/wiki di sviluppo separata per il progetto, senza segreti e senza dati cliente. | Non usare in runtime. La wiki e' memoria di sviluppo, non fonte normativa primaria. |
| `wiki-ingest` / `obsidian-wiki-ingest` | Ingerire guide, decisioni, note tecniche, mapping legacy e lezioni apprese nella wiki di progetto. Usare solo su fonti non sensibili o gia' sanificate. | Non usare direttamente. Eventuali contenuti utili ad Agno devono essere promossi a documentazione/versione controllata o a Supabase RAG curato. |
| `wiki-capture` / `wiki-quick-chat-capture` | Salvare decisioni importanti emerse durante lo sviluppo in note strutturate. | Non usare in runtime. Utile solo per memoria del team e continuita' Codex. |
| `wiki-lint`, `cross-linker`, `tag-taxonomy`, `wiki-dedup`, `wiki-synthesize`, `wiki-export` | Mantenere pulita la wiki: link, tag, duplicati, sintesi, export grafo. | Solo indiretto: Agno puo' leggere export curati, mai eseguire manutenzione libera della wiki. |
| `obsidian-markdown`, `obsidian-bases`, `json-canvas` | Migliorare formato Obsidian: markdown, basi viste/database e canvas. | Non usare in runtime. Servono per documentazione e navigazione durante sviluppo. |

## Skills/plugin Codex da usare senza installazione locale

Queste sono già disponibili nell'ambiente Codex o nei plugin installati. Non vanno reinstallate da pacchetti terzi se non necessario.

| Skill/plugin | Uso consigliato |
|---|---|
| `documents:documents` | Creare, modificare e verificare DOCX/Word quando serve un workflow documentale robusto. |
| `google-drive:google-drive` | Cercare, leggere, esportare o organizzare file Drive legacy. |
| `google-drive:google-docs` | Lavorare su Google Docs legacy se il flusso attuale lo richiede. |
| `google-drive:google-sheets` | Usare solo se servono tabelle/fogli Google per export, mapping o audit. |
| `n8n-workflow-patterns` | Capire architettura dei workflow n8n esistenti e mappare nodi verso Agno. |
| `n8n-code-javascript` | Interpretare i Code node JavaScript dei workflow n8n legacy. |
| `openai-docs` | Verificare modelli, API, embeddings e best practice OpenAI aggiornate. |
| `software-architecture` | Decisioni architetturali, separazione Clean Architecture/DDD, confini tra agenti, tool e repository. |

## Skills rimosse o da evitare

| Skill locale rimossa | Motivo | Alternativa |
|---|---|---|
| `n8n-workflow-patterns` da `czlonkowski/n8n-skills` | Il CLI l'ha segnalata come `Critical Risk`. | Usare la skill/plugin già disponibile in Codex con lo stesso scopo, senza copia locale terza. |
| `google-drive` da `membranedev/application-skills` | Il CLI ha segnalato alert di sicurezza. | Usare il plugin ufficiale Google Drive di Codex. |
| `google-docs` e `google-sheets` da pacchetto terzo | Rimosse per prudenza, visto che esistono alternative plugin già disponibili. | Usare `google-drive:google-docs` e `google-drive:google-sheets`. |
| `n8n-code-javascript` locale terza | Rimosso per prudenza. | Usare la skill già disponibile in Codex. |
| `daily-update`, `data-ingest`, `ingest-url`, `wiki-agent`, `wiki-query`, `wiki-research` da `Ar9av/obsidian-wiki` | Rimosse dopo installazione perche' il CLI le ha segnalate con rischio High/Critical. | Usare solo le skill Obsidian rimaste, preferendo ingest da file locali sanificati e query tramite lettura manuale/grep quando serve. |
| `defuddle`, `obsidian-cli` da `kepano/obsidian-skills` | Rimosse per prudenza: erano a rischio medio e non sono indispensabili ora. | Per web/article cleanup usare ricerca controllata o strumenti gia' disponibili; per Obsidian limitarsi a file Markdown/Canvas/Bases. |

## Come usare gli strumenti per realizzare il progetto

1. Analisi legacy
   - Usare Airtable MCP per leggere struttura e record esistenti.
   - Usare le skill n8n per mappare i workflow JSON verso moduli Agno.
   - Output atteso: mapping `n8n -> Agno`, schema dati target, lista campi Airtable da migrare.

2. Bonifica Supabase/RAG
   - Usare Supabase MCP Toolbox per ispezionare DB live e testare SQL.
   - Usare `supabase`, `supabase-postgres-best-practices` e `rag-implementation`.
   - Output atteso: funzioni `match_*` corrette, RLS/grant sicuri, tabella target `rag_chunks`, metadata semantici.

3. Prompt e AI engineering
   - Usare `prompt-engineering-patterns`, `ai-prompt-engineering-safety-review`, `openai-docs`, `software-architecture` e `rag-implementation`.
   - Definire prompt versionati per intake, indice, redazione capitoli, revisione, citazioni e controllo qualita'.
   - Applicare structured output/Pydantic, fallback se il RAG non basta, template riutilizzabili e metriche di qualita' per ogni agente.
   - Output atteso: prompt robusti, istruzioni Agno testabili, criteri di grounding, valutazioni ripetibili e versioning prompt-as-code.

4. Memoria persistente e auto-miglioramento controllato
   - Usare `ctsafe-agno-memory-evolution` per progettare memoria sessione/progetto/utente, QA memory, learning proposals, eval dataset e version registry.
   - L'agente puo' osservare, memorizzare, valutare e proporre miglioramenti; non puo' cambiare direttamente prompt, RAG policy, template, checklist, tool permissions o comportamento production.
   - Ogni proposta deve avere evidenze, rischio, piano eval, stato di approvazione e collegamento alla versione eventualmente rilasciata.
   - Output atteso: schema Supabase, tool Agno tipizzati, eval cases DVR, workflow di approvazione e audit trail.

5. Ops gateway, canali e provider LLM
   - Usare `ctsafe-agno-ops-gateway` per progettare Telegram/WhatsApp/web gateway, autorizzazioni, comandi operatore, routing agenti, sessioni isolate, tool policy e doctor/audit.
   - Normalizzare ogni evento canale prima di invocare Agno: `ChannelAdapter -> AuthGate -> CommandRouter -> SessionManager -> AgentRouter`.
   - Prevedere provider LLM intercambiabili: `openrouter`, `openai_api`, `openai_subscription_bridge` e `local_mock`.
   - Il bridge OpenAI subscription e' ammesso solo come provider opzionale single-tenant, con health check, riconnessione esplicita, fallback configurato e tracciamento nel DVR.
   - Output atteso: schemi eventi/comandi, matrice permessi, lista comandi, routing map, provider interface e diagnostica `/doctor`.

6. Memoria di sviluppo LLM Wiki / Obsidian
   - Usare `wiki-setup` per preparare una vault separata del progetto, senza `.env`, chiavi, dati cliente, PII o documenti DVR reali non anonimizzati.
   - Usare `wiki-ingest`/`obsidian-wiki-ingest` per guide, mapping architetturali, decisioni tecniche, checklist e analisi legacy.
   - Usare `wiki-lint`, `cross-linker`, `tag-taxonomy` e `wiki-export` per mantenere la wiki navigabile e verificabile.
   - Output atteso: memoria tecnica consultabile da Codex durante lo sviluppo, non una fonte runtime per generare DVR.

7. Backend Agno/FastAPI
   - Usare `fastapi-python` e `software-architecture`.
   - Implementare AgentOS/FastAPI con webhook Telegram, API project/document, workflow Agno.
   - Output atteso: servizio deployabile su Render con configurazione env sicura.

8. Deployment e infrastruttura
   - Target primario: Render per backend AgentOS/FastAPI, perche' Agno e' un servizio FastAPI con Postgres, HTTPS, hostname pubblico, health check e env vars.
   - Target secondario/opzionale: Vercel per frontend, dashboard, landing o preview web. Non usarlo come prima scelta per il runtime AgentOS/DVR.
   - Configurare Render MCP ufficiale solo quando abbiamo API key e progetto Render pronto. Ogni azione che crea/modifica servizi, database o env vars richiede conferma umana.
   - Non installare per ora skill `render-deploy` terze: alcune candidate risultano con audit non puliti. Preferire documentazione ufficiale Render, MCP ufficiale e configurazione esplicita.
   - Output atteso: `Dockerfile`/start command, env vars documentate, health check `/health`, deploy Render ripetibile e rollback/log consultabili.

9. Generazione DVR
   - Usare `docx` e, se necessario, `documents:documents`.
   - Eliminare Google Apps Script come componente core.
   - Output atteso: `DVR_v1.docx`, `DVR_v2.docx`, ecc. versionati in storage.

10. Debug e hardening
   - Usare `systematic-debugging` quando un flusso non funziona o quando una generazione produce output incoerente.
   - Prima riprodurre l'errore, poi isolare il componente, poi applicare il fix minimo e verificarlo.
   - Output atteso: bug report ripetibile, causa radice, test o comando di verifica.

11. Google legacy
   - Usare plugin Google Drive/Docs solo per import/export o recupero documenti storici.
   - Non far dipendere il runtime core da Google Drive se il target e' DOCX diretto.

## Come deve usarli l'agente Agno

Agno deve usare tool applicativi piccoli, non server MCP ampi:

| Agente Agno | Tool consigliati | Note |
|---|---|---|
| `IntakeAgent` | `TelegramTool`, `ProjectRepository`, `AirtableLegacyReader` temporaneo | Raccoglie dati azienda e crea progetto. |
| `IndexAgent` | `RagSearchTool`, `IndexRepository`, `RiskClassifierTool` | Genera indice DVR e rischi principali. |
| `SectionWriterAgent` | `RagSearchTool`, `SectionRepository`, `NormativeCitationTool` | Scrive capitoli con grounding normativo. |
| `RevisionAgent` | `DocumentPatchTool`, `SectionRepository`, `QualityChecklistTool` | Applica modifiche utente e controlli qualità. |
| `DocxRenderAgent` | `DocxRenderTool`, `StorageTool`, `DocumentVersionRepository` | Crea DOCX modificabile e versionato. |
| `AuditAgent` | `RagAuditTool`, `CitationVerifierTool`, `SupabaseReadOnlyDiagnosticsTool` | Controlla fonti, duplicati, lacune, sicurezza. |
| `MemoryCuratorAgent` | `MemoryReadTool`, `MemoryWriteTool`, `ProjectRepository` | Scrive solo memorie con scope chiaro: sessione, progetto, utente o organizzazione. Non promuove riflessioni a fatti senza evidenza. |
| `LearningProposalAgent` | `LearningProposalCreateTool`, `QAFindingRepository`, `ReviewEventRepository` | Crea proposte di miglioramento, non modifica prompt/template/checklist/RAG policy. |
| `EvalRunnerAgent` | `EvalRunTool`, `EvalDatasetRepository`, `VersionRegistryReadTool` | Testa proposte su casi DVR e segnala regressioni prima della review umana. |
| `ApprovalCoordinatorAgent` | `ApprovalRequestTool`, `ApprovalRepository` | Prepara pacchetti di approvazione umana con evidenze, diff, rischi, eval e rollback. |
| `VersionRegistryAgent` | `VersionRegisterTool`, `ArtifactRepository` | Attiva nuove versioni solo dopo approval event valido. |
| `ChannelGateway` | `TelegramAdapter`, futuro `WhatsAppAdapter`, futuro `WebAdapter` | Normalizza eventi canale in input interni tipizzati prima di qualunque chiamata agli agenti. |
| `AuthGate` | `UserAllowlistRepository`, `OrgMembershipRepository`, `RolePolicyTool` | Blocca utenti/chat non autorizzati e applica ruoli prima del routing. |
| `CommandRouter` | `CommandParser`, `WorkflowDispatcher` | Instrada `/nuovo_dvr`, `/stato_dvr`, `/mancanti`, `/fonti`, `/revisioni`, `/approva`, `/blocca`, `/doctor`, `/provider`. |
| `SessionManager` | `SessionRepository`, `ProjectContextResolver` | Isola sessioni per organizzazione, utente, progetto, documento e canale. |
| `DvrDoctorAgent` | `ReadOnlyDiagnosticsTool`, `ProviderHealthTool`, `RagHealthTool`, `TemplateHealthTool` | Diagnostica read-only di sistema, RAG, template, prompt version, provider, webhook e deploy. |
| `LlmProviderRouter` | `OpenRouterProvider`, `OpenAIAPIProvider`, `OpenAISubscriptionBridgeProvider`, `LocalMockProvider` | Seleziona il provider LLM configurato. Registra provider e modello usato in ogni run/DVR. |

Regole runtime:

- Agno puo' esporre agenti e workflow via AgentOS MCP.
- Agno non deve ricevere accesso libero a Supabase MCP Toolbox, Airtable MCP o Google Drive.
- Ogni tool Agno deve avere permessi minimi, input/output Pydantic e logging.
- Le chiavi `service_role` restano solo lato backend.
- Il client Telegram non deve mai accedere direttamente a Supabase con privilegi elevati.
- Le skill sono istruzioni di sviluppo per Codex; non sono una dipendenza runtime dell'applicazione.
- La wiki Obsidian/LLM Wiki e' memoria di sviluppo. Agno puo' leggerne solo contenuti esportati, curati e non sensibili tramite tool read-only esplicito, non la vault completa.
- Il deployment backend preferito e' Render. Vercel resta consigliato per eventuale frontend o preview, non per il core AgentOS se sono necessari processi lunghi, webhook affidabili, generazione DOCX e operazioni RAG articolate.
- Render MCP e Vercel MCP sono strumenti amministrativi per Codex/sviluppatore: non devono essere invocati dagli agenti DVR e non devono ricevere segreti nel prompt. Le modifiche infrastrutturali richiedono conferma umana.
- L'auto-miglioramento in stile Hermes e' ammesso solo come loop controllato: osservazione, learning proposal, eval, approvazione umana, nuova versione, monitoraggio. Nessun agente puo' auto-modificare prompt, skill, template, policy RAG, permessi tool o comportamento production.
- I pattern OpenClaw sono usati per l'ops gateway, non per sostituire Agno: canali, auth, comandi, sessioni, routing, tool policy, doctor e UX di controllo restano layer attorno agli agenti DVR.
- Il bridge OpenAI subscription puo' essere usato solo come provider opzionale single-tenant del cliente. Non va condiviso tra clienti, non deve salvare token/cookie nei prompt/log/memorie/wiki, deve avere health check e fallback esplicito, e ogni DVR deve registrare quale provider ha generato i contenuti.

# Mappatura Airtable - Base "Documenti CT Safe"

## Scopo del documento

Questo documento descrive la struttura delle due tabelle Airtable:

- `Progetti DVR` (`tbl2GOhTrhaE032us`)
- `Capitoli DVR` (`tbl0zmvKGN4ms5ApU`)

L'obiettivo e' chiarire:

- quali colonne esistono
- che tipo di dato contengono
- se sono obbligatorie o opzionali
- chi le compila
- a cosa servono nel workflow

## Nota importante sull'obbligatorieta'

La metadata API di Airtable letta per questa base non espone un flag affidabile di "campo obbligatorio" nel senso di validazione UI/form.

Per questo motivo, in questo documento l'obbligatorieta' e' classificata in modo operativo:

- `Operativamente obbligatorio`: il workflow ha senso solo se il campo e' valorizzato
- `Automatico / derivato`: il campo viene popolato da automazioni, AI o webhook
- `Opzionale / supporto`: utile ma non strettamente necessario per far avanzare il flusso

Dove necessario, la classificazione e' una inferenza basata su:

- schema Airtable
- valori reali presenti nei record campione
- presenza di bottoni webhook
- relazione logica tra tabella progetto e tabella capitoli

---

## Vista d'insieme del workflow

La base e' organizzata come una pipeline per generare un DVR.

### Tabella 1: `Progetti DVR`

Contiene il progetto principale:

- anagrafica azienda
- contesto rischio
- indice DVR
- stato di avanzamento
- trigger delle automazioni
- link al documento finale

### Tabella 2: `Capitoli DVR`

Contiene i singoli capitoli del DVR:

- riferimento al progetto
- numero e titolo del capitolo
- brief di scrittura
- stato del capitolo
- contenuto generato

### Sequenza del processo

1. Si crea un record in `Progetti DVR`
2. Si inseriscono i dati aziendali di base
3. Viene generato o incollato un primo `INDICE DVR`
4. Il bottone `VALIDA INDICE` lancia una validazione via webhook
5. Il sistema scrive `INDICE DVR VALIDATO`, `Log Validazione` e aggiorna `Stato DVR`
6. Vengono creati o popolati i record nella tabella `Capitoli DVR`
7. Il bottone `REDIGI DVR` avvia la redazione dei capitoli
8. Ogni capitolo viene popolato in `Contenuto Generato`
9. Il bottone `CREA DOC DVR` genera il documento finale
10. Il link finale viene salvato in `Link DVR Google Drive`

---

## Tabella: `Progetti DVR`

**ID tabella:** `tbl2GOhTrhaE032us`  
**Campo primario:** `Ragione Sociale`

Questa tabella rappresenta l'unita' principale del workflow: un progetto DVR per una singola azienda.

| Campo | Tipo Airtable | Obbligatorieta' operativa | Chi lo compila | Dati contenuti | Ruolo nel workflow |
|---|---|---|---|---|---|
| `Ragione Sociale` | `singleLineText` | Operativamente obbligatorio | Utente / operatore | Nome dell'azienda, es. `DMM SRL` | Identifica il progetto ed e' il principale riferimento leggibile |
| `Partita IVA` | `singleLineText` | Operativamente obbligatorio | Utente / operatore | P.IVA aziendale | Serve alla corretta anagrafica del DVR |
| `Codice ATECO` | `singleLineText` | Operativamente obbligatorio | Utente / operatore | Codice ATECO con eventuale descrizione | Determina il settore e aiuta la classificazione rischio |
| `Descrizione Attivita'` | `multilineText` | Operativamente obbligatorio | Utente / operatore | Descrizione libera dell'attivita' aziendale | Fornisce contesto alla generazione dell'indice e dei capitoli |
| `N° Dipendenti` | `number` | Operativamente obbligatorio | Utente / operatore | Numero intero di addetti | Influenza contenuti del DVR, obblighi e dimensionamento |
| `Mansioni` | `multilineText` | Operativamente obbligatorio | Utente / operatore | Elenco delle mansioni aziendali | Base per valutazione rischi per mansione |
| `Indirizzo Sede` | `singleLineText` | Operativamente obbligatorio | Utente / operatore | Sede legale e/o operativa | Inserito nel documento e usato nel contesto del sopralluogo |
| `Tipo Documento` | `singleLineText` | Operativamente obbligatorio | Utente / operatore | Tipo pratica, es. `DVR Nuovo` | Distingue il caso d'uso del record |
| `Categoria Rischio` | `singleLineText` | Operativamente obbligatorio | Utente / operatore oppure derivato da analisi | Valore come `MEDIO`, `ALTO`, ecc. | Guida la redazione del DVR e gli obblighi correlati |
| `Pericoli Settore` | `multilineText` | Operativamente obbligatorio | Utente esperto, AI o automazione | Elenco dei pericoli tipici del settore | Alimenta indice, capitoli e contenuti tecnici |
| `Rischi per Mansione` | `multilineText` | Operativamente obbligatorio | Utente esperto, AI o automazione | Associazione mansione -> rischi | Serve alla parte di valutazione analitica |
| `Normativa Riferimento` | `multilineText` | Operativamente obbligatorio | Utente esperto, AI o automazione | Elenco norme applicabili | Fornisce base normativa ai capitoli |
| `Data creazione` | `date` | Opzionale / supporto | Utente o automazione | Data di apertura progetto | Supporta tracciamento cronologico |
| `INDICE DVR` | `multilineText` | Operativamente obbligatorio prima della validazione | AI, automazione o operatore | Bozza estesa dell'indice del DVR | Input principale della fase di validazione |
| `VALIDA INDICE` | `button` | Automatico / derivato | Configurazione Airtable + n8n | Bottone con URL webhook | Avvia la validazione dell'indice |
| `INDICE DVR VALIDATO` | `multilineText` | Automatico / derivato | Automazione / AI | Indice corretto, completato o normalizzato | Output ufficiale della validazione |
| `REDIGI DVR` | `button` | Automatico / derivato | Configurazione Airtable + n8n | Bottone con URL webhook | Avvia la generazione dei capitoli |
| `Stato DVR` | `singleSelect` | Operativamente obbligatorio | Automazione e/o operatore | Stato del progetto | Governa la pipeline e indica a che punto e' il DVR |
| `CREA DOC DVR` | `button` | Automatico / derivato | Configurazione Airtable + n8n | Bottone con URL webhook | Avvia la generazione del documento finale |
| `Link DVR Google Drive` | `url` | Automatico / derivato | Automazione | URL del documento finale | Output finale consultabile o consegnabile |
| `Log Validazione` | `singleLineText` | Opzionale / supporto | Automazione | Log JSON o testo tecnico | Diagnostica della validazione e audit tecnico |

### Valori osservati per `Stato DVR`

Le scelte configurate nel campo sono:

- `In validazione`
- `Indice validato`
- `In redazione`
- `Redazione fatta - crea documento`
- `DVR in creazione`
- `DVR Creato`
- `Errore`

### Lettura funzionale dei campi in `Progetti DVR`

#### 1. Campi anagrafici e di contesto

Questi campi descrivono l'azienda e sono il nucleo minimo richiesto per far funzionare il progetto:

- `Ragione Sociale`
- `Partita IVA`
- `Codice ATECO`
- `Descrizione Attivita'`
- `N° Dipendenti`
- `Mansioni`
- `Indirizzo Sede`
- `Tipo Documento`
- `Categoria Rischio`

#### 2. Campi tecnico-redazionali

Questi campi preparano o contengono la materia del DVR:

- `Pericoli Settore`
- `Rischi per Mansione`
- `Normativa Riferimento`
- `INDICE DVR`
- `INDICE DVR VALIDATO`

#### 3. Campi di orchestrazione workflow

Questi campi attivano o segnalano passaggi di processo:

- `VALIDA INDICE`
- `REDIGI DVR`
- `CREA DOC DVR`
- `Stato DVR`

#### 4. Campi di output e diagnostica

- `Link DVR Google Drive`
- `Log Validazione`
- `Data creazione`

---

## Tabella: `Capitoli DVR`

**ID tabella:** `tbl0zmvKGN4ms5ApU`  
**Campo primario:** `Progetto DVR`

Questa tabella rappresenta l'esplosione del progetto in capitoli.

| Campo | Tipo Airtable | Obbligatorieta' operativa | Chi lo compila | Dati contenuti | Ruolo nel workflow |
|---|---|---|---|---|---|
| `Progetto DVR` | `singleLineText` | Operativamente obbligatorio | Automazione o operatore | Riferimento al progetto, es. `recl... - DMM SRL` | Collega il capitolo al progetto padre |
| `Numero Capitolo` | `singleLineText` | Operativamente obbligatorio | Automazione o operatore | Numero o codice capitolo, es. `1.1`, `3.5`, `A12` | Identifica la posizione logica del capitolo |
| `Titolo Capitolo` | `singleLineText` | Operativamente obbligatorio | Automazione o operatore | Titolo descrittivo del capitolo | Rende leggibile la struttura del DVR |
| `Brief` | `multilineText` | Operativamente obbligatorio per generazione AI | Automazione / AI / operatore esperto | Prompt o JSON con obiettivo, contenuti richiesti, norme, note | Input principale per scrivere il capitolo |
| `Stato` | `singleSelect` | Operativamente obbligatorio | Automazione e/o operatore | Stato del singolo capitolo | Permette di tracciare avanzamento della redazione |
| `Ordine` | `singleLineText` | Operativamente obbligatorio | Automazione o operatore | Chiave di ordinamento, spesso uguale al numero capitolo | Serve per ricomporre l'ordine finale del documento |
| `Contenuto Generato` | `multilineText` | Automatico / derivato | AI / automazione | Testo completo del capitolo | Output della redazione |

### Valori osservati per `Stato`

Le scelte configurate nel campo sono:

- `Da redigere`
- `In corso`
- `Completato`

### Lettura funzionale dei campi in `Capitoli DVR`

#### 1. Identificazione del capitolo

- `Progetto DVR`
- `Numero Capitolo`
- `Titolo Capitolo`
- `Ordine`

Questi campi identificano il capitolo e permettono di capire dove andra' collocato.

#### 2. Input di scrittura

- `Brief`

E' il campo piu' importante per la generazione AI a livello capitolo. Nei record osservati contiene un JSON con:

- numero capitolo
- titolo
- obiettivo
- contenuto richiesto
- dati azienda da usare
- riferimenti normativi
- mansioni coinvolte
- lunghezza target
- note specifiche

#### 3. Tracking lavorazione

- `Stato`

Serve a capire se il capitolo e':

- da generare
- in lavorazione
- completato

#### 4. Output redazionale

- `Contenuto Generato`

Contiene il testo finale del capitolo, spesso gia' in forma molto vicina al documento consegnabile.

---

## Relazione tra le due tabelle

### Struttura logica

- `Progetti DVR` = entita' padre
- `Capitoli DVR` = entita' figlie

### Nota tecnica importante

Dal metadata letto, `Progetto DVR` nella tabella `Capitoli DVR` e' un campo `singleLineText`, non un `linkedRecord`.

Questo significa che il collegamento tra progetto e capitoli non sembra essere normalizzato come relazione nativa Airtable, ma memorizzato come testo leggibile.

### Implicazioni

- Pro: semplice da leggere anche fuori Airtable
- Contro: piu' fragile per join, coerenza e automazioni avanzate

Se in futuro questa base dovesse crescere, avrebbe senso valutare un vero `linked record` tra:

- `Progetti DVR`
- `Capitoli DVR`

---

## Campi minimi per il funzionamento del workflow

### Minimo necessario in `Progetti DVR`

Per far partire un progetto in modo sensato, dovrebbero essere valorizzati almeno:

- `Ragione Sociale`
- `Partita IVA`
- `Codice ATECO`
- `Descrizione Attivita'`
- `N° Dipendenti`
- `Mansioni`
- `Indirizzo Sede`
- `Tipo Documento`
- `Categoria Rischio`
- `Pericoli Settore`
- `Rischi per Mansione`
- `Normativa Riferimento`

Poi, per il workflow AI:

- `INDICE DVR`

### Minimo necessario in `Capitoli DVR`

Per poter generare un capitolo servono almeno:

- `Progetto DVR`
- `Numero Capitolo`
- `Titolo Capitolo`
- `Brief`
- `Stato`
- `Ordine`

L'output atteso e':

- `Contenuto Generato`

---

## Mappa sintetica dei compilatori

### Compilazione manuale da utente / operatore

Principalmente:

- dati aziendali
- dati di contesto
- eventuale primo testo o revisione

Campi tipici:

- `Ragione Sociale`
- `Partita IVA`
- `Codice ATECO`
- `Descrizione Attivita'`
- `N° Dipendenti`
- `Mansioni`
- `Indirizzo Sede`
- `Tipo Documento`
- `Categoria Rischio`

### Compilazione AI / automazione

Principalmente:

- contenuti tecnici
- validazioni
- capitoli generati
- output finali

Campi tipici:

- `Pericoli Settore`
- `Rischi per Mansione`
- `Normativa Riferimento`
- `INDICE DVR`
- `INDICE DVR VALIDATO`
- `Log Validazione`
- `Brief`
- `Contenuto Generato`
- `Link DVR Google Drive`

### Campi ibridi

Campi che possono essere inizializzati manualmente e poi aggiornati da automazioni:

- `Stato DVR`
- `Stato`
- `Data creazione`

---

## Conclusione

La base `Documenti CT Safe` e' strutturata come un sistema di produzione documentale guidato da workflow:

- la tabella `Progetti DVR` governa il progetto complessivo
- la tabella `Capitoli DVR` governa la produzione puntuale dei contenuti

Il modello e' coerente con un flusso:

- input aziendale
- generazione indice
- validazione indice
- generazione capitoli
- assemblaggio documento finale

Il punto piu' delicato, dal lato modellazione dati, e' che il legame progetto-capitoli sembra essere testuale e non relazionale nativo.

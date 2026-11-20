# Connettore Plus 2000 <-> Google Sheets (OrderSender)

Questo connettore autonomo sincronizza in modo automatico e bidirezionale le **Offerte** e gli **Ordini** registrati dagli agenti su Google Drive verso il database **Microsoft SQL Server di Plus 2000**, utilizzando le Stored Procedure native del gestionale.

---

## 📁 Struttura della cartella

* `config.json`: File di configurazione per i parametri di connessione SQL Server e Google Sheets.
* `test_connessione_sql.py`: Script diagnostico per verificare in 2 secondi che la connessione a SQL Server funzioni e che le tabelle/stored procedure di Plus 2000 siano presenti.
* `connettore.py`: Il motore di sincronizzazione continuo.
* `service_account.json`: Il file delle credenziali Google Cloud Service Account (da posizionare qui).

---

## 🚀 Istruzioni di Configurazione

### 1. Configurare SQL Server (`config.json`)
Apri `config.json` e imposta:
* `server`: il nome dell'istanza SQL Server (es. `localhost`, `SERVER\SQLEXPRESS`, o indirizzo IP locale).
* `database`: il nome del database aziendale di Plus 2000 (es. `Plus_Azi`, `KFL`, ecc.).
* `trusted_connection`: imposta `"yes"` se usi l'autenticazione Windows, oppure `"no"` specificando `username` e `password` (es. utente `sa`).

### 2. Configurare Google Sheets
1. Nel file `config.json`, verifica che `spreadsheet_id` corrisponda al tuo foglio:
   `"spreadsheet_id": "1Q7E8BnydYf334O_kc6zqmQsdmuBpqM6hXuS1P23oWfM"`
2. Assicurati di condividere il foglio Google Drive con l'indirizzo email del tuo **Google Service Account** dandogli i permessi di **Editor**.
3. Posiziona il file scaricato da Google Cloud rinominandolo `service_account.json` dentro questa cartella.

---

## 🧪 Verifica e Test

Prima di avviare il connettore continuo, esegui il test di verifica SQL:

```cmd
python test_connessione_sql.py
```

Se la configurazione è corretta, riceverai conferma che:
* La connessione a SQL Server è riuscita.
* Le tabelle `DocTes`, `DocRig`, `Articoli`, `CliFor` sono presenti.
* Le Stored Procedure (`sp_Sequenze_Ricerca`, `sp_Sequenze_Aggiorna`, `sp_DocTes_SetDefault`, `sp_DocRig_SetDefault`, `sp_Doc_Aggiorna_Totali`, `sp_Doc_Conferma`) sono operative.

---

## 🔄 Avvio del Connettore

Per avviare la sincronizzazione automatica:

```cmd
python connettore.py
```

Il connettore:
1. Legge periodicamente (ogni 60 secondi di default) la scheda **`DocTes`** cercando record con `StatoSync = 'DA_SINCRONIZZARE'`.
2. Recupera le righe collegate dalla scheda **`DocRig`**.
3. Esegue la sequenza transazionale nativa su SQL Server:
   - Trova e avanza il numeratore ufficiale documento (`sp_Sequenze_Aggiorna`).
   - Inserisce la testata (`DocTes`) e applica i default del cliente (`sp_DocTes_SetDefault`).
   - Inserisce ogni riga articolo (`DocRig`) e calcola sconti e prezzi (`sp_DocRig_SetDefault`).
   - Ricalcola totali e IVA (`sp_Doc_Aggiorna_Totali`) e conferma il documento (`sp_Doc_Conferma`).
4. Aggiorna istantaneamente il foglio Google Drive impostando:
   - `StatoSync`: **`SINCRONIZZATO`**
   - `DataSync`: Data e ora dell'inserimento
   - `DocId_Plus`: L'ID univoco interno di Plus
   - `NumeroDoc_Plus`: Il numero ufficiale di ordine/offerta assegnato da Plus

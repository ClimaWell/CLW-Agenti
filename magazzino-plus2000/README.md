# Modulo Magazzino & Inventario Plus2000 (Climawell)

Applicazione web Intranet progettata per i dispositivi dei magazzinieri (smartphone, tablet, pistole barcode Android/Bluetooth o PC) all'interno della rete aziendale di Climawell.

---

## 🚀 Come Avviare l'Applicazione

Puoi avviare il server in due modi:
1. **Con doppio click:** apri il file `avvia_magazzino.bat` presente nella cartella principale di `plus-2026`.
2. **Da terminale:**
   ```powershell
   cd magazzino-plus2000
   python app.py
   ```

Il server mostrerà gli indirizzi IP locali a cui connettersi, ad esempio:
- Da questo PC: `http://localhost:5000`
- Da smartphone/tablet in Wi-Fi: `http://192.168.x.x:5000`

---

## 📱 Funzionalità Chiave

1. **Scansione Articolo:**
   - Tramite **Pistola Barcode** (lettura istantanea automatica premendo Enter).
   - Tramite **Fotocamera del dispositivo** cliccando sul tasto `📷 Fotocamera`.
   - Tramite ricerca manuale (per codice, descrizione o codice fornitore).

2. **Dati in Tempo Reale da Plus:**
   - **Giacenza Plus:** letta direttamente da `ArticoliContGen.TotEsi`.
   - **Ubicazione attuale:** letta da `Articoli.JUbiArt`.
   - **Unità di Misura:** `NR`, `PZ`, `MT`, ecc.

3. **Verifica & Modifica Ubicazione Scaffale:**
   - Mostra l'ubicazione memorizzata nel gestionale.
   - Permette di scansionare con la fotocamera o pistola il **codice a barre dello scaffale** per correggere al volo la posizione.
   - Con il flag attivo, aggiorna immediatamente anche l'anagrafica articolo su Plus (`UPDATE Articoli SET JUbiArt = ?`).

4. **Conteggio & Differenza:**
   - Tastierino rapido: pulsanti `+1`, `+5`, `+10`, `+50`, `Uguaglia Giacenza` e tasti steppers.
   - Badge scostamento dinamico: calcola all'istante l'eccedenza (+), l'ammanco (-) o la perfetta coincidenza (0).

5. **Scrittura su `WinCeInv`:**
   - Al click su `REGISTRA INVENTARIO`, inserisce il record nella tabella nativa di Plus `WinCeInv` con il nuovo `RegId`, data, ora, terminale, codice articolo, ubicazione e quantità rilevata.
   - Da Plus2000, l'ufficio o il magazziniere può quindi lanciare la normale procedura di generazione rettifiche per creare il movimento di magazzino.

6. **Feedback Sonoro:**
   - Beep ad alta frequenza al riconoscimento del barcode.
   - Tono armonico al salvataggio su database.
   - Tono basso in caso di codice inesistente o errore.

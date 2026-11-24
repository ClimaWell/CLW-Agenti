import json
import os
import sys
import time
import datetime
import requests
import pyodbc

# Libreria crypto standard o fallback per JWT Service Account
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
import base64

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

class GoogleSheetsClient:
    def __init__(self, sa_file_path):
        if not os.path.isabs(sa_file_path):
            sa_file_path = os.path.join(BASE_DIR, sa_file_path)
        self.sa_file_path = sa_file_path
        self.token = None
        self.token_expiry = 0

    def _get_access_token(self):
        if self.token and time.time() < (self.token_expiry - 60):
            return self.token

        if not os.path.exists(self.sa_file_path):
            raise FileNotFoundError(
                f"File credenziali Service Account non trovato: '{self.sa_file_path}'. "
                "Copia il file JSON delle credenziali Google Cloud in questa cartella."
            )

        with open(self.sa_file_path, "r", encoding="utf-8") as f:
            sa_info = json.load(f)

        now = int(time.time())
        header = {"alg": "RS256", "typ": "JWT"}
        payload = {
            "iss": sa_info["client_email"],
            "scope": "https://www.googleapis.com/auth/spreadsheets",
            "aud": "https://oauth2.googleapis.com/token",
            "iat": now,
            "exp": now + 3600
        }

        def b64url(data_bytes):
            return base64.urlsafe_b64encode(data_bytes).decode('utf-8').rstrip('=')

        header_b64 = b64url(json.dumps(header).encode('utf-8'))
        payload_b64 = b64url(json.dumps(payload).encode('utf-8'))
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')

        private_key = load_pem_private_key(sa_info["private_key"].encode('utf-8'), password=None)
        signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        signature_b64 = b64url(signature)

        jwt_token = f"{header_b64}.{payload_b64}.{signature_b64}"

        resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt_token
            },
            timeout=10
        )
        data = resp.json()
        if "access_token" not in data:
            raise RuntimeError(f"Errore autenticazione Google: {data.get('error_description', data)}")

        self.token = data["access_token"]
        self.token_expiry = now + data.get("expires_in", 3600)
        return self.token

    def read_range(self, spreadsheet_id, sheet_range, unformatted=False):
        token = self._get_access_token()
        opt = "?valueRenderOption=UNFORMATTED_VALUE" if unformatted else ""
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{sheet_range}{opt}"
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
        if resp.status_code != 200:
            raise RuntimeError(f"Errore lettura foglio {sheet_range}: {resp.text}")
        return resp.json().get("values", [])


    def update_range(self, spreadsheet_id, sheet_range, values):
        token = self._get_access_token()
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{sheet_range}?valueInputOption=USER_ENTERED"
        resp = requests.put(url, headers={"Authorization": f"Bearer {token}"}, json={"values": values}, timeout=15)
        if resp.status_code != 200:
            raise RuntimeError(f"Errore aggiornamento foglio {sheet_range}: {resp.text}")
        return resp.json()


class Plus2000Connector:
    def __init__(self, cfg):
        self.cfg = cfg
        self.sql_cfg = cfg["sql_server"]
        self.sheets_cfg = cfg["google_sheets"]
        self.sheets_client = GoogleSheetsClient(self.sheets_cfg.get("service_account_file", "service_account.json"))

    def get_sql_connection(self):
        c = self.sql_cfg
        dsn = c.get("dsn")
        if dsn:
            try:
                return pyodbc.connect(f"DSN={dsn};", autocommit=False, timeout=10)
            except Exception as e:
                print(f"[Avviso DSN]: {e}, fallback su connessione diretta...")

        conn_str = f"DRIVER={{{c['driver']}}};SERVER={c['server']};DATABASE={c['database']};"
        if c.get("trusted_connection", "").lower() in ["yes", "true", "1"]:
            conn_str += "Trusted_Connection=yes;"
        else:
            conn_str += f"UID={c['username']};PWD={c['password']};"
        return pyodbc.connect(conn_str, autocommit=False, timeout=10)

    def process_sync(self):
        ss_id = self.sheets_cfg["spreadsheet_id"]
        tab_tes = self.sheets_cfg.get("tab_tes", "DocTes")
        tab_rig = self.sheets_cfg.get("tab_rig", "DocRig")

        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Verifica ordini e offerte da sincronizzare...")
        
        # 1. Lettura testate
        tes_rows = self.sheets_client.read_range(ss_id, f"'{tab_tes}'!A1:R1000")
        if not tes_rows or len(tes_rows) <= 1:
            print("Nessun documento trovato nel foglio DocTes.")
            return

        header = [str(col).strip().upper() for col in tes_rows[0]]
        col_map = {name: idx for idx, name in enumerate(header)}

        # Assicura la presenza delle colonne di sincronizzazione (N:R)
        if len(tes_rows[0]) < 18:
            try:
                self.sheets_client.update_range(
                    ss_id,
                    f"'{tab_tes}'!N1:R1",
                    [["StatoSync", "DataSync", "DocId_Plus", "NumeroDoc_Plus", "LogErrore"]]
                )
            except Exception as e_h:
                print(f"[Avviso]: Aggiornamento intestazioni N1:R1: {e_h}")

        def get_val(row, col_name, default=""):
            idx = col_map.get(col_name)
            if idx is not None and idx < len(row):
                return str(row[idx]).strip()
            return default

        # Trova righe con StatoSync == 'DA_SINCRONIZZARE'
        pending = []
        for row_idx, row in enumerate(tes_rows[1:], start=2): # riga 1-indexed in Google Sheets
            stato = get_val(row, "STATOSYNC", "DA_SINCRONIZZARE").upper()
            doc_id_ext = get_val(row, "ID_DOCUMENTO")
            if stato == "DA_SINCRONIZZARE" and doc_id_ext:
                pending.append((row_idx, row, doc_id_ext))

        if not pending:
            print("Nessun documento in attesa (tutti già sincronizzati).")
            return

        print(f"Trovati {len(pending)} documenti da sincronizzare su Plus 2000.")

        # 2. Lettura righe per associazione
        rig_rows = self.sheets_client.read_range(ss_id, f"'{tab_rig}'!A1:P2000")
        rig_by_doc = {}
        if rig_rows and len(rig_rows) > 1:
            rig_header = [str(col).strip().upper() for col in rig_rows[0]]
            rig_col_map = {name: idx for idx, name in enumerate(rig_header)}
            for r in rig_rows[1:]:
                col_id_idx = rig_col_map.get("ID_DOCUMENTO", 0)
                d_id = r[col_id_idx] if col_id_idx < len(r) else ""
                if d_id:
                    d_id = str(d_id).strip()
                    if d_id not in rig_by_doc:
                        rig_by_doc[d_id] = []
                    rig_by_doc[d_id].append((r, rig_col_map))

        # 3. Connessione a SQL Server ed elaborazione
        conn = self.get_sql_connection()
        cursor = conn.cursor()

        for sheet_row_num, row_data, doc_id_ext in pending:
            tp_doc = get_val(row_data, "TPDOC", "OCL").upper() # OCL = Ordine, OFC = Offerta
            data_doc_raw = get_val(row_data, "DATADOC", datetime.date.today().strftime("%Y-%m-%d"))
            
            # Formatta data intero YYYYMMDD per Plus
            try:
                dt = datetime.datetime.strptime(data_doc_raw[:10], "%Y-%m-%d")
                d_doc_int = int(dt.strftime("%Y%m%d"))
                anno = dt.year
            except:
                d_doc_int = int(datetime.date.today().strftime("%Y%m%d"))
                anno = datetime.date.today().year

            cod_cliente = get_val(row_data, "CODICECLIENTE", "0")
            try:
                j_conto = int(cod_cliente)
            except:
                j_conto = 0

            j_seq_doc = "00" # Sezionale standard Plus
            note = get_val(row_data, "NOTE")
            rif_ord = get_val(row_data, "RIFERIMENTOCLIENTE", doc_id_ext)
            lines = rig_by_doc.get(doc_id_ext, [])

            print(f"\n--- Elaborazione Documento: {doc_id_ext} ({tp_doc}) - Cliente: {j_conto} ---")
            
            try:
                # A. Calcola e incrementa progressivo tramite Stored Procedure
                # sp_Sequenze_Ricerca @Anno, @TpSeq, @JSeq, @YProgr OUTPUT, @DProgr OUTPUT
                # sp_Sequenze_Aggiorna @ChkSequenza, @Anno, @TpSeq, @JSeq, @YProgrIn, @DProgrIn, @YProgrOut OUTPUT
                sql_seq = f"""
                SET NOCOUNT ON;
                DECLARE @YDocOut int, @DDocOut int, @YDoc int;
                EXEC sp_Sequenze_Ricerca {anno}, '{tp_doc}', '{j_seq_doc}', @YDocOut OUTPUT, @DDocOut OUTPUT;
                SET @YDoc = ISNULL(@YDocOut, 0) + 1;
                EXEC sp_Sequenze_Aggiorna 1, {anno}, '{tp_doc}', '{j_seq_doc}', @YDoc, {d_doc_int}, @YDocOut OUTPUT;
                SELECT @YDocOut;
                """
                cursor.execute(sql_seq)
                row_res = cursor.fetchone()
                y_doc = row_res[0] if row_res else 1

                # B. Inserimento Testata DocTes
                sql_insert_tes = f"""
                SET NOCOUNT ON;
                INSERT INTO DocTes (
                    Anno, TpDoc, JSeqDoc, YDoc, DDoc,
                    JCauMaga, DesCauMaga, JDepPri, JDepSec,
                    TpConto, JConto, TpContoDest, JContoDest,
                    JValuta, ACambio, RifOrd, DRifOrd
                ) VALUES (
                    {anno}, '{tp_doc}', '{j_seq_doc}', {y_doc}, {d_doc_int},
                    'ORCL', 'ORDINE CLIENTE', '000', '000',
                    'C', {j_conto}, 'C', {j_conto},
                    'EUR', 1.0, ?, {d_doc_int}
                );
                SELECT SCOPE_IDENTITY();
                """
                cursor.execute(sql_insert_tes, (rif_ord[:30],))
                doc_id_plus = int(cursor.fetchone()[0])
                print(f"  -> Inserita Testata DocTes con DocId={doc_id_plus}, Numero={y_doc}/{anno}")

                # C. Applica Default di Testata e Riafferma Causale ORCL & Deposito 000
                cursor.execute(f"EXEC sp_DocTes_SetDefault {doc_id_plus}, 0")
                cursor.execute(f"UPDATE DocTes SET JCauMaga = 'ORCL', DesCauMaga = 'ORDINE CLIENTE', JDepPri = '000', JDepSec = '000' WHERE DocId = {doc_id_plus}")

                # D. Inserimento Righe DocRig
                for r_num, (line_row, l_col_map) in enumerate(lines, start=1):
                    def get_l(col_n, def_v=""):
                        i = l_col_map.get(col_n)
                        return str(line_row[i]).strip() if i is not None and i < len(line_row) else def_v

                    ca_code = get_l("CODICEARTICOLO")
                    ca_id_raw = get_l("CAID", "0")
                    try:
                        ca_id = int(ca_id_raw)
                    except:
                        ca_id = 0

                    # Se CaId non fornito, cerca per Ca su Articoli
                    if ca_id == 0 and ca_code:
                        cursor.execute("SELECT CaId FROM Articoli WHERE Ca = ?", (ca_code,))
                        art_row = cursor.fetchone()
                        if art_row:
                            ca_id = art_row[0]

                    des_art = get_l("DESCRIZIONEARTICOLO")
                    um = get_l("UM", "PZ")[:3]
                    qt = float(get_l("QUANTITA", "1").replace(",", "."))
                    pz_netto = float(get_l("PREZZONETTO", "0").replace(",", "."))
                    pz_lordo = float(get_l("PREZZOLORDO", str(pz_netto)).replace(",", "."))
                    cod_iva = get_l("CODICEIVA", "22")[:4]
                    note_riga = get_l("NOTERIGA", note)
                    sc_extra_raw = get_l("SCONTOEXTRA", get_l("SCONTO_EXTRA", "0"))
                    try:
                        sc_extra = float(sc_extra_raw.replace(",", "."))
                    except:
                        sc_extra = 0.0

                    sql_insert_rig = f"""
                    SET NOCOUNT ON;
                    INSERT INTO DocRig (
                        DocId, Riga, TpDoc, JSeqDoc, DDoc,
                        CaId, DesArt, Um, UmQt, Pezzi, Qt,
                        PzLordo, PzNetto, ScontoExtra, JIva, Note,
                        JCauMaga, JDep
                    ) VALUES (
                        {doc_id_plus}, {r_num}, '{tp_doc}', '{j_seq_doc}', {d_doc_int},
                        {ca_id}, ?, '{um}', '{um}', {qt}, {qt},
                        {pz_lordo}, {pz_netto}, {sc_extra}, '{cod_iva}', ?,
                        'ORCL', '000'
                    );
                    SELECT SCOPE_IDENTITY();
                    """
                    cursor.execute(sql_insert_rig, (des_art, note_riga))
                    riga_id_plus = int(cursor.fetchone()[0])
                    # Imposta default riga (sconti, formule, contropartite)
                    cursor.execute(f"EXEC sp_DocRig_SetDefault {riga_id_plus}, 0, 0")
                    cursor.execute(f"UPDATE DocRig SET JCauMaga = 'ORCL', JDep = '000' WHERE RigaId = {riga_id_plus}")
                    if sc_extra > 0:
                        cursor.execute(f"UPDATE DocRig SET ScontoExtra = {sc_extra}, PzNetto = {pz_netto} WHERE RigaId = {riga_id_plus}")

                # E. Aggiorna totali e conferma documento
                cursor.execute(f"EXEC sp_Doc_Aggiorna_Totali {doc_id_plus}")
                if self.cfg.get("sync", {}).get("auto_confirm_doc", True):
                    cursor.execute(f"EXEC sp_Doc_Conferma '', {doc_id_plus}")

                # Commit transazione SQL
                conn.commit()
                print(f"  [OK] Sincronizzazione SQL Server completata con successo!")

                # F. Aggiorna Google Sheet
                sync_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Colonne N, O, P, Q, R: StatoSync, DataSync, DocId_Plus, NumeroDoc_Plus, LogErrore
                update_vals = [["SINCRONIZZATO", sync_timestamp, str(doc_id_plus), str(y_doc), ""]]
                self.sheets_client.update_range(ss_id, f"'{tab_tes}'!N{sheet_row_num}:R{sheet_row_num}", update_vals)

            except Exception as e:
                conn.rollback()
                err_msg = str(e).replace("\n", " ")[:200]
                print(f"  [ERRORE] Fallita sincronizzazione {doc_id_ext}: {err_msg}")
                # Registra errore su Google Sheets
                sync_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_vals = [["ERRORE", sync_timestamp, "", "", err_msg]]
                self.sheets_client.update_range(ss_id, f"'{tab_tes}'!N{sheet_row_num}:R{sheet_row_num}", update_vals)

        conn.close()
        print("\nSincronizzazione completata.")

def main():
    cfg = load_config()
    connector = Plus2000Connector(cfg)
    
    if "--export-clienti" in sys.argv:
        from export_clienti import run_export_clienti
        run_export_clienti()
        return

    if "--export-agenti" in sys.argv:
        from export_agenti import run_export_agenti
        run_export_agenti()
        return

    if "--export-articoli" in sys.argv:
        from export_articoli import run_export_articoli
        run_export_articoli()
        return

    once_mode = "--once" in sys.argv
    interval = cfg.get("sync", {}).get("interval_seconds", 60)
    
    print("=== CONNETTORE GOOGLE SHEETS <-> PLUS 2000 ===")
    if once_mode:
        print("Modalita: Singola esecuzione (--once)")
        connector.process_sync()
        return

    print(f"Intervallo di scansione: {interval} secondi")
    print("Premi Ctrl+C per arrestare.\n")
    
    while True:
        try:
            connector.process_sync()
        except Exception as e:
            print(f"[ERRORE LOOP]: {e}")
        time.sleep(interval)

if __name__ == "__main__":
    main()

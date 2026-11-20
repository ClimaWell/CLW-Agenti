import json
import os
import sys
import datetime
import requests
import pyodbc

# Forza UTF-8 per console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from connettore import GoogleSheetsClient, load_config, BASE_DIR

TARGET_SPREADSHEET_ID = "1DiBs4OV5vYoMTpz17p25OTMk1GokT7K9vEAvi7YkGpc"
FORNITORE_ID = 661

def export_obsoleti_cambielli():
    cfg = load_config()
    sa_file = cfg.get("google_sheets", {}).get("service_account_file", "service_account.json")
    client = GoogleSheetsClient(sa_file)
    token = client._get_access_token()
    
    print(f"=== ESPORTAZIONE ARTICOLI MAGAZZINO CAMBIELLI ({FORNITORE_ID}) ===")
    print(f"Target Google Sheet ID: {TARGET_SPREADSHEET_ID}")
    
    # 1. Verifica foglio e recupero tab name
    headers_req = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    meta_res = requests.get(f"https://sheets.googleapis.com/v4/spreadsheets/{TARGET_SPREADSHEET_ID}", headers=headers_req, timeout=15)
    if meta_res.status_code != 200:
        raise RuntimeError(f"Impossibile accedere al foglio Google {TARGET_SPREADSHEET_ID}: {meta_res.text}")
    
    meta = meta_res.json()
    sheet_title = meta.get("properties", {}).get("title", "")
    sheets = meta.get("sheets", [])
    first_tab = sheets[0]["properties"]["title"] if sheets else "Foglio1"
    print(f"Foglio rilevato: '{sheet_title}', Tab principale: '{first_tab}'")

    # 2. Connessione SQL Server Plus 2000
    sql_cfg = cfg["sql_server"]
    dsn = sql_cfg.get("dsn", "climawell")
    print(f"Connessione a SQL Server Plus 2000 (DSN={dsn})...")
    conn = pyodbc.connect(f"DSN={dsn};", autocommit=True, timeout=15)
    cursor = conn.cursor()

    # Query di estrazione completa
    print("Estrazione articoli in giacenza verificando l'ULTIMO acquisto assoluto...")
    query = f"""
        WITH Giacenze AS (
            SELECT CaId, SUM(QtEsi) AS Giacenza, SUM(QtDisp) AS Disponibile
            FROM ArticoliContGen
            GROUP BY CaId
            HAVING SUM(QtEsi) > 0
        ),
        UltimoAcquistoAssoluto AS (
            SELECT 
                r.CaId,
                t.DDoc AS DataAcquisto,
                t.JConto AS FornitoreId,
                f.RagSoc AS FornitoreNome,
                t.TpDoc,
                t.YDoc AS NumDoc,
                r.PzNetto,
                r.PzLordo,
                ROW_NUMBER() OVER (PARTITION BY r.CaId ORDER BY t.DDoc DESC, t.DocId DESC, r.Riga DESC) AS rn
            FROM DocRig r
            JOIN DocTes t ON r.DocId = t.DocId
            LEFT JOIN CliFor f ON t.JConto = f.JConto AND f.TpConto = 'F'
            WHERE t.TpConto = 'F'
        ),
        Storico661 AS (
            SELECT 
                r.CaId, 
                COUNT(DISTINCT t.DocId) AS NumDocAcq,
                SUM(r.Qt) AS TotPezziAcquistati
            FROM DocRig r
            JOIN DocTes t ON r.DocId = t.DocId
            WHERE t.JConto = {FORNITORE_ID} AND t.TpConto = 'F'
            GROUP BY r.CaId
        ),
        PrezziVen1 AS (
            SELECT CaId, Pz AS PrezzoListino, DValidita,
                   ROW_NUMBER() OVER (
                       PARTITION BY CaId 
                       ORDER BY 
                           CASE WHEN DValidita <= CAST(CONVERT(varchar(8), GETDATE(), 112) AS INT) THEN 1 ELSE 0 END DESC,
                           DValidita DESC,
                           DMod DESC,
                           DIns DESC
                   ) as rn
            FROM ListiniPrezzi
            WHERE JListino = 'VEN1'
        )
        SELECT 
            a.CaId,
            RTRIM(LTRIM(a.Ca)) AS CodiceArticolo,
            RTRIM(LTRIM(a.DesArt + CASE WHEN a.DesSup IS NOT NULL AND RTRIM(a.DesSup) <> '' THEN ' ' + RTRIM(a.DesSup) ELSE '' END)) AS Descrizione,
            RTRIM(LTRIM(ISNULL(a.Marca, ''))) AS Marca,
            ISNULL(NULLIF(RTRIM(t_set.DesTab), ''), CASE WHEN a.JSettore IN ('0', '00', '') THEN '' ELSE RTRIM(a.JSettore) END) AS Settore,
            ISNULL(NULLIF(RTRIM(t_mac.DesMacroFamiglia), ''), CASE WHEN a.JMacroFamiglia IN ('0', '00', '000', '') THEN '' ELSE RTRIM(a.JMacroFamiglia) END) AS Macrofamiglia,
            ISNULL(NULLIF(RTRIM(t_fam.DesFamiglia), ''), CASE WHEN a.JFamiglia IN ('0', '00', '000', '') THEN '' ELSE RTRIM(a.JFamiglia) END) AS Famiglia,
            RTRIM(LTRIM(ISNULL(a.JUbiArt, ''))) AS Ubicazione,
            RTRIM(LTRIM(ISNULL(a.Um, 'PZ'))) AS Um,
            g.Giacenza,
            g.Disponibile,
            u.DataAcquisto,
            u.FornitoreId,
            u.FornitoreNome,
            u.TpDoc,
            u.NumDoc,
            ISNULL(u.PzNetto, 0) AS UltimoPrezzoNetto,
            ISNULL(u.PzLordo, 0) AS UltimoPrezzoLordo,
            ISNULL(ven.PrezzoListino, 0) AS PrezzoListinoVendita,
            ISNULL(s661.NumDocAcq, 0) AS NumDocAcq661,
            ISNULL(s661.TotPezziAcquistati, 0) AS TotPezziAcq661,
            a.JFornitore AS FornitoreAnagrafica,
            RTRIM(LTRIM(ISNULL(a.Disegno, ''))) AS Disegno,
            RTRIM(LTRIM(ISNULL(a.CaProd, ''))) AS CaProd
        FROM Giacenze g
        JOIN Articoli a ON g.CaId = a.CaId
        LEFT JOIN UltimoAcquistoAssoluto u ON g.CaId = u.CaId AND u.rn = 1
        LEFT JOIN Storico661 s661 ON g.CaId = s661.CaId
        LEFT JOIN PrezziVen1 ven ON g.CaId = ven.CaId AND ven.rn = 1
        LEFT JOIN TabDes t_set ON t_set.TpTab = 'SET' AND t_set.JTab = a.JSettore
        LEFT JOIN MacroFamiglie t_mac ON t_mac.JSettore = a.JSettore AND t_mac.JMacroFamiglia = a.JMacroFamiglia
        LEFT JOIN Famiglie t_fam ON t_fam.JSettore = a.JSettore AND t_fam.JMacroFamiglia = a.JMacroFamiglia AND t_fam.JFamiglia = a.JFamiglia
        WHERE (u.FornitoreId = {FORNITORE_ID}) 
           OR (u.FornitoreId IS NULL AND a.JFornitore = {FORNITORE_ID})
        ORDER BY 
            CASE WHEN u.DataAcquisto IS NULL THEN 0 ELSE 1 END ASC,
            u.DataAcquisto ASC, 
            g.Giacenza DESC
    """
    
    cursor.execute(query)
    raw_rows = cursor.fetchall()
    conn.close()
    print(f"Estratti {len(raw_rows)} articoli da Plus 2000 il cui ultimo acquisto effettivo è da Cambielli.")

    # 3. Trasformazione e classificazione anzianità / obsolescenza
    headers = [
        "Codice Articolo",
        "Descrizione",
        "Giacenza (Pz)",
        "Disponibile (Pz)",
        "U.M.",
        "Codice Fornitore",
        "Fornitore Ultimo Carico",
        "Data Ultimo Acquisto",
        "Anno Ultimo Acq.",
        "Anni da Ultimo Acq.",
        "Fascia Obsolescenza / Priorità Reso",
        "Ultimo Costo Netto (€)",
        "Valore Totale Giacenza (€)",
        "Prezzo Listino Vendita (€)",
        "Doc. Ultimo Carico",
        "Marca",
        "Settore",
        "Macrofamiglia",
        "Famiglia",
        "Ubicazione Magazzino",
        "Num. Carichi Cambielli",
        "Tot. Pezzi Acquistati Cambielli",
        "URL-immagine",
        "CaId (Plus 2000)"
    ]

    DOMUS_ASSET_BASE_URL = "https://www.domuspartes.it/products_images/pre/assets"

    def formatta_url_domus(marca: str, disegno: str, caprod: str) -> str:
        marca_clean = str(marca or "").strip().upper()
        if not marca_clean or marca_clean in ("0", "-", "_"):
            return ""
            
        dis_clean = str(disegno or "").strip().replace("\\", "/").strip("/")
        if dis_clean and not any(dis_clean.lower().endswith(x) for x in [".exe", ".bat", "/"]):
            nome_file = os.path.basename(dis_clean)
            if nome_file and nome_file.lower() not in ("logo.jpg", "ids", "tlc", "fog.jpg"):
                if nome_file.lower().endswith(".jpg"):
                    return f"{DOMUS_ASSET_BASE_URL}/{marca_clean}/{nome_file}.jpg"
                elif nome_file.lower().endswith(".png"):
                    return f"{DOMUS_ASSET_BASE_URL}/{marca_clean}/{nome_file}"
                else:
                    return f"{DOMUS_ASSET_BASE_URL}/{marca_clean}/{nome_file}.jpg.jpg"

        caprod_clean = str(caprod or "").strip()
        if caprod_clean and caprod_clean not in ("0", "-", "_"):
            return f"{DOMUS_ASSET_BASE_URL}/{marca_clean}/{caprod_clean}.jpg.jpg"
            
        return ""

    current_year = 2026
    data_matrix = [headers]

    tot_giac = 0
    tot_valore = 0
    fasce_count = {
        "CRITICO (> 7 anni)": 0,
        "ALTA (5 - 7 anni)": 0,
        "MEDIA (3 - 5 anni)": 0,
        "BASSA (1 - 3 anni)": 0,
        "CORRENTE (< 1 anno)": 0,
        "STORICO / N.D.": 0
    }

    for r in raw_rows:
        caid = str(r.CaId)
        cod = str(r.CodiceArticolo or "").strip()
        des = str(r.Descrizione or "").strip()
        marca = str(r.Marca or "").strip()
        settore = str(r.Settore or "").strip()
        macrofam = str(r.Macrofamiglia or "").strip()
        famiglia = str(r.Famiglia or "").strip()
        ubi = str(r.Ubicazione or "").strip()
        um = str(r.Um or "PZ").strip()
        giac = float(r.Giacenza or 0)
        disp = float(r.Disponibile or 0)
        
        d_raw = str(r.DataAcquisto or "")
        forn_id = str(r.FornitoreId or r.FornitoreAnagrafica or FORNITORE_ID)
        forn_nome = str(r.FornitoreNome or "CAMBIELLI EDILFRIULI S.P.A.").strip()
        
        tp_doc = str(r.TpDoc or "").strip()
        num_doc = str(r.NumDoc or "").strip()
        doc_carico = f"{tp_doc} {num_doc}".strip() if (tp_doc or num_doc) else ""
        
        pz_netto = float(r.UltimoPrezzoNetto or 0)
        val_tot = giac * pz_netto
        pz_listino = float(r.PrezzoListinoVendita or 0)
        num_carichi = int(r.NumDocAcq661 or 0)
        tot_acq = float(r.TotPezziAcq661 or 0)

        tot_giac += giac
        tot_valore += val_tot

        if len(d_raw) == 8 and d_raw.isdigit():
            d_fmt = f"{d_raw[6:8]}/{d_raw[4:6]}/{d_raw[0:4]}"
            anno_acq = int(d_raw[0:4])
            anni_diff = current_year - anno_acq
            
            if anni_diff >= 7:
                fascia = "🔴 CRITICO (> 7 anni)"
                fasce_count["CRITICO (> 7 anni)"] += 1
            elif anni_diff >= 5:
                fascia = "🟠 ALTA (5 - 7 anni)"
                fasce_count["ALTA (5 - 7 anni)"] += 1
            elif anni_diff >= 3:
                fascia = "🟡 MEDIA (3 - 5 anni)"
                fasce_count["MEDIA (3 - 5 anni)"] += 1
            elif anni_diff >= 1:
                fascia = "🔵 BASSA (1 - 3 anni)"
                fasce_count["BASSA (1 - 3 anni)"] += 1
            else:
                fascia = "🟢 CORRENTE (< 1 anno)"
                fasce_count["CORRENTE (< 1 anno)"] += 1
        else:
            d_fmt = "Storico / N.D."
            anno_acq = ""
            anni_diff = ""
            fascia = "⚪ STORICO (Anagrafica 661)"
            fasce_count["STORICO / N.D."] += 1

        data_matrix.append([
            cod,
            des,
            giac,
            disp,
            um,
            forn_id,
            forn_nome,
            d_fmt,
            anno_acq,
            anni_diff,
            fascia,
            round(pz_netto, 2),
            round(val_tot, 2),
            round(pz_listino, 2),
            doc_carico,
            marca,
            settore,
            macrofam,
            famiglia,
            ubi,
            num_carichi,
            tot_acq,
            formatta_url_domus(marca, str(r.Disegno or ''), str(r.CaProd or '')),
            caid
        ])

    print(f"Matrice dati pronta: {len(data_matrix)} righe (inclusa intestazione).")
    print(f"Totale pezzi: {tot_giac:.0f}, Valore stimato: € {tot_valore:,.2f}")

    # 4. Scrittura su Google Sheets
    print(f"Cancellazione e aggiornamento foglio '{first_tab}' su Google Drive...")
    
    # Pulisce il foglio esistente
    requests.post(
        f"https://sheets.googleapis.com/v4/spreadsheets/{TARGET_SPREADSHEET_ID}/values/'{first_tab}'!A1:Z10000:clear",
        headers=headers_req,
        timeout=15
    )

    # Scrive i dati
    upd_res = requests.put(
        f"https://sheets.googleapis.com/v4/spreadsheets/{TARGET_SPREADSHEET_ID}/values/'{first_tab}'!A1?valueInputOption=USER_ENTERED",
        headers=headers_req,
        json={"values": data_matrix},
        timeout=30
    )

    if upd_res.status_code == 200:
        print(f"✅ Dati scritti con successo nel foglio Google Drive!")
    else:
        raise RuntimeError(f"Errore scrittura dati su Google Sheets: {upd_res.text}")

    # 5. Formattazione estetica di Google Sheets (Freeze intestazione, grassetto, larghezza colonne)
    sheet_id = sheets[0]["properties"]["sheetId"]
    fmt_requests = [
        # Blocca la prima riga
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {"frozenRowCount": 1}
                },
                "fields": "gridProperties.frozenRowCount"
            }
        },
        # Stile intestazione: sfondo blu scuro (#1E3A8A), testo bianco grassetto
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": len(headers)
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.12, "green": 0.23, "blue": 0.54},
                        "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True, "fontSize": 10},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        }
    ]

    requests.post(
        f"https://sheets.googleapis.com/v4/spreadsheets/{TARGET_SPREADSHEET_ID}:batchUpdate",
        headers=headers_req,
        json={"requests": fmt_requests},
        timeout=15
    )

    print("✅ Formattazione foglio completata con successo!")
    print("\nRiepilogo Fasce Obsolescenza:")
    for k, v in fasce_count.items():
        print(f"  {k}: {v} articoli")

if __name__ == "__main__":
    export_obsoleti_cambielli()

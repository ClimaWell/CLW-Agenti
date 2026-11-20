import json
import os
import sys
import datetime
import requests
import pyodbc
from connettore import GoogleSheetsClient, load_config, BASE_DIR

def run_export_clienti(all_records=False):
    cfg = load_config()
    sa_file = cfg.get("google_sheets", {}).get("service_account_file", "service_account.json")
    client = GoogleSheetsClient(sa_file)
    
    exp_cfg = cfg.get("export_clienti", {})
    SPREADSHEET_ID = exp_cfg.get("spreadsheet_id", "1Ui3W6-jVIww7QgTtnXaywJj2ZyQiiaHAd92Xl5KRrD8")
    TAB_NAME = exp_cfg.get("tab_name", "clienti")
    min_year = exp_cfg.get("filtro_anno_minimo", 2024)
    include_new = exp_cfg.get("includi_nuovi_inseriti", True)
    
    if "--all" in sys.argv:
        all_records = True

    print("=== AVVIO ESPORTAZIONE ANAGRAFICA CLIENTI DA PLUS 2000 ===")
    print(f"Spreadsheet ID: {SPREADSHEET_ID}")
    print(f"Tabella target: {TAB_NAME}")
    if all_records:
        print("Filtro: TUTTO LO STORICO (Nessun filtro temporale)")
    else:
        print(f"Filtro: Documenti dal {min_year} in poi" + (f" o inseriti dal {min_year}" if include_new else ""))
    
    # 1. Connessione SQL Server
    sql_cfg = cfg["sql_server"]
    dsn = sql_cfg.get("dsn", "climawell")
    print(f"Connessione a SQL Server (DSN={dsn})...")
    conn = pyodbc.connect(f"DSN={dsn};", autocommit=True, timeout=15)
    cursor = conn.cursor()
    
    # Costruzione clausola WHERE
    where_conditions = ["c.TpConto = 'C'", "c.Bloccato = 0"]
    if not all_records:
        year_filter_parts = [f"doc.MaxAnno >= {min_year}"]
        if include_new:
            year_filter_parts.append(f"c.DIns >= {min_year}0101")
        where_conditions.append(f"({' OR '.join(year_filter_parts)})")
        
    where_sql = " AND ".join(where_conditions)
    
    # 2. Query estrazione clienti consolidata con tutti i recapiti
    query = f"""
        SELECT 
            c.JConto,
            RTRIM(LTRIM(c.RagSoc + CASE WHEN c.RagSup IS NOT NULL AND RTRIM(c.RagSup) <> '' THEN ' ' + RTRIM(c.RagSup) ELSE '' END)) as RagioneSociale,
            c.JAgente,
            ISNULL(ag.RagSoc, '') as NomeAgente,
            RTRIM(LTRIM(ISNULL(c.Indirizzo, ''))) as Indirizzo,
            RTRIM(LTRIM(ISNULL(c.Cap, ''))) as Cap,
            RTRIM(LTRIM(ISNULL(c.Citta, ''))) as Citta,
            RTRIM(LTRIM(ISNULL(c.Provincia, ''))) as Provincia,
            RTRIM(LTRIM(ISNULL(c.CodFiscale, ''))) as CodiceFiscale,
            RTRIM(LTRIM(ISNULL(c.PartitaIva, ''))) as PartitaIva,
            RTRIM(LTRIM(ISNULL(c.JPagamento, ''))) as CodicePagamento,
            RTRIM(LTRIM(ISNULL(c.JListino, ''))) as CodiceListino,
            COALESCE(NULLIF(RTRIM(c.Telefono), ''), NULLIF(RTRIM(ct.Telefono), ''), '') as Telefono,
            COALESCE(NULLIF(RTRIM(c.Cellulare), ''), NULLIF(RTRIM(ct.Cellulare), ''), '') as Cellulare,
            COALESCE(NULLIF(RTRIM(c.TeleFax), ''), NULLIF(RTRIM(ct.TeleFax), ''), '') as Telefax,
            COALESCE(NULLIF(RTRIM(c.EMail), ''), NULLIF(RTRIM(c.OclMail), ''), NULLIF(RTRIM(c.FatMail), ''), NULLIF(RTRIM(ct.EMail), ''), '') as Email,
            COALESCE(NULLIF(RTRIM(c.EMailPEC), ''), '') as Pec,
            ISNULL(doc.MaxAnno, 0) as UltimoAnnoDoc,
            c.DIns as DataInserimento,
            CASE WHEN c.Bloccato = 1 THEN 'BLOCCATO' ELSE 'ATTIVO' END as Stato
        FROM CliFor c
        LEFT JOIN CliFor ag ON ag.TpConto = 'F' AND ag.JConto = c.JAgente
        LEFT JOIN (
            SELECT JConto, 
                   MAX(Telefono) as Telefono, 
                   MAX(Cellulare) as Cellulare, 
                   MAX(TeleFax) as TeleFax, 
                   MAX(EMail) as EMail
            FROM CliForContatti
            WHERE TpConto = 'C'
            GROUP BY JConto
        ) ct ON c.JConto = ct.JConto
        LEFT JOIN (
            SELECT JConto, MAX(Anno) as MaxAnno
            FROM DocTes
            WHERE TpConto = 'C'
            GROUP BY JConto
        ) doc ON c.JConto = doc.JConto
        WHERE {where_sql}
        ORDER BY c.JAgente, RagioneSociale
    """
    
    print("Esecuzione query su SQL Server...")
    cursor.execute(query)
    raw_rows = cursor.fetchall()
    conn.close()
    print(f"Estratti {len(raw_rows)} clienti da Plus 2000.")
    
    # 3. Preparazione dati per Google Sheets
    headers = [
        "Codice",
        "Ragione sociale",
        "CodiceAgente",
        "Agente",
        "Indirizzo",
        "Cap",
        "Citta",
        "Pv",
        "CodiceFiscale",
        "PartitaIva",
        "Pagamento",
        "Listino",
        "Telefono",
        "Cellulare",
        "Telefax",
        "E-mail",
        "PEC",
        "UltimoAnnoDoc",
        "DataInserimento",
        "Stato"
    ]
    
    def clean_str(val):
        s = str(val or "").strip()
        if s in ["_", "-", ".", "/"]:
            return ""
        return s

    sheet_data = [headers]
    for r in raw_rows:
        dins_str = ""
        if r[18] and r[18] > 0:
            d_raw = str(r[18])
            if len(d_raw) == 8:
                dins_str = f"{d_raw[:4]}-{d_raw[4:6]}-{d_raw[6:]}"

        sheet_data.append([
            clean_str(r[0]),              # Codice (JConto)
            clean_str(r[1]),              # Ragione sociale
            clean_str(r[2]),              # CodiceAgente (JAgente)
            clean_str(r[3]),              # Agente (NomeAgente)
            clean_str(r[4]),              # Indirizzo
            clean_str(r[5]),              # Cap
            clean_str(r[6]),              # Citta
            clean_str(r[7]),              # Pv
            clean_str(r[8]),              # CodiceFiscale
            clean_str(r[9]),              # PartitaIva
            clean_str(r[10]),             # Pagamento
            clean_str(r[11]),             # Listino
            clean_str(r[12]),             # Telefono
            clean_str(r[13]),             # Cellulare
            clean_str(r[14]),             # Telefax
            clean_str(r[15]),             # E-mail
            clean_str(r[16]),             # PEC
            str(r[17]) if r[17] else "",  # UltimoAnnoDoc
            dins_str,                     # DataInserimento (YYYY-MM-DD)
            str(r[19] or "ATTIVO")        # Stato
        ])
    
    token = client._get_access_token()
    auth_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    total_rows = len(sheet_data)
    
    # 4. Assicura che la griglia del foglio abbia righe sufficienti
    meta_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}"
    meta_res = requests.get(meta_url, headers=auth_headers, timeout=15).json()
    sheet_id_num = None
    for s in meta_res.get("sheets", []):
        if s["properties"]["title"] == TAB_NAME:
            sheet_id_num = s["properties"]["sheetId"]
            break

    if sheet_id_num is not None:
        target_rows = max(total_rows + 50, 1000)
        print(f"Adeguamento dimensione griglia foglio a {target_rows} righe e {len(headers)} colonne...")
        resize_req = {
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id_num,
                            "gridProperties": {
                                "rowCount": target_rows,
                                "columnCount": max(len(headers) + 2, 26)
                            }
                        },
                        "fields": "gridProperties.rowCount,gridProperties.columnCount"
                    }
                }
            ]
        }
        requests.post(f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}:batchUpdate", headers=auth_headers, json=resize_req, timeout=15)

    # 5. Pulizia foglio esistente
    print(f"Svuotamento dati precedenti nel foglio '{TAB_NAME}'...")
    clear_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/'{TAB_NAME}'!A1:Z:clear"
    requests.post(clear_url, headers=auth_headers, timeout=15)
    
    # 6. Scrittura nuovi dati in blocchi (batch da 2500 righe)
    BATCH_SIZE = 2500
    print(f"Caricamento di {total_rows} righe su Google Sheets in batch...")
    
    for start_idx in range(0, total_rows, BATCH_SIZE):
        end_idx = min(start_idx + BATCH_SIZE, total_rows)
        chunk = sheet_data[start_idx:end_idx]
        start_row_num = start_idx + 1
        end_row_num = end_idx
        
        range_str = f"'{TAB_NAME}'!A{start_row_num}:T{end_row_num}"
        update_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{range_str}?valueInputOption=USER_ENTERED"
        res = requests.put(update_url, headers=auth_headers, json={"values": chunk}, timeout=30)
        if res.status_code != 200:
            raise RuntimeError(f"Errore caricamento righe {start_row_num}-{end_row_num}: {res.text}")
        print(f"  -> Caricate righe {start_row_num} - {end_row_num} di {total_rows}")
        
    # 7. Formattazione estetica del foglio (Intestazione scura, testo bianco, freeze riga 1)
    if sheet_id_num is not None:
        print("Applicazione formattazione estetica...")
        batch_req = {
            "requests": [
                # Freeze riga 1
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id_num,
                            "gridProperties": {
                                "frozenRowCount": 1
                            }
                        },
                        "fields": "gridProperties.frozenRowCount"
                    }
                },
                # Stile intestazione: sfondo blu notte (#1E293B), testo bianco, grassetto
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id_num,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(headers)
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 0.117,
                                    "green": 0.160,
                                    "blue": 0.231
                                },
                                "textFormat": {
                                    "foregroundColor": {
                                        "red": 1.0,
                                        "green": 1.0,
                                        "blue": 1.0
                                    },
                                    "bold": True,
                                    "fontSize": 10
                                },
                                "horizontalAlignment": "LEFT",
                                "verticalAlignment": "MIDDLE",
                                "wrapStrategy": "CLIP"
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
                    }
                },
                # Auto-resize colonne
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": sheet_id_num,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": len(headers)
                        }
                    }
                }
            ]
        }
        batch_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}:batchUpdate"
        format_res = requests.post(batch_url, headers=auth_headers, json=batch_req, timeout=15)
        if format_res.status_code == 200:
            print("  [OK] Formattazione applicata con successo!")
        else:
            print(f"  [AVVISO Formattazione]: {format_res.text}")
            
    print(f"\nEsportazione completata con successo! {len(raw_rows)} clienti caricati su Google Drive.")

if __name__ == "__main__":
    run_export_clienti()

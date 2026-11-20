import json
import os
import sys
import requests
import pyodbc
from connettore import GoogleSheetsClient, load_config, BASE_DIR

def run_export_agenti():
    cfg = load_config()
    sa_file = cfg.get("google_sheets", {}).get("service_account_file", "service_account.json")
    client = GoogleSheetsClient(sa_file)
    
    # ID del foglio Google indicato dall'utente
    SPREADSHEET_ID = "10hp34cPu6ZxzPwSbrlIFsr_WcQTaIwBmJUUQjFZc2nw"
    TAB_NAME = "daPlus"
    
    print("=== AVVIO ESPORTAZIONE LISTA AGENTI DA PLUS 2000 ===")
    print(f"Spreadsheet ID: {SPREADSHEET_ID}")
    print(f"Tabella target: {TAB_NAME}")
    
    # 1. Connessione SQL Server
    sql_cfg = cfg["sql_server"]
    dsn = sql_cfg.get("dsn", "climawell")
    print(f"Connessione a SQL Server (DSN={dsn})...")
    conn = pyodbc.connect(f"DSN={dsn};", autocommit=True, timeout=15)
    cursor = conn.cursor()
    
    # 2. Query estrazione agenti con clienti attivi o recenti
    query = """
        SELECT 
            c.JAgente as CodiceAgente,
            RTRIM(LTRIM(ISNULL(ag.RagSoc, 'SENZA NOME') + CASE WHEN ag.RagSup IS NOT NULL AND RTRIM(ag.RagSup) <> '' THEN ' ' + RTRIM(ag.RagSup) ELSE '' END)) as NomeAgente,
            RTRIM(LTRIM(ISNULL(ag.Cellulare, ''))) as Cellulare,
            RTRIM(LTRIM(ISNULL(ag.Telefono, ''))) as Telefono,
            RTRIM(LTRIM(ISNULL(ag.EMail, ''))) as Email,
            RTRIM(LTRIM(ISNULL(ag.EMailPEC, ''))) as PEC,
            RTRIM(LTRIM(ISNULL(ag.Citta, ''))) as Citta,
            RTRIM(LTRIM(ISNULL(ag.Provincia, ''))) as Pv,
            COUNT(DISTINCT CASE WHEN doc.MaxAnno >= 2024 OR c.DIns >= 20240101 THEN c.JConto END) as ClientiRecenti2024_2026,
            COUNT(DISTINCT c.JConto) as TotClientiAttivi,
            CASE WHEN ag.Bloccato = 1 THEN 'BLOCCATO' ELSE 'ATTIVO' END as StatoAgente
        FROM CliFor c
        LEFT JOIN CliFor ag ON ag.TpConto = 'F' AND ag.JConto = c.JAgente
        LEFT JOIN (
            SELECT JConto, MAX(Anno) as MaxAnno
            FROM DocTes
            WHERE TpConto = 'C'
            GROUP BY JConto
        ) doc ON c.JConto = doc.JConto
        WHERE c.TpConto = 'C' AND c.Bloccato = 0 AND c.JAgente > 0
        GROUP BY 
            c.JAgente,
            ag.RagSoc,
            ag.RagSup,
            ag.Cellulare,
            ag.Telefono,
            ag.EMail,
            ag.EMailPEC,
            ag.Citta,
            ag.Provincia,
            ag.Bloccato
        HAVING COUNT(DISTINCT CASE WHEN doc.MaxAnno >= 2024 OR c.DIns >= 20240101 THEN c.JConto END) > 0 
            OR COUNT(DISTINCT c.JConto) >= 10
        ORDER BY ClientiRecenti2024_2026 DESC, TotClientiAttivi DESC
    """
    
    print("Esecuzione query su SQL Server...")
    cursor.execute(query)
    raw_rows = cursor.fetchall()
    conn.close()
    print(f"Estratti {len(raw_rows)} agenti con clienti associati da Plus 2000.")
    
    # 3. Preparazione dati per il foglio Google Sheets
    headers = [
        "IdAgenteOrderSender",
        "CodiceAgentePlus",
        "NomeAgente",
        "Cellulare",
        "Telefono",
        "Email",
        "PEC",
        "Citta",
        "Pv",
        "ClientiRecenti_2024_2026",
        "ClientiTotaliAttivi",
        "Stato"
    ]
    
    def clean_str(val):
        s = str(val or "").strip()
        if s in ["_", "-", ".", "/"]:
            return ""
        return s

    sheet_data = [headers]
    agent_counter = 1
    for r in raw_rows:
        cod_agente = clean_str(r[0])
        nome_agente = clean_str(r[1])
        recenti = r[8]
        totali = r[9]
        stato = clean_str(r[10])
        
        # Assegna codice progressivo AG01, AG02 per OrderSender
        os_id = f"AG{agent_counter:02d}"
        agent_counter += 1
        
        sheet_data.append([
            os_id,
            cod_agente,
            nome_agente,
            clean_str(r[2]),      # Cellulare
            clean_str(r[3]),      # Telefono
            clean_str(r[4]),      # Email
            clean_str(r[5]),      # PEC
            clean_str(r[6]),      # Citta
            clean_str(r[7]),      # Pv
            str(recenti),         # ClientiRecenti
            str(totali),          # ClientiTotali
            stato                 # Stato
        ])
        
    token = client._get_access_token()
    auth_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # 4. Verifica o creazione del foglio (tab) 'daPlus'
    meta_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}"
    meta_res = requests.get(meta_url, headers=auth_headers, timeout=15).json()
    sheet_id_num = None
    for s in meta_res.get("sheets", []):
        if s["properties"]["title"] == TAB_NAME:
            sheet_id_num = s["properties"]["sheetId"]
            break

    if sheet_id_num is None:
        print(f"Il foglio '{TAB_NAME}' non esiste nello spreadsheet. Creazione in corso...")
        add_sheet_req = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": TAB_NAME,
                            "gridProperties": {
                                "rowCount": max(len(sheet_data) + 20, 100),
                                "columnCount": len(headers) + 4
                            }
                        }
                    }
                }
            ]
        }
        create_res = requests.post(
            f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}:batchUpdate",
            headers=auth_headers,
            json=add_sheet_req,
            timeout=15
        ).json()
        sheet_id_num = create_res["replies"][0]["addSheet"]["properties"]["sheetId"]
        print(f"  [OK] Foglio '{TAB_NAME}' creato con SheetId {sheet_id_num}.")
    else:
        print(f"Foglio '{TAB_NAME}' trovato con SheetId {sheet_id_num}. Pulizia celle esistenti...")
        clear_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/'{TAB_NAME}'!A1:Z:clear"
        requests.post(clear_url, headers=auth_headers, timeout=15)

    # 5. Scrittura dati nel foglio 'daPlus'
    print(f"Scrittura di {len(sheet_data)} righe nel foglio '{TAB_NAME}'...")
    range_str = f"'{TAB_NAME}'!A1:L{len(sheet_data)}"
    update_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{range_str}?valueInputOption=USER_ENTERED"
    res = requests.put(update_url, headers=auth_headers, json={"values": sheet_data}, timeout=15)
    if res.status_code != 200:
        raise RuntimeError(f"Errore scrittura agenti: {res.text}")
    print("  [OK] Dati scritti con successo!")

    # 6. Formattazione estetica (header scuro blu notte, freeze riga 1, auto-resize)
    print("Applicazione formattazione estetica...")
    format_req = {
        "requests": [
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
                                "red": 0.082,
                                "green": 0.208,
                                "blue": 0.376
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
    format_res = requests.post(batch_url, headers=auth_headers, json=format_req, timeout=15)
    if format_res.status_code == 200:
        print("  [OK] Formattazione applicata con successo!")
    else:
        print(f"  [AVVISO Formattazione]: {format_res.text}")

    print(f"\nEsportazione agenti completata con successo nel foglio '{TAB_NAME}' dello Spreadsheet {SPREADSHEET_ID}!")

if __name__ == "__main__":
    run_export_agenti()

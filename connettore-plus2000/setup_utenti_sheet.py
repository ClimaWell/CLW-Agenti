import json
import requests
from connettore import GoogleSheetsClient, load_config

def setup_utenti_sheet():
    cfg = load_config()
    sa_file = cfg.get("google_sheets", {}).get("service_account_file", "service_account.json")
    client = GoogleSheetsClient(sa_file)
    
    SPREADSHEET_ID = "1Aspw3CnD0bgAqqZW4PoN-OOSSZBBtNrurTa3fy_56Tk"
    TAB_NAME = "Utenti"
    
    print(f"=== CONFIGURAZIONE FOGLIO UTENTI & ACCESSI ===")
    print(f"Spreadsheet ID: {SPREADSHEET_ID}")
    print(f"Tabella target: {TAB_NAME}")
    
    token = client._get_access_token()
    auth_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # 1. Verifica se il tab 'Utenti' esiste già o va creato
    meta_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}"
    meta = requests.get(meta_url, headers=auth_headers, timeout=15).json()
    sheet_id_num = None
    for s in meta.get("sheets", []):
        if s["properties"]["title"] == TAB_NAME:
            sheet_id_num = s["properties"]["sheetId"]
            break
            
    headers = ["Username", "Password", "Nome", "Ruolo", "CodiceAgente", "Email", "Note", "Attivo"]
    
    # Utenti iniziali di prova
    initial_users = [
        ["amministratore", "Clima1997", "Amministratore Climawell", "admin", "TUTTI", "amministrazione@climawell.it", "Gestione ordini e offerte di tutti gli agenti", "SI"],
        ["administrator", "Lisa4882", "SuperAdmin Climawell", "admin", "TUTTI", "amministrazione@climawell.it", "Accesso SuperAdmin di riserva e controllo globale", "SI"],
        ["admin", "clw2026!", "Admin Climawell", "admin", "TUTTI", "amministrazione@climawell.it", "Accesso di emergenza", "SI"],
        ["f.pontrelli", "clw2026!", "Francesco Pontrelli", "agent", "217", "c3296880020@gmail.com", "Agente Plus 217 (504 clienti)", "SI"],
        ["f.micozzi", "clw2026!", "Federico Micozzi", "agent", "788", "c3351828254@gmail.com", "Agente Plus 788 (486 clienti)", "SI"],
        ["f.poli", "clw2026!", "Poli Francesco", "agent", "1216", "f3491770901@gmail.com", "Agente Plus 1216 (262 clienti)", "SI"],
        ["d.voltarelli", "clw2026!", "Davide Voltarelli", "agent", "6299", "voltarelli@dierreonline.it", "Agente Plus 6299 (238 clienti)", "SI"],
        ["s.depalma", "clw2026!", "Savino De Palma", "agent", "215", "c3296880018@gmail.com", "Agente Plus 215 (198 clienti)", "SI"],
        ["l.depalma", "clw2026!", "Letizia De Palma", "agent", "2346", "", "Agente Plus 2346 (108 clienti)", "SI"],
        ["c.rygiewicz", "clw2026!", "Andrzej Rygiewicz", "agent", "6146", "a3292341156@gmail.com", "Agente Plus 6146 (95 clienti)", "SI"],
        ["c.semprepiovi", "clw2026!", "Chiara Semprepiovi", "agent", "10766", "chiarasemprepiovi@gmail.com", "Agente Plus 10766 (84 clienti)", "SI"],
        ["p.bernini", "clw2026!", "Paolo Bernini", "agent", "10877", "", "Agente Plus 10877 (81 clienti)", "SI"],
        ["g.fabris", "clw2026!", "Giorgio Fabris", "agent", "218", "c3295916850@gmail.com", "Agente Plus 218 (41 clienti)", "SI"],
        ["d.lupi", "clw2026!", "Daniele Lupi", "agent", "1136", "daniele.lupi.mail@gmail.com", "Agente Plus 1136 (22 clienti)", "SI"]
    ]
    
    sheet_data = [headers] + initial_users
    
    if sheet_id_num is None:
        print(f"Creazione del tab '{TAB_NAME}' nello spreadsheet...")
        add_sheet_req = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": TAB_NAME,
                            "gridProperties": {
                                "rowCount": max(len(sheet_data) + 30, 50),
                                "columnCount": len(headers) + 2
                            }
                        }
                    }
                }
            ]
        }
        res = requests.post(f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}:batchUpdate", headers=auth_headers, json=add_sheet_req, timeout=15).json()
        sheet_id_num = res["replies"][0]["addSheet"]["properties"]["sheetId"]
        print(f"  [OK] Tab '{TAB_NAME}' creato con SheetId {sheet_id_num}")
    else:
        print(f"Tab '{TAB_NAME}' già presente (SheetId {sheet_id_num}). Pulizia...")
        clear_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/'{TAB_NAME}'!A1:Z:clear"
        requests.post(clear_url, headers=auth_headers, timeout=15)
        
    # Scrittura dati
    print(f"Scrittura di {len(sheet_data)} righe utente...")
    range_str = f"'{TAB_NAME}'!A1:H{len(sheet_data)}"
    update_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{range_str}?valueInputOption=USER_ENTERED"
    res = requests.put(update_url, headers=auth_headers, json={"values": sheet_data}, timeout=15)
    if res.status_code != 200:
        raise RuntimeError(f"Errore scrittura utenti: {res.text}")
    print("  [OK] Utenti scritti con successo!")
    
    # Formattazione estetica
    print("Applicazione formattazione estetica (header blu notte, freeze riga 1, auto-fit)...")
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
    requests.post(f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}:batchUpdate", headers=auth_headers, json=format_req, timeout=15)
    print(f"\n[SUCCESSO] Foglio '{TAB_NAME}' pronto in Google Drive!")

if __name__ == "__main__":
    setup_utenti_sheet()

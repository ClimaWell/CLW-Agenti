import requests
from connettore import GoogleSheetsClient, load_config

cfg = load_config()
client = GoogleSheetsClient(cfg['google_sheets']['service_account_file'])
token = client._get_access_token()

SPREADSHEET_ID = "1g6zrWK_zZJZ82kdoNgda9KuoemYlSs0XGRRfJvoOvUk"
TAB_NAME = "q_listino_prezzi_catalogo"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# 1. Recupera sheetId
meta = requests.get(f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}", headers=headers).json()
sheet_id = None
row_count = 0
for s in meta.get("sheets", []):
    if s["properties"]["title"] == TAB_NAME:
        sheet_id = s["properties"]["sheetId"]
        row_count = s["properties"]["gridProperties"]["rowCount"]
        break

# 2. Imposta formato CURRENCY / NUMBER su colonna J
req = {
    "requests": [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 1,
                    "endRowIndex": row_count,
                    "startColumnIndex": 9,
                    "endColumnIndex": 10
                },
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {
                            "type": "CURRENCY",
                            "pattern": "#,##0.00 €"
                        }
                    }
                },
                "fields": "userEnteredFormat.numberFormat"
            }
        }
    ]
}
res = requests.post(f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}:batchUpdate", headers=headers, json=req)
print("Risultato batchUpdate:", res.status_code)

# 3. Leggi la cella specifica J per verificare formattedValue e effectiveFormat
url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}?ranges='{TAB_NAME}'!J2:J3&includeGridData=true"
res_grid = requests.get(url, headers=headers).json()
cell_data = res_grid["sheets"][0]["data"][0]["rowData"][0]["values"][0]
print("Cella J2:", json.dumps(cell_data, indent=2))


import requests
from connettore import GoogleSheetsClient, load_config

cfg = load_config()
client = GoogleSheetsClient(cfg['google_sheets']['service_account_file'])
token = client._get_access_token()

SPREADSHEET_ID = "1g6zrWK_zZJZ82kdoNgda9KuoemYlSs0XGRRfJvoOvUk"
TAB_NAME = "q_listino_prezzi_catalogo"

headers = {"Authorization": f"Bearer {token}"}

# Find row number of MS230
rows = client.read_range(SPREADSHEET_ID, f"'{TAB_NAME}'!A1:B13000")
ms230_row = None
for idx, r in enumerate(rows):
    if len(r) > 1 and "MS230" == str(r[1]).strip().upper():
        ms230_row = idx + 1 # 1-indexed
        break

print(f"MS230 si trova alla riga {ms230_row}")

# Get cell J{ms230_row}
url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}?ranges='{TAB_NAME}'!J{ms230_row}:J{ms230_row}&includeGridData=true"
res = requests.get(url, headers=headers).json()
cell = res["sheets"][0]["data"][0]["rowData"][0]["values"][0]
print("Dati cella MS230:")
print(cell)

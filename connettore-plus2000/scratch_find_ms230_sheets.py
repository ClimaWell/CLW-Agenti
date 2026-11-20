import json
import requests
from connettore import GoogleSheetsClient, load_config

cfg = load_config()
sa_file = cfg.get("google_sheets", {}).get("service_account_file", "service_account.json")
client = GoogleSheetsClient(sa_file)
token = client._get_access_token()

SPREADSHEET_ID = "1g6zrWK_zZJZ82kdoNgda9KuoemYlSs0XGRRfJvoOvUk"

# 1. Lettura con UNFORMATTED_VALUE
url_unf = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/'q_listino_prezzi_catalogo'!A1:N13000?valueRenderOption=UNFORMATTED_VALUE"
res_unf = requests.get(url_unf, headers={"Authorization": f"Bearer {token}"}).json()
rows_unf = res_unf.get("values", [])

for r in rows_unf:
    if len(r) > 1 and "MS230" == str(r[1]).strip().upper():
        print("MS230 (UNFORMATTED_VALUE):", r)
        print("  -> Tipo dato Prezzo:", type(r[9]), "Valore Prezzo:", r[9])
        break

# 2. Lettura con FORMATTED_VALUE
url_fmt = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/'q_listino_prezzi_catalogo'!A1:N13000?valueRenderOption=FORMATTED_VALUE"
res_fmt = requests.get(url_fmt, headers={"Authorization": f"Bearer {token}"}).json()
rows_fmt = res_fmt.get("values", [])

for r in rows_fmt:
    if len(r) > 1 and "MS230" == str(r[1]).strip().upper():
        print("MS230 (FORMATTED_VALUE):", r)
        break


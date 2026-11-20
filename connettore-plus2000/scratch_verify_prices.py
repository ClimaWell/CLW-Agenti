import pyodbc
from connettore import GoogleSheetsClient, load_config

cfg = load_config()
sa_file = cfg.get("google_sheets", {}).get("service_account_file", "service_account.json")
client = GoogleSheetsClient(sa_file)

# 1. Legge MS230 e primi 10 articoli dal Google Sheet
SPREADSHEET_ID = "1g6zrWK_zZJZ82kdoNgda9KuoemYlSs0XGRRfJvoOvUk"
TAB_NAME = "q_listino_prezzi_catalogo"

sheet_rows = client.read_range(SPREADSHEET_ID, f"'{TAB_NAME}'!A1:N50")
header = sheet_rows[0]
print("Intestazioni Sheet:", header)

art_in_sheet = {}
for r in sheet_rows[1:]:
    if len(r) > 9:
        caid = str(r[0]).strip()
        cod = str(r[1]).strip()
        pz = str(r[9]).strip()
        art_in_sheet[caid] = {"cod": cod, "pz_sheet": pz}

# Aggiungi MS230 se non nelle prime 50 righe
ms230_rows = client.read_range(SPREADSHEET_ID, f"'{TAB_NAME}'!A1:N13000")
for r in ms230_rows:
    if len(r) > 1 and "MS230" == str(r[1]).strip().upper():
        art_in_sheet[str(r[0]).strip()] = {"cod": str(r[1]).strip(), "pz_sheet": str(r[9]).strip()}
        break

caids = list(art_in_sheet.keys())
print(f"\nArticoli trovati da confrontare: {len(caids)}")

# 2. Query SQL Server per ricavare VEN1 per questi articoli
conn = pyodbc.connect('DSN=climawell;', autocommit=True)
cur = conn.cursor()

query = f"""
    WITH PrezziVen1 AS (
        SELECT CaId, Pz, DValidita,
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
    SELECT a.CaId, RTRIM(LTRIM(a.Ca)), ISNULL(p.Pz, 0), p.DValidita
    FROM Articoli a
    LEFT JOIN PrezziVen1 p ON a.CaId = p.CaId AND p.rn = 1
    WHERE a.CaId IN ({','.join(caids)})
"""
cur.execute(query)
sql_results = {str(r[0]): (r[1], float(r[2]), r[3]) for r in cur.fetchall()}

print("\n--- CONFRONTO PREZZO SHEET vs PREZZO SQL VEN1 ---")
for caid, info in art_in_sheet.items():
    if caid in sql_results:
        cod_sql, pz_sql, dval = sql_results[caid]
        print(f"CaId: {caid:8} | Cod: {info['cod']:15} | Sheet: {info['pz_sheet']:8} | SQL VEN1: {pz_sql:8.2f} (Validità: {dval})")
    else:
        print(f"CaId: {caid:8} | Cod: {info['cod']:15} | Sheet: {info['pz_sheet']:8} | SQL: Non trovato in Articoli")

conn.close()

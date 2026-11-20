import json
import requests
import pyodbc
from connettore import GoogleSheetsClient, load_config

def inspect_all():
    cfg = load_config()
    sa_file = cfg.get("google_sheets", {}).get("service_account_file", "service_account.json")
    client = GoogleSheetsClient(sa_file)
    token = client._get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Ispezione Foglio Google Articoli
    ss_id = "1g6zrWK_zZJZ82kdoNgda9KuoemYlSs0XGRRfJvoOvUk"
    print(f"=== ISPEZIONE FOGLIO GOOGLE: {ss_id} ===")
    r = requests.get(f"https://sheets.googleapis.com/v4/spreadsheets/{ss_id}", headers=headers)
    meta = r.json()
    print("Titolo foglio:", meta.get("properties", {}).get("title"))
    sheets = meta.get("sheets", [])
    for s in sheets:
        p = s["properties"]
        print(f" Tab: '{p['title']}', SheetId: {p['sheetId']}, Rows: {p.get('gridProperties', {}).get('rowCount')}")
    
    # Leggiamo le prime righe del primo tab
    first_tab = sheets[0]["properties"]["title"] if sheets else "Foglio1"
    rows = client.read_range(ss_id, f"'{first_tab}'!A1:Z5")
    print(f"\nPrime righe di '{first_tab}':")
    for row in rows:
        print(" ", row)

    # 2. Ispezione Tabelle Articoli in SQL Server
    print("\n=== ISPEZIONE TABELLE ARTICOLI IN SQL SERVER ===")
    sql_cfg = cfg["sql_server"]
    conn = pyodbc.connect(f"DSN={sql_cfg.get('dsn', 'climawell')};", autocommit=True)
    cursor = conn.cursor()
    
    # Tabelle che iniziano per Art o Mag
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE='BASE TABLE' 
          AND (TABLE_NAME LIKE 'Articoli%' OR TABLE_NAME LIKE 'Mag%' OR TABLE_NAME LIKE '%Giac%')
        ORDER BY TABLE_NAME
    """)
    art_tables = [row[0] for row in cursor.fetchall()]
    print("Tabelle trovate:", art_tables[:25])
    
    # Colonne principali di 'Articoli'
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'Articoli'
        ORDER BY ORDINAL_POSITION
    """)
    print("\nColonne tabella Articoli:")
    for col in cursor.fetchall():
        n, dt, l = col
        print(f"  {n}: {dt}" + (f"({l})" if l else ""))

    # Controllo giacenze in Magazzino / Articoli
    # Cerchiamo colonne per giacenza, disponibilità o tabelle giacenze
    cursor.execute("""
        SELECT TABLE_NAME, COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE COLUMN_NAME LIKE '%Giac%' OR COLUMN_NAME LIKE '%Dispon%' OR COLUMN_NAME LIKE '%Esist%'
    """)
    print("\nColonne Giacenza/Disponibilita:")
    for r in cursor.fetchall():
        print(f"  {r[0]}.{r[1]}")

    conn.close()

if __name__ == "__main__":
    inspect_all()

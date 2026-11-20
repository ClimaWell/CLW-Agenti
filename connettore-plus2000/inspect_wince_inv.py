import json
import os
import pyodbc

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_connection():
    cfg = load_config()["sql_server"]
    conn_str = f"DRIVER={{{cfg['driver']}}};SERVER={cfg['server']};DATABASE={cfg['database']};Trusted_Connection=yes;"
    return pyodbc.connect(conn_str, timeout=5)

def main():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Colonne di WinCeInv
    cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'WinCeInv'
    ORDER BY ORDINAL_POSITION
    """)
    cols = cursor.fetchall()
    print("--- COLONNE TABELLA WinCeInv ---")
    for c in cols:
        print(f"  {c[0]} ({c[1]}, nullable={c[3]})")
        
    # 2. Ultime 3 righe di WinCeInv per capire cosa conteneva
    print("\n--- ESEMPIO RECORD WinCeInv ---")
    cursor.execute("SELECT TOP 3 * FROM WinCeInv ORDER BY 1 DESC")
    col_names = [col[0] for col in cursor.description]
    for row in cursor.fetchall():
        d = dict(zip(col_names, row))
        print(" ", {k: v for k, v in d.items() if v is not None})
        
    # 3. Testo delle stored procedure chiave
    sps = ["sp_WinCeInv_GenRettifiche", "sp_WinCe_RettificaEsistenza"]
    for sp in sps:
        print(f"\n--- DEFINIZIONE {sp} ---")
        try:
            cursor.execute(f"EXEC sp_helptext '{sp}'")
            lines = [row[0] for row in cursor.fetchall()]
            print("".join(lines[:45])) # primi 45 righe
            if len(lines) > 45:
                print(f"... [altre {len(lines)-45} righe]")
        except Exception as e:
            print(f"Errore lettura {sp}: {e}")

if __name__ == "__main__":
    main()

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
    
    sps = ["sp_WinCeInv_GenRettifiche", "sp_WinCe_RettificaEsistenza", "sp_WinCeDoc_Conferma"]
    for sp in sps:
        print(f"\n==================== {sp} ====================")
        cursor.execute("SELECT definition FROM sys.sql_modules WHERE object_id = OBJECT_ID(?)", sp)
        row = cursor.fetchone()
        if row and row[0]:
            lines = row[0].splitlines()
            for l in lines[:70]:
                print(l)
            if len(lines) > 70:
                print(f"... [altre {len(lines)-70} righe]")
        else:
            print("Nessuna definizione trovata (potrebbe essere crittografata o assente)")

if __name__ == "__main__":
    main()

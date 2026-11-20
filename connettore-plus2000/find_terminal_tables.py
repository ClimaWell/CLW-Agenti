import json
import os
import pyodbc

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_connection():
    cfg = load_config()["sql_server"]
    dsn = cfg.get("dsn")
    if dsn:
        try:
            return pyodbc.connect(f"DSN={dsn};", timeout=5)
        except Exception:
            pass
    conn_str = f"DRIVER={{{cfg['driver']}}};SERVER={cfg['server']};DATABASE={cfg['database']};"
    if cfg.get("trusted_connection", "").lower() in ["yes", "true", "1"]:
        conn_str += "Trusted_Connection=yes;"
    else:
        conn_str += f"UID={cfg['username']};PWD={cfg['password']};"
    return pyodbc.connect(conn_str, timeout=5)

def main():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Cerca tabelle che contengono parole chiave come term, ce, inv, conta, spunt, lett, bar, palm, mag
    query_tables = """
    SELECT TABLE_SCHEMA, TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_NAME
    """
    cursor.execute(query_tables)
    all_tables = [row[1] for row in cursor.fetchall()]
    
    keywords = ["term", "ce", "inv", "conta", "spunt", "lett", "bar", "palm", "radio", "pda", "wce", "mobile", "allin", "giac"]
    found = []
    for t in all_tables:
        t_low = t.lower()
        if any(k in t_low for k in keywords):
            found.append(t)
            
    print(f"--- Totale tabelle nel DB: {len(all_tables)} ---")
    print(f"--- Tabelle candidate per terminali / inventario ({len(found)}): ---")
    for t in found:
        # Conta record
        try:
            cursor.execute(f"SELECT COUNT(*) FROM [{t}]")
            cnt = cursor.fetchone()[0]
            print(f"  {t} ({cnt} record)")
        except Exception as e:
            print(f"  {t} (errore count: {e})")
            
    # Controlliamo anche se ci sono stored procedure con nomi simili
    query_sp = """
    SELECT ROUTINE_NAME 
    FROM INFORMATION_SCHEMA.ROUTINES 
    WHERE ROUTINE_TYPE = 'PROCEDURE'
    ORDER BY ROUTINE_NAME
    """
    cursor.execute(query_sp)
    all_sp = [row[0] for row in cursor.fetchall()]
    sp_found = [sp for sp in all_sp if any(k in sp.lower() for k in keywords)]
    print(f"\n--- Stored Procedure candidate ({len(sp_found)}): ---")
    for sp in sp_found:
        print(f"  {sp}")

if __name__ == "__main__":
    main()

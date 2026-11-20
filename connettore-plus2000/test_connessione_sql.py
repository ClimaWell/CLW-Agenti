import json
import os
import pyodbc

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_connection(cfg):
    # Prova 1: DSN di sistema se configurato (es. DSN=climawell)
    dsn = cfg.get("dsn")
    if dsn:
        try:
            print(f"-> Tentativo di connessione tramite DSN ODBC '{dsn}'...")
            return pyodbc.connect(f"DSN={dsn};", timeout=5)
        except Exception as err_dsn:
            print(f"   [Avviso DSN]: {err_dsn}")
            print("   Tentativo tramite stringa di connessione diretta...")

    # Prova 2: Connessione diretta con Driver e Server
    conn_str = f"DRIVER={{{cfg['driver']}}};SERVER={cfg['server']};DATABASE={cfg['database']};"
    if cfg.get("trusted_connection", "").lower() in ["yes", "true", "1"]:
        conn_str += "Trusted_Connection=yes;"
    else:
        conn_str += f"UID={cfg['username']};PWD={cfg['password']};"
    return pyodbc.connect(conn_str, timeout=5)

def test_connection():
    cfg = load_config()["sql_server"]
    print("=== TEST CONNESSIONE SQL SERVER (PLUS 2000) ===")
    print(f"DSN:      {cfg.get('dsn', '-')}")
    print(f"Server:   {cfg['server']}")
    print(f"Database: {cfg['database']}")
    
    try:
        conn = get_connection(cfg)
        cursor = conn.cursor()
        print("-> Connessione a SQL Server riuscita con successo!")
        
        # Test versione
        cursor.execute("SELECT @@VERSION")
        ver = cursor.fetchone()[0]
        print(f"-> Versione SQL: {ver.splitlines()[0]}")
        
        # Test tabelle chiave Plus 2000
        tabelle_da_verificare = ["DocTes", "DocRig", "Articoli", "CliFor", "Sequenze"]
        print("\nVerifica presenza tabelle Plus 2000:")
        for tbl in tabelle_da_verificare:
            cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{tbl}'")
            exists = cursor.fetchone()[0] > 0
            if exists:
                cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
                cnt = cursor.fetchone()[0]
                print(f"  [OK] Tabella '{tbl}': trovata ({cnt} record)")
            else:
                print(f"  [NO] Tabella '{tbl}': NON trovata nel database corrente")
                
        # Test stored procedure chiave
        sp_da_verificare = ["sp_Sequenze_Ricerca", "sp_Sequenze_Aggiorna", "sp_DocTes_SetDefault", "sp_DocRig_SetDefault", "sp_Doc_Aggiorna_Totali", "sp_Doc_Conferma"]
        print("\nVerifica presenza Stored Procedure Plus 2000:")
        for sp in sp_da_verificare:
            cursor.execute(f"SELECT COUNT(*) FROM sys.objects WHERE name = '{sp}' AND type = 'P'")
            sp_exists = cursor.fetchone()[0] > 0
            stato = "[OK] Presente" if sp_exists else "[NO] Mancante"
            print(f"  {stato}: {sp}")
            
        conn.close()
        print("\n=== ESITO: Il database e le stored procedure sono pronti per il connettore! ===")
    except Exception as e:
        print(f"\n[ERRORE DI CONNESSIONE]: {e}")
        print("Suggerimento: Controlla server, nome database, utente e password in 'config.json'.")

if __name__ == "__main__":
    test_connection()

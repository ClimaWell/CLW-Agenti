import pyodbc
from connettore import load_config

cfg = load_config()
conn = pyodbc.connect(f"DSN={cfg['sql_server']['dsn']};", autocommit=True)
cur = conn.cursor()

print("--- LISTINI DISPONIBILI IN ListiniPrezzi ---")
cur.execute("SELECT JListino, COUNT(*) as cnt FROM ListiniPrezzi GROUP BY JListino ORDER BY cnt DESC")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} righe")

print("\n--- DESCRIZIONI DEI LISTINI (se esiste tabella Listini) ---")
try:
    cur.execute("SELECT JListino, DesListino FROM Listini")
    for r in cur.fetchall():
        print(f"  {r[0]}: {r[1]}")
except Exception as e:
    print("Errore tabella Listini:", e)

print("\n--- CASISTICA PREZZI VEN1 ---")
cur.execute("""
    SELECT 
        COUNT(DISTINCT a.CaId) as tot_art,
        COUNT(DISTINCT lp.CaId) as art_con_ven1,
        COUNT(DISTINCT CASE WHEN lp.Pz > 0 THEN lp.CaId END) as art_ven1_maggiori_zero
    FROM Articoli a
    LEFT JOIN ListiniPrezzi lp ON a.CaId = lp.CaId AND lp.JListino = 'VEN1'
    WHERE a.Blocco = 0
""")
row = cur.fetchone()
print(f"Articoli attivi totali: {row[0]}")
print(f"Articoli con almeno un record VEN1: {row[1]}")
print(f"Articoli con VEN1 > 0: {row[2]}")

conn.close()

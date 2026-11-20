import json
import pyodbc
from connettore import load_config

cfg = load_config()
conn = pyodbc.connect(f"DSN={cfg['sql_server']['dsn']};", autocommit=True)
cur = conn.cursor()

print("=== CAMPIONE DISPOSITIVI / DISEGNO IN PLUS 2000 ===")
cur.execute("""
    SELECT TOP 30 a.CaId, RTRIM(a.Ca) AS Codice, RTRIM(a.Marca) AS Marca, RTRIM(a.Disegno) AS Disegno
    FROM Articoli a
    WHERE a.Disegno IS NOT NULL AND RTRIM(a.Disegno) <> ''
    ORDER BY a.CaId DESC
""")
for r in cur.fetchall():
    print(f"CaId: {r[0]:<8} | Cod: {r[1]:<18} | Marca: {r[2]:<5} | Disegno: {r[3]}")

# Quanti articoli con giacenza > 0 o attivi hanno il campo Disegno?
cur.execute("""
    SELECT 
        COUNT(DISTINCT a.CaId) AS TotAttivi,
        COUNT(DISTINCT CASE WHEN a.Disegno IS NOT NULL AND RTRIM(a.Disegno) <> '' THEN a.CaId END) AS ConDisegno
    FROM Articoli a
    JOIN ArticoliContGen g ON a.CaId = g.CaId
    WHERE g.QtEsi > 0 AND a.Blocco = 0
""")
tot_attivi, con_dis = cur.fetchone()
print(f"\nArticoli con giacenza > 0: {tot_attivi}, di cui con campo Disegno: {con_dis}")

conn.close()

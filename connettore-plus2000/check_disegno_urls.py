import json
import pyodbc
from connettore import load_config

cfg = load_config()
conn = pyodbc.connect(f"DSN={cfg['sql_server']['dsn']};", autocommit=True)
cur = conn.cursor()

cur.execute("""
    SELECT 
        COUNT(*) AS TotAttivi,
        COUNT(NULLIF(RTRIM(a.Disegno), '')) AS ConDisegno,
        COUNT(NULLIF(RTRIM(a.CaProd), '')) AS ConCaProd
    FROM Articoli a
    JOIN ArticoliContGen g ON a.CaId = g.CaId
    WHERE g.QtEsi > 0 AND a.Blocco = 0
""")
tot, con_dis, con_caprod = cur.fetchone()
print(f"Articoli attivi a magazzino: {tot}")
print(f"  Con campo Disegno: {con_dis}")
print(f"  Con codice produttore (CaProd): {con_caprod}")

# Verifica URL validi su DomusPartes
# Proviamo a verificare se rispondono 200 via HTTP
import requests
test_urls = [
    "https://www.domuspartes.it/products_images/pre/assets/PAF/APM3010CR.jpg.jpg",
    "https://www.domuspartes.it/products_images/pre/assets/PAF/APM3010CR.jpg",
    "https://www.domuspartes.it/products_images/pre/assets/ZEN/charleston_b.jpg",
    "https://www.domuspartes.it/products_images/pre/assets/VAI/0020055184_B.JPG"
]
print("\n=== TEST ACCESSIBILITA URL SU DOMUSPARTES ===")
for u in test_urls:
    try:
        r = requests.head(u, timeout=5)
        print(f"Status {r.status_code} -> {u}")
    except Exception as e:
        print(f"Err {e} -> {u}")

conn.close()

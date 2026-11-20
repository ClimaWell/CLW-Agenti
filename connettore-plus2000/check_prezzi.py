import json
import pyodbc
from connettore import load_config

cfg = load_config()
conn = pyodbc.connect(f"DSN={cfg['sql_server']['dsn']};", autocommit=True)
cur = conn.cursor()

for caid in [766945, 705570, 1147917, 1094486]:
    print(f"\n--- CaId = {caid} ---")
    cur.execute("SELECT JListino, DValidita, Pz FROM ListiniPrezzi WHERE CaId = ? ORDER BY DValidita DESC", (caid,))
    for r in cur.fetchall()[:10]:
        print(" ", r)

conn.close()

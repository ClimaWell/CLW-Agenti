import pyodbc
from connettore import load_config

cfg = load_config()
conn = pyodbc.connect(f"DSN={cfg['sql_server']['dsn']};", autocommit=True)
cur = conn.cursor()

cur.execute("""
    WITH Giacenze AS (
        SELECT CaId, SUM(QtEsi) as TotEsi, SUM(QtDisp) as TotDisp
        FROM ArticoliContGen
        GROUP BY CaId
    ),
    MovimentiRecenti AS (
        SELECT DISTINCT r.CaId
        FROM DocRig r
        JOIN DocTes t ON r.DocId = t.DocId
        WHERE t.Anno >= 2025
    )
    SELECT 
        COUNT(*) as tot_attivi,
        COUNT(CASE WHEN g.TotEsi > 0 OR m.CaId IS NOT NULL THEN 1 END) as tot_filtrati
    FROM Articoli a
    LEFT JOIN Giacenze g ON a.CaId = g.CaId
    LEFT JOIN MovimentiRecenti m ON a.CaId = m.CaId
    WHERE a.Blocco = 0
""")
row = cur.fetchone()
print(f"Totale articoli a.Blocco = 0: {row[0]}")
print(f"Totale articoli con Giacenza > 0 o Movimentati >= 2025: {row[1]}")

conn.close()

import time
import pyodbc
from connettore import load_config

cfg = load_config()
conn = pyodbc.connect(f"DSN={cfg['sql_server']['dsn']};", autocommit=True)
cur = conn.cursor()

print("Testing query execution time...")
t0 = time.time()

query = """
    WITH PrezziVen1 AS (
        SELECT CaId, Pz, DValidita,
               ROW_NUMBER() OVER (
                   PARTITION BY CaId 
                   ORDER BY 
                       CASE WHEN DValidita <= CAST(CONVERT(varchar(8), GETDATE(), 112) AS INT) THEN 1 ELSE 0 END DESC,
                       DValidita DESC,
                       DMod DESC,
                       DIns DESC
               ) as rn
        FROM ListiniPrezzi
        WHERE JListino = 'VEN1'
    ),
    Giacenze AS (
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
    SELECT TOP 100
        a.CaId,
        RTRIM(LTRIM(a.Ca)) as CodiceArticolo,
        ISNULL(p.Pz, 0) as Prezzo,
        p.DValidita,
        ISNULL(g.TotEsi, 0) as Giacenza
    FROM Articoli a
    LEFT JOIN PrezziVen1 p ON a.CaId = p.CaId AND p.rn = 1
    LEFT JOIN Giacenze g ON a.CaId = g.CaId
    LEFT JOIN MovimentiRecenti m ON a.CaId = m.CaId
    WHERE a.Blocco = 0 AND (g.TotEsi > 0 OR m.CaId IS NOT NULL)
    ORDER BY g.TotEsi DESC, CodiceArticolo
"""
cur.execute(query)
rows = cur.fetchall()
t1 = time.time()
print(f"Esecuzione completata in {t1 - t0:.2f} secondi. Righe estratte: {len(rows)}")

# Verifica MS230 specificamente
for r in rows:
    if "MS230" in r[1]:
        print("MS230 nei top 100:", r)

cur.execute("""
    WITH PrezziVen1 AS (
        SELECT CaId, Pz, DValidita,
               ROW_NUMBER() OVER (
                   PARTITION BY CaId 
                   ORDER BY 
                       CASE WHEN DValidita <= CAST(CONVERT(varchar(8), GETDATE(), 112) AS INT) THEN 1 ELSE 0 END DESC,
                       DValidita DESC,
                       DMod DESC,
                       DIns DESC
               ) as rn
        FROM ListiniPrezzi
        WHERE JListino = 'VEN1'
    )
    SELECT a.CaId, a.Ca, p.Pz, p.DValidita
    FROM Articoli a
    LEFT JOIN PrezziVen1 p ON a.CaId = p.CaId AND p.rn = 1
    WHERE a.Ca = 'MS230'
""")
print("MS230 diretto:", cur.fetchall())

conn.close()

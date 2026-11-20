import pyodbc

conn = pyodbc.connect('DSN=climawell;', autocommit=True)
cursor = conn.cursor()

# Verifichiamo cosa estrae esattamente la CTE PrezziVen1 per MS230 (CaId = 15911)
cursor.execute("""
    WITH PrezziVen1 AS (
        SELECT CaId, Pz, DValidita, DMod, DIns,
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
    SELECT * FROM PrezziVen1 WHERE CaId = 15911
""")
rows = cursor.fetchall()
print("Risultato CTE PrezziVen1 per CaId = 15911:")
for r in rows:
    print(r)

# Controlliamo se per caso per MS230 c'è un altro CaId o CaId 1178636 (MS230-B)
cursor.execute("""
    WITH PrezziVen1 AS (
        SELECT CaId, Pz, DValidita, DMod, DIns,
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
    SELECT * FROM PrezziVen1 WHERE CaId = 1178636
""")
print("\nRisultato CTE PrezziVen1 per MS230-B (CaId = 1178636):")
for r in cursor.fetchall():
    print(r)

# Cerchiamo da dove diavolo esce 7.12 in TUTTO il database per MS230
cursor.execute("SELECT * FROM ListiniPrezzi WHERE CaId IN (15911, 1178636) AND (Pz BETWEEN 7.00 AND 7.30 OR Pz = 7.12)")
print("\nPrezzi vicini a 7.12 in ListiniPrezzi:")
for r in cursor.fetchall():
    print(r)

# Cerchiamo in DocRig se c'è 7.12
cursor.execute("""
    SELECT TOP 5 * FROM DocRig WHERE CaId IN (15911, 1178636)
""")
print("\nRighe DocRig per 15911 o 1178636:")
for r in cursor.fetchall():
    print(r)

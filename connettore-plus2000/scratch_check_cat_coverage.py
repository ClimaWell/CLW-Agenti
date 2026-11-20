import pyodbc
import json
import os

with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

conn = pyodbc.connect("DSN=climawell;", autocommit=True)
cursor = conn.cursor()

# Controlliamo la query usata in export_articoli.py per i 12.716 articoli
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
    SELECT 
        COUNT(*) as Totale,
        COUNT(CASE WHEN t_set.DesTab IS NOT NULL AND RTRIM(t_set.DesTab) <> '' THEN 1 END) as DesSet_OK,
        COUNT(CASE WHEN t_mac.DesMacroFamiglia IS NOT NULL AND RTRIM(t_mac.DesMacroFamiglia) <> '' THEN 1 END) as DesMac_OK,
        COUNT(CASE WHEN t_fam.DesFamiglia IS NOT NULL AND RTRIM(t_fam.DesFamiglia) <> '' THEN 1 END) as DesFam_OK,
        COUNT(CASE WHEN a.MarcaIdroBox IS NOT NULL AND RTRIM(a.MarcaIdroBox) <> '' THEN 1 END) as ConIdroBox
    FROM Articoli a
    LEFT JOIN Giacenze g ON a.CaId = g.CaId
    LEFT JOIN MovimentiRecenti m ON a.CaId = m.CaId
    LEFT JOIN TabDes t_set ON t_set.TpTab = 'SET' AND RTRIM(t_set.JTab) = RTRIM(a.JSettore)
    LEFT JOIN MacroFamiglie t_mac ON RTRIM(t_mac.JSettore) = RTRIM(a.JSettore) AND RTRIM(t_mac.JMacroFamiglia) = RTRIM(a.JMacroFamiglia)
    LEFT JOIN Famiglie t_fam ON RTRIM(t_fam.JSettore) = RTRIM(a.JSettore) AND RTRIM(t_fam.JMacroFamiglia) = RTRIM(a.JMacroFamiglia) AND RTRIM(t_fam.JFamiglia) = RTRIM(a.JFamiglia)
    WHERE a.Blocco = 0 AND (g.TotEsi > 0 OR m.CaId IS NOT NULL)
"""
cursor.execute(query)
row = cursor.fetchone()
print(f"Articoli esportati nel catalogo: {row[0]}")
print(f" - Settore descritto: {row[1]} / {row[0]}")
print(f" - Macrofamiglia descritta: {row[2]} / {row[0]}")
print(f" - Famiglia descritta: {row[3]} / {row[0]}")
print(f" - Con MarcaIdroBox: {row[4]} / {row[0]}")

# Mostriamo alcuni esempi dove mancano settore / macro / famiglia
cursor.execute("""
    SELECT TOP 10 a.Ca, a.Marca, a.JSettore, a.JMacroFamiglia, a.JFamiglia, a.MarcaIdroBox
    FROM Articoli a
    LEFT JOIN ArticoliContGen g ON a.CaId = g.CaId
    WHERE a.Blocco = 0 AND ISNULL(g.QtEsi, 0) > 0 
      AND (a.JSettore IS NULL OR RTRIM(a.JSettore) IN ('', '0', '00'))
""")
print("\nEsempi di articoli senza Settore:")
for r in cursor.fetchall():
    print(" ", r)

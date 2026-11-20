import pyodbc

conn = pyodbc.connect('DSN=climawell', autocommit=True)
cursor = conn.cursor()

query = """
    SELECT 
        c.JAgente as CodiceAgente,
        RTRIM(LTRIM(ISNULL(ag.RagSoc, 'SENZA NOME') + CASE WHEN ag.RagSup IS NOT NULL AND RTRIM(ag.RagSup) <> '' THEN ' ' + RTRIM(ag.RagSup) ELSE '' END)) as NomeAgente,
        RTRIM(LTRIM(ISNULL(ag.Telefono, ''))) as Telefono,
        RTRIM(LTRIM(ISNULL(ag.Cellulare, ''))) as Cellulare,
        RTRIM(LTRIM(ISNULL(ag.EMail, ''))) as Email,
        RTRIM(LTRIM(ISNULL(ag.EMailPEC, ''))) as PEC,
        RTRIM(LTRIM(ISNULL(ag.Indirizzo, ''))) as Indirizzo,
        RTRIM(LTRIM(ISNULL(ag.Citta, ''))) as Citta,
        RTRIM(LTRIM(ISNULL(ag.Provincia, ''))) as Pv,
        COUNT(DISTINCT c.JConto) as TotClientiAttivi,
        COUNT(DISTINCT CASE WHEN doc.MaxAnno >= 2024 OR c.DIns >= 20240101 THEN c.JConto END) as ClientiRecenti2024_2026,
        CASE WHEN ag.Bloccato = 1 THEN 'BLOCCATO' ELSE 'ATTIVO' END as StatoAgente
    FROM CliFor c
    LEFT JOIN CliFor ag ON ag.TpConto = 'F' AND ag.JConto = c.JAgente
    LEFT JOIN (
        SELECT JConto, MAX(Anno) as MaxAnno
        FROM DocTes
        WHERE TpConto = 'C'
        GROUP BY JConto
    ) doc ON c.JConto = doc.JConto
    WHERE c.TpConto = 'C' AND c.Bloccato = 0 AND c.JAgente > 0
    GROUP BY 
        c.JAgente,
        ag.RagSoc,
        ag.RagSup,
        ag.Telefono,
        ag.Cellulare,
        ag.EMail,
        ag.EMailPEC,
        ag.Indirizzo,
        ag.Citta,
        ag.Provincia,
        ag.Bloccato
    ORDER BY ClientiRecenti2024_2026 DESC, TotClientiAttivi DESC
"""

cursor.execute(query)
rows = cursor.fetchall()
print(f"Agenti trovati con clienti associati: {len(rows)}")
for r in rows:
    if r[10] > 0 or r[9] >= 50:
        print(f"Cod: {r[0]} | {r[1]} | Recenti: {r[10]} | Totali: {r[9]} | Cell: {r[3]} | Mail: {r[4]} | Stato: {r[11]}")

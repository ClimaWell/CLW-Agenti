import pyodbc

conn = pyodbc.connect('DSN=climawell', autocommit=True)
cursor = conn.cursor()

# Query completa clienti
query = """
    SELECT 
        c.JConto,
        RTRIM(LTRIM(c.RagSoc + CASE WHEN c.RagSup IS NOT NULL AND RTRIM(c.RagSup) <> '' THEN ' ' + RTRIM(c.RagSup) ELSE '' END)) as RagioneSociale,
        c.JAgente,
        ISNULL(ag.RagSoc, '') as NomeAgente,
        RTRIM(LTRIM(ISNULL(c.Indirizzo, ''))) as Indirizzo,
        RTRIM(LTRIM(ISNULL(c.Cap, ''))) as Cap,
        RTRIM(LTRIM(ISNULL(c.Citta, ''))) as Citta,
        RTRIM(LTRIM(ISNULL(c.Provincia, ''))) as Provincia,
        RTRIM(LTRIM(ISNULL(c.CodFiscale, ''))) as CodiceFiscale,
        RTRIM(LTRIM(ISNULL(c.PartitaIva, ''))) as PartitaIva,
        RTRIM(LTRIM(ISNULL(c.JPagamento, ''))) as CodicePagamento,
        RTRIM(LTRIM(ISNULL(c.JListino, ''))) as CodiceListino,
        RTRIM(LTRIM(ISNULL(ct.Telefono, ''))) as Telefono,
        RTRIM(LTRIM(ISNULL(ct.Cellulare, ''))) as Cellulare,
        RTRIM(LTRIM(ISNULL(ct.TeleFax, ''))) as Telefax,
        RTRIM(LTRIM(ISNULL(ct.EMail, ''))) as Email,
        ISNULL(doc.MaxAnno, 0) as UltimoAnnoDoc,
        CASE WHEN c.Bloccato = 1 THEN 'BLOCCATO' ELSE 'ATTIVO' END as Stato
    FROM CliFor c
    LEFT JOIN CliFor ag ON ag.TpConto = 'F' AND ag.JConto = c.JAgente
    LEFT JOIN (
        SELECT JConto, 
               MAX(Telefono) as Telefono, 
               MAX(Cellulare) as Cellulare, 
               MAX(TeleFax) as TeleFax, 
               MAX(EMail) as EMail
        FROM CliForContatti
        WHERE TpConto = 'C'
        GROUP BY JConto
    ) ct ON c.JConto = ct.JConto
    LEFT JOIN (
        SELECT JConto, MAX(Anno) as MaxAnno
        FROM DocTes
        WHERE TpConto = 'C'
        GROUP BY JConto
    ) doc ON c.JConto = doc.JConto
    WHERE c.TpConto = 'C' AND c.Bloccato = 0
    ORDER BY c.JAgente, RagioneSociale
"""

cursor.execute(query)
rows = cursor.fetchall()
print(f"Estratti {len(rows)} clienti attivi da Plus 2000.")
print("\nEsempio primi 3 record:")
for r in rows[:3]:
    print(r)

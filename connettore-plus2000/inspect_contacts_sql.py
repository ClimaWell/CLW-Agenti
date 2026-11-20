import pyodbc

conn = pyodbc.connect('DSN=climawell', autocommit=True)
cursor = conn.cursor()

cursor.execute("""
    SELECT 
        COUNT(*) as TotClienti,
        SUM(CASE WHEN LTRIM(RTRIM(ISNULL(Telefono, ''))) <> '' THEN 1 ELSE 0 END) as ConTelefono,
        SUM(CASE WHEN LTRIM(RTRIM(ISNULL(Cellulare, ''))) <> '' THEN 1 ELSE 0 END) as ConCellulare,
        SUM(CASE WHEN LTRIM(RTRIM(ISNULL(EMail, ''))) <> '' THEN 1 ELSE 0 END) as ConEMail,
        SUM(CASE WHEN LTRIM(RTRIM(ISNULL(EMailPEC, ''))) <> '' THEN 1 ELSE 0 END) as ConPEC,
        SUM(CASE WHEN LTRIM(RTRIM(ISNULL(OclMail, ''))) <> '' THEN 1 ELSE 0 END) as ConOclMail,
        SUM(CASE WHEN LTRIM(RTRIM(ISNULL(FatMail, ''))) <> '' THEN 1 ELSE 0 END) as ConFatMail
    FROM CliFor
    WHERE TpConto = 'C' AND Bloccato = 0
""")
print("Statistiche contatti direttamente in CliFor:")
print(cursor.fetchall())

# Campione di clienti recenti (2024-2026) con i loro contatti
cursor.execute("""
    SELECT TOP 10 
        c.JConto,
        c.RagSoc,
        c.Telefono,
        c.Cellulare,
        c.EMail,
        c.EMailPEC,
        c.OclMail,
        doc.MaxAnno
    FROM CliFor c
    JOIN (
        SELECT JConto, MAX(Anno) as MaxAnno
        FROM DocTes
        WHERE TpConto = 'C'
        GROUP BY JConto
    ) doc ON c.JConto = doc.JConto
    WHERE c.TpConto = 'C' AND c.Bloccato = 0 AND doc.MaxAnno >= 2024
      AND (LTRIM(RTRIM(ISNULL(c.Telefono, ''))) <> '' OR LTRIM(RTRIM(ISNULL(c.EMail, ''))) <> '' OR LTRIM(RTRIM(ISNULL(c.Cellulare, ''))) <> '')
""")
print("\nCampione contatti clienti recenti in CliFor:")
for r in cursor.fetchall():
    print(r)

import pyodbc

conn = pyodbc.connect('DSN=climawell', autocommit=True)
cursor = conn.cursor()

cursor.execute("""
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'CliFor'
    ORDER BY ORDINAL_POSITION
""")
cols = [r[0] for r in cursor.fetchall()]
print("TUTTE LE COLONNE DI CliFor:")
print(cols)

# Campioni di clienti con JAgente
cursor.execute("""
    SELECT TOP 5 JConto, RagSoc, RagSup, Indirizzo, Cap, Provincia, CodFiscale, PartitaIva, JPagamento, JListino, JAgente, Bloccato
    FROM CliFor
    WHERE TpConto = 'C' AND JAgente > 0
""")
print("\nCampione clienti con JAgente:")
for r in cursor.fetchall():
    print(r)

# Distribuzione clienti per JAgente
cursor.execute("""
    SELECT JAgente, COUNT(*) as TotClienti, SUM(CASE WHEN Bloccato = 0 THEN 1 ELSE 0 END) as Attivi
    FROM CliFor
    WHERE TpConto = 'C' AND JAgente > 0
    GROUP BY JAgente
    ORDER BY TotClienti DESC
""")
print("\nDistribuzione per Agente (JAgente, Totale, Non Bloccati):")
for r in cursor.fetchall():
    print(r)

# Controlliamo la tabella Agenti
cursor.execute("""
    SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%Agent%'
""")
print("\nTabelle Agenti:", cursor.fetchall())

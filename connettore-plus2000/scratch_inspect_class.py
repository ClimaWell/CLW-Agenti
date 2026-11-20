import pyodbc

conn = pyodbc.connect('DSN=climawell;', autocommit=True)
cursor = conn.cursor()

for table in ['MarcheFamiglie', 'MarcheMacroFamiglie', 'TabDes']:
    cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'")
    cols = [f"{r[0]} ({r[1]})" for r in cursor.fetchall()]
    print(f"\nColonne {table}:")
    print(", ".join(cols))

# Controlliamo quante righe in MarcheFamiglie e MarcheMacroFamiglie
cursor.execute("SELECT COUNT(*) FROM MarcheMacroFamiglie")
print("\nRighe MarcheMacroFamiglie:", cursor.fetchone()[0])
cursor.execute("SELECT TOP 5 * FROM MarcheMacroFamiglie")
for r in cursor.fetchall():
    print(" ", r)

cursor.execute("SELECT COUNT(*) FROM MarcheFamiglie")
print("\nRighe MarcheFamiglie:", cursor.fetchone()[0])
cursor.execute("SELECT TOP 5 * FROM MarcheFamiglie")
for r in cursor.fetchall():
    print(" ", r)

# Controlliamo la copertura di JSettore, JMacroFamiglia, JFamiglia sugli articoli attivi
cursor.execute("""
    SELECT 
        COUNT(*) as TotArticoli,
        COUNT(CASE WHEN JSettore IS NOT NULL AND RTRIM(JSettore) NOT IN ('', '0', '00') THEN 1 END) as ConSettore,
        COUNT(CASE WHEN JMacroFamiglia IS NOT NULL AND RTRIM(JMacroFamiglia) NOT IN ('', '0', '00', '000') THEN 1 END) as ConMacro,
        COUNT(CASE WHEN JFamiglia IS NOT NULL AND RTRIM(JFamiglia) NOT IN ('', '0', '00', '000') THEN 1 END) as ConFam,
        COUNT(CASE WHEN MarcaIdroBox IS NOT NULL AND RTRIM(MarcaIdroBox) <> '' THEN 1 END) as ConMarcaIdroBox
    FROM Articoli
    WHERE Blocco = 0
""")
row = cursor.fetchone()
print(f"\nArticoli Attivi (Blocco = 0): {row[0]}")
print(f" - Con Settore: {row[1]}")
print(f" - Con Macrofamiglia: {row[2]}")
print(f" - Con Famiglia: {row[3]}")
print(f" - Con MarcaIdroBox: {row[4]}")

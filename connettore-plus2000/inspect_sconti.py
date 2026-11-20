import pyodbc

conn = pyodbc.connect('DSN=climawell', autocommit=True)
cursor = conn.cursor()

# Tabelle relative a Sconti
cursor.execute("""
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE='BASE TABLE' AND (TABLE_NAME LIKE '%Scont%' OR TABLE_NAME LIKE '%Sc%')
    ORDER BY TABLE_NAME
""")
tables = [r[0] for r in cursor.fetchall()]
print("Tabelle Sconti:", [t for t in tables if 'scont' in t.lower()])

# Controlliamo la tabella sconti (es. Sconti, TabSconti, ScontiVen, ScontiRighe, ecc.)
for tbl in ['Sconti', 'TabSconti', 'ScontiVen', 'ScontiAcq', 'ScontiArticoli', 'ScontiClienti', 'ScontiRig']:
    try:
        cursor.execute(f"SELECT TOP 3 * FROM {tbl}")
        cols = [d[0] for d in cursor.description]
        print(f"\nTabella {tbl} (colonne: {cols}):")
        for row in cursor.fetchall():
            print(" ", row)
    except:
        pass

# Cerchiamo colonne JScontoVen nel database
cursor.execute("""
    SELECT TABLE_NAME, COLUMN_NAME 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE COLUMN_NAME = 'JScontoVen' OR COLUMN_NAME = 'JSconto'
""")
print("\nTabelle con JScontoVen / JSconto:")
for r in cursor.fetchall():
    print(f"  {r[0]}.{r[1]}")

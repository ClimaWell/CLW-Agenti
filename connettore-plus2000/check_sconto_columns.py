import pyodbc

try:
    conn = pyodbc.connect('DSN=climawell;', autocommit=True)
    cur = conn.cursor()

    cur.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'DocTes' AND (COLUMN_NAME LIKE '%scon%' OR COLUMN_NAME LIKE '%sc%')")
    print("DocTes sconto cols:")
    for row in cur.fetchall():
        print(f"  {row[0]} ({row[1]})")

    cur.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'DocRig' AND (COLUMN_NAME LIKE '%scon%' OR COLUMN_NAME LIKE '%sc%')")
    print("\nDocRig sconto cols:")
    for row in cur.fetchall():
        print(f"  {row[0]} ({row[1]})")

    conn.close()
except Exception as e:
    print(f"Error: {e}")

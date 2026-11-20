import pyodbc
conn = pyodbc.connect('DSN=climawell;', autocommit=True)
cur = conn.cursor()
cur.execute("""
    SELECT r.DocId, t.TpDoc, t.YDoc, t.DDoc, t.TpConto, t.JConto, r.PzLordo, r.PzNetto, r.JListino
    FROM DocRig r
    JOIN DocTes t ON r.DocId = t.DocId
    WHERE r.CaId = 15911 AND (r.PzNetto BETWEEN 7.11 AND 7.14 OR r.PzLordo BETWEEN 7.11 AND 7.14)

""")
for row in cur.fetchall():
    print(row)
conn.close()

import pyodbc

conn = pyodbc.connect('DSN=climawell;', autocommit=True)
cur = conn.cursor()

print("--- DOCTES OFC 3770 ---")
cur.execute("SELECT TOP 1 * FROM DocTes WHERE TpDoc = 'OFC' AND YDoc = 3770")
cols = [col[0] for col in cur.description]
row = cur.fetchone()
if row:
    data_tes = dict(zip(cols, [str(v) if v is not None else None for v in row]))
    for k, v in data_tes.items():
        if v is not None and v != '' and v != '0':
            print(f"  {k} = {v}")
    doc_id = row[cols.index('DocId')]
    print(f"\nDocId = {doc_id}")

    print("\n--- DOCRIG OFC 3770 ---")
    cur.execute(f"SELECT * FROM DocRig WHERE DocId = {doc_id}")
    r_cols = [c[0] for c in cur.description]
    for r in cur.fetchall():
        data_rig = dict(zip(r_cols, [str(v) if v is not None else None for v in r]))
        for k, v in data_rig.items():
            if v is not None and v != '' and v != '0':
                print(f"    {k} = {v}")
        print("    " + "-"*40)
else:
    print("OFC 3770 non trovata!")

print("\n--- DOCTES 3771 (la nostra appena creata) ---")
cur.execute("SELECT TOP 1 * FROM DocTes WHERE YDoc = 3771")
cols1 = [col[0] for col in cur.description]
r1 = cur.fetchone()
if r1:
    d1 = dict(zip(cols1, [str(v) if v is not None else None for v in r1]))
    for k, v in d1.items():
        if v is not None and v != '' and v != '0':
            print(f"  {k} = {v}")
    print("\n--- DOCRIG 3771 ---")
    cur.execute(f"SELECT * FROM DocRig WHERE DocId = {r1[cols1.index('DocId')]}")
    r_cols1 = [c[0] for c in cur.description]
    for r in cur.fetchall():
        dr1 = dict(zip(r_cols1, [str(v) if v is not None else None for v in r]))
        for k, v in dr1.items():
            if v is not None and v != '' and v != '0':
                print(f"    {k} = {v}")

conn.close()

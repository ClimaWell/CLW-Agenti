import pyodbc

conn = pyodbc.connect('DSN=climawell;', autocommit=True)
cursor = conn.cursor()

# 1. Cerca articolo MS230
cursor.execute("SELECT CaId, Ca, DesArt, DesSup, Marca, JSettore, JMacroFamiglia, JFamiglia FROM Articoli WHERE Ca = 'MS230' OR Ca LIKE '%MS230%'")
articoli = cursor.fetchall()
print("Articoli trovati con codice MS230:")
for a in articoli:
    print(a)

if not articoli:
    print("Nessun articolo trovato con Ca = MS230, proviamo a cercare in CaProd o Descrizione...")
    cursor.execute("SELECT TOP 5 CaId, Ca, DesArt, CaProd FROM Articoli WHERE DesArt LIKE '%MS230%' OR CaProd LIKE '%MS230%'")
    for a in cursor.fetchall():
        print(a)
    exit()

caid = articoli[0][0]
print(f"\n--- CaId per MS230: {caid} ---")

# 2. Cerca tutti i record in ListiniPrezzi per questo CaId
cursor.execute(f"""
    SELECT JListino, Pz, DValidita, DIns, DMod, UtenteIns, UtenteMod
    FROM ListiniPrezzi
    WHERE CaId = {caid}
    ORDER BY JListino, DValidita DESC, DMod DESC, DIns DESC
""")
print("\nRecord in ListiniPrezzi:")
for r in cursor.fetchall():
    print(r)

# 3. Controlliamo anche altre tabelle di listino o prezzi (Listini, LisFor, ecc.)
cursor.execute(f"""
    SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_NAME LIKE '%listin%' OR TABLE_NAME LIKE '%prezz%'
    ORDER BY TABLE_NAME
""")
print("\nTabelle con 'listin' o 'prezz':")
for r in cursor.fetchall():
    print(" -", r[0])

# 4. Controlliamo gli ultimi documenti (vendita/acquisto) per questo articolo
cursor.execute(f"""
    SELECT TOP 5 t.TpDoc, t.NumDoc, t.DDoc, r.Pz, r.Sct1, r.Sct2, r.Sct3, r.PzNetto, t.JTipoDoc, t.CodCliFor
    FROM DocRig r
    JOIN DocTes t ON r.DocId = t.DocId
    WHERE r.CaId = {caid}
    ORDER BY t.DDoc DESC
""")
print("\nUltimi movimenti in DocRig per MS230:")
for r in cursor.fetchall():
    print(r)

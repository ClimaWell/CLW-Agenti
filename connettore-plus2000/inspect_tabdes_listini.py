import json
import pyodbc
from connettore import load_config

cfg = load_config()
conn = pyodbc.connect(f"DSN={cfg['sql_server']['dsn']};", autocommit=True)
cur = conn.cursor()

print("=== PARAMGEN / PARAMWEB IMMAGINI ===")
try:
    cur.execute("SELECT PathImmaginiArt, TpPathImmaginiArt FROM ParamGen")
    for r in cur.fetchall():
        print("ParamGen:", r)
except Exception as e:
    print("Err ParamGen:", e)

try:
    cur.execute("SELECT PathImmaginiArt, PathImmaginiArtUnc, PathImmaginiOff, PathImmaginiOffUnc FROM ParamWeb")
    for r in cur.fetchall():
        print("ParamWeb:", r)
except Exception as e:
    print("Err ParamWeb:", e)

# Quanti articoli hanno il campo Disegno popolato?
print("\n=== CONTEGGIO ARTICOLI CON CAMPO DISEGNO ===")
cur.execute("SELECT COUNT(*), COUNT(NULLIF(RTRIM(Disegno), '')) FROM Articoli")
tot, con_disegno = cur.fetchone()
print(f"Totale articoli: {tot}, Articoli con campo Disegno valorizzato: {con_disegno}")

# Esempi di campo Disegno
print("\n=== ESEMPI CAMPO DISEGNO ===")
cur.execute("SELECT TOP 15 CaId, Ca, Marca, Disegno FROM Articoli WHERE Disegno IS NOT NULL AND RTRIM(Disegno) <> ''")
for r in cur.fetchall():
    print(r)

# Quanti record in WebArticoli?
print("\n=== WEBARICOLI ===")
try:
    cur.execute("SELECT COUNT(*) FROM WebArticoli")
    print("WebArticoli count:", cur.fetchone()[0])
    cur.execute("SELECT TOP 5 Ca, FileImgArticolo FROM WebArticoli WHERE FileImgArticolo IS NOT NULL AND RTRIM(FileImgArticolo) <> ''")
    for r in cur.fetchall():
        print(r)
except Exception as e:
    print("Err WebArticoli:", e)

conn.close()

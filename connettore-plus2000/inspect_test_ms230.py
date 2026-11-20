import json
import os
import pyodbc

BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
if not os.path.exists(CONFIG_PATH):
    CONFIG_PATH = os.path.join(BASE_DIR, "connettore-plus2000", "config.json")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_connection():
    cfg = load_config()["sql_server"]
    conn_str = f"DRIVER={{{cfg['driver']}}};SERVER={cfg['server']};DATABASE={cfg['database']};Trusted_Connection=yes;"
    return pyodbc.connect(conn_str, timeout=5)

def main():
    conn = get_connection()
    cursor = conn.cursor()
    ca_id = 15911
    
    print("=================================================================")
    print("1. RECORD TROVATO IN WinCeInv OGGI (2026-10-19):")
    print("=================================================================")
    cursor.execute("""
    SELECT RegId, DReg, OraReg, DDoc, JDep, JVano, JTerminale, CaId, VarId, Um, Qt, Note
    FROM WinCeInv 
    WHERE RegId = 4580
    """)
    row = cursor.fetchone()
    cols = ["RegId", "DReg", "OraReg", "DDoc", "JDep", "JVano", "JTerminale", "CaId", "VarId", "Um", "Qt", "Note"]
    for c, val in zip(cols, row):
        print(f"  {c:12}: {val}")

    # 2. Vediamo le colonne reali di DocTes per capire il movimento 1737
    print("\n=================================================================")
    print("2. COLONNE DI DocTes:")
    print("=================================================================")
    cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'DocTes'
    """)
    dostes_cols = cursor.fetchall()
    col_names = [c[0] for c in dostes_cols]
    print("  Colonne trovate:", ", ".join(col_names[:25]), "...")
    
    # 3. Cerchiamo dove compare 1737 in DocTes
    candidate_id_cols = [c for c in col_names if any(x in c.lower() for x in ["doc", "num", "nr", "mov", "reg", "id"])]
    print("\n  Colonne numeriche candidate in DocTes:", candidate_id_cols)
    
    found_doc = False
    for col in candidate_id_cols:
        try:
            cursor.execute(f"SELECT TOP 1 * FROM DocTes WHERE [{col}] = 1737")
            r = cursor.fetchone()
            if r:
                print(f"\n  >>> TROVATO DOCUMENTO CON 1737 nella colonna [{col}]!")
                d = dict(zip(col_names, r))
                for k, v in d.items():
                    if v is not None and str(v).strip() != "":
                        print(f"     {k}: {v}")
                found_doc = True
                
                # Cerchiamo le righe di questo documento
                doc_key_val = d.get("DocId", 1737)
                cursor.execute("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'DocRig'
                """)
                rig_cols = [rc[0] for rc in cursor.fetchall()]
                cursor.execute(f"SELECT * FROM DocRig WHERE DocId = ?", doc_key_val)
                print(f"\n  >>> RIGHE (DocRig) PER DocId={doc_key_val}:")
                for rig in cursor.fetchall():
                    rd = dict(zip(rig_cols, rig))
                    filtered_rd = {k: v for k, v in rd.items() if v is not None and str(v).strip() != ""}
                    print("    ", filtered_rd)
                break
        except Exception:
            pass
            
    if not found_doc:
        print("\n  Nessun record con 1737 trovato in DocTes. Cerco in MovMag o altre tabelle...")
        # Controlliamo tabelle movimenti
        cursor.execute("""
        SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME LIKE 'Mov%' OR TABLE_NAME LIKE 'Giac%'
        """)
        for tbl in cursor.fetchall():
            t_name = tbl[0]
            try:
                cursor.execute(f"SELECT TOP 1 * FROM [{t_name}] WHERE 1737 IN (SELECT 1737)")
            except:
                pass

if __name__ == "__main__":
    main()

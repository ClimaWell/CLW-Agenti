import json
import os
import pyodbc

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

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
    ca_id = 15911 # MS230
    
    print("=================================================================")
    print("1. LISTINI ESISTENTI IN ListiniPrezzi:")
    print("=================================================================")
    cursor.execute("""
    SELECT JListino, COUNT(*) as NumPrezzi
    FROM ListiniPrezzi
    GROUP BY JListino
    ORDER BY NumPrezzi DESC
    """)
    for r in cursor.fetchall():
        print(f"  Listino: {r[0]:15} -> {r[1]} prezzi registrati")
        
    print("\n=================================================================")
    print("2. COLONNE COSTO / VALORE IN ArticoliContGen:")
    print("=================================================================")
    cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'ArticoliContGen'
    """)
    for r in cursor.fetchall():
        col_name = r[0]
        if any(x in col_name.lower() for x in ["cs", "cost", "val", "med", "ult", "prez", "pz"]):
            print(f"  ArticoliContGen.{col_name} ({r[1]})")
            
    print("\n=================================================================")
    print("3. COLONNE COSTO / PREZZO IN Articoli:")
    print("=================================================================")
    cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'Articoli' AND (
        COLUMN_NAME LIKE '%cs%' OR COLUMN_NAME LIKE '%cost%' OR 
        COLUMN_NAME LIKE '%pz%' OR COLUMN_NAME LIKE '%prez%' OR 
        COLUMN_NAME LIKE '%scont%'
    )
    """)
    for r in cursor.fetchall():
        print(f"  Articoli.{r[0]} ({r[1]})")

    print("\n=================================================================")
    print(f"4. DATI COMPLETI PER L'ARTICOLO TEST MS230 (CaId {ca_id}):")
    print("=================================================================")
    # Listini per MS230
    cursor.execute("""
    SELECT JListino, DValidita, Pz, Sconto1, Sconto2, Sconto3
    FROM ListiniPrezzi
    WHERE CaId = ?
    ORDER BY JListino, DValidita DESC
    """, ca_id)
    print("  ListiniPrezzi per MS230:")
    for r in cursor.fetchall():
        print("   ", r)
        
    # ArticoliContGen per MS230
    cursor.execute("SELECT * FROM ArticoliContGen WHERE CaId = ?", ca_id)
    cols = [c[0] for c in cursor.description]
    row = cursor.fetchone()
    if row:
        d = dict(zip(cols, row))
        print("\n  ArticoliContGen per MS230:")
        for k, v in d.items():
            if v is not None and str(v) != "0" and str(v) != "0.00000":
                print(f"    {k}: {v}")
                
    # Ultimi acquisti e vendite da DocRig
    print("\n=================================================================")
    print("5. ULTIMI MOVIMENTI ACQUISTO / VENDITA IN DocRig PER MS230:")
    print("=================================================================")
    cursor.execute("""
    SELECT TOP 5 
        t.DocId, t.DDoc, t.CauId, t.DesCau, t.TpDoc,
        r.Prezzo, r.Sconto, r.Qta, r.Netto
    FROM DocRig r
    JOIN DocTes t ON r.DocId = t.DocId
    WHERE r.CaId = ?
    ORDER BY t.DDoc DESC, t.DocId DESC
    """, ca_id)
    cols_doc = [c[0] for c in cursor.description]
    for r in cursor.fetchall():
        d = dict(zip(cols_doc, r))
        print("   ", d)

if __name__ == "__main__":
    main()

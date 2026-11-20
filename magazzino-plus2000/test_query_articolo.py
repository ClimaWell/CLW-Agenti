import json
import os
import pyodbc

BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, "..", "connettore-plus2000", "config.json")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_connection():
    cfg = load_config()["sql_server"]
    conn_str = f"DRIVER={{{cfg['driver']}}};SERVER={cfg['server']};DATABASE={cfg['database']};Trusted_Connection=yes;"
    return pyodbc.connect(conn_str, timeout=5)

def search_article(query_term):
    conn = get_connection()
    cursor = conn.cursor()
    term = query_term.strip()
    
    sql = """
    WITH Giacenze AS (
        SELECT CaId, SUM(QtEsi) as TotEsi, SUM(QtDisp) as TotDisp
        FROM ArticoliContGen
        GROUP BY CaId
    )
    SELECT TOP 10
        a.CaId,
        RTRIM(LTRIM(a.Ca)) as CodiceArticolo,
        RTRIM(LTRIM(a.DesArt + CASE WHEN a.DesSup IS NOT NULL AND RTRIM(a.DesSup) <> '' THEN ' ' + RTRIM(a.DesSup) ELSE '' END)) as Descrizione,
        RTRIM(LTRIM(ISNULL(a.Marca, ''))) as Marca,
        RTRIM(LTRIM(ISNULL(a.JUbiArt, ''))) as Ubicazione,
        RTRIM(LTRIM(ISNULL(a.Um, 'NR'))) as Um,
        ISNULL(g.TotEsi, 0) as Giacenza,
        ISNULL(g.TotDisp, 0) as Disponibilita,
        (SELECT TOP 1 RTRIM(LTRIM(ac.CaCod)) FROM ArticoliCodici ac WHERE ac.CaId = a.CaId ORDER BY ac.Riga) as Ean
    FROM Articoli a
    LEFT JOIN Giacenze g ON a.CaId = g.CaId
    WHERE a.Ca = ? 
       OR a.CaId = TRY_CAST(? AS INT)
       OR a.CaProd = ?
       OR EXISTS (SELECT 1 FROM ArticoliCodici ac WHERE ac.CaId = a.CaId AND ac.CaCod = ?)
       OR a.Ca LIKE ?
    ORDER BY CASE WHEN a.Ca = ? THEN 0 ELSE 1 END, CodiceArticolo
    """
    like_param = f"%{term}%"
    cursor.execute(sql, term, term, term, term, like_param, term)
    rows = cursor.fetchall()
    
    results = []
    col_names = [col[0] for col in cursor.description]
    for r in rows:
        results.append(dict(zip(col_names, r)))
    conn.close()
    return results

if __name__ == "__main__":
    res = search_article("MS230")
    print(f"Risultati trovati: {len(res)}")
    for r in res:
        print(r)

import json
import pyodbc

cfg_path = r"c:\Users\Daniele\Documents\plus-2026\connettore-plus2000\config.json"
with open(cfg_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)["sql_server"]

dsn = cfg.get("dsn", "climawell")
conn = pyodbc.connect(f"DSN={dsn};", autocommit=True, timeout=10)
cursor = conn.cursor()

query = """
    WITH Giacenze AS (
        SELECT CaId, SUM(QtEsi) AS Giacenza, SUM(QtDisp) AS Disponibile
        FROM ArticoliContGen
        GROUP BY CaId
        HAVING SUM(QtEsi) > 0
    ),
    UltimoAcquistoAssoluto AS (
        SELECT 
            r.CaId,
            t.DDoc AS DataAcquisto,
            t.JConto AS FornitoreId,
            f.RagSoc AS FornitoreNome,
            t.TpDoc,
            t.YDoc AS NumDoc,
            r.PzNetto,
            r.PzLordo,
            ROW_NUMBER() OVER (PARTITION BY r.CaId ORDER BY t.DDoc DESC, t.DocId DESC, r.Riga DESC) AS rn
        FROM DocRig r
        JOIN DocTes t ON r.DocId = t.DocId
        LEFT JOIN CliFor f ON t.JConto = f.JConto AND f.TpConto = 'F'
        WHERE t.TpConto = 'F'
    )
    SELECT 
        a.CaId,
        RTRIM(LTRIM(a.Ca)) AS Codice,
        RTRIM(LTRIM(a.DesArt)) AS Descrizione,
        g.Giacenza,
        u.DataAcquisto,
        u.FornitoreId,
        u.FornitoreNome,
        u.TpDoc,
        u.NumDoc,
        u.PzNetto
    FROM Giacenze g
    JOIN Articoli a ON g.CaId = a.CaId
    LEFT JOIN UltimoAcquistoAssoluto u ON g.CaId = u.CaId AND u.rn = 1
    WHERE u.FornitoreId = 661 OR (u.FornitoreId IS NULL AND a.JFornitore = 661)
    ORDER BY u.DataAcquisto ASC, g.Giacenza DESC
"""
cursor.execute(query)
rows = cursor.fetchall()
print(f"Totale articoli il cui ULTIMO fornitore effettivo è Cambielli (661): {len(rows)}")

print("\nPrimi 15 articoli più vecchi:")
for r in rows[:15]:
    d_raw = str(r[4] or '')
    d_fmt = f"{d_raw[6:8]}/{d_raw[4:6]}/{d_raw[0:4]}" if len(d_raw) == 8 else "Storico"
    print(f"Cod: {r[1]:<16} | Giac: {r[3]:>4.0f} pz | Data: {d_fmt} | Forn: {r[5]} ({str(r[6])[:15]}) | Pz: {r[9] or 0:>7.2f} € | {r[2][:35]}")

print("\nUltimi 10 articoli più recenti:")
for r in rows[-10:]:
    d_raw = str(r[4] or '')
    d_fmt = f"{d_raw[6:8]}/{d_raw[4:6]}/{d_raw[0:4]}" if len(d_raw) == 8 else "Storico"
    print(f"Cod: {r[1]:<16} | Giac: {r[3]:>4.0f} pz | Data: {d_fmt} | Forn: {r[5]} ({str(r[6])[:15]}) | Pz: {r[9] or 0:>7.2f} € | {r[2][:35]}")

conn.close()

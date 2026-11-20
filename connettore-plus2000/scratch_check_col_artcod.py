import pyodbc
from connettore import GoogleSheetsClient, load_config

cfg = load_config()
client = GoogleSheetsClient(cfg['google_sheets']['service_account_file'])
sheet_rows = client.read_range("1g6zrWK_zZJZ82kdoNgda9KuoemYlSs0XGRRfJvoOvUk", "'q_listino_prezzi_catalogo'!A1:N20")

print("Prime 5 righe dello Sheet:")
for r in sheet_rows[:6]:
    print(r)

# Test query for these CaIds
caids = [r[0] for r in sheet_rows[1:10] if r and r[0].isdigit()]
print("\nCaIds da testare:", caids)

conn = pyodbc.connect('DSN=climawell;', autocommit=True)
cur = conn.cursor()
cur.execute(f"""
    WITH PrezziVen1 AS (
        SELECT CaId, Pz, DValidita,
               ROW_NUMBER() OVER (
                   PARTITION BY CaId 
                   ORDER BY 
                       CASE WHEN DValidita <= CAST(CONVERT(varchar(8), GETDATE(), 112) AS INT) THEN 1 ELSE 0 END DESC,
                       DValidita DESC,
                       DMod DESC,
                       DIns DESC
               ) as rn
        FROM ListiniPrezzi
        WHERE JListino = 'VEN1'
    )
    SELECT a.CaId, a.Ca, p.Pz
    FROM Articoli a
    LEFT JOIN PrezziVen1 p ON a.CaId = p.CaId AND p.rn = 1
    WHERE a.CaId IN ({','.join(caids)})
""")
print("\nRisultati da SQL Server:")
for r in cur.fetchall():
    print(r)




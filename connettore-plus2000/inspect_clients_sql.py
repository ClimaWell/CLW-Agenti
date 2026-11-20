import pyodbc

conn = pyodbc.connect('DSN=climawell', autocommit=True)
cursor = conn.cursor()

cursor.execute("""
    SELECT 
        COUNT(DISTINCT JConto) as ClientiConDoc,
        COUNT(DISTINCT CASE WHEN Anno >= 2024 THEN JConto END) as ClientiRecenti2024_2026,
        COUNT(DISTINCT CASE WHEN Anno >= 2025 THEN JConto END) as ClientiRecenti2025_2026
    FROM DocTes
    WHERE TpConto = 'C'
""")
print("Clienti con documenti in DocTes:")
print(cursor.fetchall())

# Distribuzione clienti recenti per agente
cursor.execute("""
    SELECT 
        c.JAgente,
        COUNT(DISTINCT c.JConto) as ClientiTotaliAttivi,
        COUNT(DISTINCT CASE WHEN d.Anno >= 2024 THEN c.JConto END) as ConDoc2024_2026,
        COUNT(DISTINCT CASE WHEN d.Anno >= 2025 THEN c.JConto END) as ConDoc2025_2026
    FROM CliFor c
    LEFT JOIN DocTes d ON c.TpConto = d.TpConto AND c.JConto = d.JConto
    WHERE c.TpConto = 'C' AND c.Bloccato = 0
    GROUP BY c.JAgente
    ORDER BY ConDoc2024_2026 DESC
""")
print("\nDistribuzione per agente (Totali vs Recenti 2024-2026):")
for r in cursor.fetchall()[:15]:
    print(r)

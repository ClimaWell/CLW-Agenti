import requests

URL = "https://fadgdncfhfpwkcbxcntc.supabase.co"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhZGdkbmNmaGZwd2tjYnhjbnRjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE4NzYzOTIsImV4cCI6MjEwNzQ1MjM5Mn0.ucGTqDigQVa6ZkBTH3l8Rvo7JHF7RVxvEv-3NGcMlfo"

headers = {
    "apikey": ANON_KEY,
    "Authorization": f"Bearer {ANON_KEY}",
    "Content-Type": "application/json"
}

print("=== VERIFICA TABELLA app_users SU SUPABASE ===")
try:
    r = requests.get(f"{URL}/rest/v1/app_users?select=*", headers=headers, timeout=10)
    print(f"Status app_users: {r.status_code}")
    if r.status_code == 200:
        users = r.json()
        print(f"Trovati {len(users)} utenti in app_users:")
        for u in users:
            print(f"  - Username: {u.get('username')}, Name: {u.get('name')}, Role: {u.get('role')}, Active: {u.get('active')}, AgentCode: {u.get('agent_code')}")
    else:
        print(f"Risposta app_users: {r.text}")
except Exception as e:
    print(f"Errore connessione a Supabase app_users: {e}")

print("\n=== VERIFICA TABELLA agents SU SUPABASE ===")
try:
    r = requests.get(f"{URL}/rest/v1/agents?select=*", headers=headers, timeout=10)
    print(f"Status agents: {r.status_code}")
    if r.status_code == 200:
        agents = r.json()
        print(f"Trovati {len(agents)} agenti:")
        for a in agents[:10]:
            print(f"  - Code: {a.get('code')}, Name: {a.get('name')}, Active: {a.get('active') or a.get('attivo')}")
    else:
        print(f"Risposta agents: {r.text}")
except Exception as e:
    print(f"Errore connessione a Supabase agents: {e}")

print("\n=== VERIFICA TABELLA documents (ORDINI/OFFERTE) SU SUPABASE ===")
try:
    r = requests.get(f"{URL}/rest/v1/documents?select=id,number,document_type,status,customer_name,created_at&order=id.desc&limit=5", headers=headers, timeout=10)
    print(f"Status documents: {r.status_code}")
    if r.status_code == 200:
        docs = r.json()
        print(f"Ultimi {len(docs)} documenti trovati:")
        for d in docs:
            print(f"  - Doc #{d.get('id')} ({d.get('document_type')} {d.get('number')}): {d.get('customer_name')}, Stato: {d.get('status')}")
    else:
        print(f"Risposta documents: {r.text}")
except Exception as e:
    print(f"Errore: {e}")

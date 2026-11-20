import requests
import json

URL = "https://fadgdncfhfpwkcbxcntc.supabase.co"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhZGdkbmNmaGZwd2tjYnhjbnRjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE4NzYzOTIsImV4cCI6MjEwNzQ1MjM5Mn0.ucGTqDigQVa6ZkBTH3l8Rvo7JHF7RVxvEv-3NGcMlfo"

headers = {
    "apikey": ANON_KEY,
    "Authorization": f"Bearer {ANON_KEY}",
    "Content-Type": "application/json"
}

print("--- 1. TEST LETTURA AGENTI ---")
r_ag = requests.get(f"{URL}/rest/v1/agents?select=*&order=name.asc", headers=headers)
print(f"Status: {r_ag.status_code}")
if r_ag.status_code == 200:
    agents = r_ag.json()
    print(f"Trovati {len(agents)} agenti su Supabase:")
    for a in agents:
        print(f" - Code: {a.get('code')}, Name: {a.get('name')}, Active: {a.get('active')}, Attivo: {a.get('attivo')}")
else:
    print(f"Errore: {r_ag.text}")

print("\n--- 2. TEST LETTURA PROFILO AZIENDALE ---")
r_comp = requests.get(f"{URL}/rest/v1/company_profile?select=*&limit=1", headers=headers)
print(f"Status: {r_comp.status_code}")
if r_comp.status_code == 200:
    print(r_comp.json())
else:
    print(f"Errore: {r_comp.text}")

import requests
import json

url = "https://fadgdncfhfpwkcbxcntc.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhZGdkbmNmaGZwd2tjYnhjbnRjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTg3NjM5MiwiZXhwIjoyMTA3NDUyMzkyfQ.PuSynWNvrTEsZnh4iSfMbO_3lMH-pWZojYY6ZWQ5-ls"

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

resp = requests.get(f"{url}/rest/v1/documents?select=number,document_type,customer_name,agent_code,total,status,created_at&order=created_at.desc", headers=headers)
print("STATUS:", resp.status_code)
docs = resp.json()
print("TOTALE DOCUMENTI SU SUPABASE:", len(docs))
for d in docs:
    print(d)

# Controlliamo anche con anon_key per verificare se anon_key vede gli stessi documenti
anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhZGdkbmNmaGZwd2tjYnhjbnRjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE4NzYzOTIsImV4cCI6MjEwNzQ1MjM5Mn0.ucGTqDigQVa6ZkBTH3l8Rvo7JHF7RVxvEv-3NGcMlfo"
headers_anon = {
    "apikey": anon_key,
    "Authorization": f"Bearer {anon_key}",
    "Content-Type": "application/json"
}
resp_anon = requests.get(f"{url}/rest/v1/documents?select=number,document_type,customer_name,total&order=created_at.desc", headers=headers_anon)
print("\nCON ANON_KEY:")
print("STATUS ANON:", resp_anon.status_code)
docs_anon = resp_anon.json()
print("TOTALE DOCUMENTI VISIBILI CON ANON KEY:", len(docs_anon))
for d in docs_anon:
    print(d)

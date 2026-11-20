import requests
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

URL = "https://fadgdncfhfpwkcbxcntc.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhZGdkbmNmaGZwd2tjYnhjbnRjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTg3NjM5MiwiZXhwIjoyMTA3NDUyMzkyfQ.PuSynWNvrTEsZnh4iSfMbO_3lMH-pWZojYY6ZWQ5-ls"

headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# 1. Recupera tutti gli agenti
r = requests.get(f"{URL}/rest/v1/agents?select=*", headers=headers)
agents = r.json()
print(f"Agenti totali su Supabase: {len(agents)}")

# Blacklist nomi di sistema o non operativi
blacklist_keywords = ["NON USARE", "SENZA AGENTE", "SENZA NOME", "CLIMAWELL 2", "CLIMAWELL SRL", "DIREZIONE", "VIA MORELLI", "VIA DELLA CASELLA", "VIA COSSERIA", "VIA XX SETTEMBRE"]

attivati = 0
disattivati = 0

for a in agents:
    code = a.get("code")
    name = str(a.get("name") or "").strip().upper()
    
    # Determina se deve essere attivo
    is_blacklisted = any(k in name for k in blacklist_keywords)
    is_active = not is_blacklisted
    
    # Aggiorna su Supabase
    up_data = {
        "active": is_active,
        "attivo": is_active
    }
    
    res = requests.patch(f"{URL}/rest/v1/agents?code=eq.{code}", json=up_data, headers=headers)
    if is_active:
        attivati += 1
        print(f" ✅ ATTIVATO: {code} - {a.get('name')}")
    else:
        disattivati += 1
        print(f" ❌ DISATTIVATO: {code} - {a.get('name')}")

print(f"\nRiepilogo: {attivati} agenti attivati, {disattivati} esclusi.")

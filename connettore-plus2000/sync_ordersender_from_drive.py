import json
import os
import sys
import datetime
from connettore import GoogleSheetsClient, load_config, BASE_DIR

def run_sync_ordersender():
    cfg = load_config()
    sa_file = cfg.get("google_sheets", {}).get("service_account_file", "service_account.json")
    client = GoogleSheetsClient(sa_file)
    
    print("=== AGGIORNAMENTO DATI ORDERSENDER DA GOOGLE DRIVE ===")
    
    # 1. Recupero Agenti da Google Drive (tab daPlus nello spreadsheet di registro)
    print("1/3. Lettura lista Agenti da Google Drive (tab 'daPlus')...")
    agents_ss_id = "10hp34cPu6ZxzPwSbrlIFsr_WcQTaIwBmJUUQjFZc2nw"
    raw_agents = client.read_range(agents_ss_id, "'daPlus'!A1:L60")
    agents = []
    agent_code_map = {}
    
    if raw_agents and len(raw_agents) > 1:
        headers = raw_agents[0]
        for r in raw_agents[1:]:
            if len(r) >= 3 and r[0].startswith("AG"):
                ag_id = r[0].strip()
                plus_code = r[1].strip()
                name = r[2].strip()
                cell = r[3].strip() if len(r) > 3 else ""
                phone = r[4].strip() if len(r) > 4 else ""
                mail = r[5].strip() if len(r) > 5 else ""
                
                # Primo e secondo nome
                parts = name.split()
                first_name = parts[0] if parts else ""
                last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
                
                agent_obj = {
                    "id": ag_id,
                    "code": plus_code,
                    "name": name,
                    "firstName": first_name,
                    "lastName": last_name,
                    "role": "Agente",
                    "head": (ag_id == "AG01"),
                    "parentAgent": None,
                    "email": mail,
                    "phone": cell or phone,
                    "active": True,
                    "canOffer": True,
                    "canOrder": True,
                    "discountLimit": None,
                    "notes": f"Codice Plus 2000: {plus_code}"
                }
                agents.append(agent_obj)
                agent_code_map[plus_code] = ag_id
                agent_code_map[name.upper()] = ag_id
                
    print(f"  -> Caricati {len(agents)} Agenti ufficiali.")

    # 2. Recupero Clienti da Google Drive
    print("2/3. Lettura Clienti da Google Drive (foglio 'clienti')...")
    cust_ss_id = "1Ui3W6-jVIww7QgTtnXaywJj2ZyQiiaHAd92Xl5KRrD8"
    raw_cust = client.read_range(cust_ss_id, "clienti!A1:T5000")
    clients = []
    
    if raw_cust and len(raw_cust) > 1:
        headers = raw_cust[0]
        # Mappa posizioni colonne
        col_idx = {h.strip(): idx for idx, h in enumerate(headers)}
        
        def val(row, key, default=""):
            idx = col_idx.get(key)
            if idx is not None and idx < len(row):
                return str(row[idx]).strip()
            return default

        for r in raw_cust[1:]:
            cid = val(r, "Codice")
            name = val(r, "Ragione sociale")
            if not cid or not name:
                continue
                
            cod_ag = val(r, "CodiceAgente")
            nome_ag = val(r, "Agente")
            matched_ag_id = agent_code_map.get(cod_ag) or agent_code_map.get(nome_ag.upper()) or "UNASSIGNED"
            
            clients.append({
                "id": cid,
                "name": name,
                "code": cid,
                "sourceAgent": nome_ag,
                "agentId": matched_ag_id,
                "address": val(r, "Indirizzo"),
                "postalCode": val(r, "Cap"),
                "city": val(r, "Citta"),
                "province": val(r, "Pv"),
                "phone": val(r, "Telefono"),
                "mobile": val(r, "Cellulare"),
                "email": val(r, "E-mail"),
                "pec": val(r, "PEC"),
                "fiscalCode": val(r, "CodiceFiscale"),
                "vatNumber": val(r, "PartitaIva"),
                "payment": val(r, "Pagamento"),
                "priceList": val(r, "Listino"),
                "lastDocYear": val(r, "UltimoAnnoDoc")
            })
            
    print(f"  -> Caricati {len(clients)} Clienti attivi.")

    # 3. Recupero Articoli da Google Drive
    print("3/3. Lettura Articoli da Google Drive (foglio 'q_listino_prezzi_catalogo')...")
    art_ss_id = "1g6zrWK_zZJZ82kdoNgda9KuoemYlSs0XGRRfJvoOvUk"
    raw_art = client.read_range(art_ss_id, "q_listino_prezzi_catalogo!A1:N20000", unformatted=True)
    articles = []

    
    if raw_art and len(raw_art) > 1:
        headers = raw_art[0]
        col_idx = {h.strip(): idx for idx, h in enumerate(headers)}
        
        def val(row, key, default=""):
            idx = col_idx.get(key)
            if idx is not None and idx < len(row):
                return str(row[idx]).strip()
            return default

        for r in raw_art[1:]:
            caid = val(r, "CaId")
            code = val(r, "CodiceArticolo")
            desc = val(r, "Descrizione")
            if not code or not desc:
                continue
                
            try:
                price = float(val(r, "Prezzo", "0").replace(",", "."))
            except:
                price = 0.0
                
            try:
                stock = float(val(r, "Giacenza (QtEsi)", "0").replace(",", "."))
            except:
                stock = 0.0

            articles.append({
                "id": caid or code,
                "code": code,
                "description": desc,
                "brand": val(r, "Marca"),
                "sector": val(r, "Settore"),
                "macroFamily": val(r, "Macrofamiglia"),
                "family": val(r, "Famiglia"),
                "status": val(r, "Jstato prodotto"),
                "group": val(r, "Ubicazione"),
                "price": price,
                "stock": stock,
                "unit": val(r, "Unità di Misura", "NR"),
                "discountCode": val(r, "JScontoVen"),
                "imageRef": val(r, "URL-immagine"),
                "vat": 22
            })
            
    print(f"  -> Caricati {len(articles)} Articoli attivi a catalogo.")

    # Profilo aziendale Climawell
    company = {
        "companyName": "CLIMAWELL S.R.L.",
        "address": "Via dei Lavatoi, 75",
        "postalCode": "50058",
        "city": "Signa",
        "province": "FI",
        "phone": "055 8997788",
        "email": "info@climawell.it",
        "pec": "climawell@pec.it",
        "vatNumber": "06926030484",
        "fiscalCode": "06926030484",
        "website": "https://www.climawell.it",
        "currency": "EUR",
        "defaultVat": "22",
        "offerValidityDays": "30",
        "ordersEmail": "cwlofn@gmail.com"
    }

    # Gerarchia agenti
    hierarchy = {}
    if agents:
        hierarchy[agents[0]["id"]] = [a["id"] for a in agents[1:5]]

    seed_data = {
        "company": company,
        "agents": agents,
        "hierarchy": hierarchy,
        "clients": clients,
        "articles": articles,
        "meta": {
            "generatedAt": datetime.datetime.now().isoformat() + "Z",
            "source": "Google Drive Live Sync (Plus 2000 Integration)",
            "articleCount": len(articles),
            "clientCount": len(clients),
            "agentCount": len(agents)
        }
    }

    # Percorso del file seed-data.json in OrderSender/site/
    seed_file_path = os.path.normpath(os.path.join(BASE_DIR, "..", "OrderSender", "site", "seed-data.json"))
    with open(seed_file_path, "w", encoding="utf-8") as f:
        json.dump(seed_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n[SUCCESSO] File {seed_file_path} aggiornato con i dati reali di Google Drive!")
    print(f"  - Azienda: {company['companyName']}")
    print(f"  - Agenti: {len(agents)}")
    print(f"  - Clienti: {len(clients)}")
    print(f"  - Articoli: {len(articles)}")

if __name__ == "__main__":
    run_sync_ordersender()

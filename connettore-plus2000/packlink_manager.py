#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
CLIMAWELL COMMERCIAL HUB - PACKLINK PRO AUTOMATION MANAGER
=============================================================================
Automatizzazione completa del flusso di spedizione con Packlink PRO:
1. Creazione automatica di BOZZE DI SPEDIZIONE su Packlink PRO via API:
   - Invia i dati da PLUS 2000 / Supabase (Mittente, Cantiere, Referente, Telefono)
   - L'operatore accede su https://pro.packlink.it e trova la spedizione pronta
   - Conferma con 1 clic e stampa l'etichetta del corriere (GLS, BRT, TNT, Poste)
2. Sincronizzazione automatica del Tracking e Lettera di Vettura (LdV):
   - Legge lo stato della spedizione da Packlink PRO
   - Aggiorna istantaneamente Supabase con lo stato 'Spedito', corriere e tracking
   - Notifica visibile per Sede, Agente Commerciale e Cliente Finale B2B
=============================================================================
"""

import os
import sys
import json
import re
import datetime
import requests

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Errore lettura config.json: {e}")
    return {}

CONFIG = load_config()
PACKLINK_CFG = CONFIG.get("packlink", {})
PACKLINK_API_KEY = PACKLINK_CFG.get("api_key", "00a55a9cede7debe5e5badeaf0ac9a695044679a593c0405cb12413b3e6e8114")
PACKLINK_ENV = PACKLINK_CFG.get("environment", "production")

BASE_URL = "https://apisandbox.packlink.com/v1" if PACKLINK_ENV == "sandbox" else "https://api.packlink.com/v1"

SUPABASE_CFG = CONFIG.get("supabase", {})
SUPABASE_URL = SUPABASE_CFG.get("url", "https://fadgdncfhfpwkcbxcntc.supabase.co")
SUPABASE_SERVICE_KEY = SUPABASE_CFG.get("service_role_key", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhZGdkbmNmaGZwd2tjYnhjbnRjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTg3NjM5MiwiZXhwIjoyMTA3NDUyMzkyfQ.PuSynWNvrTEsZnh4iSfMbO_3lMH-pWZojYY6ZWQ5-ls")


def get_packlink_headers():
    return {
        "Authorization": PACKLINK_API_KEY,
        "Content-Type": "application/json"
    }


def get_supabase_headers():
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }


def get_sender():
    return PACKLINK_CFG.get("sender", {
        "name": "Climawell S.r.l.",
        "company": "Climawell S.r.l.",
        "street1": "Via Pratese",
        "city": "Firenze",
        "zip_code": "50145",
        "country": "IT",
        "phone": "0554289074",
        "email": "logistica@climawell.it"
    })


def parse_order_recipient(order):
    """
    Estrae dati anagrafici, cantiere, referente e telefono per la spedizione
    """
    dest = order.get("destination_address") or ""
    notes = order.get("notes") or ""
    cust_name = order.get("customer_name") or "Cliente"

    recipient = {
        "name": cust_name,
        "company": cust_name,
        "street1": dest,
        "zip_code": "50100",
        "city": "Firenze",
        "province": "FI",
        "country": "IT",
        "phone": "0554289074",
        "email": "logistica@climawell.it",
        "is_cantiere": False,
        "cantiere_nome": "",
        "delivery_notes": ""
    }

    if "[CANTIERE:" in dest or "DESTINAZIONE DIVERSA CANTIERE" in notes:
        recipient["is_cantiere"] = True
        c_m = re.search(r"\[CANTIERE:\s*([^\]]+)\]", dest, re.IGNORECASE)
        if c_m:
            recipient["cantiere_nome"] = c_m.group(1).strip()

        ref_m = re.search(r"Referente[^:]*:\s*([^\n]+)", notes, re.IGNORECASE)
        if ref_m:
            ref_name = ref_m.group(1).strip()
            recipient["name"] = f"{ref_name} c/o {recipient['cantiere_nome'] or cust_name}"

        tel_m = re.search(r"Telefono[^:]*:\s*([^\n]+)", notes, re.IGNORECASE)
        if tel_m:
            clean_tel = re.sub(r"[^0-9+]", "", tel_m.group(1))
            if clean_tel:
                recipient["phone"] = clean_tel

        note_m = re.search(r"Istruzioni consegna:\s*([^\n]+)", notes, re.IGNORECASE)
        if note_m:
            recipient["delivery_notes"] = note_m.group(1).strip()

        addr_part = re.sub(r"\[CANTIERE:[^\]]+\]\s*", "", dest, flags=re.IGNORECASE).strip()
        zip_city = re.search(r"(\d{5})\s+([^(,]+)(?:\(([A-Z]{2})\))?", addr_part)
        if zip_city:
            recipient["zip_code"] = zip_city.group(1)
            recipient["city"] = zip_city.group(2).strip()
            if zip_city.group(3):
                recipient["province"] = zip_city.group(3).upper()
            recipient["street1"] = addr_part.split(recipient["zip_code"])[0].rstrip(", ").strip()
        else:
            recipient["street1"] = addr_part
    else:
        # Indirizzo sede standard
        zip_city = re.search(r"(\d{5})\s+([^(,]+)(?:\(([A-Z]{2})\))?", dest)
        if zip_city:
            recipient["zip_code"] = zip_city.group(1)
            recipient["city"] = zip_city.group(2).strip()
            if zip_city.group(3):
                recipient["province"] = zip_city.group(3).upper()
            recipient["street1"] = dest.split(recipient["zip_code"])[0].rstrip(", ").strip()
        else:
            recipient["street1"] = dest or "Via Sede Cliente"

    return recipient


def test_packlink_connection():
    """
    Verifica che la chiave API Packlink PRO sia attiva e funzionante
    """
    print("=" * 70)
    print("🔍 VERIFICA CONNESSIONE PACKLINK PRO API")
    print(f"   Endpoint: {BASE_URL}")
    print(f"   API Key:  {PACKLINK_API_KEY[:8]}...{PACKLINK_API_KEY[-8:]}")
    print("=" * 70)

    try:
        url = f"{BASE_URL}/shipments?limit=1"
        resp = requests.get(url, headers=get_packlink_headers(), timeout=12)
        print(f"   Risposta HTTP: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            total = len(data) if isinstance(data, list) else data.get("messages", 0)
            print("   ✅ CONNESSIONE RIUSCITA: API Key Packlink PRO valida e operativa!")
            return True
        elif resp.status_code == 401:
            print("   ❌ ERRORE AUTENTICAZIONE (401): API Key non valida o non autorizzata.")
            return False
        else:
            print(f"   ⚠️ Risposta API Packlink: {resp.status_code} - {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ Eccezione durante la connessione a Packlink: {e}")
        return False


def create_packlink_draft(order):
    """
    Crea una BOZZA (DRAFT) di spedizione su Packlink PRO via API
    """
    doc_num = order.get("number") or "DOC"
    recipient = parse_order_recipient(order)
    sender = get_sender()

    # Data di ritiro predefinita: giorno feriale successivo
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    if tomorrow.weekday() >= 5:  # se sabato o domenica sposta a lunedì
        tomorrow += datetime.timedelta(days=(7 - tomorrow.weekday()))
    collection_date_str = tomorrow.strftime("%Y-%m-%d")

    # Stima peso da righe o default 10kg
    weight = 10.0
    lines = order.get("lines") or []
    if lines:
        weight = max(5.0, len(lines) * 4.5)

    payload = {
        "collection_date": collection_date_str,
        "from": {
            "name": sender.get("name", "Climawell S.r.l."),
            "company": sender.get("company", "Climawell S.r.l."),
            "street1": sender.get("street1", "Via Pratese"),
            "city": sender.get("city", "Firenze"),
            "zip_code": sender.get("zip_code", "50145"),
            "country": "IT",
            "phone": sender.get("phone", "0554289074"),
            "email": sender.get("email", "logistica@climawell.it")
        },
        "to": {
            "name": recipient["name"],
            "company": recipient["company"],
            "street1": recipient["street1"] or "Via di Consegna",
            "city": recipient["city"] or "Firenze",
            "zip_code": recipient["zip_code"] or "50100",
            "country": "IT",
            "phone": recipient["phone"],
            "email": recipient["email"]
        },
        "packages": [
            {
                "weight": weight,
                "length": 60,
                "width": 40,
                "height": 35
            }
        ],
        "content": f"Forniture termoidrauliche / Rif. {doc_num}",
        "content_second_hand": False
    }

    url = f"{BASE_URL}/shipments"

    print(f"\n🚀 Invio bozza spedizione a Packlink PRO per ordine: {doc_num}")
    print(f"   Destinatario: {recipient['name']}")
    print(f"   Indirizzo:    {recipient['street1']}, {recipient['zip_code']} {recipient['city']} ({recipient['province']})")
    print(f"   Telefono:     {recipient['phone']}")
    print(f"   Peso stima:   {weight} Kg")

    try:
        resp = requests.post(url, headers=get_packlink_headers(), json=payload, timeout=15)
        if resp.status_code in [200, 201]:
            data = resp.json()
            ref = data.get("reference")
            print(f"   ✅ BOZZA CREATA CON SUCCESSO SU PACKLINK PRO!")
            print(f"      Riferimento Packlink: {ref}")
            print(f"      🔗 Visibile su: https://pro.packlink.it/private/shipments/drafts")

            # Salva il riferimento bozza nelle note dell'ordine su Supabase
            update_order_with_draft_ref(doc_num, ref)
            return ref
        else:
            print(f"   ⚠️ Errore creazione bozza Packlink: {resp.status_code} - {resp.text[:300]}")
            return None
    except Exception as e:
        print(f"   ❌ Eccezione durante la creazione bozza Packlink: {e}")
        return None


def update_order_with_draft_ref(doc_num, packlink_ref):
    """
    Aggiorna l'ordine su Supabase con il riferimento della bozza Packlink
    """
    try:
        url = f"{SUPABASE_URL}/rest/v1/documents?number=eq.{doc_num}"
        headers = get_supabase_headers()

        # Leggi note attuali
        r_curr = requests.get(url, headers=headers, timeout=10)
        curr_notes = ""
        if r_curr.status_code == 200 and r_curr.json():
            curr_notes = r_curr.json()[0].get("notes") or ""

        new_notes = f"{curr_notes}\n[Packlink PRO Ref: {packlink_ref}] - Bozza creata il {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}".strip()

        patch_payload = {
            "notes": new_notes,
            "status": "In Preparazione",
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        requests.patch(url, headers=headers, json=patch_payload, timeout=10)
    except Exception as e:
        print(f"   Avviso aggiornamento note ordine Supabase: {e}")


def sync_tracking_from_packlink():
    """
    Controlla le spedizioni su Packlink PRO:
    Se un operatore ha confermato/pagato una bozza su https://pro.packlink.it,
    recupera il corriere (GLS, BRT, ecc.) e il tracking number, aggiornando Supabase.
    """
    print("\n" + "=" * 70)
    print("🔄 VERIFICA SPEDIZIONI CONFERMATE SU PACKLINK PRO & AGGIORNAMENTO TRACKING")
    print("=" * 70)

    url = f"{BASE_URL}/shipments?limit=50"
    try:
        resp = requests.get(url, headers=get_packlink_headers(), timeout=15)
        if resp.status_code != 200:
            print(f"❌ Impossibile recuperare spedizioni da Packlink: {resp.status_code} - {resp.text[:200]}")
            return

        shipments = resp.json()
        if not isinstance(shipments, list):
            print("ℹ️ Nessuna spedizione trovata.")
            return

        print(f"📦 Trovate {len(shipments)} spedizioni su Packlink PRO:")
        updated_count = 0

        for s in shipments:
            ref = s.get("reference")
            st = s.get("status", "").upper()
            carrier = s.get("carrier", s.get("carrier_name", "Corriere Espresso"))
            tracking_codes = s.get("tracking_codes") or []
            tracking_num = tracking_codes[0] if tracking_codes else ""

            # Se la spedizione non è più una bozza (è stata confermata o è pronta)
            if st in ["READY_TO_PRINT", "SUCCESS", "PURCHASED", "IN_TRANSIT", "DELIVERED"]:
                # Cerca l'ordine corrispondente su Supabase
                matching_doc = find_order_by_packlink_ref(ref)
                if matching_doc:
                    doc_num = matching_doc.get("number")
                    curr_st = matching_doc.get("status")
                    curr_track = matching_doc.get("tracking_number")

                    # Se non è ancora segnato come Spedito o manca il tracking
                    if curr_st != "Spedito" or not curr_track or (tracking_num and curr_track != tracking_num):
                        final_track = tracking_num or ref
                        update_supabase_order_shipped(doc_num, carrier, final_track, ref, st)
                        print(f"   🚚 Ordine {doc_num} AGGIORNATO SPEDITO: {carrier} - LdV: {final_track}")
                        updated_count += 1

        print(f"🏁 Fine sincronizzazione: {updated_count} ordini aggiornati con tracking su Supabase.")
    except Exception as e:
        print(f"❌ Eccezione durante la sincronizzazione tracking: {e}")


def find_order_by_packlink_ref(ref):
    """
    Cerca su Supabase un documento che contenga il riferimento Packlink
    """
    try:
        url = f"{SUPABASE_URL}/rest/v1/documents"
        params = {
            "notes": f"ilike.*{ref}*",
            "select": "id,number,status,tracking_number,carrier_name"
        }
        resp = requests.get(url, headers=get_supabase_headers(), params=params, timeout=10)
        if resp.status_code == 200 and resp.json():
            return resp.json()[0]
    except Exception:
        pass
    return None


def update_supabase_order_shipped(doc_num, carrier, tracking, ref, status_packlink):
    """
    Aggiorna lo stato dell'ordine su Supabase con tracking live
    """
    try:
        url = f"{SUPABASE_URL}/rest/v1/documents?number=eq.{doc_num}"
        patch_payload = {
            "status": "Spedito",
            "carrier_name": carrier or "Packlink Pro",
            "tracking_number": tracking,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        requests.patch(url, headers=get_supabase_headers(), json=patch_payload, timeout=10)
    except Exception as e:
        print(f"   Errore aggiornamento Supabase: {e}")


def auto_create_drafts_for_pending_orders():
    """
    Scansiona tutti gli ordini B2B 'Inviato' e crea la bozza su Packlink PRO
    """
    url = f"{SUPABASE_URL}/rest/v1/documents"
    params = {
        "document_type": "eq.OCL",
        "status": "eq.Inviato",
        "order": "created_at.asc"
    }
    resp = requests.get(url, headers=get_supabase_headers(), params=params, timeout=15)
    if resp.status_code != 200 or not resp.json():
        print("ℹ️ Nessun ordine B2B 'Inviato' in attesa di creazione bozza.")
        return

    orders = resp.json()
    print(f"📦 Trovati {len(orders)} ordini per cui creare bozza Packlink PRO:")
    for o in orders:
        create_packlink_draft(o)


if __name__ == "__main__":
    if "--test" in sys.argv:
        test_packlink_connection()
    elif "--sync-tracking" in sys.argv:
        sync_tracking_from_packlink()
    elif "--auto" in sys.argv:
        test_packlink_connection()
        auto_create_drafts_for_pending_orders()
        sync_tracking_from_packlink()
    else:
        print("Utilizzo:")
        print("  python packlink_manager.py --test            (Verifica connessione API Packlink)")
        print("  python packlink_manager.py --auto            (Crea bozze ordini nuovi e sincronizza tracking)")
        print("  python packlink_manager.py --sync-tracking   (Sincronizza tracking da Packlink a Supabase)")


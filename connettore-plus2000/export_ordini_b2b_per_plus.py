#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
CLIMAWELL - ESPORTATORE ORDINI B2B / CANTIERE PER PLUS 2000 & PACKLINK PRO
=============================================================================
Estrae gli ordini cliente inseriti direttamente dal portale B2B su Supabase:
- Identifica destinazioni speciali (cantieri, referenti, cellulari corriere)
- Prepara i file di importazione standard OCL per PLUS2000 su SRVPLUS
- Aggiorna lo stato su Supabase in 'In Lavorazione' o 'Spedito'
=============================================================================
"""

import os
import sys
import json
import csv
import re
import datetime
import requests

# Supabase Credentials
SUPABASE_URL = "https://fadgdncfhfpwkcbxcntc.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhZGdkbmNmaGZwd2tjYnhjbnRjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTg3NjM5MiwiZXhwIjoyMTA3NDUyMzkyfQ.PuSynWNvrTEsZnh4iSfMbO_3lMH-pWZojYY6ZWQ5-ls"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "ordini_b2b_export")


def get_headers():
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }


def fetch_pending_b2b_orders():
    """
    Recupera da Supabase gli ordini OCL con stato 'Inviato'
    """
    url = f"{SUPABASE_URL}/rest/v1/documents"
    params = {
        "document_type": "eq.OCL",
        "status": "eq.Inviato",
        "order": "created_at.asc"
    }
    resp = requests.get(url, headers=get_headers(), params=params, timeout=15)
    if resp.status_code != 200:
        print(f"❌ Errore HTTP recupero ordini: {resp.status_code} - {resp.text}")
        return []
    return resp.json()


def fetch_order_lines(doc_number):
    """
    Recupera le righe articolo associate all'ordine
    """
    url = f"{SUPABASE_URL}/rest/v1/document_lines"
    params = {
        "document_number": f"eq.{doc_number}",
        "order": "line_number.asc"
    }
    resp = requests.get(url, headers=get_headers(), params=params, timeout=15)
    if resp.status_code != 200:
        return []
    return resp.json()


def parse_cantiere_info(destination_address, notes):
    """
    Estrae le informazioni strutturate del cantiere
    """
    dest = destination_address or ""
    n = notes or ""

    info = {
        "is_cantiere": False,
        "cantiere_nome": "",
        "indirizzo": dest,
        "cap": "",
        "citta": "",
        "prov": "",
        "referente": "",
        "telefono": "",
        "note_scarico": ""
    }

    if "[CANTIERE:" in dest or "DESTINAZIONE DIVERSA CANTIERE" in n:
        info["is_cantiere"] = True
        c_match = re.search(r"\[CANTIERE:\s*([^\]]+)\]", dest, re.IGNORECASE)
        if c_match:
            info["cantiere_nome"] = c_match.group(1).strip()

        ref_match = re.search(r"Referente[^:]*:\s*([^\n]+)", n, re.IGNORECASE)
        if ref_match:
            info["referente"] = ref_match.group(1).strip()

        tel_match = re.search(r"Telefono[^:]*:\s*([^\n]+)", n, re.IGNORECASE)
        if tel_match:
            info["telefono"] = tel_match.group(1).strip()

        note_match = re.search(r"Istruzioni consegna:\s*([^\n]+)", n, re.IGNORECASE)
        if note_match:
            info["note_scarico"] = note_match.group(1).strip()

        addr_part = re.sub(r"\[CANTIERE:[^\]]+\]\s*", "", dest, flags=re.IGNORECASE).strip()
        zip_city = re.search(r"(\d{5})\s+([^(,]+)(?:\(([A-Z]{2})\))?", addr_part)
        if zip_city:
            info["cap"] = zip_city.group(1)
            info["citta"] = zip_city.group(2).strip()
            if zip_city.group(3):
                info["prov"] = zip_city.group(3).upper()
            info["indirizzo"] = addr_part.split(info["cap"])[0].rstrip(", ").strip()
        else:
            info["indirizzo"] = addr_part

    return info


def mark_order_in_processing(doc_number):
    """
    Aggiorna lo stato dell'ordine in 'In Lavorazione' su Supabase
    """
    url = f"{SUPABASE_URL}/rest/v1/documents?number=eq.{doc_number}"
    payload = {
        "status": "In Lavorazione",
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    resp = requests.patch(url, headers=get_headers(), json=payload, timeout=10)
    return resp.status_code in [200, 204]


def process_orders(auto_advance=False):
    """
    Esegue l'elaborazione e l'esportazione di tutti gli ordini B2B in attesa
    """
    print("=" * 70)
    print("🔍 CLIMAWELL — RICERCA NUOVI ORDINI PORTALE B2B")
    print("=" * 70)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    orders = fetch_pending_b2b_orders()

    if not orders:
        print("ℹ️ Nessun nuovo ordine B2B con stato 'Inviato' in attesa.")
        return

    print(f"📦 Trovati {len(orders)} nuovi ordini da elaborare:")

    today_str = datetime.date.today().strftime("%Y%m%d_%H%M%S")
    export_csv_file = os.path.join(OUTPUT_DIR, f"ordini_b2b_plus2000_{today_str}.csv")

    fieldnames = [
        "NumeroOrdine", "DataOrdine", "CodiceCliente", "RagioneSociale",
        "TipoConsegna", "NomeCantiere", "IndirizzoConsegna", "CAP", "Citta", "Provincia",
        "Referente", "Telefono", "NoteConsegna",
        "Riga", "CodiceArticolo", "Descrizione", "Marca", "Quantita", "UM"
    ]

    total_lines = 0

    with open(export_csv_file, mode="w", newline="", encoding="utf-8-sig") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        for ord_doc in orders:
            doc_num = ord_doc.get("number")
            cust_code = ord_doc.get("customer_code") or ""
            cust_name = ord_doc.get("customer_name") or ""
            doc_date = ord_doc.get("document_date") or ""

            cantiere = parse_cantiere_info(ord_doc.get("destination_address"), ord_doc.get("notes"))
            lines = fetch_order_lines(doc_num)

            print(f"\n📋 Ordine: {doc_num} · Cliente: {cust_name} ({cust_code})")
            if cantiere["is_cantiere"]:
                print(f"   🏗️ DESTINAZIONE CANTIERE: {cantiere['cantiere_nome']}")
                print(f"      📍 Indirizzo: {cantiere['indirizzo']}, {cantiere['cap']} {cantiere['citta']} ({cantiere['prov']})")
                print(f"      👤 Referente: {cantiere['referente']} · 📞 Tel: {cantiere['telefono']}")
            else:
                print(f"   🏢 CONSEGNA SEDE: {ord_doc.get('destination_address')}")

            print(f"   📦 Articoli ordinati: {len(lines)}")
            for l in lines:
                total_lines += 1
                p_code = l.get("product_code") or ""
                p_desc = l.get("description") or ""
                qty = l.get("quantity") or 1
                um = l.get("um") or "PZ"
                print(f"      - {p_code}: {qty} {um} ({p_desc[:40]}...)")

                writer.writerow({
                    "NumeroOrdine": doc_num,
                    "DataOrdine": doc_date,
                    "CodiceCliente": cust_code,
                    "RagioneSociale": cust_name,
                    "TipoConsegna": "CANTIERE" if cantiere["is_cantiere"] else "SEDE",
                    "NomeCantiere": cantiere["cantiere_nome"],
                    "IndirizzoConsegna": cantiere["indirizzo"],
                    "CAP": cantiere["cap"],
                    "Citta": cantiere["citta"],
                    "Provincia": cantiere["prov"],
                    "Referente": cantiere["referente"],
                    "Telefono": cantiere["telefono"],
                    "NoteConsegna": cantiere["note_scarico"] or ord_doc.get("notes") or "",
                    "Riga": l.get("line_number") or 1,
                    "CodiceArticolo": p_code,
                    "Descrizione": p_desc,
                    "Marca": l.get("brand") or "",
                    "Quantita": qty,
                    "UM": um
                })

            if auto_advance:
                mark_order_in_processing(doc_num)
                print(f"   ✅ Stato aggiornato su Supabase: 'In Lavorazione'")

    print("\n" + "=" * 70)
    print(f"✅ FILE ESPORTATO PER PLUS 2000:")
    print(f"   📁 {export_csv_file}")
    print(f"   📊 Righe totali esportate: {total_lines}")
    print("=" * 70)


if __name__ == "__main__":
    auto = "--auto-advance" in sys.argv or "-a" in sys.argv
    process_orders(auto_advance=auto)


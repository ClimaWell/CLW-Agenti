#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
CLIMAWELL - RESET COMPLETO & RICARICA PULITA CATALOGO ARTICOLI
====================================================================
1. Pulisce la tabella 'products' su Supabase eliminando tutti i vecchi
   record storici e gli articoli a giacenza zero.
2. Ricarica da Plus 2000 solo ed esclusivamente gli articoli con
   giacenza positiva reale (> 0), arricchiti con codici a barre
   EAN-13 ufficiali (ArticoliUm) e categorie DomusPartes.
====================================================================
"""

import sys
import os
import json
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from sync_plus_to_supabase import load_config, get_sql_conn, SupabaseSyncer, sync_products

def main():
    print("=" * 70)
    print("  CLIMAWELL - RESET & RICARICA PULITA CATALOGO ARTICOLI")
    print("=" * 70)

    cfg = load_config()
    sup_cfg = cfg.get("supabase", {})
    sql_cfg = cfg.get("sql_server", {})

    url = sup_cfg.get("url")
    key = sup_cfg.get("service_role_key") or sup_cfg.get("anon_key")

    if not url or not key:
        print("❌ Credenziali Supabase mancanti in config.json!")
        sys.exit(1)

    syncer = SupabaseSyncer(url, key)

    print("\n⚠️  ATTENZIONE: Questa operazione svuota la tabella 'products' su Supabase")
    print("    e ricarica da Plus 2000 solo gli articoli con giacenza reale (> 0).")
    
    # Se eseguito con flag --yes salta la richiesta
    if "--yes" not in sys.argv:
        conferma = input("\nSei sicuro di voler procedere? (S/N): ").strip().upper()
        if conferma not in ["S", "SI", "Y", "YES"]:
            print("Operazione annullata dall'utente.")
            sys.exit(0)

    print("\n1. Pulizia tabella 'products' su Supabase in corso...")
    try:
        # Cancella i record di products (CASCADE elimina anche le product_locations correlate)
        del_headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Prefer": "return=minimal"
        }
        resp = syncer.session.delete(f"{url}/rest/v1/products?id=not.is.null", headers=del_headers, timeout=60)
        if resp.status_code in [200, 204]:
            print("   ✅ Tabella 'products' svuotata con successo!")
        else:
            print(f"   [Avviso pulizia]: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"   [Avviso durante pulizia]: {e}")

    print("\n2. Connessione a Plus 2000 per estrazione catalogo con giacenza reale...")
    conn = get_sql_conn(sql_cfg)
    cursor = conn.cursor()

    try:
        # Esegue sync_products (senza --all, quindi solo g.TotEsi > 0)
        if "--all" in sys.argv:
            sys.argv.remove("--all")
        sync_products(cursor, syncer)
        print("\n🎉 RESET E RICARICA COMPLETATA CON SUCCESSO!")
        print("Il catalogo su Supabase ora contiene solo gli articoli con giacenza reale e barcode EAN-13!")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()

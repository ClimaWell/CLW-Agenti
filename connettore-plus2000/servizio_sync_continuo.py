#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
CLIMAWELL - SERVIZIO SINCRONIZZATORE IN TEMPO REALE (DAEMON)
====================================================================
Esegue il monitoraggio continuo intelligente tra Plus 2000 e Supabase:
  - Orario Lavorativo (Lun-Ven 07:30 - 19:30): polling rapido ogni 45s
  - Notte e Weekend: modalità standby a basso consumo ogni 5 minuti (300s)
  - Filtri server-side PostgREST e firme differenziali (Egress ridotto del 99%)
  - Full-sync catalogo programmato 1 volta al giorno (06:30 Lun-Ven) o on-demand.

Funzionalità:
  1. Scarica immediatamente offerte/ordini inseriti dagli agenti sul web
  2. Inserisce nel DB aziendale Plus 2000 (SQL Server SRVPLUS)
  3. Allinea lo stato dell'ordine su Supabase con numero doc (#3772/2026)
  4. Sincronizza giacenze e picking ordini per il magazzino locale

Uso:
  python servizio_sync_continuo.py
  oppure: avvia_sync_continuo.bat
"""

import sys
import os
import json
import time
import datetime
import traceback

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from sync_plus_to_supabase import (
    load_config, get_sql_conn, SupabaseSyncer, 
    sync_documents_from_supabase_to_plus,
    sync_open_orders_from_plus_to_supabase,
    sync_incremental_stock_from_plus,
    sync_agents, sync_products, sync_customers
)

# Intervalli di polling dinamici per minimizzare consumi ed Egress
POLL_INTERVAL_WORK_HOURS = 90   # 90 secondi durante l'orario di lavoro
POLL_INTERVAL_OFF_HOURS = 600   # 10 minuti (600s) di notte e nei weekend (modalità standby)

_last_daily_sync_date = None


def log(msg, emoji="ℹ️"):
    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"[{now_str}] {emoji} {msg}", flush=True)


def get_current_poll_interval():
    """
    Rileva se siamo in orario lavorativo o in standby notturno/weekend.
    """
    now = datetime.datetime.now()
    is_weekend = (now.weekday() >= 5)  # 5=Sabato, 6=Domenica
    is_off_hours = (now.hour < 7 or (now.hour == 7 and now.minute < 30) or now.hour >= 20)

    if is_weekend:
        return POLL_INTERVAL_OFF_HOURS, "💤 Standby Weekend (Frequenza: 10 min - Zero Egress a vuoto)"
    elif is_off_hours:
        return POLL_INTERVAL_OFF_HOURS, "🌙 Standby Notturno (Frequenza: 10 min)"
    else:
        return POLL_INTERVAL_WORK_HOURS, "⚡ Operativo Orario Lavoro (Frequenza: 90s)"


def should_run_daily_full_sync():
    """
    Allinea catalogo, clienti e agenti completi 1 sola volta al giorno,
    dal lunedì al venerdì alle prime ore del mattino (tra le 06:00 e le 07:00).
    Evita il rieseguimento ogni 4 ore che saturava la quota di Supabase.
    """
    global _last_daily_sync_date
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    # Non eseguire nei weekend
    if now.weekday() >= 5:
        return False

    if 6 <= now.hour < 7 and _last_daily_sync_date != today_str:
        _last_daily_sync_date = today_str
        return True
    return False


def check_and_execute_on_demand_sync(cursor, syncer):
    """
    Intercetta le richieste di sincronizzazione on-demand inviate dalla Web App.
    Legge da Plus 2000 e aggiorna catalogo, barcode EAN-13, giacenze e clienti su Supabase.
    """
    try:
        # Seleziona solo i campi essenziali per non consumare banda Egress
        reqs = syncer.get("documents", {
            "document_type": "eq.SYNC_REQUEST",
            "status": "eq.Richiesto",
            "order": "created_at.asc",
            "limit": "1",
            "select": "id,number,notes"
        })
        if reqs and len(reqs) > 0:
            req = reqs[0]
            req_id = req.get("id")
            req_num = req.get("number")
            is_full = "FULL" in (req.get("notes") or "").upper()
            mode_str = "COMPLETO (Tutto il catalogo)" if is_full else "ATTIVO (Giacenze, barcode e movimentati)"
            log(f"⚡ RICEVUTA RICHIESTA DALLA WEB APP: Sincronizzazione da Plus 2000 ➔ Supabase [{mode_str}] (#{req_num})", "🔄")

            # Segna come In Corso
            syncer.update("documents", "id", req_id, {
                "status": "In Corso",
                "notes": f"Sincronizzazione in corso avviata alle {datetime.datetime.now().strftime('%H:%M:%S')}..."
            })

            orig_argv = list(sys.argv)
            if is_full and "--all" not in sys.argv:
                sys.argv.append("--all")
            elif not is_full and "--all" in sys.argv:
                sys.argv.remove("--all")

            try:
                sync_agents(cursor, syncer)
                sync_customers(cursor, syncer)
                sync_open_orders_from_plus_to_supabase(cursor, syncer, force=True)
                sync_products(cursor, syncer)
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                syncer.update("documents", "id", req_id, {
                    "status": "Completato",
                    "notes": f"Allineamento completato con successo alle {now_str}",
                    "plus_doc_id": "OK"
                })
                log(f"🎉 Sincronizzazione richiesta dalla Web App completata con successo! (#{req_num})", "✅")
            finally:
                sys.argv = orig_argv

            return True
    except Exception as e:
        log(f"Avviso durante verifica richieste on-demand: {e}", "⚠️")
    return False


def main():
    print("=" * 70)
    print("  CLIMAWELL - SERVIZIO TEMPO REALE BIDIREZIONALE (OTTIMIZZATO)")
    print("  PLUS 2000 ⇄ SUPABASE ⇄ WEB APP")
    print("  - Orario Lavorativo (07:30 - 19:30): Polling 90s")
    print("  - Notte & Weekend: Standby a basso consumo (10 min)")
    print("  - Filtri PostgREST server-side attivi (Egress protetto)")
    print("  Premi CTRL+C per arrestare il servizio in qualsiasi momento.")
    print("=" * 70)

    cfg = load_config()
    sup_cfg = cfg.get("supabase", {})
    sql_cfg = cfg.get("sql_server", {})

    url = os.environ.get("SUPABASE_URL") or sup_cfg.get("url")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or sup_cfg.get("service_role_key") or sup_cfg.get("anon_key")

    if not url or not key:
        log("ERRORE: Credenziali Supabase mancanti in config.json!", "❌")
        sys.exit(1)

    syncer = SupabaseSyncer(url, key)
    server_info = f"{sql_cfg.get('server')} -> {sql_cfg.get('database')}"
    log(f"Connesso a Supabase: {url}")
    log(f"SQL Server di destinazione: {server_info}")

    cycle_count = 0
    last_orders_check_time = 0

    while True:
        cycle_count += 1
        interval_secs, mode_desc = get_current_poll_interval()

        try:
            conn = get_sql_conn(sql_cfg)
            cursor = conn.cursor()

            try:
                # 0. Sincronizzazione programmata una volta al giorno (06:30 AM Lun-Ven)
                if should_run_daily_full_sync():
                    log("🌅 Avvio sincronizzazione catalogo e clienti programmata del mattino...", "🔄")
                    try:
                        sync_agents(cursor, syncer)
                        sync_customers(cursor, syncer)
                        sync_products(cursor, syncer)
                    except Exception as e_full:
                        log(f"Avviso full-sync giornaliero: {e_full}", "⚠️")

                # 1. Scarica nuovi ordini/offerte da Supabase verso Plus 2000 (con filtro server-side)
                sync_documents_from_supabase_to_plus(cursor, syncer, conn)

                # 2. Sincronizza ordini clienti aperti da Plus verso Supabase
                # Durante il lavoro ogni 10 minuti (600s), oppure se forzato da variazioni
                now_ts = time.time()
                if (now_ts - last_orders_check_time) >= 600 or cycle_count == 1:
                    sync_open_orders_from_plus_to_supabase(cursor, syncer)
                    last_orders_check_time = now_ts

                # 3. Sincronizzazione Realtime Movimenti Magazzino da Plus 2000 (DDT, bolle, carichi)
                # Verifica prima se in SQL Server c'è un nuovo DocId (0 egress se invariato)
                sync_incremental_stock_from_plus(cursor, syncer)

                # 4. Controlla richieste on-demand di sincronizzazione da Plus verso Supabase
                check_and_execute_on_demand_sync(cursor, syncer)

                # 5. Sincronizzazione Packlink PRO (bozze per nuovi ordini e allineamento tracking)
                if cycle_count % 5 == 1:
                    try:
                        from packlink_manager import auto_create_drafts_for_pending_orders, sync_tracking_from_packlink
                        auto_create_drafts_for_pending_orders()
                        sync_tracking_from_packlink()
                    except Exception as ex_pk:
                        log(f"Avviso Packlink Sync: {ex_pk}", "⚠️")
            finally:
                cursor.close()
                conn.close()

            # Heartbeat ogni 20 cicli
            if cycle_count % 20 == 0:
                log(f"Servizio attivo e allineato. Modalità: {mode_desc}", "🟢")

        except KeyboardInterrupt:
            log("Arresto del servizio richiesto dall'utente.", "🛑")
            break
        except Exception as e:
            log(f"Avviso durante il ciclo di sincronizzazione: {e}", "⚠️")
            time.sleep(5)

        # Attesa del prossimo ciclo in base alla fascia oraria
        try:
            time.sleep(interval_secs)
        except KeyboardInterrupt:
            log("Arresto del servizio richiesto dall'utente.", "🛑")
            break


if __name__ == "__main__":
    main()

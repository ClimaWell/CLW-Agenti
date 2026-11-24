#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
CLIMAWELL - SINCRONIZZATORE DIRETTO PLUS 2000 ➔ SUPABASE (POSTGRESQL)
====================================================================
Esegue l'estrazione ad alta velocità di Articoli, Giacenze, Ubicazioni,
Prezzi e Clienti da Microsoft SQL Server (SRVPLUS.Climawell) e carica
i dati direttamente su Supabase tramite API REST / PostgREST.

Uso:
  python sync_plus_to_supabase.py
  python sync_plus_to_supabase.py --url https://xyz.supabase.co --key eyJ...
  python sync_plus_to_supabase.py --pull-orders  (scarica ordini da Supabase a Plus)
"""

import sys
import os
import json
import time
import datetime
import pyodbc
import requests
import re
import collections
import traceback
import urllib.parse

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, "config.json")

# Integrazione IdroLAB / DomusPartes per categorie ufficiali produttori e immagini
DOMUS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "connettore-domuspartes"))
if DOMUS_DIR not in sys.path:
    sys.path.append(DOMUS_DIR)
try:
    from idrolab_indexer import cerca_articolo_idrolab
    print("✅ Modulo IdroLAB / DomusPartes caricato per arricchimento categorie e immagini.")
except Exception as e:
    cerca_articolo_idrolab = None
    print(f"⚠️ Modulo IdroLAB non disponibile: {e}")


def genera_ean13_interno(caid_val) -> str:
    """
    Genera un codice a barre EAN-13 valido conforme agli standard GS1 (prefisso 20 per uso interno aziendale).
    Prefisso 20 + 10 cifre da CaId + checksum modulo 10 standard.
    """
    try:
        num = int(re.sub(r'\D', '', str(caid_val)))
    except Exception:
        num = abs(hash(str(caid_val))) % 10000000000

    base12 = f"20{num:010d}"[-12:]
    total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(base12))
    check_digit = (10 - (total % 10)) % 10
    return f"{base12}{check_digit}"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"File config.json non trovato in {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_sql_conn(sql_cfg):
    dsn = sql_cfg.get("dsn")
    if dsn:
        try:
            return pyodbc.connect(f"DSN={dsn};", autocommit=True, timeout=5)
        except Exception as e:
            print(f"[Avviso DSN]: {e}, fallback su connessione diretta...")

    # Lista candidati server: nome configurato, IP LAN SRVPLUS e localhost
    srv_configured = sql_cfg.get("server", "SRVPLUS")
    candidates = [srv_configured]
    if srv_configured.upper() in ["SRVPLUS", "192.168.1.7"]:
        for extra in ["192.168.1.7", "localhost", "127.0.0.1", "SRVPLUS"]:
            if extra not in candidates:
                candidates.append(extra)

    driver = sql_cfg.get("driver", "SQL Server")
    database = sql_cfg.get("database", "Climawell")
    is_trusted = str(sql_cfg.get("trusted_connection", "")).lower() in ["yes", "true", "1"]

    last_err = None
    for target in candidates:
        conn_str = f"DRIVER={{{driver}}};SERVER={target};DATABASE={database};"
        if is_trusted:
            conn_str += "Trusted_Connection=yes;"
        else:
            conn_str += f"UID={sql_cfg.get('username', 'sa')};PWD={sql_cfg.get('password', '')};"
        try:
            return pyodbc.connect(conn_str, autocommit=True, timeout=5)
        except Exception as err:
            last_err = err

    raise last_err


class SupabaseSyncer:
    def __init__(self, url, key):
        self.url = url.rstrip("/")
        self.key = key
        self.session = requests.Session()
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Prefer": "resolution=merge-duplicates,return=minimal"
        }

    def upsert_batch(self, table, records, on_conflict=None, max_retries=3, resolution="merge-duplicates"):
        if not records:
            return 0
        endpoint = f"{self.url}/rest/v1/{table}"
        if on_conflict:
            endpoint += f"?on_conflict={on_conflict}"
            # Deduplica preventiva all'interno dello stesso batch per evitare l'errore PostgreSQL 21000:
            # "ON CONFLICT DO UPDATE command cannot affect row a second time"
            keys = [k.strip() for k in on_conflict.split(",")]
            dedup = {}
            for r in records:
                composite_key = tuple(r.get(k) for k in keys)
                dedup[composite_key] = r
            records = list(dedup.values())

        req_headers = dict(self.headers)
        req_headers["Prefer"] = f"resolution={resolution},return=minimal"

        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.post(endpoint, headers=req_headers, json=records, timeout=60)
                if resp.status_code in [200, 201, 204]:
                    return len(records)
                elif resp.status_code == 400 and "PGRST204" in resp.text:
                    m = re.search(r"Could not find the '(\w+)' column", resp.text)
                    if m:
                        missing_col = m.group(1)
                        print(f"⚠️ [Supabase {table}] Colonna '{missing_col}' non presente nella tabella cloud: rimozione automatica e re-invio...")
                        for r in records:
                            r.pop(missing_col, None)
                        continue
                raise RuntimeError(f"Errore Supabase ({table}) [{resp.status_code}]: {resp.text}")
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < max_retries:
                    time.sleep(2 * attempt)
                    continue
                raise RuntimeError(f"Timeout dopo {max_retries} tentativi su {table}: {e}")

    def get(self, table, params=None):
        endpoint = f"{self.url}/rest/v1/{table}"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate"
        }
        resp = self.session.get(endpoint, headers=headers, params=params, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            return []
        else:
            raise RuntimeError(f"Errore lettura {table} [{resp.status_code}]: {resp.text}")

    def update(self, table, match_col, match_val, data):
        quoted_val = urllib.parse.quote(str(match_val), safe='')
        endpoint = f"{self.url}/rest/v1/{table}?{match_col}=eq.{quoted_val}"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        resp = self.session.patch(endpoint, headers=headers, json=data, timeout=30)
        return resp.status_code in [200, 204]

    def delete(self, table, match_col, match_val):
        quoted_val = urllib.parse.quote(str(match_val), safe='')
        endpoint = f"{self.url}/rest/v1/{table}?{match_col}=eq.{quoted_val}"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
        }
        resp = self.session.delete(endpoint, headers=headers, timeout=30)
        return resp.status_code in [200, 204]


def sync_products(cursor, syncer, batch_size=100):
    all_catalog = ("--all" in sys.argv)
    print("\n--- 1. ESTRAZIONE ARTICOLI & GIACENZE DA PLUS 2000 ---")
    if all_catalog:
        print("Modalità: TUTTO IL CATALOGO (600k+ articoli)")
        where_filter = "ISNULL(a.JStato, '') NOT IN ('F', 'A', 'ANNULLATO')"
    else:
        print("Modalità: Catalogo Attivo (Giacenza positiva > 0)")
        where_filter = "ISNULL(a.JStato, '') NOT IN ('F', 'A', 'ANNULLATO') AND g.TotEsi > 0"

    query = f"""
    WITH PrezziVen1 AS (
        SELECT CaId, Pz, DValidita,
               ROW_NUMBER() OVER (
                   PARTITION BY CaId 
                   ORDER BY 
                       CASE WHEN DValidita <= CAST(CONVERT(varchar(8), GETDATE(), 112) AS INT) THEN 1 ELSE 0 END DESC,
                       DValidita DESC,
                       DMod DESC,
                       DIns DESC
               ) as rn
        FROM ListiniPrezzi WITH (NOLOCK)
        WHERE JListino = 'VEN1'
    ),
    Giacenze AS (
        SELECT CaId, 
               SUM(QtEsi) as TotEsi, 
               SUM(QtDisp) as TotDisp,
               SUM(ISNULL(QtImp, 0)) as TotImp,
               SUM(CASE WHEN JDep = '000' THEN QtEsi ELSE 0 END) as EsiDep000
        FROM ArticoliContGen WITH (NOLOCK)
        GROUP BY CaId
    ),
    MovimentiRecenti AS (
        SELECT DISTINCT r.CaId
        FROM DocRig r WITH (NOLOCK)
        JOIN DocTes t WITH (NOLOCK) ON r.DocId = t.DocId
        WHERE t.Anno >= 2025
    ),
    ScontiCategorie AS (
        SELECT JTab, MAX(ScontoMax) as ScontoMax
        FROM CatScontiAcqVen WITH (NOLOCK)
        GROUP BY JTab
    )
    SELECT 
        a.CaId,
        RTRIM(LTRIM(a.Ca)) as CodiceArticolo,
        RTRIM(LTRIM(a.DesArt + CASE WHEN a.DesSup IS NOT NULL AND RTRIM(a.DesSup) <> '' THEN ' ' + RTRIM(a.DesSup) ELSE '' END)) as Descrizione,
        RTRIM(LTRIM(ISNULL(a.Marca, ''))) as Marca,
        RTRIM(LTRIM(ISNULL(a.CaProd, ''))) as CodiceProduttore,
        ISNULL(NULLIF(RTRIM(t_set.DesTab), ''), CASE WHEN a.JSettore IN ('0', '00', '') THEN '' ELSE RTRIM(a.JSettore) END) as Settore,
        ISNULL(NULLIF(RTRIM(t_mac.DesMacroFamiglia), ''), CASE WHEN a.JMacroFamiglia IN ('0', '00', '000', '') THEN '' ELSE RTRIM(a.JMacroFamiglia) END) as Macrofamiglia,
        ISNULL(NULLIF(RTRIM(t_fam.DesFamiglia), ''), CASE WHEN a.JFamiglia IN ('0', '00', '000', '') THEN '' ELSE RTRIM(a.JFamiglia) END) as Famiglia,
        RTRIM(LTRIM(ISNULL(a.JStato, ''))) as JStatoProdotto,
        RTRIM(LTRIM(ISNULL(a.JUbiArt, ''))) as Ubicazione,
        ISNULL(p.Pz, 0) as Prezzo,
        RTRIM(LTRIM(ISNULL(a.JScontoVen, ''))) as JScontoVen,
        RTRIM(LTRIM(ISNULL(a.Um, 'NR'))) as UnitaDiMisura,
        ISNULL(g.TotEsi, 0) as Giacenza,
        RTRIM(LTRIM(ISNULL(a.Disegno, ''))) as Disegno,
        (SELECT TOP 1 RTRIM(LTRIM(ac.CaCod)) FROM ArticoliCodici ac WITH (NOLOCK) WHERE ac.CaId = a.CaId ORDER BY ac.Riga) as Ean,
        RTRIM(LTRIM(ISNULL(a.JClasse, ''))) as JClasse,
        RTRIM(LTRIM(ISNULL(a.JGruppo, ''))) as JGruppo,
        ISNULL(cat_sc.ScontoMax, ISNULL(a.Sconto, 0)) as ScontoMax,
        ISNULL(g.TotDisp, 0) as Disponibilita,
        ISNULL(g.TotImp, 0) as Impegnato,
        ISNULL(g.EsiDep000, 0) as GiacenzaSede
    FROM Articoli a WITH (NOLOCK)
    LEFT JOIN PrezziVen1 p ON a.CaId = p.CaId AND p.rn = 1
    LEFT JOIN Giacenze g ON a.CaId = g.CaId
    LEFT JOIN MovimentiRecenti m ON a.CaId = m.CaId
    LEFT JOIN ScontiCategorie cat_sc ON a.JScontoVen = cat_sc.JTab
    LEFT JOIN TabDes t_set WITH (NOLOCK) ON t_set.TpTab = 'SET' AND t_set.JTab = a.JSettore
    LEFT JOIN MacroFamiglie t_mac WITH (NOLOCK) ON t_mac.JSettore = a.JSettore AND t_mac.JMacroFamiglia = a.JMacroFamiglia
    LEFT JOIN Famiglie t_fam WITH (NOLOCK) ON t_fam.JSettore = a.JSettore AND t_fam.JMacroFamiglia = a.JMacroFamiglia AND t_fam.JFamiglia = a.JFamiglia
    WHERE {where_filter}
    ORDER BY g.TotEsi DESC, CodiceArticolo
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    print(f"Estratti {len(rows)} articoli da Plus 2000 (giacenza > 0 o movimentati dal 2025).")

    # Verifica quali colonne sono effettivamente presenti su Supabase products (evita errori schema cache PostgREST)
    valid_product_cols = None
    try:
        probe = syncer.session.get(f"{syncer.url}/rest/v1/products?limit=1", headers=syncer.headers, timeout=10)
        if probe.status_code == 200 and probe.json() and len(probe.json()) > 0:
            valid_product_cols = set(probe.json()[0].keys())
            print(f"  -> Tabella 'products' Supabase: rilevate {len(valid_product_cols)} colonne attive.")
    except Exception as e_prb:
        print(f"  [Avviso verifica colonne products]: {e_prb}")

    if not all_catalog:
        try:
            # Imposta active = false sui prodotti a giacenza zero precedentemente caricati
            syncer.session.patch(
                f"{syncer.url}/rest/v1/products?stock_qty=lte.0",
                headers=syncer.headers,
                json={"active": False}
            )
            print("  -> Disattivati su Supabase gli articoli a giacenza zero non attivi.")
        except Exception as e:
            print(f"  [Avviso disattivazione giacenze zero]: {e}")

    print("Estrazione codici a barre (EAN 13 / Barcode) da ArticoliUm e ArticoliCodici...")
    barcodes_by_caid = collections.defaultdict(list)
    try:
        cursor.execute("""
            SELECT CaId, RTRIM(LTRIM(CaBarCode)) 
            FROM ArticoliUm WITH (NOLOCK) 
            WHERE CaBarCode IS NOT NULL AND RTRIM(LTRIM(CaBarCode)) <> ''
            ORDER BY CaId, Riga
        """)
        for b_caid, b_code in cursor.fetchall():
            if b_caid and b_code and b_code not in barcodes_by_caid[b_caid]:
                barcodes_by_caid[b_caid].append(b_code)
        print(f"  -> Trovati codici a barre per {len(barcodes_by_caid)} articoli in ArticoliUm.")
    except Exception as e:
        print(f"  [Avviso lettura ArticoliUm]: {e}")

    try:
        cursor.execute("""
            SELECT CaId, RTRIM(LTRIM(CaCod)) 
            FROM ArticoliCodici WITH (NOLOCK) 
            WHERE CaCod IS NOT NULL AND RTRIM(LTRIM(CaCod)) <> ''
            ORDER BY CaId, Riga
        """)
        for b_caid, b_code in cursor.fetchall():
            if b_caid and b_code and b_code not in barcodes_by_caid[b_caid]:
                barcodes_by_caid[b_caid].append(b_code)
    except Exception as e:
        print(f"  [Avviso lettura ArticoliCodici]: {e}")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    product_batch = []
    location_batch = []
    total_synced = 0
    enriched_count = 0

    for r in rows:
        caid = str(r[0] or "").strip()
        code = str(r[1] or caid).strip()
        desc = str(r[2] or "").strip()
        brand = str(r[3] or "").strip()
        caprod = str(r[4] or "").strip()
        settore = str(r[5] or "").strip()
        macro = str(r[6] or "").strip()
        fam = str(r[7] or "").strip()
        ubi = str(r[9] or "").strip()
        prezzo = float(r[10] or 0.0)
        sconto = str(r[11] or "").strip()
        um = str(r[12] or "PZ").strip()
        giacenza = float(r[13] or 0.0)
        disegno = str(r[14] or "").strip()
        ean_sql = str(r[15] or "").strip()
        classe = str(r[16] or "").strip()
        gruppo = str(r[17] or "").strip()
        max_sconto = float(r[18] or 0.0)
        disp_val = float(r[19] or 0.0)
        imp_val = float(r[20] or 0.0)
        giac_sede = float(r[21] or 0.0)

        img_url = ""
        if disegno:
            if disegno.lower().startswith("http"):
                img_url = disegno
            else:
                img_url = f"https://www.domuspartes.it/immagini/{disegno}"

        # Arricchimento automatico categorie e immagini da banca dati IdroLAB / DomusPartes
        idro = None
        if cerca_articolo_idrolab:
            idro = cerca_articolo_idrolab(code, caprod=caprod, ean=ean_sql)
            if idro:
                s_domus = (idro.get("settore") or "").strip()
                m_domus = (idro.get("macrofamiglia") or "").strip()
                f_domus = (idro.get("famiglia") or "").strip()
                u_domus = (idro.get("url_immagine") or "").strip()

                did_enrich = False
                if (not settore or settore.isdigit() or settore.lower() in ("0", "non classificato")) and s_domus:
                    settore = s_domus
                    did_enrich = True
                if (not macro or macro.isdigit() or macro.lower() in ("0", "non classificato")) and m_domus:
                    macro = m_domus
                    did_enrich = True
                if (not fam or fam.isdigit() or fam.lower() in ("0", "non classificato")) and f_domus:
                    fam = f_domus
                    did_enrich = True
                if not img_url and u_domus:
                    img_url = u_domus
                    did_enrich = True
                if did_enrich:
                    enriched_count += 1

        # Risoluzione Barcode:
        # 1. Barcode presenti in Plus 2000 (ArticoliUm / ArticoliCodici)
        caid_int = int(caid) if caid.isdigit() else 0
        art_barcodes = list(barcodes_by_caid.get(caid_int, []))
        if ean_sql and ean_sql not in art_barcodes:
            art_barcodes.append(ean_sql)

        # 2. Cerca EAN in IdroLAB / DomusPartes
        if idro and idro.get("ean"):
            idro_ean = str(idro.get("ean")).strip().replace(" ", "")
            if idro_ean and idro_ean not in art_barcodes:
                art_barcodes.append(idro_ean)

        # 3. Se ancora nessun barcode, genera EAN-13 aziendale (GS1 prefisso 20)
        if not art_barcodes:
            art_barcodes.append(genera_ean13_interno(caid or code))

        final_barcode = ", ".join(art_barcodes)

        p_item = {
            "code": code,
            "caid": caid,
            "description": desc,
            "brand": brand,
            "sector": settore,
            "macro_family": macro,
            "family": fam,
            "class_code": classe,
            "group_code": gruppo,
            "um": um,
            "price": round(prezzo, 4),
            "stock_qty": round(giacenza, 2),
            "available_qty": round(disp_val, 2),
            "committed_qty": round(imp_val, 2),
            "primary_location": ubi,
            "barcode": final_barcode,
            "discount_family": sconto,
            "max_discount": round(max_sconto, 2),
            "image_ref": disegno,
            "image_url": img_url,
            "active": True,
            "plus_sync_at": now_iso
        }
        if valid_product_cols:
            p_item = {k: v for k, v in p_item.items() if k in valid_product_cols}

        product_batch.append(p_item)

        # Multi-ubicazione: se presente ubicazione, crea record in product_locations
        if ubi:
            parts = [p.strip() for p in ubi.split("|") if p.strip()]
            for idx, p in enumerate(parts):
                loc_type = "PICKING" if idx == 0 else "SCORTA"
                if "scorta" in p.lower():
                    loc_type = "SCORTA"
                location_batch.append({
                    "product_code": code,
                    "location_code": p.upper(),
                    "location_type": loc_type,
                    "is_primary": (idx == 0),
                    "quantity": round(giacenza, 2) if idx == 0 else 0
                })

        if len(product_batch) >= 500:
            syncer.upsert_batch("products", product_batch, on_conflict="code")
            if location_batch:
                try:
                    unique_locs = list({(x["product_code"], x["location_code"]): x for x in location_batch}.values())
                    syncer.upsert_batch("product_locations", unique_locs, on_conflict="product_code,location_code")
                except Exception:
                    pass
                location_batch.clear()
            total_synced += len(product_batch)
            print(f"  ... Sincronizzati {total_synced}/{len(rows)} articoli (arricchiti con DomusPartes: {enriched_count})...")
            product_batch.clear()

    if product_batch:
        syncer.upsert_batch("products", product_batch, on_conflict="code")
        if location_batch:
            try:
                unique_locs = list({(x["product_code"], x["location_code"]): x for x in location_batch}.values())
                syncer.upsert_batch("product_locations", unique_locs, on_conflict="product_code,location_code")
            except Exception:
                pass
        total_synced += len(product_batch)

    print(f"✅ Completata sincronizzazione articoli: {total_synced} record allineati su Supabase (arricchiti con categorie DomusPartes: {enriched_count})!")


def sync_customers(cursor, syncer, batch_size=100):
    all_records = ("--all" in sys.argv)
    print("\n--- 2. ESTRAZIONE ANAGRAFICA CLIENTI DA PLUS 2000 ---")
    
    # Includiamo tutti i conti clienti 'C' senza escluderli per c.Bloccato (che potrebbe essere 1 o NULL su clienti test/nuovi)
    where_conditions = ["RTRIM(LTRIM(c.TpConto)) = 'C'"]
    if "--cliente" in sys.argv:
        try:
            target_cod = sys.argv[sys.argv.index("--cliente") + 1]
            where_conditions.append(f"c.JConto = '{target_cod}'")
        except Exception:
            pass
    where_sql = " AND ".join(where_conditions)

    query = f"""
    SELECT 
        c.JConto AS CodiceConto,
        RTRIM(LTRIM(c.RagSoc + CASE WHEN c.RagSup IS NOT NULL AND RTRIM(c.RagSup) <> '' THEN ' ' + RTRIM(c.RagSup) ELSE '' END)) AS RagioneSociale,
        RTRIM(LTRIM(ISNULL(c.PartitaIva, ''))) AS PartitaIVA,
        RTRIM(LTRIM(ISNULL(c.CodFiscale, ''))) AS CodiceFiscale,
        RTRIM(LTRIM(ISNULL(c.Indirizzo, ''))) AS Indirizzo,
        RTRIM(LTRIM(ISNULL(c.Cap, ''))) AS CAP,
        RTRIM(LTRIM(ISNULL(c.Citta, ''))) AS Localita,
        RTRIM(LTRIM(ISNULL(c.Provincia, ''))) AS Provincia,
        COALESCE(NULLIF(RTRIM(c.Telefono), ''), NULLIF(RTRIM(ct.Telefono), ''), '') AS Telefono,
        COALESCE(NULLIF(RTRIM(c.Cellulare), ''), NULLIF(RTRIM(ct.Cellulare), ''), '') AS Cellulare,
        COALESCE(NULLIF(RTRIM(c.EMail), ''), NULLIF(RTRIM(c.OclMail), ''), NULLIF(RTRIM(c.FatMail), ''), NULLIF(RTRIM(ct.EMail), ''), '') AS Email,
        COALESCE(NULLIF(RTRIM(c.EMailPEC), ''), '') AS PEC,
        c.JAgente AS CodiceAgente,
        RTRIM(LTRIM(ISNULL(c.JPagamento, ''))) AS CodicePagamento,
        '0000000' AS SDI
    FROM CliFor c WITH (NOLOCK)
    LEFT JOIN (
        SELECT JConto, 
               MAX(Telefono) as Telefono, 
               MAX(Cellulare) as Cellulare, 
               MAX(EMail) as EMail
        FROM CliForContatti WITH (NOLOCK)
        WHERE TpConto = 'C'
        GROUP BY JConto
    ) ct ON c.JConto = ct.JConto
    LEFT JOIN (
        SELECT JConto, MAX(Anno) as MaxAnno
        FROM DocTes WITH (NOLOCK)
        WHERE TpConto = 'C'
        GROUP BY JConto
    ) doc ON c.JConto = doc.JConto
    WHERE {where_sql}
    ORDER BY c.JConto
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    print(f"Estratti {len(rows)} clienti da Plus 2000.")

    # Recupera i codici agenti validi presenti su Supabase per rispettare il vincolo Foreign Key
    known_agents = set()
    try:
        ag_resp = syncer.session.get(f"{syncer.url}/rest/v1/agents?select=code", headers=syncer.headers, timeout=15)
        if ag_resp.status_code == 200:
            for item in ag_resp.json():
                if item.get("code"):
                    known_agents.add(str(item["code"]).strip())
    except Exception as e:
        print(f"Avviso verifica agenti FK: {e}")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cust_batch = []
    total_synced = 0

    for r in rows:
        code = str(r[0] or "").strip()
        name = str(r[1] or "").strip()
        piva = str(r[2] or "").strip()
        cf = str(r[3] or "").strip()
        addr = str(r[4] or "").strip()
        cap = str(r[5] or "").strip()
        city = str(r[6] or "").strip()
        prov = str(r[7] or "").strip()
        tel = str(r[8] or "").strip()
        cell = str(r[9] or "").strip()
        email = str(r[10] or "").strip()
        pec = str(r[11] or "").strip()
        ag_raw = str(r[12] or "").strip()
        pag = str(r[13] or "").strip()
        sdi = str(r[14] or "0000000").strip()

        if ag_raw and ag_raw not in known_agents:
            try:
                syncer.session.post(
                    f"{syncer.url}/rest/v1/agents",
                    headers=syncer.headers,
                    json=[{"code": ag_raw, "name": f"Agente {ag_raw}", "role": "agente", "active": True, "attivo": True, "can_offer": True, "can_order": True}]
                )
                known_agents.add(ag_raw)
            except Exception:
                pass

        agente_code = ag_raw if (ag_raw in known_agents or not known_agents) else ag_raw

        cust_batch.append({
            "code": code,
            "name": name,
            "vat_number": piva or None,
            "tax_code": cf or None,
            "address": addr,
            "postal_code": cap,
            "city": city,
            "province": prov,
            "phone": tel or cell or None,
            "mobile": cell or None,
            "email": email or None,
            "pec": pec or None,
            "agent_code": agente_code,
            "payment_method": pag or None,
            "sdi_code": sdi,
            "plus_sync_at": now_iso
        })

        hub_batch = [{
            "customer_code": x["code"],
            "business_name": x["name"],
            "city": x["city"],
            "province": x["province"],
            "address": x["address"],
            "postal_code": x["postal_code"],
            "phone": x["phone"],
            "mobile_whatsapp": x["mobile"] or x["phone"],
            "email": x["email"],
            "vat_number": x["vat_number"],
            "fiscal_code": x["tax_code"],
            "assigned_agent_code": x["agent_code"]
        } for x in cust_batch]

        if len(cust_batch) >= batch_size:
            syncer.upsert_batch("customers", cust_batch, on_conflict="code")
            try:
                syncer.upsert_batch("hub_customers", hub_batch, on_conflict="customer_code")
            except Exception as e_hub:
                pass
            total_synced += len(cust_batch)
            print(f"  ... Sincronizzati {total_synced}/{len(rows)} clienti...")
            cust_batch.clear()

    if cust_batch:
        hub_batch = [{
            "customer_code": x["code"],
            "business_name": x["name"],
            "city": x["city"],
            "province": x["province"],
            "address": x["address"],
            "postal_code": x["postal_code"],
            "phone": x["phone"],
            "mobile_whatsapp": x["mobile"] or x["phone"],
            "email": x["email"],
            "vat_number": x["vat_number"],
            "fiscal_code": x["tax_code"],
            "assigned_agent_code": x["agent_code"]
        } for x in cust_batch]
        syncer.upsert_batch("customers", cust_batch, on_conflict="code")
        try:
            syncer.upsert_batch("hub_customers", hub_batch, on_conflict="customer_code")
        except Exception:
            pass
        total_synced += len(cust_batch)

    print(f"✅ Completata sincronizzazione clienti: {total_synced} anagrafiche su Supabase e Commercial Hub!")


def sync_agents(cursor, syncer):
    print("\n--- 3. ESTRAZIONE RETE AGENTI UFFICIALE DA PLUS 2000 ---")
    query = """
    SELECT 
        c.JAgente AS CodiceAgente,
        RTRIM(LTRIM(ISNULL(ag.RagSoc, 'SENZA NOME') + CASE WHEN ag.RagSup IS NOT NULL AND RTRIM(ag.RagSup) <> '' THEN ' ' + RTRIM(ag.RagSup) ELSE '' END)) AS NomeAgente,
        RTRIM(LTRIM(ISNULL(ag.Cellulare, ag.Telefono))) AS Telefono,
        RTRIM(LTRIM(ISNULL(ag.EMail, ''))) AS Email,
        CASE WHEN ag.Bloccato = 1 THEN 0 ELSE 1 END AS Attivo
    FROM CliFor c WITH (NOLOCK)
    LEFT JOIN CliFor ag WITH (NOLOCK) ON ag.TpConto = 'F' AND ag.JConto = c.JAgente
    WHERE c.TpConto = 'C' AND c.JAgente > 0
    GROUP BY c.JAgente, ag.RagSoc, ag.RagSup, ag.Cellulare, ag.Telefono, ag.EMail, ag.Bloccato
    HAVING COUNT(DISTINCT c.JConto) >= 1
    ORDER BY c.JAgente
    """
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"Estratti {len(rows)} agenti attivi da Plus 2000.")

        blacklist_keywords = ["NON USARE", "SENZA AGENTE", "SENZA NOME", "CLIMAWELL 2", "CLIMAWELL SRL", "DIREZIONE", "VIA MORELLI", "VIA DELLA CASELLA", "VIA COSSERIA", "VIA XX SETTEMBRE"]

        agent_batch = []
        for r in rows:
            code = str(r[0] or "").strip()
            name = str(r[1] or f"Agente {code}").strip()
            tel = str(r[2] or "").strip()
            email = str(r[3] or "").strip()
            plus_attivo = bool(r[4])

            # Un agente è operativo se non è bloccato in Plus 2000 e non è un conto tecnico
            name_upper = name.upper()
            is_blacklisted = any(k in name_upper for k in blacklist_keywords)
            attivo = plus_attivo and not is_blacklisted

            agent_batch.append({
                "code": code,
                "name": name,
                "role": "agente",
                "phone": tel or None,
                "email": email or None,
                "active": attivo,
                "attivo": attivo,
                "can_offer": True,
                "can_order": True,
                "can_warehouse": False,
                "discount_limit": 60.00
            })

        if agent_batch:
            syncer.upsert_batch("agents", agent_batch, on_conflict="code")
            print(f"✅ Completata sincronizzazione agenti: {len(agent_batch)} agenti allineati su Supabase!")
    except Exception as e:
        print(f"⚠️ Avviso lettura agenti da Plus 2000: {e}")


def get_ultimo_prezzo_acquisto(cursor, ca_id, anno):
    """
    Recupera il prezzo dell'ultimo acquisto per un articolo da Plus 2000:
    1. Da ArticoliContEse (PzUltAcq) dell'esercizio
    2. Da ListiniPrezzi con JListino = 'ACQ'
    3. Dall'ultimo movimento di carico fornitore in DocRig
    """
    if not ca_id:
        return 0.0
    try:
        # 1. ArticoliContEse esercizio corrente o recente
        cursor.execute("SELECT TOP 1 PzUltAcq FROM ArticoliContEse WITH (NOLOCK) WHERE CaId = ? AND Ese = ? AND PzUltAcq > 0", (ca_id, anno))
        r = cursor.fetchone()
        if r and r[0] and float(r[0]) > 0:
            return float(r[0])

        cursor.execute("SELECT TOP 1 PzUltAcq FROM ArticoliContEse WITH (NOLOCK) WHERE CaId = ? AND PzUltAcq > 0 ORDER BY Ese DESC", (ca_id,))
        r = cursor.fetchone()
        if r and r[0] and float(r[0]) > 0:
            return float(r[0])

        # 2. Listino acquisto ACQ
        cursor.execute("SELECT TOP 1 Pz FROM ListiniPrezzi WITH (NOLOCK) WHERE CaId = ? AND JListino = 'ACQ' AND Pz > 0 ORDER BY DValidita DESC", (ca_id,))
        r = cursor.fetchone()
        if r and r[0] and float(r[0]) > 0:
            return float(r[0])

        # 3. Ultimo movimento storico acquisti in DocRig
        cursor.execute("""
            SELECT TOP 1 r.PzNetto 
            FROM DocRig r WITH (NOLOCK) 
            JOIN DocTes t WITH (NOLOCK) ON r.DocId = t.DocId
            WHERE r.CaId = ? AND (r.JCauMaga IN ('CAR', 'FAC', 'DTA') OR t.TpDoc IN ('FAC', 'DTA')) AND r.PzNetto > 0
            ORDER BY t.Anno DESC, t.DDoc DESC, r.DocId DESC
        """, (ca_id,))
        r = cursor.fetchone()
        if r and r[0] and float(r[0]) > 0:
            return float(r[0])
    except Exception:
        pass
    return 0.0


def sync_documents_from_supabase_to_plus(cursor, syncer, conn):
    try:
        # Recupera SOLO i documenti non ancora allineati su Plus 2000
        # Filtraggio server-side su PostgREST: evita di riscaricare tutto lo storico (risparmio 99.9% egress)
        all_docs = syncer.get("documents", {
            "select": "id,number,document_type,status,customer_name,customer_code,agent_code,total,subtotal,vat_total,notes,created_at,plus_doc_id",
            "or": "(plus_doc_id.is.null,status.in.(Nuovo,Da allineare,submitted,approved))",
            "status": "neq.Allineato Plus",
            "order": "created_at.asc",
            "limit": "25"
        })

        if not all_docs:
            return

        # Elabora solo i documenti non ancora allineati su Plus 2000
        docs_to_process = [
            d for d in all_docs
            if (not d.get("plus_doc_id") or d.get("status") in ["Nuovo", "Da allineare", "submitted", "approved"])
               and d.get("status") != "Allineato Plus"
        ]

        if not docs_to_process:
            return

        print(f"\n--- SCARICAMENTO OFFERTE/ORDINI: Trovati {len(docs_to_process)} documenti da allineare su Plus 2000 ---")

        for doc in docs_to_process:
            doc_number = doc.get("number")
            raw_type = str(doc.get("document_type") or "OFC").upper()
            doc_notes = str(doc.get("notes") or "").strip()

            # Determinazione Tipo Documento, Sequenza e Causale Magazzino Plus 2000:
            # - MAG (Movimenti Magazzino / Rettifiche): Sequenza '000', Listino 'ACQ', Causale 'CAR' (Carico) o 'SCAR' (Scarico)
            # - OFC (Offerta Cliente): Sequenza '00', Listino 'VEN1', Causale 'OFC'
            # - OCL (Ordine Cliente): Sequenza '00', Listino 'VEN1', Causale 'OCL'
            is_mag = False
            if raw_type in ["CAR", "CARICO", "MAG_CAR", "MAG_CARICO"]:
                is_mag = True
                tp_doc = "MAG"
                cau_maga = "CAR"
                des_cau_maga = "CARICO"
                j_seq_doc = "000"
            elif raw_type in ["SCAR", "SCARICO", "MAG_SCAR", "MAG_SCARICO"]:
                is_mag = True
                tp_doc = "MAG"
                cau_maga = "SCAR"
                des_cau_maga = "SCARICO"
                j_seq_doc = "000"
            elif raw_type in ["MAG", "MOV", "INVENTARIO"]:
                is_mag = True
                tp_doc = "MAG"
                j_seq_doc = "000"
                # Rileva da note o causale se si tratta di scarico
                if "SCAR" in doc_notes.upper() or "MENO" in doc_notes.upper() or "-" in str(doc.get("total") or ""):
                    cau_maga = "SCAR"
                    des_cau_maga = "SCARICO"
                else:
                    cau_maga = "CAR"
                    des_cau_maga = "CARICO"
            elif raw_type in ["ORDER", "OCL", "ORD"]:
                tp_doc = "OCL"
                cau_maga = "ORCL"
                des_cau_maga = "ORDINE CLIENTE"
                j_seq_doc = "00"
            else:
                tp_doc = "OFC"
                cau_maga = "OFC"
                des_cau_maga = "OFFERTA A CLIENTE"
                j_seq_doc = "00"

            doc_date_str = str(doc.get("document_date") or datetime.date.today())
            try:
                dt = datetime.datetime.strptime(doc_date_str[:10], "%Y-%m-%d")
                d_doc_int = int(dt.strftime("%Y%m%d"))
                anno = dt.year
            except Exception:
                d_doc_int = int(datetime.date.today().strftime("%Y%m%d"))
                anno = datetime.date.today().year

            cust_code = str(doc.get("customer_code") or "").strip()
            cust_name = str(doc.get("customer_name") or "").strip()
            notes = str(doc.get("notes") or "").strip()
            j_seq_doc = "00"

            # 1. Determinazione Dinamica Cliente (JConto su Plus 2000) dalla scheda anagrafica
            j_conto = 0

            # A) Se il codice cliente memorizzato è già il JConto numerico di Plus 2000
            if cust_code and cust_code.isdigit():
                j_conto = int(cust_code)

            # B) Se cust_code ha caratteri alfanumerici (es. estrazione cifre)
            if j_conto == 0 and cust_code:
                m_c = re.search(r'\d+', cust_code)
                if m_c:
                    candidate_id = int(m_c.group(0))
                    # Verifica che il conto esista effettivamente in CliFor
                    cursor.execute("SELECT TOP 1 JConto FROM CliFor WITH (NOLOCK) WHERE TpConto = 'C' AND JConto = ?", (candidate_id,))
                    chk = cursor.fetchone()
                    if chk:
                        j_conto = int(chk[0])

            # C) Ricerca per codice anagrafico o Partita IVA in CliFor su Plus 2000
            if j_conto == 0 and cust_code:
                try:
                    cursor.execute("SELECT TOP 1 JConto FROM CliFor WITH (NOLOCK) WHERE TpConto = 'C' AND Codice = ?", (cust_code,))
                    r_c = cursor.fetchone()
                    if r_c: j_conto = int(r_c[0])
                except Exception:
                    pass

            # D) Ricerca per Partita IVA / Codice Fiscale da Supabase o anagrafica
            if j_conto == 0 and cust_code:
                try:
                    cust_sup = syncer.get("customers", {"code": f"eq.{cust_code}", "select": "vat_number,tax_code,name"})
                    if cust_sup and len(cust_sup) > 0:
                        c_info = cust_sup[0]
                        v_num = (c_info.get("vat_number") or "").strip()
                        cf_num = (c_info.get("tax_code") or "").strip()
                        if v_num:
                            cursor.execute("SELECT TOP 1 JConto FROM CliFor WITH (NOLOCK) WHERE TpConto = 'C' AND PartitaIva = ?", (v_num,))
                            r_v = cursor.fetchone()
                            if r_v: j_conto = int(r_v[0])
                        if j_conto == 0 and cf_num:
                            cursor.execute("SELECT TOP 1 JConto FROM CliFor WITH (NOLOCK) WHERE TpConto = 'C' AND CodFiscale = ?", (cf_num,))
                            r_cf = cursor.fetchone()
                            if r_cf: j_conto = int(r_cf[0])
                except Exception:
                    pass

            # E) Ricerca dinamica per Ragione Sociale (senza mai fissare codici manuali)
            if j_conto == 0 and cust_name:
                try:
                    clean_name = cust_name.replace("'", " ").strip()
                    first_word = clean_name.split()[0] if clean_name.split() else ""
                    if len(first_word) >= 3:
                        cursor.execute("SELECT TOP 1 JConto FROM CliFor WITH (NOLOCK) WHERE TpConto = 'C' AND (RagSoc LIKE ? OR RagSup LIKE ?)", (f"%{first_word}%", f"%{first_word}%"))
                        r_name = cursor.fetchone()
                        if r_name: j_conto = int(r_name[0])
                except Exception:
                    pass

            # 2. Determinazione Agente & Compilatore
            ag_code = str(doc.get("agent_code") or "").strip()
            m_ag = re.search(r'\d+', ag_code)
            j_agente = int(m_ag.group(0)) if m_ag else 0
            compilatore_val = str(j_agente) if j_agente > 0 else "web"

            print(f"\n  -> Elaborazione {tp_doc} {doc_number}:")
            print(f"     Cliente: '{cust_name}' (Codice: {cust_code}) -> JConto Scheda Anagrafica: {j_conto} | Agente: {j_agente} | Compilatore: '{compilatore_val}' | Causale Maga: '{cau_maga}'")

            # Recupera righe da Supabase
            lines = syncer.get("document_lines", {
                "select": "*",
                "document_number": f"eq.{doc_number}",
                "order": "line_number.asc"
            })

            # Impostazioni testata e riga in base al tipo documento
            doc_listino = "ACQ" if is_mag else "VEN1"
            doc_tipo = "" if is_mag else "CLI"
            doc_tp_conto = "N" if is_mag else "C"
            doc_j_conto = 0 if is_mag else j_conto
            doc_j_dep_pri = "000" if (is_mag or tp_doc == "OCL") else ""
            doc_j_dep_sec = "000" if (is_mag or tp_doc == "OCL") else ""

            # Verifica preventiva anti-duplicazione documento su Plus 2000
            existing = None
            p_id_match = re.search(r'ID:(\d+)', str(doc.get("plus_doc_id") or ""))
            if p_id_match:
                candidate_doc_id = int(p_id_match.group(1))
                cursor.execute("SELECT TOP 1 DocId, YDoc FROM DocTes WHERE DocId = ?", (candidate_doc_id,))
                existing = cursor.fetchone()

            if not existing:
                clean_ref = doc_number.strip()
                cursor.execute("""
                    SELECT TOP 1 DocId, YDoc 
                    FROM DocTes WITH (NOLOCK) 
                    WHERE Anno = ? AND TpDoc = ? AND (
                        RifOrd = ? OR RifOrd = ? OR RifOrd LIKE ?
                    )
                """, (anno, tp_doc, clean_ref[:30], clean_ref[:20], clean_ref[:18] + "%"))
                existing = cursor.fetchone()

            if existing:
                doc_id_plus, y_doc = int(existing[0]), int(existing[1])
                print(f"     [MODIFICA] Aggiornamento documento esistente #{y_doc}/{anno} (DocId={doc_id_plus})...")
                cursor.execute("""
                    UPDATE DocTes
                    SET JCauMaga = ?, DesCauMaga = ?,
                        TpConto = ?, JConto = ?, TpContoDest = ?, JContoDest = ?,
                        JValuta = 'EUR', ACambio = 1.0, JListino = ?, JTipo = ?,
                        JAgente = ?, JCompilatore = ?, DPrezzo = ?, RifOrd = ?,
                        JDepPri = ?, JDepSec = ?
                    WHERE DocId = ?
                """, (cau_maga, des_cau_maga, doc_tp_conto, doc_j_conto, doc_tp_conto, doc_j_conto,
                      doc_listino, doc_tipo, j_agente, compilatore_val[:10], d_doc_int, doc_number[:30],
                      doc_j_dep_pri, doc_j_dep_sec, doc_id_plus))
                cursor.execute("DELETE FROM DocRig WHERE DocId = ?", (doc_id_plus,))
            else:
                # Genera numerazione con Stored Procedure native di Plus 2000
                sql_seq = f"""
                SET NOCOUNT ON;
                DECLARE @YDocOut int, @DDocOut int, @YDoc int;
                EXEC sp_Sequenze_Ricerca {anno}, '{tp_doc}', '{j_seq_doc}', @YDocOut OUTPUT, @DDocOut OUTPUT;
                SET @YDoc = ISNULL(@YDocOut, 0) + 1;
                EXEC sp_Sequenze_Aggiorna 1, {anno}, '{tp_doc}', '{j_seq_doc}', @YDoc, {d_doc_int}, @YDocOut OUTPUT;
                SELECT @YDocOut;
                """
                cursor.execute(sql_seq)
                row_res = cursor.fetchone()
                y_doc = row_res[0] if row_res else 1

                sql_insert_tes = f"""
                SET NOCOUNT ON;
                INSERT INTO DocTes (
                    Anno, TpDoc, JSeqDoc, YDoc, DDoc,
                    JCauMaga, DesCauMaga,
                    TpConto, JConto, TpContoDest, JContoDest,
                    JValuta, ACambio, JListino, JTipo,
                    JAgente, JCompilatore, DPrezzo,
                    RifOrd, DRifOrd, Note,
                    JDepPri, JDepSec
                ) VALUES (
                    {anno}, '{tp_doc}', '{j_seq_doc}', {y_doc}, {d_doc_int},
                    '{cau_maga}', '{des_cau_maga}',
                    '{doc_tp_conto}', {doc_j_conto}, '{doc_tp_conto}', {doc_j_conto},
                    'EUR', 1.0, '{doc_listino}', '{doc_tipo}',
                    {j_agente}, ?, {d_doc_int},
                    ?, {d_doc_int}, ?,
                    '{doc_j_dep_pri}', '{doc_j_dep_sec}'
                );
                SELECT SCOPE_IDENTITY();
                """
                cursor.execute(sql_insert_tes, (compilatore_val[:10], doc_number[:30], notes[:100]))
                doc_id_plus = int(cursor.fetchone()[0])

                try:
                    cursor.execute(f"EXEC sp_DocTes_SetDefault {doc_id_plus}, 0")
                except Exception:
                    pass

                cursor.execute("""
                    UPDATE DocTes
                    SET JCauMaga = ?, DesCauMaga = ?, JConto = ?, JContoDest = ?, JAgente = ?, JCompilatore = ?, JTipo = ?, JListino = ?, JDepPri = ?, JDepSec = ?, RifOrd = ?
                    WHERE DocId = ?
                """, (cau_maga, des_cau_maga, doc_j_conto, doc_j_conto, j_agente, compilatore_val[:10], doc_tipo, doc_listino, doc_j_dep_pri, doc_j_dep_sec, doc_number[:30], doc_id_plus))

            # Inserimento Righe (DocRig)
            for r_num, line in enumerate(lines, start=1):
                p_code = line.get("product_code") or ""
                p_desc = (line.get("description") or "")[:200]
                qty_raw = float(line.get("quantity") or 1)
                qty = abs(qty_raw)

                ca_id = 0
                if p_code:
                    cursor.execute("SELECT TOP 1 CaId FROM Articoli WITH (NOLOCK) WHERE Ca = ?", (p_code,))
                    art_row = cursor.fetchone()
                    if art_row:
                        ca_id = int(art_row[0])

                if is_mag:
                    # Movimenti Magazzino: Prezzo Ultimo Acquisto da ArticoliContEse / Listino ACQ / Movimenti
                    pz_acq = get_ultimo_prezzo_acquisto(cursor, ca_id, anno)
                    pz_lordo = pz_acq
                    pz_net = pz_acq
                    sc1 = sc2 = sc3 = sc4 = 0.0
                    tot_riga = round(qty * pz_net, 4)
                    riga_cau = cau_maga  # 'CAR' o 'SCAR'
                    riga_um = "NR"
                    riga_listino = "ACQ"
                    iva = "22"
                else:
                    # Offerte / Ordini: Prezzo Vendita e Sconti Cliente
                    pz_lordo = float(line.get("list_price") or 0)
                    sc1 = float(line.get("discount_1") or 0.0)
                    sc2 = float(line.get("discount_2") or 0.0)
                    sc3 = float(line.get("discount_3") or 0.0)
                    sc4 = float(line.get("discount_4") or 0.0)
                    sc_extra = float(line.get("discount_extra") or line.get("extra_discount") or line.get("extraDiscount") or 0.0)
                    disc_mult = (1 - sc1/100) * (1 - sc2/100) * (1 - sc3/100) * (1 - sc4/100) * (1 - sc_extra/100)
                    pz_net = float(line.get("net_price") or (pz_lordo * disc_mult))
                    tot_riga = float(line.get("total") or (qty * pz_net))
                    riga_cau = cau_maga  # 'OFC' o 'ORCL'
                    riga_dep = "000" if (is_mag or tp_doc == "OCL") else ""
                    riga_um = line.get("um") or "PZ"
                    riga_listino = "VEN1"
                    iva = str(line.get("vat") or "22")[:4]

                sql_insert_rig = f"""
                SET NOCOUNT ON;
                INSERT INTO DocRig (
                    DocId, Riga, TpDoc, JSeqDoc, DDoc,
                    CaId, DesArt, Um, UmQt, Pezzi, Qt,
                    JListino, PzLordo, PzNetto,
                    Sconto1, Sconto2, Sconto3, Sconto4, ScontoExtra, Ricarico,
                    ATotale, ATotaleIC, JIva, Note,
                    TpConto, JConto, JContoDest, JCauMaga, JDep
                ) VALUES (
                    {doc_id_plus}, {r_num}, '{tp_doc}', '{j_seq_doc}', {d_doc_int},
                    {ca_id}, ?, '{riga_um}', '{riga_um}', {qty}, {qty},
                    '{riga_listino}', {pz_lordo}, {pz_net},
                    {sc1}, {sc2}, {sc3}, {sc4}, {sc_extra}, 0.0,
                    {tot_riga}, {tot_riga}, '{iva}', ?,
                    '{doc_tp_conto}', {doc_j_conto}, {doc_j_conto}, '{riga_cau}', '{riga_dep}'
                );
                SELECT SCOPE_IDENTITY();
                """
                cursor.execute(sql_insert_rig, (p_desc, notes[:100]))
                riga_id_plus = int(cursor.fetchone()[0])

                try:
                    cursor.execute(f"EXEC sp_DocRig_SetDefault {riga_id_plus}, 0, 0")
                except Exception:
                    pass

                # Riafferma causale di riga, deposito '000', listino ACQ o VEN1, prezzi e sconti (incluso ScontoExtra)
                cursor.execute("""
                    UPDATE DocRig
                    SET JCauMaga = ?, JDep = ?, JListino = ?, PzLordo = ?, PzNetto = ?,
                        Sconto1 = ?, Sconto2 = ?, Sconto3 = ?, Sconto4 = ?, ScontoExtra = ?,
                        ATotale = ?, ATotaleIC = ?, JConto = ?, JContoDest = ?
                    WHERE RigaId = ?
                """, (riga_cau, riga_dep, riga_listino, pz_lordo, pz_net, sc1, sc2, sc3, sc4, sc_extra, tot_riga, tot_riga, doc_j_conto, doc_j_conto, riga_id_plus))

            # Ricalcola totali documento
            try:
                cursor.execute(f"EXEC sp_Doc_Aggiorna_Totali {doc_id_plus}")
            except Exception:
                pass

            conn.commit()
            print(f"     ✅ Allineato con successo su Plus 2000! Documento #{y_doc}/{anno} (DocId={doc_id_plus})")

            # Aggiorna Supabase
            syncer.update("documents", "number", doc_number, {
                "plus_doc_id": f"{tp_doc} {y_doc}/{anno} (ID:{doc_id_plus})",
                "status": "Allineato Plus"
            })

    except Exception as e:
        print(f"⚠️ Errore durante scaricamento ordini su Plus 2000: {e}")


_last_orders_signature = None

def sync_open_orders_from_plus_to_supabase(cursor, syncer, force=False):
    """
    Sincronizza gli ordini clienti aperti da Plus 2000 verso Supabase (DocTes con Evaso = 'N').
    Permette alla pagina Magazzino (/magazzino) e Gestione Ordini di visualizzare gli ordini
    ancora aperti (Evaso = 'N' su testata e righe), verificare la disponibilità del materiale
    a magazzino e passarli al picking.
    """
    global _last_orders_signature
    try:
        sql_orders = """
        SELECT 
            t.DocId,
            t.Anno,
            RTRIM(t.TpDoc) as TpDoc,
            t.YDoc as NumeroOrdine,
            t.DDoc as DataDoc,
            t.TpConto,
            t.JConto,
            RTRIM(LTRIM(ISNULL(c.RagSoc, '') + CASE WHEN c.RagSup IS NOT NULL AND RTRIM(c.RagSup) <> '' THEN ' ' + RTRIM(c.RagSup) ELSE '' END)) as Cliente,
            RTRIM(ISNULL(c.Citta, '')) as Citta,
            RTRIM(ISNULL(t.RifOrd, '')) as RiferimentoOrdine,
            ISNULL(t.ATotale, 0) as TotaleImponibile,
            ISNULL(CASE WHEN t.ATotaleIC > t.ATotale THEN t.ATotaleIC - t.ATotale ELSE 0 END, 0) as TotaleIva,
            ISNULL(CASE WHEN t.ATotaleIC > 0 THEN t.ATotaleIC ELSE t.ATotale END, 0) as TotaleDocumento,
            RTRIM(ISNULL(t.Evaso, 'N')) as Evaso,
            RTRIM(ISNULL(ag.RagSoc, '')) as AgenteNome
        FROM DocTes t WITH (NOLOCK)
        LEFT JOIN CliFor c WITH (NOLOCK) ON t.TpConto = c.TpConto AND t.JConto = c.JConto
        LEFT JOIN CliFor ag WITH (NOLOCK) ON ag.TpConto = 'F' AND ag.JConto = t.JAgente
        WHERE t.TpDoc IN ('OCL', 'ORD')
          AND (t.Evaso = 'N' OR t.Evaso IS NULL)
          AND EXISTS (
              SELECT 1 FROM DocRig r WITH (NOLOCK)
              WHERE r.DocId = t.DocId
                AND (r.Evaso = 'N' OR r.Evaso IS NULL)
                AND (ISNULL(r.Qt, 0) - ISNULL(r.QtEvaso, 0)) > 0
          )
        ORDER BY t.DDoc DESC, t.YDoc DESC
        """
        cursor.execute(sql_orders)
        col_names = [col[0] for col in cursor.description]
        plus_orders = [dict(zip(col_names, row)) for row in cursor.fetchall()]

        # Firma degli ordini aperti in Plus 2000 per evitare chiamate a Supabase se invariati
        current_sig = tuple(
            (o["DocId"], o["NumeroOrdine"], o["TotaleDocumento"], o["Evaso"]) 
            for o in plus_orders
        )

        if not force and _last_orders_signature is not None and current_sig == _last_orders_signature:
            # Nessuna variazione ordini su Plus 2000: zero chiamate HTTP verso Supabase!
            return

        print(f"\n--- ESTRAZIONE ORDINI APERTI DA PLUS 2000: Trovati {len(plus_orders)} ordini con merce da prelevare ---")
        if not plus_orders:
            # Archivia comunque gli ordini rimasti su Supabase
            for d in (syncer.get("documents", {"document_type": "in.(OCL,ORD)", "status": "in.(Aperto,In Preparazione)", "select": "number"}) or []):
                syncer.update("documents", "number", d['number'], {"status": "Evaso"})
                syncer.delete("document_lines", "document_number", d['number'])
            return

        # Recupera ordini già presenti su Supabase per evitare di sovrascrivere lo stato di picking e deduplicare ordini web
        existing_sup_docs = syncer.get("documents", {
            "document_type": "in.(OCL,ORD)",
            "select": "id,number,plus_doc_id,status,picked_by"
        })
        existing_map = {}
        for d in (existing_sup_docs or []):
            num = str(d.get("number") or "").strip()
            p_id = str(d.get("plus_doc_id") or "").strip()
            if num:
                existing_map[num] = d
            if p_id:
                existing_map[p_id] = d
                # Estrae ID numerico Plus (es. "OCL 1342/2026 (ID:536939)" o "PLUS-ID:536939")
                m = re.search(r'(?:ID:|PLUS-ID:)(\d+)', p_id)
                if m:
                    existing_map[f"ID:{m.group(1)}"] = d
                    existing_map[f"PLUS-ID:{m.group(1)}"] = d
                # Estrae identificativo Plus (es. "OCL 1342/2026")
                m_txt = re.search(r'([A-Za-z0-9_-]+\s+\d+/\d+)', p_id)
                if m_txt:
                    existing_map[m_txt.group(1)] = d

        docs_batch = []
        lines_batch = []
        processed_doc_numbers = []
        products_from_orders = {}
        customers_from_orders = {}

        for ord_info in plus_orders:
            doc_id = ord_info["DocId"]
            y_doc = ord_info["NumeroOrdine"]
            anno = ord_info["Anno"]
            tp_doc = ord_info["TpDoc"] or "OCL"
            doc_id_key = f"PLUS-ID:{doc_id}"
            default_doc_number = f"ORD-{y_doc}/{anno}"
            rif_ord = str(ord_info.get("RiferimentoOrdine") or "").strip()

            # 1. Ricerca ordine corrispondente già presente su Supabase
            existing = (
                (existing_map.get(rif_ord) if rif_ord else None)
                or existing_map.get(doc_id_key)
                or existing_map.get(f"ID:{doc_id}")
                or existing_map.get(f"{tp_doc} {y_doc}/{anno}")
                or existing_map.get(default_doc_number)
            )

            # Se l'ordine proviene dal web/B2B (es. OCL-B2B-2026-1318), conserviamo il numero web per evitare doppioni!
            if existing and existing.get("number"):
                doc_number = existing["number"]
                # Se era stato erroneamente inserito in precedenza un record separato ORD-{y_doc}/{anno}:
                if doc_number != default_doc_number and default_doc_number in existing_map:
                    print(f"🧹 [Deduplica] Rilevato doppione {default_doc_number} per ordine web {doc_number}: rimozione da Supabase...")
                    try:
                        syncer.delete("document_lines", "document_number", default_doc_number)
                        syncer.delete("documents", "number", default_doc_number)
                        existing_map.pop(default_doc_number, None)
                    except Exception as e_del:
                        print(f"  [Avviso rimozione doppione]: {e_del}")
            else:
                doc_number = default_doc_number

            # Estrai righe dell'ordine con quantità da prelevare (filtrando esplicitamente r.Evaso = 'N')
            sql_lines = """
            SELECT 
                r.DocId,
                r.Riga,
                r.CaId,
                RTRIM(a.Ca) as CodiceArticolo,
                RTRIM(a.DesArt + CASE WHEN a.DesSup IS NOT NULL AND RTRIM(a.DesSup) <> '' THEN ' ' + RTRIM(a.DesSup) ELSE '' END) as Descrizione,
                RTRIM(ISNULL(a.JUbiArt, '')) as Ubicazione,
                RTRIM(ISNULL(a.Um, 'NR')) as Um,
                ISNULL(r.Qt, 0) as QuantitaOrdinata,
                ISNULL(r.QtEvaso, 0) as QuantitaEvasa,
                (ISNULL(r.Qt, 0) - ISNULL(r.QtEvaso, 0)) as QuantitaDaPrelevare,
                RTRIM(ISNULL(r.Evaso, 'N')) as EvasoRiga,
                ISNULL(r.PzNetto, 0) as PrezzoUnitario,
                ISNULL(r.ATotale, 0) as TotaleRiga,
                RTRIM(ISNULL(a.Marca, '')) as Marca,
                (SELECT TOP 1 RTRIM(LTRIM(ac.CaCod)) FROM ArticoliCodici ac WITH (NOLOCK) WHERE ac.CaId = a.CaId ORDER BY ac.Riga) as Barcode
            FROM DocRig r WITH (NOLOCK)
            JOIN Articoli a WITH (NOLOCK) ON r.CaId = a.CaId
            WHERE r.DocId = ?
              AND (r.Evaso = 'N' OR r.Evaso IS NULL)
              AND (ISNULL(r.Qt, 0) - ISNULL(r.QtEvaso, 0)) > 0
              AND RTRIM(a.Ca) NOT IN ('C', 'CI')
              AND ISNULL(r.CaId, 0) > 0
            ORDER BY r.Riga
            """
            cursor.execute(sql_lines, (doc_id,))
            col_lines = [col[0] for col in cursor.description]
            order_lines = [dict(zip(col_lines, row)) for row in cursor.fetchall()]

            # Se l'ordine non ha alcuna riga ancora da prelevare, saltalo!
            if not order_lines:
                continue

            processed_doc_numbers.append(doc_number)

            # Controlla se esiste già su Supabase
            existing = existing_map.get(doc_id_key) or existing_map.get(doc_number)
            current_status = existing.get("status") if existing else "Aperto"
            # Se è già in preparazione o preparato, non resettarlo ad Aperto!
            if current_status not in ["In Preparazione", "Preparato", "Spedito"]:
                current_status = "Aperto"

            d_doc = str(ord_info["DataDoc"] or "")
            d_fmt = f"{d_doc[0:4]}-{d_doc[4:6]}-{d_doc[6:8]}" if len(d_doc) == 8 else datetime.date.today().isoformat()

            raw_cust_code = str(ord_info["JConto"] or "").strip()
            cust_code = raw_cust_code if raw_cust_code and raw_cust_code != "0" else None

            # Censimento preventivo del cliente per soddisfare il vincolo FK (documents_customer_code_fkey)
            if cust_code and cust_code not in customers_from_orders:
                customers_from_orders[cust_code] = {
                    "code": cust_code,
                    "name": ord_info["Cliente"] or f"Cliente {cust_code}",
                    "city": ord_info["Citta"] or "",
                    "country": "Italia",
                    "sdi_code": "0000000",
                    "payment_method": "BB30DF"
                }

            doc_payload = {
                "document_type": tp_doc,
                "number": doc_number,
                "document_date": d_fmt,
                "customer_code": cust_code,
                "customer_name": ord_info["Cliente"] or "Cliente non specificato",
                "agent_name": ord_info["AgenteNome"] or "",
                "status": current_status,
                "subtotal": float(ord_info["TotaleImponibile"] or 0),
                "vat_total": float(ord_info["TotaleIva"] or 0),
                "total": float(ord_info["TotaleDocumento"] or 0),
                "destination_address": ord_info["Citta"] or "",
                "notes": ord_info["RiferimentoOrdine"] or "",
                "plus_doc_id": f"{tp_doc} {y_doc}/{anno} (ID:{doc_id})"
            }
            docs_batch.append(doc_payload)

            for l in order_lines:
                raw_code = (l["CodiceArticolo"] or "").strip()
                p_code = raw_code if raw_code else None

                # Registra l'articolo per l'inserimento in products
                if p_code and p_code not in products_from_orders:
                    products_from_orders[p_code] = {
                        "code": p_code,
                        "caid": str(l.get("CaId") or ""),
                        "description": l.get("Descrizione") or p_code,
                        "brand": l.get("Marca") or "Climawell",
                        "um": l.get("Um") or "PZ",
                        "price": float(l.get("PrezzoUnitario") or 0),
                        "primary_location": l.get("Ubicazione") or "",
                        "barcode": l.get("Barcode") or None,
                        "active": True
                    }

                lines_batch.append({
                    "document_number": doc_number,
                    "line_number": int(l["Riga"]),
                    "product_code": p_code,
                    "description": l["Descrizione"],
                    "brand": l["Marca"] or "Climawell",
                    "location": l["Ubicazione"] or "Magazzino",
                    "um": l["Um"] or "PZ",
                    "quantity": float(l["QuantitaDaPrelevare"]),
                    "net_price": float(l["PrezzoUnitario"] or 0),
                    "total": float(l["TotaleRiga"] or 0),
                    "barcode_scanned": l["Barcode"] or None
                })

        # 1. Assicura che tutti i clienti presenti negli ordini aperti esistano nella tabella customers di Supabase (evita FK error 23503)
        if customers_from_orders:
            c_list = list(customers_from_orders.values())
            for i in range(0, len(c_list), 200):
                try:
                    syncer.upsert_batch("customers", c_list[i:i + 200], on_conflict="code", resolution="ignore-duplicates")
                except Exception as ex_cust:
                    print(f"  [Avviso censimento clienti ordini]: {ex_cust}")
            print(f"👥 Verificati/censiti {len(c_list)} clienti associati agli ordini aperti.")

        # 2. Carica testate documenti su Supabase a lotti di 100 con fallback sicuro
        if docs_batch:
            for i in range(0, len(docs_batch), 100):
                chunk_docs = docs_batch[i:i + 100]
                try:
                    syncer.upsert_batch("documents", chunk_docs, on_conflict="number")
                except Exception as ex_doc:
                    print(f"⚠️ Errore salvataggio blocco documenti: {ex_doc}. Recupero documento per documento...")
                    for doc_item in chunk_docs:
                        try:
                            syncer.upsert_batch("documents", [doc_item], on_conflict="number")
                        except Exception:
                            # Se fallisce per vincolo cliente, imposta customer_code = None per non bloccare l'ordine
                            doc_safe = dict(doc_item)
                            doc_safe["customer_code"] = None
                            try:
                                syncer.upsert_batch("documents", [doc_safe], on_conflict="number")
                            except Exception as e_d_fail:
                                print(f"  ❌ Errore definitivo ordine {doc_item.get('number')}: {e_d_fail}")
            print(f"✅ Sincronizzati {len(docs_batch)} ordini clienti su Supabase.")

        # 2. Assicura che tutti gli articoli presenti negli ordini aperti esistano nella tabella products di Supabase
        # (usando resolution="ignore-duplicates" per inserire solo quelli mancanti senza toccare i prodotti già a catalogo)
        if products_from_orders:
            p_list = list(products_from_orders.values())
            for i in range(0, len(p_list), 200):
                try:
                    syncer.upsert_batch("products", p_list[i:i + 200], on_conflict="code", resolution="ignore-duplicates")
                except Exception as ex_prod:
                    print(f"  [Avviso censimento prodotti ordini]: {ex_prod}")
            print(f"📦 Verificati/censiti {len(p_list)} articoli associati agli ordini aperti.")

        # 3. Carica righe documento su Supabase a lotti di 200
        if lines_batch:
            # Per evitare righe duplicate o obsolete, puliamo con URL-encoding le righe dei documenti aggiornati
            for num in processed_doc_numbers:
                try:
                    syncer.delete("document_lines", "document_number", num)
                except Exception:
                    pass

            for i in range(0, len(lines_batch), 200):
                chunk = lines_batch[i:i + 200]
                try:
                    syncer.upsert_batch("document_lines", chunk)
                except Exception as ex_chunk:
                    print(f"⚠️ Inserimento blocco righe ({len(chunk)} righe) segnala: {ex_chunk}. Recupero riga per riga...")
                    for line_item in chunk:
                        try:
                            syncer.upsert_batch("document_lines", [line_item])
                        except Exception:
                            # Se una riga fallisce il vincolo FK, inseriscila con product_code nullo per non perderla
                            line_safe = dict(line_item)
                            line_safe["product_code"] = None
                            try:
                                syncer.upsert_batch("document_lines", [line_safe])
                            except Exception as e_fail:
                                print(f"  ❌ Errore inserimento riga {line_item.get('document_number')}: {e_fail}")

            print(f"✅ Sincronizzate {len(lines_batch)} righe articolo per picking magazzino.")

        # 4. Archivia automaticamente su Supabase come 'Evaso' gli ordini completati / già evasi su Plus 2000
        active_set = set(processed_doc_numbers)
        evasi_archiviati = 0
        for d in (existing_sup_docs or []):
            d_num = d.get("number")
            d_status = d.get("status")
            if d_num and d_num.startswith("ORD-") and d_num not in active_set:
                if d_status in ["Aperto", "In Attesa", "In Preparazione"]:
                    try:
                        syncer.update("documents", "number", d_num, {"status": "Evaso"})
                        syncer.delete("document_lines", "document_number", d_num)
                        evasi_archiviati += 1
                    except Exception:
                        pass
        if evasi_archiviati > 0:
            print(f"🏁 Archiviati come 'Evaso' su Supabase {evasi_archiviati} ordini già completati su Plus 2000.")

        _last_orders_signature = current_sig

    except Exception as e:
        print(f"⚠️ Errore durante la sincronizzazione ordini aperti da Plus: {e}")
        traceback.print_exc()


_last_synced_doc_id = None

def sync_incremental_stock_from_plus(cursor, syncer):
    """
    Rileva in tempo reale (ogni 15 secondi) qualsiasi documento emesso o modificato
    su Plus 2000 (DDT, bolle, fatture accompagnatorie, carichi merci) che altera le giacenze,
    e aggiorna all'istante le scorte dei relativi articoli su Supabase.
    """
    global _last_synced_doc_id
    try:
        if _last_synced_doc_id is None:
            # Al primo avvio: salva l'ultimo DocId corrente e controlla i movimenti odierni
            cursor.execute("SELECT ISNULL(MAX(DocId), 0) FROM DocTes WITH (NOLOCK)")
            row = cursor.fetchone()
            _last_synced_doc_id = int(row[0]) if row and row[0] else 0

            d_today = int(datetime.date.today().strftime("%Y%m%d"))
            cursor.execute("""
                SELECT DISTINCT r.CaId, RTRIM(a.Ca) as CodiceArticolo
                FROM DocRig r WITH (NOLOCK)
                JOIN Articoli a WITH (NOLOCK) ON r.CaId = a.CaId
                JOIN DocTes t WITH (NOLOCK) ON r.DocId = t.DocId
                WHERE (t.DDoc = ? OR t.DMod = ?) AND ISNULL(r.CaId, 0) > 0
            """, (d_today, d_today))
            changed_items = cursor.fetchall()
        else:
            # Cicli successivi: verifica se ci sono nuovi DocId registrati su Plus 2000
            cursor.execute("SELECT ISNULL(MAX(DocId), 0) FROM DocTes WITH (NOLOCK)")
            row = cursor.fetchone()
            current_max_id = int(row[0]) if row and row[0] else _last_synced_doc_id

            if current_max_id <= _last_synced_doc_id:
                return

            cursor.execute("""
                SELECT DISTINCT r.CaId, RTRIM(a.Ca) as CodiceArticolo
                FROM DocRig r WITH (NOLOCK)
                JOIN Articoli a WITH (NOLOCK) ON r.CaId = a.CaId
                WHERE r.DocId > ? AND ISNULL(r.CaId, 0) > 0
            """, (_last_synced_doc_id,))
            changed_items = cursor.fetchall()
            _last_synced_doc_id = current_max_id

        if not changed_items:
            return

        ca_ids = [row[0] for row in changed_items if row[0]]
        if not ca_ids:
            return

        # Estrae le giacenze aggiornate da ArticoliContGen per gli articoli movimentati
        for i in range(0, len(ca_ids), 100):
            chunk_ids = ca_ids[i:i + 100]
            placeholders = ",".join(["?"] * len(chunk_ids))
            sql_stock = f"""
            SELECT 
                a.CaId,
                RTRIM(a.Ca) as CodiceArticolo,
                ISNULL(g.TotEsi, 0) as Giacenza,
                ISNULL(g.TotDisp, 0) as Disponibilita,
                ISNULL(g.TotImp, 0) as Impegnato
            FROM Articoli a WITH (NOLOCK)
            LEFT JOIN (
                SELECT CaId, 
                       SUM(QtEsi) as TotEsi, 
                       SUM(QtDisp) as TotDisp, 
                       SUM(ISNULL(QtImp, 0)) as TotImp
                FROM ArticoliContGen WITH (NOLOCK)
                WHERE CaId IN ({placeholders})
                GROUP BY CaId
            ) g ON a.CaId = g.CaId
            WHERE a.CaId IN ({placeholders})
            """
            cursor.execute(sql_stock, chunk_ids + chunk_ids)
            for art_row in cursor.fetchall():
                c_code = art_row[1]
                stock_val = float(art_row[2] or 0.0)
                disp_val = float(art_row[3] or 0.0)
                imp_val = float(art_row[4] or 0.0)
                try:
                    syncer.update("products", "code", c_code, {
                        "stock_qty": round(stock_val, 2),
                        "available_qty": round(disp_val, 2),
                        "committed_qty": round(imp_val, 2),
                        "plus_sync_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                    })
                    print(f"  ⚡ [Realtime DDT/Movimento Plus] {c_code} ➔ Giacenza aggiornata: {stock_val} PZ (Disp: {disp_val}, Imp: {imp_val})")
                except Exception as ex_up:
                    pass

    except Exception as e:
        print(f"⚠️ [Avviso sync giacenze realtime]: {e}")


def main():
    print("=" * 65)
    print("  CLIMAWELL - SINCRONIZZATORE PLUS 2000 ➔ SUPABASE")
    print("=" * 65)

    cfg = load_config()
    sup_cfg = cfg.get("supabase", {})

    # Permette passaggio da riga di comando
    url = None
    key = None
    for i, arg in enumerate(sys.argv):
        if arg == "--url" and i + 1 < len(sys.argv):
            url = sys.argv[i + 1]
        elif arg == "--key" and i + 1 < len(sys.argv):
            key = sys.argv[i + 1]

    url = url or os.environ.get("SUPABASE_URL") or sup_cfg.get("url")
    key = key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or sup_cfg.get("service_role_key") or sup_cfg.get("anon_key")

    if not url or not key:
        print("\n❌ ERRORE: Credenziali Supabase non impostate!")
        print("Compila 'supabase.url' e 'supabase.service_role_key' in connettore-plus2000/config.json")
        print("oppure passa gli argomenti: python sync_plus_to_supabase.py --url <URL> --key <KEY>")
        sys.exit(1)

    print(f"Supabase Endpoint: {url}")
    print(f"SQL Server Host:   {cfg.get('sql_server', {}).get('server')} -> {cfg.get('sql_server', {}).get('database')}")

    syncer = SupabaseSyncer(url, key)

    conn = get_sql_conn(cfg.get("sql_server", {}))
    cursor = conn.cursor()

    try:
        # 1. Scarica nuove offerte e ordini da Supabase verso Plus 2000
        sync_documents_from_supabase_to_plus(cursor, syncer, conn)

        # 2. Aggiorna prima agenti e clienti (impiega solo 2 secondi)
        sync_agents(cursor, syncer)
        sync_customers(cursor, syncer)

        # 3. Sincronizza ordini clienti aperti da Plus 2000 (Evaso = 'N') verso Supabase
        sync_open_orders_from_plus_to_supabase(cursor, syncer)

        # 4. Aggiorna catalogo prodotti (se non richiesto solo sync clienti)
        if "--only-customers" not in sys.argv and "--no-products" not in sys.argv:
            sync_products(cursor, syncer)
        print("\n🎉 Sincronizzazione completata con successo in tempo reale!")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()

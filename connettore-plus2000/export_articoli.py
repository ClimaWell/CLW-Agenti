import json
import os
import sys
import datetime
import requests
import pyodbc
from connettore import GoogleSheetsClient, load_config, BASE_DIR

# Import modulo indicizzazione e ricerca IdroLAB / DomusPartes
DOMUS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "connettore-domuspartes"))
if DOMUS_DIR not in sys.path:
    sys.path.append(DOMUS_DIR)
try:
    from idrolab_indexer import cerca_articolo_idrolab, esegui_indicizzazione
except Exception as e:
    print(f"  [AVVISO]: Impossibile caricare modulo IdroLAB: {e}")
    cerca_articolo_idrolab = None
    esegui_indicizzazione = None

def run_export_articoli(all_catalog=False):

    # Verifica se i file listini in connettore-domuspartes/listini richiedono indicizzazione
    if esegui_indicizzazione:
        db_path = os.path.join(DOMUS_DIR, "idrolab_index.db")
        listini_folder = os.path.join(DOMUS_DIR, "listini")
        needs_indexing = "--reindex" in sys.argv
        if not needs_indexing and os.path.exists(listini_folder):
            db_mtime = os.path.getmtime(db_path) if os.path.exists(db_path) else 0
            for fn in os.listdir(listini_folder):
                if fn.lower().endswith(".csv") or fn.lower().endswith(".zip"):
                    fp = os.path.join(listini_folder, fn)
                    if os.path.getmtime(fp) > db_mtime:
                        needs_indexing = True
                        break
        if needs_indexing:
            print("Aggiornamento indice listini IdroLAB / DomusPartes in corso...")
            esegui_indicizzazione()

    cfg = load_config()
    sa_file = cfg.get("google_sheets", {}).get("service_account_file", "service_account.json")
    client = GoogleSheetsClient(sa_file)
    
    # ID del foglio Google Articoli indicato dall'utente
    SPREADSHEET_ID = "1g6zrWK_zZJZ82kdoNgda9KuoemYlSs0XGRRfJvoOvUk"
    TAB_NAME = "q_listino_prezzi_catalogo"
    
    if "--all" in sys.argv:
        all_catalog = True

    print("=== AVVIO ESPORTAZIONE CATALOGO ARTICOLI DA PLUS 2000 ===")
    print(f"Spreadsheet ID: {SPREADSHEET_ID}")
    print(f"Tabella target: {TAB_NAME}")
    if all_catalog:
        print("Filtro: TUTTO IL CATALOGO (Nessun filtro giacenza/movimenti)")
    else:
        print("Filtro: Articoli con Giacenza > 0 oppure movimentati di recente (2025-2026)")
        
    token = client._get_access_token()
    auth_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def col_letter(n: int) -> str:
        result = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            result = chr(65 + remainder) + result
        return result

    # 1. Recupero preventivo degli 'URL-immagine' e flag 'Aggiorna_in_Plus' esistenti nel foglio Google
    existing_images = {}
    existing_aggiorna = {}
    try:
        existing_rows = client.read_range(SPREADSHEET_ID, f"'{TAB_NAME}'!A1:Z50000", unformatted=True)

        if existing_rows and len(existing_rows) > 1:
            header = [str(c).strip().lower() for c in existing_rows[0]]
            caid_col = -1
            cod_col = -1
            url_col = -1
            aggiorna_col = -1
            for idx, h in enumerate(header):
                if h == "caid":
                    caid_col = idx
                elif h in ["codicearticolo", "ca", "codice"]:
                    cod_col = idx
                elif h == "url-immagine" or (url_col == -1 and ("url" in h or "immag" in h)):
                    url_col = idx
                elif "aggiorna" in h:
                    aggiorna_col = idx
                    
            for row in existing_rows[1:]:
                cid = str(row[caid_col]).strip() if caid_col != -1 and len(row) > caid_col else ""
                cod = str(row[cod_col]).strip() if cod_col != -1 and len(row) > cod_col else ""
                if url_col != -1 and len(row) > url_col:
                    img_url = str(row[url_col]).strip()
                    if img_url and img_url.startswith("http"):
                        if cid: existing_images[cid] = img_url
                        if cod: existing_images[cod] = img_url
                if aggiorna_col != -1 and len(row) > aggiorna_col:
                    agg_val = str(row[aggiorna_col]).strip()
                    if agg_val:
                        if cid: existing_aggiorna[cid] = agg_val
                        if cod: existing_aggiorna[cod] = agg_val
            print(f"  [OK] Preservati {len(existing_images)} URL immagini e {len(existing_aggiorna)} flag aggiornamento da Drive.")
    except Exception as e:
        print(f"  [AVVISO]: Impossibile leggere dati esistenti ({e}), si procede con foglio pulito.")

    # 2. Connessione a SQL Server Plus 2000
    sql_cfg = cfg["sql_server"]
    dsn = sql_cfg.get("dsn", "climawell")
    print(f"Connessione a SQL Server (DSN={dsn})...")
    conn = pyodbc.connect(f"DSN={dsn};", autocommit=True, timeout=15)
    cursor = conn.cursor()
    
    where_clause = "a.Blocco = 0"
    if not all_catalog:
        img_caids = [k for k in existing_images.keys() if k.isdigit()]
        if img_caids:
            caids_in = ",".join(img_caids[:1000])
            where_clause += f" AND (g.TotEsi > 0 OR m.CaId IS NOT NULL OR a.CaId IN ({caids_in}))"
        else:
            where_clause += " AND (g.TotEsi > 0 OR m.CaId IS NOT NULL)"

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
            FROM ListiniPrezzi
            WHERE JListino = 'VEN1'
        ),
        Giacenze AS (
            SELECT CaId, SUM(QtEsi) as TotEsi, SUM(QtDisp) as TotDisp
            FROM ArticoliContGen
            GROUP BY CaId
        ),
        MovimentiRecenti AS (
            SELECT DISTINCT r.CaId
            FROM DocRig r
            JOIN DocTes t ON r.DocId = t.DocId
            WHERE t.Anno >= 2025
        )
        SELECT 
            a.CaId,
            RTRIM(LTRIM(a.Ca)) as CodiceArticolo,
            RTRIM(LTRIM(a.DesArt + CASE WHEN a.DesSup IS NOT NULL AND RTRIM(a.DesSup) <> '' THEN ' ' + RTRIM(a.DesSup) ELSE '' END)) as Descrizione,
            RTRIM(LTRIM(ISNULL(a.Marca, ''))) as Marca,
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
            RTRIM(LTRIM(ISNULL(a.CaProd, ''))) as CaProd,
            (SELECT TOP 1 RTRIM(LTRIM(ac.CaCod)) FROM ArticoliCodici ac WHERE ac.CaId = a.CaId ORDER BY ac.Riga) as Ean
        FROM Articoli a
        LEFT JOIN PrezziVen1 p ON a.CaId = p.CaId AND p.rn = 1
        LEFT JOIN Giacenze g ON a.CaId = g.CaId
        LEFT JOIN MovimentiRecenti m ON a.CaId = m.CaId
        LEFT JOIN TabDes t_set ON t_set.TpTab = 'SET' AND t_set.JTab = a.JSettore
        LEFT JOIN MacroFamiglie t_mac ON t_mac.JSettore = a.JSettore AND t_mac.JMacroFamiglia = a.JMacroFamiglia
        LEFT JOIN Famiglie t_fam ON t_fam.JSettore = a.JSettore AND t_fam.JMacroFamiglia = a.JMacroFamiglia AND t_fam.JFamiglia = a.JFamiglia
        WHERE {where_clause}
        ORDER BY g.TotEsi DESC, CodiceArticolo
    """
    
    print("Esecuzione query articoli su SQL Server (listino VEN1 + giacenze + descrizioni TABDES + Disegno)...")
    cursor.execute(query)
    raw_rows = cursor.fetchall()
    conn.close()
    print(f"Estratti {len(raw_rows)} articoli attivi da Plus 2000.")
    
    # 3. Preparazione righe con intestazioni e composizione automatica URL-immagine DomusPartes
    headers = [
        "CaId",
        "CodiceArticolo",
        "Descrizione",
        "Marca",
        "Settore",
        "Macrofamiglia",
        "Famiglia",
        "Jstato prodotto",
        "Ubicazione",
        "Prezzo",
        "JScontoVen",
        "Unità di Misura",
        "Giacenza (QtEsi)",
        "URL-immagine",
        "Settore_Plus",
        "Macrofamiglia_Plus",
        "Famiglia_Plus",
        "Disegno_Plus",
        "Settore_Domus",
        "Macrofamiglia_Domus",
        "Famiglia_Domus",
        "Immagine_Domus",
        "URL_Immagine_Domus",
        "Stato_Allineamento",
        "Aggiorna_in_Plus"
    ]
    
    DOMUS_ASSET_BASE_URL = "https://www.domuspartes.it/products_images/pre/assets"

    def formatta_url_domus(marca: str, disegno: str, caprod: str) -> str:
        marca_clean = str(marca or "").strip().upper()
        if not marca_clean or marca_clean in ("0", "-", "_"):
            return ""
            
        dis_clean = str(disegno or "").strip().replace("\\", "/").strip("/")
        if dis_clean and not any(dis_clean.lower().endswith(x) for x in [".exe", ".bat", "/"]):
            nome_file = os.path.basename(dis_clean)
            if nome_file and nome_file.lower() not in ("logo.jpg", "ids", "tlc", "fog.jpg"):
                if nome_file.lower().endswith(".jpg"):
                    return f"{DOMUS_ASSET_BASE_URL}/{marca_clean}/{nome_file}.jpg"
                elif nome_file.lower().endswith(".png"):
                    return f"{DOMUS_ASSET_BASE_URL}/{marca_clean}/{nome_file}"
                else:
                    return f"{DOMUS_ASSET_BASE_URL}/{marca_clean}/{nome_file}.jpg.jpg"

        caprod_clean = str(caprod or "").strip()
        if caprod_clean and caprod_clean not in ("0", "-", "_"):
            return f"{DOMUS_ASSET_BASE_URL}/{marca_clean}/{caprod_clean}.jpg.jpg"
            
        return ""

    def clean_str(val):
        s = str(val or "").strip()
        if s in ["_", "-", ".", "/"]:
            return ""
        return s

    sheet_data = [headers]
    img_assigned_count = 0
    enriched_cat_count = 0
    
    for r in raw_rows:
        caid_str = str(r[0])
        cod_art = clean_str(r[1])
        desc_art = clean_str(r[2])
        marca_art = clean_str(r[3])
        settore_plus = clean_str(r[4])
        macro_plus = clean_str(r[5])
        fam_plus = clean_str(r[6])
        jstato = clean_str(r[7])
        ubi = clean_str(r[8])
        pz_val = float(r[9]) if r[9] is not None else 0.0
        jsconto = clean_str(r[10])
        um = clean_str(r[11]) or "NR"
        esi_val = float(r[12]) if r[12] is not None else 0.0
        disegno_plus = clean_str(r[13])
        caprod_art = clean_str(r[14])
        ean_art = clean_str(r[15]) if len(r) > 15 else ""

        settore_art = settore_plus
        macro_art = macro_plus
        fam_art = fam_plus

        settore_domus = ""
        macro_domus = ""
        fam_domus = ""
        img_domus = ""
        url_img_domus = ""

        # Recupero immagine memorizzata in precedenza o composizione da DomusPartes
        img_url = existing_images.get(caid_str) or existing_images.get(cod_art) or ""
        if not img_url:
            img_url = formatta_url_domus(marca_art, disegno_plus, caprod_art)

        # Arricchimento categorie e immagini da banca dati IdroLAB / DomusPartes
        idro_data = None
        if cerca_articolo_idrolab:
            idro_data = cerca_articolo_idrolab(cod_art, caprod=caprod_art, ean=ean_art)
            if idro_data:
                settore_domus = clean_str(idro_data.get("settore"))
                macro_domus = clean_str(idro_data.get("macrofamiglia"))
                fam_domus = clean_str(idro_data.get("famiglia"))
                img_domus = clean_str(idro_data.get("immagine")) or clean_str(idro_data.get("disegno_tecnico"))
                url_img_domus = clean_str(idro_data.get("url_immagine"))

                did_enrich = False
                # Se Settore è vuoto o è un codice numerico non descritto o "non classificato"
                if (not settore_art or settore_art.isdigit() or settore_art.lower() in ("0", "non classificato")) and settore_domus and settore_domus.lower() != "non classificato":
                    settore_art = settore_domus
                    did_enrich = True
                # Se Macrofamiglia è vuota o è un codice numerico
                if (not macro_art or macro_art.isdigit() or macro_art.lower() in ("0", "non classificato")) and macro_domus and macro_domus.lower() != "non classificato":
                    macro_art = macro_domus
                    did_enrich = True
                # Se Famiglia è vuota o è un codice numerico
                if (not fam_art or fam_art.isdigit() or fam_art.lower() in ("0", "non classificato")) and fam_domus and fam_domus.lower() != "non classificato":
                    fam_art = fam_domus
                    did_enrich = True
                # Immagine ricavata da Disegno Tecnico / Immagine di IdroLAB
                if url_img_domus:
                    if not img_url or "domuspartes.it" in img_url:
                        img_url = url_img_domus
                if did_enrich:
                    enriched_cat_count += 1
            
        if img_url:
            img_assigned_count += 1

        # Calcolo Stato Allineamento
        diffs = []
        if not idro_data:
            stato_allineamento = "NON_IN_LISTINI_DOMUS"
        else:
            cat_plus_vuota = not settore_plus or settore_plus.isdigit() or settore_plus.lower() in ("0", "non classificato")
            if cat_plus_vuota and settore_domus and settore_domus.lower() != "non classificato":
                diffs.append("CATEGORIE_MANCANTI_IN_PLUS")
            elif settore_plus and settore_domus and settore_plus.lower() != settore_domus.lower():
                diffs.append("CATEGORIE_DIFFERENTI")

            if not disegno_plus and (img_domus or url_img_domus):
                diffs.append("IMMAGINE_MANCANTE_IN_PLUS")
            elif disegno_plus and img_domus and disegno_plus.lower() != img_domus.lower():
                diffs.append("IMMAGINE_DIFFERENTE")

            if not diffs:
                stato_allineamento = "ALLINEATO"
            else:
                stato_allineamento = " | ".join(diffs)

        # Flag Aggiorna_in_Plus preservato se già immesso da utente, altrimenti vuoto
        aggiorna_flag = existing_aggiorna.get(caid_str) or existing_aggiorna.get(cod_art) or ""
            
        pz_val = float(r[9]) if r[9] is not None else 0.0
        esi_val = float(r[12]) if r[12] is not None else 0.0
        
        # Inserimento numerico per evitare che Google Sheets interpreti stringhe come orari
        pz_num = round(pz_val, 4) if pz_val > 0 else 0
        esi_num = round(esi_val, 2) if esi_val != 0 else 0

        sheet_data.append([
            caid_str,              # CaId
            cod_art,               # CodiceArticolo
            desc_art,              # Descrizione
            marca_art,             # Marca
            settore_art,           # Settore (attivo catalogo/OrderSender)
            macro_art,             # Macrofamiglia (attivo catalogo/OrderSender)
            fam_art,               # Famiglia (attivo catalogo/OrderSender)
            jstato,                # Jstato prodotto
            ubi,                   # Ubicazione
            pz_num,                # Prezzo (VEN1 numero float)
            jsconto,               # JScontoVen (famiglia sconto vendita)
            um,                    # Unità di Misura
            esi_num,               # Giacenza (QtEsi numero float)
            img_url,               # URL-immagine (attivo catalogo/OrderSender)
            settore_plus,          # Settore_Plus
            macro_plus,            # Macrofamiglia_Plus
            fam_plus,              # Famiglia_Plus
            disegno_plus,          # Disegno_Plus
            settore_domus,         # Settore_Domus
            macro_domus,           # Macrofamiglia_Domus
            fam_domus,             # Famiglia_Domus
            img_domus,             # Immagine_Domus
            url_img_domus,         # URL_Immagine_Domus
            stato_allineamento,    # Stato_Allineamento
            aggiorna_flag          # Aggiorna_in_Plus
        ])
        
    print(f"Totale articoli con URL immagine assegnato: {img_assigned_count} su {len(raw_rows)}.")
    print(f"Totale articoli arricchiti con categorie IdroLAB/DomusPartes: {enriched_cat_count}.")
    total_rows = len(sheet_data)

    # 4. Verifica o adeguamento dimensione foglio Google
    meta_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}"
    meta_res = requests.get(meta_url, headers=auth_headers, timeout=15).json()
    sheet_id_num = None
    for s in meta_res.get("sheets", []):
        if s["properties"]["title"] == TAB_NAME:
            sheet_id_num = s["properties"]["sheetId"]
            break

    if sheet_id_num is not None:
        target_rows = max(total_rows + 50, 1000)
        print(f"Adeguamento dimensione griglia foglio a {target_rows} righe e {len(headers)} colonne...")
        resize_req = {
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id_num,
                            "gridProperties": {
                                "rowCount": target_rows,
                                "columnCount": max(len(headers) + 2, 28)
                            }
                        },
                        "fields": "gridProperties.rowCount,gridProperties.columnCount"
                    }
                }
            ]
        }
        requests.post(f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}:batchUpdate", headers=auth_headers, json=resize_req, timeout=15)

    # 5. Pulizia foglio esistente
    last_col = col_letter(len(headers))
    print(f"Svuotamento dati precedenti nel foglio '{TAB_NAME}' (A1:{last_col})...")
    clear_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/'{TAB_NAME}'!A1:{last_col}:clear"
    requests.post(clear_url, headers=auth_headers, timeout=15)

    # 6. Scrittura nuovi dati in blocchi (batch da 2500 righe)
    BATCH_SIZE = 2500
    print(f"Caricamento di {total_rows} righe su Google Sheets in batch...")
    
    for start_idx in range(0, total_rows, BATCH_SIZE):
        end_idx = min(start_idx + BATCH_SIZE, total_rows)
        chunk = sheet_data[start_idx:end_idx]
        start_row_num = start_idx + 1
        end_row_num = end_idx
        
        range_str = f"'{TAB_NAME}'!A{start_row_num}:{last_col}{end_row_num}"
        update_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{range_str}?valueInputOption=USER_ENTERED"
        res = requests.put(update_url, headers=auth_headers, json={"values": chunk}, timeout=30)
        if res.status_code != 200:
            raise RuntimeError(f"Errore caricamento righe {start_row_num}-{end_row_num}: {res.text}")
        print(f"  -> Caricate righe {start_row_num} - {end_row_num} di {total_rows}")

    # 7. Formattazione estetica (colori di sezione distinti, freeze riga 1, numeri formattati)
    if sheet_id_num is not None:
        print("Applicazione formattazione estetica avanzata...")
        format_req = {
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id_num,
                            "gridProperties": {
                                "frozenRowCount": 1
                            }
                        },
                        "fields": "gridProperties.frozenRowCount"
                    }
                },
                # 1. Sezione Base / Vendita (col 0-14)
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id_num,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": 14
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {"red": 0.117, "green": 0.160, "blue": 0.231},
                                "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True, "fontSize": 10},
                                "horizontalAlignment": "LEFT",
                                "verticalAlignment": "MIDDLE",
                                "wrapStrategy": "CLIP"
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
                    }
                },
                # 2. Sezione Dati Plus 2000 (col 14-18)
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id_num,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 14,
                            "endColumnIndex": 18
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {"red": 0.200, "green": 0.250, "blue": 0.330},
                                "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True, "fontSize": 10},
                                "horizontalAlignment": "LEFT",
                                "verticalAlignment": "MIDDLE",
                                "wrapStrategy": "CLIP"
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
                    }
                },
                # 3. Sezione Dati DomusPartes / IdroLAB (col 18-23)
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id_num,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 18,
                            "endColumnIndex": 23
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {"red": 0.040, "green": 0.350, "blue": 0.220},
                                "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True, "fontSize": 10},
                                "horizontalAlignment": "LEFT",
                                "verticalAlignment": "MIDDLE",
                                "wrapStrategy": "CLIP"
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
                    }
                },
                # 4. Sezione Controllo e Allineamento (col 23-25)
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id_num,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 23,
                            "endColumnIndex": 25
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {"red": 0.500, "green": 0.250, "blue": 0.050},
                                "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True, "fontSize": 10},
                                "horizontalAlignment": "LEFT",
                                "verticalAlignment": "MIDDLE",
                                "wrapStrategy": "CLIP"
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
                    }
                },
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id_num,
                            "startRowIndex": 1,
                            "endRowIndex": target_rows,
                            "startColumnIndex": 9,
                            "endColumnIndex": 10
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "numberFormat": {
                                    "type": "NUMBER",
                                    "pattern": "#,##0.00"
                                }
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat"
                    }
                },
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id_num,
                            "startRowIndex": 1,
                            "endRowIndex": target_rows,
                            "startColumnIndex": 12,
                            "endColumnIndex": 13
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "numberFormat": {
                                    "type": "NUMBER",
                                    "pattern": "#,##0.00"
                                }
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat"
                    }
                },
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": sheet_id_num,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": len(headers)
                        }
                    }
                }
            ]
        }
        batch_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}:batchUpdate"
        format_res = requests.post(batch_url, headers=auth_headers, json=format_req, timeout=15)
        if format_res.status_code == 200:
            print("  [OK] Formattazione applicata con successo!")
        else:
            print(f"  [AVVISO Formattazione]: {format_res.text}")

    print(f"\nEsportazione articoli completata con successo! {len(raw_rows)} articoli caricati su Google Drive.")

if __name__ == "__main__":
    run_export_articoli()

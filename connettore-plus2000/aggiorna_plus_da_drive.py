"""
aggiorna_plus_da_drive.py
-------------------------
Legge il foglio Google Drive 'q_listino_prezzi_catalogo' (ID: 1g6zrWK_zZJZ82kdoNgda9KuoemYlSs0XGRRfJvoOvUk)
e aggiorna le anagrafiche degli articoli su Plus 2000 (SQL Server: SRVPLUS.Climawell).

Modalita di esecuzione:
  1. Simulazione sicura (Default - nessuna modifica a SQL Server):
     python aggiorna_plus_da_drive.py --dry-run

  2. Applicazione reale delle modifiche approvate:
     python aggiorna_plus_da_drive.py --apply

  3. Filtri opzionali:
     python aggiorna_plus_da_drive.py --apply --marca ERC
     python aggiorna_plus_da_drive.py --apply --all-missing-images
"""

import os
import sys
import argparse
from datetime import datetime
import pyodbc

# Import client Google Sheets e configurazione dal connettore locale
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from connettore import GoogleSheetsClient, load_config

SPREADSHEET_ID = "1g6zrWK_zZJZ82kdoNgda9KuoemYlSs0XGRRfJvoOvUk"
TAB_NAME = "q_listino_prezzi_catalogo"

def col_letter(n: int) -> str:
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result

def main():
    parser = argparse.ArgumentParser(description="Aggiorna anagrafiche articoli in Plus 2000 dai dati di Google Drive / DomusPartes.")
    parser.add_argument("--apply", action="store_true", help="Applica realmente le modifiche su SQL Server (altrimenti esegue solo simulazione --dry-run).")
    parser.add_argument("--dry-run", action="store_true", help="Esegue simulazione senza modificare il database SQL Server.")
    parser.add_argument("--marca", type=str, default="", help="Filtra solo per una specifica marca (es. ERC, PAF, DKN, IRS).")
    parser.add_argument("--all-missing-images", action="store_true", help="Aggiorna tutti gli articoli senza immagine in Plus che hanno un'immagine disponibile in DomusPartes, anche senza flag esplicito 'SI'.")
    parser.add_argument("--max", type=int, default=0, help="Limite massimo di articoli da aggiornare (0 = nessun limite).")
    args = parser.parse_args()

    is_dry_run = not args.apply or args.dry_run

    print("\n" + "=" * 70)
    print("  AGGIORNAMENTO ANAGRAFICHE PLUS 2000 DA GOOGLE DRIVE")
    print("=" * 70)
    if is_dry_run:
        print(" [MODALITÀ SIMULAZIONE - DRY RUN]: Nessuna modifica verrà scritta su SQL Server.")
        print(" Per applicare le modifiche reali usa il parametro: --apply\n")
    else:
        print(" [ATTENZIONE - MODALITÀ APPLICAZIONE REALE]: Le modifiche verranno scritte su SQL Server!\n")

    cfg = load_config()
    sa_file = cfg.get("google_sheets", {}).get("service_account_file", "service_account.json")
    client = GoogleSheetsClient(sa_file)

    # 1. Lettura dati dal foglio Google
    print(f"Lettura foglio Google '{TAB_NAME}' (ID: {SPREADSHEET_ID})...")
    rows = client.read_range(SPREADSHEET_ID, f"'{TAB_NAME}'!A1:Z60000", unformatted=True)
    if not rows or len(rows) < 2:
        print("[ERRORE]: Nessun dato trovato nel foglio Google Drive.")
        return

    header = [str(c).strip().lower() for c in rows[0]]
    col_map = {}
    for idx, h in enumerate(header):
        col_map[h] = idx

    def get_col(names):
        for n in names:
            if n in col_map:
                return col_map[n]
        return -1

    idx_caid = get_col(["caid"])
    idx_cod = get_col(["codicearticolo", "ca", "codice"])
    idx_marca = get_col(["marca"])
    idx_dis_plus = get_col(["disegno_plus", "disegno"])
    idx_img_domus = get_col(["immagine_domus"])
    idx_url_domus = get_col(["url_immagine_domus"])
    idx_aggiorna = get_col(["aggiorna_in_plus", "aggiorna"])

    if idx_caid == -1 or idx_cod == -1:
        print("[ERRORE]: Colonne CaId o CodiceArticolo non trovate nel foglio Google.")
        return

    # 2. Selezione articoli da aggiornare
    da_aggiornare = []
    
    for row_idx, r in enumerate(rows[1:], start=2):
        caid_val = str(r[idx_caid]).strip() if idx_caid != -1 and len(r) > idx_caid else ""
        cod_val = str(r[idx_cod]).strip() if idx_cod != -1 and len(r) > idx_cod else ""
        marca_val = str(r[idx_marca]).strip() if idx_marca != -1 and len(r) > idx_marca else ""
        dis_plus = str(r[idx_dis_plus]).strip() if idx_dis_plus != -1 and len(r) > idx_dis_plus else ""
        img_domus = str(r[idx_img_domus]).strip() if idx_img_domus != -1 and len(r) > idx_img_domus else ""
        url_domus = str(r[idx_url_domus]).strip() if idx_url_domus != -1 and len(r) > idx_url_domus else ""
        flag_agg = str(r[idx_aggiorna]).strip().upper() if idx_aggiorna != -1 and len(r) > idx_aggiorna else ""

        if not caid_val or not caid_val.isdigit():
            continue

        if args.marca and marca_val.upper() != args.marca.upper():
            continue

        # Criterio di approvazione:
        # Flag 'SI', 'SÌ', 'YES', '1', 'OK' OPPURE opzione --all-missing-images
        approvato = flag_agg in ("SI", "SÌ", "YES", "1", "OK")
        if not approvato and args.all_missing_images:
            if not dis_plus and (img_domus or url_domus):
                approvato = True

        if not approvato:
            continue

        # Nome file da scrivere nel campo Disegno di Plus
        target_disegno = img_domus
        if not target_disegno and url_domus:
            target_disegno = os.path.basename(url_domus)

        if not target_disegno:
            continue

        # Campo Disegno su SQL Server ha dimensione varchar(50)
        if len(target_disegno) > 50:
            root, ext = os.path.splitext(target_disegno)
            max_root = 50 - len(ext)
            if max_root > 0:
                target_disegno = f"{root[:max_root]}{ext}"
            else:
                target_disegno = target_disegno[:50]

        # Se il campo Disegno è già uguale, salta
        if dis_plus.lower() == target_disegno.lower():
            continue

        da_aggiornare.append({
            "row_number": row_idx,
            "caid": int(caid_val),
            "codice": cod_val,
            "marca": marca_val,
            "disegno_vecchio": dis_plus,
            "disegno_nuovo": target_disegno
        })

        if args.max > 0 and len(da_aggiornare) >= args.max:
            break

    print(f"Articoli candidati all'aggiornamento su Plus 2000: {len(da_aggiornare)}")
    if not da_aggiornare:
        print("Nessun articolo da aggiornare trovato con i criteri specificati.")
        return

    # 3. Anteprima dei primi articoli
    print("\n--- ANTEPRIMA AGGIORNAMENTI (Primi 10) ---")
    for item in da_aggiornare[:10]:
        v = item['disegno_vecchio'] if item['disegno_vecchio'] else "(vuoto)"
        print(f"  • CaId {item['caid']:<7} | Cod: {item['codice']:<15} | Marca: {item['marca']:<5} | Disegno: {v}  ==>  {item['disegno_nuovo']}")
    if len(da_aggiornare) > 10:
        print(f"  ... e altri {len(da_aggiornare) - 10} articoli.")
    print("-" * 50)

    if is_dry_run:
        print("\n[SIMULAZIONE COMPLETATA]: Nessun dato è stato modificato su SQL Server.")
        print(f"Per confermare e applicare l'aggiornamento di questi {len(da_aggiornare)} articoli, esegui:")
        marca_flag = f" --marca {args.marca}" if args.marca else ""
        missing_flag = " --all-missing-images" if args.all_missing_images else ""
        print(f"  python aggiorna_plus_da_drive.py --apply{marca_flag}{missing_flag}\n")
        return

    # 4. Applicazione effettiva su SQL Server
    sql_cfg = cfg["sql_server"]
    dsn = sql_cfg.get("dsn", "climawell")
    print(f"\nConnessione a SQL Server (DSN={dsn})...")
    conn = pyodbc.connect(f"DSN={dsn};", autocommit=False)
    cursor = conn.cursor()

    oggi_int = int(datetime.now().strftime("%Y%m%d"))
    aggiornati_count = 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    effettivi_aggiornati = []

    try:
        print("Applicazione aggiornamenti su tabella Articoli...")
        for item in da_aggiornare:
            try:
                cursor.execute("""
                    UPDATE Articoli
                    SET Disegno = ?,
                        DMod = ?,
                        UtenteMod = 'API'
                    WHERE CaId = ?
                """, (item['disegno_nuovo'][:50], oggi_int, item['caid']))
                aggiornati_count += 1
                effettivi_aggiornati.append(item)
            except Exception as row_err:
                print(f"  [AVVISO]: Errore su CaId {item['caid']} ({item['codice']}): {row_err}")

        conn.commit()
        print(f"[SUCCESSO]: Aggiornati {aggiornati_count} articoli in Plus 2000 (campo Disegno).")
    except Exception as e:
        conn.rollback()
        print(f"[ERRORE CRITICO]: Rollback eseguito a causa di errore: {e}")
        return
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # 5. Notifica di avvenuto allineamento sul foglio Google Drive
    if idx_aggiorna != -1 and aggiornati_count > 0:
        print("Aggiornamento stato 'Aggiorna_in_Plus' su Google Drive...")
        token = client._get_access_token()
        auth_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        import requests
        
        col_letter_agg = col_letter(idx_aggiorna + 1)
        data_updates = []
        for item in effettivi_aggiornati:
            r_num = item["row_number"]
            data_updates.append({
                "range": f"'{TAB_NAME}'!{col_letter_agg}{r_num}",
                "values": [[f"ALLINEATO {now_str}"]]
            })

        # Batch update a blocchi di 500 celle
        for i in range(0, len(data_updates), 500):
            chunk = data_updates[i:i+500]
            batch_body = {
                "valueInputOption": "USER_ENTERED",
                "data": chunk
            }
            batch_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values:batchUpdate"
            requests.post(batch_url, headers=auth_headers, json=batch_body, timeout=20)
        print(f"[OK]: Foglio Google Drive aggiornato con lo stato 'ALLINEATO {now_str}'.")

    print("\n" + "=" * 70)
    print(f"  OPERAZIONE COMPLETATA: {aggiornati_count} ARTICOLI ALLINEATI IN PLUS 2000")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()

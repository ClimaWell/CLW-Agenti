import http.server
import json
import os
import socket
import sys
import datetime
import urllib.parse
import subprocess
from decimal import Decimal
import pyodbc

# Processo globale per Lead Finder
_lead_finder_process = None

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

def launch_lead_finder_process():
    global _lead_finder_process
    port = 8501
    if is_port_in_use(port):
        return f"http://localhost:{port}"

    lead_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "Lead Finder"))
    run_script = os.path.join(lead_dir, "run_app.py")
    if os.path.exists(run_script):
        try:
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, 'DETACHED_PROCESS', 0x00000008)
            _lead_finder_process = subprocess.Popen(
                [sys.executable, run_script],
                cwd=lead_dir,
                creationflags=creation_flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("🚀 [LEAD FINDER] Processo avviato su http://localhost:8501", flush=True)
        except Exception as e:
            print(f"⚠️ [LEAD FINDER] Errore avvio: {e}", flush=True)

    return f"http://localhost:{port}"

# Cartelle e configurazione
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "site")
CONFIG_PATH = os.path.join(BASE_DIR, "..", "connettore-plus2000", "config.json")
if not os.path.exists(CONFIG_PATH):
    CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_connection():
    cfg = load_config()["sql_server"]
    dsn = cfg.get("dsn")
    if dsn:
        try:
            return pyodbc.connect(f"DSN={dsn};", timeout=5)
        except Exception:
            pass

    srv_configured = cfg.get("server", "SRVPLUS")
    candidates = [srv_configured]
    if srv_configured.upper() in ["SRVPLUS", "192.168.1.7"]:
        for extra in ["192.168.1.7", "localhost", "127.0.0.1", "SRVPLUS"]:
            if extra not in candidates:
                candidates.append(extra)

    driver = cfg.get("driver", "SQL Server")
    database = cfg.get("database", "Climawell")
    last_err = None
    for target in candidates:
        conn_str = f"DRIVER={{{driver}}};SERVER={target};DATABASE={database};Trusted_Connection=yes;"
        try:
            return pyodbc.connect(conn_str, timeout=3)
        except Exception as e:
            last_err = e
    raise last_err

def get_local_ips():
    ips = []
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass
    if not ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ips.append(s.getsockname()[0])
            s.close()
        except Exception:
            ips.append("127.0.0.1")
    return ips

# Helper per serializzare Decimal e date in JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)

# Logica di Database
def db_search_article(term):
    term = term.strip()
    if not term:
        return []
    
    conn = get_connection()
    cursor = conn.cursor()
    
    sql = """
    WITH Trovati AS (
        SELECT TOP 15
            a.CaId,
            RTRIM(LTRIM(a.Ca)) as CodiceArticolo,
            RTRIM(LTRIM(a.DesArt + CASE WHEN a.DesSup IS NOT NULL AND RTRIM(a.DesSup) <> '' THEN ' ' + RTRIM(a.DesSup) ELSE '' END)) as Descrizione,
            RTRIM(LTRIM(ISNULL(a.Marca, ''))) as Marca,
            RTRIM(LTRIM(ISNULL(a.JUbiArt, ''))) as Ubicazione,
            RTRIM(LTRIM(ISNULL(a.Um, 'NR'))) as Um
        FROM Articoli a WITH (NOLOCK)
        WHERE a.Ca = ? 
           OR a.CaId = TRY_CAST(? AS INT)
           OR a.CaProd = ?
           OR EXISTS (SELECT 1 FROM ArticoliCodici ac WITH (NOLOCK) WHERE ac.CaId = a.CaId AND ac.CaCod = ?)
           OR EXISTS (SELECT 1 FROM ArticoliUm au WITH (NOLOCK) WHERE au.CaId = a.CaId AND au.CaBarCode = ?)
           OR a.Ca LIKE ?
           OR a.DesArt LIKE ?
        ORDER BY 
           CASE 
             WHEN a.Ca = ? THEN 0
             WHEN a.Ca LIKE ? THEN 1
             ELSE 2 
           END, 
           a.Ca
    )
    SELECT 
        t.CaId,
        t.CodiceArticolo,
        t.Descrizione,
        t.Marca,
        t.Ubicazione,
        t.Um,
        ISNULL(g.TotEsi, 0) as Giacenza,
        ISNULL(g.TotDisp, 0) as Disponibilita,
        ISNULL(g.TotImp, 0) as Impegnato,
        ISNULL(g.EsiDep000, 0) as GiacenzaSede,
        ISNULL(
            (SELECT TOP 1 RTRIM(LTRIM(au.CaBarCode)) FROM ArticoliUm au WITH (NOLOCK) WHERE au.CaId = t.CaId AND au.CaBarCode IS NOT NULL AND RTRIM(LTRIM(au.CaBarCode)) <> '' ORDER BY au.Riga),
            (SELECT TOP 1 RTRIM(LTRIM(ac.CaCod)) FROM ArticoliCodici ac WITH (NOLOCK) WHERE ac.CaId = t.CaId AND ac.CaCod IS NOT NULL AND RTRIM(LTRIM(ac.CaCod)) <> '' ORDER BY ac.Riga)
        ) as Ean
    FROM Trovati t
    OUTER APPLY (
        SELECT 
            SUM(QtEsi) as TotEsi, 
            SUM(QtDisp) as TotDisp,
            SUM(ISNULL(QtImp, 0)) as TotImp,
            SUM(CASE WHEN JDep = '000' THEN QtEsi ELSE 0 END) as EsiDep000
        FROM ArticoliContGen acg WITH (NOLOCK)
        WHERE acg.CaId = t.CaId
    ) g
    """
    like_param = f"%{term}%"
    like_start = f"{term}%"
    cursor.execute(sql, term, term, term, term, term, like_start, like_param, term, like_start)
    
    results = []
    col_names = [col[0] for col in cursor.description]
    for row in cursor.fetchall():
        d = dict(zip(col_names, row))
        # Formattazione campi pulita
        results.append({
            "ca_id": d["CaId"],
            "codice": d["CodiceArticolo"],
            "descrizione": d["Descrizione"],
            "marca": d["Marca"],
            "ubicazione": d["Ubicazione"],
            "um": d["Um"],
            "giacenza": float(d["Giacenza"]),
            "disponibilita": float(d["Disponibilita"]),
            "impegnato": float(d.get("Impegnato") or 0.0),
            "giacenza_sede": float(d.get("GiacenzaSede") or 0.0),
            "ean": d["Ean"] or ""
        })
    conn.close()
    return results

def db_registra_inventario(ca_id, quantita, ubicazione, terminale='WEB01', aggiorna_ubicazione=True, note=''):
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.datetime.now()
    d_reg = int(now.strftime("%Y%m%d"))
    ora_reg = int(now.strftime("%H%M%S"))
    
    # Recupera UM articolo
    cursor.execute("SELECT RTRIM(ISNULL(Um, 'NR')), RTRIM(ISNULL(JUbiArt, '')) FROM Articoli WHERE CaId = ?", ca_id)
    art_row = cursor.fetchone()
    um = art_row[0] if art_row else 'NR'
    vecchia_ubi = art_row[1] if art_row else ''
    
    # Nuovo RegId
    cursor.execute("SELECT ISNULL(MAX(RegId), 0) + 1 FROM WinCeInv")
    new_reg_id = int(cursor.fetchone()[0])
    
    # Pulizia ubicazione e terminale
    ubi_clean = (ubicazione or "").strip().upper()
    term_clean = (terminale or "003").strip()[:10]
    note_clean = (note or "").strip()[:50]
    
    # Inserimento in WinCeInv
    sql_inv = """
    INSERT INTO WinCeInv (
        RegId, DReg, OraReg, DDoc, JDep, JVano, JTerminale, 
        CaId, VarId, Um, YLotto, DScadenza, Qt, Note
    ) VALUES (
        ?, ?, ?, ?, '000', ?, ?, 
        ?, 0, ?, '', 0, ?, ?
    )
    """
    cursor.execute(sql_inv, new_reg_id, d_reg, ora_reg, d_reg, ubi_clean, term_clean, ca_id, um, quantita, note_clean)
    
    # Se l'operatore ha modificato l'ubicazione e richiesto l'aggiornamento
    ubi_modificata = False
    if aggiorna_ubicazione and ubi_clean and ubi_clean != vecchia_ubi:
        cursor.execute("UPDATE Articoli SET JUbiArt = ? WHERE CaId = ?", ubi_clean, ca_id)
        ubi_modificata = True
        
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "reg_id": new_reg_id,
        "d_reg": d_reg,
        "ora_reg": ora_reg,
        "ca_id": ca_id,
        "quantita": quantita,
        "ubicazione": ubi_clean,
        "ubicazione_modificata_su_plus": ubi_modificata
    }

def db_get_storico_oggi(filtro_diff=None):
    conn = get_connection()
    cursor = conn.cursor()
    d_today = int(datetime.datetime.now().strftime("%Y%m%d"))
    
    sql = """
    SELECT TOP 500
        w.RegId,
        w.DReg,
        w.OraReg,
        w.CaId,
        RTRIM(a.Ca) as CodiceArticolo,
        RTRIM(a.DesArt) as Descrizione,
        w.JVano as Ubicazione,
        w.Qt,
        w.Um,
        w.JTerminale,
        ISNULL(g.TotEsi, 0) as GiacenzaAttuale,
        ISNULL(w.Note, '') as Note
    FROM WinCeInv w
    LEFT JOIN Articoli a ON w.CaId = a.CaId
    LEFT JOIN (SELECT CaId, SUM(QtEsi) as TotEsi FROM ArticoliContGen GROUP BY CaId) g ON w.CaId = g.CaId
    WHERE w.DReg = ?
    ORDER BY w.RegId DESC
    """
    cursor.execute(sql, d_today)
    rows = cursor.fetchall()
    
    history = []
    for r in rows:
        ora_str = str(r[2]).zfill(6)
        ora_fmt = f"{ora_str[0:2]}:{ora_str[2:4]}:{ora_str[4:6]}"
        qt = float(r[7])
        esi = float(r[10])
        diff = round(qt - esi, 2)
        
        # Filtro opzionale: 'only_diff', 'aligned'
        if filtro_diff == 'only_diff' and abs(diff) < 0.0001:
            continue
        if filtro_diff == 'aligned' and abs(diff) >= 0.0001:
            continue
            
        history.append({
            "reg_id": r[0],
            "data": str(r[1]),
            "ora": ora_fmt,
            "ca_id": r[3],
            "codice": r[4] or "",
            "descrizione": r[5] or "",
            "ubicazione": r[6] or "",
            "quantita": qt,
            "um": r[8] or "NR",
            "terminale": r[9] or "",
            "giacenza_attuale": esi,
            "differenza": diff,
            "stato": "allineato" if abs(diff) < 0.0001 else ("eccedenza" if diff > 0 else "ammanco"),
            "note": r[11] or ""
        })
    conn.close()
    return history

def db_get_riepilogo_inventario():
    conn = get_connection()
    cursor = conn.cursor()
    d_today = int(datetime.datetime.now().strftime("%Y%m%d"))
    
    sql = """
    SELECT 
        w.RegId,
        w.CaId,
        w.Qt,
        ISNULL(g.TotEsi, 0) as GiacenzaAttuale
    FROM WinCeInv w
    LEFT JOIN (SELECT CaId, SUM(QtEsi) as TotEsi FROM ArticoliContGen GROUP BY CaId) g ON w.CaId = g.CaId
    WHERE w.DReg = ?
    """
    cursor.execute(sql, d_today)
    rows = cursor.fetchall()
    conn.close()
    
    tot_righe = len(rows)
    tot_pezzi = sum(float(r[2]) for r in rows)
    allineati = 0
    con_differenza = 0
    pezzi_piu = 0.0
    pezzi_meno = 0.0
    
    for r in rows:
        qt = float(r[2])
        esi = float(r[3])
        diff = round(qt - esi, 2)
        if abs(diff) < 0.0001:
            allineati += 1
        else:
            con_differenza += 1
            if diff > 0:
                pezzi_piu += diff
            else:
                pezzi_meno += abs(diff)
                
    return {
        "tot_righe": tot_righe,
        "tot_pezzi": round(tot_pezzi, 2),
        "allineati": allineati,
        "con_differenza": con_differenza,
        "pezzi_piu": round(pezzi_piu, 2),
        "pezzi_meno": round(pezzi_meno, 2)
    }

def db_get_articoli_per_ubicazione(ubicazione):
    ubi = (ubicazione or "").strip()
    if not ubi:
        return []
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
    WITH Giacenze AS (
        SELECT CaId, SUM(QtEsi) as TotEsi, SUM(QtDisp) as TotDisp
        FROM ArticoliContGen
        GROUP BY CaId
    )
    SELECT TOP 100
        a.CaId,
        RTRIM(LTRIM(a.Ca)) as CodiceArticolo,
        RTRIM(LTRIM(a.DesArt)) as Descrizione,
        RTRIM(LTRIM(ISNULL(a.Marca, ''))) as Marca,
        RTRIM(LTRIM(ISNULL(a.JUbiArt, ''))) as Ubicazione,
        RTRIM(LTRIM(ISNULL(a.Um, 'NR'))) as Um,
        ISNULL(g.TotEsi, 0) as Giacenza,
        ISNULL(g.TotDisp, 0) as Disponibilita,
        ISNULL(
           (SELECT TOP 1 RTRIM(LTRIM(au.CaBarCode)) FROM ArticoliUm au WITH (NOLOCK) WHERE au.CaId = a.CaId AND au.CaBarCode IS NOT NULL AND au.CaBarCode <> '' ORDER BY au.Riga),
           (SELECT TOP 1 RTRIM(LTRIM(ac.CaCod)) FROM ArticoliCodici ac WITH (NOLOCK) WHERE ac.CaId = a.CaId ORDER BY ac.Riga)
        ) as Ean
    FROM Articoli a
    LEFT JOIN Giacenze g ON a.CaId = g.CaId
    WHERE a.JUbiArt = ? OR a.JUbiArt LIKE ?
    ORDER BY a.JUbiArt, a.Ca
    """
    like_ubi = f"{ubi}%"
    cursor.execute(sql, ubi, like_ubi)
    results = []
    for row in cursor.fetchall():
        results.append({
            "ca_id": row[0],
            "codice": row[1],
            "descrizione": row[2],
            "marca": row[3],
            "ubicazione": row[4],
            "um": row[5],
            "giacenza": float(row[6]),
            "disponibilita": float(row[7]),
            "ean": row[8] or ""
        })
    conn.close()
    return results

def db_cancella_registrazione(reg_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM WinCeInv WHERE RegId = ?", reg_id)
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# --- GESTIONE PICKING & ORDINI APERTI (FILTRO EVASO = 'N' & GIACENZA POSITIVA) ---
def db_get_ordini_aperti(filtro_giacenza=None):
    """
    Recupera ordini clienti aperti da Plus 2000 (DocTes con Evaso = 'N' o NULL).
    Calcola per ciascun ordine:
    - righe_da_prelevare (totale righe da evadere)
    - righe_positive (righe con giacenza/disponibilità reale > 0)
    - righe_complete (righe con disponibilità >= qta ordinata)
    - stato_giacenza: 'PRONTO_100', 'PARZIALE', 'ATTESA_MERCE'
    Supporta il filtro:
    - 'ready' o 'pronti': solo ordini 100% completabili subito
    - 'positive' o 'positivi': solo ordini con almeno 1 articolo con giacenza positiva
    - 'all': tutti gli ordini aperti
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    sql = """
    SELECT TOP 150
        t.DocId,
        t.Anno,
        RTRIM(t.TpDoc) as TpDoc,
        t.YDoc as NumeroOrdine,
        t.DDoc as DataDoc,
        RTRIM(LTRIM(ISNULL(c.RagSoc, '') + CASE WHEN c.RagSup IS NOT NULL AND RTRIM(c.RagSup) <> '' THEN ' ' + RTRIM(c.RagSup) ELSE '' END)) as Cliente,
        RTRIM(ISNULL(c.Citta, '')) as Citta,
        RTRIM(ISNULL(t.RifOrd, '')) as RiferimentoOrdine,
        ISNULL(t.ATotale, 0) as TotaleImponibile,
        RTRIM(ISNULL(t.Evaso, 'N')) as Evaso,
        COUNT(r.Riga) as RigheDaPrelevare,
        SUM(CASE WHEN ISNULL(g.TotEsi, 0) > 0 THEN 1 ELSE 0 END) as RigheConGiacenzaPositiva,
        SUM(CASE WHEN ISNULL(g.TotEsi, 0) > 0 AND ISNULL(g.TotEsi, 0) >= (ISNULL(r.Qt, 0) - ISNULL(r.QtEvaso, 0)) THEN 1 ELSE 0 END) as RighePronteComplete,
        SUM(ISNULL(r.Qt, 0) - ISNULL(r.QtEvaso, 0)) as PezziDaPrelevare,
        SUM(CASE WHEN ISNULL(g.TotEsi, 0) > 0 THEN ISNULL(g.TotEsi, 0) ELSE 0 END) as PezziDisponibili
    FROM DocTes t WITH (NOLOCK)
    LEFT JOIN CliFor c WITH (NOLOCK) ON t.TpConto = c.TpConto AND t.JConto = c.JConto
    JOIN DocRig r WITH (NOLOCK) ON r.DocId = t.DocId
    JOIN Articoli a WITH (NOLOCK) ON r.CaId = a.CaId
    LEFT JOIN (SELECT CaId, SUM(QtEsi) as TotEsi, SUM(QtDisp) as TotDisp FROM ArticoliContGen WITH (NOLOCK) GROUP BY CaId) g ON a.CaId = g.CaId
    WHERE t.TpDoc IN ('OCL', 'ORD')
      AND (t.Evaso = 'N' OR t.Evaso IS NULL)
      AND (r.Evaso = 'N' OR r.Evaso IS NULL)
      AND (ISNULL(r.Qt, 0) - ISNULL(r.QtEvaso, 0)) > 0
      AND RTRIM(a.Ca) NOT IN ('C', 'CI')
      AND ISNULL(r.CaId, 0) > 0
    GROUP BY
        t.DocId, t.Anno, t.TpDoc, t.YDoc, t.DDoc,
        c.RagSoc, c.RagSup, c.Citta, t.RifOrd, t.ATotale, t.Evaso
    ORDER BY t.DDoc DESC, t.YDoc DESC
    """
    cursor.execute(sql)
    col_names = [col[0].lower() for col in cursor.description]
    orders = []
    for row in cursor.fetchall():
        d = dict(zip(col_names, row))
        qta_righe = int(d.get("righedaprelevare") or 0)
        if qta_righe <= 0:
            continue
        
        qta_positive = int(d.get("righecongiacenzapositiva") or 0)
        qta_complete = int(d.get("righeprontecomplete") or 0)
        pezzi_tot = float(d.get("pezzidaprelevare") or 0.0)
        pezzi_disp = float(d.get("pezzidisponibili") or 0.0)

        is_ready_100 = bool(qta_complete >= qta_righe and qta_righe > 0)
        has_positive = bool(qta_positive > 0)

        if is_ready_100:
            stato_giac = "PRONTO_100"
            stato_label = "🟢 Pronto (100% in Magazzino)"
        elif has_positive:
            stato_giac = "PARZIALE"
            stato_label = f"🟡 Parziale ({qta_positive}/{qta_righe} disponibili)"
        else:
            stato_giac = "ATTESA_MERCE"
            stato_label = "🔴 Attesa Arrivo Merce (0 pz in esistenza)"

        # Filtraggio rigoroso lato server
        f = (filtro_giacenza or "").lower().strip()
        if f in ["ready", "pronti", "100"] and not is_ready_100:
            continue
        if f in ["positive", "positivi", "positiva", "disponibili"] and not has_positive:
            continue

        d_doc = str(d.get("datadoc") or "")
        d_fmt = f"{d_doc[6:8]}/{d_doc[4:6]}/{d_doc[0:4]}" if len(d_doc) == 8 else d_doc
        orders.append({
            "doc_id": d.get("docid"),
            "anno": d.get("anno"),
            "tp_doc": d.get("tpdoc"),
            "numero": d.get("numeroordine"),
            "data": d_fmt,
            "data_raw": d.get("datadoc"),
            "cliente": d.get("cliente") or "Cliente non specificato",
            "citta": d.get("citta") or "",
            "riferimento": d.get("riferimentoordine") or "",
            "imponibile": float(d.get("totaleimponibile") or 0.0),
            "evaso": d.get("evaso") or "N",
            "righe_da_prelevare": qta_righe,
            "righe_positive": qta_positive,
            "righe_complete": qta_complete,
            "pezzi_da_prelevare": pezzi_tot,
            "pezzi_disponibili": pezzi_disp,
            "is_ready_100": is_ready_100,
            "has_positive_stock": has_positive,
            "stato_giacenza": stato_giac,
            "stato_label": stato_label
        })
    conn.close()
    return orders

def db_get_righe_ordine_picking(doc_id):
    """Recupera le righe dell'ordine con percorso picking ordinato per ubicazione (Evaso = 'N')"""
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
    SELECT 
        r.DocId,
        r.Riga,
        r.CaId,
        RTRIM(a.Ca) as CodiceArticolo,
        RTRIM(a.DesArt + CASE WHEN a.DesSup IS NOT NULL AND RTRIM(a.DesSup) <> '' THEN ' ' + RTRIM(a.DesSup) ELSE '' END) as Descrizione,
        RTRIM(ISNULL(a.Marca, '')) as Marca,
        RTRIM(ISNULL(a.JUbiArt, '')) as Ubicazione,
        RTRIM(ISNULL(a.Um, 'NR')) as Um,
        ISNULL(r.Qt, 0) as QuantitaOrdinata,
        ISNULL(r.QtEvaso, 0) as QuantitaEvasa,
        (ISNULL(r.Qt, 0) - ISNULL(r.QtEvaso, 0)) as QuantitaDaPrelevare,
        RTRIM(ISNULL(r.Evaso, 'N')) as Evaso,
        ISNULL(g.TotDisp, 0) as GiacenzaDisponibile,
        ISNULL(g.TotEsi, 0) as GiacenzaFisica,
        ISNULL(
           (SELECT TOP 1 RTRIM(LTRIM(au.CaBarCode)) FROM ArticoliUm au WITH (NOLOCK) WHERE au.CaId = a.CaId AND au.CaBarCode IS NOT NULL AND au.CaBarCode <> '' ORDER BY au.Riga),
           (SELECT TOP 1 RTRIM(LTRIM(ac.CaCod)) FROM ArticoliCodici ac WITH (NOLOCK) WHERE ac.CaId = a.CaId ORDER BY ac.Riga)
        ) as Ean
    FROM DocRig r WITH (NOLOCK)
    JOIN Articoli a WITH (NOLOCK) ON r.CaId = a.CaId
    LEFT JOIN (SELECT CaId, SUM(QtEsi) as TotEsi, SUM(QtDisp) as TotDisp FROM ArticoliContGen WITH (NOLOCK) GROUP BY CaId) g ON a.CaId = g.CaId
    WHERE r.DocId = ?
      AND (r.Evaso = 'N' OR r.Evaso IS NULL)
      AND (ISNULL(r.Qt, 0) - ISNULL(r.QtEvaso, 0)) > 0
      AND RTRIM(a.Ca) NOT IN ('C', 'CI')
      AND ISNULL(r.CaId, 0) > 0
    ORDER BY 
        CASE WHEN a.JUbiArt IS NULL OR RTRIM(a.JUbiArt) = '' THEN 1 ELSE 0 END,
        a.JUbiArt,
        r.Riga
    """
    cursor.execute(sql, doc_id)
    col_names = [col[0].lower() for col in cursor.description]
    lines = []
    for row in cursor.fetchall():
        d = dict(zip(col_names, row))
        q_ord = float(d.get("quantitaordinata") or 0.0)
        q_eva = float(d.get("quantitaevasa") or 0.0)
        q_prel = float(d.get("quantitadaprelevare") or 0.0)
        disp = float(d.get("giacenzadisponibile") or 0.0)
        esi = float(d.get("giacenzafisica") or 0.0)
        ha_pos = bool(esi > 0)
        is_pronta = bool(esi >= q_prel and esi > 0)
        stato = "PRONTA" if is_pronta else ("PARZIALE" if ha_pos else "MANCANTE")

        lines.append({
            "doc_id": d.get("docid"),
            "riga": d.get("riga"),
            "ca_id": d.get("caid"),
            "codice": d.get("codicearticolo") or "",
            "descrizione": d.get("descrizione") or "",
            "marca": d.get("marca") or "Climawell",
            "ubicazione": d.get("ubicazione") or "SENZA UBICAZIONE",
            "um": d.get("um") or "NR",
            "qta_ordinata": q_ord,
            "qta_evasa": q_eva,
            "qta_da_prelevare": q_prel,
            "qta_prelevata": 0.0,
            "disponibilita": disp,
            "esistenza": esi,
            "ha_giacenza_positiva": ha_pos,
            "is_pronta": is_pronta,
            "stato_riga": stato,
            "ean": d.get("ean") or "",
            "is_completed": False
        })
    conn.close()
    return lines

# -----------------------------------------------------------------------------
# GIRO CLIENTE IN MAGAZZINO & CREAZIONE ORDINE OCL SU PLUS 2000
# -----------------------------------------------------------------------------
def db_search_clienti(term):
    term = (term or "").strip()
    if not term:
        return []

    clean_term = re.sub(r'[^a-zA-Z0-9]', '', term)
    is_numeric = term.isdigit()
    term_num = int(term) if is_numeric else None

    # 1. Ricerca diretta su SQL Server Plus 2000 (tabella CliFor / Conti)
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Gestione matching avanzato:
        # - Codice numerico esatto (es. 32 trova JConto = 32 o '00032')
        # - Ragione sociale con o senza punti/spazi (es. 'stag' trova 'S.T.A.G. SRL')
        sql = """
        SELECT TOP 25
            RTRIM(c.JConto) as codice,
            RTRIM(LTRIM(c.RagSoc + CASE WHEN c.RagSup IS NOT NULL AND RTRIM(c.RagSup) <> '' THEN ' ' + RTRIM(c.RagSup) ELSE '' END)) as ragione_sociale,
            RTRIM(ISNULL(c.Citta, '')) as citta,
            RTRIM(ISNULL(c.Provincia, '')) as provincia,
            RTRIM(ISNULL(c.Indirizzo, '')) as indirizzo,
            RTRIM(ISNULL(c.PartitaIva, '')) as partita_iva,
            RTRIM(ISNULL(c.CodFiscale, '')) as codice_fiscale
        FROM CliFor c WITH (NOLOCK)
        WHERE c.TpConto = 'C' AND (c.Bloccato = 0 OR c.Bloccato IS NULL)
          AND (
            c.RagSoc LIKE ? 
            OR c.RagSup LIKE ?
            OR REPLACE(REPLACE(c.RagSoc, '.', ''), ' ', '') LIKE ?
            OR c.JConto = ?
            OR CAST(c.JConto AS VARCHAR) LIKE ?
            OR c.PartitaIva LIKE ? 
            OR c.CodFiscale LIKE ?
          )
        ORDER BY c.RagSoc
        """
        like_p = f"%{term}%"
        like_clean = f"%{clean_term}%" if clean_term else like_p
        like_start = f"{term}%"
        num_param = term_num if term_num is not None else -999999
        
        cursor.execute(sql, like_p, like_p, like_clean, num_param, like_start, like_start, like_start)
        rows = cursor.fetchall()
        cols = [c[0].lower() for c in cursor.description]
        results = [dict(zip(cols, r)) for r in rows]
        conn.close()
        if results:
            return results
    except Exception as sql_err:
        print(f"⚠️ [Clienti Plus CliFor] Errore ({sql_err}), tento fallback Conti / Supabase...", flush=True)

    # 1b. Tentativo su tabella Conti se CliFor non ha restituito o ha dato errore
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql_conti = """
        SELECT TOP 25
            RTRIM(c.JConto) as codice,
            RTRIM(LTRIM(c.RagSoc + CASE WHEN c.RagSup IS NOT NULL AND RTRIM(c.RagSup) <> '' THEN ' ' + RTRIM(c.RagSup) ELSE '' END)) as ragione_sociale,
            RTRIM(ISNULL(c.Citta, '')) as citta,
            RTRIM(ISNULL(c.Provincia, '')) as provincia,
            RTRIM(ISNULL(c.Indirizzo, '')) as indirizzo,
            RTRIM(ISNULL(c.PartitaIva, '')) as partita_iva,
            RTRIM(ISNULL(c.CodFiscale, '')) as codice_fiscale
        FROM Conti c WITH (NOLOCK)
        WHERE c.TpConto = 'C' AND (c.Bloccato = 0 OR c.Bloccato IS NULL)
          AND (
            c.RagSoc LIKE ? 
            OR REPLACE(REPLACE(c.RagSoc, '.', ''), ' ', '') LIKE ?
            OR c.JConto = ?
            OR CAST(c.JConto AS VARCHAR) LIKE ?
            OR c.PartitaIva LIKE ?
          )
        ORDER BY c.RagSoc
        """
        like_p = f"%{term}%"
        like_clean = f"%{clean_term}%" if clean_term else like_p
        like_start = f"{term}%"
        num_param = term_num if term_num is not None else -999999
        cursor.execute(sql_conti, like_p, like_clean, num_param, like_start, like_start)
        rows = cursor.fetchall()
        cols = [c[0].lower() for c in cursor.description]
        results = [dict(zip(cols, r)) for r in rows]
        conn.close()
        if results:
            return results
    except Exception as conti_err:
        pass

    # 2. Fallback a Supabase se SQL Server temporaneamente offline
    try:
        cfg = load_config().get("supabase", {})
        sb_url = cfg.get("url")
        sb_key = cfg.get("service_role_key") or cfg.get("anon_key")
        if sb_url and sb_key:
            import urllib.request
            # Ricerca multi-variante su Supabase per gestire sia '32', 'CLI-00032', 'stag', 's.t.a.g.'
            or_parts = [
                f"name.ilike.*{urllib.parse.quote(term)}*",
                f"code.ilike.*{urllib.parse.quote(term)}*",
                f"vat_number.ilike.*{urllib.parse.quote(term)}*"
            ]
            if is_numeric:
                or_parts.append(f"code.eq.CLI-{term.zfill(5)}")
                or_parts.append(f"code.eq.{term}")
            if clean_term and clean_term.lower() != term.lower():
                or_parts.append(f"name.ilike.*{urllib.parse.quote(clean_term)}*")
            # Gestione specifica S.T.A.G. se cercato senza punti
            if clean_term.upper() == "STAG":
                or_parts.append("name.ilike.*S.T.A.G.*")
            
            req_url = f"{sb_url}/rest/v1/customers?select=code,name,city,province,address,vat_number,tax_code&or=({','.join(or_parts)})&limit=25"
            req = urllib.request.Request(req_url, headers={"apikey": sb_key, "Authorization": f"Bearer {sb_key}"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [
                    {
                        "codice": c.get("code") or "",
                        "ragione_sociale": c.get("name") or "",
                        "citta": c.get("city") or "",
                        "provincia": c.get("province") or "",
                        "indirizzo": c.get("address") or "",
                        "partita_iva": c.get("vat_number") or "",
                        "codice_fiscale": c.get("tax_code") or ""
                    }
                    for c in data
                ]
    except Exception as sb_err:
        print(f"⚠️ [Clienti Supabase Fallback] Errore: {sb_err}", flush=True)

    return []


def db_crea_ordine_giro_cliente(payload):
    cliente_codice = (payload.get("cliente_codice") or "").strip()
    cliente_nome = (payload.get("cliente_nome") or "").strip()
    operatore = (payload.get("operatore") or "Magazziniere").strip()
    note_ordine = (payload.get("note") or "Ordine Banco / Giro Magazzino con Cliente").strip()
    righe = payload.get("righe", [])

    if not cliente_codice:
        raise ValueError("Codice cliente obbligatorio")
    if not righe:
        raise ValueError("Nessun articolo selezionato nel carrello")

    now = datetime.datetime.now()
    anno = now.year
    d_doc_int = int(now.strftime("%Y%m%d"))
    tp_doc = "OCL"
    j_seq_doc = "01"

    doc_id_plus = None
    y_doc = None
    plus_success = False

    # 1. Inserimento diretto su Plus 2000 SQL Server
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Prossimo numero progressivo documento per OCL
        cursor.execute("SELECT ISNULL(MAX(YDoc), 0) + 1 FROM DocTes WHERE Anno = ? AND TpDoc = ? AND JSeqDoc = ?", (anno, tp_doc, j_seq_doc))
        y_doc_row = cursor.fetchone()
        y_doc = int(y_doc_row[0]) if y_doc_row else 1

        rif_ord = f"BANCO {operatore.upper()}"[:30]
        sql_insert_tes = """
        SET NOCOUNT ON;
        INSERT INTO DocTes (
            Anno, TpDoc, JSeqDoc, YDoc, DDoc,
            JCauMaga, DesCauMaga, JDepPri, JDepSec,
            TpConto, JConto, TpContoDest, JContoDest,
            JValuta, ACambio, RifOrd, DRifOrd, Note
        ) VALUES (
            ?, ?, ?, ?, ?,
            'ORCL', 'ORDINE CLIENTE', '000', '000',
            'C', ?, 'C', ?,
            'EUR', 1.0, ?, ?, ?
        );
        SELECT SCOPE_IDENTITY();
        """
        cursor.execute(sql_insert_tes, (anno, tp_doc, j_seq_doc, y_doc, d_doc_int, cliente_codice, cliente_codice, rif_ord, d_doc_int, note_ordine[:50]))
        doc_id_plus = int(cursor.fetchone()[0])

        # Applica Stored Procedure default testata (pagamento, banche, agente)
        cursor.execute(f"EXEC sp_DocTes_SetDefault {doc_id_plus}, 0")

        # Riafferma Causale ORCL e Deposito 000 su DocTes
        cursor.execute("""
            UPDATE DocTes
            SET JCauMaga = 'ORCL', DesCauMaga = 'ORDINE CLIENTE', JDepPri = '000', JDepSec = '000'
            WHERE DocId = ?
        """, (doc_id_plus,))

        # Inserimento righe
        for r_num, item in enumerate(righe, start=1):
            ca_id = int(item.get("ca_id") or 0)
            cod_art = item.get("codice", "")
            des_art = item.get("descrizione", "")
            um = (item.get("um") or "PZ")[:3]
            qt = float(item.get("quantita") or 1)

            if ca_id == 0 and cod_art:
                cursor.execute("SELECT CaId FROM Articoli WHERE Ca = ?", (cod_art,))
                art_row = cursor.fetchone()
                if art_row:
                    ca_id = art_row[0]

            sql_insert_rig = """
            SET NOCOUNT ON;
            INSERT INTO DocRig (
                DocId, Riga, TpDoc, JSeqDoc, DDoc,
                CaId, DesArt, Um, UmQt, Pezzi, Qt,
                PzLordo, PzNetto, ScontoExtra, JIva, Note,
                JCauMaga, JDep
            ) VALUES (
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                0, 0, 0, '22', ?,
                'ORCL', '000'
            );
            SELECT SCOPE_IDENTITY();
            """
            cursor.execute(sql_insert_rig, (doc_id_plus, r_num, tp_doc, j_seq_doc, d_doc_int, ca_id, des_art[:50], um, um, qt, qt, f"Giro Magazzino ({operatore})"[:50]))
            riga_id_plus = int(cursor.fetchone()[0])

            # Invocazione Stored Procedure standard Plus per impostazione automatica sconti e condizioni cliente
            cursor.execute(f"EXEC sp_DocRig_SetDefault {riga_id_plus}, 0, 0")

            # Riafferma Causale ORCL e Deposito 000 su DocRig
            cursor.execute("""
                UPDATE DocRig
                SET JCauMaga = 'ORCL', JDep = '000'
                WHERE RigaId = ?
            """, (riga_id_plus,))

        # Ricalcolo totali e IVA dell'ordine
        cursor.execute(f"EXEC sp_Doc_Aggiorna_Totali {doc_id_plus}")
        conn.commit()
        conn.close()
        plus_success = True
        print(f"✅ [Giro Cliente] Creato Ordine Plus 2000 DocId={doc_id_plus}, OCL N.{y_doc}/{anno} per Cliente={cliente_codice}", flush=True)

    except Exception as sql_err:
        print(f"⚠️ [Giro Cliente] Errore inserimento diretto SQL Server: {sql_err}", flush=True)

    # 2. Sincronizzazione in tempo reale su Supabase per gli agenti e la sede
    try:
        cfg = load_config().get("supabase", {})
        sb_url = cfg.get("url")
        sb_key = cfg.get("service_role_key") or cfg.get("anon_key")
        if sb_url and sb_key:
            import urllib.request
            doc_num_str = f"OCL-{y_doc or now.strftime('%H%M%S')}-{anno}"
            headers = {
                "apikey": sb_key,
                "Authorization": f"Bearer {sb_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
            doc_payload = {
                "number": doc_num_str,
                "document_type": "OCL",
                "status": "In Lavorazione",
                "customer_name": cliente_nome,
                "customer_code": cliente_codice,
                "notes": f"{note_ordine} [Operatore: {operatore}]",
                "plus_doc_id": doc_id_plus or 0
            }
            req = urllib.request.Request(f"{sb_url}/rest/v1/documents", data=json.dumps(doc_payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=8) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                if resp_json and len(resp_json) > 0:
                    doc_id_uuid = resp_json[0].get("id")
                    lines_payload = []
                    for idx, item in enumerate(righe, start=1):
                        lines_payload.append({
                            "document_id": doc_id_uuid,
                            "document_number": doc_num_str,
                            "line_number": idx,
                            "product_code": item.get("codice", ""),
                            "description": item.get("descrizione", ""),
                            "quantity": float(item.get("quantita") or 1),
                            "unit_of_measure": item.get("um") or "PZ",
                            "price": 0.0,
                            "total": 0.0
                        })
                    req_lines = urllib.request.Request(f"{sb_url}/rest/v1/document_lines", data=json.dumps(lines_payload).encode("utf-8"), headers=headers, method="POST")
                    urllib.request.urlopen(req_lines, timeout=8)
    except Exception as sb_err:
        print(f"⚠️ [Giro Cliente] Errore sincronizzazione Supabase: {sb_err}", flush=True)

    order_display_num = f"OCL {y_doc}/{anno}" if y_doc else f"OCL-{now.strftime('%d%m%H%M')}"
    return {
        "success": True,
        "doc_id": doc_id_plus,
        "numero": y_doc or 0,
        "anno": anno,
        "order_display": order_display_num,
        "cliente": cliente_nome,
        "cliente_codice": cliente_codice,
        "articoli_count": len(righe),
        "pezzi_totali": sum(float(r.get("quantita", 1)) for r in righe),
        "message": f"Ordine {order_display_num} creato con successo su Plus 2000!"
    }

# Request Handler HTTP
class WarehouseRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        # Header CORS e Cache-Control per forzare il refresh di HTML, JS e CSS ed evitare cache obsoleta
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, cls=DecimalEncoder).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Endpoint API Avvio / Controllo Lead Finder
        if path in ("/api/lead-finder/start", "/api/lead-finder/status"):
            url_lf = launch_lead_finder_process() if path == "/api/lead-finder/start" else ("http://localhost:8501" if is_port_in_use(8501) else None)
            self.send_json({
                "success": True,
                "running": is_port_in_use(8501),
                "url": url_lf or "http://localhost:8501"
            })
            return

        # Endpoint API Ricerca Articolo
        if path == "/api/articolo":
            term = query.get("q", [""])[0]
            try:
                items = db_search_article(term)
                self.send_json({"success": True, "results": items})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        # Endpoint API Ricerca Clienti Plus 2000 per Giro Magazzino
        if path == "/api/clienti/cerca":
            term = query.get("q", [""])[0]
            try:
                clients = db_search_clienti(term)
                self.send_json({"success": True, "count": len(clients), "results": clients})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        # Endpoint API Storico Oggi
        if path == "/api/storico":
            filtro = query.get("filtro", [None])[0]
            try:
                items = db_get_storico_oggi(filtro)
                self.send_json({"success": True, "results": items})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        # Endpoint API Riepilogo e Statistiche Inventario Oggi
        if path == "/api/inventario/riepilogo":
            try:
                summary = db_get_riepilogo_inventario()
                self.send_json({"success": True, "riepilogo": summary})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        # Endpoint API Articoli per Ubicazione
        if path == "/api/articoli-ubicazione":
            ubi = query.get("ubi", [""])[0]
            try:
                items = db_get_articoli_per_ubicazione(ubi)
                self.send_json({"success": True, "ubicazione": ubi, "count": len(items), "results": items})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        # Endpoint API Esportazione CSV Inventario Oggi
        if path == "/api/inventario/esporta":
            try:
                history = db_get_storico_oggi()
                csv_lines = ["RegId;Data;Ora;CodiceArticolo;Descrizione;Ubicazione;QtContata;GiacenzaPlus;Differenza;Stato;Terminale;Note"]
                for h in history:
                    c_clean = str(h.get("codice") or "").replace('"', '""')
                    d_clean = str(h.get("descrizione") or "").replace('"', '""')
                    u_clean = str(h.get("ubicazione") or "").replace('"', '""')
                    t_clean = str(h.get("terminale") or "").replace('"', '""')
                    n_clean = str(h.get("note") or "").replace('"', '""')
                    csv_lines.append(f"{h['reg_id']};{h['data']};{h['ora']};\"{c_clean}\";\"{d_clean}\";\"{u_clean}\";{h['quantita']};{h['giacenza_attuale']};{h['differenza']};{h['stato']};\"{t_clean}\";\"{n_clean}\"")
                csv_content = "\ufeff" + "\n".join(csv_lines)
                csv_bytes = csv_content.encode("utf-8")

                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", f"attachment; filename=inventario_plus_{datetime.datetime.now().strftime('%Y%m%d')}.csv")
                self.send_header("Content-Length", str(len(csv_bytes)))
                self.end_headers()
                self.wfile.write(csv_bytes)
                return
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
                return

        # Endpoint API Ordini Aperti Plus 2000 (Filtro Evaso = 'N' & Giacenza Positiva)
        if path == "/api/ordini-aperti":
            filtro_g = query.get("filtro", [None])[0] or query.get("giacenza", [None])[0]
            try:
                orders = db_get_ordini_aperti(filtro_giacenza=filtro_g)
                self.send_json({"success": True, "count": len(orders), "results": orders})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        # Endpoint API Righe Ordine Picking da Plus 2000
        if path == "/api/ordine-picking":
            doc_id_str = query.get("doc_id", ["0"])[0]
            try:
                doc_id = int(doc_id_str)
                lines = db_get_righe_ordine_picking(doc_id)
                self.send_json({"success": True, "doc_id": doc_id, "count": len(lines), "results": lines})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        # Endpoint API Info Server & Rete
        if path == "/api/info":
            ips = get_local_ips()
            self.send_json({
                "success": True,
                "server_name": socket.gethostname(),
                "ips": ips,
                "port": self.server.server_address[1],
                "https_port": 5443,
                "active_db": load_config()["sql_server"].get("database", "Climawell")
            })
            return

        # Fallback alle pagine statiche (index.html, ecc.)
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/inventario":
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            try:
                payload = json.loads(body_bytes.decode("utf-8"))
                ca_id = int(payload.get("ca_id"))
                quantita = float(payload.get("quantita", 0))
                ubicazione = payload.get("ubicazione", "")
                terminale = payload.get("terminale", "003")
                aggiorna_ubi = bool(payload.get("aggiorna_ubicazione_plus", True))
                note = payload.get("note", "")

                result = db_registra_inventario(
                    ca_id=ca_id,
                    quantita=quantita,
                    ubicazione=ubicazione,
                    terminale=terminale,
                    aggiorna_ubicazione=aggiorna_ubi,
                    note=note
                )
                self.send_json(result)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        if path == "/api/ordine-picking/conferma":
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            try:
                payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                doc_id = int(payload.get("doc_id", 0))
                operatore = payload.get("operatore", "Magazziniere")
                note = payload.get("note", "")
                self.send_json({
                    "success": True,
                    "doc_id": doc_id,
                    "message": f"Picking ordine {doc_id} confermato con successo da {operatore}",
                    "timestamp": datetime.datetime.now().isoformat()
                })
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        if path == "/api/giro-cliente/crea-ordine":
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            try:
                payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                res = db_crea_ordine_giro_cliente(payload)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        self.send_response(404)
        self.end_headers()

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/inventario/"):
            reg_id_str = path.split("/")[-1]
            try:
                reg_id = int(reg_id_str)
                ok = db_cancella_registrazione(reg_id)
                self.send_json({"success": ok, "reg_id": reg_id})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        self.send_response(404)
        self.end_headers()

def ensure_ssl_cert(cert_path, key_path):
    if os.path.exists(cert_path) and os.path.exists(key_path):
        return True
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import ipaddress

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        ips = get_local_ips()
        san_list = [x509.DNSName("localhost"), x509.IPAddress(ipaddress.IPv4Address("127.0.0.1"))]
        for ip in ips:
            try:
                san_list.append(x509.IPAddress(ipaddress.IPv4Address(ip)))
            except Exception:
                pass

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "Climawell Magazzino"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Climawell S.r.l.")
        ])
        now = datetime.datetime.now(datetime.timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=3650))
            .add_extension(x509.SubjectAlternativeName(san_list), critical=False)
            .sign(key, hashes.SHA256())
        )
        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        return True
    except Exception as e:
        print(f"⚠️ [SSL] Impossibile generare certificato self-signed: {e}")
        return False

def run_server(port=5000):
    os.makedirs(STATIC_DIR, exist_ok=True)
    server_address = ("0.0.0.0", port)
    
    # Threading HTTPServer per servire più dispositivi contemporaneamente
    from http.server import ThreadingHTTPServer
    import ssl
    import threading

    httpd = ThreadingHTTPServer(server_address, WarehouseRequestHandler)
    
    ips = get_local_ips()
    https_port = 5443
    cert_path = os.path.join(BASE_DIR, "cert.pem")
    key_path = os.path.join(BASE_DIR, "key.pem")
    has_ssl = ensure_ssl_cert(cert_path, key_path)

    if has_ssl:
        def start_https():
            try:
                httpsd = ThreadingHTTPServer(("0.0.0.0", https_port), WarehouseRequestHandler)
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
                httpsd.socket = ctx.wrap_socket(httpsd.socket, server_side=True)
                httpsd.serve_forever()
            except Exception as e:
                print(f"⚠️ [HTTPS] Porta {https_port} non avviata: {e}")

        t = threading.Thread(target=start_https, daemon=True)
        t.start()

    print("=================================================================")
    print("📦 SERVER GESTIONE MAGAZZINO & INVENTARIO PLUS2000 AVVIATO")
    print("=================================================================")
    print(f"Server HTTP attivo sulla porta: {port}")
    if has_ssl:
        print(f"Server HTTPS (Camera sbloccata smartphone) sulla porta: {https_port}")
    print("\nAccedi dai dispositivi dei magazzinieri tramite questi indirizzi:")
    for ip in ips:
        print(f" 👉 http://{ip}:{port}")
        if has_ssl:
            print(f" 🔒 https://{ip}:{https_port} (consigliato per fotocamera continua)")
    print(f" 👉 http://localhost:{port} (su questo PC)")
    print("=================================================================")
    print("Premi Ctrl+C per fermare il server.")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArresto del server in corso...")
        httpd.server_close()

if __name__ == "__main__":
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)

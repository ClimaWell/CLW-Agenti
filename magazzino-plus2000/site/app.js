/**
 * CLIMAWELL MAGAZZINO & INVENTARIO PLUS2000 - LOGICA APPLICATIVA
 */

// Stato Applicazione
const state = {
  currentArticle: null,
  html5QrScanner: null,
  activeCameraMode: null, // 'article' o 'shelf'
  todayCount: 0,
  terminalId: localStorage.getItem('terminal_id') || '003',
  fastCountMode: false,
  lockShelfMode: false,
  lockedShelf: '',
  currentHistoryFilter: 'all',
  currentTorchState: false,
  availableCameras: []
};

// Funzione helper sicurezza stringhe HTML
const escapeHtml = str => String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');

// ==========================================
// AUDIO FEEDBACK (Web Audio API Synthesizer)
// ==========================================
let audioCtx = null;

function getAudioContext() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) audioCtx = new AudioContext();
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
}

function playSuccessBeep() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(1200, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(1800, ctx.currentTime + 0.08);
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.09);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.09);
  } catch (e) {
    console.warn("Audio non disponibile", e);
  }
}

function playSaveSound() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(523.25, ctx.currentTime); // C5
    osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.08); // E5
    osc.frequency.setValueAtTime(783.99, ctx.currentTime + 0.16); // G5
    gain.gain.setValueAtTime(0.25, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.28);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.28);
  } catch (e) {}
}

function playErrorTone() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(220, ctx.currentTime);
    osc.frequency.setValueAtTime(180, ctx.currentTime + 0.1);
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.22);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.22);
  } catch (e) {}
}

// ==========================================
// GESTIONE TOAST NOTIFICHE
// ==========================================
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'error') icon = '⚠️';

  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 250);
  }, 3200);
}

// ==========================================
// DOM ELEMENTS
// ==========================================
const barcodeInput = document.getElementById('barcode-input');
const btnClearSearch = document.getElementById('btn-clear-search');
const btnSearchTrigger = document.getElementById('btn-search-trigger');
const btnSubmitSearch = document.getElementById('btn-submit-search');
const searchDropdown = document.getElementById('search-dropdown');
const articleCard = document.getElementById('article-card');
const emptyState = document.getElementById('empty-state');

// Articolo Campi
const artBrand = document.getElementById('art-brand');
const artCode = document.getElementById('art-code');
const artDesc = document.getElementById('art-desc');
const artCaid = document.getElementById('art-caid');
const artStock = document.getElementById('art-stock');
const artUmLabel = document.getElementById('art-um-label');
const currentUbiLabel = document.getElementById('current-ubi-label');

// Ubicazione
const ubiInput = document.getElementById('ubi-input');
const btnScanShelf = document.getElementById('btn-scan-shelf');
const btnResetUbi = document.getElementById('btn-reset-ubi');
const chkSyncUbi = document.getElementById('chk-sync-ubi');

// Quantità & Differenza
const qtyInput = document.getElementById('qty-input');
const qtyUmLabel = document.getElementById('qty-um-label');
const btnStepMinus = document.getElementById('btn-step-minus');
const btnStepPlus = document.getElementById('btn-step-plus');
const diffCard = document.getElementById('diff-card');
const diffValue = document.getElementById('diff-value');
const diffUmLabel = document.getElementById('diff-um-label');
const diffStatusText = document.getElementById('diff-status-text');
const btnMatchStock = document.getElementById('btn-match-stock');
const notesInput = document.getElementById('notes-input');

// Azioni Principali
const btnSaveInventory = document.getElementById('btn-save-inventory');
const btnCancelArticle = document.getElementById('btn-cancel-article');

// Storico & Server
const historyList = document.getElementById('history-list');
const historyBadgeCount = document.getElementById('history-badge-count');
const todayRecordsCount = document.getElementById('today-records-count');
const btnRefreshHistory = document.getElementById('btn-refresh-history');
const terminalIdLabel = document.getElementById('terminal-id-label');
const terminalBadge = document.getElementById('terminal-badge');

// Scanner Fotocamera & Snapshot
const btnStartCamera = document.getElementById('btn-start-camera');
const btnSnapPhoto = document.getElementById('btn-snap-photo');
const cameraFileInput = document.getElementById('camera-file-input');
const cameraModal = document.getElementById('camera-scanner-modal');
const btnCloseCamera = document.getElementById('btn-close-camera');
const cameraSelect = document.getElementById('camera-select');
const btnModalSnap = document.getElementById('btn-modal-snap');
const btnToggleTorch = document.getElementById('btn-toggle-torch');

// Modalità Inventario
const chkFastCount = document.getElementById('chk-fast-count');
const chkLockUbi = document.getElementById('chk-lock-ubi');
const btnOpenUbiInventory = document.getElementById('btn-open-ubi-inventory');
const btnExportCsv = document.getElementById('btn-export-csv');

// Modale Ubicazione
const ubiModal = document.getElementById('ubi-modal');
const btnCloseUbiModal = document.getElementById('btn-close-ubi-modal');
const ubiSearchInput = document.getElementById('ubi-search-input');
const btnSearchUbi = document.getElementById('btn-search-ubi');
const ubiArticlesList = document.getElementById('ubi-articles-list');
const ubiResultsCount = document.getElementById('ubi-results-count');

// KPI Bar
const kpiTotalItems = document.getElementById('kpi-total-items');
const kpiTotalQty = document.getElementById('kpi-total-qty');
const kpiDiffItems = document.getElementById('kpi-diff-items');
const kpiMatchItems = document.getElementById('kpi-match-items');

// QR Code Modal
const btnQrModal = document.getElementById('btn-qr-modal');
const qrModal = document.getElementById('qr-modal');
const btnCloseQr = document.getElementById('btn-close-qr');
const qrCodeContainer = document.getElementById('qr-code-container');
const networkLinksList = document.getElementById('network-links-list');

// Tema
const btnThemeToggle = document.getElementById('btn-theme-toggle');

// ==========================================
// INIZIALIZZAZIONE
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  initTerminalId();
  checkServerStatus();
  loadHistory();
  loadInventoryKpi();
  initNavTabs();
  initGiroClienteModule();
  initPickingModule();
  initShelfPanel();
  setupEventListeners();
});

function initTerminalId() {
  terminalIdLabel.textContent = state.terminalId;
  terminalBadge.addEventListener('click', () => {
    const newTerm = prompt("Identificativo Terminale / Magazziniere:", state.terminalId);
    if (newTerm && newTerm.trim()) {
      state.terminalId = newTerm.trim().toUpperCase();
      localStorage.setItem('terminal_id', state.terminalId);
      terminalIdLabel.textContent = state.terminalId;
      showToast(`Terminale impostato su: ${state.terminalId}`, 'info');
    }
  });
}

function setupEventListeners() {
  // Input Barcode & Pistola Barcode (Enter key automatico)
  let searchDebounceTimer = null;

  barcodeInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      clearTimeout(searchDebounceTimer);
      const val = barcodeInput.value.trim();
      if (val) executeSearch(val, true, true);
    }
  });

  barcodeInput.addEventListener('input', () => {
    const val = barcodeInput.value.trim();
    btnClearSearch.style.display = val ? 'flex' : 'none';
    
    // Ricerca automatica in tempo reale dopo 350ms di inattività di digitazione
    clearTimeout(searchDebounceTimer);
    if (val.length >= 3) {
      searchDebounceTimer = setTimeout(() => {
        executeSearch(val, false, false);
      }, 350);
    } else if (val.length === 0) {
      searchDropdown.style.display = 'none';
    }
  });

  // Tasto lente d'ingrandimento e Tasto "Cerca"
  if (btnSearchTrigger) {
    btnSearchTrigger.addEventListener('click', () => {
      const val = barcodeInput.value.trim();
      if (val) executeSearch(val, true, true);
      else barcodeInput.focus();
    });
  }

  if (btnSubmitSearch) {
    btnSubmitSearch.addEventListener('click', () => {
      const val = barcodeInput.value.trim();
      if (val) executeSearch(val, true, true);
      else barcodeInput.focus();
    });
  }

  btnClearSearch.addEventListener('click', () => {
    barcodeInput.value = '';
    btnClearSearch.style.display = 'none';
    searchDropdown.style.display = 'none';
    clearTimeout(searchDebounceTimer);
    cancelArticleSelection();
    barcodeInput.focus();
  });

  // Chiudi dropdown al click esterno
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-section')) {
      searchDropdown.style.display = 'none';
    }
  });

  // Modifica Quantità
  qtyInput.addEventListener('input', updateDifferenceCalculation);
  btnStepMinus.addEventListener('click', () => {
    let val = parseFloat(qtyInput.value) || 0;
    if (val > 0) qtyInput.value = Math.max(0, val - 1);
    updateDifferenceCalculation();
  });
  btnStepPlus.addEventListener('click', () => {
    let val = parseFloat(qtyInput.value) || 0;
    qtyInput.value = val + 1;
    updateDifferenceCalculation();
  });

  // Chips Incremento Rapido
  document.querySelectorAll('.chip[data-add]').forEach(chip => {
    chip.addEventListener('click', () => {
      const addVal = parseFloat(chip.getAttribute('data-add')) || 0;
      const current = parseFloat(qtyInput.value) || 0;
      qtyInput.value = current + addVal;
      updateDifferenceCalculation();
    });
  });

  btnMatchStock.addEventListener('click', () => {
    if (state.currentArticle) {
      qtyInput.value = state.currentArticle.giacenza;
      updateDifferenceCalculation();
      showToast("Quantità reimpostata al valore di giacenza Plus", "info");
    }
  });

  btnResetUbi.addEventListener('click', () => {
    if (state.currentArticle) {
      ubiInput.value = state.currentArticle.ubicazione;
      showToast("Ubicazione originale ripristinata", "info");
    }
  });

  // Salvataggio
  btnSaveInventory.addEventListener('click', handleSaveInventory);
  btnCancelArticle.addEventListener('click', cancelArticleSelection);

  // Storico
  btnRefreshHistory.addEventListener('click', loadHistory);
  document.getElementById('btn-toggle-history').addEventListener('click', () => {
    document.getElementById('history-section').scrollIntoView({ behavior: 'smooth' });
  });

  // Scanner Fotocamera
  btnStartCamera.addEventListener('click', () => startCameraScanner('article'));
  if (btnSnapPhoto) btnSnapPhoto.addEventListener('click', () => triggerNativeCameraSnapshot('article'));
  if (cameraFileInput) cameraFileInput.addEventListener('change', handleCameraFileSelected);
  if (btnModalSnap) btnModalSnap.addEventListener('click', () => {
    stopCameraScanner();
    triggerNativeCameraSnapshot(state.activeCameraMode || 'article');
  });
  if (btnToggleTorch) btnToggleTorch.addEventListener('click', toggleTorch);
  if (cameraSelect) cameraSelect.addEventListener('change', (e) => {
    if (e.target.value) {
      restartCameraWithDevice(e.target.value);
    }
  });

  btnScanShelf.addEventListener('click', () => {
    if (state.lockShelfMode && state.lockedShelf) {
      showToast(`Scaffale bloccato su: ${state.lockedShelf}`, "info");
      return;
    }
    // Su mobile preferiamo native snapshot se non HTTPS, altrimenti apriamo modale
    if (isSecureCameraContext()) {
      startCameraScanner('shelf');
    } else {
      triggerNativeCameraSnapshot('shelf');
    }
  });
  btnCloseCamera.addEventListener('click', stopCameraScanner);

  // Toggles Modalità Inventario
  if (chkFastCount) {
    chkFastCount.addEventListener('change', (e) => {
      state.fastCountMode = e.target.checked;
      showToast(state.fastCountMode ? "⚡ Scan Continuo (+1) ATTIVO" : "Scan Continuo disattivato", "info");
    });
  }

  if (chkLockUbi) {
    chkLockUbi.addEventListener('change', (e) => {
      state.lockShelfMode = e.target.checked;
      if (state.lockShelfMode) {
        state.lockedShelf = ubiInput.value.trim().toUpperCase();
        if (!state.lockedShelf && state.currentArticle && state.currentArticle.ubicazione) {
          state.lockedShelf = state.currentArticle.ubicazione.toUpperCase();
        }
        if (state.lockedShelf) {
          showToast(`🔒 Scaffale BLOCCATO su: ${state.lockedShelf}`, "info");
        } else {
          showToast("🔒 Blocco attivo. Digita o scansiona lo scaffale.", "info");
        }
      } else {
        state.lockedShelf = '';
        showToast("Blocco scaffale disattivato", "info");
      }
    });
  }

  // Modale Inventario per Ubicazione
  if (btnOpenUbiInventory) {
    btnOpenUbiInventory.addEventListener('click', () => {
      ubiModal.style.display = 'flex';
      ubiSearchInput.value = state.lockedShelf || (state.currentArticle ? state.currentArticle.ubicazione : '');
      if (ubiSearchInput.value) {
        searchArticlesByLocation(ubiSearchInput.value);
      }
      ubiSearchInput.focus();
    });
  }

  if (btnCloseUbiModal) {
    btnCloseUbiModal.addEventListener('click', () => { ubiModal.style.display = 'none'; });
  }

  if (btnSearchUbi) {
    btnSearchUbi.addEventListener('click', () => {
      searchArticlesByLocation(ubiSearchInput.value.trim());
    });
  }

  if (ubiSearchInput) {
    ubiSearchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        searchArticlesByLocation(ubiSearchInput.value.trim());
      }
    });
  }

  // Filtri Storico Inventario
  document.querySelectorAll('.hist-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.hist-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const filter = pill.getAttribute('data-filter') || 'all';
      state.currentHistoryFilter = filter;
      loadHistory(filter);
    });
  });

  // Export CSV
  if (btnExportCsv) {
    btnExportCsv.addEventListener('click', () => {
      window.location.href = '/api/inventario/esporta';
    });
  }

  // QR Code
  btnQrModal.addEventListener('click', openQrModal);
  btnCloseQr.addEventListener('click', () => { qrModal.style.display = 'none'; });

  // Tema chiaro/scuro
  btnThemeToggle.addEventListener('click', () => {
    document.body.classList.toggle('light-theme');
    const isLight = document.body.classList.contains('light-theme');
    btnThemeToggle.textContent = isLight ? '☀️' : '🌙';
  });
}

// ==========================================
// RICERCA ARTICOLO
// ==========================================
async function executeSearch(query, notifyIfNotFound = true, selectFirstIfExact = false) {
  if (!query) return;

  const cleanQ = query.trim();
  if (!cleanQ) return;

  try {
    const res = await fetch(`/api/articolo?q=${encodeURIComponent(cleanQ)}`);
    const data = await res.json();

    if (!data.success || !data.results || data.results.length === 0) {
      if (notifyIfNotFound) {
        playErrorTone();
        showToast(`Nessun articolo trovato per "${cleanQ}"`, 'error');
      }
      return;
    }

    // Se c'è un solo articolo trovato, selezionalo subito aprendo la scheda di controllo
    if (data.results.length === 1) {
      searchDropdown.style.display = 'none';
      selectArticle(data.results[0]);
      return;
    }

    // Se l'utente ha premuto Invio o Cerca ed esiste una corrispondenza esatta di codice
    if (selectFirstIfExact) {
      const exactMatch = data.results.find(it => it.codice.toUpperCase() === cleanQ.toUpperCase());
      if (exactMatch) {
        searchDropdown.style.display = 'none';
        selectArticle(exactMatch);
        return;
      }
    }

    // Mostra il menu a discesa con tutti i risultati corrispondenti
    showSearchDropdown(data.results, cleanQ);
  } catch (err) {
    if (notifyIfNotFound) {
      playErrorTone();
      showToast("Errore di connessione al database locale", "error");
    }
    console.error(err);
  }
}

function showSearchDropdown(items, originalQuery = '') {
  searchDropdown.innerHTML = '';

  const header = document.createElement('div');
  header.style.cssText = 'padding: 8px 12px; background: rgba(59, 130, 246, 0.18); border-bottom: 1px solid var(--border-color); font-size: 11px; font-weight: 700; color: #93c5fd; text-transform: uppercase; letter-spacing: 0.5px;';
  header.textContent = `Trovati ${items.length} articoli per "${originalQuery}" - Tocca per aprire la scheda:`;
  searchDropdown.appendChild(header);

  items.forEach(item => {
    const el = document.createElement('div');
    el.className = 'dropdown-item';
    el.innerHTML = `
      <div class="item-top">
        <span class="item-code">${item.codice}</span>
        <span class="item-stock">Giacenza: ${item.giacenza} ${item.um}</span>
      </div>
      <div class="item-desc">${item.descrizione}</div>
      <div style="font-size: 11px; color: var(--text-dim); margin-top: 2px;">
        Ubicazione: <strong>${item.ubicazione || 'NON DEFINITA'}</strong> ${item.marca ? '• ' + item.marca : ''}
      </div>
    `;
    el.addEventListener('click', () => {
      selectArticle(item);
      searchDropdown.style.display = 'none';
    });
    searchDropdown.appendChild(el);
  });
  searchDropdown.style.display = 'block';
}

function selectArticle(item) {
  state.currentArticle = item;
  playSuccessBeep();

  // Popola dati scheda
  artBrand.textContent = item.marca || 'GENERICO';
  artCode.textContent = item.codice;
  artDesc.textContent = item.descrizione;
  artCaid.textContent = item.ca_id;
  artStock.textContent = item.giacenza;
  const dispSub = document.getElementById('art-disp-sub');
  if (dispSub) {
    const dispVal = item.disponibilita !== undefined ? item.disponibilita : item.giacenza;
    const impVal = item.impegnato || 0;
    dispSub.textContent = `Disp: ${dispVal} ${item.um} | Imp: ${impVal} ${item.um}`;
  }
  artUmLabel.textContent = item.um;
  qtyUmLabel.textContent = item.um;
  diffUmLabel.textContent = item.um;
  currentUbiLabel.textContent = item.ubicazione || 'NESSUNA';

  // Ubicazione: se c'è blocco scaffale attivo, usa quella bloccata, altrimenti l'ubicazione dell'articolo
  if (state.lockShelfMode && state.lockedShelf) {
    ubiInput.value = state.lockedShelf;
  } else {
    ubiInput.value = item.ubicazione || '';
  }
  
  // Quantità iniziale
  if (state.fastCountMode) {
    // In Fast Count (+1): incrementa di 1 la giacenza attuale o segna +1 e salva subito
    qtyInput.value = (parseFloat(item.giacenza) || 0) + 1;
  } else {
    // Di default proponiamo la giacenza attuale per verifica rapida
    qtyInput.value = item.giacenza;
  }
  notesInput.value = '';

  updateDifferenceCalculation();

  // Mostra scheda
  emptyState.style.display = 'none';
  articleCard.style.display = 'flex';

  // Se è attivo il Fast Count, effettua il salvataggio automatico immediato
  if (state.fastCountMode) {
    showToast(`⚡ Fast Count: +1 salvato per ${item.codice}`, "success");
    handleSaveInventory();
    return;
  }

  // Focus sul campo quantità per digitazione/conferma
  qtyInput.focus();
  qtyInput.select();
}

function cancelArticleSelection() {
  state.currentArticle = null;
  articleCard.style.display = 'none';
  emptyState.style.display = 'block';
  barcodeInput.value = '';
  btnClearSearch.style.display = 'none';
  searchDropdown.style.display = 'none';
  barcodeInput.focus();
}

// ==========================================
// CALCOLO DIFFERENZA GIACENZA
// ==========================================
function updateDifferenceCalculation() {
  if (!state.currentArticle) return;

  const countQty = parseFloat(qtyInput.value) || 0;
  const stockQty = state.currentArticle.giacenza;
  const diff = Math.round((countQty - stockQty) * 1000) / 1000;

  diffValue.textContent = (diff > 0 ? `+${diff}` : `${diff}`);

  diffCard.classList.remove('diff-match', 'diff-positive', 'diff-negative');

  if (diff === 0) {
    diffCard.classList.add('diff-match');
    diffStatusText.textContent = "Quantità coincidente";
  } else if (diff > 0) {
    diffCard.classList.add('diff-positive');
    diffStatusText.textContent = `Eccedenza rilevata (+${diff})`;
  } else {
    diffCard.classList.add('diff-negative');
    diffStatusText.textContent = `Ammanco rilevato (${diff})`;
  }
}

// ==========================================
// SALVATAGGIO INVENTARIO (WinCeInv)
// ==========================================
async function handleSaveInventory() {
  if (!state.currentArticle) return;

  const qty = parseFloat(qtyInput.value);
  if (isNaN(qty) || qty < 0) {
    playErrorTone();
    showToast("Inserire una quantità valida (maggiore o uguale a zero)", "error");
    return;
  }

  const payload = {
    ca_id: state.currentArticle.ca_id,
    codice_articolo: state.currentArticle.codice,
    quantita: qty,
    ubicazione: ubiInput.value.trim().toUpperCase(),
    terminale: state.terminalId,
    aggiorna_ubicazione_plus: chkSyncUbi.checked,
    note: notesInput.value.trim()
  };

  btnSaveInventory.disabled = true;
  btnSaveInventory.style.opacity = '0.6';

  try {
    const res = await fetch('/api/inventario', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (data.success) {
      playSaveSound();
      
      let msg = `Registrato su WinCeInv (RegId: ${data.reg_id})!`;
      if (data.ubicazione_modificata_su_plus) {
        msg += " Ubicazione Plus aggiornata!";
      }
      showToast(msg, "success");

      // Ricarica storico e KPI di sessione
      loadHistory(state.currentHistoryFilter);
      loadInventoryKpi();

      // Reset per il prossimo articolo
      cancelArticleSelection();
    } else {
      playErrorTone();
      showToast(`Errore salvataggio: ${data.error || 'Generico'}`, "error");
    }
  } catch (err) {
    playErrorTone();
    showToast("Errore di comunicazione durante il salvataggio", "error");
    console.error(err);
  } finally {
    btnSaveInventory.disabled = false;
    btnSaveInventory.style.opacity = '1';
  }
}

// ==========================================
// KPI DI SESSIONE INVENTARIO
// ==========================================
async function loadInventoryKpi() {
  try {
    const res = await fetch('/api/inventario/riepilogo');
    const data = await res.json();
    if (data.success && data.kpi) {
      const k = data.kpi;
      if (kpiTotalItems) kpiTotalItems.textContent = k.totale_righe_contate;
      if (kpiTotalQty) kpiTotalQty.textContent = k.totale_pezzi_rilevati;
      if (kpiDiffItems) kpiDiffItems.textContent = k.articoli_con_differenza;
      if (kpiMatchItems) kpiMatchItems.textContent = k.articoli_allineati;
    }
  } catch (err) {
    console.warn("Impossibile caricare riepilogo inventario", err);
  }
}

// ==========================================
// STORICO REGISTRAZIONI DI OGGI
// ==========================================
async function loadHistory(filter = 'all') {
  try {
    let url = '/api/storico';
    if (filter === 'diff') url += '?filtro=diff';
    if (filter === 'match') url += '?filtro=match';

    const res = await fetch(url);
    const data = await res.json();

    if (data.success && data.results) {
      state.todayCount = data.results.length;
      todayRecordsCount.textContent = state.todayCount;
      historyBadgeCount.textContent = state.todayCount;
      renderHistory(data.results);
    }
  } catch (err) {
    console.warn("Impossibile caricare storico", err);
  }
}

function renderHistory(items) {
  if (!items || items.length === 0) {
    historyList.innerHTML = `
      <div style="text-align: center; padding: 20px; color: var(--text-dim); font-size: 13px;">
        Nessun articolo registrato con il filtro selezionato.
      </div>
    `;
    return;
  }

  historyList.innerHTML = '';
  items.forEach(it => {
    const row = document.createElement('div');
    row.className = 'history-row';

    const diff = Math.round((it.quantita - it.giacenza_attuale) * 1000) / 1000;
    let diffHtml = '';
    if (diff > 0) {
      diffHtml = `<span class="hist-diff" style="color: var(--accent-emerald);">+${diff}</span>`;
    } else if (diff < 0) {
      diffHtml = `<span class="hist-diff" style="color: var(--accent-amber);">${diff}</span>`;
    } else {
      diffHtml = `<span class="hist-diff" style="color: var(--accent-cyan);">= 0</span>`;
    }

    row.innerHTML = `
      <div class="history-info">
        <div class="history-title-line">
          <span class="hist-code">${it.codice}</span>
          <span class="hist-time">${it.ora}</span>
          ${it.ubicazione ? `<span class="hist-ubi">📍 ${it.ubicazione}</span>` : ''}
        </div>
        <div class="history-desc">${it.descrizione}</div>
      </div>
      <div class="history-qty-box">
        <span class="hist-qty">${it.quantita} ${it.um}</span>
        ${diffHtml}
      </div>
      <button class="btn-del-reg" data-regid="${it.reg_id}" title="Elimina registrazione">🗑️</button>
    `;

    // Tasto elimina riga errata
    row.querySelector('.btn-del-reg').addEventListener('click', async (e) => {
      e.stopPropagation();
      if (confirm(`Vuoi annullare la registrazione di ${it.codice} (${it.quantita} ${it.um})?`)) {
        await deleteHistoryRecord(it.reg_id);
      }
    });

    historyList.appendChild(row);
  });
}

async function deleteHistoryRecord(regId) {
  try {
    const res = await fetch(`/api/inventario/${regId}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast(`Registrazione #${regId} cancellata`, "info");
      loadHistory(state.currentHistoryFilter);
      loadInventoryKpi();
    } else {
      showToast("Impossibile cancellare la registrazione", "error");
    }
  } catch (err) {
    showToast("Errore di rete durante la cancellazione", "error");
  }
}

// ==========================================
// RICERCA & CONTEGGIO PER UBICAZIONE (SCAFFALE)
// ==========================================
async function searchArticlesByLocation(ubi) {
  if (!ubi) {
    showToast("Inserire o scansionare il codice scaffale", "error");
    return;
  }

  ubiArticlesList.innerHTML = `<div style="text-align:center; padding:20px; color:var(--text-dim);">Caricamento articoli scaffale ${ubi}...</div>`;

  try {
    const res = await fetch(`/api/articoli-ubicazione?ubi=${encodeURIComponent(ubi)}`);
    const data = await res.json();

    if (!data.success || !data.results || data.results.length === 0) {
      ubiArticlesList.innerHTML = `
        <div style="text-align:center; padding:20px; color:var(--text-dim);">
          Nessun articolo censito nell'ubicazione <strong>${ubi}</strong> su Plus2000.
        </div>
      `;
      ubiResultsCount.textContent = '0';
      return;
    }

    ubiResultsCount.textContent = data.results.length;
    ubiArticlesList.innerHTML = '';

    data.results.forEach(art => {
      const row = document.createElement('div');
      row.className = 'ubi-item-row';
      row.innerHTML = `
        <div class="ubi-item-info">
          <div class="ubi-item-code">${art.codice} <span style="font-size:11px; color:var(--accent-amber); font-weight:normal;">${art.marca || ''}</span></div>
          <div class="ubi-item-desc">${art.descrizione}</div>
        </div>
        <div class="ubi-item-stock">${art.giacenza} ${art.um}</div>
        <button class="btn-ubi-count" data-cod="${art.codice}">Conta ➡️</button>
      `;

      row.querySelector('.btn-ubi-count').addEventListener('click', () => {
        ubiModal.style.display = 'none';
        executeSearch(art.codice);
      });

      ubiArticlesList.appendChild(row);
    });
  } catch (err) {
    ubiArticlesList.innerHTML = `<div style="text-align:center; padding:20px; color:var(--accent-rose);">Errore caricamento articoli scaffale</div>`;
    console.error(err);
  }
}

// ==========================================
// GESTIONE TELECAMERA SMARTPHONE & SCANNER
// ==========================================

function isSecureCameraContext() {
  return window.isSecureContext || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
}

function triggerNativeCameraSnapshot(mode = 'article') {
  state.activeCameraMode = mode;
  if (!cameraFileInput) return;
  // Reset input per consentire nuovo scatto dello stesso file
  cameraFileInput.value = '';
  cameraFileInput.click();
}

async function handleCameraFileSelected(e) {
  const file = e.target.files && e.target.files[0];
  if (!file) return;

  showToast("Elaborazione foto in corso...", "info");

  try {
    if (typeof Html5Qrcode === 'undefined') {
      showToast("Libreria di decodifica non ancora caricata", "error");
      return;
    }

    // Istanza scanner temporanea per scansione file ad alta risoluzione
    const scanner = new Html5Qrcode("qr-reader");
    try {
      const decodedText = await scanner.scanFile(file, true);
      playSuccessBeep();
      onBarcodeScanned(decodedText);
    } catch (scanErr) {
      console.warn("Primo tentativo decodifica foto non riuscito:", scanErr);
      playErrorTone();
      showToast("Barcode non rilevato. Avvicina la fotocamera e controlla che sia a fuoco.", "error");
    } finally {
      try { scanner.clear(); } catch(c){}
    }
  } catch (err) {
    console.error("Errore elaborazione foto:", err);
    showToast("Errore lettura immagine", "error");
  }
}

async function startCameraScanner(mode = 'article') {
  state.activeCameraMode = mode;

  // Se siamo su HTTP non-localhost, la telecamera live streaming è bloccata dai browser mobile
  if (!isSecureCameraContext()) {
    showToast("Su connessione HTTP mobile usa 'Scatta Foto' oppure collegati in HTTPS sulla porta 5443", "info");
    triggerNativeCameraSnapshot(mode);
    return;
  }

  cameraModal.style.display = 'flex';

  if (typeof Html5Qrcode === 'undefined') {
    showToast("Libreria fotocamera non caricata. Verifica connessione internet per il primo avvio", "error");
    return;
  }

  if (state.html5QrScanner) {
    try { await state.html5QrScanner.stop(); } catch(e){}
  }

  state.html5QrScanner = new Html5Qrcode("qr-reader");

  try {
    const devices = await Html5Qrcode.getCameras();
    if (!devices || devices.length === 0) {
      showToast("Nessuna fotocamera rilevata", "error");
      stopCameraScanner();
      return;
    }

    state.availableCameras = devices;
    if (cameraSelect) {
      cameraSelect.innerHTML = '';
      devices.forEach((dev, idx) => {
        const opt = document.createElement('option');
        opt.value = dev.id;
        opt.textContent = dev.label || `Fotocamera ${idx + 1}`;
        cameraSelect.appendChild(opt);
      });
    }

    // Cerca fotocamera posteriore (rear / back / environment)
    let selectedCameraId = devices[0].id;
    for (let i = devices.length - 1; i >= 0; i--) {
      const label = (devices[i].label || '').toLowerCase();
      if (label.includes('back') || label.includes('rear') || label.includes('posteriore') || label.includes('environment')) {
        selectedCameraId = devices[i].id;
        break;
      }
    }

    if (cameraSelect) cameraSelect.value = selectedCameraId;

    await startScannerWithDeviceId(selectedCameraId);
  } catch (err) {
    console.warn("Fallback scansione con vincolo environment:", err);
    // Fallback se getCameras fallisce
    const config = {
      fps: 20,
      qrbox: { width: 280, height: 160 },
      aspectRatio: 1.0,
      formatsToSupport: [
        Html5QrcodeSupportedFormats.EAN_13,
        Html5QrcodeSupportedFormats.EAN_8,
        Html5QrcodeSupportedFormats.CODE_128,
        Html5QrcodeSupportedFormats.CODE_39,
        Html5QrcodeSupportedFormats.UPC_A,
        Html5QrcodeSupportedFormats.UPC_E,
        Html5QrcodeSupportedFormats.QR_CODE
      ]
    };

    state.html5QrScanner.start(
      { facingMode: "environment" },
      config,
      (decodedText) => onBarcodeScanned(decodedText),
      () => {}
    ).catch(e => {
      console.error("Errore avvio fotocamera:", e);
      showToast("Impossibile avviare il video live. Prova il pulsante 'Scatta Foto'.", "error");
      stopCameraScanner();
    });
  }
}

async function startScannerWithDeviceId(deviceId) {
  const formats = [
    Html5QrcodeSupportedFormats.EAN_13,
    Html5QrcodeSupportedFormats.EAN_8,
    Html5QrcodeSupportedFormats.CODE_128,
    Html5QrcodeSupportedFormats.CODE_39,
    Html5QrcodeSupportedFormats.UPC_A,
    Html5QrcodeSupportedFormats.UPC_E,
    Html5QrcodeSupportedFormats.QR_CODE
  ];

  const config = {
    fps: 20,
    qrbox: { width: 280, height: 160 },
    aspectRatio: 1.0,
    formatsToSupport: formats,
    experimentalFeatures: {
      useBarCodeDetectorIfSupported: true
    }
  };

  try {
    await state.html5QrScanner.start(
      deviceId,
      config,
      (decodedText) => onBarcodeScanned(decodedText),
      () => {}
    );
  } catch (err) {
    console.error("Errore start scanner deviceId:", err);
    showToast("Errore avvio sensore video", "error");
  }
}

async function restartCameraWithDevice(deviceId) {
  if (state.html5QrScanner) {
    try {
      await state.html5QrScanner.stop();
      await startScannerWithDeviceId(deviceId);
    } catch (e) {
      console.error(e);
    }
  }
}

async function toggleTorch() {
  if (!state.html5QrScanner) return;
  try {
    state.currentTorchState = !state.currentTorchState;
    await state.html5QrScanner.applyVideoConstraints({
      advanced: [{ torch: state.currentTorchState }]
    });
    btnToggleTorch.textContent = state.currentTorchState ? '🔦 Accesa' : '🔦 Torcia';
  } catch (err) {
    showToast("Torcia non supportata su questo dispositivo", "info");
  }
}

function onBarcodeScanned(code) {
  const cleanCode = code.trim();
  stopCameraScanner();

  if (state.activeCameraMode === 'giro') {
    if (window.handleGiroBarcodeScan) {
      window.handleGiroBarcodeScan(cleanCode);
    }
  } else if (state.activeCameraMode === 'shelf') {
    ubiInput.value = cleanCode.toUpperCase();
    if (state.lockShelfMode) {
      state.lockedShelf = cleanCode.toUpperCase();
    }
    playSuccessBeep();
    showToast(`Ubicazione scaffale letta: ${cleanCode.toUpperCase()}`, "success");
  } else {
    barcodeInput.value = cleanCode;
    executeSearch(cleanCode);
  }
}

function stopCameraScanner() {
  if (state.html5QrScanner) {
    state.html5QrScanner.stop().then(() => {
      state.html5QrScanner.clear();
      state.html5QrScanner = null;
    }).catch(e => {
      state.html5QrScanner = null;
    });
  }
  cameraModal.style.display = 'none';
}

// ==========================================
// QR CODE MODAL & NETWORK INFO
// ==========================================
async function openQrModal() {
  qrModal.style.display = 'flex';
  try {
    const res = await fetch('/api/info');
    const data = await res.json();
    if (data.success && data.ips) {
      renderNetworkLinks(data.ips, data.port, data.https_port || 5443);
    }
  } catch (err) {
    console.warn("Info rete non disponibili", err);
  }
}

function renderNetworkLinks(ips, port, httpsPort) {
  networkLinksList.innerHTML = '';
  const mainIp = ips[0] || window.location.hostname;
  
  // URL HTTPS preferenziale per sbloccare la telecamera live su smartphone
  const httpsUrl = `https://${mainIp}:${httpsPort}`;
  const httpUrl = `http://${mainIp}:${port}`;

  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(httpsUrl)}`;
  qrCodeContainer.innerHTML = `<img src="${qrUrl}" alt="QR Code" width="200" height="200" style="display:block;">`;

  const headerNotice = document.createElement('div');
  headerNotice.style.cssText = 'font-size:12px; color:var(--text-dim); margin-bottom:8px; line-height:1.4;';
  headerNotice.innerHTML = `🔒 <strong>HTTPS consigliato per smartphone:</strong> sblocca il live video stream della fotocamera. Se compare avviso di certificato, tocca <em>Avanzate &rarr; Procedi</em>.`;
  networkLinksList.appendChild(headerNotice);

  ips.forEach(ip => {
    // Link HTTPS
    const aHttps = document.createElement('a');
    aHttps.className = 'net-link-btn';
    aHttps.href = `https://${ip}:${httpsPort}`;
    aHttps.target = '_blank';
    aHttps.innerHTML = `🔒 <span>https://${ip}:${httpsPort} (Videocamera Live)</span>`;
    networkLinksList.appendChild(aHttps);

    // Link HTTP
    const aHttp = document.createElement('a');
    aHttp.className = 'net-link-btn';
    aHttp.style.opacity = '0.75';
    aHttp.href = `http://${ip}:${port}`;
    aHttp.target = '_blank';
    aHttp.innerHTML = `🌐 <span>http://${ip}:${port} (Scatto Foto)</span>`;
    networkLinksList.appendChild(aHttp);
  });
}

// ==========================================
// STATO CONNESSIONE SQL SERVER
// ==========================================
async function checkServerStatus() {
  try {
    const res = await fetch('/api/info');
    const data = await res.json();
    if (data.success) {
      document.getElementById('sql-status').className = 'status-indicator online';
      document.getElementById('sql-status-text').textContent = `SQL Server: ${data.active_db} (${data.server_name})`;
    }
  } catch (e) {
    document.getElementById('sql-status').className = 'status-indicator';
    document.getElementById('sql-status-text').textContent = "Offline / Server non raggiungibile";
  }
}

// =============================================================================
// GESTIONE NAVIGAZIONE A SCHEDE (DESKTOP E SMARTPHONE TOUCH)
// =============================================================================

function initNavTabs() {
  const topTabs = document.querySelectorAll('.app-nav-tabs .nav-tab-btn');
  const bottomNavs = document.querySelectorAll('.mobile-bottom-nav .mobile-nav-btn');

  function handleTabClick(tabId) {
    switchTab(tabId);
  }

  topTabs.forEach(btn => {
    btn.addEventListener('click', () => handleTabClick(btn.dataset.tab));
  });

  bottomNavs.forEach(btn => {
    btn.addEventListener('click', () => handleTabClick(btn.dataset.tab));
  });
}

function switchTab(tabId) {
  // Disattiva tutte le schede e pulsanti
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.mobile-nav-btn').forEach(b => b.classList.remove('active'));

  // Attiva la scheda e pulsanti selezionati
  const targetPanel = document.getElementById(`panel-${tabId}`);
  if (targetPanel) targetPanel.classList.add('active');

  document.querySelectorAll(`.nav-tab-btn[data-tab="${tabId}"]`).forEach(b => b.classList.add('active'));
  document.querySelectorAll(`.mobile-nav-btn[data-tab="${tabId}"]`).forEach(b => b.classList.add('active'));

  // Azioni specifiche al cambio scheda
  if (tabId === 'giro-cliente') {
    if (!giroState.selectedCustomer) {
      setTimeout(() => document.getElementById('giroCustomerSearchInput')?.focus(), 200);
    } else {
      setTimeout(() => document.getElementById('giroBarcodeInput')?.focus(), 200);
    }
  } else if (tabId === 'picking') {
    if (!pickingState.orders.length) {
      loadPickingOrders(pickingState.filter);
    }
    setTimeout(() => document.getElementById('pickBarcodeInput')?.focus(), 200);
  } else if (tabId === 'scaffali') {
    setTimeout(() => document.getElementById('panel-ubi-search-input')?.focus(), 200);
  } else if (tabId === 'storico') {
    loadHistory(state.currentHistoryFilter);
  }
}

// =============================================================================
// MODULO PICKING & LAVORAZIONE ORDINI CON GIACENZA POSITIVA
// =============================================================================

const pickingState = {
  orders: [],
  filter: 'ready', // 'ready', 'positive', 'all'
  selectedDocId: null,
  selectedOrder: null,
  lines: [],
  pickedQty: {} // riga_id -> qty
};

function initPickingModule() {
  const filterPills = document.querySelectorAll('.picking-filter-row .btn-filter-pill');
  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      pickingState.filter = pill.dataset.pickFilter || 'all';
      loadPickingOrders(pickingState.filter);
    });
  });

  const selOrder = document.getElementById('selOrderToPick');
  if (selOrder) {
    selOrder.addEventListener('change', (e) => {
      const docId = parseInt(e.target.value, 10);
      if (docId) {
        onPickingOrderSelected(docId);
      } else {
        resetPickingView();
      }
    });
  }

  const btnRefresh = document.getElementById('btn-refresh-orders');
  if (btnRefresh) {
    btnRefresh.addEventListener('click', () => {
      loadPickingOrders(pickingState.filter);
      showToast('Ordini aperti aggiornati da Plus 2000', 'info');
    });
  }

  const pickBarcodeInput = document.getElementById('pickBarcodeInput');
  const btnPickBarcodeSubmit = document.getElementById('btn-pick-barcode-submit');
  if (pickBarcodeInput) {
    pickBarcodeInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handlePickingBarcodeScanned(pickBarcodeInput.value);
      }
    });
  }
  if (btnPickBarcodeSubmit) {
    btnPickBarcodeSubmit.addEventListener('click', () => {
      handlePickingBarcodeScanned(pickBarcodeInput.value);
    });
  }

  const btnPickCamera = document.getElementById('btn-pick-scan-camera');
  if (btnPickCamera) {
    btnPickCamera.addEventListener('click', () => {
      startCameraScanning('picking');
    });
  }

  const btnConfirmPicking = document.getElementById('btn-confirm-picking-done');
  if (btnConfirmPicking) {
    btnConfirmPicking.addEventListener('click', confirmPickingCompleted);
  }

  // Pre-carica ordini in background per contare i pronti
  loadPickingOrders(pickingState.filter);
}

async function loadPickingOrders(filter = 'ready') {
  const selOrder = document.getElementById('selOrderToPick');
  if (!selOrder) return;

  selOrder.innerHTML = '<option value="">Caricamento ordini aperti...</option>';

  try {
    const res = await fetch(`/api/ordini-aperti?filtro=${encodeURIComponent(filter)}`);
    const data = await res.json();
    if (!data.success) throw new Error(data.error || 'Errore lettura ordini');

    pickingState.orders = data.results || [];

    // Calcolo contatori badge ordini pronti al 100% in magazzino
    const readyOrdersCount = pickingState.orders.filter(o => o.is_ready_100).length;
    const badgeReady = document.getElementById('navBadgeReady');
    const mobileBadgeReady = document.getElementById('mobileBadgeReady');
    if (badgeReady) badgeReady.textContent = `${readyOrdersCount} Pronti`;
    if (mobileBadgeReady) mobileBadgeReady.textContent = `${readyOrdersCount}`;

    // FILTRO RIGOROSO CLIENT-SIDE (garantisce che gli ordini senza esistenza contabile come OCL 1328 non appaiano)
    let displayOrders = pickingState.orders;
    if (filter === 'ready') {
      displayOrders = pickingState.orders.filter(o => o.is_ready_100);
    } else if (filter === 'positive') {
      displayOrders = pickingState.orders.filter(o => o.is_ready_100 || o.has_positive_stock);
    }

    if (displayOrders.length === 0) {
      const msg = filter === 'ready'
        ? 'Nessun ordine pronto al 100% in magazzino'
        : (filter === 'positive' ? 'Nessun ordine con giacenza positiva a magazzino' : 'Nessun ordine aperto trovato');
      selOrder.innerHTML = `<option value="">⚪ ${msg} (su ${pickingState.orders.length} ordini aperti)</option>`;
      resetPickingView();
      return;
    }

    selOrder.innerHTML = `<option value="">-- Seleziona Ordine da Lavorare (${displayOrders.length} ordini disponibili) --</option>`;
    displayOrders.forEach(o => {
      const opt = document.createElement('option');
      opt.value = o.doc_id;

      let icon = '⚪';
      if (o.is_ready_100) icon = '🟢';
      else if (o.has_positive_stock) icon = '🟡';
      else icon = '🔴';

      const righePronto = (o.righe_complete !== undefined && o.righe_complete !== null) ? o.righe_complete : (o.righe_positive || 0);
      const righeTot = o.righe_da_prelevare || 1;
      const imp = typeof o.imponibile === 'number' ? o.imponibile.toFixed(2) : parseFloat(o.imponibile || 0).toFixed(2);

      opt.textContent = `${icon} ${o.tp_doc} ${o.numero} - ${o.cliente} (${righePronto}/${righeTot} pronti in magazzino) • € ${imp}`;
      selOrder.appendChild(opt);
    });

    // Se c'era un ordine selezionato, prova a mantenerlo
    if (pickingState.selectedDocId && pickingState.orders.some(o => o.doc_id === pickingState.selectedDocId)) {
      selOrder.value = pickingState.selectedDocId;
    } else {
      resetPickingView();
    }
  } catch (err) {
    console.error('Errore caricamento ordini:', err);
    selOrder.innerHTML = '<option value="">Errore connessione a Plus 2000</option>';
  }
}

async function onPickingOrderSelected(docId) {
  pickingState.selectedDocId = docId;
  pickingState.selectedOrder = pickingState.orders.find(o => o.doc_id === docId);

  renderPickingOrderDetail();

  const linesContainer = document.getElementById('pickingLinesList');
  linesContainer.innerHTML = '<div style="padding:20px; text-align:center; color:var(--text-muted);">Caricamento righe ordine e percorso scaffali...</div>';

  try {
    const res = await fetch(`/api/ordine-picking?doc_id=${docId}`);
    const data = await res.json();
    if (!data.success) throw new Error(data.error);

    pickingState.lines = data.results || [];
    pickingState.pickedQty = {};

    // Inizializza quantità prelevate (se articolo non disponibile, resta a 0)
    pickingState.lines.forEach(l => {
      pickingState.pickedQty[l.riga] = 0;
    });

    renderPickingLines();
    updatePickingProgress();
    document.getElementById('pickingFooterCard').style.display = 'block';
  } catch (err) {
    console.error('Errore caricamento righe ordine:', err);
    linesContainer.innerHTML = `<div style="padding:20px; color:#fb7185; text-align:center;">Errore caricamento righe: ${err.message}</div>`;
  }
}

function renderPickingOrderDetail() {
  const card = document.getElementById('pickingOrderDetailCard');
  const o = pickingState.selectedOrder;
  if (!card || !o) return;

  let badgeClass = 'attesa';
  let badgeText = o.stato_label;
  if (o.is_ready_100) badgeClass = 'pronto';
  else if (o.has_positive_stock) badgeClass = 'parziale';

  card.innerHTML = `
    <div class="order-detail-header">
      <div>
        <div class="order-detail-title">${escapeHtml(o.cliente)}</div>
        <div class="order-detail-meta">
          <span>📄 <strong>${o.tp_doc} N. ${o.numero}/${o.anno}</strong></span>
          <span>📅 Data: ${o.data}</span>
          <span>📍 Città: ${escapeHtml(o.citta || 'Non specificata')}</span>
          ${o.riferimento ? `<span>🔖 Rif: ${escapeHtml(o.riferimento)}</span>` : ''}
          <span>💶 Totale: € ${o.imponibile.toFixed(2)}</span>
        </div>
      </div>
      <div>
        <span class="badge-stock ${badgeClass}">${badgeText}</span>
      </div>
    </div>
  `;
  card.style.display = 'block';
}

function renderPickingLines() {
  const container = document.getElementById('pickingLinesList');
  if (!container) return;

  if (pickingState.lines.length === 0) {
    container.innerHTML = `
      <div class="empty-state card">
        <div class="empty-icon">✅</div>
        <h3>Tutte le righe risultano evase</h3>
        <p>Questo ordine non ha materiali rimanenti da prelevare.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = '';
  pickingState.lines.forEach(l => {
    const picked = pickingState.pickedQty[l.riga] || 0;
    const isCompleted = picked >= l.qta_da_prelevare;
    const hasShelf = l.ubicazione && l.ubicazione !== 'SENZA UBICAZIONE';

    let stockColor = 'red';
    let stockBadgeText = `0 ${l.um} (Esaurito)`;
    if (l.disponibilita >= l.qta_da_prelevare) {
      stockColor = 'green';
      stockBadgeText = `${l.disponibilita} ${l.um} Disponibili`;
    } else if (l.disponibilita > 0 || l.esistenza > 0) {
      stockColor = 'yellow';
      stockBadgeText = `${l.disponibilita} ${l.um} Disp. (Parziale)`;
    }

    const itemEl = document.createElement('div');
    itemEl.className = `picking-item ${isCompleted ? 'completed' : ''} ${!l.ha_giacenza_positiva ? 'missing' : ''}`;
    itemEl.id = `pick-row-${l.riga}`;

    itemEl.innerHTML = `
      <div class="picking-item-top">
        <div>
          <span class="picking-shelf-tag ${hasShelf ? '' : 'no-shelf'}">
            📍 ${escapeHtml(l.ubicazione)}
          </span>
          <div class="picking-code" style="margin-top:6px;">${escapeHtml(l.codice)}</div>
          <div class="picking-desc">${escapeHtml(l.descrizione)} ${l.marca ? '• ' + escapeHtml(l.marca) : ''}</div>
          ${l.ean ? `<div style="font-size:11px; font-family:var(--font-mono); color:var(--text-dim); margin-top:3px;">EAN: ${escapeHtml(l.ean)}</div>` : ''}
        </div>
        <div style="text-align:right;">
          <span class="picking-stock-available ${stockColor}">
            ${stockBadgeText}
          </span>
        </div>
      </div>

      <div class="picking-item-bottom">
        <div class="picking-qty-box">
          <span class="picking-qty-target">
            Da Prelevare: <strong>${l.qta_da_prelevare} ${l.um}</strong>
          </span>
          <span>
            Prelevati: <strong id="picked-val-${l.riga}" style="color:${isCompleted ? '#34d399' : '#38bdf8'}; font-size:15px;">${picked}</strong>
          </span>
        </div>

        <div class="picking-action-buttons">
          <button type="button" class="btn-pick-touch ${isCompleted ? 'done' : ''}" onclick="stepPickingQty(${l.riga}, 1)">
            ${isCompleted ? '✓ Completato' : '+1 Preleva'}
          </button>
          <button type="button" class="btn-subtle" style="font-size:12px; padding:6px 10px;" onclick="setAllPickingQty(${l.riga})">
            Tutto (${l.qta_da_prelevare})
          </button>
        </div>
      </div>
    `;

    container.appendChild(itemEl);
  });
}

window.stepPickingQty = function(riga, delta = 1) {
  const line = pickingState.lines.find(l => l.riga === riga);
  if (!line) return;

  const current = pickingState.pickedQty[riga] || 0;
  const next = Math.max(0, Math.min(line.qta_da_prelevare, current + delta));
  pickingState.pickedQty[riga] = next;

  const valEl = document.getElementById(`picked-val-${riga}`);
  if (valEl) valEl.textContent = next;

  const rowEl = document.getElementById(`pick-row-${riga}`);
  if (rowEl) {
    if (next >= line.qta_da_prelevare) {
      rowEl.classList.add('completed');
      playSuccessBeep();
    } else {
      rowEl.classList.remove('completed');
    }
  }

  updatePickingProgress();
};

window.setAllPickingQty = function(riga) {
  const line = pickingState.lines.find(l => l.riga === riga);
  if (!line) return;
  stepPickingQty(riga, line.qta_da_prelevare);
};

function handlePickingBarcodeScanned(barcodeTerm) {
  const clean = (barcodeTerm || '').trim().toUpperCase();
  const inputEl = document.getElementById('pickBarcodeInput');
  if (inputEl) inputEl.value = '';

  if (!clean) return;
  if (!pickingState.lines.length) {
    showToast('Seleziona prima un ordine da preparare', 'warn');
    return;
  }

  // Cerca riga corrispondente per codice articolo o EAN
  const match = pickingState.lines.find(l => 
    l.codice.toUpperCase() === clean || 
    (l.ean && l.ean.toUpperCase() === clean) ||
    clean.includes(l.codice.toUpperCase())
  );

  if (match) {
    stepPickingQty(match.riga, 1);
    showToast(`✓ Prelevato: ${match.codice} (+1)`, 'success');
    const rowEl = document.getElementById(`pick-row-${match.riga}`);
    if (rowEl) {
      rowEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      rowEl.style.transition = 'background 0.3s';
      rowEl.style.background = 'rgba(56, 189, 248, 0.25)';
      setTimeout(() => {
        rowEl.style.background = '';
      }, 700);
    }
  } else {
    playErrorTone();
    showToast(`⚠️ Articolo "${clean}" non presente in questo ordine!`, 'error');
  }
}

function updatePickingProgress() {
  const total = pickingState.lines.length;
  if (total === 0) return;

  const completed = pickingState.lines.filter(l => (pickingState.pickedQty[l.riga] || 0) >= l.qta_da_prelevare).length;
  const label = document.getElementById('pickingProgressLabel');
  if (label) label.textContent = `${completed} / ${total} articoli prelevati (${Math.round((completed / total) * 100)}%)`;

  const btnConfirm = document.getElementById('btn-confirm-picking-done');
  if (btnConfirm) {
    if (completed === total) {
      btnConfirm.style.background = '#10b981';
      btnConfirm.textContent = '✅ PRELIEVO 100% COMPLETATO — CONFERMA ORDINE';
    } else {
      btnConfirm.style.background = '';
      btnConfirm.textContent = `CONFERMA PRELIEVO (${completed}/${total} PRELEVATI)`;
    }
  }
}

async function confirmPickingCompleted() {
  if (!pickingState.selectedOrder) return;
  const total = pickingState.lines.length;
  const completed = pickingState.lines.filter(l => (pickingState.pickedQty[l.riga] || 0) >= l.qta_da_prelevare).length;

  if (completed < total) {
    if (!confirm(`Attenzione: solo ${completed} su ${total} articoli sono stati prelevati. Confermare comunque la preparazione parziale?`)) {
      return;
    }
  }

  try {
    const payload = {
      doc_id: pickingState.selectedDocId,
      operatore: state.terminalId || 'Magazziniere',
      note: `Completati ${completed}/${total} articoli`,
      righe: pickingState.lines.map(l => ({
        riga: l.riga,
        codice: l.codice,
        qta_ordinata: l.qta_da_prelevare,
        qta_prelevata: pickingState.pickedQty[l.riga] || 0
      }))
    };

    const res = await fetch('/api/ordine-picking/conferma', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!data.success) throw new Error(data.error);

    playSaveSound();
    showToast(`✅ Ordine ${pickingState.selectedOrder.numero} preparato e confermato con successo!`, 'success');
    resetPickingView();
    loadPickingOrders(pickingState.filter);
  } catch (err) {
    console.error('Errore conferma picking:', err);
    showToast(`Errore conferma: ${err.message}`, 'error');
  }
}

function resetPickingView() {
  pickingState.selectedDocId = null;
  pickingState.selectedOrder = null;
  pickingState.lines = [];
  pickingState.pickedQty = {};

  const detailCard = document.getElementById('pickingOrderDetailCard');
  if (detailCard) detailCard.style.display = 'none';

  const linesContainer = document.getElementById('pickingLinesList');
  if (linesContainer) {
    linesContainer.innerHTML = `
      <div class="empty-state card">
        <div class="empty-icon">📋</div>
        <h3>Nessun Ordine Selezionato</h3>
        <p>Scegli un ordine dal menu in alto per visualizzare il percorso prelievo ordinato per scaffale.</p>
      </div>
    `;
  }

  const footer = document.getElementById('pickingFooterCard');
  if (footer) footer.style.display = 'none';
}

// =============================================================================
// PANNELLO SCAFFALI & UBICAZIONI DEDICATO
// =============================================================================

function initShelfPanel() {
  const input = document.getElementById('panel-ubi-search-input');
  const btn = document.getElementById('panel-btn-search-ubi');
  if (!input || !btn) return;

  async function doSearch() {
    const term = (input.value || '').trim();
    if (!term) return;

    const countEl = document.getElementById('panel-ubi-results-count');
    const listEl = document.getElementById('panel-ubi-articles-list');
    listEl.innerHTML = '<div style="padding:16px; text-align:center; color:var(--text-dim);">Caricamento articoli scaffale...</div>';

    try {
      const res = await fetch(`/api/articoli-ubicazione?ubi=${encodeURIComponent(term)}`);
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      countEl.textContent = `Trovati ${data.count} articoli nello scaffale "${term}"`;
      if (data.results.length === 0) {
        listEl.innerHTML = '<div style="padding:20px; text-align:center; color:var(--text-dim);">Nessun articolo trovato per questa ubicazione.</div>';
        return;
      }

      listEl.innerHTML = '';
      data.results.forEach(it => {
        const row = document.createElement('div');
        row.className = 'ubi-item-row';
        row.innerHTML = `
          <div>
            <div class="ubi-item-code">${escapeHtml(it.codice)}</div>
            <div class="ubi-item-desc">${escapeHtml(it.descrizione)} ${it.marca ? '• ' + escapeHtml(it.marca) : ''}</div>
          </div>
          <div style="text-align:right;">
            <div class="ubi-item-stock">${it.giacenza} ${it.um}</div>
            <div style="font-size:11px; color:var(--text-dim);">Disp: ${it.disponibilita}</div>
          </div>
        `;
        row.addEventListener('click', () => {
          switchTab('inventario');
          selectArticle(it);
        });
        listEl.appendChild(row);
      });
    } catch (err) {
      listEl.innerHTML = `<div style="padding:16px; color:#fb7185; text-align:center;">Errore ricerca: ${err.message}</div>`;
    }
  }

  btn.addEventListener('click', doSearch);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      doSearch();
    }
  });
}

// =============================================================================
// MODULO GIRO CLIENTE IN MAGAZZINO & BANCO (CREAZIONE ORDINE OCL SU PLUS 2000)
// =============================================================================

const giroState = {
  selectedCustomer: null,
  cart: [],
  currentArticle: null,
  isSubmitting: false
};

function initGiroClienteModule() {
  const searchInput = document.getElementById('giroCustomerSearchInput');
  const btnSearch = document.getElementById('btnGiroSearchCustomer');
  const resultsList = document.getElementById('giroCustomerResultsList');
  const selectedSection = document.getElementById('giroCustomerSelectedCard');
  const searchWrapper = document.getElementById('giroCustomerSearchWrapper');
  const btnChangeCustomer = document.getElementById('btnGiroChangeCustomer');

  const scanSection = document.getElementById('giroScanSection');
  const barcodeInput = document.getElementById('giroBarcodeInput');
  const btnCameraScan = document.getElementById('btnGiroCameraScan');

  const previewCard = document.getElementById('giroArticlePreviewCard');
  const prevBrand = document.getElementById('giroPrevBrand');
  const prevCode = document.getElementById('giroPrevCode');
  const prevUbiBadge = document.getElementById('giroPrevUbiBadge');
  const prevDesc = document.getElementById('giroPrevDesc');
  const prevStock = document.getElementById('giroPrevStock');
  const prevUm = document.getElementById('giroPrevUm');
  const inputQty = document.getElementById('giroInputQty');
  const btnQtyMinus = document.getElementById('btnGiroQtyMinus');
  const btnQtyPlus = document.getElementById('btnGiroQtyPlus');
  const btnQty5 = document.getElementById('btnGiroQtyQuick5');
  const btnQty10 = document.getElementById('btnGiroQtyQuick10');
  const btnAddToCart = document.getElementById('btnGiroAddToCart');

  const cartList = document.getElementById('giroCartItemsList');
  const btnClearCart = document.getElementById('btnGiroClearCart');
  const orderNotesInput = document.getElementById('giroOrderNotes');
  const btnSubmitOrder = document.getElementById('btnGiroSubmitOrder');

  // Ricerca Cliente
  let debounceTimeout = null;
  async function doCustomerSearch() {
    const term = (searchInput?.value || '').trim();
    if (!term || term.length < 2) {
      if (resultsList) resultsList.style.display = 'none';
      return;
    }
    if (resultsList) {
      resultsList.innerHTML = '<div style="padding:10px; text-align:center; color:var(--text-dim); font-size:0.85rem;">Ricerca cliente in corso...</div>';
      resultsList.style.display = 'block';
    }

    try {
      const res = await fetch(`/api/clienti/cerca?q=${encodeURIComponent(term)}`);
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      if (!data.results || data.results.length === 0) {
        if (resultsList) {
          resultsList.innerHTML = `<div style="padding:10px; text-align:center; color:var(--text-dim); font-size:0.85rem;">Nessun cliente trovato per "${escapeHtml(term)}"</div>`;
        }
        return;
      }

      if (resultsList) {
        resultsList.innerHTML = '';
        data.results.forEach(c => {
          const item = document.createElement('div');
          item.className = 'giro-cust-item';
          const loc = [c.indirizzo, c.citta, c.provincia ? `(${c.provincia})` : ''].filter(Boolean).join(' ');
          const fiscal = c.partita_iva ? `P.IVA: ${c.partita_iva}` : (c.codice_fiscale ? `CF: ${c.codice_fiscale}` : '');
          item.innerHTML = `
            <strong>${escapeHtml(c.ragione_sociale)}</strong>
            <small>Cod. [${escapeHtml(c.codice)}] • ${escapeHtml(loc)} ${fiscal ? '• ' + escapeHtml(fiscal) : ''}</small>
          `;
          item.addEventListener('click', () => selectGiroCustomer(c));
          resultsList.appendChild(item);
        });
      }
    } catch (err) {
      if (resultsList) {
        resultsList.innerHTML = `<div style="padding:10px; color:#fb7185; text-align:center; font-size:0.85rem;">Errore ricerca: ${err.message}</div>`;
      }
    }
  }

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimeout);
      debounceTimeout = setTimeout(doCustomerSearch, 280);
    });
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        clearTimeout(debounceTimeout);
        doCustomerSearch();
      }
    });
  }
  if (btnSearch) btnSearch.addEventListener('click', doCustomerSearch);

  function selectGiroCustomer(c) {
    giroState.selectedCustomer = c;
    if (resultsList) resultsList.style.display = 'none';
    if (searchWrapper) searchWrapper.style.display = 'none';

    const nameEl = document.getElementById('giroActiveCustomerName');
    const detailsEl = document.getElementById('giroActiveCustomerDetails');
    if (nameEl) nameEl.textContent = c.ragione_sociale;
    const loc = [c.indirizzo, c.citta, c.provincia ? `(${c.provincia})` : ''].filter(Boolean).join(' ');
    if (detailsEl) detailsEl.textContent = `Codice: ${c.codice} • ${loc} • P.IVA: ${c.partita_iva || '-'}`;
    if (selectedSection) selectedSection.style.display = 'block';

    if (scanSection) {
      scanSection.style.opacity = '1';
      scanSection.style.pointerEvents = 'auto';
    }

    showToast(`Cliente "${c.ragione_sociale}" selezionato! Inizia il giro.`, 'success');
    playSuccessBeep();
    updateGiroCartUI();
    setTimeout(() => barcodeInput?.focus(), 200);
  }

  if (btnChangeCustomer) {
    btnChangeCustomer.addEventListener('click', () => {
      if (giroState.cart.length > 0) {
        if (!confirm('Attenzione: cambiando cliente svuoterai gli articoli nel carrello del giro attuale. Continuare?')) {
          return;
        }
      }
      giroState.selectedCustomer = null;
      giroState.cart = [];
      giroState.currentArticle = null;
      if (selectedSection) selectedSection.style.display = 'none';
      if (searchWrapper) searchWrapper.style.display = 'block';
      if (scanSection) {
        scanSection.style.opacity = '0.5';
        scanSection.style.pointerEvents = 'none';
      }
      if (previewCard) previewCard.style.display = 'none';
      updateGiroCartUI();
      setTimeout(() => searchInput?.focus(), 200);
    });
  }

  // Scansione Barcode Articolo
  async function doBarcodeSearch(term) {
    const code = (term || barcodeInput?.value || '').trim();
    if (!code) return;

    try {
      const res = await fetch(`/api/articolo?q=${encodeURIComponent(code)}`);
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      if (!data.results || data.results.length === 0) {
        playErrorTone();
        showToast(`Articolo o barcode "${code}" non trovato in Plus 2000`, 'error');
        return;
      }

      const art = data.results[0];
      giroState.currentArticle = art;

      if (prevBrand) prevBrand.textContent = art.marca || 'CLIMAWELL';
      if (prevCode) prevCode.textContent = art.codice;
      if (prevUbiBadge) prevUbiBadge.textContent = '📍 ' + (art.ubicazione ? `SCAFFALE: ${art.ubicazione}` : 'SENZA UBICAZIONE');
      if (prevDesc) prevDesc.textContent = art.descrizione || 'Nessuna descrizione';
      if (prevStock) prevStock.textContent = `${art.giacenza} ${art.um || 'PZ'}`;
      if (prevUm) prevUm.textContent = art.um || 'PZ';
      if (inputQty) inputQty.value = '1';

      if (previewCard) previewCard.style.display = 'block';
      playSuccessBeep();
      setTimeout(() => btnAddToCart?.focus(), 200);
    } catch (err) {
      playErrorTone();
      showToast(`Errore ricerca articolo: ${err.message}`, 'error');
    }
  }

  window.handleGiroBarcodeScan = function(barcode) {
    if (barcodeInput) barcodeInput.value = barcode;
    doBarcodeSearch(barcode);
  };

  if (barcodeInput) {
    barcodeInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        doBarcodeSearch();
      }
    });
  }

  if (btnCameraScan) {
    btnCameraScan.addEventListener('click', () => {
      startCameraScanner('giro');
    });
  }

  // Quantità
  if (btnQtyMinus) {
    btnQtyMinus.addEventListener('click', () => {
      let v = parseInt(inputQty.value || '1', 10);
      if (v > 1) inputQty.value = v - 1;
    });
  }
  if (btnQtyPlus) {
    btnQtyPlus.addEventListener('click', () => {
      let v = parseInt(inputQty.value || '1', 10);
      inputQty.value = v + 1;
    });
  }
  if (btnQty5) {
    btnQty5.addEventListener('click', () => {
      let v = parseInt(inputQty.value || '1', 10);
      inputQty.value = v + 5;
    });
  }
  if (btnQty10) {
    btnQty10.addEventListener('click', () => {
      let v = parseInt(inputQty.value || '1', 10);
      inputQty.value = v + 10;
    });
  }

  // Aggiungi al carrello
  if (btnAddToCart) {
    btnAddToCart.addEventListener('click', () => {
      if (!giroState.currentArticle) return;
      const art = giroState.currentArticle;
      const qty = parseInt(inputQty?.value || '1', 10);
      if (qty < 1) {
        showToast('Inserisci una quantità valida (> 0)', 'error');
        return;
      }

      const existingIndex = giroState.cart.findIndex(i => i.codice === art.codice);
      if (existingIndex >= 0) {
        giroState.cart[existingIndex].quantita += qty;
      } else {
        giroState.cart.push({
          ca_id: art.ca_id,
          codice: art.codice,
          descrizione: art.descrizione,
          marca: art.marca,
          ubicazione: art.ubicazione,
          quantita: qty,
          um: art.um || 'PZ',
          giacenza: art.giacenza
        });
      }

      playSuccessBeep();
      showToast(`Aggiunto: ${qty} x ${art.codice} al carrello giro`, 'success');

      // Reset anteprima per consentire scan immediato del prossimo articolo
      giroState.currentArticle = null;
      if (previewCard) previewCard.style.display = 'none';
      if (barcodeInput) {
        barcodeInput.value = '';
        barcodeInput.focus();
      }

      updateGiroCartUI();
    });
  }

  // Render Carrello
  function updateGiroCartUI() {
    const counterBadge = document.getElementById('giroCartCounterBadge');
    const topBadge = document.getElementById('navBadgeGiroCart');
    const mobBadge = document.getElementById('mobileBadgeGiroCart');

    const totItems = giroState.cart.length;
    const totPezzi = giroState.cart.reduce((acc, it) => acc + it.quantita, 0);

    if (counterBadge) counterBadge.textContent = `${totItems} Articoli (${totPezzi} pezzi)`;
    if (topBadge) {
      topBadge.textContent = totItems;
      topBadge.style.display = totItems > 0 ? 'inline-block' : 'none';
    }
    if (mobBadge) {
      mobBadge.textContent = totItems;
      mobBadge.style.display = totItems > 0 ? 'inline-block' : 'none';
    }

    if (btnSubmitOrder) {
      btnSubmitOrder.disabled = totItems === 0 || !giroState.selectedCustomer || giroState.isSubmitting;
    }

    if (!cartList) return;

    if (totItems === 0) {
      cartList.innerHTML = `
        <div style="text-align:center; padding:24px 12px; color:var(--text-dim); font-size:0.88rem;">
          ${giroState.selectedCustomer ? 'Carrello vuoto. Scansiona i barcode degli articoli sullo scaffale per aggiungerli.' : 'Seleziona prima il cliente per iniziare il giro magazzino.'}
        </div>
      `;
      return;
    }

    let html = '';
    giroState.cart.forEach((it, idx) => {
      html += `
        <div class="giro-cart-item-row">
          <div class="giro-cart-item-info">
            <div class="giro-cart-item-code">
              <span>${escapeHtml(it.codice)}</span>
              ${it.marca ? `<span style="font-size:0.75rem; font-weight:normal; color:var(--text-dim);">• ${escapeHtml(it.marca)}</span>` : ''}
            </div>
            <div class="giro-cart-item-desc" title="${escapeHtml(it.descrizione)}">${escapeHtml(it.descrizione)}</div>
            ${it.ubicazione ? `<span class="giro-cart-item-ubi">📍 Scaffale: ${escapeHtml(it.ubicazione)}</span>` : ''}
          </div>
          <div class="giro-cart-item-controls">
            <button type="button" class="giro-qty-btn" onclick="updateGiroCartItemQty(${idx}, ${it.quantita - 1})">-</button>
            <input type="number" class="giro-qty-input" value="${it.quantita}" min="1" onchange="updateGiroCartItemQty(${idx}, parseInt(this.value, 10))">
            <button type="button" class="giro-qty-btn" onclick="updateGiroCartItemQty(${idx}, ${it.quantita + 1})">+</button>
            <span style="font-size:0.82rem; font-weight:700; color:var(--text-dim); min-width:24px;">${it.um}</span>
            <button type="button" class="giro-item-del-btn" onclick="removeGiroCartItem(${idx})" title="Rimuovi riga">🗑️</button>
          </div>
        </div>
      `;
    });
    cartList.innerHTML = html;
  }

  window.updateGiroCartItemQty = function(idx, newQty) {
    if (newQty <= 0) {
      giroState.cart.splice(idx, 1);
    } else {
      giroState.cart[idx].quantita = newQty;
    }
    updateGiroCartUI();
  };

  window.removeGiroCartItem = function(idx) {
    giroState.cart.splice(idx, 1);
    updateGiroCartUI();
  };

  if (btnClearCart) {
    btnClearCart.addEventListener('click', () => {
      if (giroState.cart.length === 0) return;
      if (confirm('Vuoi svuotare tutti gli articoli presenti nel carrello del giro?')) {
        giroState.cart = [];
        updateGiroCartUI();
      }
    });
  }

  // Invio e Creazione Ordine Cliente OCL su Plus 2000
  if (btnSubmitOrder) {
    btnSubmitOrder.addEventListener('click', async () => {
      if (!giroState.selectedCustomer) {
        showToast('Nessun cliente selezionato', 'error');
        return;
      }
      if (giroState.cart.length === 0) {
        showToast('Il carrello è vuoto', 'error');
        return;
      }

      const c = giroState.selectedCustomer;
      const totPezzi = giroState.cart.reduce((acc, it) => acc + it.quantita, 0);

      const msgConfirm = `Confermi la creazione dell'Ordine Cliente su Plus 2000?\n\nCliente: ${c.ragione_sociale} [${c.codice}]\nArticoli: ${giroState.cart.length} (${totPezzi} pezzi totali)\n\nPlus 2000 applicherà automaticamente le condizioni commerciali e i listini del cliente.`;
      if (!confirm(msgConfirm)) return;

      giroState.isSubmitting = true;
      btnSubmitOrder.disabled = true;
      btnSubmitOrder.innerHTML = `<span>⏳</span> Creazione ordine su Plus 2000 in corso...`;

      try {
        const payload = {
          cliente_codice: c.codice,
          cliente_nome: c.ragione_sociale,
          operatore: state.terminalId || '003',
          note: (orderNotesInput?.value || '').trim() || 'Ordine Banco / Giro Magazzino con Cliente',
          righe: giroState.cart
        };

        const res = await fetch('/api/giro-cliente/crea-ordine', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        playSuccessBeep();
        alert(`🎉 ORDINE CLIENTE PLUS 2000 CREATO CON SUCCESSO!\n\nDocumento: ${data.order_display}\nCliente: ${data.cliente}\nArticoli: ${data.articoli_count} (${data.pezzi_totali} pezzi)\n\nL'ordine è registrato in Plus 2000 con sconti e listini calcolati automaticamente ed è pronto per l'evasione.`);
        showToast(`Ordine ${data.order_display} creato su Plus 2000!`, 'success');

        // Reset Carrello e Stato per il prossimo cliente
        giroState.cart = [];
        giroState.selectedCustomer = null;
        giroState.currentArticle = null;
        if (orderNotesInput) orderNotesInput.value = '';

        if (selectedSection) selectedSection.style.display = 'none';
        if (searchWrapper) searchWrapper.style.display = 'block';
        if (scanSection) {
          scanSection.style.opacity = '0.5';
          scanSection.style.pointerEvents = 'none';
        }
        if (previewCard) previewCard.style.display = 'none';

        updateGiroCartUI();
        setTimeout(() => searchInput?.focus(), 200);

      } catch (err) {
        console.error('Errore creazione ordine Plus 2000:', err);
        playErrorTone();
        alert(`Errore creazione ordine su Plus 2000:\n${err.message}`);
        showToast(`Errore: ${err.message}`, 'error');
      } finally {
        giroState.isSubmitting = false;
        btnSubmitOrder.disabled = giroState.cart.length === 0;
        btnSubmitOrder.innerHTML = `<span>🚀</span> Conferma &amp; Invia Ordine a Plus 2000 (OCL)`;
      }
    });
  }
}



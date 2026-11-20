/**
 * CLIMAWELL B2B CLIENT PORTAL - JAVASCRIPT CONTROLLER
 * Portale Ordini Riservato Clienti B2B con:
 * - Solo articoli a disponibilità positiva (stock > 0)
 * - Prezzi nascosti / riservati (visibile solo disponibilità)
 * - Indirizzo di destinazione personalizzato / Cantiere con referente e telefono
 * - Tracciamento ordini e spedizioni in tempo reale (Packlink Pro / Corrieri)
 */

(function () {
  'use strict';

  // --- STATE ---
  const B2BState = {
    customer: null,
    products: [],
    filteredProducts: [],
    cart: [],
    orders: [],
    currentTab: 'catalog', // 'catalog', 'cart', 'orders'
    deliveryType: 'sede',  // 'sede' or 'cantiere'
    searchTerm: '',
    selectedBrand: 'ALL'
  };

  const STORAGE_KEY_AUTH = 'clw_b2b_customer';
  const STORAGE_KEY_CART = 'clw_b2b_cart';

  // --- INITIALIZATION ---
  window.addEventListener('DOMContentLoaded', async () => {
    loadStoredSession();
    loadStoredCart();
    setupEventListeners();

    if (B2BState.customer) {
      showAuthenticatedUI();
      await loadCatalog();
      await loadCustomerOrders();
    } else {
      showLoginModal();
    }
  });

  // --- AUTHENTICATION & SESSION ---
  function loadStoredSession() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_AUTH);
      if (saved) {
        B2BState.customer = JSON.parse(saved);
      }
    } catch (e) {
      console.warn('Errore lettura sessione B2B:', e);
      B2BState.customer = null;
    }
  }

  function saveSession(customer) {
    B2BState.customer = customer;
    try {
      localStorage.setItem(STORAGE_KEY_AUTH, JSON.stringify(customer));
    } catch (e) {}
    showAuthenticatedUI();
  }

  window.logoutB2B = function () {
    if (confirm('Sei sicuro di voler uscire dal Portale B2B?')) {
      localStorage.removeItem(STORAGE_KEY_AUTH);
      B2BState.customer = null;
      B2BState.cart = [];
      saveCart();
      location.reload();
    }
  };

  function showAuthenticatedUI() {
    const modal = document.getElementById('loginModal');
    if (modal) modal.style.display = 'none';

    const custNameEl = document.getElementById('custHeaderName');
    const custCodeEl = document.getElementById('custHeaderCode');
    if (custNameEl) custNameEl.textContent = B2BState.customer.name || 'Cliente B2B';
    if (custCodeEl) custCodeEl.textContent = B2BState.customer.code ? `[${B2BState.customer.code}]` : '';

    // Precompila indirizzo sede aziendale
    const sedeSummaryEl = document.getElementById('destSedeSummary');
    if (sedeSummaryEl) {
      const c = B2BState.customer;
      const addr = [c.address, c.postal_code, c.city, c.province ? `(${c.province})` : ''].filter(Boolean).join(' ');
      sedeSummaryEl.textContent = addr || 'Indirizzo sede registrato su anagrafica aziendale';
    }

    updateCartUI();
  }

  function showLoginModal() {
    const modal = document.getElementById('loginModal');
    if (modal) modal.style.display = 'flex';
  }

  // --- EVENT LISTENERS ---
  function setupEventListeners() {
    // Switch tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.getAttribute('data-tab');
        switchTab(tab);
      });
    });

    // Header Cart click
    const btnHeaderCart = document.getElementById('btnHeaderCart');
    if (btnHeaderCart) {
      btnHeaderCart.addEventListener('click', () => switchTab('cart'));
    }

    // Login Form Submit
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
      loginForm.addEventListener('submit', handleLogin);
    }

    // Register Form Submit
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
      registerForm.addEventListener('submit', handleRegister);
    }

    // Search and Brand Filter
    const searchInput = document.getElementById('catalogSearch');
    if (searchInput) {
      searchInput.addEventListener('input', e => {
        B2BState.searchTerm = e.target.value.trim().toLowerCase();
        applyFilters();
      });
    }

    const brandFilter = document.getElementById('brandFilter');
    if (brandFilter) {
      brandFilter.addEventListener('change', e => {
        B2BState.selectedBrand = e.target.value;
        applyFilters();
      });
    }

    // Delivery Option Switch (Sede vs Cantiere)
    const optSede = document.getElementById('optDeliverySede');
    const optCantiere = document.getElementById('optDeliveryCantiere');
    const cantiereFields = document.getElementById('cantiereFieldsWrapper');

    if (optSede && optCantiere) {
      optSede.addEventListener('click', () => {
        B2BState.deliveryType = 'sede';
        optSede.classList.add('selected');
        optCantiere.classList.remove('selected');
        document.getElementById('radioSede').checked = true;
        if (cantiereFields) cantiereFields.style.display = 'none';
        setRequiredCantiere(false);
      });

      optCantiere.addEventListener('click', () => {
        B2BState.deliveryType = 'cantiere';
        optCantiere.classList.add('selected');
        optSede.classList.remove('selected');
        document.getElementById('radioCantiere').checked = true;
        if (cantiereFields) cantiereFields.style.display = 'block';
        setRequiredCantiere(true);
      });
    }

    // Order Submit Form
    const orderForm = document.getElementById('b2bOrderForm');
    if (orderForm) {
      orderForm.addEventListener('submit', handleOrderSubmit);
    }
  }

  function setRequiredCantiere(isRequired) {
    const reqIds = ['cantiereNome', 'cantiereIndirizzo', 'cantiereCap', 'cantiereCitta', 'cantiereReferente', 'cantiereTelefono'];
    reqIds.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.required = isRequired;
    });
  }

  window.switchTab = function (tabName) {
    B2BState.currentTab = tabName;
    document.querySelectorAll('.tab-btn').forEach(b => {
      b.classList.toggle('active', b.getAttribute('data-tab') === tabName);
    });
    document.querySelectorAll('.tab-content').forEach(c => {
      c.classList.toggle('active', c.id === `tab-${tabName}`);
    });

    if (tabName === 'orders') {
      loadCustomerOrders();
    }
  };

  // --- AUTH SWITCH & REGISTRATION HANDLER ---
  window.showAuthMode = function(mode) {
    const isLogin = mode === 'login';
    const formLogin = document.getElementById('loginForm');
    const formReg = document.getElementById('registerForm');
    const tabLogin = document.getElementById('tabAuthLogin');
    const tabReg = document.getElementById('tabAuthRegister');
    const title = document.getElementById('authModalTitle');
    const subtitle = document.getElementById('authModalSubtitle');
    const demoBox = document.getElementById('demoHelperBox');
    const errEl = document.getElementById('loginError');
    const succEl = document.getElementById('loginSuccess');

    if (errEl) errEl.style.display = 'none';
    if (succEl) succEl.style.display = 'none';

    if (tabLogin) tabLogin.classList.toggle('active', isLogin);
    if (tabReg) tabReg.classList.toggle('active', !isLogin);

    if (formLogin) formLogin.style.display = isLogin ? 'block' : 'none';
    if (formReg) formReg.style.display = !isLogin ? 'block' : 'none';
    if (demoBox) demoBox.style.display = isLogin ? 'block' : 'none';

    if (title) title.textContent = isLogin ? 'Accesso Riservato B2B' : 'Registra la Tua Azienda (B2B)';
    if (subtitle) subtitle.textContent = isLogin
      ? 'Inserisci il tuo Codice Cliente o Partita IVA per accedere al catalogo.'
      : 'Compila i dati aziendali per attivare subito l\'accesso al portale B2B.';
  };

  async function handleRegister(e) {
    e.preventDefault();
    const btn = document.getElementById('btnRegisterSubmit');
    const errEl = document.getElementById('loginError');
    const succEl = document.getElementById('loginSuccess');
    if (errEl) errEl.style.display = 'none';
    if (succEl) succEl.style.display = 'none';

    const ragSoc = (document.getElementById('regRagioneSociale')?.value || '').trim();
    const piva = (document.getElementById('regPiva')?.value || '').trim();
    const cf = (document.getElementById('regCodFiscale')?.value || '').trim() || piva;
    const indirizzo = (document.getElementById('regIndirizzo')?.value || '').trim();
    const cap = (document.getElementById('regCap')?.value || '').trim();
    const citta = (document.getElementById('regCitta')?.value || '').trim();
    const prov = (document.getElementById('regProvincia')?.value || '').trim().toUpperCase();
    const tel = (document.getElementById('regTelefono')?.value || '').trim();
    const email = (document.getElementById('regEmail')?.value || '').trim().toLowerCase();
    const password = (document.getElementById('regPassword')?.value || '').trim();

    if (!ragSoc || !piva || !indirizzo || !cap || !citta || !tel || !email || !password) {
      showLoginError('Compila tutti i campi obbligatori contrassegnati con asterisco.');
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Registrazione in corso...';

    try {
      const generatedCode = `CLI-${piva.slice(-6)}`;
      const newCust = {
        code: generatedCode,
        name: ragSoc,
        address: indirizzo,
        city: citta,
        province: prov,
        postal_code: cap,
        phone: tel,
        mobile: tel,
        email: email,
        vat_number: piva,
        tax_code: cf,
        agent_code: 'B2B_WEB',
        payment_method: 'Ri.Ba. 60 gg. f.m.'
      };

      // 1. Salva in Supabase tabella customers
      if (window.ClwData) {
        await window.ClwData.saveCustomer(newCust);

        // 2. Registra anche utente in app_users
        if (window.ClwData.createUser) {
          try {
            await window.ClwData.createUser({
              username: email,
              password: password,
              name: ragSoc,
              role: 'cliente_b2b',
              customer_code: generatedCode,
              active: true,
              can_orders: true,
              can_warehouse: false
            });
          } catch (uErr) {
            console.warn('Avviso creazione utente app_users:', uErr);
          }
        }
      }

      if (succEl) {
        succEl.innerHTML = `🎉 <strong>Registrazione completata!</strong><br>Codice Cliente Assegnato: <strong>${generatedCode}</strong><br>Accesso attivato con successo!`;
        succEl.style.display = 'block';
      }

      // Salva sessione immediata e apri il portale
      setTimeout(() => {
        saveSession(newCust);
        loadCatalog();
        loadCustomerOrders();
      }, 1200);

    } catch (err) {
      console.error('Errore registrazione cliente B2B:', err);
      showLoginError(`Errore durante la registrazione: ${err.message || 'Riprova più tardi.'}`);
    } finally {
      btn.disabled = false;
      btn.textContent = '✅ Registra & Attiva Portale B2B';
    }
  }

  // --- LOGIN HANDLER ---
  async function handleLogin(e) {
    e.preventDefault();
    const btnSubmit = document.getElementById('btnLoginSubmit');
    const errEl = document.getElementById('loginError');
    if (errEl) errEl.style.display = 'none';

    const loginId = document.getElementById('loginCustomerId').value.trim();
    const pin = document.getElementById('loginPin').value.trim();

    if (!loginId) {
      showLoginError('Inserisci il Codice Cliente, Partita IVA o Email.');
      return;
    }

    btnSubmit.disabled = true;
    btnSubmit.textContent = 'Verifica in corso...';

    try {
      // 1. Cerca in Supabase fra i clienti
      let matchedCustomer = null;

      if (window.ClwData) {
        const customers = await window.ClwData.getCustomers();
        const cleanId = loginId.toLowerCase();

        matchedCustomer = customers.find(c => {
          const code = String(c.code || '').toLowerCase();
          const piva = String(c.vat_number || '').toLowerCase();
          const cf = String(c.tax_code || '').toLowerCase();
          const email = String(c.email || '').toLowerCase();
          return code === cleanId || piva === cleanId || cf === cleanId || email === cleanId;
        });
      }

      // Se non trovato per codice preciso, prova per prefisso o ragione sociale parziale
      if (!matchedCustomer && window.ClwData) {
        const customers = await window.ClwData.getCustomers();
        const cleanId = loginId.toLowerCase();
        matchedCustomer = customers.find(c => String(c.name || '').toLowerCase().includes(cleanId));
      }

      // Se ancora non trovato (es. nuova connessione o test) crea profilo di sessione cliente
      if (!matchedCustomer) {
        matchedCustomer = {
          code: loginId.toUpperCase(),
          name: `Cliente ${loginId.toUpperCase()}`,
          address: 'Via di Consegna Predefinita',
          city: 'Firenze',
          province: 'FI',
          postal_code: '50100',
          phone: '',
          email: ''
        };
      }

      saveSession(matchedCustomer);
      await loadCatalog();
      await loadCustomerOrders();
    } catch (err) {
      console.error('Errore login B2B:', err);
      showLoginError('Errore durante l\'accesso. Riprova più tardi.');
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.textContent = 'Accedi all\'Area Riservata';
    }
  }

  function showLoginError(msg) {
    const errEl = document.getElementById('loginError');
    if (errEl) {
      errEl.textContent = msg;
      errEl.style.display = 'block';
    }
  }

  // Demo Login rapido per test immediato
  window.quickDemoLogin = function (code, name, address, city, cap, prov) {
    const demoCust = {
      code: code || 'CLI-01452',
      name: name || 'Termoidraulica Fiorentina S.r.l.',
      address: address || 'Via Baracca 142',
      city: city || 'Firenze',
      postal_code: cap || '50127',
      province: prov || 'FI',
      phone: '055-312984',
      email: 'ordini@termofiorentina.it'
    };
    saveSession(demoCust);
    loadCatalog();
    loadCustomerOrders();
  };

  // --- CATALOG & POSITIVE AVAILABILITY ONLY ---
  async function loadCatalog() {
    const grid = document.getElementById('productGrid');
    if (!grid) return;

    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-muted);">
        <div style="font-size: 2rem; margin-bottom: 12px;">⏳</div>
        Caricamento catalogo articoli in pronta consegna...
      </div>
    `;

    try {
      let prods = [];
      if (window.ClwData) {
        prods = await window.ClwData.getProducts({ forceRefresh: false });
      }

      // CRITICAL REQUIREMENT 1: Solo articoli con esistenza / disponibilità positiva (> 0)
      B2BState.products = (prods || []).filter(p => {
        const stock = Number(p.stock_qty || p.available_qty || 0);
        return stock > 0;
      });

      populateBrandFilter();
      applyFilters();
    } catch (err) {
      console.error('Errore caricamento catalogo B2B:', err);
      grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--danger);">
          ⚠️ Errore nel caricamento del catalogo. Riprova.
        </div>
      `;
    }
  }

  function populateBrandFilter() {
    const filter = document.getElementById('brandFilter');
    if (!filter) return;

    const brands = new Set();
    B2BState.products.forEach(p => {
      if (p.brand && p.brand.trim()) brands.add(p.brand.trim().toUpperCase());
    });

    const sorted = Array.from(brands).sort();
    filter.innerHTML = '<option value="ALL">Tutte le Marche</option>' +
      sorted.map(b => `<option value="${escapeHtml(b)}">${escapeHtml(b)}</option>`).join('');
  }

  function applyFilters() {
    const term = B2BState.searchTerm;
    const brand = B2BState.selectedBrand;

    B2BState.filteredProducts = B2BState.products.filter(p => {
      // Filtro marca
      if (brand !== 'ALL') {
        const pBrand = String(p.brand || '').trim().toUpperCase();
        if (pBrand !== brand) return false;
      }

      // Filtro ricerca testo
      if (term) {
        const code = String(p.code || '').toLowerCase();
        const desc = String(p.description || '').toLowerCase();
        const bar = String(p.barcode || '').toLowerCase();
        const b = String(p.brand || '').toLowerCase();
        if (!code.includes(term) && !desc.includes(term) && !bar.includes(term) && !b.includes(term)) {
          return false;
        }
      }

      return true;
    });

    renderProductGrid();
  }

  function renderProductGrid() {
    const grid = document.getElementById('productGrid');
    const countEl = document.getElementById('availableCount');
    if (!grid) return;

    if (countEl) {
      countEl.textContent = `${B2BState.filteredProducts.length} articoli disponibili`;
    }

    if (B2BState.filteredProducts.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px; background: white; border-radius: var(--radius-md); border: 1px dashed var(--border);">
          <div style="font-size: 2.5rem; margin-bottom: 12px; color: var(--text-muted);">🔍</div>
          <h3 style="color: var(--navy); margin-bottom: 6px;">Nessun articolo trovato</h3>
          <p style="color: var(--text-muted); font-size: 0.9rem;">Prova a modificare i filtri di ricerca o la marca selezionata.</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = B2BState.filteredProducts.map(p => {
      const stock = Math.round(Number(p.stock_qty || p.available_qty || 0));
      const um = (p.um || 'PZ').toUpperCase();
      const code = escapeHtml(p.code || '');
      const desc = escapeHtml(p.description || 'Articolo senza descrizione');
      const brand = escapeHtml(p.brand || 'Climawell');
      const imgUrl = p.image_url || p.image_ref || '';

      const imgHtml = imgUrl
        ? `<img src="${escapeHtml(imgUrl)}" alt="${desc}" class="product-thumb-img" loading="lazy" onerror="this.onerror=null;this.parentElement.innerHTML='<span class=\\'product-thumb-placeholder\\'>📦</span>';">`
        : `<span class="product-thumb-placeholder">📦</span>`;

      return `
        <div class="product-card" data-code="${code}">
          <div class="product-thumb-container">
            ${imgHtml}
          </div>
          <div class="product-brand-tag">${brand}</div>
          <div class="product-code">${code}</div>
          <div class="product-desc" title="${desc}">${desc}</div>
          
          <div class="product-meta-row">
            <div class="stock-indicator">
              <span>🟢</span>
              <span>Disponibilità: <strong>${stock} ${um}</strong></span>
            </div>
            <!-- CRITICAL PRICING RULE: PREZZI NASCOSTI / NO PREZZO IN EURO -->
            <div class="no-price-badge" title="Prezzi e sconti riservati applicati secondo condizioni contrattuali Plus 2000">
              🔒 Prezzo Riservato
            </div>
          </div>

          <div class="add-to-cart-row">
            <div class="qty-control">
              <button type="button" class="qty-btn" onclick="adjustProductQty('${code}', -1)">-</button>
              <input type="number" id="qty_${code}" class="qty-input" value="1" min="1" max="${stock}">
              <button type="button" class="qty-btn" onclick="adjustProductQty('${code}', 1, ${stock})">+</button>
            </div>
            <button type="button" class="btn-add-cart" onclick="addToCart('${code}')">
              <span>🛒</span> Aggiungi
            </button>
          </div>
        </div>
      `;
    }).join('');
  }

  window.adjustProductQty = function (code, delta, maxStock) {
    const input = document.getElementById(`qty_${code}`);
    if (!input) return;
    let val = parseInt(input.value || '1', 10) + delta;
    if (val < 1) val = 1;
    if (maxStock && val > maxStock) val = maxStock;
    input.value = val;
  };

  // --- CART MANAGEMENT ---
  function loadStoredCart() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_CART);
      if (saved) B2BState.cart = JSON.parse(saved);
    } catch (e) {
      B2BState.cart = [];
    }
    updateCartUI();
  }

  function saveCart() {
    try {
      localStorage.setItem(STORAGE_KEY_CART, JSON.stringify(B2BState.cart));
    } catch (e) {}
    updateCartUI();
  }

  window.addToCart = function (code) {
    const prod = B2BState.products.find(p => p.code === code);
    if (!prod) return;

    const input = document.getElementById(`qty_${code}`);
    const qty = parseInt(input ? input.value : '1', 10) || 1;
    const maxStock = Math.round(Number(prod.stock_qty || prod.available_qty || 9999));

    const existingIndex = B2BState.cart.findIndex(i => i.code === code);
    if (existingIndex >= 0) {
      const newQty = B2BState.cart[existingIndex].quantity + qty;
      if (newQty > maxStock) {
        alert(`Attenzione: La giacenza massima disponibile per ${code} è di ${maxStock} ${prod.um || 'PZ'}.`);
        B2BState.cart[existingIndex].quantity = maxStock;
      } else {
        B2BState.cart[existingIndex].quantity = newQty;
      }
    } else {
      B2BState.cart.push({
        code: prod.code,
        description: prod.description || '',
        brand: prod.brand || 'Climawell',
        um: prod.um || 'PZ',
        quantity: Math.min(qty, maxStock),
        maxStock: maxStock
      });
    }

    saveCart();

    // Visual feedback
    if (input) input.value = 1;
    showToast(`Aggiunto al carrello: ${qty} x ${code}`);
  };

  window.updateCartItemQty = function (code, newQty) {
    const item = B2BState.cart.find(i => i.code === code);
    if (!item) return;

    const q = parseInt(newQty, 10);
    if (isNaN(q) || q <= 0) {
      removeFromCart(code);
      return;
    }

    if (item.maxStock && q > item.maxStock) {
      alert(`Giacenza massima disponibile: ${item.maxStock} ${item.um}`);
      item.quantity = item.maxStock;
    } else {
      item.quantity = q;
    }

    saveCart();
  };

  window.removeFromCart = function (code) {
    B2BState.cart = B2BState.cart.filter(i => i.code !== code);
    saveCart();
  };

  function updateCartUI() {
    const totalItems = B2BState.cart.reduce((sum, i) => sum + i.quantity, 0);

    // Badges
    const badgeHeader = document.getElementById('cartBadgeCount');
    const badgeTab = document.getElementById('cartTabBadge');
    if (badgeHeader) badgeHeader.textContent = totalItems;
    if (badgeTab) badgeTab.textContent = totalItems;

    // Render cart list inside checkout
    const cartList = document.getElementById('cartItemsList');
    const emptyMsg = document.getElementById('cartEmptyMessage');
    const submitBtn = document.getElementById('btnSubmitOrder');

    if (!cartList) return;

    if (B2BState.cart.length === 0) {
      cartList.innerHTML = '';
      if (emptyMsg) emptyMsg.style.display = 'block';
      if (submitBtn) submitBtn.disabled = true;
      return;
    }

    if (emptyMsg) emptyMsg.style.display = 'none';
    if (submitBtn) submitBtn.disabled = false;

    cartList.innerHTML = B2BState.cart.map(item => `
      <div class="cart-item-row">
        <div class="cart-item-details">
          <div class="cart-item-code">${escapeHtml(item.code)} <span style="font-weight:normal; color:#64748b;">· ${escapeHtml(item.brand)}</span></div>
          <div class="cart-item-desc">${escapeHtml(item.description)}</div>
          <div class="cart-item-stock-tag">🟢 Disponibilità garantita</div>
        </div>
        <div class="cart-item-actions">
          <div class="qty-control">
            <button type="button" class="qty-btn" onclick="updateCartItemQty('${item.code}', ${item.quantity - 1})">-</button>
            <input type="number" class="qty-input" value="${item.quantity}" min="1" max="${item.maxStock}" onchange="updateCartItemQty('${item.code}', this.value)">
            <button type="button" class="qty-btn" onclick="updateCartItemQty('${item.code}', ${item.quantity + 1})">+</button>
          </div>
          <span style="font-size:0.85rem; font-weight:700; color:var(--navy); min-width:30px;">${item.um}</span>
          <button type="button" class="btn-remove-item" onclick="removeFromCart('${item.code}')" title="Rimuovi riga">🗑️</button>
        </div>
      </div>
    `).join('');
  }

  // --- ORDER SUBMISSION WITH DESTINATION ADDRESS / CANTIERE ---
  async function handleOrderSubmit(e) {
    e.preventDefault();

    if (!B2BState.customer) {
      alert('Effettua prima l\'accesso al portale B2B.');
      showLoginModal();
      return;
    }

    if (B2BState.cart.length === 0) {
      alert('Il carrello è vuoto. Aggiungi prima almeno un articolo in pronta consegna.');
      switchTab('catalog');
      return;
    }

    const submitBtn = document.getElementById('btnSubmitOrder');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>⏳</span> Invio Ordine in corso...';

    try {
      const year = new Date().getFullYear();
      const randSeq = Math.floor(1000 + Math.random() * 9000);
      const docNumber = `OCL-B2B-${year}-${randSeq}`;

      let destAddressStr = '';
      let notesStr = '';

      if (B2BState.deliveryType === 'cantiere') {
        const cNome = (document.getElementById('cantiereNome')?.value || '').trim();
        const cIndirizzo = (document.getElementById('cantiereIndirizzo')?.value || '').trim();
        const cCap = (document.getElementById('cantiereCap')?.value || '').trim();
        const cCitta = (document.getElementById('cantiereCitta')?.value || '').trim();
        const cProv = (document.getElementById('cantiereProvincia')?.value || '').trim().toUpperCase();
        const cReferente = (document.getElementById('cantiereReferente')?.value || '').trim();
        const cTelefono = (document.getElementById('cantiereTelefono')?.value || '').trim();
        const cNote = (document.getElementById('cantiereNote')?.value || '').trim();

        destAddressStr = `[CANTIERE: ${cNome}] ${cIndirizzo}, ${cCap} ${cCitta} (${cProv})`;
        notesStr = `DESTINAZIONE DIVERSA CANTIERE:\n- Cantiere: ${cNome}\n- Indirizzo: ${cIndirizzo}, ${cCap} ${cCitta} (${cProv})\n- Referente per corriere: ${cReferente}\n- Telefono per preavviso: ${cTelefono}\n- Istruzioni consegna: ${cNote || 'Nessuna'}\n(Ordine B2B da valorizzare contrattualmente su Plus 2000)`;
      } else {
        const c = B2BState.customer;
        destAddressStr = [c.address, c.postal_code, c.city, c.province ? `(${c.province})` : ''].filter(Boolean).join(' ');
        notesStr = `CONSEGNA PRESSO SEDE AZIENDALE:\n${destAddressStr}\n(Ordine B2B inserito direttamente da cliente su Portale Web - Prezzi da listino contrattuale Plus 2000)`;
      }

      // Payload Testata Documento
      const docPayload = {
        document_type: 'OCL',
        number: docNumber,
        document_date: new Date().toISOString().slice(0, 10),
        customer_code: B2BState.customer.code || '',
        customer_name: B2BState.customer.name || 'Cliente B2B',
        agent_name: 'Portale B2B Clienti',
        status: 'Inviato',
        destination_address: destAddressStr,
        notes: notesStr,
        subtotal: 0,
        vat_total: 0,
        total: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      // Payload Righe Documento
      const linesPayload = B2BState.cart.map((item, idx) => ({
        document_number: docNumber,
        line_number: idx + 1,
        product_code: item.code,
        description: item.description,
        brand: item.brand,
        um: item.um,
        quantity: item.quantity,
        net_price: 0,
        total: 0
      }));

      // Inserimento tramite Supabase Client
      if (window.ClwData && window.ClwData.getConfig().url) {
        const client = window.supabase ? window.supabase.createClient(window.ClwData.getConfig().url, window.ClwData.getConfig().key) : null;
        if (client) {
          const { error: docErr } = await client.from('documents').insert([docPayload]);
          if (docErr) throw docErr;

          const { error: lineErr } = await client.from('document_lines').insert(linesPayload);
          if (lineErr) console.warn('Avviso inserimento righe:', lineErr);
        }
      }

      // Salva anche localmente nel backup ordini cliente
      B2BState.orders.unshift({
        ...docPayload,
        lines: linesPayload
      });

      // Svuota carrello
      B2BState.cart = [];
      saveCart();

      // Mostra messaggio di successo
      alert(`🎉 Ordine inviato con successo!\n\nNumero Ordine: ${docNumber}\nDestinazione: ${destAddressStr}\n\nIl nostro ufficio commerciale e il magazzino hanno preso in carico il tuo ordine.`);

      // Vai alla scheda ordini
      switchTab('orders');
    } catch (err) {
      console.error('Errore invio ordine B2B:', err);
      alert(`⚠️ Errore durante l'invio dell'ordine: ${err.message || 'Controlla la connessione'}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<span>🚀</span> Conferma & Invia Ordine B2B';
    }
  }

  // --- ORDERS TRACKING & REAL-TIME STATUS ---
  async function loadCustomerOrders() {
    const listEl = document.getElementById('ordersListContainer');
    if (!listEl) return;

    if (!B2BState.customer) {
      listEl.innerHTML = '<div style="padding:20px; text-align:center; color:#64748b;">Effettua l\'accesso per vedere lo storico ordini.</div>';
      return;
    }

    listEl.innerHTML = '<div style="padding:40px; text-align:center; color:#64748b;">Caricamento ordini in corso...</div>';

    try {
      let customerDocs = [];

      if (window.ClwData && window.ClwData.getConfig().url) {
        const client = window.supabase ? window.supabase.createClient(window.ClwData.getConfig().url, window.ClwData.getConfig().key) : null;
        if (client) {
          const custCode = B2BState.customer.code;
          const { data, error } = await client
            .from('documents')
            .select('*')
            .in('document_type', ['OCL', 'ORD'])
            .eq('customer_code', custCode)
            .order('created_at', { ascending: false })
            .limit(50);

          if (!error && data) customerDocs = data;
        }
      }

      // Unisci con ordini creati in sessione
      const allOrders = [...B2BState.orders, ...customerDocs];
      // Deduplica per number
      const seen = new Set();
      const deduped = [];
      for (const o of allOrders) {
        if (!seen.has(o.number)) {
          seen.add(o.number);
          deduped.push(o);
        }
      }

      B2BState.orders = deduped;
      renderOrdersList();
    } catch (err) {
      console.error('Errore caricamento ordini cliente:', err);
      renderOrdersList(); // fallback render
    }
  }

  function renderOrdersList() {
    const listEl = document.getElementById('ordersListContainer');
    if (!listEl) return;

    if (B2BState.orders.length === 0) {
      listEl.innerHTML = `
        <div style="text-align: center; padding: 60px 20px;">
          <div style="font-size: 2.5rem; margin-bottom: 12px; color: var(--text-muted);">📋</div>
          <h3 style="color: var(--navy); margin-bottom: 6px;">Nessun ordine registrato</h3>
          <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 16px;">Non hai ancora inviato ordini dal portale B2B.</p>
          <button type="button" class="btn-submit-order" style="max-width: 240px; margin: 0 auto; padding: 10px;" onclick="switchTab('catalog')">
            Vai al Catalogo
          </button>
        </div>
      `;
      return;
    }

    listEl.innerHTML = B2BState.orders.map(order => {
      const num = escapeHtml(order.number || 'OCL');
      const date = order.document_date ? new Date(order.document_date).toLocaleDateString('it-IT') : (order.created_at ? new Date(order.created_at).toLocaleDateString('it-IT') : '-');
      const dest = escapeHtml(order.destination_address || 'Sede del cliente');
      const st = (order.status || 'Inviato').toLowerCase();

      // Badge status
      let badgeClass = 'inviato';
      let badgeLabel = '🟡 Inviato / Ricevuto';

      if (st.includes('prep') || st.includes('lavor')) {
        badgeClass = 'preparazione';
        badgeLabel = '🔵 In Preparazione Magazzino';
      } else if (st.includes('pront') || st === 'preparato') {
        badgeClass = 'preparato';
        badgeLabel = '🟣 Preparato / Pronto al Ritiro o Spedizione';
      } else if (st.includes('sped') || st.includes('evaso')) {
        badgeClass = 'spedito';
        badgeLabel = '🟢 Merce Spedita';
      }

      // Tracking box se spedito con Packlink o Corriere
      let trackingHtml = '';
      if (order.carrier_name || order.tracking_number || st.includes('sped')) {
        const carrier = escapeHtml(order.carrier_name || 'Corriere Espresso (Packlink Pro)');
        const trackNo = escapeHtml(order.tracking_number || 'In emissione');
        const trackUrl = getTrackingUrl(order.carrier_name, order.tracking_number);

        trackingHtml = `
          <div class="order-tracking-card">
            <div class="tracking-info">
              🚚 <strong>Spedizione con ${carrier}</strong> — Codice LdV / Tracking: <strong>${trackNo}</strong>
            </div>
            ${trackUrl ? `<a href="${trackUrl}" target="_blank" rel="noopener" class="btn-track">🔍 Traccia Spedizione in Tempo Reale</a>` : ''}
          </div>
        `;
      }

      return `
        <div class="order-card-row">
          <div class="order-card-header">
            <div>
              <span class="order-number">${num}</span>
              <span class="order-date">· Emesso il ${date}</span>
            </div>
            <span class="status-badge ${badgeClass}">${badgeLabel}</span>
          </div>

          <div class="order-dest-box">
            <div class="order-dest-title">📍 Luogo di Consegna:</div>
            <div>${dest}</div>
            ${order.notes && order.notes.includes('Referente') ? `<div style="font-size:0.8rem; color:#475569; margin-top:2px;">${escapeHtml(order.notes.split('\n')[0])}</div>` : ''}
          </div>

          ${trackingHtml}
        </div>
      `;
    }).join('');
  }

  function getTrackingUrl(carrier, tracking) {
    if (!tracking || tracking === 'In emissione') return null;
    const c = String(carrier || '').toLowerCase();
    const t = encodeURIComponent(String(tracking).trim());

    if (c.includes('gls')) return `https://www.gls-italy.com/?tracking=${t}`;
    if (c.includes('brt') || c.includes('bartolini')) return `https://www.brt.it/it/tracking?n_sped=${t}`;
    if (c.includes('tnt')) return `https://www.tnt.it/tracking/Tracking.do?searchType=0&cons=${t}`;
    if (c.includes('poste') || c.includes('sda')) return `https://www.poste.it/cerca/index.html#/risultati-spedizioni/${t}`;
    if (c.includes('packlink')) return `https://tracking.packlink.com/it/tracking/${t}`;

    return `https://www.google.com/search?q=tracking+${t}`;
  }

  // Helper Toast notification
  function showToast(msg) {
    let toast = document.getElementById('b2bToast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'b2bToast';
      toast.style.cssText = 'position:fixed; bottom:24px; right:24px; background:#0b2942; color:#ffffff; padding:12px 20px; border-radius:8px; box-shadow:0 6px 20px rgba(0,0,0,0.25); z-index:3000; font-size:0.9rem; font-weight:600; transition:all 0.3s; border-left:4px solid #10b981;';
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
    }, 2800);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

})();


/**
 * CLIMAWELL E-COM — Modulo Logico Vetrina Top 10, Carrello Multi-Prodotto,
 * Regole Pagamento B2B (Ri.Ba. 60-90gg) vs Privati, Sconto Extra Immediato & Social Studio.
 */

(function () {
  'use strict';

  const STORAGE_KEY_TOP10 = 'clw_ecom_top10_bf_v3';
  const STORAGE_KEY_CART = 'clw_ecom_cart_v1';
  const STORAGE_KEY_PAY_RULES = 'clw_ecom_payment_rules_v1';

  // Configurazione Ufficiale Articoli Black Friday Core Equipment & Climawell Store (-50%)
  const DEFAULT_TOP10_CONFIG = [
    {
      code: 'COR03015010',
      coreCode: '03015010BF',
      model: 'PVDSA2L-A3-169LM',
      seoTitle: 'Pompa per Vuoto Doppio Stadio 169 L/Min (PVDSA2L-A3-169LM)',
      seoDescription: 'Pompa professionale per alto vuoto doppio stadio da 169 L/min con elettrovalvola e vacuometro. Ideale per impianti R32, R410A, R134a.',
      highlights: ['Portata elevata 169 L/min a doppio stadio', 'Elettrovalvola di sicurezza e vacuometro di precisione', 'Garanzia Ufficiale Core Equipment'],
      badge: '🖤 -50% BLACK FRIDAY',
      brand: 'CORE EQUIPMENT',
      family: 'ATTREZZATURA',
      price: 310.28,
      listPrice: 620.55,
      stock: 5,
      minQty: 1,
      imageUrl: 'https://www.core-equipment.it/4863-large_default/pompa-per-vuoto-doppiostadio-vpea-71-dev-71-ltmin.jpg'
    },
    {
      code: 'COR03014010',
      coreCode: '03014010BF',
      model: 'VP-42-DEV',
      seoTitle: 'Pompa per Vuoto Monostadio 42 L/Min (VP-42-DEV)',
      seoDescription: 'Pompa per vuoto compatta monostadio 42 L/min per installazione e manutenzione climatizzatori e piccoli impianti refrigeranti.',
      highlights: ['Leggera e portatile per cantieri e manutenzioni', 'Valvola di non ritorno olio integrata', 'Design robusto con impugnatura termoisolata'],
      badge: '🖤 -50% BLACK FRIDAY',
      brand: 'CORE EQUIPMENT',
      family: 'ATTREZZATURA',
      price: 86.33,
      listPrice: 172.66,
      stock: 8,
      minQty: 1,
      imageUrl: 'https://www.core-equipment.it/4858-large_default/pompa-per-vuoto-monostadio-vp-100-dev-100-ltmin.jpg'
    },
    {
      code: 'COR03014030',
      coreCode: '03014030BF',
      model: 'VP-100-DEV',
      seoTitle: 'Pompa per Vuoto Monostadio 100 L/Min (VP-100-DEV)',
      seoDescription: 'Pompa per vuoto monostadio ad alta efficienza 100 L/min (3,5 CFM) per impianti split e multisplit.',
      highlights: ['Portata 100 L/min per vuoto rapido', 'Corpo motore alettato in alluminio pressofuso', 'Connessione standard 1/4 SAE'],
      badge: '🖤 -50% BLACK FRIDAY',
      brand: 'CORE EQUIPMENT',
      family: 'ATTREZZATURA',
      price: 123.30,
      listPrice: 246.59,
      stock: 6,
      minQty: 1,
      imageUrl: 'https://www.core-equipment.it/4858-large_default/pompa-per-vuoto-monostadio-vp-100-dev-100-ltmin.jpg'
    },
    {
      code: 'COR03001080',
      coreCode: '03001080V32BF',
      model: '245SV-32',
      seoTitle: 'Pompa Doppio Stadio 128 L/Min Specifica Gas R32 (245SV-32)',
      seoDescription: 'Pompa per alto vuoto doppio stadio da 128 L/min a norme ATEX per gas infiammabili R32 e R1234yf con solenoide e vacuometro.',
      highlights: ['Certificata per gas infiammabili A2L (R32 / R1234yf)', 'Vuoto finale fino a 15 micron', 'Valvola solenoide automatica antisvuotamento'],
      badge: '🖤 -50% BLACK FRIDAY',
      brand: 'CORE EQUIPMENT',
      family: 'ATTREZZATURA',
      price: 209.37,
      listPrice: 418.74,
      stock: 6,
      minQty: 1,
      imageUrl: 'https://www.core-equipment.it/4869-large_default/pompa-per-vuoto-doppiostadio-vpea-71-dev-71-ltmin.jpg'
    },
    {
      code: 'COR01004010',
      coreCode: '01004010BF',
      model: 'KITAZOTO50',
      seoTitle: 'Kit Pressurizzazione Impianti ad Azoto 50 Bar in Valigetta (KITAZOTO50)',
      seoDescription: 'Kit completo professionale per prove di tenuta, ricerca fughe e pressurizzazione impianti di condizionamento fino a 50 bar.',
      highlights: ['Valigetta rigida antiurto con riduttore di pressione', 'Tubo flessibile ad altissima pressione 50 bar', 'Manometro certificato per prova tenuta a norme F-Gas'],
      badge: '🖤 -50% BLACK FRIDAY',
      brand: 'CORE EQUIPMENT',
      family: 'ATTREZZATURA',
      price: 205.54,
      listPrice: 411.08,
      stock: 5,
      minQty: 1,
      imageUrl: 'https://www.core-equipment.it/4255-large_default/kitazoto50-kit-pressurizzazione-impianti-esclusa-bombola-azoto.jpg'
    },
    {
      code: 'COR31006065',
      coreCode: '31006065BF',
      model: 'KLAR',
      seoTitle: 'Kit Lavaggio Tubazioni Frigorifere con Raccordi in Valigia (KLAR)',
      seoDescription: 'Sistema di lavaggio e bonifica linee frigorifere con serbatoio pressurizzabile, pistola di erogazione e raccordi universali in valigetta.',
      highlights: ['Indispensabile per sostituzione compressori e retrofit R32', 'Pistola di lavaggio dosatrice con serbatoio 1 Litro', 'Raccordi a cono in gomma per tutte le sezioni di tubo'],
      badge: '🖤 -50% BLACK FRIDAY',
      brand: 'CORE EQUIPMENT',
      family: 'ATTREZZATURA',
      price: 97.01,
      listPrice: 194.01,
      stock: 7,
      minQty: 1,
      imageUrl: 'https://www.core-equipment.it/4264-large_default/klar-kit-lavaggio-con-raccordi-in-valigia.jpg'
    },
    {
      code: 'COR01006000',
      coreCode: '01006000BF',
      model: 'RPA50',
      seoTitle: 'Riduttore di Pressione Azoto 50 Bar con Valvola di Sicurezza (RPA50)',
      seoDescription: 'Riduttore di pressione professionale per bombole azoto fino a 50 bar con doppia scala manometrica e valvola di scarico sovrapressione.',
      highlights: ['Corpo robusto in ottone forgiato', 'Manometro protetto da gomma antiurto', 'Connessione standard bombola UNI 11144'],
      badge: '🖤 -50% BLACK FRIDAY',
      brand: 'CORE EQUIPMENT',
      family: 'ATTREZZATURA',
      price: 117.50,
      listPrice: 235.00,
      stock: 6,
      minQty: 1,
      imageUrl: 'https://www.core-equipment.it/4250-large_default/rpa50-riduttore-press-azoto-50-bar-con-valv-sic.jpg'
    },
    {
      code: 'COR31006052',
      coreCode: '31006052BF',
      model: 'STI-1000',
      seoTitle: 'Liquido Lavaggio Interno Circuiti Frigoriferi 1 Lt (STI-1000)',
      seoDescription: 'Fluido chimico ad alta evaporazione per la pulizia e sgrassaggio delle tubazioni interne negli impianti di climatizzazione.',
      highlights: ['Non lascia residui oleosi nelle tubazioni', 'Compatibile con tutti i gas refrigeranti e oli POE/PAG', 'Confezione promozionale (Ordine minimo 12 pz)'],
      badge: '🖤 -50% • MIN 12 PZ',
      brand: 'CORE EQUIPMENT',
      family: 'LAVAGGIO',
      price: 7.08,
      listPrice: 14.16,
      stock: 48,
      minQty: 12,
      imageUrl: 'https://www.core-equipment.it/4700-large_default/detergenti-e-accessori-sti-1000-lattina-da-1-lt.jpg'
    },
    {
      code: 'COR31006053',
      coreCode: '31006053BF',
      model: 'SLI',
      seoTitle: 'Spray Lavaggio Tubazioni Interne Condizionamento (SLI)',
      seoDescription: 'Bombola spray aerosol pressurizzata con cono in gomma per lavaggio rapido e bonifica di linee split e monosplit.',
      highlights: ['Pronto all\'uso senza ausilio di serbatoi esterni', 'Pressione di spinta costante per rimuovere residui di fuliggine', 'Confezione promozionale (Ordine minimo 12 pz)'],
      badge: '🖤 -50% • MIN 12 PZ',
      brand: 'CORE EQUIPMENT',
      family: 'LAVAGGIO',
      price: 7.65,
      listPrice: 15.29,
      stock: 60,
      minQty: 12,
      imageUrl: 'https://www.core-equipment.it/4774-large_default/detergenti-e-accessori-sli-spray-lavaggio-tubazioni-interne.jpg'
    },
    {
      code: 'COR31006010',
      coreCode: '31006010BF',
      model: 'SSE',
      seoTitle: 'Igienizzante Sanificante Climatizzatori Spray 400 ml (SSE)',
      seoDescription: 'Trattamento igienizzante antibatterico profumato per filtri, batterie alettate e canali di condizionamento.',
      highlights: ['Azione battericida e fungicida certificata', 'Gradevole profumazione rinfrescante a lunga durata', 'Confezione promozionale (Ordine minimo 12 pz)'],
      badge: '🖤 -50% • MIN 12 PZ',
      brand: 'CORE EQUIPMENT',
      family: 'LAVAGGIO',
      price: 4.39,
      listPrice: 8.77,
      stock: 72,
      minQty: 12,
      imageUrl: 'https://www.core-equipment.it/4267-large_default/sse-igienizzante-400-cc.jpg'
    },
    {
      code: 'COR31006020',
      coreCode: '31006020BF',
      model: 'POWERCLEAN-SCC',
      seoTitle: 'Detergente Schiumogeno per Superfici Esterne 400 ml (POWERCLEAN-SCC)',
      seoDescription: 'Schiuma detergente attiva per pulizia profonda di unità esterne, motocondensanti e carcasse da smog e grasso.',
      highlights: ['Schiuma sgrassante ad alta aderenza', 'Non intacca le alette in alluminio e le plastiche', 'Confezione promozionale (Ordine minimo 12 pz)'],
      badge: '🖤 -50% • MIN 12 PZ',
      brand: 'CORE EQUIPMENT',
      family: 'LAVAGGIO',
      price: 6.85,
      listPrice: 13.69,
      stock: 48,
      minQty: 12,
      imageUrl: 'https://www.core-equipment.it/4266-large_default/powerclean-scc-detergente-spray-400-ml-per-superfici-esterne.jpg'
    },
    {
      code: 'COR29025013',
      coreCode: '29025013BF',
      model: 'BE120/5',
      seoTitle: 'Bilancia Elettronica Digitale di Carica 120 Kg con Valigia (BE120/5)',
      seoDescription: 'Bilancia elettronica professionale da 120 Kg con risoluzione di precisione a 5 grammi per carica refrigeranti R32/R410A.',
      highlights: ['Portata 120 Kg con precisione 5g', 'Piatto antiscivolo con display LCD retroilluminato estraibile', 'Fornita con valigetta antiurto rinforzata'],
      badge: '🖤 -50% BLACK FRIDAY',
      brand: 'CORE EQUIPMENT',
      family: 'ATTREZZATURA',
      price: 139.87,
      listPrice: 279.73,
      stock: 6,
      minQty: 1,
      imageUrl: 'https://www.core-equipment.it/3631-large_default/be120-5-kg-120-risoluzione-5-grammi-con-valigia.jpg'
    },
    {
      code: 'COR21040980',
      coreCode: '21040980BF',
      model: 'FLBD',
      seoTitle: 'Flangiatubo a Crick Eccentrico in Pollici per Rame (FLBD)',
      seoDescription: 'Cartellatrice eccentrica professionale con frizione per tubi in rame da 1/4" a 3/4" specifica per cartelle ad alta tenuta R32.',
      highlights: ['Cono eccentrico temprato per cartelle lisce e senza solchi', 'Meccanismo a scatto/cricchetto con frizione dinamometrica', 'Dima universale 1/4 - 5/16 - 3/8 - 1/2 - 5/8 - 3/4'],
      badge: '🖤 -50% BLACK FRIDAY',
      brand: 'CORE EQUIPMENT',
      family: 'ATTREZZATURA',
      price: 127.54,
      listPrice: 255.07,
      stock: 8,
      minQty: 1,
      imageUrl: 'https://www.core-equipment.it/4442-large_default/flbg-flangiatubo-a-crick-alta-qualita-in-pollici-1-4-3-8-1-2-5-8-3-4.jpg'
    },
    {
      code: 'COR21017014',
      coreCode: '21017014BF',
      model: 'CHDINPROF',
      seoTitle: 'Set Chiavi Dinamometriche Professionali in Valigetta (CHDINPROF)',
      seoDescription: 'Kit chiavi dinamometriche a forchetta intercambiabile con coppia di serraggio tarabile da 10 a 75 Nm per raccordi flare.',
      highlights: ['Coppia di serraggio regolabile con certificato di taratura', 'Misure forchette: 17, 22, 24, 26, 27, 29 mm', 'Conforme alle norme di installazione a tenuta F-Gas'],
      badge: '🖤 -50% BLACK FRIDAY',
      brand: 'CORE EQUIPMENT',
      family: 'ATTREZZATURA',
      price: 229.82,
      listPrice: 459.64,
      stock: 4,
      minQty: 1,
      imageUrl: 'https://www.core-equipment.it/3814-large_default/chdinprof-chiavi-dinamometriche-professionali-coppia-di-serraggio-19-110-nm.jpg'
    },
    {
      code: 'COR21002000',
      coreCode: '21002000NBF',
      model: 'SLIM',
      seoTitle: 'Flangiatubo Elettrico a Batteria al Litio per Cartelle (SLIM)',
      seoDescription: 'Flangiatubo a pistola automatico a batteria al litio per cartellare tubi di rame in soli 5 secondi senza sforzo manuale.',
      highlights: ['Cartelle automatiche perfette in 5 secondi', 'Batteria al litio ad alta autonomia con caricatore rapido', 'Fornito in valigetta con dime millimetriche e in pollici'],
      badge: '🖤 -50% BLACK FRIDAY',
      brand: 'CORE EQUIPMENT',
      family: 'ATTREZZATURA',
      price: 251.99,
      listPrice: 503.98,
      stock: 5,
      minQty: 1,
      imageUrl: 'https://www.core-equipment.it/4795-large_default/flbgm-flangiatubo-a-crick-alta-qualita-in-mm-6-8-10-12-15-16-18.jpg'
    },
    {
      code: 'COR25003011',
      coreCode: '25003011BF',
      model: 'TURBOSET90',
      seoTitle: 'Stazione Saldante Autogena Compatta OXYTURBO (TURBOSET90)',
      seoDescription: 'Postazione portatile di saldatura e brasatura autogena completa di bombole ossigeno/gas, riduttori, tubi e impugnatura con punte.',
      highlights: ['Temperatura fiamma fino a 3100°C per brasatura rame-rame', 'Leggera, maneggevole e sicura con valvole antiritorno', 'Prodotto originale Oxyturbo ideale per frigoristi'],
      badge: '🖤 -50% BLACK FRIDAY',
      brand: 'CORE EQUIPMENT',
      family: 'ATTREZZATURA',
      price: 130.00,
      listPrice: 260.00,
      stock: 6,
      minQty: 1,
      imageUrl: 'https://www.core-equipment.it/3924-large_default/turboset90-stazione-saldante-oxyturbo-originale.jpg'
    }
  ];

  // Regole Pagamento Predefinite (B2B Ri.Ba. 60-90gg vs Privati Obbligo Anticipato + Sconto Extra)
  const DEFAULT_PAYMENT_RULES = {
    extraDiscountCardPct: 4.0,
    extraDiscountBankPct: 4.0, // Sconto Extra 4% applicato su Bonifico Bancario Anticipato
    standardShippingCost: 6.99, // Costo trasporto corriere standard (modificabile dall'Amministratore)
    companyIban: 'IT60 X054 2811 1010 0000 0123 456',
    b2cAllowCard: false, // Disabilitato nella fase operativa: evita pagamenti test fittizi
    b2cAllowPrepaidBank: true,
    b2cAllowAssisted: true,
    b2bAccessMode: 'ALL_PIVA', // 'ALL_PIVA' oppure 'WHITELIST_ONLY'
    b2bTermRiba30: true,
    b2bTermRiba60: true,
    b2bTermRiba6090: true,
    b2bTermBonifico30: true,
    b2bWhitelist: 'BECHINI ALESSIO\nANGIOLILLO PAOLO\n01234567890\nCLIMAWELL PARTNER'
  };

  // Stato interno del modulo E-COM
  const EcomState = {
    products: [],
    filtered: [],
    top10Config: [],
    cart: [], // Array di { code, qty }
    paymentRules: { ...DEFAULT_PAYMENT_RULES },
    buyerType: 'B2B', // 'B2B' (Azienda P.IVA) oppure 'B2C' (Privato C.F.)
    priceMode: 'B2B', // 'B2B' (Prezzi netti + IVA) oppure 'B2C' (Prezzi IVA 22% inclusa)
    activePaymentTab: 'prepaid_bank', // Default su Bonifico Bancario Anticipato (100% operativo e sicuro)
    currentCategory: 'TOP10',
    brandFilter: 'ALL',
    priceFilter: 'ALL',
    sortBy: 'FEATURED',
    searchQuery: '',
    selectedProduct: null,
    context: {
      agentCode: '1136',
      clientCode: null,
      clientEmail: null,
      promoArticle: null,
      preloadCartParam: null,
      campaignId: null
    },
    stripeConfig: {
      publishableKey: 'pk_test_51P7DemoSaaSDanieleLupi00000000000000',
      connectedAccountId: 'acct_climawell_b2b',
      applicationFeePercent: 2.5
    }
  };

  // Directory Consulenti Commerciali e Tecnici Climawell
  const KNOWN_AGENTS = {
    '1136': {
      code: '1136',
      name: 'Daniele Lupi',
      role: 'Consulente Tecnico Senior',
      zone: 'Firenze & Toscana',
      phone: '388 1299371',
      telHref: 'tel:3881299371',
      waNumber: '393881299371',
      initials: 'DL'
    }
  };

  // Inizializzazione al caricamento del DOM
  document.addEventListener('DOMContentLoaded', async () => {
    loadSavedTop10Config();
    loadSavedPaymentRules();
    loadSavedCart();
    parseUrlContext();
    setupEventListeners();
    await loadCatalog();
    applyPaymentRulesToUiBanners();
    checkPromoOrCartHighlight();
    updateCartIndicators();
    updateSeoStructuredDataAndMeta();
  });

  // 0. Caricamento Configurazioni (Top 10, Regole Pagamento, Carrello)
  function loadSavedTop10Config() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_TOP10);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          EcomState.top10Config = parsed.slice(0, 24);
          return;
        }
      }
    } catch (e) {}
    EcomState.top10Config = JSON.parse(JSON.stringify(DEFAULT_TOP10_CONFIG));
  }

  function saveTop10ConfigToStorage() {
    try {
      localStorage.setItem(STORAGE_KEY_TOP10, JSON.stringify(EcomState.top10Config.slice(0, 24)));
    } catch (e) {}
  }

  function loadSavedPaymentRules() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_PAY_RULES);
      if (saved) {
        const parsed = JSON.parse(saved);
        EcomState.paymentRules = { ...DEFAULT_PAYMENT_RULES, ...parsed };
        return;
      }
    } catch (e) {}
    EcomState.paymentRules = { ...DEFAULT_PAYMENT_RULES };
  }

  function savePaymentRulesToStorage() {
    try {
      localStorage.setItem(STORAGE_KEY_PAY_RULES, JSON.stringify(EcomState.paymentRules));
    } catch (e) {}
  }

  function loadSavedCart() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_CART);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          EcomState.cart = parsed.filter(x => x && x.code && Number(x.qty) > 0);
        }
      }
    } catch (e) {
      EcomState.cart = [];
    }
  }

  function saveCartToStorage() {
    try {
      localStorage.setItem(STORAGE_KEY_CART, JSON.stringify(EcomState.cart));
    } catch (e) {}
  }

  // 1. Lettura parametri URL (?prodotto= / ?cart=COD1:2,COD2:1 / ?agente= / ?client=)
  function parseUrlContext() {
    const params = new URLSearchParams(window.location.search);

    const agentFromUrl = params.get('agente') || params.get('agent');
    if (agentFromUrl) {
      EcomState.context.agentCode = agentFromUrl.trim();
      try { localStorage.setItem('clw_agent_code', EcomState.context.agentCode); } catch (e) {}
    } else if (localStorage.getItem('clw_agent_code')) {
      EcomState.context.agentCode = localStorage.getItem('clw_agent_code');
    }

    // Modalità Prezzi B2B o B2C
    const savedPriceMode = localStorage.getItem('clw_price_mode');
    if (savedPriceMode === 'B2C' || savedPriceMode === 'B2B') {
      EcomState.priceMode = savedPriceMode;
    }
    const btnB2B = document.getElementById('btnPriceModeB2B');
    const btnB2C = document.getElementById('btnPriceModeB2C');
    if (btnB2B) btnB2B.classList.toggle('active', EcomState.priceMode === 'B2B');
    if (btnB2C) btnB2C.classList.toggle('active', EcomState.priceMode === 'B2C');

    EcomState.context.clientCode = params.get('client') || params.get('cliente') || null;
    EcomState.context.clientEmail = params.get('email') || null;
    EcomState.context.promoArticle = params.get('prodotto') || params.get('art') || params.get('sku') || null;
    EcomState.context.preloadCartParam = params.get('cart') || params.get('bundle') || null;
    EcomState.context.campaignId = params.get('campaign') || null;

    // Risoluzione Scheda Consulente Assegnato
    const ag = KNOWN_AGENTS[EcomState.context.agentCode] || {
      code: EcomState.context.agentCode,
      name: `Agente Climawell (${EcomState.context.agentCode})`,
      role: 'Consulente Commerciale & Tecnico',
      zone: 'Firenze & Toscana',
      phone: '388 1299371',
      telHref: 'tel:3881299371',
      waNumber: '393881299371',
      initials: 'CL'
    };

    const nameEl = document.getElementById('agentNameDisplay');
    if (nameEl) nameEl.textContent = ag.name;

    const avatarEl = document.querySelector('.agent-avatar');
    if (avatarEl) avatarEl.textContent = ag.initials;

    const agentLabel = document.getElementById('agentContextLabel');
    if (agentLabel) {
      agentLabel.innerHTML = `Rif. Agente: <strong>${escapeHtml(ag.code)}</strong> &bull; Zona ${escapeHtml(ag.zone)}`;
    }

    const waLink = document.getElementById('agentWaLink');
    if (waLink) {
      const waMsg = `Salve ${ag.name}, ti contatto dallo Store Climawell per richiedere consulenza e disponibilità su un articolo.`;
      waLink.href = `https://wa.me/${ag.waNumber}?text=${encodeURIComponent(waMsg)}`;
      const waSpan = waLink.querySelector('span');
      if (waSpan) waSpan.textContent = `Chiedi a ${ag.name.split(' ')[0]}`;
    }

    const telLink = document.getElementById('agentTelLink');
    if (telLink) {
      telLink.href = ag.telHref;
      const telSpan = telLink.querySelector('span');
      if (telSpan) telSpan.textContent = ag.phone;
    }

    const clientLabel = document.getElementById('clientContextLabel');
    if (clientLabel && (EcomState.context.clientCode || EcomState.context.clientEmail)) {
      clientLabel.style.display = 'inline-block';
      clientLabel.textContent = `Cliente: ${EcomState.context.clientCode || EcomState.context.clientEmail}`;
    }

    const agentInput = document.getElementById('orderAgentInput');
    if (agentInput) agentInput.value = EcomState.context.agentCode;

    if (EcomState.context.clientCode) {
      const custInput = document.getElementById('orderCustomerInput');
      if (custInput) custInput.value = EcomState.context.clientCode;
    }
  }

  // 2. Caricamento Catalogo da Supabase / Seed + Fusione con Top 10 Vetrina
  async function loadCatalog() {
    try {
      let rawProducts = [];

      if (window.ClwData && typeof window.ClwData.getProducts === 'function') {
        rawProducts = await window.ClwData.getProducts({ limit: 1000 });
      }

      if (!rawProducts || rawProducts.length === 0) {
        const res = await fetch('/seed-data.json').catch(() => null);
        if (res && res.ok) {
          const seed = await res.json();
          rawProducts = seed.products || seed.articoli || [];
        }
      }

      const normalizedDb = normalizeCatalog(rawProducts || []);
      EcomState.products = mergeTop10WithCatalog(normalizedDb);
      populateBrandFilter();
      applyFilters();
    } catch (err) {
      console.warn('[E-COM] Uso catalogo Top 10 curato:', err);
      EcomState.products = mergeTop10WithCatalog([]);
      populateBrandFilter();
      applyFilters();
    }
  }

  function normalizeCatalog(list) {
    return list.map(p => {
      const code = String(p.code || p.codice || p.id || '').trim();
      const rawDesc = String(p.description || p.descrizione || p.name || 'Articolo Tecnico Climawell').trim();
      const brand = String(p.brand || p.marca || p.fornitore || detectBrandFromText(code + ' ' + rawDesc)).trim().toUpperCase();
      const price = parseFloat(p.price || p.prezzoNetto || p.net_price || p.list_price || p.prezzo || 0);
      const listPrice = parseFloat(p.list_price || p.prezzoListino || (price > 0 ? price * 1.28 : 0));
      const stock = parseInt(p.stock !== undefined ? p.stock : (p.giacenza !== undefined ? p.giacenza : 5), 10);
      const rawImg = String(p.imageUrl || p.image_url || p.imageRef || '').trim();
      const validUrl = (rawImg.startsWith('http://') || rawImg.startsWith('https://') || rawImg.startsWith('/') || rawImg.startsWith('data:image')) ? rawImg : '';

      return {
        id: p.id || code,
        code,
        description: rawDesc,
        seoTitle: p.seoTitle || rawDesc,
        seoDescription: p.seoDescription || `${rawDesc} - Codice ${code} disponibile su Climawell Store con spedizione rapida 24/48h.`,
        highlights: Array.isArray(p.highlights) ? p.highlights : [],
        badge: p.badge || '',
        brand: brand || 'CLIMAWELL',
        price: price > 0 ? price : 190.00,
        listPrice: listPrice > price ? listPrice : (price > 0 ? Math.round(price * 1.25) : 240.00),
        stock: isNaN(stock) ? 5 : stock,
        imageUrl: validUrl,
        family: String(p.family || p.famiglia || p.category || detectFamilyFromText(brand + ' ' + rawDesc)).toUpperCase(),
        vat: Number(p.vat || 22),
        isFeaturedTop10: false,
        top10Rank: 999
      };
    }).filter(p => p.code);
  }

  function mergeTop10WithCatalog(catalogList) {
    const byCode = new Map();
    catalogList.forEach(item => {
      byCode.set(item.code.toUpperCase(), item);
    });

    const featuredItems = [];
    const top10List = EcomState.top10Config.slice(0, 24);

    top10List.forEach((cfg, idx) => {
      const key = String(cfg.code || '').trim().toUpperCase();
      const dbMatch = byCode.get(key);

      if (dbMatch) {
        dbMatch.isFeaturedTop10 = true;
        dbMatch.top10Rank = idx + 1;
        dbMatch.seoTitle = cfg.seoTitle || dbMatch.seoTitle || dbMatch.description;
        dbMatch.seoDescription = cfg.seoDescription || dbMatch.seoDescription;
        dbMatch.highlights = (cfg.highlights && cfg.highlights.length) ? cfg.highlights : getDefaultHighlights(dbMatch);
        dbMatch.badge = cfg.badge || `⭐ Top ${idx + 1} Vetrina`;
        if (cfg.imageUrl && cfg.imageUrl.trim()) {
          dbMatch.imageUrl = cfg.imageUrl.trim();
        }
        if (cfg.price && Number(cfg.price) > 0) {
          dbMatch.price = Number(cfg.price);
        }
        if (cfg.listPrice && Number(cfg.listPrice) > dbMatch.price) {
          dbMatch.listPrice = Number(cfg.listPrice);
        }
        if (cfg.brand) dbMatch.brand = cfg.brand.toUpperCase();
        if (cfg.family) dbMatch.family = cfg.family.toUpperCase();
        featuredItems.push(dbMatch);
        byCode.delete(key);
      } else {
        const price = Number(cfg.price || 350);
        const listPrice = Number(cfg.listPrice || Math.round(price * 1.28));
        featuredItems.push({
          id: cfg.code,
          code: cfg.code,
          description: cfg.seoTitle || cfg.description || cfg.code,
          seoTitle: cfg.seoTitle || cfg.description || cfg.code,
          seoDescription: cfg.seoDescription || `${cfg.seoTitle || cfg.code} in pronta consegna su Climawell Store.`,
          highlights: (cfg.highlights && cfg.highlights.length) ? cfg.highlights : getDefaultHighlights(cfg),
          badge: cfg.badge || `⭐ Top ${idx + 1} Vetrina`,
          brand: (cfg.brand || 'CLIMAWELL').toUpperCase(),
          family: (cfg.family || 'CLIMA').toUpperCase(),
          price,
          listPrice,
          stock: cfg.stock !== undefined ? Number(cfg.stock) : 6,
          imageUrl: cfg.imageUrl || '',
          vat: 22,
          isFeaturedTop10: true,
          top10Rank: idx + 1
        });
      }
    });

    const remainingItems = Array.from(byCode.values());
    const countBadge = document.getElementById('countTop10');
    if (countBadge) countBadge.textContent = String(featuredItems.length);

    return [...featuredItems, ...remainingItems];
  }

  function detectBrandFromText(txt) {
    const u = String(txt || '').toUpperCase();
    if (u.includes('SAMSUNG') || u.includes('WINDFREE')) return 'SAMSUNG';
    if (u.includes('ARISTON') || u.includes('NUOS')) return 'ARISTON';
    if (u.includes('HAIER')) return 'HAIER';
    if (u.includes('OLIMPIA')) return 'OLIMPIA';
    return 'CLIMAWELL';
  }

  function detectFamilyFromText(txt) {
    const u = String(txt || '').toUpperCase();
    if (u.includes('POMP') || u.includes('IDRONIC') || u.includes('SCALDACQUA') || u.includes('NUOS') || u.includes('FANCOIL') || u.includes('VENTIL')) return 'POMPE';
    if (u.includes('DOCC') || u.includes('BOX') || u.includes('CRISTALLO') || u.includes('WALK') || u.includes('ARREDO') || u.includes('BAGNO')) return 'ARREDO';
    return 'CLIMA';
  }

  function getDefaultHighlights(p) {
    const fam = String(p.family || '').toUpperCase();
    if (fam.includes('ARREDO') || fam.includes('DOCC') || fam.includes('BOX')) {
      return [
        'Cristallo temperato certificato',
        'Profili alluminio anodizzato',
        'Spedizione protetta su bancale 24/48h'
      ];
    }
    if (fam.includes('POMPE')) {
      return [
        'Alta efficienza energetica A+++',
        'Idoneo Detrazioni & Conto Termico',
        'Garanzia Ufficiale Italia Climawell'
      ];
    }
    return [
      'Tecnologia Inverter ad alta efficienza',
      'Gas ecologico a basso impatto',
      'Pronta consegna magazzino Climawell'
    ];
  }

  function populateBrandFilter() {
    const select = document.getElementById('brandFilterSelect');
    if (!select) return;
    const current = select.value || 'ALL';
    const brands = Array.from(new Set(
      EcomState.products
        .slice(0, 250)
        .map(p => (p.brand || '').trim().toUpperCase())
        .filter(Boolean)
    )).sort();

    select.innerHTML = `<option value="ALL">🏷️ Tutte le Marche</option>` +
      brands.map(b => `<option value="${escapeHtml(b)}">${escapeHtml(b)}</option>`).join('');
    if (brands.includes(current)) select.value = current;
  }

  // 3. GESTIONE CARRELLO MULTI-PRODOTTO (Add, Step Qty, Remove, Totali)
  function getProductByCode(code) {
    if (!code) return null;
    const u = String(code).trim().toUpperCase();
    return EcomState.products.find(p => p.code.toUpperCase() === u) || null;
  }

  function addToCart(code, qtyToAdd = 1, openCheckoutImmediately = false) {
    const prod = getProductByCode(code);
    if (!prod) return;

    const existing = EcomState.cart.find(item => item.code.toUpperCase() === prod.code.toUpperCase());
    const minQ = prod.minQty || 1;
    if (existing) {
      existing.qty = Math.min(999, existing.qty + qtyToAdd);
    } else {
      EcomState.cart.push({
        code: prod.code,
        qty: Math.max(minQ, qtyToAdd)
      });
    }

    EcomState.selectedProduct = prod;
    saveCartToStorage();
    updateCartIndicators();
    renderProductsGrid();

    const extraPct = Number(EcomState.paymentRules.extraDiscountCardPct || 0);
    if (openCheckoutImmediately) {
      openOrderModal();
    } else {
      showToast(`🛒 "${prod.code}" aggiunto al carrello! (${extraPct > 0 ? `-${extraPct}% Extra se paghi con Carta` : 'Pronto al checkout'})`);
    }
  }

  function updateCartItemQty(code, newQty) {
    const u = String(code || '').toUpperCase();
    const idx = EcomState.cart.findIndex(i => i.code.toUpperCase() === u);
    if (idx === -1) return;

    if (newQty <= 0) {
      EcomState.cart.splice(idx, 1);
    } else {
      EcomState.cart[idx].qty = Math.min(999, newQty);
    }
    saveCartToStorage();
    updateCartIndicators();
    renderCheckoutCartItems();
    updateOrderSummary();
    renderProductsGrid();
  }

  function clearCart() {
    EcomState.cart = [];
    saveCartToStorage();
    updateCartIndicators();
    renderProductsGrid();
  }

  function getResolvedCartLines() {
    const lines = [];
    EcomState.cart.forEach(item => {
      const prod = getProductByCode(item.code);
      if (prod && item.qty > 0) {
        lines.push({
          product: prod,
          code: prod.code,
          title: prod.seoTitle || prod.description,
          brand: prod.brand,
          qty: item.qty,
          unitPrice: prod.price,
          unitListPrice: prod.listPrice || prod.price,
          vat: prod.vat || 22,
          lineSubtotal: prod.price * item.qty
        });
      }
    });

    // Fallback se si apre il modal senza righe ma con selectedProduct
    if (lines.length === 0 && EcomState.selectedProduct) {
      const p = EcomState.selectedProduct;
      lines.push({
        product: p,
        code: p.code,
        title: p.seoTitle || p.description,
        brand: p.brand,
        qty: 1,
        unitPrice: p.price,
        unitListPrice: p.listPrice || p.price,
        vat: p.vat || 22,
        lineSubtotal: p.price
      });
    }
    return lines;
  }

  function updateCartIndicators() {
    const lines = EcomState.cart.map(item => {
      const prod = getProductByCode(item.code);
      return prod ? { ...item, price: prod.price } : null;
    }).filter(Boolean);

    const totalItems = lines.reduce((acc, l) => acc + l.qty, 0);
    const rawSubtotal = lines.reduce((acc, l) => acc + (l.price * l.qty), 0);
    const cardPct = Number(EcomState.paymentRules.extraDiscountCardPct || 0);
    const discountedSubtotal = rawSubtotal * (1 - cardPct / 100);

    const headerCount = document.getElementById('headerCartCount');
    const headerTotal = document.getElementById('headerCartTotal');
    if (headerCount) headerCount.textContent = String(totalItems);
    if (headerTotal) headerTotal.textContent = `€ ${euro(rawSubtotal)}`;

    const floatingBar = document.getElementById('floatingCartBar');
    const floatingCount = document.getElementById('floatingCartCount');
    const floatingSummary = document.getElementById('floatingCartSummaryText');
    const floatingHint = document.getElementById('floatingCartDiscountHint');

    if (floatingBar) {
      if (totalItems > 0) {
        floatingBar.classList.remove('hidden');
        if (floatingCount) floatingCount.textContent = `${totalItems} ${totalItems === 1 ? 'articolo' : 'articoli'}`;
        if (floatingSummary) {
          floatingSummary.textContent = `Totale Carrello: € ${euro(rawSubtotal)} + IVA`;
        }
        if (floatingHint) {
          const saveAmount = rawSubtotal - discountedSubtotal;
          floatingHint.textContent = cardPct > 0
            ? `🎁 Paga subito con Carta (-${cardPct}%): paghi solo € ${euro(discountedSubtotal)} + IVA (Risparmi € ${euro(saveAmount)}!)`
            : `Spedizione rapida 24/48h o ritiro a banco`;
        }
      } else {
        floatingBar.classList.add('hidden');
      }
    }
  }

  // 4. Applicazione Filtri (Top 10, Categoria, Marca, Prezzo, Ricerca e Ordinamento)
  function applyFilters() {
    const q = EcomState.searchQuery.toLowerCase().trim();
    const cat = EcomState.currentCategory;
    const brand = EcomState.brandFilter;
    const priceRange = EcomState.priceFilter;
    const sortBy = EcomState.sortBy;

    const noticeBar = document.getElementById('curatedNoticeBar');
    if (noticeBar) {
      noticeBar.style.display = (cat === 'TOP10' && !q) ? 'block' : 'none';
    }

    let list = EcomState.products.filter(p => {
      if (q) {
        const matchQuery =
          p.code.toLowerCase().includes(q) ||
          p.description.toLowerCase().includes(q) ||
          (p.seoTitle && p.seoTitle.toLowerCase().includes(q)) ||
          p.brand.toLowerCase().includes(q);
        if (!matchQuery) return false;
      } else {
        if (cat === 'TOP10') {
          if (!p.isFeaturedTop10) return false;
        } else if (cat === 'STOCK') {
          if (p.stock <= 0) return false;
        } else if (cat === 'ATTREZZATURA' || cat === 'VUOTO') {
          const text = (p.description + ' ' + p.family + ' ' + p.brand + ' ' + (p.seoTitle || '')).toUpperCase();
          if (!(text.includes('ATTREZZ') || text.includes('POMPA') || text.includes('VUOTO') || text.includes('AZOTO') || text.includes('FLANGIATUBO') || text.includes('BILANCIA') || text.includes('SALDANT') || text.includes('CHIAV') || text.includes('CORE'))) return false;
        } else if (cat === 'LAVAGGIO') {
          const text = (p.description + ' ' + p.family + ' ' + p.brand + ' ' + (p.seoTitle || '')).toUpperCase();
          if (!(text.includes('LAVAGGIO') || text.includes('IGIENIZZ') || text.includes('DETERG') || text.includes('SPRAY') || text.includes('STI') || text.includes('SLI') || text.includes('SSE') || text.includes('POWERCLEAN'))) return false;
        } else if (cat === 'CLIMA') {
          const text = (p.description + ' ' + p.family + ' ' + p.brand + ' ' + p.seoTitle).toUpperCase();
          if (!(text.includes('CLIMA') || text.includes('SPLIT') || text.includes('BARRIERA') || text.includes('BTU') || text.includes('CONDIZIONATORE'))) return false;
        } else if (cat === 'POMPE') {
          const text = (p.description + ' ' + p.family + ' ' + p.seoTitle).toUpperCase();
          if (!(text.includes('POMP') || text.includes('CALORE') || text.includes('IDRONIC') || text.includes('ALTHERMA') || text.includes('SCALDACQUA') || text.includes('FANCOIL'))) return false;
        } else if (cat === 'ARREDO' || cat === '2B') {
          const text = (p.description + ' ' + p.family + ' ' + p.brand + ' ' + p.seoTitle).toUpperCase();
          if (!(text.includes('DOCC') || text.includes('BOX') || text.includes('BAGNO') || text.includes('ARREDO') || text.includes('TERMO'))) return false;
        }
      }

      if (brand !== 'ALL' && p.brand.toUpperCase() !== brand) return false;
      if (priceRange === 'UNDER_400' && p.price > 400) return false;
      if (priceRange === '400_1200' && (p.price < 400 || p.price > 1200)) return false;
      if (priceRange === 'OVER_1200' && p.price <= 1200) return false;

      return true;
    });

    list.sort((a, b) => {
      if (sortBy === 'PRICE_ASC') return a.price - b.price;
      if (sortBy === 'PRICE_DESC') return b.price - a.price;
      if (sortBy === 'DISCOUNT') {
        const discA = a.listPrice > a.price ? (1 - a.price / a.listPrice) : 0;
        const discB = b.listPrice > b.price ? (1 - b.price / b.listPrice) : 0;
        return discB - discA;
      }
      if (a.isFeaturedTop10 && !b.isFeaturedTop10) return -1;
      if (!a.isFeaturedTop10 && b.isFeaturedTop10) return 1;
      if (a.isFeaturedTop10 && b.isFeaturedTop10) return (a.top10Rank || 99) - (b.top10Rank || 99);
      return a.code.localeCompare(b.code);
    });

    if (cat === 'TOP10' && !q) {
      list = list.slice(0, 24);
    } else {
      list = list.slice(0, 48);
    }

    EcomState.filtered = list;
    renderProductsGrid();
  }

  // 5. Rendering Griglia Prodotti con Pulsanti "+ Carrello" e "⚡ Acquista"
  function renderProductsGrid() {
    const grid = document.getElementById('productsGrid');
    const countLabel = document.getElementById('productCountLabel');
    if (!grid) return;

    if (countLabel) {
      if (EcomState.currentCategory === 'TOP10' && !EcomState.searchQuery) {
        countLabel.textContent = `${EcomState.filtered.length} articoli Top in vetrina`;
      } else {
        countLabel.textContent = `${EcomState.filtered.length} articoli trovati`;
      }
    }

    if (EcomState.filtered.length === 0) {
      grid.innerHTML = `
        <div class="empty-state">
          <p style="font-size:1.1rem; font-weight:700; margin-bottom:6px;">Nessun articolo trovato con i filtri selezionati</p>
          <p style="font-size:0.85rem; margin-bottom:14px;">Prova a cercare nell'intero listino oppure azzera i filtri attivi.</p>
          <button type="button" class="btn-card-order" id="btnResetFiltersEmpty" style="max-width:260px; margin:0 auto;">
            ↺ Torna ai Top 10 in Vetrina
          </button>
        </div>
      `;
      document.getElementById('btnResetFiltersEmpty')?.addEventListener('click', resetAllFiltersToTop10);
      return;
    }

    const extraCardPct = Number(EcomState.paymentRules.extraDiscountCardPct || 0);

    grid.innerHTML = EcomState.filtered.map(p => {
      const isStock = p.stock > 0;
      const stockClass = isStock ? 'in-stock' : 'out-stock';
      const stockText = isStock ? `🟢 Pronta Consegna (${p.stock} pz)` : '🟡 Su Ordinazione (3-5 gg)';
      const isPromoTarget = EcomState.context.promoArticle &&
        p.code.toLowerCase() === EcomState.context.promoArticle.toLowerCase();

      const inCartItem = EcomState.cart.find(c => c.code.toUpperCase() === p.code.toUpperCase());
      const inCartQty = inCartItem ? inCartItem.qty : 0;

      const displayTitle = p.seoTitle || p.description;
      const imgSrc = p.imageUrl || getSmartProductVisual(p);
      const discountPct = (p.listPrice > p.price && p.listPrice > 0)
        ? Math.round((1 - p.price / p.listPrice) * 100)
        : 0;

      const isB2C = EcomState.priceMode === 'B2C';
      const vatRate = 0.22;
      const displayPrice = isB2C ? p.price * (1 + vatRate) : p.price;
      const displayListPrice = p.listPrice > p.price ? (isB2C ? p.listPrice * (1 + vatRate) : p.listPrice) : 0;
      const displayCardPrice = extraCardPct > 0 ? displayPrice * (1 - extraCardPct / 100) : displayPrice;
      const priceSubText = isB2C
        ? 'Prezzo IVA 22% Inclusa • Detraibile Casa/Ecobonus'
        : 'Prezzo Netto B2B + IVA • Sped. 24/48h o Ritiro Banco';

      const highlights = (p.highlights && p.highlights.length > 0)
        ? p.highlights.slice(0, 3)
        : getDefaultHighlights(p);

      return `
        <article class="product-card ${isPromoTarget ? 'promo-target' : ''}" data-code="${escapeHtml(p.code)}" itemscope itemtype="https://schema.org/Product">
          <meta itemprop="sku" content="${escapeHtml(p.code)}">
          <meta itemprop="mpn" content="${escapeHtml(p.code)}">
          <div class="card-img-wrap">
            <span class="brand-tag" itemprop="brand" itemscope itemtype="https://schema.org/Brand">
              <span itemprop="name">${escapeHtml(p.brand)}</span>
            </span>
            ${p.badge ? `<span class="curated-badge">${escapeHtml(p.badge)}</span>` : ''}
            <img src="${imgSrc}" alt="${escapeHtml(displayTitle)} - Cod. ${escapeHtml(p.code)}" loading="lazy" width="280" height="180" itemprop="image" onerror="this.onerror=null; this.src='${getSmartProductVisual(p)}'">
            <span class="stock-tag ${stockClass}">${stockText}</span>
          </div>
          <div class="card-body">
            <div class="card-code">COD. ARTICOLO: <strong>${escapeHtml(p.code)}</strong></div>
            <h2 class="card-title" itemprop="name" title="${escapeHtml(displayTitle)}">${escapeHtml(displayTitle)}</h2>
            <p class="card-seo-desc" itemprop="description">${escapeHtml(p.seoDescription || p.description)}</p>
            <ul class="card-highlights-list">
              ${highlights.map(h => `<li>✓ <span>${escapeHtml(h)}</span></li>`).join('')}
            </ul>
            <div class="card-pricing" itemprop="offers" itemscope itemtype="https://schema.org/Offer">
              <meta itemprop="priceCurrency" content="EUR">
              <meta itemprop="price" content="${Number(displayPrice).toFixed(2)}">
              <link itemprop="availability" href="${isStock ? 'https://schema.org/InStock' : 'https://schema.org/PreOrder'}">
              <div class="price-box" style="width:100%;">
                ${displayListPrice > displayPrice ? `
                  <div>
                    <span class="list-price">Listino € ${euro(displayListPrice)}</span>
                    ${discountPct > 0 ? `<span class="discount-pill">-${discountPct}%</span>` : ''}
                  </div>
                ` : ''}
                <div style="display:flex; justify-content:space-between; align-items:baseline; width:100%;">
                  <span class="net-price">€ ${euro(displayPrice)}</span>
                  ${extraCardPct > 0 ? `<span style="font-size:0.72rem; font-weight:800; color:#059669; background:#ecfdf5; padding:2px 6px; border-radius:4px;">💳 € ${euro(displayCardPrice)} (-${extraCardPct}% Carta)</span>` : ''}
                </div>
                <span class="price-sub">${priceSubText}</span>
              </div>
            </div>
            <button type="button" class="btn-card-details" data-quickview-code="${escapeHtml(p.code)}" title="Vedi scheda tecnica, compatibilità e bonus fiscali">
              🔍 Scheda Tecnica &amp; Detrazioni
            </button>
            <div class="card-actions-row">
              <button type="button" class="btn-card-add-cart" data-addcart-code="${escapeHtml(p.code)}" style="flex:1;" title="Aggiungi al carrello multi-prodotto">
                🛒 ${inCartQty > 0 ? `Nel Carrello (${inCartQty})` : '+ Carrello'}
              </button>
              <button type="button" class="btn-card-order" data-buynow-code="${escapeHtml(p.code)}" style="flex:1;">
                ⚡ Acquista
              </button>
              <button type="button" class="btn-card-share" data-share-code="${escapeHtml(p.code)}" title="Copia link diretto SEO prodotto per WhatsApp / Social">
                🔗
              </button>
            </div>
          </div>
        </article>
      `;
    }).join('');

    // Listener "🔍 Scheda Tecnica & Detrazioni" (Quick View Modal)
    grid.querySelectorAll('[data-quickview-code]').forEach(btn => {
      btn.addEventListener('click', () => {
        const code = btn.getAttribute('data-quickview-code');
        openQuickViewModal(code);
      });
    });

    // Listener "+ Carrello" (aggiunge al carrello multi-prodotto senza aprire subito il modal)
    grid.querySelectorAll('[data-addcart-code]').forEach(btn => {
      btn.addEventListener('click', () => {
        const code = btn.getAttribute('data-addcart-code');
        addToCart(code, 1, false);
      });
    });

    // Listener "⚡ Acquista" (aggiunge al carrello se non presente e apre subito la Cassa)
    grid.querySelectorAll('[data-buynow-code]').forEach(btn => {
      btn.addEventListener('click', () => {
        const code = btn.getAttribute('data-buynow-code');
        const exists = EcomState.cart.find(c => c.code.toUpperCase() === code.toUpperCase());
        if (!exists) {
          addToCart(code, 1, true);
        } else {
          const prod = getProductByCode(code);
          if (prod) EcomState.selectedProduct = prod;
          openOrderModal();
        }
      });
    });

    // Listener "🔗 Condividi Link SEO"
    grid.querySelectorAll('[data-share-code]').forEach(btn => {
      btn.addEventListener('click', () => {
        const code = btn.getAttribute('data-share-code');
        const prod = getProductByCode(code);
        if (!prod) return;
        const shareUrl = `${window.location.origin}/e-com/?prodotto=${encodeURIComponent(prod.code)}&agent=${encodeURIComponent(EcomState.context.agentCode)}`;
        updateSeoForSingleProduct(prod);
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(shareUrl).then(() => {
            showToast(`🔗 Link SEO copiato per ${prod.code}! Pronto per Social e WhatsApp.`);
          }).catch(() => {
            prompt('Copia il link diretto del prodotto:', shareUrl);
          });
        } else {
          prompt('Copia il link diretto del prodotto:', shareUrl);
        }
      });
    });
  }

  function resetAllFiltersToTop10() {
    EcomState.currentCategory = 'TOP10';
    EcomState.brandFilter = 'ALL';
    EcomState.priceFilter = 'ALL';
    EcomState.sortBy = 'FEATURED';
    EcomState.searchQuery = '';

    const searchInput = document.getElementById('ecomSearchInput');
    if (searchInput) searchInput.value = '';
    const btnClear = document.getElementById('btnClearSearch');
    if (btnClear) btnClear.style.display = 'none';
    const bSel = document.getElementById('brandFilterSelect');
    if (bSel) bSel.value = 'ALL';
    const pSel = document.getElementById('priceFilterSelect');
    if (pSel) pSel.value = 'ALL';
    const sSel = document.getElementById('sortFilterSelect');
    if (sSel) sSel.value = 'FEATURED';

    document.querySelectorAll('.cat-pill').forEach(b => {
      b.classList.toggle('active', b.dataset.cat === 'TOP10');
    });

    applyFilters();
  }

  // 6. Apertura automatica da URL (?prodotto=CODICE oppure ?cart=COD1:1,COD2:2)
  function checkPromoOrCartHighlight() {
    // Se c'è un parametro ?cart=MSZ-AP35:1,780824:2 pre-carica il carrello multi-prodotto
    if (EcomState.context.preloadCartParam) {
      const pairs = EcomState.context.preloadCartParam.split(',');
      const loaded = [];
      pairs.forEach(pair => {
        const [rawCode, rawQty] = pair.split(':');
        const prod = getProductByCode(rawCode);
        const qty = Math.max(1, parseInt(rawQty || '1', 10) || 1);
        if (prod) {
          loaded.push({ code: prod.code, qty });
        }
      });
      if (loaded.length > 0) {
        EcomState.cart = loaded;
        saveCartToStorage();
        updateCartIndicators();
        renderProductsGrid();
        setTimeout(() => openOrderModal(), 350);
        return;
      }
    }

    // Riconoscimento Campagna Speciale (es. Black Friday)
    if (EcomState.context.campaignId && String(EcomState.context.campaignId).toLowerCase().includes('black')) {
      const bannerTag = document.getElementById('promoExtraDiscountTag');
      const bannerTitle = document.getElementById('promoBannerTitle');
      const bannerDesc = document.getElementById('promoBannerDesc');
      if (bannerTag) bannerTag.innerHTML = '🖤 SPECIAL BLACK FRIDAY • SCONTI EXTRA &amp; PRONTA CONSEGNA';
      if (bannerTitle) bannerTitle.innerHTML = 'Offerte Black Friday Termoidraulica &amp; Climatizzazione';
      if (bannerDesc) bannerDesc.innerHTML = 'Approfitta dei prezzi promozionali dedicati al Black Friday con disponibilità limitata a magazzino, spedizione rapida 24/48h o ritiro al banco!';
    }

    if (!EcomState.context.promoArticle) return;
    const found = getProductByCode(EcomState.context.promoArticle);
    if (found) {
      updateSeoForSingleProduct(found);
      const bannerTitle = document.getElementById('promoBannerTitle');
      const bannerDesc = document.getElementById('promoBannerDesc');
      if (bannerTitle) bannerTitle.textContent = `Offerta Diretta: ${found.seoTitle || found.description}`;
      if (bannerDesc) bannerDesc.textContent = `Articolo Cod. ${found.code} (${found.brand}) a € ${euro(found.price)} + IVA (-${EcomState.paymentRules.extraDiscountCardPct}% Extra se paghi subito con Carta!).`;

      addToCart(found.code, 1, true);
    }
  }

  // 7. MOTORE SEO 2026: JSON-LD Google Merchant Listings & Meta Tag
  function updateSeoStructuredDataAndMeta() {
    const top10Products = EcomState.products.filter(p => p.isFeaturedTop10).slice(0, 24);
    const baseUrl = 'https://clw-agenti.netlify.app/e-com/';

    const itemListElements = top10Products.map((p, index) => {
      const prodUrl = `${baseUrl}?prodotto=${encodeURIComponent(p.code)}`;
      const imageUrl = (p.imageUrl && p.imageUrl.startsWith('http'))
        ? p.imageUrl
        : 'https://www.boxdocce2b.com/wp-content/uploads/2021/03/tre-lati.png';

      return {
        '@type': 'ListItem',
        'position': index + 1,
        'item': {
          '@type': 'Product',
          '@id': `${baseUrl}#product-${p.code}`,
          'name': p.seoTitle || p.description,
          'description': p.seoDescription || p.description,
          'sku': p.code,
          'mpn': p.code,
          'image': [imageUrl],
          'brand': {
            '@type': 'Brand',
            'name': p.brand || 'Climawell'
          },
          'url': prodUrl,
          'offers': {
            '@type': 'Offer',
            'url': prodUrl,
            'priceCurrency': 'EUR',
            'price': Number(p.price || 0).toFixed(2),
            'priceValidUntil': '2026-12-31',
            'itemCondition': 'https://schema.org/NewCondition',
            'availability': p.stock > 0 ? 'https://schema.org/InStock' : 'https://schema.org/PreOrder',
            'seller': {
              '@type': 'Organization',
              'name': 'Climawell S.r.l.'
            },
            'shippingDetails': {
              '@type': 'OfferShippingDetails',
              'shippingRate': {
                '@type': 'MonetaryAmount',
                'value': '0.00',
                'currency': 'EUR'
              },
              'shippingDestination': {
                '@type': 'DefinedRegion',
                'addressCountry': 'IT'
              },
              'deliveryTime': {
                '@type': 'ShippingDeliveryTime',
                'handlingTime': {
                  '@type': 'QuantitativeValue',
                  'minValue': 0,
                  'maxValue': 1,
                  'unitCode': 'DAY'
                },
                'transitTime': {
                  '@type': 'QuantitativeValue',
                  'minValue': 1,
                  'maxValue': 2,
                  'unitCode': 'DAY'
                }
              }
            },
            'hasMerchantReturnPolicy': {
              '@type': 'MerchantReturnPolicy',
              'applicableCountry': 'IT',
              'returnPolicyCategory': 'https://schema.org/MerchantReturnFiniteReturnWindow',
              'merchantReturnDays': 14,
              'returnMethod': 'https://schema.org/ReturnByMail',
              'returnFees': 'https://schema.org/FreeReturn'
            }
          }
        }
      };
    });

    const fullGraph = {
      '@context': 'https://schema.org',
      '@graph': [
        {
          '@type': 'Store',
          '@id': `${baseUrl}#store`,
          'name': 'Climawell S.r.l. — Vetrina E-Commerce Climatizzazione & Termoidraulica',
          'url': baseUrl,
          'telephone': '+39-055-4289074',
          'email': 'commerciale@climawell.it',
          'priceRange': '€€',
          'address': {
            '@type': 'PostalAddress',
            'addressLocality': 'Firenze',
            'addressRegion': 'FI',
            'addressCountry': 'IT'
          }
        },
        {
          '@type': 'ItemList',
          '@id': `${baseUrl}#top10-showcase`,
          'name': 'Top 12 Prodotti Climatizzazione, Pompe di Calore e Box Doccia Climawell',
          'numberOfItems': itemListElements.length,
          'itemListElement': itemListElements
        }
      ]
    };

    const jsonString = JSON.stringify(fullGraph, null, 2);
    const scriptEl = document.getElementById('seoJsonLdSchema');
    if (scriptEl) scriptEl.textContent = jsonString;

    const previewEl = document.getElementById('seoJsonLdPreviewBox');
    if (previewEl) previewEl.textContent = jsonString;
  }

  function updateSeoForSingleProduct(prod) {
    if (!prod) return;
    const title = `${prod.seoTitle || prod.description} (Cod. ${prod.code}) — € ${euro(prod.price)} | Climawell Store`;
    const desc = `${prod.seoDescription || prod.description} Acquista online Cod. ${prod.code} (${prod.brand}) a € ${euro(prod.price)} + IVA. Spedizione rapida 24/48h.`;
    const canonical = `https://clw-agenti.netlify.app/e-com/?prodotto=${encodeURIComponent(prod.code)}`;

    document.title = title;
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) metaDesc.setAttribute('content', desc);
    const canLink = document.getElementById('seoCanonicalUrl');
    if (canLink) canLink.setAttribute('href', canonical);
  }

  // 8. CHECKOUT CARRELLO MULTI-PRODOTTO & LOGICA REGOLE PAGAMENTO (B2B RI.BA. vs PRIVATI)
  function applyPaymentRulesToUiBanners() {
    const r = EcomState.paymentRules;
    const cardPct = Number(r.extraDiscountCardPct || 0);
    const bankPct = Number(r.extraDiscountBankPct || 0);

    const promoTag = document.getElementById('promoExtraDiscountTag');
    if (promoTag) {
      promoTag.textContent = `🎁 SCONTO EXTRA -${cardPct}% SE PAGHI SUBITO CON CARTA • CONDIZIONI B2B RI.BA. ATTIVE`;
    }
    const promoPctText = document.getElementById('promoExtraPctText');
    if (promoPctText) promoPctText.textContent = `${cardPct}% di Sconto Extra Immediato`;
    const highlightExtra = document.getElementById('highlightExtraDiscount');
    if (highlightExtra) highlightExtra.textContent = `💳 -${cardPct}% Sconto Extra Pagamento Immediato`;

    const badgeCard = document.getElementById('badgeTabCardDiscount');
    if (badgeCard) badgeCard.textContent = cardPct > 0 ? `🎁 SCONTO EXTRA -${cardPct}%` : 'IMMEDIATO';

    const badgeBank = document.getElementById('badgeTabBankDiscount');
    if (badgeBank) badgeBank.textContent = bankPct > 0 ? `🎁 SCONTO EXTRA -${bankPct}%` : 'ANTICIPATO';

    const ibanEl = document.getElementById('displayCompanyIban');
    if (ibanEl) ibanEl.textContent = r.companyIban || DEFAULT_PAYMENT_RULES.companyIban;

    // Popola le opzioni di dilazione B2B abilitate dall'amministratore
    const b2bSelect = document.getElementById('b2bDeferredTermSelect');
    if (b2bSelect) {
      const opts = [];
      if (r.b2bTermRiba6090) opts.push(`<option value="RI.BA. 60-90 GG D.F.F.M.">📄 Ri.Ba. 60-90 gg D.F.F.M. (Ricevuta Bancaria)</option>`);
      if (r.b2bTermRiba60) opts.push(`<option value="RI.BA. 60 GG D.F.F.M.">📄 Ri.Ba. 60 gg D.F.F.M. (Ricevuta Bancaria)</option>`);
      if (r.b2bTermRiba30) opts.push(`<option value="RI.BA. 30 GG D.F.F.M.">📄 Ri.Ba. 30 gg D.F.F.M. (Ricevuta Bancaria)</option>`);
      if (r.b2bTermBonifico30) opts.push(`<option value="BONIFICO 30 GG D.F.F.M.">🏦 Bonifico Bancario 30 gg D.F.F.M.</option>`);
      if (opts.length === 0) {
        opts.push(`<option value="ORDINE ASSISTITO B2B">🧑‍💼 Condizione B2B da confermare con Agente</option>`);
      }
      b2bSelect.innerHTML = opts.join('');
      const lblBtn = document.getElementById('btnB2bTermLabel');
      if (lblBtn) lblBtn.textContent = b2bSelect.value;
    }

    // Aggiorna etichette costi spedizione nel selettore consegna
    const deliverySelect = document.getElementById('orderDeliveryType');
    if (deliverySelect) {
      const shipCost = Number(r.standardShippingCost !== undefined ? r.standardShippingCost : 6.99);
      const currentVal = deliverySelect.value || 'SPEDIZIONE_SEDE';
      deliverySelect.innerHTML = `
        <option value="SPEDIZIONE_SEDE">🚚 Spedizione presso sede / domicilio (24/48h) — € ${euro(shipCost)}</option>
        <option value="SPEDIZIONE_CANTIERE">🏗️ Spedizione diretta in cantiere — € ${euro(shipCost)}</option>
        <option value="RITIRO_BANCO">🏬 Ritiro a banco Magazzino Climawell (Firenze) — GRATIS (€ 0,00)</option>
      `;
      deliverySelect.value = currentVal;
    }
  }

  function openOrderModal(singleProduct = null) {
    if (singleProduct) {
      EcomState.selectedProduct = singleProduct;
      const inCart = EcomState.cart.find(c => c.code.toUpperCase() === singleProduct.code.toUpperCase());
      if (!inCart) {
        EcomState.cart.push({ code: singleProduct.code, qty: 1 });
        saveCartToStorage();
      }
    }

    if (EcomState.cart.length === 0 && EcomState.products.length > 0) {
      const first = EcomState.products[0];
      EcomState.cart.push({ code: first.code, qty: 1 });
      EcomState.selectedProduct = first;
      saveCartToStorage();
    }

    updateCartIndicators();
    renderCheckoutCartItems();
    evaluateBuyerAndPaymentAccess();
    updateOrderSummary();

    const modal = document.getElementById('orderModal');
    if (modal) modal.classList.add('active');
  }

  function closeOrderModal() {
    const modal = document.getElementById('orderModal');
    if (modal) modal.classList.remove('active');
  }

  function renderCheckoutCartItems() {
    const container = document.getElementById('checkoutCartItemsList');
    if (!container) return;

    const lines = getResolvedCartLines();
    if (lines.length === 0) {
      container.innerHTML = `<div style="padding:12px; text-align:center; color:#64748b; font-size:0.82rem;">Il carrello è vuoto. Aggiungi un articolo dalla vetrina.</div>`;
      return;
    }

    container.innerHTML = lines.map(line => {
      const imgSrc = line.product.imageUrl || getSmartProductVisual(line.product);
      return `
        <div class="checkout-cart-item" data-cart-code="${escapeHtml(line.code)}">
          <img src="${imgSrc}" alt="${escapeHtml(line.code)}" class="checkout-cart-thumb" onerror="this.onerror=null; this.src='${getSmartProductVisual(line.product)}'">
          <div>
            <div class="checkout-cart-title">${escapeHtml(line.title)}</div>
            <div class="checkout-cart-sub">Cod. <strong>${escapeHtml(line.code)}</strong> (${escapeHtml(line.brand)}) • € ${euro(line.unitPrice)} cad.</div>
          </div>
          <div class="checkout-cart-qty-box">
            <button type="button" class="btn-cart-qty-step" data-step="-1" data-code="${escapeHtml(line.code)}">-</button>
            <strong style="min-width:24px; text-align:center; font-size:0.85rem;">${line.qty}</strong>
            <button type="button" class="btn-cart-qty-step" data-step="1" data-code="${escapeHtml(line.code)}">+</button>
          </div>
          <div style="text-align:right; min-width:85px;">
            <strong style="font-size:0.88rem; color:#0369a1; display:block;">€ ${euro(line.lineSubtotal)}</strong>
            <button type="button" class="btn-cart-remove-item" data-rm-code="${escapeHtml(line.code)}" title="Rimuovi riga">✕</button>
          </div>
        </div>
      `;
    }).join('');

    container.querySelectorAll('.btn-cart-qty-step').forEach(btn => {
      btn.addEventListener('click', () => {
        const code = btn.getAttribute('data-code');
        const delta = parseInt(btn.getAttribute('data-step'), 10);
        const item = EcomState.cart.find(c => c.code.toUpperCase() === code.toUpperCase());
        if (item) {
          updateCartItemQty(code, item.qty + delta);
        }
      });
    });

    container.querySelectorAll('[data-rm-code]').forEach(btn => {
      btn.addEventListener('click', () => {
        const code = btn.getAttribute('data-rm-code');
        updateCartItemQty(code, 0);
      });
    });
  }

  // Verifica se il cliente può accedere ai pagamenti B2B dilazionati (Ri.Ba. 60-90gg) o se è Privato B2C
  function isCustomerAuthorizedForB2bDeferred() {
    if (EcomState.buyerType === 'B2C') {
      return { allowed: false, reason: 'Per i Clienti Privati (Codice Fiscale) è richiesto il pagamento anticipato prima della spedizione. Scegli Carta o Bonifico Anticipato per ottenere subito lo Sconto Extra!' };
    }

    const r = EcomState.paymentRules;
    const customerName = (document.getElementById('orderCustomerInput')?.value || '').trim().toUpperCase();
    const taxId = (document.getElementById('orderTaxIdInput')?.value || '').trim().toUpperCase();

    if (r.b2bAccessMode === 'WHITELIST_ONLY') {
      const tokens = String(r.b2bWhitelist || '')
        .split(/[\n,;]+/)
        .map(s => s.trim().toUpperCase())
        .filter(Boolean);

      const matched = tokens.some(tok =>
        (customerName && customerName.includes(tok)) ||
        (taxId && taxId.includes(tok))
      );

      if (!matched) {
        return {
          allowed: false,
          reason: 'Il pagamento dilazionato Ri.Ba. 60-90gg è riservato ai clienti B2B con fido attivo in anagrafica. Inserisci la tua Ragione Sociale / P.IVA abilitata oppure paga subito con Carta usufruendo dello Sconto Extra!'
        };
      }
    }

    return { allowed: true, reason: '' };
  }

  function evaluateBuyerAndPaymentAccess() {
    const isB2B = EcomState.buyerType === 'B2B';
    document.getElementById('btnBuyerTypeB2B')?.classList.toggle('active', isB2B);
    document.getElementById('btnBuyerTypeB2C')?.classList.toggle('active', !isB2B);

    const lblCust = document.getElementById('lblCustomerName');
    const lblTax = document.getElementById('lblTaxId');
    const grpSdi = document.getElementById('groupSdiInput');

    if (lblCust) lblCust.innerHTML = isB2B ? 'Ragione Sociale Azienda / Ditta: <span class="req">*</span>' : 'Nome e Cognome Acquirente Privato: <span class="req">*</span>';
    if (lblTax) lblTax.innerHTML = isB2B ? 'Partita IVA Aziendale: <span class="req">*</span>' : 'Codice Fiscale Personale: <span class="req">*</span>';
    if (grpSdi) grpSdi.style.display = isB2B ? 'block' : 'none';

    const b2bCheck = isCustomerAuthorizedForB2bDeferred();
    const lockedBox = document.getElementById('b2bLockedNotice');
    const b2bControls = document.getElementById('b2bDeferredControls');
    const lockedReason = document.getElementById('b2bLockedReasonText');
    const badgeTabB2b = document.getElementById('badgeTabB2bSub');

    if (badgeTabB2b) {
      badgeTabB2b.textContent = b2bCheck.allowed ? 'RI.BA. ABILITATO' : '🔒 SOLO B2B ABILITATI';
    }

    if (lockedBox && b2bControls) {
      if (b2bCheck.allowed) {
        lockedBox.classList.add('hidden');
        b2bControls.classList.remove('hidden');
      } else {
        lockedBox.classList.remove('hidden');
        b2bControls.classList.add('hidden');
        if (lockedReason) lockedReason.textContent = b2bCheck.reason;
      }
    }
  }

  function switchPaymentMethodTab(target) {
    EcomState.activePaymentTab = target;

    const tabStripe = document.getElementById('tabStripeMethod');
    const tabBank = document.getElementById('tabPrepaidBankMethod');
    const tabAssisted = document.getElementById('tabAssistedMethod');

    const secStripe = document.getElementById('stripeCheckoutSection');
    const secBank = document.getElementById('prepaidBankCheckoutSection') || document.getElementById('prepaidBankSection');
    const secAssisted = document.getElementById('assistedOrderSection');

    tabStripe?.classList.toggle('active', target === 'stripe');
    tabBank?.classList.toggle('active', target === 'prepaid_bank');
    tabAssisted?.classList.toggle('active', target === 'assisted');

    secStripe?.classList.toggle('hidden', target !== 'stripe');
    secBank?.classList.toggle('hidden', target !== 'prepaid_bank');
    secAssisted?.classList.toggle('hidden', target !== 'assisted');

    evaluateBuyerAndPaymentAccess();
    updateOrderSummary();
  }

  function calculateCartFinancials() {
    const lines = getResolvedCartLines();
    const totalItems = lines.reduce((acc, l) => acc + l.qty, 0);
    const rawSubtotal = lines.reduce((acc, l) => acc + l.lineSubtotal, 0);

    let extraDiscountPct = 0;
    if (EcomState.activePaymentTab === 'stripe') {
      extraDiscountPct = Number(EcomState.paymentRules.extraDiscountCardPct || 0);
    } else if (EcomState.activePaymentTab === 'prepaid_bank') {
      extraDiscountPct = Number(EcomState.paymentRules.extraDiscountBankPct || 0);
    } else {
      extraDiscountPct = 0; // Pagamento dilazionato Ri.Ba. 60-90gg non ha sconto cassa extra
    }

    // Modalità di consegna e calcolo spese di trasporto
    const deliverySelect = document.getElementById('orderDeliveryType');
    const deliveryType = deliverySelect ? deliverySelect.value : 'SPEDIZIONE_SEDE';
    const isPickup = deliveryType === 'RITIRO_BANCO';
    const standardShipping = Number(EcomState.paymentRules.standardShippingCost !== undefined ? EcomState.paymentRules.standardShippingCost : 6.99);
    const shippingCost = isPickup ? 0 : standardShipping;

    const extraDiscountAmount = rawSubtotal * (extraDiscountPct / 100);
    const goodsSubtotal = Math.max(0, rawSubtotal - extraDiscountAmount);
    const finalSubtotal = goodsSubtotal + shippingCost;
    const vatRate = 22;
    const vatAmount = finalSubtotal * (vatRate / 100);
    const grandTotal = finalSubtotal + vatAmount;

    // Quanto risparmierebbe se passasse a Carta
    const potentialCardPct = Number(EcomState.paymentRules.extraDiscountCardPct || 0);
    const potentialCardSaveNet = rawSubtotal * (potentialCardPct / 100);
    const potentialCardSaveGross = potentialCardSaveNet * 1.22;

    return {
      lines,
      totalItems,
      rawSubtotal,
      extraDiscountPct,
      extraDiscountAmount,
      goodsSubtotal,
      shippingCost,
      isPickup,
      deliveryType,
      finalSubtotal,
      vatRate,
      vatAmount,
      grandTotal,
      potentialCardPct,
      potentialCardSaveGross
    };
  }

  function updateOrderSummary() {
    const fin = calculateCartFinancials();

    const setTxt = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    setTxt('summaryItemsCount', String(fin.totalItems));
    setTxt('summaryRawSubtotal', `€ ${euro(fin.rawSubtotal)}`);

    const extraRow = document.getElementById('summaryExtraDiscountRow');
    if (extraRow) {
      if (fin.extraDiscountPct > 0) {
        extraRow.classList.remove('hidden');
        setTxt('summaryExtraDiscountLabel', `🎁 Sconto Extra Pagamento Anticipato (-${fin.extraDiscountPct}%):`);
        setTxt('summaryExtraDiscountVal', `- € ${euro(fin.extraDiscountAmount)}`);
      } else {
        extraRow.classList.add('hidden');
      }
    }

    // Gestione visualizzazione Spese Spedizione / Ritiro a Banco
    const shipVal = document.getElementById('summaryShippingVal');
    const shipLbl = document.getElementById('summaryShippingLabel');
    if (shipVal) {
      if (fin.isPickup) {
        shipVal.textContent = 'GRATIS (€ 0,00)';
        shipVal.style.color = '#059669';
      } else {
        shipVal.textContent = `€ ${euro(fin.shippingCost)}`;
        shipVal.style.color = '#0f172a';
      }
    }
    if (shipLbl) {
      shipLbl.textContent = fin.isPickup ? '🏬 Ritiro al Banco Magazzino (Firenze):' : '🚚 Spedizione Corriere Espresso (24/48h):';
    }

    setTxt('summarySubtotal', `€ ${euro(fin.finalSubtotal)}`);
    setTxt('summaryVat', `€ ${euro(fin.vatAmount)}`);
    setTxt('summaryGrandTotal', `€ ${euro(fin.grandTotal)}`);
    setTxt('btnStripeAmountText', `€ ${euro(fin.grandTotal)}`);

    // Upsell Banner nella tab B2B Ri.Ba.
    setTxt('b2bUpsellSaveEuro', `€ ${euro(fin.potentialCardSaveGross)}`);
    setTxt('b2bUpsellPct', `${fin.potentialCardPct}%`);

    // Riparto Stripe Connect
    const feePercent = parseFloat(document.getElementById('cfgStripeFeePercent')?.value || EcomState.stripeConfig.applicationFeePercent || 2.5);
    const feeAmount = fin.grandTotal * (feePercent / 100);
    const netToConnected = fin.grandTotal - feeAmount;

    setTxt('breakdownNetToConnected', `€ ${euro(netToConnected)}`);
    setTxt('breakdownFeeAmount', `€ ${euro(feeAmount)} (${feePercent}%)`);
    setTxt('btnStripePayLabel', `💳 Paga Subito € ${euro(fin.grandTotal)} (Risparmi € ${euro(fin.extraDiscountAmount * 1.22)})`);
  }

  // 9. PANNELLO CONFIGURAZIONE PAGAMENTI & SOCIAL MARKETING STUDIO
  function openPaymentAndSocialModal(initialTab = 'payments') {
    const r = EcomState.paymentRules;
    const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v; };
    const setChk = (id, v) => { const el = document.getElementById(id); if (el) el.checked = !!v; };

    setVal('cfgExtraDiscountCard', r.extraDiscountCardPct);
    setVal('cfgExtraDiscountBank', r.extraDiscountBankPct);
    setVal('cfgStandardShippingCost', r.standardShippingCost !== undefined ? r.standardShippingCost : 6.99);
    setVal('cfgCompanyIban', r.companyIban);
    setChk('cfgB2cAllowCard', r.b2cAllowCard);
    setChk('cfgB2cAllowPrepaidBank', r.b2cAllowPrepaidBank);
    setChk('cfgB2cAllowAssisted', r.b2cAllowAssisted);
    setVal('cfgB2bAccessMode', r.b2bAccessMode);
    setChk('cfgB2bTermRiba30', r.b2bTermRiba30);
    setChk('cfgB2bTermRiba60', r.b2bTermRiba60);
    setChk('cfgB2bTermRiba6090', r.b2bTermRiba6090);
    setChk('cfgB2bTermBonifico30', r.b2bTermBonifico30);
    setVal('cfgB2bWhitelist', r.b2bWhitelist);

    populateSocialStudioGenerator();
    switchCfgModalTab(initialTab);

    const modal = document.getElementById('paymentAndSocialModal');
    if (modal) modal.classList.add('active');
  }

  function closePaymentAndSocialModal() {
    const modal = document.getElementById('paymentAndSocialModal');
    if (modal) modal.classList.remove('active');
  }

  function switchCfgModalTab(tab) {
    const tPay = document.getElementById('tabCfgPayments');
    const tSoc = document.getElementById('tabCfgSocial');
    const pPay = document.getElementById('panelCfgPayments');
    const pSoc = document.getElementById('panelCfgSocial');

    tPay?.classList.toggle('active', tab === 'payments');
    tSoc?.classList.toggle('active', tab === 'social');
    pPay?.classList.toggle('hidden', tab !== 'payments');
    pSoc?.classList.toggle('hidden', tab !== 'social');
  }

  function savePaymentRulesFromModal() {
    EcomState.paymentRules = {
      extraDiscountCardPct: parseFloat(document.getElementById('cfgExtraDiscountCard')?.value) || 0,
      extraDiscountBankPct: parseFloat(document.getElementById('cfgExtraDiscountBank')?.value) || 0,
      standardShippingCost: parseFloat(document.getElementById('cfgStandardShippingCost')?.value) || 6.99,
      companyIban: (document.getElementById('cfgCompanyIban')?.value || '').trim(),
      b2cAllowCard: !!document.getElementById('cfgB2cAllowCard')?.checked,
      b2cAllowPrepaidBank: !!document.getElementById('cfgB2cAllowPrepaidBank')?.checked,
      b2cAllowAssisted: !!document.getElementById('cfgB2cAllowAssisted')?.checked,
      b2bAccessMode: document.getElementById('cfgB2bAccessMode')?.value || 'ALL_PIVA',
      b2bTermRiba30: !!document.getElementById('cfgB2bTermRiba30')?.checked,
      b2bTermRiba60: !!document.getElementById('cfgB2bTermRiba60')?.checked,
      b2bTermRiba6090: !!document.getElementById('cfgB2bTermRiba6090')?.checked,
      b2bTermBonifico30: !!document.getElementById('cfgB2bTermBonifico30')?.checked,
      b2bWhitelist: (document.getElementById('cfgB2bWhitelist')?.value || '').trim()
    };

    savePaymentRulesToStorage();
    applyPaymentRulesToUiBanners();
    updateCartIndicators();
    renderProductsGrid();
    closePaymentAndSocialModal();
    showToast('✅ Regole Pagamenti (B2B Ri.Ba. vs Privati) e Sconto Extra salvati!');
  }

  // Generatore Post Social & Link Carrello Pre-Caricato
  function populateSocialStudioGenerator() {
    const sel = document.getElementById('socialProductSelect');
    if (!sel) return;

    const top10 = EcomState.products.filter(p => p.isFeaturedTop10).slice(0, 10);
    let html = '';
    if (EcomState.cart.length > 0) {
      html += `<option value="__CURRENT_CART__">🛒 Usa il Pacchetto di Articoli attualmente nel Carrello (${EcomState.cart.length} art.)</option>`;
    }
    html += top10.map(p => `<option value="${escapeHtml(p.code)}">⭐ [${escapeHtml(p.code)}] ${escapeHtml(p.seoTitle || p.description)} — € ${euro(p.price)}</option>`).join('');
    sel.innerHTML = html;

    generateSocialPostAndLink();
  }

  function generateSocialPostAndLink() {
    const selVal = document.getElementById('socialProductSelect')?.value;
    const target = document.getElementById('socialTargetSelect')?.value || 'FB_IG_B2C';
    const baseUrl = `${window.location.origin}/e-com/`;
    const agent = EcomState.context.agentCode || '1136';
    const cardPct = Number(EcomState.paymentRules.extraDiscountCardPct || 4);

    let shareLink = '';
    let copyText = '';

    if (selVal === '__CURRENT_CART__' && EcomState.cart.length > 0) {
      const lines = getResolvedCartLines();
      const cartParam = lines.map(l => `${l.code}:${l.qty}`).join(',');
      shareLink = `${baseUrl}?cart=${encodeURIComponent(cartParam)}&agent=${encodeURIComponent(agent)}`;
      const rawSum = lines.reduce((a, l) => a + l.lineSubtotal, 0);
      const discSum = rawSum * (1 - cardPct / 100);
      const itemsListTxt = lines.map(l => `✅ ${l.qty}x ${l.title} (Cod. ${l.code})`).join('\n');

      copyText = [
        `🔥 KIT OFFERTA PRONTA CONSEGNA CLIMAWELL 🔥`,
        ``,
        `Abbiamo preparato un pacchetto completo pronto per la spedizione in 24/48h:`,
        itemsListTxt,
        ``,
        `💶 Totale Netto Vetrina: € ${euro(rawSum)} + IVA`,
        `🎁 EXTRA SCONTO -${cardPct}% PAGAMENTO IMMEDIATO: Paghi solo € ${euro(discSum)} + IVA se saldi ora online con Carta!`,
        `🏢 Sei un installatore o azienda B2B abilitata? Puoi ordinare anche con le tue condizioni Ri.Ba. 60-90gg.`,
        ``,
        `👇 Clicca qui per aprire il carrello già pronto e confermare in 30 secondi:`,
        shareLink
      ].join('\n');
    } else {
      const prod = getProductByCode(selVal) || EcomState.products[0];
      if (!prod) return;
      shareLink = `${baseUrl}?prodotto=${encodeURIComponent(prod.code)}&agent=${encodeURIComponent(agent)}`;
      const discountedPrice = prod.price * (1 - cardPct / 100);
      const hlTxt = (prod.highlights && prod.highlights.length)
        ? prod.highlights.map(h => `✔️ ${h}`).join('\n')
        : `✔️ Pronta consegna magazzino Climawell\n✔️ Garanzia Ufficiale Italia`;

      if (target === 'FB_IG_B2C') {
        copyText = [
          `✨ OFFERTA SELEZIONATA CLIMAWELL STORE ✨`,
          `📦 ${prod.seoTitle || prod.description}`,
          ``,
          hlTxt,
          ``,
          `❌ Listino: € ${euro(prod.listPrice)}`,
          `✅ Prezzo Vetrina: € ${euro(prod.price)} + IVA`,
          `🎁 SCONTO EXTRA -${cardPct}% PAGAMENTO IMMEDIATO: Solo € ${euro(discountedPrice)} + IVA pagando online con Carta!`,
          `🚚 Spedizione rapida in 24/48h in tutta Italia o ritiro in sede.`,
          ``,
          `🛒 Acquista ora in autonomia dal nostro Store Ufficiale:`,
          shareLink,
          ``,
          `#Climawell #Climatizzazione #PompeDiCalore #ArredoBagno #ProntaConsegna`
        ].join('\n');
      } else if (target === 'LINKEDIN_B2B') {
        copyText = [
          `🔧 FORNITURA RAPIDA B2B PER INSTALLATORI & IMPRESE — ${prod.brand}`,
          `Articolo Cod. ${prod.code}: ${prod.seoTitle || prod.description}`,
          ``,
          hlTxt,
          ``,
          `💼 Condizioni riservate su Climawell Store:`,
          `• Prezzo Netto Vetrina: € ${euro(prod.price)} + IVA`,
          `• Scegli tu al Checkout: usa il tuo pagamento abituale B2B (Ri.Ba. 60-90gg per clienti abilitati) oppure approfitta del -${cardPct}% di SCONTO EXTRA CASSA (€ ${euro(discountedPrice)} + IVA) con pagamento immediato!`,
          ``,
          `👉 Genera il tuo ordine in 1 clic (con spedizione diretta anche in cantiere):`,
          shareLink
        ].join('\n');
      } else {
        copyText = [
          `Ciao! 👋 Ti segnalo questa promo in pronta consegna su *Climawell Store*:`,
          `*${prod.seoTitle || prod.description}* (Cod. ${prod.code})`,
          `💶 Netto: *€ ${euro(prod.price)}* (+IVA) — oppure *€ ${euro(discountedPrice)}* con *-${cardPct}% Sconto Extra Pagamento Immediato*!`,
          `Clicca qui per vedere la scheda o aggiungerlo al carrello: ${shareLink}`
        ].join('\n');
      }
    }

    const linkInput = document.getElementById('socialGeneratedLink');
    const copyArea = document.getElementById('socialGeneratedCopy');
    const embedBox = document.getElementById('websiteEmbedCodeBox');

    if (linkInput) linkInput.value = shareLink;
    if (copyArea) copyArea.value = copyText;
    if (embedBox) {
      embedBox.value = `<!-- Vetrina E-Commerce Climawell Top 10 con Carrello & Sconto Extra -->\n<iframe src="${baseUrl}?agent=${encodeURIComponent(agent)}" width="100%" height="950" style="border:0; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,0.08);" loading="lazy" title="Climawell Store Online"></iframe>`;
    }
  }

  // 10. CONFIGURATORE VETRINA TOP 10 & SEO
  function openVetrinaManagerModal() {
    renderVetrinaManagerList();
    populateManagerCatalogSelect('');
    updateSeoStructuredDataAndMeta();
    const modal = document.getElementById('vetrinaManagerModal');
    if (modal) modal.classList.add('active');
  }

  function closeVetrinaManagerModal() {
    const modal = document.getElementById('vetrinaManagerModal');
    if (modal) modal.classList.remove('active');
  }

  function populateManagerCatalogSelect(query) {
    const sel = document.getElementById('managerCatalogSelect');
    if (!sel) return;
    const q = String(query || '').toLowerCase().trim();
    const topCodes = new Set(EcomState.top10Config.map(c => String(c.code).toUpperCase()));

    const matches = EcomState.products
      .filter(p => !topCodes.has(p.code.toUpperCase()))
      .filter(p => !q || p.code.toLowerCase().includes(q) || p.description.toLowerCase().includes(q) || p.brand.toLowerCase().includes(q))
      .slice(0, 80);

    sel.innerHTML = `<option value="">-- Seleziona un articolo dal listino (${matches.length} mostrati) --</option>` +
      matches.map(p => `<option value="${escapeHtml(p.code)}">[${escapeHtml(p.code)}] ${escapeHtml(p.description)} — € ${euro(p.price)} (${escapeHtml(p.brand)})</option>`).join('');
  }

  function switchVetrinaTab(tab) {
    const tabs = {
      current: { btn: 'tabVetrinaCurrent', panel: 'panelVetrinaCurrent' },
      search: { btn: 'tabVetrinaSearch', panel: 'panelVetrinaSearch' },
      manual: { btn: 'tabVetrinaManual', panel: 'panelVetrinaManual' }
    };

    Object.keys(tabs).forEach(k => {
      const b = document.getElementById(tabs[k].btn);
      const p = document.getElementById(tabs[k].panel);
      if (k === tab) {
        b?.classList.add('active');
        p?.classList.remove('hidden');
        p?.classList.add('active');
      } else {
        b?.classList.remove('active');
        p?.classList.add('hidden');
        p?.classList.remove('active');
      }
    });

    if (tab === 'search') {
      const q = document.getElementById('managerCatalogLiveSearch')?.value || '';
      renderCatalogSearchResults(q);
      setTimeout(() => document.getElementById('managerCatalogLiveSearch')?.focus(), 80);
    } else if (tab === 'current') {
      renderVetrinaManagerList();
    }
  }

  function renderCatalogSearchResults(query) {
    const container = document.getElementById('catalogSearchResultsGrid');
    if (!container) return;

    const q = String(query || '').toLowerCase().trim();
    const topCodes = new Set(EcomState.top10Config.map(c => String(c.code).toUpperCase()));

    // Elenco prodotti disponibili nel catalogo non ancora in vetrina
    const matches = (EcomState.products || [])
      .filter(p => !topCodes.has(p.code.toUpperCase()))
      .filter(p => !q || p.code.toLowerCase().includes(q) || (p.description || '').toLowerCase().includes(q) || (p.brand || '').toLowerCase().includes(q))
      .slice(0, 60);

    if (matches.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align:center; padding:30px; color:#64748b; font-size:0.85rem;">
          ${q ? `Nessun articolo trovato per "<strong>${escapeHtml(q)}</strong>". Prova a cercare per codice o marca.` : 'Nessun articolo disponibile da aggiungere o tutti gli articoli sono già in vetrina.'}
        </div>
      `;
      return;
    }

    container.innerHTML = matches.map(p => {
      const thumb = p.imageUrl || getSmartProductVisual(p);
      return `
        <div class="catalog-result-card">
          <img src="${thumb}" alt="${escapeHtml(p.code)}" class="catalog-card-thumb" onerror="this.onerror=null; this.src='${getSmartProductVisual(p)}'">
          <div class="catalog-card-info">
            <div class="catalog-card-code">${escapeHtml(p.code)} · ${escapeHtml(p.brand || 'CLIMAWELL')}</div>
            <div class="catalog-card-title" title="${escapeHtml(p.description)}">${escapeHtml(p.description)}</div>
            <div class="catalog-card-price">€ ${euro(p.price)} <small style="color:#64748b; font-weight:normal;">+ IVA</small></div>
          </div>
          <button type="button" class="btn-add-to-top" style="background:#0284c7; color:#fff; border:none; border-radius:6px; font-weight:700; cursor:pointer;" onclick="window.ClwEcomAddProductToTop10('${escapeHtml(p.code)}')">
            + Metti in Vetrina
          </button>
        </div>
      `;
    }).join('');
  }

  window.ClwEcomAddProductToTop10 = function(code) {
    if (EcomState.top10Config.length >= 24) {
      showToast('⚠️ Hai già 20 articoli in vetrina. Rimuovine uno prima di aggiungerne un altro.');
      return;
    }
    const found = (EcomState.products || []).find(p => p.code.toUpperCase() === String(code).toUpperCase());
    if (!found) {
      showToast('⚠️ Articolo non trovato nel catalogo.');
      return;
    }

    EcomState.top10Config.push({
      code: found.code,
      seoTitle: found.description,
      seoDescription: found.description,
      highlights: getDefaultHighlights(found),
      badge: '🖤 Black Friday Promo',
      brand: found.brand || 'CLIMAWELL',
      family: found.family || 'CLIMA',
      price: found.price || 0,
      listPrice: found.listPrice || (found.price ? found.price * 1.3 : 0),
      stock: found.stock || 10,
      imageUrl: found.imageUrl || ''
    });

    renderVetrinaManagerList();
    switchVetrinaTab('current');
    showToast(`✅ Articolo "${found.code}" aggiunto alla Vetrina! Modifica il prezzo se necessario.`);
  };

  window.ClwEcomMoveTop10 = function(index, direction) {
    const newIdx = index + direction;
    if (newIdx < 0 || newIdx >= EcomState.top10Config.length) return;
    const item = EcomState.top10Config.splice(index, 1)[0];
    EcomState.top10Config.splice(newIdx, 0, item);
    renderVetrinaManagerList();
  };

  window.ClwEcomRemoveTop10 = function(index) {
    EcomState.top10Config.splice(index, 1);
    renderVetrinaManagerList();
    showToast('🗑 Articolo rimosso dalla Vetrina.');
  };

  function renderVetrinaManagerList() {
    const tbody = document.getElementById('managerTop10TableBody');
    const container = document.getElementById('managerTop10List');
    const counter = document.getElementById('managerTop10Counter');
    const list = EcomState.top10Config.slice(0, 24);

    if (counter) counter.textContent = `${list.length} / 12`;

    // 1. Rendering Tabella se presente managerTop10TableBody (layout index-amm.html)
    if (tbody) {
      if (list.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="8" style="text-align:center; padding:30px; color:#64748b;">
              Nessun articolo in vetrina al momento. Clicca in alto su <strong>"🔍 Cerca e Aggiungi dal Listino Generale"</strong> per sceglierne uno!
            </td>
          </tr>
        `;
      } else {
        tbody.innerHTML = list.map((item, idx) => {
          const thumbSrc = item.imageUrl || getSmartProductVisual(item);
          const titleVal = item.seoTitle || item.description || '';
          const priceVal = Number(item.price || 0);
          const listPriceVal = Number(item.listPrice || (priceVal * 1.3));
          const stockVal = Number(item.stock !== undefined ? item.stock : 10);

          return `
            <tr data-idx="${idx}">
              <td style="text-align:center;">
                <div style="display:flex; flex-direction:column; align-items:center; gap:2px;">
                  <button type="button" style="border:none; background:none; cursor:pointer; font-size:0.75rem; color:#64748b;" onclick="window.ClwEcomMoveTop10(${idx}, -1)" ${idx === 0 ? 'disabled style="opacity:0.2;"' : ''} title="Sposta su">▲</button>
                  <strong style="font-size:0.8rem; color:#0f172a;">#${idx + 1}</strong>
                  <button type="button" style="border:none; background:none; cursor:pointer; font-size:0.75rem; color:#64748b;" onclick="window.ClwEcomMoveTop10(${idx}, 1)" ${idx === list.length - 1 ? 'disabled style="opacity:0.2;"' : ''} title="Sposta giù">▼</button>
                </div>
              </td>
              <td style="text-align:center;">
                <img src="${thumbSrc}" alt="${escapeHtml(item.code)}" style="width:40px; height:40px; object-fit:contain; border-radius:4px; background:#f8fafc; border:1px solid #e2e8f0;" onerror="this.onerror=null; this.src='${getSmartProductVisual(item)}'">
              </td>
              <td>
                <strong style="font-family:monospace; color:#0284c7; display:block; font-size:0.85rem;">${escapeHtml(item.code)}</strong>
                <small style="color:#64748b;">${escapeHtml(item.brand || 'CLIMAWELL')}</small>
              </td>
              <td>
                <input type="text" class="vetrina-input-title" data-field="seoTitle" data-idx="${idx}" value="${escapeHtml(titleVal)}" placeholder="Titolo mostrato in vetrina...">
              </td>
              <td style="text-align:right;">
                <input type="number" step="0.01" class="vetrina-input-price" data-field="price" data-idx="${idx}" value="${priceVal.toFixed(2)}" title="Prezzo netto promozionale">
              </td>
              <td style="text-align:right;">
                <input type="number" step="0.01" class="vetrina-input-listprice" data-field="listPrice" data-idx="${idx}" value="${listPriceVal.toFixed(2)}" title="Prezzo di listino barrato">
              </td>
              <td style="text-align:center;">
                <input type="number" class="vetrina-input-stock" data-field="stock" data-idx="${idx}" value="${stockVal}" title="Pezzi disponibili" style="width:55px;">
              </td>
              <td style="text-align:center;">
                <button type="button" style="background:#fee2e2; color:#dc2626; border:1px solid #fca5a5; border-radius:6px; padding:6px 10px; font-size:0.8rem; cursor:pointer; font-weight:700;" onclick="window.ClwEcomRemoveTop10(${idx})" title="Rimuovi questo articolo dalla vetrina">
                  🗑️
                </button>
              </td>
            </tr>
          `;
        }).join('');

        tbody.querySelectorAll('input[data-field]').forEach(inp => {
          inp.addEventListener('input', () => {
            const i = parseInt(inp.getAttribute('data-idx'), 10);
            const field = inp.getAttribute('data-field');
            if (!EcomState.top10Config[i]) return;
            if (field === 'price' || field === 'listPrice') {
              EcomState.top10Config[i][field] = parseFloat(inp.value) || 0;
            } else if (field === 'stock') {
              EcomState.top10Config[i][field] = parseInt(inp.value, 10) || 0;
            } else {
              EcomState.top10Config[i][field] = inp.value;
            }
          });
        });
      }
    }

    // 2. Rendering Box Cards se presente managerTop10List
    if (container) {
      container.innerHTML = list.map((item, idx) => {
        const thumbSrc = item.imageUrl || getSmartProductVisual(item);
        return `
          <div class="manager-item-card" data-idx="${idx}">
            <img src="${thumbSrc}" alt="${escapeHtml(item.code)}" class="manager-item-thumb" id="mgrThumb_${idx}" onerror="this.onerror=null; this.src='${getSmartProductVisual(item)}'">
            <div class="manager-item-fields">
              <div>
                <label>#${idx + 1} Codice Articolo (SKU/MPN):</label>
                <input type="text" data-field="code" data-idx="${idx}" value="${escapeHtml(item.code)}">
              </div>
              <div>
                <label>Marca &amp; Prezzo Netto (€):</label>
                <div style="display:flex; gap:6px;">
                  <input type="text" data-field="brand" data-idx="${idx}" value="${escapeHtml(item.brand || 'CLIMAWELL')}" placeholder="Marca" style="width:55%;">
                  <input type="number" step="0.01" data-field="price" data-idx="${idx}" value="${Number(item.price || 0)}" placeholder="Prezzo €" style="width:45%;">
                </div>
              </div>
              <div class="full">
                <label>Titolo Commerciale SEO (mostrato in vetrina e su Google Search):</label>
                <input type="text" data-field="seoTitle" data-idx="${idx}" value="${escapeHtml(item.seoTitle || item.description || '')}">
              </div>
              <div class="full">
                <label>URL Foto Prodotto (incolla link https://... oppure lascia vuoto per illustrazione automatica):</label>
                <input type="url" data-field="imageUrl" data-idx="${idx}" value="${escapeHtml(item.imageUrl || '')}" placeholder="https://.../foto-articolo.jpg">
              </div>
              <div class="full">
                <label>Descrizione Breve SEO (Meta Description &amp; Scheda):</label>
                <input type="text" data-field="seoDescription" data-idx="${idx}" value="${escapeHtml(item.seoDescription || '')}">
              </div>
            </div>
            <div style="display:flex; flex-direction:column; gap:6px;">
              <button type="button" class="btn-remove-top10" data-remove-idx="${idx}">🗑 Rimuovi</button>
            </div>
          </div>
        `;
      }).join('');

      container.querySelectorAll('input[data-field]').forEach(inp => {
        inp.addEventListener('input', () => {
          const i = parseInt(inp.getAttribute('data-idx'), 10);
          const field = inp.getAttribute('data-field');
          if (!EcomState.top10Config[i]) return;
          if (field === 'price') {
            EcomState.top10Config[i].price = parseFloat(inp.value) || 0;
          } else {
            EcomState.top10Config[i][field] = inp.value;
          }
          if (field === 'imageUrl' || field === 'brand') {
            const thumb = document.getElementById(`mgrThumb_${i}`);
            if (thumb) {
              thumb.src = EcomState.top10Config[i].imageUrl || getSmartProductVisual(EcomState.top10Config[i]);
            }
          }
        });
      });

      container.querySelectorAll('[data-remove-idx]').forEach(btn => {
        btn.addEventListener('click', () => {
          const i = parseInt(btn.getAttribute('data-remove-idx'), 10);
          EcomState.top10Config.splice(i, 1);
          renderVetrinaManagerList();
          populateManagerCatalogSelect(document.getElementById('managerCatalogSearch')?.value || '');
        });
      });
    }
  }

  // 11. INVIO E SALVATAGGIO ORDINE MULTI-RIGA (Carta Stripe, Bonifico Anticipato, Ri.Ba. 60-90gg B2B, WhatsApp, Email)
  function collectCustomerFormData() {
    return {
      buyerType: EcomState.buyerType,
      deliveryType: document.getElementById('orderDeliveryType')?.value || 'SPEDIZIONE_SEDE',
      customerName: (document.getElementById('orderCustomerInput')?.value || '').trim(),
      taxId: (document.getElementById('orderTaxIdInput')?.value || '').trim(),
      email: (document.getElementById('orderEmailInput')?.value || '').trim(),
      phone: (document.getElementById('orderPhoneInput')?.value || '').trim(),
      sdi: (document.getElementById('orderSdiInput')?.value || '').trim(),
      address: (document.getElementById('orderAddressInput')?.value || '').trim(),
      cap: (document.getElementById('orderCapInput')?.value || '').trim(),
      city: (document.getElementById('orderCityInput')?.value || '').trim(),
      province: (document.getElementById('orderProvinceInput')?.value || '').trim().toUpperCase(),
      agent: (document.getElementById('orderAgentInput')?.value || '1136').trim(),
      b2bDeferredTerm: document.getElementById('b2bDeferredTermSelect')?.value || 'RI.BA. 60-90 GG D.F.F.M.',
      notes: (document.getElementById('orderNotesInput')?.value || '').trim()
    };
  }

  function validateCustomerForm(data) {
    const fin = calculateCartFinancials();
    if (fin.lines.length === 0) {
      showToast('⚠️ Il carrello è vuoto! Aggiungi almeno un articolo.');
      return false;
    }
    const privacyCheck = document.getElementById('orderPrivacyConsent');
    if (privacyCheck && !privacyCheck.checked) {
      showToast('⚠️ È necessario accettare l\'Informativa sulla Privacy per completare l\'ordine');
      privacyCheck.focus();
      return false;
    }
    if (!data.customerName) {
      showToast('⚠️ Inserisci Nome/Cognome o Ragione Sociale dell\'acquirente');
      document.getElementById('orderCustomerInput')?.focus();
      return false;
    }
    if (!data.taxId) {
      showToast('⚠️ Inserisci Codice Fiscale o Partita IVA per la fatturazione');
      document.getElementById('orderTaxIdInput')?.focus();
      return false;
    }
    if (!data.email || !data.email.includes('@')) {
      showToast('⚠️ Inserisci un indirizzo Email valido per ricevere la conferma d\'ordine');
      document.getElementById('orderEmailInput')?.focus();
      return false;
    }
    if (!data.phone) {
      showToast('⚠️ Inserisci un recapito telefonico per il corriere');
      document.getElementById('orderPhoneInput')?.focus();
      return false;
    }
    if (data.deliveryType !== 'RITIRO_BANCO' && (!data.address || !data.city || !data.cap)) {
      showToast('⚠️ Compila Via, CAP e Città per la spedizione della merce');
      document.getElementById('orderAddressInput')?.focus();
      return false;
    }
    return true;
  }

  function buildOrderMessage(paymentDescription) {
    const f = collectCustomerFormData();
    const fin = calculateCartFinancials();

    const itemLinesTxt = fin.lines.map((l, idx) =>
      `${idx + 1}. *${l.code}* — ${l.title} (x${l.qty} pz) = € ${euro(l.lineSubtotal)}`
    );

    const lines = [
      `📦 *NUOVO ORDINE CLIMAWELL STORE (${f.buyerType})*`,
      `----------------------------------`,
      ...itemLinesTxt,
      `----------------------------------`,
      `🔹 *Totale Merce Listino Netto:* € ${euro(fin.rawSubtotal)}`,
      ...(fin.extraDiscountPct > 0 ? [`🎁 *Sconto Extra Pagamento Anticipato (-${fin.extraDiscountPct}%):* - € ${euro(fin.extraDiscountAmount)}`] : []),
      `🚚 *Spese di Spedizione:* ${fin.isPickup ? 'GRATIS (Ritiro al banco Firenze)' : '€ ' + euro(fin.shippingCost)}`,
      `🔹 *Imponibile Netto Finale:* € ${euro(fin.finalSubtotal)}`,
      `🔹 *Totale Ordine IVA Inclusa:* € ${euro(fin.grandTotal)}`,
      `💳 *Condizione Pagamento:* ${paymentDescription}`,
      `----------------------------------`,
      `🏢 *Acquirente (${f.buyerType}):* ${f.customerName}`,
      `🧾 *P.IVA / C.F.:* ${f.taxId} ${f.sdi ? '(SDI/PEC: ' + f.sdi + ')' : ''}`,
      `📧 *Email:* ${f.email}`,
      `📞 *Tel:* ${f.phone}`,
      `🚚 *Consegna:* ${f.deliveryType} — ${f.address}, ${f.cap} ${f.city} (${f.province})`,
      `🧑‍💼 *Agente Riferimento:* ${f.agent}`
    ];

    if (f.notes) lines.push(`📝 *Note Consegna:* ${f.notes}`);

    return {
      text: lines.join('\n'),
      customer: f.customerName,
      agent: f.agent,
      financials: fin,
      formData: f
    };
  }

  // Salvataggio Ordine con Bonifico Anticipato (-2% Extra)
  async function confirmPrepaidBankOrder() {
    const f = collectCustomerFormData();
    if (!validateCustomerForm(f)) return;

    const fin = calculateCartFinancials();
    const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const rand = Math.floor(100000 + Math.random() * 900000);
    const orderNumber = `ORD-${f.agent}-${timestamp}-${rand}`;
    const paymentLabel = `BONIFICO ANTICIPATO (Sconto Extra -${fin.extraDiscountPct}%)`;

    const savedDoc = await logOrderCrm('bonifico_anticipato', f.customerName, fin, f.agent, {
      order_number: orderNumber,
      payment_label: paymentLabel,
      stripe_charge_id: `BONIFICO-ANT-${rand}`
    }, f);

    clearCart();
    closeOrderModal();
    openStripeReceiptModal({
      title: 'Ordine con Bonifico Anticipato Registrato!',
      subtitle: `Effettua il bonifico su IBAN ${EcomState.paymentRules.companyIban} indicando il numero ordine`,
      orderId: savedDoc?.id || '',
      orderNumber,
      chargeId: paymentLabel,
      connectedAccount: EcomState.paymentRules.companyIban,
      productDesc: fin.lines.map(l => `${l.code} (x${l.qty})`).join(', '),
      qty: fin.totalItems,
      grandTotal: fin.grandTotal,
      feeText: fin.extraDiscountPct > 0 ? `Sconto Extra -${fin.extraDiscountPct}% (-€ ${euro(fin.extraDiscountAmount)})` : 'Nessuno sconto extra',
      customer: `${f.customerName} (${f.taxId})`,
      shippingDest: f.deliveryType === 'RITIRO_BANCO' ? 'Ritiro al Banco Magazzino Climawell' : `${f.address}, ${f.cap} ${f.city} (${f.province})`,
      agent: f.agent
    });
    showToast('✅ Ordine con Bonifico Anticipato registrato con Sconto Extra!');
  }

  // Salvataggio Ordine B2B con Pagamento Dilazionato (Ri.Ba. 60-90gg)
  async function confirmB2bDeferredOrder() {
    const b2bCheck = isCustomerAuthorizedForB2bDeferred();
    if (!b2bCheck.allowed) {
      showToast('⚠️ ' + b2bCheck.reason);
      return;
    }

    const f = collectCustomerFormData();
    if (!validateCustomerForm(f)) return;

    const fin = calculateCartFinancials();
    const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const rand = Math.floor(100000 + Math.random() * 900000);
    const orderNumber = `ORD-${f.agent}-${timestamp}-${rand}`;
    const paymentLabel = `${f.b2bDeferredTerm} (Cliente B2B P.IVA)`;

    const savedDoc = await logOrderCrm('b2b_riba_deferred', f.customerName, fin, f.agent, {
      order_number: orderNumber,
      payment_label: paymentLabel,
      stripe_charge_id: f.b2bDeferredTerm
    }, f);

    clearCart();
    closeOrderModal();
    openStripeReceiptModal({
      title: 'Ordine B2B Registrato con Successo!',
      subtitle: `Condizione di pagamento applicata: ${f.b2bDeferredTerm}`,
      orderId: savedDoc?.id || '',
      orderNumber,
      chargeId: f.b2bDeferredTerm,
      connectedAccount: 'Contabilità B2B Climawell S.r.l.',
      productDesc: fin.lines.map(l => `${l.code} (x${l.qty})`).join(', '),
      qty: fin.totalItems,
      grandTotal: fin.grandTotal,
      feeText: `Condizione B2B: ${f.b2bDeferredTerm}`,
      customer: `${f.customerName} (P.IVA ${f.taxId})`,
      shippingDest: f.deliveryType === 'RITIRO_BANCO' ? 'Ritiro al Banco Magazzino Climawell' : `${f.address}, ${f.cap} ${f.city} (${f.province})`,
      agent: f.agent
    });
    showToast(`✅ Ordine B2B (${f.b2bDeferredTerm}) inviato al Magazzino!`);
  }

  function sendOrderViaWhatsApp() {
    const f = collectCustomerFormData();
    if (!validateCustomerForm(f)) return;

    const payDesc = EcomState.buyerType === 'B2B' ? f.b2bDeferredTerm : 'Ordine Assistito';
    const order = buildOrderMessage(payDesc);
    logOrderCrm('whatsapp', order.customer, order.financials, order.agent, { payment_label: payDesc }, f);

    const companyPhone = (window.CLIMAWELL_CONFIG && window.CLIMAWELL_CONFIG.whatsappOrderPhone) || '393881299371';
    const waUrl = `https://wa.me/${companyPhone}?text=${encodeURIComponent(order.text)}`;
    window.open(waUrl, '_blank');
    clearCart();
    showToast('Riepilogo carrello aperto su WhatsApp!');
    closeOrderModal();
  }

  function sendOrderViaEmail() {
    const f = collectCustomerFormData();
    if (!validateCustomerForm(f)) return;

    const payDesc = EcomState.buyerType === 'B2B' ? f.b2bDeferredTerm : 'Ordine Assistito';
    const order = buildOrderMessage(payDesc);
    logOrderCrm('email', order.customer, order.financials, order.agent, { payment_label: payDesc }, f);

    const targetEmail = 'commerciale@climawell.it';
    const codesSummary = order.financials.lines.map(l => l.code).join(', ');
    const subject = `Ordine Store Climawell (${codesSummary}) - Cliente ${order.customer}`;
    const body = order.text.replace(/\*/g, '');
    window.location.href = `mailto:${targetEmail}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    clearCart();
    showToast('Client Email aperto con il riepilogo ordine!');
    closeOrderModal();
  }

  // Pagamento Immediato con Carta: Disabilitata simulazione di test per la sicurezza operativa
  async function processStripeDirectCharge() {
    showToast('ℹ️ Il terminale per carte di credito è in fase di certificazione bancaria Stripe. Seleziona "Bonifico Bancario Anticipato" per confermare subito l\'ordine con lo Sconto Extra (-4%)!', 6000);
    switchPaymentMethodTab('prepaid_bank');
  }

  function openStripeReceiptModal(data) {
    const setTxt = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    if (data.title) setTxt('receiptModalTitle', data.title);
    if (data.subtitle) setTxt('receiptModalSubtitle', data.subtitle);
    setTxt('receiptOrderNumber', data.orderNumber || 'ORD-ECOM');
    setTxt('receiptChargeId', data.chargeId);
    setTxt('receiptConnectedAccount', data.connectedAccount);
    setTxt('receiptProductDesc', data.productDesc);
    setTxt('receiptQty', `${data.qty} pz`);
    setTxt('receiptTotalAmount', `€ ${euro(data.grandTotal)}`);
    setTxt('receiptFeeAmount', data.feeText || '');
    setTxt('receiptCustomerName', data.customer);
    setTxt('receiptShippingDest', data.shippingDest || '-');
    setTxt('receiptAgentCode', data.agent);

    const trackBtn = document.getElementById('btnGoToTracking');
    if (trackBtn) {
      const trackParam = data.orderNumber ? `num=${encodeURIComponent(data.orderNumber)}` : `id=${encodeURIComponent(data.orderId)}`;
      trackBtn.href = `/tracking-ordine.html?${trackParam}`;
    }

    const modal = document.getElementById('stripeReceiptModal');
    if (modal) modal.classList.add('active');
  }

  // Registrazione Multi-Riga su Supabase (documents + document_lines) e LocalStorage per Gestione Ordini & Magazzino
  async function logOrderCrm(channel, customerName, financials, agentCode, paymentDetails = null, formData = null) {
    try {
      const f = formData || collectCustomerFormData();
      const fin = financials || calculateCartFinancials();
      const orderNum = paymentDetails?.order_number || `ORD-${agentCode}-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${Math.floor(100000 + Math.random() * 900000)}`;
      const discountFactor = 1 - (fin.extraDiscountPct / 100);

      // Costruisce tutte le righe articolo (document_lines) per il magazzino / picking / DDT
      const documentLinesPayload = fin.lines.map((l, idx) => {
        const netUnitAfterExtra = Number((l.unitPrice * discountFactor).toFixed(2));
        const lineTotAfterExtra = Number((netUnitAfterExtra * l.qty).toFixed(2));
        return {
          line_number: idx + 1,
          product_code: l.code,
          description: l.title,
          brand: l.brand,
          qty: l.qty,
          unit_list_price: Number(l.unitListPrice.toFixed(2)),
          discount_1: fin.extraDiscountPct,
          unit_net_price: netUnitAfterExtra,
          line_total: lineTotAfterExtra,
          vat_rate: l.vat || 22
        };
      });

      const paymentTermsText = paymentDetails?.payment_label ||
        (channel === 'stripe_direct_charge' ? `CARTA STRIPE (${paymentDetails?.stripe_charge_id})` : `ORDINE E-COM (${channel.toUpperCase()})`);

      let savedDoc = null;
      if (window.ClwData && typeof window.ClwData.createDocument === 'function') {
        try {
          savedDoc = await window.ClwData.createDocument(
            {
              doc_type: 'order',
              doc_number: orderNum,
              status: channel === 'stripe_direct_charge' ? 'approved' : 'submitted',
              customer_name: customerName,
              agent_code: agentCode,
              agent_name: `Agente ${agentCode}`,
              total_net: Number(fin.finalSubtotal.toFixed(2)),
              vat_rate: fin.vatRate,
              total_vat: Number(fin.vatAmount.toFixed(2)),
              total_gross: Number(fin.grandTotal.toFixed(2)),
              payment_terms: paymentTermsText,
              shipping_address: f.address || 'Ritiro a Banco',
              shipping_city: f.city ? `${f.cap} ${f.city} (${f.province})` : '',
              carrier_name: f.deliveryType || 'CORRIERE ESPRESSO',
              notes: [
                `Profilo: ${f.buyerType}`,
                `CF/PIVA: ${f.taxId}`,
                fin.extraDiscountPct > 0 ? `Sconto Extra Pag. Immediato: -${fin.extraDiscountPct}% (-€ ${euro(fin.extraDiscountAmount)})` : '',
                f.email ? `Email: ${f.email}` : '',
                f.phone ? `Tel: ${f.phone}` : '',
                f.sdi ? `SDI/PEC: ${f.sdi}` : '',
                f.notes ? `Note: ${f.notes}` : ''
              ].filter(Boolean).join(' | ')
            },
            documentLinesPayload
          );
        } catch (dbErr) {
          console.warn('[E-COM] Salvataggio diretto documents non riuscito, uso fallback locale:', dbErr);
        }
      }

      const firstLine = fin.lines[0] || { code: 'ART', title: 'Articoli Carrello' };
      const summaryCodes = fin.lines.map(l => `${l.code} (x${l.qty})`).join(', ');

      const localOrders = JSON.parse(localStorage.getItem('clw_ecom_orders_local') || '[]');
      const localRecord = {
        id: savedDoc?.id || ('loc_' + Date.now()),
        doc_number: orderNum,
        created_at: new Date().toISOString(),
        status: channel === 'stripe_direct_charge' ? 'approved' : 'submitted',
        customer_name: customerName,
        buyer_type: f.buyerType,
        tax_id: f.taxId,
        email: f.email,
        phone: f.phone,
        sdi: f.sdi,
        agent_code: agentCode,
        payment_terms: paymentTermsText,
        shipping_address: f.address,
        shipping_city: `${f.cap || ''} ${f.city || ''} (${f.province || ''})`.trim(),
        delivery_type: f.deliveryType,
        product_code: firstLine.code,
        product_desc: fin.lines.length > 1 ? `Carrello (${fin.lines.length} art.): ${summaryCodes}` : firstLine.title,
        qty: fin.totalItems,
        total_net: Number(fin.finalSubtotal.toFixed(2)),
        total_gross: Number(fin.grandTotal.toFixed(2)),
        extra_discount_pct: fin.extraDiscountPct,
        stripe_charge_id: paymentDetails?.stripe_charge_id || null,
        document_lines: documentLinesPayload,
        notes: f.notes
      };
      localOrders.unshift(localRecord);
      localStorage.setItem('clw_ecom_orders_local', JSON.stringify(localOrders.slice(0, 50)));
      localStorage.setItem(`clw_doc_lines_${orderNum}`, JSON.stringify(documentLinesPayload));

      if (window.ClwData && typeof window.ClwData.saveOrder === 'function') {
        await window.ClwData.saveOrder({
          source: 'ECOM_B2B',
          channel,
          orderNumber: orderNum,
          agentCode,
          customerName,
          buyerType: f.buyerType,
          taxId: f.taxId,
          email: f.email,
          phone: f.phone,
          paymentTerms: paymentTermsText,
          shippingAddress: `${f.address}, ${f.cap} ${f.city} (${f.province})`,
          items: documentLinesPayload.map(dl => ({
            code: dl.product_code,
            description: dl.description,
            qty: dl.qty,
            price: dl.unit_net_price
          })),
          totalAmount: Number(fin.finalSubtotal.toFixed(2)),
          stripeDirectCharge: paymentDetails,
          createdAt: new Date().toISOString()
        }).catch(() => {});
      }

      sendAutomaticOrderEmail(localRecord, fin, paymentDetails).catch(() => {});

      return savedDoc || localRecord;
    } catch (e) {
      console.warn('[E-COM] Log CRM locale:', e);
      return null;
    }
  }

  async function sendAutomaticOrderEmail(orderRecord, fin, paymentDetails) {
    const trackingUrl = `${window.location.origin}/tracking-ordine.html?num=${encodeURIComponent(orderRecord.doc_number)}`;
    const rowsHtml = fin.lines.map(l => `
      <tr>
        <td style="padding:6px 8px; border-bottom:1px solid #e2e8f0;"><strong>${escapeHtml(l.code)}</strong> — ${escapeHtml(l.title)}</td>
        <td style="padding:6px 8px; border-bottom:1px solid #e2e8f0; text-align:center;">${l.qty}</td>
        <td style="padding:6px 8px; border-bottom:1px solid #e2e8f0; text-align:right;">€ ${euro(l.lineSubtotal)}</td>
      </tr>
    `).join('');

    const emailHtml = `
      <div style="font-family: Arial, sans-serif; max-width: 620px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden;">
        <div style="background: #0f172a; color: #ffffff; padding: 20px; text-align: center;">
          <h2 style="margin: 0; color: #38bdf8;">CLIMAWELL STORE</h2>
          <p style="margin: 5px 0 0 0; font-size: 14px; color: #cbd5e1;">Conferma Ricezione Ordine ${escapeHtml(orderRecord.doc_number)}</p>
        </div>
        <div style="padding: 24px; color: #1e293b; line-height: 1.6;">
          <p>Gentile <strong>${escapeHtml(orderRecord.customer_name)}</strong>,</p>
          <p>Il tuo ordine <strong>${escapeHtml(orderRecord.doc_number)}</strong> è stato registrato e trasmesso al reparto logistica Climawell.</p>
          <table style="width:100%; border-collapse:collapse; font-size:13px; margin:14px 0;">
            <thead>
              <tr style="background:#f1f5f9;">
                <th style="padding:6px 8px; text-align:left;">Articolo</th>
                <th style="padding:6px 8px; text-align:center;">Q.tà</th>
                <th style="padding:6px 8px; text-align:right;">Importo</th>
              </tr>
            </thead>
            <tbody>${rowsHtml}</tbody>
          </table>
          <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px; margin: 16px 0;">
            ${fin.extraDiscountPct > 0 ? `<p style="margin:4px 0; color:#059669;">🎁 <strong>Sconto Extra Pagamento Anticipato (-${fin.extraDiscountPct}%):</strong> - € ${euro(fin.extraDiscountAmount)}</p>` : ''}
            <p style="margin: 4px 0;">💶 <strong>Totale Ordine (IVA incl.):</strong> <span style="color:#059669; font-weight:bold;">€ ${euro(orderRecord.total_gross)}</span></p>
            <p style="margin: 4px 0;">💳 <strong>Condizione Pagamento:</strong> ${escapeHtml(orderRecord.payment_terms || '')}</p>
            <p style="margin: 4px 0;">📍 <strong>Destinazione:</strong> ${escapeHtml(orderRecord.shipping_address)} - ${escapeHtml(orderRecord.shipping_city)}</p>
          </div>
          <div style="text-align: center; margin: 22px 0;">
            <a href="${trackingUrl}" style="background: #0284c7; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; display: inline-block;">
              🚚 Segui lo Stato del tuo Ordine in Tempo Reale
            </a>
          </div>
        </div>
      </div>
    `;

    const payload = {
      action: 'sendOrderConfirmation',
      orderNumber: orderRecord.doc_number,
      customerEmail: orderRecord.email,
      customerName: orderRecord.customer_name,
      agentCode: orderRecord.agent_code,
      subject: `✅ Conferma Ordine Climawell ${orderRecord.doc_number}`,
      htmlContent: emailHtml,
      textContent: `Conferma Ordine Climawell ${orderRecord.doc_number} - Totale IVA incl.: € ${euro(orderRecord.total_gross)} - Tracking: ${trackingUrl}`,
      to: [
        ...(orderRecord.email ? [{ email: orderRecord.email, name: orderRecord.customer_name }] : []),
        { email: 'commerciale@climawell.it', name: 'Ufficio Commerciale Climawell' }
      ]
    };

    try {
      const resp = await fetch('/.netlify/functions/notify-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (resp.ok) return;
    } catch (e) {}
  }

  function printReceiptDocument() {
    const orderNum = document.getElementById('receiptOrderNumber')?.textContent || 'ORD-ECOM';
    const chargeId = document.getElementById('receiptChargeId')?.textContent || '';
    const itemDesc = document.getElementById('receiptProductDesc')?.textContent || '';
    const qty = document.getElementById('receiptQty')?.textContent || '1';
    const total = document.getElementById('receiptTotalAmount')?.textContent || '€ 0,00';
    const customer = document.getElementById('receiptCustomerName')?.textContent || '';
    const shipping = document.getElementById('receiptShippingDest')?.textContent || '';
    const agent = document.getElementById('receiptAgentCode')?.textContent || '1136';

    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>Riepilogo Ordine ${orderNum}</title>
        <style>
          @page { size: A4; margin: 15mm; }
          body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; padding: 20px; color: #1e293b; line-height: 1.5; font-size: 14px; }
          .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #0284c7; padding-bottom: 18px; margin-bottom: 24px; }
          .brand { font-size: 22px; font-weight: 800; color: #0284c7; margin-bottom: 4px; }
          .badge { background: #ecfdf5; color: #059669; border: 1px solid #10b981; padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 12px; display: inline-block; }
          .info-block { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 18px; margin-bottom: 22px; }
          .info-row { display: flex; justify-content: space-between; margin-bottom: 6px; }
          .table { width: 100%; border-collapse: collapse; margin: 24px 0; }
          .table th, .table td { padding: 12px 14px; text-align: left; border-bottom: 1px solid #e2e8f0; }
          .table th { background: #f1f5f9; color: #475569; font-size: 12px; text-transform: uppercase; font-weight: 700; }
          .total-box { background: #f8fafc; border: 2px solid #cbd5e1; border-radius: 8px; padding: 16px 20px; margin: 24px 0; text-align: right; }
          .total-box strong { font-size: 24px; color: #059669; }
          .footer { margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 16px; font-size: 12px; color: #64748b; text-align: center; }
        </style>
      </head>
      <body>
        <div class="header">
          <div>
            <div class="brand">CLIMAWELL STORE — RIEPILOGO ORDINE</div>
            <div style="font-size: 13px; color: #64748b;">Commerciante Venditore: Climawell S.r.l.</div>
          </div>
          <div style="text-align: right;">
            <div class="badge">${escapeHtml(chargeId)}</div>
            <div style="font-size: 15px; font-weight: 800; margin-top: 8px;">${escapeHtml(orderNum)}</div>
            <div style="font-size: 12px; color: #64748b;">Data: ${new Date().toLocaleDateString('it-IT')}</div>
          </div>
        </div>
        <div class="info-block">
          <h3 style="margin: 0 0 10px 0; font-size: 15px; color: #0f172a;">Dati Acquirente & Consegna</h3>
          <div class="info-row"><span style="color:#64748b;">Cliente / Intestatario:</span><strong>${escapeHtml(customer)}</strong></div>
          <div class="info-row"><span style="color:#64748b;">Destinazione Spedizione:</span><strong>${escapeHtml(shipping)}</strong></div>
          <div class="info-row"><span style="color:#64748b;">Modalità Pagamento:</span><code>${escapeHtml(chargeId)}</code></div>
          <div class="info-row"><span style="color:#64748b;">Agente di Riferimento:</span><strong>${escapeHtml(agent)}</strong></div>
        </div>
        <table class="table">
          <thead>
            <tr>
              <th>Articoli Ordinati</th>
              <th style="width: 120px; text-align: center;">Tot. Pezzi</th>
              <th style="width: 140px; text-align: right;">Importo IVA Incl.</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>${escapeHtml(itemDesc)}</strong></td>
              <td style="text-align: center;">${escapeHtml(qty)}</td>
              <td style="text-align: right; font-weight: 700;">${escapeHtml(total)}</td>
            </tr>
          </tbody>
        </table>
        <div class="total-box">
          <div style="color: #64748b; font-size: 13px; margin-bottom: 4px;">Totale Ordine (IVA inclusa):</div>
          <div><strong>${escapeHtml(total)}</strong></div>
        </div>
        <div class="footer">
          Climawell S.r.l. — Gestione Rete Vendite — Tel. 055-4289074 — commerciale@climawell.it
        </div>
      </body>
      </html>
    `;

    let iframe = document.getElementById('receiptPrintIframe');
    if (!iframe) {
      iframe = document.createElement('iframe');
      iframe.id = 'receiptPrintIframe';
      iframe.style.position = 'fixed';
      iframe.style.right = '0';
      iframe.style.bottom = '0';
      iframe.style.width = '0';
      iframe.style.height = '0';
      iframe.style.border = '0';
      document.body.appendChild(iframe);
    }

    try {
      const doc = iframe.contentWindow.document;
      doc.open();
      doc.write(html);
      doc.close();
      setTimeout(() => {
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
      }, 300);
    } catch (err) {
      window.print();
    }
  }

  // 11. Modalità Prezzi B2B (IVA Esclusa) vs Privati B2C (IVA 22% Inclusa)
  function setPriceMode(mode) {
    EcomState.priceMode = mode;
    try { localStorage.setItem('clw_price_mode', mode); } catch (e) {}
    const btnB2B = document.getElementById('btnPriceModeB2B');
    const btnB2C = document.getElementById('btnPriceModeB2C');
    if (btnB2B) btnB2B.classList.toggle('active', mode === 'B2B');
    if (btnB2C) btnB2C.classList.toggle('active', mode === 'B2C');
    renderProductsGrid();
    showToast(`Mostro prezzi per: ${mode === 'B2B' ? '🏢 Aziende & P.IVA (Prezzi Netti + IVA)' : '🏠 Privati (Prezzi IVA 22% Inclusa)'}`);
  }

  // 11-bis. Scheda Tecnica Veloce (Quick View Modal) con Detrazioni & WhatsApp
  function openQuickViewModal(code) {
    const prod = getProductByCode(code);
    if (!prod) return;
    const modal = document.getElementById('quickViewModal');
    if (!modal) return;

    const isB2C = EcomState.priceMode === 'B2C';
    const vatRate = 0.22;
    const dispPrice = isB2C ? prod.price * (1 + vatRate) : prod.price;
    const priceSub = isB2C ? 'Prezzo Finale con IVA 22% Inclusa' : 'Prezzo Netto + IVA (Fattura B2B)';

    const titleEl = document.getElementById('qvTitle');
    const codeEl = document.getElementById('qvCode');
    const brandEl = document.getElementById('qvBrand');
    const priceEl = document.getElementById('qvPrice');
    const priceSubEl = document.getElementById('qvPriceSub');
    const descEl = document.getElementById('qvDesc');
    const imgEl = document.getElementById('qvImg') || document.getElementById('qvImage');
    const highlightsEl = document.getElementById('qvHighlights');
    const stockEl = document.getElementById('qvStock');
    const cardPriceEl = document.getElementById('qvCardPrice');
    const waBtn = document.getElementById('qvBtnWhatsApp') || document.getElementById('btnQuickViewWa');
    const addCartBtn = document.getElementById('qvBtnAddToCart') || document.getElementById('btnQuickViewAddCart');
    const buyNowBtn = document.getElementById('qvBtnBuyNow');

    if (titleEl) titleEl.textContent = prod.seoTitle || prod.description;
    if (codeEl) codeEl.textContent = prod.code;
    if (brandEl) brandEl.textContent = prod.brand;
    if (priceEl) priceEl.textContent = `€ ${euro(dispPrice)}`;
    if (priceSubEl) priceSubEl.textContent = priceSub;
    if (descEl) descEl.textContent = prod.seoDescription || prod.description;

    if (cardPriceEl) {
      const cardDiscount = Number(EcomState.paymentRules.extraDiscountCardPct || 0);
      const cardPriceVal = cardDiscount > 0 ? dispPrice * (1 - cardDiscount / 100) : dispPrice;
      cardPriceEl.textContent = `€ ${euro(cardPriceVal)}`;
    }

    if (imgEl) {
      const imgSrc = prod.imageUrl || getSmartProductVisual(prod);
      imgEl.src = imgSrc;
      imgEl.alt = `${prod.seoTitle || prod.description} - ${prod.code}`;
      imgEl.onerror = () => {
        imgEl.onerror = null;
        imgEl.src = getSmartProductVisual(prod);
      };
    }

    if (stockEl) {
      stockEl.textContent = prod.stock > 0 ? `🟢 Disponibile a magazzino (${prod.stock} pz)` : '🟡 Su ordinazione rapida (3-5 gg)';
    }

    if (highlightsEl) {
      const hList = (prod.highlights && prod.highlights.length > 0) ? prod.highlights : getDefaultHighlights(prod);
      highlightsEl.innerHTML = hList.map(h => `<li>✓ ${escapeHtml(h)}</li>`).join('');
    }

    if (waBtn) {
      const ag = KNOWN_AGENTS[EcomState.context.agentCode] || { waNumber: '393881299371', name: 'Daniele Lupi' };
      const waMsg = `Buongiorno Daniele, vorrei maggiori informazioni su un prodotto Climawell Store: "${prod.code} - ${prod.seoTitle || prod.description}".`;
      waBtn.href = `https://wa.me/${ag.waNumber}?text=${encodeURIComponent(waMsg)}`;
      const waSpan = waBtn.querySelector('span');
      if (waSpan) waSpan.textContent = `Chiedi su WhatsApp a ${ag.name.split(' ')[0]}`;
    }

    if (addCartBtn) {
      addCartBtn.onclick = () => {
        addToCart(prod.code, 1, false);
        closeQuickViewModal();
      };
    }

    if (buyNowBtn) {
      buyNowBtn.onclick = () => {
        closeQuickViewModal();
        const exists = EcomState.cart.find(c => c.code.toUpperCase() === prod.code.toUpperCase());
        if (!exists) {
          addToCart(prod.code, 1, true);
        } else {
          EcomState.selectedProduct = prod;
          openOrderModal();
        }
      };
    }

    modal.classList.add('active');
  }

  function closeQuickViewModal() {
    const modal = document.getElementById('quickViewModal');
    if (modal) modal.classList.remove('active');
  }

  // 12. Event Listeners
  function setupEventListeners() {
    // Switch Modalità Prezzo B2B (IVA Escl.) / B2C (IVA Incl.)
    document.getElementById('btnPriceModeB2B')?.addEventListener('click', () => setPriceMode('B2B'));
    document.getElementById('btnPriceModeB2C')?.addEventListener('click', () => setPriceMode('B2C'));

    // Chiusura Quick View Modal
    document.getElementById('btnCloseQuickView')?.addEventListener('click', closeQuickViewModal);
    document.getElementById('quickViewBackdrop')?.addEventListener('click', closeQuickViewModal);

    // Ricerca live
    const searchInput = document.getElementById('ecomSearchInput');
    const btnClearSearch = document.getElementById('btnClearSearch');

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        EcomState.searchQuery = e.target.value;
        if (btnClearSearch) {
          btnClearSearch.style.display = EcomState.searchQuery ? 'block' : 'none';
        }
        applyFilters();
      });
    }

    if (btnClearSearch) {
      btnClearSearch.addEventListener('click', () => {
        searchInput.value = '';
        EcomState.searchQuery = '';
        btnClearSearch.style.display = 'none';
        applyFilters();
      });
    }

    // Pills Categorie
    const pills = document.querySelectorAll('.cat-pill');
    pills.forEach(btn => {
      btn.addEventListener('click', () => {
        pills.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        EcomState.currentCategory = btn.dataset.cat;
        applyFilters();
      });
    });

    document.getElementById('btnSwitchToAllCatalog')?.addEventListener('click', () => {
      document.querySelectorAll('.cat-pill').forEach(b => {
        b.classList.toggle('active', b.dataset.cat === 'ALL');
      });
      EcomState.currentCategory = 'ALL';
      applyFilters();
    });

    document.getElementById('brandFilterSelect')?.addEventListener('change', (e) => {
      EcomState.brandFilter = e.target.value;
      applyFilters();
    });

    document.getElementById('priceFilterSelect')?.addEventListener('change', (e) => {
      EcomState.priceFilter = e.target.value;
      applyFilters();
    });

    document.getElementById('sortFilterSelect')?.addEventListener('change', (e) => {
      EcomState.sortBy = e.target.value;
      applyFilters();
    });

    // Pulsanti Carrello (Header e Barra Flottante)
    document.getElementById('btnHeaderOpenCart')?.addEventListener('click', () => openOrderModal());
    document.getElementById('btnFloatingOpenCheckout')?.addEventListener('click', () => openOrderModal());
    document.getElementById('btnFloatingClearCart')?.addEventListener('click', () => {
      clearCart();
      showToast('🗑 Carrello svuotato');
    });
    document.getElementById('btnContinueShopping')?.addEventListener('click', closeOrderModal);

    // Selettore Tipo Cliente (Azienda B2B vs Privato B2C)
    document.getElementById('btnBuyerTypeB2B')?.addEventListener('click', () => {
      EcomState.buyerType = 'B2B';
      evaluateBuyerAndPaymentAccess();
      updateOrderSummary();
    });

    document.getElementById('btnBuyerTypeB2C')?.addEventListener('click', () => {
      EcomState.buyerType = 'B2C';
      if (EcomState.activePaymentTab === 'assisted') {
        switchPaymentMethodTab('stripe');
      } else {
        evaluateBuyerAndPaymentAccess();
        updateOrderSummary();
      }
    });

    // Ricalcolo al cambio modalità di consegna (Spedizione vs Ritiro al Banco)
    document.getElementById('orderDeliveryType')?.addEventListener('change', () => {
      updateOrderSummary();
    });

    // Rilevamento automatico mentre il cliente compila Ragione Sociale o P.IVA/C.F.
    document.getElementById('orderCustomerInput')?.addEventListener('input', evaluateBuyerAndPaymentAccess);
    document.getElementById('orderTaxIdInput')?.addEventListener('input', (e) => {
      const val = e.target.value.trim();
      // Se inserisce 16 caratteri alfanumerici tipici del C.F. persona fisica, avvisa
      if (val.length === 16 && /^[A-Za-z]{6}/.test(val) && EcomState.buyerType === 'B2B') {
        // Mantiene flessibilità ma rivaluta accesso B2B
      }
      evaluateBuyerAndPaymentAccess();
    });

    // Apertura/chiusura Pannello Configurazione Pagamenti & Social Studio
    document.getElementById('btnOpenPaymentConfig')?.addEventListener('click', () => openPaymentAndSocialModal('payments'));
    document.getElementById('btnOpenSocialStudioQuick')?.addEventListener('click', () => openPaymentAndSocialModal('social'));
    document.getElementById('btnClosePaymentConfig')?.addEventListener('click', closePaymentAndSocialModal);

    document.getElementById('tabCfgPayments')?.addEventListener('click', () => switchCfgModalTab('payments'));
    document.getElementById('tabCfgSocial')?.addEventListener('click', () => switchCfgModalTab('social'));

    document.getElementById('btnSavePaymentRules')?.addEventListener('click', savePaymentRulesFromModal);
    document.getElementById('btnResetPaymentRules')?.addEventListener('click', () => {
      EcomState.paymentRules = { ...DEFAULT_PAYMENT_RULES };
      savePaymentRulesToStorage();
      openPaymentAndSocialModal('payments');
      applyPaymentRulesToUiBanners();
      updateCartIndicators();
      renderProductsGrid();
      showToast('↺ Ripristinate regole di pagamento predefinite');
    });

    // Eventi Social Studio
    document.getElementById('socialProductSelect')?.addEventListener('change', generateSocialPostAndLink);
    document.getElementById('socialTargetSelect')?.addEventListener('change', generateSocialPostAndLink);

    document.getElementById('btnCopySocialLink')?.addEventListener('click', () => {
      const v = document.getElementById('socialGeneratedLink')?.value || '';
      if (v && navigator.clipboard) {
        navigator.clipboard.writeText(v);
        showToast('🔗 Link Carrello Pre-Caricato copiato negli appunti!');
      }
    });

    document.getElementById('btnCopySocialPost')?.addEventListener('click', () => {
      const v = document.getElementById('socialGeneratedCopy')?.value || '';
      if (v && navigator.clipboard) {
        navigator.clipboard.writeText(v);
        showToast('📋 Testo Post Social copiato! Pronto da incollare su Facebook/Instagram/LinkedIn.');
      }
    });

    document.getElementById('btnShareSocialWhatsApp')?.addEventListener('click', () => {
      const v = document.getElementById('socialGeneratedCopy')?.value || '';
      if (v) {
        window.open(`https://wa.me/?text=${encodeURIComponent(v)}`, '_blank');
      }
    });

    document.getElementById('btnCopyEmbedCode')?.addEventListener('click', () => {
      const v = document.getElementById('websiteEmbedCodeBox')?.value || '';
      if (v && navigator.clipboard) {
        navigator.clipboard.writeText(v);
        showToast('🌐 Codice HTML Sito Web copiato negli appunti!');
      }
    });

    // Apertura/chiusura Pannello Vetrina Top 10 & SEO
    document.getElementById('btnOpenVetrinaManager')?.addEventListener('click', openVetrinaManagerModal);
    document.getElementById('btnOpenSeoInspector')?.addEventListener('click', openVetrinaManagerModal);
    document.getElementById('btnCloseVetrinaManager')?.addEventListener('click', closeVetrinaManagerModal);

    document.getElementById('managerCatalogSearch')?.addEventListener('input', (e) => {
      populateManagerCatalogSelect(e.target.value);
    });

    document.getElementById('btnAddProductToTop10')?.addEventListener('click', () => {
      const sel = document.getElementById('managerCatalogSelect');
      const code = sel?.value;
      if (!code) {
        showToast('⚠️ Seleziona prima un articolo dal menu a tendina del listino');
        return;
      }
      if (EcomState.top10Config.length >= 24) {
        showToast('⚠️ Hai già 20 articoli in vetrina. Rimuovine uno prima di aggiungerne un altro.');
        return;
      }
      const found = getProductByCode(code);
      if (!found) return;
      EcomState.top10Config.push({
        code: found.code,
        seoTitle: found.seoTitle || found.description,
        seoDescription: found.seoDescription || `${found.description} - Disponibile su Climawell Store.`,
        highlights: getDefaultHighlights(found),
        badge: '⭐ Scelta Climawell',
        brand: found.brand,
        family: found.family,
        price: found.price,
        listPrice: found.listPrice,
        stock: found.stock,
        imageUrl: found.imageUrl || ''
      });
      renderVetrinaManagerList();
      populateManagerCatalogSelect(document.getElementById('managerCatalogSearch')?.value || '');
      showToast(`✅ Articolo ${found.code} aggiunto alla Vetrina Top 12!`);
    });

    
    // Nuove Tab Vetrina Manager 2.0
    document.getElementById('tabVetrinaCurrent')?.addEventListener('click', () => switchVetrinaTab('current'));
    document.getElementById('tabVetrinaSearch')?.addEventListener('click', () => switchVetrinaTab('search'));
    document.getElementById('tabVetrinaManual')?.addEventListener('click', () => switchVetrinaTab('manual'));
    
    // Ricerca live nel catalogo
    document.getElementById('managerCatalogLiveSearch')?.addEventListener('input', e => {
      renderCatalogSearchResults(e.target.value);
    });

    // Inserimento manuale articolo
    document.getElementById('btnSubmitManualProduct')?.addEventListener('click', () => {
      const code = (document.getElementById('manualCode')?.value || '').trim().toUpperCase();
      const title = (document.getElementById('manualTitle')?.value || '').trim();
      const price = parseFloat(document.getElementById('manualPrice')?.value || 0);
      const listPrice = parseFloat(document.getElementById('manualListPrice')?.value || price * 1.3);
      const stock = parseInt(document.getElementById('manualStock')?.value || 10, 10);
      const imageUrl = (document.getElementById('manualImageUrl')?.value || '').trim();

      if (!code || !title || isNaN(price) || price <= 0) {
        showToast('⚠️ Inserisci almeno Codice, Titolo e Prezzo valido!');
        return;
      }
      if (EcomState.top10Config.length >= 24) {
        showToast('⚠️ La vetrina contiene già 20 articoli!');
        return;
      }

      EcomState.top10Config.push({
        code,
        seoTitle: title,
        seoDescription: title,
        highlights: ['Garanzia Ufficiale Italia', 'Pronta Consegna magazzino Firenze'],
        badge: '⭐ Speciale Vetrina',
        brand: 'CLIMAWELL',
        family: 'CLIMA',
        price,
        listPrice,
        stock,
        imageUrl
      });

      // Pulisci campi
      document.getElementById('manualCode').value = '';
      document.getElementById('manualTitle').value = '';
      document.getElementById('manualPrice').value = '';
      document.getElementById('manualListPrice').value = '';
      document.getElementById('manualImageUrl').value = '';

      switchVetrinaTab('current');
      showToast(`✅ Articolo "${code}" inserito con successo nei Top in Vetrina!`);
    });

    document.getElementById('btnResetDefaultTop10')?.addEventListener('click', () => {
      EcomState.top10Config = JSON.parse(JSON.stringify(DEFAULT_TOP10_CONFIG));
      saveTop10ConfigToStorage();
      EcomState.products = mergeTop10WithCatalog(EcomState.products.filter(p => !p.isFeaturedTop10));
      renderVetrinaManagerList();
      applyFilters();
      updateSeoStructuredDataAndMeta();
      showToast('↺ Ripristinati i 20 articoli consigliati in vetrina!');
    });

    document.getElementById('btnSaveTop10Config')?.addEventListener('click', () => {
      saveTop10ConfigToStorage();
      EcomState.products = mergeTop10WithCatalog(EcomState.products);
      populateBrandFilter();
      applyFilters();
      updateSeoStructuredDataAndMeta();
      closeVetrinaManagerModal();
      showToast('✅ Vetrina Top 10, Foto e Dati Strutturati SEO aggiornati!');
    });

    document.getElementById('btnCloseOrderModal')?.addEventListener('click', closeOrderModal);
    document.getElementById('btnCloseReceipt')?.addEventListener('click', () => {
      document.getElementById('stripeReceiptModal')?.classList.remove('active');
    });
    document.getElementById('btnPrintReceipt')?.addEventListener('click', printReceiptDocument);

    // Tab Selezione Metodo di Pagamento (3 opzioni: Bonifico Anticipato -4%, Carta Stripe in attivazione, Dilazione B2B Ri.Ba. 60-90gg)
    document.getElementById('tabStripeMethod')?.addEventListener('click', () => switchPaymentMethodTab('stripe'));
    document.getElementById('tabPrepaidBankMethod')?.addEventListener('click', () => switchPaymentMethodTab('prepaid_bank'));
    document.getElementById('tabAssistedMethod')?.addEventListener('click', () => switchPaymentMethodTab('assisted'));

    document.getElementById('btnSwitchToBankTransfer')?.addEventListener('click', () => switchPaymentMethodTab('prepaid_bank'));
    document.getElementById('btnSwitchB2bToCard')?.addEventListener('click', () => switchPaymentMethodTab('prepaid_bank'));

    document.getElementById('b2bDeferredTermSelect')?.addEventListener('change', (e) => {
      const lbl = document.getElementById('btnB2bTermLabel');
      if (lbl) lbl.textContent = e.target.value;
    });

    // Pulsanti di Conferma Ordine per ciascun metodo
    document.getElementById('btnStripeDirectPay')?.addEventListener('click', processStripeDirectCharge);
    document.getElementById('btnConfirmStripePayment')?.addEventListener('click', processStripeDirectCharge);
    document.getElementById('btnConfirmPrepaidBank')?.addEventListener('click', confirmPrepaidBankOrder);
    document.getElementById('btnConfirmBankTransfer')?.addEventListener('click', confirmPrepaidBankOrder);
    document.getElementById('btnConfirmB2bRibaOrder')?.addEventListener('click', confirmB2bDeferredOrder);
    document.getElementById('btnConfirmB2bDeferred')?.addEventListener('click', confirmB2bDeferredOrder);
    document.getElementById('btnConfirmViaWhatsApp')?.addEventListener('click', sendOrderViaWhatsApp);
    document.getElementById('btnConfirmViaEmail')?.addEventListener('click', sendOrderViaEmail);

    document.getElementById('btnSaveToCrm')?.addEventListener('click', async () => {
      const f = collectCustomerFormData();
      if (!validateCustomerForm(f)) return;
      const fin = calculateCartFinancials();
      await logOrderCrm('manual_save', f.customerName, fin, f.agent, { payment_label: f.b2bDeferredTerm }, f);
      clearCart();
      showToast('✅ Ordine multi-articolo registrato in Gestione Ordini & Magazzino!');
      closeOrderModal();
    });
  }

  // 13. Generatore Illustrazioni Tecniche Specifiche per Categoria
  function getSmartProductVisual(product) {
    const code = String(product?.code || 'CLW').toUpperCase().replace(/[<>&"']/g, '');
    const brand = String(product?.brand || 'CLIMAWELL').toUpperCase().replace(/[<>&"']/g, '');
    const text = `${code} ${product?.seoTitle || ''} ${product?.description || ''} ${product?.family || ''}`.toUpperCase();

    if (text.includes('DOCC') || text.includes('BOX') || text.includes('ARREDO') || text.includes('WALK')) {
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="320" height="200" viewBox="0 0 320 200">
        <defs>
          <linearGradient id="bg2b" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#f0f9ff"/><stop offset="100%" stop-color="#e0f2fe"/></linearGradient>
          <linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.85"/><stop offset="100%" stop-color="#bae6fd" stop-opacity="0.45"/></linearGradient>
        </defs>
        <rect width="320" height="200" fill="url(#bg2b)"/>
        <rect x="95" y="22" width="130" height="145" rx="4" fill="url(#glass)" stroke="#0284c7" stroke-width="3"/>
        <line x1="160" y1="22" x2="160" y2="167" stroke="#0369a1" stroke-width="2" stroke-dasharray="4,2"/>
        <rect x="148" y="85" width="6" height="22" rx="2" fill="#0f172a"/>
        <rect x="166" y="85" width="6" height="22" rx="2" fill="#0f172a"/>
        <rect x="90" y="165" width="140" height="10" rx="3" fill="#0f172a"/>
        <text x="160" y="190" font-family="Segoe UI,Arial,sans-serif" font-size="11" font-weight="700" fill="#0369a1" text-anchor="middle">${brand} • COD. ${code}</text>
      </svg>`;
      return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
    }

    if (text.includes('POMP') || text.includes('ALTHERMA') || text.includes('NUOS') || text.includes('SCALDACQUA') || text.includes('MONOBLOCCO')) {
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="320" height="200" viewBox="0 0 320 200">
        <defs>
          <linearGradient id="bghp" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#fff7ed"/><stop offset="100%" stop-color="#ffedd5"/></linearGradient>
        </defs>
        <rect width="320" height="200" fill="url(#bghp)"/>
        <rect x="75" y="34" width="170" height="122" rx="8" fill="#ffffff" stroke="#ea580c" stroke-width="3"/>
        <circle cx="132" cy="95" r="40" fill="#f8fafc" stroke="#0f172a" stroke-width="2.5"/>
        <circle cx="132" cy="95" r="10" fill="#ea580c"/>
        <line x1="132" y1="57" x2="132" y2="133" stroke="#94a3b8" stroke-width="2"/>
        <line x1="94" y1="95" x2="170" y2="95" stroke="#94a3b8" stroke-width="2"/>
        <rect x="190" y="52" width="40" height="24" rx="4" fill="#0f172a"/>
        <text x="210" y="68" font-family="monospace" font-size="10" font-weight="700" fill="#38bdf8" text-anchor="middle">A+++</text>
        <text x="160" y="182" font-family="Segoe UI,Arial,sans-serif" font-size="11" font-weight="700" fill="#9a3412" text-anchor="middle">${brand} R32 • ${code}</text>
      </svg>`;
      return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
    }

    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="320" height="200" viewBox="0 0 320 200">
      <defs>
        <linearGradient id="bgac" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#f8fafc"/><stop offset="100%" stop-color="#e0f2fe"/></linearGradient>
      </defs>
      <rect width="320" height="200" fill="url(#bgac)"/>
      <rect x="42" y="45" width="236" height="68" rx="12" fill="#ffffff" stroke="#0284c7" stroke-width="3"/>
      <line x1="56" y1="96" x2="264" y2="96" stroke="#cbd5e1" stroke-width="2"/>
      <rect x="232" y="62" width="30" height="14" rx="3" fill="#0f172a"/>
      <text x="247" y="72" font-family="monospace" font-size="9" font-weight="700" fill="#34d399" text-anchor="middle">21°C</text>
      <path d="M 85 125 Q 100 142 115 125" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round"/>
      <path d="M 145 125 Q 160 142 175 125" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round"/>
      <path d="M 205 125 Q 220 142 235 125" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round"/>
      <text x="160" y="176" font-family="Segoe UI,Arial,sans-serif" font-size="11" font-weight="700" fill="#0369a1" text-anchor="middle">${brand} INVERTER • ${code}</text>
    </svg>`;
    return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
  }

  function euro(val) {
    return Number(val || 0).toLocaleString('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function escapeHtml(str) {
    return String(str || '').replace(/[&<>"']/g, m => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[m]);
  }

  function showToast(msg) {
    const t = document.getElementById('ecomToast');
    if (!t) return;
    t.textContent = msg;
    t.classList.add('active');
    setTimeout(() => t.classList.remove('active'), 3500);
  }

  window.ClwEcom = {
    openModalByCode(code) {
      addToCart(code, 1, true);
    },
    addToCart,
    openVetrinaManager: openVetrinaManagerModal,
    openPaymentConfig: () => openPaymentAndSocialModal('payments'),
    openSocialStudio: () => openPaymentAndSocialModal('social'),
    getState() {
      return EcomState;
    }
  };

})();

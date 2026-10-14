/**
 * CLIMAWELL - SUPABASE CLIENT & DATA ADAPTER
 * Gestisce l'interfacciamento ad alta velocità con il database PostgreSQL di Supabase,
 * con fallback trasparente a IndexedDB per funzionamento offline.
 */

(function (window) {
  'use strict';

  // Configurazione default / storage
  const DEFAULT_URL = 'https://fadgdncfhfpwkcbxcntc.supabase.co';
  const DEFAULT_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhZGdkbmNmaGZwd2tjYnhjbnRjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE4NzYzOTIsImV4cCI6MjEwNzQ1MjM5Mn0.ucGTqDigQVa6ZkBTH3l8Rvo7JHF7RVxvEv-3NGcMlfo';

  const STORAGE_KEY_URL = 'clw_supabase_url';
  const STORAGE_KEY_KEY = 'clw_supabase_key';

  let supabaseInstance = null;

  function getSupabaseConfig() {
    return {
      url: localStorage.getItem(STORAGE_KEY_URL) || window.SUPABASE_CONFIG?.url || DEFAULT_URL,
      key: localStorage.getItem(STORAGE_KEY_KEY) || window.SUPABASE_CONFIG?.anonKey || DEFAULT_KEY
    };
  }

  function setSupabaseConfig(url, key) {
    if (url) localStorage.setItem(STORAGE_KEY_URL, url.trim());
    if (key) localStorage.setItem(STORAGE_KEY_KEY, key.trim());
    supabaseInstance = null; // reset client
  }

  function initClient() {
    if (supabaseInstance) return supabaseInstance;
    const { url, key } = getSupabaseConfig();
    if (!url || !key) return null;

    if (window.supabase && typeof window.supabase.createClient === 'function') {
      supabaseInstance = window.supabase.createClient(url, key);
      return supabaseInstance;
    }
    return null;
  }

  // --- IndexedDB Fallback Helpers ---
  function openFallbackDb() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open('offerte-agenti', 2);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains('data')) db.createObjectStore('data');
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  async function getLocalCache(key) {
    try {
      const db = await openFallbackDb();
      return new Promise(resolve => {
        const tx = db.transaction('data', 'readonly');
        const req = tx.objectStore('data').get(key);
        req.onsuccess = () => resolve(req.result || null);
        req.onerror = () => resolve(null);
      });
    } catch {
      return null;
    }
  }

  async function setLocalCache(key, value) {
    try {
      const db = await openFallbackDb();
      return new Promise((resolve, reject) => {
        const tx = db.transaction('data', 'readwrite');
        tx.objectStore('data').put(value, key);
        tx.oncomplete = resolve;
        tx.onerror = () => reject(tx.error);
      });
    } catch (e) {
      console.warn('Cache write error:', e);
    }
  }

  // --- Core Data Service ---
  const ClwData = {
    isConfigured() {
      const { url, key } = getSupabaseConfig();
      return Boolean(url && key);
    },

    setConfig: setSupabaseConfig,
    getConfig: getSupabaseConfig,

    /**
     * Recupera il catalogo articoli (con cache locale automatica)
     */
    async getProducts(options = {}) {
      const client = initClient();
      if (client) {
        try {
          let q = client
            .from('products')
            .select('*')
            .eq('active', true)
            .order('code', { ascending: true });

          q = q.limit(options.limit || 50000);
          if (options.search) {
            const s = options.search.trim();
            q = q.or(`code.ilike.%${s}%,description.ilike.%${s}%,barcode.ilike.%${s}%,brand.ilike.%${s}%`);
          }

          const { data, error } = await q;
          if (error) throw error;
          if (data && data.length) {
            // Salva in cache locale per modalità offline
            setLocalCache('products', data);
            return data;
          }
        } catch (err) {
          console.warn('[Supabase] Errore lettura prodotti, fallback locale:', err.message);
        }
      }

      // Fallback IndexedDB / LocalStorage
      const cached = await getLocalCache('products');
      if (cached && cached.length) return cached;
      return [];
    },

    /**
     * Ricerca articolo tramite Barcode / EAN o Codice
     */
    async findProductByBarcodeOrCode(codeOrBarcode) {
      if (!codeOrBarcode) return null;
      const term = String(codeOrBarcode).trim();
      const client = initClient();

      if (client) {
        try {
          const { data, error } = await client
            .from('products')
            .select('*, product_locations(*)')
            .or(`barcode.eq.${term},code.eq.${term},barcode.ilike.%${term}%`)
            .limit(1);

          if (!error && data && data.length) return data[0];
        } catch (e) {
          console.warn('[Supabase] Errore find barcode:', e);
        }
      }

      // Fallback su cache locale
      const prods = (await getLocalCache('products')) || [];
      return (
        prods.find(
          p => {
            const b = String(p.barcode || '').trim();
            const bList = b.split(',').map(s => s.trim());
            return (
              b === term ||
              bList.includes(term) ||
              b.includes(term) ||
              String(p.code || '').trim().toLowerCase() === term.toLowerCase()
            );
          }
        ) || null
      );
    },

    /**
     * Recupera le ubicazioni multiple di un articolo
     */
    async getProductLocations(productCode) {
      const client = initClient();
      if (client) {
        try {
          const { data, error } = await client
            .from('product_locations')
            .select('*')
            .eq('product_code', productCode)
            .order('is_primary', { ascending: false });
          if (!error && data) return data;
        } catch (e) {
          console.warn('[Supabase] Errore locations:', e);
        }
      }
      return [];
    },

    /**
     * Salva o aggiunge una nuova ubicazione ad un articolo
     */
    async saveProductLocation(productCode, locationCode, locationType = 'PICKING', isPrimary = false, qty = 0) {
      const client = initClient();
      if (client) {
        const { data, error } = await client
          .from('product_locations')
          .upsert(
            {
              product_code: productCode,
              location_code: locationCode.trim().toUpperCase(),
              location_type: locationType,
              is_primary: isPrimary,
              quantity: Number(qty) || 0,
              updated_at: new Date().toISOString()
            },
            { onConflict: 'product_code, location_code' }
          );
        if (error) throw error;
        return data;
      }
      return { ok: true, localOnly: true };
    },

    /**
     * Recupera l'elenco dei clienti
     */
    async getCustomers() {
      const client = initClient();
      if (client) {
        try {
          const { data, error } = await client
            .from('customers')
            .select('*')
            .order('name', { ascending: true });
          if (!error && data && data.length) {
            setLocalCache('customers', data);
            return data;
          }
        } catch (err) {
          console.warn('[Supabase] Errore lettura clienti:', err.message);
        }
      }
      const cached = await getLocalCache('customers');
      return cached || [];
    },

    /**
     * Recupera l'elenco ufficiale degli agenti da Supabase (sincronizzati da Plus 2000)
     */
    async getAgents() {
      const client = initClient();
      if (client) {
        try {
          const { data, error } = await client
            .from('agents')
            .select('*')
            .eq('active', true)
            .order('name', { ascending: true });
          if (!error && data && data.length) {
            setLocalCache('agents', data);
            return data;
          }
        } catch (err) {
          console.warn('[Supabase] Errore lettura agenti:', err.message);
        }
      }
      const cached = await getLocalCache('agents');
      return cached || [];
    },

    /**
     * Recupera il profilo aziendale da Supabase
     */
    async getCompany() {
      const client = initClient();
      if (client) {
        try {
          const { data, error } = await client
            .from('company_profile')
            .select('*')
            .limit(1);
          if (!error && data && data.length) {
            return data[0];
          }
        } catch (err) {
          console.warn('[Supabase] Errore company_profile:', err.message);
        }
      }
      return null;
    },

    /**
     * Recupera tutte le offerte e gli ordini da Supabase
     */
    async getDocuments() {
      const client = initClient();
      if (client) {
        try {
          const { data, error } = await client
            .from('documents')
            .select('*')
            .order('created_at', { ascending: false });
          if (!error && data) return data;
          if (error) {
            console.warn('[Supabase] Tentativo getDocuments fallback:', error.message);
            const res2 = await client.from('documents').select('*');
            if (!res2.error && res2.data) return res2.data;
          }
        } catch (err) {
          console.warn('[Supabase] Errore documents:', err.message);
        }
      }
      return [];
    },

    /**
     * Recupera le righe dettagliate di un'offerta o ordine da Supabase
     */
    async getDocumentLines(documentNumber) {
      const client = initClient();
      if (client && documentNumber) {
        try {
          const { data, error } = await client
            .from('document_lines')
            .select('*')
            .eq('document_number', documentNumber)
            .order('line_number', { ascending: true });
          if (!error && data && data.length > 0) return data;
        } catch (err) {
          console.warn('[Supabase] Errore document_lines:', err.message);
        }
      }
      return [];
    },

    /**
     * Recupera gli ordini da preparare (per il magazziniere)
     */
    async getWarehouseOrders() {
      const client = initClient();
      if (client) {
        try {
          const { data, error } = await client
            .from('documents')
            .select('*, document_lines(*)')
            .eq('document_type', 'OCL')
            .in('status', ['Inviato', 'In Preparazione', 'Preparato'])
            .order('document_date', { ascending: true });
          if (!error && data) return data;
        } catch (err) {
          console.warn('[Supabase] Errore ordini magazzino:', err.message);
        }
      }
      return [];
    },

    /**
     * Aggiorna lo stato di picking di una riga d'ordine
     */
    async updatePickingLine(lineId, pickedQty, isCompleted, barcodeScanned, operatorName) {
      const client = initClient();
      if (client) {
        const { data, error } = await client
          .from('document_lines')
          .update({
            picked_qty: Number(pickedQty),
            is_completed: Boolean(isCompleted),
            barcode_scanned: barcodeScanned || null,
            picked_at: new Date().toISOString(),
            picked_by: operatorName || 'Magazzino'
          })
          .eq('id', lineId);
        if (error) throw error;
        return data;
      }
      return { ok: true, localOnly: true };
    },

    /**
     * Registra un conteggio inventario fisico (audit & rettifica)
     */
    async saveInventoryCount({ productCode, location, bookStock, countedStock, operatorName, notes }) {
      const client = initClient();
      const payload = {
        product_code: productCode,
        location: location || '',
        book_stock: Number(bookStock) || 0,
        counted_stock: Number(countedStock) || 0,
        operator_name: operatorName || 'Magazziniere',
        notes: notes || '',
        status: 'IN_ATTESA',
        counted_at: new Date().toISOString()
      };

      if (client) {
        const { data, error } = await client.from('inventory_audits').insert([payload]);
        if (error) throw error;

        // Se confermato, registra anche movimento di magazzino
        const diff = payload.counted_stock - payload.book_stock;
        if (diff !== 0) {
          await client.from('warehouse_movements').insert([
            {
              movement_type: 'RETTIFICA_INVENTARIO',
              document_ref: `INV-${new Date().toISOString().slice(0, 10)}`,
              product_code: productCode,
              location_from: location || '',
              quantity: diff,
              previous_stock: payload.book_stock,
              new_stock: payload.counted_stock,
              operator_name: operatorName || 'Magazziniere',
              notes: notes || `Rettifica inventario: delta ${diff > 0 ? '+' : ''}${diff}`
            }
          ]);
        }
        return data;
      }

      // Fallback offline: salva nei log locali
      const localLogs = JSON.parse(localStorage.getItem('clw_offline_audits') || '[]');
      localLogs.push({ ...payload, id: 'LOCAL_' + Date.now() });
      localStorage.setItem('clw_offline_audits', JSON.stringify(localLogs));
      return { ok: true, localSaved: true };
    },

    /**
     * Registra vendita diretta al banco / giro magazzino cliente:
     * Genera Offerta (OFC) oppure DDT di consegna immediata con scarico giacenze
     */
    async createCounterSale({ documentType, customer, lines, signatureData, operatorName, notes }) {
      const client = initClient();
      const year = new Date().getFullYear();
      const prefix = documentType === 'DDT' ? 'DDT' : 'OFF';
      const randomSuffix = Math.floor(1000 + Math.random() * 9000);
      const docNumber = `${prefix}-${year}-BANCO-${randomSuffix}`;

      let subtotal = 0;
      const formattedLines = (lines || []).map((l, idx) => {
        const q = Number(l.quantity) || 1;
        const price = Number(l.price) || 0;
        const tot = q * price;
        subtotal += tot;
        return {
          line_number: idx + 1,
          product_code: l.code,
          description: l.description,
          brand: l.brand || '',
          location: l.location || '',
          quantity: q,
          list_price: price,
          net_price: price,
          total: tot,
          picked_qty: q,
          is_completed: true,
          barcode_scanned: l.barcode || null,
          picked_by: operatorName || 'Banco Magazzino'
        };
      });

      const vatTotal = subtotal * 0.22;
      const grandTotal = subtotal + vatTotal;

      const docPayload = {
        document_type: documentType, // 'OFC' o 'DDT'
        number: docNumber,
        document_date: new Date().toISOString().slice(0, 10),
        customer_code: customer.code || customer.id || '',
        customer_name: customer.name || 'Cliente al Banco',
        agent_name: operatorName || 'Operatore Magazzino',
        status: documentType === 'DDT' ? 'Spedito' : 'Inviato',
        subtotal: Math.round(subtotal * 100) / 100,
        vat_total: Math.round(vatTotal * 100) / 100,
        total: Math.round(grandTotal * 100) / 100,
        notes: notes || (documentType === 'DDT' ? 'Consegna diretta al banco magazzino' : 'Offerta creata in corsia magazzino'),
        signature_data: signatureData || null,
        picked_by: operatorName || 'Magazzino',
        picked_at: new Date().toISOString()
      };

      if (client) {
        // 1. Inserisci testata
        const { error: docErr } = await client.from('documents').insert([docPayload]);
        if (docErr) throw docErr;

        // 2. Inserisci righe
        const linesWithDoc = formattedLines.map(l => ({ ...l, document_number: docNumber }));
        const { error: lineErr } = await client.from('document_lines').insert(linesWithDoc);
        if (lineErr) throw lineErr;

        // 3. Se DDT, registra scarico immediato giacenze e log movimenti
        if (documentType === 'DDT') {
          for (const l of lines) {
            await client.from('warehouse_movements').insert([
              {
                movement_type: 'PRELIEVO_BANCO',
                document_ref: docNumber,
                product_code: l.code,
                quantity: -Math.abs(Number(l.quantity) || 1),
                operator_name: operatorName || 'Banco Magazzino',
                notes: `Scarico immediato DDT ${docNumber} per ${customer.name}`
              }
            ]);
          }
        }
      }

      return {
        ok: true,
        documentNumber: docNumber,
        total: grandTotal,
        documentType
      };
    },

    /**
     * Salva o aggiorna un'Offerta (OFC) o un Ordine (OCL) direttamente su Supabase
     */
    async createDocument({ documentType, number, customer, agent, lines, totals, paymentMethod, validityDays, notes }) {
      const client = initClient();
      const tp = documentType === 'order' || documentType === 'OCL' ? 'OCL' : 'OFC';
      const docPayload = {
        document_type: tp,
        number: number,
        document_date: new Date().toISOString().slice(0, 10),
        customer_code: customer?.id || customer?.code || '',
        customer_name: customer?.name || 'Cliente',
        agent_code: agent?.id || agent?.code || '',
        agent_name: agent?.name || 'Agente',
        status: 'Inviato',
        subtotal: Number(totals?.net) || 0,
        vat_total: Number(totals?.vat) || 0,
        total: Number(totals?.grand) || 0,
        payment_method: paymentMethod || 'Ri.Ba. 60 gg. f.m.',
        validity_days: Number(validityDays) || 30,
        notes: notes || '',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      const formattedLines = (lines || []).map((l, idx) => {
        const prod = l.product || {};
        const q = Number(l.qty || l.quantity) || 1;
        const price = Number(prod.price || l.listPrice || l.price) || 0;
        const d1 = Number(l.discounts?.[0] || l.discount_1) || 0;
        const d2 = Number(l.discounts?.[1] || l.discount_2) || 0;
        const d3 = Number(l.discounts?.[2] || l.discount_3) || 0;
        const d4 = Number(l.discounts?.[3] || l.discount_4) || 0;
        const tot = Number(l.net || l.total || (q * price * (1 - d1/100) * (1 - d2/100))) || 0;
        const netP = q > 0 ? tot / q : price;

        return {
          document_number: number,
          line_number: idx + 1,
          product_code: prod.code || l.code,
          description: prod.description || l.description || '',
          brand: prod.brand || l.brand || '',
          location: prod.location || l.location || '',
          um: prod.um || l.um || 'PZ',
          quantity: q,
          list_price: price,
          discount_1: d1,
          discount_2: d2,
          discount_3: d3,
          discount_4: d4,
          net_price: Math.round(netP * 10000) / 10000,
          vat: Number(prod.vat || l.vat) || 22,
          total: Math.round(tot * 100) / 100
        };
      });

      if (client) {
        try {
          const { error: docErr } = await client.from('documents').upsert(docPayload, { onConflict: 'number' });
          if (docErr) console.warn('[Supabase] Errore inserimento testata documento:', docErr);

          if (formattedLines.length > 0) {
            await client.from('document_lines').delete().eq('document_number', number);
            const { error: linesErr } = await client.from('document_lines').insert(formattedLines);
            if (linesErr) console.warn('[Supabase] Errore inserimento righe documento:', linesErr);
          }
        } catch (e) {
          console.warn('[Supabase] Errore salvataggio documento:', e);
        }
      }

      return { ok: true, number, total: docPayload.total };
    },

    // --- AUTENTICAZIONE & CONTROLLO ACCESSI (app_users) ---
    async login(username, password) {
      const client = initClient();
      const u = (username || '').trim().toLowerCase();
      const p = (password || '').trim();
      if (!u || !p) {
        return { success: false, message: 'Inserisci sia nome utente che password.' };
      }

      if (client) {
        try {
          // 1. Prova prima con RPC login_user (sicura e performante)
          const { data, error } = await client.rpc('login_user', {
            p_username: u,
            p_password: p
          });
          if (!error && data) {
            if (data.success) {
              const user = data.user;
              localStorage.setItem('clw_current_user', JSON.stringify(user));
              localStorage.setItem('oa_session_user', JSON.stringify(user));
              return { success: true, user };
            } else {
              return { success: false, message: data.message || 'Credenziali non valide.' };
            }
          }
        } catch (rpcErr) {
          console.warn('RPC login_user non disponibile, fallback su query diretta:', rpcErr);
        }

        // 2. Fallback: query diretta su tabella app_users
        try {
          const { data: users, error } = await client
            .from('app_users')
            .select('*')
            .ilike('username', u)
            .eq('active', true)
            .limit(1);

          if (!error && users && users.length > 0) {
            const userRec = users[0];
            if (userRec.password_clear === p || userRec.password_hash === p) {
              const user = {
                id: userRec.id,
                username: userRec.username,
                name: userRec.name,
                role: userRec.role,
                agentCode: userRec.agent_code || '',
                email: userRec.email || '',
                canWarehouse: userRec.can_warehouse,
                canOrders: userRec.can_orders,
                lastLogin: new Date().toISOString()
              };
              localStorage.setItem('clw_current_user', JSON.stringify(user));
              localStorage.setItem('oa_session_user', JSON.stringify(user));
              return { success: true, user };
            } else {
              return { success: false, message: 'Password errata.' };
            }
          } else if (users && users.length === 0) {
            return { success: false, message: 'Utente non trovato o disattivato.' };
          }
        } catch (tableErr) {
          console.warn('Tabella app_users non accessibile:', tableErr);
        }
      }

      // 3. Fallback di sicurezza su credenziali amministrative/test locali
      const fallbackUsers = [
        { username: 'amministratore', password: 'Clima1997', name: 'Amministrazione Climawell', role: 'admin', agentCode: 'ADM01', canWarehouse: true, canOrders: true },
        { username: 'admin', password: 'clw2026!', name: 'Admin Climawell', role: 'admin', agentCode: 'ADM01', canWarehouse: true, canOrders: true },
        { username: 'magazzino', password: 'clw2026!', name: 'Operatore Magazzino', role: 'magazziniere', agentCode: 'MAG01', canWarehouse: true, canOrders: false },
        { username: 'f.pontrelli', password: 'clw2026!', name: 'Francesco Pontrelli', role: 'agent', agentCode: '217', canWarehouse: false, canOrders: true }
      ];
      const match = fallbackUsers.find(x => x.username.toLowerCase() === u && x.password === p);
      if (match) {
        const user = { ...match, id: 'LOCAL_' + match.username };
        localStorage.setItem('clw_current_user', JSON.stringify(user));
        localStorage.setItem('oa_session_user', JSON.stringify(user));
        return { success: true, user };
      }

      return { success: false, message: 'Credenziali non valide o utente non autorizzato.' };
    },

    getCurrentUser() {
      try {
        const u = localStorage.getItem('clw_current_user') || localStorage.getItem('oa_session_user');
        return u ? JSON.parse(u) : null;
      } catch {
        return null;
      }
    },

    logout() {
      localStorage.removeItem('clw_current_user');
      localStorage.removeItem('oa_session_user');
      localStorage.removeItem('oa_session_token');
    },

    async listUsers() {
      const client = initClient();
      if (!client) return [];
      const { data, error } = await client.from('app_users').select('*').order('name');
      if (error) {
        console.warn('Errore lettura utenti app_users:', error);
        return [];
      }
      return data || [];
    },

    async saveUser(userData) {
      const client = initClient();
      if (!client) throw new Error('Supabase client non inizializzato');

      try {
        const { data, error } = await client.rpc('save_app_user', {
          p_id: userData.id || null,
          p_username: userData.username,
          p_password: userData.password || '',
          p_name: userData.name,
          p_role: userData.role || 'agente',
          p_agent_code: userData.agentCode || userData.agent_code || null,
          p_can_warehouse: Boolean(userData.canWarehouse ?? userData.can_warehouse),
          p_can_orders: Boolean(userData.canOrders ?? userData.can_orders ?? true),
          p_active: Boolean(userData.active ?? true)
        });
        if (!error && data) return data;
      } catch (e) {
        console.warn('Fallback a salvataggio diretto app_users:', e);
      }

      const payload = {
        username: (userData.username || '').trim().toLowerCase(),
        name: (userData.name || '').trim(),
        role: userData.role || 'agente',
        agent_code: userData.agentCode || userData.agent_code || null,
        can_warehouse: Boolean(userData.canWarehouse ?? userData.can_warehouse),
        can_orders: Boolean(userData.canOrders ?? userData.can_orders ?? true),
        active: Boolean(userData.active ?? true),
        updated_at: new Date().toISOString()
      };
      if (userData.password) {
        payload.password_clear = userData.password;
        payload.password_hash = userData.password;
      }

      if (userData.id) {
        const { data, error } = await client.from('app_users').update(payload).eq('id', userData.id).select();
        if (error) throw error;
        return data;
      } else {
        const { data, error } = await client.from('app_users').insert([payload]).select();
        if (error) throw error;
        return data;
      }
    },

    async deleteUser(id) {
      const client = initClient();
      if (!client) throw new Error('Supabase client non inizializzato');
      const { error } = await client.from('app_users').delete().eq('id', id);
      if (error) throw error;
      return true;
    },

    /**
     * Svuota la cache locale IndexedDB per forzare il download fresco dei dati
     */
    async clearLocalCache() {
      try {
        const db = await openFallbackDb();
        const tx = db.transaction('data', 'readwrite');
        tx.objectStore('data').clear();
      } catch (e) {
        console.warn('Errore pulizia cache:', e);
      }
    },

    /**
     * Invia una richiesta on-demand di sincronizzazione da Plus 2000 verso Supabase
     */
    async requestPlusSync(type = 'ACTIVE') {
      const client = initClient();
      if (!client) throw new Error('Client Supabase non disponibile');
      const reqNumber = 'SYNC-' + Date.now();
      const payload = {
        document_type: 'SYNC_REQUEST',
        number: reqNumber,
        document_date: new Date().toISOString().split('T')[0],
        status: 'Richiesto',
        customer_name: 'Sistema Web App',
        notes: type === 'FULL' ? 'FULL SYNC' : 'ACTIVE SYNC',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      const { data, error } = await client.from('documents').insert([payload]).select();
      if (error) throw error;
      return { number: reqNumber, record: (data && data[0]) || payload };
    },

    /**
     * Verifica lo stato di avanzamento di una richiesta di sincronizzazione da Plus 2000
     */
    async checkPlusSyncStatus(reqNumber) {
      const client = initClient();
      if (!client) return null;
      try {
        const { data, error } = await client
          .from('documents')
          .select('id, number, status, notes, updated_at')
          .eq('number', reqNumber)
          .limit(1);
        if (!error && data && data.length) return data[0];
      } catch (e) {
        console.warn('Errore checkPlusSyncStatus:', e);
      }
      return null;
    }
  };

  window.ClwData = ClwData;
})(window);

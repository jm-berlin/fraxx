/* Multilingo – lokale Laufzeit für die Web-App.
   Ersetzt die Claude-Umgebung (window.claude) durch:
   • Speicher auf dem Gerät (IndexedDB) in zwei Schichten:
       – Standarddaten + Sprachpakete (werden bei Updates erneuert)
       – „Meine Daten“: alles, was du änderst oder ergänzt (bleibt erhalten)
   • optional Online-Übersetzung mit eigenem Claude-API-Schlüssel */
(() => {
  "use strict";
  const DB_NAME = "multilingo", DB_VER = 1;
  const KEY_LS = "ml-api-key";
  const MODELS = { quick: "claude-haiku-5-5", default: "claude-sonnet-5-5" };

  // ---------- IndexedDB ----------
  let dbp = null;
  function idb() {
    if (dbp) return dbp;
    dbp = new Promise((res, rej) => {
      const r = indexedDB.open(DB_NAME, DB_VER);
      r.onupgradeneeded = () => { const d = r.result; for (const s of ["user", "packs", "meta"]) if (!d.objectStoreNames.contains(s)) d.createObjectStore(s); };
      r.onsuccess = () => res(r.result);
      r.onerror = () => rej(r.error);
    });
    return dbp;
  }
  async function tx(store, mode, fn) {
    const d = await idb();
    return new Promise((res, rej) => {
      const t = d.transaction(store, mode), s = t.objectStore(store);
      let out; const r = fn(s);
      if (r) r.onsuccess = () => { out = r.result; };
      t.oncomplete = () => res(out); t.onerror = () => rej(t.error); t.onabort = () => rej(t.error);
    });
  }
  const iget = (s, k) => tx(s, "readonly", st => st.get(k));
  const iput = (s, k, v) => tx(s, "readwrite", st => st.put(v, k));
  const idel = (s, k) => tx(s, "readwrite", st => st.delete(k));
  async function iall(s) {
    const d = await idb();
    return new Promise((res, rej) => {
      const out = {}; const t = d.transaction(s, "readonly"); const c = t.objectStore(s).openCursor();
      c.onsuccess = () => { const cur = c.result; if (cur) { out[cur.key] = cur.value; cur.continue(); } };
      t.oncomplete = () => res(out); t.onerror = () => rej(t.error);
    });
  }
  async function iclear(s) { return tx(s, "readwrite", st => st.clear()); }

  // ---------- Hilfen ----------
  const clone = o => (o == null ? o : JSON.parse(JSON.stringify(o)));
  function deep(a, b) {
    for (const k in b) {
      const v = b[k];
      if (v && typeof v === "object" && !Array.isArray(v) && a[k] && typeof a[k] === "object" && !Array.isArray(a[k])) deep(a[k], v);
      else a[k] = clone(v);
    }
    return a;
  }
  async function getJSON(url, opts) {
    const r = await fetch(url, opts);
    if (!r.ok) throw new Error(url + ": " + r.status);
    return r.json();
  }

  // ---------- Datenschichten ----------
  const state = {
    index: null,          // data/packs.json
    installed: [],        // installierte Sprachpakete
    base: new Map(),      // Standard + Pakete (zusammengeführt)
    user: {},             // eigene Änderungen: id -> Dokument oder {__deleted:true}
    listeners: new Set(),
    ready: null,
    changeHooks: new Set()
  };

  async function loadIndex() {
    try {
      const idx = await getJSON("data/packs.json", { cache: "no-cache" });
      await iput("meta", "index", idx); return idx;
    } catch (e) {
      const idx = await iget("meta", "index");
      if (idx) return idx;
      throw e;
    }
  }
  async function loadFile(key, file, version) {
    const cached = await iget("packs", key);
    if (cached && (cached.version || 0) >= (version || 0)) return cached;
    try {
      const data = await getJSON("data/" + file, { cache: "no-cache" });
      await iput("packs", key, data); return data;
    } catch (e) { if (cached) return cached; throw e; }
  }

  async function rebuildBase() {
    const idx = state.index;
    const core = await loadFile("core", idx.core.file, idx.version);
    const base = new Map(core.docs.map(d => [d.id, clone(d)]));
    const packs = {};
    for (const l of state.installed) {
      const p = idx.packs.find(x => x.lang === l);
      if (!p) continue;
      try { packs[l] = await loadFile("lang-" + l, p.file, p.version); } catch (e) { console.warn("Paket fehlt", l, e); }
    }
    const have = new Set(Object.keys(packs));
    for (const l of Object.keys(packs)) {
      const p = packs[l];
      for (const id in p.overlay) { const d = base.get(id); if (d) deep(d, p.overlay[id]); }
      for (const d of p.docs) {
        if (d.__req && !d.__req.every(x => have.has(x))) continue;
        const x = clone(d); delete x.__req; base.set(x.id, x);
      }
    }
    state.base = base;
  }

  const packLangs = () => new Set((state.index?.packs || []).map(p => p.lang));
  function merged(id) {
    const u = state.user[id];
    if (u) return u.__deleted ? null : { ...u, id };
    const b = state.base.get(id);
    return b ? b : null;
  }
  function viewDoc(d) {
    if (d.kind === "settings" && Array.isArray(d.langs)) {
      const known = packLangs(), inst = new Set(state.installed);
      const langs = d.langs.filter(l => !known.has(l) || inst.has(l));
      if (langs.length !== d.langs.length) return { ...d, langs };
    }
    return d;
  }
  function allDocs() {
    const out = [];
    const ids = new Set([...state.base.keys(), ...Object.keys(state.user)]);
    for (const id of ids) { const d = merged(id); if (d) out.push(viewDoc(d)); }
    out.sort((a, b) => (Number(b.createdAt) || 0) - (Number(a.createdAt) || 0));
    return out;
  }

  let emitQueued = false;
  function emit() {
    if (emitQueued) return; emitQueued = true;
    queueMicrotask(() => {
      emitQueued = false;
      const docs = allDocs();
      const snap = { docs: docs.map(d => { const { id, ...rest } = d; return { id, data: () => rest }; }), size: docs.length };
      state.listeners.forEach(fn => { try { fn(snap); } catch (e) { console.error(e); } });
    });
  }
  function changed() { emit(); state.changeHooks.forEach(fn => { try { fn(); } catch (e) {} }); }

  async function writeUser(id, doc) {
    if (doc === undefined) { delete state.user[id]; await idel("user", id); }
    else { state.user[id] = doc; await iput("user", id, doc); }
    changed();
  }

  // ---------- Start ----------
  state.ready = (async () => {
    try { if (navigator.storage && navigator.storage.persist) navigator.storage.persist(); } catch (e) {}
    state.index = await loadIndex();
    let inst = await iget("meta", "installed");
    if (!Array.isArray(inst)) { inst = state.index.packs.map(p => p.lang); await iput("meta", "installed", inst); }
    state.installed = inst;
    state.user = await iall("user");
    await rebuildBase();
  })();

  // ---------- Datenbank-Schnittstelle (wie in Claude) ----------
  function docRef(id) {
    return {
      async get() { await state.ready; const d = merged(id); return { exists: !!d, id, data: () => clone(d) }; },
      async set(data) { await state.ready; const d = clone(data); delete d.id; await writeUser(id, d); },
      async update(patch) {
        await state.ready;
        const cur = merged(id); if (!cur) { const e = new Error("not found"); e.code = "not_found"; throw e; }
        const next = { ...clone(cur), ...clone(patch) }; delete next.id;
        await writeUser(id, next);
      },
      async delete() { await state.ready; await writeUser(id, state.base.has(id) ? { __deleted: true } : undefined); }
    };
  }
  const collection = {
    doc: docRef,
    orderBy() { return collection; },
    where() { return collection; },
    onSnapshot(fn, err) {
      state.listeners.add(fn);
      state.ready.then(emit, e => { console.error(e); err && err(e); });
      return () => state.listeners.delete(fn);
    },
    async get() { await state.ready; const docs = allDocs(); return { docs: docs.map(d => { const { id, ...r } = d; return { id, data: () => r }; }) }; }
  };
  const dbApi = { collection: () => collection };

  // ---------- Online-Übersetzung (eigener Claude-API-Schlüssel) ----------
  function parseJSON(t) {
    t = String(t || "").trim().replace(/^```(?:json)?\s*/i, "").replace(/```\s*$/, "");
    try { return JSON.parse(t); } catch (e) {}
    const i = Math.min(...["{", "["].map(c => { const k = t.indexOf(c); return k < 0 ? Infinity : k; }));
    const j = Math.max(t.lastIndexOf("}"), t.lastIndexOf("]"));
    if (i < Infinity && j > i) return JSON.parse(t.slice(i, j + 1));
    throw new Error("Antwort war kein JSON");
  }
  function makeSample(key) {
    return {
      async json(prompt, opts = {}) {
        const model = MODELS[opts.modelTier] || MODELS.default;
        let r;
        try {
          r = await fetch("https://api.anthropic.com/v1/messages", {
            method: "POST",
            headers: { "content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01", "anthropic-dangerous-direct-browser-access": "true" },
            body: JSON.stringify({ model, max_tokens: 16000, system: "Antworte ausschließlich mit gültigem JSON, ohne Erklärungen und ohne Markdown-Codeblock.", messages: [{ role: "user", content: String(prompt) }] })
          });
        } catch (e) { const x = new Error("offline"); x.code = "unavailable"; throw x; }
        if (!r.ok) {
          const x = new Error("API " + r.status);
          x.code = r.status === 429 || r.status === 529 ? "resource_exhausted" : r.status >= 500 ? "unavailable" : r.status === 401 ? "unauthenticated" : "api_error";
          if (r.status === 401) window.dispatchEvent(new CustomEvent("ml-badkey"));
          throw x;
        }
        const j = await r.json();
        return parseJSON((j.content || []).map(c => c.text || "").join(""));
      }
    };
  }

  // ---------- window.claude ----------
  window.claude = {
    async use(name) {
      if (name === "db") { await state.ready; return dbApi; }
      if (name === "user") return { id: async () => "local" };
      if (name === "sample") {
        let key = ""; try { key = localStorage.getItem(KEY_LS) || ""; } catch (e) {}
        return key ? makeSample(key) : null;
      }
      return null;
    }
  };

  // ---------- Verwaltung (für die Einstellungen der App) ----------
  window.Multilingo = {
    ready: () => state.ready,
    index: () => state.index,
    installed: () => state.installed.slice(),
    userCount: () => Object.keys(state.user).length,
    onChange: fn => state.changeHooks.add(fn),
    async installPack(lang) {
      const p = state.index.packs.find(x => x.lang === lang); if (!p) throw new Error("unbekannt");
      await loadFile("lang-" + lang, p.file, p.version);
      if (!state.installed.includes(lang)) state.installed.push(lang);
      await iput("meta", "installed", state.installed);
      await rebuildBase();
      const s = merged("settings");
      if (s && Array.isArray(s.langs) && !s.langs.includes(lang)) { const d = clone(s); delete d.id; d.langs = [...d.langs, lang]; await writeUser("settings", d); }
      else changed();
    },
    async removePack(lang) {
      state.installed = state.installed.filter(l => l !== lang);
      await iput("meta", "installed", state.installed);
      await idel("packs", "lang-" + lang);
      await rebuildBase(); changed();
    },
    async checkUpdates() {
      state.index = await loadIndex(); await rebuildBase(); changed();
    },
    async exportBackup() {
      await state.ready;
      const prefs = {};
      try { for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (/^(rw-|redewendungen)/.test(k)) prefs[k] = localStorage.getItem(k); } } catch (e) {}
      return { app: "multilingo", type: "backup", version: 1, createdAt: new Date().toISOString(), installed: state.installed, user: state.user, prefs };
    },
    async importBackup(b) {
      if (!b || b.app !== "multilingo" || b.type !== "backup" || typeof b.user !== "object") throw new Error("Das ist keine Multilingo-Sicherung.");
      for (const id in b.user) { state.user[id] = b.user[id]; await iput("user", id, b.user[id]); }
      if (b.prefs) try { for (const k in b.prefs) localStorage.setItem(k, b.prefs[k]); } catch (e) {}
      if (Array.isArray(b.installed)) {
        for (const l of b.installed) if (!state.installed.includes(l) && state.index.packs.some(p => p.lang === l)) { try { await loadFile("lang-" + l, state.index.packs.find(p => p.lang === l).file, 0); state.installed.push(l); } catch (e) {} }
        await iput("meta", "installed", state.installed);
      }
      await rebuildBase(); changed();
      return Object.keys(b.user).length;
    },
    async resetUser() { state.user = {}; await iclear("user"); changed(); },
    meta: { get: k => iget("meta", k), set: (k, v) => iput("meta", k, v) },
    apiKey: {
      get() { try { return localStorage.getItem(KEY_LS) || ""; } catch (e) { return ""; } },
      set(k) { try { k ? localStorage.setItem(KEY_LS, k.trim()) : localStorage.removeItem(KEY_LS); } catch (e) {} }
    }
  };
})();

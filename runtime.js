/* Viavox – lokale Laufzeit für die Web-App.
   Ersetzt die Claude-Umgebung (window.claude) durch:
   • Speicher auf dem Gerät (IndexedDB) in zwei Schichten:
       – Standarddaten + Sprachpakete (werden bei Updates erneuert)
       – „Meine Daten“: alles, was du änderst oder ergänzt (bleibt erhalten)
   • optional Online-Übersetzung mit eigenem Claude-API-Schlüssel */
(() => {
  "use strict";
  // Admin-Fassung (…/admin/): eigener Speicher auf dem Gerät, Daten aus dem gemeinsamen Ordner der öffentlichen App
  const ADMIN = window.ML_ADMIN === true;
  const DB_NAME = ADMIN ? "multilingo-admin" : "multilingo", DB_VER = 1;
  const DATA = window.ML_DATA || "data/";
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
    index: null,          // data/packs.json (aktive Fassung)
    pending: null,        // neuere Fassung, die auf Zustimmung wartet
    installed: [],        // installierte Sprachpakete
    base: new Map(),      // Standard + Pakete (zusammengeführt)
    user: {},             // eigene Änderungen: id -> Dokument oder {__deleted:true}
    listeners: new Set(),
    ready: null,
    changeHooks: new Set()
  };

  // Neue Veröffentlichung (anderes „release“) wird nicht sofort übernommen: sie wartet in state.pending,
  // bis der Nutzer im Hinweis „Update verfügbar“ zustimmt. Erster Start und ältere Stände: direkt übernehmen.
  async function loadIndex() {
    const active = await iget("meta", "index");
    try {
      const idx = await getJSON(DATA + "packs.json", { cache: "no-cache" });
      if (active && active.release && idx.release && idx.release !== active.release) { state.pending = idx; return active; }
      state.pending = null;
      await iput("meta", "index", idx); return idx;
    } catch (e) {
      if (active) return active;
      throw e;
    }
  }
  async function loadFile(key, file, version) {
    const cached = await iget("packs", key);
    // Gleiche Version (Fingerabdruck des Inhalts) = schon aktuell; sonst die neue, vollständige Datei laden
    if (cached && version && cached.version === version) return cached;
    if (cached && !version) return cached;
    try {
      const data = await getJSON(DATA + file, { cache: "no-cache" });
      await iput("packs", key, data); return data;
    } catch (e) { if (cached) return cached; throw e; }
  }

  async function rebuildBase() {
    const idx = state.index;
    const core = await loadFile("core", idx.core.file, idx.core.version || idx.version);
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
    state.raw = base; state.installedSet = have;
    state.base = localize(base, curSrc());
  }

  // ---------- Ausgangssprache ----------
  // Die Standarddaten sind auf Deutsch aufgebaut. Für jede weitere Ausgangssprache liegt je Eintrag eine fertige
  // Fassung in nb[Sprache] (aus den Sprachpaketen). Sie wird hier beim Zusammenbauen eingesetzt, ohne dass
  // etwas in „Meine Daten“ geschrieben wird, und ohne dass neu übersetzt werden muss.
  function curSrc() {
    const u = state.user.settings, c = (u && !u.__deleted && u.srcLang) || "";
    if (c) return c;
    try { return localStorage.getItem("rw-src") || "de"; } catch (e) { return "de"; }
  }
  function snap(d) {
    const s = { de: { text: d.de || "", note: d.denote || "" } };
    for (const k in d) if (k.length <= 3 && k !== "de" && k !== "pos" && k !== "lvl" && d[k] && typeof d[k] === "object" && typeof d[k].text === "string" && d[k].text) s[k] = { text: d[k].text, note: d[k].note || "" };
    return s;
  }
  function localize(raw, src) {
    state.src = src;
    if (!src || src === "de") return raw;
    const out = new Map();
    for (const [id, d0] of raw) {
      const old = !d0.kind && d0.nb && d0.nb[src];
      if (!old || (d0.noteLang || "de") === src || !old.de || !old.de.text) { out.set(id, d0); continue; }
      const d = { ...d0 };
      const nb = { ...(d0.nb || {}) }; delete nb[src]; nb[d0.noteLang || "de"] = snap(d0); d.nb = nb;
      for (const c in old) { const v = old[c]; if (!v || !v.text) continue; if (c === "de") { d.de = v.text; d.denote = v.note || ""; } else d[c] = { ...(d0[c] || {}), text: v.text, note: v.note || "" }; }
      d.noteLang = src; d.nbCur = JSON.stringify(snap(d));
      out.set(id, d);
    }
    return out;
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
    if (id === "settings" && state.raw) {
      const nsrc = (doc && !doc.__deleted && doc.srcLang) || "de";
      if (nsrc !== state.src) state.base = localize(state.raw, nsrc);
    }
    if (doc === undefined) { delete state.user[id]; await idel("user", id); }
    else { state.user[id] = doc; await iput("user", id, doc); }
    changed();
  }

  // ---------- Erster Start: Ausgangssprache wählen ----------
  const ENDO = { de: ["Deutsch", "Welche Sprache sprichst du?"], en: ["English", "Which language do you speak?"], fr: ["Français", "Quelle langue parles-tu ?"],
    es: ["Español", "¿Qué idioma hablas?"], it: ["Italiano", "Che lingua parli?"], pt: ["Português", "Que língua falas?"], nl: ["Nederlands", "Welke taal spreek je?"],
    pl: ["Polski", "Jakim językiem mówisz?"], tr: ["Türkçe", "Hangi dili konuşuyorsun?"], el: ["Ελληνικά", "Ποια γλώσσα μιλάς;"], hr: ["Hrvatski", "Koji jezik govoriš?"],
    sv: ["Svenska", "Vilket språk talar du?"], da: ["Dansk", "Hvilket sprog taler du?"], nb: ["Norsk", "Hvilket språk snakker du?"], cs: ["Čeština", "Jakým jazykem mluvíš?"],
    hu: ["Magyar", "Milyen nyelven beszélsz?"], ro: ["Română", "Ce limbă vorbești?"], ca: ["Català", "Quina llengua parles?"], ru: ["Русский", "На каком языке ты говоришь?"],
    ja: ["日本語", "何語を話しますか？"], zh: ["中文", "你说哪种语言？"], ar: ["العربية", "ما اللغة التي تتحدثها؟"] };
  function askSource(idx) {
    const ready = ["de", ...(idx.packs || []).filter(p => p.src).map(p => p.lang)];
    if (ready.length < 2) return Promise.resolve("de");
    return new Promise(res => {
      const show = () => {
        const nav = (navigator.language || "de").slice(0, 2).toLowerCase();
        const ov = document.createElement("div"); ov.id = "mlsrc";
        ov.innerHTML = `<style>#mlsrc{position:fixed;inset:0;z-index:9999;background:#e5e2e0;display:grid;place-items:center;padding:20px;font-family:Urbanist,Inter,system-ui,sans-serif;color:#141212}
#mlsrc .bx{background:#f3f1ef;border-radius:24px;box-shadow:0 8px 32px rgb(40 30 25 / .12);padding:34px 30px 28px;width:min(520px,100%);text-align:center}
#mlsrc h1{font-size:34px;font-weight:800;letter-spacing:-.03em;margin:0 0 6px}
#mlsrc .q{margin:0 0 4px;font-size:19px;font-weight:600;min-height:1.4em}
#mlsrc .s{margin:0 0 22px;color:#6b635d;font-size:14px}
#mlsrc .g{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}
#mlsrc button{font:inherit;font-size:16px;font-weight:600;border:1px solid #d3ccc6;background:#fff;color:#141212;border-radius:14px;padding:13px 10px;cursor:pointer}
#mlsrc button:hover,#mlsrc button:focus-visible{border-color:#141212;outline:none}
#mlsrc button.pre{background:#141212;color:#f3f1ef;border-color:#141212}</style>
<div class="bx" role="dialog" aria-modal="true" aria-labelledby="mlsrcq"><h1><svg viewBox="0 0 512 512" aria-hidden="true" style="width:.9em;height:.9em;vertical-align:-.08em;margin-right:.18em;border-radius:22%"><rect width="512" height="512" rx="114" fill="#161314"/><path d="M150 150 L256 372" stroke="#fff" stroke-width="62" stroke-linecap="round" fill="none"/><path d="M362 150 L256 372" stroke="#a3395f" stroke-width="62" stroke-linecap="round" fill="none"/></svg>Viavox</h1><p class="q" id="mlsrcq"></p><p class="s">Du kannst das später unter ⚙ ändern · You can change this later under ⚙</p><div class="g"></div></div>`;
        const g = ov.querySelector(".g"), q = ov.querySelector(".q");
        const first = ready.includes(nav) ? nav : "de";
        q.textContent = (ENDO[first] || ENDO.de)[1];
        for (const l of [first, ...ready.filter(x => x !== first)]) {
          const b = document.createElement("button"); b.type = "button"; b.textContent = (ENDO[l] || [l])[0]; b.lang = l;
          if (l === first) b.className = "pre";
          b.addEventListener("mouseenter", () => { q.textContent = (ENDO[l] || ENDO.de)[1]; });
          b.addEventListener("focus", () => { q.textContent = (ENDO[l] || ENDO.de)[1]; });
          b.addEventListener("click", () => { ov.remove(); res(l); });
          g.appendChild(b);
        }
        document.body.appendChild(ov);
        setTimeout(() => { const b = g.querySelector("button"); if (b) b.focus(); }, 50);
      };
      if (document.body) show(); else document.addEventListener("DOMContentLoaded", show, { once: true });
    });
  }

  // ---------- Start ----------
  state.ready = (async () => {
    try { if (navigator.storage && navigator.storage.persist) navigator.storage.persist(); } catch (e) {}
    state.index = await loadIndex();
    let inst = await iget("meta", "installed");
    let firstSrc = "";
    if (!Array.isArray(inst)) {
      // Erster Start: Ausgangssprache abfragen, dann nur die Standardpakete laden (Deutsch steckt im Kern)
      // plus das Paket der gewählten Ausgangssprache. Alle anderen lassen sich unter ⚙ nachladen.
      firstSrc = await askSource(state.index);
      state.firstRun = true;
      const def = state.index.packs.filter(p => p.default);
      // Admin: alle verfügbaren Sprachen sofort mitinstallieren
      inst = (ADMIN || !def.length ? state.index.packs : def).map(p => p.lang);
      if (firstSrc !== "de" && !inst.includes(firstSrc)) inst.push(firstSrc);
      await iput("meta", "installed", inst);
    }
    state.installed = inst;
    state.user = await iall("user");
    if (firstSrc) {
      try { localStorage.setItem("rw-src", firstSrc); } catch (e) {}
      if (firstSrc !== "de") {
        const core = await loadFile("core", state.index.core.file, state.index.core.version || state.index.version);
        const s0 = core.docs.find(d => d.kind === "settings") || { kind: "settings", langs: [], createdAt: 0 };
        const st = clone(s0); delete st.id; st.srcLang = firstSrc;
        if (Array.isArray(st.langs) && !st.langs.includes(firstSrc)) st.langs = [...st.langs, firstSrc];
        state.user.settings = st; await iput("user", "settings", st);
      }
    }
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
    // Eigene Daten, die bei einem Verlust wirklich fehlen würden (ohne Einstellungen und Oberflächen-Übersetzungen)
    ownCount: () => Object.entries(state.user).filter(([id, d]) => id !== "settings" && !(d && (d.kind === "ui" || d.kind === "settings"))).length,
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
      return !!state.pending;
    },
    // Update: was wartet, und übernehmen
    pendingUpdate: () => state.pending ? { release: state.pending.release, version: state.pending.appVersion || "", from: (state.index && state.index.release) || "" } : null,
    firstRun: () => !!state.firstRun,
    appVersion: () => (state.index && state.index.appVersion) || "",
    release: () => (state.index && state.index.release) || "",
    async applyUpdate() {
      if (!state.pending) return;
      const idx = state.pending; state.pending = null;
      state.index = idx; await iput("meta", "index", idx);
      await rebuildBase(); changed();
    },
    srcLang: () => curSrc(),
    async exportBackup() {
      await state.ready;
      const prefs = {};
      try { for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (/^(rw-|redewendungen)/.test(k)) prefs[k] = localStorage.getItem(k); } } catch (e) {}
      return { app: "multilingo", type: "backup", version: 1, createdAt: new Date().toISOString(), installed: state.installed, user: state.user, prefs };
    },
    async importBackup(b) {
      if (!b || b.app !== "multilingo" || b.type !== "backup" || typeof b.user !== "object") throw new Error("Das ist keine Viavox-Sicherung.");
      for (const id in b.user) { state.user[id] = b.user[id]; await iput("user", id, b.user[id]); }
      if (b.prefs) try { for (const k in b.prefs) localStorage.setItem(k, b.prefs[k]); } catch (e) {}
      if (Array.isArray(b.installed)) {
        for (const l of b.installed) if (!state.installed.includes(l) && state.index.packs.some(p => p.lang === l)) { try { await loadFile("lang-" + l, state.index.packs.find(p => p.lang === l).file, state.index.packs.find(p => p.lang === l).version); state.installed.push(l); } catch (e) {} }
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

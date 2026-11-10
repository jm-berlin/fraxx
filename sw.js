/* Phraxx – Service Worker: Offline-Betrieb und Updates
   Die App kommt immer aus dem Speicher (schnell und offline). Eine neue Fassung wird im Hintergrund geladen,
   aber erst übernommen, wenn der Nutzer im Hinweis „Update verfügbar“ auf „Jetzt aktualisieren“ tippt. */
const VERSION = "d0c917e51b";
const SHELL = ["./", "index.html", "runtime.js", "ui.js", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png", "icons/favicon-32.png", "icons/phraxx.svg", "img/band.jpg", "data/packs.json"];
const SHELL_CACHE = "ml-shell-" + VERSION, RUNTIME = "ml-runtime";

self.addEventListener("install", e => {
  e.waitUntil(caches.open(SHELL_CACHE).then(c => c.addAll(SHELL.map(u => new Request(u, { cache: "reload" }))))
    // Erste Installation: sofort aktiv. Sonst warten, bis der Nutzer das Update bestätigt.
    .then(() => { if (!self.registration.active) return self.skipWaiting(); }));
});
self.addEventListener("message", e => { if (e.data === "skipWaiting") self.skipWaiting(); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith("ml-shell-") && k !== SHELL_CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request; if (req.method !== "GET") return;
  const url = new URL(req.url);
  // Schriften: einmal laden, dann aus dem Speicher
  if (/fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)) {
    e.respondWith(caches.open(RUNTIME).then(async c => { const hit = await c.match(req); if (hit) return hit; const r = await fetch(req); if (r.ok || r.type === "opaque") c.put(req, r.clone()); return r; }));
    return;
  }
  if (url.origin !== location.origin) return;
  // Anleitung: eigene Seiten, nicht die App. Netz zuerst, offline die zuletzt gesehene Fassung
  // Icons und Manifest: Netz zuerst, damit neue Icons sofort beim Installieren ankommen
  if (url.pathname.includes("/icons/") || url.pathname.endsWith("manifest.webmanifest")) {
    e.respondWith(fetch(req, { cache: "no-cache" }).catch(async () => (await caches.match(req, { ignoreSearch: true })) || Response.error()));
    return;
  }
  if (url.pathname.includes("/anleitung/")) {
    e.respondWith(fetch(req).then(r => { if (r.ok) { const k = r.clone(); caches.open(RUNTIME).then(c => c.put(req, k)); } return r; })
      .catch(async () => (await caches.match(req)) || (await caches.match(req, { ignoreSearch: true })) || Response.error()));
    return;
  }
  // Daten (Pakete) lädt die App selbst und speichert sie; hier nur Netz mit Rückfall auf Cache
  if (url.pathname.includes("/data/")) {
    e.respondWith(fetch(req).then(r => { if (r.ok) caches.open(RUNTIME).then(c => c.put(req, r.clone())); return r; }).catch(() => caches.match(req, { ignoreSearch: true })));
    return;
  }
  // App: aus dem Speicher dieser Fassung; nur was dort fehlt, kommt aus dem Netz
  e.respondWith(caches.open(SHELL_CACHE).then(async c => {
    const hit = await c.match(req, { ignoreSearch: true }) || (req.mode === "navigate" ? await c.match("index.html") || await c.match("./") : null);
    if (hit) return hit;
    try { const r = await fetch(req); if (r.ok) c.put(req, r.clone()); return r; }
    catch (err) { return Response.error(); }
  }));
});

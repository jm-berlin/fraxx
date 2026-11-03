/* Multilingo – Service Worker: Offline-Betrieb und Updates */
const VERSION = "d2a3a2d95e";
const SHELL = ["./", "index.html", "runtime.js", "ui.js", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png", "icons/favicon-32.png", "img/paris.jpg", "img/andalucia.jpg", "img/toscana.jpg", "img/band.jpg", "data/packs.json"];
const SHELL_CACHE = "ml-shell-" + VERSION, RUNTIME = "ml-runtime";

self.addEventListener("install", e => {
  e.waitUntil(caches.open(SHELL_CACHE).then(c => c.addAll(SHELL.map(u => new Request(u, { cache: "reload" })))).then(() => self.skipWaiting()));
});
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
  // Daten (Pakete) lädt die App selbst und speichert sie; hier nur Netz mit Rückfall auf Cache
  if (url.pathname.includes("/data/")) {
    e.respondWith(fetch(req).then(r => { if (r.ok) caches.open(RUNTIME).then(c => c.put(req, r.clone())); return r; }).catch(() => caches.match(req, { ignoreSearch: true })));
    return;
  }
  // App: zuerst Netz (frische Version), offline aus dem Speicher
  e.respondWith(fetch(req).then(r => { if (r.ok) { const cp = r.clone(); caches.open(SHELL_CACHE).then(c => c.put(req, cp)); } return r; })
    .catch(async () => (await caches.match(req, { ignoreSearch: true })) || (req.mode === "navigate" ? caches.match("index.html") : Response.error())));
});

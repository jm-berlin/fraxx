/* Phraxx → Fraxx: alter Service Worker räumt auf und schickt offene Fenster zur neuen Adresse */
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil((async () => {
  for (const k of await caches.keys()) await caches.delete(k);
  await self.clients.claim();
  for (const c of await self.clients.matchAll({ type: "window" })) { try { c.navigate(c.url); } catch (_) {} }
  await self.registration.unregister();
})()));

/* Multilingo – App-Einstellungen: Sprachpakete, Sicherung, Online-Übersetzung (nur Admin), Installation */
// Eigene Übersetzung mit API-Schlüssel ist in der öffentlichen Testversion noch nicht freigeschaltet
const KEYUI = window.ML_ADMIN === true;
(() => {
  "use strict";
  const ML = window.Multilingo;
  if (!ML) return;

  // ---------- Service Worker (offline + Updates) ----------
  if ("serviceWorker" in navigator && location.protocol !== "file:") {
    window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
  }
  let installEvt = null;
  window.addEventListener("beforeinstallprompt", e => { e.preventDefault(); installEvt = e; refresh(); });
  const standalone = () => matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
  const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);

  // ---------- Stil ----------
  const css = document.createElement("style");
  css.textContent = `
  .mlbtn{border:0;background:var(--surface-2);color:var(--ink);border-radius:999px;padding:6px 14px;font:inherit;font-size:13.5px;font-weight:600;cursor:pointer;display:inline-flex;gap:7px;align-items:center}
  .mlbtn:hover{filter:brightness(.96)}
  .mlbtn.pri{background:var(--blue);color:var(--blue-ink)}
  .mlbtn.warn{background:transparent;color:var(--danger);box-shadow:inset 0 0 0 1px currentColor}
  .mlbtn:disabled{opacity:.55;cursor:default}
  #mlapp{position:fixed;inset:0;z-index:60;background:rgb(10 14 20 / .45);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);display:flex;justify-content:center;align-items:flex-start;padding:max(16px,env(safe-area-inset-top)) 16px 16px;overflow:auto}
  #mlapp[hidden]{display:none}
  .mlpanel{width:min(760px,100%);background:var(--surface);color:var(--ink);border-radius:calc(var(--radius) + 4px);box-shadow:0 24px 60px rgb(10 14 20 / .3);overflow:hidden;margin:auto 0}
  .mlhead{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:18px 22px;background:var(--blue);color:var(--blue-ink)}
  .mlhead h2{margin:0;font-size:1.3rem}
  .mlhead button{border:0;background:transparent;color:inherit;font-size:20px;cursor:pointer;width:36px;height:36px;border-radius:50%}
  .mlbody{padding:8px 22px 22px;display:flex;flex-direction:column}
  .mlsec{padding:16px 0;border-bottom:1px solid var(--line)}
  .mlsec:last-child{border-bottom:0}
  .mlsec h3{margin:0 0 4px;font-size:1.02rem}
  .mlsec p{margin:0 0 10px;color:var(--muted);font-size:14px;line-height:1.5}
  .mlrow{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
  .mlpacks{display:grid;gap:6px;margin-top:4px}
  .mlpack{display:flex;align-items:center;gap:10px;padding:8px 12px;background:var(--surface-2);border-radius:12px}
  .mlpack b{flex:1 1 auto;font-weight:600}
  .mlpack small{color:var(--muted);font-size:12.5px;white-space:nowrap}
  .mlpack .mlok{white-space:nowrap}
  @media (max-width:520px){ .mlpack small{display:none} .mlpack{padding:8px 10px} }
  .mlok{color:var(--ok);font-weight:600;font-size:13px}
  .mlkey{flex:1 1 260px;min-width:0;border:1px solid var(--line);background:var(--surface-2);border-radius:10px;padding:9px 12px;font:inherit;font-size:14px;color:var(--ink)}
  .mlmsg{font-size:13.5px;color:var(--muted);margin-top:8px}
  .mlmsg.err{color:var(--danger)}
  .mlsetbtn{flex:1 1 100%;justify-content:center}
  `;
  document.head.appendChild(css);

  // ---------- Fenster ----------
  const wrap = document.createElement("div");
  wrap.id = "mlapp"; wrap.hidden = true; wrap.setAttribute("role", "dialog"); wrap.setAttribute("aria-modal", "true"); wrap.setAttribute("aria-labelledby", "mltitle");
  wrap.innerHTML = `<div class="mlpanel">
    <div class="mlhead"><h2 id="mltitle">App &amp; Daten</h2><button type="button" id="mlclose" aria-label="Schließen">✕</button></div>
    <div class="mlbody">
      <section class="mlsec" id="mlinstall"><h3>Als App installieren</h3><p id="mlinstalltx"></p><div class="mlrow"><button type="button" class="mlbtn pri" id="mlinstallbtn" hidden>Jetzt installieren</button></div></section>
      <section class="mlsec"><h3>Sprachpakete</h3><p>Jede Sprache enthält die Übersetzungen aller Standardeinträge, Konjugationen, Grammatik und Speisekarten. Entfernte Pakete kannst du jederzeit wieder laden.</p><div class="mlpacks" id="mlpacks"></div><div class="mlmsg" id="mlpackmsg"></div></section>
      <section class="mlsec"><h3>Meine Daten sichern</h3><p id="mlbacktx"></p>
        <div class="mlrow"><button type="button" class="mlbtn pri" id="mlexport">Sicherung herunterladen</button><button type="button" class="mlbtn" id="mlimport">Sicherung einlesen</button><input type="file" id="mlfile" accept=".json,application/json" hidden></div>
        <div class="mlrow" id="mlautorow" style="margin-top:8px" hidden><button type="button" class="mlbtn" id="mlauto">Automatisch in eine Datei sichern …</button><button type="button" class="mlbtn" id="mlautoperm" hidden>Automatische Sicherung fortsetzen</button></div>
        <div class="mlmsg" id="mlbackmsg"></div></section>
${KEYUI ? `<section class="mlsec"><h3>Online-Übersetzung</h3><p>Ohne Schlüssel arbeitet Multilingo komplett offline mit allem, was in den Sprachpaketen steckt. Mit einem eigenen <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noopener">Claude-API-Schlüssel</a> übersetzt es neue Wörter, Konjugationen und Speisekarten wie bisher. Die Kosten liegen bei Bruchteilen eines Cents pro Eintrag. Der Schlüssel bleibt nur auf diesem Gerät.</p>
        <div class="mlrow"><input class="mlkey" id="mlkey" type="password" autocomplete="off" spellcheck="false" placeholder="sk-ant-…"><button type="button" class="mlbtn pri" id="mlkeysave">Speichern</button><button type="button" class="mlbtn warn" id="mlkeydel" hidden>Entfernen</button></div>
        <div class="mlmsg" id="mlkeymsg"></div></section>` : ""}
      <section class="mlsec"><h3>Zurücksetzen</h3><p>Löscht alle eigenen Änderungen auf diesem Gerät. Die Standarddaten bleiben. Lade vorher eine Sicherung herunter.</p><div class="mlrow"><button type="button" class="mlbtn warn" id="mlreset">Eigene Änderungen löschen</button><button type="button" class="mlbtn" id="mlupdate">Nach Updates suchen</button></div><div class="mlmsg" id="mlresetmsg"></div></section>
    </div></div>`;
  document.body.appendChild(wrap);
  const $ = id => document.getElementById(id);
  const fmtMB = b => (b / 1e6).toLocaleString("de-DE", { maximumFractionDigits: 1 }) + " MB";

  function open() { wrap.hidden = false; refresh(); $("mlclose").focus(); }
  function close() { wrap.hidden = true; }
  $("mlclose").addEventListener("click", close);
  wrap.addEventListener("click", e => { if (e.target === wrap) close(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !wrap.hidden) close(); });

  // Knopf in den Einstellungen (⚙)
  function addSetButton() {
    const pop = document.getElementById("setpop");
    if (!pop || pop.querySelector(".mlsetbtn")) return;
    const b = document.createElement("button");
    b.type = "button"; b.className = "mlbtn pri mlsetbtn"; b.innerHTML = "<span aria-hidden=\"true\">⤓</span>App, Sprachpakete &amp; Sicherung";
    b.addEventListener("click", () => { document.getElementById("setbtn")?.click(); open(); });
    pop.appendChild(b);
  }
  addSetButton();

  // ---------- Inhalte ----------
  async function refresh() {
    await ML.ready();
    // Installation
    const it = $("mlinstalltx"), ib = $("mlinstallbtn");
    if (standalone()) { $("mlinstall").hidden = true; }
    else {
      $("mlinstall").hidden = false;
      ib.hidden = !installEvt;
      it.textContent = installEvt ? "Multilingo bekommt ein eigenes Fenster und ein Symbol auf dem Startbildschirm bzw. im Startmenü und funktioniert auch offline."
        : isIOS ? "In Safari unten auf das Teilen-Symbol tippen und „Zum Home-Bildschirm“ wählen."
        : "Im Browsermenü (⋮) „App installieren“ oder „Zum Startbildschirm hinzufügen“ wählen.";
    }
    // Pakete
    const idx = ML.index(), inst = new Set(ML.installed()), box = $("mlpacks");
    box.innerHTML = "";
    for (const p of idx.packs) {
      const row = document.createElement("div"); row.className = "mlpack";
      row.innerHTML = `<b></b><small></small>`;
      row.querySelector("b").textContent = p.name;
      row.querySelector("small").textContent = fmtMB(p.bytes) + (p.default ? " · Standard" : " · optional");
      const btn = document.createElement("button"); btn.type = "button";
      if (inst.has(p.lang)) { btn.className = "mlbtn"; btn.textContent = "Entfernen"; const ok = document.createElement("span"); ok.className = "mlok"; ok.textContent = "✓ installiert"; row.appendChild(ok); }
      else { btn.className = "mlbtn pri"; btn.textContent = "Laden"; }
      btn.addEventListener("click", async () => {
        btn.disabled = true; $("mlpackmsg").className = "mlmsg"; $("mlpackmsg").textContent = inst.has(p.lang) ? "Wird entfernt …" : "Wird geladen …";
        try { inst.has(p.lang) ? await ML.removePack(p.lang) : await ML.installPack(p.lang); $("mlpackmsg").textContent = "Fertig."; }
        catch (e) { $("mlpackmsg").className = "mlmsg err"; $("mlpackmsg").textContent = "Das hat nicht geklappt. Bist du online?"; }
        refresh();
      });
      row.appendChild(btn); box.appendChild(row);
    }
    // Sicherung
    const n = ML.userCount(), last = await ML.meta.get("lastBackup");
    $("mlbacktx").textContent = `Deine eigenen Einträge und Änderungen (${n.toLocaleString("de-DE")}) liegen getrennt von den Standarddaten und bleiben bei Updates erhalten. Für einen neuen PC, ein neues Handy oder nach dem Löschen der App: Sicherung herunterladen, z. B. in OneDrive, Google Drive oder iCloud ablegen, und auf dem anderen Gerät einlesen.` + (last ? ` Letzte Sicherung: ${new Date(last).toLocaleString("de-DE", { dateStyle: "medium", timeStyle: "short" })}.` : "");
    if ("showSaveFilePicker" in window) {
      $("mlautorow").hidden = false;
      const h = await ML.meta.get("backupHandle");
      $("mlauto").textContent = h ? "Andere Sicherungsdatei wählen …" : "Automatisch in eine Datei sichern …";
      let perm = "denied"; try { perm = h ? await h.queryPermission({ mode: "readwrite" }) : "denied"; } catch (e) {}
      $("mlautoperm").hidden = !(h && perm !== "granted");
      if (h && perm === "granted") $("mlbackmsg").textContent = `Automatische Sicherung aktiv: ${h.name}`;
    }
    // Schlüssel
    const k = ML.apiKey.get();
    if (KEYUI) {
    $("mlkey").value = k ? "••••••••••••" + k.slice(-4) : ""; $("mlkey").dataset.masked = k ? "1" : "";
    $("mlkeydel").hidden = !k;
    }
  }

  $("mlinstallbtn").addEventListener("click", async () => { if (!installEvt) return; installEvt.prompt(); try { await installEvt.userChoice; } catch (e) {} installEvt = null; refresh(); });

  // Sicherung herunterladen / einlesen
  async function download() {
    const data = await ML.exportBackup();
    const blob = new Blob([JSON.stringify(data)], { type: "application/json" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
    a.download = `multilingo-sicherung-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    await ML.meta.set("lastBackup", Date.now());
  }
  $("mlexport").addEventListener("click", async () => { await download(); $("mlbackmsg").className = "mlmsg"; $("mlbackmsg").textContent = "Sicherung gespeichert (Ordner „Downloads“)."; refresh(); });
  $("mlimport").addEventListener("click", () => $("mlfile").click());
  $("mlfile").addEventListener("change", async e => {
    const f = e.target.files[0]; e.target.value = ""; if (!f) return;
    const m = $("mlbackmsg");
    try { const n = await ML.importBackup(JSON.parse(await f.text())); m.className = "mlmsg"; m.textContent = `${n.toLocaleString("de-DE")} eigene Einträge eingelesen. Multilingo lädt neu …`; setTimeout(() => location.reload(), 1200); }
    catch (err) { m.className = "mlmsg err"; m.textContent = err.message || "Die Datei konnte nicht gelesen werden."; }
  });

  // Erinnerung an die Sicherung: eigene Einträge liegen nur auf diesem Gerät
  const DAY = 864e5;
  async function backupReminder() {
    try {
      await ML.ready();
      const n = ML.ownCount();
      if (!n) return;
      let since = await ML.meta.get("ownSince"); if (!since) { since = Date.now(); await ML.meta.set("ownSince", since); }
      const last = await ML.meta.get("lastBackup"), snooze = await ML.meta.get("backupSnooze"), handle = await ML.meta.get("backupHandle");
      const now = Date.now();
      if (snooze && snooze > now) return;
      if (handle && last && now - last < 30 * DAY) return;
      const due = last ? now - last >= 30 * DAY : now - since >= 14 * DAY;
      if (!due) return;
      const days = last ? Math.floor((now - last) / DAY) : 0;
      const box = document.createElement("div"); box.id = "mlbackupremind";
      box.setAttribute("role", "status");
      box.innerHTML = `<style>#mlbackupremind{position:fixed;left:50%;bottom:calc(18px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);z-index:250;width:min(560px,calc(100% - 32px));background:var(--ink,#141212);color:var(--surface,#f3f1ef);border-radius:16px;box-shadow:0 12px 32px rgb(0 0 0 / .3);padding:14px 16px;display:flex;flex-wrap:wrap;gap:10px 14px;align-items:center;font-size:14.5px;line-height:1.45}
#mlbackupremind p{margin:0;flex:1 1 260px}#mlbackupremind b{font-weight:700}
#mlbackupremind .r{display:flex;gap:8px;margin-left:auto}#mlbackupremind button{font:inherit;font-weight:700;border:0;border-radius:999px;padding:8px 14px;cursor:pointer}
#mlbackupremind .y{background:var(--hl,#cc5530);color:var(--hl-ink,#fff)}#mlbackupremind .n{background:transparent;color:inherit;opacity:.8}</style>
<p></p><div class="r"><button type="button" class="n">Später</button><button type="button" class="y">Jetzt sichern</button></div>`;
      const what = n === 1 ? "Deine eigene Änderung liegt" : `Deine ${n.toLocaleString("de-DE")} eigenen Einträge und Änderungen liegen`;
      box.querySelector("p").innerHTML = (last ? `<b>Letzte Sicherung vor ${days} Tagen.</b> ` : `<b>Noch keine Sicherung.</b> `) + what + " nur auf diesem Gerät.";
      box.querySelector(".n").addEventListener("click", async () => { await ML.meta.set("backupSnooze", Date.now() + 7 * DAY); box.remove(); });
      box.querySelector(".y").addEventListener("click", async () => {
        try { if (await ML.meta.get("backupHandle")) await autoSave(true); else await download(); } catch (e) {}
        box.remove();
      });
      document.body.appendChild(box);
    } catch (e) { console.warn("Erinnerung", e); }
  }
  setTimeout(backupReminder, 6000);

  // Automatische Sicherung in eine Datei (Chrome/Edge am PC)
  let autoTimer = null;
  async function autoSave(interactive) {
    const h = await ML.meta.get("backupHandle"); if (!h) return;
    try {
      let perm = await h.queryPermission({ mode: "readwrite" });
      if (perm !== "granted" && interactive) perm = await h.requestPermission({ mode: "readwrite" });
      if (perm !== "granted") return;
      const w = await h.createWritable(); await w.write(JSON.stringify(await ML.exportBackup())); await w.close();
      await ML.meta.set("lastBackup", Date.now());
    } catch (e) { console.warn("Sicherung", e); }
  }
  $("mlauto").addEventListener("click", async () => {
    try {
      const h = await window.showSaveFilePicker({ suggestedName: "multilingo-sicherung.json", types: [{ description: "Multilingo-Sicherung", accept: { "application/json": [".json"] } }] });
      await ML.meta.set("backupHandle", h); await autoSave(true);
      $("mlbackmsg").className = "mlmsg"; $("mlbackmsg").textContent = `Automatische Sicherung aktiv: ${h.name}. Jede Änderung wird dort gespeichert.`;
    } catch (e) { if (e.name !== "AbortError") { $("mlbackmsg").className = "mlmsg err"; $("mlbackmsg").textContent = "Die Datei konnte nicht angelegt werden."; } }
    refresh();
  });
  $("mlautoperm").addEventListener("click", async () => { await autoSave(true); refresh(); });
  ML.onChange(() => { clearTimeout(autoTimer); autoTimer = setTimeout(() => autoSave(false), 4000); });

  // Schlüssel
  if (KEYUI) {
  $("mlkey").addEventListener("focus", e => { if (e.target.dataset.masked) { e.target.value = ""; e.target.dataset.masked = ""; } });
  $("mlkeysave").addEventListener("click", async () => {
    const v = $("mlkey").value.trim(), m = $("mlkeymsg");
    if (!v || $("mlkey").dataset.masked) { m.className = "mlmsg err"; m.textContent = "Bitte den Schlüssel einfügen."; return; }
    m.className = "mlmsg"; m.textContent = "Schlüssel wird geprüft …";
    try {
      const r = await fetch("https://api.anthropic.com/v1/messages", { method: "POST", headers: { "content-type": "application/json", "x-api-key": v, "anthropic-version": "2023-06-01", "anthropic-dangerous-direct-browser-access": "true" }, body: JSON.stringify({ model: "claude-haiku-5-5", max_tokens: 5, messages: [{ role: "user", content: "Hi" }] }) });
      if (r.status === 401 || r.status === 403) { m.className = "mlmsg err"; m.textContent = "Der Schlüssel wurde abgelehnt. Bitte prüfen."; return; }
    } catch (e) { m.textContent = "Konnte den Schlüssel gerade nicht prüfen (offline?). Er wird trotzdem gespeichert."; }
    ML.apiKey.set(v); m.className = "mlmsg"; m.textContent = "Gespeichert. Multilingo lädt neu …"; setTimeout(() => location.reload(), 900);
  });
  $("mlkeydel").addEventListener("click", () => { ML.apiKey.set(""); $("mlkeymsg").textContent = "Schlüssel entfernt. Multilingo lädt neu …"; setTimeout(() => location.reload(), 900); });
  }
  window.addEventListener("ml-badkey", () => { const n = document.getElementById("notice"); if (n) { n.hidden = false; n.textContent = "Der Claude-API-Schlüssel wurde abgelehnt. Unter ⚙ → App, Sprachpakete & Sicherung kannst du ihn ändern."; } });

  // Zurücksetzen / Updates
  $("mlreset").addEventListener("click", async () => {
    if (!confirm("Wirklich alle eigenen Änderungen auf diesem Gerät löschen?")) return;
    await ML.resetUser(); $("mlresetmsg").textContent = "Gelöscht. Multilingo lädt neu …"; setTimeout(() => location.reload(), 900);
  });
  $("mlupdate").addEventListener("click", async () => {
    const m = $("mlresetmsg"); m.className = "mlmsg"; m.textContent = "Suche …";
    try { const reg = await navigator.serviceWorker?.getRegistration(); await reg?.update(); await ML.checkUpdates(); m.textContent = "Alles aktuell."; }
    catch (e) { m.className = "mlmsg err"; m.textContent = "Keine Verbindung."; }
  });
})();

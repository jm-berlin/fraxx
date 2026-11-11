/* Fraxx – App-Einstellungen: Sprachpakete, Sicherung, Online-Übersetzung (nur Admin), Installation */
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
${KEYUI ? `<section class="mlsec"><h3>Online-Übersetzung</h3><p>Ohne Schlüssel arbeitet Fraxx komplett offline mit allem, was in den Sprachpaketen steckt. Mit einem eigenen <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noopener">Claude-API-Schlüssel</a> übersetzt es neue Wörter, Konjugationen und Speisekarten wie bisher. Die Kosten liegen bei Bruchteilen eines Cents pro Eintrag. Der Schlüssel bleibt nur auf diesem Gerät.</p>
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
      it.textContent = installEvt ? "Fraxx bekommt ein eigenes Fenster und ein Symbol auf dem Startbildschirm bzw. im Startmenü und funktioniert auch offline."
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
    try { const n = await ML.importBackup(JSON.parse(await f.text())); m.className = "mlmsg"; m.textContent = `${n.toLocaleString("de-DE")} eigene Einträge eingelesen. Fraxx lädt neu …`; setTimeout(() => location.reload(), 1200); }
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

  // ---------- Update verfügbar: erst zeigen, was neu ist, dann auf Wunsch übernehmen ----------
  const UPD_T = {
    de: { v: "Version", ok: "Aktuell", since: "Neu seit deiner Version", t: "Update verfügbar", l: "Eine neue Version von Fraxx ist da.", w: "Was ist neu", now: "Jetzt aktualisieren", later: "Später", h: "Bis dahin funktioniert alles wie gewohnt, auch offline. Deine eigenen Einträge bleiben erhalten.", busy: "Wird aktualisiert …", gen: "Verbesserungen und Korrekturen." },
    en: { v: "Version", ok: "Up to date", since: "New since your version", t: "Update available", l: "A new version of Fraxx is ready.", w: "What’s new", now: "Update now", later: "Later", h: "Until then everything works as usual, offline too. Your own entries are kept.", busy: "Updating …", gen: "Improvements and fixes." },
    fr: { v: "Version", ok: "À jour", since: "Nouveau depuis ta version", t: "Mise à jour disponible", l: "Une nouvelle version de Fraxx est prête.", w: "Nouveautés", now: "Mettre à jour", later: "Plus tard", h: "D’ici là, tout fonctionne comme d’habitude, même hors ligne. Tes propres entrées sont conservées.", busy: "Mise à jour …", gen: "Améliorations et corrections." },
    it: { v: "Versione", ok: "Aggiornata", since: "Novità dalla tua versione", t: "Aggiornamento disponibile", l: "È pronta una nuova versione di Fraxx.", w: "Novità", now: "Aggiorna ora", later: "Più tardi", h: "Fino ad allora tutto funziona come sempre, anche offline. Le tue voci restano salvate.", busy: "Aggiornamento …", gen: "Miglioramenti e correzioni." },
    es: { v: "Versión", ok: "Actualizada", since: "Novedades desde tu versión", t: "Actualización disponible", l: "Hay una nueva versión de Fraxx.", w: "Novedades", now: "Actualizar ahora", later: "Más tarde", h: "Hasta entonces todo funciona como siempre, también sin conexión. Tus propias entradas se conservan.", busy: "Actualizando …", gen: "Mejoras y correcciones." },
    pt: { v: "Versão", ok: "Atualizada", since: "Novidades desde a tua versão", t: "Atualização disponível", l: "Há uma nova versão do Fraxx.", w: "Novidades", now: "Atualizar agora", later: "Mais tarde", h: "Até lá tudo funciona como de costume, também offline. As tuas entradas são mantidas.", busy: "A atualizar …", gen: "Melhorias e correções." },
    nl: { v: "Versie", ok: "Up-to-date", since: "Nieuw sinds jouw versie", t: "Update beschikbaar", l: "Er is een nieuwe versie van Fraxx.", w: "Wat is er nieuw", now: "Nu bijwerken", later: "Later", h: "Tot die tijd werkt alles zoals gewoonlijk, ook offline. Je eigen items blijven bewaard.", busy: "Bijwerken …", gen: "Verbeteringen en correcties." },
    pl: { v: "Wersja", ok: "Aktualna", since: "Nowości od twojej wersji", t: "Dostępna aktualizacja", l: "Jest nowa wersja Fraxx.", w: "Co nowego", now: "Aktualizuj teraz", later: "Później", h: "Do tego czasu wszystko działa jak zwykle, także offline. Twoje własne wpisy zostaną zachowane.", busy: "Aktualizacja …", gen: "Ulepszenia i poprawki." },
    sv: { v: "Version", ok: "Uppdaterad", since: "Nytt sedan din version", t: "Uppdatering tillgänglig", l: "En ny version av Fraxx finns.", w: "Nyheter", now: "Uppdatera nu", later: "Senare", h: "Tills dess fungerar allt som vanligt, även offline. Dina egna poster finns kvar.", busy: "Uppdaterar …", gen: "Förbättringar och rättelser." },
    nb: { v: "Versjon", ok: "Oppdatert", since: "Nytt siden din versjon", t: "Oppdatering tilgjengelig", l: "En ny versjon av Fraxx er klar.", w: "Hva er nytt", now: "Oppdater nå", later: "Senere", h: "Inntil da fungerer alt som vanlig, også uten nett. Dine egne oppføringer beholdes.", busy: "Oppdaterer …", gen: "Forbedringer og rettelser." }
  };
  let updShown = false;
  const swReg = async () => { try { return await navigator.serviceWorker?.getRegistration(); } catch (e) { return null; } };
  function waitWaiting(reg, ms) {
    return new Promise(res => {
      if (!reg) return res(null);
      if (reg.waiting) return res(reg.waiting);
      const t = setTimeout(() => res(reg.waiting || null), ms);
      const watch = w => w && w.addEventListener("statechange", () => { if (w.state === "installed") { clearTimeout(t); res(reg.waiting || w); } });
      watch(reg.installing);
      reg.addEventListener("updatefound", () => watch(reg.installing));
    });
  }
  async function updateDialog(force) {
    if (updShown && !force) return;
    if (document.getElementById("mlupd")) return;
    try {
      await ML.ready();
      const reg = await swReg();
      const pend = ML.pendingUpdate();
      const codeWaiting = !!(reg && reg.waiting && navigator.serviceWorker.controller);
      if (!pend && !codeWaiting) return;
      updShown = true;
      const lang = ML.srcLang(), T = UPD_T[lang] || UPD_T.en;
      // Änderungen seit der eigenen Fassung (neueste zuerst)
      // Alle Änderungen von der Fassung des Nutzers bis zur neuesten, je Version gruppiert
      let groups = [];
      try {
        const ch = await changes(true);
        const from = (pend && pend.from) || ML.release();
        const rel = (ch.releases || []).filter(r => !from || r.release > from);
        (rel.length ? rel : (ch.releases || []).slice(0, 1)).slice(0, 12).forEach(r => {
          const n = ((r.notes && (r.notes[lang] || r.notes.en || r.notes.de)) || []).filter(x => !groups.some(g => g.n.includes(x)));
          if (n.length) groups.push({ v: r.version || "", d: r.date || "", n });
        });
      } catch (e) {}
      if (!groups.length) groups = [{ v: "", d: "", n: [T.gen] }];
      const ov = document.createElement("div"); ov.id = "mlupd"; ov.setAttribute("data-notr", "");
      ov.innerHTML = `<style>#mlupd{position:fixed;inset:0;z-index:300;background:rgb(10 14 20 / .45);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);display:flex;align-items:center;justify-content:center;padding:max(16px,env(safe-area-inset-top)) max(16px,env(safe-area-inset-right)) max(24px,calc(env(safe-area-inset-bottom) + 16px)) max(16px,env(safe-area-inset-left));box-sizing:border-box}
#mlupd .b{box-sizing:border-box;width:min(520px,100%);max-height:100%;overflow:auto;-webkit-overflow-scrolling:touch;background:var(--surface,#f3f1ef);color:var(--ink,#141212);border-radius:22px;box-shadow:0 24px 60px rgb(10 14 20 / .3);padding:24px 24px 20px}
#mlupd .k{font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--hl,#cc5530);margin:0 0 6px}
#mlupd h2{margin:0 0 6px;font-size:1.5rem;letter-spacing:-.02em}#mlupd p{margin:0;color:var(--muted,#6b635d);line-height:1.5}
#mlupd h3{margin:16px 0 8px;font-size:1rem}#mlupd ul{margin:0;padding-left:20px;line-height:1.5}#mlupd li{margin:4px 0}
#mlupd .r{display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap;margin-top:20px;position:sticky;bottom:-20px;background:var(--surface,#f3f1ef);padding:12px 0 20px;margin-bottom:-20px;z-index:1}
#mlupd button{font:inherit;font-weight:700;border:0;border-radius:999px;padding:10px 18px;cursor:pointer}
#mlupd .y{background:var(--hl,#cc5530);color:var(--hl-ink,#fff)}#mlupd .n{background:var(--surface-2,#e9e5e2);color:inherit}#mlupd .y:disabled{opacity:.7;cursor:default}
#mlupd .h{font-size:13px;margin-top:14px}#mlupd h4{margin:14px 0 4px;font-size:.92rem;color:var(--muted,#6b635d)}#mlupd h4:first-of-type{margin-top:4px}</style>
<div class="b" role="dialog" aria-modal="true" aria-labelledby="mlupdt"><p class="k">Fraxx</p><h2 id="mlupdt"></h2><p class="l"></p><h3></h3><div class="g"></div><p class="h"></p>
<div class="r"><button type="button" class="n"></button><button type="button" class="y"></button></div></div>`;
      ov.querySelector("h2").textContent = T.t; ov.querySelector(".l").textContent = T.l; ov.querySelector("h3").textContent = T.w;
      ov.querySelector(".h").textContent = T.h;
      const cur = curVersion(), box = ov.querySelector(".g");
      if (cur && groups.length > 1) ov.querySelector(".l").textContent = T.l + " " + T.since + " " + cur + ":";
      groups.forEach(g => {
        if (groups.length > 1 && g.v) { const h = document.createElement("h4"); h.textContent = T.v + " " + g.v + (g.d ? " · " + new Date(g.d).toLocaleDateString(lang, { day: "numeric", month: "long", year: "numeric" }) : ""); box.appendChild(h); }
        const ul = document.createElement("ul"); g.n.forEach(x => { const li = document.createElement("li"); li.textContent = x; ul.appendChild(li); }); box.appendChild(ul);
      });
      const yes = ov.querySelector(".y"), no = ov.querySelector(".n");
      yes.textContent = T.now; no.textContent = T.later;
      no.addEventListener("click", () => ov.remove());
      yes.addEventListener("click", async () => {
        yes.disabled = true; no.disabled = true; yes.textContent = T.busy;
        try { await ML.applyUpdate(); } catch (e) {}
        // Neue App-Fassung (falls vorhanden) aktivieren und neu laden
        const r = await swReg(); try { await r?.update(); } catch (e) {}
        const w = await waitWaiting(r, 12000);
        if (w && navigator.serviceWorker.controller) {
          navigator.serviceWorker.addEventListener("controllerchange", () => location.reload(), { once: true });
          w.postMessage("skipWaiting");
          setTimeout(() => location.reload(), 5000);
        } else location.reload();
      });
      document.body.appendChild(ov);
      setTimeout(() => yes.focus(), 50);
    } catch (e) { console.warn("Update", e); }
  }
  setTimeout(updateDialog, 2500);
  // Eine neue App-Fassung kann auch erst während der Nutzung fertig geladen sein
  (async () => { const r = await swReg(); if (!r) return; r.addEventListener("updatefound", () => { const w = r.installing; w && w.addEventListener("statechange", () => { if (w.state === "installed" && navigator.serviceWorker.controller) { updateDialog(); checkAvail(); } }); }); })();

  // ---------- Version in den Einstellungen, Markierung am ⚙ ----------
  let chCache = null;
  async function changes(fresh) {
    if (chCache && !fresh) return chCache;
    try { chCache = await (await fetch((window.ML_DATA || "data/") + "changes.json", { cache: "no-cache" })).json(); } catch (e) { chCache = chCache || {}; }
    return chCache;
  }
  // Versionsnummer der eigenen Fassung; ältere Installationen kennen sie noch nicht und schlagen sie nach
  function curVersion() {
    const v = ML.appVersion && ML.appVersion(); if (v) return v;
    const rel = (chCache && chCache.releases) || [], mine = ML.release();
    const r = rel.find(x => x.release === mine); if (r) return r.version || "0.1";
    return rel.length ? (rel[rel.length - 1].version || "0.1") : "";
  }
  const vcss = document.createElement("style");
  vcss.textContent = `
  .mlver{flex:1 1 100%;display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding-bottom:12px;border-bottom:1px solid var(--line);font-size:13.5px}
  .mlver .vl{color:var(--muted);font-weight:500}.mlver b{font-weight:700;font-variant-numeric:tabular-nums}
  .mlver .vok{color:var(--muted);font-size:13px}
  .mlver .vbuild{color:var(--muted);font-size:12px;font-variant-numeric:tabular-nums}
  .mlver .vup{margin-left:auto;border:0;cursor:pointer;font:inherit;font-size:13.5px;font-weight:700;border-radius:999px;padding:6px 14px;background:var(--hl,#a3395f);color:var(--hl-ink,#fff);display:inline-flex;align-items:center;gap:7px}
  .mlver .vup::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor;opacity:.9}
  .mlver .vup:hover{filter:brightness(1.08)}
  #setbtn.mlhasupd{position:relative}
  #setbtn.mlhasupd::after{content:"";position:absolute;top:-1px;right:-1px;width:12px;height:12px;border-radius:50%;background:var(--hl,#a3395f);box-shadow:0 0 0 2px var(--bg,#fff);animation:mlpulse 2.4s ease-in-out infinite}
  @keyframes mlpulse{0%,100%{transform:scale(1)}50%{transform:scale(1.25)}}
  @media (prefers-reduced-motion:reduce){ #setbtn.mlhasupd::after{animation:none} }`;
  document.head.appendChild(vcss);
  function versionRow() {
    const pop = document.getElementById("setpop"); if (!pop) return null;
    let row = pop.querySelector(".mlver");
    if (!row) {
      row = document.createElement("div"); row.className = "mlver"; row.setAttribute("data-notr", "");
      row.innerHTML = `<span class="vl"></span><b></b><span class="vok"></span><span class="vbuild"></span><button type="button" class="vup" hidden></button>`;
      { const m = document.querySelector('meta[name="fraxx-build"]'); const vb = row.querySelector(".vbuild"); if (vb && m) vb.textContent = "· Stand " + String(m.content || "").slice(0, 7); }
      row.querySelector(".vup").addEventListener("click", () => { document.getElementById("setbtn")?.click(); updateDialog(true); });
      const gb = document.createElement("button"); gb.type = "button"; gb.className = "vguide";
      gb.addEventListener("click", () => { document.getElementById("setbtn")?.click(); ML.showGuide && ML.showGuide(); });
      row.insertBefore(gb, row.querySelector(".vup"));
      pop.prepend(row);
    }
    return row;
  }
  async function checkAvail() {
    try {
      await ML.ready(); await changes();
      const reg = await swReg(), pend = ML.pendingUpdate();
      const avail = !!pend || !!(reg && reg.waiting && navigator.serviceWorker.controller);
      const T = UPD_T[ML.srcLang()] || UPD_T.en, row = versionRow();
      if (row) {
        const v = curVersion();
        row.querySelector(".vl").textContent = T.v; row.querySelector("b").textContent = (v || "–") + " Beta";
        row.querySelector(".vok").textContent = avail ? "" : "✓ " + T.ok;
        { const gb = row.querySelector(".vguide"); if (gb) gb.textContent = "▶ " + (GUIDE_T[ML.srcLang()] || GUIDE_T.en)[0]; }
        const b = row.querySelector(".vup"); b.hidden = !avail;
        b.textContent = T.t + (pend && pend.version ? " · " + pend.version : "");
      }
      document.getElementById("setbtn")?.classList.toggle("mlhasupd", avail);
      const sb = document.getElementById("setbtn"); if (sb) sb.title = avail ? T.t : (sb.getAttribute("aria-label") || "");
    } catch (e) { console.warn("Version", e); }
  }
  checkAvail();
  ML.onChange(() => { clearTimeout(checkAvail.t); checkAvail.t = setTimeout(checkAvail, 800); });
  // Wer die App lange offen hat, erfährt beim Zurückkehren von neuen Fassungen (höchstens alle 30 Minuten)
  let lastLook = Date.now();
  document.addEventListener("visibilitychange", async () => {
    if (document.hidden || Date.now() - lastLook < 30 * 60e3) return;
    lastLook = Date.now();
    try { (await swReg())?.update(); await ML.checkUpdates(); } catch (e) {}
    checkAvail();
  });

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
      const h = await window.showSaveFilePicker({ suggestedName: "multilingo-sicherung.json", types: [{ description: "Fraxx-Sicherung", accept: { "application/json": [".json"] } }] });
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
    ML.apiKey.set(v); m.className = "mlmsg"; m.textContent = "Gespeichert. Fraxx lädt neu …"; setTimeout(() => location.reload(), 900);
  });
  $("mlkeydel").addEventListener("click", () => { ML.apiKey.set(""); $("mlkeymsg").textContent = "Schlüssel entfernt. Fraxx lädt neu …"; setTimeout(() => location.reload(), 900); });
  }
  window.addEventListener("ml-badkey", () => { const n = document.getElementById("notice"); if (n) { n.hidden = false; n.textContent = "Der Claude-API-Schlüssel wurde abgelehnt. Unter ⚙ → App, Sprachpakete & Sicherung kannst du ihn ändern."; } });

  // Zurücksetzen / Updates
  $("mlreset").addEventListener("click", async () => {
    if (!confirm("Wirklich alle eigenen Änderungen auf diesem Gerät löschen?")) return;
    await ML.resetUser(); $("mlresetmsg").textContent = "Gelöscht. Fraxx lädt neu …"; setTimeout(() => location.reload(), 900);
  });
  $("mlupdate").addEventListener("click", async () => {
    const m = $("mlresetmsg"); m.className = "mlmsg"; m.textContent = "Suche …";
    try { const reg = await navigator.serviceWorker?.getRegistration(); await reg?.update(); const has = await ML.checkUpdates(); await new Promise(r => setTimeout(r, 1500));
      // Neue App-Fassung wird gerade geladen: abwarten, bis sie bereitsteht (sonst hieße es fälschlich „Alles aktuell“)
      const w = reg && reg.installing; if (w) { m.textContent = "…"; await new Promise(r => { const t = setTimeout(r, 45000); w.addEventListener("statechange", () => { if (w.state === "installed" || w.state === "redundant") { clearTimeout(t); r(); } }); }); }
      checkAvail(); if (has || (reg && reg.waiting)) { m.textContent = ""; close(); updateDialog(true); } else m.textContent = "Alles aktuell."; }
    catch (e) { m.className = "mlmsg err"; m.textContent = "Keine Verbindung."; }
  });
  // ---------- Anleitung: Willkommen nach dem ersten Start, Link in den Einstellungen ----------
  const GUIDE_T = {
    de: ["Anleitung", "Willkommen bei Fraxx!", "Möchtest du dir zuerst die kurze Anleitung ansehen? Sie zeigt dir in wenigen Minuten, wie alles funktioniert.", "Anleitung ansehen", "Sofort loslegen", "Schließen", "Jetzt loslegen"],
    en: ["Guide", "Welcome to Fraxx!", "Would you like to watch the short guide first? It shows you how everything works in just a few minutes.", "Watch the guide", "Start right away", "Close", "Get started now"],
    fr: ["Guide", "Bienvenue sur Fraxx !", "Veux-tu d'abord regarder le petit guide ? Il te montre en quelques minutes comment tout fonctionne.", "Voir le guide", "Commencer tout de suite", "Fermer", "Commencer maintenant"],
    es: ["Guía", "¡Bienvenido a Fraxx!", "¿Quieres ver primero la guía breve? Te muestra en pocos minutos cómo funciona todo.", "Ver la guía", "Empezar ya", "Cerrar", "Empezar ahora"],
    it: ["Guida", "Benvenuto su Fraxx!", "Vuoi guardare prima la breve guida? Ti mostra in pochi minuti come funziona tutto.", "Guarda la guida", "Inizia subito", "Chiudi", "Inizia ora"],
    pt: ["Guia", "Bem-vindo ao Fraxx!", "Queres ver primeiro o guia rápido? Mostra-te em poucos minutos como tudo funciona.", "Ver o guia", "Começar já", "Fechar", "Começar agora"],
    nl: ["Handleiding", "Welkom bij Fraxx!", "Wil je eerst de korte handleiding bekijken? Die laat je in een paar minuten zien hoe alles werkt.", "Handleiding bekijken", "Meteen beginnen", "Sluiten", "Nu beginnen"],
    pl: ["Przewodnik", "Witaj w Fraxx!", "Chcesz najpierw obejrzeć krótki przewodnik? W kilka minut pokaże ci, jak wszystko działa.", "Zobacz przewodnik", "Zacznij od razu", "Zamknij", "Zacznij teraz"],
    tr: ["Kılavuz", "Fraxx'a hoş geldin!", "Önce kısa kılavuza göz atmak ister misin? Birkaç dakikada her şeyin nasıl çalıştığını gösterir.", "Kılavuzu izle", "Hemen başla", "Kapat", "Şimdi başla"],
    el: ["Οδηγός", "Καλώς ήρθες στο Fraxx!", "Θέλεις να δεις πρώτα τον σύντομο οδηγό; Σου δείχνει σε λίγα λεπτά πώς λειτουργούν όλα.", "Δες τον οδηγό", "Ξεκίνα αμέσως", "Κλείσιμο", "Ξεκίνα τώρα"],
    hr: ["Vodič", "Dobro došli u Fraxx!", "Želiš li prvo pogledati kratki vodič? U nekoliko minuta pokazuje kako sve funkcionira.", "Pogledaj vodič", "Odmah počni", "Zatvori", "Počni sada"],
    sv: ["Guide", "Välkommen till Fraxx!", "Vill du titta på den korta guiden först? Den visar på några minuter hur allt fungerar.", "Visa guiden", "Börja direkt", "Stäng", "Börja nu"],
    da: ["Vejledning", "Velkommen til Fraxx!", "Vil du først se den korte vejledning? Den viser dig på få minutter, hvordan alt fungerer.", "Se vejledningen", "Start med det samme", "Luk", "Kom i gang nu"],
    nb: ["Veiledning", "Velkommen til Fraxx!", "Vil du se den korte veiledningen først? Den viser deg på noen få minutter hvordan alt fungerer.", "Se veiledningen", "Start med en gang", "Lukk", "Kom i gang nå"],
    cs: ["Návod", "Vítej v Multilingu!", "Chceš se nejdřív podívat na krátký návod? Za pár minut ti ukáže, jak všechno funguje.", "Zobrazit návod", "Začít hned", "Zavřít", "Začít teď"],
    hu: ["Útmutató", "Üdv a Multilingóban!", "Szeretnéd először megnézni a rövid útmutatót? Néhány perc alatt megmutatja, hogyan működik minden.", "Útmutató megnézése", "Azonnal kezdem", "Bezárás", "Kezdjük most"],
    ro: ["Ghid", "Bine ai venit la Fraxx!", "Vrei să vezi mai întâi ghidul scurt? Îți arată în câteva minute cum funcționează totul.", "Vezi ghidul", "Începe imediat", "Închide", "Începe acum"],
    ca: ["Guia", "Benvingut a Fraxx!", "Vols veure primer la guia breu? Et mostra en pocs minuts com funciona tot.", "Veure la guia", "Començar ja", "Tancar", "Començar ara"],
    ru: ["Руководство", "Добро пожаловать в Fraxx!", "Хочешь сначала посмотреть короткое руководство? За несколько минут оно покажет, как всё работает.", "Смотреть руководство", "Начать сразу", "Закрыть", "Начать сейчас"],
    ja: ["ガイド", "Fraxxへようこそ！", "まず短いガイドを見ますか？数分ですべての使い方がわかります。", "ガイドを見る", "すぐに始める", "閉じる", "今すぐ始める"],
    zh: ["使用指南", "欢迎使用 Fraxx！", "要先看一下简短的使用指南吗？只需几分钟，就能了解所有功能。", "查看指南", "立即开始", "关闭", "现在开始"],
    ar: ["الدليل", "مرحبًا بك في Fraxx!", "هل تريد مشاهدة الدليل القصير أولًا؟ يوضح لك في دقائق قليلة كيف يعمل كل شيء.", "مشاهدة الدليل", "ابدأ فورًا", "إغلاق", "ابدأ الآن"] };
  const gT = () => GUIDE_T[ML.srcLang()] || GUIDE_T.en;
  const GUIDE_BASE = window.ML_ADMIN ? "../anleitung/" : "anleitung/";
  const gcss = document.createElement("style");
  gcss.textContent = `#mlguide{position:fixed;inset:0;z-index:320;background:var(--bg,#e5e2e0);display:flex;flex-direction:column}
  #mlguide iframe{flex:1 1 auto;width:100%;border:0;background:#fff}
  #mlguide .gbar{flex:none;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:calc(8px + env(safe-area-inset-top)) max(14px, env(safe-area-inset-right)) 8px max(16px, env(safe-area-inset-left));background:var(--surface,#f3f1ef);color:var(--ink,#141212);box-shadow:0 1px 0 var(--line,#d9d4d0);font-weight:700}
  #mlguide .gx{width:38px;height:38px;flex:none;border-radius:50%;border:0;background:var(--surface-2,#e9e5e2);color:inherit;font-size:17px;cursor:pointer}
  #mlwel{position:fixed;inset:0;z-index:310;background:rgb(10 14 20 / .45);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);display:grid;place-items:center;padding:16px;font-family:inherit}
  #mlwel .wb{box-sizing:border-box;width:min(480px,100%);background:var(--surface,#f3f1ef);color:var(--ink,#141212);border-radius:24px;box-shadow:0 24px 60px rgb(10 14 20 / .3);padding:30px 26px 24px;text-align:center}
  #mlwel .wlogo{display:block;height:40px;width:auto;margin:0 auto 18px;color:var(--ink,#141212)}
  #mlwel h2{margin:0 0 10px;font-size:1.6rem;letter-spacing:-.02em}#mlwel p{margin:0 0 22px;color:var(--muted,#6b635d);line-height:1.5}
  #mlwel .r{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
  #mlwel button{font:inherit;font-weight:700;border:0;border-radius:999px;padding:12px 22px;cursor:pointer}
  #mlwel .y{background:var(--ink,#141212);color:var(--surface,#f3f1ef)}#mlwel .n{background:var(--surface-2,#e9e5e2);color:inherit}
  .mlver .vguide{border:0;cursor:pointer;font:inherit;font-size:13.5px;font-weight:600;border-radius:999px;padding:6px 14px;background:var(--surface-2,#e9e5e2);color:var(--ink,#141212)}`;
  document.head.appendChild(gcss);
  function showGuide() {
    if (document.getElementById("mlguide")) return;
    const T = gT(), ov = document.createElement("div"); ov.id = "mlguide"; ov.setAttribute("data-notr", "");
    ov.setAttribute("role", "dialog"); ov.setAttribute("aria-modal", "true"); ov.setAttribute("aria-label", T[0]);
    const fr = document.createElement("iframe"); fr.title = T[0];
    fr.src = GUIDE_BASE + "?lang=" + encodeURIComponent(ML.srcLang() || "de") + "&embed=1";
    const x = document.createElement("button"); x.type = "button"; x.className = "gx"; x.textContent = "✕"; x.setAttribute("aria-label", T[5]); x.title = T[5];
    const close = () => { ov.remove(); window.removeEventListener("message", onMsg); document.documentElement.style.overflow = ""; };
    const onMsg = ev => { if (ev.origin === location.origin && ev.data === "ml-guide-close") close(); };
    x.addEventListener("click", close); window.addEventListener("message", onMsg);
    // Eigene Leiste oben (mit Abstand zur Statusleiste/Notch), damit nichts über der Anleitung liegt
    const bar = document.createElement("div"); bar.className = "gbar"; const tt = document.createElement("span"); tt.textContent = T[0];
    bar.append(tt, x); ov.append(bar, fr); document.body.appendChild(ov); document.documentElement.style.overflow = "hidden";
    setTimeout(() => x.focus(), 50);
  }
  ML.showGuide = showGuide;
  // ---------- Ladeanzeige: Sprachpakete werden noch geladen ----------
  // Beim ersten Start (oder nach einem Update) kommen die Einträge erst nach ein paar Sekunden.
  // Damit niemand denkt, die App sei leer oder kaputt, steht solange unten ein Hinweis mit Fortschritt.
  const LOAD_T = {
    de: ["Sprachen werden geladen …", "Beim ersten Start dauert das einen Moment.", "Die Sprachen konnten nicht geladen werden. Prüfe deine Internetverbindung.", "Erneut versuchen"],
    en: ["Loading languages …", "The first start takes a moment.", "The languages could not be loaded. Check your internet connection.", "Try again"],
    fr: ["Chargement des langues …", "Le premier démarrage prend un instant.", "Les langues n'ont pas pu être chargées. Vérifie ta connexion Internet.", "Réessayer"],
    es: ["Cargando idiomas …", "El primer inicio tarda un momento.", "No se han podido cargar los idiomas. Comprueba tu conexión a Internet.", "Reintentar"],
    it: ["Caricamento delle lingue …", "Il primo avvio richiede un momento.", "Non è stato possibile caricare le lingue. Controlla la connessione a Internet.", "Riprova"],
    pt: ["A carregar idiomas …", "O primeiro arranque demora um momento.", "Não foi possível carregar os idiomas. Verifica a tua ligação à Internet.", "Tentar novamente"],
    nl: ["Talen worden geladen …", "De eerste keer duurt dit even.", "De talen konden niet worden geladen. Controleer je internetverbinding.", "Opnieuw proberen"],
    pl: ["Ładowanie języków …", "Pierwsze uruchomienie chwilę trwa.", "Nie udało się załadować języków. Sprawdź połączenie z internetem.", "Spróbuj ponownie"],
    tr: ["Diller yükleniyor …", "İlk açılış biraz sürer.", "Diller yüklenemedi. İnternet bağlantını kontrol et.", "Tekrar dene"],
    el: ["Φόρτωση γλωσσών …", "Η πρώτη εκκίνηση διαρκεί λίγο.", "Δεν ήταν δυνατή η φόρτωση των γλωσσών. Έλεγξε τη σύνδεσή σου στο διαδίκτυο.", "Δοκίμασε ξανά"],
    hr: ["Učitavanje jezika …", "Prvo pokretanje traje trenutak.", "Jezici se nisu mogli učitati. Provjeri internetsku vezu.", "Pokušaj ponovno"],
    sv: ["Språken laddas …", "Första starten tar en stund.", "Språken kunde inte laddas. Kontrollera din internetanslutning.", "Försök igen"],
    da: ["Sprogene indlæses …", "Første start tager et øjeblik.", "Sprogene kunne ikke indlæses. Tjek din internetforbindelse.", "Prøv igen"],
    nb: ["Språkene lastes inn …", "Første oppstart tar et øyeblikk.", "Språkene kunne ikke lastes inn. Sjekk internettforbindelsen.", "Prøv igjen"],
    cs: ["Načítání jazyků …", "První spuštění chvíli trvá.", "Jazyky se nepodařilo načíst. Zkontroluj připojení k internetu.", "Zkusit znovu"],
    hu: ["Nyelvek betöltése …", "Az első indítás eltart egy pillanatig.", "A nyelveket nem sikerült betölteni. Ellenőrizd az internetkapcsolatot.", "Újra"],
    ro: ["Se încarcă limbile …", "Prima pornire durează puțin.", "Limbile nu au putut fi încărcate. Verifică conexiunea la internet.", "Încearcă din nou"],
    ca: ["S'estan carregant les llengües …", "El primer inici triga un moment.", "No s'han pogut carregar les llengües. Comprova la connexió a Internet.", "Torna-ho a provar"],
    ru: ["Загрузка языков …", "Первый запуск занимает немного времени.", "Не удалось загрузить языки. Проверь подключение к интернету.", "Повторить"],
    ja: ["言語を読み込んでいます …", "初回の起動には少し時間がかかります。", "言語を読み込めませんでした。インターネット接続を確認してください。", "再試行"],
    zh: ["正在加载语言 …", "首次启动需要一点时间。", "无法加载语言。请检查网络连接。", "重试"],
    ar: ["جارٍ تحميل اللغات …", "يستغرق التشغيل الأول لحظة.", "تعذّر تحميل اللغات. تحقّق من اتصالك بالإنترنت.", "إعادة المحاولة"]
  };
  {
    const lcss = document.createElement("style");
    lcss.textContent = `
    #mlload{box-sizing:border-box;position:fixed;left:50%;bottom:max(18px,env(safe-area-inset-bottom));transform:translate(-50%,12px);z-index:70;width:min(420px,calc(100% - 28px));
      background:var(--ink);color:var(--surface);border-radius:18px;box-shadow:0 12px 36px rgb(20 14 12 / .28);padding:13px 16px 12px;
      display:grid;grid-template-columns:auto 1fr;gap:2px 12px;align-items:center;opacity:0;transition:opacity .25s,transform .25s;pointer-events:none}
    #mlload.on{opacity:1;transform:translate(-50%,0);pointer-events:auto}
    #mlload.full{inset:0;left:0;bottom:0;transform:none;width:auto;border-radius:0;background:var(--bg,#e5e2e0);color:var(--ink,#141212);box-shadow:none;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px max(16px,env(safe-area-inset-right)) 24px max(16px,env(safe-area-inset-left));z-index:300}
    #mlload.full .fwrap{width:min(420px,100%);display:flex;flex-direction:column;gap:14px}
    #mlload.full .flogo{height:44px;width:auto;align-self:center;margin-bottom:10px;color:var(--ink,#141212)}
    #mlload.full b{font-size:20px;text-align:center}
    #mlload.full small{font-size:14px;text-align:center;opacity:.7}
    #mlload.full .frow{display:grid;grid-template-columns:1fr auto;gap:6px 10px;align-items:center;font-size:15px;font-weight:600}
    #mlload.full .frow em{font-style:normal;font-size:13px;font-weight:600;opacity:.6;font-variant-numeric:tabular-nums}
    #mlload.full .frow .lbar{grid-column:1 / -1;margin:0;height:6px;background:rgb(0 0 0 / .1)}
    #mlload.full .frow.done em{color:var(--ok,#1f8a53);opacity:1}
    #mlload .lsp{grid-row:1 / span 2;width:22px;height:22px;border-radius:50%;border:3px solid rgb(255 255 255 / .25);border-top-color:var(--hl,#a3395f);animation:mlspin .9s linear infinite}
    #mlload b{font-size:15px;font-weight:700}
    #mlload small{font-size:13px;opacity:.75;line-height:1.35}
    #mlload .lbar{grid-column:1 / -1;height:4px;border-radius:4px;background:rgb(255 255 255 / .18);margin-top:9px;overflow:hidden}
    #mlload .lbar > i{display:block;height:100%;width:0;background:var(--hl,#a3395f);border-radius:inherit;transition:width .3s}
    #mlload.err .lsp{display:none}
    #mlload.err{grid-template-columns:1fr}
    #mlload .lbtn{grid-column:1 / -1;justify-self:start;margin-top:9px;border:0;border-radius:999px;background:var(--surface);color:var(--ink);font:inherit;font-size:13.5px;font-weight:700;padding:6px 14px;cursor:pointer}
    @keyframes mlspin{to{transform:rotate(360deg)}}
    @media (prefers-reduced-motion:reduce){ #mlload .lsp{animation:none} #mlload{transition:none} }
    @media print{ #mlload{display:none} }`;
    document.head.appendChild(lcss);
    const box = document.createElement("div"); box.id = "mlload"; box.setAttribute("data-notr", "");
    box.setAttribute("role", "status"); box.setAttribute("aria-live", "polite");
    let timer = null, shown = false;
    const lt = () => LOAD_T[ML.srcLang()] || LOAD_T.en;
    // Erster Start (Pakete werden aus dem Netz geholt): ganzer Bildschirm mit einem Balken je Sprache,
    // die App erscheint erst, wenn alles da ist. Spätere Starts kommen aus dem Gerätespeicher und zeigen nur den kleinen Hinweis.
    let full = false;
    const names = (() => { try { return new Intl.DisplayNames([ML.srcLang()], { type: "language" }); } catch (e) { return null; } })();
    const nm = it => it.k === "core" ? ({ de: "Grunddaten", en: "Basics", fr: "Données de base", es: "Datos básicos", it: "Dati di base", pt: "Dados básicos", nl: "Basisgegevens", pl: "Dane podstawowe", sv: "Grunddata", nb: "Grunndata", tr: "Temel veriler", zh: "基础数据", ar: "البيانات الأساسية" }[ML.srcLang()] || "Basics")
      : ((names && (() => { try { const n = names.of(it.k === "nb" ? "nb" : it.k); return n ? n.charAt(0).toUpperCase() + n.slice(1) : ""; } catch (e) { return ""; } })()) || it.name || it.k);
    const drawFull = st => {
      const T = lt();
      if (!box.querySelector(".fwrap")) {
        box.innerHTML = `<div class="fwrap"></div>`;
        const w = box.querySelector(".fwrap");
        const lg = document.querySelector("#logo .vxlogo"); if (lg) { const c = lg.cloneNode(true); c.setAttribute("class", "flogo"); c.removeAttribute("style"); w.append(c); }
        const b = document.createElement("b"); const sm = document.createElement("small"); w.append(b, sm);
        const list = document.createElement("div"); list.className = "flist"; list.style.cssText = "display:flex;flex-direction:column;gap:12px;margin-top:6px"; w.append(list);
      }
      box.querySelector("b").textContent = T[0]; box.querySelector("small").textContent = T[1];
      const list = box.querySelector(".flist"); list.replaceChildren();
      (st.items || []).forEach(it => {
        const r = document.createElement("div"); r.className = "frow" + (it.st === "done" ? " done" : "");
        const pc = it.st === "done" ? 100 : (it.bytes ? Math.min(99, Math.round(100 * it.got / it.bytes)) : (it.st === "load" ? 5 : 0));
        const n = document.createElement("span"); n.textContent = nm(it);
        const e = document.createElement("em"); e.textContent = it.st === "done" ? "✓" : pc + " %";
        const bar = document.createElement("span"); bar.className = "lbar"; const i = document.createElement("i"); i.style.width = pc + "%"; bar.append(i);
        r.append(n, e, bar); list.append(r);
      });
    };
    const draw = st => {
      if (full && !st.error) { drawFull(st); return; }
      const T = lt();
      box.classList.toggle("err", !!st.error);
      box.dir = ML.srcLang() === "ar" ? "rtl" : "";
      if (st.error) {
        box.innerHTML = `<b></b><button type="button" class="lbtn"></button>`;
        box.querySelector("b").textContent = T[2]; const r = box.querySelector("button"); r.textContent = T[3];
        r.addEventListener("click", () => location.reload());
        return;
      }
      if (!box.querySelector(".lbar")) box.innerHTML = `<span class="lsp" aria-hidden="true"></span><b></b><small></small><span class="lbar" aria-hidden="true"><i></i></span>`;
      box.querySelector("b").textContent = T[0];
      box.querySelector("small").textContent = st.total > 1 ? `${T[1]} ${Math.min(st.done, st.total)}\u202f/\u202f${st.total}` : T[1];
      box.querySelector(".lbar > i").style.width = (st.total ? Math.round(100 * Math.min(st.done, st.total) / st.total) : 5) + "%";
    };
    const show = () => { if (!box.isConnected) document.body.appendChild(box); shown = true; requestAnimationFrame(() => box.classList.add("on")); };
    const hide = () => { clearTimeout(timer); timer = null; if (!shown) return; shown = false; box.classList.remove("on"); setTimeout(() => { if (!shown) box.remove(); }, 300); };
    const update = st => {
      if (st.error) { clearTimeout(timer); draw(st); show(); return; }
      if (!st.active) { hide(); full = false; box.classList.remove("full"); return; }
      // Vollbild, sobald wirklich aus dem Netz geladen wird (dann gibt es Fortschritt in Bytes)
      // Nur wenn ein Paket noch gar nicht auf dem Gerät ist (erster Start, neue Sprache); Aktualisierungen zeigen den kleinen Hinweis
      if (!full && (st.items || []).some(x => x.st === "load" && x.got > 0 && x.fresh)) { full = true; box.innerHTML = ""; box.classList.add("full"); box.classList.remove("err"); clearTimeout(timer); timer = null; draw(st); show(); return; }
      draw(st);
      // Nur zeigen, wenn es spürbar dauert (aus dem Gerätespeicher ist es meist sofort fertig)
      if (!shown && !timer) timer = setTimeout(() => { timer = null; if (ML.loading().active) { draw(ML.loading()); show(); } }, 350);
    };
    window.addEventListener("ml-load", e => update(e.detail || {}));
    if (ML.loading) update(ML.loading());
  }
  (async () => {
    try {
      await ML.ready(); if (!(ML.firstRun && ML.firstRun())) return;
      try { if (localStorage.getItem("ml-nowelcome")) return; } catch (e) {}
      const T = gT(), ov = document.createElement("div"); ov.id = "mlwel"; ov.setAttribute("data-notr", "");
      ov.innerHTML = `<div class="wb" role="dialog" aria-modal="true" aria-labelledby="mlwelt"><svg class="wlogo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 424.2 100" role="img" aria-label="Fraxx"><path d="M0 100V0H80.81V23.98H32.12V41.13H73.98V64.1H32.12V100ZM86.92 100V23.26H110.61L112.5 34.88H113.52Q116.28 28.34 121.66 24.85Q127.03 21.37 133.58 21.37Q136.48 21.37 138.81 21.95Q141.13 22.53 142.15 23.11V47.38H132.85Q123.55 47.38 119.69 52.25Q115.84 57.12 115.84 65.84V100ZM166.13 101.74Q158.14 101.74 152.03 99.71Q145.93 97.67 142.51 92.95Q139.1 88.23 139.1 80.23Q139.1 68.75 145.35 62.86Q151.6 56.98 163.52 54.94Q175.44 52.91 192.15 52.91V49.13Q192.15 44.48 188.88 42.22Q185.61 39.97 180.96 39.97Q177.18 39.97 173.55 41.42Q169.91 42.88 169.91 46.66V47.24H141.42Q141.28 46.66 141.28 46.22Q141.28 45.78 141.28 45.2Q141.28 34.59 151.45 28.05Q161.63 21.51 181.4 21.51Q192.01 21.51 201.02 23.84Q210.03 26.16 215.55 31.61Q221.08 37.06 221.08 46.51V76.45Q221.08 78.78 222.24 80.45Q223.4 82.12 225.73 82.12H230.96V98.84Q229.22 99.85 225.22 100.8Q221.22 101.74 215.84 101.74Q207.12 101.74 201.74 99.13Q196.37 96.51 194.91 92.15H193.9Q189.24 96.22 182.56 98.98Q175.87 101.74 166.13 101.74ZM177.91 83.72Q183.43 83.72 187.79 80.74Q192.15 77.76 192.15 73.11V66.57Q179.36 66.57 173.69 69.4Q168.02 72.24 168.02 76.45Q168.02 80.96 171.15 82.34Q174.27 83.72 177.91 83.72ZM224.27 100 253.78 59.3 227.18 23.26H261.19L273.4 43.6H273.98L286.19 23.26H318.17L291.13 60.03L319.91 100H286.19L271.66 75.87H271.08L256.4 100ZM313.23 100 342.73 59.3 316.13 23.26H350.15L362.35 43.6H362.94L389.76 0H424.22L380.09 60.03L408.87 100H375.15L360.61 75.87H360.03L345.35 100Z" fill="currentColor"/></svg><h2 id="mlwelt"></h2><p></p><div class="r"><button type="button" class="y"></button><button type="button" class="n"></button></div></div>`;
      ov.querySelector("h2").textContent = T[1]; ov.querySelector("p").textContent = T[2];
      const y = ov.querySelector(".y"), n = ov.querySelector(".n"); y.textContent = "▶ " + T[3]; n.textContent = T[4] + " →";
      y.addEventListener("click", () => { ov.remove(); showGuide(); });
      n.addEventListener("click", () => ov.remove());
      document.body.appendChild(ov); setTimeout(() => y.focus(), 50);
    } catch (e) { console.warn("Willkommen", e); }
  })();
})();

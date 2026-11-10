"""Änderungen an der App, die (noch) nicht im Artefakt stehen. build_app.py wendet sie beim Bauen an.
Jede Änderung wird übersprungen, sobald das Artefakt sie selbst enthält (new_text schon vorhanden) –
dann kann der Eintrag hier gelöscht werden. Fehlt die Stelle ganz, gibt es eine Warnung."""
EDITS = []
def E(a, b): EDITS.append((a, b))

# 1) Tabelle: Tipp auf das Wort öffnet auf dem Handy die Übersetzungen; Ändern über ✎
E('''      t.addEventListener("click",()=>{ editId=e.id; editCtx=ekey; editDraft=srcText(e); confirmId=null; render(); });''',
  '''      // Handy: Tipp auf Wort oder Satz klappt die Übersetzungen darunter auf (Ändern über ✎). Breiter Bildschirm: Tipp ändert.
      t.addEventListener("click",()=>{ if(window.matchMedia && matchMedia("(max-width:760px)").matches && r._mt){ r._mt.click(); return; } editId=e.id; editCtx=ekey; editDraft=srcText(e); confirmId=null; render(); });''')
E('''    a.append(star, pin, re, del); r.append(a);''',
  '''    const ed = el("button","icon medit","✎"); ed.type="button"; ed.title="Ändern"; ed.setAttribute("aria-label","Ändern: "+srcText(e));
    ed.addEventListener("click",()=>{ editId=e.id; editCtx=ekey; editDraft=srcText(e); confirmId=null; render(); });
    a.append(star, pin, ed, re, del); r.append(a);''')
E('''.icon.del:hover{color:var(--danger)}''',
  '''.icon.del:hover{color:var(--danger)}
.icon.medit{display:none}
@media (max-width:760px){ .row:not(.head) .actions .icon.medit{display:inline-grid} .detx{cursor:pointer} }
@media (max-width:760px) and (hover:none){ .detx:hover{background:transparent} }''')

# 2) Quiz: eigene, gestaltete Auswahlliste statt des nackten <select>
E('''  function renderQuizSetup(){''',
  '''  // Gestaltete Auswahlliste: das <select> bleibt (unsichtbar) für Wert und change-Ereignis,
  // davor ein Knopf mit eigener Liste. Auf dem Handy als Blatt von unten.
  function fancySelect(sel, label){
    sel.classList.add("fsnative"); sel.tabIndex = -1; sel.setAttribute("aria-hidden","true");
    const w = el("div","fsel"), b = el("button","fsbtn"); b.type = "button"; b.id = sel.id + "-btn";
    b.setAttribute("aria-haspopup","listbox"); b.setAttribute("aria-expanded","false");
    const cur = () => sel.options[sel.selectedIndex] || sel.options[0];
    const parse = o => { const raw = o ? o.textContent : ""; const sub = /^\\s*↳\\s*/.test(raw); return {sub, text: raw.replace(/^\\s*↳\\s*/,"").trim()}; };
    const bl = el("span","fsval", parse(cur()).text); b.append(bl, el("span","fschev"));
    if(label){ b.setAttribute("aria-label", label); }
    sel.before(w); w.append(b, sel);
    let pop = null, back = null;
    const close = (focus) => { if(!pop) return; pop.remove(); back && back.remove(); pop = back = null; b.setAttribute("aria-expanded","false"); document.removeEventListener("pointerdown", outside, true); if(focus) b.focus(); };
    const outside = ev => { if(pop && !pop.contains(ev.target) && !b.contains(ev.target)) close(false); };
    const pick = i => { close(true); if(sel.selectedIndex === i) return; sel.selectedIndex = i; bl.textContent = parse(cur()).text; sel.dispatchEvent(new Event("change", {bubbles:true})); };
    const open = () => {
      const sheet = window.matchMedia && matchMedia("(max-width:760px)").matches;
      pop = el("div","fspop" + (sheet ? " sheet" : "")); pop.setAttribute("role","listbox"); pop.id = sel.id + "-list";
      if(label) pop.setAttribute("aria-label", label);
      if(sheet){ back = el("div","fsback"); back.addEventListener("click",()=>close(true)); document.body.append(back); if(label) pop.append(el("div","fshead", label)); }
      const items = [];
      [...sel.options].forEach((o,i)=>{
        const {sub, text} = parse(o), it = el("button","fsopt" + (sub ? " sub" : "") + (i===sel.selectedIndex ? " on" : ""));
        it.type = "button"; it.setAttribute("role","option"); it.setAttribute("aria-selected", String(i===sel.selectedIndex));
        it.append(el("span","fstx", text)); it.addEventListener("click",()=>pick(i)); items.push(it); pop.append(it);
      });
      pop.addEventListener("keydown", ev=>{
        const k = items.indexOf(document.activeElement);
        if(ev.key==="ArrowDown"){ ev.preventDefault(); (items[k+1]||items[0]).focus(); }
        else if(ev.key==="ArrowUp"){ ev.preventDefault(); (items[k-1]||items[items.length-1]).focus(); }
        else if(ev.key==="Home"){ ev.preventDefault(); items[0].focus(); }
        else if(ev.key==="End"){ ev.preventDefault(); items[items.length-1].focus(); }
        else if(ev.key==="Escape" || ev.key==="Tab"){ ev.preventDefault(); close(true); }
      });
      (sheet ? document.body : w).append(pop); b.setAttribute("aria-expanded","true");
      const on = items[sel.selectedIndex] || items[0];
      if(on){ on.focus({preventScroll:true}); on.scrollIntoView({block:"center"}); }
      setTimeout(()=>document.addEventListener("pointerdown", outside, true));
    };
    b.addEventListener("click",()=> pop ? close(true) : open());
    b.addEventListener("keydown", ev=>{ if((ev.key==="ArrowDown" || ev.key==="ArrowUp") && !pop){ ev.preventDefault(); open(); } });
    return w;
  }
  function renderQuizSetup(){''')
E('''    sel.addEventListener("change",()=>{ qs.scope = sel.value; qs.confirmReset=false; saveQuizPrefs(); renderQuiz(); });
    g3.append(sel);''',
  '''    sel.addEventListener("change",()=>{ qs.scope = sel.value; qs.confirmReset=false; saveQuizPrefs(); renderQuiz(); });
    g3.append(sel); fancySelect(sel, "Bereich"); g3.querySelector("label").setAttribute("for","quizscope-btn");''')
E('''    sel.addEventListener("change",()=>{ qs.gch = sel.value; saveQuizPrefs(); renderQuiz(); });
    g3.append(sel);''',
  '''    sel.addEventListener("change",()=>{ qs.gch = sel.value; saveQuizPrefs(); renderQuiz(); });
    g3.append(sel); fancySelect(sel, "Kapitel"); g3.querySelector("label").setAttribute("for","gqch-btn");''')
E('''#quiz .sel{background:var(--surface);box-shadow:var(--shadow)}''',
  '''#quiz .sel{background:var(--surface);box-shadow:var(--shadow)}
.fsel{position:relative;max-width:520px}
.fsel .fsnative{position:absolute;inset:0;opacity:0;pointer-events:none;width:100%;height:100%}
.fsbtn{width:100%;display:flex;align-items:center;gap:10px;border:1px solid var(--line);background:var(--surface);box-shadow:var(--shadow);color:var(--ink);border-radius:14px;padding:11px 14px 11px 16px;font:inherit;font-size:15px;font-weight:600;text-align:left;cursor:pointer;transition:border-color .12s}
.fsbtn:hover,.fsbtn[aria-expanded="true"]{border-color:var(--accent)}
.fsval{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.fschev{flex:none;width:9px;height:9px;border-right:2px solid currentColor;border-bottom:2px solid currentColor;transform:translateY(-3px) rotate(45deg);opacity:.6;transition:transform .15s}
.fsbtn[aria-expanded="true"] .fschev{transform:translateY(2px) rotate(-135deg)}
.fspop{position:absolute;left:0;right:0;top:calc(100% + 6px);z-index:40;max-height:min(420px,60vh);overflow:auto;overscroll-behavior:contain;background:var(--surface);color:var(--ink);border-radius:16px;box-shadow:0 0 0 1px var(--line), 0 14px 40px rgb(20 14 12 / .18);padding:6px;display:flex;flex-direction:column;gap:1px;animation:fsin .14s ease-out}
.fsopt{display:flex;align-items:center;gap:10px;width:100%;border:0;background:transparent;color:var(--ink);font:inherit;font-size:15px;font-weight:500;text-align:left;padding:10px 12px;border-radius:10px;cursor:pointer;line-height:1.3}
.fsopt:hover,.fsopt:focus-visible{background:var(--surface-2);outline:none;box-shadow:none}
.fsopt.sub{padding-left:30px;font-size:14px;color:var(--muted)}
.fsopt.sub::before{content:"";flex:none;width:6px;height:6px;border-radius:50%;background:var(--line);margin-left:-14px}
.fsopt.on{background:var(--accent-soft);color:var(--ink);font-weight:700}
.fsopt.on::after{content:"✓";margin-left:auto;font-weight:700;color:var(--accent)}
.fstx{flex:1 1 auto;min-width:0}
.fsback{position:fixed;inset:0;z-index:80;background:rgb(20 14 12 / .38);animation:fsfade .18s ease-out}
.fspop.sheet{position:fixed;left:0;right:0;top:auto;bottom:0;z-index:81;max-height:72vh;border-radius:22px 22px 0 0;padding:8px 10px max(14px,env(safe-area-inset-bottom));box-shadow:0 -10px 40px rgb(20 14 12 / .25);animation:fsup .2s ease-out}
.fspop.sheet .fshead{position:sticky;top:-8px;margin:-8px -10px 4px;padding:16px 20px 10px;background:var(--surface);font-size:12px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--line)}
.fspop.sheet .fsopt{padding:12px 14px;font-size:16px}
.fspop.sheet .fsopt.sub{padding-left:32px;font-size:15px}
@keyframes fsin{from{opacity:0;transform:translateY(-4px)}}
@keyframes fsfade{from{opacity:0}}
@keyframes fsup{from{transform:translateY(100%)}}
@media (prefers-reduced-motion:reduce){ .fspop,.fsback{animation:none} }''')

def apply(s, log=print):
    for a, b in EDITS:
        if b in s: continue
        n = s.count(a)
        if n != 1: log(f"WARNUNG app_patches: Stelle nicht eindeutig gefunden ({n}×): {a.strip()[:70]}"); continue
        s = s.replace(a, b)
    return s

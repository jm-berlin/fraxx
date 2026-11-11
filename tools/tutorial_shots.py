"""Screenshots für die Anleitung in einer Ausgangssprache aufnehmen (aus der gebauten Web-App).

    python3 tools/tutorial_shots.py <lang> <ausgabe-ordner> [basis-url]

Schreibt die PNGs und marks.json (Lage der Knöpfe für die pulsierenden Markierungen, in CSS-Pixeln).
Wählt alles über Struktur statt über Text, damit es in jeder Sprache funktioniert.
"""
import json, os, sys
from playwright.sync_api import sync_playwright

LANG, D = sys.argv[1], sys.argv[2]
BASE = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8765/"
os.makedirs(D, exist_ok=True)
P = lambda n: os.path.join(D, n)
LOCALE = {"de": "de-DE", "en": "en-GB", "fr": "fr-FR", "it": "it-IT", "es": "es-ES", "pt": "pt-PT", "nl": "nl-NL", "pl": "pl-PL", "sv": "sv-SE", "nb": "nb-NO", "tr": "tr-TR", "ar": "ar", "zh": "zh-CN"}
M = {}

def rect(pg, sel):
    return pg.evaluate("s=>{const e=document.querySelector(s); if(!e) return null; const b=e.getBoundingClientRect(); return [b.x,b.y,b.width,b.height]}", sel)

with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
    init = "try{localStorage.setItem('rw-design','taupe-beere'); localStorage.setItem('rw-mode','light'); localStorage.setItem('ml-nowelcome','1')}catch(e){}"

    def context(w, h, dsf, mobile=False):
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=dsf, is_mobile=mobile, has_touch=mobile, locale=LOCALE.get(LANG, "de-DE"))
        ctx.add_init_script(init)
        return ctx, ctx.new_page()

    ctx, pg = context(1280, 820, 2)

    def fresh(first=False):
        pg.goto(BASE); pg.wait_for_timeout(1500)
        if pg.locator("#mlsrc").count():
            if first:
                M["src"] = rect(pg, f'#mlsrc button[lang="{LANG}"]'); pg.screenshot(path=P("01-src.png"))
            pg.locator(f'#mlsrc button[lang="{LANG}"]').click()
        pg.wait_for_timeout(4000)
        # Oberfläche ist erst übersetzt, wenn die Seite die Sprache gesetzt hat
        try: pg.wait_for_function(f"document.documentElement.lang === '{LANG}'", timeout=120000)
        except Exception: print("Sprache", LANG, "nicht gesetzt – Screenshots evtl. teilweise auf Deutsch")
        pg.wait_for_timeout(2500 if LANG != "de" else 1500)
        if pg.locator("#mlupd").count(): pg.locator("#mlupd .n").click()
        if pg.locator("#mlwel").count(): pg.locator("#mlwel .n").click()
        if pg.locator(".mlremind, #mlremind").count():
            try: pg.locator(".mlremind button, #mlremind button").last.click()
            except Exception: pass

    fresh(True)
    pg.screenshot(path=P("02-home.png"))
    M["loslegen"] = rect(pg, ".hcta .primary"); M["setbtn"] = rect(pg, "#setbtn")
    # Inhalt, Reiter „Redewendungen nach Themen“
    pg.click("#tocbtn"); pg.wait_for_timeout(1200)
    pg.locator("#tocposf .tpt").nth(0).click(); pg.wait_for_timeout(800)
    pg.screenshot(path=P("03-inhalt.png"))
    card = pg.locator("#tocnav .toccard").filter(has=pg.locator(".hie", has_text="🍽")).first
    if not card.count(): card = pg.locator("#tocnav .toccard").nth(3)
    card.locator(".tocmain").click(); pg.wait_for_timeout(2500)
    pg.screenshot(path=P("04-tabelle.png"))
    M["speak"] = pg.evaluate("""()=>{const e=[...document.querySelectorAll('button.say:not(.copy)')].find(b=>{const r=b.getBoundingClientRect(); return b.offsetParent && r.y>60 && r.y<760;});
      if(!e) return null; const b=e.getBoundingClientRect(); return [b.x,b.y,b.width,b.height]}""")
    # Verben mit Konjugation
    fresh(); pg.click("#tocbtn"); pg.wait_for_timeout(1000)
    pg.locator("#tocposf .tpt").nth(2).click(); pg.wait_for_timeout(1500)
    v = pg.locator('#posf2 [data-pos="verb"]')
    if v.count(): v.click(); pg.wait_for_timeout(2500)
    kb = pg.locator("button.conjbtn:visible").first
    if kb.count(): kb.click(); pg.wait_for_timeout(1500)
    pg.screenshot(path=P("04b-konjugation.png"))
    # Einstellungen
    fresh(); pg.click("#setbtn"); pg.wait_for_timeout(700)
    pg.screenshot(path=P("05-settings.png"))
    M["srcsel"] = rect(pg, "#srcsel"); M["ver"] = rect(pg, ".mlver")
    # Grammatik, Verben & Endungen, Speisekarte, Spickzettel, Quiz
    for name, btn, tab in [("06-grammatik", "#grambtn", 0), ("06c-verben", "#grambtn", 1), ("07-speisekarte", "#dishbtn", None),
                           ("08-spick", "#favbtn", None), ("09-quiz", "#quizbtn", None)]:
        fresh(); pg.click(btn); pg.wait_for_timeout(2500)
        if tab is not None: pg.locator(".gramtab").nth(tab).click(); pg.wait_for_timeout(2000)
        pg.screenshot(path=P(name + ".png"))
    # Quiz: eine Frage mit richtig gewählter Antwort (bei falscher Wahl neue Runde, höchstens 8 Versuche)
    for _ in range(8):
        fresh(); pg.click("#quizbtn"); pg.wait_for_timeout(2000)
        st = pg.locator("#quizbody button.primary").first
        if not st.count() or st.is_disabled(): break
        st.click(); pg.wait_for_timeout(1200)
        if not pg.locator("#quizbody .qopt").count(): break
        pg.locator("#quizbody .qopt").nth(0).click(); pg.wait_for_timeout(900)
        if pg.locator("#quizbody .qopt.ok").count() and not pg.locator("#quizbody .qopt.bad").count():
            pg.screenshot(path=P("09b-quiz-frage.png")); break
    fresh(); pg.click("#setbtn"); pg.wait_for_timeout(600); pg.click(".mlsetbtn"); pg.wait_for_timeout(1500)
    pg.screenshot(path=P("12-appdaten.png"))
    ctx.close()
    # Handy
    ctx, pg = context(390, 844, 3, True)
    fresh(); pg.screenshot(path=P("11-mobile-home.png"))
    pg.click("#tocbtn"); pg.wait_for_timeout(1000); pg.locator("#tocposf .tpt").nth(0).click(); pg.wait_for_timeout(600)
    card = pg.locator("#tocnav .toccard").filter(has=pg.locator(".hie", has_text="🍽")).first
    if not card.count(): card = pg.locator("#tocnav .toccard").nth(3)
    card.locator(".tocmain").click(); pg.wait_for_timeout(2500)
    pg.screenshot(path=P("11b-mobile-karte.png"))
    ctx.close(); b.close()

json.dump(M, open(P("marks.json"), "w"))
print("Screenshots", LANG, "→", D, M)

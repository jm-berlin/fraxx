"""Baut die Anleitung für Erstnutzer als animierte HTML-Seite (eine Datei mit eingebetteten Bildern).
Deutsch → anleitung/index.html, andere Sprachen → anleitung/<lang>.html. Das PDF erzeugt tutorial_all.py.
Der deutsche Text steht unten in TEXT["de"] (Quelle); die Übersetzungen erstellt das Artefakt (Auftrag
„Anleitung übersetzen“), sie kommen mit dem Export und liegen dann in tools/tutorial-texts/<lang>.json.

    python3 tools/build_tutorial.py <screenshot-ordner> <ausgabe-ordner> [lang]
"""
import base64, io, json, os, sys
from PIL import Image

SHOTS, OUT = sys.argv[1], sys.argv[2]
LANG = sys.argv[3] if len(sys.argv) > 3 else "de"
APP = "https://jm-berlin.github.io/fraxx/"
VIEW_W, VIEW_H = 1280, 820  # CSS-Pixel der Screenshots am PC

# Ausschnitte (CSS-Pixel x, y, b, h) und Markierungen (CSS-Pixel x, y, b, h) je Screenshot
SHOT = {
    "src":     ("01-src.png",          (330, 175, 620, 470), [(556, 353, 167, 53)]),
    "home":    ("02-home.png",         None, [(94, 636, 142, 51)]),
    "nav":     ("02-home.png",         (560, 30, 700, 80), [(1193, 52, 37, 37)]),
    "inhalt":  ("03-inhalt.png",       None, []),
    "tabelle": ("04-tabelle.png",      (0, 34, 1280, 786), [(480, 135, 22, 22)]),
    "konj":    ("04b-konjugation.png", None, []),
    "set":     ("05-settings.png",     (0, 30, 1280, 560), [(204, 189, 220, 31), (62, 140, 190, 30)]),
    "gram":    ("06-grammatik.png",    None, []),
    "verben":  ("06c-verben.png",      None, []),
    "dish":    ("07-speisekarte.png",  None, []),
    "spick":   ("08-spick.png",        None, []),
    "quiz":    ("09-quiz.png",         None, []),
    "quiz2":   ("09b-quiz-frage.png",  None, []),
    "app":     ("12-appdaten.png",     (210, 0, 800, 820), []),
    "mhome":   ("11-mobile-home.png",  "m", []),
    "mkarte":  ("11b-mobile-karte.png", "m", []),
}

MARKS = {}
try: MARKS = json.load(open(os.path.join(SHOTS, "marks.json")))
except Exception: pass
# Markierungen aus der Aufnahme (marks.json) haben Vorrang vor den festen Werten
LIVE = {"src": ["src"], "home": ["loslegen"], "nav": ["setbtn"], "tabelle": ["speak"], "set": ["srcsel", "ver"]}

def img(key):
    f, crop, marks = SHOT[key]
    if key in LIVE and any(MARKS.get(k) for k in LIVE[key]):
        marks = []
        for k in LIVE[key]:
            r = MARKS.get(k)
            if not r: continue
            x0, y0, w0, h0 = r
            if k == "ver": w0 = min(w0, 190)
            if k == "speak": x0, y0, w0, h0 = x0 - 4, y0 - 4, w0 + 8, h0 + 8
            marks.append((x0, y0, w0, h0))
    im = Image.open(os.path.join(SHOTS, f)).convert("RGB")
    sc = im.width / (390 if crop == "m" else VIEW_W)
    if crop and crop != "m":
        x, y, w, h = crop
    else:
        x, y, w, h = 0, 0, im.width / sc, im.height / sc
    im = im.crop((int(x*sc), int(y*sc), int((x+w)*sc), int((y+h)*sc)))
    maxw = 760 if crop == "m" else 1600
    if im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=80, optimize=True, progressive=True)
    src = "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
    pings = "".join(
        f'<span class="ping" style="left:{(mx-x)/w*100:.2f}%;top:{(my-y)/h*100:.2f}%;width:{mw/w*100:.2f}%;height:{mh/h*100:.2f}%"></span>'
        for mx, my, mw, mh in marks)
    return src, pings, w / h

# Text des Knopfs am Ende („Jetzt loslegen“), passend zum Willkommensfenster der App (ui.js GUIDE_T)
START = {"de": "Jetzt loslegen", "en": "Get started now", "fr": "Commencer maintenant", "es": "Empezar ahora", "it": "Inizia ora", "pt": "Começar agora",
         "nl": "Nu beginnen", "pl": "Zacznij teraz", "tr": "Şimdi başla", "el": "Ξεκίνα τώρα", "hr": "Počni sada", "sv": "Börja nu", "da": "Kom i gang nu",
         "nb": "Kom i gang nå", "cs": "Začít teď", "hu": "Kezdjük most", "ro": "Începe acum", "ca": "Començar ara", "ru": "Начать сейчас", "ja": "今すぐ始める",
         "zh": "现在开始", "ar": "ابدأ الآن"}

TEXT = {"de": {
  "title": "Fraxx – Anleitung",
  "eyebrow": "Anleitung · in 5 Minuten startklar",
  "h1": "So funktioniert <em>Fraxx</em>.",
  "lead": "Fraxx ist deine persönliche Sprach-App für Reisen und Alltag: Wörter, Sätze und Redewendungen in vielen Sprachen, mit Aussprache, Konjugation, Grammatik, Speisekarten und Quiz. Hier siehst du in wenigen Schritten, wie du loslegst, und danach alles, was in Fraxx steckt.",
  "open": "Fraxx öffnen",
  "pdf": "Als PDF",
  "beta": "Testversion: Eigene neue Wörter übersetzen ist noch nicht freigeschaltet und kommt in einer späteren Version. Alles andere funktioniert schon, auch offline.",
  "s1": "Die ersten Schritte", "s1sub": "Fünf Schritte vom ersten Öffnen bis zur ersten Übersetzung.",
  "steps": [
    ("src", "Sprache wählen", "Beim ersten Start fragt Fraxx, welche Sprache du sprichst. Das ist deine <b>Ausgangssprache</b>: Darin sind Menü, Erklärungen und Hinweise geschrieben. Du kannst sie später unter ⚙ jederzeit ändern."),
    ("home", "Loslegen", "Die Startseite zeigt, was Fraxx kann. <b>Loslegen →</b> öffnet das Inhaltsverzeichnis. Ein Tipp auf das Logo bringt dich jederzeit hierher zurück."),
    ("inhalt", "Thema öffnen", "Im <b>Inhalt</b> stehen alle Themen als Kästen: Redewendungen nach Themen (Restaurant, Hotel, Apotheke …) und Wortschatz nach Themen. <b>Öffnen ▾</b> springt direkt hinein."),
    ("tabelle", "Lesen, hören, merken", "Jede Zeile zeigt einen Eintrag in all deinen Sprachen. Der Lautsprecher 🔊 liest vor, graue Hinweise erklären Besonderheiten. Der Stern ☆ setzt den Eintrag auf deinen Spickzettel."),
    ("set", "Einstellen", "Unter <b>⚙</b> wählst du Ausgangssprache, Sprachniveau (A1 bis C2), deine Sprachen und das Design (Hell oder Dunkel). Ganz oben steht deine Version."),
  ],
  "s2": "Nach der Installation", "s2sub": "Einmal einrichten, dann läuft Fraxx auch ohne Internet.",
  "after": [
    ("Sprachpakete laden", "Unter ⚙ → <b>App, Sprachpakete &amp; Sicherung</b> lädst du die Sprachen, die du brauchst. Jedes Paket enthält alle Übersetzungen, Konjugationen, Grammatik und Speisekarten dieser Sprache."),
    ("Offline nutzen", "Alles, was installiert ist, funktioniert ohne Internet: im Flugzeug, im Ausland ohne Datenvolumen, im Funkloch."),
    ("Gute Stimmen", "Vorgelesen wird mit den Stimmen deines Geräts. Am Mac und unter Windows klingt Chrome meist am natürlichsten. Weitere Stimmen installierst du in den Spracheinstellungen deines Geräts."),
    ("Daten sichern", "Deine Sterne, Lernstände und Einstellungen liegen auf dem Gerät. Unter ⚙ → App, Sprachpakete &amp; Sicherung lädst du eine Sicherung herunter und spielst sie bei Bedarf wieder ein."),
    ("Updates", "Gibt es eine neue Version, erscheint ein Punkt am ⚙. Dort siehst du, was neu ist, und entscheidest selbst, wann du aktualisierst."),
  ],
  "appcap": "App, Sprachpakete &amp; Sicherung: Sprachen laden oder entfernen, Sicherung herunterladen.",
  "s3": "Alles, was Fraxx kann", "s3sub": "Die Bereiche im Überblick – oben in der Leiste findest du sie alle.",
  "navcap": "Die Leiste oben: Inhalt, Grammatik, Speisekarte, Spickzettel, Quiz, Hilfe (?) und Einstellungen (⚙).",
  "features": [
    ("inhalt", "☰ Inhalt", "Über 6.000 Wörter, Sätze und Redewendungen in Themen geordnet: vom Restaurant über Apotheke und Werkstatt bis zum Amt. Dazu alphabetische Listen für Substantive, Verben, Adjektive und mehr. Das Suchfeld findet Themen nach Namen."),
    ("tabelle", "Übersetzungen und Aussprache", "Jeder Eintrag steht in allen deinen Sprachen nebeneinander, Substantive mit Artikel, Redewendungen sinngemäß übersetzt. 🔊 liest vor, ein zweiter Tipp stoppt. Mit dem Pin hältst du wichtige Einträge oben, mit A–Z sortierst du."),
    ("konj", "Verben und Konjugation", "Verben werden in allen Sprachen konjugiert: Präsens, Perfekt, Präteritum und Futur. <b>Konjugation ▸</b> klappt die Tabellen auf, die Zeit-Knöpfe wechseln die Zeitform."),
    ("gram", "§ Grammatik", "Die wichtigsten Regeln jeder Sprache von A1 bis C1, mit Beispielen zum Anhören. <b>Verben &amp; Endungen</b> zeigt Endungstabellen und unregelmäßige Verben, <b>Typische Fehler</b> die Stolpersteine für Sprecher deiner Sprache. <b>Im Quiz üben</b> fragt ein Kapitel mit Lückensätzen ab."),
    ("verben", "Verben &amp; Endungen", "Endungen auf einen Blick: regelmäßige Muster, Ausnahmen und die wichtigsten unregelmäßigen Verben, jeweils mit Beispiel."),
    ("dish", "🍽 Speisekarte", "Rund 250 beliebte Gerichte und Getränke je Land mit Originalnamen und Erklärung, dazu Kaffee, Bier und Wein. Warnhinweise zeigen, wenn ein Name anderswo etwas anderes bedeutet. <b>Bestellen ▸</b> zeigt, wie du es bestellst."),
    ("spick", "★ Spickzettel", "Alles, was du mit dem Stern markiert hast, kompakt in einer Sprache: Wörter, Redewendungen und Gerichte. <b>Drucken</b> macht daraus einen Zettel für die Reise."),
    ("quiz", "Quiz", "Lernen mit vier Antworten pro Frage: Wörter &amp; Sätze oder Grammatik, in beide Richtungen, nach Niveau und Thema. Bei <b>🔊 Hören</b> wird nur vorgelesen. Nach drei richtigen Antworten gilt ein Eintrag als gelernt, der Lernstand zeigt deinen Fortschritt."),
  ],
  "mob": "Auf dem Handy", "mobsub": "Gleiche Inhalte, für den Daumen gemacht: Die Zeilen werden zu Karten, die Leiste sitzt oben.",
  "tips": "Kleine Tipps", "tiplist": [
    "Sprachniveau unter ⚙ blendet alles über deinem Niveau aus, in Tabelle, Grammatik und Quiz.",
    "Bis zu 5 Sprachen passen nebeneinander in die Tabelle: deine Ausgangssprache und vier weitere.",
    "Bei Sprachen mit anderer Schrift (Arabisch, Russisch, Japanisch …) steht die Umschrift kursiv darunter.",
    "Das <b>?</b> oben rechts erklärt jede Funktion ausführlich.",
    "Die Gesundheitsangaben sind ohne Gewähr und ersetzen keine Beratung. Sie helfen dir, dich mit Arzt oder Apotheke zu verständigen.",
  ],
  "end": "Gute Reise!", "endsub": "Viel Spaß mit Fraxx. Hast du eine Idee oder einen Fehler gefunden? Wir freuen uns über jede Rückmeldung.",
  "pause": "Anhalten", "play": "Abspielen", "prev": "Zurück", "next": "Weiter", "step": "Schritt",
}}

TXT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tutorial-texts")
def load_texts():
    os.makedirs(TXT_DIR, exist_ok=True)
    json.dump(TEXT["de"], open(os.path.join(TXT_DIR, "de.json"), "w"), ensure_ascii=False, indent=1)
    for f in sorted(os.listdir(TXT_DIR)):
        l = f[:-5]
        if f.endswith(".json") and l != "de":
            try:
                t = json.load(open(os.path.join(TXT_DIR, f)))
                t = json.loads(json.dumps(t, ensure_ascii=False).replace("Multilingo", "Fraxx").replace("Phraxx", "Fraxx").replace("Viavox", "Fraxx"))  # neuer App-Name, ältere Übersetzungen
                TEXT[l] = {**TEXT["de"], **t}
            except Exception as e: print("Text", f, "nicht lesbar:", e)
NAMES = {"de": "Deutsch", "en": "English", "fr": "Français", "it": "Italiano", "es": "Español", "pt": "Português",
         "nl": "Nederlands", "pl": "Polski", "sv": "Svenska", "nb": "Norsk", "tr": "Türkçe", "ar": "العربية", "zh": "中文"}
page = lambda l: "index.html" if l == "de" else f"{l}.html"
pdfname = lambda l: "Fraxx-Anleitung.pdf" if l == "de" else f"Fraxx-Anleitung-{l}.pdf"

def build():
    load_texts()
    if LANG not in TEXT: sys.exit(f"Kein Text für {LANG}")
    T = TEXT[LANG]
    avail = [l for l in NAMES if l in TEXT]
    switch = "".join(f'<a href="{page(l)}"{" aria-current=\"page\"" if l == LANG else ""} hreflang="{l}">{NAMES[l]}</a>' for l in avail) if len(avail) > 1 else ""
    def fig(key, cap="", cls=""):
        src, pings, ar = img(key)
        c = f"<figcaption>{cap}</figcaption>" if cap else ""
        return f'<figure class="shot {cls}"><div class="frame" style="aspect-ratio:{ar:.4f}"><img src="{src}" alt="">{pings}</div>{c}</figure>'
    # Quiz: Auswahl und eine beantwortete Frage untereinander
    def fig2(key):
        if key == "quiz" and os.path.exists(os.path.join(SHOTS, SHOT["quiz2"][0])):
            return f'<div class="figs">{fig(key)}{fig("quiz2")}</div>'
        return fig(key)
    slides = "".join(
        f'<div class="slide" data-i="{i}"><div class="stxt"><span class="sn">{T["step"]} {i+1}</span><h3>{h}</h3><p>{p}</p></div>{fig(k)}</div>'
        for i, (k, h, p) in enumerate(T["steps"]))
    dots = "".join(f'<button type="button" class="dot" data-i="{i}" aria-label="{T["step"]} {i+1}"></button>' for i in range(len(T["steps"])))
    after = "".join(f'<li class="rv"><b>{h}</b><span>{p}</span></li>' for h, p in T["after"])
    feats = "".join(
        f'<section class="feat card rv{" rev" if i % 2 else ""}"><div class="ftxt"><h3>{h}</h3><p>{p}</p></div>{fig2(k)}</section>'
        for i, (k, h, p) in enumerate(T["features"]))
    tips = "".join(f"<li>{t}</li>" for t in T["tiplist"])
    html = f'''<!doctype html>
<html lang="{LANG}"{' dir="rtl"' if LANG == "ar" else ""}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{T["title"]}</title>
<link rel="icon" href="../icons/favicon-32.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root{{--bg:#e5e2e0;--surface:#f3f1ef;--surface-2:#e9e5e2;--ink:#141212;--muted:#6b635d;--line:#d3ccc6;--hl:#a3395f;--hl-soft:#efd5df;--r:28px}}
*{{box-sizing:border-box}}
html{{background:var(--bg);-webkit-print-color-adjust:exact;print-color-adjust:exact;scroll-behavior:smooth}}
body{{margin:0;font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);font-size:17px;line-height:1.6;background:var(--bg)}}
.wrap{{max-width:1180px;margin:0 auto;padding:24px 16px 64px}}
header.top{{display:flex;align-items:center;justify-content:space-between;gap:16px;margin:0 4px 20px}}
.logo{{font-weight:900;font-size:clamp(30px,5vw,44px);letter-spacing:-.06em;line-height:1;position:relative;text-decoration:none;color:var(--ink)}}
.logo sup{{position:absolute;left:100%;top:-2px;margin-left:4px;font-size:11px;letter-spacing:.08em;background:var(--hl);color:#fff;border-radius:99px;padding:3px 8px;font-weight:700}}
.embed .top>.pill{{visibility:hidden}}
.logo .vxlogo{{height:.78em;width:auto;vertical-align:-.04em;color:var(--ink);--vxberry:#a3395f}}
.figs{{display:flex;flex-direction:column;gap:14px;min-width:0}}
.langs{{display:flex;flex-wrap:wrap;gap:4px;justify-content:center;flex:1}} .langs a{{font-size:13px;font-weight:600;color:var(--muted);text-decoration:none;padding:5px 10px;border-radius:99px}} .langs a[aria-current]{{background:var(--ink);color:#fff}} .langs a:hover{{color:var(--ink)}}
@media (max-width:860px){{ header.top{{flex-wrap:wrap}} .langs{{order:3;flex-basis:100%;justify-content:flex-start}} }}
.pill{{display:inline-flex;align-items:center;gap:8px;border-radius:999px;padding:12px 22px;font-weight:700;font-size:15px;text-decoration:none;border:0;cursor:pointer;font-family:inherit}}
.pill.pri{{background:var(--ink);color:#fff}} .pill.sec{{background:var(--surface);color:var(--ink);box-shadow:inset 0 0 0 1px var(--line)}}
.pill:hover{{filter:brightness(1.1)}}
.card{{background:var(--surface);border-radius:var(--r);padding:clamp(22px,4vw,44px);margin:0 0 16px;box-shadow:0 1px 2px rgb(40 30 25 / .05)}}
.hero{{display:grid;grid-template-columns:1.1fr .9fr;gap:36px;align-items:center;overflow:hidden}}
.eyebrow{{font-size:12px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;margin:0 0 14px}}
h1{{font-size:clamp(38px,6.4vw,68px);line-height:1.02;letter-spacing:-.045em;font-weight:800;margin:0 0 18px}}
h1 em,h2 em{{font-style:normal;color:var(--hl)}}
.lead{{color:var(--muted);font-size:18px;margin:0 0 24px;max-width:56ch}}
.ctas{{display:flex;gap:12px;flex-wrap:wrap}}
.beta{{margin:22px 0 0;padding:14px 18px;border-radius:16px;background:var(--surface-2);border:2px solid var(--hl);font-weight:600;font-size:14.5px;max-width:60ch}}
.hero .phones{{position:relative;height:440px}}
.hero .phones .shot{{position:absolute;width:52%;margin:0}}
.hero .phones .shot:first-child{{left:2%;top:0;transform:rotate(-4deg)}}
.hero .phones .shot:last-child{{right:2%;top:40px;transform:rotate(4deg)}}
.hero .phones .frame{{border-radius:26px;box-shadow:0 20px 50px rgb(40 30 25 / .22),0 0 0 6px var(--ink)}}
h2{{font-size:clamp(28px,4vw,42px);letter-spacing:-.035em;line-height:1.08;margin:0 0 8px}}
.sub{{color:var(--muted);margin:0 0 26px;font-size:17px}}
h3{{font-size:21px;letter-spacing:-.02em;margin:0 0 8px;line-height:1.25}}
p{{margin:0 0 10px}}
.shot{{margin:0}}
.frame{{position:relative;border-radius:16px;overflow:hidden;background:var(--bg);box-shadow:0 10px 30px rgb(40 30 25 / .14),0 0 0 1px rgb(40 30 25 / .06)}}
.frame img{{display:block;width:100%;height:100%;object-fit:cover}}
figcaption{{color:var(--muted);font-size:14px;margin-top:10px}}
.ping{{position:absolute;border-radius:999px;box-shadow:0 0 0 3px var(--hl);pointer-events:none}}
.ping::after{{content:"";position:absolute;inset:-3px;border-radius:inherit;box-shadow:0 0 0 3px var(--hl);animation:ping 1.8s ease-out infinite}}
@keyframes ping{{0%{{opacity:.9;transform:scale(1)}}100%{{opacity:0;transform:scale(1.6)}}}}
/* Diashow */
.show{{position:relative}}
.slides{{display:grid}}
.slide{{grid-area:1/1;display:grid;grid-template-columns:.8fr 1.2fr;gap:36px;align-items:center;opacity:0;visibility:hidden;transform:translateX(24px);transition:opacity .6s ease,transform .6s ease,visibility 0s .6s}}
.slide.on{{opacity:1;visibility:visible;transform:none;transition:opacity .6s ease,transform .6s ease}}
.sn{{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--hl);margin-bottom:10px}}
.stxt p{{color:var(--muted)}} .stxt b{{color:var(--ink)}}
.ctrl{{display:flex;align-items:center;gap:10px;margin-top:26px;flex-wrap:wrap}}
.dot{{width:34px;height:6px;border-radius:9px;border:0;background:var(--line);cursor:pointer;padding:0;position:relative;overflow:hidden}}
.dot.on{{background:var(--hl-soft)}}
.dot.on::after{{content:"";position:absolute;inset:0;background:var(--hl);transform-origin:left;animation:fill var(--dur,7s) linear forwards}}
.paused .dot.on::after{{animation-play-state:paused}}
@keyframes fill{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
.cbtn{{border:0;background:var(--surface-2);border-radius:999px;padding:8px 14px;font:inherit;font-size:14px;font-weight:600;cursor:pointer;color:var(--ink)}}
.ctrl .sp{{flex:1}}
/* Liste */
.after{{display:grid;grid-template-columns:1fr 1fr;gap:26px;align-items:start}}
.after ol{{list-style:none;counter-reset:a;padding:0;margin:0}}
.after li{{counter-increment:a;position:relative;padding:0 0 18px 50px}}
.after li::before{{content:counter(a);position:absolute;left:0;top:0;width:34px;height:34px;border-radius:50%;background:var(--hl);color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;font-size:15px}}
.after li>b{{display:block;font-size:17px;margin:4px 0 2px}} .after li span b{{color:var(--ink)}} .after li span{{color:var(--muted);font-size:15.5px}}
/* Funktionen */
.feat{{display:grid;grid-template-columns:.75fr 1.25fr;gap:36px;align-items:center}}
.feat.rev{{grid-template-columns:1.25fr .75fr}} .feat.rev .ftxt{{order:2}}
.ftxt p{{color:var(--muted)}} .ftxt b{{color:var(--ink)}}
.navshot{{margin:0 0 16px}}
.mob{{display:grid;grid-template-columns:1fr 1fr 1.1fr;gap:26px;align-items:center}}
.mob .frame{{border-radius:24px;box-shadow:0 16px 40px rgb(40 30 25 / .18),0 0 0 5px var(--ink)}}
.tips ul{{margin:0;padding-left:20px}} .tips li{{margin:0 0 8px;color:var(--muted)}} .tips li::marker{{color:var(--hl)}} .tips li b{{color:var(--ink)}}
.end{{text-align:center;background:var(--ink);color:#f3f1ef}}
.end h2{{color:#fff}} .end p{{color:#cfc7c2;max-width:52ch;margin:0 auto 22px}}
.end .pill.pri{{background:var(--hl)}}
footer{{text-align:center;color:var(--muted);font-size:13px;margin-top:22px}}
/* Einblenden beim Scrollen */
.js .rv{{opacity:0;transform:translateY(26px);transition:opacity .7s ease,transform .7s ease}}
.js .rv.in{{opacity:1;transform:none}}
@media (max-width:860px){{
  .hero,.slide,.feat,.after,.mob{{grid-template-columns:1fr}}
  .feat.rev{{grid-template-columns:1fr}} .feat.rev .ftxt{{order:0}}
  .hero .phones{{height:380px;max-width:420px;margin:0 auto;width:100%}}
  body{{font-size:16px}}
}}
@media (prefers-reduced-motion:reduce){{
  .ping::after,.dot.on::after{{animation:none}} .slide,.js .rv{{transition:none}} .js .rv{{opacity:1;transform:none}}
}}
@media print{{
  @page{{size:A4;margin:10mm}}
  html,body{{background:var(--bg)}} body{{font-size:11pt}} .wrap{{max-width:none;padding:0}}
  .card{{break-inside:avoid;padding:8mm;margin-bottom:5mm;border-radius:6mm}}
  .js .rv{{opacity:1;transform:none}}
  .ctrl,.ctas,.noprint{{display:none!important}}
  .hero{{grid-template-columns:1.2fr .8fr}} .hero .phones{{height:92mm}}
  .slides{{display:block}} .slide{{opacity:1;visibility:visible;transform:none;margin:0 0 8mm;break-inside:avoid;grid-template-columns:.8fr 1.2fr}}
  .ping::after{{display:none}}
  h2{{break-after:avoid}} .sub{{margin-bottom:5mm}}
  .show-card{{break-inside:auto;break-before:page}} .aftercard{{break-before:page;break-inside:avoid}} .end{{break-inside:avoid}}
  .hero,.slide,.feat,.feat.rev,.after{{grid-template-columns:.85fr 1.15fr;gap:7mm}}
  .after{{grid-template-columns:1.25fr .75fr}} .after li{{padding-bottom:3mm;padding-left:11mm}} .after li::before{{width:7mm;height:7mm;font-size:9pt}} .after li>b{{font-size:11pt;margin:0}}
  .feat{{break-inside:avoid;padding:6mm 8mm}} .feat.rev .ftxt{{order:0}}
  .feat h3,.slide h3{{font-size:13pt}} .ftxt p,.stxt p,.after li span{{font-size:10pt}}
  .mob{{grid-template-columns:1.2fr .9fr .9fr;gap:7mm}} .mob .frame{{max-height:120mm}}
  .mob .shot .frame{{aspect-ratio:auto!important;height:120mm}} .mob .frame img{{object-position:top}}
  .lead{{font-size:12pt}} h1{{font-size:34pt}} h2{{font-size:22pt}}
}}
</style>
</head>
<body>
<div class="wrap">
<header class="top"><a class="logo" href="{APP}" aria-label="Fraxx"><svg class="vxlogo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 450.0 100" role="img" aria-label="Fraxx"><path d="M57.10 10.90 L10.90 10.90 M10.90 50.00 L47.00 50.00" stroke="var(--vxberry, #a3395f)" stroke-width="21.80" stroke-linecap="round" stroke-linejoin="round" fill="none"/><path d="M10.90 89.10 L10.90 10.90" stroke="currentColor" stroke-width="21.80" stroke-linecap="round" stroke-linejoin="round" fill="none"/><path d="M98.90 10.90 L125.00 10.90 A20.10 20.10 0 0 1 125.00 51.10 L98.90 51.10" stroke="currentColor" stroke-width="21.80" stroke-linecap="round" stroke-linejoin="round" fill="none"/><path d="M98.90 89.10 L98.90 10.90" stroke="currentColor" stroke-width="21.80" stroke-linecap="round" stroke-linejoin="round" fill="none"/><path d="M121.99 51.10 L147.10 89.10" stroke="currentColor" stroke-width="21.80" stroke-linecap="round" stroke-linejoin="round" fill="none"/><path d="M188.90 89.10 L221.00 10.90 L253.10 89.10" stroke="currentColor" stroke-width="21.80" stroke-linecap="round" stroke-linejoin="round" fill="none"/><path d="M294.90 10.90 L353.10 89.10" stroke="currentColor" stroke-width="21.80" stroke-linecap="round" stroke-linejoin="round" fill="none"/><path d="M353.10 10.90 L294.90 89.10" stroke="currentColor" stroke-width="21.80" stroke-linecap="round" stroke-linejoin="round" fill="none"/><path d="M380.90 10.90 L439.10 89.10" stroke="currentColor" stroke-width="21.80" stroke-linecap="round" stroke-linejoin="round" fill="none"/><path d="M439.10 10.90 L380.90 89.10" stroke="currentColor" stroke-width="21.80" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg><sup>BETA</sup></a><nav class="langs noprint">{switch}</nav><a class="pill pri noprint" href="{APP}">{T["open"]} →</a></header>

<section class="card hero">
  <div>
    <p class="eyebrow">{T["eyebrow"]}</p>
    <h1>{T["h1"]}</h1>
    <p class="lead">{T["lead"]}</p>
    <div class="ctas"><a class="pill pri" href="{APP}">{T["open"]} →</a><a class="pill sec" href="{pdfname(LANG)}" download>⤓ {T["pdf"]}</a></div>
    <p class="beta">{T["beta"]}</p>
  </div>
  <div class="phones" aria-hidden="true">{fig("mhome")}{fig("mkarte")}</div>
</section>

<section class="card show-card rv">
  <h2>{T["s1"]}</h2><p class="sub">{T["s1sub"]}</p>
  <div class="show" id="show"><div class="slides">{slides}</div>
  <div class="ctrl"><button type="button" class="cbtn" id="prev">← {T["prev"]}</button>{dots}<button type="button" class="cbtn" id="next">{T["next"]} →</button><span class="sp"></span><button type="button" class="cbtn" id="pp">❚❚ {T["pause"]}</button></div></div>
</section>

<section class="card rv aftercard">
  <h2>{T["s2"]}</h2><p class="sub">{T["s2sub"]}</p>
  <div class="after"><ol>{after}</ol>{fig("app", T["appcap"])}</div>
</section>

<section class="card rv">
  <h2>{T["s3"]}</h2><p class="sub">{T["s3sub"]}</p>
  <div class="navshot">{fig("nav", T["navcap"])}</div>
</section>
{feats}

<section class="card rv">
  <div class="mob"><div><h2>{T["mob"]}</h2><p class="sub" style="margin:0">{T["mobsub"]}</p></div>{fig("mhome")}{fig("mkarte")}</div>
</section>

<section class="card tips rv"><h2>{T["tips"]}</h2><ul>{tips}</ul></section>

<section class="card end rv"><h2>{T["end"]}</h2><p>{T["endsub"]}</p><a class="pill pri noprint" href="{APP}">{START.get(LANG, START["en"])} →</a></section>
<footer>Fraxx · {APP.replace("https://","")}</footer>
</div>
<script>
(function(){{ var A = {json.dumps(avail)}, l = (new URLSearchParams(location.search).get("lang") || "").slice(0,2);
  if({json.dumps(LANG == "de")} && l && l !== "de" && A.indexOf(l) >= 0) location.replace(l + ".html" + location.search); }})();
// In der App geöffnet (?embed=1): Knöpfe zur App schließen die Anleitung, statt die App neu zu laden
(function(){{ var emb = /[?&]embed=1/.test(location.search) && window.parent !== window; if(!emb) return;
  document.documentElement.classList.add("embed");
  document.querySelectorAll('a[href="{APP}"]').forEach(function(a){{ a.addEventListener("click", function(ev){{ ev.preventDefault(); parent.postMessage("ml-guide-close", location.origin); }}); }});
  document.querySelectorAll(".langs a").forEach(function(a){{ a.href = a.getAttribute("href") + "?embed=1"; }}); }})();
document.documentElement.classList.add("js");
(function(){{
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  // Einblenden beim Scrollen
  var els = document.querySelectorAll(".rv");
  if("IntersectionObserver" in window && !reduce){{
    var io = new IntersectionObserver(function(es){{ es.forEach(function(e){{ if(e.isIntersecting){{ e.target.classList.add("in"); io.unobserve(e.target); }} }}); }}, {{threshold:.12}});
    els.forEach(function(e){{ io.observe(e); }});
  }} else els.forEach(function(e){{ e.classList.add("in"); }});
  // Diashow
  var show = document.getElementById("show"), sl = show.querySelectorAll(".slide"), dots = show.querySelectorAll(".dot");
  var i = 0, DUR = 7000, t = null, playing = !reduce, pp = document.getElementById("pp");
  function go(n){{ i = (n + sl.length) % sl.length; sl.forEach(function(s,k){{ s.classList.toggle("on", k===i); }});
    dots.forEach(function(d,k){{ d.classList.remove("on"); if(k===i){{ void d.offsetWidth; d.classList.add("on"); }} }}); arm(); }}
  function arm(){{ clearTimeout(t); if(playing) t = setTimeout(function(){{ go(i+1); }}, DUR); }}
  function setPlay(v){{ playing = v; show.classList.toggle("paused", !v); pp.textContent = v ? "❚❚ {T["pause"]}" : "▶ {T["play"]}"; if(v) go(i); else clearTimeout(t); }}
  document.getElementById("prev").onclick = function(){{ go(i-1); }};
  document.getElementById("next").onclick = function(){{ go(i+1); }};
  dots.forEach(function(d){{ d.onclick = function(){{ go(+d.dataset.i); }}; }});
  pp.onclick = function(){{ setPlay(!playing); }};
  show.style.setProperty("--dur", DUR/1000 + "s");
  // nur abspielen, solange die Diashow sichtbar ist
  if("IntersectionObserver" in window) new IntersectionObserver(function(es){{ var v = es[0].isIntersecting; if(!v) clearTimeout(t); else if(playing) arm(); }}, {{threshold:.3}}).observe(show);
  setPlay(playing); go(0);
}})();
</script>
</body>
</html>
'''
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, page(LANG))
    open(p, "w").write(html)
    print(p, round(len(html)/1e6, 2), "MB")
    return p

if __name__ == "__main__":
    build()

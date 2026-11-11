"""Baut die Web-App (index.html + sw.js) aus der Artefakt-Datei redewendungen.html."""
import sys, re, hashlib, os
src, out = sys.argv[1], sys.argv[2]
s = open(src).read()
# Vorgemerkte App-Änderungen, die im Artefakt noch fehlen (siehe tools/app_patches.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app_patches, rename_fraxx
s = app_patches.apply(s)
def rep(a, b, count=1):
    global s
    # Das Artefakt heißt inzwischen evtl. schon „Fraxx“: dann die Suchtexte ebenso umstellen
    if a not in s: a, b = rename_fraxx.convert(a), rename_fraxx.convert(b)
    assert a in s, a[:80]; s = s.replace(a, b, count)
rep('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
head = '''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Fraxx – deine persönliche Sprach-App für Reisen.">
<meta name="theme-color" content="#e5e2e0">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/svg+xml" href="icons/fraxx.svg">
<link rel="icon" type="image/png" sizes="32x32" href="icons/favicon-32.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png?v=2">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Fraxx">
<script src="runtime.js"></script>
'''
s = head + s
# Hinweise an die App anpassen
# Öffentliche Testversion: keine eigene Übersetzung, kein Schlüssel. Admin: Hinweis auf den Schlüssel
rep('if(!sample){ showNotice(IN_WEBAPP ? "Eigene Übersetzungen sind in dieser Testversion noch nicht freigeschaltet. Sie kommen in einer späteren Version." : "Übersetzen ist in dieser Ansicht nicht verfügbar. Öffne die Seite in Claude, angemeldet mit deinem Konto."); return; }',
    'if(!sample){ showNotice(window.ML_ADMIN ? "Für neue Übersetzungen braucht Phraxx einen Claude-API-Schlüssel. Du kannst ihn unter ⚙ → App, Sprachpakete & Sicherung eintragen." : "Eigene Übersetzungen sind in dieser Testversion noch nicht freigeschaltet. Sie kommen in einer späteren Version."); return; }')
rep('if(!sample && !IN_WEBAPP) showNotice("Übersetzen ist in dieser Ansicht nicht verfügbar. Öffne die Seite in Claude, angemeldet mit deinem Konto.");',
    'if(!sample && window.ML_ADMIN){ try{ if(!localStorage.getItem("ml-offnote")){ localStorage.setItem("ml-offnote","1"); showNotice("Phraxx läuft offline mit deinen Sprachpaketen. Neue Wörter übersetzt es, sobald du unter ⚙ → App, Sprachpakete & Sicherung einen Claude-API-Schlüssel einträgst."); } }catch(e){} }')
rep('statusEl.textContent = "Gespeichert in deinem Konto";', 'statusEl.textContent = "Gespeichert auf diesem Gerät";')
s = re.sub(r'(data-img="(\w+)" src=")data:image/jpeg;base64,[^"]+', lambda m: m.group(1) + 'img/' + m.group(2) + '.jpg', s)
s = s.rstrip() + '\n<script src="ui.js"></script>\n</html>\n'
# Neuer Name Fraxx (Wortmarke, Icon, Texte, Adresse), solange das Artefakt noch „Phraxx“ heißt
s = rename_fraxx.convert(s)
# Eigene Domain: alte GitHub-Pages-Adresse durch https://fraxx.app/ ersetzen (auch wenn das Artefakt sie noch enthält)
s = s.replace("https://jm-berlin.github.io/fraxx/", "https://fraxx.app/")
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "index.html"), "w").write(s)
ver = hashlib.sha1((s + open(os.path.join(out, "runtime.js")).read() + open(os.path.join(out, "ui.js")).read()).encode()).hexdigest()[:10]
# Stand der App (Fingerabdruck) sichtbar machen: unter ⚙ neben der Version
s = s.replace("<head>", '<head>\n<meta name="fraxx-build" content="' + ver + '">', 1) if "<head>" in s else s.replace("<title>", '<meta name="fraxx-build" content="' + ver + '">\n<title>', 1)
open(os.path.join(out, "index.html"), "w").write(s)
sw = open(os.path.join(os.path.dirname(__file__), "sw.template.js")).read().replace("__VERSION__", ver)
open(os.path.join(out, "sw.js"), "w").write(sw)
print("index.html", len(s), "Version", ver)

# ---------- Admin-Fassung in …/admin/ ----------
# Seit 11.11.2026 nicht mehr öffentlich (Admin arbeitet im Claude-Artefakt). Nur bauen mit ML_BUILD_ADMIN=1.
if not os.environ.get("ML_BUILD_ADMIN"):
    raise SystemExit(0)
# Gleiche App, aber mit Auftragsliste, allen Sprachpaketen und eigenem Speicher. Daten kommen aus ../data/.
adm = os.path.join(out, "admin"); os.makedirs(adm, exist_ok=True)
a = s
a = a.replace('<script src="runtime.js"></script>', '<script>window.ML_ADMIN = true; window.ML_DATA = "../data/";</script>\n<script src="runtime.js"></script>', 1)
a = a.replace('<meta name="apple-mobile-web-app-title" content="Fraxx">', '<meta name="apple-mobile-web-app-title" content="FX Admin">', 1)
a = a.replace('<title>Fraxx</title>', '<title>Fraxx Admin</title>', 1)
a = a.replace('<meta name="robots"', '<meta name="robots"', 1)
a = a.replace('<head>\n', '<head>\n<meta name="robots" content="noindex, nofollow">\n', 1)
a = re.sub(r'(href|src)="(icons|img)/', lambda m: m.group(1) + '="../' + m.group(2) + '/', a)
open(os.path.join(adm, "index.html"), "w").write(a)
import shutil, json as _json
for f in ("runtime.js", "ui.js"): shutil.copy(os.path.join(out, f), os.path.join(adm, f))
man = _json.load(open(os.path.join(out, "manifest.webmanifest")))
man.update({"name": "Fraxx Admin", "short_name": "FX Admin", "id": "./admin/"})
man["icons"] = [{**i, "src": "../" + i["src"]} for i in man["icons"]]
_json.dump(man, open(os.path.join(adm, "manifest.webmanifest"), "w"), ensure_ascii=False, indent=2)
aver = hashlib.sha1((a + open(os.path.join(adm, "runtime.js")).read() + open(os.path.join(adm, "ui.js")).read()).encode()).hexdigest()[:10]
asw = (open(os.path.join(os.path.dirname(__file__), "sw.template.js")).read().replace("__VERSION__", aver)
       .replace('"ml-shell-"', '"mla-shell-"').replace('"ml-runtime"', '"mla-runtime"')
       .replace('"icons/', '"../icons/').replace('"img/', '"../img/').replace('"data/packs.json"', '"../data/packs.json"'))
assert "mla-shell-" in asw
open(os.path.join(adm, "sw.js"), "w").write(asw)
print("admin/index.html", len(a), "Version", aver)

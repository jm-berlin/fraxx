"""Baut die Web-App (index.html + sw.js) aus der Artefakt-Datei redewendungen.html."""
import sys, re, hashlib, os
src, out = sys.argv[1], sys.argv[2]
s = open(src).read()
def rep(a, b, count=1):
    global s
    assert a in s, a[:80]; s = s.replace(a, b, count)
rep('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
head = '''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Multilingo – deine persönliche Sprach-App für Reisen.">
<meta name="theme-color" content="#2f52d6">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" sizes="32x32" href="icons/favicon-32.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Multilingo">
<script src="runtime.js"></script>
'''
s = head + s
# Hinweise an die App anpassen
rep('if(!sample){ showNotice("Übersetzen ist in dieser Ansicht nicht verfügbar. Öffne die Seite in Claude, angemeldet mit deinem Konto."); return; }',
    'if(!sample){ showNotice("Für neue Übersetzungen braucht Multilingo einen Claude-API-Schlüssel. Du kannst ihn unter ⚙ → App, Sprachpakete & Sicherung eintragen."); return; }')
rep('if(!sample) showNotice("Übersetzen ist in dieser Ansicht nicht verfügbar. Öffne die Seite in Claude, angemeldet mit deinem Konto.");',
    'if(!sample){ try{ if(!localStorage.getItem("ml-offnote")){ localStorage.setItem("ml-offnote","1"); showNotice("Multilingo läuft offline mit deinen Sprachpaketen. Neue Wörter übersetzt es, sobald du unter ⚙ → App, Sprachpakete & Sicherung einen Claude-API-Schlüssel einträgst."); } }catch(e){} }')
rep('statusEl.textContent = "Gespeichert in deinem Konto";', 'statusEl.textContent = "Gespeichert auf diesem Gerät";')
s = re.sub(r'(data-img="(\w+)" src=")data:image/jpeg;base64,[^"]+', lambda m: m.group(1) + 'img/' + m.group(2) + '.jpg', s)
s = s.rstrip() + '\n<script src="ui.js"></script>\n</html>\n'
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "index.html"), "w").write(s)
ver = hashlib.sha1((s + open(os.path.join(out, "runtime.js")).read() + open(os.path.join(out, "ui.js")).read()).encode()).hexdigest()[:10]
sw = open(os.path.join(os.path.dirname(__file__), "sw.template.js")).read().replace("__VERSION__", ver)
open(os.path.join(out, "sw.js"), "w").write(sw)
print("index.html", len(s), "Version", ver)

# ---------- Admin-Fassung in …/admin/ ----------
# Gleiche App, aber mit Auftragsliste, allen Sprachpaketen und eigenem Speicher. Daten kommen aus ../data/.
adm = os.path.join(out, "admin"); os.makedirs(adm, exist_ok=True)
a = s
a = a.replace('<script src="runtime.js"></script>', '<script>window.ML_ADMIN = true; window.ML_DATA = "../data/";</script>\n<script src="runtime.js"></script>', 1)
a = a.replace('<meta name="apple-mobile-web-app-title" content="Multilingo">', '<meta name="apple-mobile-web-app-title" content="ML Admin">', 1)
a = a.replace('<title>Multilingo</title>', '<title>Multilingo Admin</title>', 1)
a = a.replace('<meta name="robots"', '<meta name="robots"', 1)
a = a.replace('<head>\n', '<head>\n<meta name="robots" content="noindex, nofollow">\n', 1)
a = re.sub(r'(href|src)="(icons|img)/', lambda m: m.group(1) + '="../' + m.group(2) + '/', a)
open(os.path.join(adm, "index.html"), "w").write(a)
import shutil, json as _json
for f in ("runtime.js", "ui.js"): shutil.copy(os.path.join(out, f), os.path.join(adm, f))
man = _json.load(open(os.path.join(out, "manifest.webmanifest")))
man.update({"name": "Multilingo Admin", "short_name": "ML Admin", "id": "./admin/"})
man["icons"] = [{**i, "src": "../" + i["src"]} for i in man["icons"]]
_json.dump(man, open(os.path.join(adm, "manifest.webmanifest"), "w"), ensure_ascii=False, indent=2)
aver = hashlib.sha1((a + open(os.path.join(adm, "runtime.js")).read()).encode()).hexdigest()[:10]
asw = (open(os.path.join(os.path.dirname(__file__), "sw.template.js")).read().replace("__VERSION__", aver)
       .replace('"ml-shell-"', '"mla-shell-"').replace('"ml-runtime"', '"mla-runtime"')
       .replace('"icons/', '"../icons/').replace('"img/', '"../img/').replace('"data/packs.json"', '"../data/packs.json"'))
assert "mla-shell-" in asw
open(os.path.join(adm, "sw.js"), "w").write(asw)
print("admin/index.html", len(a), "Version", aver)

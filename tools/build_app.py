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
<meta name="description" content="Multilingo – dein persönliches Vokabelheft für Reisen.">
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
rep('Für die beste Aussprache Multilingo in Chrome unter claude.ai öffnen.', 'Für die beste Aussprache Multilingo in Chrome öffnen.')
s = re.sub(r'(data-img="(\w+)" src=")data:image/jpeg;base64,[^"]+', lambda m: m.group(1) + 'img/' + m.group(2) + '.jpg', s)
s = s.rstrip() + '\n<script src="ui.js"></script>\n</html>\n'
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "index.html"), "w").write(s)
ver = hashlib.sha1((s + open(os.path.join(out, "runtime.js")).read() + open(os.path.join(out, "ui.js")).read()).encode()).hexdigest()[:10]
sw = open(os.path.join(os.path.dirname(__file__), "sw.template.js")).read().replace("__VERSION__", ver)
open(os.path.join(out, "sw.js"), "w").write(sw)
print("index.html", len(s), "Version", ver)

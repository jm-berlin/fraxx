# Multilingo veröffentlichen (Ablauf für Claude)

Auslöser: die geplante Aufgabe „Multilingo veröffentlichen“ (jeden Abend) oder der Befehl **„Multilingo hochladen“** im Chat.

Grundregel: **Nur ein neuer Export wird veröffentlicht.** Der Klick auf „Export für Web-App“ (im Artefakt unter ⚙ → Admin) ist das OK des Admins. Ohne neuen Export wird nichts hochgeladen.

- Artefakt (Admin-Master): https://claude.ai/artifact/2U2W7WC52qfFMDeqTGo8om
- Repository: jm-berlin/multilingo (Branch `main`, GitHub Pages)
- Öffentlich: https://jm-berlin.github.io/multilingo/ · Admin: https://jm-berlin.github.io/multilingo/admin/

## Schritte

1. **Repository holen:** `git clone --depth 1 https://github.com/jm-berlin/multilingo.git` (falls nicht erreichbar: Repository mit Schreibrechten zur Sitzung hinzufügen, dann klonen).
2. **Exportteile finden:** Dateispeicher des Artefakts auflisten (Artifact `list`, `scope: "assets"`). Ein Export besteht aus mehreren JSON-Teilen, die innerhalb weniger Minuten hochgeladen wurden. Die Teile des **neuesten** Exports nehmen (alle mit fast gleicher Uhrzeit wie die jüngste Datei).
   - Ist die jüngste Datei nicht neuer als `publishedAt`/`stamp` in `tools/last-export.json`: **nichts tun**, fertig (keine Nachricht nötig).
3. **Teile herunterladen:** jede Datei mit Artifact `read` (`path` = Asset-ID) in einen leeren Ordner, z. B. `export/`.
4. **Artefakt-Quelltext holen:** Artifact `read` mit der Artefakt-URL; die gespeicherte HTML-Datei verwenden.
5. **Änderungshinweise schreiben:** Die App zeigt Nutzern vor dem Update „Was ist neu“. Dafür `hinweise.json` anlegen: 1–5 kurze Sätze aus Nutzersicht (keine Technik, keine Admin-Themen), was sich gegenüber dem letzten Stand geändert hat – in **allen** Oberflächensprachen: `{"de":[…],"en":[…],"fr":[…],"it":[…],"es":[…],"pt":[…],"nl":[…],"pl":[…],"sv":[…],"nb":[…]}`. Grundlage: Vergleich alter und neuer Stand (Anzahl Einträge je Bereich, neue Sprachpakete, Speisekarten/Grammatik je Sprache, sichtbare Änderungen in `tools/multilingo-artefakt.html` gegenüber der neuen Artefakt-Fassung). Sicher ist nur, was der Vergleich zeigt – nichts erfinden. Nur Kleinigkeiten: „Verbesserungen und Korrekturen.“
6. **Bauen und prüfen:** im Repository `python3 tools/publish.py <export-ordner> <artefakt.html> hinweise.json > publish.log 2>&1` und die letzte Zeile lesen (nicht mit `head` abschneiden):
   - `ERGEBNIS: NICHTS-NEU` → fertig, nichts committen.
   - `ERGEBNIS: ABBRUCH …` → nichts committen; dem Admin den Grund kurz melden.
   - `ERGEBNIS: FERTIG` → weiter mit 7.
7. **Hochladen:** `git add -A`, Commit „Veröffentlicht: Export vom <stamp>“ (mit den Attributionszeilen der Sitzung), `git push origin HEAD:main`. Danach mit `git ls-remote origin main` prüfen, dass der Commit angekommen ist.
8. **Melden:** kurze Nachricht auf Deutsch: Export vom …, Anzahl Einträge, Sprachpakete, was sich gegenüber vorher geändert hat (z. B. neue Sprache, mehr Einträge). Hinweis: installierte Apps holen sich das Update beim nächsten Start mit Internet.

## Wichtig

- Nie `.git` aus einem anderen Ordner in das Repository kopieren.
- Ausgaben der Bauskripte in eine Datei umleiten, nicht nach `head` pipen (das bricht das Bauen ab).
- Keine Inhalte erfinden oder von Hand ändern; nur bauen, prüfen, hochladen.

## Update-Hinweis in der App

`data/packs.json` enthält `release` (Kennung der Veröffentlichung), `data/changes.json` die Hinweise je Release.
Geräte übernehmen eine neue Veröffentlichung erst, wenn der Nutzer im Hinweis „Update verfügbar“ zustimmt.
Wird von Hand etwas veröffentlicht (z. B. Änderung an runtime.js/ui.js), danach `python3 tools/release.py hinweise.json` ausführen, sonst sehen Geräte das Update nicht.

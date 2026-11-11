# Fraxx – Mein bester Reisebegleiter

Persönliche Sprach-App für Reisen: Wörter und Redewendungen eintragen, dazu Übersetzungen, Aussprache, Artikel, Konjugationen, Grammatik und Speisekarten aus vielen Ländern. Funktioniert nach der Installation auch offline.

**Zur App:** https://fraxx.app/

## Installieren

Fraxx ist eine Web-App: Adresse im Browser öffnen und als App hinzufügen. Es gibt keinen Installer.

- **Anleitung auf Deutsch:** [INSTALLATION.md](INSTALLATION.md) · [PDF](Fraxx-Installation.pdf)
- **Guide in English:** [INSTALL.md](INSTALL.md) · [PDF](Fraxx-Install-Guide.pdf)

## Sprachen

Standardmäßig installiert: Deutsch, Englisch, Französisch, Italienisch, Spanisch.
Zum Nachladen unter ⚙ → *App, Sprachpakete & Sicherung*: Polnisch, Portugiesisch, Niederländisch, Schwedisch, Norwegisch.
Beim ersten Start lässt sich die Ausgangssprache wählen.

## Daten

- **Standarddaten** (`data/core.json`) und **Sprachpakete** (`data/lang-xx.json`) kommen von hier. Bei Updates laden die Geräte nur geänderte Pakete neu.
- **Eigene Einträge und Änderungen** liegen getrennt auf dem Gerät und bleiben bei Updates erhalten. Unter ⚙ lassen sie sich als Datei sichern und auf einem anderen Gerät einlesen.
- **Eigene Übersetzungen** neuer Wörter sind in der Testversion noch nicht freigeschaltet und kommen in einer späteren Version.

## Aufbau

```
index.html            App
runtime.js            lokaler Speicher (Standard + eigene Daten), Ausgangssprache
ui.js                 App-Einstellungen: Sprachpakete, Sicherung, Installation
sw.js                 Offline-Betrieb
data/                 core.json, lang-xx.json, packs.json
tools/                Bauskripte (build_app.py, build_data.py), Design-Archiv
```

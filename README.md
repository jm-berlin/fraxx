# Multilingo – Mein bester Reisebegleiter

Persönliche Sprach-App für Reisen: Wörter und Redewendungen eintragen, dazu Übersetzungen, Aussprache, Artikel, Konjugationen, Grammatik und Speisekarten aus vielen Ländern. Funktioniert nach der Installation auch offline.

**Zur App:** https://jm-berlin.github.io/multilingo/

## Installieren

Multilingo ist eine Web-App: Adresse im Browser öffnen und als App hinzufügen. Es gibt keinen Installer.

- **Anleitung auf Deutsch:** [INSTALLATION.md](INSTALLATION.md) · [PDF](Multilingo-Installation.pdf)
- **Guide in English:** [INSTALL.md](INSTALL.md) · [PDF](Multilingo-Install-Guide.pdf)

## Sprachen

Standardmäßig installiert: Deutsch, Englisch, Französisch, Italienisch, Spanisch.
Zum Nachladen unter ⚙ → *App, Sprachpakete & Sicherung*: Polnisch, Portugiesisch, Niederländisch, Schwedisch, Norwegisch.
Beim ersten Start lässt sich die Ausgangssprache wählen.

## Daten

- **Standarddaten** (`data/core.json`) und **Sprachpakete** (`data/lang-xx.json`) kommen von hier. Bei Updates laden die Geräte nur geänderte Pakete neu.
- **Eigene Einträge und Änderungen** liegen getrennt auf dem Gerät und bleiben bei Updates erhalten. Unter ⚙ lassen sie sich als Datei sichern und auf einem anderen Gerät einlesen.
- **Online-Übersetzung** neuer Wörter ist optional: mit einem eigenen Claude-API-Schlüssel (bleibt nur auf dem Gerät).

## Aufbau

```
index.html            App
admin/                Admin-Fassung (Auftragsliste, alle Sprachpakete, eigener Speicher)
runtime.js            lokaler Speicher (Standard + eigene Daten), Ausgangssprache, optionale Online-Übersetzung
ui.js                 App-Einstellungen: Sprachpakete, Sicherung, Schlüssel, Installation
sw.js                 Offline-Betrieb
data/                 core.json, lang-xx.json, packs.json
tools/                Bauskripte (build_app.py, build_data.py), Design-Archiv
```

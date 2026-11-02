# Multilingo – Mein bester Reisebegleiter

Persönliches Vokabelheft für Reisen: Wörter und Redewendungen auf Deutsch eintragen, dazu Übersetzungen, Aussprache, Artikel, Konjugationen, Grammatik und Speisekarten aus vielen Ländern.

**Zur App:** https://jm-berlin.github.io/multilingo/

## Installieren

| Gerät | So geht’s |
|---|---|
| Windows / Mac (Chrome oder Edge) | Seite öffnen → in der Adressleiste auf das Installieren-Symbol klicken (oder Menü ⋮ → „App installieren“) |
| Android (Chrome) | Seite öffnen → Menü ⋮ → „App installieren“ / „Zum Startbildschirm hinzufügen“ |
| iPhone / iPad (Safari) | Seite öffnen → Teilen-Symbol → „Zum Home-Bildschirm“ |

Danach startet Multilingo wie eine eigene App und funktioniert auch offline.

## Daten

- **Standarddaten** (`data/core.json`) und **Sprachpakete** (`data/lang-xx.json`) kommen von hier und werden bei Updates erneuert.
- **Eigene Einträge und Änderungen** liegen getrennt auf dem Gerät und bleiben bei Updates erhalten.
  Unter ⚙ → *App, Sprachpakete & Sicherung* lassen sie sich als Datei sichern und auf einem anderen Gerät einlesen.
- **Online-Übersetzung** neuer Wörter ist optional: mit einem eigenen Claude-API-Schlüssel (bleibt nur auf dem Gerät).

## Aufbau

```
index.html            App
runtime.js            lokaler Speicher (Standard + eigene Daten), optionale Online-Übersetzung
ui.js                 App-Einstellungen: Sprachpakete, Sicherung, Schlüssel, Installation
sw.js                 Offline-Betrieb
data/packs.json       Verzeichnis der Sprachpakete
tools/                Skripte zum Erzeugen von App und Datenpaketen
```

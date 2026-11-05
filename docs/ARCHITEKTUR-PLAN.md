# Multilingo – Plan für die Aufräumphase (nach der Beta)

Vereinbart am 5. November 2026. Bis dahin wird wie bisher in der einen Artefakt-Datei weitergearbeitet,
bis alle Funktionen da sind und das Design geklärt ist. Danach wird auf Basis des Verabschiedeten aufgeräumt.

## Grundsatz
Modular entwickeln, aber weiterhin **eine Datei ausliefern** (narrensichere Installation, komplett austauschbar).
Ein Build-Schritt (z. B. esbuild) bündelt die Module wieder zu je einer HTML-Datei.

## Stand bei der Entscheidung
- Artefakt-Datei ca. 1 MB / 6.600 Zeilen: ~450 KB JavaScript (~260 Funktionen), ~105 KB CSS, eingebettete Bilder, ~33 KB UI-Texte.
- 39 CSS-Regeln mit `html:root:root` zum Überstimmen älterer Schichten.
- Auftragsliste, Warteschlange und Inhalts-Generatoren über gemeinsamen Zustand gekoppelt.
- Keine automatischen Tests (bisher Playwright-Prüfungen von Hand mit simulierten Claude-Antworten).
- Öffentliche Fassung enthält Admin-Code und alle Prompts.

## Zielstruktur
- **core**: Datenmodell, Speicher, Seeds, Ausgangssprache/Fassungen
- **ui**: Tabelle, Inhalt, Spickzettel, Quiz, Grammatik, Speisekarte (je ein Modul)
- **i18n**: Oberflächentexte und Übersetzung
- **design**: CSS mit Tokens, Komponenten, Themes – ohne Überstimm-Regeln
- **admin**: Auftragsliste, Generatoren/Prompts, Export
- Zwei Bündel: öffentlich (ohne admin) und Admin (alles; daraus auch das Claude-Artefakt)
- Tests: Unit-Tests für reine Funktionen (Dubletten, Umschrift, Speisekarten-Lücken, Prompt-Bausteine) + Playwright-Rauchtests vor jeder Veröffentlichung

## Reihenfolge (schrittweise, kein Neustart)
1. CSS bereinigen und als Design-System ordnen
2. Admin-Teil herauslösen (öffentlicher Code schlanker, ohne Prompts)
3. Fachbereiche einzeln auslagern, jeweils mit Tests

## Arbeitsweise
Der Admin arbeitet als Nutzer/Product Owner an der Customer Journey; Claude setzt um, testet und veröffentlicht –
wie unter Kollegen, ohne Zeilen-für-Zeilen-Review.

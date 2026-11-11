# Fraxx – Entscheidungen und offene Punkte

Logbuch für alle Sitzungen: kurz, mit Datum, neueste oben. Wer an Fraxx arbeitet, liest das zuerst.
Details stehen in `docs/ARCHITEKTUR-PLAN.md` und `tools/VEROEFFENTLICHEN.md`.

## Offene Punkte
- **Zahlungsabwickler** auswählen (Stripe, Paddle oder Lemon Squeezy) und festlegen, wie das Bezahlen eingebaut wird. → ARCHITEKTUR-PLAN, Abschnitt „Bezahlmodell“
- **Kostenlos vs. bezahlt:** Wie viele Zielsprachen sind gratis? Was kommt ins Pro-Paket?
- **Store-Apps** (Google Play / App Store): Verpackung und Bezahlregeln vor dem Umsetzen prüfen.
- **Modulare Sprachpakete** (Kern, Sprachpaket, Hinweispaket je Sprachpaar, Zusatzpakete): erst nach der Testphase.
- **Ladestrategie der Web-App:** Der Admin denkt noch darüber nach. Seit 11.11. gibt es Ladebalken je Sprache beim ersten Start.
- **Artefakt weiter verschlanken:** Speisekarten (15 MB) nur beim Öffnen der Speisekarte laden.
- **iPhone:** Prüfen, ob die Sprachausgabe auch im Lautlos-Modus klappt und ob der Update-Knopf im Hochformat tippbar ist (Korrekturen vom 11.11.).
- **Erinnerung 24.11.:** Aufräumphase / modulare Struktur besprechen (geplante Aufgabe „nach dem Urlaub“).

## Entscheidungen

### 11.11.2026
- **Testphase:** Erst die Bedienung mit den vorhandenen Daten testen und verbessern, die Datenstruktur bleibt vorerst.
- **Veröffentlichen nur auf Zuruf:** Die nächtliche Aufgabe „Fraxx veröffentlichen“ ist deaktiviert. Der Admin sagt, wann veröffentlicht wird. Dafür muss ein Fenster des Artefakts vollständig geladen sein, damit es exportieren kann.
- **Kein fester Hauptrechner:** Aufträge und Export übernimmt das Fraxx-Fenster, das offen und vollständig geladen ist. Derzeit ist das der Laptop des Admins.
- **Artefakt verschlankt:** Die Fassungen für andere Ausgangssprachen liegen in einer eigenen Ablage (`data/users/<id>/nbs/p`). Die norwegische Übersetzung bleibt im Eintrag, denn das Feld `nb` ist zugleich Norwegisch. Exporte ohne Fassungen (`nbFull: false`) ergänzt `tools/fill_nb.py` aus der Sicherung.
- **Schutz beim Laden:** Aufträge, Angebote und Export starten erst, wenn alle Einträge geladen sind. Ein Zwischenspeicher auf dem Gerät zeigt den letzten Stand sofort.
- **Sicherung:** Privates Repo `jm-berlin/fraxx-backup` mit dem kompletten Rohexport und dem Artefakt-Quelltext. Wird bei jeder Veröffentlichung aktualisiert, ein deutlich kleinerer Stand wird abgelehnt.
- **Keine öffentliche Admin-Version:** `/admin/` ist entfernt. Der Admin arbeitet nur im Claude-Artefakt.
- **Domain:** `https://fraxx.app/` (GitHub Pages, HTTPS erzwungen). `fraxx.io` soll per Weiterleitung beim Anbieter (Checkdomain) auf fraxx.app zeigen.
- **Logo:** Schriftzug „Fraxx“ in Archivo Black, das letzte x mit langem Aufstrich bis zur Höhe des F. Icon: F in Archivo Black, weiß auf schwarzem Kasten. Der Schriftzug steht auch in den Überschriften der Startseite.
- **Suche:** Das Feld heißt „Suchen“. Eine Lupe in der Kopfzeile sucht auf jeder Seite, genaue Treffer stehen oben, dazu Wortkarte auf dem Handy und „Zuletzt gesucht“. Neu anlegen bzw. Übersetzen gibt es nur in der Admin- bzw. späteren Pro-Version.
- **Reiter:** Nur noch drei (Redewendungen, Wortschatz, Wortarten mit Unterauswahl).
- **Startseite:** „6.400+ Einträge“. Die 7.247 Datensätze enthalten auch Speisekarten, Grammatik und Oberflächentexte.

### 10.11.2026
- **Name:** Fraxx (vorher Multilingo, Viavox, Phraxx). Das Repo heißt `jm-berlin/fraxx`.
- **Domains gesichert:** fraxx.app und fraxx.io.

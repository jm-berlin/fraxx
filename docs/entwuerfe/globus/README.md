# Entwurf: Drahtgitter-Globus für die Startseite

Stand 6. November 2026 – Entwurf 1, noch nicht in der App.

- `globus-entwurf-1.html` – fertige Seite zum Ansehen (im Browser öffnen), mit den drei bisherigen Fotos.
- `vorlage.html` – Quelltext mit Platzhaltern (`__COUNTRIES__`, `__PARIS__`, `__ANDALUCIA__`, `__TOSCANA__`).
- `laender-110m.txt` – Ländergrenzen (Natural Earth 1:110 Mio., gemeinfrei), kompakt kodiert: Ringe durch `;` getrennt, Koordinaten ×5, ab dem zweiten Punkt als Differenzen.

Technik: WebGL zeichnet die Fotos auf die Kugel (orthografische Projektion, gewölbt, zum Rand hin abgedunkelt),
ein 2D-Canvas darüber die Linien (Gradnetz, Ländergrenzen, Umriss; Rückseite durchscheinend). Drehen per Maus/Finger,
ruht bei „Bewegung reduzieren“.

Offene Frage: Anordnung der Fotos (die meisten Länder liegen in Europa). Ideen siehe Chat vom 6. November.

## Entwurf 2: drei Varianten (6. November 2026)

`globus-varianten.html` – zum Umschalten:
1. **Hineinzoomen** – dreht sich ein, zoomt auf Europa, Bilder in ihren Ländern, danach sanftes Pendeln.
2. **Fotos an Fäden** – freie Drehung, Bilder im freien Raum um Europa, Faden zum Pin am Ort.
3. **Mosaik** – 21 Bilder gleichmäßig über die Kugel verteilt (symbolisch).

Paris, Andalusien und Toskana sind echte Fotos, die übrigen 18 Karten Platzhalter (Gruß + Ort). Quelltext: `vorlage-varianten.html`.

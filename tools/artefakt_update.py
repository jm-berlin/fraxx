"""Bringt die Artefakt-Datei auf den Stand der Web-App: vorgemerkte App-Änderungen (app_patches.py) und neuer Name Fraxx.

    python3 tools/artefakt_update.py <artefakt.html> <ausgabe.html>

Danach die Ausgabe als neue Fassung des Artefakts veröffentlichen (Artifact publish_files, Titel „Fraxx“).
Ist das Artefakt schon auf dem Stand, ist die Ausgabe gleich der Eingabe."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app_patches, rename_fraxx
src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()
n = rename_fraxx.convert(app_patches.apply(s))
open(out, "w", encoding="utf-8").write(n)
print("unverändert" if n == s else "aktualisiert", "→", out)

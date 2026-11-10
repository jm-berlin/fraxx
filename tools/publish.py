"""Veröffentlichen: Export aus dem Claude-Artefakt -> öffentliche Fassung + Admin-Fassung in diesem Repository.

Aufruf (im Repository-Ordner):
    python3 tools/publish.py <ordner-mit-export-teilen> <artefakt.html> [hinweise.json]

<ordner-mit-export-teilen>: die JSON-Dateien, die der Knopf „Export für Web-App“ im Artefakt in dessen
Dateispeicher legt (je Teil eine Datei mit {"app":"multilingo","type":"export","stamp",...,"docs":[...]}).
Es dürfen auch Teile älterer Exporte darin liegen: verwendet wird nur der neueste vollständige Export.
<artefakt.html>: die aktuelle Fassung des Artefakts (Quelltext der Seite).
[hinweise.json]: was sich für Nutzer geändert hat, in allen Oberflächensprachen (Format siehe tools/release.py).
Die App zeigt es beim nächsten Start im Hinweis „Update verfügbar“.

Ergebnis (letzte Zeile der Ausgabe):
    ERGEBNIS: NICHTS-NEU        Dieser Export ist schon veröffentlicht. Nichts geändert.
    ERGEBNIS: FERTIG            Alles gebaut und geprüft. Jetzt committen und pushen.
    ERGEBNIS: ABBRUCH <grund>   Etwas stimmt nicht. Nichts committen; Grund melden.
"""
import json, glob, os, sys, shutil, subprocess, tempfile, datetime

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STAMP_FILE = os.path.join(REPO, "tools", "last-export.json")


def stop(msg, code=1):
    print("ERGEBNIS:", msg); sys.exit(code)


def main():
    if len(sys.argv) not in (3, 4): stop("ABBRUCH Aufruf: publish.py <export-ordner> <artefakt.html> [hinweise.json]", 2)
    exp_dir, art = sys.argv[1], sys.argv[2]
    notes = {}
    if len(sys.argv) == 4:
        try: notes = json.load(open(sys.argv[3]))
        except Exception as e: stop(f"ABBRUCH Hinweise nicht lesbar: {e}")

    # 1) Neuesten vollständigen Export finden
    groups = {}
    for f in glob.glob(os.path.join(exp_dir, "**", "*.json"), recursive=True):
        try: d = json.load(open(f))
        except Exception: continue
        if not isinstance(d, dict) or d.get("app") != "multilingo" or d.get("type") != "export": continue
        groups.setdefault(d["stamp"], {})[d["part"]] = d
    complete = {s: g for s, g in groups.items() if g and len(g) == next(iter(g.values()))["parts"]}
    if not complete: stop("ABBRUCH kein vollständiger Export gefunden")
    stamp = max(complete)
    parts = complete[stamp]
    docs = [doc for i in sorted(parts) for doc in parts[i]["docs"]]
    total = next(iter(parts.values()))["total"]
    if len(docs) != total: stop(f"ABBRUCH Export unvollständig ({len(docs)} von {total} Dokumenten)")
    print(f"Export vom {stamp}: {total} Dokumente in {len(parts)} Teilen")

    last = {}
    if os.path.exists(STAMP_FILE):
        try: last = json.load(open(STAMP_FILE))
        except Exception: last = {}
    if last.get("stamp") == stamp: stop("NICHTS-NEU", 0)

    # 2) Dokumente einzeln ablegen (Format, das build_data.py erwartet)
    tmp = tempfile.mkdtemp(prefix="ml-export-")
    for doc in docs:
        doc = dict(doc); i = doc.pop("id", None)
        if not i: continue
        json.dump(doc, open(os.path.join(tmp, i + ".json"), "w"), ensure_ascii=False)

    # Vorheriger Stand zum Vergleich
    old_packs = {}
    pj = os.path.join(REPO, "data", "packs.json")
    if os.path.exists(pj):
        try: old_packs = json.load(open(pj))
        except Exception: old_packs = {}

    # 3) App bauen (öffentlich + admin/) aus der aktuellen Artefakt-Fassung
    shutil.copy(art, os.path.join(REPO, "tools", "multilingo-artefakt.html"))
    r = subprocess.run([sys.executable, "tools/build_app.py", "tools/multilingo-artefakt.html", "."], cwd=REPO, capture_output=True, text=True)
    print(r.stdout[-2000:], r.stderr[-2000:])
    if r.returncode != 0: stop("ABBRUCH build_app.py fehlgeschlagen (siehe oben)")

    # 4) Daten bauen
    data_new = os.path.join(tmp, "data")
    r = subprocess.run([sys.executable, "tools/build_data.py", tmp, data_new], cwd=REPO, capture_output=True, text=True)
    print(r.stdout[-4000:], r.stderr[-2000:])
    if r.returncode != 0: stop("ABBRUCH build_data.py fehlgeschlagen (siehe oben)")

    # 5) Prüfen, bevor etwas ersetzt wird
    try: new_packs = json.load(open(os.path.join(data_new, "packs.json")))
    except Exception: stop("ABBRUCH packs.json fehlt im neuen Stand")
    def langs(p):
        L = p.get("langs") or p.get("packs") or []
        if isinstance(L, dict): return set(L)
        return {x.get("code") or x.get("lang") for x in L if isinstance(x, dict)}
    lost = langs(old_packs) - langs(new_packs)
    if lost: stop("ABBRUCH Sprachpakete würden wegfallen: " + ", ".join(sorted(lost)))
    if not os.path.exists(os.path.join(data_new, "core.json")): stop("ABBRUCH core.json fehlt")
    def entries(dirp):
        try: return sum(1 for d in json.load(open(os.path.join(dirp, "core.json")))["docs"] if d.get("kind") is None)
        except Exception: return 0
    n_old, n_new = entries(os.path.join(REPO, "data")), entries(data_new)
    print(f"Einträge: vorher {n_old}, jetzt {n_new}")
    if n_old and n_new < n_old * 0.97: stop(f"ABBRUCH deutlich weniger Einträge als vorher ({n_new} statt {n_old})")
    for f in ("index.html", "admin/index.html"):
        if not os.path.exists(os.path.join(REPO, f)): stop("ABBRUCH " + f + " fehlt")

    # 6) Übernehmen (Release-Kennung und Änderungshinweise für den Hinweis „Update verfügbar“)
    try: old_changes = json.load(open(os.path.join(REPO, "data", "changes.json")))
    except Exception: old_changes = {}
    sys.path.insert(0, os.path.join(REPO, "tools")); from release import add_release
    # Vorgemerkte Hinweise zu Änderungen an der App selbst (runtime.js/ui.js) kommen zuerst und werden danach geleert
    pend_f = os.path.join(REPO, "tools", "offene-hinweise.json")
    if os.path.exists(pend_f):
        try:
            pend = json.load(open(pend_f))
            for l, v in pend.items():
                if isinstance(v, list): notes[l] = list(v) + [x for x in (notes.get(l) or []) if x not in v and x != "Verbesserungen und Korrekturen."]
        except Exception as e: print("Hinweis: offene-hinweise.json nicht lesbar:", e)
        os.remove(pend_f)
    add_release(data_new, stamp, notes, old_changes)
    # Anleitung: Übersetzungen aus dem Export übernehmen (nur passend zum aktuellen deutschen Text) und alle Sprachen neu bauen.
    # Fehler hier brechen die Veröffentlichung nicht ab.
    try:
        import hashlib
        tdir = os.path.join(REPO, "tools", "tutorial-texts"); os.makedirs(tdir, exist_ok=True)
        de_txt = json.load(open(os.path.join(tdir, "de.json")))
        th = hashlib.sha1(json.dumps(de_txt, ensure_ascii=False, sort_keys=True).replace("Fraxx", "Multilingo").replace("Phraxx", "Multilingo").replace("Viavox", "Multilingo").encode()).hexdigest()[:10]  # Hash wie im Artefakt (Text noch mit altem Namen)
        for d in docs:
            if d.get("kind") == "tutorial" and d.get("hash") == th and isinstance(d.get("text"), dict) and d.get("lang") and (d["text"].get("after") or [[None]])[0][0] != de_txt["after"][0][0]:
                json.dump(d["text"], open(os.path.join(tdir, d["lang"] + ".json"), "w"), ensure_ascii=False, indent=1)
    except Exception as e: print("Hinweis: Anleitungstexte nicht übernommen:", e)
    tutorial_pending = True
    shutil.rmtree(os.path.join(REPO, "data"), ignore_errors=True)
    shutil.copytree(data_new, os.path.join(REPO, "data"))
    if tutorial_pending:
        try:
            r = subprocess.run([sys.executable, "tools/tutorial_all.py"], cwd=REPO, capture_output=True, text=True, timeout=7200)
            print(r.stdout[-1500:], r.stderr[-1500:])
        except Exception as e: print("Hinweis: Anleitung nicht gebaut:", e)
    json.dump({"stamp": stamp, "documents": total, "entries": n_new,
               "publishedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
               "langs": sorted(x for x in langs(new_packs) if x)}, open(STAMP_FILE, "w"), ensure_ascii=False, indent=1)
    print(f"Sprachpakete: {', '.join(sorted(x for x in langs(new_packs) if x))}")
    stop("FERTIG", 0)


if __name__ == "__main__":
    main()

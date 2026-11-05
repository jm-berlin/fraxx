"""Release vermerken: data/packs.json bekommt eine neue Kennung ("release"), data/changes.json die Hinweise dazu.
Die App zeigt beim nächsten Start „Update verfügbar“ mit diesen Hinweisen und übernimmt erst nach Zustimmung.

Hinweise-Datei (JSON): {"de": ["…", "…"], "en": ["…"], "fr": [...], ...} – kurze Sätze aus Nutzersicht,
in allen Oberflächensprachen der App (de en fr it es pt nl pl sv nb). Fehlt eine Sprache, zeigt die App Englisch.

Von Hand (z. B. nach einer Änderung an runtime.js/ui.js):  python3 tools/release.py hinweise.json
"""
import json, os, sys, datetime

UI_LANGS = ["de", "en", "fr", "it", "es", "pt", "nl", "pl", "sv", "nb"]


def add_release(data_dir, release, notes, old_changes=None):
    pj = os.path.join(data_dir, "packs.json")
    packs = json.load(open(pj)); packs["release"] = release
    json.dump(packs, open(pj, "w"), ensure_ascii=False, separators=(",", ":"))
    ch = old_changes
    if ch is None:
        try: ch = json.load(open(os.path.join(data_dir, "changes.json")))
        except Exception: ch = {}
    rel = [r for r in (ch.get("releases") or []) if r.get("release") != release]
    clean = {l: [str(x).strip() for x in v if str(x).strip()][:8] for l, v in (notes or {}).items() if isinstance(v, list)}
    rel.insert(0, {"release": release, "date": release[:10], "notes": clean})
    json.dump({"releases": rel[:30]}, open(os.path.join(data_dir, "changes.json"), "w"), ensure_ascii=False, indent=1)
    missing = [l for l in UI_LANGS if l not in clean]
    if missing: print("Hinweis: keine Release-Hinweise für", ", ".join(missing), "(App zeigt dort Englisch)")


if __name__ == "__main__":
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    notes = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {}
    rid = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    add_release(os.path.join(repo, "data"), rid, notes)
    print("Release", rid)

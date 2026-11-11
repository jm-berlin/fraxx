"""Ergänzt in einem Export die Fassungen für andere Ausgangssprachen (Feld nb) aus der letzten Sicherung.
Seit dem 11.11.2026 liegen diese Fassungen im Artefakt in einer eigenen Ablage und sind nur dann im Export,
wenn das exportierende Fenster sie geladen hatte (Kennzeichen nbFull). Fehlt nb bei einem Eintrag, wird es aus
export.json.gz des Backup-Repos übernommen. Aufruf: python3 tools/fill_nb.py <export-ordner> <backup-ordner>"""
import sys, os, json, gzip, glob
exp, bak = sys.argv[1:3]
src = os.path.join(bak, "export.json.gz")
if not os.path.exists(src): sys.exit("ABBRUCH keine Sicherung mit Fassungen gefunden")
old = {d["id"]: d.get("nb") for d in json.load(gzip.open(src, "rt", encoding="utf-8"))["docs"] if d.get("nb")}
n = 0
for f in glob.glob(os.path.join(exp, "*.json")):
    try: p = json.load(open(f))
    except Exception: continue
    if p.get("type") != "export" or p.get("nbFull") is not False: continue
    ch = False
    for d in p["docs"]:
        if not d.get("kind") and not d.get("nb") and d.get("id") in old: d["nb"] = old[d["id"]]; n += 1; ch = True
    if ch: json.dump(p, open(f, "w"), ensure_ascii=False)
print(f"FASSUNGEN ergänzt: {n}")

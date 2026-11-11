"""Sicherung des kompletten Rohexports ins private Repo jm-berlin/fraxx-backup.
Aufruf: python3 tools/backup.py <export-ordner> <artefakt.html> <backup-repo-ordner>
Legt export.json.gz (alle Teile zu einer Liste zusammengefügt, gleicher stamp, vollständig),
artefakt.html.gz und stand.json ab. Ältere Stände stehen in der Git-Geschichte des Backup-Repos.
Wiederherstellen: siehe README.md im Backup-Repo."""
import sys, os, json, gzip, glob

exp, art, repo = sys.argv[1:4]
parts = []
for f in glob.glob(os.path.join(exp, "*.json")):
    try: d = json.load(open(f))
    except Exception: continue
    if d.get("type") == "export": parts.append(d)
if not parts: sys.exit("ABBRUCH keine Exportteile")
stamp = max(p["stamp"] for p in parts)
parts = sorted((p for p in parts if p["stamp"] == stamp), key=lambda p: p["part"])
n = parts[0]["parts"]
if [p["part"] for p in parts] != list(range(1, n + 1)): sys.exit("ABBRUCH Export unvollständig")
docs = [d for p in parts for d in p["docs"]]
if len(docs) != parts[0]["total"]: sys.exit(f"ABBRUCH {len(docs)} statt {parts[0]['total']} Einträge")
os.makedirs(repo, exist_ok=True)
with gzip.open(os.path.join(repo, "export.json.gz"), "wt", encoding="utf-8", compresslevel=9) as g:
    json.dump({"app": parts[0].get("app"), "type": "export", "stamp": stamp, "total": len(docs), "docs": docs}, g, ensure_ascii=False)
with open(art, "rb") as src, gzip.open(os.path.join(repo, "artefakt.html.gz"), "wb", compresslevel=9) as g:
    g.write(src.read())
json.dump({"stamp": stamp, "eintraege": len(docs), "teile": n}, open(os.path.join(repo, "stand.json"), "w"), ensure_ascii=False, indent=2)
print(f"BACKUP {stamp} {len(docs)} Einträge")

"""Erzeugt aus dem Datenbank-Export die Standarddaten (core.json) und je Sprache ein Paket (lang-xx.json)."""
import json, glob, os, sys, gzip, re
SRC_DIR = sys.argv[1]; OUT = sys.argv[2]
LANGS = {"en":"Englisch","fr":"Französisch","es":"Spanisch","it":"Italienisch","pl":"Polnisch"}
docs = []
for f in glob.glob(os.path.join(SRC_DIR, "*.json")):
    d = json.load(open(f)); d["id"] = os.path.basename(f)[:-5]; docs.append(d)
core = []; packs = {l: {"overlay": {}, "docs": []} for l in LANGS}
def codes_in(id_):
    parts = re.split(r"[-]", id_)[1:]
    return [p for p in parts if p in LANGS]
for d in docs:
    kind = d.get("kind")
    if kind is None:  # Eintrag
        c = {k:v for k,v in d.items() if k not in LANGS and k not in ("conj","nb","quiz")}
        conj = d.get("conj"); nb = d.get("nb") or {}; quiz = d.get("quiz")
        if isinstance(conj, dict): c["conj"] = {k:v for k,v in conj.items() if k not in LANGS}
        elif "conj" in d: c["conj"] = conj
        if nb: c["nb"] = {"de": {k:v for k,v in (nb.get("de") or {}).items() if k not in LANGS}} if "de" in nb else {}
        if isinstance(quiz, dict): c["quiz"] = {k:v for k,v in quiz.items() if k not in LANGS}
        core.append(c)
        for l in LANGS:
            o = {}
            if l in d: o[l] = d[l]
            if isinstance(conj, dict) and l in conj: o["conj"] = {l: conj[l]}
            nbo = {}
            for s, snap in nb.items():
                if not isinstance(snap, dict): continue
                for t, v in snap.items():
                    owner = t if t != "de" else s
                    if owner == l and not (s == "de" and t == "de"): nbo.setdefault(s, {})[t] = v
            if nbo: o["nb"] = nbo
            if isinstance(quiz, dict) and l in quiz: o["quiz"] = {l: quiz[l]}
            if o: packs[l]["overlay"][d["id"]] = o
    elif kind in ("section", "settings"):
        core.append(d)
    else:
        cs = codes_in(d["id"])
        if not cs: core.append(d); continue
        x = dict(d)
        if len(cs) > 1: x["__req"] = cs[1:]
        packs[cs[0]]["docs"].append(x)
os.makedirs(OUT, exist_ok=True)
def dump(name, obj):
    s = json.dumps(obj, ensure_ascii=False, separators=(",",":"))
    open(os.path.join(OUT, name), "w").write(s)
    return len(s.encode()), len(gzip.compress(s.encode()))
sizes = {}
sizes["core"] = dump("core.json", {"version": 1, "docs": core})
index = {"version": 1, "core": {"file": "core.json", "bytes": sizes["core"][0]}, "packs": []}
for l, p in packs.items():
    p.update({"lang": l, "name": LANGS[l], "version": 1})
    b = dump(f"lang-{l}.json", p); sizes[l] = b
    index["packs"].append({"lang": l, "name": LANGS[l], "file": f"lang-{l}.json", "version": 1, "bytes": b[0], "entries": len(p["overlay"]), "docs": len(p["docs"])})
json.dump(index, open(os.path.join(OUT, "packs.json"), "w"), ensure_ascii=False, indent=1)
for k, (a, g) in sizes.items(): print(f"{k:5} {a/1e6:6.2f} MB  gzip {g/1e6:5.2f} MB")

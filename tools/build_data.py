"""Erzeugt aus dem Datenbank-Export die Standarddaten (core.json) und je Sprache ein Paket (lang-xx.json)."""
import json, glob, os, sys, gzip, re
SRC_DIR = sys.argv[1]; OUT = sys.argv[2]
# Alle Sprachen, die Multilingo kennt (wie CATALOG in der App). Ein Paket entsteht automatisch für jede Sprache,
# zu der im Export Übersetzungen stehen, also für jede Sprache, die in Claude angelegt wurde.
CATALOG = {"en":"Englisch","fr":"Französisch","es":"Spanisch","it":"Italienisch","pt":"Portugiesisch","nl":"Niederländisch",
  "pl":"Polnisch","tr":"Türkisch","el":"Griechisch","hr":"Kroatisch","sv":"Schwedisch","da":"Dänisch","nb":"Norwegisch",
  "cs":"Tschechisch","hu":"Ungarisch","ro":"Rumänisch","ca":"Katalanisch","ru":"Russisch","ja":"Japanisch","zh":"Chinesisch","ar":"Arabisch"}
# Standardinstallation: diese Pakete werden beim ersten Start geladen, alle anderen kann man unter ⚙ nachladen
DEFAULT = ["en", "fr", "it", "es"]
docs = []
for f in glob.glob(os.path.join(SRC_DIR, "*.json")):
    d = json.load(open(f)); d["id"] = os.path.basename(f)[:-5]; docs.append(d)
# Einträge auf Deutsch als Grundfassung bringen: Wurde in Claude zuletzt mit einer anderen Ausgangssprache gearbeitet,
# liegt die deutsche Fassung in nb["de"]. Sie wird eingesetzt, die aktuelle Fassung wandert nach nb[<Sprache>].
def _snap(d):
    s = {"de": {"text": d.get("de",""), "note": d.get("denote","")}}
    for l in CATALOG:
        v = d.get(l)
        if isinstance(v, dict) and v.get("text"): s[l] = {"text": v["text"], "note": v.get("note","")}
    return s
_norm = 0
for d in docs:
    if d.get("kind") is not None: continue
    L = d.get("noteLang") or "de"; nb = d.get("nb") or {}
    if L == "de" or not isinstance(nb.get("de"), dict) or not (nb["de"].get("de") or {}).get("text"): continue
    old = nb["de"]; nb2 = dict(nb); del nb2["de"]; nb2[L] = _snap(d)
    for c, v in old.items():
        if not isinstance(v, dict) or not v.get("text"): continue
        if c == "de": d["de"] = v["text"]; d["denote"] = v.get("note","")
        else: d[c] = {**(d.get(c) or {}), "text": v["text"], "note": v.get("note","")}
    d["nb"] = nb2; d["noteLang"] = "de"; d["nbCur"] = json.dumps(_snap(d), ensure_ascii=False, separators=(",",":")); _norm += 1
print("auf Deutsch umgestellt:", _norm)
# Sprachen mit Übersetzungen finden
from collections import Counter
_cnt = Counter(l for d in docs if d.get("kind") is None for l in CATALOG if isinstance(d.get(l), dict) and d[l].get("text"))
# Nur vollständige Sprachen werden zum Paket (mind. 98 % der fertigen Einträge übersetzt). Halbfertige bleiben draußen
# und kommen beim nächsten Bauen automatisch dazu.
_done = sum(1 for d in docs if d.get("kind") is None and d.get("status") == "done") or 1
LANGS = {l: CATALOG[l] for l in CATALOG if _cnt[l] / _done >= 0.98}
for l in CATALOG:
    if _cnt[l] and l not in LANGS: print(f"noch nicht vollständig, kein Paket: {CATALOG[l]} ({_cnt[l]}/{_done})")
print("Sprachpakete:", ", ".join(f"{l} ({_cnt[l]})" for l in LANGS))
core = []; packs = {l: {"overlay": {}, "docs": []} for l in LANGS}
def codes_in(id_):
    parts = re.split(r"[-]", id_)[1:]
    return [p for p in parts if p in LANGS]
for d in docs:
    kind = d.get("kind")
    if kind is None:  # Eintrag
        c = {k:v for k,v in d.items() if k not in CATALOG and k not in ("conj","nb","quiz","nbCur","nbGap","nbGapFrom")}
        conj = d.get("conj"); nb = d.get("nb") or {}; quiz = d.get("quiz")
        if isinstance(conj, dict): c["conj"] = {k:v for k,v in conj.items() if k not in CATALOG}
        elif "conj" in d: c["conj"] = conj
        if nb: c["nb"] = {"de": {k:v for k,v in (nb.get("de") or {}).items() if k not in CATALOG}} if "de" in nb else {}
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
    elif kind == "settings":
        # Grundeinstellung der App: Deutsch als Ausgangssprache, Standardsprachen in fester Reihenfolge
        x = {k:v for k,v in d.items() if k not in ("srcLang",)}
        x["langs"] = list(DEFAULT); x["srcLang"] = "de"
        core.append(x)
    elif kind == "section":
        core.append(d)
    else:
        cs = codes_in(d["id"])
        if not cs: core.append(d); continue
        x = dict(d)
        if len(cs) > 1: x["__req"] = cs[1:]
        packs[cs[0]]["docs"].append(x)
os.makedirs(OUT, exist_ok=True)
import hashlib
def chash(obj):
    # Version = Fingerabdruck des Inhalts: Nur geänderte Pakete werden auf den Geräten neu geladen, und zwar als
    # vollständige, frisch gebaute Datei (keine angehängten Änderungen)
    return hashlib.sha1(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",",":")).encode()).hexdigest()[:12]
def dump(name, obj):
    s = json.dumps(obj, ensure_ascii=False, separators=(",",":"))
    open(os.path.join(OUT, name), "w").write(s)
    return len(s.encode()), len(gzip.compress(s.encode()))
sizes = {}
core_v = chash(core)
sizes["core"] = dump("core.json", {"version": core_v, "docs": core})
index = {"version": 2, "core": {"file": "core.json", "version": core_v, "bytes": sizes["core"][0]}, "packs": []}
for l, p in packs.items():
    p.update({"lang": l, "name": LANGS[l]}); p["version"] = chash(p)
    b = dump(f"lang-{l}.json", p); sizes[l] = b
    # Als Ausgangssprache wählbar, wenn fast alle Einträge eine fertige Fassung haben und die Oberfläche übersetzt ist
    n_all = sum(1 for d in docs if d.get("kind") is None and d.get("status") == "done")
    n_src = sum(1 for d in docs if d.get("kind") is None and d.get("status") == "done" and isinstance((d.get("nb") or {}).get(l), dict))
    has_ui = any(d.get("kind") == "ui" and d.get("lang") == l and len(d.get("pairs") or []) >= 300 for d in docs)
    src_ok = bool(n_all) and n_src / n_all >= 0.95 and has_ui
    print(f"Ausgangssprache {l}: {n_src}/{n_all} Fassungen, Oberfläche {'ja' if has_ui else 'nein'} -> {'wählbar' if src_ok else 'noch nicht'}")
    index["packs"].append({"lang": l, "name": LANGS[l], "file": f"lang-{l}.json", "version": p["version"], "default": l in DEFAULT, "src": src_ok, "bytes": b[0], "entries": len(p["overlay"]), "docs": len(p["docs"])})
json.dump(index, open(os.path.join(OUT, "packs.json"), "w"), ensure_ascii=False, indent=1)
for k, (a, g) in sizes.items(): print(f"{k:5} {a/1e6:6.2f} MB  gzip {g/1e6:5.2f} MB")

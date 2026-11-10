"""Erzeugt aus dem Datenbank-Export die Standarddaten (core.json) und je Sprache ein Paket (lang-xx.json)."""
import json, glob, os, sys, gzip, re
SRC_DIR = sys.argv[1]; OUT = sys.argv[2]
# Alle Sprachen, die Fraxx kennt (wie CATALOG in der App). Ein Paket entsteht automatisch für jede Sprache,
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
# Aufräumen wie die App beim Start (sonst schreibt die Web-App diese Korrekturen bei jedem Nutzer in „Meine Daten“):
# Wörter, die keine Verben sein können, verlieren die Verb-Markierung; leere „Weitere“-Unterbereiche fallen weg
SECS = {d["id"]: d for d in docs if d.get("kind") == "section"}
GRAM_POS = {"pron", "prep", "konj"}
def _top(sec):
    while sec and sec.get("parent") and sec["parent"] in SECS: sec = SECS[sec["parent"]]
    return sec
def no_verb_here(d):
    t = (d.get("de") or "").strip()
    if re.match(r"^(der|die|das|ein|eine)\s", t, re.I): return True
    if d.get("pos") in ("adj", "noun") or d.get("pos") in GRAM_POS: return True
    ids = [d.get("section")] + list(d.get("also") or [])
    for i, sid in enumerate(ids):
        sec = SECS.get(sid)
        if not sec: continue
        tt = ((_top(sec) or {}).get("title") or "").strip().lower()
        if tt == "adjektive" or (i == 0 and tt == "substantive") or (sec.get("title") or "").strip().lower() == "farben": return True
    return False
_fixed = 0
for d in docs:
    if d.get("kind") is None and d.get("verb") is True and no_verb_here(d):
        d.update({"verb": False, "conj": None, "conjFor": "", "conjStatus": ""}); _fixed += 1
# „Weitere“ unter Substantive / Wortschatz nach Themen auflösen (wie undoWeitere in der App)
for top in [x for x in SECS.values() if not x.get("parent") and (x.get("title") or "").strip().lower() in ("substantive", "wortschatz nach themen")]:
    for w in [x for x in SECS.values() if x.get("parent") == top["id"] and (x.get("title") or "").strip().lower() == "weitere"]:
        for d in docs:
            if d.get("kind") is None and d.get("section") == w["id"]:
                also = [x for x in (d.get("also") or []) if x != w["id"] and x in SECS]
                if also: d["section"] = also[-1]; d["also"] = also[:-1]
            elif d.get("kind") is None and w["id"] in (d.get("also") or []):
                d["also"] = [x for x in d["also"] if x != w["id"]]
_used = {d.get("section") for d in docs if d.get("kind") is None} | {x for d in docs if d.get("kind") is None for x in (d.get("also") or [])}
_drop = {i for i, sdoc in SECS.items() if (sdoc.get("title") or "").strip() == "Weitere" and sdoc.get("parent") and i not in _used and not any(x.get("parent") == i for x in SECS.values())}
docs = [d for d in docs if d.get("id") not in _drop]
# Doppelte Einträge zusammenführen (wie „Zusammenführen“ in der App), sonst meldet die Web-App sie bei jedem neuen Nutzer.
# Pronomen u. ä. unterscheiden Groß-/Kleinschreibung („ihnen“/„Ihnen“).
import unicodedata
def _nd(t, keepcase=False):
    t = unicodedata.normalize("NFC", t or "")
    if not keepcase: t = t.lower()
    return re.sub(r"\s+", " ", re.sub(r'[.!?,;:¿¡"„“”«»]+', "", t)).strip()
_groups = {}
for d in docs:
    if d.get("kind") is not None: continue
    o = d.get("orig") or "de"
    t = d.get("de", "") if o == "de" else ((d.get(o) or {}).get("text") or d.get("de", ""))
    k = _nd(t, d.get("pos") in GRAM_POS)
    if k: _groups.setdefault(o + "|" + k, []).append(d)
_gone = set()
for g in _groups.values():
    if len(g) < 2: continue
    keep = sorted(g, key=lambda e: (-(1 if e.get("conj") else 0), -(1 if e.get("status") == "done" else 0), e.get("createdAt") or 0))[0]
    secs = list(keep.get("also") or []); quiz = dict(keep.get("quiz") or {})
    for e in g:
        if e is keep: continue
        for x in [e.get("section")] + list(e.get("also") or []):
            if x and x != keep.get("section") and x in SECS and x not in secs: secs.append(x)
        for c, n in (e.get("quiz") or {}).items(): quiz[c] = max(quiz.get(c, 0), n or 0)
        _gone.add(e["id"])
    keep["also"] = secs
    if quiz: keep["quiz"] = quiz
docs = [d for d in docs if d.get("id") not in _gone]
print("doppelte Einträge zusammengeführt:", len(_gone))
# Anleitung ohne API-Schlüssel: vorhandene Übersetzungen des geänderten Satzes übernehmen
for d in docs:
    if d.get("kind") != "ui" or not isinstance(d.get("pairs"), list): continue
    for p in d["pairs"]:
        if isinstance(p, list) and len(p) == 2 and "Sprachpakete, API-Schlüssel und Sicherungen" in p[0]:
            p[0] = p[0].replace("Sprachpakete, API-Schlüssel und Sicherungen", "Sprachpakete und Sicherungen")
            p[1] = re.sub(r",\s[^,]*API[^,]*?\s(and|y|et|e|og|en|i|och)\s", r" \1 ", p[1])
# Hinweis der Testversion (eigene Übersetzungen noch nicht freigeschaltet) in allen Oberflächen
UI_EXTRA = {"Eigene Übersetzungen sind in dieser Testversion noch nicht freigeschaltet. Sie kommen in einer späteren Version.": {
  "en": "Your own translations are not yet enabled in this test version. They will come in a later version.",
  "fr": "Les traductions personnelles ne sont pas encore activées dans cette version de test. Elles arriveront dans une version ultérieure.",
  "it": "Le traduzioni personali non sono ancora attive in questa versione di prova. Arriveranno in una versione successiva.",
  "es": "Las traducciones propias aún no están activadas en esta versión de prueba. Llegarán en una versión posterior.",
  "pt": "As traduções próprias ainda não estão ativadas nesta versão de teste. Chegarão numa versão posterior.",
  "nl": "Eigen vertalingen zijn in deze testversie nog niet ingeschakeld. Ze komen in een latere versie.",
  "pl": "Własne tłumaczenia nie są jeszcze włączone w tej wersji testowej. Pojawią się w późniejszej wersji.",
  "sv": "Egna översättningar är ännu inte aktiverade i den här testversionen. De kommer i en senare version.",
  "nb": "Egne oversettelser er ennå ikke aktivert i denne testversjonen. De kommer i en senere versjon."}}
for d in docs:
    if d.get("kind") != "ui" or not isinstance(d.get("pairs"), list): continue
    have = {p[0] for p in d["pairs"] if isinstance(p, list)}
    for k, tr in UI_EXTRA.items():
        if k not in have and d.get("lang") in tr: d["pairs"].append([k, tr[d["lang"]]])
print("Verb-Markierung korrigiert:", _fixed, "· leere Unterbereiche entfernt:", len(_drop))
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
    elif kind == "tutorial":
        continue  # Anleitung: wird von publish.py als eigene Seite gebaut, nicht in die Sprachpakete
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

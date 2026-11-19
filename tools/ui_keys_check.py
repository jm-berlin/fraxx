"""Findet feste Oberflächentexte im Artefakt, die in UI_KEYS fehlen (sonst bleiben sie in der Web-App deutsch).

    python3 tools/ui_keys_check.py <redewendungen.html> <ausgabe.json>

Texte, die erst per JavaScript entstehen, findet es nicht: die von Hand in UI_KEYS eintragen.
"""
import json, re, sys
from html.parser import HTMLParser
src = open(sys.argv[1]).read()
i = src.index("const UI_KEYS = ")+16; j = src.index("];\n", i)+1; K = set(json.loads(src[i:j]))
body = src[src.index("<header"):]
body = re.sub(r"<script\b.*?</script>", "", body, flags=re.S)
NAMES = ["Deutsch"]
m = re.search(r"const CATALOG = (\[.*?\]);\n", src, re.S)
try:
    NAMES += [x[1] for x in json.loads(m.group(1))]
except Exception as e: pass
NAMES.sort(key=len, reverse=True)
NAME_RE = re.compile(r"(?<![^\W\d_])(" + "|".join(map(re.escape, NAMES)) + r")(?![^\W\d_])")
def tmpl(s):
    q = []; 
    def fq(mm): q.append(1); return "„{q%s}“" % chr(64+len(q))
    k = re.sub(r"„([^“]*)“", fq, s)
    L = []
    def fl(mm): L.append(1); return "{L%s}" % chr(64+len(L))
    k = NAME_RE.sub(fl, k)
    n = []
    def fn(mm): n.append(1); return "{n%s}" % chr(64+len(n))
    k = re.sub(r"\d[\d.,:]*", fn, k)
    return k
SKIPTAG = {"style","script","svg","textarea","h1"}
SKIPCLS = {"tx","detx","note","renamer","deinput","flagimg","gin","gramnav","qword","conj","seccount","dname","dtr","dtext"}
VOID = {"br","img","input","meta","link","hr","source","wbr","col","area","base","param","track","embed"}
class P(HTMLParser):
    def __init__(s): super().__init__(convert_charrefs=True); s.st=[]; s.out=[]; s.html=None; s.depth=0
    def handle_starttag(s, t, a):
        a = dict(a); skip = t in SKIPTAG or "data-notr" in a or bool(SKIPCLS & set((a.get("class") or "").split()))
        if t in ("input","textarea") or "data-notr" in a: pass
        for at in ("title","placeholder","aria-label"):
            if a.get(at) and not (s.st and s.st[-1]) and not "data-notr" in a: s.out.append(a[at])
        if t in VOID: return
        s.st.append(skip or (bool(s.st) and s.st[-1]))
    def handle_endtag(s, t):
        if t in VOID: return
        if s.st: s.st.pop()
    def handle_data(s, d):
        if s.st and s.st[-1]: return
        if d.strip() and re.search(r"[^\W\d_]", d): s.out.append(d)
p = P(); p.feed(body)
miss = []
for t in p.out:
    k = tmpl(t.strip())
    if not re.search(r"[^\W\d_]", re.sub(r"\{[qLn][A-Z]\}", "", k)): continue
    if k not in K and k not in miss: miss.append(k)
print(len(miss))
json.dump(miss, open(sys.argv[2], "w"), ensure_ascii=False, indent=0)

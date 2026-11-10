"""Neuer App-Name: Phraxx → Fraxx (Wortmarke ohne „H“, Buchstabe F statt P, Icon mit F).
Wird von build_app.py auf die Artefakt-Datei angewandt, solange das Artefakt noch „Phraxx“ heißt,
und lässt sich auf andere Textdateien anwenden:  python3 tools/rename_fraxx.py <datei> …"""
import re, sys

OLD_URL, NEW_URL = "jm-berlin.github.io/phraxx", "jm-berlin.github.io/fraxx"
OLD_REPO, NEW_REPO = "jm-berlin/phraxx", "jm-berlin/fraxx"

_P_BOWL = re.compile(r'<path d="M10\.90 10\.90 L37\.00 10\.90 A20\.10 20\.10 0 0 1 37\.00 51\.10 L10\.90 51\.10"( [^>]*)/>')
_H = [re.compile(r'<path d="M98\.90 10\.90 L98\.90 89\.10"[^>]*/>'), re.compile(r'<path d="M147\.10 10\.90 L147\.10 89\.10"[^>]*/>'),
      re.compile(r'<path d="M98\.90 50\.00 L147\.10 50\.00"[^>]*/>')]
_NUM = re.compile(r'(?<![\d.])(\d+\.\d+)')

def _logo(m):
    svg = m.group(0)
    if 'viewBox="0 0 540.0 100"' not in svg: return svg
    svg = _P_BOWL.sub(lambda b: f'<path d="M57.10 10.90 L10.90 10.90 M10.90 50.00 L47.00 50.00"{b.group(1)}/>', svg)
    for h in _H: svg = h.sub("", svg)
    # R, A, X, X um die Breite des weggefallenen H nach links
    def shift(p):
        d = p.group(1)
        xs = [float(x) for x in re.findall(r'[ML] ?(\d+\.\d+)', d)]
        if not xs or min(xs) < 180: return p.group(0)
        nd = re.sub(r'([MLA]) ?(\d+\.\d+) (\d+\.\d+)', lambda q: f'{q.group(1)}{float(q.group(2)) - 90:.2f} {q.group(3)}' if q.group(1) != "A" else q.group(0), d)
        nd = re.sub(r'(0 0 1 )(\d+\.\d+)', lambda q: f'{q.group(1)}{float(q.group(2)) - 90:.2f}', nd)
        return p.group(0).replace(d, nd)
    svg = re.sub(r'<path d="([^"]+)"', shift, svg)
    return svg.replace('viewBox="0 0 540.0 100"', 'viewBox="0 0 450.0 100"')

_ICON_BOWL = 'd="M190.4 145.0 L264.5 145.0 A57.0 57.0 0 0 1 264.5 259.1 L190.4 259.1"'
_ICON_F = 'd="M321.5 145.0 L190.4 145.0 M190.4 250.0 L292.0 250.0"'

def convert(s):
    s = re.sub(r'<svg[^>]*viewBox="0 0 540\.0 100".*?</svg>', _logo, s, flags=re.S)
    s = s.replace(_ICON_BOWL, _ICON_F)
    s = s.replace(OLD_URL, NEW_URL).replace("github.com/" + OLD_REPO, "github.com/" + NEW_REPO)
    s = s.replace("icons/phraxx.svg", "icons/fraxx.svg")
    s = s.replace("Phraxx", "Fraxx").replace("PHRAXX", "FRAXX").replace("PX Admin", "FX Admin")
    return s

if __name__ == "__main__":
    for f in sys.argv[1:]:
        t = open(f, encoding="utf-8").read(); n = convert(t)
        if n != t: open(f, "w", encoding="utf-8").write(n); print("geändert:", f)

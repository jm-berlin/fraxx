import markdown,re,sys
from playwright.sync_api import sync_playwright
S='/tmp/claude-0/-home-claude/2ad5d760-ad6f-557c-9e99-6e8f89c257dc/scratchpad/'
R='/home/claude/multilingo/'
JOBS=[("INSTALLATION.md","Fraxx-Installation","de","Schritt für Schritt","Fraxx <em>installieren</em>","Seite","Adresse"),
      ("INSTALL.md","Fraxx-Install-Guide","en","Step by step","Install <em>Fraxx</em>","Page","Address")]
CSS='''
@page{size:A4;margin:12mm 0 14mm}
:root{--bg:#e5e2e0;--surface:#f3f1ef;--ink:#141212;--muted:#6b635d;--line:#d3ccc6;--hl:#a3395f;--hl-soft:#efd5df;--chip:#e5e2e0}
html{background:var(--bg);-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0;padding:0 13mm;font-family:Inter,system-ui,sans-serif;color:var(--ink);font-size:9.8pt;line-height:1.55}
.top{display:flex;justify-content:space-between;align-items:center;margin:0 1mm 5mm}
.mark{font-weight:900;font-size:24pt;letter-spacing:-.055em;line-height:1}
.url{font-size:8.5pt;font-weight:600;background:var(--hl);color:#fff;padding:1.6mm 4mm;border-radius:99px}
.card{background:var(--surface);border-radius:7mm;padding:7mm 8mm;margin:0 0 4.5mm;box-shadow:0 1px 2px rgb(40 30 25 / .05)}
.hero{padding:10mm 10mm 9mm}
.eyebrow{font-size:7.6pt;font-weight:700;letter-spacing:.16em;text-transform:uppercase;margin:0 0 3mm}
h1{font-size:30pt;line-height:1.02;letter-spacing:-.035em;font-weight:800;margin:0 0 5mm}
h1 em{font-style:normal;color:var(--hl)}
.hero p{color:var(--muted);font-size:11pt;line-height:1.6;margin:0 0 3mm;max-width:150mm}
.hero p strong{color:var(--ink)}
.herogrid{display:flex;gap:8mm;align-items:flex-start;justify-content:space-between}
.qr{flex:none;width:36mm;text-decoration:none;text-align:center;color:var(--muted);font-size:7.6pt;line-height:1.3}
.qr svg{display:block;width:36mm;height:36mm;border-radius:3mm;margin-bottom:1.6mm}
.addr{display:flex;align-items:center;gap:4mm;flex-wrap:wrap;margin:5mm 0 0}
.addr a.go{background:var(--hl);color:#fff;text-decoration:none;font-weight:700;font-size:11pt;padding:2.8mm 6mm;border-radius:99px}
.addr a.link{color:var(--ink);font-weight:600;font-size:10.5pt;text-decoration:underline;text-decoration-color:var(--hl);text-underline-offset:2px}
.hero p.tip{margin:3.5mm 0 0;font-size:8.6pt;color:var(--muted)}
.sec{break-inside:avoid}
.sub h3{margin-top:0}
h2{display:flex;align-items:center;gap:3.5mm;font-size:15pt;letter-spacing:-.02em;margin:0 0 4mm;break-after:avoid}
h2 .n{flex:none;width:9mm;height:9mm;border-radius:50%;background:var(--hl);color:#fff;font-size:10.5pt;font-weight:700;display:flex;align-items:center;justify-content:center}
h3{font-size:10.6pt;margin:5mm 0 2mm;break-after:avoid}
h3:first-of-type{margin-top:0}
p{margin:0 0 2.5mm}
ol{list-style:none;counter-reset:s;padding:0;margin:0 0 3mm}
ol>li{counter-increment:s;position:relative;padding-left:8.5mm;margin:0 0 1.8mm;break-inside:avoid}
ol>li::before{content:counter(s);position:absolute;left:0;top:.2mm;width:5.6mm;height:5.6mm;border-radius:50%;background:var(--chip);font-size:7.8pt;font-weight:700;display:flex;align-items:center;justify-content:center}
ul{padding-left:5mm;margin:1.2mm 0 2mm} ul li{margin:.8mm 0} ul li::marker{color:var(--hl)}
li ul{margin-top:1mm}
blockquote{margin:3.5mm 0 0;padding:3.2mm 4.5mm;background:var(--hl-soft);border-radius:4mm;break-inside:avoid}
blockquote p{margin:0}
blockquote strong{color:var(--hl)}
table{border-collapse:separate;border-spacing:0;width:100%;font-size:9.2pt}
th{background:var(--ink);color:#f3f1ef;text-align:left;padding:2.4mm 3.2mm;font-weight:600}
th:first-child{border-radius:3mm 0 0 0} th:last-child{border-radius:0 3mm 0 0}
td{padding:2.4mm 3.2mm;border-bottom:.5pt solid var(--line);vertical-align:top}
td:first-child{font-weight:600;width:38%}
tr{break-inside:avoid}
a{color:var(--ink)}
'''
def build(src,out,lang,eyebrow,title,pg,addrlabel):
    md=open(R+src).read()
    md=re.sub(r'^> (English version|Deutsche Fassung):.*\n','',md,flags=re.M)
    md=re.sub(r'^# .*\n','',md,count=1,flags=re.M)
    parts=[p.strip() for p in re.split(r'^---\s*$',md,flags=re.M)]
    intro=parts[0]; secs=parts[1:]
    m=re.search(r'\*\*[^*]+:\*\*\s*(\S+)',intro); url=m.group(1)
    intro=re.sub(r'^\*\*[^*]+:\*\*.*$','',intro,flags=re.M).strip()
    de = lang == "de"
    qr = open(S+'qr.svg').read()
    hero=(f'<div class="card hero"><div class="herogrid"><div><p class="eyebrow">{eyebrow}</p><h1>{title}</h1>{markdown.markdown(intro)}</div>'
          f'<a class="qr" href="{url}">{qr}<span>{"Mit der Handykamera scannen" if de else "Scan with your phone camera"}</span></a></div>'
          f'<div class="addr"><a class="go" href="{url}">{"Fraxx öffnen" if de else "Open Fraxx"} →</a>'
          f'<a class="link" href="{url}">{url}</a></div>'
          f'<p class="tip">{"Tippe oder klicke auf den Knopf: Fraxx öffnet sich direkt im Browser. Danach geht es mit Schritt 1 weiter." if de else "Tap or click the button: Fraxx opens directly in your browser. Then continue with step 1."}</p></div>')
    cards=[]
    for s in secs:
        h=markdown.markdown(s,extensions=['tables'])
        def h2(m):
            t=m.group(1); mm=re.match(r'(\d+)\.\s*(.*)',t)
            n,tt=(mm.group(1),mm.group(2)) if mm else ('?',t)
            return f'<h2><span class="n">{n}</span>{tt}</h2>'
        h=re.sub(r'<h2>(.*?)</h2>',h2,h)
        if h.count('<h3>')>2:
            head,*rest=re.split(r'(?=<h3>)',h)
            last=rest[-1]; bq=''
            if '<blockquote>' in last: last,bq=last.split('<blockquote>',1); bq='<blockquote>'+bq; rest[-1]=last
            cards.append(f'<section class="card sec sub">{head}{rest[0]}</section>')
            for r in rest[1:-1]: cards.append(f'<section class="card sec sub">{r}</section>')
            cards.append(f'<section class="card sec sub">{rest[-1]}{bq}</section>')
        else:
            cards.append(f'<section class="card sec">{h}</section>')
    html=f'<!doctype html><html lang="{lang}"><meta charset="utf-8"><title>{out}</title><style>{CSS}</style><body><div class="top"><div class="mark">Fraxx</div><div class="url">{"Testversion" if lang=="de" else "Test version"}</div></div>{hero}{"".join(cards)}</body></html>'
    open(S+out+'.html','w').write(html)
    return pg
with sync_playwright() as p:
    b=p.chromium.launch(); page=b.new_page()
    for j in JOBS:
        pgw=build(*j)
        page.goto("file://"+S+j[1]+".html"); page.wait_for_timeout(300)
        page.pdf(path=S+j[1]+".pdf",prefer_css_page_size=True,print_background=True,display_header_footer=True,header_template='<div style="-webkit-print-color-adjust:exact;print-color-adjust:exact;background:#e5e2e0;position:fixed;left:0;right:0;top:0;height:12mm"></div>',
          footer_template=f'<div style="-webkit-print-color-adjust:exact;print-color-adjust:exact;background:#e5e2e0;position:fixed;left:0;right:0;bottom:0;height:14mm;padding-top:4mm;box-sizing:border-box;font-family:Inter,sans-serif;font-size:7.5pt;color:#6b635d;width:100%;text-align:center">Fraxx · {pgw} <span class="pageNumber"></span> / <span class="totalPages"></span></div>')
    b.close()

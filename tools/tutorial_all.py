"""Anleitung für alle vorhandenen Sprachen neu bauen: Screenshots aus der gebauten Web-App, HTML und PDF.

    python3 tools/tutorial_all.py [sprachen …]     (ohne Angabe: Deutsch + alle in tools/tutorial-texts/)

Läuft im Repository-Ordner; startet dafür kurz einen lokalen Webserver. Wird von publish.py aufgerufen,
Fehler hier brechen die Veröffentlichung nie ab.
"""
import http.server, json, os, shutil, socketserver, subprocess, sys, tempfile, threading
from playwright.sync_api import sync_playwright

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TXT = os.path.join(REPO, "tools", "tutorial-texts")
OUT = os.path.join(REPO, "anleitung")

def serve():
    h = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=REPO, **k)
    http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
    srv = socketserver.TCPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"

def main():
    langs = sys.argv[1:]
    if not langs:
        langs = ["de"] + (sorted(f[:-5] for f in os.listdir(TXT) if f.endswith(".json") and f != "de.json") if os.path.isdir(TXT) else [])
    srv, base = serve()
    done = []
    try:
        for l in langs:
            shots = tempfile.mkdtemp(prefix=f"tut-{l}-")
            try:
                r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "tutorial_shots.py"), l, shots, base], capture_output=True, text=True, timeout=600)
                if r.returncode != 0: print("Screenshots", l, "fehlgeschlagen:", r.stderr[-800:]); continue
                r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "build_tutorial.py"), shots, OUT, l], capture_output=True, text=True, timeout=300)
                if r.returncode != 0: print("Anleitung", l, "fehlgeschlagen:", r.stderr[-800:]); continue
                page = "index.html" if l == "de" else f"{l}.html"
                pdf = "Multilingo-Anleitung.pdf" if l == "de" else f"Multilingo-Anleitung-{l}.pdf"
                with sync_playwright() as p:
                    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1280, "height": 900})
                    pg.goto(base + "anleitung/" + page + "?print=1"); pg.wait_for_timeout(1500)
                    pg.pdf(path=os.path.join(OUT, pdf), format="A4", print_background=True); b.close()
                done.append(l)
            finally:
                shutil.rmtree(shots, ignore_errors=True)
    finally:
        srv.shutdown()
    print("ANLEITUNG:", ", ".join(done) or "nichts gebaut")

if __name__ == "__main__":
    main()

from playwright.sync_api import sync_playwright
D='shots/'
with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
    ctx = b.new_context(viewport={"width":1280,"height":820}, device_scale_factor=2)
    ctx.add_init_script("try{localStorage.setItem('rw-design','taupe-beere'); localStorage.setItem('rw-mode','light')}catch(e){}")
    pg = ctx.new_page(); errs=[]; pg.on("pageerror",lambda e: errs.append(str(e)))
    def fresh():
        pg.goto("http://localhost:8765/"); pg.wait_for_timeout(1500)
        if pg.locator("#mlsrc").count(): pg.locator("#mlsrc button",has_text="Deutsch").click()
        pg.wait_for_timeout(5000)
        if pg.locator("#mlupd").count(): pg.locator("#mlupd .n").click()
    fresh()
    # Thema öffnen über Inhalt
    pg.click("#tocbtn"); pg.wait_for_timeout(1200)
    pg.click("#toc >> text=Redewendungen nach Themen"); pg.wait_for_timeout(800)
    pg.screenshot(path=D+"03-inhalt.png")
    card = pg.locator("#tocnav .toccard", has_text="Restaurant").first
    if not card.count(): card = pg.locator("#tocnav .toccard").nth(3)
    print("card:", card.inner_text()[:40].replace("\n"," "))
    card.locator("text=Öffnen").first.click(); pg.wait_for_timeout(2500)
    pg.screenshot(path=D+"04-tabelle.png")
    # Konjugation: Verben-Reiter
    fresh(); pg.click("#tocbtn"); pg.wait_for_timeout(1000)
    print("verben"); pg.click("#tocposf >> text=Verben"); pg.wait_for_timeout(2500)
    kb = pg.locator("button:visible", has_text="Konjugation").first
    print("kb", kb.count())
    if kb.count(): kb.click(); pg.wait_for_timeout(1500)
    pg.screenshot(path=D+"04b-konjugation.png")
    for name, btn, close, extra in [("06-grammatik","#grambtn","#gramclose",None),("06b-fehler","#grambtn","#gramclose","Typische Fehler"),("06c-verben","#grambtn","#gramclose","Verben & Endungen"),
                                    ("07-speisekarte","#dishbtn","#dishclose",None),("08-spick","#favbtn","#favclose",None),("09-quiz","#quizbtn","#quizclose",None)]:
        fresh(); pg.click(btn); pg.wait_for_timeout(2500)
        if extra: pg.click(f"text={extra} >> nth=0"); pg.wait_for_timeout(2000)
        pg.screenshot(path=D+name+".png")
    fresh(); pg.click("#helpbtn"); pg.wait_for_timeout(1200); pg.screenshot(path=D+"10-hilfe.png")
    fresh(); pg.click("#setbtn"); pg.wait_for_timeout(600); pg.click(".mlsetbtn"); pg.wait_for_timeout(1500); pg.screenshot(path=D+"12-appdaten.png")
    print(errs[:3]); ctx.close()
    # Handy
    ctx = b.new_context(viewport={"width":390,"height":844}, device_scale_factor=3, is_mobile=True, has_touch=True)
    ctx.add_init_script("try{localStorage.setItem('rw-design','taupe-beere'); localStorage.setItem('rw-mode','light'); localStorage.setItem('ml-src','de')}catch(e){}")
    pg = ctx.new_page(); fresh(); pg.screenshot(path=D+"11-mobile-home.png")
    pg.click("#tocbtn"); pg.wait_for_timeout(1000); pg.click("#toc >> text=Redewendungen nach Themen"); pg.wait_for_timeout(600)
    pg.locator("#tocnav .toccard", has_text="Restaurant").first.locator("text=Öffnen").first.click(); pg.wait_for_timeout(2500)
    pg.screenshot(path=D+"11b-mobile-karte.png")
    ctx.close(); b.close()

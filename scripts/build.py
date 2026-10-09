#!/usr/bin/env python3
"""Build the presentation website (docs/) from the Claude Slides export (source/).

Usage:
  python3 scripts/build.py            build docs/
  python3 scripts/build.py --check    check source/ only, write nothing
Settings: scripts/site.json
"""
import glob, hashlib, html, json, math, os, re, shutil, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, OUT, SCR = f"{ROOT}/source", f"{ROOT}/docs", f"{ROOT}/scripts"
CFG = json.load(open(f"{SCR}/site.json"))

ICONS = {"Activity": "activity", "Book": "book", "Chart": "chart-column", "Chat": "message-circle",
         "CheckCircle": "circle-check", "Link": "link", "PaperPlane": "send", "Search": "search", "Tool": "wrench"}
FONTS = [("Montserrat", "montserrat", (500, 600, 700, 800)), ("Figtree", "figtree", (400, 500, 600, 700))]


def fail(msg):
    print("ERROR:", msg); sys.exit(1)


def load_source():
    deck = json.load(open(f"{SRC}/deck.json"))
    slides = {}
    for sid in deck["order"]:
        f = f"{SRC}/slides/{sid}.html"
        if not os.path.exists(f):
            fail(f"slide {sid} is in deck.json but source/slides/{sid}.html is missing")
        slides[sid] = open(f).read().strip()
    assets = {os.path.splitext(os.path.basename(f))[0]: os.path.basename(f) for f in glob.glob(f"{SRC}/assets/*")}
    for sid, s in slides.items():
        for bid in re.findall(r"/_blob/([0-9a-f]{32})", s):
            if bid not in assets:
                fail(f"slide {sid} uses asset {bid}, which is not in source/assets/")
        for name in re.findall(r'<x-icon[^>]*name="([A-Za-z]+)"', s):
            if name not in ICONS:
                fail(f"slide {sid} uses icon {name}; add it to ICONS and scripts/vendor/icons/")
    for sid in CFG["live"]:
        if sid not in slides:
            fail(f"live slide {sid} (scripts/site.json) is not in the deck")
    return deck, slides, assets


def icon(m):
    a = m.group(1)
    name = re.search(r'name="([A-Za-z]+)"', a).group(1)
    st = (re.search(r'style="([^"]*)"', a) or [None, ""])[1]
    inner = re.search(r"<svg[^>]*>(.*)</svg>", open(f"{SCR}/vendor/icons/{ICONS[name]}.svg").read(), re.S).group(1).strip()
    return (f'<svg class="xi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" style="{st}">{inner}</svg>')


def connector(m):
    a = m.group(1)
    g = lambda k, d=None: (re.search(rf'\b{k}="([^"]*)"', a) or [None, d])[1]
    x1, y1, x2, y2 = (float(g(k)) for k in ("x1", "y1", "x2", "y2"))
    head, st = g("head", "end"), g("style", "")
    col = (re.search(r"color:\s*([^;]+)", st) or [None, "#141414"])[1].strip()
    w = float((re.search(r"border-width:\s*([\d.]+)", st) or [None, "2"])[1])
    dash = ""
    if "dashed" in st: dash = f' stroke-dasharray="{w*3} {w*2}"'
    elif "dotted" in st: dash = f' stroke-dasharray="0 {w*2}"'
    L = math.hypot(x2 - x1, y2 - y1) or 1
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    hl = 4 * w + 8
    def tip(px, py, dx, dy):
        bx, by = px - dx * hl, py - dy * hl
        nx, ny = -dy * hl * .55, dx * hl * .55
        return f'<polygon points="{px},{py} {bx+nx},{by+ny} {bx-nx},{by-ny}" fill="{col}"/>'
    heads, sx1, sy1, sx2, sy2 = "", x1, y1, x2, y2
    if head in ("end", "both"):
        heads += tip(x2, y2, ux, uy); sx2, sy2 = x2 - ux * hl * .8, y2 - uy * hl * .8
    if head == "both":
        heads += tip(x1, y1, -ux, -uy); sx1, sy1 = x1 + ux * hl * .8, y1 + uy * hl * .8
    return (f'<svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;left:0;top:0;width:1920px;height:1080px;pointer-events:none;overflow:visible">'
            f'<line x1="{sx1}" y1="{sy1}" x2="{sx2}" y2="{sy2}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"{dash}/>{heads}</svg>')


def px(st, k):
    m = re.search(rf"(?:^|[;\s]){k}:\s*(-?[\d.]+)px", st)
    return float(m.group(1)) if m else None


def make_live(sid, s, spec):
    """Replace the slide's demo panel (the pinned div at spec['panel'] left/top) with a live frame."""
    l, t = spec["panel"]
    for m in re.finditer(r'<div style="([^"]*)"', s):
        st = m.group(1)
        if px(st, "left") == l and px(st, "top") == t:
            w, h = px(st, "width"), px(st, "height")
            start = m.start()
            depth, i = 0, start
            for tag in re.finditer(r"<(/?)div\b[^>]*>", s[start:]):
                depth += -1 if tag.group(1) else 1
                if depth == 0:
                    end = start + tag.end(); break
            box = (f'<div class="live" data-live="{sid}" style="position:absolute;left:{l}px;top:{t}px;'
                   f'width:{w:g}px;height:{h:g}px;border-radius:16px"></div>')
            return s[:start] + box + s[end:]
    fail(f"live slide {sid}: no panel at left {l}px, top {t}px. Update scripts/site.json")


def build(deck, slides, assets):
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(f"{OUT}/assets"); os.makedirs(f"{OUT}/fonts")
    for f in assets.values():
        shutil.copy(f"{SRC}/assets/{f}", f"{OUT}/assets/{f}")
    ff = []
    for fam, key, ws in FONTS:
        for w in ws:
            name = f"{key}-latin-{w}-normal.woff2"
            shutil.copy(f"{SCR}/vendor/fonts/{name}", f"{OUT}/fonts/{name}")
            ff.append(f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{w};font-display:block;src:url(fonts/{name}) format('woff2')}}")
    keys = r"(SAY|DO NOT SAY|DO \(red box\)|DO|NOTE|MOTION|DISCLOSE|LIVE OPTION|STEP \d+|REPLACE LATER|QR|QUESTIONS|RECOVERY TIME|SAY if asked|Return|CLICKER ONLY|WITH A TRACKPAD|IF THE APP FAILS|IF NO TAB OPENS|PRESENT FROM THE WEBSITE COPY|BEFORE THE TALK)"
    out = []
    for sid in deck["order"]:
        s = slides[sid]
        if sid in CFG["live"]:
            s = make_live(sid, s, CFG["live"][sid])
        s = re.sub(r"<x-icon([^>]*)>\s*</x-icon>", icon, s)
        s = re.sub(r"<x-connector([^>]*)>\s*</x-connector>", connector, s)
        s = re.sub(r"/_blob/([0-9a-f]{32})", lambda m: "assets/" + assets[m.group(1)], s)
        head = re.match(r"<section\b[^>]*>", s).group(0)
        hidden = re.search(r'\shidden(?:="[^"]*")?(?=[\s>])', head) is not None
        newhead = re.sub(r'\shidden(?:="[^"]*")?(?=[\s>])', "", head)[:-1] + f' data-hidden="{1 if hidden else 0}">'
        s = newhead + s[len(head):]
        if CFG.get("notes") == "strip":
            s = re.sub(r"<aside>.*?</aside>", "<aside></aside>", s, flags=re.S)
        else:
            s = re.sub(r"<aside>(.*?)</aside>", lambda m: "<aside>" + re.sub(r"\s+(?=" + keys + r"[: ])", "\n", m.group(1)) + "</aside>", s, flags=re.S)
        out.append(s)
    digest = hashlib.sha1("".join(out).encode()).hexdigest()[:7]
    meta = {"order": deck["order"], "live": CFG["live"], "appLocal": CFG["appLocal"], "appOnline": CFG["appOnline"],
            "version": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()) + " · " + digest}
    page = open(f"{SCR}/player.html").read()
    page = (page.replace("{{TITLE}}", html.escape(CFG.get("title") or deck["title"]))
                .replace("{{FONTFACES}}", "\n".join(ff))
                .replace("{{SLIDES}}", "\n".join(out))
                .replace("{{META}}", json.dumps(meta)))
    open(f"{OUT}/index.html", "w").write(page)
    open(f"{OUT}/.nojekyll", "w").write("")
    json.dump({"name": CFG.get("title") or deck["title"], "short_name": CFG.get("shortName", "Deck"), "start_url": ".",
               "display": "fullscreen", "orientation": "landscape", "background_color": "#0d0d0d", "theme_color": "#E54B4B",
               "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                         {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}]},
              open(f"{OUT}/manifest.webmanifest", "w"))
    for n in (192, 512):
        shutil.copy(f"{SCR}/vendor/icon-{n}.png", f"{OUT}/icon-{n}.png")
    print(f"Built docs/ · {len(out)} slides · {len(assets)} images · notes: {CFG.get('notes')} · version {meta['version']}")


if __name__ == "__main__":
    deck, slides, assets = load_source()
    if "--check" in sys.argv:
        print(f"OK · {len(slides)} slides · {len(assets)} images"); sys.exit(0)
    build(deck, slides, assets)

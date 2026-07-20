#!/usr/bin/env python3
"""Render astroreeti carousel slides from a JSON spec via Playwright."""
import json, sys, pathlib
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).parent

DIVIDER = """<svg class="divider" viewBox="0 0 420 24" fill="none">
  <line x1="0" y1="12" x2="150" y2="12" stroke="#C19A49" stroke-width="2"/>
  <line x1="270" y1="12" x2="420" y2="12" stroke="#C19A49" stroke-width="2"/>
  <circle cx="210" cy="12" r="6" fill="#7A2323"/>
  <circle cx="180" cy="12" r="3.5" fill="#C19A49"/>
  <circle cx="240" cy="12" r="3.5" fill="#C19A49"/>
</svg>"""

MOON = """<svg class="icon-top" width="120" height="120" viewBox="0 0 120 120" fill="none">
  <circle cx="60" cy="60" r="44" stroke="#C19A49" stroke-width="2.5"/>
  <path d="M78 26 A44 44 0 1 0 78 94 A36 36 0 0 1 78 26 Z" fill="#7A2323"/>
  <circle cx="60" cy="60" r="52" stroke="#7A2323" stroke-width="1.2" stroke-dasharray="2 7"/>
</svg>"""

STAR = """<svg class="icon-top" width="90" height="90" viewBox="0 0 90 90" fill="none">
  <path d="M45 8 L52 38 L82 45 L52 52 L45 82 L38 52 L8 45 L38 38 Z" fill="#C19A49"/>
  <circle cx="45" cy="45" r="6" fill="#7A2323"/>
</svg>"""

ICONS = {"moon": MOON, "star": STAR, "": ""}

def slide_html(s):
    parts = []
    if s.get("icon"):
        parts.append(ICONS[s["icon"]])
    if s.get("eyebrow"):
        parts.append(f'<div class="eyebrow">{s["eyebrow"]}</div>')
    parts.append(DIVIDER)
    if s.get("h1"):
        parts.append(f'<h1>{s["h1"]}</h1>')
    if s.get("h2"):
        parts.append(f'<h2>{s["h2"]}</h2>')
    if s.get("sub"):
        parts.append(f'<div class="sub">{s["sub"]}</div>')
    if s.get("body"):
        parts.append(f'<div class="body">{s["body"]}</div>')
    if s.get("points"):
        pts = "".join(
            f'<div class="point"><div class="num">{i+1}</div><div class="pt">{p}</div></div>'
            for i, p in enumerate(s["points"]))
        parts.append(f'<div class="points">{pts}</div>')
    if s.get("handle"):
        parts.append(f'<div class="cta-handle">{s["handle"]}</div>')
    if s.get("swipe"):
        parts.append(f'<div class="swipe">{s["swipe"]}</div>')
    return "\n".join(parts)

def main(spec_path, outdir):
    spec = json.loads(pathlib.Path(spec_path).read_text())
    template = (BASE / "template.html").read_text()
    template = template.replace("url('fonts/", f"url('file://{BASE.resolve()}/fonts/")
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    n = len(spec["slides"])
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350})
        for i, s in enumerate(spec["slides"], 1):
            html = template.replace("<!--SLIDE-->", slide_html(s))
            html = html.replace("<!--PAGE-->", f"{i} / {n}")
            f = outdir / f"_slide{i}.html"
            f.write_text(html)
            page.goto(f"file://{f.resolve()}")
            page.wait_for_timeout(250)
            out = outdir / f"slide{i:02d}.jpg"
            page.screenshot(path=str(out), type="jpeg", quality=92)
            print("rendered", out)
        browser.close()
    for f in outdir.glob("_slide*.html"):
        f.unlink()

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

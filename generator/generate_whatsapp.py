#!/usr/bin/env python3
"""Render a single WhatsApp Channel post (1080x1080 image) from a JSON spec,
using one of 4 brand background variants (bg-1..bg-4), picked randomly unless
a --bg index is passed. Logo sits fixed top-left on every variant; text is
placed in the lower text-safe zone that stays clear of it.

Usage: generate_whatsapp.py <spec.json> <outdir> [--bg N]
spec.json: {"eyebrow": "...", "h1": "...", "body": "...", "handle": "@astroreeti"}
"""
import json, random, re, sys, pathlib
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).parent


def slot_html(s):
    parts = []
    if s.get("eyebrow"):
        parts.append(f'<div class="eyebrow">{s["eyebrow"]}</div>')
    if s.get("h1"):
        parts.append(f'<h1>{s["h1"]}</h1>')
    if s.get("body"):
        parts.append(f'<div class="body">{s["body"]}</div>')
    parts.append('<div class="divider"></div>')
    if s.get("handle"):
        parts.append(f'<div class="handle">{s["handle"]}</div>')
    return "\n".join(parts)


def main(spec_path, outdir, bg=None):
    spec = json.loads(pathlib.Path(spec_path).read_text())
    bg_idx = bg if bg is not None else random.randint(1, 4)
    template = (BASE / "template_whatsapp.html").read_text()
    template = template.replace("file://FONTDIR/", f"file://{(BASE / 'fonts').resolve()}/")
    template = template.replace("file://BGDIR/", f"file://{(BASE / 'backgrounds').resolve()}/")
    template = template.replace("BGCLASS", f"bg-{bg_idx}")
    template = template.replace("<!--SLOT-->", slot_html(spec))

    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    f = outdir / "_wa.html"
    f.write_text(template)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1080})
        page.goto(f"file://{f.resolve()}")
        page.wait_for_timeout(200)
        out = outdir / "whatsapp.jpg"
        page.screenshot(path=str(out), type="jpeg", quality=94)
        browser.close()
    f.unlink()
    print("rendered", out, "bg variant", bg_idx)


if __name__ == "__main__":
    args = sys.argv[1:]
    bg = None
    if "--bg" in args:
        i = args.index("--bg")
        bg = int(args[i + 1])
        del args[i:i + 2]
    main(args[0], args[1], bg)

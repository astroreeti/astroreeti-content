#!/usr/bin/env python3
"""Render an animated reel video (staggered text entrances, ambient star
twinkle, slow zoom, glowing frame pulse) from a JSON spec via Playwright
screen recording, then mux in the given audio track with ffmpeg.

Usage: generate_reel.py <spec.json> <outdir> <audio.mp3> [seconds_per_slide]
Writes <outdir>/reel.mp4 (1080x1920). For visual QA, extract still frames
from the finished video with ffmpeg, e.g.:
  ffmpeg -ss <seconds> -i reel.mp4 -frames:v 1 check.jpg
(no separate slide*.jpg stills are produced — everything is baked into the
animated video).
"""
import json, sys, pathlib, subprocess

from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).parent
sys.path.insert(0, str(BASE))
from generate import slide_html  # noqa: E402

W, H = 1080, 1920


def main(spec_path, outdir, audio, per_slide=4.0):
    per_slide = float(per_slide)
    assert per_slide >= 4.0, "each slide must stay on screen at least 4 seconds"
    spec = json.loads(pathlib.Path(spec_path).read_text())
    slides = spec["slides"]
    n = len(slides)
    assert n >= 2, "need at least 2 slides"
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    template = (BASE / "template_reel.html").read_text()
    template = template.replace("url('fonts/", f"url('file://{BASE.resolve()}/fonts/")

    slides_json = json.dumps([
        {"html": slide_html(s), "page": f"{idx + 1} / {n}"} for idx, s in enumerate(slides)
    ])
    html = template.replace("__SLIDES__", slides_json).replace("__PER_SLIDE_MS__", str(int(per_slide * 1000)))
    hf = outdir / "_reel.html"
    hf.write_text(html)

    hold_tail_ms = 900  # let the last (usually CTA) slide sit before we cut
    total_ms = int(per_slide * 1000 * n) + hold_tail_ms

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": W, "height": H},
            record_video_dir=str(outdir),
            record_video_size={"width": W, "height": H},
        )
        page = context.new_page()
        page.goto(f"file://{hf.resolve()}")
        page.wait_for_timeout(total_ms)
        context.close()
        browser.close()

    webm = next(outdir.glob("*.webm"))
    raw_mp4 = outdir / "_reel_raw.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(webm), "-r", "30", "-pix_fmt", "yuv420p", str(raw_mp4)],
        check=True, capture_output=True,
    )

    total_s = total_ms / 1000
    fade_start = max(total_s - 1.2, 0.1)
    out = outdir / "reel.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(raw_mp4), "-i", str(audio),
        "-map", "0:v", "-map", "1:a",
        "-t", f"{total_s:.2f}",
        "-af", f"afade=t=out:st={fade_start:.2f}:d=1.2",
        "-r", "30", "-c:v", "libx264", "-profile:v", "high", "-level", "4.0",
        "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "21",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-shortest",
        str(out),
    ], check=True, capture_output=True)

    webm.unlink(missing_ok=True)
    raw_mp4.unlink(missing_ok=True)
    hf.unlink(missing_ok=True)
    size = out.stat().st_size
    print(f"reel.mp4 written: {total_s:.1f}s, {size / 1e6:.1f} MB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], *(sys.argv[4:5] or []))

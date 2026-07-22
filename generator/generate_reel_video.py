#!/usr/bin/env python3
"""Render an animated text overlay (light-colored, no card/frame — just a
staggered entrance per slide plus a fade at each slide boundary) and
composite it on top of a user-supplied background video, keeping the
background video's own built-in audio untouched.

Captures the overlay as a true-alpha PNG sequence (Playwright screenshots
with a transparent page background, driven deterministically frame-by-frame
via a JS renderAtTime() function) rather than a chroma-keyed green-screen
recording — this avoids color-spill/fringing artifacts on thin text that a
green-screen + colorkey pipeline is prone to, at the cost of a slower render
(one screenshot per output frame instead of one continuous recording).

Usage: generate_reel_video.py <spec.json> <outdir> <bg_video.mp4> [seconds_per_slide]
Writes <outdir>/reel.mp4, matching the background video's resolution.
"""
import json, math, re, sys, pathlib, subprocess, shutil

from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).parent
sys.path.insert(0, str(BASE))
from generate import slide_html  # noqa: E402

FPS = 30
MIN_TOTAL_S = 30.0   # every reel must run at least this long
MAX_TOTAL_S = 58.0   # Facebook Reels hard-require <=60s; keep a safety margin
SLIDE_SANITY_CAP_S = 16.0  # backstop so one freak-long slide can't dominate before total scaling
WORDS_PER_SEC = 3.0   # comfortable reading pace for short Hindi/English reel text
SETTLE_S = 1.0        # extra beat so the staggered entrance finishes before reading starts

_TAG_RE = re.compile(r"<[^>]+>")


def slide_read_seconds(s, min_s):
    """Estimate a realistic on-screen duration for a slide from how much text
    it actually holds, instead of giving every slide the same fixed beat
    regardless of content. This is a per-slide RAW estimate; main() scales the
    whole set up/down afterwards to fit [MIN_TOTAL_S, MAX_TOTAL_S] while
    preserving the relative proportions between slides."""
    fields = [s.get(k, "") for k in ("eyebrow", "h1", "h2", "sub", "body", "handle", "swipe")]
    fields += s.get("points", [])
    plain = _TAG_RE.sub(" ", " ".join(fields))
    words = len(plain.split())
    read_s = words / WORDS_PER_SEC + SETTLE_S
    return max(min_s, min(read_s, SLIDE_SANITY_CAP_S))


def probe(path, entry):
    return subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         f"stream={entry}", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return float(out)


def main(spec_path, outdir, bg_video, min_per_slide=4.0):
    # min_per_slide is a FLOOR, not a fixed duration — each slide actually gets
    # max(min_per_slide, a read-time estimate from its own text), and the whole
    # reel is scaled up to MIN_TOTAL_S if it would otherwise come in short.
    min_per_slide = float(min_per_slide)
    assert min_per_slide >= 4.0, "each slide must stay on screen at least 4 seconds"
    spec = json.loads(pathlib.Path(spec_path).read_text())
    slides = spec["slides"]
    n = len(slides)
    assert n >= 2, "need at least 2 slides"
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    bg_video = pathlib.Path(bg_video)

    w = int(probe(bg_video, "width"))
    h = int(probe(bg_video, "height"))
    video_dur = probe_duration(bg_video)

    durations = [slide_read_seconds(s, min_per_slide) for s in slides]
    total_s = sum(durations)
    if total_s < MIN_TOTAL_S:
        scale = MIN_TOTAL_S / total_s
        durations = [d * scale for d in durations]
        total_s = MIN_TOTAL_S
    elif total_s > MAX_TOTAL_S:
        scale = MAX_TOTAL_S / total_s
        durations = [max(min_per_slide, d * scale) for d in durations]
        total_s = sum(durations)
    durations_ms = [int(round(d * 1000)) for d in durations]
    total_ms = sum(durations_ms)
    total_s = total_ms / 1000
    print(f"Per-slide durations (s): {[round(d, 1) for d in durations]}  total={total_s:.1f}s")

    # If the content runs longer than the background video, loop the video
    # (audio included) enough times to cover it rather than cutting slides
    # short.
    loop_count = max(0, math.ceil(total_s / video_dur) - 1)
    if loop_count:
        print(f"Content is {total_s:.1f}s but the background video is only "
              f"{video_dur:.1f}s — looping it {loop_count + 1}x to cover the full reel.")
    total_frames = int(round(total_s * FPS))

    template = (BASE / "template_reel_video.html").read_text()
    template = template.replace("url('fonts/", f"url('file://{BASE.resolve()}/fonts/")
    template = template.replace("__CANVAS_W__", str(w)).replace("__CANVAS_H__", str(h))

    slides_json = json.dumps([
        {"html": slide_html(s), "page": f"{idx + 1} / {n}", "durMs": durations_ms[idx]}
        for idx, s in enumerate(slides)
    ])
    html = template.replace("__SLIDES__", slides_json)
    hf = outdir / "_reel_text.html"
    hf.write_text(html)

    frames_dir = outdir / "_frames"
    frames_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(f"file://{hf.resolve()}")
        for f in range(total_frames):
            t_ms = f * 1000 / FPS
            page.evaluate(f"window.renderAtTime({t_ms})")
            page.screenshot(path=str(frames_dir / f"f{f:05d}.png"), omit_background=True)
        browser.close()

    out = outdir / "reel.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-stream_loop", str(loop_count), "-i", str(bg_video),
        "-framerate", str(FPS), "-i", str(frames_dir / "f%05d.png"),
        "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1[vout]",
        "-map", "[vout]", "-map", "0:a?",
        "-t", f"{total_s:.2f}",
        "-r", str(FPS), "-c:v", "libx264", "-profile:v", "high", "-level", "4.0",
        "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest",
        str(out),
    ], check=True, capture_output=True)

    shutil.rmtree(frames_dir, ignore_errors=True)
    hf.unlink(missing_ok=True)
    size = out.stat().st_size
    print(f"reel.mp4 written: {total_s:.1f}s, {w}x{h}, {total_frames} frames, "
          f"{size / 1e6:.1f} MB (background audio kept)")

    # A static cover.jpg so IG/inbox previews don't default to frame 0 (which
    # is blank pre-entrance-animation). Grabbed late in slide 1's hold — the
    # hook slide fully settled and readable, just before it fades to slide 2
    # — so the cover itself sells the reel instead of catching a half-risen
    # transition frame.
    slide1_s = durations_ms[0] / 1000
    cover_t = min(max(slide1_s - 0.5, 1.2), max(total_s - 0.1, 0.1))
    cover = outdir / "cover.jpg"
    subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{cover_t:.2f}", "-i", str(out), "-frames:v", "1",
         "-q:v", "2", str(cover)],
        check=True, capture_output=True,
    )
    print(f"cover.jpg written (frame @ {cover_t:.2f}s)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], *(sys.argv[4:5] or []))

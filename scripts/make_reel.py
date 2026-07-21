#!/usr/bin/env python3
"""Build a 1080x1920 Reel video from carousel slides + background music.

Usage: make_reel.py <post_dir> <music_file> [seconds_per_slide]
Writes <post_dir>/reel.mp4
"""
import pathlib, subprocess, sys

BG = "#F6EEDF"
FADE = 0.6

def main(post_dir, music, per_slide=4.0):
    post = pathlib.Path(post_dir)
    slides = sorted(post.glob("slide*.jpg"))
    n = len(slides)
    assert n >= 2, "need at least 2 slides"
    per_slide = float(per_slide)
    assert per_slide >= 4.0, "each slide must stay on screen at least 4 seconds"
    total = n * per_slide - (n - 1) * FADE

    inputs, filters = [], []
    for i, s in enumerate(slides):
        inputs += ["-loop", "1", "-t", str(per_slide + FADE), "-i", str(s)]
        filters.append(
            f"[{i}:v]scale=1080:1350,pad=1080:1920:0:285:color={BG},"
            f"setsar=1,format=yuv420p[v{i}]")

    # chain xfade transitions
    prev = "v0"
    off = per_slide - FADE
    for i in range(1, n):
        out = f"x{i}"
        filters.append(f"[{prev}][v{i}]xfade=transition=fade:duration={FADE}:offset={off:.3f}[{out}]")
        prev = out
        off += per_slide - FADE

    # force yuv420p at the very end for universal playback (phones/IG)
    filters.append(f"[{prev}]format=yuv420p[vout]")
    cmd = ["ffmpeg", "-y", *inputs, "-i", str(music),
           "-filter_complex", ";".join(filters),
           "-map", "[vout]", "-map", f"{n}:a",
           "-t", f"{total:.2f}", "-af", f"afade=t=out:st={total-1.2:.2f}:d=1.2",
           "-r", "30", "-c:v", "libx264", "-profile:v", "high", "-level", "4.0",
           "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "21",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-shortest",
           str(post / "reel.mp4")]
    subprocess.run(cmd, check=True, capture_output=True)
    size = (post / "reel.mp4").stat().st_size
    print(f"reel.mp4 written: {total:.1f}s, {size/1e6:.1f} MB")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *(sys.argv[3:4] or []))

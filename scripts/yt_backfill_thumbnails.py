#!/usr/bin/env python3
"""Re-set thumbnails on every already-published YouTube Short.

Why this exists: cover.jpg is a frame of the reel, so it is 9:16. YouTube
thumbnails are 16:9 -- a vertical image gets pillarboxed into a thin strip
between bars, which looks like the Short has no cover at all even though
thumbnails.set returned success. The renderer now also emits a true 1280x720
yt_thumb.jpg; this script pushes it onto Shorts that went live with the old
vertical one.

Uploads no video and touches no other platform. Safe to re-run.

Usage: yt_backfill_thumbnails.py [--dry-run]
Requires env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
"""
import glob, json, os, pathlib, sys, time, urllib.error, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from publish import yt_get_access_token  # noqa: E402

DRY = "--dry-run" in sys.argv


def live_shorts():
    """Every (video_id, post_dir) we have ever published, newest last."""
    seen = {}
    for f in sorted(glob.glob("results/*.json")):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        name = os.path.basename(f)[:-5]
        if name in ("yt-test", "yt-thumb-test"):
            vid, post = d.get("video_id"), d.get("post_dir")
        else:
            yt = d.get("youtube")
            vid = yt.get("video_id") if isinstance(yt, dict) else None
            post = "posts/" + name
        if vid and post:
            seen[vid] = post
    return sorted(seen.items(), key=lambda kv: kv[1])


def set_thumb(video_id, thumb, token):
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
        f"?uploadType=media&videoId={video_id}",
        data=thumb.read_bytes(), method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "image/jpeg"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        json.load(r)


def main():
    token = None if DRY else yt_get_access_token()
    results, ok, failed, skipped = [], 0, 0, 0

    for video_id, post in live_shorts():
        thumb = pathlib.Path(post) / "yt_thumb.jpg"
        if not thumb.exists():
            print(f"SKIP  {video_id}  {post}  (no yt_thumb.jpg)")
            results.append({"video_id": video_id, "post_dir": post, "status": "skipped",
                            "reason": "no yt_thumb.jpg"})
            skipped += 1
            continue
        if DRY:
            print(f"WOULD {video_id}  {post}")
            continue
        try:
            set_thumb(video_id, thumb, token)
            print(f"OK    {video_id}  {post}")
            results.append({"video_id": video_id, "post_dir": post, "status": "success"})
            ok += 1
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            print(f"FAIL  {video_id}  {post}  HTTP {e.code}: {body}")
            results.append({"video_id": video_id, "post_dir": post, "status": "failed",
                            "error": f"HTTP {e.code}: {body}"})
            failed += 1
        except Exception as e:
            print(f"FAIL  {video_id}  {post}  {e}")
            results.append({"video_id": video_id, "post_dir": post, "status": "failed",
                            "error": str(e)})
            failed += 1
        time.sleep(1)  # be gentle with quota

    if DRY:
        return
    out = pathlib.Path("results") / "yt-thumb-backfill.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(
        {"ok": ok, "failed": failed, "skipped": skipped, "results": results}, indent=2))
    print(f"\nDone: {ok} set, {failed} failed, {skipped} skipped.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

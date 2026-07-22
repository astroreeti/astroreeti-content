#!/usr/bin/env python3
"""One-off fix-up: set a thumbnail on an ALREADY-UPLOADED YouTube video,
without touching Instagram/Facebook or uploading a new video (no duplicate
post). Used when a video went live before cover.jpg existed for that post.

Usage: yt_set_thumbnail_only.py <video_id> <post_dir>
Requires env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
post_dir must contain a cover.jpg (generate it first if the post predates
the cover.jpg fix, e.g. via ffmpeg -ss ... -frames:v 1 on its reel.mp4).
"""
import json, pathlib, sys, urllib.error, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from publish import yt_get_access_token  # noqa: E402


def set_thumbnail_raising(video_id, access_token, cover_path):
    """Same call as publish.yt_set_thumbnail(), but raises instead of
    swallowing the error -- this script's whole point is to surface failures."""
    data = pathlib.Path(cover_path).read_bytes()
    req = urllib.request.Request(
        f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
        f"?uploadType=media&videoId={video_id}",
        data=data, method="POST",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "image/jpeg"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main(video_id, post_dir):
    post = pathlib.Path(post_dir)
    cover = post / "cover.jpg"
    out_path = pathlib.Path("results") / "yt-thumb-test.json"
    out_path.parent.mkdir(exist_ok=True)
    if not cover.exists():
        result = {"video_id": video_id, "status": "failed", "error": f"{cover} does not exist"}
        out_path.write_text(json.dumps(result, indent=2))
        raise SystemExit(result["error"])
    try:
        access_token = yt_get_access_token()
        set_thumbnail_raising(video_id, access_token, cover)
        result = {"video_id": video_id, "status": "success"}
        print("Thumbnail set OK for", video_id)
        out_path.write_text(json.dumps(result, indent=2))
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        err = f"HTTP {e.code}: {body}"
        print("THUMBNAIL SET FAILED:", err)
        out_path.write_text(json.dumps({"video_id": video_id, "status": "failed", "error": err}, indent=2))
        raise
    except Exception as e:
        print("THUMBNAIL SET FAILED:", e)
        out_path.write_text(json.dumps({"video_id": video_id, "status": "failed", "error": str(e)}, indent=2))
        raise


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

#!/usr/bin/env python3
"""One-off fix-up: fully re-publish a post to Facebook from scratch (fresh
START + upload + FINISH, using the now-hardened fb_publish_reel() which
verifies the reel actually left draft status) and correct
results/<date>.json's "facebook" field with the true, verified outcome.

Use this when a previous "published" result turns out to have been a false
positive (Meta returned success but the reel never actually went public).

Usage: fb_republish.py <post_dir> <page_id>
Requires env: FB_PAGE_TOKEN
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from publish import fb_publish_reel  # noqa: E402


def main(post_dir, page_id):
    post = pathlib.Path(post_dir)
    date = post.name
    caption = (post / "caption.txt").read_text()

    rj = pathlib.Path("results") / f"{date}.json"
    existing = json.loads(rj.read_text()) if rj.exists() else {"date": date}

    try:
        video_id = fb_publish_reel(post, page_id, caption)
        existing["facebook"] = {"status": "published", "post_id": video_id, "verified": True}
        print("Facebook re-publish OK, verified published:", video_id)
    except Exception as e:
        existing["facebook"] = {"status": "failed", "error": str(e)}
        print("Facebook re-publish failed:", e)

    rj.parent.mkdir(exist_ok=True)
    rj.write_text(json.dumps(existing, indent=2))
    print(json.dumps(existing, indent=2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

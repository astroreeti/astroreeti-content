#!/usr/bin/env python3
"""One-off fix-up: re-issue the FINISH call on a Facebook Reel that's stuck
in publish_status=="draft" (uploaded successfully but never actually made
public -- invisible to everyone except the Page admin). Then verify it
actually flipped to "published" instead of trusting a bare success response.

Usage: fb_force_publish.py <page_id> <video_id>
Requires env: FB_PAGE_TOKEN
"""
import json, os, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from publish import fb_api  # noqa: E402


def main(page_id, video_id):
    out = {"video_id": video_id}

    before = fb_api(video_id, {"fields": "status"})
    out["status_before"] = before.get("status")
    print("BEFORE:", json.dumps(before.get("status"), indent=2))

    finish = fb_api(f"{page_id}/video_reels", {
        "upload_phase": "finish", "video_id": video_id, "video_state": "PUBLISHED",
    }, "POST")
    out["finish_response"] = finish
    print("FINISH response:", json.dumps(finish, indent=2))

    after = fb_api(video_id, {"fields": "status,permalink_url"})
    out["status_after"] = after.get("status")
    out["permalink_after"] = after.get("permalink_url")
    print("AFTER:", json.dumps(after, indent=2))

    out["fixed"] = (after.get("status", {}).get("publishing_phase", {}).get("publish_status") == "published")

    out_path = pathlib.Path("results") / "fb-force-publish.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

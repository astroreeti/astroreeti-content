#!/usr/bin/env python3
"""Read-only diagnostic: check the FB Page token's granted scopes/access
level, the Page's verification/publish status, and the actual reach/insight
numbers on the most recent published reel -- to find out WHY reels aren't
reaching followers (vs. just guessing from Meta's sparse docs).

Usage: fb_diagnose.py <page_id> <video_id>
Requires env: FB_PAGE_TOKEN
Writes results/fb-diagnose.json. Never modifies anything -- GET calls only.
"""
import json, os, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from publish import fb_api  # noqa: E402


def safe(fn, label):
    try:
        return {"ok": True, "data": fn()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main(page_id, video_id):
    token = os.environ["FB_PAGE_TOKEN"]
    out = {}

    out["token_debug"] = safe(
        lambda: fb_api("debug_token", {"input_token": token}), "token_debug")

    out["page_info"] = safe(
        lambda: fb_api(page_id, {"fields": "name,verification_status,fan_count,is_published,link,category,"
                                            "restriction_info,is_permanently_closed,is_unclaimed"}),
        "page_info")

    out["page_permissions"] = safe(
        lambda: fb_api(f"{page_id}/permissions"), "page_permissions")

    out["video_info"] = safe(
        lambda: fb_api(video_id, {"fields": "permalink_url,description,length,status,created_time,"
                                             "privacy,unpublished_content_type,is_crosspost_video,"
                                             "content_category,backdated_time,updated_time"}),
        "video_info")

    out["video_insights"] = safe(
        lambda: fb_api(f"{video_id}/video_insights", {
            "metric": "total_video_views,total_video_views_unique,total_video_impressions,"
                      "total_video_impressions_unique,total_video_impressions_fan,"
                      "total_video_impressions_fan_unique"
        }), "video_insights")

    # List what the Page's own video/reel/post libraries actually contain,
    # via our own token -- if our uploads don't show up here either, that's
    # independent confirmation they never truly registered as public content,
    # regardless of what an outside viewer sees.
    out["page_videos_list"] = safe(
        lambda: fb_api(f"{page_id}/videos", {"fields": "id,description,permalink_url,created_time,status"}),
        "page_videos_list")

    out["page_video_reels_list"] = safe(
        lambda: fb_api(f"{page_id}/video_reels", {"fields": "id,description,permalink_url,created_time,status"}),
        "page_video_reels_list")

    out["page_posts_list"] = safe(
        lambda: fb_api(f"{page_id}/posts", {"fields": "id,message,permalink_url,created_time,status_type"}),
        "page_posts_list")

    out["page_feed_list"] = safe(
        lambda: fb_api(f"{page_id}/feed", {"fields": "id,message,permalink_url,created_time,status_type"}),
        "page_feed_list")

    out_path = pathlib.Path("results") / "fb-diagnose.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

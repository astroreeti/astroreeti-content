#!/usr/bin/env python3
"""One-off diagnostic: publish an EXISTING already-rendered post's reel.mp4 to
YouTube Shorts only (no Instagram/Facebook calls, so it never duplicates a
public post there). Used to test/diagnose the YouTube upload path in
isolation, e.g. after a code fix, without re-publishing to IG/FB.

Usage: yt_test_publish.py <post_dir>
Requires env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
Prints the real HTTP error body on failure (this is the whole point of the
script) instead of the generic "403 Forbidden" that used to be shown.
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from publish import yt_get_access_token, yt_upload_short, yt_set_thumbnail  # noqa: E402


def main(post_dir):
    post = pathlib.Path(post_dir)
    caption = (post / "caption.txt").read_text()
    title = caption.split("\n", 1)[0][:95] + " #Shorts"
    description = caption + "\n\n#Shorts"

    # Write the outcome to a results file and commit it back (mirrors how the
    # real publish pipeline reports results) so a session with only git
    # push/pull access -- no GitHub Actions log API -- can read what actually
    # happened by just pulling.
    out_path = pathlib.Path("results") / "yt-test.json"
    out_path.parent.mkdir(exist_ok=True)
    try:
        print("Requesting YouTube access token...")
        access_token = yt_get_access_token()
        print("Got access token. Uploading", post / "reel.mp4", "...")
        video_id = yt_upload_short(post, access_token, title, description)
        print("UPLOAD OK, video_id =", video_id)
        result = {"post_dir": str(post), "status": "success", "video_id": video_id}
        if video_id:
            yt_set_thumbnail(video_id, access_token, post)
            result["permalink"] = f"https://youtube.com/shorts/{video_id}"
            print(f"Permalink: {result['permalink']}")
        out_path.write_text(json.dumps(result, indent=2))
    except Exception as e:
        print("YOUTUBE TEST FAILED:", e)
        out_path.write_text(json.dumps({"post_dir": str(post), "status": "failed", "error": str(e)}, indent=2))
        raise


if __name__ == "__main__":
    main(sys.argv[1])

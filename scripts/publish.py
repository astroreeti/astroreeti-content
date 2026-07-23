#!/usr/bin/env python3
"""Publish a post to Instagram (required) and, if configured, cross-post the
same rendered media to the linked Facebook Page (best-effort).

Usage: publish.py <post_dir>   e.g. publish.py posts/2026-07-20
Requires env: IG_TOKEN, IG_USER_ID, REPO (owner/name), BRANCH (default main)
Optional env (enables Facebook cross-post): FB_PAGE_ID, FB_PAGE_TOKEN
Writes results/<date>.json with the outcome. A Facebook failure never fails
the run or the results status — Instagram is the primary channel.
"""
import json, mimetypes, os, pathlib, sys, time, urllib.parse, urllib.request

GRAPH = "https://graph.instagram.com/v23.0"
FB_GRAPH = "https://graph.facebook.com/v21.0"

def api(path, params=None, method="GET"):
    params = dict(params or {})
    params["access_token"] = os.environ["IG_TOKEN"]
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        req = urllib.request.Request(f"{GRAPH}/{path}?{data.decode()}")
    else:
        req = urllib.request.Request(f"{GRAPH}/{path}", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"{path} -> HTTP {e.code}: {body}")

def wait_finished(container_id, label, tries=40, delay=5):
    for _ in range(tries):
        st = api(container_id, {"fields": "status_code,status"})
        code = st.get("status_code")
        if code == "FINISHED":
            return
        if code == "ERROR":
            raise RuntimeError(f"{label} container ERROR: {st}")
        time.sleep(delay)
    raise RuntimeError(f"{label} container not ready after {tries*delay}s")

def publish_reel(post, date, repo, branch, ig_user, caption):
    base = f"https://raw.githubusercontent.com/{repo}/{branch}/{post}"
    url = f"{base}/reel.mp4"
    print("reel container for", url)
    params = {
        "media_type": "REELS", "video_url": url,
        "caption": caption, "share_to_feed": "true",
    }
    # A public JPEG cover so the IG inbox/preview doesn't default to frame 0
    # (which is blank pre-entrance-animation) via thumb_offset=0.
    if (pathlib.Path(post) / "cover.jpg").exists():
        params["cover_url"] = f"{base}/cover.jpg"
    res = api(f"{ig_user}/media", params, "POST")
    wait_finished(res["id"], "reel", tries=60, delay=10)
    pub = api(f"{ig_user}/media_publish", {"creation_id": res["id"]}, "POST")
    return pub["id"]

# ---------------------------------------------------------------------------
# Facebook Page cross-post (best-effort; never raises out of publish_to_facebook)
# ---------------------------------------------------------------------------

def fb_api(path, params=None, method="GET", full_url=None):
    page_token = os.environ["FB_PAGE_TOKEN"]
    params = dict(params or {})
    params["access_token"] = page_token
    data = urllib.parse.urlencode(params).encode()
    url = full_url or f"{FB_GRAPH}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"{path} -> HTTP {e.code}: {body}")

def fb_publish_reel(post, page_id, caption):
    """Upload local reel.mp4 to the Facebook Page as a Reel (resumable upload)."""
    video_path = post / "reel.mp4"
    size = video_path.stat().st_size

    # Meta's docs document description/title as START-phase params (not FINISH,
    # where we were previously sending description only) — send it here too so
    # the caption is actually attached to the reel.
    start = fb_api(f"{page_id}/video_reels", {
        "upload_phase": "start", "description": caption,
    }, "POST")
    video_id = start["video_id"]
    upload_url = start["upload_url"]

    with open(video_path, "rb") as f:
        body = f.read()
    req = urllib.request.Request(upload_url, data=body, method="POST", headers={
        "Authorization": f"OAuth {os.environ['FB_PAGE_TOKEN']}",
        "offset": "0",
        "file_size": str(size),
        "Content-Type": "application/octet-stream",
    })
    with urllib.request.urlopen(req, timeout=180) as r:
        upload_res = json.load(r)
    if not upload_res.get("success"):
        raise RuntimeError(f"Facebook video byte upload did not report success: {upload_res}")

    finish = fb_api(f"{page_id}/video_reels", {
        "upload_phase": "finish", "video_id": video_id,
        "video_state": "PUBLISHED", "description": caption,
    }, "POST")
    if not finish.get("success", True):
        raise RuntimeError(f"Facebook video_reels finish call did not report success: {finish}")

    # Meta's FINISH response returning {"success": true} does NOT guarantee
    # the reel actually left draft state -- seen in practice: a video whose
    # byte upload silently failed still got a success response here, and the
    # reel sat in publish_status="draft" forever (invisible to everyone but
    # the Page admin) while our code happily reported it as published. Poll
    # the video's own status until it actually reports "published" before
    # trusting this.
    for _ in range(6):
        time.sleep(5)
        status = fb_api(video_id, {"fields": "status"}).get("status", {})
        publish_status = status.get("publishing_phase", {}).get("publish_status")
        if publish_status == "published":
            return video_id
        if publish_status not in (None, "draft", "scheduled"):
            raise RuntimeError(f"Facebook reel {video_id} in unexpected state: {status}")
    raise RuntimeError(
        f"Facebook reel {video_id} never left draft status after FINISH reported success "
        f"(last status: {status}) -- the underlying video upload likely failed silently."
    )

def fb_publish_photos(post, repo, branch, page_id, caption):
    """Post carousel slides to the Facebook Page as a multi-photo feed post."""
    slides = sorted(post.glob("slide*.jpg"))
    base = f"https://raw.githubusercontent.com/{repo}/{branch}/{post}"
    photo_ids = []
    for s in slides:
        res = fb_api(f"{page_id}/photos", {
            "url": f"{base}/{s.name}", "published": "false",
        }, "POST")
        photo_ids.append(res["id"])
    attached = [{"media_fbid": pid} for pid in photo_ids]
    post_res = fb_api(f"{page_id}/feed", {
        "message": caption,
        "attached_media": json.dumps(attached),
    }, "POST")
    return post_res.get("id")

def publish_to_facebook(post, date, repo, branch, fmt, caption):
    """Best-effort Facebook cross-post. Returns a result dict, never raises."""
    if not (os.environ.get("FB_PAGE_ID") and os.environ.get("FB_PAGE_TOKEN")):
        return {"status": "skipped", "reason": "FB_PAGE_ID/FB_PAGE_TOKEN not configured"}
    page_id = os.environ["FB_PAGE_ID"]
    try:
        if fmt == "reel":
            fb_id = fb_publish_reel(post, page_id, caption)
        else:
            fb_id = fb_publish_photos(post, repo, branch, page_id, caption)
        return {"status": "published", "post_id": fb_id}
    except Exception as e:
        print("Facebook cross-post failed (non-fatal):", e)
        return {"status": "failed", "error": str(e)}

# ---------------------------------------------------------------------------
# YouTube Shorts cross-post (best-effort; never raises out of publish_to_youtube)
# ---------------------------------------------------------------------------

YT_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
YT_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"

def yt_get_access_token():
    params = {
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(YT_OAUTH_TOKEN_URL, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"YT token refresh -> HTTP {e.code}: {body}")

def yt_upload_short(post, access_token, title, description):
    """Resumable upload of reel.mp4 to YouTube as a Short."""
    video_path = post / "reel.mp4"
    size = video_path.stat().st_size

    metadata = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "categoryId": "24",  # Entertainment
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    body = json.dumps(metadata).encode()
    init_req = urllib.request.Request(
        f"{YT_UPLOAD_URL}?uploadType=resumable&part=snippet,status",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(size),
        },
    )
    try:
        with urllib.request.urlopen(init_req, timeout=60) as r:
            upload_url = r.headers.get("Location")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"YouTube upload init -> HTTP {e.code}: {body}")
    if not upload_url:
        raise RuntimeError("YouTube resumable upload init did not return a Location header")

    with open(video_path, "rb") as f:
        video_bytes = f.read()
    up_req = urllib.request.Request(
        upload_url, data=video_bytes, method="PUT",
        headers={"Content-Type": "video/mp4", "Content-Length": str(size)},
    )
    try:
        with urllib.request.urlopen(up_req, timeout=300) as r:
            res = json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"YouTube upload -> HTTP {e.code}: {body}")
    return res.get("id")


def yt_set_thumbnail(video_id, access_token, post):
    """Best-effort: set the reel's cover.jpg as the YouTube Short's thumbnail.

    A video freshly finished uploading is often not yet fully registered on
    YouTube's side -- calling thumbnails.set immediately can fail even though
    the exact same call succeeds seconds later (confirmed: both 2026-07-22-pm
    and 2026-07-23-am's Shorts went live with no cover image, then had their
    thumbnail set successfully on a manual retry a few minutes after
    publish). Retry with backoff instead of trying once and giving up, and
    return whether it actually succeeded instead of swallowing the outcome
    entirely -- so callers/results.json can tell a real failure from success.
    """
    thumb = pathlib.Path(post) / "cover.jpg"
    if not thumb.exists():
        return {"ok": False, "error": "cover.jpg does not exist for this post"}
    data = thumb.read_bytes()
    last_err = None
    for attempt in range(5):  # ~0s, 5s, 10s, 20s, 30s => ~65s of retry budget
        if attempt:
            time.sleep([5, 10, 20, 30][attempt - 1])
        req = urllib.request.Request(
            f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
            f"?uploadType=media&videoId={video_id}",
            data=data, method="POST",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "image/jpeg"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                json.load(r)
            return {"ok": True, "attempts": attempt + 1}
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}: {e.read().decode()}"
        except Exception as e:
            last_err = str(e)
    print(f"YouTube thumbnail set failed after {attempt + 1} attempts (non-fatal): {last_err}")
    return {"ok": False, "error": last_err, "attempts": attempt + 1}

def publish_to_youtube(post, date, fmt, caption):
    """Best-effort YouTube Shorts cross-post. Only applies to reels. Never raises."""
    if fmt != "reel":
        return {"status": "skipped", "reason": "not a reel"}
    if not (os.environ.get("YT_CLIENT_ID") and os.environ.get("YT_CLIENT_SECRET")
            and os.environ.get("YT_REFRESH_TOKEN")):
        return {"status": "skipped", "reason": "YT_CLIENT_ID/YT_CLIENT_SECRET/YT_REFRESH_TOKEN not configured"}
    try:
        access_token = yt_get_access_token()
        title = caption.split("\n", 1)[0][:95] + " #Shorts"
        description = caption + "\n\n#Shorts"
        video_id = yt_upload_short(post, access_token, title, description)
        thumbnail_result = None
        if video_id:
            thumbnail_result = yt_set_thumbnail(video_id, access_token, post)
        return {"status": "published", "video_id": video_id,
                "permalink": f"https://youtube.com/shorts/{video_id}" if video_id else "",
                "thumbnail": thumbnail_result}
    except Exception as e:
        print("YouTube cross-post failed (non-fatal):", e)
        return {"status": "failed", "error": str(e)}

def main(post_dir):
    post = pathlib.Path(post_dir)
    date = post.name
    repo = os.environ["REPO"]
    branch = os.environ.get("BRANCH", "main")
    ig_user = os.environ["IG_USER_ID"]
    caption = (post / "caption.txt").read_text()

    fmt = "carousel"
    pj = post / "publish.json"
    if pj.exists():
        fmt = json.loads(pj.read_text()).get("format", "carousel")

    if fmt == "reel":
        # Instagram is the primary/required channel, but Facebook and YouTube
        # are entirely independent platforms/credentials -- an Instagram-side
        # failure (token issue, Meta app restriction, etc.) should never
        # silently skip attempting the other two. Try IG first, capture its
        # outcome without raising, then always attempt Facebook + YouTube.
        #
        # IMPORTANT: a retry (re-pushing publish.json after a partial
        # failure) must be idempotent PER PLATFORM. Once a platform reports
        # "published" in a previous results file, a later retry (e.g. to get
        # a still-failing Instagram working) must NOT re-publish to that
        # platform again -- otherwise every retry duplicates the post on
        # whichever platforms already succeeded.
        rj = pathlib.Path("results") / f"{date}.json"
        existing = {}
        if rj.exists():
            try:
                existing = json.loads(rj.read_text())
            except Exception:
                existing = {}

        media_id, permalink, ig_error = None, "", None
        if existing.get("status") == "published":
            print("Instagram already published on a previous attempt; not re-publishing.")
            media_id = existing.get("media_id")
            permalink = existing.get("permalink", "")
        else:
            try:
                media_id = publish_reel(post_dir, date, repo, branch, ig_user, caption)
                try:
                    perma = api(media_id, {"fields": "permalink"})
                    permalink = perma.get("permalink", "")
                except Exception as e:
                    print("permalink lookup failed:", e)
            except Exception as e:
                ig_error = str(e)
                print("Instagram publish failed (still attempting Facebook/YouTube):", e)

        out = {"date": date, "format": "reel"}
        if ig_error:
            out["status"] = "failed"
            out["error"] = ig_error
        else:
            out["status"] = "published"
            out["media_id"] = media_id
            out["permalink"] = permalink

        if existing.get("facebook", {}).get("status") == "published":
            print("Facebook already published on a previous attempt; not re-publishing.")
            out["facebook"] = existing["facebook"]
        else:
            out["facebook"] = publish_to_facebook(post, date, repo, branch, fmt, caption)

        if existing.get("youtube", {}).get("status") == "published":
            print("YouTube already published on a previous attempt; not re-publishing.")
            out["youtube"] = existing["youtube"]
        else:
            out["youtube"] = publish_to_youtube(post, date, fmt, caption)
        rj.parent.mkdir(exist_ok=True)
        rj.write_text(json.dumps(out, indent=2))
        print("RESULT:", json.dumps(out))
        # Don't raise on an IG-only failure -- results already captured the
        # full picture (including any Facebook/YouTube success) and __main__'s
        # exception handler would otherwise clobber that richer result with a
        # bare {"status":"failed"} dict.
        return

    slides = sorted(post.glob("slide*.jpg"))
    if not 2 <= len(slides) <= 10:
        raise SystemExit(f"need 2-10 slides, found {len(slides)}")

    base = f"https://raw.githubusercontent.com/{repo}/{branch}/{post_dir}"
    children = []
    for s in slides:
        url = f"{base}/{s.name}"
        print("item container for", url)
        res = api(f"{ig_user}/media", {"image_url": url, "is_carousel_item": "true"}, "POST")
        children.append(res["id"])

    for cid in children:
        wait_finished(cid, "item")

    print("carousel container...")
    car = api(f"{ig_user}/media", {
        "media_type": "CAROUSEL",
        "children": ",".join(children),
        "caption": caption,
    }, "POST")
    wait_finished(car["id"], "carousel")

    print("publishing...")
    pub = api(f"{ig_user}/media_publish", {"creation_id": car["id"]}, "POST")
    media_id = pub["id"]

    perma = {}
    try:
        perma = api(media_id, {"fields": "permalink"})
    except Exception as e:
        print("permalink lookup failed:", e)

    out = {"date": date, "status": "published", "media_id": media_id,
           "permalink": perma.get("permalink", ""), "slides": len(slides)}
    out["facebook"] = publish_to_facebook(post, date, repo, branch, fmt, caption)
    out["youtube"] = publish_to_youtube(post, date, fmt, caption)
    rj = pathlib.Path("results") / f"{date}.json"
    rj.parent.mkdir(exist_ok=True)
    rj.write_text(json.dumps(out, indent=2))
    print("SUCCESS:", json.dumps(out))

if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except Exception as e:
        date = pathlib.Path(sys.argv[1]).name
        rj = pathlib.Path("results") / f"{date}.json"
        rj.parent.mkdir(exist_ok=True)
        rj.write_text(json.dumps({"date": date, "status": "failed", "error": str(e)}, indent=2))
        print("FAILED:", e)
        raise

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
    res = api(f"{ig_user}/media", {
        "media_type": "REELS", "video_url": url,
        "caption": caption, "share_to_feed": "true",
    }, "POST")
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

    start = fb_api(f"{page_id}/video_reels", {"upload_phase": "start"}, "POST")
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
        json.load(r)

    finish = fb_api(f"{page_id}/video_reels", {
        "upload_phase": "finish", "video_id": video_id,
        "video_state": "PUBLISHED", "description": caption,
    }, "POST")
    return video_id if finish.get("success", True) else None

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
        media_id = publish_reel(post_dir, date, repo, branch, ig_user, caption)
        perma = {}
        try:
            perma = api(media_id, {"fields": "permalink"})
        except Exception as e:
            print("permalink lookup failed:", e)
        out = {"date": date, "status": "published", "format": "reel",
               "media_id": media_id, "permalink": perma.get("permalink", "")}
        out["facebook"] = publish_to_facebook(post, date, repo, branch, fmt, caption)
        rj = pathlib.Path("results") / f"{date}.json"
        rj.parent.mkdir(exist_ok=True)
        rj.write_text(json.dumps(out, indent=2))
        print("SUCCESS:", json.dumps(out))
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

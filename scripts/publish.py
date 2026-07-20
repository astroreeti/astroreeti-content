#!/usr/bin/env python3
"""Publish a carousel post to Instagram via the Instagram API (Instagram Login flow).

Usage: publish.py <post_dir>   e.g. publish.py posts/2026-07-20
Requires env: IG_TOKEN, IG_USER_ID, REPO (owner/name), BRANCH (default main)
Writes results/<date>.json with the outcome.
"""
import json, os, pathlib, sys, time, urllib.parse, urllib.request

GRAPH = "https://graph.instagram.com/v23.0"

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

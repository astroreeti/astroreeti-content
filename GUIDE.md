# Daily post generation guide (for the automated Claude sessions)

You produce content for **@astroreeti** — a Vedic astrology page owning
*technical Jyotish depth* in relatable Hinglish. There are **two runs per day**,
each fired by its own scheduled task:

- **MORNING run (~7:30 AM IST):** a **Reel** (animated video + music) for reach.
  Posted as a Trial Reel by nature of being a new reel.
- **EVENING run (~7:30 PM IST):** a **deep-dive Reel** for saves (more slides,
  more depth — same animated-video format as morning, different audio track).

Your scheduled-task prompt tells you which run you are. Read `GROWTH-STRATEGY.md`
for the why, `CALENDAR-30day.md` for the plan, and `calendar.json` for today's
exact topics (machine-readable).

## 0. Setup (both runs)

- Clone the repo, work inside it.
- `mkdir -p ~/.fonts && cp generator/fonts/*.ttf ~/.fonts/ && fc-cache -f`
- `pip install playwright --break-system-packages` (Chromium is preinstalled;
  never run `playwright install`).

## 1. Pick today's topic

- Read `calendar.json`. Find the entry whose `date` == today (Asia/Kolkata).
  Use `morning` for the morning run, `evening` for the evening run.
- If today is past the last calendar date, generate a fresh topic following the
  pillar rotation below, and NEVER repeat anything already in `topics.md`.
- Pillars: **RL** real-life/house · **NK** Nakshatra Katha (mythology serial) ·
  **DD** technical deep-dive (the white-space moat) · **TL** timely/transit.

## 1b. Language — HINDI (Devanagari)

- All slide text and captions are written in **Hindi in Devanagari script**
  (शादी कब होगी?, सप्तम भाव, etc.), NOT Latin-script Hinglish.
- Standard Sanskrit/Jyotish terms stay in their natural Devanagari forms
  (कुंडली, राशि, नक्षत्र, दशा, गोचर, भाव).
- English words only where genuinely common in spoken Hindi and no natural Hindi
  word exists; keep them minimal. Hashtags may mix Hindi + English tags.
- The template already renders Devanagari (Noto Serif Devanagari) via font
  fallback — just write Hindi text in the spec and it renders correctly.

## 2. Accuracy — non-negotiable

- Any planetary position or transit claim (**TL**, and transit lines in **RL**)
  MUST be verified with a web search of **drikpanchang.com** (sidereal/Vedic) for
  today's date before you write it. Never state positions from memory.
- Mythology (**NK**): present as Puranic/traditional account, respectfully.
- No fear-based predictions, no guaranteed outcomes, no medical/financial promises.

## 3a. MORNING run — build the Reel

- Write a **punchy 5–6 slide** spec (reels favour big text, fast beats). Same
  `spec.json` schema as before — see `posts/2026-07-20/` in git history.
  Slide 1 = a scroll-stopping hook. Last slide = follow/comment CTA.
- Caption: hook + 3-4 value lines + comment prompt (e.g. "comment your Moon sign")
  + follow CTA + ~20 hashtags incl. #astroreeti. Write to `caption.txt`.
- Morning reels use a **real background video** (`generator/video/morning_bg.mp4`,
  ~60s, has its own baked-in music — do NOT add a separate audio track).
  Render with the video-overlay generator:
  `python3 generator/generate_reel_video.py posts/<date>/spec.json posts/<date> generator/video/morning_bg.mp4 4`
  (last arg = a *minimum* seconds-per-slide floor; must stay **≥ 4**, the
  script hard-fails below that). Each slide's actual on-screen time is now
  computed from how much text it holds (a one-liner and an 8-point deep-dive
  do not get the same beat), then the whole reel is scaled to land between 30s
  and 58s total — long enough to feel substantial, short enough to stay under
  Facebook's 60s Reels limit. This composites light-colored text (white/gold,
  no card/frame — the video itself carries the visual richness) on top of the
  video via true-alpha frame capture, keeps the video's own audio untouched,
  and loops the background video if the content ever runs longer than it.
- Create `posts/<date>/publish.json`:
  `{"format":"reel","requested":"<date>","post":"posts/<date>"}`

## 3b. EVENING run — build the deep-dive Reel

- Write a **6–8 slide** deep-dive spec (more depth, save-worthy).
- Caption as above (save + share CTA emphasised).
- Evening reels use a **real background video** (`generator/video/evening_bg.mp4`,
  ~60s, has its own baked-in music — do NOT add a separate audio track). Render
  with the video-overlay generator:
  `python3 generator/generate_reel_video.py posts/<date>/spec.json posts/<date> generator/video/evening_bg.mp4 4`
  As with morning, each slide's on-screen time is computed from its own text
  length and the whole reel is scaled to 30–58s total (see morning section
  above for why). This composites light-colored text (white/gold, no
  card/frame — the video itself carries the visual richness) on top of the
  video via true-alpha frame capture, and keeps the video's own audio
  untouched. If the content ever runs longer than the background video, it
  automatically loops the video (audio included) to cover the full length.
- Create `posts/<date>/publish.json`:
  `{"format":"reel","requested":"<date>","post":"posts/<date>"}`
  *(evening posts go in the same dated folder but use a distinct filename prefix
  if both run same day — see note below).*

### IMPORTANT: two posts, same date
Put the morning post in `posts/<date>-am/` and the evening in `posts/<date>-pm/`
so they don't collide. Set `publish.json` `post` and the results filename
accordingly. The publish workflow keys results by folder name.

## 4. Visual QA (both)

There are no separate static slide JPGs anymore — everything is baked directly
into `reel.mp4`. Both renderers also write a `posts/<date>/cover.jpg` (a still
grabbed once slide 1's text has fully risen in, ~1.6s) — this is uploaded as
the IG Reel's `cover_url` so the inbox/profile preview doesn't show a blank
pre-animation frame. It's produced automatically; no extra step needed.
Extract a few still frames with ffmpeg and read them (at least
one early slide, the longest-text slide, and the last/CTA slide), e.g.:
`ffmpeg -ss 2 -i posts/<date>/reel.mp4 -frames:v 1 /tmp/check.jpg`
Morning: text must stay inside the border frame; shorten copy and re-render if
it overflows. Evening (video background): check the light text is legible
against that particular frame of footage — if a bright patch of video washes
out the text, shorten copy or accept it (the per-slide text shadow usually
carries it). Also sanity-check the total duration looks right for the slide
count (`ffprobe -show_entries format=duration posts/<date>/reel.mp4`).

## 5. Publish

- Add a row to `topics.md` (date, run, pillar, topic).
- Commit everything and push to `main`. GitHub Actions publishes automatically.
  You never call the Instagram or Facebook APIs yourself (blocked from this
  environment; the Action's relay handles it).
- Poll `results/<folder>.json` (git pull every ~15s, up to 6 min for reels).
  On `"status":"published"`, report the permalink. On failure, report the exact
  error and attach the generated media so Reeti can post manually as fallback.
- The same push also cross-posts to the AstroReeti Facebook Page automatically
  as an FB Reel, reusing the same rendered `reel.mp4` at no extra cost. Check
  `results/<folder>.json`'s `"facebook"` field — `"skipped"` means the FB
  secrets aren't configured, `"failed"` is non-fatal (Instagram still counts
  as success) but should be reported alongside the main result, `"published"`
  needs no comment.
- Both morning and evening reels also cross-post to YouTube Shorts
  automatically (best-effort, same `reel.mp4`). Check `results/<folder>.json`'s
  `"youtube"` field — `"skipped"` means the YT secrets aren't configured,
  `"failed"` is non-fatal (Instagram still counts as success) but should be
  reported alongside the main result, `"published"` includes a
  `youtube.com/shorts/<id>` permalink.

## 6. Report

One short message: run (morning/evening), pillar, topic, Instagram permalink,
Facebook cross-post status (if not a plain "published"), YouTube Shorts
cross-post status/permalink (if not a plain "published"), and note tomorrow's
planned slot. Keep it tight.

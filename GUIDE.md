# Daily post generation guide (for the automated Claude sessions)

You produce content for **@astroreeti** — a Vedic astrology page owning
*technical Jyotish depth* in relatable Hinglish. There are **two runs per day**,
each fired by its own scheduled task:

- **MORNING run (~7:30 AM IST):** a **Reel** (video + music) for reach. Posted
  as a Trial Reel by nature of being a new reel.
- **EVENING run (~7:30 PM IST):** a **deep-dive Carousel** for saves.

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
  `spec.json` schema as carousels — see `posts/2026-07-20/` in git history.
  Slide 1 = a scroll-stopping hook. Last slide = follow/comment CTA.
- Caption: hook + 3-4 value lines + comment prompt (e.g. "comment your Moon sign")
  + follow CTA + ~20 hashtags incl. #astroreeti. Write to `caption.txt`.
- Render slides: `python3 generator/generate.py posts/<date>/spec.json posts/<date>/`
- Music track: use the fixed brand track `generator/audio/astroreeti_raga.mp3`
  for all morning reels (no more rotation).
- Render reel: `python3 scripts/make_reel.py posts/<date> generator/audio/astroreeti_raga.mp3 4`
  (at least 4 seconds per slide — do not go faster than this, slides need to
  be readable).
- Create `posts/<date>/publish.json`:
  `{"format":"reel","requested":"<date>","post":"posts/<date>"}`

## 3b. EVENING run — build the Carousel

- Write a **6–8 slide** deep-dive spec (more depth, save-worthy). Render slides.
- Caption as above (save + share CTA emphasised).
- Create `posts/<date>/publish.json`:
  `{"format":"carousel","requested":"<date>","post":"posts/<date>"}`
  *(evening posts go in the same dated folder but use a distinct filename prefix
  if both run same day — see note below).*

### IMPORTANT: two posts, same date
Put the morning post in `posts/<date>-am/` and the evening in `posts/<date>-pm/`
so they don't collide. Set `publish.json` `post` and the results filename
accordingly. The publish workflow keys results by folder name.

## 4. Visual QA (both)

Read the rendered slide JPGs (at least slide 1, the longest-text slide, and the
last). Text must stay inside the border frame; shorten copy and re-render if it
overflows. For reels, also extract a frame from the mp4 and check it looks right.

## 5. Publish

- Add a row to `topics.md` (date, run, pillar, topic).
- Commit everything and push to `main`. GitHub Actions publishes automatically.
  You never call the Instagram or Facebook APIs yourself (blocked from this
  environment; the Action's relay handles it).
- Poll `results/<folder>.json` (git pull every ~15s, up to 6 min for reels).
  On `"status":"published"`, report the permalink. On failure, report the exact
  error and attach the generated media so Reeti can post manually as fallback.
- The same push also cross-posts to the AstroReeti Facebook Page automatically
  (reel → FB Reel, carousel → FB multi-photo post), reusing the same rendered
  media at no extra cost. Check `results/<folder>.json`'s `"facebook"` field —
  `"skipped"` means the FB secrets aren't configured, `"failed"` is non-fatal
  (Instagram still counts as success) but should be reported alongside the
  main result, `"published"` needs no comment.
- Morning reels also cross-post to YouTube Shorts automatically (best-effort,
  same `reel.mp4`). Check `results/<folder>.json`'s `"youtube"` field —
  `"skipped"` means it's not a reel or the YT secrets aren't configured,
  `"failed"` is non-fatal (Instagram still counts as success) but should be
  reported alongside the main result, `"published"` includes a
  `youtube.com/shorts/<id>` permalink. Carousel (evening) posts always show
  `"skipped"` for YouTube since there's no video to upload.

## 6. Report

One short message: run (morning/evening), pillar, topic, Instagram permalink,
Facebook cross-post status (if not a plain "published"), YouTube Shorts
cross-post status/permalink for morning reels (if not a plain "published" or
expected "skipped"), and note tomorrow's planned slot. Keep it tight.

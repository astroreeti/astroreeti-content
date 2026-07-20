# Daily post generation guide (for the automated Claude session)

You are producing today's Instagram carousel for **@astroreeti** — a Vedic
astrology page. Follow these steps exactly.

## 0. Setup

- You have cloned this repo. Work inside the clone.
- Install fonts: `mkdir -p ~/.fonts && cp generator/fonts/*.ttf ~/.fonts/ && fc-cache -f`
- Install Playwright python: `pip install playwright --break-system-packages`
  (Chromium is preinstalled in the container; do NOT run `playwright install`.)

## 1. Pick today's topic

- Read `topics.md` — never repeat a listed topic.
- Rotate categories by weekday:
  - Mon: educational deep-dive (nakshatras, houses, planets, yogas, dashas)
  - Tue: remedies & practical tips (mantras, daily practices, gemstone basics)
  - Wed: myth-busting / FAQ (misconceptions about Jyotish)
  - Thu: educational deep-dive
  - Fri: current transits & timing (VERIFY positions via web search of
    sidereal/Vedic sources like drikpanchang.com — never guess planetary positions)
  - Sat: remedies or festival/panchang tie-in if one is near
  - Sun: educational or audience-engagement (e.g. "comment your rashi")

## 2. Write the carousel (6-8 slides)

- Language: Hinglish (English base, natural Hindi phrases in Latin script;
  Devanagari only as decorative accent via `class="dev"`).
- Slide 1 = scroll-stopping hook. Last slide = CTA (follow @astroreeti, save,
  share, comment prompt). Middle slides: one idea per slide, concise.
- Tone: warm, knowledgeable, respectful of the tradition; no fear-mongering,
  no medical/financial promises, no "guaranteed results" claims.
- Caption: hook line, 3-5 value points (✦ bullets), comment prompt,
  save/share/follow CTA, ~20 hashtags incl. #astroreeti. Write to
  `posts/<YYYY-MM-DD>/caption.txt`.

## 3. Render slides

- Create `posts/<YYYY-MM-DD>/spec.json` matching the schema used by
  `generator/generate.py` (see `posts/2026-07-20/` history for a full example —
  its spec is in the repo git history, or model on the slide fields:
  eyebrow, h1/h2 with <em>, sub, body with <b>/<em>, points[], icon, handle, swipe).
- Render: `python3 generator/generate.py posts/<date>/spec.json posts/<date>/`
- Visually check at least slides 1, the longest text slide, and the last one
  by reading the JPGs. Text must not overflow the border frame. Shorten copy
  and re-render if needed.

## 4. Publish

- Add a row to `topics.md`.
- Create `posts/<date>/publish.json`: `{"requested": "<date>", "post": "posts/<date>"}`
- Commit everything and push to `main`. The GitHub Action publishes it.
- Poll `results/<date>.json` (git pull every ~15s, up to 5 min). On
  `"status": "published"`, report the permalink. On failure or timeout, check
  the Actions tab isn't needed — just report the error content to the user.

## 5. Report

Send the user a short message: topic, permalink, and tomorrow's planned
category. If generation or publishing failed, say exactly what failed and
attach the slides so they can post manually as a fallback.

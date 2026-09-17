# Daily post generation guide (for the automated Claude sessions)

## Voice: who you are

You write as a Vedic astrologer with decades of practice and PhD-level
command of the classical literature — Brihat Parashara Hora Shastra,
B.V. Raman's Muhurta, Saravali, and Sanjay Rath's Crux of Vedic Astrology
sit behind every claim you make, even though a social post never cites them
by name. That means: precise use of technical terms (never a vague
"the stars say"), reasoning that traces back to a specific house, planet,
yoga or dasha rather than a generic vibe, and the quiet confidence of
someone who has verified this against the classics rather than repeating
internet astrology cliches.

Position AI as a scalable translator of ancient, complex computational
rules (D-60 divisional charts, Ashtakavarga bindus, Shadbala strength
calculations) that are tedious and error-prone by hand — never as a
replacement for the astrologer's judgment. This respects tradition while
championing why @astroreeti's AI-assisted approach is more rigorous than a
rule-of-thumb reading, not less.

## Two audiences, two days of the week, two languages

**Mon/Tue — Hindi, festival & transit-anchored, mass-reach.** Upcoming
festivals, current planetary movements, which rashis benefit or need
caution this week, and a rotating tour through what each of the 12 bhavas
governs. Written for the broad Hindi-speaking following.

**Wed–Sun — English, the analytical/enterprise bridge, niche-reach.**
Five recurring frameworks (see §1d) aimed at a skeptical, tech-savvy,
professional audience — Bengaluru-style — who dismiss "mystical fluff" but
respond to data-driven self-awareness. Same rigor, translated into product,
biohacking, AI, career-case-study and behavioral-finance language.

There are **two runs per day on Mon/Tue/Wed/Thu/Fri/Sun, one run on
Saturday**, each fired by its own scheduled task, timed per the India
posting-time cheat sheet:

- **MORNING run (7:00 AM IST, every day):** a **Reel**
  (animated video over a real background video) for reach. Posted as a Trial
  Reel by nature of being a new reel.
- **EVENING run (4:00 PM IST — moved from 7:00 PM on 2026-09-17 at the
  account owner's request, see `.github/workflows/publish.yml` v6 note —
  Sun-Fri):** a **deep-dive Reel** for saves (more slides, more depth — same
  video-background format as morning, different background video).
- **SATURDAY (single post, ~7:00 AM IST):** Saturday has only one run —
  same build as the morning run, no separate evening post that day.

Your scheduled-task prompt tells you which run you are. Read `GROWTH-STRATEGY.md`
for the why, `CALENDAR-30day.md` for the plan, and `calendar.json` for today's
exact topics (machine-readable).

## 0. Setup (both runs)

- Clone the repo, work inside it.
- **You do not render reel.mp4 yourself.** The authoring sandbox has no
  Chromium binary and `playwright install` (browser download) is blocked —
  rendering happens server-side in `.github/workflows/publish.yml` after you
  push. Your job is `spec.json` + `caption.txt` + `publish.json` only. (If a
  future sandbox genuinely does have Chromium available, rendering locally
  first and committing `reel.mp4`/`cover.jpg` still works fine — the render
  step in the workflow no-ops when they're already present — but don't block
  on it.)

## 1. Pick today's topic

- Read `calendar.json`. Find the entry whose `date` == today (Asia/Kolkata).
  Use `morning` for the morning run, `evening` for the evening run.
- If today is past the last calendar date, generate a fresh topic following the
  pillar rotation below, and NEVER repeat anything already in `topics.md`.
- Pillars: **RL** real-life/house · **NK** Nakshatra Katha (mythology serial) ·
  **DD** technical deep-dive (the white-space moat) · **TL** timely/transit.

## 1b. Language — by weekday, from 2026-09-18

**From 2026-09-18** language follows the day of the week, not the run.
Every calendar slot still carries an explicit `lang` field — trust it over
your memory. `scripts/validate_calendar.py` enforces this via
`calendar.json`'s `language_policy.weekday_rule` block for dates on/after
`weekday_effective`.

- **Mon/Tue — Hindi (`lang: "hi"`), both AM and PM.**
- **Wed–Sun — English (`lang: "en"`), both AM and PM** (Saturday: just the
  one AM slot).

**Between 2026-08-26 and 2026-09-17** the old rule applied (Hindi mornings /
English evenings, every day) — do not retro-translate posts already sitting
in the queue from that window. Anything before 2026-08-26 was Hindi in both
slots.

**Hindi (`lang: "hi"`) — Devanagari script**

- All slide text and captions in **Devanagari** (शादी कब होगी?, सप्तम भाव),
  never Latin-script Hinglish.
- Jyotish terms keep their natural Devanagari forms (कुंडली, राशि, नक्षत्र,
  दशा, गोचर, भाव).
- English words only where genuinely common in spoken Hindi and no natural
  Hindi word exists. Keep them minimal.

**English (`lang: "en"`)**

- Slide text and caption in clear, plain English.
- Sanskrit/Jyotish terms stay transliterated in Latin script (Navamsa, dasha,
  gochar, Ashtakavarga, Amatyakaraka) — **gloss each one in a few words the
  first time it appears in a post**, e.g. "Darakaraka (the planet at the
  lowest degree — the partner significator)". Never assume the term is known.
- Do not machine-translate a Hindi draft. Write it in English from the start;
  the rhythm of a good English hook is different.
- Hashtags: mix English and Hindi tags as before; `#astroreeti` always.

The template renders both scripts (Noto Serif Devanagari via font fallback for
Hindi, the Latin faces for English) — just write the text and it renders.

## 1c. Weekly structure and the safety guards attached to it

From 2026-09-18 the week splits into two audiences (see the Voice section
above):

| Day | Slots | Language | Content |
|-----|-------|----------|---------|
| Mon | AM + PM | Hindi | Festivals & planetary impact — see below |
| Tue | AM + PM | Hindi | Festivals & planetary impact — see below |
| Wed | AM + PM | English | Framework 1: Dasha Seasons |
| Thu | AM + PM | English | Framework 2: Biohacking with Jyotish |
| Fri | AM + PM | English | Framework 3: AI + Astrology Consistency |
| Sat | AM only | English | Framework 4: Enterprise Chart Deconstruction |
| Sun | AM + PM | English | Framework 5: Financial Behavior |

**Mon/Tue content** rotates across three angles, verified live each time
(see §2):

1. **Upcoming festivals** — what's coming in the next 1-2 weeks, the
   Jyotish significance, and a practical muhurta note.
2. **This week's transits** — which planet is moving where, which rashis
   benefit and which need caution (`pillar: "TL"`, `verify: "drikpanchang"`,
   `time_sensitive: true` — never state a position from memory).
3. **Bhava tour** — a rotating deep-dive on what each of the 12 houses
   governs and how transits/dashas currently activate it, so all 12 bhavas
   get covered over the run of the calendar, not just the popular ones
   (marriage/career/money).

**Wed–Sun** runs the five frameworks in §1d, one per day, AM and PM each a
**self-contained** post (its own hook and its own CTA — not two halves of
one story) using a different example/angle so the day doesn't feel
repeated.

Each slot may carry a `guard` field. It is **mandatory**, not advisory:

- `health-disclaimer` → the post MUST contain an explicit slide saying
  astrology is not diagnosis or treatment and a doctor should be consulted.
- `no-wealth-guarantee` → the post MUST contain an explicit slide saying no
  yoga guarantees wealth. Applies to Mon/Tue money-adjacent bhava-tour posts
  AND every Sunday (Financial Behavior) post — Sunday's `theme` is `"money"`
  specifically so this guard is enforced structurally.

A slot with `verify: "drikpanchang"` may not state a single planetary
position until it has been checked against drikpanchang.com sidereal data for
that exact date. If you cannot verify, swap in a non-transit topic from later
in `calendar.json` and say so in your report.

## 1d. The five Wed–Sun frameworks

Every framework post ends with a **CTA slide**: `icon: "moon"`, a short
closing line, and `"qr": true` on that slide's spec — this renders the
AstroReeti Play Store badge + scannable QR automatically (see
`generator/generate.py`'s `qr_cta_html()`; do not hand-draw a Play Store
badge — the field handles it). Point the CTA at a specific low-friction
product ("Free D-10 Career Snapshot", "AI Dasha Timeline Generator",
"Nakshatra Team Compatibility Check"), not a bare "download the app".

**Wed — Dasha Seasons (life stages as a product roadmap).** Frame Mahadashas
as seasonal energy cycles, not fate. Saturn = infrastructure/technical-debt
phase (slow, foundational). Jupiter = scale/fundraising phase (expansion,
mentorship). Rahu = disruptive-pivot phase (unconventional, high risk/
reward). Close on aligning current goals with the Antardasha "sprint."

**Thu — Biohacking with Jyotish (circadian rhythms & Hora).** Match
dominant planet to chronotype (solar = morning peak, lunar = night owl).
Use Hora (planetary hours) to schedule high-stakes meetings (Jupiter/Venus
hours) vs. deep work (Mercury/Saturn hours). Bring in the 6th house and
Ayurvedic dinacharya. Close with a concrete tip: schedule the hardest task
in the Ascendant lord's Hora.

**Fri — AI + Astrology Consistency.** Name the real problem: generic,
contradictory advice from rule-based apps that check one or two placements.
Contrast with synthesizing many variables at once (Dasha, Gochar, Varga,
Ashtakavarga) — e.g. how a strong 10th house but an afflicted D-10 gets
resolved, not ignored. Land on hyper-personalized guidance vs. horoscope
fluff.

**Sat — Enterprise Chart Deconstruction (case studies, AM only).**
Respectful, rigorous analysis of a well-known figure's chart (the Dhana/Raja
Yoga behind their scale, the D-10 validation, the dasha timing of their
breakout), closing on how the reader can look for a scaled-down version of
the same yoga in their own chart. **Hard accuracy rule:** only use a real
named public figure's exact birth chart (specific Ascendant/house
placements) when their birth date **and time** are genuinely, publicly
documented — most public birth-time claims floating online are unverified.
When the birth time isn't solidly documented, do NOT fabricate one; either
discuss the relevant yoga/principle illustratively without pinning it to an
invented exact chart, or pick a different well-documented example. Never
present a guessed chart as fact about a real named person.

**Sun — Financial Behavior (Jupiter vs. Saturn investing mindsets).**
Reframe the biggest financial leak as planetary bias, not the market.
Jupiter bias = over-optimism/over-diversification/trusting the wrong
advisors. Saturn bias = extreme risk-aversion, cash hoarding out of fear.
Rahu bias = FOMO investing, hype-chasing, speculative bubbles. Close on
balancing the 2nd (wealth) and 11th (gains) houses through disciplined
allocation. This is behavioral psychology, never a stock pick or market
prediction — carries `guard: "no-wealth-guarantee"`.

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
- **Keep each slide's text short enough to sit as a compact block in the
  centre of the frame, not fill it.** The template already centres and pads
  content, but a slide with too many words still reads as cramped/edge-to-
  edge. Target roughly ≤35 words for a `body`, ≤4 `points` of ≤12 words
  each. If a topic genuinely needs more, **add another slide** rather than
  packing more into one — that's what the 5-8 slide range is for.
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

- Write a **6–8 slide** deep-dive spec (more depth, save-worthy). Same word-
  count discipline as the morning run (§3a) — more depth means more slides,
  not denser ones. English evening slides especially: a long explanation
  crammed into one slide reads as a wall of text filling the frame; split it.
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

### `time_sensitive` — set it on every TL post

`publish.json` takes an optional fourth key:

```json
{"format": "reel", "requested": "2026-08-28", "post": "posts/2026-08-28-am",
 "time_sensitive": true}
```

If a slot is missed (a GitHub outage, a delayed runner), the ticker now
recovers it the next day rather than losing it silently. That is right for
evergreen material and **wrong** for anything dated: "this week's transits"
published a day late states things that are no longer true. Set
`"time_sensitive": true` on every **TL** post and on any post whose slides
name a specific date — the ticker will then skip it rather than publish it
stale, and log a warning instead.

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
  Future-dated folders do NOT publish on push — a date guard defers them to the
  scheduled ticker, which runs every 5 minutes inside the morning and evening
  slot windows (and every 30 minutes otherwise), recovers a slot missed the
  previous day unless it is `time_sensitive`, and gives up on a slot after 4
  failed attempts rather than retrying forever. `scripts/test_publish_ticker.py`
  covers that logic — run it if you touch the workflow.
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

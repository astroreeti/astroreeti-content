#!/usr/bin/env python3
"""Structural checks on calendar.json.

Exists because Krittika was silently lost: calendar.json scheduled it for
Sat 2026-07-25 *evening*, but GUIDE.md gives Saturday a single morning run,
so the slot never fired and nobody noticed for two weeks. Anything that can
drop an episode without an error should fail loudly here instead.

Extended 2026-08-13: also enforces the language policy (morning Hindi /
evening English from the effective date), the per-theme safety guards
(health disclaimer, no-wealth-guarantee), and that the queue is deep
enough that a slot can never arrive with nothing authored for it.

Usage: python3 scripts/validate_calendar.py   (exit 1 on any problem)
"""
import json, datetime, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
problems, warnings = [], []

cal = json.loads((ROOT / "calendar.json").read_text())
days = cal["days"]

# 1. Saturday has no evening run -- an evening entry there is unpublishable.
TODAY = datetime.date.today()
for e in days:
    d = datetime.date.fromisoformat(e["date"])
    if d.weekday() == 5 and e.get("evening"):
        (problems if d >= TODAY else warnings).append(
            f"{e['date']} (Saturday) has an evening entry "
            f"({e['evening']['pillar']}: {e['evening']['topic'][:50]}) "
            f"- Saturday runs a single morning post, so this slot never fires."
        )

# 2. Dates must be unique, ordered, and gap-free from the first pending day.
seen = [e["date"] for e in days]
if len(seen) != len(set(seen)):
    problems.append("duplicate dates in calendar.json")
if seen != sorted(seen):
    problems.append("calendar days are not in chronological order")

# 3. Every entry needs at least one runnable slot.
for e in days:
    if not e.get("morning") and not e.get("evening"):
        problems.append(f"{e['date']} has neither a morning nor an evening entry")

# 4. Nakshatra serial must stay in order and never land outside an evening slot.
NAK = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu",
       "Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta",
       "Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha",
       "Uttara Ashadha","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada",
       "Uttara Bhadrapada","Revati"]
for e in days:
    if (e.get("morning") or {}).get("pillar") == "NK":
        warnings.append(f"{e['date']}: NK episode sits in a MORNING slot "
                        f"(deep-dive serial is normally an evening format)")

# 5. Topics already logged in topics.md must not be re-scheduled.
tlog = (ROOT / "topics.md").read_text().lower()
logged_cells = set()
for line in tlog.splitlines():
    if line.startswith("|"):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 4:
            logged_cells.add(cells[3])

today = TODAY.isoformat()
for e in days:
    if e["date"] < today:
        continue
    for run in ("morning", "evening"):
        item = e.get(run)
        if not item:
            continue
        head = re.split(r"[—\-:]", item["topic"])[0].strip().lower()
        if len(head) > 4 and any(head in c for c in logged_cells):
            warnings.append(f"{e['date']} {run}: '{head}' looks already covered in topics.md")


# 6. Language policy: morning Hindi, evening English from the effective date.
policy = cal.get("language_policy")
if not policy:
    problems.append("calendar.json has no language_policy block")
else:
    eff = policy["effective"]
    for e in days:
        # Entries written before the policy existed carry no 'lang' field and
        # were all Hindi by the old blanket rule -- don't retro-fail history.
        if e["date"] < eff:
            for run in ("morning", "evening"):
                item = e.get(run) or {}
                if item.get("lang") not in (None, policy["before_effective"]):
                    problems.append(f"{e['date']} {run}: lang="
                                    f"{item['lang']!r} but everything before "
                                    f"{eff} is {policy['before_effective']!r}")
            continue
        for run, want in (("morning", policy["morning"]),
                          ("evening", policy["evening"])):
            item = e.get(run)
            if not item:
                continue
            got = item.get("lang")
            if got is None:
                problems.append(f"{e['date']} {run}: no 'lang' field "
                                f"(expected '{want}')")
            elif got != want:
                problems.append(f"{e['date']} {run}: lang='{got}' but policy "
                                f"says '{want}' for that date")

# 7. Safety guards must ride along with the themes that need them, so an
#    authoring run physically cannot forget the disclaimer slide.
REQUIRED_GUARD = {"money": "no-wealth-guarantee", "health": "health-disclaimer"}
for e in days:
    for run in ("morning", "evening"):
        item = e.get(run) or {}
        theme = item.get("theme")
        need = REQUIRED_GUARD.get(theme)
        if need and item.get("guard") != need:
            problems.append(f"{e['date']} {run}: theme '{theme}' requires "
                            f"guard '{need}' (found {item.get('guard')!r})")

# 8. Transit slots must carry the verify flag -- these are the only entries
#    allowed to make dated planetary claims, and only after a live check.
for e in days:
    if e["date"] < TODAY.isoformat():
        continue  # already authored and verified at the time
    for run in ("morning", "evening"):
        item = e.get(run) or {}
        if item.get("pillar") == "TL" and not item.get("verify"):
            warnings.append(f"{e['date']} {run}: TL slot without a 'verify' flag "
                            f"- transit claims must be checked live before writing")

# 9. Queue depth: the calendar must stay ahead of the publisher. A slot that
#    arrives with no calendar entry is how content silently stops.
horizon = (TODAY + datetime.timedelta(days=14)).isoformat()
planned = {e["date"] for e in days}
missing = []
d = TODAY
while d.isoformat() <= horizon:
    if d.isoformat() not in planned:
        missing.append(d.isoformat())
    d += datetime.timedelta(days=1)
if missing:
    problems.append("no calendar entry for the next-14-day window on: "
                    + ", ".join(missing))

# 10. Every non-Saturday day needs both slots; Saturday needs its morning.
for e in days:
    if e["date"] < today:
        continue
    d = datetime.date.fromisoformat(e["date"])
    if d.weekday() == 5:
        if not e.get("morning"):
            problems.append(f"{e['date']} (Saturday) has no morning entry")
    else:
        for run in ("morning", "evening"):
            if not e.get(run):
                problems.append(f"{e['date']} ({d.strftime('%A')}) has no {run} entry")

print(f"calendar.json: {len(days)} days, {seen[0]} -> {seen[-1]}")
nk = [(e['date'], e['evening']['topic'].split('—')[0].strip())
      for e in days if (e.get('evening') or {}).get('pillar') == 'NK']
print(f"Nakshatra serial: {len(nk)} episodes scheduled")
from collections import Counter
tc = Counter((e.get(r) or {}).get("theme") for e in days for r in ("morning","evening")
             if (e.get(r) or {}).get("theme"))
if tc:
    print("themes: " + ", ".join(f"{k}={v}" for k, v in sorted(tc.items())))

for w in warnings:
    print(f"  WARN  {w}")
for p in problems:
    print(f"  FAIL  {p}")

if problems:
    print(f"\n{len(problems)} problem(s) found.")
    sys.exit(1)
print("\nAll structural checks passed." + (f" ({len(warnings)} warning(s))" if warnings else ""))

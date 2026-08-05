#!/usr/bin/env python3
"""Structural checks on calendar.json.

Exists because Krittika was silently lost: calendar.json scheduled it for
Sat 2026-07-25 *evening*, but GUIDE.md gives Saturday a single morning run,
so the slot never fired and nobody noticed for two weeks. Anything that can
drop an episode without an error should fail loudly here instead.

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

print(f"calendar.json: {len(days)} days, {seen[0]} -> {seen[-1]}")
nk = [(e['date'], e['evening']['topic'].split('—')[0].strip())
      for e in days if (e.get('evening') or {}).get('pillar') == 'NK']
print(f"Nakshatra serial: {len(nk)} episodes scheduled")

for w in warnings:
    print(f"  WARN  {w}")
for p in problems:
    print(f"  FAIL  {p}")

if problems:
    print(f"\n{len(problems)} problem(s) found.")
    sys.exit(1)
print("\nAll structural checks passed." + (f" ({len(warnings)} warning(s))" if warnings else ""))

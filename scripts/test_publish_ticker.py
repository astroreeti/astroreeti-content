#!/usr/bin/env python3
"""Tests for the catch-up ticker embedded in .github/workflows/publish.yml.

The ticker decides which slot publishes and when. It is the single piece of
logic that can silently stop the account posting, and it lives inside a YAML
heredoc where nothing type-checks it. This extracts that exact block and runs
it against a fake repo at controlled times.

Run:  python3 scripts/test_publish_ticker.py
"""
import json, os, pathlib, shutil, subprocess, sys, tempfile, textwrap

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github/workflows/publish.yml"
TMP = pathlib.Path(tempfile.mkdtemp(prefix="ticker-test-"))


def extract_chooser():
    y = WORKFLOW.read_text()
    marker = "DIR=$(python3 - <<'PYEOF'"
    block = y[y.index(marker) + len(marker):y.index("          PYEOF")]
    code = textwrap.dedent(block).replace(
        "now = datetime.datetime.now(IST)",
        "import os as _os; now = datetime.datetime.fromisoformat("
        "_os.environ['FAKE_NOW']).replace(tzinfo=IST)")
    path = TMP / "chooser.py"
    path.write_text(code)
    return path


def extract_guard():
    """Extract the push-time 'is this slot due yet' guard from publish.yml.

    Separate block from the ticker chooser, and separately fallible: on
    2026-08-31 the date-only version of it let a same-day post published at
    11:31 IST go out immediately instead of waiting for its 19:00 slot.
    """
    y = WORKFLOW.read_text()
    marker = "<<'PYGUARD'"
    block = y[y.index(marker) + len(marker):y.index("          PYGUARD")]
    code = textwrap.dedent(block).replace(
        "now = datetime.datetime.now(IST)",
        "import os as _os; now = datetime.datetime.fromisoformat("
        "_os.environ['FAKE_NOW']).replace(tzinfo=IST)")
    path = TMP / "guard.py"
    path.write_text(code)
    return path


CHOOSER = extract_chooser()
GUARD = extract_guard()


def guard_case(name, now, folder, expect):
    env = dict(os.environ, FAKE_NOW=now)
    p = subprocess.run([sys.executable, str(GUARD), f"posts/{folder}"],
                       capture_output=True, text=True, env=env)
    got = p.stdout.strip()
    ok = got == expect
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        print(f"   expected {expect!r} got {got!r}   stderr: {p.stderr.strip()}")
    return ok

def scenario(name, now, posts, results, expect, expect_warn=None):
    root = TMP / "work"; shutil.rmtree(root, ignore_errors=True)
    (root/"posts").mkdir(parents=True); (root/"results").mkdir()
    for d, extra in posts.items():
        pd = root/"posts"/d; pd.mkdir()
        pj = {"format":"reel","requested":d[:10],"post":f"posts/{d}"}
        pj.update(extra or {})
        (pd/"publish.json").write_text(json.dumps(pj))
    for d, r in results.items():
        (root/"results"/f"{d}.json").write_text(json.dumps(r))
    env = dict(os.environ, FAKE_NOW=now)
    p = subprocess.run([sys.executable, str(CHOOSER)], cwd=root,
                       capture_output=True, text=True, env=env)
    got = p.stdout.strip()
    ok = got == expect
    warn_ok = True if expect_warn is None else (expect_warn in p.stderr)
    print(("PASS " if ok and warn_ok else "FAIL ") + name)
    if not ok:
        print(f"   expected {expect!r} got {got!r}")
    if not warn_ok:
        print(f"   expected warning containing {expect_warn!r}; stderr:\n{p.stderr}")
    return ok and warn_ok

R = []
# Thu 2026-08-13. AM slot 07:00, PM slot 19:00 (uniform daily, set 2026-08-31).
R.append(scenario("before AM slot -> nothing", "2026-08-13T06:45",
    {"2026-08-13-am":None,"2026-08-13-pm":None}, {}, ""))
R.append(scenario("after AM slot -> publishes AM", "2026-08-13T07:05",
    {"2026-08-13-am":None,"2026-08-13-pm":None}, {}, "posts/2026-08-13-am"))
R.append(scenario("AM done, before PM -> nothing", "2026-08-13T12:00",
    {"2026-08-13-am":None,"2026-08-13-pm":None},
    {"2026-08-13-am":{"status":"published"}}, ""))
R.append(scenario("after PM slot -> publishes PM", "2026-08-13T19:05",
    {"2026-08-13-am":None,"2026-08-13-pm":None},
    {"2026-08-13-am":{"status":"published"}}, "posts/2026-08-13-pm"))

# THE BUG THIS FIXES: a slot missed before midnight used to be unrecoverable.
R.append(scenario("missed yesterday PM -> recovered next morning", "2026-08-14T06:30",
    {"2026-08-13-pm":None,"2026-08-14-am":None},
    {"2026-08-13-am":{"status":"published"}}, "posts/2026-08-13-pm",
    expect_warn="missed its slot yesterday"))
R.append(scenario("missed yesterday PM but time-sensitive -> skipped, not stale-published",
    "2026-08-14T06:30",
    {"2026-08-13-pm":{"time_sensitive":True},"2026-08-14-am":None},
    {"2026-08-13-am":{"status":"published"}}, "",
    expect_warn="time-sensitive"))
R.append(scenario("today's slot is chosen BEFORE yesterday's leftover (no blocking)",
    "2026-08-14T08:00",
    {"2026-08-13-pm":None,"2026-08-14-am":None},
    {"2026-08-13-am":{"status":"published"}}, "posts/2026-08-14-am"))
R.append(scenario("repeatedly failing slot is abandoned after MAX_ATTEMPTS",
    "2026-08-13T08:00",
    {"2026-08-13-am":None,"2026-08-13-pm":None},
    {"2026-08-13-am":{"status":"failed","attempts":4,"error":"bad token"}}, "",
    expect_warn="giving up"))
R.append(scenario("failed but under the cap -> retried", "2026-08-13T08:00",
    {"2026-08-13-am":None,"2026-08-13-pm":None},
    {"2026-08-13-am":{"status":"failed","attempts":2}}, "posts/2026-08-13-am"))

# Saturday 2026-08-15: morning only, and a -pm folder must never be published.
R.append(scenario("Saturday evening never fires", "2026-08-15T20:00",
    {"2026-08-15-am":None,"2026-08-15-pm":None},
    {"2026-08-15-am":{"status":"published"}}, ""))
R.append(scenario("Saturday morning at 07:00", "2026-08-15T07:05",
    {"2026-08-15-am":None}, {}, "posts/2026-08-15-am"))
# Sunday 2026-08-16: AM 07:00, same as every other day now.
R.append(scenario("Sunday AM not due at 06:45", "2026-08-16T06:45",
    {"2026-08-16-am":None,"2026-08-16-pm":None}, {}, ""))
R.append(scenario("Sunday AM due at 07:05", "2026-08-16T07:05",
    {"2026-08-16-am":None,"2026-08-16-pm":None}, {}, "posts/2026-08-16-am"))
# Exact-boundary tests for the 07:00 / 19:00 uniform times (v4, 2026-08-31).
R.append(scenario("AM fires exactly at 07:00", "2026-08-13T07:00",
    {"2026-08-13-am":None,"2026-08-13-pm":None}, {}, "posts/2026-08-13-am"))
R.append(scenario("PM fires exactly at 19:00", "2026-08-13T19:00",
    {"2026-08-13-am":None,"2026-08-13-pm":None},
    {"2026-08-13-am":{"status":"published"}}, "posts/2026-08-13-pm"))
R.append(scenario("PM not due at 18:45", "2026-08-13T18:45",
    {"2026-08-13-am":None,"2026-08-13-pm":None},
    {"2026-08-13-am":{"status":"published"}}, ""))
# Sunday PM was 19:30 before v4; pin it at 19:00 now.
R.append(scenario("Sunday PM fires at 19:00", "2026-08-16T19:00",
    {"2026-08-16-am":None,"2026-08-16-pm":None},
    {"2026-08-16-am":{"status":"published"}}, "posts/2026-08-16-pm"))

# queue alarms
R.append(scenario("empty queue warns", "2026-08-13T08:00",
    {"2026-08-13-pm":None}, {}, "", expect_warn="Queue gap"))
R.append(scenario("shallow queue warns", "2026-08-13T21:00",
    {"2026-08-13-am":None,"2026-08-13-pm":None,"2026-08-14-am":None,"2026-08-14-pm":None},
    {"2026-08-13-am":{"status":"published"},"2026-08-13-pm":{"status":"published"}}, "",
    expect_warn="queue is only 1 day(s) deep"))

# --- push-time guard: a push must never publish a post off its slot ---
# Mon 2026-08-31. AM slot 07:00, PM slot 19:00.
R.append(guard_case("push: future-dated slot deferred",
    "2026-08-31T11:31", "2026-09-01-am", "yes"))
R.append(guard_case("push: today's AM before 07:00 deferred",
    "2026-08-31T06:30", "2026-08-31-am", "yes"))
R.append(guard_case("push: today's AM after 07:00 publishes",
    "2026-08-31T07:30", "2026-08-31-am", "no"))
# THE 2026-08-31 BUG: this returned "no" and published at 11:31 instead of 19:00.
R.append(guard_case("push: today's PM before 19:00 deferred",
    "2026-08-31T11:31", "2026-08-31-pm", "yes"))
R.append(guard_case("push: today's PM after 19:00 publishes",
    "2026-08-31T19:30", "2026-08-31-pm", "no"))
R.append(guard_case("push: yesterday's slot still publishes",
    "2026-08-31T11:31", "2026-08-30-pm", "no"))

shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{sum(R)}/{len(R)} passed")
sys.exit(0 if all(R) else 1)

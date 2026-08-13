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


CHOOSER = extract_chooser()

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
# Thu 2026-08-13. AM slot 07:30, PM slot 19:30.
R.append(scenario("before AM slot -> nothing", "2026-08-13T07:00",
    {"2026-08-13-am":None,"2026-08-13-pm":None}, {}, ""))
R.append(scenario("after AM slot -> publishes AM", "2026-08-13T07:35",
    {"2026-08-13-am":None,"2026-08-13-pm":None}, {}, "posts/2026-08-13-am"))
R.append(scenario("AM done, before PM -> nothing", "2026-08-13T12:00",
    {"2026-08-13-am":None,"2026-08-13-pm":None},
    {"2026-08-13-am":{"status":"published"}}, ""))
R.append(scenario("after PM slot -> publishes PM", "2026-08-13T19:35",
    {"2026-08-13-am":None,"2026-08-13-pm":None},
    {"2026-08-13-am":{"status":"published"}}, "posts/2026-08-13-pm"))

# THE BUG THIS FIXES: a slot missed before midnight used to be unrecoverable.
R.append(scenario("missed yesterday PM -> recovered next morning", "2026-08-14T06:00",
    {"2026-08-13-pm":None,"2026-08-14-am":None},
    {"2026-08-13-am":{"status":"published"}}, "posts/2026-08-13-pm",
    expect_warn="missed its slot yesterday"))
R.append(scenario("missed yesterday PM but time-sensitive -> skipped, not stale-published",
    "2026-08-14T06:00",
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
R.append(scenario("Saturday morning at 10:00", "2026-08-15T10:05",
    {"2026-08-15-am":None}, {}, "posts/2026-08-15-am"))
# Sunday 2026-08-16: AM 10:30
R.append(scenario("Sunday AM not due at 09:00", "2026-08-16T09:00",
    {"2026-08-16-am":None,"2026-08-16-pm":None}, {}, ""))
R.append(scenario("Sunday AM due at 10:35", "2026-08-16T10:35",
    {"2026-08-16-am":None,"2026-08-16-pm":None}, {}, "posts/2026-08-16-am"))
# queue alarms
R.append(scenario("empty queue warns", "2026-08-13T08:00",
    {"2026-08-13-pm":None}, {}, "", expect_warn="Queue gap"))
R.append(scenario("shallow queue warns", "2026-08-13T21:00",
    {"2026-08-13-am":None,"2026-08-13-pm":None,"2026-08-14-am":None,"2026-08-14-pm":None},
    {"2026-08-13-am":{"status":"published"},"2026-08-13-pm":{"status":"published"}}, "",
    expect_warn="queue is only 1 day(s) deep"))

shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{sum(R)}/{len(R)} passed")
sys.exit(0 if all(R) else 1)

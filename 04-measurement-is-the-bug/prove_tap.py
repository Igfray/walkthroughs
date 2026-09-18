"""Prove the tap-target test is load-bearing. [audit #7]"""
import subprocess
from pathlib import Path

ROOT = Path("/home/legion/PANTHEON")
PY = ROOT / ".venv/bin/python"
TEST = "apps/gateway/tests/test_tap_targets.py"
SITE = ROOT / "apps/gateway/src/gateway/site.py"
TOOL = ROOT / "tools/measure_tap_targets.py"


def run():
    r = subprocess.run([str(PY), "-m", "pytest", TEST, "-q"],
                       cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout.strip().splitlines() or ["?"])[-1]


MUTATIONS = [
    (SITE, "remove the tap floor (the original defect)",
     "    :root {{ --tap: 44px; }}", "    :root {{ --tap: 1px; }}  /* MUTANT */"),
    (SITE, "un-hide the brand monogram from screen readers",
     "<svg class='logo-mark' viewBox='0 0 40 40' aria-hidden='true'>",
     "<svg class='logo-mark' viewBox='0 0 40 40'>  <!-- MUTANT -->"),
    (TOOL, "probe stops emulating touch (the bug I hit)",
     'has_touch=True', 'has_touch=False'),
]

code, line = run()
print(f"unmutated: {line}\n")
assert code == 0, "baseline must be green"

caught = 0
for path, label, find, repl in MUTATIONS:
    orig = path.read_text()
    assert find in orig, f"anchor missing: {label}"
    path.write_text(orig.replace(find, repl, 1))
    code, line = run()
    verdict = "CAUGHT " if code != 0 else "VACUOUS"
    caught += code != 0
    print(f"{verdict} {label}\n        {line}")
    path.write_text(orig)

code, line = run()
print(f"\nrestored: {line}")
raise SystemExit(0 if caught == len(MUTATIONS) and code == 0 else 1)

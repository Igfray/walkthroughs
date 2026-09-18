"""Prove the soft-404 tests are load-bearing. [audit #10]"""
import subprocess
from pathlib import Path

ROOT = Path("/home/legion/PANTHEON")
PY = ROOT / ".venv/bin/python"
TEST = "apps/gateway/tests/test_soft_404.py"
SITE = ROOT / "apps/gateway/src/gateway/routes/site.py"


def run():
    r = subprocess.run([str(PY), "-m", "pytest", TEST, "-q"],
                       cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout.strip().splitlines() or ["?"])[-1]


MUTATIONS = [
    ("serve every slug again (the original defect)",
     "    if not is_real_page(page, content, custom_pages, archetype):",
     "    if False:  # MUTANT: soft 404 restored"),
    ("404 without noindex",
     "\"<meta name='robots' content='noindex'>\"",
     "\"\"  # MUTANT: no noindex"),
    ("404 with no way home",
     "f\"<p><a href='{_h.escape(home, quote=True)}'>Go to the home page</a></p>\"",
     "\"\"  # MUTANT: dead end"),
]

orig = SITE.read_text()
code, line = run()
print(f"unmutated: {line}\n")
assert code == 0, "baseline must be green"

caught = 0
for label, find, repl in MUTATIONS:
    assert find in orig, f"anchor missing: {label}"
    SITE.write_text(orig.replace(find, repl, 1))
    code, line = run()
    verdict = "CAUGHT " if code != 0 else "VACUOUS"
    caught += code != 0
    print(f"{verdict} {label}\n        {line}")
    SITE.write_text(orig)

code, line = run()
print(f"\nrestored: {line}")
raise SystemExit(0 if caught == len(MUTATIONS) and code == 0 else 1)

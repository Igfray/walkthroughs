"""Prove the CSS-extraction tests are load-bearing. [audit #2]"""
import subprocess
from pathlib import Path

ROOT = Path("/home/legion/PANTHEON")
PY = ROOT / ".venv/bin/python"
TEST = "apps/gateway/tests/test_css_extraction.py"
SITE = ROOT / "apps/gateway/src/gateway/site.py"


def run():
    r = subprocess.run([str(PY), "-m", "pytest", TEST, "-q"],
                       cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout.strip().splitlines() or ["?"])[-1]


MUTATIONS = [
    ("stop linking the sheet (back to inline-only)",
     "<link rel='stylesheet' href='{base}/site.css?v={_css_v}'>",
     "<!-- MUTANT: no stylesheet -->"),
    ("version stops tracking the CSS (stale cache forever)",
     'return _hashlib.sha256(_SITE_CSS.encode()).hexdigest()[:12]',
     'return "constant0000"  # MUTANT'),
    ("tenant accent leaks into the SHARED file",
     "  :root {{ --accent: {accent};",
     "  :root {{ --notaccent: {accent};"),
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

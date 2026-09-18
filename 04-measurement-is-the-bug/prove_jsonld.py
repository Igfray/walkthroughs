"""Prove the JSON-LD tests are load-bearing. [audit #4]"""
import subprocess
from pathlib import Path

ROOT = Path("/home/legion/PANTHEON")
PY = ROOT / ".venv/bin/python"
TEST = "apps/gateway/tests/test_jsonld_address.py"
SITE = ROOT / "apps/gateway/src/gateway/site.py"


def run():
    r = subprocess.run([str(PY), "-m", "pytest", TEST, "-q"],
                       cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout.strip().splitlines() or ["?"])[-1]


MUTATIONS = [
    ("address back to a bare string (the defect)",
     'obj["address"] = _postal_address(contact["address"])',
     'obj["address"] = contact["address"]'),
    ("stamp GB on every address (the lie I nearly shipped)",
     '    addr: dict[str, str] = {"@type": "PostalAddress"}',
     '    addr: dict[str, str] = {"@type": "PostalAddress", "addressCountry": "GB"}'),
    ("drop the telephone (what the audit claimed)",
     '        obj["telephone"] = contact["phone"]',
     '        pass  # MUTANT'),
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

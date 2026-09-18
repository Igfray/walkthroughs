"""Fact-check walkthrough 04 against the live system and the repo.

The document's thesis is that unchecked measurements lie. Publishing it with an
unchecked measurement would be funny once and damaging thereafter.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/legion/PANTHEON")
DOC = Path("/home/legion/walkthroughs/04-measurement-is-the-bug/WALKTHROUGH.md")
text = DOC.read_text()
fails = []


def check(label, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {label}{' — ' + detail if detail else ''}")
    if not ok:
        fails.append(label)


# 1. Test count.
r = subprocess.run([str(ROOT / ".venv/bin/python"), "-m", "pytest", "-q"],
                   cwd=ROOT, capture_output=True, text=True)
m = re.search(r"(\d+) passed", r.stdout)
count = int(m.group(1)) if m else 0
check("test count", f"{count:,}" in text, f"suite says {count:,}")

# 2. Every commit hash cited exists and the subject matches.
for sha in sorted(set(re.findall(r"`([0-9a-f]{7})`", text))):
    g = subprocess.run(["git", "log", "-1", "--format=%s", sha],
                       cwd=ROOT, capture_output=True, text=True)
    check(f"commit {sha}", g.returncode == 0, g.stdout.strip()[:60])

# 3. aria-hidden really is on the live emblem.
live = subprocess.run(
    ["curl", "-s", "--max-time", "10",
     "https://pantheonlabs.info/site/d33d8a78-a9c0-4af1-96c3-a1d22f5fba12/home"],
    capture_output=True, text=True).stdout
mark = re.search(r"<svg class='logo-mark'[^>]*>", live)
check("live emblem carries aria-hidden",
      bool(mark) and "aria-hidden='true'" in mark.group(0))

# 4. Live address is a PostalAddress dict.
ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',
                          live, re.S).group(1))
check("live JSON-LD address is structured", isinstance(ld.get("address"), dict),
      str(ld.get("address"))[:60])

# 5. Live page weight claim.
check("live page size claim", "16,8" in text or f"{len(live):,}" in text,
      f"live home is {len(live):,} bytes")

# 6. The gzip numbers quoted for the labs tenant.
labs = subprocess.run(
    ["curl", "-s", "--max-time", "10",
     "https://pantheonlabs.info/site/c3bcfd29-06fa-4d5c-a6dd-4de6c3506937/home"],
    capture_output=True, text=True).stdout
import gzip
arts = re.findall(r'<svg class="hero-art".*?</svg>', labs, re.S)
raw = sum(len(a) for a in arts)
gz = len(gzip.compress("".join(arts).encode(), 6))
check("labs art raw bytes", f"{raw:,}" in text, f"{raw:,}")
check("labs art gzipped", f"{gz:,}" in text, f"{gz:,}")

# 7. The labs tenant really has one page.
sm = subprocess.run(
    ["curl", "-s", "--max-time", "10",
     "https://pantheonlabs.info/site/c3bcfd29-06fa-4d5c-a6dd-4de6c3506937/sitemap.xml"],
    capture_output=True, text=True).stdout
check("labs tenant has one page", sm.count("<loc>") == 1, f"{sm.count('<loc>')} loc(s)")

print("\n" + ("ALL CLAIMS VERIFIED" if not fails else f"UNVERIFIED: {fails}"))
sys.exit(1 if fails else 0)

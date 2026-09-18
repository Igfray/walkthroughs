"""What does the hero art actually COST on the wire? Gzip decides #5.

The inline SVG is repetitive markup, which is exactly what gzip is good at. A
raw byte count overstates the cost; the transfer size is what a visitor pays.
"""
import gzip
import hashlib
import re

for name, path in (("labs", "/tmp/h.html"), ("demo", "/tmp/sv.html")):
    s = open(path).read()
    arts = re.findall(r'<svg class="hero-art".*?</svg>', s, re.S)
    raw = sum(len(a) for a in arts)
    art_gz = len(gzip.compress("".join(arts).encode(), 6))
    page_gz = len(gzip.compress(s.encode(), 6))
    without = len(gzip.compress(re.sub(r'<svg class="hero-art".*?</svg>', "", s, flags=re.S).encode(), 6))
    print(f"{name:5} page_raw={len(s):>7,}  page_gz={page_gz:>6,}")
    print(f"      art_raw={raw:>7,}  art_gz={art_gz:>6,}  "
          f"page_gz_without_art={without:>6,}  saving={page_gz - without:>5,} bytes")

"""Does the address parser degrade honestly on messy input?

A wrong PostalAddress is worse than an honest string: it feeds a search engine
a confident lie about where a business is.
"""
import json
import sys

sys.path.insert(0, "apps/gateway/src")
from gateway.site import _postal_address  # noqa: E402

CASES = [
    "12 Market Street, Wells BA5 2RF",          # the common shape
    "Taliaris, Llandeilo, Carmarthenshire, SA19 7YE",  # the live tenant
    "Unit 4, Brunel Way, Bristol, BS1 6TY",
    "SA19 7YE",                                  # postcode only
    "Somewhere with no postcode at all",         # unparseable -> stay a string
    "",                                          # nothing
    "1600 Amphitheatre Parkway, Mountain View",  # non-UK, no postcode
]

for raw in CASES:
    out = _postal_address(raw)
    kind = type(out).__name__
    print(f"{raw[:46]:<48} -> {kind:4} {json.dumps(out)[:110]}")

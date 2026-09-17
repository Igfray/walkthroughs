# Walkthrough 02: the enquiry form that lied to the visitor

A production defect on the money path, taken from discovery to deployed fix.
Unlike walkthrough 01 (built fresh), this one is reconstructed from the real
git record of my product - the diffs and outputs quoted here are from the
repository, and the fix is live. The product is a website+agent studio for
small businesses; the enquiry form IS the money path.

## 1. Discovery - measurement, not report

No user reported this. It surfaced in a systematic audit of the generated
sites, in round six, ranked #9 of 11 findings - and measurement promoted it
to #1. The probe: load the enquiry page with JavaScript disabled, fill the
form, submit, observe.

    landed on: enq.html?party=1&dogs=0&name=T&email=t%40example.com

The form had no method and no action. With JS, an inline script POSTs the
lead. Without JS - or with the script failed, blocked, or half-loaded - the
browser default is a GET back onto the same page: the lead goes into the
query string, the page re-renders looking like success, nothing is captured,
and nobody is told. A silent failure that flatters itself.

## 2. Why this ranked above ten other findings

The same audit found 55KB of duplicated CSS, missing heading structure,
soft-404s, sub-44px tap targets. This beat all of them on one axis: it is
the only defect where the product tells the user an untruth about the thing
they came to do. A slow page costs patience; a silent lead loss costs the
business a customer and the visitor their booking - and neither ever knows.

A comment in the source claimed the opposite: "captured even if widget.js
is blocked/slow". True for the widget; false for the page itself.

## 3. Design - progressive enhancement, one mechanism at a time

The fix is the oldest pattern on the web, applied honestly:

- The form gains method=post action={origin}/site-enquiry + a hidden
  HMAC-signed token; the date/party fields gain name attributes.
- A new POST /site-enquiry route verifies the token and REUSES the existing
  JSON capture handler - same validation, same dedupe, same durable outbox.
  Two routes, one capture path: no second code path to rot.
- The inline script still preventDefaults where it runs; JS visitors keep
  the in-page flow. The server route is the floor, not a rival.

## 4. TDD, and the failure that made the suite honest

RED first: tests asserting the form carries method/action, and that a real
form-encoded POST round-trips. The attribute tests went green with the
template change. The round-trip test did something better - it failed:

    request.form() -> python-multipart not installed -> 500

Every attribute-level test passed while the route would have crashed on its
first real submit in production. Only the test that exercised the actual
wire shape caught the missing dependency. It went into the gateway's own
pyproject with a comment saying which audit finding requires it.

## 5. Verification - the original reproduction, re-run

The probe that found the bug is the proof it died. Same browser, JS disabled,
same form, same submit:

    POST fired to: https://x/site-enquiry
    body carries email: True
    landed on: Enquiry sent
    lead leaked into query string: False

Plus a TestClient round trip (403 on a bad token, 422 keeps the typed lead
with a way back, thank-you page on success), 4 new tests, suite at 2,102.
Deployed same day; the live route answers 403 to a bad token.

## 6. Honest limits

- The no-JS thank-you page is plainer than the JS flow - equivalent outcome,
  not equivalent polish.
- The HMAC token in a hidden field is the same token the JS path already
  exposes to the page; no new surface, but no improvement either.
- Reconstructed narrative: the commit (d05179c) and its tests are the
  primary record, this document is the guided tour. Artefacts alongside:
  commit_stat.txt, test_diff.patch.


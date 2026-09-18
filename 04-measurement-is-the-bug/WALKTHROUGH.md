# Walkthrough 04: when the measurement is the bug

An eleven-finding audit of my own product, carried to completion. Eight findings
were real and are fixed. **Three were artefacts of how I measured them** — the
code was already correct, and the probe was lying.

That ratio is the point of this document. Every one of the three looked exactly
like a defect: a screen reader announcing junk, missing structured data, 19KB of
dead weight. Each survived until someone checked the measurement itself.

Everything below is from the real run. Commits are on `phase-11` in a private
repo; the diffs quoted are what shipped, and the numbers are what the tools
printed.

---

## The ledger

| # | Finding | Verdict |
|---|---|---|
| 9 | No-JS enquiry silently loses the lead | real — fixed `d05179c` |
| 1 | Five sections, heading outline is the business name twice | real — fixed `369c682` |
| 10 | Any invented slug returns 200 with home content | real — fixed `ff4613c` |
| 7 | Ten of twelve tap targets under 44px | real — fixed `9da7d75` |
| 3 | Lead form under-uses autofill | real — fixed `fa1c19a` |
| 11 | Date inputs accept last year without JS | real — fixed `fa1c19a` |
| 2 | 56KB of identical CSS inlined in every page | real — fixed `971c74d` |
| 4a | `address` is a string, not a `PostalAddress` | real — fixed `879c7fb` |
| 6 | Screen readers announce "B Bryn's Place" | **artefact** |
| 4b | JSON-LD lacks `telephone` | **artefact** |
| 5 | 19KB inline hero SVG is dead weight | **artefact** |

---

## Artefact 1: the phantom "B"

The finding: the nav monogram is an SVG letter inside the brand link, so a
screen reader reads the initial and then the business name — "B Bryn's Place",
every tenant, every page, first thing announced.

Before changing anything I looked at the live page:

```html
<a href="..." class="brand">
  <svg class='logo-mark' viewBox='0 0 40 40' aria-hidden='true'>...<text>W</text></svg>
  West Barn Holidays
</a>
```

`aria-hidden='true'` was already there. No screen reader has ever announced the
letter.

So where did "B Bryn's Place" come from? My own probe:

```js
(e.innerText || e.getAttribute('aria-label') || e.tagName)
```

`innerText` returns rendered text and **ignores `aria-hidden` entirely**. The
probe was reporting what the DOM contains, not what an assistive tech consumes —
and then I read its output as an accessibility defect.

The fix was to the probe, not the product:

```js
const own = [...e.childNodes]
  .filter(n => n.nodeType === 3 ||
               (n.nodeType === 1 && n.getAttribute('aria-hidden') !== 'true'))
  .map(n => n.textContent).join(' ');
const label = (e.getAttribute('aria-label') || own || e.tagName)
```

The finding is now a regression test instead, and a mutation proves it bites:
remove `aria-hidden`, the test fails.

## Artefact 2: the missing telephone

The finding: JSON-LD omits `telephone` even when the tenant has a phone.

Reproduction attempt, with a phone in the tenant's content:

```
JSON-LD keys : @context, @type, address, email, hasOfferCatalog, image, name,
               openingHoursSpecification, priceRange, telephone, url
telephone    : 01749 123456
```

It works. The fixtures I audited — and the live tenant — simply have no phone
number, so `telephone` was correctly absent. The audit measured an **absent
input** and blamed the output.

What the same probe *did* surface, on every tenant including live:

```json
"address": "Taliaris, Llandeilo, Carmarthenshire, SA19 7YE"
```

A bare string, where Schema.org defines `PostalAddress` and Google's docs
require the structured form for the rich results this markup exists to earn.
That one was real, and it is fixed.

## Artefact 3: the 19KB that costs 2.4KB

The finding: the labs tenant inlines 19KB of generative hero SVG — 75% of the
page — uncacheable, re-sent on every navigation. Extract it to a URL.

Before building that, two measurements.

**What does it cost on the wire?** The art is repetitive markup, which is what
gzip is for:

```
labs  page_raw= 25,349  page_gz= 5,069
      art_raw= 18,830  art_gz= 2,434  page_gz_without_art= 2,559  saving=2,510
```

18,830 bytes become 2,434. The finding was counted in raw bytes; the visitor
pays gzipped ones.

**What would extraction amortise against?** The art is unique per tenant, and:

```xml
<urlset><url><loc>https://pantheonlabs.info/site/c3bcfd29-...</loc></url></urlset>
```

The only tenant with heavy art has **exactly one page**. There is no second
navigation to save, and a separate request would block the hero paint on the
one page that exists.

Closed without change, with the numbers recorded in the commit so the next
person does not re-open it.

---

## The same failure, twice more, mid-fix

The artefacts above were findings that never existed. Two more appeared while
fixing the real ones — measurements that would have made me draw the wrong
conclusion about my own work.

**The fix that appeared to do nothing.** I added a 44px tap-target floor scoped
to `@media (pointer: coarse)`, re-ran the probe, and got the identical
before-numbers. The CSS was correct; Playwright's default pointer is *fine*, not
coarse, so the media query never matched. `has_touch=True` fixed the probe. Had
I trusted the first run, I would have "fixed" working code.

**The test that passed on a constant.** The extracted stylesheet is cached
`immutable` for a year, so its URL carries a version. My first test asserted the
version's *shape*:

```python
assert len(v1) >= 8 and v1.isalnum()
```

The mutation harness replaced the function body with `return "constant0000"` and
the test still passed. With a year-long immutable cache, a frozen version pins
every returning visitor to the CSS they first saw — permanently. The test now
asserts the digest derivation.

---

## What I do differently now

1. **Reproduce before agreeing.** Three of eleven findings dissolved on contact.
   The cost of checking is minutes; the cost of "fixing" correct code is a
   regression plus the confidence that you fixed something.
2. **A probe is code, and it is the least-tested code you have.** Every
   measurement in this audit that disagreed with the source turned out to be the
   measurement's fault. `innerText` vs the accessibility tree, fine vs coarse
   pointers, `file://` vs http, raw vs gzipped bytes.
3. **Mutate the guard, not just the code.** Four of the tests written here
   passed first time and only one deserved to. A test that cannot fail is a
   comment with a run cost.
4. **Record the closes.** "Measured, not worth doing, here are the numbers"
   is a result. Without it the finding gets re-opened by the next reader — or by
   me, in three months.

---

## Verification

```
2,136 tests pass
8 fixes shipped and verified on the live renderer, not just locally
mutation harnesses: 3/3, 3/3, 3/3, 4/4, 3/3 across the fixes
home page 68,489 -> ~16,800 bytes (5.2KB on the wire)
```

Each fix's mutation harness is in the repo it belongs to; the pattern is the
same one in [walkthrough 03](../03-external-review/WALKTHROUGH.md): revert the
fix, the test must scream, restore it, the test must pass.

## Honest limits

- This was my own audit of my own product. An outsider would find a different
  eleven, and [walkthrough 03](../03-external-review/WALKTHROUGH.md) is what
  happened when one did.
- "Three of eleven were artefacts" is a count from one audit, not a rate.
- The fixes are verified on the live renderer for the tenants I checked, not
  across every tenant on the platform.

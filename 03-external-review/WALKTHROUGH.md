# Walkthrough 03: three findings from an external source review

Someone read the full PANTHEON source and reported three defects. This is what
I did with them — reproduce, fix, prove the fix load-bearing — and the moment
the process caught *my own* new test being decorative.

Unlike 01 (built fresh) and 02 (reconstructed), this one is about receiving
criticism of work already shipped. Commits: `a2fe99c`, `2ce188b`.

## 0. The findings

1. **The quality judge did not gate delivery.** The gate scored an answer,
   regenerated on a low score, then delivered the replacement *unscored* and
   with no failure flag.
2. **Priced settlement was not atomic.** Debit caller → run agent → credit
   provider are three separate operations, and the credit wrapper ignored a
   returned `Charge(ok=False)`.
3. **The executor adapter bypassed the durable tool cache.**
   `tool_step_handler()` passed `idempotency_key` but not `tenant_id`.

All three were correct.

## 1. Verify before agreeing (the repo's own rule)

CLAUDE.md in this repo says: quote the offending line, or you have a *memory*
of a defect, not a defect. So each finding got read at source before anything
was touched. Finding 3, line 137 of `tool_registry.py`:

    durable = self._store is not None and tenant_id is not None

and the adapter, line 99 of `executor/base.py`:

    result = await registry.invoke(tool_name, ctx.input,
                                   idempotency_key=ctx.idempotency_key)

Confirmed at the line level. The reviewer was right, and now so was I.

## 2. The shape shared by all three

Every one is a **seam** defect. The component keeps its promise; the caller
drops it at the boundary:

| Component guarantee | How the caller lost it |
|---|---|
| registry honours a durable store | adapter omitted the tenant |
| `grant()` reports refusal via `ok=False` | `earn()` caught only exceptions |
| the gate scores an answer | nobody scored the *second* answer |

There was even a passing test for the registry's durable store
(`test_tool_registry_idem.py`) — and none for the adapter that called it wrong.
A unit test proves a component keeps its promise in isolation. It says nothing
about whether the caller preserved it.

## 3. Fixes, each pinned by a test proven to fail without it

RED first for all three, then fixed:

- **R1**: re-judge the regenerated answer; a twice-failed turn sets
  `LoopResult.gate_failed`. The regenerate bound stays at one — unbounded
  regeneration is its own failure mode. Streaming still skips the pre-delivery
  judge *by stated policy* (the reader already saw the tokens; it is judged
  post-hoc for audit), which is now written down rather than implied.
- **R2**: `ok=False` is logged as loudly as a raise.
- **R3**: pass `tenant_id`. One argument. Also binds the calling tenant's RLS
  scope for executor tool calls.

Mutation proof — revert each fix, its test must scream:

    CAUGHT  R1 re-judge the regenerate      fixed: 2 passed   mutant: 2 failed
    CAUGHT  R2 earn reports ok=False        fixed: 2 passed   mutant: 1 failed
    CAUGHT  R3 adapter passes tenant_id     fixed: 1 passed   mutant: 1 failed

## 4. A guard the codebase set against itself, firing

The full suite then failed on something I had not touched:

    loop.py is 654 lines (> 650). This is a soft fence, not a hard rule:
    read the BOUNDARY CHARTER in loop.py — if the growth belongs elsewhere,
    move it; if it genuinely belongs here, bump this threshold in the same
    reviewed diff.

My 9 lines pushed an anti-god-module fence over its limit. The charter lists
"judge" as orchestration order that *does* belong in that module, so the
sanctioned action was to bump the fence in the same diff — which the error
message itself prescribes. A guard that tells you how to be right about
crossing it is worth more than one that only says no.

## 5. The test that caught itself being decorative

The reviewer's closing recommendation was a test following one request through
authorization → execution → accounting → interruption → recovery. I wrote it:
a T3 payment, gated, charged, crashed after the effect landed but before the
step was recorded, then resumed. **It passed first time** — which is the moment
to distrust a test.

So each guarantee got mutated in turn. Three of four mutations were caught.
One was not:

    VACUOUS durable replay: drop the tenant so the cache goes per-process
            2 passed

The test claimed to cover R3 and did not: my registry had no durable store
injected, so `durable` was False either way and the tenant argument was never
load-bearing. Fixed by injecting a recording store and asserting the cache was
read *and* written. Now:

    CAUGHT  authorization: let a T3 step run ungated
    CAUGHT  durable replay: drop the tenant so the cache goes per-process
    CAUGHT  accounting: make the charge non-idempotent
    CAUGHT  recovery: never resume after the crash

Final assertions after the crash: effect rows **1**, ledger rows **1**, balance
exactly **90.0**. Suite: 2,111.

## 6. Honest limits

- **R2 is only partly closed.** The silent `ok=False` is fixed; the gap the
  reviewer actually named — debit/run/credit are not atomic and there is no
  durable settlement record to reconcile from — is still open. A log line is
  not a settlement guarantee, and calling it closed would be the exact kind of
  overclaim this project keeps auditing itself for.
- The seam test runs against a dev Postgres, single worker. It does not prove
  behaviour under concurrency or load.
- The reviewer read an uploaded snapshot; I have not established it matches
  production byte for byte.

## 7. What I take from it

The findings were not bugs in careless code — every component was written with
its guarantee in mind. They were bugs in the **joins**. The durable store, the
settlement reporter and the quality gate each worked exactly as designed, and
each was silently disarmed one call up the stack.

The generalisation, now in my notes: *test the seam, not the component.* And
prefer one test that follows a request through its whole life over another
test of a part that already has one.

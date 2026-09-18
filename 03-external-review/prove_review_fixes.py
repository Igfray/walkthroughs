"""Mutation-prove the three external-review fixes: revert each, the test must fail."""
import re
import subprocess
from pathlib import Path

ROOT = Path("/home/legion/PANTHEON")
PY = ROOT / ".venv/bin/python"

CASES = [
    ("R1 re-judge the regenerate",
     "packages/pantheon-core/src/pantheon/runtime/loop.py",
     "            rescore = await guardrails.score_if_needed(answer, manifest)",
     "            rescore = None  # MUTANT: ship the replacement unjudged",
     "packages/pantheon-core/tests/test_gate_regenerate.py"),
    ("R2 earn reports ok=False",
     "apps/gateway/src/gateway/deps.py",
     "        if _res is not None and not getattr(_res, \"ok\", True):",
     "        if False:  # MUTANT: swallow a failed settlement",
     "apps/gateway/tests/test_mcp_settlement.py"),
    ("R3 adapter passes tenant_id",
     "packages/pantheon-core/src/pantheon/runtime/executor/base.py",
     "                                       tenant_id=ctx.tenant_id)",
     "                                       )",
     "packages/pantheon-core/tests/test_executor_durable_replay.py"),
]


def run_tests(path: str) -> tuple[bool, str]:
    r = subprocess.run(
        [str(PY), "-m", "pytest", path, "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True, timeout=300,
    )
    last = [ln for ln in r.stdout.strip().splitlines() if ln.strip()][-1]
    return r.returncode == 0, last


print("verifying each fix is load-bearing\n")
all_ok = True
for name, src, orig, mutant, test in CASES:
    f = ROOT / src
    before = f.read_text()
    assert orig in before, f"anchor missing for {name}: {orig!r}"

    ok_clean, line_clean = run_tests(test)
    f.write_text(before.replace(orig, mutant, 1))
    try:
        ok_mut, line_mut = run_tests(test)
    finally:
        f.write_text(before)
    ok_restored, _ = run_tests(test)

    caught = ok_clean and not ok_mut and ok_restored
    all_ok &= caught
    print(f"{'CAUGHT ' if caught else 'VACUOUS'} {name}")
    print(f"         fixed:  {line_clean}")
    print(f"         mutant: {line_mut}\n")

raise SystemExit(0 if all_ok else 1)

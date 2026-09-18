"""Prove the seam test is load-bearing: break each guarantee, it must fail.

A test that passes first time is the moment to distrust it. Four mutations,
each removing ONE guarantee the test claims to check.
"""
import subprocess
from pathlib import Path

ROOT = Path("/home/legion/PANTHEON")
PY = ROOT / ".venv/bin/python"
TEST = "packages/pantheon-core/tests/test_seam_end_to_end.py"

MUTATIONS = [
    ("authorization: let a T3 step run ungated",
     "packages/pantheon-core/src/pantheon/runtime/executor/base.py",
     "        if registry.is_consequential(tool_name):",
     "        if False:  # MUTANT: no gate for consequential tools"),
    ("durable replay: drop the tenant so the cache goes per-process",
     "packages/pantheon-core/src/pantheon/runtime/executor/base.py",
     "                                       tenant_id=ctx.tenant_id)",
     "                                       )"),
    ("accounting: make the charge non-idempotent",
     "packages/pantheon-core/tests/test_seam_end_to_end.py",
     'idempotency_key=f"charge:{rid}", engine=engine)\n        await ex.tick()',
     'idempotency_key=None, engine=engine)\n        await ex.tick()'),
    ("recovery: never resume after the crash",
     "packages/pantheon-core/tests/test_seam_end_to_end.py",
     "        await ex.drain()                           # RECOVERY",
     "        pass  # MUTANT: no recovery"),
]


def run() -> tuple[bool, str]:
    r = subprocess.run([str(PY), "-m", "pytest", TEST, "-q", "--no-header",
                        "-p", "no:cacheprovider"],
                       cwd=ROOT, capture_output=True, text=True, timeout=300)
    lines = [ln for ln in r.stdout.strip().splitlines() if ln.strip()]
    return r.returncode == 0, lines[-1] if lines else "(no output)"


ok, line = run()
print(f"unmutated: {line}\n")
assert ok, "the seam test must pass before mutation"

all_caught = True
for name, src, orig, mutant in MUTATIONS:
    f = ROOT / src
    before = f.read_text()
    if orig not in before:
        print(f"SKIP    {name}: anchor not found")
        all_caught = False
        continue
    f.write_text(before.replace(orig, mutant, 1))
    try:
        mut_ok, mut_line = run()
    finally:
        f.write_text(before)
    caught = not mut_ok
    all_caught &= caught
    print(f"{'CAUGHT ' if caught else 'VACUOUS'} {name}")
    print(f"        {mut_line}")

restored_ok, restored_line = run()
print(f"\nrestored: {restored_line}")
raise SystemExit(0 if (all_caught and restored_ok) else 1)

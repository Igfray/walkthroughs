"""Prove the settlement tests are load-bearing. [external review R2]"""
import subprocess
from pathlib import Path

ROOT = Path("/home/legion/PANTHEON")
PY = ROOT / ".venv/bin/python"
TEST = "apps/gateway/tests/test_settlement_reconcile.py"

MUTATIONS = [
    ("record nothing (back to the original defect)",
     "apps/gateway/src/gateway/deps.py",
     "            earn_key=idempotency_key) if payer_tenant else None",
     "            earn_key=idempotency_key) if False else None"),
    ("mark settled even when the credit failed",
     "apps/gateway/src/gateway/deps.py",
     '                provider_tenant, net, reason, idempotency_key, _sid)\n            return\n        settlement.mark_settled(_sid)',
     '                provider_tenant, net, reason, idempotency_key, _sid)\n        settlement.mark_settled(_sid)'),
    ("reaper closes every row, landed or not",
     "packages/pantheon-core/src/pantheon/substrate/settlement.py",
     "            if landed is not None:          # the credit DID land; only the marker was lost",
     "            if True:  # MUTANT: close everything"),
    ("reaper mints the missing credit",
     "packages/pantheon-core/src/pantheon/substrate/settlement.py",
     '                log.error("UNSETTLED component earning: settlement=%s provider=%s net=%s reason=%s",\n                          sid, provider, net, reason)',
     '                c.execute(text("INSERT INTO credit_ledger (id, tenant_id, delta, reason, balance_after) '
     'VALUES (gen_random_uuid(), :t, :d, :r, 0)"), {"t": str(provider), "d": float(net), "r": reason})'),
]


def run() -> tuple[bool, str]:
    r = subprocess.run([str(PY), "-m", "pytest", TEST, "-q", "--no-header",
                        "-p", "no:cacheprovider"],
                       cwd=ROOT, capture_output=True, text=True, timeout=300)
    lines = [ln for ln in r.stdout.strip().splitlines() if ln.strip()]
    return r.returncode == 0, lines[-1] if lines else "(no output)"


ok, line = run()
print(f"unmutated: {line}\n")
assert ok, "the settlement tests must pass before mutation"

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

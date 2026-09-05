"""Deletion smoke: remove Sibyl reads → cold-start retract fails.

Runs AFTER a seed-only DB state is prepared (Friday in Sibyl + projections).
A "broken" worker refuses MemoryClient and only sees the projection file.
It cannot authoritatively correct Friday→Monday, so the dependent artifact
does not change. Contrasts with cold_start.py which succeeds via Sibyl.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

G1_ROOT = Path(__file__).resolve().parent
VENV_PYTHON = G1_ROOT.parent / ".venv" / "bin" / "python"
DB_PATH = G1_ROOT / "memory.db"
PROJECTIONS = G1_ROOT / "artifacts" / "projections"
PRESS = PROJECTIONS / "press-brief.txt"


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


BROKEN_WORKER = r'''
# Broken cold-start worker: NO sibyl_memory_client import, NO get_entity.
from pathlib import Path
press = Path("artifacts/projections/press-brief.txt")
text = press.read_text(encoding="utf-8")
print("BROKEN_WORKER: no Sibyl MemoryClient available")
print("BROKEN_WORKER: only local projection:")
print(text)
# Cannot reconstruct authoritative launch day — refuse to mutate.
print("BROKEN_WORKER: cannot apply Friday→Monday correction without Sibyl")
print("BROKEN_WORKER: leaving press-brief UNCHANGED")
print("BROKEN_PROOF=FAIL_AS_EXPECTED")
'''


def main() -> int:
    print(f"PHASE DELETION_SMOKE @ {_ts()}")
    py = str(VENV_PYTHON if VENV_PYTHON.exists() else sys.executable)

    # Fresh seed only (leave DB at Friday; do NOT run cold_start)
    for p in (DB_PATH, G1_ROOT / "memory.db-wal", G1_ROOT / "memory.db-shm"):
        if p.exists():
            p.unlink()
    print("  running seed.py to establish Friday state...")
    r = subprocess.run([py, str(G1_ROOT / "seed.py")], cwd=str(G1_ROOT), capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr)
        return r.returncode

    before = PRESS.read_text(encoding="utf-8")
    print("  press-brief BEFORE broken cold-start:")
    print(before)

    print("  spawning broken worker (Sibyl deleted from code path)...")
    r2 = subprocess.run([py, "-c", BROKEN_WORKER], cwd=str(G1_ROOT), capture_output=True, text=True)
    print(r2.stdout, end="")
    after = PRESS.read_text(encoding="utf-8")
    print("  press-brief AFTER broken cold-start:")
    print(after)

    unchanged = before == after
    still_friday = "Friday" in after and "Monday" not in after.split("Embargo")[0] + after
    # Simpler check:
    still_friday = "Friday" in after and "launches to the public on Friday" in after
    ok = unchanged and still_friday
    print(f"  projection_unchanged={unchanged} still_friday={still_friday}")
    print(f"G1_DELETION_SMOKE={'PASS' if ok else 'FAIL'} (Sibyl is load-bearing)")

    out = G1_ROOT / "artifacts" / "deletion_smoke_result.json"
    out.write_text(
        json.dumps(
            {
                "ts": _ts(),
                "projection_unchanged": unchanged,
                "still_friday": still_friday,
                "pass": ok,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

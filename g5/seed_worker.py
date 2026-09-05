"""PROCESS A — SEED Friday into g5/memory.db, then EXIT (cold-start kill)."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import ops
from bridge import ARTIFACTS_DIR, DB_PATH, TENANT_ID
from hashes import CONTROL_ALWAYS, PRESS_FRIDAY


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    run_id = os.environ.get("G5_RUN_ID") or "unset"
    pid = os.getpid()
    print(f"PHASE SEED @ {_ts()}")
    print(f"  run_id={run_id}")
    print(f"  pid={pid}")
    print(f"  db={DB_PATH}")
    print(f"  tenant_id={TENANT_ID}")
    print(f"  python_state=empty (fresh process)")

    result = ops.seed(force=True, day="Friday")
    g = result["graph"]
    print(f"  svid={result['svid']}")
    print(f"  entity_ids={json.dumps(result['entity_ids'])}")
    print(f"CONTROL_HASH_BEFORE={g.get('control_sha256')}")
    print(f"PRESS_HASH_BEFORE={g.get('press_sha256')}")
    print(f"  control_ok={result['control_ok']} (expect {CONTROL_ALWAYS[:12]}…)")
    print(f"  press_ok={result['press_ok']} (expect {PRESS_FRIDAY[:12]}…)")

    # Snapshot before projections for continuous segment
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    before_press = ARTIFACTS_DIR / "projections" / "press-brief.txt"
    before_ctrl = ARTIFACTS_DIR / "projections" / "company-blurb.txt"
    snap_dir = ARTIFACTS_DIR / "before_projections"
    snap_dir.mkdir(parents=True, exist_ok=True)
    if before_press.exists():
        (snap_dir / "press-brief.txt").write_text(
            before_press.read_text(encoding="utf-8"), encoding="utf-8"
        )
    if before_ctrl.exists():
        (snap_dir / "company-blurb.txt").write_text(
            before_ctrl.read_text(encoding="utf-8"), encoding="utf-8"
        )

    seed_meta = {
        "phase": "SEED",
        "run_id": run_id,
        "pid": pid,
        "ts": _ts(),
        "db": str(DB_PATH),
        "svid": result["svid"],
        "entity_ids": result["entity_ids"],
        "control_sha256": g.get("control_sha256"),
        "press_sha256": g.get("press_sha256"),
    }
    meta_path = Path(ARTIFACTS_DIR) / "seed_meta.json"
    meta_path.write_text(json.dumps(seed_meta, indent=2), encoding="utf-8")
    print(f"  seed_meta -> {meta_path}")
    print("PHASE SEED DONE — process will EXIT (KILL); Sibyl state persists in DB")
    return 0 if result["control_ok"] and result["press_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

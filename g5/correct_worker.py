"""PROCESS B — fresh PID, empty Python state; read Sibyl only; Friday→Monday."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import ops
from bridge import ARTIFACTS_DIR, DB_PATH, TENANT_ID
from hashes import CONTROL_ALWAYS, PRESS_FRIDAY, PRESS_MONDAY


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    run_id = os.environ.get("G5_RUN_ID") or "unset"
    pid = os.getpid()
    print(f"PHASE CORRECT @ {_ts()}")
    print(f"  run_id={run_id}")
    print(f"  pid={pid}")
    print(f"  db={DB_PATH}")
    print(f"  tenant_id={TENANT_ID}")
    print(f"  python_state=empty (fresh process; no in-memory seed)")
    print(f"  SoT=Sibyl only at {DB_PATH}")

    if not Path(DB_PATH).exists():
        print("G5_PROOF=FAIL reason=missing_db")
        return 1

    # Capture pointers BEFORE correction (live Friday from Sibyl)
    pointers_before = ops.capture_sibyl_pointers(phase="before_correct_read")
    print(
        "  sibyl_read live day="
        f"{(pointers_before.get('entities') or {}).get('novadesk-launch', {}).get('day')}"
        f" svid={pointers_before.get('source_version_ids', {}).get('live')}"
    )

    result = ops.correct(day="Monday", reason="Calendar confirmed Monday.")
    print(f"  old_svid={result['old_svid']}")
    print(f"  new_svid={result['new_svid']}")
    print(f"  regenerated={result['regenerated']}")
    print(f"CONTROL_HASH_AFTER={result['control_sha256']}")
    print(f"PRESS_HASH_AFTER={result['press_sha256']}")

    pointers_after = ops.capture_sibyl_pointers(phase="after_correct")
    pointers = {
        "run_id": run_id,
        "correct_pid": pid,
        "db_path": str(DB_PATH),
        "tenant_id": TENANT_ID,
        "before": pointers_before,
        "after": pointers_after,
        "locked_hashes": {
            "control_always": CONTROL_ALWAYS,
            "press_friday": PRESS_FRIDAY,
            "press_monday": PRESS_MONDAY,
        },
    }
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    ptr_path = ARTIFACTS_DIR / "g5_sibyl_pointers.json"
    ptr_path.write_text(json.dumps(pointers, indent=2), encoding="utf-8")
    print(f"  sibyl_pointers -> {ptr_path}")

    # Load before hashes from seed graph if present
    before_path = ARTIFACTS_DIR / "before_graph.json"
    control_before = None
    press_before = None
    if before_path.exists():
        before = json.loads(before_path.read_text(encoding="utf-8"))
        control_before = before.get("control_sha256")
        press_before = before.get("press_sha256")
        print(f"CONTROL_HASH_BEFORE={control_before}")
        print(f"PRESS_HASH_BEFORE={press_before}")

    control_ok = result["control_sha256"] == CONTROL_ALWAYS
    press_ok = result["press_sha256"] == PRESS_MONDAY
    control_unchanged = (
        control_before is None or control_before == result["control_sha256"]
    )
    press_changed = press_before is None or (
        press_before != result["press_sha256"] and press_before == PRESS_FRIDAY
    )
    trail_ok = any(
        (not s.get("archived")) and s.get("supersedes") == result["old_svid"]
        for s in result["graph"].get("sources") or []
    ) and any(
        s.get("archived") and s.get("source_version_id") == result["old_svid"]
        for s in result["graph"].get("sources") or []
    )
    monday_ok = any(
        (not s.get("archived")) and s.get("day") == "Monday"
        for s in result["graph"].get("sources") or []
    )

    passed = (
        control_ok
        and press_ok
        and control_unchanged
        and press_changed
        and trail_ok
        and monday_ok
        and bool(result["regenerated"])
    )
    proof = "PASS" if passed else "FAIL"
    print(f"  control_ok={control_ok} press_ok={press_ok}")
    print(f"  control_unchanged={control_unchanged} press_changed={press_changed}")
    print(f"  supersedes_trail_ok={trail_ok} monday_ok={monday_ok}")
    print(f"G5_PROOF={proof}")

    seed_meta = {}
    seed_meta_path = ARTIFACTS_DIR / "seed_meta.json"
    if seed_meta_path.exists():
        seed_meta = json.loads(seed_meta_path.read_text(encoding="utf-8"))

    out = {
        "phase": "CORRECT",
        "run_id": run_id,
        "seed_pid": seed_meta.get("pid"),
        "correct_pid": pid,
        "pids_distinct": seed_meta.get("pid") != pid if seed_meta.get("pid") else None,
        "ts": _ts(),
        "db": str(DB_PATH),
        "old_svid": result["old_svid"],
        "new_svid": result["new_svid"],
        "control_sha256": result["control_sha256"],
        "press_sha256": result["press_sha256"],
        "expected": {
            "control": CONTROL_ALWAYS,
            "press": PRESS_MONDAY,
        },
        "control_ok": control_ok,
        "press_ok": press_ok,
        "control_unchanged": control_unchanged,
        "press_changed": press_changed,
        "supersedes_trail_ok": trail_ok,
        "monday_ok": monday_ok,
        "regenerated": result["regenerated"],
        "G5_PROOF": proof,
    }
    result_path = ARTIFACTS_DIR / "g5_result.json"
    result_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"  result -> {result_path}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())

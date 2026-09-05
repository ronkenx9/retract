#!/usr/bin/env python3
"""RETRACT G4 adversarial suite runner — local only, G4 DBs only."""
from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

G4_ROOT = Path(__file__).resolve().parent
if str(G4_ROOT) not in sys.path:
    sys.path.insert(0, str(G4_ROOT))

from bridge import DB_PATH, DB_PATH_B, TENANT_A, rebind_db  # noqa: E402
from cases import (  # noqa: E402
    concurrent_requests,
    conflicting_sources,
    deletion_litmus,
    repeated_corrections,
    stale_cache,
    tenant_separation,
)


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


CASES = [
    ("stale_ui_projection_cache", stale_cache.run),
    ("repeated_corrections", repeated_corrections.run),
    ("conflicting_sources", conflicting_sources.run),
    ("tenant_separation", tenant_separation.run),
    ("deleted_memory_litmus", deletion_litmus.run),
    ("concurrent_requests", concurrent_requests.run),
]


def main() -> int:
    artifacts = G4_ROOT / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "projections").mkdir(parents=True, exist_ok=True)

    # Ensure default binding
    rebind_db(DB_PATH, TENANT_A)

    print(f"G4 ADVERSARIAL SUITE @ {_ts()}")
    print(f"  g4_root={G4_ROOT}")
    print(f"  db_a={DB_PATH}")
    print(f"  db_b={DB_PATH_B}")
    print(f"  cases={len(CASES)}")
    print()

    results: list[dict] = []
    all_pass = True

    for name, fn in CASES:
        print(f"=== CASE {name} @ {_ts()} ===")
        try:
            rebind_db(DB_PATH, TENANT_A)
            out = fn()
            passed = bool(out.get("pass"))
            out.setdefault("case", name)
            results.append(out)
            status = "PASS" if passed else "FAIL"
            print(f"  RESULT {name}={status}")
            # Compact one-liner extras
            for k in (
                "sibyl_day",
                "cache_day",
                "live_day",
                "refused_regen",
                "tenant_a_day",
                "tenant_b_day_same_db",
                "final_live_day",
                "control_unchanged",
                "stale_detected",
            ):
                if k in out:
                    print(f"    {k}={out[k]}")
            if name == "deleted_memory_litmus":
                print(f"    normal_pass={out.get('normal', {}).get('pass')}")
                print(f"    blocked_pass={out.get('blocked', {}).get('pass')}")
                print(f"    missing_pass={out.get('missing_db', {}).get('pass')}")
            if not passed:
                all_pass = False
                print(f"    detail={json.dumps({k: out[k] for k in out if k != 'conflicts'}, default=str)[:500]}")
        except Exception as e:
            all_pass = False
            err = {
                "case": name,
                "pass": False,
                "error": f"{type(e).__name__}: {e}",
                "traceback": traceback.format_exc(),
            }
            results.append(err)
            print(f"  RESULT {name}=FAIL exception={e}")
            print(traceback.format_exc())
        print()

    proof = "PASS" if all_pass else "FAIL"
    payload = {
        "suite": "G4_ADVERSARIAL",
        "ts": _ts(),
        "G4_PROOF": proof,
        "all_pass": all_pass,
        "cases": results,
        "dbs": {"memory_a": str(DB_PATH), "memory_b": str(DB_PATH_B)},
    }
    out_path = artifacts / "g4_results.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"results -> {out_path}")
    print()
    print("PER-CASE SUMMARY")
    print(f"{'case':<32} {'result':<6}")
    print("-" * 40)
    for r in results:
        print(f"{r.get('case', '?'):<32} {'PASS' if r.get('pass') else 'FAIL':<6}")
    print("-" * 40)
    print(f"G4_PROOF={proof}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())

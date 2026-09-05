#!/usr/bin/env python3
"""Seed → correct and seed → dispute; exit 0 only if locked hashes match."""
from __future__ import annotations

import sys
from pathlib import Path

G3 = Path(__file__).resolve().parent
sys.path.insert(0, str(G3))

import ops  # noqa: E402
from g2_bridge import DB_PATH  # noqa: E402
from hashes import (  # noqa: E402
    CONTROL_ALWAYS,
    PRESS_DISPUTE,
    PRESS_FRIDAY,
    PRESS_MONDAY,
)

OUT = G3 / "artifacts" / "g3_verify.txt"


def main() -> int:
    lines: list[str] = []
    overall = True

    def log(msg: str) -> None:
        print(msg)
        lines.append(msg)

    log("===== RETRACT G3 HASH VERIFY =====")
    log(f"db={DB_PATH}")

    log("--- PATH A: seed → correct ---")
    a = ops.seed(force=True)
    log(f"SEED control={a['graph']['control_sha256']}")
    log(f"SEED press={a['graph']['press_sha256']}")
    seed_ok = (
        a["graph"]["control_sha256"] == CONTROL_ALWAYS
        and a["graph"]["press_sha256"] == PRESS_FRIDAY
        and a["checks"]["control_ok"]
        and a["checks"]["press_ok"]
    )
    log(f"SEED_LOCKED={'PASS' if seed_ok else 'FAIL'}")

    c = ops.correct(day="Monday", reason="Calendar confirmed Monday.")
    log(f"CORRECT control={c['graph']['control_sha256']}")
    log(f"CORRECT press={c['graph']['press_sha256']}")
    path_a = (
        seed_ok
        and c["graph"]["control_sha256"] == CONTROL_ALWAYS
        and c["graph"]["press_sha256"] == PRESS_MONDAY
        and c["checks"]["control_ok"]
        and c["checks"]["press_ok"]
        and c.get("hash_check", {}).get("passed", False)
    )
    log(f"PATH_A={'PASS' if path_a else 'FAIL'}")
    overall = overall and path_a

    log("--- PATH B: seed → dispute ---")
    ops.seed(force=True)
    d = ops.dispute(reason="Launch day disputed; treat as not established.")
    log(f"DISPUTE control={d['graph']['control_sha256']}")
    log(f"DISPUTE press={d['graph']['press_sha256']}")
    path_b = (
        d["graph"]["control_sha256"] == CONTROL_ALWAYS
        and d["graph"]["press_sha256"] == PRESS_DISPUTE
        and d["checks"]["control_ok"]
        and d["checks"]["press_ok"]
        and d.get("hash_check", {}).get("passed", False)
    )
    log(f"PATH_B={'PASS' if path_b else 'FAIL'}")
    overall = overall and path_b

    log(f"CONTROL={CONTROL_ALWAYS}")
    log(f"PRESS_FRI={PRESS_FRIDAY}")
    log(f"PRESS_MON={PRESS_MONDAY}")
    log(f"PRESS_NE={PRESS_DISPUTE}")

    # Leave Friday baseline for the desk
    ops.seed(force=True)
    log("reseeded Friday baseline for desk")

    proof = "PASS" if overall else "FAIL"
    log(f"G3_PROOF={proof}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())

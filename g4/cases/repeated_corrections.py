"""Case 2 — Repeated corrections Friday→Monday→Tuesday; control hash stable."""
from __future__ import annotations

from typing import Any

from hashes import CONTROL_ALWAYS, PRESS_MONDAY, PRESS_TUESDAY
from ops import correct_to, seed


def run() -> dict[str, Any]:
    seed(force=True, day="Friday")
    r1 = correct_to(
        "Monday",
        reason="Calendar confirmed Monday.",
        correction_name="friday-to-monday-approved",
        expect_from="Friday",
    )
    r2 = correct_to(
        "Tuesday",
        reason="Calendar re-approved Tuesday.",
        correction_name="monday-to-tuesday-approved",
        expect_from="Monday",
    )

    g = r2["graph"]
    live_sources = [s for s in g["sources"] if not s.get("archived")]
    archived = [s for s in g["sources"] if s.get("archived")]
    live_day = next((s.get("day") for s in live_sources), None)

    # Each correction supersedes prior: Tuesday live; Friday+Monday archived
    archived_days = {s.get("day") for s in archived}
    supersedes_ok = (
        live_day == "Tuesday"
        and "Friday" in archived_days
        and "Monday" in archived_days
        and any(s.get("supersedes") == r1["old_svid"] for s in live_sources + archived)
        and any(s.get("supersedes") == r2["old_svid"] for s in live_sources)
    )

    control_ok = (
        r1.get("control_sha256") == CONTROL_ALWAYS
        and r2.get("control_sha256") == CONTROL_ALWAYS
        and g.get("control_sha256") == CONTROL_ALWAYS
    )
    press_ok = (
        r1.get("press_sha256") == PRESS_MONDAY
        and r2.get("press_sha256") == PRESS_TUESDAY
    )

    passed = supersedes_ok and control_ok and press_ok and bool(r1["regenerated"]) and bool(r2["regenerated"])

    return {
        "case": "repeated_corrections",
        "pass": passed,
        "steps": [
            {"from": r1["old_day"], "to": r1["new_day"], "press": r1["press_sha256"]},
            {"from": r2["old_day"], "to": r2["new_day"], "press": r2["press_sha256"]},
        ],
        "live_day": live_day,
        "archived_days": sorted(d for d in archived_days if d),
        "control_sha256": g.get("control_sha256"),
        "control_unchanged": control_ok,
        "control_locked": CONTROL_ALWAYS,
        "press_sha256": g.get("press_sha256"),
        "press_monday": PRESS_MONDAY,
        "press_tuesday": PRESS_TUESDAY,
        "supersedes_chain_ok": supersedes_ok,
    }

"""Case 5 — Deleted memory litmus: Sibyl available PASS; blocked FAIL."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest import mock

from bridge import ARTIFACTS_DIR, NAME_CONTROL, NAME_PRESS, PROJECTIONS_DIR, memory_io
from hashes import CONTROL_ALWAYS, PRESS_FRIDAY, PRESS_MONDAY
from ops import correct_to, seed, wipe_db


def _selective_invalidation_ok(result: dict[str, Any]) -> bool:
    return (
        result.get("new_day") == "Monday"
        and result.get("press_sha256") == PRESS_MONDAY
        and result.get("control_sha256") == CONTROL_ALWAYS
        and bool(result.get("regenerated"))
    )


def _run_normal() -> dict[str, Any]:
    seed(force=True, day="Friday")
    result = correct_to(
        "Monday",
        reason="Litmus normal path Monday.",
        expect_from="Friday",
    )
    ok = _selective_invalidation_ok(result)
    return {
        "mode": "sibyl_available",
        "pass": ok,
        "press_sha256": result.get("press_sha256"),
        "control_sha256": result.get("control_sha256"),
        "regenerated": result.get("regenerated"),
        "day": result.get("new_day"),
    }


def _run_blocked_monkeypatch() -> dict[str, Any]:
    """With Sibyl reads blocked, selective invalidation must FAIL."""
    seed(force=True, day="Friday")
    press_before = (PROJECTIONS_DIR / f"{NAME_PRESS}.txt").read_text(encoding="utf-8")
    control_before_hash = memory_io.content_sha256(
        (PROJECTIONS_DIR / f"{NAME_CONTROL}.txt").read_text(encoding="utf-8")
    )

    # Optional JSON "fact store" that must NOT rescue correction
    fake_store = ARTIFACTS_DIR / "parallel_json_fact_store.json"
    fake_store.write_text(
        json.dumps({"launch_day": "Monday", "note": "must not rescue"}),
        encoding="utf-8",
    )

    err: str | None = None
    corrected = False
    try:
        with mock.patch.object(
            memory_io,
            "open_memory",
            side_effect=RuntimeError("SIBYL_BLOCKED: open_memory unavailable"),
        ), mock.patch.object(
            memory_io,
            "read_site_source",
            side_effect=RuntimeError("SIBYL_BLOCKED: get_entity unavailable"),
        ):
            # Product-like path: cannot correct without Sibyl; must not use JSON store
            try:
                correct_to("Monday", reason="Should fail without Sibyl.")
                corrected = True
            except Exception as e:  # noqa: BLE001
                err = f"{type(e).__name__}: {e}"
    except Exception as e:  # noqa: BLE001
        err = f"{type(e).__name__}: {e}"

    press_after = (PROJECTIONS_DIR / f"{NAME_PRESS}.txt").read_text(encoding="utf-8")
    still_friday = "launches to the public on Friday" in press_after
    unchanged = press_before == press_after
    # Prove JSON store was present but unused
    json_exists = fake_store.exists()
    json_says_monday = json.loads(fake_store.read_text(encoding="utf-8")).get("launch_day") == "Monday"

    # PASS criterion for blocked half: selective invalidation FAILED / degraded
    blocked_failed_as_expected = (
        not corrected
        and err is not None
        and still_friday
        and unchanged
        and control_before_hash == CONTROL_ALWAYS
        and json_exists
        and json_says_monday  # store tempted Monday but did not apply
    )

    return {
        "mode": "sibyl_blocked_monkeypatch",
        "pass": blocked_failed_as_expected,  # litmus expects FAIL of correction
        "correction_attempted": True,
        "correction_succeeded": corrected,
        "error": err,
        "projection_unchanged": unchanged,
        "still_friday": still_friday,
        "parallel_json_store_present": json_exists,
        "parallel_json_said_monday": json_says_monday,
        "parallel_json_rescued": corrected and json_exists,  # must be False
        "press_sha256": memory_io.content_sha256(press_after),
        "expected_press_friday": PRESS_FRIDAY,
    }


def _run_missing_db() -> dict[str, Any]:
    """Point at missing DB — no fallback JSON store may rescue."""
    from bridge import DB_PATH, rebind_db, TENANT_A

    missing = Path(str(DB_PATH)).parent / "memory_missing_litmus.db"
    wipe_db(missing)
    if missing.exists():
        missing.unlink()
    rebind_db(missing, TENANT_A)

    fake_store = ARTIFACTS_DIR / "parallel_json_fact_store_missing.json"
    fake_store.write_text(json.dumps({"launch_day": "Monday"}), encoding="utf-8")

    err = None
    corrected = False
    try:
        # open_memory may create empty DB; get_entity for source should fail / empty
        try:
            correct_to("Monday", reason="Missing DB should not correct.")
            corrected = True
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {e}"
    finally:
        rebind_db(DB_PATH, TENANT_A)
        wipe_db(missing)

    # If somehow "succeeded", still check it didn't come from JSON
    failed_or_degraded = not corrected
    return {
        "mode": "sibyl_missing_db",
        "pass": failed_or_degraded and err is not None,
        "correction_succeeded": corrected,
        "error": err,
        "parallel_json_store_present": fake_store.exists(),
    }


def run() -> dict[str, Any]:
    normal = _run_normal()
    blocked = _run_blocked_monkeypatch()
    missing = _run_missing_db()

    # Overall: normal PASS + blocked FAIL-as-expected + missing FAIL-as-expected
    # and no JSON rescue
    passed = (
        normal["pass"] is True
        and blocked["pass"] is True
        and missing["pass"] is True
        and blocked.get("parallel_json_rescued") is False
    )

    return {
        "case": "deleted_memory_litmus",
        "pass": passed,
        "normal": normal,
        "blocked": blocked,
        "missing_db": missing,
        "detail": (
            "With Sibyl: selective invalidation PASS. "
            "With Sibyl blocked/missing: correction FAIL; parallel JSON store does not rescue."
        ),
    }

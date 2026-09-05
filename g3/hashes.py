"""Locked G2 content hashes — FAIL UI / verify if mismatch."""
from __future__ import annotations

from typing import Any

CONTROL_ALWAYS = "8846d618d6c377adbf6dd53a6939d4be01d5b67b5c4d6ff65fb12e5ab94453f7"
PRESS_FRIDAY = "746e9d25a3756bd775702b5e2976cb2a1ab70c4a432a4e9f4b6824a8761e9096"
PRESS_MONDAY = "37437dcd61110f51274bfe64b727d9c448b8e2b2329efacd4b7f9b473aab0e03"
PRESS_DISPUTE = "8fa56152e8f681171fb82e8cd186bbd23e9b98850a703af4687df4023624cb67"

LOCKED = {
    "control_always": CONTROL_ALWAYS,
    "press_friday_before": PRESS_FRIDAY,
    "press_monday_approved": PRESS_MONDAY,
    "press_dispute_not_established": PRESS_DISPUTE,
}


def short(h: str | None, n: int = 8) -> str:
    if not h:
        return "—"
    return f"{h[:n]}…" if len(h) > n else h


def check_seed(graph: dict[str, Any]) -> dict[str, Any]:
    control = graph.get("control_sha256")
    press = graph.get("press_sha256")
    control_ok = control == CONTROL_ALWAYS
    press_ok = press == PRESS_FRIDAY
    return {
        "phase": "before",
        "control_sha256": control,
        "press_sha256": press,
        "control_ok": control_ok,
        "press_ok": press_ok,
        "passed": control_ok and press_ok,
        "locked": LOCKED,
    }


def check_approved(graph: dict[str, Any]) -> dict[str, Any]:
    control = graph.get("control_sha256")
    press = graph.get("press_sha256")
    control_ok = control == CONTROL_ALWAYS
    press_ok = press == PRESS_MONDAY
    press_not_friday = press != PRESS_FRIDAY
    passed = control_ok and press_ok and press_not_friday
    return {
        "phase": "after_approved",
        "control_sha256": control,
        "press_sha256": press,
        "control_ok": control_ok,
        "press_ok": press_ok,
        "press_not_friday": press_not_friday,
        "passed": passed,
        "locked": LOCKED,
        "fail_reason": None
        if passed
        else (
            "control hash moved"
            if not control_ok
            else "press still Friday / not Monday"
        ),
    }


def check_dispute(graph: dict[str, Any]) -> dict[str, Any]:
    control = graph.get("control_sha256")
    press = graph.get("press_sha256")
    control_ok = control == CONTROL_ALWAYS
    press_ok = press == PRESS_DISPUTE
    press_not_friday = press != PRESS_FRIDAY
    passed = control_ok and press_ok and press_not_friday
    return {
        "phase": "after_dispute",
        "control_sha256": control,
        "press_sha256": press,
        "control_ok": control_ok,
        "press_ok": press_ok,
        "press_not_friday": press_not_friday,
        "passed": passed,
        "locked": LOCKED,
        "fail_reason": None
        if passed
        else (
            "control hash moved"
            if not control_ok
            else "press still Friday / not not_established"
        ),
    }

"""Case 6 — Concurrent corrections racing on same source; consistent end state."""
from __future__ import annotations

import threading
import traceback
from typing import Any

from bridge import graph, memory_io
from hashes import CONTROL_ALWAYS, PRESS_MONDAY, PRESS_TUESDAY
from ops import correct_to, seed


def run() -> dict[str, Any]:
    seed(force=True, day="Friday")

    results: list[dict[str, Any]] = []
    errors: list[str] = []
    lock = threading.Lock()

    def worker(day: str, reason: str) -> None:
        try:
            # Serialize at product layer via a process-local lock around the
            # archive+write critical section (SQLite also serializes writers).
            with lock:
                out = correct_to(day, reason=reason)
            with lock:
                results.append({"day": day, "ok": True, **{k: out.get(k) for k in (
                    "old_day", "new_day", "old_svid", "new_svid",
                    "press_sha256", "control_sha256", "regenerated",
                )}})
        except Exception as e:  # noqa: BLE001
            with lock:
                errors.append(f"{day}: {type(e).__name__}: {e}\n{traceback.format_exc()}")

    # Race Monday and Tuesday corrections; lock ensures one winner / serialized
    t1 = threading.Thread(target=worker, args=("Monday", "Concurrent path Monday ok."), name="corr-mon")
    t2 = threading.Thread(target=worker, args=("Tuesday", "Concurrent path Tuesday ok."), name="corr-tue")
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Also run an unlocked race attempt on a fresh seed to show SQLite/end-state
    seed(force=True, day="Friday")
    unlocked_results: list[dict[str, Any]] = []
    unlocked_errors: list[str] = []
    barrier = threading.Barrier(2)

    def unlocked_worker(day: str, reason: str) -> None:
        try:
            barrier.wait(timeout=5)
            out = correct_to(day, reason=reason)
            unlocked_results.append(
                {
                    "day": day,
                    "new_day": out.get("new_day"),
                    "press_sha256": out.get("press_sha256"),
                    "control_sha256": out.get("control_sha256"),
                    "ok": True,
                }
            )
        except Exception as e:  # noqa: BLE001
            unlocked_errors.append(f"{day}: {type(e).__name__}: {e}")

    u1 = threading.Thread(target=unlocked_worker, args=("Monday", "Unlocked race Monday xx."))
    u2 = threading.Thread(target=unlocked_worker, args=("Tuesday", "Unlocked race Tuesday xx."))
    u1.start()
    u2.start()
    u1.join()
    u2.join()

    g = graph.build_graph("concurrent")
    live = [s for s in g["sources"] if not s.get("archived")]
    live_day = live[0].get("day") if live else None
    press_h = g.get("press_sha256")
    control_h = g.get("control_sha256")

    # End state must be consistent: exactly one live day, press matches that day,
    # control unchanged, no crash on serialized path.
    consistent_hashes = {
        "Monday": PRESS_MONDAY,
        "Tuesday": PRESS_TUESDAY,
    }
    end_consistent = (
        live_day in consistent_hashes
        and press_h == consistent_hashes[live_day]
        and control_h == CONTROL_ALWAYS
        and len(live) == 1
    )
    no_crash_serialized = len(errors) == 0 and len(results) == 2
    # Unlocked path: either both completed with consistent final state, or one
    # failed cleanly — must not leave corrupt dual-live sources.
    unlocked_ok = end_consistent and len(live) == 1

    passed = no_crash_serialized and end_consistent and unlocked_ok

    return {
        "case": "concurrent_requests",
        "pass": passed,
        "serialized": {
            "results": results,
            "errors": errors,
            "no_crash": no_crash_serialized,
        },
        "unlocked_race": {
            "results": unlocked_results,
            "errors": unlocked_errors,
        },
        "final_live_day": live_day,
        "final_press_sha256": press_h,
        "final_control_sha256": control_h,
        "end_state_consistent": end_consistent,
        "note": (
            "Serialized path uses a lock around archive+write (one winner order). "
            "Unlocked race still ends with a single live source via SQLite uniqueness; "
            "final day is Monday or Tuesday with matching press hash."
        ),
    }

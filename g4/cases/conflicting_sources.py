"""Case 3 — Conflicting sources: detect conflict; refuse ambiguous regen."""
from __future__ import annotations

from typing import Any

from bridge import (
    CAT_CLAIM,
    NAME_CLAIM_PRESS,
    NAME_CONTROL,
    NAME_PRESS,
    STATUS_ACTIVE,
    memory_io,
)
from hashes import CONTROL_ALWAYS, PRESS_FRIDAY
from ops import detect_claim_conflicts, refuse_ambiguous_regen, seed


ALT_CLAIM = "press-brief-cites-launch-alt"


def run() -> dict[str, Any]:
    seeded = seed(force=True, day="Friday")
    memory = memory_io.open_memory()
    live = memory_io.read_site_source(memory)
    live_svid = live["body"]["source_version_id"]

    # Inject a second disagreeing live claim asserting Tuesday with a fake svid
    alt_svid = memory_io.new_id()
    memory.set_entity(
        CAT_CLAIM,
        ALT_CLAIM,
        {
            "artifact": NAME_PRESS,
            "source_version_id": alt_svid,
            "quote": "NovaDesk public launch is on Tuesday.",
            "span": "launch-day",
            "status": STATUS_ACTIVE,
        },
        status="active",
    )

    conflicts = detect_claim_conflicts(memory)
    gate = refuse_ambiguous_regen(memory)

    # Snapshot press + control BEFORE any attempted merge
    press_before = memory_io.read_site_artifact(memory, NAME_PRESS)
    control_before = memory_io.read_site_artifact(memory, NAME_CONTROL)
    press_hash_before = press_before["body"]["content_sha256"]
    control_hash_before = control_before["body"]["content_sha256"]

    # Attempt a naive "merge" regen — product path must refuse
    regenerated = []
    if not gate["refused"]:
        # Would be a bug — silently merge
        regenerated.append(NAME_PRESS)
    else:
        # Documented behavior: archive alt claim path rather than merge
        memory.archive_entity(CAT_CLAIM, ALT_CLAIM, reason="conflict: disagreeing live claim")
        # Still refuse regen until single coherent source; leave press Friday
        regenerated = []

    press_after = memory_io.read_site_artifact(memory, NAME_PRESS)
    control_after = memory_io.read_site_artifact(memory, NAME_CONTROL)
    press_hash_after = press_after["body"]["content_sha256"]
    control_hash_after = control_after["body"]["content_sha256"]

    conflict_detected = any(
        c.get("type") in ("disagreeing_live_claims", "claim_svid_mismatch", "claim_day_mismatch")
        for c in conflicts
    )
    dependents_consistent = (
        press_hash_before == press_hash_after == PRESS_FRIDAY
        and control_hash_before == control_hash_after == CONTROL_ALWAYS
        and not regenerated
    )
    refused = gate["refused"] is True

    passed = conflict_detected and refused and dependents_consistent

    return {
        "case": "conflicting_sources",
        "pass": passed,
        "behavior": (
            "Detect disagreeing live claims; refuse ambiguous regen; "
            "archive conflicting claim path; leave dependents unchanged "
            "until resolution. No silent merge."
        ),
        "conflicts": conflicts,
        "refused_regen": refused,
        "refuse_reason": gate.get("reason"),
        "press_unchanged": press_hash_before == press_hash_after,
        "control_unchanged": control_hash_before == control_hash_after,
        "press_sha256": press_hash_after,
        "control_sha256": control_hash_after,
        "live_svid": live_svid,
        "alt_svid": alt_svid,
        "seed_svid": seeded["svid"],
        "primary_claim": NAME_CLAIM_PRESS,
        "alt_claim": ALT_CLAIM,
    }

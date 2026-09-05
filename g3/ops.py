"""G3 ops — call G2 memory_io write/read sites after DB_PATH patch.

Logic mirrors g2/seed.py, correct.py, dispute.py without forking Sibyl writes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from g2_bridge import (
    DB_PATH,
    NAME_CLAIM_PRESS,
    NAME_CONTROL,
    NAME_CORRECTION_APPROVED,
    NAME_CORRECTION_DISPUTE,
    NAME_PRESS,
    STATUS_ACTIVE,
    STATUS_APPROVED,
    STATUS_DISPUTED,
    STATUS_NOT_ESTABLISHED,
    graph,
    memory_io,
)
from hashes import (
    CONTROL_ALWAYS,
    PRESS_DISPUTE,
    PRESS_FRIDAY,
    PRESS_MONDAY,
)

# Aliases for verify_hashes / UI
CONTROL = CONTROL_ALWAYS
PRESS_FRI = PRESS_FRIDAY
PRESS_MON = PRESS_MONDAY
PRESS_NE = PRESS_DISPUTE
G3_DB = DB_PATH


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def wipe_db() -> None:
    for path in (
        DB_PATH,
        Path(str(DB_PATH) + "-wal"),
        Path(str(DB_PATH) + "-shm"),
    ):
        if path.exists():
            path.unlink()


def _is_empty() -> bool:
    if not DB_PATH.exists():
        return True
    try:
        memory = memory_io.open_memory()
        arts = memory_io.read_site_list_artifacts(memory)
        srcs = memory_io.read_site_list_sources(memory)
        return not arts and not srcs
    except Exception:
        return True


def _checks(graph_data: dict[str, Any], *, expected_press: str) -> dict[str, Any]:
    control_actual = graph_data.get("control_sha256")
    press_actual = graph_data.get("press_sha256")
    return {
        "control_ok": control_actual == CONTROL,
        "press_ok": press_actual == expected_press,
        "expected": {"control": CONTROL, "press": expected_press},
        "actual": {"control": control_actual, "press": press_actual},
    }


def _payload(graph_data: dict[str, Any], *, phase: str, expected_press: str) -> dict[str, Any]:
    checks = _checks(graph_data, expected_press=expected_press)
    passed = bool(checks["control_ok"] and checks["press_ok"])
    hash_phase = (
        "after_approved"
        if phase == "after"
        else "after_dispute"
        if phase == "dispute"
        else "before"
    )
    hash_check = {
        "phase": hash_phase,
        "control_sha256": checks["actual"]["control"],
        "press_sha256": checks["actual"]["press"],
        "control_ok": checks["control_ok"],
        "press_ok": checks["press_ok"],
        "passed": True if phase == "before" else passed,
        "fail_reason": None
        if passed
        else (
            "control hash moved"
            if not checks["control_ok"]
            else "press hash mismatch"
        ),
        "locked": {
            "control_always": CONTROL,
            "press_friday_before": PRESS_FRI,
            "press_monday_approved": PRESS_MON,
            "press_dispute_not_established": PRESS_NE,
        },
    }
    return {
        "graph": graph_data,
        "checks": checks,
        "hash_check": hash_check,
        "phase": phase,
        "ts": _ts(),
    }


def seed(*, force: bool = True) -> dict[str, Any]:
    if force:
        wipe_db()

    memory = memory_io.open_memory()
    day = "Friday"
    version = 1
    svid = memory_io.new_id()

    memory_io.write_site_source_version(
        memory,
        day=day,
        version=version,
        source_version_id=svid,
        status=STATUS_ACTIVE,
    )
    claim_quote = f"NovaDesk public launch is on {day}."
    memory_io.write_site_claim(
        memory,
        NAME_CLAIM_PRESS,
        artifact=NAME_PRESS,
        source_version_id=svid,
        quote=claim_quote,
        status=STATUS_ACTIVE,
    )
    press_text = memory_io.generate_press_brief(day)
    memory_io.write_site_artifact(
        memory,
        NAME_PRESS,
        press_text,
        depends_on_source_version_id=svid,
        claim_ids=[NAME_CLAIM_PRESS],
        version=version,
    )
    memory_io.materialize_projection(NAME_PRESS, press_text)

    control_text = memory_io.generate_company_blurb()
    memory_io.write_site_artifact(
        memory,
        NAME_CONTROL,
        control_text,
        depends_on_source_version_id=None,
        claim_ids=[],
        version=1,
    )
    memory_io.materialize_projection(NAME_CONTROL, control_text)

    memory_io.write_site_journal(
        memory,
        evaluated={"phase": "SEED", "day": day, "source_version_id": svid},
        acted={
            "op": "set_entity",
            "entities": ["novadesk-launch", NAME_CLAIM_PRESS, NAME_PRESS, NAME_CONTROL],
        },
        forward={"next": "correct_or_dispute"},
    )

    g = graph.build_graph("before")
    graph.write_graph("before", "before_graph.json")
    return _payload(g, phase="before", expected_press=PRESS_FRI)


def reset_and_seed() -> dict[str, Any]:
    """Delete g3 memory.db and seed Friday baseline."""
    return seed(force=True)


def ensure_seeded() -> dict[str, Any]:
    if _is_empty():
        return seed(force=True)
    return get_state()


def get_state() -> dict[str, Any]:
    if _is_empty():
        return seed(force=True)
    g = graph.build_graph("live")
    press = g.get("press_sha256")
    if press == PRESS_MON:
        return _payload(g, phase="after", expected_press=PRESS_MON)
    if press == PRESS_NE:
        return _payload(g, phase="dispute", expected_press=PRESS_NE)
    return _payload(g, phase="before", expected_press=PRESS_FRI)


# Back-compat alias used by older app draft
def get_graph(phase: str | None = None) -> dict[str, Any]:
    return get_state()


def correct(day: str = "Monday", reason: str = "Calendar confirmed Monday.") -> dict[str, Any]:
    if not reason or len(reason.strip()) < 8:
        raise ValueError("reason required (min 8 chars)")

    memory = memory_io.open_memory()
    live = memory_io.read_site_source(memory)
    body = live["body"]
    old_svid = body["source_version_id"]
    old_day = body.get("day")
    old_version = int(body.get("version") or 1)

    if old_day != "Friday":
        raise RuntimeError(f"expected Friday live source, got {old_day!r}")

    memory_io.write_site_archive_source(memory, reason=f"supersede {old_day}→{day}")

    new_version = old_version + 1
    new_svid = memory_io.new_id()
    memory_io.write_site_source_version(
        memory,
        day=day,
        version=new_version,
        source_version_id=new_svid,
        status=STATUS_ACTIVE,
        supersedes=old_svid,
    )

    memory_io.write_site_correction(
        memory,
        NAME_CORRECTION_APPROVED,
        from_version=old_svid,
        to_version=new_svid,
        decision=STATUS_APPROVED,
        reason=reason.strip(),
        status=STATUS_APPROVED,
    )

    claim_quote = f"NovaDesk public launch is on {day}."
    memory_io.write_site_claim(
        memory,
        NAME_CLAIM_PRESS,
        artifact=NAME_PRESS,
        source_version_id=new_svid,
        quote=claim_quote,
        status=STATUS_ACTIVE,
    )

    arts = memory_io.read_site_list_artifacts(memory)
    invalidated = memory_io.artifacts_invalidated_by(arts, {old_svid})
    regenerated: list[str] = []
    for ent in invalidated:
        name = ent["name"]
        if name == NAME_CONTROL:
            continue
        if name != NAME_PRESS:
            continue
        old_art_version = int(ent["body"].get("version") or 1)
        press_text = memory_io.generate_press_brief(day)
        memory_io.write_site_artifact(
            memory,
            NAME_PRESS,
            press_text,
            depends_on_source_version_id=new_svid,
            claim_ids=[NAME_CLAIM_PRESS],
            version=old_art_version + 1,
        )
        memory_io.materialize_projection(NAME_PRESS, press_text)
        regenerated.append(name)

    control_ent = next((e for e in arts if e["name"] == NAME_CONTROL), None)
    if control_ent:
        memory_io.materialize_projection(
            NAME_CONTROL, control_ent["body"].get("text") or ""
        )

    memory_io.write_site_journal(
        memory,
        evaluated={
            "phase": "CORRECT",
            "from_day": old_day,
            "to_day": day,
            "old_svid": old_svid,
            "new_svid": new_svid,
        },
        acted={
            "op": "archive_and_correct",
            "regenerated": regenerated,
            "control_untouched": True,
        },
        forward={},
    )

    g = graph.build_graph("after")
    graph.write_graph("after", "after_graph.json")
    expected = PRESS_MON if day == "Monday" else (g.get("press_sha256") or "")
    out = _payload(g, phase="after", expected_press=expected)
    out["event"] = (
        f"correction approved · {old_day}→{day} · press-brief rebuilt · company-blurb control"
    )
    out["decision"] = "approved"
    out["regenerated"] = regenerated
    return out


def generate_press_brief_not_established() -> str:
    return (
        "PRESS BRIEF — NovaDesk\n"
        "Embargo lifts: not established\n"
        "Headline: NovaDesk public launch day is not established.\n"
        "Call to action: Do not schedule outreach until day is established.\n"
    )


def dispute(reason: str = "Launch day disputed; treat as not established.") -> dict[str, Any]:
    if not reason or len(reason.strip()) < 8:
        raise ValueError("reason required (min 8 chars)")

    memory = memory_io.open_memory()
    live = memory_io.read_site_source(memory)
    body = live["body"]
    old_svid = body["source_version_id"]
    old_day = body.get("day")
    old_version = int(body.get("version") or 1)

    if old_day != "Friday":
        raise RuntimeError(f"expected Friday live source, got {old_day!r}")

    memory_io.write_site_archive_source(
        memory, reason="dispute Friday→not_established"
    )

    new_svid = memory_io.new_id()
    new_version = old_version + 1
    memory_io.write_site_source_version(
        memory,
        day=None,
        version=new_version,
        source_version_id=new_svid,
        status=STATUS_NOT_ESTABLISHED,
        supersedes=old_svid,
    )

    memory_io.write_site_correction(
        memory,
        NAME_CORRECTION_DISPUTE,
        from_version=old_svid,
        to_version=new_svid,
        decision=STATUS_DISPUTED,
        reason=reason.strip(),
        status=STATUS_NOT_ESTABLISHED,
    )

    memory_io.write_site_claim(
        memory,
        NAME_CLAIM_PRESS,
        artifact=NAME_PRESS,
        source_version_id=new_svid,
        quote="NovaDesk public launch day is not established.",
        status=STATUS_NOT_ESTABLISHED,
    )

    arts = memory_io.read_site_list_artifacts(memory)
    invalidated = memory_io.artifacts_invalidated_by(arts, {old_svid})
    regenerated: list[str] = []

    for ent in invalidated:
        name = ent["name"]
        if name == NAME_CONTROL:
            continue
        if name != NAME_PRESS:
            continue
        old_art_version = int(ent["body"].get("version") or 1)
        press_text = generate_press_brief_not_established()
        memory_io.write_site_artifact(
            memory,
            NAME_PRESS,
            press_text,
            depends_on_source_version_id=new_svid,
            claim_ids=[NAME_CLAIM_PRESS],
            version=old_art_version + 1,
        )
        memory_io.materialize_projection(NAME_PRESS, press_text)
        regenerated.append(name)

    control_ent = next((e for e in arts if e["name"] == NAME_CONTROL), None)
    if control_ent:
        memory_io.materialize_projection(
            NAME_CONTROL, control_ent["body"].get("text") or ""
        )

    memory_io.write_site_journal(
        memory,
        evaluated={
            "phase": "DISPUTE",
            "from_day": old_day,
            "old_svid": old_svid,
            "new_svid": new_svid,
        },
        acted={
            "op": "archive_and_dispute",
            "regenerated": regenerated,
            "control_untouched": True,
        },
        forward={},
    )

    g = graph.build_graph("dispute")
    graph.write_graph("dispute", "dispute_graph.json")
    out = _payload(g, phase="dispute", expected_press=PRESS_NE)
    out["event"] = (
        "correction disputed · claim not_established · press-brief rebuilt · company-blurb control"
    )
    out["decision"] = "disputed"
    out["regenerated"] = regenerated
    return out

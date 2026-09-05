"""G4 ops — seed / correct / conflict helpers over patched G2 write/read sites."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from bridge import (
    DB_PATH,
    NAME_CLAIM_PRESS,
    NAME_CONTROL,
    NAME_CORRECTION_APPROVED,
    NAME_PRESS,
    STATUS_ACTIVE,
    STATUS_APPROVED,
    graph,
    memory_io,
)
from hashes import CONTROL_ALWAYS, DAY_TO_PRESS


def wipe_db(path: Path | None = None) -> None:
    db = Path(path) if path is not None else Path(DB_PATH)
    for p in (db, Path(str(db) + "-wal"), Path(str(db) + "-shm")):
        if p.exists():
            p.unlink()


def seed(*, force: bool = True, day: str = "Friday") -> dict[str, Any]:
    if force:
        wipe_db()

    memory = memory_io.open_memory()
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
        forward={"next": "g4_adversarial"},
    )

    g = graph.build_graph("seed")
    return {
        "graph": g,
        "svid": svid,
        "day": day,
        "control_sha256": g.get("control_sha256"),
        "press_sha256": g.get("press_sha256"),
    }


def correct_to(
    day: str,
    *,
    reason: str = "Calendar confirmed.",
    correction_name: str | None = None,
    expect_from: str | None = None,
) -> dict[str, Any]:
    """Archive live source and write new day; regenerate press only.

    Unlike g3.ops.correct, accepts any current live day (for repeat corrections).
    """
    if not reason or len(reason.strip()) < 8:
        raise ValueError("reason required (min 8 chars)")

    memory = memory_io.open_memory()
    live = memory_io.read_site_source(memory)
    body = live["body"]
    old_svid = body["source_version_id"]
    old_day = body.get("day")
    old_version = int(body.get("version") or 1)

    if expect_from is not None and old_day != expect_from:
        raise RuntimeError(f"expected live day {expect_from!r}, got {old_day!r}")

    memory_io.write_site_archive_source(
        memory, reason=f"supersede {old_day}→{day}"
    )

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

    corr_name = correction_name or f"{(old_day or 'x').lower()}-to-{day.lower()}-approved"
    memory_io.write_site_correction(
        memory,
        corr_name,
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
    return {
        "graph": g,
        "old_day": old_day,
        "new_day": day,
        "old_svid": old_svid,
        "new_svid": new_svid,
        "regenerated": regenerated,
        "control_sha256": g.get("control_sha256"),
        "press_sha256": g.get("press_sha256"),
        "control_ok": g.get("control_sha256") == CONTROL_ALWAYS,
        "press_ok": g.get("press_sha256") == DAY_TO_PRESS.get(day),
    }


def live_source_day() -> str | None:
    memory = memory_io.open_memory()
    body = memory_io.read_site_source(memory)["body"]
    return body.get("day")


def detect_claim_conflicts(memory=None) -> list[dict[str, Any]]:
    """Surface disagreements among live claims vs live source day."""
    if memory is None:
        memory = memory_io.open_memory()
    live = memory_io.read_site_source(memory)
    live_day = live["body"].get("day")
    live_svid = live["body"].get("source_version_id")
    conflicts: list[dict[str, Any]] = []
    claims = memory_io.read_site_list_claims(memory)
    days_seen: dict[str, list[str]] = {}
    for ent in claims:
        body = ent.get("body") or {}
        quote = body.get("quote") or ""
        svid = body.get("source_version_id")
        name = ent.get("name")
        # Extract asserted day from quote if present
        asserted = None
        for d in ("Friday", "Monday", "Tuesday", "Wednesday", "Thursday"):
            if d in quote:
                asserted = d
                break
        if asserted:
            days_seen.setdefault(asserted, []).append(name)
        if svid and live_svid and svid != live_svid:
            conflicts.append(
                {
                    "type": "claim_svid_mismatch",
                    "claim": name,
                    "claim_svid": svid,
                    "live_svid": live_svid,
                    "live_day": live_day,
                    "asserted_day": asserted,
                }
            )
        elif asserted and live_day and asserted != live_day:
            conflicts.append(
                {
                    "type": "claim_day_mismatch",
                    "claim": name,
                    "asserted_day": asserted,
                    "live_day": live_day,
                }
            )
    if len(days_seen) > 1:
        conflicts.append(
            {
                "type": "disagreeing_live_claims",
                "days": sorted(days_seen.keys()),
                "by_day": days_seen,
            }
        )
    return conflicts


def refuse_ambiguous_regen(memory=None) -> dict[str, Any]:
    """Product-like gate: refuse regen when conflicts are present."""
    conflicts = detect_claim_conflicts(memory)
    if conflicts:
        return {
            "refused": True,
            "reason": "ambiguous_sources_conflict",
            "conflicts": conflicts,
            "regenerated": [],
        }
    return {"refused": False, "conflicts": [], "regenerated": None}

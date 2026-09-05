"""G5 ops — seed / correct over patched G2 write/read sites (mirrors g3.ops)."""
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
from hashes import CONTROL_ALWAYS, PRESS_FRIDAY, PRESS_MONDAY


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

    src = memory_io.write_site_source_version(
        memory,
        day=day,
        version=version,
        source_version_id=svid,
        status=STATUS_ACTIVE,
    )
    claim_quote = f"NovaDesk public launch is on {day}."
    claim = memory_io.write_site_claim(
        memory,
        NAME_CLAIM_PRESS,
        artifact=NAME_PRESS,
        source_version_id=svid,
        quote=claim_quote,
        status=STATUS_ACTIVE,
    )
    press_text = memory_io.generate_press_brief(day)
    press = memory_io.write_site_artifact(
        memory,
        NAME_PRESS,
        press_text,
        depends_on_source_version_id=svid,
        claim_ids=[NAME_CLAIM_PRESS],
        version=version,
    )
    memory_io.materialize_projection(NAME_PRESS, press_text)

    control_text = memory_io.generate_company_blurb()
    control = memory_io.write_site_artifact(
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
        forward={"next": "g5_cold_start_correct"},
    )

    g = graph.build_graph("before")
    graph.write_graph("before", "before_graph.json")
    return {
        "graph": g,
        "svid": svid,
        "day": day,
        "entity_ids": {
            "source": src.get("id"),
            "claim": claim.get("id"),
            "press": press.get("id"),
            "control": control.get("id"),
        },
        "control_sha256": g.get("control_sha256"),
        "press_sha256": g.get("press_sha256"),
        "control_ok": g.get("control_sha256") == CONTROL_ALWAYS,
        "press_ok": g.get("press_sha256") == PRESS_FRIDAY,
    }


def correct(
    day: str = "Monday",
    *,
    reason: str = "Calendar confirmed Monday.",
) -> dict[str, Any]:
    """Archive live Friday source and write Monday; regenerate press only.

    Reads live state ONLY from Sibyl (empty Python process state).
    """
    if not reason or len(reason.strip()) < 8:
        raise ValueError("reason required (min 8 chars)")

    memory = memory_io.open_memory()

    # READ SITE: get_entity(source_version, novadesk-launch)
    live = memory_io.read_site_source(memory)
    body = live["body"]
    old_svid = body["source_version_id"]
    old_day = body.get("day")
    old_version = int(body.get("version") or 1)
    source_entity_id = live.get("id")

    if old_day != "Friday":
        raise RuntimeError(f"expected Friday live source, got {old_day!r}")

    memory_io.write_site_archive_source(
        memory, reason=f"supersede {old_day}→{day}"
    )

    new_version = old_version + 1
    new_svid = memory_io.new_id()
    src2 = memory_io.write_site_source_version(
        memory,
        day=day,
        version=new_version,
        source_version_id=new_svid,
        status=STATUS_ACTIVE,
        supersedes=old_svid,
    )

    corr = memory_io.write_site_correction(
        memory,
        NAME_CORRECTION_APPROVED,
        from_version=old_svid,
        to_version=new_svid,
        decision=STATUS_APPROVED,
        reason=reason.strip(),
        status=STATUS_APPROVED,
    )

    claim_quote = f"NovaDesk public launch is on {day}."
    claim = memory_io.write_site_claim(
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
    return {
        "graph": g,
        "old_day": old_day,
        "new_day": day,
        "old_svid": old_svid,
        "new_svid": new_svid,
        "source_entity_id_before": source_entity_id,
        "source_entity_id_after": src2.get("id"),
        "correction_entity_id": corr.get("id"),
        "claim_entity_id": claim.get("id"),
        "regenerated": regenerated,
        "control_sha256": g.get("control_sha256"),
        "press_sha256": g.get("press_sha256"),
        "control_ok": g.get("control_sha256") == CONTROL_ALWAYS,
        "press_ok": g.get("press_sha256") == PRESS_MONDAY,
    }


def capture_sibyl_pointers(*, phase: str) -> dict[str, Any]:
    """Record entity ids + source_version_ids + get_entity call sites from Sibyl."""
    memory = memory_io.open_memory()
    pointers: dict[str, Any] = {
        "phase": phase,
        "db_path": str(DB_PATH),
        "get_entity_call_sites": [
            {
                "fn": "memory_io.read_site_source",
                "calls": "memory.get_entity(CAT_SOURCE, NAME_LAUNCH)",
                "category": "source_version",
                "name": "novadesk-launch",
            },
            {
                "fn": "memory_io.read_site_artifact",
                "calls": "memory.get_entity(CAT_ARTIFACT, name)",
                "category": "artifact",
                "names": ["press-brief", "company-blurb"],
            },
            {
                "fn": "memory_io.read_site_claim",
                "calls": "memory.get_entity(CAT_CLAIM, name)",
                "category": "claim",
                "names": ["press-brief-cites-launch"],
            },
            {
                "fn": "memory_io.read_site_correction",
                "calls": "memory.get_entity(CAT_CORRECTION, name)",
                "category": "correction",
                "names": ["friday-to-monday-approved"],
            },
        ],
        "entities": {},
        "source_version_ids": {},
    }

    try:
        src = memory_io.read_site_source(memory)
        pointers["entities"]["novadesk-launch"] = {
            "id": src.get("id"),
            "body_source_version_id": (src.get("body") or {}).get("source_version_id"),
            "day": (src.get("body") or {}).get("day"),
            "status": (src.get("body") or {}).get("status"),
            "supersedes": (src.get("body") or {}).get("supersedes"),
        }
        pointers["source_version_ids"]["live"] = (src.get("body") or {}).get(
            "source_version_id"
        )
    except Exception as e:
        pointers["entities"]["novadesk-launch"] = {"error": str(e)}

    for name in ("press-brief", "company-blurb"):
        try:
            ent = memory_io.read_site_artifact(memory, name)
            body = ent.get("body") or {}
            pointers["entities"][name] = {
                "id": ent.get("id"),
                "depends_on_source_version_id": body.get("depends_on_source_version_id"),
                "content_sha256": body.get("content_sha256"),
                "version": body.get("version"),
            }
            if body.get("depends_on_source_version_id"):
                pointers["source_version_ids"][f"artifact:{name}"] = body.get(
                    "depends_on_source_version_id"
                )
        except Exception as e:
            pointers["entities"][name] = {"error": str(e)}

    try:
        claim = memory_io.read_site_claim(memory, NAME_CLAIM_PRESS)
        body = claim.get("body") or {}
        pointers["entities"][NAME_CLAIM_PRESS] = {
            "id": claim.get("id"),
            "source_version_id": body.get("source_version_id"),
            "quote": body.get("quote"),
        }
        pointers["source_version_ids"]["claim"] = body.get("source_version_id")
    except Exception as e:
        pointers["entities"][NAME_CLAIM_PRESS] = {"error": str(e)}

    try:
        corr = memory_io.read_site_correction(memory, NAME_CORRECTION_APPROVED)
        body = corr.get("body") or {}
        pointers["entities"][NAME_CORRECTION_APPROVED] = {
            "id": corr.get("id"),
            "from_version": body.get("from_version"),
            "to_version": body.get("to_version"),
            "decision": body.get("decision"),
        }
        pointers["source_version_ids"]["correction_from"] = body.get("from_version")
        pointers["source_version_ids"]["correction_to"] = body.get("to_version")
    except Exception as e:
        pointers["entities"][NAME_CORRECTION_APPROVED] = {"error": str(e)}

    archived = memory_io.read_site_archived_sources()
    pointers["archived_sources"] = [
        {
            "archived_id": a.get("archived_id"),
            "original_entity_id": a.get("original_entity_id"),
            "source_version_id": (a.get("body") or {}).get("source_version_id"),
            "day": (a.get("body") or {}).get("day"),
            "archive_reason": a.get("archive_reason"),
        }
        for a in archived
    ]
    return pointers

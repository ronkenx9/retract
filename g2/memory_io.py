"""Sibyl Memory write_site / read_site for RETRACT G2.

Typed source versions in body; UNIQUE (tenant, category, name): archive
superseded live row then set new body. Claims link artifacts → source version
ids. Corrections record approved|disputed. SoT = Sibyl only.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from sibyl_memory_client import MemoryClient

from config import (
    CAT_ARTIFACT,
    CAT_CLAIM,
    CAT_CORRECTION,
    CAT_SOURCE,
    DB_PATH,
    NAME_LAUNCH,
    PROJECTIONS_DIR,
    STATUS_ACTIVE,
    STATUS_NOT_ESTABLISHED,
    TENANT_ID,
)


def open_memory() -> MemoryClient:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return MemoryClient.local(str(DB_PATH), tenant_id=TENANT_ID)


def content_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# alias used by older scaffold
content_hash = content_sha256


def new_id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# WRITE SITES
# ---------------------------------------------------------------------------

def write_site_source_version(
    memory: MemoryClient,
    *,
    day: str | None,
    version: int,
    source_version_id: str,
    status: str = STATUS_ACTIVE,
    supersedes: str | None = None,
    claim: str | None = None,
) -> dict[str, Any]:
    """WRITE SITE: persist typed launch source version into Sibyl."""
    if claim is None:
        if status == STATUS_NOT_ESTABLISHED or day is None:
            claim = "NovaDesk public launch day is not established."
        else:
            claim = f"NovaDesk public launch is on {day}."
    body: dict[str, Any] = {
        "source_version_id": source_version_id,
        "status": status,
        "supersedes": supersedes,
        "product": "NovaDesk",
        "claim": claim,
        "day": day,
        "version": version,
        "corpus": "fictional-owned-launch",
    }
    return memory.set_entity(CAT_SOURCE, NAME_LAUNCH, body, status="active")


def write_site_archive_source(memory: MemoryClient, reason: str) -> dict[str, Any]:
    """WRITE SITE: archive superseded/disputed source (prefer over delete)."""
    return memory.archive_entity(CAT_SOURCE, NAME_LAUNCH, reason=reason)


def write_site_artifact(
    memory: MemoryClient,
    name: str,
    text: str,
    *,
    depends_on_source_version_id: str | None,
    claim_ids: list[str],
    version: int,
) -> dict[str, Any]:
    """WRITE SITE: persist artifact with dependency + claim links."""
    body = {
        "text": text,
        "depends_on_source_version_id": depends_on_source_version_id,
        "source_version_ids": (
            [depends_on_source_version_id] if depends_on_source_version_id else []
        ),
        "claim_ids": list(claim_ids),
        "content_sha256": content_sha256(text),
        "version": version,
    }
    return memory.set_entity(CAT_ARTIFACT, name, body, status="active")


def write_site_claim(
    memory: MemoryClient,
    name: str,
    *,
    artifact: str,
    source_version_id: str,
    quote: str,
    status: str = STATUS_ACTIVE,
) -> dict[str, Any]:
    """WRITE SITE: claim linking artifact → source_version_id."""
    body = {
        "artifact": artifact,
        "source_version_id": source_version_id,
        "quote": quote,
        "span": "launch-day",
        "status": status,
    }
    return memory.set_entity(CAT_CLAIM, name, body, status="active")


def write_site_correction(
    memory: MemoryClient,
    name: str,
    *,
    from_version: str,
    to_version: str | None,
    decision: str,
    reason: str,
    status: str,
) -> dict[str, Any]:
    """WRITE SITE: correction record (approved | disputed)."""
    body = {
        "from_version": from_version,
        "to_version": to_version,
        "decision": decision,
        "reason": reason,
        "status": status,
    }
    return memory.set_entity(CAT_CORRECTION, name, body, status="active")


def write_site_journal(
    memory: MemoryClient,
    *,
    evaluated: dict[str, Any],
    acted: dict[str, Any],
    forward: dict[str, Any] | None = None,
) -> str:
    """WRITE SITE: journal event for audit / retract history."""
    return memory.write_event(evaluated=evaluated, acted=acted, forward=forward or {})


# ---------------------------------------------------------------------------
# READ SITES
# ---------------------------------------------------------------------------

def read_site_source(memory: MemoryClient) -> dict[str, Any]:
    """READ SITE: load live source version from Sibyl."""
    return memory.get_entity(CAT_SOURCE, NAME_LAUNCH)


def read_site_artifact(memory: MemoryClient, name: str) -> dict[str, Any]:
    """READ SITE: load artifact entity from Sibyl."""
    return memory.get_entity(CAT_ARTIFACT, name)


def read_site_claim(memory: MemoryClient, name: str) -> dict[str, Any]:
    """READ SITE: load claim entity from Sibyl."""
    return memory.get_entity(CAT_CLAIM, name)


def read_site_correction(memory: MemoryClient, name: str) -> dict[str, Any]:
    """READ SITE: load correction entity from Sibyl."""
    return memory.get_entity(CAT_CORRECTION, name)


def read_site_list_artifacts(memory: MemoryClient, limit: int = 50) -> list[dict[str, Any]]:
    """READ SITE: list artifact entities."""
    return memory.list_entities(category=CAT_ARTIFACT, limit=limit)


def read_site_list_sources(memory: MemoryClient, limit: int = 50) -> list[dict[str, Any]]:
    """READ SITE: list live source_version entities."""
    return memory.list_entities(category=CAT_SOURCE, limit=limit)


def read_site_list_claims(memory: MemoryClient, limit: int = 50) -> list[dict[str, Any]]:
    """READ SITE: list claim entities."""
    return memory.list_entities(category=CAT_CLAIM, limit=limit)


def read_site_list_corrections(memory: MemoryClient, limit: int = 50) -> list[dict[str, Any]]:
    """READ SITE: list correction entities."""
    return memory.list_entities(category=CAT_CORRECTION, limit=limit)


def read_site_events(memory: MemoryClient, limit: int = 40) -> list[dict[str, Any]]:
    """READ SITE: journal events."""
    return memory.read_events(limit=limit)


def read_site_archived_sources() -> list[dict[str, Any]]:
    """READ SITE: Sibyl archive tier (archived_entities) for supersedes trail.

    Client 0.8.0 has no list_archived API; archive table is still Sibyl SoT.
    """
    if not DB_PATH.exists():
        return []
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            "SELECT id, original_entity_id, category, name, body, archive_reason, archived_at "
            "FROM archived_entities WHERE tenant_id=? AND category=? ORDER BY archived_at",
            (TENANT_ID, CAT_SOURCE),
        ).fetchall()
    finally:
        con.close()
    out = []
    for r in rows:
        body = r["body"]
        if isinstance(body, str):
            body = json.loads(body)
        out.append(
            {
                "archived_id": r["id"],
                "original_entity_id": r["original_entity_id"],
                "name": r["name"],
                "body": body,
                "archive_reason": r["archive_reason"],
                "archived_at": r["archived_at"],
            }
        )
    return out


# ---------------------------------------------------------------------------
# Generation + invalidation
# ---------------------------------------------------------------------------

def generate_press_brief(day: str) -> str:
    return (
        f"PRESS BRIEF — NovaDesk\n"
        f"Embargo lifts: {day}\n"
        f"Headline: NovaDesk launches to the public on {day}.\n"
        f"Call to action: Mark your calendar for {day}.\n"
    )


def generate_company_blurb() -> str:
    return (
        "COMPANY BLURB — NovaDesk\n"
        "NovaDesk is a fictional productivity suite owned by the RETRACT demo corpus.\n"
        "Mission: calm desks, clear calendars.\n"
    )


def artifacts_invalidated_by(
    artifacts: list[dict[str, Any]],
    invalidated_version_ids: set[str],
) -> list[dict[str, Any]]:
    out = []
    for ent in artifacts:
        body = ent.get("body", {})
        cites = set(body.get("source_version_ids") or [])
        dep = body.get("depends_on_source_version_id")
        if dep:
            cites.add(dep)
        if cites & invalidated_version_ids:
            out.append(ent)
    return out


def materialize_projection(name: str, text: str) -> Path:
    PROJECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = PROJECTIONS_DIR / f"{name}.txt"
    path.write_text(text, encoding="utf-8")
    return path

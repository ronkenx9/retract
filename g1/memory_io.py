"""Sibyl Memory write_site / read_site for RETRACT G1.

Semantic state lives ONLY in Sibyl Memory (MemoryClient.local).
Projection files under artifacts/projections/ are regenerated views, not SoT.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from sibyl_memory_client import MemoryClient

from config import (
    CAT_ARTIFACT,
    CAT_SOURCE,
    DB_PATH,
    NAME_CONTROL,
    NAME_LAUNCH,
    NAME_PRESS,
    PROJECTIONS_DIR,
    TENANT_ID,
)


def open_memory() -> MemoryClient:
    """Open project-scoped DB with dedicated tenant_id."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return MemoryClient.local(str(DB_PATH), tenant_id=TENANT_ID)


# ---------------------------------------------------------------------------
# WRITE SITES — judges: these are the Sibyl write call sites
# ---------------------------------------------------------------------------

def write_site_source(memory: MemoryClient, day: str, version: int) -> dict[str, Any]:
    """WRITE SITE: persist the launch-note source entity into Sibyl."""
    body = {
        "product": "NovaDesk",
        "claim": f"NovaDesk public launch is on {day}.",
        "day": day,
        "version": version,
        "corpus": "fictional-owned-launch",
    }
    return memory.set_entity(CAT_SOURCE, NAME_LAUNCH, body, status="active")


def write_site_artifact(
    memory: MemoryClient,
    name: str,
    text: str,
    *,
    depends_on: str | None,
    version: int,
) -> dict[str, Any]:
    """WRITE SITE: persist a generated artifact entity into Sibyl."""
    body = {
        "text": text,
        "depends_on": depends_on,
        "version": version,
    }
    return memory.set_entity(CAT_ARTIFACT, name, body, status="active")


def write_site_journal(
    memory: MemoryClient,
    *,
    evaluated: dict[str, Any],
    acted: dict[str, Any],
    forward: dict[str, Any] | None = None,
) -> str:
    """WRITE SITE: append a journal event for audit / retract history."""
    return memory.write_event(evaluated=evaluated, acted=acted, forward=forward or {})


def write_site_archive_source(memory: MemoryClient, reason: str) -> dict[str, Any]:
    """WRITE SITE: archive superseded source (prefer over delete_entity)."""
    return memory.archive_entity(CAT_SOURCE, NAME_LAUNCH, reason=reason)


# ---------------------------------------------------------------------------
# READ SITES — judges: these are the Sibyl read call sites
# ---------------------------------------------------------------------------

def read_site_source(memory: MemoryClient) -> dict[str, Any]:
    """READ SITE: load launch-note source from Sibyl (cold-start reconstruct)."""
    return memory.get_entity(CAT_SOURCE, NAME_LAUNCH)


def read_site_artifact(memory: MemoryClient, name: str) -> dict[str, Any]:
    """READ SITE: load an artifact entity from Sibyl."""
    return memory.get_entity(CAT_ARTIFACT, name)


def read_site_events(memory: MemoryClient, limit: int = 20) -> list[dict[str, Any]]:
    """READ SITE: read journal events from Sibyl."""
    return memory.read_events(limit=limit)


# ---------------------------------------------------------------------------
# Generation helpers (pure; output persisted only via write_site_*)
# ---------------------------------------------------------------------------

def generate_press_brief(day: str) -> str:
    """Dependent artifact text — changes when launch day changes."""
    return (
        f"PRESS BRIEF — NovaDesk\n"
        f"Embargo lifts: {day}\n"
        f"Headline: NovaDesk launches to the public on {day}.\n"
        f"Call to action: Mark your calendar for {day}.\n"
    )


def generate_company_blurb() -> str:
    """Control artifact — must NOT change when launch day is corrected."""
    return (
        "COMPANY BLURB — NovaDesk\n"
        "NovaDesk is a fictional productivity suite owned by the RETRACT demo corpus.\n"
        "Mission: calm desks, clear calendars.\n"
    )


def materialize_projection(name: str, text: str) -> Path:
    """Write a human-visible projection file (NOT source of truth)."""
    PROJECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = PROJECTIONS_DIR / f"{name}.txt"
    path.write_text(text, encoding="utf-8")
    return path

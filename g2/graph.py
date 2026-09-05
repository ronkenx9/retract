"""Dependency graph projection — rebuilt from Sibyl reads only (not a parallel DB)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import ARTIFACTS_DIR, NAME_CONTROL, NAME_PRESS
from memory_io import (
    content_sha256,
    open_memory,
    read_site_archived_sources,
    read_site_list_artifacts,
    read_site_list_claims,
    read_site_list_corrections,
    read_site_list_sources,
)


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_graph(phase: str) -> dict[str, Any]:
    """READ from Sibyl and emit machine-readable dependency graph."""
    memory = open_memory()
    sources_out: list[dict[str, Any]] = []

    for ent in read_site_list_sources(memory):
        body = ent["body"]
        sources_out.append(
            {
                "id": ent["id"],
                "name": ent["name"],
                "version": body.get("version"),
                "day": body.get("day"),
                "archived": False,
                "supersedes": body.get("supersedes"),
                "source_version_id": body.get("source_version_id"),
                "status": body.get("status"),
                "claim": body.get("claim"),
            }
        )

    for arch in read_site_archived_sources():
        body = arch["body"]
        sources_out.append(
            {
                "id": arch["original_entity_id"],
                "archived_id": arch["archived_id"],
                "name": arch["name"],
                "version": body.get("version"),
                "day": body.get("day"),
                "archived": True,
                "supersedes": body.get("supersedes"),
                "source_version_id": body.get("source_version_id"),
                "status": body.get("status", "superseded"),
                "archive_reason": arch.get("archive_reason"),
            }
        )

    claims_out: list[dict[str, Any]] = []
    for ent in read_site_list_claims(memory):
        body = ent["body"]
        claims_out.append(
            {
                "id": ent["id"],
                "artifact": body.get("artifact"),
                "source_version_id": body.get("source_version_id"),
                "status": body.get("status"),
                "quote": body.get("quote"),
            }
        )

    artifacts_out: list[dict[str, Any]] = []
    for ent in read_site_list_artifacts(memory):
        body = ent["body"]
        text = body.get("text") or ""
        artifacts_out.append(
            {
                "name": ent["name"],
                "depends_on_source_version_id": body.get("depends_on_source_version_id"),
                "content_sha256": body.get("content_sha256") or content_sha256(text),
                "text": text,
                "claim_ids": body.get("claim_ids") or [],
                "version": body.get("version"),
            }
        )

    corrections_out: list[dict[str, Any]] = []
    for ent in read_site_list_corrections(memory):
        body = ent["body"]
        corrections_out.append(
            {
                "id": ent["id"],
                "name": ent["name"],
                "from_version": body.get("from_version"),
                "to_version": body.get("to_version"),
                "decision": body.get("decision"),
                "reason": body.get("reason"),
                "status": body.get("status"),
            }
        )

    by_name = {a["name"]: a for a in artifacts_out}
    control = by_name.get(NAME_CONTROL)
    press = by_name.get(NAME_PRESS)

    return {
        "phase": phase,
        "ts": _ts(),
        "sources": sources_out,
        "claims": claims_out,
        "artifacts": artifacts_out,
        "corrections": corrections_out,
        "control_sha256": control["content_sha256"] if control else None,
        "press_sha256": press["content_sha256"] if press else None,
    }


def write_graph(phase: str, filename: str) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    graph = build_graph(phase)
    path = ARTIFACTS_DIR / filename
    path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    return path

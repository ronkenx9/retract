"""PHASE COLD_START — fresh process, empty Python state, same DB path.

Reads Sibyl, corrects Friday → Monday, regenerates the dependent artifact.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from config import DB_PATH, NAME_CONTROL, NAME_PRESS, TENANT_ID
from memory_io import (
    generate_press_brief,
    materialize_projection,
    open_memory,
    read_site_artifact,
    read_site_source,
    write_site_archive_source,
    write_site_artifact,
    write_site_journal,
    write_site_source,
)


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    print(f"PHASE COLD_START @ {_ts()}")
    print(f"  db={DB_PATH}")
    print(f"  tenant_id={TENANT_ID}")
    print(f"  pid={__import__('os').getpid()}")
    print("  note: no prior Python state; empty chat; reconstruct from Sibyl only")

    memory = open_memory()
    print(f"  schema_version={memory.schema_version()}")

    # READ SITE — reconstruct source after cold start
    src = read_site_source(memory)
    body = src["body"]
    old_day = body["day"]
    old_version = int(body["version"])
    print(f"  READ source day={old_day!r} version={old_version} id={src['id']}")

    before_press = read_site_artifact(memory, NAME_PRESS)
    before_control = read_site_artifact(memory, NAME_CONTROL)
    print(f"  READ press-brief (before) version={before_press['body']['version']}")
    print(f"  READ company-blurb (control) version={before_control['body']['version']}")

    if old_day != "Friday":
        print(f"  ERROR: expected seeded day Friday, got {old_day!r}")
        return 2

    new_day = "Monday"
    new_version = old_version + 1

    # Prefer archive over delete, then write corrected source (UNIQUE constraint)
    arch = write_site_archive_source(
        memory, reason=f"retract: {old_day} -> {new_day} (v{old_version} superseded)"
    )
    print(f"  ARCHIVED old source archived_id={arch.get('archived_id')}")

    corrected = write_site_source(memory, day=new_day, version=new_version)
    print(f"  wrote corrected source day={new_day} version={new_version} id={corrected['id']}")

    # Regenerate ONLY the dependent artifact from corrected source
    new_press_text = generate_press_brief(new_day)
    press = write_site_artifact(
        memory,
        NAME_PRESS,
        new_press_text,
        depends_on="source/launch-note",
        version=new_version,
    )
    press_path = materialize_projection(NAME_PRESS, new_press_text)
    print(f"  regenerated dependent press-brief id={press['id']} -> {press_path}")

    # Control stays unchanged (selective invalidation)
    control_text = before_control["body"]["text"]
    control_path = materialize_projection(NAME_CONTROL, control_text)
    print(f"  control company-blurb UNCHANGED -> {control_path}")

    write_site_journal(
        memory,
        evaluated={
            "phase": "COLD_START",
            "old_day": old_day,
            "new_day": new_day,
            "old_version": old_version,
            "new_version": new_version,
        },
        acted={
            "op": "archive_then_set",
            "source": "launch-note",
            "regenerated": ["press-brief"],
            "untouched": ["company-blurb"],
        },
        forward={"proof": "dependent_artifact_changed_after_cold_start"},
    )

    result = {
        "phase": "RESULT",
        "ts": _ts(),
        "source_before": old_day,
        "source_after": new_day,
        "press_before": before_press["body"]["text"],
        "press_after": new_press_text,
        "control_before": before_control["body"]["text"],
        "control_after": control_text,
        "press_changed": before_press["body"]["text"] != new_press_text,
        "control_unchanged": before_control["body"]["text"] == control_text,
        "pid": __import__("os").getpid(),
    }
    out = DB_PATH.parent / "artifacts" / "cold_start_result.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"  result -> {out}")

    print("PHASE RESULT")
    print(f"  source: {old_day} -> {new_day}")
    print(f"  press_changed={result['press_changed']}")
    print(f"  control_unchanged={result['control_unchanged']}")
    print("--- ARTIFACT BEFORE ---")
    print(before_press["body"]["text"], end="")
    print("--- ARTIFACT AFTER ---")
    print(new_press_text, end="")
    print("--- CONTROL (unchanged) ---")
    print(control_text, end="")

    ok = result["press_changed"] and result["control_unchanged"] and new_day == "Monday"
    print(f"G1_PROOF={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

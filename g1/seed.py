"""PHASE SEED — write source + dependent artifacts through Sibyl, then exit."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from config import DB_PATH, NAME_CONTROL, NAME_PRESS, TENANT_ID
from memory_io import (
    generate_company_blurb,
    generate_press_brief,
    materialize_projection,
    open_memory,
    write_site_artifact,
    write_site_journal,
    write_site_source,
)


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    print(f"PHASE SEED @ {_ts()}")
    print(f"  db={DB_PATH}")
    print(f"  tenant_id={TENANT_ID}")
    print(f"  pid={__import__('os').getpid()}")

    memory = open_memory()
    print(f"  schema_version={memory.schema_version()}")

    day = "Friday"
    version = 1

    src = write_site_source(memory, day=day, version=version)
    print(f"  wrote source launch-note day={day} version={version} id={src['id']}")

    press_text = generate_press_brief(day)
    press = write_site_artifact(
        memory, NAME_PRESS, press_text, depends_on="source/launch-note", version=version
    )
    press_path = materialize_projection(NAME_PRESS, press_text)
    print(f"  wrote dependent artifact press-brief id={press['id']}")
    print(f"  projection -> {press_path}")

    control_text = generate_company_blurb()
    control = write_site_artifact(
        memory, NAME_CONTROL, control_text, depends_on=None, version=1
    )
    control_path = materialize_projection(NAME_CONTROL, control_text)
    print(f"  wrote control artifact company-blurb id={control['id']}")
    print(f"  projection -> {control_path}")

    eid = write_site_journal(
        memory,
        evaluated={"phase": "SEED", "day": day},
        acted={"op": "set_entity", "entities": ["launch-note", "press-brief", "company-blurb"]},
        forward={"next": "kill_then_cold_start"},
    )
    print(f"  journal event id={eid}")

    # Snapshot for RESULT comparison (projections only; SoT is Sibyl)
    snap = {
        "phase": "SEED",
        "ts": _ts(),
        "press_brief": press_text,
        "company_blurb": control_text,
        "source_day": day,
        "source_version": version,
    }
    snap_path = DB_PATH.parent / "artifacts" / "seed_snapshot.json"
    snap_path.parent.mkdir(parents=True, exist_ok=True)
    snap_path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    print(f"  seed_snapshot -> {snap_path}")
    print("PHASE SEED DONE — process will exit (KILL)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

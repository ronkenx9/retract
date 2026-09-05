"""PROCESS 1 — SEED typed source v1 (Friday) + claim + artifacts, then exit."""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

from config import (
    ARTIFACTS_DIR,
    DB_PATH,
    NAME_CLAIM_PRESS,
    NAME_CONTROL,
    NAME_PRESS,
    STATUS_ACTIVE,
    TENANT_ID,
)
from graph import write_graph
from memory_io import (
    generate_company_blurb,
    generate_press_brief,
    materialize_projection,
    new_id,
    open_memory,
    write_site_artifact,
    write_site_claim,
    write_site_journal,
    write_site_source_version,
)


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    print(f"PHASE SEED @ {_ts()}")
    print(f"  db={DB_PATH}")
    print(f"  tenant_id={TENANT_ID}")
    print(f"  pid={os.getpid()}")

    memory = open_memory()
    print(f"  schema_version={memory.schema_version()}")

    day = "Friday"
    version = 1
    svid = new_id()

    src = write_site_source_version(
        memory,
        day=day,
        version=version,
        source_version_id=svid,
        status=STATUS_ACTIVE,
    )
    print(f"  wrote source v{version} day={day} svid={svid} id={src['id']}")

    claim_quote = f"NovaDesk public launch is on {day}."
    claim = write_site_claim(
        memory,
        NAME_CLAIM_PRESS,
        artifact=NAME_PRESS,
        source_version_id=svid,
        quote=claim_quote,
        status=STATUS_ACTIVE,
    )
    print(f"  wrote claim {NAME_CLAIM_PRESS} -> svid={svid} id={claim['id']}")

    press_text = generate_press_brief(day)
    press = write_site_artifact(
        memory,
        NAME_PRESS,
        press_text,
        depends_on_source_version_id=svid,
        claim_ids=[NAME_CLAIM_PRESS],
        version=version,
    )
    press_path = materialize_projection(NAME_PRESS, press_text)
    print(f"  wrote artifact {NAME_PRESS} citing svid={svid} id={press['id']}")
    print(f"  projection -> {press_path}")

    control_text = generate_company_blurb()
    control = write_site_artifact(
        memory,
        NAME_CONTROL,
        control_text,
        depends_on_source_version_id=None,
        claim_ids=[],
        version=1,
    )
    control_path = materialize_projection(NAME_CONTROL, control_text)
    print(f"  wrote control {NAME_CONTROL} source_version_ids=[] id={control['id']}")
    print(f"  projection -> {control_path}")

    eid = write_site_journal(
        memory,
        evaluated={"phase": "SEED", "day": day, "source_version_id": svid},
        acted={
            "op": "set_entity",
            "entities": ["novadesk-launch", NAME_CLAIM_PRESS, NAME_PRESS, NAME_CONTROL],
        },
        forward={"next": "correct_or_dispute_fresh_process"},
    )
    print(f"  journal SEED event id={eid}")

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    graph_path = write_graph("before", "before_graph.json")
    import json

    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    control_hash = graph["control_sha256"]
    press_hash = graph["press_sha256"]
    print(f"  before_graph -> {graph_path}")
    print(f"CONTROL_HASH_BEFORE={control_hash}")
    print(f"PRESS_HASH_BEFORE={press_hash}")
    print("PHASE SEED DONE — process will exit (KILL)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

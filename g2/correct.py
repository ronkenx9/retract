"""PROCESS 2 — fresh PID: approved Friday→Monday correction via Sibyl only."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import (
    ARTIFACTS_DIR,
    DB_PATH,
    NAME_CLAIM_PRESS,
    NAME_CONTROL,
    NAME_CORRECTION_APPROVED,
    NAME_PRESS,
    STATUS_ACTIVE,
    STATUS_APPROVED,
    TENANT_ID,
)
from graph import write_graph
from memory_io import (
    artifacts_invalidated_by,
    generate_press_brief,
    materialize_projection,
    new_id,
    open_memory,
    read_site_list_artifacts,
    read_site_source,
    write_site_archive_source,
    write_site_artifact,
    write_site_claim,
    write_site_correction,
    write_site_journal,
    write_site_source_version,
)


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    print(f"PHASE CORRECT @ {_ts()}")
    print(f"  db={DB_PATH}")
    print(f"  tenant_id={TENANT_ID}")
    print(f"  pid={os.getpid()}")

    memory = open_memory()
    print(f"  schema_version={memory.schema_version()}")

    # 1–2. Read live source ONLY from Sibyl
    live = read_site_source(memory)
    body = live["body"]
    old_svid = body["source_version_id"]
    old_day = body.get("day")
    old_version = int(body.get("version") or 1)
    print(f"  live source day={old_day} version={old_version} svid={old_svid}")
    if old_day != "Friday":
        print(f"G2_PROOF=FAIL reason=expected_Friday_got_{old_day}")
        return 1

    # 3. Archive superseded Friday source
    reason = "supersede Friday→Monday"
    arch = write_site_archive_source(memory, reason=reason)
    print(f"  archived source reason={reason} archived_id={arch.get('id')}")

    # 4. Write source v2 Monday superseding old_svid
    new_day = "Monday"
    new_version = old_version + 1
    new_svid = new_id()
    src2 = write_site_source_version(
        memory,
        day=new_day,
        version=new_version,
        source_version_id=new_svid,
        status=STATUS_ACTIVE,
        supersedes=old_svid,
    )
    print(f"  wrote source v{new_version} day={new_day} svid={new_svid} supersedes={old_svid} id={src2['id']}")

    # 5. Approved correction entity
    corr = write_site_correction(
        memory,
        NAME_CORRECTION_APPROVED,
        from_version=old_svid,
        to_version=new_svid,
        decision=STATUS_APPROVED,
        reason="Calendar confirmed Monday.",
        status=STATUS_APPROVED,
    )
    print(f"  wrote correction decision=approved id={corr['id']}")

    # Update claim to cite new svid
    claim_quote = f"NovaDesk public launch is on {new_day}."
    write_site_claim(
        memory,
        NAME_CLAIM_PRESS,
        artifact=NAME_PRESS,
        source_version_id=new_svid,
        quote=claim_quote,
        status=STATUS_ACTIVE,
    )
    print(f"  updated claim {NAME_CLAIM_PRESS} -> svid={new_svid}")

    # 6. Invalidate dependents citing old_svid; regenerate ONLY those
    arts = read_site_list_artifacts(memory)
    invalidated = artifacts_invalidated_by(arts, {old_svid})
    names = [e["name"] for e in invalidated]
    print(f"  invalidated dependents: {names}")

    regenerated = []
    for ent in invalidated:
        name = ent["name"]
        if name == NAME_CONTROL:
            print(f"  SKIP control {NAME_CONTROL} (must not rewrite)")
            continue
        if name != NAME_PRESS:
            print(f"  SKIP unexpected artifact {name}")
            continue
        old_art_version = int(ent["body"].get("version") or 1)
        press_text = generate_press_brief(new_day)
        write_site_artifact(
            memory,
            NAME_PRESS,
            press_text,
            depends_on_source_version_id=new_svid,
            claim_ids=[NAME_CLAIM_PRESS],
            version=old_art_version + 1,
        )
        materialize_projection(NAME_PRESS, press_text)
        regenerated.append(name)
        print(f"  regenerated {name} citing new svid={new_svid}")

    # 7. Do NOT rewrite control — rematerialize control projection from live Sibyl only
    control_ent = next((e for e in arts if e["name"] == NAME_CONTROL), None)
    if control_ent:
        materialize_projection(NAME_CONTROL, control_ent["body"].get("text") or "")

    write_site_journal(
        memory,
        evaluated={
            "phase": "CORRECT",
            "from_day": old_day,
            "to_day": new_day,
            "old_svid": old_svid,
            "new_svid": new_svid,
        },
        acted={
            "op": "archive_and_correct",
            "regenerated": regenerated,
            "control_untouched": True,
        },
        forward={"next": "verify_hashes"},
    )

    # 8. after graph from Sibyl reads only
    after_path = write_graph("after", "after_graph.json")
    after = json.loads(after_path.read_text(encoding="utf-8"))
    print(f"  after_graph -> {after_path}")

    before_path = ARTIFACTS_DIR / "before_graph.json"
    before = json.loads(before_path.read_text(encoding="utf-8"))

    control_before = before["control_sha256"]
    control_after = after["control_sha256"]
    press_before = before["press_sha256"]
    press_after = after["press_sha256"]

    print(f"CONTROL_HASH_BEFORE={control_before}")
    print(f"CONTROL_HASH_AFTER={control_after}")
    print(f"PRESS_HASH_BEFORE={press_before}")
    print(f"PRESS_HASH_AFTER={press_after}")

    # supersedes trail
    live_sources = [s for s in after["sources"] if not s.get("archived")]
    archived = [s for s in after["sources"] if s.get("archived")]
    trail_ok = any(s.get("supersedes") == old_svid for s in live_sources) and any(
        s.get("source_version_id") == old_svid for s in archived
    )
    print(f"  supersedes_trail_ok={trail_ok}")

    control_ok = control_before is not None and control_before == control_after
    press_ok = (
        press_before is not None
        and press_after is not None
        and press_before != press_after
    )
    monday_ok = any(
        (not s.get("archived")) and s.get("day") == "Monday" for s in after["sources"]
    )
    corr_ok = any(c.get("decision") == STATUS_APPROVED for c in after.get("corrections") or [])

    passed = control_ok and press_ok and trail_ok and monday_ok and corr_ok and bool(regenerated)
    proof = "PASS" if passed else "FAIL"
    print(f"G2_PROOF={proof}")

    result = {
        "phase": "CORRECT",
        "ts": _ts(),
        "pid": os.getpid(),
        "old_svid": old_svid,
        "new_svid": new_svid,
        "control_hash_before": control_before,
        "control_hash_after": control_after,
        "press_hash_before": press_before,
        "press_hash_after": press_after,
        "control_unchanged": control_ok,
        "press_changed": press_ok,
        "supersedes_trail_ok": trail_ok,
        "regenerated": regenerated,
        "G2_PROOF": proof,
    }
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    result_path = ARTIFACTS_DIR / "g2_result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"  result -> {result_path}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())

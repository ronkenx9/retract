"""PROCESS 2 (dispute path) — Friday → not_established; control unchanged."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

from config import (
    ARTIFACTS_DIR,
    DB_PATH,
    NAME_CLAIM_PRESS,
    NAME_CONTROL,
    NAME_CORRECTION_DISPUTE,
    NAME_PRESS,
    STATUS_DISPUTED,
    STATUS_NOT_ESTABLISHED,
    TENANT_ID,
)
from graph import write_graph
from memory_io import (
    artifacts_invalidated_by,
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


def generate_press_brief_not_established() -> str:
    return (
        "PRESS BRIEF — NovaDesk\n"
        "Embargo lifts: not established\n"
        "Headline: NovaDesk public launch day is not established.\n"
        "Call to action: Do not schedule outreach until day is established.\n"
    )


def main() -> int:
    print(f"PHASE DISPUTE @ {_ts()}")
    print(f"  db={DB_PATH}")
    print(f"  tenant_id={TENANT_ID}")
    print(f"  pid={os.getpid()}")

    memory = open_memory()
    print(f"  schema_version={memory.schema_version()}")

    live = read_site_source(memory)
    body = live["body"]
    old_svid = body["source_version_id"]
    old_day = body.get("day")
    old_version = int(body.get("version") or 1)
    print(f"  live source day={old_day} version={old_version} svid={old_svid}")
    if old_day != "Friday":
        print(f"G2_DISPUTE_PROOF=FAIL reason=expected_Friday_got_{old_day}")
        return 1

    reason = "dispute Friday→not_established"
    arch = write_site_archive_source(memory, reason=reason)
    print(f"  archived source reason={reason} archived_id={arch.get('id')}")

    new_svid = new_id()
    new_version = old_version + 1
    src2 = write_site_source_version(
        memory,
        day=None,
        version=new_version,
        source_version_id=new_svid,
        status=STATUS_NOT_ESTABLISHED,
        supersedes=old_svid,
    )
    print(
        f"  wrote source v{new_version} day=null status=not_established "
        f"svid={new_svid} supersedes={old_svid} id={src2['id']}"
    )

    corr = write_site_correction(
        memory,
        NAME_CORRECTION_DISPUTE,
        from_version=old_svid,
        to_version=new_svid,
        decision=STATUS_DISPUTED,
        reason="Launch day disputed; treat as not established.",
        status=STATUS_NOT_ESTABLISHED,
    )
    print(f"  wrote correction decision=disputed id={corr['id']}")

    write_site_claim(
        memory,
        NAME_CLAIM_PRESS,
        artifact=NAME_PRESS,
        source_version_id=new_svid,
        quote="NovaDesk public launch day is not established.",
        status=STATUS_NOT_ESTABLISHED,
    )
    print(f"  updated claim {NAME_CLAIM_PRESS} status=not_established -> svid={new_svid}")

    arts = read_site_list_artifacts(memory)
    invalidated = artifacts_invalidated_by(arts, {old_svid})
    names = [e["name"] for e in invalidated]
    print(f"  invalidated dependents: {names}")

    regenerated = []
    for ent in invalidated:
        name = ent["name"]
        if name == NAME_CONTROL:
            print(f"  SKIP control {NAME_CONTROL}")
            continue
        if name != NAME_PRESS:
            continue
        old_art_version = int(ent["body"].get("version") or 1)
        press_text = generate_press_brief_not_established()
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
        print(f"  regenerated {name} -> not_established text citing svid={new_svid}")

    control_ent = next((e for e in arts if e["name"] == NAME_CONTROL), None)
    if control_ent:
        materialize_projection(NAME_CONTROL, control_ent["body"].get("text") or "")

    write_site_journal(
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

    after_path = write_graph("dispute", "dispute_graph.json")
    after = json.loads(after_path.read_text(encoding="utf-8"))
    print(f"  dispute_graph -> {after_path}")

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

    control_ok = control_before is not None and control_before == control_after
    press_changed = press_before != press_after
    press_text = ""
    for a in after.get("artifacts") or []:
        if a.get("name") == NAME_PRESS:
            press_text = a.get("text") or ""
    not_est_text = "not established" in press_text.lower()
    claim_ne = any(
        (c.get("status") == STATUS_NOT_ESTABLISHED)
        for c in after.get("claims") or []
    )
    corr_ne = any(
        c.get("decision") == STATUS_DISPUTED
        or c.get("status") == STATUS_NOT_ESTABLISHED
        for c in after.get("corrections") or []
    )
    source_ne = any(
        (not s.get("archived")) and s.get("status") == STATUS_NOT_ESTABLISHED
        for s in after.get("sources") or []
    )

    passed = (
        control_ok
        and press_changed
        and not_est_text
        and (claim_ne or corr_ne)
        and source_ne
        and bool(regenerated)
    )
    proof = "PASS" if passed else "FAIL"
    print(f"G2_DISPUTE_PROOF={proof}")
    print(f"  not_established_press_text={not_est_text}")
    print(f"  control_unchanged={control_ok}")

    result = {
        "phase": "DISPUTE",
        "ts": _ts(),
        "pid": os.getpid(),
        "old_svid": old_svid,
        "new_svid": new_svid,
        "control_hash_before": control_before,
        "control_hash_after": control_after,
        "press_hash_before": press_before,
        "press_hash_after": press_after,
        "control_unchanged": control_ok,
        "press_not_established": not_est_text,
        "G2_DISPUTE_PROOF": proof,
    }
    result_path = ARTIFACTS_DIR / "g2_dispute_result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"  result -> {result_path}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())

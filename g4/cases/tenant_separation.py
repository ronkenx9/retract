"""Case 4 — Tenant A correction must not appear in tenant B reads/graph."""
from __future__ import annotations

from typing import Any

from sibyl_memory_client import MemoryClient

from bridge import (
    CAT_ARTIFACT,
    CAT_CLAIM,
    CAT_SOURCE,
    DB_PATH,
    DB_PATH_B,
    NAME_CLAIM_PRESS,
    NAME_CONTROL,
    NAME_LAUNCH,
    NAME_PRESS,
    STATUS_ACTIVE,
    TENANT_A,
    TENANT_B,
    memory_io,
    rebind_db,
)
from hashes import CONTROL_ALWAYS, PRESS_FRIDAY, PRESS_MONDAY
from ops import correct_to, wipe_db


def _seed_tenant(db_path, tenant_id: str, day: str = "Friday", *, wipe: bool = False) -> str:
    if wipe:
        wipe_db(db_path)
    mem = MemoryClient.local(str(db_path), tenant_id=tenant_id)
    svid = memory_io.new_id()
    mem.set_entity(
        CAT_SOURCE,
        NAME_LAUNCH,
        {
            "source_version_id": svid,
            "status": STATUS_ACTIVE,
            "supersedes": None,
            "product": "NovaDesk",
            "claim": f"NovaDesk public launch is on {day}.",
            "day": day,
            "version": 1,
            "corpus": "fictional-owned-launch",
        },
        status="active",
    )
    mem.set_entity(
        CAT_CLAIM,
        NAME_CLAIM_PRESS,
        {
            "artifact": NAME_PRESS,
            "source_version_id": svid,
            "quote": f"NovaDesk public launch is on {day}.",
            "span": "launch-day",
            "status": STATUS_ACTIVE,
        },
        status="active",
    )
    press = memory_io.generate_press_brief(day)
    mem.set_entity(
        CAT_ARTIFACT,
        NAME_PRESS,
        {
            "text": press,
            "depends_on_source_version_id": svid,
            "source_version_ids": [svid],
            "claim_ids": [NAME_CLAIM_PRESS],
            "content_sha256": memory_io.content_sha256(press),
            "version": 1,
        },
        status="active",
    )
    control = memory_io.generate_company_blurb()
    mem.set_entity(
        CAT_ARTIFACT,
        NAME_CONTROL,
        {
            "text": control,
            "depends_on_source_version_id": None,
            "source_version_ids": [],
            "claim_ids": [],
            "content_sha256": memory_io.content_sha256(control),
            "version": 1,
        },
        status="active",
    )
    return svid


def run() -> dict[str, Any]:
    # Same DB file, two tenants — strongest isolation check
    wipe_db(DB_PATH)
    wipe_db(DB_PATH_B)

    svid_a = _seed_tenant(DB_PATH, TENANT_A, "Friday", wipe=False)
    svid_b = _seed_tenant(DB_PATH, TENANT_B, "Friday", wipe=False)

    # Verify both tenants see Friday before correction
    pre_a = MemoryClient.local(str(DB_PATH), tenant_id=TENANT_A).get_entity(CAT_SOURCE, NAME_LAUNCH)
    pre_b = MemoryClient.local(str(DB_PATH), tenant_id=TENANT_B).get_entity(CAT_SOURCE, NAME_LAUNCH)
    if pre_a["body"].get("day") != "Friday" or pre_b["body"].get("day") != "Friday":
        return {
            "case": "tenant_separation",
            "pass": False,
            "error": f"pre-check failed a={pre_a['body'].get('day')} b={pre_b['body'].get('day')}",
        }

    # Correct tenant A Friday→Monday via G2 call sites rebound to TENANT_A
    rebind_db(DB_PATH, TENANT_A)
    corr = correct_to(
        "Monday",
        reason="Tenant A calendar Monday.",
        expect_from="Friday",
    )

    mem_a = MemoryClient.local(str(DB_PATH), tenant_id=TENANT_A)
    mem_b = MemoryClient.local(str(DB_PATH), tenant_id=TENANT_B)

    a_src = mem_a.get_entity(CAT_SOURCE, NAME_LAUNCH)
    b_src = mem_b.get_entity(CAT_SOURCE, NAME_LAUNCH)
    a_press = mem_a.get_entity(CAT_ARTIFACT, NAME_PRESS)
    b_press = mem_b.get_entity(CAT_ARTIFACT, NAME_PRESS)

    a_day = a_src["body"].get("day")
    b_day = b_src["body"].get("day")
    a_hash = a_press["body"].get("content_sha256")
    b_hash = b_press["body"].get("content_sha256")

    # Separate DB file for tenant B remains Friday
    svid_b2 = _seed_tenant(DB_PATH_B, TENANT_B, "Friday", wipe=True)
    mem_b2 = MemoryClient.local(str(DB_PATH_B), tenant_id=TENANT_B)
    b2_day = mem_b2.get_entity(CAT_SOURCE, NAME_LAUNCH)["body"].get("day")

    isolation_ok = (
        a_day == "Monday"
        and b_day == "Friday"
        and a_hash == PRESS_MONDAY
        and b_hash == PRESS_FRIDAY
        and b2_day == "Friday"
        and a_src["body"].get("source_version_id") != b_src["body"].get("source_version_id")
    )
    control_ok = (
        mem_a.get_entity(CAT_ARTIFACT, NAME_CONTROL)["body"]["content_sha256"] == CONTROL_ALWAYS
        and mem_b.get_entity(CAT_ARTIFACT, NAME_CONTROL)["body"]["content_sha256"] == CONTROL_ALWAYS
    )

    passed = isolation_ok and control_ok and corr.get("control_ok") is True

    rebind_db(DB_PATH, TENANT_A)

    return {
        "case": "tenant_separation",
        "pass": passed,
        "db": str(DB_PATH),
        "db_b": str(DB_PATH_B),
        "tenant_a": TENANT_A,
        "tenant_b": TENANT_B,
        "tenant_a_day": a_day,
        "tenant_b_day_same_db": b_day,
        "tenant_b_day_separate_db": b2_day,
        "tenant_a_press_sha256": a_hash,
        "tenant_b_press_sha256": b_hash,
        "seed_svid_a": svid_a,
        "seed_svid_b": svid_b,
        "seed_svid_b2": svid_b2,
        "isolation_ok": isolation_ok,
    }

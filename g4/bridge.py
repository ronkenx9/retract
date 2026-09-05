"""Patch G2 config to a G4-dedicated DB before importing Sibyl call sites.

Does not modify G2/G3 source or DBs. Patches module-level bindings captured
at import time (same pattern as g3/g2_bridge.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

G4_ROOT = Path(__file__).resolve().parent
G2_ROOT = G4_ROOT.parent / "g2"
DB_PATH = G4_ROOT / "memory_a.db"
ARTIFACTS_DIR = G4_ROOT / "artifacts"
PROJECTIONS_DIR = ARTIFACTS_DIR / "projections"

# Dedicated G4 tenants (do not share with G1/G2/G3)
TENANT_A = "a4444444-b444-c444-d444-e44444444444"
TENANT_B = "b4444444-b444-c444-d444-e44444444445"
DB_PATH_B = G4_ROOT / "memory_b.db"

_g2_on_path = str(G2_ROOT)
if _g2_on_path not in sys.path:
    sys.path.insert(0, _g2_on_path)

import config as g2_config  # noqa: E402

g2_config.DB_PATH = DB_PATH
g2_config.ARTIFACTS_DIR = ARTIFACTS_DIR
g2_config.PROJECTIONS_DIR = PROJECTIONS_DIR
g2_config.TENANT_ID = TENANT_A

import memory_io  # noqa: E402
import graph  # noqa: E402

memory_io.DB_PATH = DB_PATH
memory_io.PROJECTIONS_DIR = PROJECTIONS_DIR
memory_io.TENANT_ID = TENANT_A
graph.ARTIFACTS_DIR = ARTIFACTS_DIR

from config import (  # noqa: E402,F401
    NAME_CLAIM_PRESS,
    NAME_CONTROL,
    NAME_CORRECTION_APPROVED,
    NAME_CORRECTION_DISPUTE,
    NAME_LAUNCH,
    NAME_PRESS,
    STATUS_ACTIVE,
    STATUS_APPROVED,
    STATUS_DISPUTED,
    STATUS_NOT_ESTABLISHED,
    STATUS_SUPERSEDED,
    CAT_SOURCE,
    CAT_ARTIFACT,
    CAT_CLAIM,
    CAT_CORRECTION,
)


def rebind_db(path: Path, tenant_id: str = TENANT_A) -> None:
    """Point G2 call sites at a different G4-local DB + tenant."""
    global DB_PATH
    DB_PATH = Path(path)
    g2_config.DB_PATH = DB_PATH
    g2_config.TENANT_ID = tenant_id
    memory_io.DB_PATH = DB_PATH
    memory_io.TENANT_ID = tenant_id


__all__ = [
    "G4_ROOT",
    "G2_ROOT",
    "DB_PATH",
    "DB_PATH_B",
    "ARTIFACTS_DIR",
    "PROJECTIONS_DIR",
    "TENANT_A",
    "TENANT_B",
    "g2_config",
    "memory_io",
    "graph",
    "rebind_db",
    "NAME_CLAIM_PRESS",
    "NAME_CONTROL",
    "NAME_CORRECTION_APPROVED",
    "NAME_CORRECTION_DISPUTE",
    "NAME_LAUNCH",
    "NAME_PRESS",
    "STATUS_ACTIVE",
    "STATUS_APPROVED",
    "STATUS_DISPUTED",
    "STATUS_NOT_ESTABLISHED",
    "STATUS_SUPERSEDED",
    "CAT_SOURCE",
    "CAT_ARTIFACT",
    "CAT_CLAIM",
    "CAT_CORRECTION",
]

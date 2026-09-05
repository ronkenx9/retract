"""Patch G2 config to a G5-dedicated DB before importing Sibyl call sites.

Does not modify G2/G3 source or DBs. Patches module-level bindings captured
at import time (same pattern as g3/g2_bridge.py / g4/bridge.py).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

G5_ROOT = Path(__file__).resolve().parent
G2_ROOT = G5_ROOT.parent / "g2"
G3_ROOT = G5_ROOT.parent / "g3"

# Optional env overrides (also mirrored into g3/g2_bridge for desk demos)
_db_env = os.environ.get("RETRACT_DB_PATH")
_art_env = os.environ.get("RETRACT_ARTIFACTS_DIR")
DB_PATH = Path(_db_env) if _db_env else (G5_ROOT / "memory.db")
ARTIFACTS_DIR = Path(_art_env) if _art_env else (G5_ROOT / "artifacts")
PROJECTIONS_DIR = ARTIFACTS_DIR / "projections"

# Dedicated G5 tenant (do not share with G1/G2/G3/G4)
TENANT_ID = "a5555555-b555-c555-d555-e55555555555"

_g2_on_path = str(G2_ROOT)
if _g2_on_path not in sys.path:
    sys.path.insert(0, _g2_on_path)

import config as g2_config  # noqa: E402

g2_config.DB_PATH = DB_PATH
g2_config.ARTIFACTS_DIR = ARTIFACTS_DIR
g2_config.PROJECTIONS_DIR = PROJECTIONS_DIR
g2_config.TENANT_ID = TENANT_ID

import memory_io  # noqa: E402
import graph  # noqa: E402

memory_io.DB_PATH = DB_PATH
memory_io.PROJECTIONS_DIR = PROJECTIONS_DIR
memory_io.TENANT_ID = TENANT_ID
graph.ARTIFACTS_DIR = ARTIFACTS_DIR

from config import (  # noqa: E402,F401
    CAT_ARTIFACT,
    CAT_CLAIM,
    CAT_CORRECTION,
    CAT_SOURCE,
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
)


def rebind_db(path: Path, tenant_id: str = TENANT_ID) -> None:
    """Point G2 call sites at a different G5-local DB + tenant."""
    global DB_PATH
    DB_PATH = Path(path)
    g2_config.DB_PATH = DB_PATH
    g2_config.TENANT_ID = tenant_id
    memory_io.DB_PATH = DB_PATH
    memory_io.TENANT_ID = tenant_id


__all__ = [
    "G5_ROOT",
    "G2_ROOT",
    "G3_ROOT",
    "DB_PATH",
    "ARTIFACTS_DIR",
    "PROJECTIONS_DIR",
    "TENANT_ID",
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

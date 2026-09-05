"""Patch G2 config to a G3-dedicated DB before importing Sibyl call sites.

Does not modify G2 source files. Patches module-level DB_PATH bindings that
were bound at import time in memory_io / graph.

Optional env (for G5 desk demos):
  RETRACT_DB_PATH       — override DB file (default: g3/memory.db)
  RETRACT_ARTIFACTS_DIR — override artifacts dir (default: g3/artifacts)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

G3_ROOT = Path(__file__).resolve().parent
G2_ROOT = G3_ROOT.parent / "g2"
_db_env = os.environ.get("RETRACT_DB_PATH")
_art_env = os.environ.get("RETRACT_ARTIFACTS_DIR")
DB_PATH = Path(_db_env) if _db_env else (G3_ROOT / "memory.db")
ARTIFACTS_DIR = Path(_art_env) if _art_env else (G3_ROOT / "artifacts")
PROJECTIONS_DIR = ARTIFACTS_DIR / "projections"

_g2_on_path = str(G2_ROOT)
if _g2_on_path not in sys.path:
    sys.path.insert(0, _g2_on_path)

import config as g2_config  # noqa: E402

g2_config.DB_PATH = DB_PATH
g2_config.ARTIFACTS_DIR = ARTIFACTS_DIR
g2_config.PROJECTIONS_DIR = PROJECTIONS_DIR
_tenant_env = os.environ.get("RETRACT_TENANT_ID")
if _tenant_env:
    g2_config.TENANT_ID = _tenant_env

import memory_io  # noqa: E402
import graph  # noqa: E402

# Re-bind names captured at import time inside those modules.
memory_io.DB_PATH = DB_PATH
memory_io.PROJECTIONS_DIR = PROJECTIONS_DIR
if _tenant_env:
    memory_io.TENANT_ID = _tenant_env
graph.ARTIFACTS_DIR = ARTIFACTS_DIR

# Re-export for ops / app convenience
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
    TENANT_ID,
)

__all__ = [
    "G3_ROOT",
    "G2_ROOT",
    "DB_PATH",
    "ARTIFACTS_DIR",
    "PROJECTIONS_DIR",
    "g2_config",
    "memory_io",
    "graph",
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
    "TENANT_ID",
]

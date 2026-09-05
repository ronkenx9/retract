#!/usr/bin/env python3
"""G1 hardest-proof runner — SEED / KILL / COLD_START / RESULT with timestamps.

Spawns seed.py as a child, waits for exit (KILL), then spawns cold_start.py
as a brand-new process with empty Python state and the same DB path.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

G1_ROOT = Path(__file__).resolve().parent
VENV_PYTHON = G1_ROOT.parent / ".venv" / "bin" / "python"
DB_PATH = G1_ROOT / "memory.db"
TRACE_PATH = G1_ROOT / "TRACE.txt"


def _ts() -> str:
    # Commit-style UTC timestamp (labeled; user zone is WAT/UTC+1)
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _commit_style_id() -> str:
    raw = f"{_ts()}-{os.getpid()}-{time.time_ns()}".encode()
    return hashlib.sha1(raw).hexdigest()[:12]


def _run_phase(label: str, script: str, env: dict | None = None) -> int:
    py = str(VENV_PYTHON if VENV_PYTHON.exists() else sys.executable)
    cmd = [py, str(G1_ROOT / script)]
    print(f"\n==== SPAWN {label} @ {_ts()} commit={_commit_style_id()} ====")
    print(f"  cmd={cmd}")
    print(f"  parent_pid={os.getpid()}")
    proc = subprocess.Popen(
        cmd,
        cwd=str(G1_ROOT),
        env=env or os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    rc = proc.wait()
    print(f"==== EXIT {label} rc={rc} child_pid={proc.pid} @ {_ts()} ====")
    return rc


def main() -> int:
    # Fresh DB for a clean proof run
    if DB_PATH.exists():
        DB_PATH.unlink()
    for side in (G1_ROOT / "memory.db-wal", G1_ROOT / "memory.db-shm"):
        if side.exists():
            side.unlink()
    proj = G1_ROOT / "artifacts" / "projections"
    if proj.exists():
        shutil.rmtree(proj)
    proj.mkdir(parents=True, exist_ok=True)

    print(f"PHASE RUNNER_START @ {_ts()} commit={_commit_style_id()}")
    print(f"  g1_root={G1_ROOT}")
    print(f"  db_path={DB_PATH}")
    print(f"  python={VENV_PYTHON if VENV_PYTHON.exists() else sys.executable}")

    rc_seed = _run_phase("SEED", "seed.py")
    if rc_seed != 0:
        print("PHASE RESULT FAIL — seed failed")
        return rc_seed

    print(f"\nPHASE KILL @ {_ts()} commit={_commit_style_id()}")
    print("  seed child process has fully exited; no shared Python state remains")
    print("  sleeping 0.5s to make process boundary obvious in transcript")
    time.sleep(0.5)

    rc_cold = _run_phase("COLD_START", "cold_start.py")
    print(f"\nPHASE RUNNER_END @ {_ts()} commit={_commit_style_id()}")
    return rc_cold


if __name__ == "__main__":
    # Tee stdout to TRACE.txt unedited
    class Tee:
        def __init__(self, *streams):
            self.streams = streams

        def write(self, data):
            for s in self.streams:
                s.write(data)
                s.flush()

        def flush(self):
            for s in self.streams:
                s.flush()

    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TRACE_PATH.open("w", encoding="utf-8") as tf:
        tf.write(f"# RETRACT G1 TRACE — unedited capture\n")
        tf.write(f"# started {_ts()} (UTC; WAT=UTC+1)\n")
        tf.write(f"# runner={__file__}\n\n")
        sys.stdout = Tee(sys.__stdout__, tf)
        try:
            code = main()
        finally:
            sys.stdout = sys.__stdout__
            tf.write(f"\n# finished {_ts()} exit={code}\n")
    print(f"TRACE written -> {TRACE_PATH}")
    raise SystemExit(code)

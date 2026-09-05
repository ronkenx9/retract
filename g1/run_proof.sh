#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PY="$ROOT/../.venv/bin/python"
cd "$ROOT"
rm -f memory.db memory.db-wal memory.db-shm
rm -rf artifacts/*
mkdir -p artifacts/projections
{
  echo "===== RETRACT G1 UNEDITED TRACE ====="
  echo "host=$(hostname) date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "python=$($PY -c 'import sys,sibyl_memory_client as s; print(sys.executable, s.__version__)')"
  echo
  echo "----- PROCESS 1: SEED (then EXIT/KILL) -----"
  "$PY" seed.py
  echo "seed_pid_gone=yes (process exited)"
  echo
  echo "----- PROCESS 2: COLD_START (fresh PID, same DB) -----"
  "$PY" cold_start.py
  echo
  echo "===== END TRACE ====="
} 2>&1 | tee artifacts/g1_unedited_trace.txt

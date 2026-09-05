#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PY="$ROOT/../.venv/bin/python"
cd "$ROOT"

clean_db() {
  rm -f memory.db memory.db-wal memory.db-shm
}

clean_artifacts() {
  # Preserve the live unedited trace while tee is writing it
  find artifacts -mindepth 1 -maxdepth 1 ! -name 'g2_unedited_trace.txt' -exec rm -rf {} +
  mkdir -p artifacts/projections
}

OVERALL=PASS
mkdir -p artifacts/projections
: > artifacts/g2_unedited_trace.txt

{
  echo "===== RETRACT G2 UNEDITED TRACE ====="
  echo "host=$(hostname) date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  VER=$($PY -c "import sys,sibyl_memory_client as s; print(sys.executable, getattr(s, '__version__', '?'))")
  echo "python=$VER"
  echo

  echo "===== PATH A: clean → seed → correct ====="
  clean_db
  clean_artifacts
  echo "----- PROCESS 1: SEED (then EXIT/KILL) -----"
  "$PY" seed.py
  echo "seed_pid_gone=yes (process exited)"
  echo
  echo "----- PROCESS 2: CORRECT (fresh PID, same DB) -----"
  if "$PY" correct.py; then
    echo "PATH_A=PASS"
  else
    echo "PATH_A=FAIL"
    OVERALL=FAIL
  fi
  echo

  # Preserve correct-path graphs/result across path B (seed rewrites before_graph)
  cp -f artifacts/before_graph.json artifacts/before_graph.correct.json
  cp -f artifacts/after_graph.json artifacts/after_graph.correct.json
  cp -f artifacts/g2_result.json artifacts/g2_result.correct.json

  echo "===== PATH B: clean → seed → dispute ====="
  clean_db
  echo "----- PROCESS 1: SEED (then EXIT/KILL) -----"
  "$PY" seed.py
  echo "seed_pid_gone=yes (process exited)"
  echo
  echo "----- PROCESS 2: DISPUTE (fresh PID, same DB) -----"
  if "$PY" dispute.py; then
    echo "PATH_B=PASS"
  else
    echo "PATH_B=FAIL"
    OVERALL=FAIL
  fi
  echo

  # Restore correct-path graphs as canonical packaging artifacts
  mv -f artifacts/before_graph.correct.json artifacts/before_graph.json
  mv -f artifacts/after_graph.correct.json artifacts/after_graph.json
  mv -f artifacts/g2_result.correct.json artifacts/g2_result.json

  echo "===== OVERALL ====="
  echo "G2_PROOF=${OVERALL}"
  echo "===== END TRACE ====="
} 2>&1 | tee artifacts/g2_unedited_trace.txt

if grep -q '^G2_PROOF=PASS$' artifacts/g2_unedited_trace.txt; then
  exit 0
else
  exit 1
fi

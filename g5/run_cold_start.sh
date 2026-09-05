#!/usr/bin/env bash
# RETRACT G5 — live cold-start proof (seed PID exit → correct PID). Local only.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PY="$ROOT/../.venv/bin/python"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

mkdir -p artifacts/projections artifacts/screenshots
: > artifacts/g5_unedited_trace.txt

# Unique run_id shared by both workers
G5_RUN_ID="$("$PY" -c 'import uuid; print(uuid.uuid4())')"
export G5_RUN_ID

OVERALL=PASS
DESK_NOTE="skipped"

{
  echo "===== RETRACT G5 UNEDITED COLD-START TRACE ====="
  echo "host=$(hostname) date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "run_id=${G5_RUN_ID}"
  VER=$("$PY" -c "import sys,sibyl_memory_client as s; print(sys.executable, getattr(s, '__version__', '?'))")
  echo "python=$VER"
  echo "db=$ROOT/memory.db"
  echo

  echo "----- PROCESS A: SEED Friday (then EXIT/KILL) -----"
  rm -f memory.db memory.db-wal memory.db-shm
  # Preserve live tee log; clear other artifacts except the trace itself
  find artifacts -mindepth 1 -maxdepth 1 ! -name 'g5_unedited_trace.txt' -exec rm -rf {} +
  mkdir -p artifacts/projections artifacts/screenshots
  "$PY" seed_worker.py
  SEED_EXIT=$?
  echo "seed_exit=${SEED_EXIT}"
  echo "seed_pid_gone=yes (process exited — Python state discarded)"
  if [[ "$SEED_EXIT" -ne 0 ]]; then
    OVERALL=FAIL
  fi
  echo

  echo "----- PROCESS B: CORRECT Friday→Monday (fresh PID, same DB) -----"
  if "$PY" correct_worker.py; then
    echo "CLI_COLD_START=PASS"
  else
    echo "CLI_COLD_START=FAIL"
    OVERALL=FAIL
  fi
  echo

  # Preserve CLI cold-start artifacts before optional desk (desk re-seeds DB)
  mkdir -p artifacts/cli_proof
  for f in before_graph.json after_graph.json g5_result.json g5_sibyl_pointers.json seed_meta.json; do
    [[ -f "artifacts/$f" ]] && cp -f "artifacts/$f" "artifacts/cli_proof/$f"
  done
  if [[ -d artifacts/projections ]]; then
    rm -rf artifacts/cli_proof/projections
    cp -a artifacts/projections artifacts/cli_proof/projections
  fi
  if [[ -d artifacts/before_projections ]]; then
    rm -rf artifacts/cli_proof/before_projections
    cp -a artifacts/before_projections artifacts/cli_proof/before_projections
  fi

  # Optional G3 desk path: start uvicorn with RETRACT_DB_PATH → g5/memory.db
  echo "----- OPTIONAL: G3 desk HTTP against G5 DB -----"
  if [[ -f "$ROOT/../g3/app.py" ]]; then
    # Re-seed Friday so desk can apply the same beat via HTTP
    echo "Re-seeding Friday for desk drive (separate from CLI proof above)..."
    SAVED_RUN_ID="$G5_RUN_ID"
    export G5_RUN_ID="${SAVED_RUN_ID}-desk"
    "$PY" seed_worker.py >/dev/null
    export G5_RUN_ID="$SAVED_RUN_ID"

    export RETRACT_DB_PATH="$ROOT/memory.db"
    export RETRACT_ARTIFACTS_DIR="$ROOT/artifacts"
    export RETRACT_TENANT_ID="a5555555-b555-c555-d555-e55555555555"
    # Stop any prior listener on 8765
    if command -v fuser >/dev/null 2>&1; then
      fuser -k 8765/tcp >/dev/null 2>&1 || true
    else
      pkill -f 'uvicorn app:app' >/dev/null 2>&1 || true
    fi
    sleep 0.3
    (
      cd "$ROOT/../g3"
      export PYTHONPATH="$ROOT/../g3${PYTHONPATH:+:$PYTHONPATH}"
      export RETRACT_DB_PATH="$ROOT/memory.db"
      export RETRACT_ARTIFACTS_DIR="$ROOT/artifacts"
      export RETRACT_TENANT_ID="a5555555-b555-c555-d555-e55555555555"
      exec "$PY" -m uvicorn app:app --host 127.0.0.1 --port 8765 --log-level warning
    ) >artifacts/uvicorn_g5.log 2>&1 &
    UV_PID=$!
    echo "uvicorn_pid=${UV_PID}"
    # Wait for health
    DESK_OK=0
    for i in 1 2 3 4 5 6 7 8 9 10; do
      if curl -sf http://127.0.0.1:8765/api/health >/dev/null 2>&1; then
        DESK_OK=1
        break
      fi
      sleep 0.4
    done
    if [[ "$DESK_OK" -eq 1 ]]; then
      echo "desk_health=ok"
      STATE_BEFORE=$(curl -sf http://127.0.0.1:8765/api/state || true)
      echo "desk_state_before_press=$(echo "$STATE_BEFORE" | "$PY" -c 'import sys,json; d=json.load(sys.stdin); print((d.get("checks") or d.get("hash_check") or {}).get("actual",d.get("graph",{})).get("press") if False else (d.get("graph") or {}).get("press_sha256") or (d.get("hash_check") or {}).get("press_sha256",""))' 2>/dev/null || echo '?')"
      CORRECT_RESP=$(curl -sf -X POST http://127.0.0.1:8765/api/correct \
        -H 'Content-Type: application/json' \
        -d '{"day":"Monday","reason":"Calendar confirmed Monday."}' || echo '{"error":"curl_failed"}')
      echo "desk_correct_resp_snip=$(echo "$CORRECT_RESP" | head -c 200)"
      PRESS_AFTER=$(echo "$CORRECT_RESP" | "$PY" -c '
import sys,json
d=json.load(sys.stdin)
h=(d.get("hash_check") or {})
print(h.get("press_sha256") or (d.get("graph") or {}).get("press_sha256") or "")
' 2>/dev/null || true)
      CTRL_AFTER=$(echo "$CORRECT_RESP" | "$PY" -c '
import sys,json
d=json.load(sys.stdin)
h=(d.get("hash_check") or {})
print(h.get("control_sha256") or (d.get("graph") or {}).get("control_sha256") or "")
' 2>/dev/null || true)
      echo "desk_control_sha256=${CTRL_AFTER}"
      echo "desk_press_sha256=${PRESS_AFTER}"
      EXPECT_C=8846d618d6c377adbf6dd53a6939d4be01d5b67b5c4d6ff65fb12e5ab94453f7
      EXPECT_P=37437dcd61110f51274bfe64b727d9c448b8e2b2329efacd4b7f9b473aab0e03
      if [[ "$CTRL_AFTER" == "$EXPECT_C" && "$PRESS_AFTER" == "$EXPECT_P" ]]; then
        echo "DESK_DRIVE=PASS"
        DESK_NOTE="PASS (uvicorn+RETRACT_DB_PATH→g5/memory.db)"
      else
        echo "DESK_DRIVE=FAIL"
        DESK_NOTE="FAIL hashes mismatch"
        # Desk failure does not fail primary CLI cold-start; note only
      fi
    else
      echo "DESK_DRIVE=SKIP reason=uvicorn_not_ready"
      DESK_NOTE="SKIP uvicorn not ready — see artifacts/uvicorn_g5.log"
    fi
    kill "$UV_PID" 2>/dev/null || true
    wait "$UV_PID" 2>/dev/null || true
  else
    echo "DESK_DRIVE=SKIP reason=no_g3_app"
    DESK_NOTE="SKIP no g3/app.py"
  fi
  # Restore CLI cold-start artifacts as canonical packaging outputs
  if [[ -d artifacts/cli_proof ]]; then
    for f in before_graph.json after_graph.json g5_result.json g5_sibyl_pointers.json seed_meta.json; do
      [[ -f "artifacts/cli_proof/$f" ]] && cp -f "artifacts/cli_proof/$f" "artifacts/$f"
    done
    if [[ -d artifacts/cli_proof/projections ]]; then
      rm -rf artifacts/projections
      cp -a artifacts/cli_proof/projections artifacts/projections
    fi
    if [[ -d artifacts/cli_proof/before_projections ]]; then
      rm -rf artifacts/before_projections
      cp -a artifacts/cli_proof/before_projections artifacts/before_projections
    fi
    echo "restored_cli_proof_artifacts=yes"
  fi
  echo

  echo "===== OVERALL ====="
  # Prefer CLI proof from g5_result.json
  if [[ -f artifacts/g5_result.json ]]; then
    CLI=$("$PY" -c 'import json; print(json.load(open("artifacts/g5_result.json"))["G5_PROOF"])')
    OVERALL="$CLI"
  fi
  echo "G5_PROOF=${OVERALL}"
  echo "desk_note=${DESK_NOTE}"
  echo "run_id=${G5_RUN_ID}"
  echo "===== END TRACE ====="
} 2>&1 | tee artifacts/g5_unedited_trace.txt

# Write desk_drive.md summary
cat > artifacts/desk_drive.md << MD
# G5 desk drive notes

Primary proof is **CLI cold-start** (\`seed_worker.py\` exit → \`correct_worker.py\`).

## Desk APIs that mirror G5 ops

| HTTP | Mirrors |
|---|---|
| \`POST /api/reset\` / \`POST /api/seed\` | \`ops.seed(force=True)\` |
| \`GET /api/state\` | graph + hash checks from Sibyl |
| \`POST /api/correct\` | \`ops.correct(day=Monday)\` Friday→Monday |
| \`POST /api/dispute\` | dispute path (not used in G5 cold-start) |

## This run

- Env: \`RETRACT_DB_PATH=$ROOT/memory.db\` \`RETRACT_ARTIFACTS_DIR=$ROOT/artifacts\`
- Result: see \`desk_note\` line in \`g5_unedited_trace.txt\`
- If desk was SKIP/FAIL, CLI cold-start remains authoritative for \`G5_PROOF\`.

MD

if grep -q '^G5_PROOF=PASS$' artifacts/g5_unedited_trace.txt; then
  exit 0
else
  exit 1
fi

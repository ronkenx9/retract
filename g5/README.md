# RETRACT G5 — live cold-start proof

**Product:** RETRACT (Sibyl Labs Hackathon)  
**Package:** `sibyl-memory-client==0.8.0` via `/workspace/retract/.venv`  
**Scope:** Local only. Do not publish. Dedicated DB under `g5/` only.

## What this proves

Fresh correction with **new worker/agent contexts** and **persisted Sibyl state**:

1. **Process A** (`seed_worker.py`): seed Friday via G2 write sites into `g5/memory.db`, then **EXIT**
2. **Process B** (`correct_worker.py`): fresh PID, empty Python state, same DB — read Sibyl only, apply approved Friday→Monday
3. Assert locked hashes:
   - control `8846d618d6c377adbf6dd53a6939d4be01d5b67b5c4d6ff65fb12e5ab94453f7`
   - press (Monday) `37437dcd61110f51274bfe64b727d9c448b8e2b2329efacd4b7f9b473aab0e03`
4. Print `G5_PROOF=PASS|FAIL`

The unedited tee log **is** the continuous cold-start segment (seed PID exit → correct PID).

Optional: G3 desk HTTP against the same G5 DB via `RETRACT_DB_PATH` (see `artifacts/desk_drive.md`).

## Run

```bash
cd /workspace/retract/g5
./run_cold_start.sh
```

## Layout

| Path | Role |
|---|---|
| `bridge.py` | Patch G2 `DB_PATH` / tenant / artifacts → `g5/memory.db` |
| `ops.py` | Seed + correct (mirrors g3 ops) + Sibyl pointer capture |
| `hashes.py` | Locked Friday/Monday/control hashes |
| `seed_worker.py` | Process A — seed then exit |
| `correct_worker.py` | Process B — cold-start correct |
| `run_cold_start.sh` | Orchestrator → tee `artifacts/g5_unedited_trace.txt` |
| `memory.db` | G5-only Sibyl DB |
| `artifacts/g5_sibyl_pointers.json` | Entity ids, svids, get_entity call sites |
| `artifacts/g5_result.json` | Machine-readable proof result |

## Safety

- Never writes `/workspace/retract/g{1,2,3,4}/memory.db`
- Prefers `archive_entity` over hard-delete
- Reuses G2 `memory_io` / `graph` via `sys.path` + rebind
- Unique `run_id` (uuid) printed in both workers

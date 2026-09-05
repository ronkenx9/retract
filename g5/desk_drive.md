# G5 desk drive notes

Primary proof is **CLI cold-start** (`seed_worker.py` exit → `correct_worker.py`).

## Desk APIs that mirror G5 ops

| HTTP | Mirrors |
|---|---|
| `POST /api/reset` / `POST /api/seed` | `ops.seed(force=True)` |
| `GET /api/state` | graph + hash checks from Sibyl |
| `POST /api/correct` | `ops.correct(day=Monday)` Friday→Monday |
| `POST /api/dispute` | dispute path (not used in G5 cold-start) |

## This run

- Env: `RETRACT_DB_PATH=/workspace/retract/g5/memory.db`
- Env: `RETRACT_ARTIFACTS_DIR=/workspace/retract/g5/artifacts`
- Env: `RETRACT_TENANT_ID=a5555555-b555-c555-d555-e55555555555`
- Result: **DESK_DRIVE=PASS** (uvicorn + POST /api/correct → Monday hashes)
- CLI cold-start remains authoritative for `G5_PROOF` (artifacts restored from `cli_proof/`).

Without those env vars, the desk continues to use `g3/memory.db` (unchanged default).

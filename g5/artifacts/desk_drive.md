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

- Env: `RETRACT_DB_PATH=/workspace/retract/g5/memory.db` `RETRACT_ARTIFACTS_DIR=/workspace/retract/g5/artifacts`
- Result: see `desk_note` line in `g5_unedited_trace.txt`
- If desk was SKIP/FAIL, CLI cold-start remains authoritative for `G5_PROOF`.


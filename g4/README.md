# RETRACT G4 — adversarial test suite

**Product:** RETRACT (Sibyl Labs Hackathon)  
**Package:** `sibyl-memory-client==0.8.0` via `/workspace/retract/.venv`  
**Scope:** Local only. Do not publish. Dedicated DBs under `g4/` only.

## What this proves

Six adversarial cases against G2 Sibyl write/read sites (patched like G3):

| # | Case | Pass criterion |
|---|---|---|
| 1 | Stale UI/projection cache vs Sibyl | After correction, stale cache shows Friday; Sibyl/graph show Monday; staleness detected; product truth = Sibyl |
| 2 | Repeated corrections | Friday→Monday→Tuesday each supersedes prior; press updates; control hash stays `8846d618…453f7` |
| 3 | Conflicting sources | Disagreeing live claims detected; ambiguous regen refused; dependents not inconsistently updated |
| 4 | Tenant separation | Tenant A Monday correction absent from tenant B reads on same + separate DB |
| 5 | Deleted memory litmus | Sibyl available → selective invalidation PASS; Sibyl blocked/missing → FAIL; no JSON fact-store rescue |
| 6 | Concurrent requests | Racing corrections → consistent end state (one live day + matching press); no crash |

`G4_PROOF=PASS` only if **all six** pass.

## Run

```bash
cd /workspace/retract/g4
../.venv/bin/python run_adversarial.py 2>&1 | tee artifacts/g4_unedited_trace.txt
```

Or:

```bash
./run.sh
```

## Layout

| Path | Role |
|---|---|
| `bridge.py` | Patch G2 `DB_PATH` / tenant / artifacts (does not touch G2/G3 files or DBs) |
| `ops.py` | Seed + generalized `correct_to` + conflict detection/refuse gate |
| `hashes.py` | Locked Friday/Monday/Tuesday/control hashes |
| `cases/*.py` | One module per adversarial case |
| `run_adversarial.py` | Suite runner → `artifacts/g4_results.json` |
| `memory_a.db` / `memory_b.db` | G4-only Sibyl DBs |
| `artifacts/g4_unedited_trace.txt` | Tee’d run log ending `G4_PROOF=PASS\|FAIL` |

## Safety

- Never writes `/workspace/retract/g{1,2,3}/memory.db`
- Prefers `archive_entity` over hard-delete
- Reuses G2 `memory_io` / `graph` via `sys.path` + rebind (same pattern as `g3/g2_bridge.py`)

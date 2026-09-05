# RETRACT G1 — hardest proof

**Product:** RETRACT (Sibyl Labs Hackathon, team `scar`)  
**Gate:** write source + dependent artifact through Sibyl → kill process → cold start (empty chat / new process, same DB) → correct source → dependent artifact changes.

## What this proves

1. Semantic state lives **only** in Sibyl Memory (`MemoryClient.local`).
2. After a full process kill, a **new** Python process reconstructs state from the same `memory.db`.
3. Correcting the source (`Friday` → `Monday`) regenerates the **dependent** artifact (`press-brief`).
4. A **control** artifact (`company-blurb`) stays unchanged (selective invalidation).
5. Deletion smoke: without Sibyl reads, the cold-start correction cannot change the artifact.

## Layout

| Path | Role |
|---|---|
| `config.py` | Project DB path + dedicated `tenant_id` |
| `memory_io.py` | **`write_site_*` / `read_site_*`** Sibyl call sites |
| `seed.py` | PHASE SEED — write source + artifacts, exit |
| `cold_start.py` | PHASE COLD_START — read, archive+correct, regenerate |
| `run_g1.py` | Runner: SEED → KILL → COLD_START → RESULT; writes `TRACE.txt` |
| `deletion_smoke.py` | Optional: proves Sibyl is load-bearing |
| `memory.db` | Project-scoped Sibyl SQLite (created at run) |
| `artifacts/projections/` | Regenerated views only — **not** source of truth |
| `TRACE.txt` | Unedited terminal capture of a successful run |
| `POINTERS.md` | file:line for write/read sites |

## Run

```bash
cd /workspace/retract/g1
../.venv/bin/python run_g1.py
# optional:
../.venv/bin/python deletion_smoke.py
```

Requires `sibyl-memory-client==0.8.0` in `/workspace/retract/.venv`.

## Memory is load-bearing

- Writes: `memory.set_entity` / `archive_entity` / `write_event` via `write_site_*` in `memory_io.py`.
- Reads: `memory.get_entity` / `read_events` via `read_site_*` in `memory_io.py`.
- UNIQUE `(tenant_id, category, name)`: corrections **archive** the superseded source, then set a new body with `version` bumped; journal records the retract.
- See `POINTERS.md` for exact lines (judge findable in &lt; 2 minutes).

## Fictional corpus

NovaDesk launch copy is fictional and owned by the demo. No public outreach / real-person claims.

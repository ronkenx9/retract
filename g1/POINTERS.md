# G1 POINTERS — Sibyl write/read call sites

Judge map: find write + read in under two minutes.

## Core wrappers (`memory_io.py`)

| Kind | Symbol | File:line | Underlying Sibyl call |
|---|---|---|---|
| WRITE | `write_site_source` | `memory_io.py:35` | `set_entity` @ L44 |
| WRITE | `write_site_artifact` | `memory_io.py:47` | `set_entity` @ L61 |
| WRITE | `write_site_journal` | `memory_io.py:64` | `write_event` @ L72 |
| WRITE | `write_site_archive_source` | `memory_io.py:75` | `archive_entity` @ L77 |
| READ | `read_site_source` | `memory_io.py:84` | `get_entity` @ L86 |
| READ | `read_site_artifact` | `memory_io.py:89` | `get_entity` @ L91 |
| READ | `read_site_events` | `memory_io.py:94` | `read_events` @ L96 |

## Invocation sites

### SEED (`seed.py`)
- `seed.py:36` — `src = write_site_source(memory, day=day, version=version)`
- `seed.py:40` — `press = write_site_artifact(`
- `seed.py:48` — `control = write_site_artifact(`
- `seed.py:55` — `eid = write_site_journal(`

### COLD_START (`cold_start.py`)
- `cold_start.py:40` — `src = read_site_source(memory)`
- `cold_start.py:46` — `before_press = read_site_artifact(memory, NAME_PRESS)`
- `cold_start.py:47` — `before_control = read_site_artifact(memory, NAME_CONTROL)`
- `cold_start.py:59` — `arch = write_site_archive_source(`
- `cold_start.py:64` — `corrected = write_site_source(memory, day=new_day, version=new_version)`
- `cold_start.py:69` — `press = write_site_artifact(`
- `cold_start.py:84` — `write_site_journal(`

## Config

- DB path: `config.py` → `DB_PATH` = `/workspace/retract/g1/memory.db`
- Tenant: `config.py` → `TENANT_ID` dedicated G1 UUID

## Trace

- Unedited run capture: `TRACE.txt` (produced by `run_g1.py`)

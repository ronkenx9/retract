# RETRACT G2 — typed source versions + selective invalidation

**Product:** RETRACT (Sibyl Labs Hackathon, team `scar`)  
**Package:** `sibyl-memory-client==0.8.0`  
**DB:** `g2/memory.db` · tenant from `config.TENANT_ID`

## What this proves

1. Typed **source versions** live in Sibyl (`source_version_id`, `day`, `status`, `supersedes`).
2. **Claims** link artifacts → source version ids; **corrections** record approved | disputed.
3. Fresh process (cold start) reads Sibyl only, archives superseded source, writes v2, regenerates **only** dependents via `artifacts_invalidated_by`.
4. **Control** artifact (`company-blurb`) hash unchanged; **press-brief** hash changes Friday → Monday.
5. **Dispute** path: source/claim/correction → `not_established`; press text regenerated; control unchanged.
6. Before/after graphs are **views from Sibyl reads only** (not a parallel DB).

## Run

```bash
cd /workspace/retract/g2
./run_proof.sh
```

Uses `/workspace/retract/.venv/bin/python`. Trace → `artifacts/g2_unedited_trace.txt`.

## Call sites (judge &lt; 2 min)

| Intent | Site | File:line |
|---|---|---|
| Open DB / tenant | `open_memory` → `MemoryClient.local` | `memory_io.py:32` |
| WRITE source version | `write_site_source_version` → `set_entity` | `memory_io.py:53` / `:79` |
| WRITE archive source | `write_site_archive_source` → `archive_entity` | `memory_io.py:82` / `:84` |
| WRITE artifact | `write_site_artifact` → `set_entity` | `memory_io.py:87` / `:107` |
| WRITE claim | `write_site_claim` → `set_entity` | `memory_io.py:110` / `:127` |
| WRITE correction | `write_site_correction` → `set_entity` | `memory_io.py:130` / `:148` |
| WRITE journal | `write_site_journal` → `write_event` | `memory_io.py:151` / `:159` |
| READ live source | `read_site_source` → `get_entity` | `memory_io.py:166` / `:168` |
| READ artifact | `read_site_artifact` → `get_entity` | `memory_io.py:171` / `:173` |
| READ list artifacts | `read_site_list_artifacts` → `list_entities` | `memory_io.py:186` / `:188` |
| READ list claims | `read_site_list_claims` → `list_entities` | `memory_io.py:196` / `:198` |
| READ list corrections | `read_site_list_corrections` → `list_entities` | `memory_io.py:201` / `:203` |
| READ archived trail | `read_site_archived_sources` (archive tier) | `memory_io.py:211` |
| Graph from Sibyl | `build_graph` / `write_graph` | `graph.py:25` / `:122` |
| SEED process | `seed.py` | process 1, exits |
| CORRECT process | `correct.py` | process 2, fresh PID |
| DISPUTE process | `dispute.py` | process 2, cheap path |

## Layout

| Path | Role |
|---|---|
| `config.py` | DB path, tenant, category/name constants |
| `memory_io.py` | `write_site_*` / `read_site_*` Sibyl call sites |
| `graph.py` | Dependency graph projection (Sibyl reads only) |
| `seed.py` | Source v1 Friday + claim + press + control |
| `correct.py` | Archive → Monday v2 → approved correction → selective regen |
| `dispute.py` | Archive → not_established → disputed correction → regen |
| `run_proof.sh` | Path A (correct) + Path B (dispute), unedited tee |
| `artifacts/before_graph.json` | Graph after seed (correct path) |
| `artifacts/after_graph.json` | Graph after approved correction |
| `artifacts/g2_result.json` | Hash / PASS machine result |
| `artifacts/g2_unedited_trace.txt` | Full terminal capture |

## Fictional corpus

NovaDesk launch copy is fictional and owned by the demo. No public outreach / real-person claims.

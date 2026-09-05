# Implementation note

## Architecture

```
┌─────────────┐     write_site_* / read_site_*      ┌──────────────────────┐
│ seed/correct│ ───────────────────────────────────► │ Sibyl Memory (SQLite) │
│ workers     │ ◄─────────────────────────────────── │ memory.db per gate    │
└─────────────┘              get_entity              └──────────────────────┘
       │                                                      ▲
       │ materialize projections (views only)                 │
       ▼                                                      │
 artifacts/projections/*.txt                    G3 desk / G4 / G5 bridges
```

**Source of truth:** Sibyl entities only. Projections and graphs are derived reads.

## Call sites (judge < 2 minutes)

| Intent | Primary file | Functions |
|---|---|---|
| Write source version | `g2/memory_io.py` | `write_site_source_version` → `set_entity` |
| Archive superseded | `g2/memory_io.py` | `write_site_archive_source` → `archive_entity` |
| Write claim / artifact / correction | `g2/memory_io.py` | `write_site_claim`, `write_site_artifact`, `write_site_correction` |
| Read for cold start | `g2/memory_io.py` | `read_site_source`, `read_site_artifact`, `read_site_list_*` |
| Invalidate dependents | `g2/memory_io.py` | `artifacts_invalidated_by` |
| Graph from Sibyl | `g2/graph.py` | `build_graph` |
| G1 minimal proof | `g1/memory_io.py` | same pattern, smaller surface |
| G3 desk | `g3/ops.py` + `g3/g2_bridge.py` | patches DB path; FastAPI `/api/correct`, `/api/dispute` |
| G4 suite | `g4/run_adversarial.py` | six cases over dedicated DBs/tenants |
| G5 cold-start | `g5/seed_worker.py`, `g5/correct_worker.py` | separate processes, shared `g5/memory.db` |

## Correction flow (approved)

1. Cold process opens Sibyl (`MemoryClient.local`).
2. `read_site_source` → live Friday + `source_version_id`.
3. `archive_entity` old launch-note.
4. `set_entity` new version (Monday) with `supersedes`.
5. Write approved correction + refresh claim.
6. Regenerate only artifacts whose `depends_on_source_version_id` matched the old id.
7. Control (`company-blurb`, no dependency) untouched → same SHA-256.

## Dispute flow

Archives live source; writes not-established source + disputed correction; regenerates press to locked dispute hash `8fa56152…`.

## Pin

```
sibyl-memory-client==0.8.0
```

See `rules-lock.md` for contest rules and API surface.

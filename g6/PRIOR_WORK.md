# Prior Work

## What already existed

**[Sibyl Memory](https://github.com/Sibyl-Labs/Sibyl-Memory)** — local-first hierarchical memory SDK for agents (`sibyl-memory-client`).

RETRACT pins **`sibyl-memory-client==0.8.0`** (G0). Capabilities we rely on:

- `MemoryClient.local(path, tenant_id=…)` — SQLite-backed, multi-tenant
- `set_entity` / `get_entity` / `list_entities`
- `archive_entity` (history-preserving supersession)
- journal / events for audit trail
- UNIQUE `(tenant_id, category, name)`

We did **not** invent a new memory database. We did not add a parallel JSON “source of truth.”

## What RETRACT adds

| Layer | Contribution |
|---|---|
| Product contract | Correct one source → after cold start, dependents rebuild; control stays byte-identical |
| Typed domain | Launch-note versions, claims linking artifacts→`source_version_id`, approved vs disputed corrections |
| Selective invalidation | `artifacts_invalidated_by` + regenerate only dependents |
| Editorial desk (G3) | Local UI over the same Sibyl shapes (sources above, artifacts below) |
| Adversarial suite (G4) | Stale cache, repeats, conflicts, tenants, deletion litmus, concurrency |
| Live cold-start (G5) | Separate PIDs, empty process state, unedited continuous log + Sibyl read pointers |
| Packaging (G6) | Claims→evidence, Prior Work, MIT, fresh-clone notes |

## Non-claims

- No partner stack (Base / Virtuals) executed in G0–G5; no PMF bonus asserted.
- NovaDesk corpus is fictional demo copy.
- Demo video is local-only until Tega approves publish.

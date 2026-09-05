# Sibyl Memory docs brief (for RETRACT)
Pinned from docs.sibyllabs.org/memory + GitHub README + client README + PyPI. Date: 2026-09-05.

## Package pin
- `sibyl-memory-client` **0.8.0** on PyPI (Python >=3.10). Also cli / mcp / hermes / langgraph family.
- Install product path: `pip install 'sibyl-memory-cli[mcp]'` then `sibyl init` / `sibyl setup`
- RETRACT worker path: `pip install sibyl-memory-client` → `MemoryClient.local("~/.sibyl-memory/memory.db")`

## Architecture (load-bearing facts)
- Local-first SQLite under `~/.sibyl-memory/` (+ `memory.db`). No cloud read/write of content.
- FTS5 only. No vectors / embeddings.
- Multi-tenant isolation (tenant_id on records).
- UNIQUE `(tenant_id, category, name)` — one live entity per name. Rule 43: single source of truth per entity.
- Five tiers:
  - HOT `state` — `set_state` / `get_state` (rewritten in place)
  - WARM `entities` — `set_entity` / `get_entity` / `list_entities`
  - COLD `journal` — `write_event` / `read_events` (append-only)
  - REFERENCE — `set_reference` / `get_reference`
  - ARCHIVE — `archive_entity` (recoverable plaintext archive); `delete_entity` is hard delete

## MCP tools (agent surface)
| Purpose | MCP | SDK |
|---|---|---|
| Save entity | `memory_remember(category, name, body)` | `set_entity` |
| Recall | `memory_recall(category, name)` | `get_entity` |
| List | `memory_list(category, limit)` | `list_entities` |
| Search | `memory_search(query, …)` | `search` / `search_entities` |
| State set/get | `memory_set_state` / `memory_get_state` | `set_state` / `get_state` |
| Journal | `memory_record_event` | `write_event` |
| Forget/archive | `memory_forget` | `archive_entity` |

## Tiers & access
- Free: full five-tier model; local size cap **5,242,880 bytes** per tiers page (overview also says “2 MB” — treat tiers page + `sibyl status` as live).
- Staker / Subscription: remove cap, self-learning, memory linter.
- Privacy: content never leaves machine. Activated free may call `check-write` with account id + DB byte size only.

## Docs pages reached
- https://docs.sibyllabs.org/memory/ (overview) ✓
- /memory/install ✓
- /memory/integrations ✓
- /memory/tiers ✓
- /memory/cli ✓
- /memory/how-it-works — **404** at fetch time (API surface covered by client README instead)
- /memory/benchmarks — **404** at fetch time (numbers on overview / GitHub README)

## RETRACT implications
1. Do **not** store a parallel JSON fact DB as source of truth. All semantic state via Sibyl.
2. Versioning: cannot have two live entities with same (category, name). Put versions in body + journal events, or versioned names (`source:launch-note@v2`) with archive of superseded.
3. Historical record: prefer `archive_entity` + journal corrections over `delete_entity`.
4. Cold start: new process + empty chat; open same `memory.db` path; prove selective invalidation from Sibyl reads alone.
5. Deletion test: remove Sibyl calls → selective retract must fail.
6. Free 5 MB is enough for the fictional launch corpus MVP.
7. Pin exact package versions in G0 `rules-lock.md` after install (`pip show sibyl-memory-client`).

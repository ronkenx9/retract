# RETRACT — G0 rules lock

**Locked:** 2026-09-05 (WAT / UTC+1)  
**Product:** RETRACT (Sibyl Labs Hackathon)  
**Team name:** `scar` (organizer registration confirmed 2026-08-20 per brain/projects/SIBYL.md)  
**Private submission URL:** exists; **never store or paste the bearer token** in repo, docs, chat logs, or memory.

This file is the G0 acceptance artifact. It pins contest rules, license, build window, and the exact Sibyl Memory package/API surface used for implementation. Re-check official pages if they change before submit.

---

## 1. Contest clock (UTC)

| Window | Dates |
|---|---|
| Registration | 2026-08-16 → 2026-08-31 23:59 (closed; team scar already registered) |
| Build / submit | 2026-09-01 → **2026-09-10 23:59** |
| Workshops (Base + Virtuals) | 2026-09-05 → 2026-09-07 |
| Judging | 2026-09-11 → 2026-09-12 |
| Winners | 2026-09-13 → 2026-09-15 |

Internal planning cutoff from OPPORTUNITIES.md: submit-ready **Sep 9 evening WAT**.

Sources: https://hack.sibyllabs.org/rules · brain/projects/SIBYL.md · hackathon-ideation-tank OPPORTUNITIES.md

---

## 2. Gate (pass/fail) — non-negotiable

Sibyl Memory must be **load-bearing**.

Litmus: delete the Sibyl Memory layer. If RETRACT still performs selective invalidation / cold-start retract, the entry fails.

Required demo beat: persist → **genuinely fresh session** (empty chat, new process) → decision/result changes. One continuous unedited segment with on-screen timestamp or commit hash.

README must point to write + read call sites so a judge finds them in under two minutes.

---

## 3. Scoring (after gate)

Final = (rubric + PMF bonus) × partner multiplier.

| Criterion | Max |
|---|---|
| Memory load-bearing | 40 |
| Innovation & originality | 25 |
| Technical execution | 20 |
| Pitch & presentation | 15 |
| PMF bonus (evidenced only) | +10 |

Partner multiplier: 0 → ×1.00, 1 → ×1.15, 2 → ×1.25. Sibyl is never a stack. Base needs an **executed onchain action** in the demo (wallet / x402 / B20 / contract), not deploy-only. Virtuals needs ACP/agent path exercised live.

**RETRACT budget for G0–G5:** no partner multiplier and no PMF points assumed until independently evidenced (product contract).

---

## 4. Submit artifacts

- Public GitHub repo, **MIT or Apache-2.0**, real commit history
- 2–5 min demo with cold-start recall beat
- README: what it does, where memory is load-bearing, partner stacks (if any), “how memory made this possible”, Prior Work
- Two public X posts tagging **@sibylcap** (+ any claimed partners): demo + build-log
- Memory implementation note on the private build page
- Mark ready before Sep 10 23:59 UTC

---

## 5. Product license intent

Ship RETRACT under **MIT** (matches Sibyl Memory packages). Confirm LICENSE file on first public commit.

---

## 6. Pinned Sibyl Memory packages (2026-09-05 PyPI)

| Package | Pinned version | Role in RETRACT |
|---|---|---|
| `sibyl-memory-client` | **0.8.0** | Sole semantic store for the Python worker |
| `sibyl-memory-cli` | **0.4.0** | Init / status / health (optional for agents) |
| `sibyl-memory-mcp` | **0.2.0** | Optional MCP front door; same engine |

Install for worker:

```bash
pip install 'sibyl-memory-client==0.8.0'
```

Verified locally in `/workspace/retract/.venv` on 2026-09-05: `pip show` reports Name=sibyl-memory-client Version=0.8.0. Requires-Python: >=3.10. License: MIT.

Docs: https://docs.sibyllabs.org/memory/ · Source: https://github.com/Sibyl-Labs/Sibyl-Memory

**Note:** Package family versions are deliberately skewed across PyPI (client 0.8.0 vs cli 0.4.0 vs mcp 0.2.0). Pin all three explicitly. Do not float `latest` in CI.

---

## 7. Pinned API surface (client 0.8.0)

Constructor:

```python
from sibyl_memory_client import MemoryClient
memory = MemoryClient.local(
    "~/.sibyl-memory/memory.db",  # or project-scoped path for demos
    tenant_id="<workspace-uuid>",
)
```

`MemoryClient.local(path='~/.sibyl-memory/memory.db', *, tenant_id=DEFAULT, tier='free', ...)`

Core methods used by RETRACT:

| Intent | Method |
|---|---|
| Write / upsert entity | `set_entity(category, name, body, status=...)` |
| Read entity | `get_entity(category, name)` |
| List | `list_entities(category=..., limit=...)` |
| Archive (keep history) | `archive_entity(category, name, reason=...)` |
| Hard delete (avoid in MVP) | `delete_entity(category, name)` |
| HOT state | `set_state(key, body)` / `get_state(key)` |
| Journal | `write_event(...)` / `read_events(...)` |
| Reference docs | `set_reference(...)` / `get_reference(...)` |
| Search | `search(...)` / `search_entities(...)` |
| Tenant | `get_tenant()` / `set_tenant(tenant_id)` |
| Schema | `schema_version()` → expect DB schema version **≥ 2** (`EXPECTED_SCHEMA_VERSION = 2` in package lint) |

Schema facts from installed `schema.sql`:

- SQLite + FTS5, WAL, foreign keys on
- `UNIQUE (tenant_id, category, name)` on entities (Rule 43)
- Body is JSON TEXT with `json_valid` check
- Five tiers: entities, state_documents, journal_events, reference_documents, archived_entities

MCP equivalents (if used): `memory_remember`, `memory_recall`, `memory_list`, `memory_search`, `memory_set_state`, `memory_get_state`, `memory_record_event`, `memory_forget`.

---

## 8. RETRACT architecture constraints (from product contract + docs)

1. **No duplicate persistent fact store.** UI may cache projections; all semantic state must reconstruct from Sibyl.
2. **Versioning:** cannot keep two live rows for the same `(tenant, category, name)`. Put version fields in body + journal, or use versioned names and archive superseded entities.
3. Prefer **archive** over hard delete so the historical record survives.
4. **Cold start:** new worker process, empty conversation, same DB path; selective invalidation from Sibyl reads alone.
5. **Deletion test:** remove Sibyl calls → selective retract must fail or materially degrade.
6. Fictional owned launch corpus only. No public misinformation / automatic outreach / real-person allegations.
7. Distinguishing behavior is selective invalidation after cold start with an **unaffected control artifact**. “I remember Monday” alone is SCAR-costume and a kill condition.

---

## 9. G0 checklist

| Item | Status |
|---|---|
| Team `scar` registration confirmed (brain, Aug 20) | YES |
| Bearer submission token not recorded here | YES |
| Rules / gate / rubric pinned | YES |
| Build deadline pinned (Sep 10 23:59 UTC) | YES |
| License intent MIT | YES |
| `sibyl-memory-client==0.8.0` installed and inspected | YES |
| CLI / MCP versions pinned | YES |
| API / schema uniqueness constraints recorded | YES |
| Official “How it works” docs page | 404 at lock time; API taken from installed package + client README |

---

## 10. Next gate

**G1 — hardest proof:** write a source + dependency through Sibyl, kill the process, restart with empty chat history, read and change one generated artifact. Produce an unedited terminal/video trace and source pointers for write/read.

Owner action still required later: keep the private build link available for submission; never paste the token into the repo.

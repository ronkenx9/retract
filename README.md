# RETRACT

**Selective invalidation after a cold start — powered by Sibyl Memory.**

Correct one source. Kill the process. Start fresh with empty history. Dependent briefings withdraw and rebuild from Sibyl alone. An unaffected control artifact stays **byte-identical**.

Hackathon entry for [Sibyl Labs](https://hack.sibyllabs.org/) (team `scar`). Build window closes **2026-09-10 23:59 UTC**.

## The claim (one sentence)

Sibyl Memory (`sibyl-memory-client==0.8.0`) is the **sole semantic store**: after a genuine cold start, RETRACT reads truth only from Sibyl, regenerates dependents of a corrected source, and leaves unrelated artifacts untouched.

## Locked corpus hashes (SHA-256)

| Artifact | Status | SHA-256 |
|---|---|---|
| `company-blurb` (control) | always unchanged | `8846d618d6c377adbf6dd53a6939d4be01d5b67b5c4d6ff65fb12e5ab94453f7` |
| `press-brief` | Friday (seed) | `746e9d25a3756bd775702b5e2976cb2a1ab70c4a432a4e9f4b6824a8761e9096` |
| `press-brief` | Monday (approved) | `37437dcd61110f51274bfe64b727d9c448b8e2b2329efacd4b7f9b473aab0e03` |
| `press-brief` | not established (dispute) | `8fa56152e8f681171fb82e8cd186bbd23e9b98850a703af4687df4023624cb67` |

## Proof ladder (G0–G5)

| Gate | Path | Result |
|---|---|---|
| G0 rules lock | [`rules-lock.md`](rules-lock.md) | pinned client **0.8.0**, MIT intent, submit checklist |
| G1 cold-start | [`g1/`](g1/) | seed → kill → correct; selective invalidation |
| G2 versions / claims / graphs | [`g2/`](g2/) | typed sources, corrections, dispute, hash-locked graphs |
| G3 editorial desk | [`g3/`](g3/) | local FastAPI desk on `127.0.0.1:8765` |
| G4 adversarial suite | [`g4/`](g4/) | 6 cases PASS (stale cache, repeat, conflict, tenants, deletion litmus, concurrent) |
| G5 live cold-start | [`g5/`](g5/) | `G5_PROOF=PASS` · run `b21262b5-d165-4b84-8889-72b72d6c6e53` · pids **172905→172906** |

Submission packaging (Prior Work, claims→evidence, fresh-clone notes, inventory): [`g6/`](g6/).

## Demo (local only)

Continuous cold-start cut (do **not** publish without Tega’s yes):

- Video: `g5/retract-g5-cold-start-demo.mp4` (60s, 1920×1080)
- Shot list: `g5/SHOT_LIST.md`
- Unedited trace: `g5/artifacts/g5_unedited_trace.txt`

## Quick start

```bash
cd /workspace/retract   # or your clone root
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# G1 hardest proof
(cd g1 && ../.venv/bin/python run_g1.py)

# G2 hash-locked graphs
(cd g2 && ./run_proof.sh)

# G3 desk (local)
(cd g3 && ./run.sh)   # http://127.0.0.1:8765

# G4 adversarial
(cd g4 && ./run.sh)

# G5 live cold-start
(cd g5 && ./run_cold_start.sh)
```

See [`g6/FRESH_CLONE.md`](g6/FRESH_CLONE.md) for a judge-oriented fresh-machine walkthrough.

## Where memory is load-bearing

Judge-facing call sites live in `g1/memory_io.py` and `g2/memory_io.py` (`write_site_*` / `read_site_*`). G3–G5 import those sites via bridges; they do **not** keep a parallel JSON fact store. Prefer `archive_entity` over hard delete. UNIQUE `(tenant_id, category, name)` drives versioning by archive + new body.

Deletion litmus (G4): remove Sibyl access → correction cannot proceed. That is the gate.

## License

[MIT](LICENSE) — Copyright (c) 2026 RETRACT contributors.

Sibyl Memory packages are also MIT; pin `sibyl-memory-client==0.8.0` (see G0).

## Privacy / tokens

Private submission URL may exist for the contest. **Never store or paste the bearer token** in this repo, docs, chat, or memory.

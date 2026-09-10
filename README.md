# RETRACT

**Selective invalidation after a cold start — powered by Sibyl Memory.**

Correct one source. Kill the process. Start fresh with empty history. Dependent briefings withdraw and rebuild from Sibyl alone. An unaffected control artifact stays **byte-identical**.

Hackathon entry for [Sibyl Labs](https://hack.sibyllabs.org/) (team `scar`).

**Public repo:** https://github.com/ronkenx9/retract
**Live demo:** https://retract-scar.vercel.app
Build window closes **2026-09-10 23:59 UTC**.

## Why this matters

Agents and teams rarely fail because they *can't* produce work. They fail because **old work keeps getting served after the fact behind it changed.** Someone corrects a launch date, a price, a policy, a spec — but the press brief that cited it, the cached summary, the downstream doc, the next agent in the chain all still repeat the old version. Nobody re-derived anything; they just trusted a stale copy.

RETRACT makes the stale work **withdraw itself.** Correct the source once, and every artifact that depended on it rebuilds from memory — while everything that didn't depend on it is left byte-for-byte untouched. The correction propagates; nothing else moves.

Where this shows up:

- **Editorial / PR** — an embargo date slips from Friday to Monday. Every brief that cited Friday must change; the boilerplate company blurb must not.
- **Multi-agent handoffs** — agent A's finding is retracted. The next agent hired should inherit the retraction, not re-run on a discredited fact.
- **Compliance / knowledge bases** — a policy is superseded. Documents that quote it withdraw; unrelated records stay provably intact.

The hard part isn't regenerating everything — that's easy and wasteful. It's regenerating **exactly** what changed and proving you didn't touch anything else. And it only works if a *fresh* session, with no in-memory history, can still tell what depended on what — which is why memory has to be load-bearing, not a cache. That proof is what the rest of this repo is.

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

## Demo

Narrated 2:04 walkthrough of every beat — desk (Friday) → correction preview → apply (press rebuilds to Monday, control byte-identical) → dispute (not-established) → G5 cold-start `PASS` → G4 deletion litmus. The desk beats are driven on the live app; hashes on screen match the locked table above. Demo video URL is on the [submission page]; the live desk is at https://retract-scar.vercel.app.

Reproduce the underlying cold-start locally:

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


## Desk stills (G3)

Locked-hash screenshots for the editorial desk (local demo):

| Beat | File |
|---|---|
| Before (Friday) | [`g3/artifacts/screenshots/01-desk-before.png`](g3/artifacts/screenshots/01-desk-before.png) |
| Correct preview | [`g3/artifacts/screenshots/02-correct-preview.png`](g3/artifacts/screenshots/02-correct-preview.png) |
| After approved (Monday) | [`g3/artifacts/screenshots/03-after-approved.png`](g3/artifacts/screenshots/03-after-approved.png) |
| After dispute | [`g3/artifacts/screenshots/04-after-dispute.png`](g3/artifacts/screenshots/04-after-dispute.png) |

## License

[MIT](LICENSE) — Copyright (c) 2026 RETRACT contributors.

Sibyl Memory packages are also MIT; pin `sibyl-memory-client==0.8.0` (see G0).

## Privacy / tokens

Private submission URL may exist for the contest. **Never store or paste the bearer token** in this repo, docs, chat, or memory.

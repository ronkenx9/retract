# Claims → evidence

| # | Claim | Evidence | Locked hash / marker |
|---|---|---|---|
| C1 | Sibyl is sole semantic store | `g1/memory_io.py`, `g2/memory_io.py`; no parallel fact JSON | G0 `rules-lock.md` |
| C2 | Cold start: new process reads Sibyl and corrects | `g1/TRACE.txt` / `g1/run_g1.py`; `g5/artifacts/g5_unedited_trace.txt` | `G5_PROOF=PASS` |
| C3 | Dependent press rebuilds Friday→Monday | G2 after graph; G5 result | press `37437dcd61110f51274bfe64b727d9c448b8e2b2329efacd4b7f9b473aab0e03` |
| C4 | Control stays byte-identical | G2/G3/G5 control hash | `8846d618d6c377adbf6dd53a6939d4be01d5b67b5c4d6ff65fb12e5ab94453f7` |
| C5 | Dispute regenerates to not-established | `g2/dispute.py`; G3 `/api/dispute` | press `8fa56152e8f681171fb82e8cd186bbd23e9b98850a703af4687df4023624cb67` |
| C6 | Typed versions + claims + graphs | `g2/` graphs in `artifacts/` | before/after machine-readable graphs |
| C7 | Editorial desk shows selective invalidation | `g3/` screenshots + `verify_hashes.py` | `G3_PROOF=PASS` |
| C8 | Adversarial robustness | `g4/artifacts/g4_results.json` | all 6 cases PASS |
| C9 | Deletion litmus (Sibyl load-bearing) | G4 Sibyl-deletion case; `g1/deletion_smoke.py` | must FAIL without Sibyl |
| C10 | Live continuous segment | `g5/artifacts/g5_unedited_trace.txt`; demo `g5/retract-g5-cold-start-demo.mp4` | run `b21262b5…` · pids 172905→172906 |
| C11 | Sibyl read pointers for judges | `g5/artifacts/g5_sibyl_pointers.json` | entity ids + call sites |
| C12 | Pinned package | `requirements.txt`, G0 | `sibyl-memory-client==0.8.0` |

Canonical G5 run on disk: `b21262b5-d165-4b84-8889-72b72d6c6e53`.

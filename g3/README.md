# RETRACT G3 — Editorial desk (local)

**Local only. Do not publish. Do not touch Muse Mirror.**

Desk UI over G2 Sibyl ops: correct the launch-day source, watch `press-brief` withdraw, watch `company-blurb` stay byte-identical.

## Run

```bash
cd /workspace/retract/g3
./run.sh
# → http://127.0.0.1:8765
```

Uses `/workspace/retract/.venv` (`sibyl-memory-client==0.8.0`, FastAPI, uvicorn).  
Dedicated DB: `g3/memory.db` (G2 `DB_PATH` patched at G3 startup only — G2 proofs untouched).

## Screens

1. **Desk** — sources above, press-brief + company-blurb below  
2. **Correct preview** — old/new source, Apply correction + Dispute instead  
3. **After** — proof screen; PASS/FAIL banner if locked hashes mismatch  

## API

| Method | Path | Role |
|---|---|---|
| GET | `/api/graph` | Sibyl graph + hash check |
| POST | `/api/seed` | Wipe + Friday baseline |
| POST | `/api/correct` | `{day, reason}` approved path |
| POST | `/api/dispute` | `{reason}` not_established path |

## Locked hashes (FAIL if mismatch)

| Artifact | State | sha256 |
|---|---|---|
| `company-blurb` (control) | always | `8846d618d6c377adbf6dd53a6939d4be01d5b67b5c4d6ff65fb12e5ab94453f7` |
| `press-brief` | Friday before | `746e9d25a3756bd775702b5e2976cb2a1ab70c4a432a4e9f4b6824a8761e9096` |
| `press-brief` | Monday approved | `37437dcd61110f51274bfe64b727d9c448b8e2b2329efacd4b7f9b473aab0e03` |
| `press-brief` | dispute not_established | `8fa56152e8f681171fb82e8cd186bbd23e9b98850a703af4687df4023624cb67` |

## Verify

```bash
cd /workspace/retract/g3
../.venv/bin/python verify_hashes.py | tee artifacts/g3_verify.txt
# expects G3_PROOF=PASS
```

## Layout

| Path | Role |
|---|---|
| `g2_bridge.py` | Patch G2 `DB_PATH` → `g3/memory.db`, import memory_io/graph |
| `ops.py` | seed / correct / dispute via G2 write sites |
| `hashes.py` | Locked hashes + check helpers |
| `app.py` | FastAPI + StaticFiles |
| `static/` | `index.html` `app.js` `styles.css` |
| `verify_hashes.py` | Automated hash proof |
| `run.sh` | uvicorn 127.0.0.1:8765 |
| `mock/` `screens.md` `fixtures.json` | UX reference (pre-wire) |

## Forbidden

Feature soup, regenerate-all, Muse Mirror language, publishing this desk.

## Screenshots

Live UI captures under `artifacts/screenshots/`:

- `01-desk.png`
- `02-correct-preview.png`
- `03-after-approved.png`
- `04-after-dispute.png`

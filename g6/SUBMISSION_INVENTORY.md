# Submission inventory

## Include (source + docs)

- [x] `LICENSE` (MIT)
- [x] `README.md` (public)
- [x] `requirements.txt` (`sibyl-memory-client==0.8.0`, fastapi, uvicorn, httpx)
- [x] `rules-lock.md` (G0)
- [x] `g1/` … `g5/` source + READMEs + proof artifacts (traces, graphs, results JSON)
- [x] `g6/` packaging docs
- [x] `g3/artifacts/screenshots/` (desk stills)
- [x] `g5/SHOT_LIST.md`
- [ ] Public GitHub remote (blocked until Tega says push)
- [ ] Two X posts (owned by X bot; hold publish)
- [ ] Private build-page memory note (paste from `IMPLEMENTATION.md`; no token in repo)

## Optional / large

- `g5/retract-g5-cold-start-demo.mp4` — include in release assets or Git LFS; cite path in README
- Root `*.tgz` proof bundles — optional convenience; regenerateable

## Exclude

- `.venv/`
- `__pycache__/`, `*.pyc`
- Contest **bearer token** / private submission secrets (never)
- Live production credentials
- Unrelated Muse Mirror / Capsule work

## Local DB files

`memory.db` (+ `-wal`/`-shm`) are regenerable demo state. Prefer shipping without large DBs and documenting `seed` / `run_*.sh`. If included, they contain only fictional NovaDesk copy.

## Ready vs blocked

| Item | Status |
|---|---|
| Local package docs (this folder + root README/LICENSE) | **READY** |
| G0–G5 proofs on disk | **READY** (PASS locked) |
| Demo cut path | **READY** (local; hold publish) |
| Public git push | **BLOCKED** — needs Tega’s yes |
| X posts live | **BLOCKED** — X bot drafts; needs Tega’s yes |
| Bearer token in repo | **NEVER** |

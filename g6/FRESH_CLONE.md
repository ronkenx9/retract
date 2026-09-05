# Fresh-clone run notes

Assumes a clean Linux/macOS machine with Python ≥ 3.10. No bearer tokens required for local proofs.

## 1. Setup

```bash
git clone <PUBLIC_REPO_URL> retract   # when published
cd retract
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -c "import sibyl_memory_client as s; print(s.__version__)"  # expect 0.8.0
```

## 2. Proofs (order)

```bash
# G1
(cd g1 && ../.venv/bin/python run_g1.py)

# G2
(cd g2 && bash ./run_proof.sh)

# G3 desk — local only
(cd g3 && bash ./run.sh)
# open http://127.0.0.1:8765
# verify: ../.venv/bin/python verify_hashes.py

# G4
(cd g4 && bash ./run.sh)

# G5 continuous cold-start
(cd g5 && bash ./run_cold_start.sh)
# expect G5_PROOF=PASS and fresh pids across seed/correct
```

## 3. What judges should look at

1. `g1/POINTERS.md` or `g2/memory_io.py` — write/read sites  
2. `g5/artifacts/g5_unedited_trace.txt` — continuous seed-kill-correct  
3. Hash chips / `CLAIMS_TO_EVIDENCE.md` — control unchanged, press Monday  
4. G4 deletion litmus — Sibyl removed ⇒ fail  

## 4. Notes

- Each gate uses its **own** `memory.db` under that folder (or g4 `memory_a.db` / `memory_b.db`).
- Delete `*.db` and re-run seed scripts to regenerate demo state.
- Demo MP4 is optional large media under `g5/`; proofs do not require playing it.
- Never paste contest bearer tokens into env files checked into git.

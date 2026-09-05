#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PY="${ROOT}/../.venv/bin/python"
mkdir -p "${ROOT}/artifacts/projections"
cd "${ROOT}"
"${PY}" run_adversarial.py 2>&1 | tee artifacts/g4_unedited_trace.txt

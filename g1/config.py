"""G1 RETRACT proof — project-scoped Sibyl Memory config."""
from pathlib import Path

G1_ROOT = Path(__file__).resolve().parent
DB_PATH = G1_ROOT / "memory.db"
TENANT_ID = "a1111111-b222-c333-d444-e55555555555"  # dedicated G1 tenant
PROJECTIONS_DIR = G1_ROOT / "artifacts" / "projections"

# Entity names (UNIQUE per tenant+category+name)
CAT_SOURCE = "source"
CAT_ARTIFACT = "artifact"
NAME_LAUNCH = "launch-note"
NAME_PRESS = "press-brief"       # dependent — must change on retract
NAME_CONTROL = "company-blurb"   # control — must stay unchanged

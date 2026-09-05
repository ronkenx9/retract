"""G2 RETRACT — typed source versions + dependency graph config."""
from pathlib import Path

G2_ROOT = Path(__file__).resolve().parent
DB_PATH = G2_ROOT / "memory.db"
# Dedicated G2 tenant (do not share with G1)
TENANT_ID = "c2222222-b222-c333-d444-e55555555555"
PROJECTIONS_DIR = G2_ROOT / "artifacts" / "projections"
ARTIFACTS_DIR = G2_ROOT / "artifacts"

CAT_SOURCE = "source_version"
CAT_ARTIFACT = "artifact"
CAT_CLAIM = "claim"
CAT_CORRECTION = "correction"

NAME_LAUNCH = "novadesk-launch"  # live row; archived on supersede
NAME_PRESS = "press-brief"
NAME_CONTROL = "company-blurb"
NAME_CLAIM_PRESS = "press-brief-cites-launch"
NAME_CORRECTION_APPROVED = "friday-to-monday-approved"
NAME_CORRECTION_DISPUTE = "friday-to-monday-disputed"

STATUS_ACTIVE = "active"
STATUS_SUPERSEDED = "superseded"
STATUS_DISPUTED = "disputed"
STATUS_NOT_ESTABLISHED = "not_established"
STATUS_APPROVED = "approved"

"""Locked NovaDesk corpus hashes (from G2/G3)."""
from __future__ import annotations

CONTROL_ALWAYS = "8846d618d6c377adbf6dd53a6939d4be01d5b67b5c4d6ff65fb12e5ab94453f7"
PRESS_FRIDAY = "746e9d25a3756bd775702b5e2976cb2a1ab70c4a432a4e9f4b6824a8761e9096"
PRESS_MONDAY = "37437dcd61110f51274bfe64b727d9c448b8e2b2329efacd4b7f9b473aab0e03"
PRESS_DISPUTE = "8fa56152e8f681171fb82e8cd186bbd23e9b98850a703af4687df4023624cb67"

LOCKED = {
    "control_always": CONTROL_ALWAYS,
    "press_friday": PRESS_FRIDAY,
    "press_monday": PRESS_MONDAY,
    "press_dispute_not_established": PRESS_DISPUTE,
}

DAY_TO_PRESS = {
    "Friday": PRESS_FRIDAY,
    "Monday": PRESS_MONDAY,
}

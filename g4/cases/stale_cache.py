"""Case 1 — Stale UI/projection cache vs Sibyl truth."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from bridge import NAME_PRESS, PROJECTIONS_DIR, graph, memory_io
from hashes import PRESS_FRIDAY, PRESS_MONDAY
from ops import correct_to, seed


def run() -> dict[str, Any]:
    seed(force=True, day="Friday")
    press_path = PROJECTIONS_DIR / f"{NAME_PRESS}.txt"
    friday_text = press_path.read_text(encoding="utf-8")
    cache_path = PROJECTIONS_DIR / "ui_cache_press-brief.txt"
    # Explicit stale UI cache snapshot (simulates projection left behind)
    cache_path.write_text(friday_text, encoding="utf-8")

    out = correct_to("Monday", reason="Calendar confirmed Monday.", expect_from="Friday")
    # Deliberately leave cache stale — do NOT refresh ui_cache after correction
    # (ops.correct_to refreshes the real projection; we re-stale a parallel cache)
    cache_path.write_text(friday_text, encoding="utf-8")

    # Product truth = Sibyl graph / read sites
    g = graph.build_graph("stale_check")
    live = memory_io.read_site_source(memory_io.open_memory())
    sibyl_day = live["body"].get("day")
    press_ent = memory_io.read_site_artifact(memory_io.open_memory(), NAME_PRESS)
    sibyl_press = press_ent["body"].get("text") or ""
    sibyl_hash = press_ent["body"].get("content_sha256")

    cache_text = cache_path.read_text(encoding="utf-8")
    cache_has_friday = "Friday" in cache_text and "launches to the public on Friday" in cache_text
    cache_has_monday = "Monday" in cache_text and "launches to the public on Monday" in cache_text
    naive_cache_day = "Friday" if cache_has_friday and not cache_has_monday else (
        "Monday" if cache_has_monday else "unknown"
    )

    # Detect staleness: cache day ≠ Sibyl day / hash
    stale_detected = (
        sibyl_day == "Monday"
        and naive_cache_day == "Friday"
        and sibyl_hash == PRESS_MONDAY
        and memory_io.content_sha256(cache_text) == PRESS_FRIDAY
    )
    product_truth_is_sibyl = sibyl_day == "Monday" and "Monday" in sibyl_press
    naive_would_be_wrong = naive_cache_day != sibyl_day

    passed = (
        product_truth_is_sibyl
        and naive_would_be_wrong
        and stale_detected
        and out.get("control_ok") is True
    )

    return {
        "case": "stale_ui_projection_cache",
        "pass": passed,
        "sibyl_day": sibyl_day,
        "sibyl_press_sha256": sibyl_hash,
        "cache_day": naive_cache_day,
        "cache_sha256": memory_io.content_sha256(cache_text),
        "graph_press_sha256": g.get("press_sha256"),
        "stale_detected": stale_detected,
        "product_truth_is_sibyl": product_truth_is_sibyl,
        "naive_cache_would_be_wrong": naive_would_be_wrong,
        "detail": (
            "After Monday correction, ui_cache still shows Friday; "
            "Sibyl read_site / graph show Monday. Product truth = Sibyl."
        ),
        "cache_path": str(cache_path),
    }

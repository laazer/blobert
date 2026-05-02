"""Opt-in debug logging for spot image → base image compositing (Blender runs).

Set environment variable ``BLOBERT_DEBUG_SPOTS=1`` to print diagnostic lines to stdout
(visible in the asset editor run log / terminal). No effect when unset.
"""

from __future__ import annotations

import os

_SPOTS_DEBUG_ENV = "BLOBERT_DEBUG_SPOTS"


def spots_composite_debug_enabled() -> bool:
    v = os.environ.get(_SPOTS_DEBUG_ENV, "")
    return v.strip().lower() in ("1", "true", "yes", "on")


def log_spots_composite(msg: str) -> None:
    if spots_composite_debug_enabled():
        print(f"[blobert:spots] {msg}", flush=True)

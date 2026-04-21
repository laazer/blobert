"""Shared validation helpers (stdlib + typing only; no domain rules)."""

from __future__ import annotations

import math
from typing import Any


def clamp01(value: Any, default: float = 0.5) -> float:
    """Clamp a value to ``[0.0, 1.0]``; non-numeric inputs use ``default``.

    ``float('nan')`` maps to ``1.0``; infinities map to ``0.0``/``1.0``.
    """
    try:
        x = float(value)
    except (TypeError, ValueError):
        x = default
    if math.isnan(x):
        return 1.0
    if math.isinf(x):
        return 1.0 if x > 0 else 0.0
    return max(0.0, min(1.0, x))

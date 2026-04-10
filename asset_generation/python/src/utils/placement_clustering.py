"""Angular clustering for multi-instance procedural placement (eyes, zone extras).

``clustering`` ∈ [0, 1]: 0 = use the full legacy sampling domain (spread); 1 = concentrate
samples near the domain center (tight pack). Ticket 16 will add explicit random vs uniform
mode; until then, ellipsoid extras use ``model.rng`` with this concentration factor.
"""

from __future__ import annotations

import math
from typing import Any, Protocol


class _RNG(Protocol):
    def random(self) -> float: ...


def clamp01(value: Any, default: float = 0.5) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError):
        x = default
    return max(0.0, min(1.0, x))


def clustered_ellipsoid_angles_bounded(
    rng: _RNG,
    clustering: float,
    *,
    theta_lo: float,
    theta_hi: float,
    phi_lo: float,
    phi_hi: float,
) -> tuple[float, float]:
    """Sample ``(theta, phi)`` inside ``[theta_lo, theta_hi] × [phi_lo, phi_hi]``.

    At ``clustering == 0`` the pair is uniform in that rectangle (modulo wrap/clamp).
    At ``clustering == 1`` samples hug the rectangle center.
    """
    c = clamp01(clustering, 0.5)
    focus_theta = (theta_lo + theta_hi) * 0.5
    focus_phi = (phi_lo + phi_hi) * 0.5
    half_theta = (theta_hi - theta_lo) * 0.5 * (1.0 - c * 0.92) + 1e-9
    half_phi = (phi_hi - phi_lo) * 0.5 * (1.0 - c * 0.92) + 1e-9
    u1, u2 = rng.random(), rng.random()
    theta = focus_theta + (u1 - 0.5) * 2.0 * half_theta
    phi = focus_phi + (u2 - 0.5) * 2.0 * half_phi
    theta = theta % (2.0 * math.pi)
    span_p = phi_hi - phi_lo
    if span_p <= 2e-8:
        phi = focus_phi
    else:
        phi = max(phi_lo + 1e-6, min(phi_hi - 1e-6, phi))
    return theta, phi

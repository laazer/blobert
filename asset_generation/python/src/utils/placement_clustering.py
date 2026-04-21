"""Angular clustering for multi-instance procedural placement (eyes, zone extras).

``clustering`` ∈ [0, 1]: 0 = use the full legacy sampling domain (spread); 1 = concentrate
samples near the domain center (tight pack). Ticket 16 will add explicit random vs uniform
mode; until then, ellipsoid extras use ``model.rng`` with this concentration factor.
"""

from __future__ import annotations

import math
import random
from typing import Any, Protocol

from .validation import clamp01


class _RNG(Protocol):
    def random(self) -> float: ...


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


def uniform_arc_angles(
    index: int,
    count: int,
    *,
    theta_lo: float,
    theta_hi: float,
    phi_lo: float,
    phi_hi: float,
    clustering: float,
) -> tuple[float, float]:
    """Deterministic ``(theta, phi)`` for instance ``index`` of ``count`` (arc preset).

    Evenly spaces ``theta`` along ``[theta_lo, theta_hi]``; ``phi`` sits at band center,
    narrowed toward mid-band as ``clustering`` approaches 1.
    """
    c = clamp01(clustering, 0.5)
    n = max(1, count)
    span_t = theta_hi - theta_lo
    theta_mid = (theta_lo + theta_hi) * 0.5
    t_raw = theta_lo + (index + 0.5) / n * span_t
    half_t = span_t * 0.5 * (1.0 - c * 0.92) + 1e-9
    theta = theta_mid + (t_raw - theta_mid) * (half_t / max(1e-9, span_t * 0.5))
    theta = theta % (2.0 * math.pi)

    phi_mid = (phi_lo + phi_hi) * 0.5
    phi = max(phi_lo + 1e-6, min(phi_hi - 1e-6, phi_mid))
    return theta, phi


def uniform_ring_angles(
    index: int,
    count: int,
    *,
    theta_lo: float,
    theta_hi: float,
    phi_a: float,
    phi_b: float,
    clustering: float,
) -> tuple[float, float]:
    """Alternating latitudes ``phi_a`` / ``phi_b`` with even ``theta`` spacing."""
    c = clamp01(clustering, 0.5)
    n = max(1, count)
    span_t = theta_hi - theta_lo
    theta_mid = (theta_lo + theta_hi) * 0.5
    t_raw = theta_lo + (index + 0.5) / n * span_t
    half_t = span_t * 0.5 * (1.0 - c * 0.92) + 1e-9
    theta = theta_mid + (t_raw - theta_mid) * (half_t / max(1e-9, span_t * 0.5))
    theta = theta % (2.0 * math.pi)
    phi_pick = phi_a if index % 2 == 0 else phi_b
    mid_p = (phi_a + phi_b) * 0.5
    phi = mid_p + (phi_pick - mid_p) * (1.0 - c * 0.88)
    lo, hi = min(phi_a, phi_b), max(phi_a, phi_b)
    phi = max(lo + 1e-6, min(hi - 1e-6, phi))
    return theta, phi


def placement_prng(model: Any) -> random.Random:
    """Deterministic RNG stream from ``build_options['placement_seed']`` (random distribution path)."""
    try:
        seed = int(model.build_options.get("placement_seed", 0))
    except (TypeError, ValueError):
        seed = 0
    return random.Random(seed % (2**31))

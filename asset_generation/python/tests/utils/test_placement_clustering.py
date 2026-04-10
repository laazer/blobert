"""Tests for placement clustering helpers (ticket 15)."""

from __future__ import annotations

import math
import random
import statistics

from src.utils.placement_clustering import clamp01, clustered_ellipsoid_angles_bounded


def test_clamp01_defaults_and_bounds() -> None:
    assert clamp01(0.3) == 0.3
    assert clamp01(-1) == 0.0
    assert clamp01(2) == 1.0
    assert clamp01("nope", default=0.25) == 0.25


def test_clustered_angles_spread_vs_tight() -> None:
    rng_lo = random.Random(42)
    rng_hi = random.Random(42)
    theta_lo, theta_hi = 0.0, 2.0 * math.pi
    phi_lo, phi_hi = 0.0, math.pi
    samples_spread: list[tuple[float, float]] = []
    samples_tight: list[tuple[float, float]] = []
    for _ in range(400):
        samples_spread.append(
            clustered_ellipsoid_angles_bounded(
                rng_lo, 0.0, theta_lo=theta_lo, theta_hi=theta_hi, phi_lo=phi_lo, phi_hi=phi_hi
            )
        )
        samples_tight.append(
            clustered_ellipsoid_angles_bounded(
                rng_hi, 1.0, theta_lo=theta_lo, theta_hi=theta_hi, phi_lo=phi_lo, phi_hi=phi_hi
            )
        )
    st_t = statistics.pstdev(t for t, _ in samples_spread)
    st_p = statistics.pstdev(p for _, p in samples_spread)
    tt_t = statistics.pstdev(t for t, _ in samples_tight)
    tt_p = statistics.pstdev(p for _, p in samples_tight)
    assert st_t > tt_t * 3.0
    assert st_p > tt_p * 3.0


def test_clustered_angles_stays_in_bounds() -> None:
    rng = random.Random(7)
    p_lo, p_hi = 0.1 * math.pi, 0.85 * math.pi
    for c in (0.0, 0.5, 1.0):
        for _ in range(50):
            t, p = clustered_ellipsoid_angles_bounded(
                rng,
                c,
                theta_lo=0.15 * math.pi,
                theta_hi=0.9 * math.pi,
                phi_lo=p_lo,
                phi_hi=p_hi,
            )
            assert 0.0 <= t <= 2.0 * math.pi
            assert p_lo + 1e-7 <= p <= p_hi - 1e-7

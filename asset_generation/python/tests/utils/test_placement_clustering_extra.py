"""Extra coverage for placement clustering helpers (ticket 16 / diff-cover)."""

from __future__ import annotations

from types import SimpleNamespace

from src.utils.placement_clustering import (
    clustered_ellipsoid_angles_bounded,
    placement_prng,
    uniform_ring_angles,
)


def test_uniform_ring_angles_is_deterministic() -> None:
    a0 = uniform_ring_angles(
        1,
        4,
        theta_lo=0.0,
        theta_hi=3.0,
        phi_a=0.2,
        phi_b=1.1,
        clustering=0.4,
    )
    a1 = uniform_ring_angles(
        1,
        4,
        theta_lo=0.0,
        theta_hi=3.0,
        phi_a=0.2,
        phi_b=1.1,
        clustering=0.4,
    )
    assert a0 == a1


def test_clustered_ellipsoid_collapses_phi_when_band_is_paper_thin() -> None:
    class _R:
        def random(self) -> float:
            return 0.5

    focus = 0.7
    t, p = clustered_ellipsoid_angles_bounded(
        _R(),
        0.5,
        theta_lo=0.0,
        theta_hi=2.0,
        phi_lo=focus,
        phi_hi=focus + 1e-9,
    )
    assert abs(p - focus) < 1e-6
    assert 0.0 <= t <= 7.0


def test_placement_prng_invalid_seed_falls_back_to_zero() -> None:
    m = SimpleNamespace(build_options={"placement_seed": "not-a-number"})
    r0 = placement_prng(m)
    r1 = placement_prng(m)
    assert r0.random() == r1.random()

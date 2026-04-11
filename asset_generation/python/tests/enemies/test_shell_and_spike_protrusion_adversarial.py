"""
Adversarial extensions for shell attach + spike protrusion (Test Breaker).

Companion to ``test_shell_and_spike_protrusion.py`` (kept under 900 lines for org hook).

Spec: project_board/specs/enemy_body_part_extras_spec.md
Ticket: extras-shell-visible-spikes-on-top
"""

from __future__ import annotations

import math
from typing import Any
from unittest.mock import MagicMock, patch

from mathutils import Vector

from src.enemies.zone_geometry_extras_attach import (
    _append_body_ellipsoid_extras,
    _append_head_ellipsoid_extras,
    _ellipsoid_normal,
    _facing_allows_normal,
    _head_ref_scale,
    _zone_extra_clustering,
    _zone_extra_scale,
)
from tests.enemies.test_shell_and_spike_protrusion import (
    _capture_cone_with_depth,
    _fake_model,
    _shell_spec,
    _spike_spec,
)


def _horn_spec(**overrides: Any) -> dict[str, Any]:
    """Minimal spec for kind=horns (head zone)."""
    base = _spike_spec(kind="horns", spike_count=2)
    base.update(overrides)
    return base


def _expected_horn_tip_xyz(
    spec: dict[str, Any],
    hx: float,
    hy: float,
    hz: float,
    ax: float,
    ay: float,
    az: float,
    factor: float,
) -> list[tuple[float, float, float]]:
    """
    Mirror head horn placement in zone_geometry_extras_attach (kind == "horns").

    Exposes whether tip offset uses ``depth * factor`` (target 1.0 post-fix vs 0.55 legacy).
    """
    ref = _head_ref_scale(ax, ay, az)
    spike_sz = _zone_extra_scale(spec, "spike_size")
    cl = _zone_extra_clustering(spec)
    horn_spread = 1.0 - cl * 0.88
    depth = ref * 0.42 * spike_sz
    tips: list[tuple[float, float, float]] = []
    for side in (-1, 1):
        px = hx + ax * 0.3
        py = hy + float(side) * ay * 0.35 * horn_spread
        pz = hz + az * 0.5
        p = (px, py, pz)
        nrm = _ellipsoid_normal(hx, hy, hz, ax, ay, az, p)
        if not _facing_allows_normal(spec, nrm):
            continue
        tip = Vector(p) + nrm * (depth * factor)
        tips.append((float(tip.x), float(tip.y), float(tip.z)))
    return tips


# ---------------------------------------------------------------------------
# ADVERSARIAL — shell_scale at attach layer (raw spec, not only sanitize)
# ---------------------------------------------------------------------------


def test_shell_scale_clamped_to_min_at_attach_body() -> None:
    """
    ADV: Raw spec shell_scale below 1.01 must clamp at attach via _zone_extra_scale
    (defense in depth if options merge passes a bad value).

    Weakness exposed: attach reads spec dict directly; without clamp, shell could shrink
    inside the body ellipsoid.
    """
    model = _fake_model()
    spec = _shell_spec(shell_scale=0.3)
    a, b, h = 1.0, 0.8, 0.6
    sphere_calls: list[dict[str, Any]] = []

    def _capture_sphere(**kwargs: Any) -> MagicMock:
        sphere_calls.append(kwargs)
        return MagicMock()

    with patch(
        "src.enemies.zone_geometry_extras_attach.create_sphere",
        side_effect=_capture_sphere,
    ):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_body_ellipsoid_extras(model, spec, {}, {}, 0.0, 0.0, 0.0, a, b, h)

    assert len(sphere_calls) == 1
    scale = sphere_calls[0].get("scale")
    assert scale is not None
    assert abs(float(scale[0]) - 1.01 * a) < 1e-6, (
        f"clamped min scale[0] expected {1.01 * a}, got {scale[0]}"
    )


def test_shell_scale_clamped_to_max_at_attach_body() -> None:
    """ADV: shell_scale far above 1.5 must clamp at attach so shell stays a thin overlay."""
    model = _fake_model()
    spec = _shell_spec(shell_scale=9.99)
    a, b, h = 1.0, 0.8, 0.6
    sphere_calls: list[dict[str, Any]] = []

    def _capture_sphere(**kwargs: Any) -> MagicMock:
        sphere_calls.append(kwargs)
        return MagicMock()

    with patch(
        "src.enemies.zone_geometry_extras_attach.create_sphere",
        side_effect=_capture_sphere,
    ):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_body_ellipsoid_extras(model, spec, {}, {}, 0.0, 0.0, 0.0, a, b, h)

    assert len(sphere_calls) == 1
    scale = sphere_calls[0].get("scale")
    assert scale is not None
    assert abs(float(scale[0]) - 1.5 * a) < 1e-6, (
        f"clamped max scale[0] expected {1.5 * a}, got {scale[0]}"
    )


def test_shell_scale_missing_key_uses_default_at_attach_body() -> None:
    """
    ADV: Missing shell_scale in spec must fall back to default 1.08 at attach
    (same as _zone_extra_scale default), not 1.0 or spike_size logic.
    """
    model = _fake_model()
    spec = _shell_spec()
    del spec["shell_scale"]
    a, b, h = 1.0, 1.0, 1.0
    sphere_calls: list[dict[str, Any]] = []

    def _capture_sphere(**kwargs: Any) -> MagicMock:
        sphere_calls.append(kwargs)
        return MagicMock()

    with patch(
        "src.enemies.zone_geometry_extras_attach.create_sphere",
        side_effect=_capture_sphere,
    ):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_body_ellipsoid_extras(model, spec, {}, {}, 0.0, 0.0, 0.0, a, b, h)

    assert len(sphere_calls) == 1
    scale = sphere_calls[0].get("scale")
    assert scale is not None
    assert abs(float(scale[0]) - 1.08 * a) < 1e-6, (
        f"missing shell_scale should default to 1.08 * a, got {scale[0]}"
    )


def test_shell_scale_invalid_string_uses_default_at_attach_body() -> None:
    """ADV: Non-numeric shell_scale in raw spec → _zone_extra_scale falls back to default."""
    model = _fake_model()
    spec = _shell_spec(shell_scale="not_a_number")  # type: ignore[arg-type]
    a, b, h = 1.0, 0.9, 0.7
    sphere_calls: list[dict[str, Any]] = []

    def _capture_sphere(**kwargs: Any) -> MagicMock:
        sphere_calls.append(kwargs)
        return MagicMock()

    with patch(
        "src.enemies.zone_geometry_extras_attach.create_sphere",
        side_effect=_capture_sphere,
    ):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_body_ellipsoid_extras(model, spec, {}, {}, 0.0, 0.0, 0.0, a, b, h)

    assert len(sphere_calls) == 1
    scale = sphere_calls[0].get("scale")
    assert scale is not None
    assert abs(float(scale[0]) - 1.08 * a) < 1e-6


def test_shell_combined_negative_offset_and_extreme_scale_head() -> None:
    """
    ADV combinatorial: negative offset + large valid shell_scale on head —
    location must still be (hx+ox, hy+oy, hz+oz), scales use clamped shell_scale.
    """
    model = _fake_model()
    spec = _shell_spec(shell_scale=1.5, offset_x=-0.2, offset_y=0.1, offset_z=-0.05)
    hx, hy, hz = 1.0, 2.0, 3.0
    ax, ay, az = 0.5, 0.5, 0.5
    sphere_calls: list[dict[str, Any]] = []

    def _capture_sphere(**kwargs: Any) -> MagicMock:
        sphere_calls.append(kwargs)
        return MagicMock()

    with patch(
        "src.enemies.zone_geometry_extras_attach.create_sphere",
        side_effect=_capture_sphere,
    ):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_head_ellipsoid_extras(model, spec, {}, {}, hx, hy, hz, ax, ay, az)

    assert len(sphere_calls) == 1
    loc = sphere_calls[0].get("location")
    assert loc is not None
    lx = float(loc[0]) if hasattr(loc, "__getitem__") else float(getattr(loc, "x", 0.0))
    ly = float(loc[1]) if hasattr(loc, "__getitem__") else float(getattr(loc, "y", 0.0))
    lz = float(loc[2]) if hasattr(loc, "__getitem__") else float(getattr(loc, "z", 0.0))
    assert abs(lx - (hx - 0.2)) < 1e-6
    assert abs(ly - (hy + 0.1)) < 1e-6
    assert abs(lz - (hz - 0.05)) < 1e-6
    scale = sphere_calls[0].get("scale")
    assert scale is not None
    assert abs(float(scale[0]) - 1.5 * ax) < 1e-6


# ---------------------------------------------------------------------------
# ADVERSARIAL — spike paths beyond uniform arc + unit sphere
# ---------------------------------------------------------------------------


def test_spike_pyramid_body_base_not_embedded() -> None:
    """
    ADV: spike_shape=pyramid still uses create_cone (vertices=4); same flush invariant.

    Weakness: a refactor to a different primitive could drop the protrusion fix on pyramids.
    """
    spec = _spike_spec(
        spike_shape="pyramid",
        spike_count=1,
        distribution="uniform",
        uniform_shape="arc",
    )
    cx, cy, cz = 0.0, 0.0, 0.0
    a = b = h = 1.0
    cone_calls: list[tuple[tuple[float, float, float], float]] = []
    model = _fake_model()

    with patch(
        "src.enemies.zone_geometry_extras_attach.create_cone",
        side_effect=_capture_cone_with_depth(cone_calls),
    ):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_body_ellipsoid_extras(model, spec, {}, {}, cx, cy, cz, a, b, h)

    assert len(cone_calls) >= 1
    tip_loc, depth = cone_calls[0]
    tip_x, tip_y, tip_z = tip_loc
    dist_tip = math.sqrt(tip_x ** 2 + tip_y ** 2 + tip_z ** 2)
    nrm_x = tip_x / dist_tip
    nrm_y = tip_y / dist_tip
    nrm_z = tip_z / dist_tip
    base_x = tip_x - depth * nrm_x
    base_y = tip_y - depth * nrm_y
    base_z = tip_z - depth * nrm_z
    dist_base = math.sqrt(base_x ** 2 + base_y ** 2 + base_z ** 2)
    assert dist_base >= 1.0 - 1e-9


def test_spike_body_random_distribution_each_base_not_embedded() -> None:
    """
    ADV: distribution=random must apply the same tip factor at every placement
    (rng is deterministic via MagicMock returning 0.25).
    """
    spec = _spike_spec(
        spike_count=3,
        distribution="random",
        uniform_shape="arc",
    )
    cx, cy, cz = 0.0, 0.0, 0.0
    a = b = h = 1.0
    cone_calls: list[tuple[tuple[float, float, float], float]] = []
    model = _fake_model()

    with patch(
        "src.enemies.zone_geometry_extras_attach.create_cone",
        side_effect=_capture_cone_with_depth(cone_calls),
    ):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_body_ellipsoid_extras(model, spec, {}, {}, cx, cy, cz, a, b, h)

    assert len(cone_calls) == 3, f"expected 3 spikes, got {len(cone_calls)}"
    for tip_loc, depth in cone_calls:
        tip_x, tip_y, tip_z = tip_loc
        dist_tip = math.sqrt(tip_x ** 2 + tip_y ** 2 + tip_z ** 2)
        nrm_x = tip_x / dist_tip
        nrm_y = tip_y / dist_tip
        nrm_z = tip_z / dist_tip
        base_x = tip_x - depth * nrm_x
        base_y = tip_y - depth * nrm_y
        base_z = tip_z - depth * nrm_z
        dist_base = math.sqrt(base_x ** 2 + base_y ** 2 + base_z ** 2)
        assert dist_base >= 1.0 - 1e-9, f"random path embedded base dist_base={dist_base}"


def test_spike_head_uniform_ring_base_not_embedded() -> None:
    """ADV: head spikes + uniform_shape=ring exercises different angle helper; tip factor must hold."""
    spec = _spike_spec(
        kind="spikes",
        spike_count=1,
        distribution="uniform",
        uniform_shape="ring",
    )
    hx, hy, hz = 0.0, 0.0, 0.0
    ax = ay = az = 1.0
    cone_calls: list[tuple[tuple[float, float, float], float]] = []
    model = _fake_model()

    with patch(
        "src.enemies.zone_geometry_extras_attach.create_cone",
        side_effect=_capture_cone_with_depth(cone_calls),
    ):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_head_ellipsoid_extras(model, spec, {}, {}, hx, hy, hz, ax, ay, az)

    assert len(cone_calls) >= 1
    tip_loc, depth = cone_calls[0]
    tip_x, tip_y, tip_z = tip_loc
    dist_tip = math.sqrt(tip_x ** 2 + tip_y ** 2 + tip_z ** 2)
    nrm_x = tip_x / dist_tip
    nrm_y = tip_y / dist_tip
    nrm_z = tip_z / dist_tip
    base_x = tip_x - depth * nrm_x
    base_y = tip_y - depth * nrm_y
    base_z = tip_z - depth * nrm_z
    dist_base = math.sqrt(base_x ** 2 + base_y ** 2 + base_z ** 2)
    assert dist_base >= 1.0 - 1e-9


def test_head_spike_random_distribution_base_not_embedded() -> None:
    """ADV: head spikes random mode — same invariant as body random."""
    spec = _spike_spec(
        kind="spikes",
        spike_count=2,
        distribution="random",
        uniform_shape="arc",
    )
    hx, hy, hz = 0.0, 0.0, 0.0
    ax = ay = az = 1.0
    cone_calls: list[tuple[tuple[float, float, float], float]] = []
    model = _fake_model()

    with patch(
        "src.enemies.zone_geometry_extras_attach.create_cone",
        side_effect=_capture_cone_with_depth(cone_calls),
    ):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_head_ellipsoid_extras(model, spec, {}, {}, hx, hy, hz, ax, ay, az)

    assert len(cone_calls) == 2
    for tip_loc, depth in cone_calls:
        tip_x, tip_y, tip_z = tip_loc
        dist_tip = math.sqrt(tip_x ** 2 + tip_y ** 2 + tip_z ** 2)
        nrm_x = tip_x / dist_tip
        nrm_y = tip_y / dist_tip
        nrm_z = tip_z / dist_tip
        base_x = tip_x - depth * nrm_x
        base_y = tip_y - depth * nrm_y
        base_z = tip_z - depth * nrm_z
        dist_base = math.sqrt(base_x ** 2 + base_y ** 2 + base_z ** 2)
        assert dist_base >= 1.0 - 1e-9


def test_horn_cone_tips_match_full_depth_factor() -> None:
    """
    ADV: Horn path uses anchor points off the uniform sphere grid; unit-sphere shortcut
    does not validate normals. Compare captured tips to analytically expected tips
    for factor 1.0 (post-fix).

    Catches: updating body/head spike factors but missing horn call site.
    """
    spec = _horn_spec()
    hx, hy, hz = 0.0, 0.0, 0.0
    ax = ay = az = 1.0
    expected = _expected_horn_tip_xyz(spec, hx, hy, hz, ax, ay, az, factor=1.0)
    assert len(expected) == 2, "test setup: both horns should pass facing with all faces on"

    cone_calls: list[tuple[tuple[float, float, float], float]] = []
    model = _fake_model()

    with patch(
        "src.enemies.zone_geometry_extras_attach.create_cone",
        side_effect=_capture_cone_with_depth(cone_calls),
    ):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_head_ellipsoid_extras(model, spec, {}, {}, hx, hy, hz, ax, ay, az)

    assert len(cone_calls) == 2
    got_tips = [t[0] for t in cone_calls]
    for exp in expected:
        found = any(
            math.sqrt((exp[0] - g[0]) ** 2 + (exp[1] - g[1]) ** 2 + (exp[2] - g[2]) ** 2) < 1e-5
            for g in got_tips
        )
        assert found, f"expected horn tip {exp} not found in {got_tips}"

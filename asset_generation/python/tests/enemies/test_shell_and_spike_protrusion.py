"""
Zone geometry extras — shell geometry and spike protrusion tests.

Spec: project_board/specs/enemy_body_part_extras_spec.md  (v2)
Ticket: extras-shell-visible-spikes-on-top

Covered ACs:
  AC-Shell-Body  — kind=shell on body zone appends one sphere, location equals zone center
  AC-Shell-Head  — kind=shell on head zone appends one sphere, location equals head center
  AC-Shell-Noop  — kind=none produces no create_sphere call and no parts
  AC-Shell-Scale — shell_scale applied to all three sphere scale axes
  AC-Shell-Offset — offset_xyz shifts the shell sphere location
  AC-P3/P4       — spike tip factor=1.0 (post-fix); tip strictly above ellipsoid surface

Mocking strategy:
  - ``create_sphere`` and ``create_cone`` are patched at the
    ``src.enemies.zone_geometry_extras_attach`` module path.
  - ``apply_material_to_object`` and ``material_for_zone_geometry_extra`` are
    patched to avoid material-system dependencies.
  - The _vec_xyz helper is NOT patched — it is tested indirectly through location
    assertions to ensure it extracts correctly from Vector stubs.
"""

from __future__ import annotations

import math
from typing import Any
from unittest.mock import MagicMock, patch

from src.enemies.zone_geometry_extras_attach import (
    _append_body_ellipsoid_extras,
    _append_head_ellipsoid_extras,
)
from tests.enemies.test_zone_extras_offset_attach import _spike_spec

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_model() -> Any:
    """Minimal model stub accepted by the attach functions."""
    m = MagicMock()
    m.name = "slug"
    m.parts = []
    m.rng = MagicMock()
    m.rng.random = MagicMock(return_value=0.25)
    return m


def _shell_spec(**overrides: Any) -> dict[str, Any]:
    """Minimal spec dict for kind=shell with default shell_scale."""
    defaults: dict[str, Any] = {
        "kind": "shell",
        "shell_scale": 1.08,
        "finish": "default",
        "hex": "",
        "offset_x": 0.0,
        "offset_y": 0.0,
        "offset_z": 0.0,
        # placement flags — unused by shell but must be present for completeness
        "place_top": True,
        "place_bottom": True,
        "place_front": True,
        "place_back": True,
        "place_left": True,
        "place_right": True,
    }
    defaults.update(overrides)
    return defaults


def _none_spec(**overrides: Any) -> dict[str, Any]:
    """Minimal spec dict for kind=none."""
    defaults: dict[str, Any] = {
        "kind": "none",
        "shell_scale": 1.08,
        "finish": "default",
        "hex": "",
        "offset_x": 0.0,
        "offset_y": 0.0,
        "offset_z": 0.0,
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# AC-Shell-Body: kind=shell on body zone appends exactly one sphere
# ---------------------------------------------------------------------------


def test_shell_body_appends_sphere() -> None:
    """
    AC-Shell-Body: kind=shell on body zone → create_sphere called exactly once;
    one part appended to model.parts.

    Spec ref: enemy_body_part_extras_spec.md §Per-kind semantics (shell),
              §Tests (obligations) — test_shell_body_appends_sphere
    """
    model = _fake_model()
    spec = _shell_spec()
    cx, cy, cz = 0.0, 0.0, 0.0
    a, b, h = 1.0, 0.8, 0.6

    fake_obj = MagicMock()
    sphere_calls: list[Any] = []

    def _capture_sphere(**kwargs: Any) -> MagicMock:
        sphere_calls.append(kwargs)
        return fake_obj

    with patch(
        "src.enemies.zone_geometry_extras_attach.create_sphere",
        side_effect=_capture_sphere,
    ):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_body_ellipsoid_extras(model, spec, {}, {}, cx, cy, cz, a, b, h)

    assert len(sphere_calls) == 1, (
        f"expected create_sphere called once for kind=shell on body, got {len(sphere_calls)}"
    )
    assert len(model.parts) == 1, (
        f"expected exactly one part appended for kind=shell on body, got {len(model.parts)}"
    )


# ---------------------------------------------------------------------------
# AC-Shell-Head: kind=shell on head zone appends exactly one sphere
# ---------------------------------------------------------------------------


def test_shell_head_appends_sphere() -> None:
    """
    AC-Shell-Head: kind=shell on head zone → create_sphere called exactly once;
    one part appended to model.parts.

    Spec ref: enemy_body_part_extras_spec.md §Per-kind semantics (shell),
              §Tests (obligations) — test_shell_head_appends_sphere
    """
    model = _fake_model()
    spec = _shell_spec()
    hx, hy, hz = 0.5, 0.0, 1.2
    ax, ay, az = 0.3, 0.3, 0.3

    fake_obj = MagicMock()
    sphere_calls: list[Any] = []

    def _capture_sphere(**kwargs: Any) -> MagicMock:
        sphere_calls.append(kwargs)
        return fake_obj

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

    assert len(sphere_calls) == 1, (
        f"expected create_sphere called once for kind=shell on head, got {len(sphere_calls)}"
    )
    assert len(model.parts) == 1, (
        f"expected exactly one part appended for kind=shell on head, got {len(model.parts)}"
    )


# ---------------------------------------------------------------------------
# AC-Shell-Noop: kind=none → no create_sphere call from shell path
# ---------------------------------------------------------------------------


def test_shell_none_is_noop_body() -> None:
    """
    AC-Shell-Noop (body): kind=none → create_sphere NOT called; no parts appended.

    Spec ref: enemy_body_part_extras_spec.md §Per-kind semantics (none),
              §Tests (obligations) — test_shell_none_is_noop
    """
    model = _fake_model()
    spec = _none_spec()

    with patch(
        "src.enemies.zone_geometry_extras_attach.create_sphere"
    ) as p_sphere:
        with patch("src.enemies.zone_geometry_extras_attach.create_cone") as p_cone:
            with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
                with patch(
                    "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                    return_value=MagicMock(),
                ):
                    _append_body_ellipsoid_extras(model, spec, {}, {}, 0.0, 0.0, 0.0, 1.0, 0.8, 0.6)

    p_sphere.assert_not_called()
    p_cone.assert_not_called()
    assert len(model.parts) == 0, (
        f"expected 0 parts for kind=none, got {len(model.parts)}"
    )


def test_shell_none_is_noop_head() -> None:
    """
    AC-Shell-Noop (head): kind=none on head zone → create_sphere NOT called; no parts.

    Spec ref: enemy_body_part_extras_spec.md §Per-kind semantics (none)
    """
    model = _fake_model()
    spec = _none_spec()

    with patch(
        "src.enemies.zone_geometry_extras_attach.create_sphere"
    ) as p_sphere:
        with patch("src.enemies.zone_geometry_extras_attach.create_cone") as p_cone:
            with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
                with patch(
                    "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                    return_value=MagicMock(),
                ):
                    _append_head_ellipsoid_extras(model, spec, {}, {}, 0.0, 0.0, 1.0, 0.3, 0.3, 0.3)

    p_sphere.assert_not_called()
    p_cone.assert_not_called()
    assert len(model.parts) == 0, (
        f"expected 0 parts for kind=none (head), got {len(model.parts)}"
    )


# ---------------------------------------------------------------------------
# AC-Shell-Scale: shell_scale applied to sphere scale axes
# ---------------------------------------------------------------------------


def test_shell_scale_applied_to_sphere_args_body() -> None:
    """
    AC-Shell-Scale (body): kind=shell, shell_scale=1.2, zone (a=1.0, b=0.8, h=0.6)
    → create_sphere called with scale ≈ (1.2, 0.96, 0.72) within tolerance 1e-6.

    Spec ref: enemy_body_part_extras_spec.md §Per-kind semantics (shell):
      scale=(a * shell_scale, b * shell_scale, h * shell_scale)
    """
    model = _fake_model()
    spec = _shell_spec(shell_scale=1.2)
    cx, cy, cz = 0.0, 0.0, 0.0
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
                _append_body_ellipsoid_extras(model, spec, {}, {}, cx, cy, cz, a, b, h)

    assert len(sphere_calls) == 1, "expected exactly one create_sphere call for kind=shell"
    scale = sphere_calls[0].get("scale")
    assert scale is not None, "create_sphere must receive scale kwarg"
    sx, sy, sz = float(scale[0]), float(scale[1]), float(scale[2])
    assert abs(sx - 1.2 * a) < 1e-6, f"scale[0] expected {1.2 * a}, got {sx}"
    assert abs(sy - 1.2 * b) < 1e-6, f"scale[1] expected {1.2 * b}, got {sy}"
    assert abs(sz - 1.2 * h) < 1e-6, f"scale[2] expected {1.2 * h}, got {sz}"


def test_shell_default_scale_applied_to_sphere_args_body() -> None:
    """
    AC-Shell-Scale default (body): shell_scale=1.08 (default),
    zone (a=1.0, b=0.8, h=0.6) → scale ≈ (1.08, 0.864, 0.648).

    Spec ref: enemy_body_part_extras_spec.md §shell_scale field specification
    """
    model = _fake_model()
    spec = _shell_spec(shell_scale=1.08)
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
    sx, sy, sz = float(scale[0]), float(scale[1]), float(scale[2])
    assert abs(sx - 1.08 * a) < 1e-6, f"scale[0] expected {1.08 * a}, got {sx}"
    assert abs(sy - 1.08 * b) < 1e-6, f"scale[1] expected {1.08 * b}, got {sy}"
    assert abs(sz - 1.08 * h) < 1e-6, f"scale[2] expected {1.08 * h}, got {sz}"


def test_shell_scale_applied_to_sphere_args_head() -> None:
    """
    AC-Shell-Scale (head): kind=shell, shell_scale=1.15, head semi-axes (ax=0.4, ay=0.35, az=0.5)
    → create_sphere called with scale ≈ (0.46, 0.4025, 0.575).

    Spec ref: enemy_body_part_extras_spec.md §Per-kind semantics (shell) — applies to head zone
    """
    model = _fake_model()
    spec = _shell_spec(shell_scale=1.15)
    hx, hy, hz = 0.5, 0.0, 1.0
    ax, ay, az = 0.4, 0.35, 0.5

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

    assert len(sphere_calls) == 1, "expected exactly one create_sphere call for kind=shell (head)"
    scale = sphere_calls[0].get("scale")
    assert scale is not None, "create_sphere must receive scale kwarg (head shell)"
    sx, sy, sz = float(scale[0]), float(scale[1]), float(scale[2])
    assert abs(sx - 1.15 * ax) < 1e-6, f"head scale[0] expected {1.15 * ax}, got {sx}"
    assert abs(sy - 1.15 * ay) < 1e-6, f"head scale[1] expected {1.15 * ay}, got {sy}"
    assert abs(sz - 1.15 * az) < 1e-6, f"head scale[2] expected {1.15 * az}, got {sz}"


# ---------------------------------------------------------------------------
# AC-Shell-Offset: shell sphere location reflects offset_xyz
# ---------------------------------------------------------------------------


def test_shell_offset_applied_to_sphere_location_body() -> None:
    """
    AC-Shell-Offset (body): kind=shell, offset_x=0.5, cx=0.0
    → create_sphere location x ≈ 0.5.

    Spec ref: enemy_body_part_extras_spec.md §Per-kind semantics (shell):
      location=(cx, cy, cz) where (cx,cy,cz) is zone center after offset_xyz applied.
    """
    model = _fake_model()
    spec = _shell_spec(offset_x=0.5, offset_y=0.0, offset_z=0.0)
    cx, cy, cz = 0.0, 0.0, 0.0
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
                _append_body_ellipsoid_extras(model, spec, {}, {}, cx, cy, cz, a, b, h)

    assert len(sphere_calls) == 1
    loc = sphere_calls[0].get("location")
    assert loc is not None, "create_sphere must receive location kwarg"
    loc_x = float(loc[0]) if hasattr(loc, "__getitem__") else float(getattr(loc, "x", loc[0]))
    assert abs(loc_x - 0.5) < 1e-6, (
        f"shell sphere location x expected 0.5 with offset_x=0.5, got {loc_x}"
    )


def test_shell_zero_offset_location_equals_zone_center_body() -> None:
    """
    AC-Shell-Offset identity (body): offset_x=0, offset_y=0, offset_z=0
    → shell sphere location == zone center (cx, cy, cz).

    Spec ref: enemy_body_part_extras_spec.md §Per-kind semantics (shell)
    """
    model = _fake_model()
    spec = _shell_spec(offset_x=0.0, offset_y=0.0, offset_z=0.0)
    cx, cy, cz = 0.3, -0.1, 0.8
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
                _append_body_ellipsoid_extras(model, spec, {}, {}, cx, cy, cz, a, b, h)

    assert len(sphere_calls) == 1
    loc = sphere_calls[0].get("location")
    assert loc is not None
    lx = float(loc[0]) if hasattr(loc, "__getitem__") else float(getattr(loc, "x", 0.0))
    ly = float(loc[1]) if hasattr(loc, "__getitem__") else float(getattr(loc, "y", 0.0))
    lz = float(loc[2]) if hasattr(loc, "__getitem__") else float(getattr(loc, "z", 0.0))
    assert abs(lx - cx) < 1e-6, f"location x expected {cx}, got {lx}"
    assert abs(ly - cy) < 1e-6, f"location y expected {cy}, got {ly}"
    assert abs(lz - cz) < 1e-6, f"location z expected {cz}, got {lz}"


# ---------------------------------------------------------------------------
# AC-P3/P4: spike cone base does not embed inside the ellipsoid surface
# ---------------------------------------------------------------------------


def _capture_cone_with_depth(dest: list) -> Any:
    """
    Return a side_effect function that captures (location, scale) from create_cone calls.
    scale[2] (the Z scale component) is used as the cone depth by the attach code
    (create_cone is called with scale=(rad, rad, depth)).
    """
    def _fn(location=None, scale=None, **kwargs: Any) -> MagicMock:
        if location is not None and scale is not None:
            if hasattr(location, "_t"):
                loc = (float(location._t[0]), float(location._t[1]), float(location._t[2]))
            elif hasattr(location, "x"):
                loc = (float(location.x), float(location.y), float(location.z))
            else:
                loc = (float(location[0]), float(location[1]), float(location[2]))
            depth = float(scale[2])
            dest.append((loc, depth))
        obj = MagicMock()
        obj.rotation_euler = (0.0, 0.0, 0.0)
        return obj
    return _fn


def test_spike_tip_protrudes_above_surface() -> None:
    """
    AC-P3/P4: unit sphere zone (a=b=h=1.0), one body spike.

    The fix changes the tip offset factor from 0.55 to 1.0. The observable
    consequence is that the cone BASE (at tip - depth * nrm) sits flush on the
    surface rather than embedded in it.

    For any spike placed on a unit sphere:
      surface_point p has |p - center| = 1.0
      outward normal nrm = p - center  (unit vector for unit sphere)
      tip = p + nrm * depth * factor
      base_center = tip - nrm * depth = p + nrm * depth * (factor - 1.0)

    The cone is axis-aligned with nrm, so its base circle sits at base_center.
    The base_center distance from center:
      |base_center - center| = |p + nrm * depth * (factor - 1.0) - center|
                             = 1.0 + depth * (factor - 1.0)   [nrm is unit]

    For factor=0.55: base distance = 1.0 - 0.45 * depth < 1.0 → embedded.
    For factor=1.0:  base distance = 1.0 → flush on surface.

    Test invariant (post-fix): |base_center - center| >= 1.0
    i.e. the base of the cone does not sit inside the ellipsoid.

    This test will FAIL against the current implementation (factor=0.55) and
    PASS once the factor is changed to 1.0.

    Spec ref: enemy_body_part_extras_spec.md §Spike tip offset geometry (v2):
      tip = Vector(surface_point) + nrm * depth * 1.0
      → base sits flush on surface: dot(base - center, nrm) == 1.0
    """
    spec = _spike_spec(
        spike_count=1,
        distribution="uniform",
        uniform_shape="arc",
        place_top=True,
        place_bottom=True,
        place_front=True,
        place_back=True,
        place_left=True,
        place_right=True,
        offset_x=0.0,
        offset_y=0.0,
        offset_z=0.0,
    )

    cx, cy, cz = 0.0, 0.0, 0.0
    # Unit sphere: every surface point is at distance 1.0 from center.
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

    assert len(cone_calls) >= 1, "expected at least one spike to be placed"

    tip_loc, depth = cone_calls[0]
    tip_x, tip_y, tip_z = tip_loc

    # Distance from center to tip = 1 + depth * factor
    dist_tip = math.sqrt(tip_x ** 2 + tip_y ** 2 + tip_z ** 2)

    # Recover the outward normal direction: nrm = tip / |tip| for a unit sphere
    # (since tip = p + nrm * depth * factor, and p = nrm for unit sphere)
    # nrm = tip_loc / dist_tip
    nrm_x = tip_x / dist_tip
    nrm_y = tip_y / dist_tip
    nrm_z = tip_z / dist_tip

    # Compute base_center = tip - depth * nrm
    base_x = tip_x - depth * nrm_x
    base_y = tip_y - depth * nrm_y
    base_z = tip_z - depth * nrm_z

    # Base distance from center (should equal 1.0 for factor=1.0, < 1.0 for factor=0.55)
    dist_base = math.sqrt(base_x ** 2 + base_y ** 2 + base_z ** 2)

    # Post-fix invariant: base must be at or above the surface (>= 1.0)
    assert dist_base >= 1.0 - 1e-9, (
        f"cone base distance from center ({dist_base:.6f}) must be >= 1.0 (flush on surface); "
        f"tip={tip_loc}, depth={depth:.4f}, base=({base_x:.4f},{base_y:.4f},{base_z:.4f}); "
        f"factor inferred={(dist_tip - 1.0) / depth:.4f} (should be 1.0, was 0.55 pre-fix)"
    )


def test_spike_tip_protrudes_above_surface_head() -> None:
    """
    AC-P3/P4 (head spikes): unit sphere head zone, one head spike.
    Cone base must NOT be embedded in the head ellipsoid surface.

    Same invariant as body variant — head spikes path must also use factor=1.0.

    Spec ref: enemy_body_part_extras_spec.md §Spike tip offset geometry (v2)
    """
    spec = _spike_spec(
        kind="spikes",
        spike_count=1,
        distribution="uniform",
        uniform_shape="arc",
        place_top=True,
        place_bottom=True,
        place_front=True,
        place_back=True,
        place_left=True,
        place_right=True,
        offset_x=0.0,
        offset_y=0.0,
        offset_z=0.0,
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

    assert len(cone_calls) >= 1, "expected at least one head spike placed"

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

    assert dist_base >= 1.0 - 1e-9, (
        f"head cone base distance from center ({dist_base:.6f}) must be >= 1.0 (flush on surface); "
        f"tip={tip_loc}, depth={depth:.4f}, base=({base_x:.4f},{base_y:.4f},{base_z:.4f}); "
        f"factor inferred={(dist_tip - 1.0) / depth:.4f} (should be 1.0, was 0.55 pre-fix)"
    )

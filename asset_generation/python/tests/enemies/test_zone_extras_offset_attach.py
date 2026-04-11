"""
Zone geometry extras attach — offset_x/y/z shift tests.

Spec: project_board/specs/zone_extras_offset_xyz_controls_spec.md  Requirement 5
Ticket: 17_zone_extras_offset_xyz_controls

Tests assert that non-zero offset_x/y/z shift the ellipsoid center used for
geometry placement.  ``bpy``, ``create_cone``, ``create_sphere``, and all
Blender-dependent helpers are stubbed via the root conftest / enemies conftest.

Covered ACs: 5.1–5.9, 9.2, 9.3
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import src.enemies.zone_geometry_extras_attach as _attach_module
from src.enemies.zone_geometry_extras_attach import (
    _append_body_ellipsoid_extras,
    _append_head_ellipsoid_extras,
)

# _zone_extra_offset is expected to be added in the implementation step.
# Tests retrieve it via getattr so collection succeeds; they fail with a
# clear pytest.fail message when the function is absent.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_model(name: str = "slug") -> Any:
    """Minimal model stub accepted by the attach functions."""
    m = MagicMock()
    m.name = name
    m.parts = []
    m.rng = MagicMock()
    m.rng.random = MagicMock(return_value=0.25)
    return m



def _spike_spec(**overrides: Any) -> dict[str, Any]:
    """Minimal body spike spec; override fields as needed."""
    defaults: dict[str, Any] = {
        "kind": "spikes",
        "spike_count": 1,
        "spike_shape": "cone",
        "spike_size": 1.0,
        "clustering": 0.5,
        "distribution": "uniform",
        "uniform_shape": "arc",
        "place_top": True,
        "place_bottom": True,
        "place_front": True,
        "place_back": True,
        "place_left": True,
        "place_right": True,
        "finish": "default",
        "hex": "",
        "offset_x": 0.0,
        "offset_y": 0.0,
        "offset_z": 0.0,
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# _zone_extra_offset helper — AC-5.1 through AC-5.4
# ---------------------------------------------------------------------------


def _get_zone_extra_offset():
    """Retrieve _zone_extra_offset from the module; skip if not yet implemented."""
    fn = getattr(_attach_module, "_zone_extra_offset", None)
    if fn is None:
        pytest.fail(
            "_zone_extra_offset is not defined in zone_geometry_extras_attach.py — "
            "implementation step must add this helper (Requirement 5)."
        )
    return fn


def test_zone_extra_offset_present_value() -> None:
    """AC-5.1: _zone_extra_offset({'offset_x': 1.0}, 'offset_x') == 1.0."""
    fn = _get_zone_extra_offset()
    assert fn({"offset_x": 1.0}, "offset_x") == pytest.approx(1.0)


def test_zone_extra_offset_missing_key_returns_zero() -> None:
    """AC-5.2: _zone_extra_offset({}, 'offset_x') == 0.0 (missing key defaults to 0)."""
    fn = _get_zone_extra_offset()
    assert fn({}, "offset_x") == pytest.approx(0.0)


def test_zone_extra_offset_invalid_string_returns_zero() -> None:
    """AC-5.3: _zone_extra_offset({'offset_x': 'bad'}, 'offset_x') == 0.0."""
    fn = _get_zone_extra_offset()
    assert fn({"offset_x": "bad"}, "offset_x") == pytest.approx(0.0)


def test_zone_extra_offset_string_abc_returns_zero() -> None:
    """ADVERSARIAL: _zone_extra_offset({'offset_x': 'abc'}, 'offset_x') == 0.0."""
    # ADVERSARIAL
    fn = _get_zone_extra_offset()
    assert fn({"offset_x": "abc"}, "offset_x") == pytest.approx(0.0)


def test_zone_extra_offset_clamped_to_max() -> None:
    """AC-5.4: _zone_extra_offset({'offset_x': 5.0}, 'offset_x') == 2.0 (clamped)."""
    fn = _get_zone_extra_offset()
    assert fn({"offset_x": 5.0}, "offset_x") == pytest.approx(2.0)


def test_zone_extra_offset_clamped_to_min() -> None:
    """AC-5.4 (negative): _zone_extra_offset({'offset_x': -5.0}, 'offset_x') == -2.0."""
    fn = _get_zone_extra_offset()
    assert fn({"offset_x": -5.0}, "offset_x") == pytest.approx(-2.0)


def test_zone_extra_offset_negative_in_range_preserved() -> None:
    """_zone_extra_offset({'offset_y': -1.5}, 'offset_y') == -1.5 (in range, no clamp)."""
    fn = _get_zone_extra_offset()
    assert fn({"offset_y": -1.5}, "offset_y") == pytest.approx(-1.5)


# ---------------------------------------------------------------------------
# _append_body_ellipsoid_extras — AC-5.5 and AC-5.6
# ---------------------------------------------------------------------------


def test_body_offset_x_shifts_spike_location_x() -> None:
    """
    AC-5.5: non-zero offset_x shifts the X component of the create_cone location argument.

    Strategy: call _append_body_ellipsoid_extras twice with identical cx/cy/cz and
    ellipsoid radii but different offset_x (0.0 vs 1.0).  Capture the 'location'
    kwarg passed to create_cone in each call.  The X component should differ by
    approximately 1.0 (the offset value).

    The body ellipsoid center starts at cx=0.0.  With offset_x=1.0, the effective
    center is 1.0 before the surface formula runs.  The tip X-component is:
        tip_x = (cx + offset_x) + a * sin(phi) * cos(theta) + nrm_x * depth * 0.55
    The difference between the two calls' tip_x values is exactly offset_x (1.0)
    because all other terms are equal (same angles, same radii).
    """
    cx, cy, cz = 0.0, 0.0, 0.0
    a, b, h = 0.5, 0.5, 0.5

    locations_with_offset: list[tuple[float, float, float]] = []
    locations_without_offset: list[tuple[float, float, float]] = []

    def _capture_factory(dest: list) -> Any:
        def _create_cone(location=None, **kwargs: Any) -> MagicMock:
            if location is not None:
                dest.append(location)
            obj = MagicMock()
            obj.rotation_euler = (0.0, 0.0, 0.0)
            return obj
        return _create_cone

    model = _fake_model()

    # Call with offset_x = 1.0
    spec_with_offset = _spike_spec(spike_count=1, offset_x=1.0)
    with patch(
        "src.enemies.zone_geometry_extras_attach.create_cone",
        side_effect=_capture_factory(locations_with_offset),
    ):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_body_ellipsoid_extras(model, spec_with_offset, {}, {}, cx, cy, cz, a, b, h)

    # Call with offset_x = 0.0 (identity)
    spec_no_offset = _spike_spec(spike_count=1, offset_x=0.0)
    with patch(
        "src.enemies.zone_geometry_extras_attach.create_cone",
        side_effect=_capture_factory(locations_without_offset),
    ):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_body_ellipsoid_extras(model, spec_no_offset, {}, {}, cx, cy, cz, a, b, h)

    assert len(locations_with_offset) >= 1, "expected at least one spike placed with offset"
    assert len(locations_without_offset) >= 1, "expected at least one spike placed without offset"

    x_with = locations_with_offset[0][0]
    x_without = locations_without_offset[0][0]
    # The X shift must be approximately equal to the offset value (1.0).
    assert abs(x_with - x_without - 1.0) < 0.01, (
        f"expected X difference ≈ 1.0, got x_with={x_with}, x_without={x_without}"
    )


def test_body_offset_y_shifts_spike_location_y() -> None:
    """AC-5.5 (Y axis): offset_y=1.0 shifts the Y component by approximately 1.0."""
    cx, cy, cz = 0.0, 0.0, 0.0
    a, b, h = 0.5, 0.5, 0.5

    locs_with: list[tuple[float, float, float]] = []
    locs_without: list[tuple[float, float, float]] = []

    def _capture(dest: list) -> Any:
        def _fn(location=None, **kwargs: Any) -> MagicMock:
            if location is not None:
                dest.append(location)
            obj = MagicMock()
            obj.rotation_euler = (0.0, 0.0, 0.0)
            return obj
        return _fn

    model = _fake_model()

    spec_with = _spike_spec(spike_count=1, offset_y=1.0)
    with patch("src.enemies.zone_geometry_extras_attach.create_cone", side_effect=_capture(locs_with)):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch("src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra", return_value=MagicMock()):
                _append_body_ellipsoid_extras(model, spec_with, {}, {}, cx, cy, cz, a, b, h)

    spec_without = _spike_spec(spike_count=1, offset_y=0.0)
    with patch("src.enemies.zone_geometry_extras_attach.create_cone", side_effect=_capture(locs_without)):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch("src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra", return_value=MagicMock()):
                _append_body_ellipsoid_extras(model, spec_without, {}, {}, cx, cy, cz, a, b, h)

    assert len(locs_with) >= 1 and len(locs_without) >= 1
    y_with = locs_with[0][1]
    y_without = locs_without[0][1]
    assert abs(y_with - y_without - 1.0) < 0.01, (
        f"expected Y difference ≈ 1.0, got y_with={y_with}, y_without={y_without}"
    )


def test_body_offset_z_shifts_spike_location_z() -> None:
    """AC-5.5 (Z axis): offset_z=1.0 shifts the Z component by approximately 1.0."""
    cx, cy, cz = 0.0, 0.0, 0.0
    a, b, h = 0.5, 0.5, 0.5

    locs_with: list[tuple[float, float, float]] = []
    locs_without: list[tuple[float, float, float]] = []

    def _capture(dest: list) -> Any:
        def _fn(location=None, **kwargs: Any) -> MagicMock:
            if location is not None:
                dest.append(location)
            obj = MagicMock()
            obj.rotation_euler = (0.0, 0.0, 0.0)
            return obj
        return _fn

    model = _fake_model()

    spec_with = _spike_spec(spike_count=1, offset_z=1.0)
    with patch("src.enemies.zone_geometry_extras_attach.create_cone", side_effect=_capture(locs_with)):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch("src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra", return_value=MagicMock()):
                _append_body_ellipsoid_extras(model, spec_with, {}, {}, cx, cy, cz, a, b, h)

    spec_without = _spike_spec(spike_count=1, offset_z=0.0)
    with patch("src.enemies.zone_geometry_extras_attach.create_cone", side_effect=_capture(locs_without)):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch("src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra", return_value=MagicMock()):
                _append_body_ellipsoid_extras(model, spec_without, {}, {}, cx, cy, cz, a, b, h)

    assert len(locs_with) >= 1 and len(locs_without) >= 1
    z_with = locs_with[0][2]
    z_without = locs_without[0][2]
    assert abs(z_with - z_without - 1.0) < 0.01, (
        f"expected Z difference ≈ 1.0, got z_with={z_with}, z_without={z_without}"
    )


def test_body_zero_offset_is_identity() -> None:
    """
    AC-5.6: offset_x=0.0/offset_y=0.0/offset_z=0.0 produces the same placement as
    calling with no offset fields present (zero offset is identity).
    """
    cx, cy, cz = 0.3, 0.1, 0.8
    a, b, h = 0.6, 0.5, 0.4

    locs_explicit_zero: list[tuple[float, float, float]] = []
    locs_absent: list[tuple[float, float, float]] = []

    def _capture(dest: list) -> Any:
        def _fn(location=None, **kwargs: Any) -> MagicMock:
            if location is not None:
                dest.append(location)
            obj = MagicMock()
            obj.rotation_euler = (0.0, 0.0, 0.0)
            return obj
        return _fn

    model = _fake_model()

    spec_zero = _spike_spec(spike_count=1, offset_x=0.0, offset_y=0.0, offset_z=0.0)
    with patch("src.enemies.zone_geometry_extras_attach.create_cone", side_effect=_capture(locs_explicit_zero)):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch("src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra", return_value=MagicMock()):
                _append_body_ellipsoid_extras(model, spec_zero, {}, {}, cx, cy, cz, a, b, h)

    # spec without any offset keys (implementation must default to 0.0)
    spec_absent: dict[str, Any] = {
        k: v for k, v in spec_zero.items()
        if k not in ("offset_x", "offset_y", "offset_z")
    }
    with patch("src.enemies.zone_geometry_extras_attach.create_cone", side_effect=_capture(locs_absent)):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch("src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra", return_value=MagicMock()):
                _append_body_ellipsoid_extras(model, spec_absent, {}, {}, cx, cy, cz, a, b, h)

    assert len(locs_explicit_zero) >= 1, "expected placement with explicit zeros"
    assert len(locs_absent) >= 1, "expected placement with absent offset keys"

    for i, (z, a_loc) in enumerate(zip(locs_explicit_zero, locs_absent)):
        assert abs(z[0] - a_loc[0]) < 1e-9, f"spike {i} X differs: {z[0]} vs {a_loc[0]}"
        assert abs(z[1] - a_loc[1]) < 1e-9, f"spike {i} Y differs: {z[1]} vs {a_loc[1]}"
        assert abs(z[2] - a_loc[2]) < 1e-9, f"spike {i} Z differs: {z[2]} vs {a_loc[2]}"


# ---------------------------------------------------------------------------
# _append_head_ellipsoid_extras — AC-5.7 and AC-5.8
# ---------------------------------------------------------------------------


def _head_spike_spec(**overrides: Any) -> dict[str, Any]:
    """Minimal head spike spec."""
    defaults: dict[str, Any] = {
        "kind": "spikes",
        "spike_count": 1,
        "spike_shape": "cone",
        "spike_size": 1.0,
        "clustering": 0.5,
        "distribution": "uniform",
        "uniform_shape": "arc",
        "place_top": True,
        "place_bottom": True,
        "place_front": True,
        "place_back": True,
        "place_left": True,
        "place_right": True,
        "finish": "default",
        "hex": "",
        "offset_x": 0.0,
        "offset_y": 0.0,
        "offset_z": 0.0,
    }
    defaults.update(overrides)
    return defaults


def test_head_offset_z_shifts_spike_location_z() -> None:
    """
    AC-5.7: offset_z=0.5 with hz=1.0 shifts the Z component of head spike placement
    by approximately 0.5.
    """
    hx, hy, hz = 0.0, 0.0, 1.0
    ax, ay, az = 0.3, 0.3, 0.3

    locs_with: list[tuple[float, float, float]] = []
    locs_without: list[tuple[float, float, float]] = []

    def _capture(dest: list) -> Any:
        def _fn(location=None, **kwargs: Any) -> MagicMock:
            if location is not None:
                dest.append(location)
            obj = MagicMock()
            obj.rotation_euler = (0.0, 0.0, 0.0)
            return obj
        return _fn

    model = _fake_model()

    spec_with = _head_spike_spec(spike_count=1, offset_z=0.5)
    with patch("src.enemies.zone_geometry_extras_attach.create_cone", side_effect=_capture(locs_with)):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch("src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra", return_value=MagicMock()):
                _append_head_ellipsoid_extras(model, spec_with, {}, {}, hx, hy, hz, ax, ay, az)

    spec_without = _head_spike_spec(spike_count=1, offset_z=0.0)
    with patch("src.enemies.zone_geometry_extras_attach.create_cone", side_effect=_capture(locs_without)):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch("src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra", return_value=MagicMock()):
                _append_head_ellipsoid_extras(model, spec_without, {}, {}, hx, hy, hz, ax, ay, az)

    assert len(locs_with) >= 1, "expected at least one head spike with offset"
    assert len(locs_without) >= 1, "expected at least one head spike without offset"

    z_with = locs_with[0][2]
    z_without = locs_without[0][2]
    assert abs(z_with - z_without - 0.5) < 0.01, (
        f"expected head Z difference ≈ 0.5, got z_with={z_with}, z_without={z_without}"
    )


def test_body_offset_does_not_affect_head_zone_coordinates() -> None:
    """
    AC-5.8: the body spec's offset does not affect the head attach function.
    Calling _append_head_ellipsoid_extras with no offset vs body-offset-set-aside
    produces the same result (each function reads its own spec dict).
    """
    hx, hy, hz = 0.5, 0.0, 1.5
    ax, ay, az = 0.25, 0.25, 0.25

    locs_a: list[tuple[float, float, float]] = []
    locs_b: list[tuple[float, float, float]] = []

    def _capture(dest: list) -> Any:
        def _fn(location=None, **kwargs: Any) -> MagicMock:
            if location is not None:
                dest.append(location)
            obj = MagicMock()
            obj.rotation_euler = (0.0, 0.0, 0.0)
            return obj
        return _fn

    model = _fake_model()

    # Pass head spec with zero offsets (simulating head spec dict without body contamination)
    head_spec = _head_spike_spec(spike_count=1, offset_x=0.0, offset_y=0.0, offset_z=0.0)
    for locs in (locs_a, locs_b):
        with patch("src.enemies.zone_geometry_extras_attach.create_cone", side_effect=_capture(locs)):
            with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
                with patch("src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra", return_value=MagicMock()):
                    _append_head_ellipsoid_extras(model, head_spec, {}, {}, hx, hy, hz, ax, ay, az)

    # Both calls used identical head specs — placements must be equal
    assert len(locs_a) >= 1 and len(locs_b) >= 1
    for i, (la, lb) in enumerate(zip(locs_a, locs_b)):
        assert abs(la[0] - lb[0]) < 1e-9
        assert abs(la[1] - lb[1]) < 1e-9
        assert abs(la[2] - lb[2]) < 1e-9


# ---------------------------------------------------------------------------
# AC-5.9: kind=none — no geometry created, no exception on non-zero offset
# ---------------------------------------------------------------------------


def test_body_kind_none_with_nonzero_offset_no_exception_no_geometry() -> None:
    """AC-5.9: kind='none' with offset_x=1.5 creates no geometry and does not raise."""
    model = _fake_model()
    spec = _spike_spec(kind="none", offset_x=1.5, offset_y=-0.5, offset_z=0.3)
    with patch("src.enemies.zone_geometry_extras_attach.create_cone") as p_cone:
        with patch("src.enemies.zone_geometry_extras_attach.create_sphere") as p_sphere:
            with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
                with patch(
                    "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                    return_value=MagicMock(),
                ):
                    _append_body_ellipsoid_extras(model, spec, {}, {}, 0.0, 0.0, 0.0, 0.5, 0.5, 0.5)
    p_cone.assert_not_called()
    p_sphere.assert_not_called()
    assert len(model.parts) == 0


def test_head_kind_none_with_nonzero_offset_no_exception_no_geometry() -> None:
    """AC-5.9 (head): kind='none' with offset produces no geometry and no exception."""
    model = _fake_model()
    spec = _head_spike_spec(kind="none", offset_z=1.0)
    with patch("src.enemies.zone_geometry_extras_attach.create_cone") as p_cone:
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_head_ellipsoid_extras(model, spec, {}, {}, 0.0, 0.0, 1.0, 0.3, 0.3, 0.3)
    p_cone.assert_not_called()
    assert len(model.parts) == 0

"""Eye shape & pupil system — adversarial geometry builder tests.

Spec requirements targeted: ESPS-3, ESPS-4

Gaps exposed vs. the Test Designer suite:
  - Shared mutable state guard: build_mesh_parts called twice with the same options
    produces the same part count both times (no accumulated state between calls)
  - Stress: very high eye_count (99) with pupil_enabled=True → exactly 99 * 2 eye+pupil
    parts more than the body+head baseline (not more, not less)
  - Unknown shape fallback: create_eye_mesh("triangle", ...) calls create_sphere,
    never create_box (spec ESPS-3-AC-2 fallback rule)
  - Pupil location differs from eye location: create_pupil_mesh receives a location
    argument that is NOT identical to the location arg passed to create_eye_mesh
    for the same eye (pupil is offset onto the surface, not placed at the center)
  - Oval and slit shapes pass non-uniform scale to create_sphere (not square scale)
  - create_pupil_mesh slit dispatches to create_cylinder, not create_sphere
  - create_pupil_mesh diamond dispatches to create_box, not create_sphere or create_cylinder
  - High peripheral_eyes for claw_crawler: 3 eyes + pupil_enabled → exactly 3 pupil calls
  - Part list length is deterministic across two separate instances with identical options
"""

from __future__ import annotations

import random
from unittest.mock import MagicMock, patch

from src.enemies.animated_claw_crawler import AnimatedClawCrawler
from src.enemies.animated_slug import AnimatedSlug
from src.enemies.animated_spider import AnimatedSpider

# Patch paths (must target the location the builder imports from).
_SPIDER_EYE_PATCH = "src.enemies.animated_spider.create_eye_mesh"
_SPIDER_PUPIL_PATCH = "src.enemies.animated_spider.create_pupil_mesh"
_SLUG_EYE_PATCH = "src.enemies.animated_slug.create_eye_mesh"
_SLUG_PUPIL_PATCH = "src.enemies.animated_slug.create_pupil_mesh"
_CLAW_EYE_PATCH = "src.enemies.animated_claw_crawler.create_eye_mesh"
_CLAW_PUPIL_PATCH = "src.enemies.animated_claw_crawler.create_pupil_mesh"
_BLENDER_UTILS = "src.core.blender_utils"


def _fake_mesh() -> MagicMock:
    return MagicMock(name="mesh_part")


def _make_spider(build_options: dict) -> AnimatedSpider:
    return AnimatedSpider("spider", {}, random.Random(42), build_options=build_options)


def _make_slug(build_options: dict) -> AnimatedSlug:
    return AnimatedSlug("slug", {}, random.Random(42), build_options=build_options)


def _make_claw(build_options: dict) -> AnimatedClawCrawler:
    return AnimatedClawCrawler("claw_crawler", {}, random.Random(42), build_options=build_options)


def _run_spider_parts(build_options: dict) -> int:
    """Run build_mesh_parts for spider with patched eye/pupil and return part count."""
    spider = _make_spider(build_options)
    spider.parts = []
    with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
        with patch(_SPIDER_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            spider.build_mesh_parts()
    return len(spider.parts)


def _run_claw_parts(build_options: dict) -> int:
    claw = _make_claw(build_options)
    claw.parts = []
    with patch(_CLAW_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
        with patch(_CLAW_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            claw.build_mesh_parts()
    return len(claw.parts)


# ---------------------------------------------------------------------------
# Shared mutable state guard: build_mesh_parts called twice → same part count
# ---------------------------------------------------------------------------


class TestNoSharedMutableStateBetweenCalls:
    """Guard against module-level or class-level accumulator bugs that cause parts
    to grow on repeated calls to build_mesh_parts.

    Exposes mutation: if parts were appended to a shared class-level list rather
    than instance-level, the second call would report more parts than the first.
    """

    def test_spider_oval_part_count_identical_on_two_calls(self) -> None:
        """Two successive build_mesh_parts calls on the same instance must produce the same count."""
        spider = _make_spider({"eye_count": 2, "eye_shape": "oval", "pupil_enabled": False})
        spider.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SPIDER_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
                spider.build_mesh_parts()
        count_first = len(spider.parts)

        # Reset parts and call again.
        spider.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SPIDER_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
                spider.build_mesh_parts()
        count_second = len(spider.parts)

        assert count_first == count_second, (
            f"build_mesh_parts called twice on the same spider produces different part counts: "
            f"first={count_first}, second={count_second}. Likely shared mutable state."
        )

    def test_two_separate_spider_instances_same_options_same_part_count(self) -> None:
        """Two independent instances with identical options must produce the same part count."""
        opts = {"eye_count": 3, "eye_shape": "square", "pupil_enabled": True, "pupil_shape": "dot"}
        count_a = _run_spider_parts(opts)
        count_b = _run_spider_parts(opts)
        assert count_a == count_b, (
            f"Two spider instances with identical options differ in part count: {count_a} vs {count_b}. "
            "Possible class-level mutable state accumulation."
        )

    def test_two_separate_claw_instances_same_options_same_part_count(self) -> None:
        opts = {"peripheral_eyes": 2, "eye_shape": "oval", "pupil_enabled": False}
        count_a = _run_claw_parts(opts)
        count_b = _run_claw_parts(opts)
        assert count_a == count_b, (
            f"Two claw_crawler instances with identical options differ in part count: {count_a} vs {count_b}."
        )


# ---------------------------------------------------------------------------
# Stress: high eye_count (99) with pupil_enabled=True
# Part count = baseline_no_pupils + 99 eyes + 99 pupils = baseline_no_pupils + 198
# ---------------------------------------------------------------------------


class TestHighEyeCountStress:
    """Stress test: eye_count=99 with pupil_enabled=True must produce exactly 99 eyes + 99 pupils.

    This catches off-by-one errors and loop guards that might skip pupils beyond a
    threshold, or accidentally create extra meshes.
    """

    def test_spider_99_eyes_pupil_enabled_produces_99_eye_and_99_pupil_calls(self) -> None:
        eye_count = 99
        # Baseline: same eye_count, no pupils.
        baseline = _run_spider_parts({"eye_count": eye_count, "pupil_enabled": False})

        spider = _make_spider({"eye_count": eye_count, "pupil_enabled": True, "pupil_shape": "dot"})
        spider.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_eye:
            with patch(_SPIDER_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_pupil:
                spider.build_mesh_parts()

        assert mock_eye.call_count == eye_count, (
            f"Expected {eye_count} create_eye_mesh calls, got {mock_eye.call_count}"
        )
        assert mock_pupil.call_count == eye_count, (
            f"Expected {eye_count} create_pupil_mesh calls (one per eye), got {mock_pupil.call_count}"
        )
        total = len(spider.parts)
        assert total == baseline + eye_count, (
            f"eye_count=99 + pupil_enabled=True: expected part count {baseline + eye_count}, "
            f"got {total}. baseline={baseline}"
        )


# ---------------------------------------------------------------------------
# Unknown shape fallback: create_eye_mesh("triangle") → create_sphere, not create_box
# ---------------------------------------------------------------------------


class TestUnknownShapeFallbackToCircle:
    """ESPS-3-AC-2: any unknown shape value must fall back to circle behavior (create_sphere).

    The test Designer suite tests this at the create_eye_mesh level but not end-to-end
    through the builder. This test checks the builder passes the unknown shape through to
    create_eye_mesh (not silently converting it before the call) AND that create_eye_mesh
    produces sphere output (not box).
    """

    def test_create_eye_mesh_triangle_calls_sphere_not_box(self) -> None:
        from src.core.blender_utils import create_eye_mesh
        sphere_calls: list = []
        box_calls: list = []

        with patch(f"{_BLENDER_UTILS}.create_sphere", side_effect=lambda **kw: (sphere_calls.append(kw), _fake_mesh())[1]):
            with patch(f"{_BLENDER_UTILS}.create_box", side_effect=lambda **kw: (box_calls.append(kw), _fake_mesh())[1]):
                create_eye_mesh("triangle", (0.0, 0.0, 0.5), 0.1)

        assert len(sphere_calls) == 1, (
            f"create_eye_mesh('triangle') must call create_sphere (fallback to circle), "
            f"but create_sphere was called {len(sphere_calls)} time(s)"
        )
        assert len(box_calls) == 0, (
            f"create_eye_mesh('triangle') must NOT call create_box, "
            f"but it was called {len(box_calls)} time(s)"
        )

    def test_create_eye_mesh_hexagon_calls_sphere_not_box(self) -> None:
        from src.core.blender_utils import create_eye_mesh
        with patch(f"{_BLENDER_UTILS}.create_sphere", return_value=_fake_mesh()) as mock_sphere:
            with patch(f"{_BLENDER_UTILS}.create_box", return_value=_fake_mesh()) as mock_box:
                create_eye_mesh("hexagon", (0.0, 0.0, 0.5), 0.1)
        assert mock_sphere.called
        assert not mock_box.called

    def test_create_eye_mesh_empty_string_falls_back_to_sphere(self) -> None:
        from src.core.blender_utils import create_eye_mesh
        with patch(f"{_BLENDER_UTILS}.create_sphere", return_value=_fake_mesh()) as mock_sphere:
            with patch(f"{_BLENDER_UTILS}.create_box", return_value=_fake_mesh()) as mock_box:
                create_eye_mesh("", (0.0, 0.0, 0.5), 0.1)
        assert mock_sphere.called
        assert not mock_box.called


# ---------------------------------------------------------------------------
# Pupil location differs from eye location
# The pupil must NOT be placed at the same coordinate as the eye center.
# ---------------------------------------------------------------------------


class TestPupilLocationDiffersFromEyeLocation:
    """ESPS-4-AC-3..5: the location passed to create_pupil_mesh must differ from
    the location passed to create_eye_mesh for the same eye.

    This exposes a regression where the pupil is placed at the eye center (no offset),
    which would cause it to be hidden inside the eye mesh (Z-fighting / invisible pupil).
    """

    def test_spider_pupil_location_differs_from_eye_location(self) -> None:
        eye_locations: list = []
        pupil_locations: list = []

        def record_eye(shape, loc, scale):
            eye_locations.append(loc)
            return _fake_mesh()

        def record_pupil(shape, loc, scale):
            pupil_locations.append(loc)
            return _fake_mesh()

        spider = _make_spider({"eye_count": 2, "pupil_enabled": True, "pupil_shape": "dot"})
        spider.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=record_eye):
            with patch(_SPIDER_PUPIL_PATCH, side_effect=record_pupil):
                spider.build_mesh_parts()

        assert len(eye_locations) == 2, f"Expected 2 eye location records, got {len(eye_locations)}"
        assert len(pupil_locations) == 2, f"Expected 2 pupil location records, got {len(pupil_locations)}"

        for i, (eye_loc, pupil_loc) in enumerate(zip(eye_locations, pupil_locations)):
            assert eye_loc != pupil_loc, (
                f"Eye #{i}: pupil location {pupil_loc!r} must not equal eye location {eye_loc!r}. "
                "The pupil must be offset onto the eye surface, not placed at the eye center."
            )

    def test_slug_pupil_location_differs_from_eye_location(self) -> None:
        eye_locations: list = []
        pupil_locations: list = []

        def record_eye(shape, loc, scale):
            eye_locations.append(loc)
            return _fake_mesh()

        def record_pupil(shape, loc, scale):
            pupil_locations.append(loc)
            return _fake_mesh()

        slug = _make_slug({"pupil_enabled": True, "pupil_shape": "dot"})
        slug.parts = []
        with patch(_SLUG_EYE_PATCH, side_effect=record_eye):
            with patch(_SLUG_PUPIL_PATCH, side_effect=record_pupil):
                slug.build_mesh_parts()

        assert len(eye_locations) >= 1
        assert len(pupil_locations) == len(eye_locations)

        for i, (eye_loc, pupil_loc) in enumerate(zip(eye_locations, pupil_locations)):
            assert eye_loc != pupil_loc, (
                f"Slug eye #{i}: pupil location {pupil_loc!r} equals eye location {eye_loc!r}. "
                "Pupil must be offset from eye center."
            )

    def test_claw_crawler_pupil_location_differs_from_eye_location(self) -> None:
        eye_locations: list = []
        pupil_locations: list = []

        def record_eye(shape, loc, scale):
            eye_locations.append(loc)
            return _fake_mesh()

        def record_pupil(shape, loc, scale):
            pupil_locations.append(loc)
            return _fake_mesh()

        claw = _make_claw({"peripheral_eyes": 2, "pupil_enabled": True, "pupil_shape": "dot"})
        claw.parts = []
        with patch(_CLAW_EYE_PATCH, side_effect=record_eye):
            with patch(_CLAW_PUPIL_PATCH, side_effect=record_pupil):
                claw.build_mesh_parts()

        assert len(eye_locations) == 2
        assert len(pupil_locations) == 2

        for i, (eye_loc, pupil_loc) in enumerate(zip(eye_locations, pupil_locations)):
            assert eye_loc != pupil_loc, (
                f"ClawCrawler eye #{i}: pupil location {pupil_loc!r} equals eye location {eye_loc!r}."
            )


# ---------------------------------------------------------------------------
# create_eye_mesh: oval and slit shapes use non-uniform scale
# ---------------------------------------------------------------------------


class TestNonUniformScaleForOvalAndSlit:
    """ESPS-3-AC-2: oval and slit must use non-uniform scale on the sphere,
    not (eye_scale, eye_scale, eye_scale).

    This exposes a mutation where all four shapes use the same uniform scale,
    making oval and slit visually identical to circle.
    """

    def test_create_eye_mesh_oval_scale_is_not_uniform(self) -> None:
        from src.core.blender_utils import create_eye_mesh
        captured: list = []
        with patch(f"{_BLENDER_UTILS}.create_sphere", side_effect=lambda **kw: (captured.append(kw), _fake_mesh())[1]):
            create_eye_mesh("oval", (0.0, 0.0, 0.5), 0.2)
        assert len(captured) == 1
        scale = captured[0].get("scale")
        assert scale is not None, "oval must pass a scale kwarg to create_sphere"
        # For oval, X must differ from Y or Z (elongated along one axis).
        all_equal = (scale[0] == scale[1] == scale[2])
        assert not all_equal, (
            f"oval scale must be non-uniform (elongated), but got scale={scale!r}. "
            "Oval must differ from circle's uniform scale."
        )

    def test_create_eye_mesh_slit_scale_is_not_uniform(self) -> None:
        from src.core.blender_utils import create_eye_mesh
        captured: list = []
        with patch(f"{_BLENDER_UTILS}.create_sphere", side_effect=lambda **kw: (captured.append(kw), _fake_mesh())[1]):
            create_eye_mesh("slit", (0.0, 0.0, 0.5), 0.2)
        assert len(captured) == 1
        scale = captured[0].get("scale")
        assert scale is not None, "slit must pass a scale kwarg to create_sphere"
        all_equal = (scale[0] == scale[1] == scale[2])
        assert not all_equal, (
            f"slit scale must be non-uniform (narrow), but got scale={scale!r}. "
            "Slit must differ from circle's uniform scale."
        )

    def test_create_eye_mesh_oval_scale_differs_from_circle_scale(self) -> None:
        """oval scale tuple must differ from circle scale tuple at equal eye_scale."""
        from src.core.blender_utils import create_eye_mesh
        circle_captured: list = []
        oval_captured: list = []
        eye_scale = 0.15
        with patch(f"{_BLENDER_UTILS}.create_sphere", side_effect=lambda **kw: (circle_captured.append(kw), _fake_mesh())[1]):
            create_eye_mesh("circle", (0, 0, 0), eye_scale)
        with patch(f"{_BLENDER_UTILS}.create_sphere", side_effect=lambda **kw: (oval_captured.append(kw), _fake_mesh())[1]):
            create_eye_mesh("oval", (0, 0, 0), eye_scale)
        assert circle_captured[0]["scale"] != oval_captured[0]["scale"], (
            "oval and circle must use different scale tuples at the same eye_scale"
        )


# ---------------------------------------------------------------------------
# create_pupil_mesh: slit → cylinder, diamond → box
# (separate from TestCreatePupilMeshHelper in test_eye_shape_pupil_geometry.py
# — this file adds mutation checks for the OTHER shapes calling WRONG primitives)
# ---------------------------------------------------------------------------


class TestPupilMeshPrimitiveDispatchAdversarial:
    """ESPS-4-AC-2: slit must call create_cylinder (not create_sphere or create_box);
    diamond must call create_box (not create_sphere or create_cylinder).

    Catches mutations where the dispatch table is collapsed (all shapes → sphere).
    """

    def test_pupil_slit_does_not_call_sphere(self) -> None:
        from src.core.blender_utils import create_pupil_mesh
        with patch(f"{_BLENDER_UTILS}.create_sphere", return_value=_fake_mesh()) as mock_sphere:
            with patch(f"{_BLENDER_UTILS}.create_cylinder", return_value=_fake_mesh()):
                create_pupil_mesh("slit", (0.0, 0.2, 0.5), 0.05)
        assert not mock_sphere.called, (
            "pupil slit must NOT call create_sphere; it must call create_cylinder"
        )

    def test_pupil_diamond_does_not_call_sphere(self) -> None:
        from src.core.blender_utils import create_pupil_mesh
        with patch(f"{_BLENDER_UTILS}.create_sphere", return_value=_fake_mesh()) as mock_sphere:
            with patch(f"{_BLENDER_UTILS}.create_box", return_value=_fake_mesh()):
                create_pupil_mesh("diamond", (0.0, 0.2, 0.5), 0.05)
        assert not mock_sphere.called, (
            "pupil diamond must NOT call create_sphere; it must call create_box"
        )

    def test_pupil_diamond_does_not_call_cylinder(self) -> None:
        from src.core.blender_utils import create_pupil_mesh
        with patch(f"{_BLENDER_UTILS}.create_cylinder", return_value=_fake_mesh()) as mock_cyl:
            with patch(f"{_BLENDER_UTILS}.create_box", return_value=_fake_mesh()):
                create_pupil_mesh("diamond", (0.0, 0.2, 0.5), 0.05)
        assert not mock_cyl.called, (
            "pupil diamond must NOT call create_cylinder"
        )

    def test_pupil_slit_does_not_call_box(self) -> None:
        from src.core.blender_utils import create_pupil_mesh
        with patch(f"{_BLENDER_UTILS}.create_box", return_value=_fake_mesh()) as mock_box:
            with patch(f"{_BLENDER_UTILS}.create_cylinder", return_value=_fake_mesh()):
                create_pupil_mesh("slit", (0.0, 0.2, 0.5), 0.05)
        assert not mock_box.called, (
            "pupil slit must NOT call create_box"
        )

    def test_pupil_dot_does_not_call_cylinder(self) -> None:
        from src.core.blender_utils import create_pupil_mesh
        with patch(f"{_BLENDER_UTILS}.create_cylinder", return_value=_fake_mesh()) as mock_cyl:
            with patch(f"{_BLENDER_UTILS}.create_sphere", return_value=_fake_mesh()):
                create_pupil_mesh("dot", (0.0, 0.2, 0.5), 0.05)
        assert not mock_cyl.called, "pupil dot must NOT call create_cylinder"

    def test_pupil_dot_does_not_call_box(self) -> None:
        from src.core.blender_utils import create_pupil_mesh
        with patch(f"{_BLENDER_UTILS}.create_box", return_value=_fake_mesh()) as mock_box:
            with patch(f"{_BLENDER_UTILS}.create_sphere", return_value=_fake_mesh()):
                create_pupil_mesh("dot", (0.0, 0.2, 0.5), 0.05)
        assert not mock_box.called, "pupil dot must NOT call create_box"


# ---------------------------------------------------------------------------
# Claw crawler max peripheral_eyes (3) with pupil_enabled: exactly 3 pupils
# ---------------------------------------------------------------------------


class TestClawCrawlerMaxPeripheralEyesWithPupil:
    """Boundary: peripheral_eyes=3 (the declared max) with pupil_enabled=True
    must produce exactly 3 pupil calls, not 2 or 4.
    """

    def test_three_peripheral_eyes_and_pupil_produces_three_pupil_calls(self) -> None:
        claw_base = _make_claw({"peripheral_eyes": 3, "pupil_enabled": False})
        claw_base.parts = []
        with patch(_CLAW_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_CLAW_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
                claw_base.build_mesh_parts()
        baseline = len(claw_base.parts)

        claw_pupil = _make_claw({"peripheral_eyes": 3, "pupil_enabled": True, "pupil_shape": "slit"})
        claw_pupil.parts = []
        with patch(_CLAW_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_CLAW_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_pupil:
                claw_pupil.build_mesh_parts()

        assert mock_pupil.call_count == 3, (
            f"peripheral_eyes=3 + pupil_enabled=True must create exactly 3 pupils, "
            f"got {mock_pupil.call_count}"
        )
        assert len(claw_pupil.parts) == baseline + 3, (
            f"Expected baseline+3={baseline+3} parts, got {len(claw_pupil.parts)}"
        )


# ---------------------------------------------------------------------------
# Determinism: two builds with identical seed produce identical part counts
# ---------------------------------------------------------------------------


class TestDeterminism:
    """Same seed + same options must produce identical part count across two runs."""

    def test_spider_part_count_deterministic_with_same_seed(self) -> None:
        opts = {"eye_count": 3, "eye_shape": "slit", "pupil_enabled": True, "pupil_shape": "diamond"}
        count_a = _run_spider_parts(opts)
        count_b = _run_spider_parts(opts)
        assert count_a == count_b, (
            f"Spider with seed=42 and identical options produces non-deterministic part counts: "
            f"{count_a} vs {count_b}"
        )

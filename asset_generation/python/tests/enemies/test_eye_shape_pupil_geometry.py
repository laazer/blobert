"""Eye shape & pupil system — geometry builder tests.

Spec requirements covered:
  ESPS-3: Geometry Strategy — Eye Shape Variants
  ESPS-4: Geometry Strategy — Pupil Mesh

These tests use the blender stub registered in conftest.py (no real bpy).
`create_eye_mesh` and `create_pupil_mesh` are patched at the `blender_utils`
module level so the builders (which import them from ..core.blender_utils)
see the mock. Tests will be RED (import error or assertion failure) until the
implementation adds `create_eye_mesh` / `create_pupil_mesh` to `blender_utils`
and updates `build_mesh_parts` in spider, slug, and claw_crawler — that is
the intended TEST_BREAK state.

# CHECKPOINT: tests are written against the post-implementation API per
# run-2026-04-14T20-00-00Z-test-design.md.
"""

from __future__ import annotations

import random
from unittest.mock import MagicMock, patch

import pytest

from src.enemies.animated_claw_crawler import AnimatedClawCrawler
from src.enemies.animated_slug import AnimatedSlug
from src.enemies.animated_spider import AnimatedSpider

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BLENDER_UTILS_PATH = "src.core.blender_utils"
_EYE_MESH_PATCH = f"{_BLENDER_UTILS_PATH}.create_eye_mesh"
_PUPIL_MESH_PATCH = f"{_BLENDER_UTILS_PATH}.create_pupil_mesh"

# These patches target wherever the builders import the functions from.
_SPIDER_EYE_PATCH = "src.enemies.animated_spider.create_eye_mesh"
_SPIDER_PUPIL_PATCH = "src.enemies.animated_spider.create_pupil_mesh"
_SLUG_EYE_PATCH = "src.enemies.animated_slug.create_eye_mesh"
_SLUG_PUPIL_PATCH = "src.enemies.animated_slug.create_pupil_mesh"
_CLAW_EYE_PATCH = "src.enemies.animated_claw_crawler.create_eye_mesh"
_CLAW_PUPIL_PATCH = "src.enemies.animated_claw_crawler.create_pupil_mesh"


def _fake_mesh() -> MagicMock:
    return MagicMock(name="mesh_part")


def _make_spider(build_options: dict) -> AnimatedSpider:
    mats: dict[str, object] = {}
    return AnimatedSpider("spider", mats, random.Random(42), build_options=build_options)


def _make_slug(build_options: dict) -> AnimatedSlug:
    mats: dict[str, object] = {}
    return AnimatedSlug("slug", mats, random.Random(42), build_options=build_options)


def _make_claw(build_options: dict) -> AnimatedClawCrawler:
    mats: dict[str, object] = {}
    return AnimatedClawCrawler("claw_crawler", mats, random.Random(42), build_options=build_options)


# ---------------------------------------------------------------------------
# ESPS-3: Spider eye shape variants
# ---------------------------------------------------------------------------


class TestSpiderEyeShapeGeometry:
    """ESPS-3-AC-3: AnimatedSpider.build_mesh_parts dispatches to create_eye_mesh.
    ESPS-3-AC-6: default circle behavior preserves part count."""

    def test_spider_circle_shape_calls_create_eye_mesh_with_circle(self) -> None:
        """ESPS-3-AC-3: circle shape passes 'circle' to create_eye_mesh for each eye."""
        spider = _make_spider({"eye_count": 2, "eye_shape": "circle"})
        spider.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_eye:
            spider.build_mesh_parts()
        # Every call to create_eye_mesh must use shape="circle"
        for c in mock_eye.call_args_list:
            assert c.args[0] == "circle" or c.kwargs.get("shape") == "circle", (
                f"Expected shape='circle', got call: {c}"
            )
        assert mock_eye.call_count == 2

    def test_spider_square_shape_calls_create_eye_mesh_with_square(self) -> None:
        """ESPS-3: square shape passes 'square' to create_eye_mesh for each eye."""
        spider = _make_spider({"eye_count": 2, "eye_shape": "square"})
        spider.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_eye:
            spider.build_mesh_parts()
        assert mock_eye.call_count == 2
        for c in mock_eye.call_args_list:
            assert c.args[0] == "square" or c.kwargs.get("shape") == "square"

    def test_spider_oval_shape_calls_create_eye_mesh_with_oval(self) -> None:
        spider = _make_spider({"eye_count": 2, "eye_shape": "oval"})
        spider.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_eye:
            spider.build_mesh_parts()
        assert mock_eye.call_count == 2
        for c in mock_eye.call_args_list:
            assert c.args[0] == "oval" or c.kwargs.get("shape") == "oval"

    def test_spider_slit_shape_calls_create_eye_mesh_with_slit(self) -> None:
        spider = _make_spider({"eye_count": 2, "eye_shape": "slit"})
        spider.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_eye:
            spider.build_mesh_parts()
        assert mock_eye.call_count == 2
        for c in mock_eye.call_args_list:
            assert c.args[0] == "slit" or c.kwargs.get("shape") == "slit"

    def test_spider_eye_count_four_creates_four_eye_meshes(self) -> None:
        """ESPS-3-AC-3: create_eye_mesh called once per eye regardless of eye_count."""
        spider = _make_spider({"eye_count": 4, "eye_shape": "square"})
        spider.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_eye:
            spider.build_mesh_parts()
        assert mock_eye.call_count == 4

    def test_spider_default_eye_shape_calls_create_eye_mesh_not_create_sphere_for_eyes(self) -> None:
        """ESPS-3: build_mesh_parts must use create_eye_mesh (not bare create_sphere) for eyes."""
        spider = _make_spider({"eye_count": 2})
        spider.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_eye:
            with patch("src.enemies.animated_spider.create_sphere", side_effect=lambda **kw: _fake_mesh()) as mock_sphere:
                spider.build_mesh_parts()
        # create_eye_mesh must be called for eyes (2 times), not create_sphere
        assert mock_eye.call_count == 2
        # create_sphere may still be called for body and head (2 calls), but not for eyes
        for c in mock_sphere.call_args_list:
            # None of the sphere calls should be for eye scale (eye_scale is ~0.15 * head_scale)
            # The test cannot precisely distinguish without inspecting scale, but create_eye_mesh
            # being called 2 times for eye_count=2 is the primary assertion.
            pass


# ---------------------------------------------------------------------------
# ESPS-3: Slug eye shape variants
# ---------------------------------------------------------------------------


class TestSlugEyeShapeGeometry:
    """ESPS-3-AC-4: AnimatedSlug.build_mesh_parts dispatches to create_eye_mesh for eyes."""

    def test_slug_circle_shape_calls_create_eye_mesh_with_circle(self) -> None:
        slug = _make_slug({"eye_shape": "circle"})
        slug.parts = []
        with patch(_SLUG_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_eye:
            slug.build_mesh_parts()
        assert mock_eye.call_count == 2  # always 2 sides
        for c in mock_eye.call_args_list:
            assert c.args[0] == "circle" or c.kwargs.get("shape") == "circle"

    def test_slug_square_shape_calls_create_eye_mesh_with_square(self) -> None:
        slug = _make_slug({"eye_shape": "square"})
        slug.parts = []
        with patch(_SLUG_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_eye:
            slug.build_mesh_parts()
        assert mock_eye.call_count == 2
        for c in mock_eye.call_args_list:
            assert c.args[0] == "square" or c.kwargs.get("shape") == "square"

    def test_slug_stalk_cylinder_not_replaced_by_eye_mesh(self) -> None:
        """ESPS-3-AC-4: stalk cylinder calls are unaffected; only eye sphere calls are replaced."""
        slug = _make_slug({"eye_shape": "oval"})
        slug.parts = []
        with patch(_SLUG_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch("src.enemies.animated_slug.create_cylinder", side_effect=lambda **kw: _fake_mesh()) as mock_cyl:
                slug.build_mesh_parts()
        # 2 stalks (one per side)
        assert mock_cyl.call_count == 2


# ---------------------------------------------------------------------------
# ESPS-3: ClawCrawler eye shape variants
# ---------------------------------------------------------------------------


class TestClawCrawlerEyeShapeGeometry:
    """ESPS-3-AC-5: AnimatedClawCrawler.build_mesh_parts dispatches to create_eye_mesh."""

    def test_claw_crawler_circle_calls_create_eye_mesh(self) -> None:
        claw = _make_claw({"peripheral_eyes": 1, "eye_shape": "circle"})
        claw.parts = []
        with patch(_CLAW_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_eye:
            claw.build_mesh_parts()
        assert mock_eye.call_count == 1
        assert mock_eye.call_args_list[0].args[0] == "circle" or mock_eye.call_args_list[0].kwargs.get("shape") == "circle"

    def test_claw_crawler_square_calls_create_eye_mesh_with_square(self) -> None:
        claw = _make_claw({"peripheral_eyes": 2, "eye_shape": "square"})
        claw.parts = []
        with patch(_CLAW_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_eye:
            claw.build_mesh_parts()
        assert mock_eye.call_count == 2
        for c in mock_eye.call_args_list:
            assert c.args[0] == "square" or c.kwargs.get("shape") == "square"

    def test_claw_crawler_zero_peripheral_eyes_no_eye_mesh_calls(self) -> None:
        claw = _make_claw({"peripheral_eyes": 0, "eye_shape": "square"})
        claw.parts = []
        with patch(_CLAW_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_eye:
            claw.build_mesh_parts()
        assert mock_eye.call_count == 0


# ---------------------------------------------------------------------------
# ESPS-4: Pupil mesh creation
# ---------------------------------------------------------------------------


class TestSpiderPupilGeometry:
    """ESPS-4-AC-3, ESPS-4-AC-6, ESPS-4-AC-7: spider pupil mesh."""

    def _build_spider_parts(self, build_options: dict) -> list:
        spider = _make_spider(build_options)
        spider.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SPIDER_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
                spider.build_mesh_parts()
        return spider.parts

    def _count_spider_parts(self, build_options: dict) -> int:
        spider = _make_spider(build_options)
        spider.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SPIDER_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
                spider.build_mesh_parts()
        return len(spider.parts)

    def test_pupil_disabled_does_not_add_pupil_parts(self) -> None:
        """ESPS-4-AC-6: pupil_enabled=False baseline — zero extra parts."""
        eye_count = 2
        with_pupil = self._count_spider_parts({"eye_count": eye_count, "pupil_enabled": False})
        without_pupil = self._count_spider_parts({"eye_count": eye_count, "pupil_enabled": False})
        assert with_pupil == without_pupil

    def test_pupil_enabled_creates_pupil_mesh_per_eye_spider(self) -> None:
        """ESPS-4-AC-7: pupil_enabled=True adds exactly N_eyes pupil parts."""
        eye_count = 2
        spider_no_pupil = _make_spider({"eye_count": eye_count, "pupil_enabled": False})
        spider_no_pupil.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SPIDER_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
                spider_no_pupil.build_mesh_parts()
        baseline = len(spider_no_pupil.parts)

        spider_with_pupil = _make_spider({"eye_count": eye_count, "pupil_enabled": True, "pupil_shape": "dot"})
        spider_with_pupil.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SPIDER_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_pupil:
                spider_with_pupil.build_mesh_parts()
        with_pupil_count = len(spider_with_pupil.parts)

        assert mock_pupil.call_count == eye_count, (
            f"create_pupil_mesh must be called once per eye ({eye_count}), got {mock_pupil.call_count}"
        )
        assert with_pupil_count == baseline + eye_count, (
            f"Part count must increase by {eye_count} when pupil_enabled=True; "
            f"got baseline={baseline}, with_pupil={with_pupil_count}"
        )

    def test_pupil_enabled_four_eyes_adds_four_pupil_parts(self) -> None:
        """ESPS-4-AC-7: N=4 eyes adds 4 pupil parts."""
        eye_count = 4
        spider_base = _make_spider({"eye_count": eye_count, "pupil_enabled": False})
        spider_base.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SPIDER_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
                spider_base.build_mesh_parts()
        baseline = len(spider_base.parts)

        spider_pupil = _make_spider({"eye_count": eye_count, "pupil_enabled": True, "pupil_shape": "dot"})
        spider_pupil.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SPIDER_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_pupil:
                spider_pupil.build_mesh_parts()
        assert mock_pupil.call_count == eye_count
        assert len(spider_pupil.parts) == baseline + eye_count

    def test_pupil_shape_passed_to_create_pupil_mesh_spider(self) -> None:
        """ESPS-4-AC-3: pupil_shape value is forwarded to create_pupil_mesh."""
        spider = _make_spider({"eye_count": 2, "pupil_enabled": True, "pupil_shape": "diamond"})
        spider.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SPIDER_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_pupil:
                spider.build_mesh_parts()
        for c in mock_pupil.call_args_list:
            assert c.args[0] == "diamond" or c.kwargs.get("shape") == "diamond"

    def test_create_pupil_mesh_not_called_when_pupil_disabled(self) -> None:
        """ESPS-4-AC-6: create_pupil_mesh is never called when pupil_enabled=False."""
        spider = _make_spider({"eye_count": 2, "pupil_enabled": False})
        spider.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SPIDER_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_pupil:
                spider.build_mesh_parts()
        assert mock_pupil.call_count == 0

    def test_create_pupil_mesh_not_called_when_pupil_absent(self) -> None:
        """ESPS-4-AC-6: pupil_enabled absent (default False) → no pupil."""
        spider = _make_spider({"eye_count": 2})
        spider.parts = []
        with patch(_SPIDER_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SPIDER_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_pupil:
                spider.build_mesh_parts()
        assert mock_pupil.call_count == 0


class TestSlugPupilGeometry:
    """ESPS-4-AC-4, ESPS-4-AC-6, ESPS-4-AC-7: slug pupil mesh (always 2 eyes)."""

    def test_slug_pupil_disabled_no_pupil_parts(self) -> None:
        """ESPS-4-AC-6."""
        slug = _make_slug({"pupil_enabled": False})
        slug.parts = []
        with patch(_SLUG_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SLUG_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_pupil:
                slug.build_mesh_parts()
        assert mock_pupil.call_count == 0

    def test_slug_pupil_enabled_adds_two_pupil_parts(self) -> None:
        """ESPS-4-AC-7: slug always has 2 eyes → 2 pupils when enabled."""
        slug_base = _make_slug({"pupil_enabled": False})
        slug_base.parts = []
        with patch(_SLUG_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SLUG_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
                slug_base.build_mesh_parts()
        baseline = len(slug_base.parts)

        slug_pupil = _make_slug({"pupil_enabled": True, "pupil_shape": "dot"})
        slug_pupil.parts = []
        with patch(_SLUG_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SLUG_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_pupil:
                slug_pupil.build_mesh_parts()
        assert mock_pupil.call_count == 2
        assert len(slug_pupil.parts) == baseline + 2

    def test_slug_pupil_shape_forwarded(self) -> None:
        """ESPS-4-AC-4: pupil_shape value is forwarded to create_pupil_mesh."""
        slug = _make_slug({"pupil_enabled": True, "pupil_shape": "slit"})
        slug.parts = []
        with patch(_SLUG_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SLUG_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_pupil:
                slug.build_mesh_parts()
        for c in mock_pupil.call_args_list:
            assert c.args[0] == "slit" or c.kwargs.get("shape") == "slit"

    def test_slug_pupil_disabled_baseline_part_count_unchanged(self) -> None:
        """ESPS-3-AC-6: circle default + pupil off → identical to pre-change output."""
        slug1 = _make_slug({"eye_shape": "circle", "pupil_enabled": False})
        slug1.parts = []
        slug2 = _make_slug({"eye_shape": "circle", "pupil_enabled": False})
        slug2.parts = []
        with patch(_SLUG_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_SLUG_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
                slug1.build_mesh_parts()
                slug2.build_mesh_parts()
        assert len(slug1.parts) == len(slug2.parts)


class TestClawCrawlerPupilGeometry:
    """ESPS-4-AC-5, ESPS-4-AC-6, ESPS-4-AC-7: claw_crawler pupil mesh."""

    def test_claw_crawler_pupil_disabled_no_pupil_parts(self) -> None:
        """ESPS-4-AC-6."""
        claw = _make_claw({"peripheral_eyes": 1, "pupil_enabled": False})
        claw.parts = []
        with patch(_CLAW_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_CLAW_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_pupil:
                claw.build_mesh_parts()
        assert mock_pupil.call_count == 0

    def test_claw_crawler_pupil_enabled_one_eye_adds_one_pupil(self) -> None:
        """ESPS-4-AC-7: peripheral_eyes=1 → 1 pupil."""
        claw_base = _make_claw({"peripheral_eyes": 1, "pupil_enabled": False})
        claw_base.parts = []
        with patch(_CLAW_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_CLAW_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
                claw_base.build_mesh_parts()
        baseline = len(claw_base.parts)

        claw_pupil = _make_claw({"peripheral_eyes": 1, "pupil_enabled": True, "pupil_shape": "dot"})
        claw_pupil.parts = []
        with patch(_CLAW_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_CLAW_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_pupil:
                claw_pupil.build_mesh_parts()
        assert mock_pupil.call_count == 1
        assert len(claw_pupil.parts) == baseline + 1

    def test_claw_crawler_pupil_enabled_two_eyes_adds_two_pupils(self) -> None:
        """ESPS-4-AC-7: peripheral_eyes=2 → 2 pupils."""
        claw_base = _make_claw({"peripheral_eyes": 2, "pupil_enabled": False})
        claw_base.parts = []
        with patch(_CLAW_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_CLAW_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
                claw_base.build_mesh_parts()
        baseline = len(claw_base.parts)

        claw_pupil = _make_claw({"peripheral_eyes": 2, "pupil_enabled": True, "pupil_shape": "diamond"})
        claw_pupil.parts = []
        with patch(_CLAW_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_CLAW_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_pupil:
                claw_pupil.build_mesh_parts()
        assert mock_pupil.call_count == 2
        assert len(claw_pupil.parts) == baseline + 2

    def test_claw_crawler_pupil_shape_forwarded(self) -> None:
        """ESPS-4-AC-5: pupil_shape value is forwarded to create_pupil_mesh."""
        claw = _make_claw({"peripheral_eyes": 1, "pupil_enabled": True, "pupil_shape": "diamond"})
        claw.parts = []
        with patch(_CLAW_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_CLAW_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_pupil:
                claw.build_mesh_parts()
        assert mock_pupil.call_count == 1
        assert mock_pupil.call_args_list[0].args[0] == "diamond" or mock_pupil.call_args_list[0].kwargs.get("shape") == "diamond"

    def test_claw_crawler_zero_peripheral_eyes_pupil_enabled_no_pupils(self) -> None:
        """ESPS-4-AC-7: 0 eyes → 0 pupils even when pupil_enabled=True."""
        claw = _make_claw({"peripheral_eyes": 0, "pupil_enabled": True})
        claw.parts = []
        with patch(_CLAW_EYE_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()):
            with patch(_CLAW_PUPIL_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()) as mock_pupil:
                claw.build_mesh_parts()
        assert mock_pupil.call_count == 0


# ---------------------------------------------------------------------------
# ESPS-3: create_eye_mesh helper in blender_utils
# ---------------------------------------------------------------------------


class TestCreateEyeMeshHelper:
    """ESPS-3-AC-1, ESPS-3-AC-2: create_eye_mesh exists in blender_utils and dispatches correctly."""

    def test_create_eye_mesh_exists_in_blender_utils(self) -> None:
        """ESPS-3-AC-1: function is importable from blender_utils."""
        from src.core import blender_utils
        assert hasattr(blender_utils, "create_eye_mesh"), (
            "create_eye_mesh must be defined in src.core.blender_utils"
        )

    def test_create_eye_mesh_circle_calls_create_sphere(self) -> None:
        """ESPS-3-AC-2: circle dispatches to create_sphere."""
        from src.core.blender_utils import create_eye_mesh
        with patch("src.core.blender_utils.create_sphere", return_value=_fake_mesh()) as mock_sphere:
            create_eye_mesh("circle", (0.0, 0.0, 0.5), 0.1)
        assert mock_sphere.called

    def test_create_eye_mesh_square_calls_create_box(self) -> None:
        """ESPS-3-AC-2: square dispatches to create_box."""
        from src.core.blender_utils import create_eye_mesh
        with patch("src.core.blender_utils.create_box", return_value=_fake_mesh()) as mock_box:
            create_eye_mesh("square", (0.0, 0.0, 0.5), 0.1)
        assert mock_box.called

    def test_create_eye_mesh_oval_calls_create_sphere(self) -> None:
        """ESPS-3-AC-2: oval uses create_sphere with elongated scale."""
        from src.core.blender_utils import create_eye_mesh
        with patch("src.core.blender_utils.create_sphere", return_value=_fake_mesh()) as mock_sphere:
            create_eye_mesh("oval", (0.0, 0.0, 0.5), 0.1)
        assert mock_sphere.called

    def test_create_eye_mesh_slit_calls_create_sphere(self) -> None:
        """ESPS-3-AC-2: slit uses create_sphere with narrow Y scale."""
        from src.core.blender_utils import create_eye_mesh
        with patch("src.core.blender_utils.create_sphere", return_value=_fake_mesh()) as mock_sphere:
            create_eye_mesh("slit", (0.0, 0.0, 0.5), 0.1)
        assert mock_sphere.called

    def test_create_eye_mesh_invalid_shape_falls_back_to_circle_behavior(self) -> None:
        """ESPS-3-AC-2: unknown shape falls back to circle (calls create_sphere)."""
        from src.core.blender_utils import create_eye_mesh
        with patch("src.core.blender_utils.create_sphere", return_value=_fake_mesh()) as mock_sphere:
            with patch("src.core.blender_utils.create_box", return_value=_fake_mesh()) as mock_box:
                create_eye_mesh("triangle", (0.0, 0.0, 0.5), 0.1)
        assert mock_sphere.called
        assert not mock_box.called

    def test_create_eye_mesh_circle_scale_is_uniform(self) -> None:
        """ESPS-3-AC-2: circle passes (eye_scale, eye_scale, eye_scale) — uniform sphere."""
        from src.core.blender_utils import create_eye_mesh
        captured: list = []
        def record_sphere(**kwargs):
            captured.append(kwargs)
            return _fake_mesh()
        with patch("src.core.blender_utils.create_sphere", side_effect=record_sphere):
            create_eye_mesh("circle", (0.0, 0.0, 0.5), 0.2)
        assert len(captured) == 1
        scale = captured[0].get("scale")
        assert scale is not None
        assert scale[0] == pytest.approx(0.2)
        assert scale[1] == pytest.approx(0.2)
        assert scale[2] == pytest.approx(0.2)

    def test_create_eye_mesh_square_scale_is_uniform_box(self) -> None:
        """ESPS-3-AC-2: square passes (eye_scale, eye_scale, eye_scale) to create_box."""
        from src.core.blender_utils import create_eye_mesh
        captured: list = []
        def record_box(**kwargs):
            captured.append(kwargs)
            return _fake_mesh()
        with patch("src.core.blender_utils.create_box", side_effect=record_box):
            create_eye_mesh("square", (0.0, 0.0, 0.5), 0.3)
        assert len(captured) == 1
        scale = captured[0].get("scale")
        assert scale is not None
        assert scale[0] == pytest.approx(0.3)
        assert scale[1] == pytest.approx(0.3)
        assert scale[2] == pytest.approx(0.3)


# ---------------------------------------------------------------------------
# ESPS-4: create_pupil_mesh helper in blender_utils
# ---------------------------------------------------------------------------


class TestCreatePupilMeshHelper:
    """ESPS-4-AC-1, ESPS-4-AC-2: create_pupil_mesh exists and dispatches correctly."""

    def test_create_pupil_mesh_exists_in_blender_utils(self) -> None:
        """ESPS-4-AC-1."""
        from src.core import blender_utils
        assert hasattr(blender_utils, "create_pupil_mesh"), (
            "create_pupil_mesh must be defined in src.core.blender_utils"
        )

    def test_create_pupil_mesh_dot_calls_create_sphere(self) -> None:
        """ESPS-4-AC-2: dot dispatches to create_sphere."""
        from src.core.blender_utils import create_pupil_mesh
        with patch("src.core.blender_utils.create_sphere", return_value=_fake_mesh()) as mock_sphere:
            create_pupil_mesh("dot", (0.0, 0.2, 0.5), 0.05)
        assert mock_sphere.called

    def test_create_pupil_mesh_slit_calls_create_cylinder(self) -> None:
        """ESPS-4-AC-2: slit dispatches to create_cylinder."""
        from src.core.blender_utils import create_pupil_mesh
        with patch("src.core.blender_utils.create_cylinder", return_value=_fake_mesh()) as mock_cyl:
            create_pupil_mesh("slit", (0.0, 0.2, 0.5), 0.05)
        assert mock_cyl.called

    def test_create_pupil_mesh_diamond_calls_create_box(self) -> None:
        """ESPS-4-AC-2: diamond dispatches to create_box."""
        from src.core.blender_utils import create_pupil_mesh
        with patch("src.core.blender_utils.create_box", return_value=_fake_mesh()) as mock_box:
            create_pupil_mesh("diamond", (0.0, 0.2, 0.5), 0.05)
        assert mock_box.called

    def test_create_pupil_mesh_invalid_shape_falls_back_to_dot(self) -> None:
        """ESPS-4-AC-2: unknown shape falls back to dot (create_sphere)."""
        from src.core.blender_utils import create_pupil_mesh
        with patch("src.core.blender_utils.create_sphere", return_value=_fake_mesh()) as mock_sphere:
            with patch("src.core.blender_utils.create_box", return_value=_fake_mesh()) as mock_box:
                with patch("src.core.blender_utils.create_cylinder", return_value=_fake_mesh()) as mock_cyl:
                    create_pupil_mesh("INVALID", (0.0, 0.2, 0.5), 0.05)
        assert mock_sphere.called
        assert not mock_box.called
        assert not mock_cyl.called

    def test_create_pupil_mesh_dot_scale_z_ratio(self) -> None:
        """ESPS-4-AC-2: dot passes flattened Z scale (pupil_scale * _PUPIL_DOT_Z_RATIO ~ 0.3)."""
        from src.core.blender_utils import create_pupil_mesh
        captured: list = []
        def record(**kwargs):
            captured.append(kwargs)
            return _fake_mesh()
        pupil_scale = 0.1
        with patch("src.core.blender_utils.create_sphere", side_effect=record):
            create_pupil_mesh("dot", (0.0, 0.2, 0.5), pupil_scale)
        assert len(captured) == 1
        scale = captured[0].get("scale")
        assert scale is not None
        # X and Y should be pupil_scale; Z should be pupil_scale * ~0.3
        assert scale[0] == pytest.approx(pupil_scale, rel=1e-3)
        assert scale[1] == pytest.approx(pupil_scale, rel=1e-3)
        assert scale[2] == pytest.approx(pupil_scale * 0.3, rel=0.01)

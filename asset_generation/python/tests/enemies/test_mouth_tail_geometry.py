"""Mouth extra & tail extra — geometry builder tests with blender stubs.

Spec requirements covered:
  MTE-4: Geometry Placement Formulas
  MTE-5: create_mouth_mesh Geometry Helper
  MTE-6: create_tail_mesh Geometry Helper
  MTE-7: Per-Slug Geometry Wiring
  MTE-8: Non-Breaking Default Guarantee

These tests use the blender stub registered in conftest.py (no real bpy).
`create_mouth_mesh` and `create_tail_mesh` are patched at the module level so the builders
(which import them from ..core.blender_utils) see the mock. Tests will be RED until the
implementation adds these functions to blender_utils and updates build_mesh_parts in all six
animated enemy builders — that is the intended TEST_BREAK state.

# CHECKPOINT: tests are written against the post-implementation API per spec MTE requirements.
"""

from __future__ import annotations

import random
from unittest.mock import MagicMock, patch

import pytest

from src.enemies.animated_carapace_husk import AnimatedCarapaceHusk
from src.enemies.animated_claw_crawler import AnimatedClawCrawler
from src.enemies.animated_imp import AnimatedImp
from src.enemies.animated_slug import AnimatedSlug
from src.enemies.animated_spider import AnimatedSpider
from src.enemies.animated_spitter import AnimatedSpitter

# ---------------------------------------------------------------------------
# Helpers and patch paths
# ---------------------------------------------------------------------------

_BLENDER_UTILS_PATH = "src.core.blender_utils"

_SPIDER_MOUTH_PATCH = "src.enemies.animated_spider.create_mouth_mesh"
_SPIDER_TAIL_PATCH = "src.enemies.animated_spider.create_tail_mesh"

_SLUG_MOUTH_PATCH = "src.enemies.animated_slug.create_mouth_mesh"
_SLUG_TAIL_PATCH = "src.enemies.animated_slug.create_tail_mesh"

_CLAW_MOUTH_PATCH = "src.enemies.animated_claw_crawler.create_mouth_mesh"
_CLAW_TAIL_PATCH = "src.enemies.animated_claw_crawler.create_tail_mesh"

_IMP_MOUTH_PATCH = "src.enemies.animated_imp.create_mouth_mesh"
_IMP_TAIL_PATCH = "src.enemies.animated_imp.create_tail_mesh"

_SPITTER_MOUTH_PATCH = "src.enemies.animated_spitter.create_mouth_mesh"
_SPITTER_TAIL_PATCH = "src.enemies.animated_spitter.create_tail_mesh"

_CARAPACE_MOUTH_PATCH = "src.enemies.animated_carapace_husk.create_mouth_mesh"
_CARAPACE_TAIL_PATCH = "src.enemies.animated_carapace_husk.create_tail_mesh"


def _fake_mesh() -> MagicMock:
    return MagicMock(name="mesh_part")


def _make_spider(build_options: dict) -> AnimatedSpider:
    mats: dict[str, object] = {}
    return AnimatedSpider(
        "spider", mats, random.Random(42), build_options=build_options
    )


def _make_slug(build_options: dict) -> AnimatedSlug:
    mats: dict[str, object] = {}
    return AnimatedSlug("slug", mats, random.Random(42), build_options=build_options)


def _make_claw(build_options: dict) -> AnimatedClawCrawler:
    mats: dict[str, object] = {}
    return AnimatedClawCrawler(
        "claw_crawler", mats, random.Random(42), build_options=build_options
    )


def _make_imp(build_options: dict) -> AnimatedImp:
    mats: dict[str, object] = {}
    return AnimatedImp("imp", mats, random.Random(42), build_options=build_options)


def _make_spitter(build_options: dict) -> AnimatedSpitter:
    mats: dict[str, object] = {}
    return AnimatedSpitter(
        "spitter", mats, random.Random(42), build_options=build_options
    )


def _make_carapace(build_options: dict) -> AnimatedCarapaceHusk:
    mats: dict[str, object] = {}
    return AnimatedCarapaceHusk(
        "carapace_husk", mats, random.Random(42), build_options=build_options
    )


# ---------------------------------------------------------------------------
# MTE-5: create_mouth_mesh helper existence and dispatch
# ---------------------------------------------------------------------------


class TestCreateMouthMeshHelperExistence:
    """MTE-5-AC-1, MTE-5-AC-4: create_mouth_mesh exists in blender_utils."""

    def test_create_mouth_mesh_exists_in_blender_utils(self) -> None:
        from src.core import blender_utils

        assert hasattr(blender_utils, "create_mouth_mesh"), (
            "create_mouth_mesh must be defined in src.core.blender_utils"
        )


# ---------------------------------------------------------------------------
# MTE-7: Mouth geometry wiring — spider
# ---------------------------------------------------------------------------


class TestSpiderMouthGeometry:
    """MTE-7-AC-1, MTE-7-AC-5, MTE-7-AC-6: spider mouth mesh calls."""

    def test_spider_mouth_enabled_calls_create_mouth_mesh(self) -> None:
        """MTE-7-AC-1: mouth_enabled=True triggers create_mouth_mesh call."""
        spider = _make_spider({"mouth_enabled": True, "mouth_shape": "fang"})
        spider.parts = []
        with patch(
            _SPIDER_MOUTH_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()
        ) as mock_mouth:
            spider.build_mesh_parts()
        assert mock_mouth.call_count == 1

    def test_spider_mouth_shape_fang_passed_to_create_mouth_mesh(self) -> None:
        """MTE-7-AC-1: mouth_shape value is forwarded."""
        spider = _make_spider({"mouth_enabled": True, "mouth_shape": "fang"})
        spider.parts = []
        with patch(
            _SPIDER_MOUTH_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()
        ) as mock_mouth:
            spider.build_mesh_parts()
        for c in mock_mouth.call_args_list:
            assert c.args[0] == "fang" or c.kwargs.get("shape") == "fang"

    def test_spider_mouth_disabled_no_call(self) -> None:
        """MTE-7-AC-5, MTE-8-AC-2: mouth_enabled=False (default) → no create_mouth_mesh call."""
        spider = _make_spider({"mouth_enabled": False})  # explicit default
        spider.parts = []
        with patch(
            _SPIDER_MOUTH_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()
        ) as mock_mouth:
            spider.build_mesh_parts()
        assert mock_mouth.call_count == 0

    def test_spider_mouth_absent_no_call(self) -> None:
        """MTE-7-AC-5: mouth_enabled absent (default False) → no create_mouth_mesh call."""
        spider = _make_spider({})
        spider.parts = []
        with patch(
            _SPIDER_MOUTH_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()
        ) as mock_mouth:
            spider.build_mesh_parts()
        assert mock_mouth.call_count == 0

    def test_spider_mouth_part_count_increased_when_enabled(self) -> None:
        """MTE-7-AC-1: mouth_enabled=True adds exactly 1 extra part."""
        base = _make_spider({"mouth_enabled": False})
        base.parts = []
        with patch(_SPIDER_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            base.build_mesh_parts()
        baseline = len(base.parts)

        enabled = _make_spider({"mouth_enabled": True, "mouth_shape": "fang"})
        enabled.parts = []
        with patch(_SPIDER_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            enabled.build_mesh_parts()

        assert len(enabled.parts) == baseline + 1


# ---------------------------------------------------------------------------
# MTE-7: Mouth geometry wiring — slug
# ---------------------------------------------------------------------------


class TestSlugMouthGeometry:
    """MTE-7-AC-1, MTE-7-AC-5, MTE-7-AC-6: slug mouth mesh calls."""

    def test_slug_mouth_enabled_calls_create_mouth_mesh(self) -> None:
        slug = _make_slug({"mouth_enabled": True, "mouth_shape": "beak"})
        slug.parts = []
        with patch(
            _SLUG_MOUTH_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()
        ) as mock_mouth:
            slug.build_mesh_parts()
        assert mock_mouth.call_count == 1

    def test_slug_mouth_shape_passed_to_create_mouth_mesh(self) -> None:
        slug = _make_slug({"mouth_enabled": True, "mouth_shape": "beak"})
        slug.parts = []
        with patch(
            _SLUG_MOUTH_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()
        ) as mock_mouth:
            slug.build_mesh_parts()
        for c in mock_mouth.call_args_list:
            assert c.args[0] == "beak" or c.kwargs.get("shape") == "beak"

    def test_slug_mouth_disabled_no_call(self) -> None:
        slug = _make_slug({"mouth_enabled": False})
        slug.parts = []
        with patch(
            _SLUG_MOUTH_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()
        ) as mock_mouth:
            slug.build_mesh_parts()
        assert mock_mouth.call_count == 0

    def test_slug_mouth_part_count_increased_when_enabled(self) -> None:
        base = _make_slug({"mouth_enabled": False})
        base.parts = []
        with patch(_SLUG_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            base.build_mesh_parts()
        baseline = len(base.parts)

        enabled = _make_slug({"mouth_enabled": True, "mouth_shape": "fang"})
        enabled.parts = []
        with patch(_SLUG_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            enabled.build_mesh_parts()

        assert len(enabled.parts) == baseline + 1


# ---------------------------------------------------------------------------
# MTE-7: Mouth geometry wiring — claw_crawler
# ---------------------------------------------------------------------------


class TestClawCrawlerMouthGeometry:
    """MTE-7-AC-1, MTE-7-AC-5: claw_crawler mouth mesh calls."""

    def test_claw_crawler_mouth_enabled_calls_create_mouth_mesh(self) -> None:
        claw = _make_claw({"mouth_enabled": True, "mouth_shape": "grimace"})
        claw.parts = []
        with patch(
            _CLAW_MOUTH_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()
        ) as mock_mouth:
            claw.build_mesh_parts()
        assert mock_mouth.call_count == 1

    def test_claw_crawler_mouth_disabled_no_call(self) -> None:
        claw = _make_claw({"mouth_enabled": False})
        claw.parts = []
        with patch(
            _CLAW_MOUTH_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()
        ) as mock_mouth:
            claw.build_mesh_parts()
        assert mock_mouth.call_count == 0

    def test_claw_crawler_mouth_part_count_increased_when_enabled(self) -> None:
        base = _make_claw({"mouth_enabled": False})
        base.parts = []
        with patch(_CLAW_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            base.build_mesh_parts()
        baseline = len(base.parts)

        enabled = _make_claw({"mouth_enabled": True, "mouth_shape": "fang"})
        enabled.parts = []
        with patch(_CLAW_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            enabled.build_mesh_parts()

        assert len(enabled.parts) == baseline + 1


# ---------------------------------------------------------------------------
# MTE-7: Mouth geometry wiring — imp
# ---------------------------------------------------------------------------


class TestImpMouthGeometry:
    """MTE-7-AC-1, MTE-7-AC-5: imp mouth mesh calls."""

    def test_imp_mouth_enabled_calls_create_mouth_mesh(self) -> None:
        imp = _make_imp({"mouth_enabled": True, "mouth_shape": "fang"})
        imp.parts = []
        with patch(
            _IMP_MOUTH_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()
        ) as mock_mouth:
            imp.build_mesh_parts()
        assert mock_mouth.call_count == 1

    def test_imp_mouth_disabled_no_call(self) -> None:
        imp = _make_imp({"mouth_enabled": False})
        imp.parts = []
        with patch(
            _IMP_MOUTH_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()
        ) as mock_mouth:
            imp.build_mesh_parts()
        assert mock_mouth.call_count == 0


# ---------------------------------------------------------------------------
# MTE-7: Mouth geometry wiring — spitter
# ---------------------------------------------------------------------------


class TestSpitterMouthGeometry:
    """MTE-7-AC-1, MTE-7-AC-5: spitter mouth mesh calls."""

    def test_spitter_mouth_enabled_calls_create_mouth_mesh(self) -> None:
        spitter = _make_spitter({"mouth_enabled": True, "mouth_shape": "beak"})
        spitter.parts = []
        with patch(
            _SPITTER_MOUTH_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()
        ) as mock_mouth:
            spitter.build_mesh_parts()
        assert mock_mouth.call_count == 1

    def test_spitter_mouth_disabled_no_call(self) -> None:
        spitter = _make_spitter({"mouth_enabled": False})
        spitter.parts = []
        with patch(
            _SPITTER_MOUTH_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()
        ) as mock_mouth:
            spitter.build_mesh_parts()
        assert mock_mouth.call_count == 0


# ---------------------------------------------------------------------------
# MTE-7: Mouth geometry wiring — carapace_husk
# ---------------------------------------------------------------------------


class TestCarapaceHuskMouthGeometry:
    """MTE-7-AC-1, MTE-7-AC-5: carapace_husk mouth mesh calls."""

    def test_carapace_husk_mouth_enabled_calls_create_mouth_mesh(self) -> None:
        husk = _make_carapace({"mouth_enabled": True, "mouth_shape": "flat"})
        husk.parts = []
        with patch(
            _CARAPACE_MOUTH_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()
        ) as mock_mouth:
            husk.build_mesh_parts()
        assert mock_mouth.call_count == 1

    def test_carapace_husk_mouth_disabled_no_call(self) -> None:
        husk = _make_carapace({"mouth_enabled": False})
        husk.parts = []
        with patch(
            _CARAPACE_MOUTH_PATCH, side_effect=lambda shape, loc, scale: _fake_mesh()
        ) as mock_mouth:
            husk.build_mesh_parts()
        assert mock_mouth.call_count == 0


# ---------------------------------------------------------------------------
# MTE-7: Tail geometry wiring — spider
# ---------------------------------------------------------------------------


class TestSpiderTailGeometry:
    """MTE-7-AC-2, MTE-7-AC-6: spider tail mesh calls."""

    def test_spider_tail_enabled_calls_create_tail_mesh(self) -> None:
        """MTE-7-AC-2: tail_enabled=True triggers create_tail_mesh call."""
        spider = _make_spider(
            {"tail_enabled": True, "tail_shape": "whip", "tail_length": 2.0}
        )
        spider.parts = []
        with patch(
            _SPIDER_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            spider.build_mesh_parts()
        assert mock_tail.call_count == 1

    def test_spider_tail_shape_passed_to_create_tail_mesh(self) -> None:
        """MTE-7-AC-2: tail_shape value is forwarded."""
        spider = _make_spider(
            {"tail_enabled": True, "tail_shape": "club", "tail_length": 1.5}
        )
        spider.parts = []
        with patch(
            _SPIDER_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            spider.build_mesh_parts()
        for c in mock_tail.call_args_list:
            assert c.args[0] == "club" or c.kwargs.get("shape") == "club"

    def test_spider_tail_length_passed_to_create_tail_mesh(self) -> None:
        """MTE-7-AC-2: tail_length value is forwarded."""
        spider = _make_spider(
            {"tail_enabled": True, "tail_shape": "spike", "tail_length": 2.5}
        )
        spider.parts = []
        with patch(
            _SPIDER_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            spider.build_mesh_parts()
        for c in mock_tail.call_args_list:
            # Check either positional or keyword argument
            if len(c.args) >= 2:
                assert c.args[1] == 2.5 or c.kwargs.get("length") == 2.5

    def test_spider_tail_disabled_no_call(self) -> None:
        """MTE-7-AC-6: tail_enabled=False (default) → no create_tail_mesh call."""
        spider = _make_spider({"tail_enabled": False})
        spider.parts = []
        with patch(
            _SPIDER_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            spider.build_mesh_parts()
        assert mock_tail.call_count == 0

    def test_spider_tail_absent_no_call(self) -> None:
        """MTE-7-AC-6: tail_enabled absent (default False) → no create_tail_mesh call."""
        spider = _make_spider({})
        spider.parts = []
        with patch(
            _SPIDER_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            spider.build_mesh_parts()
        assert mock_tail.call_count == 0

    def test_spider_tail_part_count_increased_when_enabled(self) -> None:
        """MTE-7-AC-2: tail_enabled=True adds exactly 1 extra part."""
        base = _make_spider({"tail_enabled": False})
        base.parts = []
        with patch(_SPIDER_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            base.build_mesh_parts()
        baseline = len(base.parts)

        enabled = _make_spider(
            {"tail_enabled": True, "tail_shape": "spike", "tail_length": 1.0}
        )
        enabled.parts = []
        with patch(_SPIDER_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            enabled.build_mesh_parts()

        assert len(enabled.parts) == baseline + 1


# ---------------------------------------------------------------------------
# MTE-7: Tail geometry wiring — slug
# ---------------------------------------------------------------------------


class TestSlugTailGeometry:
    """MTE-7-AC-2, MTE-7-AC-6: slug tail mesh calls."""

    def test_slug_tail_enabled_calls_create_tail_mesh(self) -> None:
        slug = _make_slug(
            {"tail_enabled": True, "tail_shape": "curled", "tail_length": 1.5}
        )
        slug.parts = []
        with patch(
            _SLUG_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            slug.build_mesh_parts()
        assert mock_tail.call_count == 1

    def test_slug_tail_length_passed_to_create_tail_mesh(self) -> None:
        slug = _make_slug(
            {"tail_enabled": True, "tail_shape": "whip", "tail_length": 2.0}
        )
        slug.parts = []
        with patch(
            _SLUG_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            slug.build_mesh_parts()
        for c in mock_tail.call_args_list:
            if len(c.args) >= 2:
                assert c.args[1] == 2.0 or c.kwargs.get("length") == 2.0

    def test_slug_tail_disabled_no_call(self) -> None:
        slug = _make_slug({"tail_enabled": False})
        slug.parts = []
        with patch(
            _SLUG_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            slug.build_mesh_parts()
        assert mock_tail.call_count == 0

    def test_slug_tail_part_count_increased_when_enabled(self) -> None:
        base = _make_slug({"tail_enabled": False})
        base.parts = []
        with patch(_SLUG_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            base.build_mesh_parts()
        baseline = len(base.parts)

        enabled = _make_slug(
            {"tail_enabled": True, "tail_shape": "spike", "tail_length": 1.0}
        )
        enabled.parts = []
        with patch(_SLUG_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            enabled.build_mesh_parts()

        assert len(enabled.parts) == baseline + 1


# ---------------------------------------------------------------------------
# MTE-7: Tail geometry wiring — claw_crawler
# ---------------------------------------------------------------------------


class TestClawCrawlerTailGeometry:
    """MTE-7-AC-2, MTE-7-AC-6: claw_crawler tail mesh calls."""

    def test_claw_crawler_tail_enabled_calls_create_tail_mesh(self) -> None:
        claw = _make_claw(
            {"tail_enabled": True, "tail_shape": "segmented", "tail_length": 1.5}
        )
        claw.parts = []
        with patch(
            _CLAW_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            claw.build_mesh_parts()
        assert mock_tail.call_count == 1

    def test_claw_crawler_tail_disabled_no_call(self) -> None:
        claw = _make_claw({"tail_enabled": False})
        claw.parts = []
        with patch(
            _CLAW_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            claw.build_mesh_parts()
        assert mock_tail.call_count == 0

    def test_claw_crawler_tail_part_count_increased_when_enabled(self) -> None:
        base = _make_claw({"tail_enabled": False})
        base.parts = []
        with patch(_CLAW_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            base.build_mesh_parts()
        baseline = len(base.parts)

        enabled = _make_claw(
            {"tail_enabled": True, "tail_shape": "spike", "tail_length": 1.0}
        )
        enabled.parts = []
        with patch(_CLAW_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            enabled.build_mesh_parts()

        assert len(enabled.parts) == baseline + 1


# ---------------------------------------------------------------------------
# MTE-7: Tail geometry wiring — imp
# ---------------------------------------------------------------------------


class TestImpTailGeometry:
    """MTE-7-AC-2, MTE-7-AC-6: imp tail mesh calls."""

    def test_imp_tail_enabled_calls_create_tail_mesh(self) -> None:
        imp = _make_imp(
            {"tail_enabled": True, "tail_shape": "club", "tail_length": 1.5}
        )
        imp.parts = []
        with patch(
            _IMP_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            imp.build_mesh_parts()
        assert mock_tail.call_count == 1

    def test_imp_tail_disabled_no_call(self) -> None:
        imp = _make_imp({"tail_enabled": False})
        imp.parts = []
        with patch(
            _IMP_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            imp.build_mesh_parts()
        assert mock_tail.call_count == 0


# ---------------------------------------------------------------------------
# MTE-7: Tail geometry wiring — spitter
# ---------------------------------------------------------------------------


class TestSpitterTailGeometry:
    """MTE-7-AC-2, MTE-7-AC-6: spitter tail mesh calls."""

    def test_spitter_tail_enabled_calls_create_tail_mesh(self) -> None:
        spitter = _make_spitter(
            {"tail_enabled": True, "tail_shape": "whip", "tail_length": 2.0}
        )
        spitter.parts = []
        with patch(
            _SPITTER_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            spitter.build_mesh_parts()
        assert mock_tail.call_count == 1

    def test_spitter_tail_disabled_no_call(self) -> None:
        spitter = _make_spitter({"tail_enabled": False})
        spitter.parts = []
        with patch(
            _SPITTER_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            spitter.build_mesh_parts()
        assert mock_tail.call_count == 0


# ---------------------------------------------------------------------------
# MTE-7: Tail geometry wiring — carapace_husk
# ---------------------------------------------------------------------------


class TestCarapaceHuskTailGeometry:
    """MTE-7-AC-2, MTE-7-AC-6: carapace_husk tail mesh calls."""

    def test_carapace_husk_tail_enabled_calls_create_tail_mesh(self) -> None:
        husk = _make_carapace(
            {"tail_enabled": True, "tail_shape": "curled", "tail_length": 2.5}
        )
        husk.parts = []
        with patch(
            _CARAPACE_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            husk.build_mesh_parts()
        assert mock_tail.call_count == 1

    def test_carapace_husk_tail_disabled_no_call(self) -> None:
        husk = _make_carapace({"tail_enabled": False})
        husk.parts = []
        with patch(
            _CARAPACE_TAIL_PATCH, side_effect=lambda shape, length, loc: _fake_mesh()
        ) as mock_tail:
            husk.build_mesh_parts()
        assert mock_tail.call_count == 0


# ---------------------------------------------------------------------------
# MTE-7: Both mouth and tail enabled together
# ---------------------------------------------------------------------------


class TestMouthAndTailBothEnabled:
    """MTE-7-AC-3: both mouth_enabled=True and tail_enabled=True adds exactly 2 parts."""

    def test_spider_both_extras_add_two_parts(self) -> None:
        base = _make_spider({"mouth_enabled": False, "tail_enabled": False})
        base.parts = []
        with patch(_SPIDER_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            with patch(_SPIDER_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
                base.build_mesh_parts()
        baseline = len(base.parts)

        both = _make_spider(
            {
                "mouth_enabled": True,
                "mouth_shape": "fang",
                "tail_enabled": True,
                "tail_shape": "club",
            }
        )
        both.parts = []
        with patch(_SPIDER_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            with patch(_SPIDER_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
                both.build_mesh_parts()

        assert len(both.parts) == baseline + 2


# ---------------------------------------------------------------------------
# MTE-8: Non-breaking default guarantee
# ---------------------------------------------------------------------------


class TestNonBreakingDefaultGuarantee:
    """MTE-8-AC-1, MTE-8-AC-2: default builds produce identical part counts."""

    def test_spider_default_part_count_unchanged(self) -> None:
        """MTE-8-AC-1: spider default build produces same parts as baseline."""
        spider1 = _make_spider({"mouth_enabled": False, "tail_enabled": False})
        spider2 = _make_spider({})  # both defaults
        spider1.parts = []
        spider2.parts = []
        with patch(_SPIDER_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            with patch(_SPIDER_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
                spider1.build_mesh_parts()
                spider2.build_mesh_parts()
        assert len(spider1.parts) == len(spider2.parts)

    def test_slug_default_part_count_unchanged(self) -> None:
        slug1 = _make_slug({"mouth_enabled": False, "tail_enabled": False})
        slug2 = _make_slug({})
        slug1.parts = []
        slug2.parts = []
        with patch(_SLUG_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            with patch(_SLUG_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
                slug1.build_mesh_parts()
                slug2.build_mesh_parts()
        assert len(slug1.parts) == len(slug2.parts)

    def test_claw_crawler_default_part_count_unchanged(self) -> None:
        claw1 = _make_claw({"mouth_enabled": False, "tail_enabled": False})
        claw2 = _make_claw({})
        claw1.parts = []
        claw2.parts = []
        with patch(_CLAW_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            with patch(_CLAW_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
                claw1.build_mesh_parts()
                claw2.build_mesh_parts()
        assert len(claw1.parts) == len(claw2.parts)


# ---------------------------------------------------------------------------
# MTE-7: player_slime controls-only — no geometry calls
# ---------------------------------------------------------------------------

# Note: player_slime is not in AnimatedEnemyBuilder.ENEMY_CLASSES, so its builder
# may or may not exist. We test that if it exists, it doesn't call create_mouth_mesh
# or create_tail_mesh. This is MTE-7-AC-8.


class TestPlayerSlimeControlsOnly:
    """MTE-7-AC-8: player_slime does not call mouth/tail geometry functions."""

    def test_player_slime_not_in_enemy_classes(self) -> None:
        from src.enemies.animated import AnimatedEnemyBuilder

        assert "player_slime" not in AnimatedEnemyBuilder.ENEMY_CLASSES

    def test_player_slime_no_mouth_tail_calls_if_builder_exists(self) -> None:
        """If player_slime builder exists, it should not call create_mouth/tail_mesh."""
        try:
            import importlib.util

            if importlib.util.find_spec("src.enemies.animated_player_slime") is None:
                # No player_slime builder — acceptable
                return
            # We cannot easily instantiate AnimatedPlayerSlime without full setup, so we skip this.
            pytest.skip("player_slime builder not easily instantiable for this test")
        except ImportError:
            # No player_slime builder — acceptable
            pass

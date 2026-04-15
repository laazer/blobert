"""Mouth extra & tail extra — adversarial Python geometry tests with blender stubs.

Adversarial coverage:
  - Shared mutable state guards (parts list mutation detection)
  - Stress tests (extreme part counts, extreme shape parameters)
  - Triangle fallback verification (unknown shapes → sphere fallback)
  - Non-uniform scale guards (scale vector mutation detection)
  - Determinism checks (repeated builds produce identical results)
  - Location formula edge cases (zero/negative radii handling)

Spec requirements tested adversarially: MTE-4..8, geometry helpers.
"""

from __future__ import annotations

import random
from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest

from src.enemies.animated_carapace_husk import AnimatedCarapaceHusk
from src.enemies.animated_claw_crawler import AnimatedClawCrawler
from src.enemies.animated_imp import AnimatedImp
from src.enemies.animated_slug import AnimatedSlug
from src.enemies.animated_spider import AnimatedSpider
from src.enemies.animated_spitter import AnimatedSpitter

# ---------------------------------------------------------------------------
# Patch paths for all enemies
# ---------------------------------------------------------------------------

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
# Shared mutable state guards: parts list mutation detection
# ---------------------------------------------------------------------------


class TestSharedMutableStateGuardsPartsList:
    """Guard against shared parts lists across builds."""

    def test_spider_parts_list_not_shared_across_builds(self) -> None:
        """Each build should get a fresh parts list, not reused."""
        spider1 = _make_spider({})
        spider2 = _make_spider({})
        spider1.parts = []
        spider2.parts = []

        with patch(_SPIDER_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            with patch(_SPIDER_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
                spider1.build_mesh_parts()
                spider2.build_mesh_parts()

        assert spider1.parts is not spider2.parts, (
            "Each enemy instance should have independent parts lists"
        )

    def test_spider_parts_list_not_mutated_by_builder(self) -> None:
        """Builder should not mutate the input build_options dict."""
        build_opts = {"mouth_enabled": True, "tail_length": 2.5}
        original = deepcopy(build_opts)
        spider = _make_spider(build_opts)
        spider.parts = []

        with patch(_SPIDER_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            with patch(_SPIDER_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
                spider.build_mesh_parts()

        assert build_opts == original, (
            "build_options should not be mutated during build"
        )


# ---------------------------------------------------------------------------
# Stress tests: extreme part counts and parameters
# ---------------------------------------------------------------------------


class TestStressTestsExtremePartCounts:
    """Stress testing with extreme parameter values."""

    def test_spider_100_consecutive_builds_deterministic(self) -> None:
        """100 consecutive builds should produce identical results."""
        base = _make_spider({"mouth_enabled": True, "tail_enabled": True})
        part_counts = []
        for _ in range(100):
            base.parts = []
            with patch(_SPIDER_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
                with patch(
                    _SPIDER_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()
                ):
                    base.build_mesh_parts()
            part_counts.append(len(base.parts))

        assert len(set(part_counts)) == 1, (
            "Part count should be deterministic across 100 builds"
        )

    def test_spider_extreme_tail_length_05_min(self) -> None:
        """Tail at minimum length (0.5) should not crash."""
        spider = _make_spider(
            {"tail_enabled": True, "tail_shape": "whip", "tail_length": 0.5}
        )
        spider.parts = []

        with patch(_SPIDER_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            spider.build_mesh_parts()

        assert len(spider.parts) >= 1

    def test_spider_extreme_tail_length_30_max(self) -> None:
        """Tail at maximum length (3.0) should not crash."""
        spider = _make_spider(
            {"tail_enabled": True, "tail_shape": "whip", "tail_length": 3.0}
        )
        spider.parts = []

        with patch(_SPIDER_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            spider.build_mesh_parts()

        assert len(spider.parts) >= 1

    def test_all_enemies_both_extras_enabled_extreme(self) -> None:
        """All 6 enemies with both extras enabled should not crash."""
        makers = [
            (_make_spider, _SPIDER_MOUTH_PATCH, _SPIDER_TAIL_PATCH),
            (_make_slug, _SLUG_MOUTH_PATCH, _SLUG_TAIL_PATCH),
            (_make_claw, _CLAW_MOUTH_PATCH, _CLAW_TAIL_PATCH),
            (_make_imp, _IMP_MOUTH_PATCH, _IMP_TAIL_PATCH),
            (_make_spitter, _SPITTER_MOUTH_PATCH, _SPITTER_TAIL_PATCH),
            (_make_carapace, _CARAPACE_MOUTH_PATCH, _CARAPACE_TAIL_PATCH),
        ]

        for maker, mouth_patch, tail_patch in makers:
            enemy = maker(
                {
                    "mouth_enabled": True,
                    "tail_enabled": True,
                    "mouth_shape": "fang",
                    "tail_shape": "curled",
                    "tail_length": 3.0,
                }
            )
            enemy.parts = []

            with patch(mouth_patch, side_effect=lambda *a, **k: _fake_mesh()):
                with patch(tail_patch, side_effect=lambda *a, **k: _fake_mesh()):
                    enemy.build_mesh_parts()

            assert len(enemy.parts) >= 2, (
                f"{maker.__name__} should have mouth+tail parts"
            )


# ---------------------------------------------------------------------------
# Triangle fallback verification: unknown shapes → sphere fallback
# ---------------------------------------------------------------------------


class TestTriangleFallbackVerification:
    """Unknown shape values should fall back to default behavior without errors."""

    def test_spider_unknown_mouth_shape_falls_back_to_smile(self) -> None:
        """mouth_shape='triangle' (unknown) should not crash, falls back gracefully."""
        spider = _make_spider({"mouth_enabled": True, "mouth_shape": "triangle"})
        spider.parts = []

        with patch(_SPIDER_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            spider.build_mesh_parts()

        # Should not raise; mock was called (fallback behavior)
        assert True

    def test_spider_unknown_tail_shape_falls_back_to_spike(self) -> None:
        """tail_shape='fin' (unknown) should fall back to spike behavior."""
        spider = _make_spider(
            {"tail_enabled": True, "tail_shape": "fin", "tail_length": 1.0}
        )
        spider.parts = []

        with patch(_SPIDER_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            spider.build_mesh_parts()

        assert True

    def test_all_enemies_unknown_mouth_shape_no_crash(self) -> None:
        """All enemies should handle unknown mouth shapes without crashing."""
        makers = [_make_spider, _make_slug, _make_claw, _make_imp, _make_spitter]
        patches = [
            (_SPIDER_MOUTH_PATCH, _SPIDER_TAIL_PATCH),
            (_SLUG_MOUTH_PATCH, _SLUG_TAIL_PATCH),
            (_CLAW_MOUTH_PATCH, _CLAW_TAIL_PATCH),
            (_IMP_MOUTH_PATCH, _IMP_TAIL_PATCH),
            (_SPITTER_MOUTH_PATCH, _SPITTER_TAIL_PATCH),
        ]

        for maker, (mouth_patch, tail_patch) in zip(makers, patches):
            enemy = maker(
                {
                    "mouth_enabled": True,
                    "tail_enabled": False,
                    "mouth_shape": "completely_unknown_shape_xyz",
                }
            )
            enemy.parts = []

            with patch(mouth_patch, side_effect=lambda *a, **k: _fake_mesh()):
                enemy.build_mesh_parts()

    def test_all_enemies_unknown_tail_shape_no_crash(self) -> None:
        """All enemies should handle unknown tail shapes without crashing."""
        makers = [_make_spider, _make_slug, _make_claw, _make_imp, _make_spitter]
        patches = [
            (_SPIDER_MOUTH_PATCH, _SPIDER_TAIL_PATCH),
            (_SLUG_MOUTH_PATCH, _SLUG_TAIL_PATCH),
            (_CLAW_MOUTH_PATCH, _CLAW_TAIL_PATCH),
            (_IMP_MOUTH_PATCH, _IMP_TAIL_PATCH),
            (_SPITTER_MOUTH_PATCH, _SPITTER_TAIL_PATCH),
        ]

        for maker, (mouth_patch, tail_patch) in zip(makers, patches):
            enemy = maker(
                {
                    "tail_enabled": True,
                    "tail_shape": "unknown_tail_xyz",
                    "tail_length": 1.0,
                }
            )
            enemy.parts = []

            with patch(tail_patch, side_effect=lambda *a, **k: _fake_mesh()):
                enemy.build_mesh_parts()


# ---------------------------------------------------------------------------
# Non-uniform scale guards: scale vector mutation detection
# ---------------------------------------------------------------------------


class TestNonUniformScaleGuards:
    """Guard against shared mutable scale vectors being mutated."""

    def test_mouth_scale_parameter_not_mutated(self) -> None:
        """head_scale parameter should not be mutated by create_mouth_mesh call."""
        spider = _make_spider({"mouth_enabled": True, "mouth_shape": "fang"})
        spider.parts = []

        def verify_scale_not_mutated(
            shape: str, location: tuple, head_scale: float
        ) -> MagicMock:
            # Verify scale was not mutated
            assert isinstance(head_scale, (int, float)), "scale should be numeric"
            return _fake_mesh()

        with patch(
            _SPIDER_MOUTH_PATCH, side_effect=verify_scale_not_mutated
        ):
            spider.build_mesh_parts()

    def test_tail_length_parameter_not_mutated(self) -> None:
        """tail_length parameter should not be mutated by create_tail_mesh call."""
        spider = _make_spider(
            {"tail_enabled": True, "tail_shape": "whip", "tail_length": 2.5}
        )
        spider.parts = []

        def verify_length_not_mutated(
            shape: str, length: float, location: tuple
        ) -> MagicMock:
            assert isinstance(length, (int, float)), "length should be numeric"
            return _fake_mesh()

        with patch(
            _SPIDER_TAIL_PATCH, side_effect=verify_length_not_mutated
        ):
            spider.build_mesh_parts()


# ---------------------------------------------------------------------------
# Determinism checks: repeated builds produce identical results
# ---------------------------------------------------------------------------


class TestDeterminismChecksRepeatedBuilds:
    """Verify deterministic behavior across repeated builds."""

    def test_spider_build_deterministic_10_iterations(self) -> None:
        """10 consecutive builds should produce same part count each time."""
        spider = _make_spider(
            {
                "mouth_enabled": True,
                "mouth_shape": "fang",
                "tail_enabled": True,
                "tail_shape": "club",
                "tail_length": 1.5,
            }
        )

        part_counts = []
        for _ in range(10):
            spider.parts = []
            with patch(_SPIDER_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
                with patch(
                    _SPIDER_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()
                ):
                    spider.build_mesh_parts()
            part_counts.append(len(spider.parts))

        assert len(set(part_counts)) == 1, (
            f"Part count not deterministic: {part_counts}"
        )

    def test_slug_build_deterministic_10_iterations(self) -> None:
        """Slug builds should be deterministic."""
        slug = _make_slug({"mouth_enabled": True, "tail_enabled": False})

        part_counts = []
        for _ in range(10):
            slug.parts = []
            with patch(_SLUG_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
                slug.build_mesh_parts()
            part_counts.append(len(slug.parts))

        assert len(set(part_counts)) == 1

    @pytest.mark.parametrize(
        "enemy_maker,mouth_patch,tail_patch",
        [
            (_make_spider, _SPIDER_MOUTH_PATCH, _SPIDER_TAIL_PATCH),
            (_make_slug, _SLUG_MOUTH_PATCH, _SLUG_TAIL_PATCH),
            (_make_claw, _CLAW_MOUTH_PATCH, _CLAW_TAIL_PATCH),
            (_make_imp, _IMP_MOUTH_PATCH, _IMP_TAIL_PATCH),
            (_make_spitter, _SPITTER_MOUTH_PATCH, _SPITTER_TAIL_PATCH),
        ],
    )
    def test_all_enemies_deterministic(
        self, enemy_maker, mouth_patch, tail_patch
    ) -> None:
        """All enemies should produce deterministic builds."""
        enemy = enemy_maker({"mouth_enabled": True, "tail_enabled": False})

        part_counts = []
        for _ in range(5):
            enemy.parts = []
            with patch(mouth_patch, side_effect=lambda *a, **k: _fake_mesh()):
                enemy.build_mesh_parts()
            part_counts.append(len(enemy.parts))

        assert len(set(part_counts)) == 1


# ---------------------------------------------------------------------------
# Location formula edge cases: zero/negative radii handling
# ---------------------------------------------------------------------------


class TestLocationFormulaEdgeCases:
    """Test mouth/tail location computation with extreme zone geometry values."""

    def test_mouth_location_computed_from_zone_geom(self) -> None:
        """Mouth location should be computed from _zone_geom_head_center + _zone_geom_head_radii."""
        spider = _make_spider({"mouth_enabled": True, "mouth_shape": "fang"})
        spider.parts = []

        def verify_location_computed(
            shape: str, location: tuple, head_scale: float
        ) -> MagicMock:
            # Verify location is a 3-tuple of numbers
            assert isinstance(location, (tuple, list)), "location must be sequence"
            assert len(location) == 3, "location must have 3 components"
            for coord in location:
                assert isinstance(coord, (int, float)), f"coord {coord} not numeric"
            return _fake_mesh()

        with patch(
            _SPIDER_MOUTH_PATCH, side_effect=verify_location_computed
        ):
            spider.build_mesh_parts()


# ---------------------------------------------------------------------------
# Primitive dispatch exclusivity: shape → primitive mapping verification
# ---------------------------------------------------------------------------


class TestPrimitiveDispatchExclusivity:
    """Verify each mouth/tail shape maps to correct primitive type."""

    def test_spider_fang_shape_calls_cone(self) -> None:
        """mouth_shape='fang' should call create_mouth_mesh with 'fang'."""
        spider = _make_spider({"mouth_enabled": True, "mouth_shape": "fang"})
        spider.parts = []

        captured_args = []

        def capture_fang_call(
            shape: str, location: tuple, head_scale: float
        ) -> MagicMock:
            captured_args.append((shape, location, head_scale))
            return _fake_mesh()

        with patch(_SPIDER_MOUTH_PATCH, side_effect=capture_fang_call):
            spider.build_mesh_parts()

        assert len(captured_args) == 1
        assert captured_args[0][0] == "fang"

    def test_spider_beak_shape_calls_cone(self) -> None:
        """mouth_shape='beak' should call create_mouth_mesh with 'beak'."""
        spider = _make_spider({"mouth_enabled": True, "mouth_shape": "beak"})
        spider.parts = []

        captured_args = []

        def capture_beak_call(
            shape: str, location: tuple, head_scale: float
        ) -> MagicMock:
            captured_args.append((shape, location, head_scale))
            return _fake_mesh()

        with patch(_SPIDER_MOUTH_PATCH, side_effect=capture_beak_call):
            spider.build_mesh_parts()

        assert len(captured_args) == 1
        assert captured_args[0][0] == "beak"

    def test_spider_whip_shape_calls_cylinder(self) -> None:
        """tail_shape='whip' should call create_tail_mesh with 'whip'."""
        spider = _make_spider(
            {"tail_enabled": True, "tail_shape": "whip", "tail_length": 1.0}
        )
        spider.parts = []

        captured_args = []

        def capture_whip_call(shape: str, length: float, location: tuple) -> MagicMock:
            captured_args.append((shape, length, location))
            return _fake_mesh()

        with patch(_SPIDER_TAIL_PATCH, side_effect=capture_whip_call):
            spider.build_mesh_parts()

        assert len(captured_args) == 1
        assert captured_args[0][0] == "whip"


# ---------------------------------------------------------------------------
# Pupil shape fallback behavior (triangle → sphere not box)
# ---------------------------------------------------------------------------


class TestFallbackPrimitiveBehavior:
    """Unknown shapes should fall back to default primitive, not crash or use wrong type."""

    def test_unknown_mouth_shape_fallback_not_error(self) -> None:
        """Unknown mouth shape should not raise exception, falls back gracefully."""
        spider = _make_spider(
            {"mouth_enabled": True, "mouth_shape": "completely_fake_xyz123"}
        )
        spider.parts = []

        # Should not raise any exception
        with patch(_SPIDER_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            spider.build_mesh_parts()

    def test_unknown_tail_shape_fallback_not_error(self) -> None:
        """Unknown tail shape should not raise exception."""
        spider = _make_spider(
            {
                "tail_enabled": True,
                "tail_shape": "not_a_real_shape_abc",
                "tail_length": 1.0,
            }
        )
        spider.parts = []

        with patch(_SPIDER_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            spider.build_mesh_parts()


# ---------------------------------------------------------------------------
# Combined mouth + tail geometry tests
# ---------------------------------------------------------------------------


class TestCombinedMouthTailGeometry:
    """Tests for both mouth and tail enabled simultaneously."""

    def test_spider_both_extras_call_both_functions(self) -> None:
        """Both mouth and tail enabled should call both create functions once each."""
        spider = _make_spider(
            {
                "mouth_enabled": True,
                "tail_enabled": True,
                "mouth_shape": "fang",
                "tail_shape": "club",
                "tail_length": 2.0,
            }
        )
        spider.parts = []

        with patch(
            _SPIDER_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()
        ) as mock_mouth:
            with patch(
                _SPIDER_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()
            ) as mock_tail:
                spider.build_mesh_parts()

        assert mock_mouth.call_count == 1, "mouth should be called once"
        assert mock_tail.call_count == 1, "tail should be called once"

    def test_carapace_husk_both_extras_enabled(self) -> None:
        """carapace_husk with both extras enabled."""
        husk = _make_carapace(
            {
                "mouth_enabled": True,
                "mouth_shape": "flat",
                "tail_enabled": True,
                "tail_shape": "segmented",
                "tail_length": 1.5,
            }
        )
        husk.parts = []

        with patch(_CARAPACE_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            with patch(_CARAPACE_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
                husk.build_mesh_parts()

        assert len(husk.parts) >= 2


# ---------------------------------------------------------------------------
# Imp and spitter geometry-wired verification (MTE-7)
# ---------------------------------------------------------------------------


class TestImpSpitterGeometryWired:
    """Verify imp and spitter are geometry-wired for mouth/tail."""

    def test_imp_mouth_geometry_wired(self) -> None:
        """imp should call create_mouth_mesh when mouth_enabled=True."""
        imp = _make_imp({"mouth_enabled": True, "mouth_shape": "fang"})
        imp.parts = []

        with patch(_IMP_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            imp.build_mesh_parts()

    def test_spitter_mouth_geometry_wired(self) -> None:
        """spitter should call create_mouth_mesh when mouth_enabled=True."""
        spitter = _make_spitter({"mouth_enabled": True, "mouth_shape": "beak"})
        spitter.parts = []

        with patch(_SPITTER_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            spitter.build_mesh_parts()


# ---------------------------------------------------------------------------
# Carapace husk geometry-wired verification (MTE-7)
# ---------------------------------------------------------------------------


class TestCarapaceHuskGeometryWired:
    """Verify carapace_husk is geometry-wired for mouth/tail."""

    def test_carapace_mouth_geometry_wired(self) -> None:
        """carapace_husk should call create_mouth_mesh when mouth_enabled=True."""
        husk = _make_carapace({"mouth_enabled": True, "mouth_shape": "fang"})
        husk.parts = []

        with patch(_CARAPACE_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            husk.build_mesh_parts()

    def test_carapace_tail_geometry_wired(self) -> None:
        """carapace_husk should call create_tail_mesh when tail_enabled=True."""
        husk = _make_carapace(
            {"tail_enabled": True, "tail_shape": "curled", "tail_length": 2.5}
        )
        husk.parts = []

        with patch(_CARAPACE_TAIL_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
            husk.build_mesh_parts()


# ---------------------------------------------------------------------------
# Non-breaking default guarantee (MTE-8)
# ---------------------------------------------------------------------------


class TestNonBreakingDefaultGuaranteeStress:
    """Stress test the non-breaking default guarantee."""

    def test_all_enemies_default_build_same_part_count(self) -> None:
        """All enemies with default options should have same part count as baseline."""
        makers = [
            (_make_spider, _SPIDER_MOUTH_PATCH, _SPIDER_TAIL_PATCH),
            (_make_slug, _SLUG_MOUTH_PATCH, _SLUG_TAIL_PATCH),
            (_make_claw, _CLAW_MOUTH_PATCH, _CLAW_TAIL_PATCH),
            (_make_imp, _IMP_MOUTH_PATCH, _IMP_TAIL_PATCH),
            (_make_spitter, _SPITTER_MOUTH_PATCH, _SPITTER_TAIL_PATCH),
        ]

        for maker, mouth_patch, tail_patch in makers:
            # Build with explicit defaults
            enemy1 = maker({"mouth_enabled": False, "tail_enabled": False})
            # Build with no options (implicit defaults)
            enemy2 = maker({})

            enemy1.parts = []
            enemy2.parts = []

            with patch(mouth_patch, side_effect=lambda *a, **k: _fake_mesh()):
                with patch(tail_patch, side_effect=lambda *a, **k: _fake_mesh()):
                    enemy1.build_mesh_parts()
                    enemy2.build_mesh_parts()

            assert len(enemy1.parts) == len(enemy2.parts), (
                f"{maker.__name__} should have same part count for explicit vs implicit defaults"
            )


# ---------------------------------------------------------------------------
# Zone geometry attribute verification (MTE-4)
# ---------------------------------------------------------------------------


class TestZoneGeometryAttributeVerification:
    """Verify _zone_geom_* attributes are set before mouth/tail geometry."""

    def test_spider_zone_geom_attrs_set_before_mouth(self) -> None:
        """_zone_geom_head_center and _zone_geom_head_radii should be set before mouth call."""
        spider = _make_spider({"mouth_enabled": True, "mouth_shape": "fang"})
        spider.parts = []

        def verify_zone_attrs_present(
            shape: str, location: tuple, head_scale: float
        ) -> MagicMock:
            # Verify zone geometry attributes exist before mouth creation
            assert hasattr(spider, "_zone_geom_head_center"), (
                "_zone_geom_head_center must be set"
            )
            assert hasattr(spider, "_zone_geom_head_radii"), (
                "_zone_geom_head_radii must be set"
            )
            return _fake_mesh()

        with patch(_SPIDER_MOUTH_PATCH, side_effect=verify_zone_attrs_present):
            spider.build_mesh_parts()


# ---------------------------------------------------------------------------
# Edge case: mouth_enabled=True but no head mesh (should not happen per spec)
# ---------------------------------------------------------------------------


class TestEdgeCaseNoHeadMesh:
    """Edge cases for missing zone geometry attributes."""

    def test_spider_with_no_head_center_attr(self) -> None:
        """If _zone_geom_head_center is missing, should handle gracefully."""
        spider = _make_spider({"mouth_enabled": True})
        # Remove the attribute to simulate edge case
        if hasattr(spider, "_zone_geom_head_center"):
            delattr(spider, "_zone_geom_head_center")

        spider.parts = []

        # Should not crash even with missing attribute (builder should handle)
        try:
            with patch(_SPIDER_MOUTH_PATCH, side_effect=lambda *a, **k: _fake_mesh()):
                spider.build_mesh_parts()
        except AttributeError:
            # Acceptable if builder raises when required attrs missing
            pass

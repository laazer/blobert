"""Mouth extra & tail extra — adversarial geometry tests (Part 2: spec gap coverage).

Adversarial coverage (extending test_mouth_tail_geometry_adversarial.py):
  - MTE-4 location formula sign correctness (mouth on +X, tail on -X)
  - MTE-5-AC-5, MTE-6 constant relational constraints in blender_utils
  - MTE-7-AC-7 import contract (create_mouth_mesh / create_tail_mesh importable)
  - MTE-8-AC-1/2/3 all 6 animated slugs parametrized baseline regression
  - Mutation guard: mouth_shape=None in geometry layer must not become "None" string

Spec requirements tested adversarially: MTE-4, MTE-5, MTE-6, MTE-7, MTE-8.
"""

from __future__ import annotations

import inspect
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
# Patch paths (must match where each enemy builder imports from)
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
# MTE-4 location formula sign correctness
# Exposes gap: no existing test verifies that mouth is placed on the +X surface
# (positive x offset from head center) and tail on the -X surface (negative x
# offset from body center). An implementation that negates the head offset
# would place the mouth inside the head — these tests catch that.
# ---------------------------------------------------------------------------


class TestLocationFormulaSignCorrectness:
    """MTE-4-AC-1/2: mouth on +X surface (positive x), tail on -X surface (negative x).

    Key invariants from spec MTE-4:
    - mouth_location[0] == head_center.x + head_radii.x  (positive offset)
    - tail_location[0] == body_center.x - body_radii.x   (negative offset)

    Conservative assertion: since head/body centers are near origin and radii > 0,
    mouth_location[0] >= 0 and tail_location[0] <= 0.
    """

    def test_spider_mouth_location_x_is_positive_offset(self) -> None:
        """Mouth X must be >= 0 (front +X surface of head).

        # CHECKPOINT: conservative assumption — spider head center x >= 0 in default build.
        # If head center is offset to x < 0 in some configs, this test might need revision.
        """
        spider = _make_spider({"mouth_enabled": True, "mouth_shape": "fang"})
        spider.parts = []

        captured_locations: list[tuple] = []

        def capture_mouth(shape: str, location: tuple, head_scale: float) -> MagicMock:
            captured_locations.append(location)
            return _fake_mesh()

        with patch(_SPIDER_MOUTH_PATCH, side_effect=capture_mouth):
            spider.build_mesh_parts()

        assert len(captured_locations) == 1, "create_mouth_mesh must be called exactly once"
        mouth_x = captured_locations[0][0]
        assert mouth_x >= 0.0, (
            f"Mouth X={mouth_x} must be >= 0 (front +X surface). "
            "Negative value indicates sign error: formula should use +head_radii.x."
        )

    def test_spider_tail_location_x_is_negative_offset(self) -> None:
        """Tail X must be <= 0 (rear -X surface of body).

        # CHECKPOINT: conservative assumption — spider body center x <= 0 in default build.
        """
        spider = _make_spider({"tail_enabled": True, "tail_shape": "spike", "tail_length": 1.0})
        spider.parts = []

        captured_locations: list[tuple] = []

        def capture_tail(shape: str, length: float, location: tuple) -> MagicMock:
            captured_locations.append(location)
            return _fake_mesh()

        with patch(_SPIDER_TAIL_PATCH, side_effect=capture_tail):
            spider.build_mesh_parts()

        assert len(captured_locations) == 1, "create_tail_mesh must be called exactly once"
        tail_x = captured_locations[0][0]
        assert tail_x <= 0.0, (
            f"Tail X={tail_x} must be <= 0 (rear -X surface). "
            "Positive value indicates sign error: formula should use -body_radii.x."
        )

    def test_slug_mouth_x_greater_than_tail_x(self) -> None:
        """Mouth (front +X) X must exceed tail (rear -X) X for any slug build.

        This is the definitive directional test: front > rear in X axis.
        """
        slug = _make_slug({
            "mouth_enabled": True, "mouth_shape": "fang",
            "tail_enabled": True, "tail_shape": "spike", "tail_length": 1.0,
        })
        slug.parts = []

        mouth_x_vals: list[float] = []
        tail_x_vals: list[float] = []

        def cap_mouth(shape: str, location: tuple, head_scale: float) -> MagicMock:
            mouth_x_vals.append(location[0])
            return _fake_mesh()

        def cap_tail(shape: str, length: float, location: tuple) -> MagicMock:
            tail_x_vals.append(location[0])
            return _fake_mesh()

        with patch(_SLUG_MOUTH_PATCH, side_effect=cap_mouth):
            with patch(_SLUG_TAIL_PATCH, side_effect=cap_tail):
                slug.build_mesh_parts()

        assert mouth_x_vals and tail_x_vals
        assert mouth_x_vals[0] > tail_x_vals[0], (
            f"Mouth X ({mouth_x_vals[0]}) must be > tail X ({tail_x_vals[0]}). "
            "Mouth is front (+X face), tail is rear (-X face)."
        )

    def test_claw_crawler_mouth_location_is_3d_tuple(self) -> None:
        """Mouth location must be a 3-element sequence of numeric values."""
        claw = _make_claw({"mouth_enabled": True, "mouth_shape": "grimace"})
        claw.parts = []
        captured: list[tuple] = []

        def cap(shape: str, location: tuple, head_scale: float) -> MagicMock:
            captured.append(location)
            return _fake_mesh()

        with patch(_CLAW_MOUTH_PATCH, side_effect=cap):
            claw.build_mesh_parts()

        assert len(captured) == 1
        loc = captured[0]
        assert len(loc) == 3, f"Mouth location must be 3D, got length {len(loc)}"
        for i, coord in enumerate(loc):
            assert isinstance(coord, (int, float)), f"coord[{i}]={coord!r} not numeric"

    def test_claw_crawler_tail_location_is_3d_tuple(self) -> None:
        """Tail location must be a 3-element sequence of numeric values."""
        claw = _make_claw({"tail_enabled": True, "tail_shape": "club", "tail_length": 1.5})
        claw.parts = []
        captured: list[tuple] = []

        def cap(shape: str, length: float, location: tuple) -> MagicMock:
            captured.append(location)
            return _fake_mesh()

        with patch(_CLAW_TAIL_PATCH, side_effect=cap):
            claw.build_mesh_parts()

        assert len(captured) == 1
        loc = captured[0]
        assert len(loc) == 3, f"Tail location must be 3D, got length {len(loc)}"


# ---------------------------------------------------------------------------
# MTE-5-AC-5, MTE-6 constant relational constraints in blender_utils
# Exposes gap: no existing test reads the module-level constants from
# blender_utils and asserts the relational invariants mandated by the spec.
# An implementation that accidentally swaps FANG/BEAK would pass all current
# tests while violating the spec aesthetic constraint.
# ---------------------------------------------------------------------------


class TestBlenderUtilsConstantConstraints:
    """MTE-5-AC-5 and MTE-6: module-level constant relational constraints.

    These tests are RED until implementation introduces these constants.
    """

    def test_mouth_fang_ratio_less_than_beak_ratio(self) -> None:
        """MTE-5-AC-5: fang is narrower than beak (_MOUTH_FANG_X_RATIO < _MOUTH_BEAK_X_RATIO)."""
        from src.core import blender_utils as bu

        assert hasattr(bu, "_MOUTH_FANG_X_RATIO"), "_MOUTH_FANG_X_RATIO must exist in blender_utils"
        assert hasattr(bu, "_MOUTH_BEAK_X_RATIO"), "_MOUTH_BEAK_X_RATIO must exist in blender_utils"
        assert bu._MOUTH_FANG_X_RATIO < bu._MOUTH_BEAK_X_RATIO, (
            f"_MOUTH_FANG_X_RATIO ({bu._MOUTH_FANG_X_RATIO}) must be < "
            f"_MOUTH_BEAK_X_RATIO ({bu._MOUTH_BEAK_X_RATIO}). Fang is narrower than beak."
        )

    def test_tail_whip_ratio_less_than_seg_ratio(self) -> None:
        """MTE-6-AC-2: whip is thinner than segmented (_TAIL_WHIP_XY_RATIO < _TAIL_SEG_XY_RATIO)."""
        from src.core import blender_utils as bu

        assert hasattr(bu, "_TAIL_WHIP_XY_RATIO"), "_TAIL_WHIP_XY_RATIO must exist in blender_utils"
        assert hasattr(bu, "_TAIL_SEG_XY_RATIO"), "_TAIL_SEG_XY_RATIO must exist in blender_utils"
        assert bu._TAIL_WHIP_XY_RATIO < bu._TAIL_SEG_XY_RATIO, (
            f"_TAIL_WHIP_XY_RATIO ({bu._TAIL_WHIP_XY_RATIO}) must be < "
            f"_TAIL_SEG_XY_RATIO ({bu._TAIL_SEG_XY_RATIO}). Whip is thinner than segmented."
        )

    def test_tail_curled_z_ratio_less_than_x_ratio(self) -> None:
        """MTE-6: curled tail is flattened (_TAIL_CURLED_Z_RATIO < _TAIL_CURLED_X_RATIO)."""
        from src.core import blender_utils as bu

        assert hasattr(bu, "_TAIL_CURLED_X_RATIO"), "_TAIL_CURLED_X_RATIO must exist in blender_utils"
        assert hasattr(bu, "_TAIL_CURLED_Z_RATIO"), "_TAIL_CURLED_Z_RATIO must exist in blender_utils"
        assert bu._TAIL_CURLED_Z_RATIO < bu._TAIL_CURLED_X_RATIO, (
            f"_TAIL_CURLED_Z_RATIO ({bu._TAIL_CURLED_Z_RATIO}) must be < "
            f"_TAIL_CURLED_X_RATIO ({bu._TAIL_CURLED_X_RATIO}). Curled is a flattened sphere."
        )

    def test_mouth_smile_z_ratio_less_than_x_ratio(self) -> None:
        """Smile is a thin wide disc: Z (depth) < X (width)."""
        from src.core import blender_utils as bu

        assert hasattr(bu, "_MOUTH_SMILE_X_RATIO"), "_MOUTH_SMILE_X_RATIO must exist"
        assert hasattr(bu, "_MOUTH_SMILE_Z_RATIO"), "_MOUTH_SMILE_Z_RATIO must exist"
        assert bu._MOUTH_SMILE_Z_RATIO < bu._MOUTH_SMILE_X_RATIO, (
            "Smile cylinder: Z (depth) must be < X (width) — thin wide disc, not tall cylinder"
        )

    def test_mouth_flat_z_ratio_less_than_x_ratio(self) -> None:
        """Flat slit: Z (slit depth) < X (width)."""
        from src.core import blender_utils as bu

        assert hasattr(bu, "_MOUTH_FLAT_X_RATIO"), "_MOUTH_FLAT_X_RATIO must exist"
        assert hasattr(bu, "_MOUTH_FLAT_Z_RATIO"), "_MOUTH_FLAT_Z_RATIO must exist"
        assert bu._MOUTH_FLAT_Z_RATIO < bu._MOUTH_FLAT_X_RATIO, (
            "Flat mouth box: Z (slit depth) must be < X (width)"
        )

    def test_all_mouth_constants_are_positive(self) -> None:
        """All mouth scale ratio constants must be positive values (no zero or negative)."""
        from src.core import blender_utils as bu

        constant_names = [
            "_MOUTH_SMILE_X_RATIO", "_MOUTH_SMILE_Y_RATIO", "_MOUTH_SMILE_Z_RATIO",
            "_MOUTH_GRIMACE_X_RATIO", "_MOUTH_GRIMACE_Y_RATIO", "_MOUTH_GRIMACE_Z_RATIO",
            "_MOUTH_FLAT_X_RATIO", "_MOUTH_FLAT_Y_RATIO", "_MOUTH_FLAT_Z_RATIO",
            "_MOUTH_FANG_X_RATIO", "_MOUTH_FANG_Z_RATIO",
            "_MOUTH_BEAK_X_RATIO", "_MOUTH_BEAK_Z_RATIO",
        ]
        for name in constant_names:
            assert hasattr(bu, name), f"{name} must exist in blender_utils"
            val = getattr(bu, name)
            assert val > 0, f"{name}={val} must be positive (non-zero scale ratio)"

    def test_all_tail_constants_are_positive(self) -> None:
        """All tail scale ratio constants must be positive values."""
        from src.core import blender_utils as bu

        constant_names = [
            "_TAIL_WHIP_XY_RATIO", "_TAIL_SEG_XY_RATIO",
            "_TAIL_CLUB_Z_RATIO", "_TAIL_CURLED_X_RATIO", "_TAIL_CURLED_Z_RATIO",
        ]
        for name in constant_names:
            assert hasattr(bu, name), f"{name} must exist in blender_utils"
            val = getattr(bu, name)
            assert val > 0, f"{name}={val} must be positive (non-zero scale ratio)"


# ---------------------------------------------------------------------------
# MTE-7-AC-7: create_mouth_mesh and create_tail_mesh import contract
# Exposes gap: no existing test verifies the canonical import path from
# src.core.blender_utils. If an implementer defines these functions inline
# inside enemy modules, the import contract breaks. Tests verify both
# importability and correct function signatures.
# ---------------------------------------------------------------------------


class TestBlenderUtilsImportContract:
    """MTE-7-AC-7: create_mouth_mesh and create_tail_mesh importable from blender_utils."""

    def test_create_mouth_mesh_importable_from_blender_utils(self) -> None:
        """create_mouth_mesh must be importable from src.core.blender_utils."""
        from src.core.blender_utils import create_mouth_mesh  # noqa: F401

        assert callable(create_mouth_mesh), "create_mouth_mesh must be callable"

    def test_create_tail_mesh_importable_from_blender_utils(self) -> None:
        """create_tail_mesh must be importable from src.core.blender_utils."""
        from src.core.blender_utils import create_tail_mesh  # noqa: F401

        assert callable(create_tail_mesh), "create_tail_mesh must be callable"

    def test_create_mouth_mesh_signature_has_required_params(self) -> None:
        """create_mouth_mesh(shape, location, head_scale) — 3 required params."""
        from src.core.blender_utils import create_mouth_mesh

        sig = inspect.signature(create_mouth_mesh)
        params = list(sig.parameters.keys())
        assert "shape" in params, "create_mouth_mesh must have 'shape' parameter"
        assert "location" in params, "create_mouth_mesh must have 'location' parameter"
        assert "head_scale" in params, "create_mouth_mesh must have 'head_scale' parameter"

    def test_create_tail_mesh_signature_has_length_before_location(self) -> None:
        """create_tail_mesh(shape, length, location) — 'length' must precede 'location'.

        Spec MTE-6 explicitly mandates: parameter order is (shape, length, location).
        An implementation that swaps length/location would break all call sites.
        """
        from src.core.blender_utils import create_tail_mesh

        sig = inspect.signature(create_tail_mesh)
        params = list(sig.parameters.keys())
        assert "shape" in params, "create_tail_mesh must have 'shape' parameter"
        assert "length" in params, "create_tail_mesh must have 'length' parameter"
        assert "location" in params, "create_tail_mesh must have 'location' parameter"
        shape_idx = params.index("shape")
        length_idx = params.index("length")
        location_idx = params.index("location")
        assert shape_idx < length_idx < location_idx, (
            f"create_tail_mesh parameter order must be (shape, length, location); "
            f"got order: {params}. Wrong order would silently pass location as length."
        )

    def test_create_tail_mesh_callable_with_stub(self) -> None:
        """MTE-6-AC-5: create_tail_mesh('spike', 1.0, (0, 0, 0)) returns non-None."""
        from src.core.blender_utils import create_tail_mesh

        result = create_tail_mesh("spike", 1.0, (0, 0, 0))
        assert result is not None, (
            "create_tail_mesh('spike', 1.0, (0,0,0)) must return a non-None object"
        )

    def test_create_mouth_mesh_callable_with_stub(self) -> None:
        """create_mouth_mesh('smile', (0, 0, 0), 0.5) returns non-None."""
        from src.core.blender_utils import create_mouth_mesh

        result = create_mouth_mesh("smile", (0, 0, 0), 0.5)
        assert result is not None, (
            "create_mouth_mesh('smile', (0,0,0), 0.5) must return a non-None object"
        )

    def test_create_tail_mesh_unknown_shape_does_not_raise(self) -> None:
        """MTE-6-AC-6: unknown shape falls back silently — no exception raised."""
        from src.core.blender_utils import create_tail_mesh

        try:
            result = create_tail_mesh("fin", 1.0, (0, 0, 0))
            assert result is not None, "Fallback must return an object, not None"
        except Exception as exc:
            raise AssertionError(
                f"create_tail_mesh('fin', ...) must not raise; got {exc!r}"
            ) from exc

    def test_create_mouth_mesh_unknown_shape_does_not_raise(self) -> None:
        """MTE-5-AC-6: unknown mouth shape falls back silently — no exception raised."""
        from src.core.blender_utils import create_mouth_mesh

        try:
            result = create_mouth_mesh("triangle", (0, 0, 0), 0.5)
            assert result is not None, "Fallback must return an object, not None"
        except Exception as exc:
            raise AssertionError(
                f"create_mouth_mesh('triangle', ...) must not raise; got {exc!r}"
            ) from exc


# ---------------------------------------------------------------------------
# MTE-8-AC-1/2/3: All 6 animated slugs parametrized baseline part count regression
# Exposes gap: existing TestNonBreakingDefaultGuarantee only covers spider, slug,
# claw_crawler. imp, spitter, and carapace_husk are absent from named regression
# tests. This parametrized class covers all 6 slugs for 3 invariants.
# ---------------------------------------------------------------------------


class TestAllSixSlugsBaselineRegression:
    """MTE-8-AC-1/2/3: Regression across all 6 geometry-wired animated slugs."""

    @pytest.mark.parametrize(
        "enemy_maker,mouth_patch,tail_patch,slug_name",
        [
            (_make_spider, _SPIDER_MOUTH_PATCH, _SPIDER_TAIL_PATCH, "spider"),
            (_make_slug, _SLUG_MOUTH_PATCH, _SLUG_TAIL_PATCH, "slug"),
            (_make_claw, _CLAW_MOUTH_PATCH, _CLAW_TAIL_PATCH, "claw_crawler"),
            (_make_imp, _IMP_MOUTH_PATCH, _IMP_TAIL_PATCH, "imp"),
            (_make_spitter, _SPITTER_MOUTH_PATCH, _SPITTER_TAIL_PATCH, "spitter"),
            (_make_carapace, _CARAPACE_MOUTH_PATCH, _CARAPACE_TAIL_PATCH, "carapace_husk"),
        ],
    )
    def test_explicit_defaults_match_implicit_defaults_part_count(
        self,
        enemy_maker: object,
        mouth_patch: str,
        tail_patch: str,
        slug_name: str,
    ) -> None:
        """MTE-8-AC-1: explicit {mouth_enabled:False, tail_enabled:False} == {} for all 6."""
        explicit = enemy_maker({"mouth_enabled": False, "tail_enabled": False})
        implicit = enemy_maker({})
        explicit.parts = []
        implicit.parts = []

        with patch(mouth_patch, side_effect=lambda *a, **k: _fake_mesh()):
            with patch(tail_patch, side_effect=lambda *a, **k: _fake_mesh()):
                explicit.build_mesh_parts()
                implicit.build_mesh_parts()

        assert len(explicit.parts) == len(implicit.parts), (
            f"slug '{slug_name}': explicit defaults must yield same part count as implicit. "
            f"explicit={len(explicit.parts)}, implicit={len(implicit.parts)}"
        )

    @pytest.mark.parametrize(
        "enemy_maker,mouth_patch,tail_patch,slug_name",
        [
            (_make_spider, _SPIDER_MOUTH_PATCH, _SPIDER_TAIL_PATCH, "spider"),
            (_make_slug, _SLUG_MOUTH_PATCH, _SLUG_TAIL_PATCH, "slug"),
            (_make_claw, _CLAW_MOUTH_PATCH, _CLAW_TAIL_PATCH, "claw_crawler"),
            (_make_imp, _IMP_MOUTH_PATCH, _IMP_TAIL_PATCH, "imp"),
            (_make_spitter, _SPITTER_MOUTH_PATCH, _SPITTER_TAIL_PATCH, "spitter"),
            (_make_carapace, _CARAPACE_MOUTH_PATCH, _CARAPACE_TAIL_PATCH, "carapace_husk"),
        ],
    )
    def test_no_geometry_calls_on_default_build(
        self,
        enemy_maker: object,
        mouth_patch: str,
        tail_patch: str,
        slug_name: str,
    ) -> None:
        """MTE-8-AC-2: zero geometry calls for default build across all 6 slugs."""
        enemy = enemy_maker({})
        enemy.parts = []

        with patch(mouth_patch, side_effect=lambda *a, **k: _fake_mesh()) as mock_m:
            with patch(tail_patch, side_effect=lambda *a, **k: _fake_mesh()) as mock_t:
                enemy.build_mesh_parts()

        assert mock_m.call_count == 0, (
            f"slug '{slug_name}': create_mouth_mesh must NOT be called in default build"
        )
        assert mock_t.call_count == 0, (
            f"slug '{slug_name}': create_tail_mesh must NOT be called in default build"
        )

    @pytest.mark.parametrize(
        "enemy_maker,mouth_patch,tail_patch,slug_name",
        [
            (_make_spider, _SPIDER_MOUTH_PATCH, _SPIDER_TAIL_PATCH, "spider"),
            (_make_slug, _SLUG_MOUTH_PATCH, _SLUG_TAIL_PATCH, "slug"),
            (_make_claw, _CLAW_MOUTH_PATCH, _CLAW_TAIL_PATCH, "claw_crawler"),
            (_make_imp, _IMP_MOUTH_PATCH, _IMP_TAIL_PATCH, "imp"),
            (_make_spitter, _SPITTER_MOUTH_PATCH, _SPITTER_TAIL_PATCH, "spitter"),
            (_make_carapace, _CARAPACE_MOUTH_PATCH, _CARAPACE_TAIL_PATCH, "carapace_husk"),
        ],
    )
    def test_both_enabled_adds_exactly_two_parts(
        self,
        enemy_maker: object,
        mouth_patch: str,
        tail_patch: str,
        slug_name: str,
    ) -> None:
        """MTE-7-AC-3: both extras enabled adds exactly 2 parts for all 6 slugs."""
        baseline = enemy_maker({"mouth_enabled": False, "tail_enabled": False})
        baseline.parts = []
        with patch(mouth_patch, side_effect=lambda *a, **k: _fake_mesh()):
            with patch(tail_patch, side_effect=lambda *a, **k: _fake_mesh()):
                baseline.build_mesh_parts()
        baseline_count = len(baseline.parts)

        both = enemy_maker({
            "mouth_enabled": True, "mouth_shape": "fang",
            "tail_enabled": True, "tail_shape": "spike", "tail_length": 1.0,
        })
        both.parts = []
        with patch(mouth_patch, side_effect=lambda *a, **k: _fake_mesh()):
            with patch(tail_patch, side_effect=lambda *a, **k: _fake_mesh()):
                both.build_mesh_parts()

        assert len(both.parts) == baseline_count + 2, (
            f"slug '{slug_name}': both extras must add exactly 2 parts. "
            f"baseline={baseline_count}, got={len(both.parts)}"
        )


# ---------------------------------------------------------------------------
# Mutation guard: mouth_shape=None in geometry layer
# Exposes gap: even if options_for_enemy coerces None → "smile", the builder
# calls build_options.get("mouth_shape", "smile") directly. If None slips
# through (e.g. in unit tests that bypass options_for_enemy), str(None) == "None"
# which is an invalid shape and should fall through to fallback, not reach
# the geometry helper as the literal string "None".
# ---------------------------------------------------------------------------


class TestMouthShapeNoneInGeometryLayer:
    """Guard: mouth_enabled=True with mouth_shape=None in build_options.

    # CHECKPOINT: tests inject None directly into build_options, bypassing
    # options_for_enemy coercion. Conservative assumption: builder uses
    # self.build_options.get("mouth_shape", "smile") and str() coerces None
    # to "None". If builder does NOT str()-coerce, None stays None which would
    # cause create_mouth_mesh to receive None as shape. Both behaviors (passing
    # "None" string or None directly) are invalid per spec — shape must be
    # one of the 5 valid option values.
    """

    def test_spider_none_mouth_shape_does_not_reach_geometry_as_none_string(self) -> None:
        """If mouth_shape=None bypasses coercion, create_mouth_mesh must not receive 'None'."""
        spider = _make_spider({"mouth_enabled": True, "mouth_shape": None})
        spider.parts = []

        captured_shapes: list[str] = []

        def capture(shape: str, location: tuple, head_scale: float) -> MagicMock:
            captured_shapes.append(shape)
            return _fake_mesh()

        with patch(_SPIDER_MOUTH_PATCH, side_effect=capture):
            spider.build_mesh_parts()

        if captured_shapes:
            shape_arg = captured_shapes[0]
            assert shape_arg in ("smile", "grimace", "flat", "fang", "beak"), (
                f"Builder passed invalid shape '{shape_arg}' to create_mouth_mesh. "
                "None must default to 'smile' via builder's .get('mouth_shape', 'smile')."
            )
            assert shape_arg != "None", (
                "Builder must not pass the string 'None' to create_mouth_mesh."
            )

    def test_slug_none_tail_shape_does_not_reach_geometry_as_none_string(self) -> None:
        """If tail_shape=None bypasses coercion, create_tail_mesh must not receive 'None'."""
        slug = _make_slug({"tail_enabled": True, "tail_shape": None, "tail_length": 1.0})
        slug.parts = []

        captured_shapes: list[str] = []

        def capture(shape: str, length: float, location: tuple) -> MagicMock:
            captured_shapes.append(shape)
            return _fake_mesh()

        with patch(_SLUG_TAIL_PATCH, side_effect=capture):
            slug.build_mesh_parts()

        if captured_shapes:
            shape_arg = captured_shapes[0]
            assert shape_arg in ("spike", "whip", "club", "segmented", "curled"), (
                f"Builder passed invalid shape '{shape_arg}' to create_tail_mesh."
            )
            assert shape_arg != "None", (
                "Builder must not pass the string 'None' to create_tail_mesh."
            )

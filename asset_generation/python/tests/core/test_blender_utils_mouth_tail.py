"""create_mouth_mesh and create_tail_mesh dispatch tests (MTE-5, MTE-6).

Covers shape-dispatch branches in blender_utils to satisfy diff-cover for the
new mouth/tail geometry helpers added in ticket M25-06.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.core import creature_parts as cp

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_obj(name: str = "obj") -> MagicMock:
    return MagicMock(name=name)


LOC = (1.0, 0.0, 0.5)


# ---------------------------------------------------------------------------
# MTE-5: create_mouth_mesh shape dispatch
# ---------------------------------------------------------------------------


class TestCreateMouthMeshShapeDispatch:
    """Each mouth shape must call the correct primitive and return it."""

    def test_fang_calls_create_cone(self) -> None:
        fake = _fake_obj("fang_obj")
        with patch.object(cp, "create_cone", return_value=fake) as mock_cone:
            result = cp.create_mouth_mesh("fang", LOC, 1.0)
        assert result is fake
        mock_cone.assert_called_once()

    def test_beak_calls_create_cone(self) -> None:
        fake = _fake_obj("beak_obj")
        with patch.object(cp, "create_cone", return_value=fake) as mock_cone:
            result = cp.create_mouth_mesh("beak", LOC, 1.0)
        assert result is fake
        mock_cone.assert_called_once()

    def test_flat_calls_create_box(self) -> None:
        fake = _fake_obj("flat_obj")
        with patch.object(cp, "create_box", return_value=fake) as mock_box:
            result = cp.create_mouth_mesh("flat", LOC, 1.0)
        assert result is fake
        mock_box.assert_called_once()

    def test_grimace_calls_create_cylinder(self) -> None:
        fake = _fake_obj("grimace_obj")
        with patch.object(cp, "create_cylinder", return_value=fake) as mock_cyl:
            result = cp.create_mouth_mesh("grimace", LOC, 1.0)
        assert result is fake
        mock_cyl.assert_called_once()

    def test_smile_calls_create_cylinder(self) -> None:
        fake = _fake_obj("smile_obj")
        with patch.object(cp, "create_cylinder", return_value=fake) as mock_cyl:
            result = cp.create_mouth_mesh("smile", LOC, 1.0)
        assert result is fake
        mock_cyl.assert_called_once()

    def test_unknown_shape_falls_back_to_cylinder(self) -> None:
        """Unknown shapes fall back to smile (cylinder) — no exception."""
        fake = _fake_obj("fallback_obj")
        with patch.object(cp, "create_cylinder", return_value=fake) as mock_cyl:
            result = cp.create_mouth_mesh("NOT_A_REAL_SHAPE", LOC, 1.0)
        assert result is fake
        mock_cyl.assert_called_once()

    @pytest.mark.parametrize("shape", ["smile", "grimace", "flat", "fang", "beak"])
    def test_all_shapes_return_an_object(self, shape: str) -> None:
        fake = _fake_obj(shape)
        with (
            patch.object(cp, "create_cone", return_value=fake),
            patch.object(cp, "create_cylinder", return_value=fake),
            patch.object(cp, "create_box", return_value=fake),
            patch.object(cp, "create_sphere", return_value=fake),
        ):
            result = cp.create_mouth_mesh(shape, LOC, 1.0)
        assert result is fake

    def test_scale_constants_used_for_fang(self) -> None:
        """Verify named scale constants are applied (not zero) for fang shape."""
        fake = _fake_obj()
        with patch.object(cp, "create_cone", return_value=fake) as mock_cone:
            cp.create_mouth_mesh("fang", LOC, 1.0)
        call_kw = mock_cone.call_args.kwargs
        sx, sy, sz = call_kw["scale"]
        assert sx == pytest.approx(cp._MOUTH_FANG_X_RATIO)
        assert sz == pytest.approx(cp._MOUTH_FANG_Z_RATIO)

    def test_scale_constants_used_for_smile(self) -> None:
        """Verify named scale constants are applied for smile shape."""
        fake = _fake_obj()
        with patch.object(cp, "create_cylinder", return_value=fake) as mock_cyl:
            cp.create_mouth_mesh("smile", LOC, 1.0)
        call_kw = mock_cyl.call_args.kwargs
        sx, _sy, sz = call_kw["scale"]
        assert sx == pytest.approx(cp._MOUTH_SMILE_X_RATIO)
        assert sz == pytest.approx(cp._MOUTH_SMILE_Z_RATIO)


# ---------------------------------------------------------------------------
# MTE-6: create_tail_mesh shape dispatch
# ---------------------------------------------------------------------------


class TestCreateTailMeshShapeDispatch:
    """Each tail shape must call the correct primitive and return it."""

    def test_spike_calls_create_cone(self) -> None:
        fake = _fake_obj("spike_obj")
        with patch.object(cp, "create_cone", return_value=fake) as mock_cone:
            result = cp.create_tail_mesh("spike", 1.0, LOC)
        assert result is fake
        mock_cone.assert_called_once()

    def test_whip_calls_create_cylinder(self) -> None:
        fake = _fake_obj("whip_obj")
        with patch.object(cp, "create_cylinder", return_value=fake) as mock_cyl:
            result = cp.create_tail_mesh("whip", 1.0, LOC)
        assert result is fake
        mock_cyl.assert_called_once()

    def test_club_calls_create_sphere(self) -> None:
        fake = _fake_obj("club_obj")
        with patch.object(cp, "create_sphere", return_value=fake) as mock_sphere:
            result = cp.create_tail_mesh("club", 1.0, LOC)
        assert result is fake
        mock_sphere.assert_called_once()

    def test_segmented_calls_create_cylinder(self) -> None:
        fake = _fake_obj("seg_obj")
        with patch.object(cp, "create_cylinder", return_value=fake) as mock_cyl:
            result = cp.create_tail_mesh("segmented", 1.0, LOC)
        assert result is fake
        mock_cyl.assert_called_once()

    def test_curled_falls_back_to_create_sphere(self) -> None:
        """curled is the fallback (sphere) shape."""
        fake = _fake_obj("curled_obj")
        with patch.object(cp, "create_sphere", return_value=fake) as mock_sphere:
            result = cp.create_tail_mesh("curled", 1.0, LOC)
        assert result is fake
        mock_sphere.assert_called_once()

    def test_unknown_shape_falls_back_to_sphere(self) -> None:
        """Unknown shapes fall back to curled (sphere) — no exception."""
        fake = _fake_obj("fallback_obj")
        with patch.object(cp, "create_sphere", return_value=fake) as mock_sphere:
            result = cp.create_tail_mesh("UNKNOWN_SHAPE", 1.0, LOC)
        assert result is fake
        mock_sphere.assert_called_once()

    @pytest.mark.parametrize("shape", ["spike", "whip", "club", "segmented", "curled"])
    def test_all_shapes_return_an_object(self, shape: str) -> None:
        fake = _fake_obj(shape)
        with (
            patch.object(cp, "create_cone", return_value=fake),
            patch.object(cp, "create_cylinder", return_value=fake),
            patch.object(cp, "create_sphere", return_value=fake),
        ):
            result = cp.create_tail_mesh(shape, 1.0, LOC)
        assert result is fake

    def test_length_scales_spike_cone(self) -> None:
        """tail_length value is passed through to scale the spike geometry."""
        fake = _fake_obj()
        with patch.object(cp, "create_cone", return_value=fake) as mock_cone:
            cp.create_tail_mesh("spike", 2.0, LOC)
        call_kw = mock_cone.call_args.kwargs
        sx, sy, sz = call_kw["scale"]
        # length=2.0 scales radius by 2 * 0.25 = 0.5
        assert sx == pytest.approx(2.0 * 0.25)
        assert sy == pytest.approx(2.0 * 0.25)

    def test_whip_scale_constants_applied(self) -> None:
        """Verify named scale constants used for whip tail."""
        fake = _fake_obj()
        with patch.object(cp, "create_cylinder", return_value=fake) as mock_cyl:
            cp.create_tail_mesh("whip", 1.0, LOC)
        call_kw = mock_cyl.call_args.kwargs
        sx, sy, _sz = call_kw["scale"]
        assert sx == pytest.approx(cp._TAIL_WHIP_XY_RATIO)
        assert sy == pytest.approx(cp._TAIL_WHIP_XY_RATIO)

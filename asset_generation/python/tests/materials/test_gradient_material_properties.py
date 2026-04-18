"""Test gradient material properties are set correctly (metallic, roughness, etc)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.materials import material_system as ms


def test_gradient_zone_material_calls_create_with_zero_metallic() -> None:
    """_material_for_gradient_zone must call create_material with metallic=0.0."""
    with patch.object(ms, "create_material") as mock_create, patch.object(
        ms, "_add_uv_gradient_to_principled"
    ):
        mock_create.return_value = MagicMock()

        ms._material_for_gradient_zone(
            base_palette_name="blood_red",
            finish="default",
            grad_a_hex="ff0000",
            grad_b_hex="0000ff",
            direction="horizontal",
            zone_hex_fallback="ffffff",
            instance_suffix="test_grad",
        )

        args, kwargs = mock_create.call_args
        assert args[2] == 0.0, "Gradient material must pass metallic=0.0 (3rd positional arg)"
        assert 0.7 <= args[3] <= 0.8, "Roughness should be ~0.75 (4th positional arg)"
        assert kwargs.get("add_texture") is False, "Gradient material should disable add_texture"


def test_gradient_material_creates_without_texture() -> None:
    """_material_for_gradient_zone must call create_material with add_texture=False.

    The gradient texture is added separately via _add_uv_gradient_to_principled,
    not via the create_material texture handlers.
    """
    with patch.object(ms, "create_material") as mock_create, patch.object(
        ms, "_add_uv_gradient_to_principled"
    ):
        mock_create.return_value = MagicMock()

        ms._material_for_gradient_zone(
            base_palette_name="blood_red",
            finish="default",
            grad_a_hex="ff0000",
            grad_b_hex="0000ff",
            direction="horizontal",
            zone_hex_fallback="ffffff",
            instance_suffix="test",
        )

        args, kwargs = mock_create.call_args
        assert kwargs.get("add_texture") is False, "Gradient material should disable add_texture handler"


def test_gradient_material_with_invalid_palette_uses_fallback() -> None:
    """Invalid palette name should use fallback color (gray)."""
    with patch.object(ms, "create_material") as mock_create, patch.object(
        ms, "_add_uv_gradient_to_principled"
    ):
        mock_create.return_value = MagicMock()

        ms._material_for_gradient_zone(
            base_palette_name="nonexistent_palette",
            finish="default",
            grad_a_hex="ff0000",
            grad_b_hex="0000ff",
            direction="horizontal",
            zone_hex_fallback="",
            instance_suffix="test",
        )

        args, kwargs = mock_create.call_args
        color_a = args[1]
        assert len(color_a) == 4, "Color should be RGBA tuple"
        assert 0 <= color_a[0] <= 1, "Color values should be normalized [0, 1]"


def test_gradient_material_respects_finish_preset() -> None:
    """Non-default finish should set force_surface=True and use finish roughness."""
    with patch.object(ms, "create_material") as mock_create, patch.object(
        ms, "_add_uv_gradient_to_principled"
    ):
        mock_create.return_value = MagicMock()

        ms._material_for_gradient_zone(
            base_palette_name="blood_red",
            finish="metallic",
            grad_a_hex="ff0000",
            grad_b_hex="0000ff",
            direction="horizontal",
            zone_hex_fallback="ffffff",
            instance_suffix="test",
        )

        args, kwargs = mock_create.call_args
        assert kwargs.get("force_surface") is True, "Non-default finish should set force_surface=True"
        assert args[2] == 0.0, "Gradient metallic must always be 0.0 regardless of finish"


def test_gradient_material_calls_add_uv_gradient() -> None:
    """_material_for_gradient_zone must call _add_uv_gradient_to_principled."""
    with patch.object(ms, "create_material") as mock_create, patch.object(
        ms, "_add_uv_gradient_to_principled"
    ) as mock_gradient:
        mat = MagicMock()
        mock_create.return_value = mat

        ms._material_for_gradient_zone(
            base_palette_name="blood_red",
            finish="default",
            grad_a_hex="ff0000",
            grad_b_hex="0000ff",
            direction="vertical",
            zone_hex_fallback="ffffff",
            instance_suffix="test_grad",
        )

        mock_gradient.assert_called_once()
        call_args = mock_gradient.call_args
        assert call_args[0][0] is mat, "First arg should be the material"
        assert call_args[0][3] == "vertical", "Direction should be passed to gradient function"

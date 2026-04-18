"""Per-zone texture (feat_body_texture_*) — adversarial coercion and mutation-guard tests."""

import json

from src.utils.animated_build_options import options_for_enemy

_B = "feat_body_texture_"


class TestTextureModeCoercionAdversarial:
    def test_whitespace_padded_gradient_mode_strips_and_coerces(self) -> None:
        o = options_for_enemy("slug", {f"{_B}mode": "  gradient  "})
        assert o[f"{_B}mode"] == "gradient"

    def test_none_texture_mode_falls_back_to_none(self) -> None:
        o = options_for_enemy("slug", {f"{_B}mode": None})
        assert o[f"{_B}mode"] == "none"

    def test_list_texture_mode_falls_back_to_none(self) -> None:
        o = options_for_enemy("slug", {f"{_B}mode": ["gradient"]})
        assert o[f"{_B}mode"] == "none"


class TestGradDirectionCoercionAdversarial:
    def test_whitespace_padded_radial_direction_strips_and_coerces(self) -> None:
        o = options_for_enemy("spider", {f"{_B}grad_direction": "  radial "})
        assert o[f"{_B}grad_direction"] == "radial"

    def test_uppercase_vertical_direction_coerces_to_lowercase(self) -> None:
        o = options_for_enemy("spider", {f"{_B}grad_direction": "VERTICAL"})
        assert o[f"{_B}grad_direction"] == "vertical"

    def test_none_grad_direction_falls_back_to_horizontal(self) -> None:
        o = options_for_enemy("spider", {f"{_B}grad_direction": None})
        assert o[f"{_B}grad_direction"] == "horizontal"


class TestSpotDensityCoercionAdversarial:
    def test_spot_density_string_numeric_is_coerced(self) -> None:
        o = options_for_enemy("slug", {f"{_B}spot_density": "2.25"})
        assert o[f"{_B}spot_density"] == 2.25
        assert type(o[f"{_B}spot_density"]) is float

    def test_spot_density_nan_falls_back_to_default(self) -> None:
        o = options_for_enemy("slug", {f"{_B}spot_density": float("nan")})
        assert o[f"{_B}spot_density"] == 1.0

    def test_spot_density_positive_infinity_clamped_to_max(self) -> None:
        o = options_for_enemy("slug", {f"{_B}spot_density": float("inf")})
        assert o[f"{_B}spot_density"] == 5.0

    def test_spot_density_negative_infinity_clamped_to_min(self) -> None:
        o = options_for_enemy("slug", {f"{_B}spot_density": float("-inf")})
        assert o[f"{_B}spot_density"] == 0.1


class TestStripeWidthCoercionAdversarial:
    def test_stripe_width_string_numeric_is_coerced(self) -> None:
        o = options_for_enemy("slug", {f"{_B}stripe_width": "0.35"})
        assert o[f"{_B}stripe_width"] == 0.35
        assert type(o[f"{_B}stripe_width"]) is float

    def test_stripe_width_nan_falls_back_to_default(self) -> None:
        o = options_for_enemy("slug", {f"{_B}stripe_width": float("nan")})
        assert o[f"{_B}stripe_width"] == 0.2

    def test_stripe_width_positive_infinity_clamped_to_max(self) -> None:
        o = options_for_enemy("slug", {f"{_B}stripe_width": float("inf")})
        assert o[f"{_B}stripe_width"] == 1.0

    def test_stripe_width_negative_infinity_clamped_to_min(self) -> None:
        o = options_for_enemy("slug", {f"{_B}stripe_width": float("-inf")})
        assert o[f"{_B}stripe_width"] == 0.05


class TestInputMutationGuards:
    def test_options_for_enemy_does_not_mutate_input_dict(self) -> None:
        params = {
            f"{_B}mode": "spots",
            f"{_B}spot_density": 3.0,
            f"{_B}spot_color": "aabbcc",
        }
        params_before = json.loads(json.dumps(params))
        _ = options_for_enemy("spider", params)
        assert params == params_before

    def test_options_for_enemy_does_not_mutate_nested_input_objects(self) -> None:
        params = {
            f"{_B}mode": "gradient",
            f"{_B}grad_color_a": "ff0000",
            "unknown": {"x": 1, "y": [1, 2, 3]},
        }
        before = json.loads(json.dumps(params))
        _ = options_for_enemy("slug", params)
        assert params == before

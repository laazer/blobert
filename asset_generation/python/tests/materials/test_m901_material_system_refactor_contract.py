"""Behavioral contracts for M901-05 material system decomposition."""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest


def _load(module_path: str):
    """Import helper with a concise assertion surface for module contracts."""
    return importlib.import_module(module_path)


def test_refactor_modules_import_without_blender_runtime_context() -> None:
    _load("src.materials.presets")
    _load("src.materials.texture_handlers")
    _load("src.materials.feature_zones")
    _load("src.materials.material_lookup")
    _load("src.materials.system")


def test_system_public_api_contract_is_present() -> None:
    system = _load("src.materials.system")
    assert callable(system.setup_materials)
    assert callable(system.get_enemy_materials)
    assert callable(system.apply_material_to_object)


def test_legacy_material_system_path_preserves_public_api() -> None:
    legacy = _load("src.materials.material_system")
    assert callable(legacy.setup_materials)
    assert callable(legacy.get_enemy_materials)
    assert callable(legacy.apply_material_to_object)


def test_texture_handler_registration_rejects_non_callables() -> None:
    handlers = _load("src.materials.texture_handlers")
    with pytest.raises((TypeError, ValueError)):
        handlers.register_handler("broken", "not-a-callable")


def test_texture_handler_unknown_type_is_noop_for_material() -> None:
    handlers = _load("src.materials.texture_handlers")
    marker = SimpleNamespace(name="material-marker")
    result = handlers.apply_texture("unregistered_type", marker, None, None, None, (1, 1, 1, 1))
    assert result is marker


def test_feature_slot_overrides_return_derived_copy_not_mutation() -> None:
    zones = _load("src.materials.feature_zones")
    base = SimpleNamespace(name="Organic_Brown")
    original = {"body": base, "head": base, "limbs": base}
    got = zones.apply_feature_slot_overrides(
        original,
        {"body": {"finish": "matte", "hex": "aabbcc"}},
    )
    assert got is not original
    assert original["body"] is base
    assert got["head"] is base
    assert got["limbs"] is base


def test_feature_slot_overrides_nested_color_image_uses_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Image mode reads nested color_image (schema shape), not only flat build keys."""
    zones = _load("src.materials.feature_zones")
    base = SimpleNamespace(name="Organic_Brown")
    original = {"body": base}
    called: dict[str, str] = {}

    def _fake_color_image(**kwargs):
        called["asset_id"] = str(kwargs.get("asset_id", ""))
        return SimpleNamespace(name="ImgOverride")

    monkeypatch.setattr(zones, "_material_for_color_image_zone", _fake_color_image)
    got = zones.apply_feature_slot_overrides(
        original,
        {
            "body": {
                "color_image": {"mode": "image", "id": "demo_textures3"},
            }
        },
    )
    assert called["asset_id"] == "demo_textures3"
    assert got["body"].name == "ImgOverride"


def test_feature_slot_overrides_ignore_non_dict_feature_entries() -> None:
    zones = _load("src.materials.feature_zones")
    base = SimpleNamespace(name="Bone_White")
    original = {"limbs": base}
    got = zones.apply_feature_slot_overrides(original, {"limbs": "invalid-shape"})
    assert got["limbs"] is base


def test_zone_texture_density_clamped_before_spots_material_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    zones = _load("src.materials.feature_zones")
    base = SimpleNamespace(name="Organic_Brown")
    slots = {"body": base}
    captured: dict[str, float] = {}

    def _capture_spots(**kwargs):
        captured["density"] = kwargs["density"]
        return base

    monkeypatch.setattr(zones, "_material_for_spots_zone", _capture_spots)
    zones.apply_zone_texture_pattern_overrides(
        slots,
        {
            "feat_body_texture_mode": "spots",
            "feat_body_texture_spot_density": 999,
            "features": {"body": {"finish": "default", "hex": ""}},
        },
    )
    assert captured["density"] == 5.0


@pytest.mark.parametrize("raw_rot", [float("inf"), float("-inf"), float("nan"), 9999.0, -9999.0])
def test_zone_texture_stripe_rotation_values_sanitized(monkeypatch: pytest.MonkeyPatch, raw_rot: float) -> None:
    zones = _load("src.materials.feature_zones")
    base = SimpleNamespace(name="Organic_Brown")
    slots = {"body": base}
    captured: dict[str, float] = {}

    def _capture_stripes(**kwargs):
        captured["yaw"] = kwargs["rot_yaw_deg"]
        captured["pitch"] = kwargs["rot_pitch_deg"]
        return base

    monkeypatch.setattr(zones, "_material_for_stripes_zone", _capture_stripes)
    zones.apply_zone_texture_pattern_overrides(
        slots,
        {
            "feat_body_texture_mode": "stripes",
            "feat_body_texture_stripe_rot_yaw": raw_rot,
            "feat_body_texture_stripe_rot_pitch": raw_rot,
            "features": {"body": {"finish": "default", "hex": ""}},
        },
    )
    assert -360.0 <= captured["yaw"] <= 360.0
    assert -360.0 <= captured["pitch"] <= 360.0


def test_material_lookup_unknown_enemy_returns_expected_base_slots() -> None:
    lookup = _load("src.materials.material_lookup")
    palette = {
        "Organic_Brown": SimpleNamespace(name="Organic_Brown"),
        "Flesh_Pink": SimpleNamespace(name="Flesh_Pink"),
        "Bone_White": SimpleNamespace(name="Bone_White"),
    }
    got = lookup.get_materials_for_enemy_type("unknown_enemy_type_m901_05", palette, rng=None)
    assert set(("body", "head", "limbs")).issubset(got.keys())


def test_texture_handler_registry_dispatches_latest_registration() -> None:
    handlers = _load("src.materials.texture_handlers")
    marker = SimpleNamespace(name="dispatch-marker")
    calls: list[str] = []

    def _first(*_args, **_kwargs):
        calls.append("first")
        return marker

    def _second(*_args, **_kwargs):
        calls.append("second")
        return marker

    handlers.register_handler("m901_dispatch", _first)
    handlers.register_handler("m901_dispatch", _second)

    got = handlers.apply_texture("m901_dispatch", marker, None, None, None, (1, 1, 1, 1))
    assert got is marker
    assert calls == ["second"]


def test_feature_zone_part_override_precedence_part_over_zone_over_base(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    zones = _load("src.materials.feature_zones")
    base = SimpleNamespace(name="Organic_Brown")
    slot_materials = {"body": base}
    features = {
        "body": {
            "finish": "metallic",
            "hex": "112233",
            "parts": {
                "jaw": {
                    "finish": "default",
                    "hex": "abcdef",
                }
            },
        }
    }
    captured: dict[str, str] = {}

    def _capture_finish_hex(**kwargs):
        captured["finish"] = kwargs["finish"]
        captured["hex_str"] = kwargs["hex_str"]
        return SimpleNamespace(name="PartOverride")

    monkeypatch.setattr(zones, "_material_for_finish_hex", _capture_finish_hex)
    got = zones.material_for_zone_part("body", "jaw", slot_materials, features)
    assert got.name == "PartOverride"
    assert captured["finish"] == "metallic"
    assert captured["hex_str"] == "abcdef"


def test_feature_zone_spots_invalid_density_does_not_raise_and_keeps_base_material() -> None:
    zones = _load("src.materials.feature_zones")
    base = SimpleNamespace(name="Organic_Brown")
    slot_materials = {"body": base}
    got = zones.apply_zone_texture_pattern_overrides(
        slot_materials,
        {
            "feat_body_texture_mode": "spots",
            "feat_body_texture_spot_density": "not-a-float",
            "features": {"body": {"finish": "default", "hex": ""}},
        },
    )
    assert got["body"] is base


def test_material_lookup_unknown_enemy_is_deterministic_across_palette_order() -> None:
    lookup = _load("src.materials.material_lookup")
    a = SimpleNamespace(name="Organic_Brown")
    b = SimpleNamespace(name="Flesh_Pink")
    c = SimpleNamespace(name="Bone_White")
    palette_a = {
        "Organic_Brown": a,
        "Flesh_Pink": b,
        "Bone_White": c,
    }
    palette_b = {
        "Bone_White": c,
        "Organic_Brown": a,
        "Flesh_Pink": b,
    }

    # CHECKPOINT: Conservative assumption per R5 fallback semantics:
    # unknown enemy lookup should not depend on source dict iteration order.
    got_a = lookup.get_materials_for_enemy_type("unknown_enemy_type_m901_05", palette_a, rng=None)
    got_b = lookup.get_materials_for_enemy_type("unknown_enemy_type_m901_05", palette_b, rng=None)
    assert got_a.keys() == got_b.keys()
    assert got_a["body"] is got_b["body"]
    assert got_a["head"] is got_b["head"]
    assert got_a["limbs"] is got_b["limbs"]


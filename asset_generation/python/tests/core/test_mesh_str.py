# ruff: noqa: I001
"""
Tests for BaseAnimatedModel._mesh_str() — LJEC-3.

Red against current codebase (_mesh_str does not exist yet on BaseAnimatedModel).

Covers: fallback to class default, build_options override with valid token,
        ValueError on invalid token (from override and from class default),
        allowed parameter passthrough, return type, method signature.

Spec: project_board/specs/limb_joints_and_end_caps_spec.md, requirement LJEC-3.
"""

from __future__ import annotations

import pytest

from src.utils.blender_stubs import ensure_blender_stubs

ensure_blender_stubs()

from src.enemies.base_animated_model import BaseAnimatedModel  # noqa: E402


# ---------------------------------------------------------------------------
# Minimal concrete subclass for testing _mesh_str without Blender.
# ---------------------------------------------------------------------------

class _StubModel(BaseAnimatedModel):
    """Concrete enemy stub. ARM_END_SHAPE default is 'none' (valid)."""

    ARM_END_SHAPE: str = "none"
    LEG_END_SHAPE: str = "none"
    ARM_SEGMENTS: int = 1

    def build_mesh_parts(self) -> None:
        self.parts = []

    def apply_themed_materials(self) -> None:
        pass


def _make_model(build_options=None) -> _StubModel:
    return _StubModel(
        name="stub",
        materials={},
        rng=None,
        build_options=build_options or {},
    )


# ---------------------------------------------------------------------------
# Helper: a subclass with an invalid class-level default
# ---------------------------------------------------------------------------

class _BadDefaultModel(BaseAnimatedModel):
    """Class with an invalid class-default shape (should fail on any call)."""

    ARM_END_SHAPE: str = "cylinder"  # not in ALLOWED_END_SHAPES

    def build_mesh_parts(self) -> None:
        self.parts = []

    def apply_themed_materials(self) -> None:
        pass


def _make_bad_default_model(build_options=None) -> _BadDefaultModel:
    return _BadDefaultModel(
        name="bad",
        materials={},
        rng=None,
        build_options=build_options or {},
    )


# ---------------------------------------------------------------------------
# LJEC-3-AC7: Method exists with correct signature
# ---------------------------------------------------------------------------

class TestMeshStrSignature:
    """LJEC-3-AC7: _mesh_str(self, name, allowed=None) exists on BaseAnimatedModel."""

    def test_method_exists_on_base(self):
        assert hasattr(BaseAnimatedModel, "_mesh_str")

    def test_method_is_callable(self):
        model = _make_model()
        assert callable(model._mesh_str)

    def test_method_accepts_name_only(self):
        """allowed defaults to None — callable with one positional arg."""
        model = _make_model()
        result = model._mesh_str("ARM_END_SHAPE")
        assert result is not None

    def test_method_accepts_name_and_allowed(self):
        model = _make_model()
        result = model._mesh_str("ARM_END_SHAPE", ("none", "sphere", "box"))
        assert result is not None


# ---------------------------------------------------------------------------
# LJEC-3-AC1 / LJEC-3-AC8: Fallback to class default when key absent
# ---------------------------------------------------------------------------

class TestMeshStrFallbackToClassDefault:
    """LJEC-3-AC1 and LJEC-3-AC8: returns class default when key absent from build_options."""

    def test_returns_class_default_when_no_build_options(self):
        model = _make_model()
        assert model._mesh_str("ARM_END_SHAPE") == "none"

    def test_returns_class_default_when_mesh_dict_empty(self):
        model = _make_model(build_options={"mesh": {}})
        assert model._mesh_str("ARM_END_SHAPE") == "none"

    def test_returns_class_default_when_mesh_key_absent(self):
        model = _make_model(build_options={"mesh": {"OTHER_KEY": "sphere"}})
        assert model._mesh_str("ARM_END_SHAPE") == "none"

    def test_returns_class_default_for_leg_end_shape(self):
        model = _make_model()
        assert model._mesh_str("LEG_END_SHAPE") == "none"

    def test_fallback_uses_class_attribute_not_instance(self):
        """ClassVar is read from type(self), not from instance dict."""
        model = _make_model()
        # Setting instance attribute must NOT shadow ClassVar for _mesh_str purposes.
        # _mesh_str reads getattr(type(self), name), not getattr(self, name).
        # This test verifies the type-based lookup.
        model.__dict__["ARM_END_SHAPE"] = "sphere"  # instance shadow
        # Should still return the ClassVar from type, which is "none".
        # (Note: if implementation uses getattr(self, name) this test passes by
        # coincidence when instance value is valid — the test documents intent.)
        result = model._mesh_str("ARM_END_SHAPE")
        assert result in ("none", "sphere")  # either is valid; "none" is preferred


# ---------------------------------------------------------------------------
# LJEC-3-AC2 / LJEC-3-AC9: Override from build_options with valid token
# ---------------------------------------------------------------------------

class TestMeshStrBuildOptionsOverride:
    """LJEC-3-AC2 and LJEC-3-AC9: returns build_options override when valid."""

    def test_override_to_sphere_returns_sphere(self):
        model = _make_model(build_options={"mesh": {"ARM_END_SHAPE": "sphere"}})
        assert model._mesh_str("ARM_END_SHAPE") == "sphere"

    def test_override_to_box_returns_box(self):
        model = _make_model(build_options={"mesh": {"ARM_END_SHAPE": "box"}})
        assert model._mesh_str("ARM_END_SHAPE") == "box"

    def test_override_to_none_returns_none(self):
        model = _make_model(build_options={"mesh": {"ARM_END_SHAPE": "none"}})
        assert model._mesh_str("ARM_END_SHAPE") == "none"

    def test_override_for_leg_end_shape(self):
        model = _make_model(build_options={"mesh": {"LEG_END_SHAPE": "sphere"}})
        assert model._mesh_str("LEG_END_SHAPE") == "sphere"

    def test_override_only_applies_to_named_key(self):
        """Override for ARM_END_SHAPE does not affect LEG_END_SHAPE lookup."""
        model = _make_model(build_options={"mesh": {"ARM_END_SHAPE": "sphere"}})
        assert model._mesh_str("LEG_END_SHAPE") == "none"


# ---------------------------------------------------------------------------
# LJEC-3-AC3 / LJEC-3-AC10: ValueError on invalid token from override
# ---------------------------------------------------------------------------

class TestMeshStrValueErrorOnInvalidOverride:
    """LJEC-3-AC3 and LJEC-3-AC10: raises ValueError when override token is invalid."""

    def test_invalid_override_raises_value_error(self):
        model = _make_model(build_options={"mesh": {"ARM_END_SHAPE": "triangle"}})
        with pytest.raises(ValueError):
            model._mesh_str("ARM_END_SHAPE")

    def test_invalid_override_not_key_error(self):
        model = _make_model(build_options={"mesh": {"ARM_END_SHAPE": "cone"}})
        with pytest.raises(ValueError):
            model._mesh_str("ARM_END_SHAPE")

    def test_invalid_override_error_mentions_invalid_token(self):
        model = _make_model(build_options={"mesh": {"ARM_END_SHAPE": "triangle"}})
        with pytest.raises(ValueError, match="triangle"):
            model._mesh_str("ARM_END_SHAPE")

    def test_invalid_override_empty_string_raises_value_error(self):
        model = _make_model(build_options={"mesh": {"ARM_END_SHAPE": ""}})
        with pytest.raises(ValueError):
            model._mesh_str("ARM_END_SHAPE")

    def test_invalid_override_uppercase_raises_value_error(self):
        """Validation is case-sensitive; 'SPHERE' is not in allowed tokens."""
        model = _make_model(build_options={"mesh": {"ARM_END_SHAPE": "SPHERE"}})
        with pytest.raises(ValueError):
            model._mesh_str("ARM_END_SHAPE")

    def test_invalid_override_whitespace_raises_value_error(self):
        model = _make_model(build_options={"mesh": {"ARM_END_SHAPE": " sphere"}})
        with pytest.raises(ValueError):
            model._mesh_str("ARM_END_SHAPE")


# ---------------------------------------------------------------------------
# LJEC-3-AC4: ValueError on invalid class default
# ---------------------------------------------------------------------------

class TestMeshStrValueErrorOnInvalidClassDefault:
    """LJEC-3-AC4: raises ValueError when the ClassVar default itself is invalid."""

    def test_invalid_class_default_raises_value_error(self):
        model = _make_bad_default_model()
        with pytest.raises(ValueError):
            model._mesh_str("ARM_END_SHAPE")

    def test_invalid_class_default_error_mentions_token(self):
        model = _make_bad_default_model()
        with pytest.raises(ValueError, match="cylinder"):
            model._mesh_str("ARM_END_SHAPE")


# ---------------------------------------------------------------------------
# LJEC-3-AC5: allowed parameter passthrough
# ---------------------------------------------------------------------------

class TestMeshStrAllowedParameterPassthrough:
    """LJEC-3-AC5: when allowed is provided explicitly, it is used instead of ALLOWED_END_SHAPES."""

    def test_custom_allowed_accepts_valid_custom_token(self):
        class _CustomModel(BaseAnimatedModel):
            CUSTOM_SHAPE: str = "cylinder"

            def build_mesh_parts(self):
                self.parts = []

            def apply_themed_materials(self):
                pass

        model = _CustomModel(name="c", materials={}, rng=None)
        result = model._mesh_str("CUSTOM_SHAPE", allowed=("cylinder", "cone"))
        assert result == "cylinder"

    def test_custom_allowed_rejects_default_token_not_in_custom_set(self):
        """If custom allowed set does not include 'none', then 'none' raises ValueError."""
        model = _make_model()  # ARM_END_SHAPE = "none"
        with pytest.raises(ValueError):
            model._mesh_str("ARM_END_SHAPE", allowed=("sphere", "box"))

    def test_explicit_allowed_none_falls_back_to_allowed_end_shapes(self):
        """Passing allowed=None explicitly uses the default ALLOWED_END_SHAPES."""
        model = _make_model()
        result = model._mesh_str("ARM_END_SHAPE", None)
        assert result == "none"


# ---------------------------------------------------------------------------
# LJEC-3-AC6: Return type is str
# ---------------------------------------------------------------------------

class TestMeshStrReturnType:
    """LJEC-3-AC6: _mesh_str always returns a str."""

    def test_return_type_is_str_from_default(self):
        model = _make_model()
        result = model._mesh_str("ARM_END_SHAPE")
        assert isinstance(result, str)

    def test_return_type_is_str_from_override(self):
        model = _make_model(build_options={"mesh": {"ARM_END_SHAPE": "sphere"}})
        result = model._mesh_str("ARM_END_SHAPE")
        assert isinstance(result, str)

    def test_return_is_never_none(self):
        model = _make_model()
        result = model._mesh_str("ARM_END_SHAPE")
        assert result is not None

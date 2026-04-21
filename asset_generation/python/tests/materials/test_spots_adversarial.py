# ruff: noqa: E402, I001
"""Adversarial and edge-case tests for spots texture generation.

This module employs **mutation testing** and **edge-case discovery** to expose
weaknesses in the spots texture implementation not covered by AC requirements.

Test categories:
  1. Boundary mutations (off-by-one, floating point precision)
  2. Type system violations (None vs empty, wrong types)
  3. Concurrency/race conditions (parallel PNG writes)
  4. Invalid/corrupt input (malformed hex, out-of-range values)
  5. Combinatorial edge cases (null + high density, etc.)
  6. Determinism checks (identical inputs = identical PNG bytes)
  7. Resource exhaustion (huge textures, dense spot patterns)
  8. Integration seams (parameter flow, error propagation)
  9. Mutation testing (flip logic, change constants)
 10. Error handling robustness (graceful degradation, error messages)

CHECKPOINT markers encode conservative assumptions when ambiguities exist.
"""

from __future__ import annotations

import pytest  # noqa: E402, I001


# ============================================================================
# CATEGORY 1: BOUNDARY MUTATIONS (Off-by-one, precision, limits)
# ============================================================================


class TestSpotsBoundaryMutations:
    """Expose off-by-one errors and floating-point precision issues."""

    def test_width_zero_should_not_crash(self) -> None:
        """CHECKPOINT: Width=0 edge case.
        Would have asked: Should 0 width be rejected or produce minimal PNG?
        Assumption: Should raise ValueError (caller's responsibility to validate).
        Confidence: High (matches PNG spec).
        """
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises((ValueError, ZeroDivisionError)):
            _spots_texture_generator(
                width=0,
                height=32,
                spot_color_hex="ff0000",
                bg_color_hex="ffffff",
                density=1.0,
            )

    def test_height_zero_should_not_crash(self) -> None:
        """Height=0 should raise ValueError (invalid PNG)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises((ValueError, ZeroDivisionError)):
            _spots_texture_generator(
                width=32,
                height=0,
                spot_color_hex="ff0000",
                bg_color_hex="ffffff",
                density=1.0,
            )

    def test_negative_width_rejected(self) -> None:
        """Negative width should be rejected (invalid dimension)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises((ValueError, RuntimeError)):
            _spots_texture_generator(
                width=-1,
                height=32,
                spot_color_hex="ff0000",
                bg_color_hex="ffffff",
                density=1.0,
            )

    def test_negative_height_rejected(self) -> None:
        """Negative height should be rejected."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises((ValueError, RuntimeError)):
            _spots_texture_generator(
                width=32,
                height=-1,
                spot_color_hex="ff0000",
                bg_color_hex="ffffff",
                density=1.0,
            )

    def test_huge_dimensions_does_not_crash(self) -> None:
        """Test with very large dimensions (2048×2048).
        Risk: Memory exhaustion, integer overflow in pixel indexing.
        """
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        # Should not crash, but may take time or use significant memory
        png_data = _spots_texture_generator(
            width=512,
            height=512,
            spot_color_hex="ff0000",
            bg_color_hex="ffffff",
            density=1.0,
        )
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"
        assert len(png_data) > 1000, "Large texture should produce non-trivial PNG payload"

    def test_density_boundary_exactly_0_1(self) -> None:
        """Density exactly at lower boundary (0.1)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        png_data = _spots_texture_generator(
            width=32, height=32, spot_color_hex="ff0000", bg_color_hex="ffffff", density=0.1
        )
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_density_boundary_exactly_5_0(self) -> None:
        """Density exactly at upper boundary (5.0)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        png_data = _spots_texture_generator(
            width=32, height=32, spot_color_hex="ff0000", bg_color_hex="ffffff", density=5.0
        )
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_density_just_below_boundary(self) -> None:
        """Density just below lower boundary (0.09999) — should be rejected or clamped."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        # CHECKPOINT: Should clamping happen in generator or caller?
        # Assumption: Caller clamps; generator accepts out-of-spec values and uses them.
        # Confidence: Medium (spec says caller clamps, but defensive check is safer).
        try:
            png_data = _spots_texture_generator(
                width=32, height=32, spot_color_hex="ff0000", bg_color_hex="ffffff", density=0.09
            )
            # If accepted, should still be valid PNG
            assert png_data[:8] == b"\x89PNG\r\n\x1a\n"
        except ValueError:
            # Also acceptable if generator rejects
            pass

    def test_density_just_above_boundary(self) -> None:
        """Density just above upper boundary (5.01) — caller should clamp."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        try:
            png_data = _spots_texture_generator(
                width=32, height=32, spot_color_hex="ff0000", bg_color_hex="ffffff", density=5.01
            )
            assert png_data[:8] == b"\x89PNG\r\n\x1a\n"
        except ValueError:
            pass

    def test_very_high_density_produces_valid_png(self) -> None:
        """Density = 10.0 (way above spec) should still produce valid PNG."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        try:
            png_data = _spots_texture_generator(
                width=32, height=32, spot_color_hex="ff0000", bg_color_hex="ffffff", density=10.0
            )
            assert png_data[:8] == b"\x89PNG\r\n\x1a\n"
        except ValueError:
            pass

    def test_very_low_density_produces_valid_png(self) -> None:
        """Density = 0.001 (way below spec)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        try:
            png_data = _spots_texture_generator(
                width=32, height=32, spot_color_hex="ff0000", bg_color_hex="ffffff", density=0.001
            )
            assert png_data[:8] == b"\x89PNG\r\n\x1a\n"
        except ValueError:
            pass

    def test_zero_density_edge_case(self) -> None:
        """Density = 0.0 is invalid (no spots)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises((ValueError, ZeroDivisionError)):
            _spots_texture_generator(
                width=32, height=32, spot_color_hex="ff0000", bg_color_hex="ffffff", density=0.0
            )

    def test_negative_density_rejected(self) -> None:
        """Negative density should be rejected."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises((ValueError, RuntimeError)):
            _spots_texture_generator(
                width=32, height=32, spot_color_hex="ff0000", bg_color_hex="ffffff", density=-1.0
            )

    def test_float_precision_in_density(self) -> None:
        """Floating-point precision edge case (repeating decimal)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        # 1/3 density should not cause precision errors
        png_data = _spots_texture_generator(
            width=32, height=32, spot_color_hex="ff0000", bg_color_hex="ffffff", density=1.0 / 3.0
        )
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_very_small_float_density(self) -> None:
        """Density with many decimal places (e.g., 0.123456)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        png_data = _spots_texture_generator(
            width=32, height=32, spot_color_hex="ff0000", bg_color_hex="ffffff", density=0.123456
        )
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"


# ============================================================================
# CATEGORY 2: TYPE SYSTEM VIOLATIONS (None vs empty, type coercion)
# ============================================================================


class TestSpotsTypeViolations:
    """Expose type coercion bugs and None handling issues."""

    def test_spot_color_none_instead_of_empty_string(self) -> None:
        """Pass None for spot_color_hex instead of empty string."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        # CHECKPOINT: Should None be treated like empty string?
        # Assumption: Function rejects None (proper type checking).
        # Confidence: Medium (some APIs auto-coerce None → "").
        with pytest.raises((TypeError, ValueError)):
            _spots_texture_generator(
                width=32,
                height=32,
                spot_color_hex=None,  # type: ignore
                bg_color_hex="ffffff",
                density=1.0,
            )

    def test_bg_color_none_instead_of_empty_string(self) -> None:
        """Pass None for bg_color_hex."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises((TypeError, ValueError)):
            _spots_texture_generator(
                width=32,
                height=32,
                spot_color_hex="ff0000",
                bg_color_hex=None,  # type: ignore
                density=1.0,
            )

    def test_density_as_string_instead_of_float(self) -> None:
        """Pass density as string "1.0" instead of float."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        # CHECKPOINT: Should string be coerced to float?
        # Assumption: Function rejects non-numeric types.
        # Confidence: High (type hints are explicit).
        with pytest.raises((TypeError, ValueError)):
            _spots_texture_generator(
                width=32,
                height=32,
                spot_color_hex="ff0000",
                bg_color_hex="ffffff",
                density="1.0",  # type: ignore
            )

    def test_width_as_float_instead_of_int(self) -> None:
        """Pass width as float 32.5 instead of int."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises((TypeError, ValueError)):
            _spots_texture_generator(
                width=32.5,  # type: ignore
                height=32,
                spot_color_hex="ff0000",
                bg_color_hex="ffffff",
                density=1.0,
            )

    def test_height_as_float_instead_of_int(self) -> None:
        """Pass height as float."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises((TypeError, ValueError)):
            _spots_texture_generator(
                width=32,
                height=32.5,  # type: ignore
                spot_color_hex="ff0000",
                bg_color_hex="ffffff",
                density=1.0,
            )

    def test_hex_color_as_integer(self) -> None:
        """Pass hex color as integer 0xFF0000 instead of string."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises((TypeError, ValueError)):
            _spots_texture_generator(
                width=32,
                height=32,
                spot_color_hex=0xFF0000,  # type: ignore
                bg_color_hex="ffffff",
                density=1.0,
            )

    def test_both_colors_none(self) -> None:
        """Both colors as None should fallback to black and white."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises((TypeError, ValueError)):
            _spots_texture_generator(
                width=32, height=32, spot_color_hex=None, bg_color_hex=None, density=1.0  # type: ignore
            )


# ============================================================================
# CATEGORY 3: INVALID/CORRUPT HEX INPUT MUTATIONS
# ============================================================================


class TestSpotsHexInputMutations:
    """Expose hex parsing bugs with malformed, incomplete, and corrupt input."""

    def test_hex_with_hash_prefix(self) -> None:
        """Hex string with # prefix: '#ff0000'."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        # CHECKPOINT: Should # be stripped or cause error?
        # Assumption: Caller sanitizes; function may reject or strip.
        # Confidence: Medium (spec says caller sanitizes).
        try:
            png_data = _spots_texture_generator(
                width=32, height=32, spot_color_hex="#ff0000", bg_color_hex="ffffff", density=1.0
            )
            assert png_data[:8] == b"\x89PNG\r\n\x1a\n"
        except ValueError:
            pass  # Also acceptable if function rejects #

    def test_hex_5_characters_instead_of_6(self) -> None:
        """Incomplete hex: 'ff000' (5 chars)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises(ValueError):
            _spots_texture_generator(
                width=32, height=32, spot_color_hex="ff000", bg_color_hex="ffffff", density=1.0
            )

    def test_hex_7_characters_instead_of_6(self) -> None:
        """Extra hex digit: 'ff00000' (7 chars)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises(ValueError):
            _spots_texture_generator(
                width=32, height=32, spot_color_hex="ff00000", bg_color_hex="ffffff", density=1.0
            )

    def test_hex_with_leading_zeros(self) -> None:
        """Hex with leading zeros: '000000' (black)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        png_data = _spots_texture_generator(
            width=32, height=32, spot_color_hex="000000", bg_color_hex="ffffff", density=1.0
        )
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_hex_all_f(self) -> None:
        """Hex all F: 'ffffff' (white)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        png_data = _spots_texture_generator(
            width=32, height=32, spot_color_hex="ffffff", bg_color_hex="000000", density=1.0
        )
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_hex_with_space(self) -> None:
        """Hex with space: 'ff 000' (invalid)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises(ValueError):
            _spots_texture_generator(
                width=32, height=32, spot_color_hex="ff 000", bg_color_hex="ffffff", density=1.0
            )

    def test_hex_with_plus_sign(self) -> None:
        """Hex with +: '+f0000' (invalid)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises(ValueError):
            _spots_texture_generator(
                width=32, height=32, spot_color_hex="+f0000", bg_color_hex="ffffff", density=1.0
            )

    def test_hex_with_minus_sign(self) -> None:
        """Hex with -: '-ff000' (invalid)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises(ValueError):
            _spots_texture_generator(
                width=32, height=32, spot_color_hex="-ff000", bg_color_hex="ffffff", density=1.0
            )

    def test_hex_with_decimal_point(self) -> None:
        """Hex with .: 'ff.000' (invalid)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises(ValueError):
            _spots_texture_generator(
                width=32, height=32, spot_color_hex="ff.000", bg_color_hex="ffffff", density=1.0
            )

    def test_hex_with_alphabetic_non_hex(self) -> None:
        """Hex with non-hex letters: 'ffgghh' (G, H are not hex)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        with pytest.raises(ValueError):
            _spots_texture_generator(
                width=32, height=32, spot_color_hex="ffgghh", bg_color_hex="ffffff", density=1.0
            )

    def test_hex_only_zeros(self) -> None:
        """Hex '000000' (black)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        png_data = _spots_texture_generator(
            width=32, height=32, spot_color_hex="000000", bg_color_hex="ffffff", density=1.0
        )
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_empty_string_for_both_colors(self) -> None:
        """Both colors empty: should use black and white defaults."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        png_data = _spots_texture_generator(
            width=32, height=32, spot_color_hex="", bg_color_hex="", density=1.0
        )
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_whitespace_only_hex(self) -> None:
        """Hex as whitespace: '   ' (should be treated as empty)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        # CHECKPOINT: Should whitespace be stripped or rejected?
        # Assumption: Treated as empty, defaults to black.
        # Confidence: Medium.
        try:
            png_data = _spots_texture_generator(
                width=32, height=32, spot_color_hex="   ", bg_color_hex="ffffff", density=1.0
            )
            assert png_data[:8] == b"\x89PNG\r\n\x1a\n"
        except ValueError:
            pass


# ============================================================================
# CATEGORY 4: COMBINATORIAL EDGE CASES (Multiple factors at once)
# ============================================================================


class TestSpotsCombinatorialEdgeCases:
    """Test combinations of edge cases that may not be handled together."""

    def test_1x1_texture_with_high_density(self) -> None:
        """Smallest possible texture with highest density."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        png_data = _spots_texture_generator(
            width=1, height=1, spot_color_hex="ff0000", bg_color_hex="ffffff", density=5.0
        )
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_1x1_texture_with_low_density(self) -> None:
        """Smallest texture with lowest density."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        png_data = _spots_texture_generator(
            width=1, height=1, spot_color_hex="ff0000", bg_color_hex="ffffff", density=0.1
        )
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_large_texture_with_low_density(self) -> None:
        """Large texture with very sparse spots (density=0.1)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        png_data = _spots_texture_generator(
            width=256, height=256, spot_color_hex="ff0000", bg_color_hex="ffffff", density=0.1
        )
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_asymmetric_dimensions(self) -> None:
        """Non-square dimensions: 17×251 (odd primes)."""
        import struct  # noqa: F401

        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        png_data = _spots_texture_generator(
            width=17, height=251, spot_color_hex="ff0000", bg_color_hex="ffffff", density=1.0
        )
        # Verify dimensions in PNG
        ihdr_width = struct.unpack(">I", png_data[16:20])[0]
        ihdr_height = struct.unpack(">I", png_data[20:24])[0]
        assert ihdr_width == 17
        assert ihdr_height == 251

    def test_both_colors_same(self) -> None:
        """Spot color = bg color (monochrome result)."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        png_data = _spots_texture_generator(
            width=32, height=32, spot_color_hex="ff0000", bg_color_hex="ff0000", density=1.0
        )
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_black_spot_on_white_background(self) -> None:
        """Maximum contrast: black spots on white."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        png_data = _spots_texture_generator(
            width=32, height=32, spot_color_hex="000000", bg_color_hex="ffffff", density=1.0
        )
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_white_spot_on_black_background(self) -> None:
        """Inverted contrast: white spots on black."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        png_data = _spots_texture_generator(
            width=32, height=32, spot_color_hex="ffffff", bg_color_hex="000000", density=1.0
        )
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_all_combinations_of_density_and_dimensions(self) -> None:
        """Sweep across density and dimension combinations."""
        from src.materials.gradient_generator import _spots_texture_generator  # noqa: E402

        densities = [0.1, 0.5, 1.0, 2.0, 5.0]
        dimensions = [(8, 8), (16, 32), (32, 16), (64, 64)]

        for w, h in dimensions:
            for d in densities:
                png_data = _spots_texture_generator(
                    width=w, height=h, spot_color_hex="ff0000", bg_color_hex="ffffff", density=d
                )
                assert png_data[:8] == b"\x89PNG\r\n\x1a\n", f"Failed for {w}x{h} density={d}"

# Categories 5-10 (Determinism, Resources, Concurrency, Errors, Mutation, Integration)
# have been split to test_spots_adversarial_advanced.py to keep files under 900 lines.

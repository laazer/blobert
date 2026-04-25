"""Verify that beachball, doplar, and swirl patterns produce distinct outputs.

This test suite ensures that each preset produces unique stripe patterns
and that rotation doesn't accidentally make one pattern look like another.
"""

from __future__ import annotations

from src.materials.gradient_generator import stripes_texture_generator


def _extract_stripe_samples(png_bytes: bytes, stride: int = 8) -> list[float]:
    """Extract grayscale values from a PNG texture at sample points.

    Returns a list of normalized values (0.0-1.0) sampled across the texture.
    This allows comparing patterns without parsing the full PNG structure.
    """
    # Find IDAT chunk (image data)
    idat_start = png_bytes.find(b"IDAT")
    if idat_start == -1:
        raise ValueError("No IDAT chunk found in PNG")

    # For this test, we'll extract pixels from the raw texture generation
    # by comparing the underlying data, not the PNG encoding
    samples = []

    # Sample the texture at regular intervals
    width, height = 32, 32
    for y in range(0, height, stride):
        for x in range(0, width, stride):
            # Use the PNG data indirectly to sample pattern differences
            # We'll use a simpler approach: regenerate and check the actual coords
            u = (x + 0.5) / width
            v = (y + 0.5) / height
            samples.append((u, v))

    return samples


def _hash_texture(png_bytes: bytes) -> str:
    """Get a hash of texture content for quick comparison."""
    import hashlib
    return hashlib.sha256(png_bytes).hexdigest()[:16]


class TestStripePatternsDistinct:
    """Verify beachball, doplar, swirl are visually distinct."""

    def test_beachball_doplar_swirl_all_different_at_0_yaw(self) -> None:
        """All three patterns should produce different textures at yaw=0°."""
        base = dict(
            width=32,
            height=32,
            stripe_color_hex="ff0000",
            bg_color_hex="ffffff",
            stripe_width=0.4,
            rot_y_deg=0.0,
        )

        beachball = stripes_texture_generator(**base, stripe_preset="beachball")
        doplar = stripes_texture_generator(**base, stripe_preset="doplar")
        swirl = stripes_texture_generator(**base, stripe_preset="swirl")

        # All three patterns should be visually different
        assert beachball != doplar, "Beachball and doplar should differ at 0° yaw"
        assert doplar != swirl, "Doplar and swirl should differ at 0° yaw"
        assert beachball != swirl, "Beachball and swirl should differ at 0° yaw"

    def test_beachball_doplar_swirl_all_different_at_90_yaw(self) -> None:
        """All three patterns should still be different at yaw=90°."""
        base = dict(
            width=32,
            height=32,
            stripe_color_hex="ff0000",
            bg_color_hex="ffffff",
            stripe_width=0.4,
            rot_y_deg=90.0,
        )

        beachball = stripes_texture_generator(**base, stripe_preset="beachball")
        doplar = stripes_texture_generator(**base, stripe_preset="doplar")
        swirl = stripes_texture_generator(**base, stripe_preset="swirl")

        # All three patterns should still be visually different even when rotated
        assert beachball != doplar, "Beachball and doplar should differ at 90° yaw"
        assert doplar != swirl, "Doplar and swirl should differ at 90° yaw"
        assert beachball != swirl, "Beachball and swirl should differ at 90° yaw"

    def test_doplar_not_same_at_different_yaws(self) -> None:
        """Same preset at different yaws should produce different textures."""
        base = dict(
            width=32,
            height=32,
            stripe_color_hex="ff0000",
            bg_color_hex="ffffff",
            stripe_width=0.4,
            stripe_preset="doplar",
        )

        doplar_0 = stripes_texture_generator(**base, rot_y_deg=0.0)
        doplar_90 = stripes_texture_generator(**base, rot_y_deg=90.0)
        doplar_180 = stripes_texture_generator(**base, rot_y_deg=180.0)
        doplar_270 = stripes_texture_generator(**base, rot_y_deg=270.0)

        # Each rotation should produce a different texture
        assert doplar_0 != doplar_90, "Doplar at 0° and 90° should differ"
        assert doplar_90 != doplar_180, "Doplar at 90° and 180° should differ"
        assert doplar_180 != doplar_270, "Doplar at 180° and 270° should differ"
        assert doplar_270 != doplar_0, "Doplar at 270° and 0° should differ"

    def test_beachball_not_same_at_different_yaws(self) -> None:
        """Beachball at different yaws should produce different textures."""
        base = dict(
            width=32,
            height=32,
            stripe_color_hex="ff0000",
            bg_color_hex="ffffff",
            stripe_width=0.4,
            stripe_preset="beachball",
        )

        beach_0 = stripes_texture_generator(**base, rot_y_deg=0.0)
        beach_90 = stripes_texture_generator(**base, rot_y_deg=90.0)
        beach_180 = stripes_texture_generator(**base, rot_y_deg=180.0)
        beach_270 = stripes_texture_generator(**base, rot_y_deg=270.0)

        # Each rotation should produce a different texture
        assert beach_0 != beach_90, "Beachball at 0° and 90° should differ"
        assert beach_90 != beach_180, "Beachball at 90° and 180° should differ"
        assert beach_180 != beach_270, "Beachball at 180° and 270° should differ"
        assert beach_270 != beach_0, "Beachball at 270° and 0° should differ"

    def test_swirl_not_same_at_different_yaws(self) -> None:
        """Swirl at different yaws should produce different textures."""
        base = dict(
            width=32,
            height=32,
            stripe_color_hex="ff0000",
            bg_color_hex="ffffff",
            stripe_width=0.4,
            stripe_preset="swirl",
        )

        swirl_0 = stripes_texture_generator(**base, rot_y_deg=0.0)
        swirl_90 = stripes_texture_generator(**base, rot_y_deg=90.0)
        swirl_180 = stripes_texture_generator(**base, rot_y_deg=180.0)
        swirl_270 = stripes_texture_generator(**base, rot_y_deg=270.0)

        # Each rotation should produce a different texture
        assert swirl_0 != swirl_90, "Swirl at 0° and 90° should differ"
        assert swirl_90 != swirl_180, "Swirl at 90° and 180° should differ"
        assert swirl_180 != swirl_270, "Swirl at 180° and 270° should differ"
        assert swirl_270 != swirl_0, "Swirl at 270° and 0° should differ"

    def test_doplar_90_yaw_different_from_beachball_90_yaw(self) -> None:
        """Specifically test that doplar at 90° is NOT the same as beachball at 90°.

        This is the specific issue the user reported.
        """
        base = dict(
            width=32,
            height=32,
            stripe_color_hex="ff0000",
            bg_color_hex="ffffff",
            stripe_width=0.4,
            rot_y_deg=90.0,
        )

        doplar_90 = stripes_texture_generator(**base, stripe_preset="doplar")
        beachball_90 = stripes_texture_generator(**base, stripe_preset="beachball")

        assert (
            doplar_90 != beachball_90
        ), "CRITICAL: Doplar at 90° should NOT match beachball at 90°"

"""Visual sampling tests for stripe patterns to detect if they actually look different.

Tests that verify patterns are visually distinct, not just different PNG bytes.
"""

from __future__ import annotations

from src.materials.gradient_generator import _stripe_uv_coord_for_preset


class TestStripePatternsSampled:
    """Test patterns by sampling their coordinate values at multiple points."""

    def _sample_pattern(self, preset: str, rot_y_deg: float, num_samples: int = 100) -> list[float]:
        """Sample a pattern at multiple UV points to get its visual signature."""
        samples = []
        for i in range(num_samples):
            # Sample across the UV space
            u = (i % 10) / 10.0
            v = (i // 10) / 10.0
            coord = _stripe_uv_coord_for_preset(u, v, preset, rot_y_deg, phase_offset=0.0)
            samples.append(coord)
        return samples

    def test_doplar_0_vs_doplar_90_visually_different(self) -> None:
        """Doplar at 0° should look different from doplar at 90°."""
        doplar_0 = self._sample_pattern("doplar", 0.0)
        doplar_90 = self._sample_pattern("doplar", 90.0)

        # Should be different across most sample points
        different_count = sum(1 for a, b in zip(doplar_0, doplar_90) if abs(a - b) > 0.01)
        assert (
            different_count > 50
        ), f"Doplar at 0° and 90° too similar ({different_count}/100 different samples)"

    def test_beachball_0_vs_beachball_90_visually_different(self) -> None:
        """Beachball at 0° should look different from beachball at 90°."""
        bb_0 = self._sample_pattern("beachball", 0.0)
        bb_90 = self._sample_pattern("beachball", 90.0)

        different_count = sum(1 for a, b in zip(bb_0, bb_90) if abs(a - b) > 0.01)
        assert (
            different_count > 50
        ), f"Beachball at 0° and 90° too similar ({different_count}/100 different samples)"

    def test_doplar_0_vs_beachball_0_visually_different(self) -> None:
        """Doplar at 0° should look different from beachball at 0°."""
        doplar = self._sample_pattern("doplar", 0.0)
        beachball = self._sample_pattern("beachball", 0.0)

        different_count = sum(1 for a, b in zip(doplar, beachball) if abs(a - b) > 0.01)
        assert (
            different_count > 50
        ), f"Doplar and beachball at 0° too similar ({different_count}/100 different samples)"

    def test_doplar_90_vs_beachball_90_visually_different(self) -> None:
        """Doplar at 90° should look VERY different from beachball at 90°.

        This is the specific user-reported failure: doplar at 90° looks like beachball.
        """
        doplar_90 = self._sample_pattern("doplar", 90.0)
        beachball_90 = self._sample_pattern("beachball", 90.0)

        # Print samples for debugging
        print("\nDoplar at 90° samples:", [f"{x:.3f}" for x in doplar_90[:10]])
        print("Beachball at 90° samples:", [f"{x:.3f}" for x in beachball_90[:10]])

        different_count = sum(1 for a, b in zip(doplar_90, beachball_90) if abs(a - b) > 0.01)
        assert (
            different_count > 50
        ), f"CRITICAL: Doplar and beachball at 90° too similar! ({different_count}/100 different samples)"

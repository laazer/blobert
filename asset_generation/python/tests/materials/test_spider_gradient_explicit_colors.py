"""Spider GLB export with explicit gradient colors (not mocked bpy).

Tests whether gradients render with explicit colors when applied to a real spider.
Skipped when ``blender`` is not on PATH and ``BLOBERT_BLENDER_BIN`` is unset.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from .gradient_glb_utils import (
    first_image_png_from_glb,
    parse_glb,
    png_histogram,
)

PYTHON_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = PYTHON_ROOT / "tests" / "fixtures" / "blender_spider_gradient_explicit_colors.py"


def _find_blender() -> str | None:
    return os.environ.get("BLOBERT_BLENDER_BIN") or shutil.which("blender")


@pytest.mark.skipif(_find_blender() is None, reason="Blender not installed (PATH or BLOBERT_BLENDER_BIN)")
def test_spider_gradient_with_explicit_red_blue_colors() -> None:
    """Generate spider with explicit red→blue gradient and verify PNG is not solid black.

    Regression test: if gradient colors are being lost or set to black, this will catch it.
    The spider is generated with feat_body_texture_grad_color_a="ff0000" and
    feat_body_texture_grad_color_b="0000ff" (red→blue horizontal).
    """
    blender = _find_blender()
    assert blender is not None

    with tempfile.TemporaryDirectory() as tmp:
        out_glb = Path(tmp) / "spider_grad_explicit.glb"
        env = os.environ.copy()
        _pp = [str(PYTHON_ROOT)]
        if env.get("PYTHONPATH"):
            _pp.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = os.pathsep.join(_pp)
        r = subprocess.run(
            [blender, "-b", "--python", str(FIXTURE), "--", str(out_glb)],
            cwd=str(PYTHON_ROOT),
            capture_output=True,
            text=True,
            timeout=180,
            env=env,
            check=False,
        )
        assert r.returncode == 0, f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
        assert out_glb.is_file(), r.stdout
        glb = out_glb.read_bytes()
        glb_json, bin_data = parse_glb(glb)

        # Verify GLB has a baseColorTexture
        mats = glb_json.get("materials")
        assert isinstance(mats, list) and len(mats) > 0, "no materials in GLB"
        m0 = mats[0]
        assert isinstance(m0, dict)
        pbr = m0.get("pbrMetallicRoughness")
        assert isinstance(pbr, dict)
        bct = pbr.get("baseColorTexture")
        assert isinstance(bct, dict), "expected baked baseColorTexture in exported GLB"

        # Extract and analyze PNG
        png_bytes = first_image_png_from_glb(glb_json, bin_data)
        max_r, max_g, max_b = png_histogram(png_bytes)

        # For red→blue gradient, we expect:
        # - High red values (gradient starts at ff0000)
        # - High blue values (gradient ends at 0000ff)
        # - Low green values (red and blue have no green)
        # If gradient is black, all channels would be near 0
        assert max_r > 200, f"expected high red channel for red→blue gradient, got max_r={max_r}"
        assert max_b > 200, f"expected high blue channel for red→blue gradient, got max_b={max_b}"
        assert max_g < 100, f"expected low green channel for red→blue gradient, got max_g={max_g}"

"""Optional Blender subprocess: real GLB export for gradient materials (not mocked bpy).

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
FIXTURE = PYTHON_ROOT / "tests" / "fixtures" / "blender_gradient_glb_smoke.py"


def _find_blender() -> str | None:
    return os.environ.get("BLOBERT_BLENDER_BIN") or shutil.which("blender")


def _png_max_rgb_channel(png_bytes: bytes) -> int:
    """Return max RGB value (any channel) — wrapper for compatibility."""
    max_r, max_g, max_b = png_histogram(png_bytes)
    return max(max_r, max_g, max_b)


def _first_image_png_from_glb(glb_json: dict[str, object], bin_data: bytes) -> bytes:
    """Wrapper for compatibility — delegates to shared utility."""
    return first_image_png_from_glb(glb_json, bin_data)


@pytest.mark.skipif(_find_blender() is None, reason="Blender not installed (PATH or BLOBERT_BLENDER_BIN)")
def test_blender_exports_gradient_glb_with_non_black_base_color_texture() -> None:
    blender = _find_blender()
    assert blender is not None

    with tempfile.TemporaryDirectory() as tmp:
        out_glb = Path(tmp) / "grad_smoke.glb"
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
        mats = glb_json.get("materials")
        assert isinstance(mats, list) and len(mats) > 0
        m0 = mats[0]
        assert isinstance(m0, dict)
        pbr = m0.get("pbrMetallicRoughness")
        assert isinstance(pbr, dict)
        bct = pbr.get("baseColorTexture")
        assert isinstance(bct, dict), "expected baked baseColorTexture in exported GLB"
        png_bytes = _first_image_png_from_glb(glb_json, bin_data)
        mx = _png_max_rgb_channel(png_bytes)
        assert mx > 8, "gradient PNG must not be flat black (regression guard)"

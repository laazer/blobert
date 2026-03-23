"""
Blender-invocation integration tests for build_parts_library.py.

All tests in this file are marked @pytest.mark.integration.
Run with:
    python -m pytest asset_generation/python/tests/enemies/test_parts_library_integration.py -v -m integration

Skip in pure-Python CI with:
    python -m pytest ... -m "not integration"

Spec traceability:
  BPL-INT-1  → TestBlendFileExists::*
  BPL-INT-2  → TestBlenderInvocationSucceeds::*
  BPL-INT-3  → TestPartSummaryLinesInOutput::*
  BPL-INT-4  → TestPartsCollectionVerification::*
"""

import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[5]
_PYTHON_ROOT = _REPO_ROOT / "asset_generation" / "python"
_SCRIPT_PATH = _PYTHON_ROOT / "src" / "enemies" / "build_parts_library.py"
_BLEND_PATH = _REPO_ROOT / "assets" / "enemies" / "parts" / "enemy_parts.blend"
_FIND_BLENDER_PATH = _PYTHON_ROOT / "bin" / "find_blender.py"

_EXPECTED_PART_NAMES = [
    "BaseBlob",
    "BaseSphere",
    "BaseCapsule",
    "EyeNode",
    "Spike",
    "Claw",
    "Shell",
    "Tentacle",
    "Wing",
    "OrbCore",
    "Blade",
]

_MAX_TRIANGLES = 100
_SUBPROCESS_TIMEOUT = 120  # seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_blender_executable() -> str:
    """Return path to Blender executable via find_blender.py helper."""
    result = subprocess.run(
        [sys.executable, str(_FIND_BLENDER_PATH)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        pytest.skip(f"Blender not found: {result.stderr.strip()}")
    return result.stdout.strip()


def _run_blender_script(blender: str, script_path: Path, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run a Blender Python script headlessly and return the CompletedProcess."""
    cmd = [blender, "--background", "--python", str(script_path)]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
        cwd=str(_REPO_ROOT),
    )


# ---------------------------------------------------------------------------
# BPL-INT-1: Blend file exists and is non-zero size
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestBlendFileExists:
    """BPL-INT-1: the generated .blend file is present on disk and non-empty."""

    def test_blend_file_exists(self):
        """BPL-INT-1.1: assets/enemies/parts/enemy_parts.blend must exist."""
        assert _BLEND_PATH.is_file(), (
            f"Blend file not found at: {_BLEND_PATH}\n"
            "Run build_parts_library.py via Blender to generate it."
        )

    def test_blend_file_is_non_zero_size(self):
        """BPL-INT-1.2: the .blend file must not be empty (zero bytes)."""
        assert _BLEND_PATH.is_file(), (
            f"Blend file not found at: {_BLEND_PATH}"
        )
        size = _BLEND_PATH.stat().st_size
        assert size > 0, (
            f"Blend file at {_BLEND_PATH} has zero bytes; it may be corrupt or incomplete."
        )

    def test_blend_file_has_blend_magic_bytes(self):
        """BPL-INT-1.3: file starts with Blender's 'BLENDER' magic header."""
        assert _BLEND_PATH.is_file(), (
            f"Blend file not found at: {_BLEND_PATH}"
        )
        with open(_BLEND_PATH, "rb") as f:
            magic = f.read(7)
        assert magic == b"BLENDER", (
            f"File at {_BLEND_PATH} does not start with Blender magic bytes 'BLENDER'. "
            f"Got: {magic!r}"
        )


# ---------------------------------------------------------------------------
# BPL-INT-2: Blender invocation exits with returncode 0
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestBlenderInvocationSucceeds:
    """BPL-INT-2: blender --background --python build_parts_library.py exits 0."""

    def test_blender_invocation_exits_zero(self):
        """BPL-INT-2.1: script must complete without error (returncode == 0)."""
        blender = _resolve_blender_executable()
        result = _run_blender_script(blender, _SCRIPT_PATH)
        combined = result.stdout + "\n" + result.stderr
        assert result.returncode == 0, (
            f"Blender exited with returncode {result.returncode}.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    def test_blender_invocation_no_python_traceback(self):
        """BPL-INT-2.2: no Python Traceback in stdout or stderr."""
        blender = _resolve_blender_executable()
        result = _run_blender_script(blender, _SCRIPT_PATH)
        combined = result.stdout + "\n" + result.stderr
        assert "Traceback (most recent call last)" not in combined, (
            f"Python traceback detected in Blender output:\n{combined}"
        )

    def test_blender_invocation_no_error_keyword(self):
        """BPL-INT-2.3: no bare 'Error:' line (Blender's own error prefix) in output."""
        blender = _resolve_blender_executable()
        result = _run_blender_script(blender, _SCRIPT_PATH)
        combined_lines = (result.stdout + "\n" + result.stderr).splitlines()
        error_lines = [ln for ln in combined_lines if re.match(r"^\s*Error:", ln)]
        assert not error_lines, (
            f"Blender reported errors:\n" + "\n".join(error_lines)
        )

    def test_blend_file_created_after_invocation(self):
        """BPL-INT-2.4: .blend file exists after successful invocation."""
        blender = _resolve_blender_executable()
        _run_blender_script(blender, _SCRIPT_PATH)
        assert _BLEND_PATH.is_file(), (
            f"Blend file not created at {_BLEND_PATH} after successful Blender run."
        )

    def test_final_done_line_in_output(self):
        """BPL-INT-2.5: stdout contains '[BPL] Done: enemy_parts.blend'."""
        blender = _resolve_blender_executable()
        result = _run_blender_script(blender, _SCRIPT_PATH)
        assert "[BPL] Done: enemy_parts.blend" in result.stdout, (
            f"Expected '[BPL] Done: enemy_parts.blend' in stdout.\nstdout:\n{result.stdout}"
        )


# ---------------------------------------------------------------------------
# BPL-INT-3: stdout contains all 11 [BPL] summary lines with count < 100
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestPartSummaryLinesInOutput:
    """BPL-INT-3: stdout has one '[BPL] <name>: <N> triangles' line per part, N < 100."""

    # Regex matching a BPL summary line: [BPL] <name>: <N> triangles
    _BPL_LINE_RE = re.compile(r"\[BPL\]\s+(\w+):\s+(\d+)\s+triangles")

    @pytest.fixture(scope="class")
    def blender_output(self):
        """Run the script once for the whole class; cache stdout."""
        blender = _resolve_blender_executable()
        result = _run_blender_script(blender, _SCRIPT_PATH)
        return result.stdout

    def _parse_bpl_lines(self, stdout: str) -> dict[str, int]:
        """Return {part_name: triangle_count} for every [BPL] summary line found."""
        parsed: dict[str, int] = {}
        for match in self._BPL_LINE_RE.finditer(stdout):
            name, count = match.group(1), int(match.group(2))
            parsed[name] = count
        return parsed

    def test_all_11_summary_lines_present(self, blender_output):
        """BPL-INT-3.1: one summary line per expected part name."""
        parsed = self._parse_bpl_lines(blender_output)
        missing = [name for name in _EXPECTED_PART_NAMES if name not in parsed]
        assert not missing, (
            f"Missing [BPL] summary lines for: {missing}.\nstdout:\n{blender_output}"
        )

    def test_no_unexpected_summary_lines(self, blender_output):
        """BPL-INT-3.2: no extra part names appear in summary lines."""
        parsed = self._parse_bpl_lines(blender_output)
        extra = [name for name in parsed if name not in _EXPECTED_PART_NAMES]
        assert not extra, (
            f"Unexpected [BPL] summary lines for: {extra}.\nstdout:\n{blender_output}"
        )

    def test_exactly_11_summary_lines(self, blender_output):
        """BPL-INT-3.3: exactly 11 summary lines, no duplicates."""
        parsed = self._parse_bpl_lines(blender_output)
        assert len(parsed) == 11, (
            f"Expected 11 [BPL] summary lines, found {len(parsed)}: {list(parsed)}.\nstdout:\n{blender_output}"
        )

    @pytest.mark.parametrize("part_name", _EXPECTED_PART_NAMES)
    def test_each_part_triangle_count_under_100(self, blender_output, part_name):
        """BPL-INT-3.4: each part's triangle count is strictly less than 100."""
        parsed = self._parse_bpl_lines(blender_output)
        assert part_name in parsed, (
            f"No summary line found for '{part_name}'.\nstdout:\n{blender_output}"
        )
        count = parsed[part_name]
        assert count < _MAX_TRIANGLES, (
            f"'{part_name}' has {count} triangles, which is not < {_MAX_TRIANGLES}."
        )

    @pytest.mark.parametrize("part_name", _EXPECTED_PART_NAMES)
    def test_each_part_triangle_count_is_positive(self, blender_output, part_name):
        """BPL-INT-3.5: each reported triangle count must be > 0."""
        parsed = self._parse_bpl_lines(blender_output)
        if part_name not in parsed:
            pytest.skip(f"No summary line for '{part_name}'; covered by test_all_11_summary_lines_present.")
        count = parsed[part_name]
        assert count > 0, (
            f"'{part_name}' reported {count} triangles; expected > 0."
        )


# ---------------------------------------------------------------------------
# BPL-INT-4: Blender collection verification (11 objects in "Parts" collection)
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestPartsCollectionVerification:
    """
    BPL-INT-4: open enemy_parts.blend in Blender and verify the 'Parts' collection
    contains exactly 11 mesh objects with the correct names and triangle counts < 100.
    """

    _VERIFICATION_SCRIPT = textwrap.dedent("""\
        import sys
        import bpy

        EXPECTED_NAMES = {expected_names}
        MAX_TRIANGLES = {max_triangles}
        BLEND_PATH = r\"{blend_path}\"

        bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)

        # --- Check 'Parts' collection exists ---
        if "Parts" not in bpy.data.collections:
            print("[VERIFY-FAIL] 'Parts' collection not found in blend file.")
            sys.exit(1)

        parts_col = bpy.data.collections["Parts"]
        objects = list(parts_col.objects)

        # --- Check object count ---
        if len(objects) != 11:
            print(f"[VERIFY-FAIL] Expected 11 objects in 'Parts', found {{len(objects)}}: {{[o.name for o in objects]}}")
            sys.exit(1)

        # --- Check all expected names present ---
        actual_names = {{o.name for o in objects}}
        missing = EXPECTED_NAMES - actual_names
        if missing:
            print(f"[VERIFY-FAIL] Missing objects in 'Parts': {{missing}}")
            sys.exit(1)

        extra = actual_names - EXPECTED_NAMES
        if extra:
            print(f"[VERIFY-FAIL] Unexpected objects in 'Parts': {{extra}}")
            sys.exit(1)

        # --- Check all are MESH type with triangle count < 100 ---
        import bmesh
        errors = []
        for obj in objects:
            if obj.type != "MESH":
                errors.append(f"{{obj.name}} is type {{obj.type!r}}, expected MESH")
                continue
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bmesh.ops.triangulate(bm, faces=bm.faces[:])
            tri_count = len(bm.faces)
            bm.free()
            if tri_count >= MAX_TRIANGLES:
                errors.append(f"{{obj.name}} has {{tri_count}} triangles (>= {{MAX_TRIANGLES}})")
            elif tri_count <= 0:
                errors.append(f"{{obj.name}} has {{tri_count}} triangles (<= 0)")
            else:
                print(f"[VERIFY-OK] {{obj.name}}: {{tri_count}} triangles")

        if errors:
            for e in errors:
                print(f"[VERIFY-FAIL] {{e}}")
            sys.exit(1)

        print("[VERIFY-PASS] All 11 parts verified successfully.")
        sys.exit(0)
    """)

    def _write_verification_script(self, tmp: tempfile.NamedTemporaryFile) -> None:
        """Write the verification script, substituting runtime constants."""
        script_content = self._VERIFICATION_SCRIPT.format(
            expected_names=repr(set(_EXPECTED_PART_NAMES)),
            max_triangles=_MAX_TRIANGLES,
            blend_path=str(_BLEND_PATH).replace("\\", "/"),
        )
        tmp.write(script_content.encode("utf-8"))
        tmp.flush()

    def test_parts_collection_exists(self):
        """BPL-INT-4.1: 'Parts' collection exists in enemy_parts.blend."""
        blender = _resolve_blender_executable()
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            self._write_verification_script(tmp)
            tmp_path = tmp.name

        result = subprocess.run(
            [blender, "--background", "--python", tmp_path],
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT,
            cwd=str(_REPO_ROOT),
        )
        combined = result.stdout + "\n" + result.stderr
        assert "[VERIFY-FAIL] 'Parts' collection not found" not in combined, (
            f"'Parts' collection missing in blend file.\nOutput:\n{combined}"
        )

    def test_parts_collection_has_11_objects(self):
        """BPL-INT-4.2: 'Parts' collection contains exactly 11 objects."""
        blender = _resolve_blender_executable()
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            self._write_verification_script(tmp)
            tmp_path = tmp.name

        result = subprocess.run(
            [blender, "--background", "--python", tmp_path],
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT,
            cwd=str(_REPO_ROOT),
        )
        combined = result.stdout + "\n" + result.stderr
        assert "Expected 11 objects" not in combined, (
            f"Object count mismatch in 'Parts' collection.\nOutput:\n{combined}"
        )

    def test_all_expected_part_names_in_collection(self):
        """BPL-INT-4.3: all 11 canonical part names are present in 'Parts'."""
        blender = _resolve_blender_executable()
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            self._write_verification_script(tmp)
            tmp_path = tmp.name

        result = subprocess.run(
            [blender, "--background", "--python", tmp_path],
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT,
            cwd=str(_REPO_ROOT),
        )
        combined = result.stdout + "\n" + result.stderr
        assert "Missing objects" not in combined, (
            f"Missing part names in 'Parts' collection.\nOutput:\n{combined}"
        )
        assert "Unexpected objects" not in combined, (
            f"Unexpected part names in 'Parts' collection.\nOutput:\n{combined}"
        )

    def test_all_parts_are_mesh_objects(self):
        """BPL-INT-4.4: every object in 'Parts' is type MESH."""
        blender = _resolve_blender_executable()
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            self._write_verification_script(tmp)
            tmp_path = tmp.name

        result = subprocess.run(
            [blender, "--background", "--python", tmp_path],
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT,
            cwd=str(_REPO_ROOT),
        )
        combined = result.stdout + "\n" + result.stderr
        assert "expected MESH" not in combined, (
            f"Non-MESH object found in 'Parts' collection.\nOutput:\n{combined}"
        )

    def test_all_parts_triangle_count_under_100_via_blender(self):
        """BPL-INT-4.5: every mesh in 'Parts' has < 100 triangles when verified by Blender."""
        blender = _resolve_blender_executable()
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            self._write_verification_script(tmp)
            tmp_path = tmp.name

        result = subprocess.run(
            [blender, "--background", "--python", tmp_path],
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT,
            cwd=str(_REPO_ROOT),
        )
        combined = result.stdout + "\n" + result.stderr
        assert "triangles (>=" not in combined, (
            f"One or more parts exceed the 100-triangle budget.\nOutput:\n{combined}"
        )

    def test_full_verification_passes(self):
        """BPL-INT-4.6: the complete verification script exits 0 with [VERIFY-PASS]."""
        blender = _resolve_blender_executable()
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            self._write_verification_script(tmp)
            tmp_path = tmp.name

        result = subprocess.run(
            [blender, "--background", "--python", tmp_path],
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT,
            cwd=str(_REPO_ROOT),
        )
        combined = result.stdout + "\n" + result.stderr
        assert result.returncode == 0, (
            f"Blender verification script exited {result.returncode}.\nOutput:\n{combined}"
        )
        assert "[VERIFY-PASS]" in combined, (
            f"Expected '[VERIFY-PASS]' in output.\nOutput:\n{combined}"
        )

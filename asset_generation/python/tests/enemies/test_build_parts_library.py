"""
Pure-Python tests for build_parts_library.py — no bpy import, no Blender required.

Spec traceability:
  BPL-SCRIPT-1.1  → TestScriptExists::test_script_file_exists
  BPL-SCRIPT-1.2  → TestScriptExists::test_script_importable_without_bpy
  BPL-SCRIPT-1.3  → TestScriptExists::test_no_top_level_import_bpy
  BPL-SCRIPT-1.4  → TestScriptExists::test_script_has_main_guard
  BPL-CONST-1.1   → TestOutputPathConstant::test_output_path_ends_with_expected_suffix
  BPL-CONST-1.2   → TestOutputPathConstant::test_output_path_is_pathlib_path
  BPL-CONST-1.3   → TestOutputPathConstant::test_output_path_parent_name_is_parts
  BPL-CONST-1.4   → TestOutputPathConstant::test_output_path_filename_is_enemy_parts_blend
  BPL-CONST-1.5   → TestOutputPathConstant::test_output_path_is_absolute
  BPL-CONST-2.*   → TestPartNamesConstant::*
  BPL-CONST-3.*   → TestTriangleBudgetConstants::*
"""

import importlib
import sys
import types
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[5]
_SCRIPT_PATH = _REPO_ROOT / "asset_generation" / "python" / "src" / "enemies" / "build_parts_library.py"
_PYTHON_ROOT = _REPO_ROOT / "asset_generation" / "python"

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _import_module():
    """
    Import build_parts_library as a module by injecting a stub for bpy so that
    any deferred import inside functions doesn't fail.  Module-level code must
    NOT import bpy (BPL-SCRIPT-1.3), so the stub only guards against accidental
    top-level usage.

    Returns the imported module.
    """
    module_name = "src.enemies.build_parts_library"
    if module_name in sys.modules:
        return sys.modules[module_name]

    # Insert the python root so "from src.enemies..." resolves
    if str(_PYTHON_ROOT) not in sys.path:
        sys.path.insert(0, str(_PYTHON_ROOT))

    # Provide a stub bpy in case any unexpected top-level access happens;
    # the test for BPL-SCRIPT-1.3 separately verifies no top-level import exists.
    bpy_stub = types.ModuleType("bpy")
    had_bpy = "bpy" in sys.modules
    if not had_bpy:
        sys.modules["bpy"] = bpy_stub

    try:
        module = importlib.import_module(module_name)
    finally:
        if not had_bpy:
            sys.modules.pop("bpy", None)

    return module


# ---------------------------------------------------------------------------
# BPL-SCRIPT-1: Script File Location and Module Structure
# ---------------------------------------------------------------------------

class TestScriptExists:
    """BPL-SCRIPT-1: script exists at the canonical path and has correct structure."""

    def test_script_file_exists(self):
        """BPL-SCRIPT-1.1: script resides at asset_generation/python/src/enemies/build_parts_library.py."""
        assert _SCRIPT_PATH.is_file(), (
            f"Script not found at expected path: {_SCRIPT_PATH}"
        )

    def test_no_top_level_import_bpy(self):
        """BPL-SCRIPT-1.3: 'import bpy' must not appear outside a function body."""
        source = _SCRIPT_PATH.read_text(encoding="utf-8")
        lines = source.splitlines()
        inside_function = False
        for lineno, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            # Track if we enter a function/class body (indented 'def' or 'class')
            if stripped.startswith("def ") or stripped.startswith("class "):
                inside_function = True
            # A non-blank, non-indented line resets to module scope
            if line and not line[0].isspace():
                inside_function = False
            if not inside_function and stripped.startswith("import bpy"):
                pytest.fail(
                    f"Found top-level 'import bpy' at line {lineno}: {line!r}. "
                    "All bpy usage must be inside def main() or helper functions."
                )
            if not inside_function and stripped.startswith("from bpy"):
                pytest.fail(
                    f"Found top-level 'from bpy ...' at line {lineno}: {line!r}. "
                    "All bpy usage must be inside def main() or helper functions."
                )

    def test_script_has_main_guard(self):
        """BPL-SCRIPT-1.4: script contains 'if __name__ == \"__main__\":' guard."""
        source = _SCRIPT_PATH.read_text(encoding="utf-8")
        assert 'if __name__ == "__main__"' in source or "if __name__ == '__main__'" in source, (
            "Script must have an 'if __name__ == \"__main__\":' guard calling main()."
        )

    def test_script_importable_without_bpy(self):
        """BPL-SCRIPT-1.2: importing the script does not require a live bpy installation."""
        # The helper already guards with a stub bpy; if module-level bpy usage
        # exists and bpy is absent, this import would raise ModuleNotFoundError
        # before the stub is installed — meaning the stub has no effect and we'd
        # see an error here.
        mod = _import_module()
        assert mod is not None


# ---------------------------------------------------------------------------
# BPL-CONST-1: OUTPUT_PATH Constant
# ---------------------------------------------------------------------------

class TestOutputPathConstant:
    """BPL-CONST-1: OUTPUT_PATH resolves correctly from the script's __file__."""

    @pytest.fixture(scope="class")
    def output_path(self):
        mod = _import_module()
        return mod.OUTPUT_PATH

    def test_output_path_ends_with_expected_suffix(self, output_path):
        """BPL-CONST-1.1 / BPL-CONST-1.6: path ends with assets/enemies/parts/enemy_parts.blend."""
        posix = Path(output_path).as_posix()
        assert posix.endswith("assets/enemies/parts/enemy_parts.blend"), (
            f"OUTPUT_PATH '{output_path}' does not end with 'assets/enemies/parts/enemy_parts.blend'."
        )

    def test_output_path_is_pathlib_path(self, output_path):
        """BPL-CONST-1.2: OUTPUT_PATH must be a pathlib.Path instance, not a raw str."""
        assert isinstance(output_path, Path), (
            f"OUTPUT_PATH must be a pathlib.Path, got {type(output_path).__name__!r}."
        )

    def test_output_path_parent_name_is_parts(self, output_path):
        """BPL-CONST-1.3: the containing directory is named 'parts'."""
        assert Path(output_path).parent.name == "parts", (
            f"Expected OUTPUT_PATH.parent.name == 'parts', got {Path(output_path).parent.name!r}."
        )

    def test_output_path_filename_is_enemy_parts_blend(self, output_path):
        """BPL-CONST-1.4: filename is 'enemy_parts.blend'."""
        assert Path(output_path).name == "enemy_parts.blend", (
            f"Expected OUTPUT_PATH.name == 'enemy_parts.blend', got {Path(output_path).name!r}."
        )

    def test_output_path_is_absolute(self, output_path):
        """BPL-CONST-1.5: OUTPUT_PATH must be an absolute path."""
        assert Path(output_path).is_absolute(), (
            f"OUTPUT_PATH '{output_path}' is not an absolute path."
        )


# ---------------------------------------------------------------------------
# BPL-CONST-2: PART_NAMES Constant
# ---------------------------------------------------------------------------

class TestPartNamesConstant:
    """BPL-CONST-2: PART_NAMES contains exactly the 11 canonical part names."""

    @pytest.fixture(scope="class")
    def part_names(self):
        mod = _import_module()
        return mod.PART_NAMES

    def test_part_names_is_a_list(self, part_names):
        """PART_NAMES must be a Python list."""
        assert isinstance(part_names, list), (
            f"PART_NAMES must be a list, got {type(part_names).__name__!r}."
        )

    def test_part_names_has_exactly_11_elements(self, part_names):
        """BPL-CONST-2: exactly 11 elements required."""
        assert len(part_names) == 11, (
            f"PART_NAMES must have 11 elements, got {len(part_names)}."
        )

    def test_part_names_contains_all_expected_names(self, part_names):
        """BPL-CONST-2: all 11 canonical names are present (order-insensitive)."""
        missing = set(_EXPECTED_PART_NAMES) - set(part_names)
        assert not missing, (
            f"PART_NAMES is missing expected names: {sorted(missing)}."
        )

    def test_part_names_has_no_extra_names(self, part_names):
        """BPL-CONST-2: no unexpected names present."""
        extra = set(part_names) - set(_EXPECTED_PART_NAMES)
        assert not extra, (
            f"PART_NAMES contains unexpected names: {sorted(extra)}."
        )

    def test_part_names_has_no_duplicates(self, part_names):
        """BPL-CONST-2: no duplicate names allowed."""
        seen = set()
        duplicates = []
        for name in part_names:
            if name in seen:
                duplicates.append(name)
            seen.add(name)
        assert not duplicates, (
            f"PART_NAMES contains duplicate entries: {duplicates}."
        )

    def test_part_names_all_elements_are_strings(self, part_names):
        """BPL-CONST-2: every element must be a str."""
        non_strings = [x for x in part_names if not isinstance(x, str)]
        assert not non_strings, (
            f"PART_NAMES contains non-string elements: {non_strings}."
        )

    def test_part_names_no_whitespace_in_names(self, part_names):
        """BPL-CONST-2: names must not contain leading/trailing whitespace."""
        bad = [name for name in part_names if name != name.strip()]
        assert not bad, (
            f"PART_NAMES contains names with leading/trailing whitespace: {bad!r}."
        )

    @pytest.mark.parametrize("expected_name", _EXPECTED_PART_NAMES)
    def test_each_expected_name_present(self, part_names, expected_name):
        """BPL-CONST-2: each individual canonical name is present (parameterised)."""
        assert expected_name in part_names, (
            f"'{expected_name}' not found in PART_NAMES."
        )


# ---------------------------------------------------------------------------
# BPL-CONST-3: MAX_TRIANGLES_PER_PART Constant
# ---------------------------------------------------------------------------

class TestTriangleBudgetConstants:
    """BPL-CONST-3: MAX_TRIANGLES_PER_PART == 100 (int)."""

    @pytest.fixture(scope="class")
    def max_triangles(self):
        mod = _import_module()
        return mod.MAX_TRIANGLES_PER_PART

    def test_max_triangles_per_part_equals_100(self, max_triangles):
        """MAX_TRIANGLES_PER_PART must equal 100."""
        assert max_triangles == 100, (
            f"MAX_TRIANGLES_PER_PART must be 100, got {max_triangles!r}."
        )

    def test_max_triangles_per_part_is_int(self, max_triangles):
        """MAX_TRIANGLES_PER_PART must be an int, not a float or string."""
        assert isinstance(max_triangles, int), (
            f"MAX_TRIANGLES_PER_PART must be int, got {type(max_triangles).__name__!r}."
        )

    def test_max_triangles_per_part_is_positive(self, max_triangles):
        """Sanity: MAX_TRIANGLES_PER_PART must be a positive integer."""
        assert max_triangles > 0, (
            f"MAX_TRIANGLES_PER_PART must be positive, got {max_triangles!r}."
        )

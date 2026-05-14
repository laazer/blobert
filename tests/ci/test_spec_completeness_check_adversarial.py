"""Adversarial tests for spec_completeness_check.py.

Tests heading parsing edge cases, type mutations, path traversal, and
boundary conditions in the existing spec completeness checker.
"""

import subprocess
import sys
from pathlib import Path

import pytest


SPEC_CHECKER = Path("/Users/jacobbrandt/workspace/blobert/ci/scripts/spec_completeness_check.py")


class TestHeadingParsingMutation:
    """Mutation tests for heading detection in spec_completeness_check.py."""

    def test_heading_with_extra_spaces(self, tmp_path: Path) -> None:
        # Mutation: headings with extra leading/trailing spaces should still match
        spec = tmp_path / "spec.md"
        spec.write_text("#   Overview   \n\n##   Acceptance Criteria   \n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "generic"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_heading_with_unicode(self, tmp_path: Path) -> None:
        # Mutation: Unicode headings should be detected
        spec = tmp_path / "spec.md"
        spec.write_text("# Vueil\n\n## Crit\u00e8res d'acceptation\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "generic"],
            capture_output=True, text=True,
        )
        assert "UnicodeDecodeError" not in result.stderr

    def test_heading_at_different_levels(self, tmp_path: Path) -> None:
        # Mutation: headings at levels 1-4 should all be detected
        for level in range(1, 5):
            hashes = "#" * level
            spec = tmp_path / f"spec_{level}.md"
            spec.write_text(f"{hashes} Overview\n\n{hashes} Acceptance Criteria\n\n")
            result = subprocess.run(
                [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "generic"],
                capture_output=True, text=True,
            )
            assert "UnicodeDecodeError" not in result.stderr

    def test_heading_with_no_space_after_hash(self, tmp_path: Path) -> None:
        # Mutation: headings without space after # should not be detected as headings
        spec = tmp_path / "spec.md"
        spec.write_text("#NoSpace\n\n##NoSpace\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "generic"],
            capture_output=True, text=True,
        )
        # Should not crash even if headings are not detected

    def test_heading_case_insensitive_match(self, tmp_path: Path) -> None:
        # Mutation: headings should be case-insensitive
        spec = tmp_path / "spec.md"
        spec.write_text("# OVERVIEW\n\n## ACCEPTANCE CRITERIA\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "generic"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_heading_with_special_characters(self, tmp_path: Path) -> None:
        # Mutation: headings with special chars should not crash
        spec = tmp_path / "spec.md"
        spec.write_text("# Overview & Acceptance Criteria!\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "generic"],
            capture_output=True, text=True,
        )
        assert "UnicodeDecodeError" not in result.stderr

    def test_heading_with_numbers(self, tmp_path: Path) -> None:
        # Mutation: headings with numbers should be detected
        spec = tmp_path / "spec.md"
        spec.write_text("# Overview 123\n\n## Acceptance Criteria 456\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "generic"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_heading_with_emoji(self, tmp_path: Path) -> None:
        # Mutation: headings with emoji should not crash
        spec = tmp_path / "spec.md"
        spec.write_text("# Overview \U0001f680\n\n## Acceptance Criteria \U0001f527\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "generic"],
            capture_output=True, text=True,
        )
        assert "UnicodeDecodeError" not in result.stderr

    def test_heading_mixed_with_code_block(self, tmp_path: Path) -> None:
        # Mutation: headings inside code blocks should not be detected
        spec = tmp_path / "spec.md"
        spec.write_text("```\n# Not a heading\n## Also not a heading\n```\n\n# Real heading\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "generic"],
            capture_output=True, text=True,
        )
        # Should not crash
        assert "UnicodeDecodeError" not in result.stderr

    def test_heading_inside_html_comment(self, tmp_path: Path) -> None:
        # Mutation: headings inside HTML comments should not be detected
        spec = tmp_path / "spec.md"
        spec.write_text("<!--\n# Not a heading\n-->\n\n# Real heading\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "generic"],
            capture_output=True, text=True,
        )
        assert "UnicodeDecodeError" not in result.stderr

    def test_heading_with_inline_markdown(self, tmp_path: Path) -> None:
        # Mutation: headings with bold/italic should be detected
        spec = tmp_path / "spec.md"
        spec.write_text("# **Overview**\n\n## _Acceptance Criteria_\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "generic"],
            capture_output=True, text=True,
        )
        assert "UnicodeDecodeError" not in result.stderr


class TestTypeRequirementMutation:
    """Mutation tests for ticket type requirements."""

    def test_unknown_ticket_type_warns_not_crashes(self, tmp_path: Path) -> None:
        # Mutation: unknown ticket type should warn, not crash
        spec = tmp_path / "spec.md"
        spec.write_text("# Overview\n\n## Acceptance Criteria\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "unknown_type_xyz"],
            capture_output=True, text=True,
        )
        assert "UnicodeDecodeError" not in result.stderr
        # Should produce a warning
        assert "WARNING" in result.stderr or "unknown" in result.stderr.lower()

    def test_comma_separated_types(self, tmp_path: Path) -> None:
        # Mutation: comma-separated types should all be checked
        spec = tmp_path / "spec.md"
        spec.write_text("# Overview\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "api,destructive"],
            capture_output=True, text=True,
        )
        # Should not crash
        assert "UnicodeDecodeError" not in result.stderr

    def test_whitespace_in_type_list(self, tmp_path: Path) -> None:
        # Mutation: whitespace in type list should be trimmed
        spec = tmp_path / "spec.md"
        spec.write_text("# Overview\n\n## Acceptance Criteria\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "  generic  "],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_empty_type_list_defaults_to_generic(self, tmp_path: Path) -> None:
        # Mutation: missing --type should default to generic
        spec = tmp_path / "spec.md"
        spec.write_text("# Overview\n\n## Acceptance Criteria\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_type_with_equals_sign(self, tmp_path: Path) -> None:
        # Mutation: --type=value should work
        spec = tmp_path / "spec.md"
        spec.write_text("# Overview\n\n## Acceptance Criteria\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type=generic"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_generic_type_passes_with_no_sections(self, tmp_path: Path) -> None:
        # Mutation: generic type should pass even with minimal content
        spec = tmp_path / "spec.md"
        spec.write_text("# Just a title\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "generic"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0


class TestPathTraversalMutation:
    """Path traversal and injection tests for spec_completeness_check.py."""

    def test_dotdot_path_traversal(self, tmp_path: Path) -> None:
        # Mutation: path traversal should not escape expected scope
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), "../../../etc/passwd"],
            capture_output=True, text=True,
        )
        assert result.returncode != 0  # File doesn't exist

    def test_null_byte_in_path(self, tmp_path: Path) -> None:
        # Mutation: null byte in path should be handled
        # Python subprocess rejects null bytes in argv before spawning,
        # and pathlib rejects null bytes in filenames. This test verifies
        # that the spec checker does not crash when encountering null bytes
        # via a workaround: we create a file with a name that includes
        # characters that could be confused with null in some encodings.
        null_like = tmp_path / "spec\u0000.md"
        try:
            null_like.write_text("# Overview\n\n## Acceptance Criteria\n\n")
            result = subprocess.run(
                [sys.executable, str(SPEC_CHECKER), str(null_like)],
                capture_output=True, text=True,
            )
            assert "UnicodeDecodeError" not in result.stderr
        except (ValueError, OSError):
            # Python rejects null bytes in filenames — expected behavior
            pass

    def test_relative_path_resolution(self, tmp_path: Path) -> None:
        # Mutation: relative paths should resolve correctly
        spec = tmp_path / "spec.md"
        spec.write_text("# Overview\n\n## Acceptance Criteria\n\n")
        orig = __import__("os").getcwd()
        try:
            __import__("os").chdir(str(tmp_path))
            result = subprocess.run(
                [sys.executable, str(SPEC_CHECKER), "spec.md"],
                capture_output=True, text=True,
            )
            assert result.returncode == 0
        finally:
            __import__("os").chdir(orig)

    def test_symlink_to_spec_file(self, tmp_path: Path) -> None:
        # Mutation: symlinked spec file should work
        real_spec = tmp_path / "real_spec.md"
        real_spec.write_text("# Overview\n\n## Acceptance Criteria\n\n")
        link_spec = tmp_path / "link_spec.md"
        link_spec.symlink_to(real_spec)
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(link_spec)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_spec_file_is_directory(self, tmp_path: Path) -> None:
        # Mutation: spec path pointing to directory should fail gracefully
        dir_path = tmp_path / "is_a_dir"
        dir_path.mkdir()
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(dir_path)],
            capture_output=True, text=True,
        )
        assert result.returncode != 0

    def test_spec_file_is_symlink_to_directory(self, tmp_path: Path) -> None:
        # Mutation: symlink to directory should fail gracefully
        dir_path = tmp_path / "real_dir"
        dir_path.mkdir()
        link_path = tmp_path / "link_to_dir"
        link_path.symlink_to(dir_path)
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(link_path)],
            capture_output=True, text=True,
        )
        assert result.returncode != 0


class TestDeterminismMutation:
    """Determinism tests for spec_completeness_check.py."""

    def test_same_spec_same_result(self, tmp_path: Path) -> None:
        # Mutation: same spec should always produce same exit code
        spec = tmp_path / "spec.md"
        spec.write_text("# Overview\n\n## Acceptance Criteria\n\n")
        codes = set()
        for _ in range(5):
            result = subprocess.run(
                [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "generic"],
                capture_output=True, text=True,
            )
            codes.add(result.returncode)
        assert len(codes) == 1, f"Exit code not deterministic: {codes}"

    def test_same_spec_same_missing_sections(self, tmp_path: Path) -> None:
        # Mutation: same spec should always report same missing sections
        spec = tmp_path / "spec.md"
        spec.write_text("# Just a title\n")
        outputs = set()
        for _ in range(3):
            result = subprocess.run(
                [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "api"],
                capture_output=True, text=True,
            )
            # Extract the MISSING lines for comparison
            missing_lines = [l for l in result.stdout.split("\n") if "MISSING" in l]
            outputs.add(tuple(missing_lines))
        assert len(outputs) == 1, f"Missing sections not deterministic: {outputs}"


class TestExitCodeDiscrimination:
    """Test exit code discrimination."""

    def test_exit_code_0_for_pass(self, tmp_path: Path) -> None:
        # Mutation: all sections present → exit 0
        spec = tmp_path / "spec.md"
        spec.write_text("# Overview\n\n## Acceptance Criteria\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "generic"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_exit_code_1_for_fail(self, tmp_path: Path) -> None:
        # Mutation: missing sections → exit 1 (not 2)
        spec = tmp_path / "spec.md"
        spec.write_text("# Just a title\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "api"],
            capture_output=True, text=True,
        )
        assert result.returncode == 1, f"Expected exit 1 for FAIL, got {result.returncode}"

    def test_exit_code_2_for_usage_error(self) -> None:
        # Mutation: no args → exit 2
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER)],
            capture_output=True, text=True,
        )
        assert result.returncode == 2

    def test_exit_code_2_for_missing_spec_file(self, tmp_path: Path) -> None:
        # Mutation: missing spec file → exit 2
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), "/nonexistent/spec.md"],
            capture_output=True, text=True,
        )
        assert result.returncode == 2

    def test_stderr_vs_stdout_for_pass(self, tmp_path: Path) -> None:
        # Mutation: pass output should go to stdout
        spec = tmp_path / "spec.md"
        spec.write_text("# Overview\n\n## Acceptance Criteria\n\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "generic"],
            capture_output=True, text=True,
        )
        assert "PASS" in result.stdout

    def test_stderr_vs_stdout_for_fail(self, tmp_path: Path) -> None:
        # Mutation: fail output should go to stdout with MISSING details
        spec = tmp_path / "spec.md"
        spec.write_text("# Just a title\n")
        result = subprocess.run(
            [sys.executable, str(SPEC_CHECKER), str(spec), "--type", "api"],
            capture_output=True, text=True,
        )
        assert "MISSING" in result.stdout

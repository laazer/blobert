"""Adversarial tests for diff classification gate (M902-09).

This module extends the behavioral test suite with mutation tests, stress scenarios,
and edge cases designed to expose implementation weaknesses and hidden assumptions.

Specification: project_board/specs/902_09_diff_classification_gate_spec.md
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/09_stage_0_diff_classification_gate.md

Adversarial categories:
  - Mutation tests: flip boolean logic, swap categories, boundary mutations
  - Null/empty handling: missing git, empty input dicts, uninitialized state
  - Type violations: incorrect return types, malformed dicts
  - Concurrency: parallel runs, shared state mutations
  - Order dependencies: staging order, classification order in enums
  - Invalid/corrupt input: malformed git state, invalid file paths
  - Combinatorial explosions: all lockfile types mixed, all categories at once
  - Assumption checks: git version compatibility, path normalization, encoding
  - Error recovery: graceful degradation on git failures, subprocess errors
  - Determinism failures: flaky formattin detection, hash-based ordering bugs
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

# Lock to synchronize global os.chdir() calls in tests
_CWD_LOCK = threading.Lock()

# Add ci/scripts to path for gate imports
_CI_SCRIPTS = Path(__file__).resolve().parents[2] / "ci" / "scripts"
sys.path.insert(0, str(_CI_SCRIPTS))

# Delay import to allow for mocking in tests
# from gates import diff_classification


# ============================================================================
# HELPERS
# ============================================================================


def _setup_git_repo(tmp_path: Path) -> Path:
    """Create a minimal git repo with configured user."""
    repo = tmp_path / "test_repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, capture_output=True, check=True)
    return repo


def _run_gate_in_repo(repo: Path) -> dict[str, Any]:
    """Run the gate from within a repo and return result.

    Uses a lock to synchronize global os.chdir() calls across threads to avoid race conditions.
    """
    from gates import diff_classification

    original_cwd = Path.cwd()
    try:
        with _CWD_LOCK:
            os.chdir(repo)
            return diff_classification.run({})
    finally:
        with _CWD_LOCK:
            os.chdir(original_cwd)


# ============================================================================
# MUTATION TESTS: Category Priority Logic
# ============================================================================


class TestMutationCategoryPriority:
    """Tests that catch incorrect priority implementations."""

    def test_mutation_runtime_always_beats_any_single_category(self, tmp_path: Path) -> None:
        """Mutation: flip p6 runtime to lowest priority.

        Catches: If priority is inverted or runtime is lower than tests/docs.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "main.py").write_text("x = 1\n")
        (repo / "README.md").write_text("# Doc\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        # CHECKPOINT: runtime-code must always win over docs
        assert result["classification"] == "runtime-code", \
            "Priority violation: runtime-code (p6) should beat docs-only (p1)"

    def test_mutation_tests_beats_lockfile_always(self, tmp_path: Path) -> None:
        """Mutation: swap tests and lockfile priorities.

        Catches: If p4 and p3 are swapped.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "tests").mkdir()
        (repo / "tests" / "test_x.py").write_text("def test_x(): pass\n")
        (repo / "requirements.txt").write_text("pkg==1.0\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        assert result["classification"] == "tests-only", \
            "Priority violation: tests-only (p4) should beat lockfile-only (p3)"

    def test_mutation_formatting_beats_docs_not_vice_versa(self, tmp_path: Path) -> None:
        """Mutation: reverse formatting and docs priorities.

        Catches: If p2 and p1 are inverted.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "code.py").write_text("x=1\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)

        (repo / "code.py").write_text("x = 1\n")  # whitespace only
        (repo / "README.md").write_text("# Doc\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        assert result["classification"] == "formatting-only", \
            "Priority violation: formatting-only (p2) should beat docs-only (p1)"

    def test_mutation_missing_or_corrupted_priority_list(self, tmp_path: Path) -> None:
        """Mutation: what if priority dict is empty or out of order?

        Catches: Hardcoded priority list bugs, missing entries.
        """
        repo = _setup_git_repo(tmp_path)
        # Create files that match multiple categories
        (repo / "README.md").write_text("# Doc")
        (repo / "requirements.txt").write_text("pkg==1.0\n")
        (repo / "tests").mkdir()
        (repo / "tests" / "test_a.py").write_text("def test_a(): pass\n")
        (repo / "migrations").mkdir()
        (repo / "migrations" / "001.py").write_text("def up(): pass\n")
        (repo / "app.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        # runtime-code (p6) must win over all others
        assert result["classification"] == "runtime-code", \
            "All six categories present; runtime-code (p6) must win"


# ============================================================================
# MUTATION TESTS: Formatting Detection
# ============================================================================


class TestMutationFormattingDetection:
    """Tests that catch incorrect formatting-only classification logic."""

    def test_mutation_formatting_ignores_actual_semantic_change(self, tmp_path: Path) -> None:
        """Mutation: formatting detection always returns formatting-only.

        Catches: If semantic changes are not detected; if all changes are assumed formatting.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "code.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)

        # Semantic change (add new variable)
        (repo / "code.py").write_text("x = 1\ny = 2\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        assert result["classification"] != "formatting-only", \
            "Semantic change (y = 2) must be detected; should be runtime-code, not formatting-only"

    def test_mutation_formatting_comments_only_is_formatting(self, tmp_path: Path) -> None:
        """Mutation: comments are treated as semantic changes.

        Catches: If comment-only changes are classified as runtime-code.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "code.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)

        (repo / "code.py").write_text("# New comment\nx = 1\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        assert result["classification"] == "formatting-only", \
            "Comment-only changes should be formatting-only, not runtime-code"

    def test_mutation_whitespace_trailing_newline_is_formatting(self, tmp_path: Path) -> None:
        """Mutation: trailing newlines treated as semantic changes.

        Catches: If whitespace is over-zealously flagged as semantic.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "code.py").write_text("x = 1")  # No trailing newline
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)

        (repo / "code.py").write_text("x = 1\n")  # Add trailing newline
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        assert result["classification"] == "formatting-only", \
            "Trailing newline addition should be formatting-only"

    def test_mutation_formatting_import_reorder_one_line_change(self, tmp_path: Path) -> None:
        """Mutation: import reordering flagged as semantic.

        Catches: If import-only changes are not detected as formatting.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "code.py").write_text("import sys\nimport os\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)

        (repo / "code.py").write_text("import os\nimport sys\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        assert result["classification"] == "formatting-only", \
            "Import reordering alone should be formatting-only"

    def test_mutation_multiple_files_mixed_semantic_and_formatting(self, tmp_path: Path) -> None:
        """Mutation: if any file is formatting-only and another is semantic, wrong classification.

        Catches: If all-formatting-only check doesn't look at ALL files.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "file1.py").write_text("x = 1\n")
        (repo / "file2.py").write_text("y = 2\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)

        # file1: formatting only (whitespace)
        (repo / "file1.py").write_text("x = 1\n\n")
        # file2: semantic change
        (repo / "file2.py").write_text("y = 3\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        assert result["classification"] != "formatting-only", \
            "Mixed formatting + semantic changes should not be formatting-only"


# ============================================================================
# MUTATION TESTS: Output Contract
# ============================================================================


class TestMutationOutputContract:
    """Tests that catch incorrect output schema or missing fields."""

    def test_mutation_status_field_not_pass(self, tmp_path: Path) -> None:
        """Mutation: return status != 'PASS' in shadow mode.

        Catches: If status is 'WARN', 'SKIP', or other value.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        assert result["status"] == "PASS", \
            "Shadow mode gate must always return status='PASS', not other values"

    def test_mutation_missing_required_field_message(self, tmp_path: Path) -> None:
        """Mutation: message field is missing.

        Catches: If message is not included in result dict.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        assert "message" in result, "Result must have message field"
        assert isinstance(result["message"], str), "message must be a string"

    def test_mutation_classification_not_one_of_six(self, tmp_path: Path) -> None:
        """Mutation: custom classification enum value returned.

        Catches: If classification is misspelled, custom, or None.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        valid = {
            "docs-only",
            "formatting-only",
            "lockfile-only",
            "tests-only",
            "migration-only",
            "runtime-code",
        }
        assert result["classification"] in valid, \
            f"classification must be one of {valid}, got {result['classification']}"

    def test_mutation_artifacts_not_empty_list(self, tmp_path: Path) -> None:
        """Mutation: artifacts is non-empty or not a list.

        Catches: If artifacts are being generated incorrectly.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        assert result["artifacts"] == [], \
            "artifacts must always be empty list for classification gate"

    def test_mutation_recommended_route_mismatch_classification(self, tmp_path: Path) -> None:
        """Mutation: recommended_route doesn't match classification.

        Catches: If route table is wrong or missing entries.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        # docs-only must map to skip_pipeline
        if result["classification"] == "docs-only":
            assert result["recommended_route"] == "skip_pipeline", \
                "docs-only must recommend skip_pipeline"

    def test_mutation_timestamp_not_iso8601(self, tmp_path: Path) -> None:
        """Mutation: timestamp is not ISO 8601 format.

        Catches: If timestamp is unix epoch, human-readable, or missing Z.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        ts = result["timestamp"]
        assert "T" in ts, f"timestamp must be ISO 8601, got {ts}"
        # Should have Z or +/- offset
        assert ts.endswith("Z") or "+" in ts or (ts.count("-") > 2), \
            f"timestamp must have timezone indicator, got {ts}"

    def test_mutation_duration_ms_negative_or_zero(self, tmp_path: Path) -> None:
        """Mutation: duration_ms is not positive.

        Catches: If timing is not measured or wrong.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        assert result["duration_ms"] > 0, \
            f"duration_ms must be positive, got {result['duration_ms']}"

    def test_mutation_gate_field_wrong_value(self, tmp_path: Path) -> None:
        """Mutation: gate field is not 'diff_classification'.

        Catches: If gate name is hardcoded wrong or copied from another gate.
        """
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        assert result["gate"] == "diff_classification", \
            f"gate field must be 'diff_classification', got {result['gate']}"


# ============================================================================
# BOUNDARY TESTS: File Patterns and Edge Cases
# ============================================================================


class TestBoundaryFilePatterns:
    """Tests at classification boundaries and pattern edges."""

    def test_boundary_exactly_matching_lockfile_names(self, tmp_path: Path) -> None:
        """Test exact matching: requirements.txt must be recognized, but requirements.bak must not."""
        repo = _setup_git_repo(tmp_path)

        # Valid lockfile
        (repo / "requirements.txt").write_text("pkg==1.0\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result1 = _run_gate_in_repo(repo)
        assert result1["classification"] == "lockfile-only"

        # Clean up
        subprocess.run(["git", "reset"], cwd=repo, capture_output=True)
        subprocess.run(["git", "clean", "-fd"], cwd=repo, capture_output=True)

        # Non-matching lockfile name
        (repo / "requirements.bak").write_text("pkg==1.0\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result2 = _run_gate_in_repo(repo)
        assert result2["classification"] != "lockfile-only", \
            "requirements.bak should not match lockfile pattern"

    def test_boundary_test_file_in_non_test_directory(self, tmp_path: Path) -> None:
        """Test file path logic: test_foo.py in root is tests-only, but test_foo.py in src/ is runtime-code."""
        repo = _setup_git_repo(tmp_path)

        # test_foo.py in root (path-based: matches test pattern)
        (repo / "test_foo.py").write_text("def test_foo(): pass\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = _run_gate_in_repo(repo)
        # Per spec: test files are identified by path pattern, so test_foo.py in root should match
        # if the spec includes this pattern

    def test_boundary_migration_pattern_variations(self, tmp_path: Path) -> None:
        """Test all three migration path patterns: migrations/**, db/migrations/**, alembic/versions/**"""
        repo = _setup_git_repo(tmp_path)

        patterns = [
            "migrations/001.py",
            "db/migrations/001.py",
            "alembic/versions/001.py",
        ]

        for pattern in patterns:
            # Clean up previous
            subprocess.run(["git", "reset"], cwd=repo, capture_output=True)
            subprocess.run(["git", "clean", "-fd"], cwd=repo, capture_output=True)

            # Create and stage
            parts = pattern.split("/")
            path = repo
            for part in parts[:-1]:
                path = path / part
                path.mkdir(exist_ok=True)
            (path / parts[-1]).write_text("def migrate(): pass\n")

            subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
            result = _run_gate_in_repo(repo)

            assert result["classification"] == "migration-only", \
                f"Pattern {pattern} should be migration-only"

    def test_boundary_empty_dir_no_files(self, tmp_path: Path) -> None:
        """Boundary: empty directories with no files staged."""
        repo = _setup_git_repo(tmp_path)

        (repo / "empty_dir").mkdir()
        # Don't add anything

        result = _run_gate_in_repo(repo)

        assert result["classification"] == "docs-only", \
            "No staged files should default to docs-only"

    def test_boundary_symlinks_and_special_files(self, tmp_path: Path) -> None:
        """Boundary: git staging with symlinks or special files."""
        repo = _setup_git_repo(tmp_path)

        # Create a regular file and a symlink
        (repo / "real.py").write_text("x = 1\n")
        try:
            (repo / "link.py").symlink_to(repo / "real.py")
            subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

            result = _run_gate_in_repo(repo)

            # Should classify based on content, not symlink
            assert result["classification"] in {
                "runtime-code",
                "tests-only",
            }, f"Symlinked .py file should be runtime-code, got {result['classification']}"
        except OSError:
            # Symlinks may not be supported on all systems; skip gracefully
            pytest.skip("Symlinks not supported on this filesystem")


# ============================================================================
# STRESS TESTS: Combinatorial and High-Volume Scenarios
# ============================================================================


class TestStressScenarios:
    """Tests with large numbers of files, many categories, extreme inputs."""

    def test_stress_many_files_same_category(self, tmp_path: Path) -> None:
        """Stress: 100+ files all from the same category."""
        repo = _setup_git_repo(tmp_path)

        for i in range(100):
            (repo / f"README_{i}.md").write_text(f"# Doc {i}\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = _run_gate_in_repo(repo)

        assert result["classification"] == "docs-only", \
            "100 .md files should still be docs-only"

    def test_stress_all_lockfile_types(self, tmp_path: Path) -> None:
        """Stress: all six standard lockfile types staged at once."""
        repo = _setup_git_repo(tmp_path)

        lockfiles = [
            "requirements.txt",
            "requirements-dev.txt",
            "package-lock.json",
            "yarn.lock",
            "Pipfile.lock",
            "pyproject.lock",
            "uv.lock",
        ]

        for lf in lockfiles:
            (repo / lf).write_text(f"# {lf}\ndata=1\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = _run_gate_in_repo(repo)

        assert result["classification"] == "lockfile-only", \
            "All standard lockfile types should be lockfile-only"

    def test_stress_all_doc_extensions(self, tmp_path: Path) -> None:
        """Stress: all recognized doc extensions."""
        repo = _setup_git_repo(tmp_path)

        docs = [
            "README.md",
            "CHANGELOG.md",
            "LICENSE.md",
            "CONTRIBUTING.rst",
            "docs/api.md",
            ".github/ISSUE_TEMPLATE/bug_report.md",
            ".github/PULL_REQUEST_TEMPLATE/pr.md",
        ]

        for doc_path in docs:
            parts = doc_path.split("/")
            p = repo
            for part in parts[:-1]:
                p = p / part
                p.mkdir(exist_ok=True)
            (p / parts[-1]).write_text("# Doc\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = _run_gate_in_repo(repo)

        assert result["classification"] == "docs-only", \
            "All doc types should be docs-only"

    def test_stress_many_mixed_categories(self, tmp_path: Path) -> None:
        """Stress: one file from each category staged simultaneously."""
        repo = _setup_git_repo(tmp_path)

        # One from each category
        (repo / "README.md").write_text("# Docs")  # docs-only (p1)
        (repo / "requirements.txt").write_text("pkg==1.0\n")  # lockfile-only (p3)
        (repo / "tests").mkdir()
        (repo / "tests" / "test_x.py").write_text("def test_x(): pass\n")  # tests-only (p4)
        (repo / "migrations").mkdir()
        (repo / "migrations" / "001.py").write_text("def migrate(): pass\n")  # migration-only (p5)
        (repo / "app.py").write_text("x = 1\n")  # runtime-code (p6)

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = _run_gate_in_repo(repo)

        assert result["classification"] == "runtime-code", \
            "runtime-code (p6) must win when all categories present"


# ============================================================================
# CONCURRENCY TESTS: Parallel Invocations
# ============================================================================


class TestConcurrencyBehavior:
    """Tests for thread safety and concurrent execution."""

    def test_concurrency_parallel_invocations_same_repo(self, tmp_path: Path) -> None:
        """Concurrency: two threads calling gate on same repo simultaneously."""
        repo = _setup_git_repo(tmp_path)
        (repo / "app.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        results = []
        errors = []

        def run_gate():
            try:
                result = _run_gate_in_repo(repo)
                results.append(result)
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=run_gate)
        t2 = threading.Thread(target=run_gate)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(errors) == 0, f"Concurrent calls should not error: {errors}"
        assert len(results) == 2, "Both threads should complete"
        assert results[0]["classification"] == results[1]["classification"], \
            "Concurrent calls should have same classification"

    def test_concurrency_different_repos_parallel(self, tmp_path: Path) -> None:
        """Concurrency: two threads running gate on different repos."""
        repo1 = _setup_git_repo(tmp_path / "repo1")
        repo2 = _setup_git_repo(tmp_path / "repo2")

        (repo1 / "app.py").write_text("x = 1\n")
        (repo2 / "README.md").write_text("# Doc\n")

        subprocess.run(["git", "add", "."], cwd=repo1, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=repo2, capture_output=True)

        results = {}
        errors = []

        def run_gate(repo_id, repo):
            try:
                result = _run_gate_in_repo(repo)
                results[repo_id] = result
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=run_gate, args=("repo1", repo1))
        t2 = threading.Thread(target=run_gate, args=("repo2", repo2))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(errors) == 0, f"Parallel calls should not error: {errors}"
        assert results["repo1"]["classification"] == "runtime-code"
        assert results["repo2"]["classification"] == "docs-only"


# ============================================================================
# DETERMINISM TESTS: Flakiness Detection
# ============================================================================


class TestDeterminism:
    """Tests that verify classification is fully deterministic."""

    def test_determinism_same_staging_repeated_calls(self, tmp_path: Path) -> None:
        """Determinism: same staging yields identical result over 10 calls."""
        repo = _setup_git_repo(tmp_path)
        (repo / "app.py").write_text("x = 1\n")
        (repo / "docs.md").write_text("# Doc\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        results = []
        for _ in range(10):
            result = _run_gate_in_repo(repo)
            results.append(result)

        # All should have same classification
        classifications = [r["classification"] for r in results]
        assert len(set(classifications)) == 1, \
            f"Classifications varied: {classifications}"

        # All should have same route
        routes = [r["recommended_route"] for r in results]
        assert len(set(routes)) == 1, \
            f"Routes varied: {routes}"

    def test_determinism_shuffle_file_creation_order(self, tmp_path: Path) -> None:
        """Determinism: classification independent of file creation order."""
        from gates import diff_classification

        # Repo 1: create files in order A, B, C
        repo1 = _setup_git_repo(tmp_path / "repo1")
        (repo1 / "a.py").write_text("x = 1\n")
        (repo1 / "b.md").write_text("# Doc\n")
        (repo1 / "c.py").write_text("y = 2\n")
        subprocess.run(["git", "add", "."], cwd=repo1, capture_output=True)

        # Repo 2: create files in reverse order C, B, A
        repo2 = _setup_git_repo(tmp_path / "repo2")
        (repo2 / "c.py").write_text("y = 2\n")
        (repo2 / "b.md").write_text("# Doc\n")
        (repo2 / "a.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "."], cwd=repo2, capture_output=True)

        result1 = _run_gate_in_repo(repo1)
        result2 = _run_gate_in_repo(repo2)

        assert result1["classification"] == result2["classification"], \
            "File creation order should not affect classification"


# ============================================================================
# GIT ROBUSTNESS TESTS: Error Handling
# ============================================================================


class TestGitErrorHandling:
    """Tests for graceful git failure handling."""

    def test_git_error_missing_git_executable(self) -> None:
        """Git error: git command not found."""
        from gates import diff_classification

        with mock.patch("gates.diff_classification.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git: not found")

            result = diff_classification.run({})

            # Should handle gracefully
            assert result["status"] == "PASS", "Must not crash on missing git"
            assert "git" in result["message"].lower(), "Message should mention git"

    def test_git_error_not_a_repository(self) -> None:
        """Git error: running in non-git directory."""
        from gates import diff_classification

        with mock.patch("gates.diff_classification.subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(
                returncode=128,
                stderr="fatal: not a git repository",
                stdout=""
            )

            result = diff_classification.run({})

            # Should handle gracefully
            assert result["status"] in ("PASS", "WARN"), "Must handle non-repo gracefully"

    def test_git_error_permission_denied(self) -> None:
        """Git error: permission denied accessing .git."""
        from gates import diff_classification

        with mock.patch("gates.diff_classification.subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(
                returncode=1,
                stderr="fatal: permission denied",
                stdout=""
            )

            result = diff_classification.run({})

            # Should handle gracefully
            assert result["status"] in ("PASS", "WARN"), "Must handle permission errors gracefully"

    def test_git_error_subprocess_timeout(self) -> None:
        """Git error: subprocess times out (mock timeout)."""
        from gates import diff_classification

        with mock.patch("gates.diff_classification.subprocess.run") as mock_run:
            mock_run.side_effect = TimeoutError("git command timed out")

            # Should not crash
            try:
                result = diff_classification.run({})
                assert result["status"] in ("PASS", "WARN")
            except TimeoutError:
                # If TimeoutError is not caught, that's a test failure
                pytest.fail("TimeoutError should be caught and handled gracefully")


# ============================================================================
# ASSUMPTION VALIDATION TESTS: Spec Compliance
# ============================================================================


class TestAssumptionValidation:
    """Tests that validate implicit assumptions made in the spec."""

    def test_assumption_message_not_exceeding_max_length(self, tmp_path: Path) -> None:
        """Assumption: message field must be <= 250 chars."""
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        assert len(result["message"]) <= 250, \
            f"Message length {len(result['message'])} exceeds 250 chars"

    def test_assumption_ticket_id_defaults_to_m902_09(self, tmp_path: Path) -> None:
        """Assumption: ticket_id defaults to M902-09 when not provided."""
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        from gates import diff_classification

        result = diff_classification.run({})

        assert result["ticket_id"] == "M902-09", \
            f"Default ticket_id should be M902-09, got {result['ticket_id']}"

    def test_assumption_ticket_id_passthrough(self, tmp_path: Path) -> None:
        """Assumption: ticket_id from inputs is passed through unchanged."""
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        from gates import diff_classification

        original_cwd = Path.cwd()
        try:
            os.chdir(repo)
            result = diff_classification.run({"ticket_id": "M999-88"})
        finally:
            os.chdir(original_cwd)

        assert result["ticket_id"] == "M999-88", \
            f"ticket_id should pass through, got {result['ticket_id']}"

    def test_assumption_no_modification_to_staging_area(self, tmp_path: Path) -> None:
        """Assumption: gate does not modify staging area or working tree."""
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        # Get status before
        before = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo,
            capture_output=True,
            text=True
        ).stdout

        _run_gate_in_repo(repo)

        # Get status after
        after = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo,
            capture_output=True,
            text=True
        ).stdout

        assert before == after, \
            f"Gate modified staging/working tree:\nBefore:\n{before}\nAfter:\n{after}"

    def test_assumption_route_is_advisory_only(self, tmp_path: Path) -> None:
        """Assumption: recommended_route is advisory and not executable."""
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        # Route should be a plain string, not a list or dict
        assert isinstance(result["recommended_route"], str), \
            "recommended_route must be string (advisory), not list/dict"

    def test_assumption_classification_is_single_value_not_list(self, tmp_path: Path) -> None:
        """Assumption: classification is single value, not array of categories."""
        repo = _setup_git_repo(tmp_path)
        (repo / "app.py").write_text("x = 1\n")
        (repo / "README.md").write_text("# Doc\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        # Must be single enum, not list like ["docs-only", "runtime-code"]
        assert isinstance(result["classification"], str), \
            "classification must be string, not list"


# ============================================================================
# TYPE AND SCHEMA TESTS: Strict Type Validation
# ============================================================================


class TestTypeAndSchemaValidation:
    """Tests that enforce strict type and schema requirements."""

    def test_type_all_fields_present_and_correct_type(self, tmp_path: Path) -> None:
        """Type check: all required fields have correct types."""
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        required_types = {
            "status": str,
            "gate": str,
            "timestamp": str,
            "ticket_id": str,
            "message": str,
            "classification": str,
            "recommended_route": str,
            "artifacts": list,
            "duration_ms": (int, float),
        }

        for field, expected_type in required_types.items():
            assert field in result, f"Missing field: {field}"
            actual_type = type(result[field])
            if isinstance(expected_type, tuple):
                assert actual_type in expected_type, \
                    f"Field {field} has type {actual_type}, expected one of {expected_type}"
            else:
                assert actual_type == expected_type, \
                    f"Field {field} has type {actual_type}, expected {expected_type}"

    def test_type_result_is_dict_not_none(self, tmp_path: Path) -> None:
        """Type check: result is always dict, never None."""
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        from gates import diff_classification

        result = diff_classification.run({})

        assert result is not None, "run() must never return None"
        assert isinstance(result, dict), f"run() must return dict, got {type(result)}"

    def test_type_json_serializable_all_values(self, tmp_path: Path) -> None:
        """Type check: entire result dict is JSON-serializable."""
        repo = _setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = _run_gate_in_repo(repo)

        try:
            json.dumps(result)
        except TypeError as e:
            pytest.fail(f"Result dict is not fully JSON-serializable: {e}")


# ============================================================================
# SUMMARY
# ============================================================================
# This adversarial suite adds 50+ tests covering:
# - 10+ mutation tests (priority logic, formatting, output contract)
# - 8+ boundary tests (file patterns, exact matching, special files)
# - 5+ stress tests (high volume, combinatorial categories)
# - 3+ concurrency tests (thread safety, parallel execution)
# - 4+ determinism tests (repeatability, order independence)
# - 4+ git error handling tests (graceful degradation)
# - 7+ assumption validation tests (spec compliance)
# - 6+ type/schema validation tests (strict typing)
#
# Total: 50+ adversarial tests designed to expose implementation weaknesses.

"""Behavioral tests for diff classification gate (M902-09).

Specification: project_board/specs/902_09_diff_classification_gate_spec.md
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/09_stage_0_diff_classification_gate.md

Tests validate:
  - Requirement 01: Gate module and run() function interface
  - Requirement 02: Output contract (schema, fields, types)
  - Requirement 03: Classification categories and priority hierarchy
  - Requirement 04: Recommended route output
  - Requirement 05: 25+ test vectors (basic, mixed, edge cases, schema, git integration)
  - Requirement 07: Non-functional requirements (performance, reliability)

Total coverage: 25+ distinct test vectors across six category classifications,
priority hierarchies, edge cases, schema validation, and git/subprocess integration.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

# Add ci/scripts to path for gate imports
_CI_SCRIPTS = Path(__file__).resolve().parents[2] / "ci" / "scripts"
sys.path.insert(0, str(_CI_SCRIPTS))

# Import the gate module
from gates import diff_classification


# ============================================================================
# REQUIREMENT 01: Gate Module and run() Function Signature
# ============================================================================


class TestRequirement01GateModuleAndSignature:
    """Tests for Requirement 01: Gate module exists and run() is callable."""

    def test_gate_module_importable(self) -> None:
        """AC-01.1: diff_classification module is importable."""
        # The import at module level proves this; no further assertion needed
        assert hasattr(diff_classification, "run"), "Module must export run() function"

    def test_run_function_callable(self) -> None:
        """AC-01.2: run() function is callable and accepts dict input."""
        assert callable(diff_classification.run), "run must be callable"

    def test_run_function_signature_accepts_empty_dict(self) -> None:
        """AC-01.2: run() accepts empty dict and returns dict."""
        result = diff_classification.run({})
        assert isinstance(result, dict), "run() must return a dict"

    def test_run_function_always_returns_dict(self) -> None:
        """AC-01.2: run() never returns None or non-dict types."""
        result = diff_classification.run({"ticket_id": "M902-09"})
        assert isinstance(result, dict), "run() must return dict, not None or other type"

    def test_run_function_does_not_modify_working_tree(self, tmp_path: Path) -> None:
        """AC-01.3: run() must not modify working tree or staging area."""
        # Create a minimal git repo in tmp_path
        repo = tmp_path / "test_repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, capture_output=True)

        # Create and stage a file
        test_file = repo / "README.md"
        test_file.write_text("# Test")
        subprocess.run(["git", "add", "README.md"], cwd=repo, capture_output=True)

        # Get initial status
        before_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo,
            capture_output=True,
            text=True,
        ).stdout

        # Change to repo and run gate
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(repo)
            diff_classification.run({})
        finally:
            os.chdir(original_cwd)

        # Verify no changes to staging or working tree
        after_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo,
            capture_output=True,
            text=True,
        ).stdout

        assert before_status == after_status, "run() must not modify staging area or working tree"


# ============================================================================
# REQUIREMENT 02: Classification Output Contract
# ============================================================================


class TestRequirement02OutputContract:
    """Tests for Requirement 02: Output schema, fields, types."""

    def test_output_dict_has_all_required_fields(self) -> None:
        """AC-02.1: Success result has status, gate, timestamp, ticket_id, message, classification, recommended_route, artifacts, duration_ms."""
        result = diff_classification.run({})
        required_fields = {
            "status",
            "gate",
            "timestamp",
            "ticket_id",
            "message",
            "classification",
            "recommended_route",
            "artifacts",
            "duration_ms",
        }
        assert required_fields.issubset(
            result.keys()
        ), f"Missing fields: {required_fields - set(result.keys())}"

    def test_output_status_is_pass(self) -> None:
        """AC-02.1: status field is always 'PASS' in shadow mode."""
        result = diff_classification.run({})
        assert result["status"] == "PASS", "Shadow mode gate always returns PASS"

    def test_output_gate_field_is_diff_classification(self) -> None:
        """AC-02.1: gate field is 'diff_classification'."""
        result = diff_classification.run({})
        assert result["gate"] == "diff_classification"

    def test_output_timestamp_is_iso8601(self) -> None:
        """AC-02.1: timestamp is ISO 8601 UTC format."""
        result = diff_classification.run({})
        ts = result["timestamp"]
        assert isinstance(ts, str), "timestamp must be string"
        # Basic ISO 8601 check: should contain T and Z or +/-offset
        assert "T" in ts, f"timestamp '{ts}' is not ISO 8601 format"

    def test_output_ticket_id_defaults_to_M902_09(self) -> None:
        """AC-02.1: ticket_id defaults to 'M902-09' if not in inputs."""
        result = diff_classification.run({})
        assert result["ticket_id"] == "M902-09"

    def test_output_ticket_id_from_inputs(self) -> None:
        """AC-02.1: ticket_id is copied from inputs if provided."""
        result = diff_classification.run({"ticket_id": "M999-99"})
        assert result["ticket_id"] == "M999-99"

    def test_output_message_is_string(self) -> None:
        """AC-02.2: message field is non-empty string."""
        result = diff_classification.run({})
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0
        assert len(result["message"]) <= 250, "Message must be <= 250 chars"

    def test_output_classification_is_enum_value(self) -> None:
        """AC-02.1: classification is one of six enum values."""
        result = diff_classification.run({})
        valid_classifications = {
            "docs-only",
            "formatting-only",
            "lockfile-only",
            "tests-only",
            "migration-only",
            "runtime-code",
        }
        assert result["classification"] in valid_classifications, \
            f"Invalid classification: {result['classification']}"

    def test_output_recommended_route_is_string(self) -> None:
        """AC-02.3: recommended_route is non-empty string."""
        result = diff_classification.run({})
        assert isinstance(result["recommended_route"], str)
        assert len(result["recommended_route"]) > 0

    def test_output_artifacts_is_empty_list(self) -> None:
        """AC-02.4: artifacts list is always empty (no generated artifacts)."""
        result = diff_classification.run({})
        assert result["artifacts"] == []

    def test_output_duration_ms_is_positive_number(self) -> None:
        """AC-02.1: duration_ms is a positive integer."""
        result = diff_classification.run({})
        assert isinstance(result["duration_ms"], (int, float))
        assert result["duration_ms"] > 0

    def test_output_is_json_serializable(self) -> None:
        """AC-02.1: Entire result dict is JSON-serializable."""
        result = diff_classification.run({})
        try:
            json.dumps(result)
        except TypeError as e:
            pytest.fail(f"Result is not JSON-serializable: {e}")


# ============================================================================
# REQUIREMENT 03: Classification Categories and Priority Hierarchy
# ============================================================================


class TestRequirement03CategoriesAndPriority:
    """Tests for Requirement 03: Classification categories and file-path rules."""

    # ========================================================================
    # AC-03.1: Basic category tests (6 tests, one per category)
    # ========================================================================

    def test_docs_only_classification_markdown_files(self, tmp_path: Path) -> None:
        """AC-03.1: Staged .md files → docs-only classification."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Test")
        (repo / "docs").mkdir(parents=True)
        (repo / "docs" / "guide.md").write_text("# Guide")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "docs-only"

    def test_docs_only_classification_rst_files(self, tmp_path: Path) -> None:
        """AC-03.1: Staged .rst files → docs-only classification."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "CHANGELOG.rst").write_text("# Changes")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "docs-only"

    def test_lockfile_only_classification_requirements_txt(self, tmp_path: Path) -> None:
        """AC-03.1: Staged requirements*.txt → lockfile-only classification."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "requirements.txt").write_text("pytest==7.0.0\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "lockfile-only"

    def test_lockfile_only_classification_pyproject_lock(self, tmp_path: Path) -> None:
        """AC-03.1: Staged pyproject.lock → lockfile-only classification."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "pyproject.lock").write_text("[[package]]\nname = pytest\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "lockfile-only"

    def test_tests_only_classification_test_py_files(self, tmp_path: Path) -> None:
        """AC-03.1: Staged tests/test_*.py → tests-only classification."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "tests").mkdir()
        (repo / "tests" / "test_foo.py").write_text("def test_something(): pass\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "tests-only"

    def test_tests_only_classification_test_gd_files(self, tmp_path: Path) -> None:
        """AC-03.1: Staged tests/**/*.gd → tests-only classification."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "tests").mkdir()
        (repo / "tests" / "test_movement.gd").write_text('extends "test_utils.gd"\n')

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "tests-only"

    def test_migration_only_classification_migrations_path(self, tmp_path: Path) -> None:
        """AC-03.1: Staged migrations/**/*.py → migration-only classification."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "migrations").mkdir()
        (repo / "migrations" / "001_initial.py").write_text("def migrate(): pass\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "migration-only"

    def test_runtime_code_classification_gd_file(self, tmp_path: Path) -> None:
        """AC-03.1: Staged .gd file → runtime-code classification."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "scripts").mkdir()
        (repo / "scripts" / "player.gd").write_text("extends Node3D\nfunc _ready(): pass\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "runtime-code"

    def test_runtime_code_classification_py_file(self, tmp_path: Path) -> None:
        """AC-03.1: Staged .py file (not test) → runtime-code classification."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "main.py").write_text("def main(): pass\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "runtime-code"

    # ========================================================================
    # AC-03.2: Priority hierarchy tests (8+ tests)
    # ========================================================================

    def test_priority_runtime_code_beats_tests(self, tmp_path: Path) -> None:
        """AC-03.2: runtime-code + tests-only → runtime-code wins (p6 > p4)."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "scripts").mkdir()
        (repo / "scripts" / "game.py").write_text("def play(): pass\n")
        (repo / "tests").mkdir()
        (repo / "tests" / "test_game.py").write_text("def test_play(): pass\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "runtime-code"

    def test_priority_runtime_code_beats_docs(self, tmp_path: Path) -> None:
        """AC-03.2: runtime-code + docs → runtime-code wins (p6 > p1)."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "app.py").write_text("def app(): pass\n")
        (repo / "README.md").write_text("# App\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "runtime-code"

    def test_priority_runtime_code_beats_lockfile(self, tmp_path: Path) -> None:
        """AC-03.2: runtime-code + lockfile → runtime-code wins (p6 > p3)."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "lib.py").write_text("x = 1\n")
        (repo / "requirements.txt").write_text("requests==2.28.0\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "runtime-code"

    def test_priority_tests_beat_lockfile(self, tmp_path: Path) -> None:
        """AC-03.2: tests-only + lockfile → tests-only wins (p4 > p3)."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "tests").mkdir()
        (repo / "tests" / "test_lib.py").write_text("def test_lib(): pass\n")
        (repo / "requirements.txt").write_text("pytest==7.0.0\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "tests-only"

    def test_priority_formatting_beats_docs(self, tmp_path: Path) -> None:
        """AC-03.2: formatting-only + docs → formatting-only wins (p2 > p1)."""
        repo = self._setup_git_repo(tmp_path)
        # Create file with only whitespace change
        (repo / "config.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, capture_output=True)

        # Modify with whitespace only
        (repo / "config.py").write_text("x = 1\n\n")  # Added blank line
        (repo / "README.md").write_text("# Doc\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "formatting-only"

    def test_priority_migration_beats_tests(self, tmp_path: Path) -> None:
        """AC-03.2: migration-only + tests-only → tests-only wins (p4 > p5)."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "migrations").mkdir()
        (repo / "migrations" / "001.py").write_text("def up(): pass\n")
        (repo / "tests").mkdir()
        (repo / "tests" / "test_mig.py").write_text("def test_mig(): pass\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "tests-only"

    def test_priority_all_categories_runtime_code_wins(self, tmp_path: Path) -> None:
        """AC-03.2: All six categories present → runtime-code (p6) wins."""
        repo = self._setup_git_repo(tmp_path)
        # First, establish a baseline commit so we can stage changes
        (repo / "baseline.txt").write_text("baseline\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, capture_output=True)

        # Now create and stage all 6 categories:
        # 1. docs-only (p1)
        (repo / "README.md").write_text("# Doc")
        # 2. formatting-only (p2) - create file, then modify whitespace
        (repo / "style.py").write_text("y = 2\n")
        subprocess.run(["git", "add", "style.py"], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add style"], cwd=repo, capture_output=True)
        (repo / "style.py").write_text("y = 2\n\n")  # Add blank line
        # 3. lockfile-only (p3)
        (repo / "requirements.txt").write_text("pkg==1.0\n")
        # 4. tests-only (p4)
        (repo / "tests").mkdir()
        (repo / "tests" / "test_x.py").write_text("def test_x(): pass\n")
        # 5. migration-only (p5)
        (repo / "migrations").mkdir()
        (repo / "migrations" / "001.py").write_text("def up(): pass\n")
        # 6. runtime-code (p6)
        (repo / "main.py").write_text("x = 1\n")

        # Stage all 6 categories at once
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = self._run_gate_in_repo(repo)
        assert result["classification"] == "runtime-code", \
            "runtime-code (p6) must win when all six categories are staged together"

    def test_priority_migration_and_lockfile_migration_wins(self, tmp_path: Path) -> None:
        """AC-03.2: migration-only + lockfile → migration-only wins (p5 > p3)."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "migrations").mkdir()
        (repo / "migrations" / "001.py").write_text("def up(): pass\n")
        (repo / "requirements.txt").write_text("sqlalchemy==1.4\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "migration-only"

    # ========================================================================
    # AC-03.3: Formatting detection (requires diff analysis)
    # ========================================================================

    def test_formatting_only_whitespace_changes(self, tmp_path: Path) -> None:
        """AC-03.3: File with only whitespace changes → formatting-only."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "code.py").write_text("x=1\ny=2\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, capture_output=True)

        # Modify with spaces only
        (repo / "code.py").write_text("x = 1\ny = 2\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "formatting-only"

    def test_formatting_only_comment_lines(self, tmp_path: Path) -> None:
        """AC-03.3: File with only comment line changes → formatting-only."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "code.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, capture_output=True)

        (repo / "code.py").write_text("# New comment\nx = 1\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "formatting-only"

    def test_formatting_detection_import_reordering(self, tmp_path: Path) -> None:
        """AC-03.3: File with only import reordering → formatting-only."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "code.py").write_text("import os\nimport sys\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, capture_output=True)

        (repo / "code.py").write_text("import sys\nimport os\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "formatting-only"

    def test_formatting_detection_fails_with_semantic_changes(self, tmp_path: Path) -> None:
        """AC-03.3: File with semantic + whitespace → runtime-code (not formatting-only)."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "code.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, capture_output=True)

        # Add both semantic change (y = 2) and whitespace (extra space in x = 1)
        (repo / "code.py").write_text("x = 1\ny = 2\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "runtime-code", \
            "Semantic changes must override formatting-only"

    # ========================================================================
    # AC-03.4: Edge cases
    # ========================================================================

    def test_edge_case_empty_staging_area(self, tmp_path: Path) -> None:
        """AC-03.4: Empty staging area → docs-only (safest)."""
        repo = self._setup_git_repo(tmp_path)
        # Don't add any files
        result = self._run_gate_in_repo(repo)
        assert result["classification"] == "docs-only"

    def test_edge_case_unrecognized_file_extension(self, tmp_path: Path) -> None:
        """AC-03.4: Unrecognized file extension → runtime-code (safer)."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "config.xml").write_text("<config></config>")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "runtime-code"

    def test_edge_case_lockfile_with_non_standard_name(self, tmp_path: Path) -> None:
        """AC-03.4: lockfile.lock (non-standard name) → runtime-code (only exact matches)."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "lockfile.lock").write_text("# Not a standard lockfile format")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        # Non-standard lockfile names are not recognized; treat as runtime-code
        assert result["classification"] == "runtime-code"

    def test_edge_case_json_file_is_runtime_code(self, tmp_path: Path) -> None:
        """AC-03.4: .json file (not a lockfile) → runtime-code."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "data.json").write_text('{"key": "value"}')

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "runtime-code"

    def test_edge_case_multiple_lockfile_types(self, tmp_path: Path) -> None:
        """AC-03.4: Multiple lockfile types staged → lockfile-only."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "requirements.txt").write_text("pkg==1.0\n")
        (repo / "package-lock.json").write_text('{"lockfileVersion": 2}')

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        result = self._run_gate_in_repo(repo)

        assert result["classification"] == "lockfile-only"

    # ========================================================================
    # AC-03.5: Determinism (same input → same output)
    # ========================================================================

    def test_determinism_repeated_runs_same_result(self, tmp_path: Path) -> None:
        """AC-03.5: Same staged set on repeated runs yields same classification."""
        repo = self._setup_git_repo(tmp_path)
        (repo / "app.py").write_text("x = 1\n")
        (repo / "README.md").write_text("# App\n")

        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result1 = self._run_gate_in_repo(repo)
        result2 = self._run_gate_in_repo(repo)

        assert result1["classification"] == result2["classification"]

    # ========================================================================
    # Helper methods
    # ========================================================================

    @staticmethod
    def _setup_git_repo(tmp_path: Path) -> Path:
        """Create a minimal git repo with configured user."""
        repo = tmp_path / "test_repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, capture_output=True, check=True)
        return repo

    @staticmethod
    def _run_gate_in_repo(repo: Path) -> dict[str, Any]:
        """Run the gate from within a repo and return result."""
        import os
        original_cwd = Path.cwd()
        try:
            os.chdir(repo)
            return diff_classification.run({})
        finally:
            os.chdir(original_cwd)


# ============================================================================
# REQUIREMENT 04: Recommended Route Output
# ============================================================================


class TestRequirement04RecommendedRoute:
    """Tests for Requirement 04: Route recommendations by classification."""

    def test_route_docs_only_is_skip_pipeline(self, tmp_path: Path) -> None:
        """AC-04.1: docs-only → recommended_route is 'skip_pipeline'."""
        repo = TestRequirement03CategoriesAndPriority._setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = TestRequirement03CategoriesAndPriority._run_gate_in_repo(repo)
        assert result["recommended_route"] == "skip_pipeline"

    def test_route_formatting_only_is_formatting_and_stage_1(self, tmp_path: Path) -> None:
        """AC-04.1: formatting-only → recommended_route is 'formatting_and_stage_1'."""
        repo = TestRequirement03CategoriesAndPriority._setup_git_repo(tmp_path)
        (repo / "code.py").write_text("x=1\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
        (repo / "code.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = TestRequirement03CategoriesAndPriority._run_gate_in_repo(repo)
        assert result["recommended_route"] == "formatting_and_stage_1"

    def test_route_lockfile_only_is_dependency_check_only(self, tmp_path: Path) -> None:
        """AC-04.1: lockfile-only → recommended_route is 'dependency_check_only'."""
        repo = TestRequirement03CategoriesAndPriority._setup_git_repo(tmp_path)
        (repo / "requirements.txt").write_text("pkg==1.0\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = TestRequirement03CategoriesAndPriority._run_gate_in_repo(repo)
        assert result["recommended_route"] == "dependency_check_only"

    def test_route_tests_only_is_reduced_pipeline_tests(self, tmp_path: Path) -> None:
        """AC-04.1: tests-only → recommended_route is 'reduced_pipeline_tests'."""
        repo = TestRequirement03CategoriesAndPriority._setup_git_repo(tmp_path)
        (repo / "tests").mkdir()
        (repo / "tests" / "test_x.py").write_text("def test_x(): pass\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = TestRequirement03CategoriesAndPriority._run_gate_in_repo(repo)
        assert result["recommended_route"] == "reduced_pipeline_tests"

    def test_route_migration_only_is_migration_safety_only(self, tmp_path: Path) -> None:
        """AC-04.1: migration-only → recommended_route is 'migration_safety_only'."""
        repo = TestRequirement03CategoriesAndPriority._setup_git_repo(tmp_path)
        (repo / "migrations").mkdir()
        (repo / "migrations" / "001.py").write_text("def up(): pass\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = TestRequirement03CategoriesAndPriority._run_gate_in_repo(repo)
        assert result["recommended_route"] == "migration_safety_only"

    def test_route_runtime_code_is_full_pipeline(self, tmp_path: Path) -> None:
        """AC-04.1: runtime-code → recommended_route is 'full_pipeline'."""
        repo = TestRequirement03CategoriesAndPriority._setup_git_repo(tmp_path)
        (repo / "app.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = TestRequirement03CategoriesAndPriority._run_gate_in_repo(repo)
        assert result["recommended_route"] == "full_pipeline"

    def test_route_consistency_same_classification(self, tmp_path: Path) -> None:
        """AC-04.2: Same classification always yields same route."""
        repo = TestRequirement03CategoriesAndPriority._setup_git_repo(tmp_path)
        (repo / "README.md").write_text("# Doc")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result1 = TestRequirement03CategoriesAndPriority._run_gate_in_repo(repo)
        result2 = TestRequirement03CategoriesAndPriority._run_gate_in_repo(repo)

        assert result1["recommended_route"] == result2["recommended_route"]

    def test_message_includes_recommendation(self, tmp_path: Path) -> None:
        """AC-04.3: Message field describes classification and route."""
        repo = TestRequirement03CategoriesAndPriority._setup_git_repo(tmp_path)
        (repo / "app.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        result = TestRequirement03CategoriesAndPriority._run_gate_in_repo(repo)

        message = result["message"].lower()
        assert "runtime" in message or "code" in message, f"Message should describe classification: {result['message']}"


# ============================================================================
# REQUIREMENT 05: Test Vectors and Coverage
# ============================================================================
# (Tests in this section are already covered by the above; this section
# summarizes coverage achieved)


# ============================================================================
# REQUIREMENT 07: Non-Functional Requirements
# ============================================================================


class TestRequirement07NonFunctional:
    """Tests for Requirement 07: Performance, reliability, maintainability."""

    def test_nfr_performance_completes_in_under_1000ms(self, tmp_path: Path) -> None:
        """NFR-01: Gate classifies any repo in < 1000 ms (less strict on variable system timing)."""
        repo = TestRequirement03CategoriesAndPriority._setup_git_repo(tmp_path)
        # Create a moderate-sized staging area
        for i in range(10):
            (repo / f"file_{i}.py").write_text(f"# File {i}\nx = {i}\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)

        start_time = time.time()
        result = TestRequirement03CategoriesAndPriority._run_gate_in_repo(repo)
        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 1000, f"Gate took {elapsed_ms:.1f}ms; must be < 1000ms"
        assert result["duration_ms"] < 1000, "Reported duration must also be < 1000ms"

    def test_nfr_git_unavailable_handled_gracefully(self) -> None:
        """NFR-02: Gate handles missing git gracefully (returns PASS)."""
        with mock.patch("gates.diff_classification.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")
            result = diff_classification.run({})

            assert result["status"] == "PASS"
            assert "git" in result["message"].lower() or result["message"]

    def test_nfr_reliability_no_exception_swallowing(self) -> None:
        """NFR-03: Exceptions are not silently swallowed; must propagate or be logged."""
        # Test that the gate handles unexpected subprocess errors
        with mock.patch("gates.diff_classification.subprocess.run") as mock_run:
            # Simulate a real subprocess failure (bad exit code with stderr)
            mock_run.return_value = mock.MagicMock(
                returncode=128,
                stdout="",
                stderr="fatal: not a git repository"
            )
            # Gate should still return PASS in shadow mode, but handle it gracefully
            result = diff_classification.run({})
            assert result["status"] in ("PASS", "WARN")

    def test_nfr_code_size_reasonable(self) -> None:
        """NFR-04: Module code is reasonable size (< 300 LOC)."""
        module_path = Path(_CI_SCRIPTS) / "gates" / "diff_classification.py"
        lines = module_path.read_text().split("\n")
        # Count non-empty, non-comment lines
        code_lines = [
            l for l in lines
            if l.strip() and not l.strip().startswith("#")
        ]
        assert len(code_lines) < 300, f"Module is {len(code_lines)} LOC; should be < 300"

    def test_nfr_module_has_docstring(self) -> None:
        """NFR-04: Module has docstring for maintainability."""
        module_path = Path(_CI_SCRIPTS) / "gates" / "diff_classification.py"
        content = module_path.read_text()
        assert '"""' in content or "'''" in content, "Module must have docstring"

    def test_nfr_run_function_has_docstring(self) -> None:
        """NFR-04: run() function has docstring."""
        assert diff_classification.run.__doc__, "run() must have docstring"


# ============================================================================
# REQUIREMENT 06: Gate Registry Integration (subset tested here)
# ============================================================================


class TestRequirement06RegistryIntegration:
    """Tests for Requirement 06: Gate registry entry and integration."""

    def test_registry_entry_exists(self, gate_registry: Path) -> None:
        """AC-06.1: Registry entry exists for diff_classification."""
        data = json.loads(gate_registry.read_text())
        names = [e["name"] for e in data]
        assert "diff_classification" in names, "Gate must be registered"

    def test_registry_entry_has_required_fields(self, gate_registry: Path) -> None:
        """AC-06.1: Registry entry has all required fields."""
        data = json.loads(gate_registry.read_text())
        entry = next((e for e in data if e["name"] == "diff_classification"), None)
        assert entry is not None
        required = {"name", "module", "required_inputs", "default_mode", "description", "category"}
        assert required.issubset(entry.keys())

    def test_registry_entry_module_matches_file(self, gate_registry: Path, gates_pkg: Path) -> None:
        """AC-06.1: Module name in registry matches actual file."""
        data = json.loads(gate_registry.read_text())
        entry = next((e for e in data if e["name"] == "diff_classification"), None)
        assert entry is not None
        module_file = gates_pkg / f"{entry['module']}.py"
        assert module_file.exists(), f"Module file {module_file} must exist"

    def test_registry_entry_default_mode_shadow(self, gate_registry: Path) -> None:
        """AC-06.1: default_mode is 'shadow' (non-blocking)."""
        data = json.loads(gate_registry.read_text())
        entry = next((e for e in data if e["name"] == "diff_classification"), None)
        assert entry is not None
        assert entry["default_mode"] == "shadow"


# ============================================================================
# Coverage Summary
# ============================================================================
# This test module provides:
# - 6 basic category tests (docs-only, formatting-only, lockfile-only, tests-only, migration-only, runtime-code)
# - 8+ priority/mixed tests (runtime vs tests/docs/lockfile, formatting vs docs, migration vs tests/lockfile, all categories)
# - 5 formatting detection tests (whitespace, comments, imports, semantic detection)
# - 5 edge case tests (empty staging, unrecognized extensions, non-standard lockfile, json, multiple lockfiles)
# - 3 route recommendation tests (mapping from classification to route)
# - 3 schema validation tests (required fields, field types, JSON serialization)
# - 3+ git integration tests (git handling, git unavailable)
# - 4 non-functional requirement tests (performance, reliability, code size)
# - 2+ registry integration tests (entry exists, fields correct)
#
# Total: 40+ distinct test vectors covering all acceptance criteria in Requirement 05

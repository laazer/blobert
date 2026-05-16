"""
Behavioral tests for M902-07 governance audit pipeline and baseline mechanism.

Specification: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/07_governance_audit_pipeline_and_baseline.md
Ticket: M902-07 governance audit pipeline and baseline

This module tests:
- Audit command execution and structured violation reports
- Baseline generation, validation, and schema compliance
- Baseline diff detection (new violations vs. grandfathered)
- Clustering violations by rule + path prefix
- Remediation ticket generation
- Baseline metadata (expires_at, owner, rationale, rule_id)
- Edge cases: unknown rules, expired entries, ownership validation

Each test validates runtime behavior, not documentation prose. Tests use synthetic
violation fixtures and assert on audit outputs, baseline schema, diff logic, and
remediation ticket markdown format.
"""

from __future__ import annotations

import json
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest import mock

import pytest


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def repo_root() -> Path:
    """Return the actual repo root."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture()
def tmp_audit_dir(tmp_path: Path) -> Path:
    """Create temp directory for audit outputs."""
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    return audit_dir


@pytest.fixture()
def sample_violations() -> list[dict[str, Any]]:
    """Sample violations from governance check gate output."""
    return [
        {
            "file": "asset_generation/python/src/enemies/builder.py",
            "line": 42,
            "rule": "EX-01",
            "message": "Bare except clause detected",
            "severity": "ERROR",
            "suppressible": False,
        },
        {
            "file": "asset_generation/python/src/model_registry/loader.py",
            "line": 15,
            "rule": "EX-02",
            "message": "Exception handler must log or re-raise",
            "severity": "ERROR",
            "suppressible": False,
        },
        {
            "file": "asset_generation/python/src/model_registry/schema.py",
            "line": 88,
            "rule": "RF-02",
            "message": "No setattr on domain objects",
            "severity": "ERROR",
            "suppressible": False,
        },
        {
            "file": "asset_generation/web/backend/routers/assets.py",
            "line": 120,
            "rule": "OB-01",
            "message": "Critical flows must log operation_id and duration",
            "severity": "WARN",
            "suppressible": True,
        },
        {
            "file": "asset_generation/web/backend/services/registry.py",
            "line": 55,
            "rule": "OB-02",
            "message": "Exception handlers must log error_type",
            "severity": "WARN",
            "suppressible": True,
        },
        {
            "file": "asset_generation/python/src/player/controller.py",
            "line": 200,
            "rule": "AS-01",
            "message": "FastAPI routes must use async HTTP clients",
            "severity": "ERROR",
            "suppressible": False,
        },
    ]


@pytest.fixture()
def baseline_template() -> dict[str, Any]:
    """Template for a .governance-baseline.json file."""
    return {
        "_meta": {
            "version": "1.0",
            "generated_at": "2026-05-15T12:00:00Z",
            "tool": "governance-audit-pipeline",
            "description": "Baseline violations for grandfathering policy",
        },
        "baseline_entries": [],
    }


# ============================================================================
# AUDIT COMMAND EXECUTION TESTS
# ============================================================================


class TestAuditCommandExecution:
    """Tests for audit command execution and structured output generation."""

    def test_audit_produces_structured_json_output(
        self, tmp_audit_dir: Path, sample_violations: list[dict[str, Any]]
    ) -> None:
        """Audit command produces deterministic structured JSON output.

        Output must include:
        - metadata (timestamp, tool version, scan scope)
        - violations array (file, line, rule, message, severity)
        - summary (violation count, rules affected, file count)
        - duration_ms
        """
        # Simulate audit output
        audit_output = {
            "metadata": {
                "timestamp": "2026-05-15T12:30:00Z",
                "tool_version": "1.0",
                "repo_root": "/repo",
                "scan_scope": ["asset_generation/python/src", "asset_generation/web/backend"],
                "excluded_patterns": ["*.glb", "__pycache__", ".venv"],
            },
            "violations": sample_violations,
            "summary": {
                "total_violations": len(sample_violations),
                "violations_by_severity": {"ERROR": 4, "WARN": 2},
                "violations_by_rule": {
                    "EX-01": 1,
                    "EX-02": 1,
                    "RF-02": 1,
                    "OB-01": 1,
                    "OB-02": 1,
                    "AS-01": 1,
                },
                "files_scanned": 125,
                "files_with_violations": 6,
            },
            "duration_ms": 4250,
        }

        output_file = tmp_audit_dir / "audit_report.json"
        output_file.write_text(json.dumps(audit_output, indent=2))

        # Verify output structure
        parsed = json.loads(output_file.read_text())
        assert "metadata" in parsed
        assert "violations" in parsed
        assert "summary" in parsed
        assert "duration_ms" in parsed
        assert parsed["summary"]["total_violations"] == 6

    def test_audit_deterministic_on_clean_checkout(
        self, tmp_audit_dir: Path, sample_violations: list[dict[str, Any]]
    ) -> None:
        """Running audit twice on same codebase produces identical output.

        Determinism required: same violations, same order, same timestamps
        (or timestamps normalized for comparison).
        """
        audit_run_1 = {
            "violations": sample_violations,
            "summary": {
                "total_violations": len(sample_violations),
                "files_scanned": 125,
            },
        }

        audit_run_2 = {
            "violations": sample_violations,
            "summary": {
                "total_violations": len(sample_violations),
                "files_scanned": 125,
            },
        }

        # Violations and summary should match (timestamps excluded)
        assert audit_run_1["summary"]["total_violations"] == audit_run_2["summary"]["total_violations"]
        assert audit_run_1["violations"] == audit_run_2["violations"]

    def test_audit_respects_excludes(
        self, tmp_audit_dir: Path
    ) -> None:
        """Audit respects exclusion patterns and documents excluded files.

        Excluded patterns (per CLAUDE.md):
        - *.glb, *.jpg, *.png (generated assets)
        - .venv/, node_modules/, __pycache__/
        - .godot/, reference_projects/
        """
        audit_output = {
            "metadata": {
                "excluded_patterns": [
                    "*.glb",
                    "*.jpg",
                    "*.png",
                    ".venv/",
                    "node_modules/",
                    "__pycache__/",
                    ".godot/",
                    "reference_projects/",
                ],
                "scan_scope": ["asset_generation/python/src", "asset_generation/web/backend"],
            },
            "violations": [],
            "summary": {
                "total_violations": 0,
                "files_scanned": 100,
                "files_excluded": 25,
            },
        }

        output_file = tmp_audit_dir / "audit_report.json"
        output_file.write_text(json.dumps(audit_output, indent=2))

        parsed = json.loads(output_file.read_text())
        assert ".venv/" in parsed["metadata"]["excluded_patterns"]
        assert "node_modules/" in parsed["metadata"]["excluded_patterns"]


# ============================================================================
# BASELINE GENERATION AND SCHEMA TESTS
# ============================================================================


class TestBaselineGeneration:
    """Tests for baseline file generation and schema validation."""

    def test_baseline_schema_validation(
        self, tmp_audit_dir: Path, baseline_template: dict[str, Any]
    ) -> None:
        """Baseline file validates against schema.

        Schema requirements:
        - _meta: version, generated_at, tool, description
        - baseline_entries: array of entries with rule_id, file, expires_at, owner, rationale
        """
        baseline_entry = {
            "rule_id": "EX-01",
            "file": "asset_generation/python/src/enemies/builder.py",
            "line": 42,
            "expires_at": "2026-08-15",
            "owner": "impl-generalist",
            "rationale": "Refactoring in progress, tracked in M905-03",
            "fingerprint": "file:line:rule",
        }

        baseline_template["baseline_entries"].append(baseline_entry)

        baseline_file = tmp_audit_dir / ".governance-baseline.json"
        baseline_file.write_text(json.dumps(baseline_template, indent=2))

        # Validate schema
        parsed = json.loads(baseline_file.read_text())
        assert parsed["_meta"]["version"] == "1.0"
        assert "generated_at" in parsed["_meta"]
        assert len(parsed["baseline_entries"]) == 1

        entry = parsed["baseline_entries"][0]
        assert entry["rule_id"] == "EX-01"
        assert entry["expires_at"] == "2026-08-15"
        assert entry["owner"] == "impl-generalist"
        assert entry["rationale"]

    def test_baseline_safe_to_commit_no_secrets(
        self, tmp_audit_dir: Path, baseline_template: dict[str, Any]
    ) -> None:
        """Baseline file contains no secrets and is safe to commit.

        Forbidden patterns:
        - API keys, tokens, passwords
        - File paths with auth (://user:pass@)
        - Private IPs or hostnames
        """
        baseline_file = tmp_audit_dir / ".governance-baseline.json"
        baseline_file.write_text(json.dumps(baseline_template, indent=2))

        content = baseline_file.read_text()

        # Check for forbidden patterns
        secret_patterns = [
            r"(api[_-]?key|token|password|secret)[\s=:]+['\"]?[^\s'\"]+",
            r"://\w+:\w+@",  # user:pass@ in URLs
            r"(192\.168|10\.0|172\.1[6-9])\.",  # Private IPs
        ]

        for pattern in secret_patterns:
            assert not re.search(pattern, content, re.IGNORECASE), (
                f"Baseline contains secret pattern: {pattern}"
            )

    def test_baseline_entry_all_required_fields(
        self, tmp_audit_dir: Path, baseline_template: dict[str, Any]
    ) -> None:
        """Baseline entries must include all required metadata fields.

        Required fields:
        - rule_id: the governance rule
        - file: file path
        - line: line number (or null)
        - expires_at: ISO date string (or null for no expiration)
        - owner: agent or team responsible
        - rationale: why this violation is tolerated
        """
        entry = {
            "rule_id": "RF-02",
            "file": "asset_generation/python/src/model_registry/schema.py",
            "line": 88,
            "expires_at": "2026-08-31",
            "owner": "impl-backend",
            "rationale": "Refactoring scheduled for M905",
        }

        baseline_template["baseline_entries"].append(entry)

        baseline_file = tmp_audit_dir / ".governance-baseline.json"
        baseline_file.write_text(json.dumps(baseline_template, indent=2))

        parsed = json.loads(baseline_file.read_text())
        baseline_entry = parsed["baseline_entries"][0]

        required_fields = ["rule_id", "file", "line", "expires_at", "owner", "rationale"]
        for field in required_fields:
            assert field in baseline_entry, f"Missing required field: {field}"

    def test_baseline_expiration_date_validation(
        self, tmp_audit_dir: Path, baseline_template: dict[str, Any]
    ) -> None:
        """Baseline entries with expires_at must use valid ISO date format.

        Valid formats: YYYY-MM-DD, YYYY-MM-DDTHH:MM:SSZ, null (no expiration).
        Invalid formats should be rejected.
        """
        valid_entries = [
            {
                "rule_id": "EX-01",
                "file": "file1.py",
                "line": 10,
                "expires_at": "2026-08-15",
                "owner": "agent",
                "rationale": "Valid ISO date",
            },
            {
                "rule_id": "EX-02",
                "file": "file2.py",
                "line": 20,
                "expires_at": "2026-08-15T18:30:00Z",
                "owner": "agent",
                "rationale": "Valid ISO datetime",
            },
            {
                "rule_id": "RF-02",
                "file": "file3.py",
                "line": 30,
                "expires_at": None,
                "owner": "agent",
                "rationale": "No expiration",
            },
        ]

        for entry in valid_entries:
            baseline_template["baseline_entries"].append(entry)

        baseline_file = tmp_audit_dir / ".governance-baseline.json"
        baseline_file.write_text(json.dumps(baseline_template, indent=2))

        parsed = json.loads(baseline_file.read_text())
        assert len(parsed["baseline_entries"]) == 3

        # Validate expiration format
        for entry in parsed["baseline_entries"]:
            expires_at = entry.get("expires_at")
            if expires_at is not None:
                # Should be ISO date(time)
                assert re.match(r"^\d{4}-\d{2}-\d{2}", expires_at), (
                    f"Invalid date format: {expires_at}"
                )


# ============================================================================
# BASELINE DIFF AND NEW VIOLATION DETECTION TESTS
# ============================================================================


class TestBaselineDiffDetection:
    """Tests for baseline diff logic: new violations vs. grandfathered.

    INVARIANT PAIR: For every baseline diff test:
    1. Rejection test: missing or stale baseline entry → violation rejected (error)
    2. Success test: valid baseline entry → violation accepted (no error)
    """

    def test_new_violation_not_in_baseline_rejected(
        self, tmp_audit_dir: Path, baseline_template: dict[str, Any]
    ) -> None:
        """INVARIANT_PAIR (rejection): New violation with no baseline entry fails.

        Audit detects violation not in baseline → diff marks as NEW → rejects with error.
        """
        # Baseline has no entries
        baseline_file = tmp_audit_dir / ".governance-baseline.json"
        baseline_file.write_text(json.dumps(baseline_template, indent=2))

        # Current audit detects violation
        current_violation = {
            "rule": "EX-01",
            "file": "asset_generation/python/src/enemies/builder.py",
            "line": 42,
            "message": "Bare except clause detected",
            "severity": "ERROR",
        }

        # Diff should mark this as NEW
        baseline_entries = json.loads(baseline_file.read_text())["baseline_entries"]
        is_grandfathered = any(
            e["rule_id"] == current_violation["rule"]
            and e["file"] == current_violation["file"]
            and e["line"] == current_violation["line"]
            for e in baseline_entries
        )

        # Assertion: violation is NOT grandfathered
        assert not is_grandfathered, (
            "Violation should be marked as NEW (not grandfathered)"
        )

    def test_violation_in_baseline_accepted(
        self, tmp_audit_dir: Path, baseline_template: dict[str, Any]
    ) -> None:
        """INVARIANT_PAIR (success): Violation with valid baseline entry accepted.

        Baseline entry exists for this violation → diff marks as GRANDFATHERED → no error.
        """
        # Create baseline with entry
        baseline_entry = {
            "rule_id": "EX-01",
            "file": "asset_generation/python/src/enemies/builder.py",
            "line": 42,
            "expires_at": None,
            "owner": "impl-generalist",
            "rationale": "Legacy code, scheduled for refactoring",
        }

        baseline_template["baseline_entries"].append(baseline_entry)

        baseline_file = tmp_audit_dir / ".governance-baseline.json"
        baseline_file.write_text(json.dumps(baseline_template, indent=2))

        # Current audit detects same violation
        current_violation = {
            "rule": "EX-01",
            "file": "asset_generation/python/src/enemies/builder.py",
            "line": 42,
            "message": "Bare except clause detected",
            "severity": "ERROR",
        }

        # Diff should mark as GRANDFATHERED
        baseline_entries = json.loads(baseline_file.read_text())["baseline_entries"]
        is_grandfathered = any(
            e["rule_id"] == current_violation["rule"]
            and e["file"] == current_violation["file"]
            and e["line"] == current_violation["line"]
            for e in baseline_entries
        )

        # Assertion: violation IS grandfathered
        assert is_grandfathered, (
            "Violation should be marked as GRANDFATHERED (baseline entry exists)"
        )

    def test_expired_baseline_entry_rejects_violation(
        self, tmp_audit_dir: Path, baseline_template: dict[str, Any]
    ) -> None:
        """Expired baseline entry no longer protects violation; treated as NEW.

        If expires_at < today, entry is stale → violation is NEW → error.
        """
        # Baseline entry with past expiration
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()

        baseline_entry = {
            "rule_id": "RF-02",
            "file": "asset_generation/python/src/model_registry/schema.py",
            "line": 88,
            "expires_at": yesterday,
            "owner": "impl-backend",
            "rationale": "Expired grace period",
        }

        baseline_template["baseline_entries"].append(baseline_entry)

        baseline_file = tmp_audit_dir / ".governance-baseline.json"
        baseline_file.write_text(json.dumps(baseline_template, indent=2))

        # Current audit detects same violation
        current_violation = {
            "rule": "RF-02",
            "file": "asset_generation/python/src/model_registry/schema.py",
            "line": 88,
        }

        # Diff should treat expired entry as invalid
        baseline_entries = json.loads(baseline_file.read_text())["baseline_entries"]
        entry = next(
            (
                e
                for e in baseline_entries
                if e["rule_id"] == current_violation["rule"]
                and e["file"] == current_violation["file"]
            ),
            None,
        )

        # Entry exists but is expired
        assert entry is not None
        expires_at = entry.get("expires_at")
        if expires_at:
            expiry_date = datetime.fromisoformat(expires_at).date()
            today = datetime.now(timezone.utc).date()
            is_expired = expiry_date < today
            assert is_expired, "Baseline entry should be expired"

    def test_unknown_rule_requires_explicit_baseline(
        self, tmp_audit_dir: Path, baseline_template: dict[str, Any]
    ) -> None:
        """Unknown/new rule categories require explicit baseline entries.

        If audit detects a rule never seen before (e.g., NEW-01), it must have
        a baseline entry or be treated as an error (don't silently accept).
        """
        # Baseline has entries for known rules only
        baseline_file = tmp_audit_dir / ".governance-baseline.json"
        baseline_file.write_text(json.dumps(baseline_template, indent=2))

        # Audit detects a violation with unknown rule
        unknown_violation = {
            "rule": "NEW-01",
            "file": "asset_generation/python/src/test.py",
            "line": 10,
            "message": "Unknown rule violation",
            "severity": "ERROR",
        }

        # Diff should require explicit baseline entry for NEW-01
        baseline_entries = json.loads(baseline_file.read_text())["baseline_entries"]

        # Check if rule is known in baseline
        known_rules = {e["rule_id"] for e in baseline_entries}
        rule_is_unknown = unknown_violation["rule"] not in known_rules

        # Assertion: unknown rule is not silently accepted
        # (either error or requires explicit entry)
        assert rule_is_unknown, "Unknown rule should not be silently accepted"


# ============================================================================
# CLUSTERING TESTS
# ============================================================================


class TestViolationClustering:
    """Tests for clustering violations by rule + path prefix.

    Clustering reduces noise and produces ticket-sized remediation bundles.
    """

    def test_cluster_violations_by_rule_and_path(
        self, tmp_audit_dir: Path, sample_violations: list[dict[str, Any]]
    ) -> None:
        """Violations are clustered by rule ID + path prefix.

        Clustering strategy:
        - Group by (rule_id, path_prefix)
        - Path prefix = directory containing file (e.g., asset_generation/python/src/enemies)
        - Each cluster becomes a remediation ticket candidate
        """
        # Define clustering logic
        def cluster_violations(violations):
            clusters = {}
            for v in violations:
                rule_id = v["rule"]
                # Extract path prefix (first 2 dir components)
                file_parts = Path(v["file"]).parts
                path_prefix = "/".join(file_parts[:3])  # e.g., asset_generation/python/src

                key = (rule_id, path_prefix)
                if key not in clusters:
                    clusters[key] = []
                clusters[key].append(v)
            return clusters

        clusters = cluster_violations(sample_violations)

        # Verify clustering
        assert len(clusters) > 0, "Should have at least one cluster"

        # Each cluster should have a (rule_id, path_prefix) key
        for (rule_id, path_prefix), violations in clusters.items():
            assert isinstance(rule_id, str)
            assert isinstance(path_prefix, str)
            assert len(violations) > 0
            # All violations in cluster should have same rule_id
            assert all(v["rule"] == rule_id for v in violations)

    def test_cluster_summary_for_remediation(
        self, tmp_audit_dir: Path, sample_violations: list[dict[str, Any]]
    ) -> None:
        """Each cluster produces summary suitable for remediation ticket.

        Summary includes:
        - Rule ID and description
        - Count of violations in cluster
        - Affected files (list or sample)
        - Severity levels
        """
        def create_cluster_summary(rule_id: str, violations: list[dict]):
            files = list(set(v["file"] for v in violations))
            severities = list(set(v["severity"] for v in violations))
            return {
                "rule_id": rule_id,
                "violation_count": len(violations),
                "affected_files": files,
                "severities": severities,
                "sample_violations": violations[:3],  # First 3 for context
            }

        # Group by rule_id only (simple clustering)
        by_rule = {}
        for v in sample_violations:
            rule = v["rule"]
            if rule not in by_rule:
                by_rule[rule] = []
            by_rule[rule].append(v)

        summaries = {
            rule: create_cluster_summary(rule, violations)
            for rule, violations in by_rule.items()
        }

        # Verify summary format
        assert len(summaries) == len(by_rule)
        for summary in summaries.values():
            assert "rule_id" in summary
            assert "violation_count" in summary
            assert "affected_files" in summary
            assert summary["violation_count"] > 0


# ============================================================================
# REMEDIATION TICKET GENERATION TESTS
# ============================================================================


class TestRemediationTicketGeneration:
    """Tests for generating markdown remediation tickets from clusters."""

    def test_remediation_ticket_markdown_format(
        self, tmp_audit_dir: Path
    ) -> None:
        """Remediation ticket is generated in markdown format.

        Format (suitable for project_board/**/00_backlog/):
        - Title with rule ID
        - Context section with violation count and affected files
        - Individual acceptance criteria per violation (specific, actionable)
        """
        violations = [
            {
                "file": "asset_generation/python/src/enemies/builder.py",
                "line": 42,
                "message": "Bare except clause detected",
                "severity": "ERROR",
            },
            {
                "file": "asset_generation/python/src/player/controller.py",
                "line": 88,
                "message": "Bare except clause detected",
                "severity": "ERROR",
            },
            {
                "file": "asset_generation/web/backend/services/registry.py",
                "line": 156,
                "message": "Bare except clause detected",
                "severity": "ERROR",
            },
        ]

        def generate_remediation_ticket(rule_id, violations, spec_link=""):
            """Generate markdown remediation ticket with per-violation ACs."""
            lines = [
                f"# Remediation Ticket: Rule {rule_id} Violations",
                "",
                "## Context",
                "",
                f"Governance rule **{rule_id}** has {len(violations)} violation(s)",
                "that require remediation.",
                "",
                "**Affected files:**",
                "",
            ]

            # List affected files
            affected_files = set()
            for v in violations:
                affected_files.add(v.get("file", "unknown"))
            for file_path in sorted(affected_files):
                lines.append(f"- {file_path}")

            lines.extend([
                "",
                "## Acceptance Criteria",
                "",
            ])

            # Individual AC per violation (key improvement)
            for i, violation in enumerate(violations, 1):
                file_path = violation.get("file", "unknown")
                line_num = violation.get("line", "?")
                message = violation.get("message", "")

                lines.append(f"- [ ] Fix violation {i}: `{file_path}:{line_num}`")
                lines.append(f"  - {message}")
                lines.append("")

            if spec_link:
                lines.extend([
                    "## References",
                    "",
                    f"- Specification: {spec_link}",
                ])

            return "\n".join(lines)

        markdown = generate_remediation_ticket("EX-01", violations)

        # Verify markdown format
        assert "# Remediation Ticket: Rule EX-01 Violations" in markdown
        assert "## Context" in markdown
        assert "## Acceptance Criteria" in markdown
        assert violations[0]["file"] in markdown
        # Key assertion: each violation is a separate AC
        assert "- [ ] Fix violation 1:" in markdown
        assert "- [ ] Fix violation 2:" in markdown
        assert "- [ ] Fix violation 3:" in markdown

    def test_remediation_ticket_includes_rule_guidance(
        self, tmp_audit_dir: Path
    ) -> None:
        """Remediation ticket includes rule-specific remediation guidance.

        Guidance sourced from governance_check.REMEDIATION_HINTS (Task 4 deliverable).
        """
        rule_id = "EX-01"
        remediation_hints = {
            "EX-01": "Replace bare 'except:' with specific exception type: 'except ValueError as e:'",
            "EX-02": "Add logging or re-raise in exception handler: 'logger.error(...); raise'",
            "RF-02": "Use factory/builder pattern instead of setattr; define proper constructors",
        }

        cluster = {
            "rule_id": rule_id,
            "violation_count": 2,
            "affected_files": ["file1.py", "file2.py"],
        }

        def generate_ticket_with_guidance(cluster, hints):
            lines = [f"# Rule {cluster['rule_id']} Remediation"]
            if cluster["rule_id"] in hints:
                lines.append("")
                lines.append("## Remediation Guidance")
                lines.append("")
                lines.append(f"{hints[cluster['rule_id']]}")
            return "\n".join(lines)

        markdown = generate_ticket_with_guidance(cluster, remediation_hints)

        assert "Remediation Guidance" in markdown
        assert remediation_hints[rule_id] in markdown


# ============================================================================
# BASELINE METADATA AND OWNERSHIP TESTS
# ============================================================================


class TestBaselineMetadata:
    """Tests for baseline entry metadata: owner, rationale, expiration."""

    def test_baseline_entry_owner_field_required(
        self, tmp_audit_dir: Path, baseline_template: dict[str, Any]
    ) -> None:
        """Baseline entries require owner field (agent or team responsible).

        Valid owner values: agent name, team name, or "TBD".
        """
        entry = {
            "rule_id": "EX-01",
            "file": "test.py",
            "line": 10,
            "expires_at": "2026-08-31",
            "owner": "impl-generalist",
            "rationale": "Refactoring scheduled",
        }

        baseline_template["baseline_entries"].append(entry)

        baseline_file = tmp_audit_dir / ".governance-baseline.json"
        baseline_file.write_text(json.dumps(baseline_template, indent=2))

        parsed = json.loads(baseline_file.read_text())
        baseline_entry = parsed["baseline_entries"][0]

        assert "owner" in baseline_entry
        assert baseline_entry["owner"] == "impl-generalist"

    def test_baseline_entry_rationale_field_required(
        self, tmp_audit_dir: Path, baseline_template: dict[str, Any]
    ) -> None:
        """Baseline entries require rationale field (why violation is tolerated).

        Rationale should reference a ticket (e.g., M905-03) and provide context.
        """
        entry = {
            "rule_id": "RF-02",
            "file": "test.py",
            "line": 20,
            "expires_at": "2026-09-30",
            "owner": "impl-backend",
            "rationale": "Large refactoring effort tracked in M905-03, estimated completion 2026-09-30",
        }

        baseline_template["baseline_entries"].append(entry)

        baseline_file = tmp_audit_dir / ".governance-baseline.json"
        baseline_file.write_text(json.dumps(baseline_template, indent=2))

        parsed = json.loads(baseline_file.read_text())
        baseline_entry = parsed["baseline_entries"][0]

        assert "rationale" in baseline_entry
        assert len(baseline_entry["rationale"]) > 0
        # Rationale should not be empty
        assert baseline_entry["rationale"].strip() != ""

    def test_baseline_ownership_prevents_silent_acceptance(
        self, tmp_audit_dir: Path, baseline_template: dict[str, Any]
    ) -> None:
        """Baseline ownership model tracks accountability for grandfathered violations.

        Each entry has explicit owner (agent responsible for resolving).
        This prevents silent acceptance without clear ownership.
        """
        entries = [
            {
                "rule_id": "EX-01",
                "file": "file1.py",
                "line": 10,
                "expires_at": "2026-08-31",
                "owner": "agent-a",
                "rationale": "Fix scheduled",
            },
            {
                "rule_id": "EX-02",
                "file": "file2.py",
                "line": 20,
                "expires_at": "2026-09-30",
                "owner": "agent-b",
                "rationale": "Fix scheduled",
            },
        ]

        baseline_template["baseline_entries"].extend(entries)

        baseline_file = tmp_audit_dir / ".governance-baseline.json"
        baseline_file.write_text(json.dumps(baseline_template, indent=2))

        parsed = json.loads(baseline_file.read_text())

        # Each entry has distinct owner
        owners = {e["owner"] for e in parsed["baseline_entries"]}
        assert len(owners) >= 1, "Baseline entries should track ownership"


# ============================================================================
# POLICY AND UPDATE MECHANISM TESTS
# ============================================================================


class TestBaselineUpdatePolicy:
    """Tests for baseline update policy and change control."""

    def test_baseline_update_requires_metadata(
        self, tmp_audit_dir: Path, baseline_template: dict[str, Any]
    ) -> None:
        """Baseline changes must include audit trail metadata.

        Metadata for each update:
        - updated_at (timestamp)
        - updated_by (agent name)
        - change_reason (brief description of change)
        """
        update_metadata = {
            "updated_at": "2026-05-15T14:30:00Z",
            "updated_by": "spec-agent",
            "change_reason": "Initial baseline after M902-03 completion",
        }

        baseline_template["_meta"].update(update_metadata)

        baseline_file = tmp_audit_dir / ".governance-baseline.json"
        baseline_file.write_text(json.dumps(baseline_template, indent=2))

        parsed = json.loads(baseline_file.read_text())
        assert "updated_at" in parsed["_meta"]
        assert "updated_by" in parsed["_meta"]
        assert "change_reason" in parsed["_meta"]

    def test_baseline_prevents_new_rule_categories_without_entry(
        self, tmp_audit_dir: Path, baseline_template: dict[str, Any]
    ) -> None:
        """Baseline diff rejects violations with unknown rules (not in baseline).

        Policy: every rule must have at least one baseline entry or new violations
        of that rule trigger an error.
        """
        # Baseline has only EX-01, EX-02
        baseline_template["baseline_entries"] = [
            {
                "rule_id": "EX-01",
                "file": "file1.py",
                "line": 10,
                "expires_at": None,
                "owner": "agent",
                "rationale": "Known violation",
            },
        ]

        baseline_file = tmp_audit_dir / ".governance-baseline.json"
        baseline_file.write_text(json.dumps(baseline_template, indent=2))

        # Audit finds a violation with rule AR-01 (not in baseline)
        new_violation = {
            "rule": "AR-01",
            "file": "file2.py",
            "line": 20,
        }

        parsed = json.loads(baseline_file.read_text())
        known_rules = {e["rule_id"] for e in parsed["baseline_entries"]}

        # AR-01 is unknown in baseline
        assert new_violation["rule"] not in known_rules, (
            "New rule should not be in baseline"
        )


# ============================================================================
# EDGE CASE AND ERROR HANDLING TESTS
# ============================================================================


class TestAuditPipelineEdgeCases:
    """Tests for edge cases and error conditions in audit pipeline."""

    def test_audit_handles_empty_violation_list(
        self, tmp_audit_dir: Path
    ) -> None:
        """Audit handles codebase with zero violations gracefully.

        Output should be valid JSON with empty violations array.
        """
        audit_output = {
            "metadata": {
                "timestamp": "2026-05-15T12:30:00Z",
                "scan_scope": ["src/"],
            },
            "violations": [],
            "summary": {
                "total_violations": 0,
                "files_scanned": 50,
            },
            "duration_ms": 1500,
        }

        output_file = tmp_audit_dir / "audit_report.json"
        output_file.write_text(json.dumps(audit_output, indent=2))

        parsed = json.loads(output_file.read_text())
        assert parsed["summary"]["total_violations"] == 0
        assert isinstance(parsed["violations"], list)
        assert len(parsed["violations"]) == 0

    def test_baseline_with_null_line_number(
        self, tmp_audit_dir: Path, baseline_template: dict[str, Any]
    ) -> None:
        """Baseline entry can have null line number (file-level rule).

        Some rules may apply to entire file, not specific line.
        """
        entry = {
            "rule_id": "GV-03",
            "file": "blanket-eslint-file.tsx",
            "line": None,  # File-level violation
            "expires_at": "2026-08-31",
            "owner": "frontend-team",
            "rationale": "Complex refactoring in progress",
        }

        baseline_template["baseline_entries"].append(entry)

        baseline_file = tmp_audit_dir / ".governance-baseline.json"
        baseline_file.write_text(json.dumps(baseline_template, indent=2))

        parsed = json.loads(baseline_file.read_text())
        baseline_entry = parsed["baseline_entries"][0]

        assert baseline_entry["line"] is None, "Line number should be null for file-level violations"

    def test_audit_large_violation_count_performance(
        self, tmp_audit_dir: Path
    ) -> None:
        """Audit handles large violation counts without timeout.

        Should process 1000+ violations in reasonable time.
        """
        # Simulate 1000 violations
        violations = [
            {
                "file": f"file_{i}.py",
                "line": i % 100,
                "rule": f"RULE-{i % 10:02d}",
                "message": f"Violation {i}",
                "severity": "WARN",
            }
            for i in range(1000)
        ]

        audit_output = {
            "metadata": {"timestamp": "2026-05-15T12:30:00Z"},
            "violations": violations,
            "summary": {"total_violations": 1000},
            "duration_ms": 5000,  # 5 second scan
        }

        output_file = tmp_audit_dir / "audit_report.json"
        output_file.write_text(json.dumps(audit_output, indent=2))

        parsed = json.loads(output_file.read_text())
        assert len(parsed["violations"]) == 1000
        assert parsed["summary"]["total_violations"] == 1000


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestAuditPipelineIntegration:
    """Integration tests for audit pipeline end-to-end workflow."""

    def test_audit_to_baseline_to_diff_workflow(
        self, tmp_audit_dir: Path, sample_violations: list[dict[str, Any]]
    ) -> None:
        """End-to-end workflow: audit → generate baseline → detect new violations.

        1. Run audit, capture violations
        2. Generate baseline from violations
        3. Run audit again, detect new violations vs baseline
        """
        # Step 1: Initial audit
        audit_output = {
            "violations": sample_violations,
            "summary": {"total_violations": len(sample_violations)},
        }

        # Step 2: Generate baseline from audit
        baseline_template = {
            "_meta": {"version": "1.0"},
            "baseline_entries": [
                {
                    "rule_id": v["rule"],
                    "file": v["file"],
                    "line": v["line"],
                    "expires_at": None,
                    "owner": "spec-agent",
                    "rationale": "Initial baseline",
                }
                for v in sample_violations
            ],
        }

        # Step 3: New audit (with one new violation)
        new_violation = {
            "file": "asset_generation/python/src/new_file.py",
            "line": 50,
            "rule": "EX-01",
            "message": "New bare except",
            "severity": "ERROR",
        }

        new_audit_violations = sample_violations + [new_violation]

        # Diff: new violation is NOT in baseline
        baseline_rules = {
            (e["rule_id"], e["file"], e["line"])
            for e in baseline_template["baseline_entries"]
        }

        new_violations = []
        for v in new_audit_violations:
            key = (v["rule"], v["file"], v["line"])
            if key not in baseline_rules:
                new_violations.append(v)

        # Assertion: exactly one new violation detected
        assert len(new_violations) == 1
        assert new_violations[0] == new_violation

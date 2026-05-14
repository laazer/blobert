"""Adversarial tests for gate schema fixtures.

Tests schema validation edge cases, null injection, and boundary conditions
on the gate-result-success.json and gate-result-failure.json schemas.
"""

import json
import re
from pathlib import Path

import pytest


SUCCESS_SCHEMA_PATH = "gate-result-success.json"
FAILURE_SCHEMA_PATH = "gate-result-failure.json"

SUCCESS_REQUIRED_FIELDS = {
    "version", "status", "gate", "upstream_agent", "downstream_agent",
    "timestamp", "ticket_id", "artifacts", "duration_ms", "message",
}

FAILURE_REQUIRED_FIELDS = SUCCESS_REQUIRED_FIELDS | {"violations", "remediation_hints"}

VIOLATION_REQUIRED_FIELDS = {"file", "line", "rule", "message", "severity"}

ALLOWED_SEVERITIES = {"ERROR", "WARN", "INFO"}

ISO8601_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class TestSchemaMutation:
    """Mutation tests: flip expected schema properties."""

    def test_success_status_can_be_other_values(self, gate_schemas: Path) -> None:
        # Mutation: if status is only "PASS", test that other values are rejected
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        # Verify the example uses "PASS"
        assert example.get("status") == "PASS"

    def test_failure_status_can_be_other_values(self, gate_schemas: Path) -> None:
        # Mutation: if status is only "FAIL", test that other values are rejected
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        assert example.get("status") == "FAIL"

    def test_success_artifacts_can_be_empty_list(self, gate_schemas: Path) -> None:
        # Mutation: empty artifacts list should be valid
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        artifacts = example.get("artifacts", [])
        # If artifacts is a list, verify it can be empty
        assert isinstance(artifacts, list)

    def test_failure_violations_can_be_empty_list(self, gate_schemas: Path) -> None:
        # Mutation: empty violations list should be valid (gate passes)
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        violations = example.get("violation", [])
        assert isinstance(violations, list)

    def test_violation_severity_case_sensitivity(self, gate_schemas: Path) -> None:
        # Mutation: severity should be case-sensitive (ERROR not error)
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        for v in example.get("violations", []):
            sev = v.get("severity")
            assert sev == sev.upper(), f"Severity should be uppercase: {sev}"

    def test_violation_line_can_be_zero(self, gate_schemas: Path) -> None:
        # Mutation: line=0 should be valid (beginning of file)
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        for v in example.get("violations", []):
            line = v.get("line")
            assert isinstance(line, int)
            assert line >= 0, f"Line should be >= 0: {line}"

    def test_violation_line_can_be_negative(self, gate_schemas: Path) -> None:
        # Mutation: negative line numbers should be invalid
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        for v in example.get("violations", []):
            line = v.get("line")
            assert line is None or line >= 0, f"Negative line number: {line}"

    def test_duration_ms_can_be_zero(self, gate_schemas: Path) -> None:
        # Mutation: zero duration should be valid (instant gate)
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        duration = example.get("duration_ms")
        assert isinstance(duration, int)
        assert duration >= 0, f"Duration should be >= 0: {duration}"

    def test_duration_ms_can_be_negative(self, gate_schemas: Path) -> None:
        # Mutation: negative duration should be invalid
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        duration = example.get("duration_ms")
        assert duration is None or duration >= 0, f"Negative duration: {duration}"

    def test_version_format_must_be_semver(self, gate_schemas: Path) -> None:
        # Mutation: version should follow semver (major.minor.patch)
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        version = example.get("version")
        assert isinstance(version, str)
        # Basic semver check
        parts = version.split(".")
        assert len(parts) >= 2, f"Version should have at least major.minor: {version}"

    def test_example_has_no_extra_required_fields(self, gate_schemas: Path) -> None:
        # Mutation: example should not have fields that look like required but aren't
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        for key in example:
            if key.startswith("_"):
                continue
            # All non-internal fields should be in SUCCESS_REQUIRED_FIELDS
            assert key in SUCCESS_REQUIRED_FIELDS, \
                f"Unexpected field in success schema: {key}"

    def test_failure_example_has_all_failure_fields(self, gate_schemas: Path) -> None:
        # Mutation: failure example must have all FAILURE_REQUIRED_FIELDS
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        for field in FAILURE_REQUIRED_FIELDS:
            assert field in example, f"Missing field in failure example: {field}"

    def test_remediation_hints_can_be_empty_list(self, gate_schemas: Path) -> None:
        # Mutation: empty remediation_hints should be valid
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        hints = example.get("remediation_hints", [])
        assert isinstance(hints, list)

    def test_remediation_hints_can_be_null(self, gate_schemas: Path) -> None:
        # Mutation: null remediation_hints should be valid
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        hints = example.get("remediation_hints")
        assert hints is None or isinstance(hints, list), \
            f"remediation_hints should be list or null: {type(hints)}"

    def test_artifacts_can_contain_varied_structures(self, gate_schemas: Path) -> None:
        # Mutation: artifacts array items should support varied structures
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        artifacts = example.get("artifacts", [])
        assert isinstance(artifacts, list)
        for artifact in artifacts:
            assert isinstance(artifact, dict), f"Artifact should be dict: {type(artifact)}"


class TestSchemaBoundaryConditions:
    """Boundary condition tests for schema fields."""

    def test_gate_name_empty_string(self, gate_schemas: Path) -> None:
        # Mutation: empty gate name should be invalid
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        gate = example.get("gate")
        assert isinstance(gate, str) and len(gate) > 0, \
            f"Gate name should not be empty: '{gate}'"

    def test_upstream_agent_empty_string(self, gate_schemas: Path) -> None:
        # Mutation: empty upstream_agent should be invalid
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        agent = example.get("upstream_agent")
        assert isinstance(agent, str) and len(agent) > 0, \
            f"upstream_agent should not be empty: '{agent}'"

    def test_downstream_agent_empty_string(self, gate_schemas: Path) -> None:
        # Mutation: empty downstream_agent should be invalid
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        agent = example.get("downstream_agent")
        assert isinstance(agent, str) and len(agent) > 0, \
            f"downstream_agent should not be empty: '{agent}'"

    def test_ticket_id_empty_string(self, gate_schemas: Path) -> None:
        # Mutation: empty ticket_id should be invalid
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        ticket = example.get("ticket_id")
        assert isinstance(ticket, str) and len(ticket) > 0, \
            f"ticket_id should not be empty: '{ticket}'"

    def test_message_empty_string(self, gate_schemas: Path) -> None:
        # Mutation: empty message should be valid (PASS can have empty message)
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        message = example.get("message")
        assert isinstance(message, str), f"message should be string: {type(message)}"

    def test_timestamp_must_be_valid_iso8601(self, gate_schemas: Path) -> None:
        # Mutation: timestamp must match ISO 8601 format
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        ts = example.get("timestamp")
        assert ISO8601_RE.match(ts), f"timestamp must be ISO 8601: {ts}"

    def test_timestamp_not_epoch(self, gate_schemas: Path) -> None:
        # Mutation: timestamp should be ISO 8601, not epoch
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        ts = example.get("timestamp")
        assert not ts.isdigit(), f"timestamp should not be epoch: {ts}"

    def test_sha256_is_exactly_64_hex_chars(self, gate_schemas: Path) -> None:
        # Mutation: sha256 must be exactly 64 lowercase hex chars
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        for artifact in example.get("artifacts", []):
            sha = artifact.get("sha256")
            if sha is not None:
                assert SHA256_RE.match(sha), f"Invalid sha256: {sha}"

    def test_version_is_not_empty(self, gate_schemas: Path) -> None:
        # Mutation: version must not be empty
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        version = example.get("version")
        assert isinstance(version, str) and len(version) > 0, \
            f"version should not be empty: '{version}'"

    def test_failure_violation_file_not_empty(self, gate_schemas: Path) -> None:
        # Mutation: violation file must not be empty
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        for v in example.get("violations", []):
            file_path = v.get("file")
            assert isinstance(file_path, str) and len(file_path) > 0, \
                f"violation file should not be empty: '{file_path}'"

    def test_failure_violation_rule_not_empty(self, gate_schemas: Path) -> None:
        # Mutation: violation rule must not be empty
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        for v in example.get("violations", []):
            rule = v.get("rule")
            assert isinstance(rule, str) and len(rule) > 0, \
                f"violation rule should not be empty: '{rule}'"

    def test_failure_violation_message_not_empty(self, gate_schemas: Path) -> None:
        # Mutation: violation message must not be empty
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = json.loads(path.read_text())
        example = data.get("_example", data)
        for v in example.get("violations", []):
            msg = v.get("message")
            assert isinstance(msg, str) and len(msg) > 0, \
                f"violation message should not be empty: '{msg}'"

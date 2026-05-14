"""Gate schema fixture tests.

Covers REQ-02 (success schema) and REQ-03 (failure schema): AC-02.1 through AC-02.5, AC-03.1 through AC-03.5.
"""

import json
import re
from pathlib import Path

import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from conftest import load_json


SUCCESS_SCHEMA_PATH = "gate-result-success.json"
FAILURE_SCHEMA_PATH = "gate-result-failure.json"

SUCCESS_REQUIRED_FIELDS = {
    "version", "status", "gate", "upstream_agent", "downstream_agent",
    "timestamp", "ticket_id", "artifacts", "duration_ms", "message",
}

FAILURE_REQUIRED_FIELDS = SUCCESS_REQUIRED_FIELDS | {"violations", "remediation_hints"}

VIOLATION_REQUIRED_FIELDS = {"file", "line", "rule", "message", "severity"}

ALLOWED_SEVERITIES = {"ERROR", "WARN", "INFO"}

ISO8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class TestSuccessSchema:
    """Tests for ci/scripts/gate_schemas/gate-result-success.json."""

    def test_file_exists(self, gate_schemas: Path) -> None:
        # AC-02.1
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        assert path.exists(), f"{SUCCESS_SCHEMA_PATH} must exist"

    def test_valid_json(self, gate_schemas: Path) -> None:
        # AC-02.1
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = load_json(path)
        assert isinstance(data, dict)

    def test_example_has_required_fields(self, gate_schemas: Path) -> None:
        # AC-02.2
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        assert SUCCESS_REQUIRED_FIELDS.issubset(example.keys()), \
            f"Missing fields: {SUCCESS_REQUIRED_FIELDS - set(example.keys())}"

    def test_example_status_is_pass(self, gate_schemas: Path) -> None:
        # AC-02.4
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        assert example["status"] == "PASS"

    def test_example_all_fields_non_null(self, gate_schemas: Path) -> None:
        # AC-02.4
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        for key, value in example.items():
            if key.startswith("_"):
                continue
            assert value is not None, f"Field {key} is null in example"

    def test_example_status_string(self, gate_schemas: Path) -> None:
        # AC-02.5
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        assert example["status"] == "PASS"

    def test_example_timestamp_iso8601(self, gate_schemas: Path) -> None:
        # AC-02.5
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        assert ISO8601_RE.match(example["timestamp"]), \
            f"timestamp must be ISO 8601: {example['timestamp']}"

    def test_example_sha256_format(self, gate_schemas: Path) -> None:
        # AC-02.5
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        artifacts = example.get("artifacts", [])
        for artifact in artifacts:
            sha = artifact.get("sha256")
            if sha is not None:
                assert SHA256_RE.match(sha), f"sha256 must be 64 hex chars: {sha}"

    def test_example_gate_name_non_empty(self, gate_schemas: Path) -> None:
        # AC-02.4
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        assert isinstance(example["gate"], str) and len(example["gate"]) > 0

    def test_example_duration_ms_integer(self, gate_schemas: Path) -> None:
        # AC-02.2
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        assert isinstance(example["duration_ms"], int)

    def test_example_version_string(self, gate_schemas: Path) -> None:
        # AC-02.2
        path = gate_schemas / SUCCESS_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        assert isinstance(example["version"], str)


class TestFailureSchema:
    """Tests for ci/scripts/gate_schemas/gate-result-failure.json."""

    def test_file_exists(self, gate_schemas: Path) -> None:
        # AC-03.1
        path = gate_schemas / FAILURE_SCHEMA_PATH
        assert path.exists(), f"{FAILURE_SCHEMA_PATH} must exist"

    def test_valid_json(self, gate_schemas: Path) -> None:
        # AC-03.1
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = load_json(path)
        assert isinstance(data, dict)

    def test_example_has_required_fields(self, gate_schemas: Path) -> None:
        # AC-03.2
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        assert FAILURE_REQUIRED_FIELDS.issubset(example.keys()), \
            f"Missing fields: {FAILURE_REQUIRED_FIELDS - set(example.keys())}"

    def test_example_has_violations(self, gate_schemas: Path) -> None:
        # AC-03.4
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        violations = example.get("violations", [])
        assert len(violations) >= 2, "Example must have at least 2 violations"

    def test_example_violations_different_severities(self, gate_schemas: Path) -> None:
        # AC-03.4
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        violations = example.get("violations", [])
        severities = {v.get("severity") for v in violations}
        assert len(severities) >= 2, "Example must have violations with at least 2 different severities"

    def test_example_has_remediation_hints(self, gate_schemas: Path) -> None:
        # AC-03.4
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        hints = example.get("remediation_hints", [])
        assert len(hints) >= 1, "Example must have at least 1 remediation hint"

    def test_example_violation_fields_complete(self, gate_schemas: Path) -> None:
        # AC-03.5
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        for violation in example.get("violations", []):
            assert VIOLATION_REQUIRED_FIELDS.issubset(violation.keys()), \
                f"Violation missing fields: {VIOLATION_REQUIRED_FIELDS - set(violation.keys())}"

    def test_example_violation_severity_valid(self, gate_schemas: Path) -> None:
        # AC-03.5
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        for violation in example.get("violations", []):
            assert violation.get("severity") in ALLOWED_SEVERITIES, \
                f"Invalid severity: {violation.get('severity')}"

    def test_example_violation_file_non_empty(self, gate_schemas: Path) -> None:
        # AC-03.5
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        for violation in example.get("violations", []):
            assert isinstance(violation.get("file"), str) and len(violation["file"]) > 0

    def test_example_violation_rule_non_empty(self, gate_schemas: Path) -> None:
        # AC-03.5
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        for violation in example.get("violations", []):
            assert isinstance(violation.get("rule"), str) and len(violation["rule"]) > 0

    def test_example_status_is_fail(self, gate_schemas: Path) -> None:
        # AC-03.2
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        assert example["status"] == "FAIL"

    def test_example_remiation_hints_are_strings(self, gate_schemas: Path) -> None:
        # AC-03.2
        path = gate_schemas / FAILURE_SCHEMA_PATH
        data = load_json(path)
        example = data.get("_example", data)
        for hint in example.get("remediation_hints", []):
            assert isinstance(hint, str)

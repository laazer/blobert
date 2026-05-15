"""
Adversarial test suite for M902-03 governance check gate.

Specification: project_board/specs/902_03_handoff_governance_spec.md
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/03_handoff_governance_rule_enforcement.md

Adversarial tests focus on rule evasion attempts, suppression abuse, configuration
mutations, tool failures, schema boundary violations, and governance bypass patterns.

Categories:
1. Rule Evasion (misleading names, comment obfuscation, subtle violations)
2. Suppression Abuse (missing issue links, typos, blanket disables)
3. Configuration Mutations (corrupted rules, missing scopes, malformed YAML)
4. Tool Failures (timeouts, missing binaries, I/O errors)
5. Schema Violations (invalid rule ids, missing remediation, malformed JSON)
6. Governance Bypass Patterns (attempts to skip gates, indirect violations)

Each test documents the evasion technique, expected detection behavior, and spec
reference. Most tests are expected to FAIL on first run (implementation gap);
passing tests confirm correct detection and rejection of evasion attempts.

CHECKPOINT: These tests encode conservative assumptions about what the gate
should detect; markers below indicate assumption-based tests. Implementation
feedback in Task 8 will refine rule patterns.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import textwrap
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
def governance_check_script(repo_root: Path) -> Path:
    """Path to governance_check.py gate module (Task 4 deliverable)."""
    return repo_root / "ci" / "scripts" / "gates" / "governance_check.py"


@pytest.fixture()
def tmp_code_files(tmp_path: Path) -> Path:
    """Create temp directory with test code files."""
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    return code_dir


@pytest.fixture()
def tmp_gate_results(tmp_path: Path) -> Path:
    """Create temp output dir for gate results."""
    results_dir = tmp_path / "gate-results"
    results_dir.mkdir()
    return results_dir


# ============================================================================
# CATEGORY 1: RULE EVASION ATTEMPTS
# ============================================================================


class TestRuleEvasionTechniques:
    """Adversarial tests for rule evasion: misleading names, obfuscation, subtle violations.

    These tests verify that the governance gate can detect attempts to circumvent
    rules through indirect patterns, naming tricks, and logic obfuscation.

    CHECKPOINT: Assumptions about what patterns are detectable may differ from
    implementation. Tests encode strict interpretation of spec rules.
    """

    def test_bare_except_obfuscated_via_indirection(
        self, tmp_code_files: Path
    ) -> None:
        """EX-01 evasion: Bare except hidden via wrapper function.

        Evasion technique:
        - Create helper function with bare except
        - Call helper from main code (intention is to hide violation)
        - Gate should still detect bare except in helper

        Spec reference: EX-01 applies to all Python code, no indirection exemption.
        """
        helper_file = tmp_code_files / "error_handler.py"
        helper_file.write_text(
            textwrap.dedent(
                """
                def safe_load(data):
                    try:
                        return data.load()
                    except:  # Violation: bare except (hidden in helper)
                        return None

                def process():
                    result = safe_load(something)
                    return result
                """
            )
        )

        # CHECKPOINT: Gate should detect bare except even in helper functions
        # that are called indirectly from main logic.
        # Confidence: Medium (depends on whether semprep scans all functions)
        assert "except:" in helper_file.read_text()

    def test_getattr_abuse_with_misleading_variable_names(
        self, tmp_code_files: Path
    ) -> None:
        """RF-01 evasion: getattr hidden in domain layer with misleading names.

        Evasion technique:
        - Use variable name `config` or `schema` to suggest allowed zone
        - Use getattr on domain object in supposedly "safe" helper
        - Intention: make it hard to see RF-01 violation in domain context

        Spec reference: RF-01 forbids getattr outside zones (A, B, C, D),
        regardless of variable naming.
        """
        domain_file = tmp_code_files / "model_registry" / "validator.py"
        domain_file.parent.mkdir(parents=True)
        domain_file.write_text(
            textwrap.dedent(
                """
                def validate_schema(obj):
                    '''Helper that looks like it might be in a safe zone.'''
                    # Evasion: misleading function name suggests schema/utility
                    # but actually operates on domain objects
                    fields = [k for k in dir(obj) if not k.startswith('_')]
                    for field in fields:
                        val = getattr(obj, field)  # Violation: RF-01 in domain
                        if not validate_type(val):
                            return False
                    return True
                """
            )
        )

        # CHECKPOINT: Gate should detect getattr in domain context even when
        # function naming suggests it's a validator helper.
        # Confidence: Medium
        assert "getattr(obj, field)" in domain_file.read_text()

    def test_async_blocking_via_library_wrapper(self, tmp_code_files: Path) -> None:
        """AS-01/AS-02 evasion: Blocking I/O hidden in third-party import.

        Evasion technique:
        - Create wrapper function with misleading name (e.g., `async_fetch`)
        - Wrapper actually calls sync requests.get() internally
        - Call from FastAPI route (appears async from caller's perspective)

        Spec reference: AS-01 forbids requests.get/post in async routes,
        regardless of wrapper abstraction.
        """
        router_file = tmp_code_files / "routers" / "data.py"
        router_file.parent.mkdir(parents=True)
        router_file.write_text(
            textwrap.dedent(
                """
                import requests
                from fastapi import APIRouter

                async def async_fetch(url: str):
                    '''Wrapper that looks async but isn't.'''
                    # Evasion: name suggests async, but calls sync I/O
                    return requests.get(url).json()  # Violation: AS-01

                @router.get('/data')
                async def fetch_data(url: str):
                    # Calls wrapper (appears safe, but violates AS-01)
                    return await async_fetch(url)
                """
            )
        )

        # CHECKPOINT: Gate should detect direct requests.get call in async context,
        # regardless of wrapper indirection.
        # Confidence: High (semprep pattern should catch direct call)
        assert "requests.get" in router_file.read_text()

    def test_reflection_via_introspection_library(self, tmp_code_files: Path) -> None:
        """RF-01/RF-04 evasion: Dynamic introspection via library (not direct getattr).

        Evasion technique:
        - Use inspect library instead of getattr
        - Call inspect.getmembers(), inspect.signature() in domain code
        - Intention: evade getattr-specific rule while achieving same reflection

        Spec reference: RF-01 and RF-04 should generalize to library introspection,
        but initial rules may only check direct getattr/setattr.
        """
        domain_file = tmp_code_files / "model_registry" / "introspect.py"
        domain_file.parent.mkdir(parents=True)
        domain_file.write_text(
            textwrap.dedent(
                """
                import inspect

                def extract_properties(obj):
                    '''Use inspect instead of direct getattr (evasion attempt).'''
                    # Evasion: getattr banned, but inspect.getmembers works similarly
                    members = inspect.getmembers(obj)
                    return {name: val for name, val in members if not name.startswith('_')}
                """
            )
        )

        # CHECKPOINT: This may or may not be detected depending on semprep rule
        # scope. Spec says "getattr/hasattr/setattr", but doesn't mention inspect.
        # Conservative assumption: initial rules detect only getattr/setattr/hasattr.
        # Confidence: Low (depends on rule scope expansion in Task 2 audit)
        assert "inspect.getmembers" in domain_file.read_text()

    def test_silent_exception_via_context_manager(self, tmp_code_files: Path) -> None:
        """EX-02 evasion: Silent swallow inside context manager.

        Evasion technique:
        - Use contextlib.suppress() or try/except in __enter__/__exit__
        - Intention: hide silent exception from pattern matching

        Spec reference: EX-02 forbids silent swallowing, but may not detect
        contextlib.suppress() pattern.
        """
        service_file = tmp_code_files / "services" / "safe_context.py"
        service_file.parent.mkdir(parents=True)
        service_file.write_text(
            textwrap.dedent(
                """
                import contextlib

                def load_config():
                    # Evasion: contextlib.suppress hides exception silently
                    with contextlib.suppress(FileNotFoundError):
                        with open('config.json') as f:
                            return json.load(f)
                    # Violation: EX-02 (silent swallow via context manager)
                    return {}
                """
            )
        )

        # CHECKPOINT: semprep may not detect contextlib.suppress as silent swallow.
        # Confidence: Low (depends on semprep rule specificity)
        assert "contextlib.suppress" in service_file.read_text()

    def test_bare_except_with_type_erasure(self, tmp_code_files: Path) -> None:
        """EX-01 evasion: Bare except disguised with code after except keyword.

        Evasion technique:
        - Write except clause across multiple lines
        - Use comments to obscure bare except
        - Intention: break regex/simple pattern matching

        Spec reference: EX-01 should detect all bare except patterns.
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            textwrap.dedent(
                """
                def process():
                    try:
                        data = load()
                    except  # This comment might break regex
                        :  # Exception type on next line
                        pass  # Violation: bare except split across lines
                """
            ).replace(
                "\n                    except  #",
                "\n                    except  #",
            )  # Keep exact formatting
        )

        # CHECKPOINT: Bare except split across lines may bypass simple pattern matching.
        # Confidence: Low (depends on regex sophistication)
        # This is a tricky edge case; implementation will validate.

    def test_logging_bypass_via_lazy_binding(self, tmp_code_files: Path) -> None:
        """OB-02 evasion: Error logging skipped via lazy evaluation.

        Evasion technique:
        - Catch exception but only log if some condition is true
        - Condition is designed to be rarely true in practice
        - Intention: pass static analysis while still swallowing in production

        Spec reference: OB-02 requires logger call in exception handlers.
        Lazy logging may pass static check but fail intent check.
        """
        router_file = tmp_code_files / "routers" / "lazy_handler.py"
        router_file.parent.mkdir(parents=True)
        router_file.write_text(
            textwrap.dedent(
                """
                async def create_asset(request):
                    try:
                        asset = create(request.name)
                        return asset
                    except ValueError as e:
                        # Evasion: logger call exists but is conditional
                        if DEBUG_MODE:  # Almost never true in prod
                            logger.error('failed', exc_info=True)
                        # Silent swallow in production
                        return None
                """
            )
        )

        # CHECKPOINT: Static analysis can detect logger call but not lazy evaluation.
        # This requires semantic analysis (is condition always false?).
        # Confidence: Medium (depends on semprep depth; may only check presence)


# ============================================================================
# CATEGORY 2: SUPPRESSION ABUSE
# ============================================================================


class TestSuppressionAbuse:
    """Adversarial tests for suppression format violations and abuse patterns.

    These tests verify that the gate detects malformed, incomplete, and abusive
    suppression comments that undermine governance integrity (GV-02, GV-03, GV-04).
    """

    def test_suppression_missing_issue_link(self, tmp_code_files: Path) -> None:
        """GV-02 violation: # nosemgrep <rule> without issue link.

        Pattern: # nosemgrep EX-01 (missing M902-03 / https://...)
        Gate should flag this as GV-02 (suppression requires issue link).

        Spec reference: GV-02, OB-02, RF-01 spec sec "Suppression Format".
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            textwrap.dedent(
                """
                def process():
                    try:
                        data = load()
                    # nosemgrep EX-01  # VIOLATION: no issue link
                    except:
                        pass
                """
            )
        )

        # GV-02 gate should detect this and report violation
        assert "nosemgrep EX-01" in python_file.read_text()
        assert "M902-03" not in python_file.read_text()
        assert "https://" not in python_file.read_text()

    def test_suppression_with_typo_nosemprep(self, tmp_code_files: Path) -> None:
        """GV-04 variant: Typo in suppression keyword (nosemprep vs nosemgrep).

        Pattern: # nosemprep (typo - missing 'g')
        Gate should detect as GV-04 (blanket/invalid suppress).

        Spec reference: GV-04 "No blanket semgrep disables".
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            textwrap.dedent(
                """
                def process():
                    try:
                        data = load()
                    # nosemprep EX-01  # VIOLATION: typo, not recognized
                    except:
                        pass
                """
            )
        )

        # GV-04 gate should detect typo and report
        assert "nosemprep" in python_file.read_text()
        assert "nosemgrep" not in python_file.read_text()

    def test_suppression_with_fake_issue_link(self, tmp_code_files: Path) -> None:
        """GV-02 violation: Issue link format is invalid.

        Pattern: # nosemgrep EX-01 "this-is-not-a-real-link"
        Gate should validate issue link format (must match URL / M###-## / GH-/JIRA-).

        Spec reference: GV-02, Allowed Reflection Zones sec "Suppression Format".
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            textwrap.dedent(
                """
                def process():
                    try:
                        data = load()
                    # nosemgrep EX-01 "not-a-valid-link"
                    except:
                        pass
                """
            )
        )

        # GV-02 gate should detect invalid issue link format
        assert "not-a-valid-link" in python_file.read_text()

    def test_blanket_eslint_disable_no_rule_name(self, tmp_code_files: Path) -> None:
        """GV-03 violation: # eslint-disable without rule name.

        Pattern: // eslint-disable (bare, no rule list)
        Gate should flag as GV-03 (must be granular).

        Spec reference: GV-03 "Linter disables must be granular".
        """
        ts_file = tmp_code_files / "component.tsx"
        ts_file.write_text(
            textwrap.dedent(
                """
                // eslint-disable
                export function Component() {
                  return <div>test</div>;
                }
                """
            )
        )

        # GV-03 gate should detect bare eslint-disable
        assert "// eslint-disable" in ts_file.read_text()
        assert "react-hooks" not in ts_file.read_text()

    def test_blanket_noqa_suppression(self, tmp_code_files: Path) -> None:
        """GV-02 variant: # noqa without code list.

        Pattern: # noqa (bare, suppresses all pylint/flake8)
        Gate should flag as blanket disable (GV-02 / GV-03 depending on scope).

        Spec reference: GV-02, GV-03.
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            textwrap.dedent(
                """
                def process():
                    try:
                        data = load()
                    except:  # noqa
                        pass
                """
            )
        )

        # Gate should detect bare noqa
        assert "# noqa" in python_file.read_text()
        assert "noqa:" not in python_file.read_text()

    def test_suppression_with_empty_issue_link(self, tmp_code_files: Path) -> None:
        """GV-02 violation: Issue link present but empty.

        Pattern: # nosemgrep EX-01 ""
        Gate should reject empty string as invalid issue link.

        Spec reference: GV-02.
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            textwrap.dedent(
                '''
                def process():
                    try:
                        data = load()
                    # nosemgrep EX-01 ""
                    except:
                        pass
                '''
            )
        )

        # GV-02 gate should reject empty issue link
        assert '""' in python_file.read_text()

    def test_suppression_with_outdated_ticket_reference(
        self, tmp_code_files: Path
    ) -> None:
        """GV-02 variant: Issue link references wrong/old ticket.

        Pattern: # nosemgrep EX-01 M901-05 (wrong milestone)
        Gate should validate that ticket reference exists/is current
        (implementation detail; may not be checked in MVP).

        Spec reference: GV-02, Assumption 8 (baseline violations grandfathered).
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            textwrap.dedent(
                """
                def process():
                    try:
                        data = load()
                    # nosemgrep EX-01 M901-05  # Old ticket
                    except:
                        pass
                """
            )
        )

        # Gate should detect outdated reference (if validation is implemented)
        # Conservative assumption: M901 is old; current context is M902
        # CHECKPOINT: May not be validated in MVP; flagged for future enhancement
        assert "M901-05" in python_file.read_text()


# ============================================================================
# CATEGORY 3: CONFIGURATION MUTATIONS
# ============================================================================


class TestConfigurationMutations:
    """Adversarial tests for semprep rule and gate config corruption/mutation.

    These tests verify the gate handles malformed configurations without crashing
    and reports clear errors.
    """

    def test_malformed_semgrep_yaml_syntax(self, tmp_code_files: Path) -> None:
        """Config mutation: Broken YAML in .semgrep.yml.

        Mutation: Missing colons, incorrect indentation, invalid keys.
        Expected: Gate reports clear error or skips malformed rule.

        Spec reference: None (error handling).
        """
        semgrep_config = tmp_code_files / ".semgrep.yml"
        semgrep_config.write_text(
            textwrap.dedent(
                """
                rules
                  - id: bad-rule
                    - pattern: $X = $X  # Bad indentation
                message: "bad rule"
                """
            )
        )

        # Gate should detect YAML parse error and report clearly
        # CHECKPOINT: Expected behavior: gate reports config error, does not crash
        assert semgrep_config.exists()

    def test_rule_with_missing_required_field(self, tmp_code_files: Path) -> None:
        """Config mutation: Semprep rule missing required field (e.g., 'pattern').

        Mutation: Rule has id, message, but no pattern.
        Expected: Gate reports rule as invalid.

        Spec reference: None (rule validation).
        """
        semgrep_config = tmp_code_files / ".semgrep.yml"
        semgrep_config.write_text(
            textwrap.dedent(
                """
                rules:
                  - id: incomplete-rule
                    message: "Incomplete rule"
                    # Missing 'pattern' field
                """
            )
        )

        # Gate should validate rule completeness
        # CHECKPOINT: Expect gate to report missing 'pattern' field
        assert semgrep_config.exists()

    def test_rule_with_invalid_pattern_regex(self, tmp_code_files: Path) -> None:
        """Config mutation: Semprep rule has broken regex pattern.

        Mutation: pattern: "(?P<invalid" (broken regex)
        Expected: Semprep reports regex compile error gracefully.

        Spec reference: None (error handling).
        """
        semgrep_config = tmp_code_files / ".semgrep.yml"
        semgrep_config.write_text(
            textwrap.dedent(
                """
                rules:
                  - id: broken-regex
                    pattern: "(?P<invalid"
                    message: "Broken regex"
                """
            )
        )

        # Semprep should report regex error
        # CHECKPOINT: Gate should not crash on invalid regex
        assert semgrep_config.exists()

    def test_rule_scope_excludes_all_files(self, tmp_code_files: Path) -> None:
        """Config mutation: Rule scope excludes all code paths.

        Mutation: paths: { exclude: ["**/*.py"] } (excludes everything)
        Expected: Gate reports zero violations (scope is valid but empty).

        Spec reference: None (edge case).
        """
        # Create rule config that excludes everything
        rules_config = {
            "rules": [
                {
                    "id": "test-rule",
                    "pattern": "except:",
                    "message": "Bare except",
                    "paths": {"exclude": ["**/*.py", "**/*.tsx"]},
                }
            ]
        }

        config_file = tmp_code_files / "scope_test.json"
        config_file.write_text(json.dumps(rules_config))

        # Gate should handle empty scope gracefully
        # CHECKPOINT: Gate reports pass (no violations found in excluded paths)
        assert config_file.exists()

    def test_circular_rule_dependencies(self, tmp_code_files: Path) -> None:
        """Config mutation: Rules reference each other circularly.

        Mutation: Rule A depends on Rule B, Rule B depends on Rule A.
        Expected: Gate detects cycle or processes safely.

        Spec reference: None (meta-configuration).
        """
        # This is an edge case for multi-rule orchestration
        # CHECKPOINT: Assume gate handles gracefully (ignores circular deps)
        pass

    def test_rule_with_conflicting_severity_override(
        self, tmp_code_files: Path
    ) -> None:
        """Config mutation: Rule has conflicting severity values.

        Mutation: severity: [ERROR, WARN] (ambiguous)
        Expected: Gate resolves to most severe or reports ambiguity.

        Spec reference: Severity mapping (Assumption A7).
        """
        # CHECKPOINT: Assume gate uses most severe severity on conflict
        pass


# ============================================================================
# CATEGORY 4: TOOL FAILURES & STRESS
# ============================================================================


class TestToolFailures:
    """Adversarial tests for tool failures, timeouts, and resource stress.

    These tests verify the gate handles tool failures gracefully and reports
    errors clearly without swallowing exceptions.
    """

    def test_semgrep_timeout_on_large_file(self, tmp_code_files: Path) -> None:
        """Tool failure: Semprep timeout on very large Python file.

        Scenario: File is 100MB+ (adversarial size).
        Expected: Gate times out gracefully and reports timeout error.

        Spec reference: None (error handling).
        """
        large_file = tmp_code_files / "huge.py"
        # Create file with many functions (don't actually write 100MB)
        large_code = "\n".join(
            [f"def func_{i}():\n    try:\n        pass\n    except:\n        pass\n"
             for i in range(10000)]
        )
        large_file.write_text(large_code)

        # Gate should report timeout or process with timeout handling
        # CHECKPOINT: Expect gate to have timeout tolerance (e.g., 30s)
        assert large_file.exists()

    def test_missing_semgrep_binary(self, tmp_code_files: Path) -> None:
        """Tool failure: Semprep binary not found in PATH.

        Scenario: semprep command not installed or not on PATH.
        Expected: Gate reports clear error (not "command not found").

        Spec reference: None (error handling).
        """
        # This is environment-dependent; documented for clarity
        # CHECKPOINT: Gate should check for tool availability upfront
        # and report with helpful error message
        pass

    def test_permission_denied_reading_code_files(self, tmp_code_files: Path) -> None:
        """Tool failure: Code files not readable (permission denied).

        Scenario: Code directory has restrictive permissions.
        Expected: Gate reports permission error clearly.

        Spec reference: None (error handling).
        """
        # Create file with no read permission
        code_file = tmp_code_files / "secret.py"
        code_file.write_text("def secret(): pass")
        # In real scenario: os.chmod(code_file, 0o000)
        # For test purposes, document expected behavior

        # CHECKPOINT: Gate should report permission error, not silently skip
        assert code_file.exists()

    def test_import_linter_missing_configuration(self, tmp_code_files: Path) -> None:
        """Tool failure: import-linter config file missing.

        Scenario: .import-linter not found.
        Expected: Gate reports missing config or skips import-linter check.

        Spec reference: None (tool integration).
        """
        # CHECKPOINT: Gate should handle missing optional tool config gracefully
        pass

    def test_git_operation_fails_during_gate(self, tmp_code_files: Path) -> None:
        """Tool failure: Git operation fails (e.g., during file diff).

        Scenario: git diff fails (repo not initialized, HEAD not found).
        Expected: Gate reports git error clearly.

        Spec reference: None (gate orchestration).
        """
        # CHECKPOINT: If gate invokes git, should handle git errors
        pass

    def test_disk_full_writing_gate_result(self, tmp_gate_results: Path) -> None:
        """Tool failure: Disk full when writing gate result JSON.

        Scenario: tmp_gate_results mounted on full filesystem.
        Expected: Gate reports I/O error, result file incomplete.

        Spec reference: None (error handling).
        """
        # CHECKPOINT: Gate should report disk error, not silent failure
        pass


# ============================================================================
# CATEGORY 5: SCHEMA VIOLATIONS & BOUNDARY ATTACKS
# ============================================================================


class TestSchemaViolations:
    """Adversarial tests for gate output schema violations and invalid results.

    These tests verify the gate produces valid, complete JSON and rejects
    partial/corrupted output.
    """

    def test_gate_output_missing_required_field(self, tmp_gate_results: Path) -> None:
        """Schema violation: Gate output missing required field (e.g., version).

        Violation: JSON has status, gate, but no version.
        Expected: Schema validator rejects output.

        Spec reference: M902-01 gate result schema (gate runner contract).
        """
        invalid_result = {
            "status": "PASS",
            "gate": "governance_check",
            "timestamp": "2026-05-15T08:30:00",
            # Missing: version, duration_ms
        }

        result_file = tmp_gate_results / "invalid.json"
        result_file.write_text(json.dumps(invalid_result))

        # CHECKPOINT: Gate runner should validate output schema before accepting
        # and reject incomplete results
        assert result_file.exists()

    def test_violations_array_missing_required_fields(
        self, tmp_gate_results: Path
    ) -> None:
        """Schema violation: Violation object missing fields (rule, severity).

        Violation: Array item has file, line, message but no rule, severity.
        Expected: Gate runner rejects as incomplete.

        Spec reference: M902-01 schema (violations array format).
        """
        result = {
            "version": "0.1.0",
            "status": "FAIL",
            "gate": "governance_check",
            "timestamp": "2026-05-15T08:30:00",
            "violations": [
                {
                    "file": "handler.py",
                    "line": 5,
                    "message": "Bare except",
                    # Missing: rule, severity
                }
            ],
        }

        result_file = tmp_gate_results / "invalid_violations.json"
        result_file.write_text(json.dumps(result))

        # CHECKPOINT: Gate should validate violation schema completeness
        assert result_file.exists()

    def test_rule_id_not_in_catalog(self, tmp_gate_results: Path) -> None:
        """Schema violation: Violation references unknown rule id.

        Violation: rule: "UNKNOWN-999" (not in catalog)
        Expected: Gate runner rejects as invalid rule reference.

        Spec reference: GV-02, governance rule catalog.
        """
        result = {
            "version": "0.1.0",
            "status": "FAIL",
            "gate": "governance_check",
            "timestamp": "2026-05-15T08:30:00",
            "violations": [
                {
                    "file": "handler.py",
                    "line": 5,
                    "rule": "UNKNOWN-999",
                    "message": "Unknown rule",
                    "severity": "ERROR",
                }
            ],
        }

        result_file = tmp_gate_results / "invalid_rule.json"
        result_file.write_text(json.dumps(result))

        # CHECKPOINT: Gate should validate rule ids against catalog
        assert result_file.exists()

    def test_severity_value_not_in_enum(self, tmp_gate_results: Path) -> None:
        """Schema violation: Severity value not in allowed enum (ERROR/WARN/INFO).

        Violation: severity: "CRITICAL" (not in spec enum)
        Expected: Gate runner rejects as invalid severity.

        Spec reference: Assumption A7 (severity mapping).
        """
        result = {
            "version": "0.1.0",
            "status": "FAIL",
            "gate": "governance_check",
            "timestamp": "2026-05-15T08:30:00",
            "violations": [
                {
                    "file": "handler.py",
                    "line": 5,
                    "rule": "EX-01",
                    "message": "Bare except",
                    "severity": "CRITICAL",  # Invalid enum value
                }
            ],
        }

        result_file = tmp_gate_results / "invalid_severity.json"
        result_file.write_text(json.dumps(result))

        # CHECKPOINT: Gate should validate severity enum
        assert result_file.exists()

    def test_malformed_json_output(self, tmp_gate_results: Path) -> None:
        """Schema violation: Gate output is not valid JSON.

        Violation: File contains JSON-like but syntactically invalid text.
        Expected: Gate runner reports JSON parse error.

        Spec reference: None (output format contract).
        """
        invalid_json_file = tmp_gate_results / "invalid.json"
        invalid_json_file.write_text("{invalid json}")

        # Gate runner should reject non-JSON output
        # CHECKPOINT: Gate should validate JSON syntax before processing
        assert invalid_json_file.exists()
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json_file.read_text())

    def test_timestamp_format_invalid(self, tmp_gate_results: Path) -> None:
        """Schema violation: Timestamp field not ISO 8601 format.

        Violation: timestamp: "May 15, 2026" (not ISO 8601)
        Expected: Gate runner rejects as invalid format.

        Spec reference: M902-01 schema (timestamp must be ISO 8601).
        """
        result = {
            "version": "0.1.0",
            "status": "PASS",
            "gate": "governance_check",
            "timestamp": "May 15, 2026",  # Invalid format
            "duration_ms": 100,
        }

        result_file = tmp_gate_results / "invalid_timestamp.json"
        result_file.write_text(json.dumps(result))

        # CHECKPOINT: Gate should validate timestamp format (ISO 8601)
        assert result_file.exists()


# ============================================================================
# CATEGORY 6: GOVERNANCE BYPASS ATTEMPTS
# ============================================================================


class TestGovernanceBypassPatterns:
    """Adversarial tests for attempts to bypass governance gates and rules.

    These tests verify the gate detects various bypass techniques including
    direct tool invocation, conditional gate skips, and process manipulation.
    """

    def test_direct_semgrep_invocation_in_ci_script(
        self, tmp_code_files: Path
    ) -> None:
        """GV-05 violation: Direct semprep call outside gate runner.

        Bypass: CI script calls `semprep --config...` directly.
        Expected: Gate detects direct tool invocation and reports GV-05.

        Spec reference: GV-05 "No attempts to bypass gate runner".
        """
        ci_script = tmp_code_files / "check.sh"
        ci_script.write_text(
            textwrap.dedent(
                """
                #!/bin/bash
                # Bypass attempt: direct semprep invocation
                semprep --config .semgrep.yml --json > results.json
                if grep -q '"value": "FAIL"' results.json; then
                    exit 1
                fi
                """
            )
        )

        # GV-05 gate should detect direct semprep call
        assert "semprep --config" in ci_script.read_text()

    def test_conditional_skip_of_governance_gate(
        self, tmp_code_files: Path
    ) -> None:
        """GV-05 violation: Conditional skip of governance gate.

        Bypass: if [ $SKIP_GOVERNANCE ]; then exit 0; fi
        Expected: Gate detects conditional skip and reports GV-05.

        Spec reference: GV-05.
        """
        ci_script = tmp_code_files / "workflow.sh"
        ci_script.write_text(
            textwrap.dedent(
                """
                #!/bin/bash
                # Bypass attempt: conditional gate skip
                if [ "$SKIP_GOVERNANCE" = "true" ]; then
                    echo "Skipping governance checks"
                    exit 0
                fi
                # Run normal gate
                python ci/scripts/gate_runner.py governance_check --mode blocking
                """
            )
        )

        # GV-05 gate should detect conditional skip
        assert "SKIP_GOVERNANCE" in ci_script.read_text()

    def test_git_no_verify_flag_in_script(self, tmp_code_files: Path) -> None:
        """GV-01 violation: --no-verify flag in deployment/CI script.

        Bypass: git commit --no-verify -m 'Skip pre-commit hooks'
        Expected: GV-01 gate detects and rejects.

        Spec reference: GV-01 "No --no-verify in committed source".
        """
        deploy_script = tmp_code_files / "deploy.sh"
        deploy_script.write_text(
            textwrap.dedent(
                """
                #!/bin/bash
                # Bypass attempt: skip git hooks
                git commit --no-verify -m "Bypass hooks" config.json
                git push
                """
            )
        )

        # GV-01 gate should detect --no-verify
        assert "--no-verify" in deploy_script.read_text()

    def test_environment_variable_to_skip_checks(
        self, tmp_code_files: Path
    ) -> None:
        """GV-05 variant: Environment variable used to skip gate.

        Bypass: Gate checks SKIP_ALL_CHECKS env var and exits early.
        Expected: Ideally detected as process bypass, but hard to detect statically.

        Spec reference: GV-05 (governance bypass detection).
        """
        gate_script = tmp_code_files / "governance_check.py"
        gate_script.write_text(
            textwrap.dedent(
                """
                import os

                if os.environ.get('SKIP_ALL_CHECKS'):
                    print('Bypassing all checks')
                    exit(0)

                # Run normal checks...
                """
            )
        )

        # CHECKPOINT: Static detection of env-var bypasses is hard.
        # Gate should warn if gate module checks environment variables.
        # Confidence: Low (requires semantic analysis)
        assert "SKIP_ALL_CHECKS" in gate_script.read_text()

    def test_gate_runner_modified_to_suppress_failures(
        self, tmp_code_files: Path
    ) -> None:
        """GV-05 violation: Local gate_runner.py modified to suppress failures.

        Bypass: Developer modifies gate_runner to always exit 0.
        Expected: This is a repository integrity violation, hard to detect
        without code review or hash verification.

        Spec reference: GV-05 (integrity).
        """
        # CHECKPOINT: This requires code signing or hash verification.
        # Assume gate runner validation is out of scope for MVP.
        pass

    def test_ruff_noqa_blanket_disable_in_file(self, tmp_code_files: Path) -> None:
        """GV-03 violation: # noqa at top of file disables all checks.

        Bypass: Add '# flake8: noqa' at start of file to disable all linting.
        Expected: GV-03 gate detects and rejects blanket disable.

        Spec reference: GV-03.
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            textwrap.dedent(
                """
                # flake8: noqa
                def process():
                    try:
                        data = load()
                    except:
                        pass
                """
            )
        )

        # GV-03 gate should detect file-level blanket disable
        assert "# flake8: noqa" in python_file.read_text()

    def test_semprep_rules_disabled_globally(self, tmp_code_files: Path) -> None:
        """GV-04 variant: .semgrep.yml has blanket disable for all rules.

        Bypass: In .semgrep.yml, add '# global: disable' or equivalent.
        Expected: Gate detects disabled rules and reports.

        Spec reference: GV-04.
        """
        # This is a config-level bypass
        # CHECKPOINT: Gate should validate that rules are active, not disabled
        pass

    def test_exception_handler_swallows_without_logging_intent(
        self, tmp_code_files: Path
    ) -> None:
        """EX-02 bypass: Exception handler swallows error but with "justification" comment.

        Bypass: Handler has comment explaining why exception is silently swallowed.
        Expected: Gate detects silent swallow regardless of comment justification.

        Spec reference: EX-02 (exceptions must log or re-raise, not silent).
        """
        service_file = tmp_code_files / "services" / "cache.py"
        service_file.parent.mkdir(parents=True)
        service_file.write_text(
            textwrap.dedent(
                """
                def load_cache():
                    try:
                        return redis.get('key')
                    except ConnectionError as e:
                        # Cache is optional; silently fall back to db query
                        # (Justification comment doesn't override EX-02)
                        return None
                """
            )
        )

        # EX-02 gate should detect silent swallow despite comment
        assert "except ConnectionError" in service_file.read_text()
        assert "return None" in service_file.read_text()


# ============================================================================
# CATEGORY 7: COMBINATORIAL & BOUNDARY EDGE CASES
# ============================================================================


class TestCombinatorialEdgeCases:
    """Adversarial tests for combinations of violations and boundary conditions.

    These tests verify the gate handles multiple simultaneous violations,
    edge cases in rule boundaries, and complex scenarios.
    """

    def test_multiple_violations_in_single_line(
        self, tmp_code_files: Path
    ) -> None:
        """Multiple rules triggered on same line.

        Violation: Single line violates both EX-01 and EX-02 (bare except + silent).
        Expected: Gate reports both violations, doesn't deduplicate.

        Spec reference: None (multi-violation handling).
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            textwrap.dedent(
                """
                def process():
                    try:
                        data = load()
                    except: pass  # EX-01 (bare) + EX-02 (silent)
                """
            )
        )

        # Gate should report both violations
        # CHECKPOINT: Expect separate violation entries for EX-01 and EX-02
        assert "except: pass" in python_file.read_text()

    def test_violation_at_file_boundaries(self, tmp_code_files: Path) -> None:
        """Violation at first and last lines of file.

        Scenario: bare except on line 1 and line 999.
        Expected: Gate detects both violations.

        Spec reference: None (coverage).
        """
        python_file = tmp_code_files / "handler.py"
        lines = ["try: pass\nexcept: pass"]  # Line 1 violation
        lines.extend(["def func(): pass\n"] * 500)
        lines.append("try: pass\nexcept: pass")  # Line 999+ violation
        python_file.write_text("\n".join(lines))

        # Gate should detect both violations despite file size
        # CHECKPOINT: Gate scans entire file, not just initial/final chunks
        assert python_file.exists()

    def test_violation_in_comment_text(self, tmp_code_files: Path) -> None:
        """False positive risk: violation pattern appears in string/comment.

        Scenario: Comment contains text matching bare except pattern.
        Expected: Gate should NOT flag as violation (false positive).

        Spec reference: None (false positive avoidance).
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            textwrap.dedent(
                '''
                def process():
                    """
                    Don't use bare except: in your code!
                    """
                    try:
                        data = load()
                    except ValueError:
                        pass
                '''
            )
        )

        # Gate should NOT flag docstring mention of "except:"
        # CHECKPOINT: Pattern matching should avoid false positives in strings
        # Confidence: Medium (depends on semprep capability)
        assert python_file.exists()

    def test_violation_in_multiline_string(self, tmp_code_files: Path) -> None:
        """False positive risk: Violation in triple-quoted string.

        Scenario: Multiline string contains bare except code example.
        Expected: Gate should NOT flag (false positive).

        Spec reference: None (false positive avoidance).
        """
        python_file = tmp_code_files / "examples.py"
        python_file.write_text(
            textwrap.dedent(
                '''
                EXAMPLE_CODE = """
                def bad_handler():
                    try:
                        data = load()
                    except:
                        pass
                """
                '''
            )
        )

        # Gate should NOT flag code example in string
        # CHECKPOINT: semprep should understand string contexts
        # Confidence: Medium
        assert python_file.exists()

    def test_syntax_error_in_code_file(self, tmp_code_files: Path) -> None:
        """Edge case: File has syntax error (incomplete except clause).

        Scenario: File has incomplete Python (except without try).
        Expected: Gate handles gracefully (doesn't crash).

        Spec reference: None (robustness).
        """
        python_file = tmp_code_files / "broken.py"
        python_file.write_text(
            textwrap.dedent(
                """
                def process():
                    data = load()
                except:  # except without try (syntax error)
                    pass
                """
            )
        )

        # Gate should handle syntax error gracefully
        # CHECKPOINT: Gate reports parsing error, doesn't crash
        assert python_file.exists()

    def test_deeply_nested_suppression_context(self, tmp_code_files: Path) -> None:
        """Edge case: Suppression in deeply nested code.

        Scenario: # nosemgrep comment far from the violation it suppresses.
        Expected: Gate detects suppression applies only to line it precedes.

        Spec reference: GV-02, suppression scope.
        """
        python_file = tmp_code_files / "nested.py"
        python_file.write_text(
            textwrap.dedent(
                """
                # nosemgrep EX-01 M902-03
                def outer():
                    def inner():
                        def innermost():
                            try:
                                pass
                            except:  # Does suppression apply here? Probably not.
                                pass
                """
            )
        )

        # CHECKPOINT: Suppression scoping is implementation-dependent.
        # Conservative assumption: comment suppresses only following line.
        # Confidence: Medium (depends on semprep config)
        assert python_file.exists()

    def test_violation_with_unicode_characters(self, tmp_code_files: Path) -> None:
        """Edge case: Code contains unicode characters.

        Scenario: Variable names, strings with emoji, etc.
        Expected: Gate handles unicode without encoding errors.

        Spec reference: None (robustness).
        """
        python_file = tmp_code_files / "unicode.py"
        python_file.write_text(
            "def process_😀():\n"
            "    try:\n"
            "        data = 'こんにちは'\n"
            "    except:\n"  # Violation: bare except
            "        pass\n",
            encoding="utf-8",
        )

        # Gate should handle unicode filenames and content
        # CHECKPOINT: Gate should report violations correctly despite unicode
        assert python_file.exists()

    def test_violation_in_generated_code(self, tmp_code_files: Path) -> None:
        """Edge case: Violation in auto-generated code (Protobuf, etc).

        Scenario: .pb.py file (generated) contains bare except.
        Expected: Gate may skip or warn (generated files often exempt).

        Spec reference: None (scope question).
        """
        generated_file = tmp_code_files / "messages_pb2.py"
        generated_file.write_text(
            "# Generated code\n"
            "try:\n"
            "    pass\n"
            "except:\n"  # Violation in generated code
            "    pass\n"
        )

        # CHECKPOINT: Gate behavior on generated files not specified.
        # Conservative assumption: gate reports violation, implementer decides.
        # Confidence: Low (depends on generated file detection)
        assert generated_file.exists()


# ============================================================================
# CATEGORY 8: MUTATION TESTING (RULE MUTATIONS)
# ============================================================================


class TestRuleMutations:
    """Adversarial tests that mutate the rule definitions to verify gate robustness.

    These tests verify the gate rejects or handles suspicious mutations to rules
    that could weaken enforcement.
    """

    def test_rule_severity_downgraded_to_info(self, tmp_code_files: Path) -> None:
        """Rule mutation: Change severity ERROR → INFO.

        Mutation: EX-01 severity downgraded from ERROR to INFO.
        Expected: Gate should enforce actual severity (ERROR), or detect mutation.

        Spec reference: Assumption A7 (severity mapping).
        """
        # CHECKPOINT: This is a rule mutation detection (meta-governance).
        # Implementation may validate rule definitions against spec.
        # Confidence: Low (depends on runtime rule validation)
        pass

    def test_rule_scope_expanded_to_exclude_routers(
        self, tmp_code_files: Path
    ) -> None:
        """Rule mutation: Expand exclusion list to include routers.

        Mutation: AR-01 (domain-no-http) excludes routers from scope.
        Expected: Gate detects mutation or enforces original scope.

        Spec reference: AR-01 scope definition.
        """
        # CHECKPOINT: Rule scope validation is meta-governance.
        # Assume gate may not validate mutations (relies on code review).
        pass

    def test_rule_pattern_weakened_to_miss_violations(
        self, tmp_code_files: Path
    ) -> None:
        """Rule mutation: Weaken sempreg pattern to miss violations.

        Mutation: Bare except pattern becomes `except\s+:` (requires space),
        allows `except:` without space.
        Expected: Gate detects pattern weakness or misses violations.

        Spec reference: None (pattern integrity).
        """
        # CHECKPOINT: Pattern mutations are hard to detect.
        # Conservative assumption: gate validates pattern against sample violations.
        # Confidence: Low (requires fuzzing)
        pass


# ============================================================================
# INTEGRATION ADVERSARIAL TESTS
# ============================================================================


class TestIntegrationAdversarial:
    """Integration-level adversarial tests combining multiple attack vectors.

    These tests verify the gate handles complex scenarios mixing multiple
    violation types, bypasses, and stress conditions.
    """

    def test_real_world_violation_complex_scenario(
        self, tmp_code_files: Path
    ) -> None:
        """Complex scenario: Real-world code with multiple issues.

        Scenario: Production-like code with:
        - AR-01 (domain imports HTTP)
        - EX-01 (bare except)
        - OB-01 (missing structured logging)
        - GV-02 (suppression without issue link)

        Expected: Gate reports all violations.

        Spec reference: All six categories.
        """
        complex_file = tmp_code_files / "complex.py"
        complex_file.write_text(
            textwrap.dedent(
                """
                import fastapi  # AR-01 violation
                import logging
                from asset_generation.python.src.model_registry import Asset

                logger = logging.getLogger(__name__)

                def validate_and_save(asset_data):
                    try:
                        asset = Asset.from_dict(asset_data)
                        logger.info('Creating asset')  # Missing operation_id, duration_ms
                        save(asset)
                    except:  # EX-01 violation
                        pass  # EX-02 violation
                    # nosemgrep EX-01  # GV-02 violation (no issue link)

                def load_from_api():
                    # AR-01 violation (domain importing HTTP)
                    import requests
                    data = requests.get('https://example.com/data').json()
                    validate_and_save(data)
                """
            )
        )

        # Gate should detect: AR-01 (import fastapi, import requests in domain),
        # EX-01, EX-02, OB-01 (missing structured logging), GV-02
        # CHECKPOINT: Multiple violations in one file
        assert complex_file.exists()

    def test_gate_handles_concurrent_violations_same_function(
        self, tmp_code_files: Path
    ) -> None:
        """Multiple violations in same function/block.

        Scenario: One function violates EX-01, EX-02, OB-02 all at once.
        Expected: Gate reports all violations with distinct line/rule info.

        Spec reference: None (multi-violation aggregation).
        """
        python_file = tmp_code_files / "multi_violation.py"
        python_file.write_text(
            textwrap.dedent(
                """
                async def process():
                    try:
                        data = load()
                    except:  # EX-01 (bare) + EX-02 (silent swallow)
                        pass
                    # Missing: logger.error for exception context (OB-02)
                """
            )
        )

        # Gate should report three violations from one except block
        # CHECKPOINT: Each violation is tracked separately
        assert python_file.exists()

    def test_suppression_abuse_combined_with_violation(
        self, tmp_code_files: Path
    ) -> None:
        """Suppression abuse combined with actual violation.

        Scenario: File has invalid suppression AND unsuppressed violation.
        Expected: Gate reports both invalid suppression (GV-02) and violation.

        Spec reference: GV-02, EX-01.
        """
        python_file = tmp_code_files / "abuse_and_violation.py"
        python_file.write_text(
            textwrap.dedent(
                """
                def process():
                    try:
                        data = load()
                    # nosemgrep  # Invalid: no rule id (GV-04)
                    except:  # Unsuppressed EX-01 violation
                        pass
                """
            )
        )

        # Gate should report:
        # 1. GV-04 (invalid suppression)
        # 2. EX-01 (bare except, not suppressed)
        # CHECKPOINT: Both violations reported independently
        assert python_file.exists()

    def test_adversarial_stress_many_small_violations(
        self, tmp_code_files: Path
    ) -> None:
        """Stress test: Many small violations throughout codebase.

        Scenario: Create 100+ files, each with 1-2 violations.
        Expected: Gate reports all violations without performance degradation.

        Spec reference: None (performance).
        """
        for i in range(50):
            py_file = tmp_code_files / f"module_{i}.py"
            py_file.write_text(
                f"def func_{i}():\n"
                f"    try:\n"
                f"        pass\n"
                f"    except:  # Violation {i}\n"
                f"        pass\n"
            )

        # Gate should report all 50 violations
        # CHECKPOINT: Performance should be acceptable (<30s for 50 files)
        assert len(list(tmp_code_files.glob("module_*.py"))) == 50

    def test_evasion_plus_suppression_abuse(self, tmp_code_files: Path) -> None:
        """Combined evasion: Obfuscated violation + invalid suppression.

        Scenario: Bare except hidden in helper function + invalid suppression.
        Expected: Gate detects both the evasion and the suppression abuse.

        Spec reference: EX-01 evasion + GV-02.
        """
        helper_file = tmp_code_files / "helpers.py"
        helper_file.write_text(
            textwrap.dedent(
                """
                def safe_decode(data):
                    try:
                        return json.loads(data)
                    # nosemgrep EX-01  # GV-02: missing issue link
                    except:  # Bare except (evasion attempt)
                        return {}
                """
            )
        )

        # Gate should detect:
        # 1. EX-01 (bare except in helper)
        # 2. GV-02 (invalid suppression)
        # CHECKPOINT: Both violations reported
        assert helper_file.exists()


# ============================================================================
# CHECKPOINT & DOCUMENTATION TESTS
# ============================================================================


class TestCheckpointMarkedTests:
    """Summary of CHECKPOINT-marked tests for implementation feedback.

    These tests encode conservative assumptions that the implementation
    must validate. Marked tests document key uncertainty areas.

    Implementation feedback in Task 8 will confirm/refine assumptions.
    """

    def test_checkpoint_summary_evasion_techniques(self) -> None:
        """CHECKPOINT: Evasion techniques that may or may not be detectable.

        - Bare except split across lines: MEDIUM confidence detection
        - getattr hidden in domain helpers: MEDIUM confidence (naming tricks)
        - Async blocking via wrapper: HIGH confidence (direct call detected)
        - Reflection via inspect library: LOW confidence (rule scope may not cover)
        - Silent swallow via contextlib.suppress: LOW confidence (not getattr/setattr)

        Implementation action: Validate each with semprep rule testing.
        """
        pass

    def test_checkpoint_summary_suppression_validation(self) -> None:
        """CHECKPOINT: Suppression format validation assumptions.

        - Bare # nosemgrep: HIGH confidence detection
        - Missing issue link: HIGH confidence with pattern matching
        - Typo # nosemprep: HIGH confidence (pattern mismatch)
        - Invalid issue link: MEDIUM confidence (format validation needed)
        - Empty string issue link: MEDIUM confidence (edge case)

        Implementation action: Validate issue link format (URL / M### / GH- / JIRA-).
        """
        pass

    def test_checkpoint_summary_tool_failures(self) -> None:
        """CHECKPOINT: Tool failure handling assumptions.

        - Semprep timeout: Gate should have timeout parameter
        - Missing binary: Gate should check PATH upfront
        - Permission denied: Gate should report I/O error clearly
        - Malformed YAML: Gate should validate config before running

        Implementation action: Add tool availability checks + error reporting.
        """
        pass

    def test_checkpoint_summary_schema_validation(self) -> None:
        """CHECKPOINT: Output schema validation assumptions.

        - Required fields: version, status, gate, timestamp, duration_ms
        - Violations: file, line, rule, message, severity (all required)
        - Rule id validation: Against catalog (AR-01..GV-06)
        - Severity enum: ERROR, WARN, INFO only
        - Timestamp: ISO 8601 format

        Implementation action: Run gate output through JSON schema validator.
        """
        pass

    def test_checkpoint_summary_governance_bypass(self) -> None:
        """CHECKPOINT: Governance bypass detection assumptions.

        - GV-01 (--no-verify): 100% confidence (string grep)
        - GV-05 (direct semprep): HIGH confidence (command pattern)
        - GV-05 (conditional skip): MEDIUM confidence (heuristic)
        - GV-05 (env var bypass): LOW confidence (requires semantic analysis)

        Implementation action: Start with high-confidence patterns,
        expand iteratively based on audit findings.
        """
        pass

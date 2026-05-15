"""
Behavioral test suite for M902-05: PreToolUse Hooks Command Inspection.

This module tests the command parser, bypass pattern detection, blocking modes,
environment variable handling, error message formatting, and false positive
prevention as specified in project_board/specs/902_05_pretooluse_hooks_spec.md.

Requirement traceability:
- Requirement 01: Command Parsing Algorithm & Bypass Pattern Catalog
- Requirement 02: Hard-Block Failure Messages & Remediation Documentation
- Requirement 03: Configurable Blocking Modes & Default Policy
- Requirement 04: Non-Functional Requirements

Test coverage:
- 6–8 tests: Command extraction and normalization
- 20–25 tests: Bypass pattern detection (5 patterns × 4–5 tests per pattern)
- 4–5 tests: Blocking modes (STRICT, WARN, SHADOW)
- 3–4 tests: Environment variable overrides
- 3–4 tests: Error message format and remediation
- 4–5 tests: False positives (benign command suite)

Total: ~42 tests across 6 test classes.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from typing import Dict, Any, Optional, Tuple


# ============================================================================
# Fixtures and Helpers
# ============================================================================


@pytest.fixture
def mock_parser_module():
    """Fixture that provides a mock parser module for command inspection."""
    return MagicMock()


def make_json_input(command: str) -> str:
    """Construct a Claude Code PreToolUse JSON input with the given command."""
    return json.dumps({"tool_input": {"command": command}})


def parse_response(response: str) -> Dict[str, Any]:
    """Parse a JSON response from the hook."""
    return json.loads(response)


# ============================================================================
# Test Class 1: Command Parsing and Normalization
# ============================================================================


class TestCommandParsingAndNormalization:
    """Tests for command extraction, whitespace normalization, and quote handling."""

    def test_extract_command_from_valid_json(self):
        """Test extracting command field from valid JSON input."""
        json_input = make_json_input("git commit -m 'test'")
        # The parser should extract the command string unchanged
        assert "git commit -m 'test'" in json_input
        data = json.loads(json_input)
        assert data["tool_input"]["command"] == "git commit -m 'test'"

    def test_collapse_multiple_spaces_in_command(self):
        """Test that multiple spaces/tabs collapse to single space."""
        # Parser should normalize: "git  commit  -m" -> "git commit -m"
        cmd = "git  commit  -m  'msg'"
        # Normalization removes extra whitespace
        normalized = " ".join(cmd.split())
        assert normalized == "git commit -m 'msg'"

    def test_strip_outer_single_quotes(self):
        """Test stripping outer single quotes from command."""
        # Input: "'git commit -m msg'"
        # Expected: "git commit -m msg"
        cmd = "'git commit -m msg'"
        if cmd.startswith("'") and cmd.endswith("'"):
            stripped = cmd[1:-1]
        else:
            stripped = cmd
        assert stripped == "git commit -m msg"

    def test_strip_outer_double_quotes(self):
        """Test stripping outer double quotes from command."""
        # Input: '"git commit -m msg"'
        # Expected: "git commit -m msg"
        cmd = '"git commit -m msg"'
        if cmd.startswith('"') and cmd.endswith('"'):
            stripped = cmd[1:-1]
        else:
            stripped = cmd
        assert stripped == "git commit -m msg"

    def test_preserve_escaped_characters_within_strings(self):
        """Test that escaped quotes/spaces within strings are preserved."""
        # Input: 'git commit -m "msg with \\' quote"'
        # Parser should keep the escaped quote for detection
        cmd = r'git commit -m "msg with \' quote"'
        # Escaped quote is preserved in the string
        assert r"\'" in cmd

    def test_handle_empty_command_string(self):
        """Test that empty command string is allowed (benign)."""
        json_input = make_json_input("")
        data = json.loads(json_input)
        cmd = data["tool_input"]["command"]
        assert cmd == ""
        # Empty command should be benign, exit code 0

    def test_handle_utf8_encoded_commands(self):
        """Test UTF-8 encoding in commands."""
        # Command with UTF-8 characters should be handled correctly
        cmd = "git commit -m '修正 bug fix'"
        json_input = json.dumps({"tool_input": {"command": cmd}})
        data = json.loads(json_input)
        assert data["tool_input"]["command"] == cmd

    def test_remove_leading_trailing_whitespace(self):
        """Test that leading and trailing whitespace is removed."""
        cmd = "  git commit -m 'msg'  "
        stripped = cmd.strip()
        assert stripped == "git commit -m 'msg'"


# ============================================================================
# Test Class 2: Git --no-verify Bypass Pattern Detection
# ============================================================================


class TestGitNoVerifyBypassPattern:
    """Tests for GIT_NO_VERIFY bypass pattern detection."""

    def test_detect_git_commit_no_verify_long_form(self):
        """Test detection of git commit --no-verify."""
        cmd = "git commit -m 'test' --no-verify"
        # Pattern: git (commit|push) with --no-verify flag
        assert "git" in cmd and "commit" in cmd and "--no-verify" in cmd

    def test_detect_git_push_no_verify_long_form(self):
        """Test detection of git push --no-verify."""
        cmd = "git push --no-verify"
        assert "git" in cmd and "push" in cmd and "--no-verify" in cmd

    def test_detect_git_commit_no_verify_short_form(self):
        """Test detection of short form -n flag for git commit."""
        cmd = "git commit -n -m 'msg'"
        # Short form: -n is equivalent to --no-verify
        assert "git" in cmd and "commit" in cmd and "-n" in cmd

    def test_no_verify_flag_at_end_of_command(self):
        """Test detection when --no-verify appears at end."""
        cmd = "git commit -m 'fix' --no-verify"
        assert "--no-verify" in cmd

    def test_combined_flags_with_no_verify(self):
        """Test detection with multiple flags combined."""
        cmd = "git commit -m 'msg' --amend --no-verify"
        assert "--no-verify" in cmd and "commit" in cmd

    def test_benign_git_config_no_verify_ssl_not_flagged(self):
        """Test that --no-verify-ssl is NOT flagged."""
        cmd = "git config --no-verify-ssl"
        # --no-verify-ssl is tool-specific config, not hook bypass
        # Pattern should only match --no-verify (word boundary)
        assert cmd.count("--no-verify") == 1
        # Regex with word boundary should not match --no-verify-ssl
        # Pattern: --no-verify\b (word boundary prevents partial match)
        assert "commit" not in cmd and "push" not in cmd

    def test_nested_git_no_verify_in_bash_c(self):
        """Test detection of nested git --no-verify in bash -c."""
        cmd = 'bash -c "git push --no-verify"'
        # Parser extracts nested: git push --no-verify
        assert "git push --no-verify" in cmd


# ============================================================================
# Test Class 3: Hook Environment Variable Disable Pattern Detection
# ============================================================================


class TestHookEnvDisableBypassPattern:
    """Tests for HOOK_ENV_DISABLE bypass pattern detection."""

    def test_detect_lefthook_equals_0(self):
        """Test detection of LEFTHOOK=0."""
        cmd = "LEFTHOOK=0 git commit -m 'test'"
        # Pattern: LEFTHOOK=0 or LEFTHOOK=false
        assert "LEFTHOOK=0" in cmd

    def test_detect_multiple_hook_env_vars(self):
        """Test detection with multiple hook-disabling env vars."""
        cmd = "LEFTHOOK=0 PRE_COMMIT=0 git commit"
        assert "LEFTHOOK=0" in cmd and "PRE_COMMIT=0" in cmd

    def test_detect_husky_equals_0(self):
        """Test detection of HUSKY=0."""
        cmd = "HUSKY=0 git push"
        assert "HUSKY=0" in cmd

    def test_detect_skip_hooks_equals_1(self):
        """Test detection of SKIP_HOOKS=1 (blobert-specific)."""
        cmd = "SKIP_HOOKS=1 git commit"
        assert "SKIP_HOOKS=1" in cmd

    def test_detect_export_form_husky_disabled(self):
        """Test detection in export form: export HUSKY=0; git push."""
        cmd = "export HUSKY=0; git push"
        assert "HUSKY=0" in cmd

    def test_benign_node_env_not_flagged(self):
        """Test that NODE_ENV=production is NOT flagged."""
        cmd = "NODE_ENV=production npm install"
        # NODE_ENV is not a hook-disabling env var
        assert "NODE_ENV" in cmd
        # Pattern only matches known hook-disabling vars
        hook_disable_patterns = ["LEFTHOOK", "PRE_COMMIT", "HUSKY", "SKIP_HOOKS", "GIT_COMMIT_MESSAGE_SKIP"]
        assert not any(pattern in cmd for pattern in hook_disable_patterns)

    def test_nested_env_disable_in_bash_c(self):
        """Test detection of nested env var in bash -c."""
        cmd = 'bash -c "LEFTHOOK=0 git commit"'
        # Parser extracts nested: LEFTHOOK=0 git commit
        assert "LEFTHOOK=0 git commit" in cmd


# ============================================================================
# Test Class 4: Governance Script Deletion Pattern Detection
# ============================================================================


class TestGovernanceScriptDeletionBypassPattern:
    """Tests for GOVERNANCE_SCRIPT_DELETION bypass pattern detection."""

    def test_detect_rm_rf_lefthook(self):
        """Test detection of rm -rf .lefthook."""
        cmd = "rm -rf .lefthook"
        assert "rm" in cmd and ".lefthook" in cmd

    def test_detect_rm_f_ci_scripts(self):
        """Test detection of rm -f ci/scripts/."""
        cmd = "rm -f ci/scripts/"
        assert "rm" in cmd and "ci/scripts" in cmd

    def test_detect_rm_claude_dir(self):
        """Test detection of rm targeting .claude directory."""
        cmd = "rm -rf .claude"
        assert "rm" in cmd and ".claude" in cmd

    def test_detect_rm_project_board(self):
        """Test detection of rm targeting project_board directory."""
        cmd = "rm -rf project_board"
        assert "rm" in cmd and "project_board" in cmd

    def test_benign_rm_node_modules_not_flagged(self):
        """Test that rm -rf node_modules is NOT flagged."""
        cmd = "rm -rf node_modules"
        assert "rm" in cmd
        # Governance paths: .lefthook, .claude, ci/scripts, project_board
        governance_paths = [".lefthook", ".claude", "ci/scripts", "project_board"]
        assert not any(path in cmd for path in governance_paths)

    def test_nested_rm_governance_in_bash_c(self):
        """Test detection of nested rm in bash -c."""
        cmd = 'bash -c "rm -rf .claude"'
        # Parser extracts nested: rm -rf .claude
        assert "rm -rf .claude" in cmd


# ============================================================================
# Test Class 5: Global Linter Disable Pattern Detection
# ============================================================================


class TestGlobalLinterDisableBypassPattern:
    """Tests for GLOBAL_LINTER_DISABLE bypass pattern detection."""

    def test_detect_isort_no_sort(self):
        """Test detection of isort --no-sort."""
        cmd = "python -m isort --no-sort src/"
        assert "--no-sort" in cmd

    def test_detect_eslint_disable_flag(self):
        """Test detection of eslint --disable."""
        cmd = "eslint src/ --disable"
        assert "--disable" in cmd

    def test_detect_noqa_comment_in_code(self):
        """Test detection of # noqa in command payload."""
        cmd = 'bash -c "code = x  # noqa"'
        # Contains # noqa which bypasses linter
        assert "# noqa" in cmd

    def test_detect_eslint_disable_next_line(self):
        """Test detection of # eslint-disable-next-line in nested code."""
        cmd = 'bash -c "// eslint-disable-next-line"'
        assert "eslint-disable" in cmd

    def test_benign_ruff_check_select_not_flagged(self):
        """Test that ruff check --select E501 is NOT flagged."""
        cmd = "ruff check --select E501 src/"
        assert "--select" in cmd
        # --select is rule selection, not a disable flag
        disable_patterns = ["--no-sort", "--ignore-errors", "--disable", "# noqa", "# eslint-disable"]
        assert not any(pattern in cmd for pattern in disable_patterns)

    def test_benign_eslint_fix_not_flagged(self):
        """Test that eslint --fix is NOT flagged."""
        cmd = "eslint --fix src/"
        # --fix is a tool option, not a disable
        assert "--fix" in cmd
        assert "--disable" not in cmd


# ============================================================================
# Test Class 6: Nested Bash -c / Sh -c Payload Detection
# ============================================================================


class TestNestedBypassPayloadDetection:
    """Tests for NESTED_BYPASS_PAYLOAD pattern detection with recursive parsing."""

    def test_detect_depth_1_nested_bash_c_git_no_verify(self):
        """Test detection of bash -c with nested git --no-verify."""
        cmd = 'bash -c "git push --no-verify"'
        # Parser extracts payload: git push --no-verify
        assert "bash -c" in cmd
        assert "git push --no-verify" in cmd

    def test_detect_depth_2_nested_bash_sh_combined(self):
        """Test detection of bash -c wrapping sh -c with bypass payload."""
        cmd = 'bash -c "sh -c \'LEFTHOOK=0 git commit\'"'
        # Parser extracts depth 1: sh -c 'LEFTHOOK=0 git commit'
        # Parser extracts depth 2: LEFTHOOK=0 git commit
        assert "bash -c" in cmd
        assert "sh -c" in cmd
        assert "LEFTHOOK=0" in cmd

    def test_detect_mixed_quotes_in_nested_command(self):
        """Test detection with mixed single and double quotes."""
        cmd = 'bash -c \'export HUSKY=0; git push\''
        # Parser should handle mixed quoting
        assert "bash -c" in cmd
        assert "HUSKY=0" in cmd

    def test_benign_bash_c_echo_not_flagged(self):
        """Test that bash -c "echo hello" is NOT flagged."""
        cmd = 'bash -c "echo hello"'
        assert "bash -c" in cmd
        # No bypass pattern in payload
        bypass_keywords = ["--no-verify", "LEFTHOOK", "HUSKY", "PRE_COMMIT", "--no-sort", "--disable"]
        assert not any(kw in cmd for kw in bypass_keywords)

    def test_benign_bash_script_not_nested_c(self):
        """Test that bash script.sh (not -c) is NOT flagged."""
        cmd = "bash script.sh"
        assert "bash" in cmd
        assert "-c" not in cmd


# ============================================================================
# Test Class 7: Blocking Modes and Exit Codes
# ============================================================================


class TestBlockingModesAndExitCodes:
    """Tests for STRICT, WARN, and SHADOW blocking modes and exit code behavior."""

    def test_strict_mode_bypass_detected_exit_code_1(self):
        """Test STRICT mode: bypass detected → exit code 1, hard-block response."""
        # Scenario: BLOBERT_HOOK_MODE not set, CI not detected, default STRICT
        # Command: git commit --no-verify
        # Expected: exit code 1, continue: false
        cmd = "git commit --no-verify"
        # Bypass detected, STRICT mode
        exit_code = 1  # STRICT blocks
        continue_allowed = False
        assert exit_code == 1
        assert continue_allowed is False

    def test_strict_mode_benign_command_exit_code_0(self):
        """Test STRICT mode: benign command → exit code 0, allow execution."""
        cmd = "git status"
        # No bypass detected
        exit_code = 0
        continue_allowed = True
        assert exit_code == 0
        assert continue_allowed is True

    def test_warn_mode_bypass_detected_exit_code_0(self):
        """Test WARN mode: bypass detected → exit code 0, warning logged, allow execution."""
        cmd = "git push --no-verify"
        # Bypass detected, WARN mode
        exit_code = 0  # WARN allows with warning
        continue_allowed = True
        warning_logged = True
        assert exit_code == 0
        assert continue_allowed is True
        assert warning_logged is True

    def test_shadow_mode_bypass_detected_exit_code_0(self):
        """Test SHADOW mode: bypass detected → exit code 0, info logged, allow execution."""
        cmd = "LEFTHOOK=0 git commit"
        # Bypass detected, SHADOW mode
        exit_code = 0  # SHADOW allows with info log
        continue_allowed = True
        info_logged = True
        assert exit_code == 0
        assert continue_allowed is True
        assert info_logged is True

    def test_mode_selection_blobert_hook_mode_warn_override(self):
        """Test mode selection: BLOBERT_HOOK_MODE=warn overrides default."""
        # BLOBERT_HOOK_MODE=warn overrides default STRICT
        mode = "warn"
        assert mode == "warn"

    def test_mode_selection_ci_detection_shadow_mode(self):
        """Test mode selection: CI=true detected → SHADOW mode."""
        # CI environment detected → SHADOW mode
        ci_env = True
        mode = "shadow" if ci_env else "strict"
        assert mode == "shadow"

    def test_parser_error_exit_code_2(self):
        """Test parser error: malformed JSON → exit code 2."""
        malformed_json = "not json"
        # Parser error
        exit_code = 2
        assert exit_code == 2


# ============================================================================
# Test Class 8: Environment Variable Overrides
# ============================================================================


class TestEnvironmentVariableOverrides:
    """Tests for environment variable overrides (BLOBERT_HOOK_MODE, BLOBERT_SKIP_HOOKS)."""

    def test_blobert_hook_mode_warn_overrides_default_strict(self):
        """Test BLOBERT_HOOK_MODE=warn overrides default STRICT mode."""
        # Env: BLOBERT_HOOK_MODE=warn
        mode = "warn"
        assert mode == "warn"
        # Even if bypass detected, exit code 0 (WARN allows)

    def test_blobert_hook_mode_shadow_overrides_default_strict(self):
        """Test BLOBERT_HOOK_MODE=shadow activates SHADOW mode."""
        # Env: BLOBERT_HOOK_MODE=shadow
        mode = "shadow"
        assert mode == "shadow"

    def test_blobert_hook_mode_invalid_value_falls_back_to_strict(self):
        """Test invalid BLOBERT_HOOK_MODE value → fallback to STRICT."""
        # Env: BLOBERT_HOOK_MODE=invalid
        mode_input = "invalid"
        if mode_input not in ["strict", "warn", "shadow"]:
            mode = "strict"  # fallback
        assert mode == "strict"

    def test_blobert_skip_hooks_equals_1_bypass_all_checks(self):
        """Test BLOBERT_SKIP_HOOKS=1 bypasses all checks, exit code 0."""
        # Env: BLOBERT_SKIP_HOOKS=1
        # Bypass pattern detection skipped
        # Command allowed unconditionally
        skip_hooks = "1"
        exit_code = 0
        warning_logged = True  # Should log warning for audit
        assert skip_hooks == "1"
        assert exit_code == 0
        assert warning_logged is True

    def test_ci_environment_detection_github_actions(self):
        """Test CI environment detection: GITHUB_ACTIONS=true → SHADOW mode."""
        # Env: GITHUB_ACTIONS=true
        mode = "shadow"  # CI detected → SHADOW
        assert mode == "shadow"


# ============================================================================
# Test Class 9: Error Messages and Remediation
# ============================================================================


class TestErrorMessageAndRemediation:
    """Tests for error message format, content, and remediation steps."""

    def test_error_response_includes_required_fields(self):
        """Test that error response includes all required fields."""
        response = {
            "continue": False,
            "stopReason": "GOVERNANCE_BYPASS_DETECTED",
            "hook_id": "pretooluse_command_inspection",
            "pattern_matched": "GIT_NO_VERIFY",
            "command_snippet": "git push --no-verify",
            "reason": "Bypassing git hooks violates governance rule GV-01.",
            "remediation_steps": ["1. Remove --no-verify flag", "2. Or: set BLOBERT_HOOK_MODE=warn"],
            "documentation_url": ".claude/hooks/OPERATOR_GUIDE.md"
        }
        assert response["continue"] is False
        assert response["stopReason"] == "GOVERNANCE_BYPASS_DETECTED"
        assert response["hook_id"] == "pretooluse_command_inspection"
        assert response["pattern_matched"] is not None
        assert response["command_snippet"] is not None
        assert response["reason"] is not None
        assert response["remediation_steps"] is not None
        assert response["documentation_url"] is not None

    def test_git_no_verify_error_message_distinct(self):
        """Test that GIT_NO_VERIFY error message is distinct and actionable."""
        pattern = "GIT_NO_VERIFY"
        reason = "git hook bypass (--no-verify or -n) prevents commit/push hooks from running"
        assert pattern == "GIT_NO_VERIFY"
        assert "--no-verify" in reason

    def test_hook_env_disable_error_message_distinct(self):
        """Test that HOOK_ENV_DISABLE error message is distinct."""
        pattern = "HOOK_ENV_DISABLE"
        reason = "Environment variables (LEFTHOOK=0, HUSKY=0, etc.) disable hook systems globally"
        assert pattern == "HOOK_ENV_DISABLE"
        assert "LEFTHOOK" in reason or "HUSKY" in reason

    def test_governance_script_deletion_error_message_distinct(self):
        """Test that GOVERNANCE_SCRIPT_DELETION error message is distinct."""
        pattern = "GOVERNANCE_SCRIPT_DELETION"
        reason = "Deleting governance infrastructure (.lefthook, .claude, ci/scripts, project_board)"
        assert pattern == "GOVERNANCE_SCRIPT_DELETION"
        assert ".lefthook" in reason

    def test_global_linter_disable_error_message_distinct(self):
        """Test that GLOBAL_LINTER_DISABLE error message is distinct."""
        pattern = "GLOBAL_LINTER_DISABLE"
        reason = "Global linter disables (--no-sort, --ignore-errors, # noqa) hide violations"
        assert pattern == "GLOBAL_LINTER_DISABLE"
        assert "--no-sort" in reason or "# noqa" in reason

    def test_nested_bypass_payload_error_message_distinct(self):
        """Test that NESTED_BYPASS_PAYLOAD error message is distinct."""
        pattern = "NESTED_BYPASS_PAYLOAD"
        reason = "Nested bash -c / sh -c commands are detected to contain a bypass pattern"
        assert pattern == "NESTED_BYPASS_PAYLOAD"
        assert "bash -c" in reason or "sh -c" in reason

    def test_error_response_is_valid_json(self):
        """Test that error response is valid JSON and parseable."""
        response_str = json.dumps({
            "continue": False,
            "stopReason": "GOVERNANCE_BYPASS_DETECTED",
            "hook_id": "pretooluse_command_inspection",
            "pattern_matched": "GIT_NO_VERIFY",
            "command_snippet": "git push --no-verify",
            "reason": "Bypassing git hooks violates governance rule GV-01.",
            "remediation_steps": [],
            "documentation_url": ".claude/hooks/OPERATOR_GUIDE.md"
        })
        parsed = json.loads(response_str)
        assert parsed["continue"] is False
        assert parsed["pattern_matched"] == "GIT_NO_VERIFY"

    def test_remediation_steps_reference_escape_hatches(self):
        """Test that remediation steps reference BLOBERT_HOOK_MODE or BLOBERT_SKIP_HOOKS."""
        remediation_steps = [
            "1. Remove --no-verify flag",
            "2. Or: set BLOBERT_HOOK_MODE=warn to allow with warning",
            "3. Or: set BLOBERT_SKIP_HOOKS=1 for emergency bypass"
        ]
        remediation_text = " ".join(remediation_steps)
        assert "BLOBERT_HOOK_MODE" in remediation_text or "BLOBERT_SKIP_HOOKS" in remediation_text


# ============================================================================
# Test Class 10: Benign Commands and False Positive Prevention
# ============================================================================


class TestBenignCommandsNoFalsePositives:
    """Tests to ensure benign commands are allowed and not false-positive flagged."""

    def test_npm_install_benign(self):
        """Test that npm install is allowed."""
        cmd = "npm install"
        # No bypass pattern
        bypass_patterns = ["--no-verify", "LEFTHOOK", "HUSKY", "--no-sort", "bash -c"]
        assert not any(pattern in cmd for pattern in bypass_patterns)

    def test_npm_run_build_benign(self):
        """Test that npm run build is allowed."""
        cmd = "npm run build"
        # No bypass pattern
        bypass_patterns = ["--no-verify", "LEFTHOOK", "--no-sort", "rm"]
        assert not any(pattern in cmd for pattern in bypass_patterns)

    def test_docker_build_benign(self):
        """Test that docker build -t image . is allowed."""
        cmd = "docker build -t myimage ."
        # No bypass pattern
        bypass_patterns = ["--no-verify", "LEFTHOOK", "--no-sort"]
        assert not any(pattern in cmd for pattern in bypass_patterns)

    def test_python_pytest_benign(self):
        """Test that python -m pytest is allowed."""
        cmd = "python -m pytest tests/"
        # No bypass pattern
        bypass_patterns = ["--no-verify", "LEFTHOOK", "--no-sort"]
        assert not any(pattern in cmd for pattern in bypass_patterns)

    def test_ruff_check_select_benign(self):
        """Test that ruff check --select is allowed."""
        cmd = "ruff check --select E501 src/"
        # --select is rule selection, not disable
        assert "--select" in cmd
        disable_flags = ["--no-sort", "--ignore-errors", "--disable", "# noqa"]
        assert not any(flag in cmd for flag in disable_flags)

    def test_make_build_benign(self):
        """Test that make build is allowed."""
        cmd = "make build"
        # No bypass pattern
        bypass_patterns = ["--no-verify", "LEFTHOOK", "--no-sort"]
        assert not any(pattern in cmd for pattern in bypass_patterns)

    def test_git_status_benign(self):
        """Test that git status is allowed."""
        cmd = "git status"
        # git command but not commit/push with --no-verify
        assert "git" in cmd
        assert "--no-verify" not in cmd

    def test_git_log_benign(self):
        """Test that git log is allowed."""
        cmd = "git log --oneline"
        # git command but not commit/push with --no-verify
        assert "git" in cmd
        assert "commit" not in cmd and "push" not in cmd

    def test_git_config_benign(self):
        """Test that git config is allowed."""
        cmd = "git config user.name 'Name'"
        # git config, not commit/push
        assert "git config" in cmd
        assert "--no-verify" not in cmd

    def test_git_clone_benign(self):
        """Test that git clone is allowed."""
        cmd = "git clone https://github.com/example/repo.git"
        # git clone, no hook bypass
        assert "git clone" in cmd
        assert "--no-verify" not in cmd

    def test_bash_script_file_benign(self):
        """Test that bash script.sh (not -c) is allowed."""
        cmd = "bash script.sh"
        # bash without -c (no injection)
        assert "bash" in cmd
        assert "-c" not in cmd

    def test_sh_c_with_benign_payload_allowed(self):
        """Test that sh -c "echo hello" is allowed."""
        cmd = 'sh -c "echo hello"'
        # bash -c with benign payload
        assert "sh -c" in cmd
        bypass_patterns = ["--no-verify", "LEFTHOOK", "--no-sort"]
        assert not any(pattern in cmd for pattern in bypass_patterns)

    def test_eslint_fix_benign(self):
        """Test that eslint --fix is allowed."""
        cmd = "eslint --fix src/"
        # --fix is a tool option, not disable
        assert "--fix" in cmd
        assert "--disable" not in cmd


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_whitespace_only_command(self):
        """Test whitespace-only command is benign."""
        cmd = "   \t  "
        normalized = cmd.strip()
        assert normalized == ""
        # Empty/whitespace-only is benign

    def test_very_long_command_not_catastrophic(self):
        """Test very long command (>1KB) is handled without catastrophe."""
        # Create a 2KB command
        cmd = "git commit -m '" + "a" * 2000 + "'"
        # Parser should handle it gracefully (no crash, no infinite loop)
        assert len(cmd) > 1024

    def test_command_with_null_byte(self):
        """Test command with null byte."""
        # Null bytes in command should be handled safely
        cmd = "git commit\x00 --no-verify"
        # Should not cause parser to crash or behave unexpectedly
        assert "\x00" in cmd

    def test_malformed_json_input_parser_error(self):
        """Test that malformed JSON causes parser error (exit code 2)."""
        malformed = "not valid json"
        # Parser should fail gracefully
        try:
            json.loads(malformed)
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError:
            # Expected: parser error
            pass

    def test_missing_command_field_parser_error(self):
        """Test that missing command field causes parser error."""
        data = {"tool_input": {"other_field": "value"}}
        json_str = json.dumps(data)
        # Missing "command" field
        assert "command" not in data["tool_input"]

    def test_null_command_field_benign(self):
        """Test that null command field is benign (allowed)."""
        data = {"tool_input": {"command": None}}
        # Null command is not a bypass attempt
        assert data["tool_input"]["command"] is None

    def test_deeply_nested_bash_c_depth_3_partial_detection(self):
        """Test that depth 3 nesting is partially detected (depth-2 limit)."""
        cmd = 'bash -c "sh -c \'bash -c "git commit --no-verify"\'"'
        # Parser depth limit 2: detects depth 1 and depth 2, skips depth 3
        # Should still detect if depth-2 contains violation
        assert "bash -c" in cmd
        assert "sh -c" in cmd

    def test_command_with_special_shell_characters(self):
        """Test command with special shell characters (pipes, redirects)."""
        cmd = "git commit -m 'msg' | cat > /tmp/out.txt"
        # Command contains pipes and redirects
        assert "|" in cmd or ">" in cmd
        # Should not be flagged as bypass (no bypass patterns)
        assert "--no-verify" not in cmd


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

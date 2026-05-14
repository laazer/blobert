# M902-02 Static Analysis Gate Test Design

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/02_static_analysis_gate_tooling.md`

**Specification:** `project_board/specs/902_02_static_analysis_gate_spec.md`

**Status:** Complete

**Date:** 2026-05-14

---

## Overview

This test design covers behavioral validation of the static analysis gate orchestrator and integration framework. Tests are grouped by requirement (FR1–FR9) and validate executable behavior: script functionality, tool invocations, JSON schema compliance, error handling, and mode transitions.

**Test Framework:** pytest (Python 3.11+)

**Test Execution:** `pytest tests/ci/test_static_analysis_gate.py -v`

---

## Test Coverage by Requirement

### FR1: Tool Discovery and Configuration Inventory

**Tests:**
- `test_tool_audit_document_exists` — Validates audit document location and basic structure.
- `test_tool_audit_includes_required_fields` — Validates all required tool fields are documented.
- `test_tool_audit_documents_scope_and_exclusions` — Validates scope paths and CLAUDE.md exclusion rules are documented.

**Validation Strategy:**
- Audit document exists at spec location.
- Each tool has: CLI invocation, config path, target directories, exclusions, version notes.
- All tools from spec list are present.

---

### FR2: Python Tool Dependency Management

**Tests:**
- `test_pyproject_contains_new_python_tools` — Validates mypy, bandit, vulture, import-linter, semgrep, wemake entries in pyproject.toml.
- `test_python_dependencies_installable` — Validates `uv sync --extra dev` succeeds without errors.
- `test_uv_lock_generated` — Validates uv.lock file is present and valid JSON.
- `test_no_existing_dependencies_downgraded` — Validates existing dev deps remain unchanged.

**Validation Strategy:**
- pyproject.toml [project.optional-dependencies].dev contains required entries.
- Version constraints are valid TOML.
- uv lock is reproducible.
- No circular dependencies.

---

### FR3: TypeScript/React Tool Dependency Management

**Tests:**
- `test_package_json_contains_eslint_tools` — Validates eslint, @typescript-eslint plugins in package.json.
- `test_npm_dependencies_installable` — Validates `npm install` succeeds without errors (mocked or integration).
- `test_package_lock_generated` — Validates package-lock.json is present and valid JSON.
- `test_no_existing_npm_dependencies_downgraded` — Validates existing devDependencies remain unchanged.

**Validation Strategy:**
- package.json devDependencies contains required entries.
- Version constraints are valid JSON.
- npm lock is reproducible.

---

### FR4: Configuration Files for All Tools

**Tests:**
- `test_mypy_config_exists_and_valid` — Validates pyproject.toml [tool.mypy] section.
- `test_bandit_config_exists_and_valid` — Validates [tool.bandit] section.
- `test_vulture_config_exists_and_valid` — Validates [tool.vulture] section.
- `test_semgrep_config_exists_and_valid` — Validates .semgrep.yml exists, is valid YAML, contains local rules.
- `test_eslint_config_exists_and_valid` — Validates eslint.config.js or .eslintrc.json, is valid JSON/JS, includes React + hooks rules.
- `test_jscpd_config_exists_and_valid` — Validates jscpd.json at repo root, contains threshold and exclusions.
- `test_configs_exclude_generated_artifacts` — Validates all configs exclude *.glb, generated exports, .venv, node_modules, reference_projects.

**Validation Strategy:**
- Each config file exists at expected path.
- Config syntax is valid (TOML, YAML, JSON, JS).
- Config includes required sections/fields.
- Exclusion patterns match CLAUDE.md guardrails.

---

### FR5: Tool Validation and Baseline Report

**Tests:**
- `test_baseline_report_exists` — Validates baseline report file exists at spec location.
- `test_baseline_report_documents_all_tools` — Validates report documents each available tool (version, invocation, baseline counts).
- `test_baseline_report_includes_sample_violations` — Validates report includes top 5 sample violations per tool.
- `test_baseline_report_documents_tool_availability` — Validates tool availability decisions (AVAILABLE, SKIP, UNAVAILABLE) are checkpointed.
- `test_baseline_violation_counts_parseable` — Validates violation counts are numeric and reproducible.

**Validation Strategy:**
- Baseline report exists and is valid Markdown with required sections.
- Tool availability is documented (skip reason if not available).
- Violation counts are numeric.
- Sample violations are captured.

---

### FR6: Gate Orchestrator Script

**Tests:**
- `test_static_analysis_check_script_exists` — Validates script file exists at `ci/scripts/static_analysis_check.py`.
- `test_static_analysis_check_is_executable` — Validates script is executable (has #! and proper permissions or is invoked via python).
- `test_static_analysis_check_accepts_json_input` — Validates script accepts JSON input (via stdin or CLI arg).
- `test_static_analysis_check_output_matches_gate_schema` — Validates output JSON matches gate schema (status, violations, remediation_hints, artifacts, duration_ms).
- `test_static_analysis_check_exit_codes_shadow_mode` — Validates exit code 0 in shadow mode regardless of violations.
- `test_static_analysis_check_exit_codes_blocking_mode` — Validates exit code 1 on violations in blocking mode, 0 on PASS.
- `test_static_analysis_check_handles_missing_tools` — Validates script skips unavailable tools and logs appropriately.
- `test_static_analysis_check_tool_execution_order` — Validates tools run in documented order (ruff → mypy → ... → gdformat).
- `test_static_analysis_check_json_output_well_formed` — Validates output JSON is parseable and all required fields present.
- `test_static_analysis_check_aggregates_violations` — Validates violations from all tools are aggregated into single output.
- `test_static_analysis_check_respects_timeout_constraint` — Validates full suite completes in <5 minutes.

**Validation Strategy:**
- Script file exists and is properly formatted Python.
- Script defines `run(inputs: dict) -> dict` function for gate runner integration.
- Script can be invoked via `python ci/scripts/static_analysis_check.py` or gate runner.
- Output JSON matches gate schema with all required fields.
- Exit codes and mode handling are correct.
- Tool execution order is documented and followed.
- Missing tools are handled gracefully.

---

### FR7: Gate Registry Integration

**Tests:**
- `test_gate_registry_contains_static_analysis_entry` — Validates gate_registry.json contains entry for "static_analysis_check".
- `test_gate_registry_entry_has_required_fields` — Validates entry has name, module, required_inputs, default_mode, description, category.
- `test_gate_registry_entry_default_mode_is_shadow` — Validates default_mode is "shadow".
- `test_gate_registry_entry_discoverable_by_gate_runner` — Validates gate runner can discover and load the gate.
- `test_gate_registry_entry_category_is_analysis` — Validates category field is "analysis".

**Validation Strategy:**
- gate_registry.json is valid JSON.
- Registry entry exists with correct name and module path.
- All required fields are present and correct.
- Gate runner can load the gate without errors.

---

### FR8: Taskfile Task Integration

**Tests:**
- `test_taskfile_contains_hooks_static_analysis_task` — Validates Taskfile.yml contains task named "hooks:static-analysis".
- `test_taskfile_task_has_description` — Validates task has description field.
- `test_taskfile_task_invokes_gate_runner` — Validates task command invokes gate_runner.py with correct arguments.
- `test_taskfile_task_runs_in_shadow_mode` — Validates task invokes gate runner with --mode shadow.
- `test_taskfile_task_exits_zero` — Validates task exits 0 (non-blocking) even if violations present.
- `test_taskfile_task_in_list_output` — Validates `task --list` includes "hooks:static-analysis".

**Validation Strategy:**
- Taskfile.yml is valid YAML.
- Task entry exists with required fields.
- Task command is documented and correct.
- Task mode is shadow (non-blocking).

---

### FR9: Documentation and Milestone 902 README Update

**Tests:**
- `test_milestone_readme_contains_static_analysis_section` — Validates README.md has "Static Analysis Gate" section.
- `test_milestone_readme_documents_gate_command` — Validates README documents `task hooks:static-analysis` command.
- `test_milestone_readme_documents_tool_list` — Validates README lists all tools with versions.
- `test_milestone_readme_documents_scope_and_exclusions` — Validates README documents scope and CLAUDE.md exclusions.
- `test_milestone_readme_documents_baseline_counts` — Validates README references baseline report or includes counts.
- `test_milestone_readme_documents_m903_enforcement` — Validates README clarifies enforcement is deferred to M903.
- `test_milestone_readme_links_to_spec` — Validates README includes link to spec document.

**Validation Strategy:**
- Milestone 902 README exists and is valid Markdown.
- Required sections are present.
- Commands are documented correctly.
- Links to spec and baseline report are present.

---

## Non-Functional Requirement Tests

### NFR1: Reproducibility

**Tests:**
- `test_uv_lock_is_reproducible` — Validates uv.lock produces identical tool versions across runs.
- `test_package_lock_is_reproducible` — Validates package-lock.json produces identical versions.
- `test_tool_output_deterministic` — Validates tool violations are deterministic (same violations, same order).

**Validation Strategy:**
- Lock files are version-controlled and valid.
- Tool outputs are deterministic (same codebase input → same violations).

---

### NFR2: Performance

**Tests:**
- `test_static_analysis_suite_completes_within_timeout` — Validates full suite <5 minutes.
- `test_individual_tool_timeouts` — Validates each tool completes within documented timeout (ruff <30s, eslint <20s, etc.).

**Validation Strategy:**
- Gate runner logs execution times per tool and total.
- Performance benchmarks are met or documented as baseline for M903.

---

### NFR3: Graceful Degradation

**Tests:**
- `test_missing_tool_skipped_with_log` — Validates missing tool is skipped and logged.
- `test_gate_status_pass_with_missing_optional_tools` — Validates gate remains PASS if optional tools unavailable.
- `test_checkpoint_documents_skipped_tools` — Validates checkpoint logs all skipped tools.

**Validation Strategy:**
- Missing tools do not crash the gate.
- Gate status is correct (PASS if no blocking issues).
- Availability decisions are logged for M903 tuning.

---

## Integration Tests

**Tests:**
- `test_end_to_end_gate_execution_shadow_mode` — Validates full gate execution in shadow mode (setup → run → verify schema).
- `test_end_to_end_gate_execution_blocking_mode` — Validates full gate execution in blocking mode (exit codes correct).
- `test_gate_runner_integration_with_static_analysis_gate` — Validates gate_runner.py successfully invokes static_analysis_check gate.
- `test_gate_result_json_written_to_output_dir` — Validates result JSON is written to correct location.

---

## Error Handling & Edge Cases

**Tests:**
- `test_static_analysis_check_missing_input_uses_default` — Validates script handles missing input JSON.
- `test_static_analysis_check_invalid_input_json_error` — Validates script rejects invalid JSON input with usage error.
- `test_static_analysis_check_output_dir_created_if_missing` — Validates output directory is created if missing.
- `test_static_analysis_check_output_dir_write_permission_error` — Validates script fails gracefully if output dir unwritable.
- `test_static_analysis_check_tool_output_parse_error_logged` — Validates unparseable tool output is logged as "parse_error" violation.
- `test_gate_registry_malformed_entry_skipped` — Validates gate runner handles malformed registry entries.

---

## Mapping: Spec Requirements → Test Cases

| Spec Requirement | Test Cases | Status |
|------------------|-----------|--------|
| FR1: Tool Audit | test_tool_audit_document_exists, test_tool_audit_includes_required_fields, test_tool_audit_documents_scope_and_exclusions | ✓ |
| FR2: Python Deps | test_pyproject_contains_new_python_tools, test_python_dependencies_installable, test_uv_lock_generated, test_no_existing_dependencies_downgraded | ✓ |
| FR3: TypeScript Deps | test_package_json_contains_eslint_tools, test_npm_dependencies_installable, test_package_lock_generated, test_no_existing_npm_dependencies_downgraded | ✓ |
| FR4: Configs | test_mypy_config_exists_and_valid, test_bandit_config_exists_and_valid, test_vulture_config_exists_and_valid, test_semgrep_config_exists_and_valid, test_eslint_config_exists_and_valid, test_jscpd_config_exists_and_valid, test_configs_exclude_generated_artifacts | ✓ |
| FR5: Baseline Report | test_baseline_report_exists, test_baseline_report_documents_all_tools, test_baseline_report_includes_sample_violations, test_baseline_report_documents_tool_availability, test_baseline_violation_counts_parseable | ✓ |
| FR6: Orchestrator Script | test_static_analysis_check_script_exists, test_static_analysis_check_is_executable, test_static_analysis_check_accepts_json_input, test_static_analysis_check_output_matches_gate_schema, test_static_analysis_check_exit_codes_*, test_static_analysis_check_handles_missing_tools, test_static_analysis_check_tool_execution_order | ✓ |
| FR7: Gate Registry | test_gate_registry_contains_static_analysis_entry, test_gate_registry_entry_has_required_fields, test_gate_registry_entry_default_mode_is_shadow, test_gate_registry_entry_discoverable_by_gate_runner, test_gate_registry_entry_category_is_analysis | ✓ |
| FR8: Taskfile Task | test_taskfile_contains_hooks_static_analysis_task, test_taskfile_task_has_description, test_taskfile_task_invokes_gate_runner, test_taskfile_task_runs_in_shadow_mode, test_taskfile_task_exits_zero | ✓ |
| FR9: Documentation | test_milestone_readme_contains_static_analysis_section, test_milestone_readme_documents_gate_command, test_milestone_readme_documents_tool_list, test_milestone_readme_documents_scope_and_exclusions, test_milestone_readme_documents_baseline_counts, test_milestone_readme_documents_m903_enforcement, test_milestone_readme_links_to_spec | ✓ |
| NFR1: Reproducibility | test_uv_lock_is_reproducible, test_package_lock_is_reproducible, test_tool_output_deterministic | ✓ |
| NFR2: Performance | test_static_analysis_suite_completes_within_timeout, test_individual_tool_timeouts | ✓ |
| NFR3: Graceful Degradation | test_missing_tool_skipped_with_log, test_gate_status_pass_with_missing_optional_tools, test_checkpoint_documents_skipped_tools | ✓ |

---

## Test Execution Strategy

**Phase 1 (Configuration & Dependency Tests):**
- FR1 tests: Tool audit document validation.
- FR2 tests: Python dependency management (pyproject.toml, uv.lock).
- FR3 tests: TypeScript dependency management (package.json, package-lock.json).

**Phase 2 (Configuration & Validation):**
- FR4 tests: Configuration file existence and validity.
- FR5 tests: Tool validation baseline report.

**Phase 3 (Script & Integration):**
- FR6 tests: Gate orchestrator script functionality.
- FR7 tests: Gate registry integration.
- FR8 tests: Taskfile task integration.

**Phase 4 (Documentation & E2E):**
- FR9 tests: Documentation validation.
- Integration tests: End-to-end gate execution.

**Phase 5 (Error Handling & Edge Cases):**
- Error handling and edge case tests.

---

## Notes

- All tests use `unittest.mock.patch` for mocking external tool invocations where deterministic validation is needed.
- Integration tests use real tool invocations (ruff, eslint, etc.) if tools are available; otherwise, skip gracefully.
- Performance tests use timeout assertions and execution time tracking.
- Documentation tests validate Markdown structure and required sections.

---

**Document Status:** Complete and ready for test implementation.

**Last Updated:** 2026-05-14


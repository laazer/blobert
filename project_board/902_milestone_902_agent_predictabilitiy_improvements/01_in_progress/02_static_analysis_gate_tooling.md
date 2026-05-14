# Title

Mandatory static analysis gate: Python, TypeScript/React, Godot, and duplication tooling

# Context

The MVP mandates a dedicated static analysis gate after implementation agents complete work and before diff-cover, script review, and AC validation. The gate must run deterministic governance checks across the repo's primary languages and cross-cutting duplication analysis.

# Scope

- Python: integrate `ruff`, `mypy`, `bandit`, `vulture`, `import-linter`, `semgrep`, and `wemake-python-styleguide` in a way that is runnable locally and in CI (exact packaging via `uv`/`pyproject.toml` as appropriate).
- React/TypeScript: integrate `eslint`, `typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-sonarjs`, and `eslint-plugin-boundaries` for `asset_generation/web/frontend`.
- Godot: integrate `gdformat` and `gdlint` for GDScript under `scripts/`, `scenes/`, `tests/` (scoped paths consistent with repo conventions).
- Cross-repo: integrate `jscpd` (or equivalent) for duplication analysis with configurable thresholds.

# Acceptance Criteria

- One orchestrated command (or Taskfile task) runs the static analysis bundle and exits non-zero on configured severities.
- Tooling versions are pinned or constrained reproducibly (lockfiles / package.json / uv lock as applicable).
- Each tool's scope is documented (which directories; excludes generated/binary paths per `CLAUDE.md` guardrails).
- The gate emits machine-parseable output paths in the handoff metadata file produced by the framework ticket (or a documented interim file until that lands).

# Agent Execution Prompt

Add the mandatory static analysis gate tooling.

Goal: Create a reproducible static analysis bundle and a single entry command that runs: Python tools on `asset_generation/python` (+ web backend if in scope), ESLint on `asset_generation/web/frontend`, gdformat/gdlint on Godot script paths, and jscpd with sensible defaults.

Constraints:
- Respect repo policy: do not rewrite generated/binary artifacts; exclude `*.glb`, large generated exports unless explicitly included by policy.
- Do not introduce unbounded network fetches in CI.
- Start with configuration that can run in shadow mode if the codebase currently violates rules; enforcement toggles belong in Milestone 903, but this ticket must still wire the tools.

Expected output:
- Config files (`pyproject.toml`, `eslint.config.*`, `.semgrep.yml`, etc.) as needed.
- Documentation of the command in milestone README or `CLAUDE.md` only if required by repo norms (prefer minimal doc; update Milestone 902 README if that is the chosen index).

# Failure Handling Prompt

If blocked, ask:

- What dependency is missing? (tool not installable on macOS/Linux CI)
- What assumption cannot be verified? (Godot CLI availability for gdlint)
- What ambiguity prevents completion? (whether web backend TS should be included now)

# Clarification Prompt

If unclear, ask:

- What specific ambiguity exists about wemake-python-styleguide compatibility with current Ruff configuration?
- What decision needs to be made about semgrep ruleset ownership (local rules vs remote registry)?
- What are the possible interpretations of "before diff-cover" in current `bash .lefthook/scripts/py-tests.sh` ordering?

# Dependencies

- Validation gate framework for multi-agent handoffs (orchestration, routing, remediation)

# Definition of Done

- Static analysis bundle runs locally via one documented command.
- CI/hook integration is either implemented or explicitly deferred with a blocking ticket in Milestone 903, but the local runner must be complete and deterministic.

---

## EXECUTION PLAN

Decomposed into 9 sequential specification tasks. Each task is independently executable once dependencies complete.

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Write detailed technical specification for static analysis gate architecture, tool scope, configuration strategy, and handoff metadata integration. | Spec Agent | Ticket acceptance criteria, gate framework (M902-01 COMPLETE), existing tool configs (Ruff, Taskfile), CLAUDE.md guardrails. | Specification document at `project_board/specs/902_02_static_analysis_gate_spec.md` with FR1–FR7, NFR1–NFR3, risk taxonomy, assumptions/decisions frozen. | None (parallel start) | Specification passes `spec_completeness_check.py --type generic` with all required sections. Decisions on tool bundling, shadow mode, wemake scope documented. Ambiguity resolutions checkpointed. | Assumption 1: wemake is optional/advisory (primary gate is ruff). Assumption 2: semgrep uses conservative local rules (remote registry deferred to M903). Assumption 3: gdlint is optional if Godot CLI unavailable. Assumption 4: Web backend Python shares tool config with asset_generation/python. Assumption 5: jscpd duplication threshold is 10+ lines with generated/binary exclusions. |
| 2 | Identify all existing static analysis tool configurations and integration points; map scope of each tool across codebase directories; document exclusions. | Spec Agent | Codebase file system, `pyproject.toml`, `package.json`, `Taskfile.yml`, `.lefthook/` hook scripts, `CLAUDE.md` guardrails, existing Ruff/Pylint rules. | Configuration audit document with: Python tools (ruff, mypy, bandit, vulture, import-linter, semgrep, wemake) scope/paths, TypeScript tools scope, Godot tools scope, exclusions (*.glb, generated exports), tool compatibility matrix. Checkpoint ambiguity resolutions in run log. | Task 1 | Audit artifact includes tool→directory mapping, conflict notes (ruff vs wemake overlap), and guard-rail compliance per CLAUDE.md. All tool CLI invocation paths documented (pyenv, uv, npm, Godot CLI). | Risk: Some tools may not yet be installed/available on this machine (mypy, bandit, vulture, import-linter, semgrep not found in pyproject.toml). Assumption: Installation via uv/npm/external package managers will be discovered in Task 5. Godot CLI availability in CI is uncertain (optional). |
| 3 | Create/update `asset_generation/python/pyproject.toml` to include all missing Python analysis tools as dev dependencies with pinned/constrained versions. | Spec Agent | Spec from Task 1, current pyproject.toml, tool package availability on PyPI, uv resolver behavior. | Updated `pyproject.toml` with: mypy, bandit, vulture, import-linter, semgrep, wemake-python-styleguide added to `[project.optional-dependencies].dev`. Version constraints documented (e.g., mypy>=1.8, bandit>=1.7.5). Rationale for each tool version choice in checkpoint. uv.lock regenerated (deterministic). | Task 1, Task 2 | All tools installable via `cd asset_generation/python && uv sync --extra dev` without network errors or version conflicts. `uv.lock` is regenerated and reproducible. No circular dependencies introduced. All pre-existing dev dependencies remain compatible. | Assumption: All tools available on PyPI and compatible with Python 3.11. Risk: Some tools may have incompatible transitive dependencies. Assumption: Version ranges allow for security patches without breaking changes. |
| 4 | Create configuration files for tools: `asset_generation/python/.semgrep.yml` (local rules), `asset_generation/web/frontend/.eslintrc` or `eslint.config.js`, root-level `jscpd.json`, optional `.gdlintrc` or Godot invocation wrapper. | Spec Agent | Spec from Task 1, audit from Task 2, tool-specific documentation, repo conventions. | Configuration files with clear scope, exclusions, and rule sets: `.semgrep.yml` (local rules for security/style), `eslint.config.js` or `.eslintrc.json` (React hooks, boundaries, sonarjs), `jscpd.json` (duplication thresholds, excludes *.glb and generated paths). Optional Godot config documented. All configs reference CLAUDE.md guardrails. | Task 1, Task 2 | Configs are syntactically valid, parseable by respective tools, and respect exclusions (no analysis of generated artifacts). Each tool can be invoked locally on target paths without errors. Config files follow project conventions (minimal, source-backed). | Assumption: ESLint/TypeScript tools install via npm in asset_generation/web/frontend/package.json. Assumption: Godot tools (gdformat, gdlint) are optional or external (not in scope for initial uv/npm lockfiles). Risk: Config syntax varies widely per tool; errors will be caught in Task 6 validation. |
| 5 | Update `asset_generation/web/frontend/package.json` to include ESLint plugins and TypeScript analysis tools with pinned versions. | Spec Agent | Spec from Task 1, current package.json, npm registry availability, tool compatibility. | Updated `package.json` with eslint, typescript-eslint, eslint-plugin-react-hooks, eslint-plugin-sonarjs, eslint-plugin-boundaries in devDependencies. `package-lock.json` (or npm.lock) regenerated (deterministic). Version constraints documented. | Task 1, Task 2 | All tools installable via `cd asset_generation/web/frontend && npm install` without errors. package-lock.json is regenerated and reproducible. No conflicts with existing dev dependencies (Vite, Vitest, React, etc.). | Assumption: npm is available and version 8+. Assumption: All plugins compatible with target TypeScript/ESLint versions. Risk: ESLint ecosystem version drift; compatibility with monorepo tooling (Vite, etc.) must be verified. |
| 6 | Validate all tool configurations by running each tool against target paths locally; document any codebase violations in shadow mode and capture baseline violation counts. | Spec Agent | Configs from Task 4, Tool installations from Tasks 3 & 5, repo codebase. | Tool validation report with: ruff check output (E9, F, I on asset_generation/python), mypy, bandit, vulture, import-linter, semgrep baseline violation counts (shadow mode, no enforcement). ESLint on `asset_generation/web/frontend` baseline counts. jscpd duplication report. Godot tools (if available) baseline. Report stored in `project_board/specs/902_02_tool_baseline_report.md`. Checkpoint any tool unavailability with fallback strategy. | Task 3, Task 4, Task 5 | All available tools execute without crashing. Violation counts and severity distribution documented. Any tool that cannot be invoked is flagged with a checkpoint decision (skip vs defer to M903 task). Baselines are deterministic and reproducible. Report includes all tool versions and CLI invocations used. | Risk: Codebase may have high violation counts (especially legacy code); shadow mode prevents CI failure. Assumption: ruff, mypy, eslint, jscpd are installable; others (bandit, vulture, import-linter, semgrep, gdformat, gdlint) may require external installs or deferral. |
| 7 | Create a unified gate entry point script `ci/scripts/static_analysis_check.py` (or bash equivalent) that orchestrates all tool invocations, aggregates results, and outputs structured JSON matching gate schema (from M902-01). | Spec Agent | Gate runner schema (from M902-01 framework), specs from Tasks 1 & 4, tool configurations. | Executable script at `ci/scripts/static_analysis_check.py` (or `.sh`) that: 1) runs ruff, mypy, bandit, vulture, import-linter, semgrep, wemake on asset_generation/python; 2) runs eslint on asset_generation/web/frontend; 3) runs jscpd on repo root; 4) invokes Godot tools if available; 5) aggregates violations into JSON matching gate-result schema; 6) exits 0 (shadow) or 1 (violations in blocking mode, deferred to M903). Script is deterministic and environment-agnostic. | Task 1, Task 4, Task 5, Task 6 (baseline report validates tool paths). | Script executes without errors on local machine and CI. JSON output matches gate schema (status, violations[], remediation_hints[], artifacts[]). All tool paths respect CLAUDE.md exclusions. Script properly handles missing tool availability (skip vs fail). Documentation of script flags in script header (--mode shadow/blocking, --output-dir, etc.). | Assumption: Script can aggregate results from heterogeneous tools (different JSON/text outputs). Assumption: Gate runner framework from M902-01 is available and stable (`ci/scripts/gate_runner.py`). Risk: Tool output parsing fragile; requires robust error handling. |
| 8 | Register the static analysis gate in `ci/scripts/gate_registry.json` with shadow mode default; document gate invocation in Milestone 902 README. | Spec Agent | gate_registry.json structure (from M902-01), gate script from Task 7, Milestone README location. | Updated gate_registry.json with entry: `"static_analysis_check": { "module": "static_analysis_check", "mode": "shadow", "category": "analysis", "description": "..."}`. Updated Milestone 902 README with: gate command, tool list, exclusion policy, baseline violation counts, mode toggle instructions. | Task 7, M902-01 (framework COMPLETE). | Gate is discoverable by gate runner (`python ci/scripts/gate_runner.py static_analysis_check ...`). README documents gate invocation and link to spec. All tool scope/exclusion policy visible to operators. | Low risk. Assumption: gate_registry.json follows existing entry pattern. |
| 9 | Create or update a Taskfile.yml task `hooks:static-analysis` that invokes the gate with shadow mode; ensure it is optional/advisory in current workflow and document deferral of enforcement to M903. | Spec Agent | Taskfile.yml structure, gate script from Task 7, gate runner from M902-01. | New Taskfile task: `hooks:static-analysis` that runs `python ci/scripts/gate_runner.py static_analysis_check --mode shadow --upstream-agent Implementation --downstream-agent Spec --ticket-id M902-02`. Task is discoverable as `task hooks:static-analysis`. Documentation in Taskfile or README explains that enforcement (exit 1 on violations) is deferred to M903. | Task 7, Task 8. | Task executes without error in shadow mode. No CI breakage. Developers can run `task hooks:static-analysis` locally to preview analysis results. Enforcement path to M903 is clear and traceable. | Low risk. Assumption: Taskfile syntax unchanged. Enforcement toggle deferred; this task documents the deferral path. |

---

## PLANNING NOTES

**Framework Dependency Satisfied:** M902-01 (Validation gate framework) is COMPLETE. Gate runner (`ci/scripts/gate_runner.py`), registry system, and JSON schema are stable and tested (220 tests, all PASS).

**Tool Ecosystem Assessment:**
- **Python:** ruff (existing, E9/F/I rules configured), mypy (new), bandit, vulture, import-linter, semgrep, wemake (all new) require pyproject.toml additions.
- **TypeScript/React:** eslint, typescript-eslint, plugins all new to package.json; install via npm.
- **Godot:** gdformat, gdlint are external tools; optional pending Godot CLI availability.
- **Duplication:** jscpd (new), install via npm root or dedicated npm package.

**Scope Exclusions (Per CLAUDE.md):**
- `*.glb` (model files)
- Large generated exports (images, baked assets)
- `.venv/`, `node_modules/`
- `reference_projects/` (read-only)

**Shadow Mode Strategy:**
- Tools run and report violations but do not fail CI.
- Enforcement (exit 1) is deferred to M903.
- Developers can use `task hooks:static-analysis` to preview violations locally.
- Baselines are documented so M903 can set grandfathering policies.

**Risk Mitigations:**
- Task 2 audit identifies tool availability before commits.
- Task 6 baseline validation ensures tools execute without crashes.
- Task 7 script handles missing tool gracefully (skip or log).
- Checkpoint protocol captures tool incompatibilities and deferral decisions.

---

## WORKFLOW STATE

| Field | Value |
|-------|-------|
| Stage | IMPLEMENTATION_GENERALIST |
| Revision | 5 |
| Last Updated By | Test Breaker Agent |
| Next Responsible Agent | Implementation Generalist |
| Status | Proceed |
| Validation Status | TEST_BREAK complete. 72 behavioral tests + 100+ adversarial tests. Adversarial suite covers: (1) configuration file corruption & parsing edge cases, (2) gate registry entry mutations, (3) exclusion pattern correctness, (4) gate script structure weaknesses, (5) JSON schema violations, (6) tool invocation & output parsing edge cases, (7) taskfile parsing edge cases, (8) reproducibility mutations, (9) performance degradation, (10) order dependency & concurrency, (11) boundary conditions, (12) assumption validation. Test suite syntax validated. Checkpoint log at `project_board/checkpoints/M902-02/2026-05-14T21-00-00Z-test-break.md`. 5 checkpoint decisions logged (CP-1 through CP-5). 6 remaining gaps identified and documented. Ready for IMPLEMENTATION stage. |
| Blocking Issues | None |

## NEXT ACTION

**Responsible Agent:** Implementation Generalist

**Input Schema:**
```json
{
  "ticket_path": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/02_static_analysis_gate_tooling.md",
  "spec_path": "project_board/specs/902_02_static_analysis_gate_spec.md",
  "test_suite_path": "tests/ci/test_static_analysis_gate.py",
  "adversarial_test_suite_path": "tests/ci/test_static_analysis_gate_adversarial.py",
  "checkpoint_log": "project_board/checkpoints/M902-02/2026-05-14T21-00-00Z-test-break.md"
}
```

**Required Output:**
1. Implementation of static analysis gate orchestrator script (`ci/scripts/gates/static_analysis_check.py`).
2. Configuration files for all tools (`.semgrep.yml`, `eslint.config.js`, `jscpd.json`, pyproject.toml sections).
3. Dependency management updates (`asset_generation/python/pyproject.toml`, `asset_generation/web/frontend/package.json`).
4. Gate registry entry (`ci/scripts/gate_registry.json` update).
5. Taskfile task definition (`Taskfile.yml` update).
6. Tool audit and baseline report documents.
7. Milestone 902 README documentation.

**Success Criteria:**
- All 72 behavioral tests PASS.
- 80%+ of adversarial tests PASS (some may indicate expected missing edge cases).
- No regression in existing test suites.
- Configuration files valid and parseable.
- Gate output conforms to JSON schema.

**Risks to address (per adversarial suite):**
- Tool availability checking (missing tools must gracefully skip).
- Config validation before parsing.
- JSON schema validation on output.
- Type checking on violations array.
- Boundary value handling (line numbers, thresholds).
- Tool output parsing robustness (mixed text/JSON, malformed output).

**Status:** Proceed to IMPLEMENTATION_GENERALIST stage.

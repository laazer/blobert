# M902-02 Static Analysis Gate Specification

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/02_static_analysis_gate_tooling.md`

**Status:** SPECIFICATION (proceeding to TEST_DESIGN)

**Revision:** 1

**Date:** 2026-05-14

---

## Executive Summary

This specification defines the mandatory static analysis gate that runs deterministic governance checks across Python, TypeScript/React, Godot, and cross-repo duplication analysis. The gate integrates into the blobert multi-agent workflow as a discrete post-implementation validation step before diff-cover and script review.

**Key objectives:**
1. Establish reproducible tool configurations (ruff, mypy, bandit, vulture, import-linter, semgrep, wemake, eslint, jscpd).
2. Create a unified orchestrator script that runs all tools, aggregates results, and emits structured JSON matching the gate schema from M902-01.
3. Register the gate in the gate registry and wire it into the workflow via Taskfile tasks (shadow mode, non-blocking for M902).
4. Document scope, exclusions, and baselines so M903 can enforce with grandfathering policies.

---

## Requirement Grouping & Acceptance Criteria

### Requirement FR1: Tool Discovery and Configuration Inventory

#### 1. Spec Summary

**Description:** Conduct a comprehensive audit of all static analysis tools (Python, TypeScript/React, Godot, and duplication detection) currently installed or available on the system. Map each tool's scope, invocation method, configuration file locations, and exclusion rules. Document compatibility with target languages/frameworks.

**Constraints:**
- Audit must cover: ruff (existing), mypy, bandit, vulture, import-linter, semgrep, wemake-python-styleguide, eslint (+ plugins), gdformat, gdlint, jscpd.
- All existing tool configurations (ruff in pyproject.toml, etc.) must be preserved and integrated, not replaced.
- Configuration paths must follow repo conventions (pyproject.toml for Python, package.json for npm, .eslintrc or eslint.config.js for TypeScript, .semgrep.yml for semgrep).
- Godot tools may be external; availability depends on Godot CLI presence.

**Assumptions:** 
- All Python tools are available on PyPI or via package managers.
- ESLint ecosystem tools are available via npm.
- jscpd is installable via npm or as standalone utility.
- Godot CLI is optional; skip if unavailable.

**Scope:** Applies to `asset_generation/python`, `asset_generation/web/backend`, `asset_generation/web/frontend`, `scripts/`, `scenes/`, `tests/` (Godot), and repo root (duplication).

#### 2. Acceptance Criteria

- **AC1.1** An audit document exists at `project_board/specs/902_02_tool_audit.md` mapping each tool to: CLI invocation method, config file path(s), target directories, exclusion/ignore patterns, and version constraints.
- **AC1.2** Existing ruff configuration in `asset_generation/python/pyproject.toml` is documented with no breaking changes.
- **AC1.3** All tool compatibility notes (e.g., Python 3.11+, Node 18+, Godot 4.x CLI) are listed with fallback strategies for missing tools.
- **AC1.4** Exclusion paths per CLAUDE.md (*.glb, generated exports, .venv, node_modules, reference_projects) are enumerated per tool.
- **AC1.5** Tool invocation examples (full CLI flags) are documented for each tool.

#### 3. Risk & Ambiguity Analysis

**Risks:**
- Some tools may not be installed on the CI agent; dependency on external tool availability could block gate execution. Mitigation: graceful skip/log with checkpoint decision.
- Godot CLI may not be available in CI; gdformat/gdlint integration is uncertain. Mitigation: optional tool, skip if unavailable.
- Conflicting rules between ruff and wemake (e.g., line length, import order). Mitigation: both run independently; wemake is advisory in M902.
- jscpd configuration may have non-obvious duplication threshold defaults. Mitigation: explicit threshold documented (10+ lines).

**Ambiguities:**
- None identified; audit is straightforward inventory task.

#### 4. Clarifying Questions

None at this stage; audit is factual discovery.

---

### Requirement FR2: Python Tool Dependency Management

#### 1. Spec Summary

**Description:** Update `asset_generation/python/pyproject.toml` to include all required Python static analysis tools as dev dependencies with explicit version constraints. Ensure reproducibility via uv lock.

**Constraints:**
- Tools: mypy, bandit, vulture, import-linter, semgrep, wemake-python-styleguide (in addition to existing ruff, pylint, pytest, diff-cover).
- Version constraints must be pinned or sufficiently constrained to avoid version drift (e.g., mypy>=1.8,<2.0).
- All dev dependencies must install cleanly with Python 3.11 and produce a reproducible `uv.lock`.
- No circular dependencies or transitive conflicts.
- Existing dependencies (pytest, pytest-asyncio, pytest-cov, diff-cover, fastapi, httpx, pydantic-settings, sse-starlette, chardet, ruff, pylint, fastmcp) remain unchanged.

**Assumptions:**
- All tools listed are available on PyPI.
- Python 3.11+ is the target runtime.
- uv is the package manager (see Taskfile.yml and CLAUDE.md).
- wemake-python-styleguide is installable and compatible with current flake8/plugins ecosystem.

**Scope:** Updates `asset_generation/python/pyproject.toml` [project.optional-dependencies].dev section only.

#### 2. Acceptance Criteria

- **AC2.1** `asset_generation/python/pyproject.toml` contains entries for mypy, bandit, vulture, import-linter, semgrep, and wemake-python-styleguide in [project.optional-dependencies].dev.
- **AC2.2** Version constraints are documented (e.g., mypy>=1.8,<2.0) with rationale in a checkpoint decision if non-standard.
- **AC2.3** Running `cd asset_generation/python && uv sync --extra dev` produces no errors and generates a valid `uv.lock`.
- **AC2.4** No existing dev dependencies are downgraded or made incompatible.
- **AC2.5** `uv.lock` is committed (deterministic artifact for CI reproducibility).

#### 3. Risk & Ambiguity Analysis

**Risks:**
- wemake-python-styleguide may have transitive dependencies on older versions of flake8, pycodestyle, or other packages that conflict with ruff or pylint. Mitigation: test `uv sync --extra dev` in isolation; if conflict occurs, checkpoint the conflict and defer wemake to M903.
- Some tools (bandit, vulture, semgrep) are less commonly used and may have API/CLI breaking changes between major versions. Mitigation: use sufficiently loose constraints (e.g., bandit>=1.7.5,<2.0) and test baseline in Task 6.
- mypy may require additional type stubs for Pillow, Pydantic, or other dependencies. Mitigation: mypy runs with `--ignore-missing-imports` if stubs are unavailable.

**Ambiguities:**
- None identified; dependency versions are factual installation constraints.

#### 4. Clarifying Questions

None; dependency management is straightforward.

---

### Requirement FR3: TypeScript/React Tool Dependency Management

#### 1. Spec Summary

**Description:** Update `asset_generation/web/frontend/package.json` to include ESLint, TypeScript ESLint plugins, React-specific rules, and boundary enforcement tools. Ensure reproducibility via package-lock.json.

**Constraints:**
- Tools: eslint, @typescript-eslint/eslint-plugin, @typescript-eslint/parser, eslint-plugin-react-hooks, eslint-plugin-sonarjs, eslint-plugin-boundaries.
- Version constraints must be pinned or sufficiently constrained (e.g., eslint>=9.0,<10.0).
- Compatibility with existing dependencies: React 18.3+, TypeScript 5.5+, Vite 5.4+, Vitest 2.1+.
- All tools must install cleanly via `npm install` and produce a reproducible `package-lock.json`.
- No breaking changes to existing build, dev, or test workflows.

**Assumptions:**
- npm 8+ is available in CI/local environment.
- All ESLint plugins are compatible with ESLint 9.x and @typescript-eslint ecosystem.
- Node 18+ is the target runtime.

**Scope:** Updates `asset_generation/web/frontend/package.json` devDependencies section only.

#### 2. Acceptance Criteria

- **AC3.1** `asset_generation/web/frontend/package.json` contains entries for eslint, @typescript-eslint/eslint-plugin, @typescript-eslint/parser, eslint-plugin-react-hooks, eslint-plugin-sonarjs, eslint-plugin-boundaries.
- **AC3.2** Version constraints are documented with compatibility notes.
- **AC3.3** Running `cd asset_generation/web/frontend && npm install` produces no errors and generates a valid `package-lock.json`.
- **AC3.4** No existing devDependencies (including @vitejs/plugin-react, TypeScript, Vite, Vitest) are downgraded or made incompatible.
- **AC3.5** `package-lock.json` is committed (deterministic artifact for CI reproducibility).

#### 3. Risk & Ambiguity Analysis

**Risks:**
- ESLint 9.x ecosystem is relatively new; some plugins may have compatibility issues. Mitigation: test `npm install` in isolation; if conflicts occur, checkpoint and defer non-critical plugins to M903.
- eslint-plugin-boundaries requires explicit configuration to define module boundaries; misconfiguration can cause noise. Mitigation: configuration deferred to FR4 with conservative defaults.
- React 18.3 + modern ESLint may flag different patterns than earlier versions; codebase may have pre-existing violations. Mitigation: shadow mode in FR7 allows advisory reporting without blocking CI.

**Ambiguities:**
- None identified; dependency versions are factual.

#### 4. Clarifying Questions

None; dependency management is straightforward.

---

### Requirement FR4: Configuration Files for All Tools

#### 1. Spec Summary

**Description:** Create or update configuration files for all static analysis tools, defining scope, exclusions, and rule sets. Configurations must respect CLAUDE.md guardrails and be deterministic.

**Constraints:**
- **Python tools** configuration:
  - ruff: update `asset_generation/python/pyproject.toml` [tool.ruff] to include mypy, bandit, vulture, import-linter, semgrep scopes (or keep ruff focused on E9/F/I and invoke other tools separately).
  - mypy: create `asset_generation/python/pyproject.toml` [tool.mypy] with target Python 3.11, strict mode, excludes .venv.
  - bandit: create `asset_generation/python/.bandit` or use pyproject.toml [tool.bandit] with security severity thresholds.
  - vulture: create `asset_generation/python/pyproject.toml` [tool.vulture] or `.vulture` file.
  - import-linter: create `asset_generation/python/.import-linter` with module graph rules.
  - semgrep: create `asset_generation/python/.semgrep.yml` with local hardcoded rules (no remote registry in M902).
  - wemake: create `asset_generation/python/.wemake-python-styleguide.yml` (or use flake8 config) with style rules; advisory mode.

- **TypeScript/React configuration**:
  - eslint: create `asset_generation/web/frontend/eslint.config.js` or `.eslintrc.json` with rules for React, TypeScript, hooks, sonarjs, boundaries.
  - Exclude node_modules, dist, build.

- **Cross-repo duplication**:
  - jscpd: create `jscpd.json` at repo root with duplication threshold (10+ lines), exclusion patterns (*.glb, node_modules, .venv, reference_projects, generated exports).

- **Godot (optional)**:
  - gdformat: optional configuration if Godot CLI available; scope GDScript in scripts/, scenes/, tests/.
  - gdlint: optional configuration if Godot CLI available.

- **Exclusions apply globally**:
  - *.glb (binary model files)
  - *.png, *.jpg (large generated exports, baked assets)
  - .venv/, node_modules/ (dependency directories)
  - reference_projects/ (read-only reference)
  - Generated asset pipeline outputs (from asset_generation/python/animated_exports, etc.)

**Assumptions:**
- Configuration syntax is standard per tool (TOML for pyproject.toml, JSON for eslint, YAML for semgrep, etc.).
- No custom tool plugins or extensions are required for M902.
- semgrep local rules are conservative (security + style only; no advanced domain rules).

**Scope:** Creates/updates config files across `asset_generation/python/`, `asset_generation/web/frontend/`, repo root, and optional Godot integration points.

#### 2. Acceptance Criteria

- **AC4.1** `asset_generation/python/pyproject.toml` contains [tool.mypy], [tool.bandit], [tool.vulture] sections with clear scope and exclusions.
- **AC4.2** `asset_generation/python/.semgrep.yml` exists with local hardcoded security/style rules; no remote registry calls.
- **AC4.3** `asset_generation/python/.import-linter` or equivalent defines module graph constraints (if applicable).
- **AC4.4** `asset_generation/web/frontend/eslint.config.js` (or `.eslintrc.json`) defines React, TypeScript, hooks, sonarjs, boundaries rules.
- **AC4.5** `jscpd.json` at repo root defines 10+ line threshold and exclusion patterns per CLAUDE.md guardrails.
- **AC4.6** All configs are syntactically valid (parseable by respective tools without errors).
- **AC4.7** All configs reference exclusion paths per CLAUDE.md; no analysis of *.glb, generated exports, .venv, node_modules, reference_projects.
- **AC4.8** Godot configuration files (if created) are documented with availability fallback strategy.

#### 3. Risk & Ambiguity Analysis

**Risks:**
- semgrep `.semgrep.yml` must be carefully curated to avoid false positives; too strict rules cause advisory reporting overhead. Mitigation: conservative rules initially (security + basic style); expand in M903.
- eslint boundaries configuration complexity; misconfigured modules may cause excessive violations. Mitigation: start with permissive boundaries; tighten in M903.
- bandit may flag legitimate code patterns (e.g., subprocess calls, hardcoded strings); severity tuning is per-organization. Mitigation: shadow mode allows tuning without CI breakage.
- jscpd false positives on repeated code patterns (e.g., similar test fixtures, repeated API error handling). Mitigation: 10-line threshold reduces noise; M903 can refine.

**Ambiguities:**
- None identified; configuration is deterministic per tool docs.

#### 4. Clarifying Questions

None; configuration is straightforward mapping of tool options.

---

### Requirement FR5: Tool Validation and Baseline Report

#### 1. Spec Summary

**Description:** Run all configured static analysis tools against target codebase directories. Validate that each tool executes without crashing. Capture baseline violation counts and severity distributions. Document any tool unavailability with fallback decisions.

**Constraints:**
- Tools must be tested against actual codebase paths (not mock fixtures).
- Baseline report must include: tool version, CLI invocation, target directories, violation counts by severity (ERROR, WARNING, INFO), and sample violations (top 5 per tool).
- Shadow mode: tools run but do not cause CI failure; violations are logged for review.
- Tool unavailability (e.g., gdformat not in PATH): checkpoint the decision (skip vs defer to M903), do not fail the spec.
- Baseline violation counts are used by M903 for grandfathering policies.

**Assumptions:**
- Tools installed in prior requirements are available.
- Codebase may have pre-existing violations; shadow mode allows reporting without enforcement.
- Tool output parsing is deterministic (JSON, XML, or line-delimited text).

**Scope:** Validates Python, TypeScript, Godot, and duplication tools against `asset_generation/python`, `asset_generation/web/frontend`, `scripts/`, `scenes/`, `tests/`, and repo root.

#### 2. Acceptance Criteria

- **AC5.1** Baseline report exists at `project_board/specs/902_02_tool_baseline_report.md` documenting each tool's availability, version, and baseline violation counts.
- **AC5.2** Each available tool has been invoked locally with sample output captured (top 5 violations per tool).
- **AC5.3** Tool availability decisions are checkpointed (e.g., "gdlint: SKIP (Godot CLI not available)" or "mypy: AVAILABLE, 42 errors, 18 warnings").
- **AC5.4** Baseline violation counts per tool are documented for M903 enforcement tuning.
- **AC5.5** All tools that executed successfully produced parseable output (no crashes or timeouts).
- **AC5.6** Report includes all tool versions (`ruff --version`, `npm list eslint`, etc.).

#### 3. Risk & Ambiguity Analysis

**Risks:**
- Tool output formats vary; parsing may be fragile (JSON, XML, plain text). Mitigation: Task 7 script uses fallback parsers; if a tool's output cannot be parsed, log as "unparseable" and defer to M903.
- Some tools may timeout on large codebases (semgrep, bandit); baseline report needs to document timeout thresholds. Mitigation: set reasonable timeouts (e.g., 60s per tool); if timeout, checkpoint and skip.
- Baseline counts may be high (legacy code violations); this is expected and documented for M903. No action in M902.

**Ambiguities:**
- How long is acceptable for tool runs? Assumption: ~60s per tool, parallel execution where safe.

#### 4. Clarifying Questions

None; baseline reporting is factual validation.

---

### Requirement FR6: Gate Orchestrator Script

#### 1. Spec Summary

**Description:** Create `ci/scripts/static_analysis_check.py` (or bash equivalent) that orchestrates all static analysis tool invocations, aggregates results, and outputs structured JSON matching the gate schema from M902-01 (gate_runner.py).

**Constraints:**
- Script must be executable via: `python ci/scripts/static_analysis_check.py` or invoked by gate_runner.py.
- Input: JSON dict with optional parameters (e.g., { "mode": "shadow", "output_dir": "./gate-results", "upstream_agent": "Implementation", "downstream_agent": "Spec", "ticket_id": "M902-02" }).
- Output: JSON object matching gate schema:
  ```json
  {
    "version": "1.0",
    "status": "PASS" | "FAIL",
    "gate": "static_analysis_check",
    "upstream_agent": "<name>",
    "downstream_agent": "<name>",
    "timestamp": "<ISO 8601>",
    "ticket_id": "<id>",
    "mode": "shadow" | "blocking",
    "_shadow_mode": true | false,
    "artifacts": [
      { "path": "<file>", "sha256": "<hash>" }
    ],
    "duration_ms": <int>,
    "message": "<summary>",
    "violations": [
      {
        "file": "<path>",
        "line": <int>,
        "rule": "<tool>:<rule_id>",
        "message": "<details>",
        "severity": "ERROR" | "WARNING" | "INFO",
        "tool": "<tool_name>"
      }
    ],
    "remediation_hints": [
      "<hint 1>",
      "<hint 2>"
    ]
  }
  ```
- Exit codes: 0 (PASS or shadow mode), 1 (FAIL in blocking mode), 2 (usage error).
- Tool execution order: ruff → mypy → bandit → vulture → import-linter → semgrep → wemake → eslint → jscpd → gdformat (optional).
- Handles missing tools gracefully (skip with log, do not crash).
- All tool output parsing is robust (handles JSON, XML, plain text; if unparseable, log as "parse_error" violation).

**Assumptions:**
- Gate runner (M902-01) framework is stable and script can be called by gate_runner.py.
- Output directory is writable (default: `./gate-results` in cwd or override via input).
- Script has access to all configured tools (via PATH or virtual environments).
- Python 3.11+ is the target runtime.

**Scope:** Single entry point for all static analysis tooling; used by gate_runner.py and Taskfile tasks.

#### 2. Acceptance Criteria

- **AC6.1** Script exists at `ci/scripts/static_analysis_check.py` and is executable.
- **AC6.2** Script accepts JSON input (from gate_runner.py or Taskfile).
- **AC6.3** Script runs all configured tools in sequence (or parallel where safe) and aggregates results.
- **AC6.4** Output JSON matches gate schema (all required fields present, types correct).
- **AC6.5** Exit codes are correct: 0 on PASS/shadow, 1 on FAIL/blocking, 2 on usage error.
- **AC6.6** Script handles missing tools gracefully (skip with log, continue to next tool).
- **AC6.7** Tool output parsing is robust (no crashes on malformed output).
- **AC6.8** Total execution time is documented (target: <5 min for full suite).

#### 3. Risk & Ambiguity Analysis

**Risks:**
- Tool output parsing fragility; some tools may have non-standard output. Mitigation: use tool-specific parsers (e.g., ruff --output-format=json); if a tool doesn't support JSON output, use text parsing with error handling.
- Parallel tool execution may cause race conditions (e.g., semgrep creating temp files). Mitigation: run sequentially in M902; parallelize in M903 if performance needed.
- Script invoked by gate_runner.py must define a `run(inputs: dict) -> dict` function; unclear if script is directly callable or if a wrapper module is needed. Mitigation: script defines `run()` function and also has CLI fallback for direct invocation.

**Ambiguities:**
- None identified; script structure is defined by gate runner contract.

#### 4. Clarifying Questions

None; orchestration is straightforward integration of prior requirements.

---

### Requirement FR7: Gate Registry Integration

#### 1. Spec Summary

**Description:** Register the static analysis gate in `ci/scripts/gate_registry.json` with metadata (name, module, required inputs, default mode, description, category). Wire the gate into Milestone 902 orchestration.

**Constraints:**
- Registry entry format:
  ```json
  {
    "name": "static_analysis_check",
    "module": "static_analysis_check",
    "required_inputs": ["mode"],
    "default_mode": "shadow",
    "description": "Deterministic static analysis bundle for Python, TypeScript, Godot, and duplication detection.",
    "category": "analysis"
  }
  ```
- Mode default is "shadow" (non-blocking) for M902; enforcement toggle to M903.
- Gate must be discoverable by gate_runner.py: `python ci/scripts/gate_runner.py static_analysis_check ...`.

**Assumptions:**
- gate_registry.json follows existing format (JSON array of gate entries).
- gate_runner.py is stable and does not require changes.

**Scope:** Single registry entry update; no gate_runner.py changes.

#### 2. Acceptance Criteria

- **AC7.1** `ci/scripts/gate_registry.json` contains an entry for `"static_analysis_check"` with all required fields.
- **AC7.2** Gate is discoverable: `python ci/scripts/gate_runner.py static_analysis_check --help` or similar works.
- **AC7.3** Default mode is "shadow" (non-blocking).
- **AC7.4** Category is "analysis".
- **AC7.5** All fields in registry entry are documented and match gate runner contract.

#### 3. Risk & Ambiguity Analysis

**Risks:**
- Registry format may differ from expected; malformed entry could cause gate runner to fail. Mitigation: validate entry format before committing; run gate_runner.py with test inputs to verify registration.

**Ambiguities:**
- None identified; registry is simple JSON metadata.

#### 4. Clarifying Questions

None; registration is straightforward entry addition.

---

### Requirement FR8: Taskfile Task Integration

#### 1. Spec Summary

**Description:** Create or update a Taskfile.yml task `hooks:static-analysis` that invokes the gate orchestrator in shadow mode. Task is optional/advisory for developers; documentation clarifies that enforcement is deferred to M903.

**Constraints:**
- Task name: `hooks:static-analysis`.
- Task invocation: `task hooks:static-analysis` (no args required, but allow optional flags).
- Internally invokes: `python ci/scripts/gate_runner.py static_analysis_check --mode shadow --upstream-agent Implementation --downstream-agent Spec --ticket-id M902-02` (or similar).
- Task output is human-readable (summary of violations, remediation hints).
- Task exits 0 (shadow mode is non-blocking); violations are logged but do not fail the task.
- Task is discoverable in `task --list` output with description.

**Assumptions:**
- Taskfile.yml exists and follows existing task structure (see current tasks in Taskfile.yml).
- gate_runner.py is on PATH or invoked via python.

**Scope:** Single task addition to Taskfile.yml; documentation in Taskfile or Milestone 902 README.

#### 2. Acceptance Criteria

- **AC8.1** Taskfile.yml contains a task `hooks:static-analysis` with description and command.
- **AC8.2** Task executes `python ci/scripts/gate_runner.py static_analysis_check --mode shadow ...` or equivalent.
- **AC8.3** Task exits 0 (non-blocking) even if violations are found.
- **AC8.4** Task output includes summary of tool results (PASS/FAIL, violation counts).
- **AC8.5** Task is listed in `task --list` output.
- **AC8.6** Documentation (in Taskfile or README) clarifies that enforcement is deferred to M903.

#### 3. Risk & Ambiguity Analysis

**Risks:**
- Task may not inherit environment variables (e.g., PATH for tool binaries). Mitigation: task explicitly sets environment (e.g., PATH=$(.venv/bin:$PATH) if needed).
- Task output may be verbose (many violations); terminal output could be overwhelming. Mitigation: gate_runner.py provides `--quiet` flag (future) or task redirects to file (optional).

**Ambiguities:**
- Should task accept arguments (e.g., `task hooks:static-analysis -- --mode blocking`)? Assumption: task supports CLI_ARGS passthrough per Taskfile.yml convention (e.g., `{{.CLI_ARGS}}`).

#### 4. Clarifying Questions

None; task integration is straightforward Taskfile entry.

---

### Requirement FR9: Documentation and Milestone 902 README Update

#### 1. Spec Summary

**Description:** Document the static analysis gate in Milestone 902 README, including: gate command, tool list, scope/exclusion policy, baseline violation counts from Task 5, and enforcement toggle path to M903.

**Constraints:**
- Documentation must be in Milestone 902 README or a link from it.
- Must include: command to run locally (`task hooks:static-analysis`), tool list with versions, scope, exclusion policy, baseline counts, and M903 enforcement plan.
- Must reference this spec (`project_board/specs/902_02_static_analysis_gate_spec.md`) for detailed requirements.
- Must clarify that enforcement (exit 1 on violations) is deferred to M903.

**Assumptions:**
- Milestone 902 README exists and is maintained (confirmed: yes, at `project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md`).

**Scope:** Documentation updates only; no code changes.

#### 2. Acceptance Criteria

- **AC9.1** Milestone 902 README contains a section "Static Analysis Gate" or similar.
- **AC9.2** Section includes gate command: `task hooks:static-analysis` and `python ci/scripts/gate_runner.py static_analysis_check ...`.
- **AC9.3** Tool list with versions is documented (from baseline report, Task 5).
- **AC9.4** Scope and exclusion policy (CLAUDE.md guardrails) are documented.
- **AC9.5** Baseline violation counts per tool are listed (from Task 5 report).
- **AC9.6** Enforcement plan for M903 is documented (blocking mode, grandfathering policies).
- **AC9.7** Link to detailed spec (`project_board/specs/902_02_static_analysis_gate_spec.md`) is provided.

#### 3. Risk & Ambiguity Analysis

**Risks:**
- Documentation may become stale if baseline counts are not updated. Mitigation: baseline report is source of truth; README links to it for current counts.

**Ambiguities:**
- None identified; documentation is straightforward summary.

#### 4. Clarifying Questions

None; documentation is informational.

---

## Non-Functional Requirements

### NFR1: Reproducibility

**Description:** All tool configurations and dependency definitions must be deterministic and reproducible across runs.

**Acceptance Criteria:**
- `uv.lock` and `package-lock.json` are committed and used for reproducible installs.
- Tool versions are pinned or constrained (no `*` or `latest` version specs).
- Configs are version-controlled and immutable (no external registry fetches; semgrep uses local rules only).
- CI and local runs produce identical tool outputs (same violations, same order where deterministic).

---

### NFR2: Performance

**Description:** Tool execution must complete within reasonable time bounds for local development and CI.

**Acceptance Criteria:**
- Full static analysis suite completes in <5 minutes on a standard developer machine.
- Individual tool execution: ruff <30s, eslint <20s, jscpd <30s, others <30s each.
- Timeouts are documented; if a tool times out, gracefully skip and log warning.

---

### NFR3: Graceful Degradation

**Description:** Missing tools must not block gate execution; instead, skip gracefully and log availability status.

**Acceptance Criteria:**
- If a tool is not installed, gate logs "SKIP: <tool_name> (not available)" and continues.
- Gate status remains "PASS" if missing tools do not affect core gate result.
- Checkpoint logs document all skipped tools for M903 enforcement tuning.

---

## Risk Taxonomy

### High-Priority Risks

1. **Tool Installation Conflicts (Python)**
   - Risk: wemake-python-styleguide has transitive dependencies that conflict with ruff or existing dev dependencies.
   - Mitigation: Test `uv sync --extra dev` in isolated environment; if conflict occurs, checkpoint and defer wemake to M903.
   - Owner: Spec Agent (Task 3), Test Designer (Task 6 validation).

2. **Tool Output Parsing Fragility**
   - Risk: Tool output formats vary; script parsers may fail on unexpected format variants.
   - Mitigation: Use tool-native JSON output where available; fallback to text parsing with robust error handling.
   - Owner: Implementer (Task 7).

3. **Godot CLI Unavailability**
   - Risk: gdformat and gdlint require Godot CLI, which may not be available in CI or on all machines.
   - Mitigation: Make tools optional; graceful skip if unavailable. Document fallback strategy.
   - Owner: Spec Agent (Task 2 audit), Implementer (Task 7).

4. **Codebase Pre-Existing Violations**
   - Risk: Baseline violation counts may be high; developers may be overwhelmed by noise.
   - Mitigation: Shadow mode (non-blocking) in M902; M903 implements grandfathering policies.
   - Owner: Spec Agent (Task 5 baseline report), M903 Implementer.

### Medium-Priority Risks

5. **ESLint Boundaries Configuration Complexity**
   - Risk: eslint-plugin-boundaries configuration is complex; misconfigured modules cause excessive violations.
   - Mitigation: Start with permissive boundaries; tighten in M903.
   - Owner: Spec Agent (Task 4), Implementer (Task 7).

6. **semgrep Local Rule Maintenance**
   - Risk: Local `.semgrep.yml` rules are manually curated; rule drift or false positives over time.
   - Mitigation: Conservative initial rules (security + basic style); expand and tune in M903.
   - Owner: Spec Agent (Task 4), M903 Implementer.

7. **jscpd False Positives**
   - Risk: Duplication detector may flag legitimate repeated patterns (e.g., test fixtures, error handling boilerplate).
   - Mitigation: 10-line threshold reduces noise; M903 can adjust per codebase.
   - Owner: Spec Agent (Task 4), M903 Implementer.

### Low-Priority Risks

8. **Tool Version Drift in CI**
   - Risk: CI environment may install newer tool versions (minor/patch) not pinned in lockfiles.
   - Mitigation: Use lockfiles (uv.lock, package-lock.json); CI pins exact versions.
   - Owner: Implementer (Task 3, Task 5).

---

## Decisions Frozen (Checkpoint Summary)

1. **wemake-python-styleguide scope:** Advisory mode; primary enforcement is ruff. wemake violations logged for M903 baseline.
2. **semgrep ruleset:** Local `.semgrep.yml` with conservative hardcoded rules; remote registry deferred to M903.
3. **Godot tools:** Optional; skip if unavailable. Fallback strategy checkpointed in Task 2.
4. **Web backend Python:** Shares Python tool config with asset_generation/python.
5. **jscpd threshold:** 10+ lines (default); exclusions per CLAUDE.md guardrails.
6. **Orchestration:** Both Python script (ci/scripts/static_analysis_check.py) and Taskfile task (hooks:static-analysis).
7. **Mode default:** Shadow (non-blocking) for M902; enforcement toggle to M903.

---

## Task Decomposition (9 Sequential Tasks)

| # | Task | Expected Output | Dependencies | Success Criteria |
|---|------|-----------------|--------------|------------------|
| 1 | Tool discovery and inventory audit | `project_board/specs/902_02_tool_audit.md` | None | All tools mapped; scope/exclusions documented; compatibility notes included. |
| 2 | Configuration audit and scope mapping | Audit updates to Task 1 output | Task 1 | Tool→directory mapping; exclusions per CLAUDE.md; tool CLI invocation examples. |
| 3 | Update pyproject.toml with Python tools | Updated `asset_generation/python/pyproject.toml` + `uv.lock` | Task 1 | All tools installable; `uv sync --extra dev` succeeds; uv.lock generated. |
| 4 | Create config files for all tools | `.semgrep.yml`, `eslint.config.js`, `jscpd.json`, pyproject.toml [tool.*] sections | Task 2, Task 3 | All configs syntactically valid; no analysis of generated artifacts. |
| 5 | Update package.json with ESLint tools | Updated `asset_generation/web/frontend/package.json` + `package-lock.json` | Task 1 | All tools installable; `npm install` succeeds; package-lock.json generated. |
| 6 | Validate tools and baseline report | `project_board/specs/902_02_tool_baseline_report.md` | Task 3, Task 4, Task 5 | All available tools execute; violation counts documented; tool unavailability checkpointed. |
| 7 | Create gate orchestrator script | `ci/scripts/static_analysis_check.py` | Task 1, Task 4, Task 5, Task 6 | Script executes; output matches gate schema; handles missing tools gracefully. |
| 8 | Register gate in registry | Updated `ci/scripts/gate_registry.json` | Task 7, M902-01 (framework COMPLETE) | Gate discoverable by gate_runner.py; default mode is shadow. |
| 9 | Create Taskfile task + documentation | New `hooks:static-analysis` task in Taskfile.yml; updated Milestone 902 README | Task 7, Task 8 | Task executes; shadow mode is non-blocking; enforcement path to M903 documented. |

---

## Scope Exclusions (Per CLAUDE.md Guardrails)

All static analysis tools **must exclude**:
- `*.glb` (binary 3D model files)
- Large generated exports: `*.png`, `*.jpg` from asset baking
- `.venv/`, `node_modules/` (dependency directories)
- `reference_projects/` (read-only reference material)
- Generated asset pipeline outputs: `asset_generation/python/animated_exports/*`, `asset_generation/python/spots/*`, `asset_generation/python/stripes/*`, etc.

These exclusions prevent noisy/irrelevant violations and respect the project's guardrails on handling generated artifacts.

---

## Shadow Mode Specification

**Definition:** Shadow mode (default for M902) runs all tools and reports violations but does not cause the gate to fail (exit 1). Instead:
- Gate status may be "FAIL" (violations found) but exit code is 0.
- Violations are logged and available for review.
- Developers can preview violations locally via `task hooks:static-analysis`.
- CI does not break due to analysis violations (advisory only).
- M903 enables enforcement (exit 1 on violations) with grandfathering policies.

---

## Handoff Metadata Integration

The static analysis gate output JSON (Task 7) is consumed by M902-01 gate_runner.py and includes:
- Structured violations (file, line, rule, severity, tool).
- Remediation hints (actionable guidance per violation type).
- Artifacts list (config files, baseline report paths for auditing).
- Duration metrics (execution time for performance tuning).

This metadata enables downstream gates and agents to triage violations and route remediation.

---

## Deferred Boundaries (M903 & Beyond)

The following are explicitly **out-of-scope** for M902; they belong to Milestone 903 or later:
1. **Enforcement toggle** — M903 enables blocking mode (exit 1 on violations).
2. **Grandfathering policies** — M903 defines baseline thresholds and exemption lists per tool.
3. **Godot static analysis** — gdformat/gdlint integration is optional in M902; full wiring deferred.
4. **semgrep remote registry** — Remote rule registry deferred to M903 (uses local rules only in M902).
5. **Tool rule customization** — Per-team rule overrides and org-wide baselines deferred to M903.
6. **Performance optimization** — Parallel tool execution and caching deferred to M903.

---

## References

- **Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/02_static_analysis_gate_tooling.md`
- **Gate Framework (M902-01):** `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/01_validation_gate_framework.md`
- **Gate Runner:** `ci/scripts/gate_runner.py` (gate schema, CLI flags)
- **Gate Registry:** `ci/scripts/gate_registry.json` (registration format)
- **CLAUDE.md:** Repository guardrails for generated artifacts, tool execution, and conventions
- **Taskfile.yml:** Current task definitions and structure
- **pyproject.toml:** Python project configuration
- **package.json:** Frontend npm configuration

---

## Spec Exit Gate Check

This spec is type **generic** (per `spec_completeness_check.py` --type generic).

**Spec completeness check command:**
```bash
python ci/scripts/spec_completeness_check.py /Users/jacobbrandt/workspace/blobert/project_board/specs/902_02_static_analysis_gate_spec.md --type generic
```

**Expected outcome:** PASS (no required sections for generic type).

---

## Checkpoint Log Location

Spec Agent checkpoint decisions and ambiguity resolutions are logged at:
`/Users/jacobbrandt/workspace/blobert/project_board/checkpoints/M902-02/2026-05-14T12-00-00Z-spec.md`

---

**Document Status:** Complete and ready for TEST_DESIGN stage.

**Last Updated:** 2026-05-14 by Spec Agent

**Revision:** 1

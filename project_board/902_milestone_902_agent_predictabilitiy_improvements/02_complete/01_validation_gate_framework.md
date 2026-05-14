# Title

Validation gate framework for multi-agent handoffs (orchestration, routing, remediation)

# Context

The MVP requires every major agent handoff to run through a deterministic validation gate that can fail fast, return work to the originating agent, and emit actionable remediation context plus structured handoff metadata. This ticket establishes the shared framework hooks and contracts used by later tickets.

# Scope

- Define where gates plug into the existing workflow (planner→spec, spec→test design, test design→test breaker, test breaker→implementation, implementation→reviewer, reviewer→AC gatekeeper, learning→blog).
- Implement or extend orchestration so each gate runs as a discrete step with explicit inputs/outputs on disk (artifacts), not implicit chat state.
- Standardize exit codes / machine-readable failure payloads consumed by downstream automation (CI, autopilot scripts, lefthook where applicable).
- Document how a gate “routes back” (which artifact to update, which agent owns the retry).

# Acceptance Criteria

- A single documented “gate runner” entry surface exists (script or documented command sequence) that can execute an arbitrary gate by name with stable CLI flags.
- Gate failures produce a structured failure record (JSON or YAML) that includes: `gate`, `upstream_agent`, `downstream_agent`, `violations[]` with file/line/rule/message, and `remediation_hints[]`.
- Gate success emits a minimal structured success record referencing input artifact hashes or paths used for the decision.
- At least one existing handoff in-repo is wired to call the framework in a dry-run or shadow mode without breaking current CI (feature-flag or non-blocking mode acceptable until Milestone 903 enables enforcement).

# Agent Execution Prompt

Implement the validation gate framework for blobert’s multi-agent workflow.

Goal: Add a small, deterministic gate runner and artifact contract under `project_board/` or `ci/scripts/` (pick the repo’s existing orchestration conventions) that can execute named gates and emit structured JSON results.

Constraints:
- Do not weaken existing tests or hooks.
- Prefer Python or bash consistent with existing CI scripts.
- No gameplay changes.

Expected output:
- Gate runner command documented in the ticket’s follow-up README section of the milestone (update Milestone 902 README only if you add a new canonical command).
- Example `gate-result.json` schema checked into repo as documentation or test fixture.

# Failure Handling Prompt

If blocked, ask:

- What dependency is missing? (e.g., no CI runner, no agreed artifact paths)
- What assumption cannot be verified? (e.g., autopilot not invocable locally)
- What ambiguity prevents completion? (e.g., which handoff should be first consumer)

# Clarification Prompt

If unclear, ask:

- What specific ambiguity exists about where gate outputs should be written?
- What decision needs to be made about blocking vs shadow mode during rollout?
- What are the possible interpretations of “artifact” in this repo (paths under `project_board/checkpoints/` vs git diff)?

# Dependencies

None.

# Definition of Done

- Gate runner exists and is documented.
- At least one gate invocation is integrated in shadow/non-blocking mode OR fully blocking with explicit approval documented.
- Structured failure/success records match the documented schema and are validated by a unit test or snapshot test where practical.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: 220 total (64 primary + 112 adversarial + 44 additional); all 220 PASS
  - `tests/ci/test_gate_runner_cli.py` — CLI flag parsing, exit codes, mode routing
  - `tests/ci/test_gate_runner_cli_adversarial.py` — adversarial CLI edge cases
  - `tests/ci/test_gate_registry.py` — gate registry loading, validation
  - `tests/ci/test_gate_registry_adversarial.py` — adversarial registry scenarios
  - `tests/ci/test_gate_schemas.py` — success/failure schema fixture validation
  - `tests/ci/test_gate_schemas_adversarial.py` — adversarial schema mutation tests
- Static QA: Passed (ruff clean)
- Integration: Passed (full suite)
- AC1 (gate runner CLI): Verified — `ci/scripts/gate_runner.py` exists with documented CLI flags; registered in `gate_registry.json`
- AC2 (structured failure record): Verified — `ci/scripts/gate_schemas/gate-result-failure.json` contains all required fields (`gate`, `upstream_agent`, `downstream_agent`, `violations[]`, `remediation_hints[]`); schema validated by tests
- AC3 (structured success record): Verified — `ci/scripts/gate_schemas/gate-result-success.json` contains `artifacts[]` with `path` + `sha256`; placeholder hash was replaced with actual SHA-256 computation
- AC4 (shadow-mode handoff wiring): Verified — `spec_completeness_check` gate registered in `shadow` mode; `ci/scripts/spec_completeness_check.py` implements the gate; non-breaking to CI
- Blocking Issues: All resolved by Engine Integration Agent (bare `dict` annotations, dead code, shadow mode exit codes, OSError handling, exception filtering, unknown type handling, sha256 fix, unused code removal, test fixes)

## Blocking Issues
- Resolved by Engine Integration Agent:
  - HIGH: 6 bare `dict` annotations → fixed with `dict[str, Any]` and `_GateRegistryEntry` TypedDict
  - HIGH: 2 dead code references (_SPEC_CHECKER) → removed
  - HIGH: `spec_missing` returning exit 2 in shadow mode → fixed to respect mode (shadow exits 0)
  - MEDIUM: 2 silent OSError swallowing → fixed to log + re-raise
  - MEDIUM: bare `except Exception` catching KeyboardInterrupt/SystemExit → fixed with explicit re-raise
  - MEDIUM: silent fallback for unknown ticket type → fixed to return FAIL status
  - MEDIUM: placeholder `"sha256": ""` → fixed to compute actual SHA-256 hash
  - MEDIUM: unused `_SCHEMAS_DIR` → removed
  - MEDIUM: unused `json` import in spec_completeness.py → removed
  - MEDIUM: f-string without placeholders → fixed
  - Test fix: timestamp collision in `test_shadow_and_blocking_write_to_same_dir` → added 1.1s sleep
  - Test fix: adversarial tests testing outdated behavior → updated to match new behavior

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Learning Agent

## Required Input Schema
```json
{
  "ticket_path": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/01_validation_gate_framework.md"
}
```

## Status
Proceed

## Reason
All four acceptance criteria have explicit test or integration coverage verified by the AC Gatekeeper. Gate runner CLI documented and tested (220 tests, all PASS). Structured failure/success schema fixtures present and validated. `spec_completeness_check` gate wired in shadow mode without breaking CI. All prior blocking issues resolved. Ticket is ready for Learning Agent to extract engineering insights. **Note:** Ticket is currently in `01_in_progress/`; per workflow enforcement, it should be moved to `done/` before or alongside the Learning stage.

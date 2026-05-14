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
TEST_BREAK

## Revision
4

## Last Updated By
Test Designer Agent

## Validation Status
- Tests: Written (64 cases, 8 pass, 56 expect RED pre-implementation)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

## Required Input Schema
```json
{
  "spec_path": "project_board/specs/902_01_gate_runner_spec.md"
}
```

## Status
Proceed

## Reason
Tests written and executed. 64 behavioral tests across 5 modules under `tests/ci/`: gate runner CLI (13 tests), gate registry (10 tests), schema fixtures (22 tests), shadow mode (7 tests), handoff wiring (12 tests). All tests are pytest-discoverable. 8 pass (error-path/absence tests), 56 expect RED until implementation files are created (gate_runner.py, gate_registry.json, gate_schemas/, gates/). Test Breaker Agent to add adversarial/mutation tests and verify full suite turns GREEN after implementation.

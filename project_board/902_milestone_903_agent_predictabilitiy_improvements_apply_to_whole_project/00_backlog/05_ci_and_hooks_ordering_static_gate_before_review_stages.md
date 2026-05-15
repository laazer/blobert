# Title

CI and lefthook ordering: run static analysis gate before diff-cover, script review, and AC validation

# Context

The MVP explicitly orders: implementation → static analysis gate → diff-cover preflight → script reviewer → review validation → AC gatekeeper. This ticket updates repository automation to match that ordering for human and agent workflows.

# Scope

- Update `ci/scripts/*`, `.lefthook.yml`, and `Taskfile.yml` tasks as needed to preserve the repo’s command source-of-truth hierarchy (`Taskfile.yml` > hooks > `CLAUDE.md`).
- Ensure local developer workflows remain fast: provide staged vs full modes if necessary.

# Acceptance Criteria

- Canonical full suite (`timeout 300 ci/scripts/run_tests.sh` or successor) runs static analysis at the specified stage relative to Python diff-cover and review steps.
- Lefthook pre-push equivalents remain documented in `CLAUDE.md` if behavior changes.
- Failure messages point to the static analysis output artifacts.

# Agent Execution Prompt

Reorder CI and hook stages to insert the mandatory static analysis gate before diff-cover and review.

Goal: Make the automation order match the MVP diagram without duplicating work or doubling runtime unnecessarily.

Constraints:
- Must remain fail-fast and bounded by timeouts.
- Do not introduce network-dependent CI steps.

Expected output:
- CI/hook/Taskfile edits + minimal `CLAUDE.md` updates if commands change.

# Failure Handling Prompt

If blocked, ask:

- What dependency is missing? (static gate command not yet implemented)
- What assumption cannot be verified? (runtime budget)
- What ambiguity prevents completion? (which review step is considered “script reviewer” in-repo)

# Clarification Prompt

If unclear, ask:

- What specific ambiguity exists about whether Godot tests run before or after static analysis?
- What decision needs to be made about partial checks on staged files?
- What are the possible interpretations of “diff-cover preflight” in current scripts?

# Dependencies

- Mandatory static analysis gate: Python, TypeScript/React, Godot, and duplication tooling (Milestone 902)
- Python committed code: turn on static analysis enforcement with an explicit `.governance-baseline.json` (Milestone 903) — may be coordinated in same PR series

# Definition of Done

- CI ordering matches MVP intent and is documented in `CLAUDE.md` when user-facing commands change.

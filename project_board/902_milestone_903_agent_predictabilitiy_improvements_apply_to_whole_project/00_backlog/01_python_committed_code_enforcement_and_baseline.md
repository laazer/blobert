# Title

Python committed code: turn on static analysis enforcement with an explicit `.governance-baseline.json`

# Context

Milestone 902 introduces Python tooling (ruff/mypy/bandit/vulture/import-linter/semgrep/wemake). This ticket applies those tools to the committed Python tree so CI fails on new violations while grandfathering known legacy violations via the baseline mechanism.

# Scope

- `asset_generation/python` (primary), plus `asset_generation/web/backend` if included by the Milestone 902 tool scope decision.
- Align with existing `bash .lefthook/scripts/py-tests.sh` and diff-cover gate: ensure new failures are actionable and not flaky.
- Generate and commit an initial baseline only after violations are bucketed with owners/expiry metadata policy (minimum viable: rule+path fingerprints).

# Acceptance Criteria

- CI runs the Python static analysis bundle on committed code paths and fails on violations not covered by baseline.
- Baseline updates require explicit rationale in the PR description or ticket reference (enforced by policy doc snippet in PR template or contributing note—choose least invasive repo convention).
- `bash .lefthook/scripts/py-tests.sh` (or canonical CI script) remains the source of truth for ordering changes; if ordering changes, `CLAUDE.md` is updated accordingly.

# Agent Execution Prompt

Enforce Milestone 902 Python static analysis on committed code.

Goal: Wire CI/hooks to run the Python bundle against committed sources and add `.governance-baseline.json` entries for all current violations, with expirations and owners.

Constraints:
- Do not weaken existing Ruff E9/F/I enforcement already described in `CLAUDE.md`.
- Avoid scanning generated export trees.

Expected output:
- CI/hook diff + baseline file + short note in Milestone 903 README status.

# Failure Handling Prompt

If blocked, ask:

- What dependency is missing? (tool too slow, missing native deps)
- What assumption cannot be verified? (mypy strictness level)
- What ambiguity prevents completion? (whether backend is in scope)

# Clarification Prompt

If unclear, ask:

- What specific ambiguity exists about strict typing scope for FastAPI modules?
- What decision needs to be made about semgrep rules being ERROR vs WARN in CI?
- What are the possible interpretations of “new violations” when baselines use path prefixes?

# Dependencies

- Governance audit pipeline and `.governance-baseline.json` (grandfathering with expiration and ownership) (Milestone 902)
- Mandatory static analysis gate: Python, TypeScript/React, Godot, and duplication tooling (Milestone 902)

# Definition of Done

- CI enforces Python checks with a committed baseline and tests proving “new violation fails”.

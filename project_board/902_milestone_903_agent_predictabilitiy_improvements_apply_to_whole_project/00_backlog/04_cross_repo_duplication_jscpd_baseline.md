# Title

Cross-repo duplication (jscpd): thresholds, excludes, and baseline on committed code

# Context

The MVP includes `jscpd` duplication analysis across the repository. This ticket sets practical thresholds and exclusions for generated/binary content, then applies enforcement to committed human-authored sources.

# Scope

- Configure excludes for `reference_projects/`, generated exports, lockfiles, and large assets per repo guardrails.
- Choose initial thresholds that reflect current duplication reality; use baseline/warn policy if needed until remediation tickets burn down debt.

# Acceptance Criteria

- `jscpd` runs in CI with stable configuration checked into the repo.
- Duplication regressions beyond threshold fail CI OR emit ESCALATE/WARN per the Milestone 902 metadata policy (pick one consistent policy and document it).
- Output is machine-readable and archived as an artifact path documented in Milestone 903 README.

# Agent Execution Prompt

Roll out jscpd on committed code with sensible excludes and thresholds.

Goal: Add jscpd config, integrate into CI static stage, and establish baseline/remediation backlog slices.

Constraints:
- Do not scan gigabyte binary paths.
- Keep CI runtime bounded.

Expected output:
- jscpd config + CI integration + documented thresholds.

# Failure Handling Prompt

If blocked, ask:

- What dependency is missing? (jscpd not available in CI)
- What assumption cannot be verified? (baseline format compatibility)
- What ambiguity prevents completion? (what duplication is acceptable in tests)

# Clarification Prompt

If unclear, ask:

- What specific ambiguity exists about comparing GDScript vs Python duplication rules?
- What decision needs to be made about thresholds per language?
- What are the possible interpretations of “duplication delta” without historical metrics?

# Dependencies

- Mandatory static analysis gate: Python, TypeScript/React, Godot, and duplication tooling (Milestone 902)
- Handoff metadata schema and risk-based escalation (PASS/WARN/FAIL/ESCALATE) (Milestone 902)

# Definition of Done

- jscpd integrated with documented policy and a passing CI state on `main`-equivalent branch.

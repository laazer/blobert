# Title

Governance audit pipeline and `.governance-baseline.json` (grandfathering with expiration and ownership)

# Context

The MVP requires a repository-wide audit pipeline that scans the repo, normalizes and clusters violations, generates remediation tasks, and maintains `.governance-baseline.json` so existing violations may be temporarily tolerated while new violations fail immediately. Baselines must support expiration, ownership metadata, and suppression metadata.

# Scope

- Implement an audit command that runs the static analysis suite repo-wide (respecting excludes) and emits structured violation reports.
- Implement clustering (by rule + path prefix) to reduce noise and produce ticket-sized remediation bundles.
- Implement baseline generation and diff: new violations outside baseline fail; baseline entries carry `expires_at`, `owner`, `rationale`, and `rule_id`.
- Define policy for baseline updates (requires human approval or second reviewer) and wire metadata fields for audit events.

# Acceptance Criteria

- Running audit on a clean checkout produces deterministic outputs given pinned tool versions.
- Baseline file validates against a schema and is safe to commit (no secrets).
- "New violation" detection has automated tests using synthetic fixtures.
- Remediation ticket generator outputs markdown snippets suitable for `project_board/**/00_backlog/`.

# Agent Execution Prompt

Build the governance audit pipeline and baseline mechanism.

Goal: Add `audit` and `baseline` subcommands (or equivalent) that integrate with the static analysis gate tooling and emit clustered reports + suggested backlog tickets.

Constraints:
- Baseline must not silently accept new categories; unknown rules require explicit baseline entries.
- Keep runtime bounded for CI (document scan scope).

Expected output:
- Implementation + tests + example baseline fragment in docs (not necessarily committed as real baseline).

# Failure Handling Prompt

If blocked, ask:

- What dependency is missing? (jsonschema, clustering thresholds)
- What assumption cannot be verified? (tool output formats unstable)
- What ambiguity prevents completion? (ownership model for violations)

# Clarification Prompt

If unclear, ask:

- What specific ambiguity exists about baseline granularity (per-rule vs per-violation fingerprint)?
- What decision needs to be made about expiration defaults?
- What are the possible interpretations of "governance trend metrics" without historical storage?

# Dependencies

- Mandatory static analysis gate: Python, TypeScript/React, Godot, and duplication tooling

# Definition of Done

- Audit+baseline workflow is usable locally and documented in Milestone 902 README.
- Tests cover baseline diff behavior.

---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | COMPLETE |
| Revision | 8 |
| Last Updated By | Human |
| Next Responsible Agent | N/A |
| Status | Proceed |
| Validation Status | Implementation and Tests Complete - AC Validation Pending Manual Verification. Primary Test Suite: test_audit_pipeline_and_baseline.py (35 tests across 9 test classes covering audit execution, baseline schema, diff detection, clustering, remediation generation, metadata, edge cases, and integration). Adversarial Test Suite: test_audit_pipeline_baseline_adversarial.py (37 tests across 14 test classes covering mutations, boundaries, schema violations, clustering edge cases, stress scenarios, concurrency, and diff logic errors). Implementation artifacts: ci/scripts/audit.py (766 lines), ci/scripts/baseline.py (278 lines), project_board/schemas/governance-baseline-schema.json. All acceptance criteria have explicit test coverage except AC#4 (remediation markdown format) which requires manual human verification of output quality. |
| Blocking Issues | None - all acceptance criteria have test coverage or documented manual verification path. |

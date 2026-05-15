# Title

Frontend committed code: eslint (typescript-eslint, sonarjs, boundaries, hooks) in CI with baseline

# Context

The MVP requires ESLint-based governance for React/TypeScript, including boundaries and hooks rules. This ticket applies those rules to `asset_generation/web/frontend` committed sources and enforces them in CI.

# Scope

- Configure rulesets and import boundaries consistent with the frontend’s module layout.
- Ensure `npm test` / `npm run lint` (use existing scripts) remain the canonical developer entrypoints; update them minimally.

# Acceptance Criteria

- CI runs frontend lint with the expanded ruleset.
- New violations fail CI unless covered by an approved suppression entry with owner+expiry (prefer baseline over inline disables).
- No new `eslint-disable` file-wide comments without ticket references (enforced by policy check or grep gate as agreed in Milestone 902 governance checks).

# Agent Execution Prompt

Enforce expanded ESLint governance on committed frontend code.

Goal: Wire eslint configs, fix straightforward issues, baseline the remainder with `.governance-baseline.json` or eslint inline policy per repo standards.

Constraints:
- Do not use `@ts-ignore` / `as any` to silence types.
- Keep changes focused to lint-driven fixes.

Expected output:
- package.json scripts if needed + CI + baseline/suppressions as required.

# Failure Handling Prompt

If blocked, ask:

- What dependency is missing? (eslint plugin compatibility with Vite/TS version)
- What assumption cannot be verified? (desired boundary graph)
- What ambiguity prevents completion? (whether backend TS is included)

# Clarification Prompt

If unclear, ask:

- What specific ambiguity exists about module boundary layers?
- What decision needs to be made about sonarjs rule severity defaults?
- What are the possible interpretations of “react-hooks” scope (only src/ vs tests)?

# Dependencies

- Automated governance checks for handoffs (architecture, safety, observability, integrity) (Milestone 902)
- Mandatory static analysis gate: Python, TypeScript/React, Godot, and duplication tooling (Milestone 902)

# Definition of Done

- CI enforces frontend lint with baseline/suppression policy aligned to governance rules.

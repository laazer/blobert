# Title

Suppression grandfathering: replace blanket disables with scoped, owned suppressions tied to baselines

# Context

The MVP rejects blanket lint suppressions and abusive `semgrep` disable-all usage. Committed code may contain historical suppressions; this ticket migrates them to scoped forms with owners and expiration aligned to `.governance-baseline.json` policy.

# Scope

- Inventory new/changed suppressions via git history scope and static checks from Milestone 902.
- Replace file-wide disables where possible with targeted suppressions + ticket references.
- Ensure semgrep policy matches: disallow disable-all except in explicitly allowlisted test fixtures (if any).

# Acceptance Criteria

- A repo scan report lists remaining suppressions with owners and expiry dates.
- CI fails if a new file-wide eslint disable or semgrep disable-all appears outside allowlist.
- At least N highest-risk suppressions are removed or narrowed (set N based on initial scan; document N in PR).

# Agent Execution Prompt

Clean up suppressions across committed code to match governance integrity rules.

Goal: Reduce blanket suppression usage and connect remaining suppressions to baseline metadata and tickets.

Constraints:
- Do not change behavior except via equivalent refactors required by lint correctness.
- No secret leakage in logs.

Expected output:
- Code edits + baseline updates + checklist of remaining debt.

# Failure Handling Prompt

If blocked, ask:

- What dependency is missing? (allowlist not defined)
- What assumption cannot be verified? (third-party vendored code)
- What ambiguity prevents completion? (generated files contain disables)

# Clarification Prompt

If unclear, ask:

- What specific ambiguity exists about allowlisting `reference_projects/`?
- What decision needs to be made about test-only suppressions?
- What are the possible interpretations of “suppression abuse” for Ruff per-file-ignores?

# Dependencies

- Automated governance checks for handoffs (architecture, safety, observability, integrity) (Milestone 902)
- Governance audit pipeline and `.governance-baseline.json` (grandfathering with expiration and ownership) (Milestone 902)

# Definition of Done

- Suppression inventory exists, policy checks are enforced, and measurable reduction is merged.

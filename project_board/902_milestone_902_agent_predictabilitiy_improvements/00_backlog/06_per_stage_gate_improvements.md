# Title

Per-stage validation gate improvements (planner, spec, tests, adversarial, reviewer, learning)

# Context

The MVP lists targeted improvements for each stage: planner (cycles, umbrella sanity, ownership, scope sizing), spec (observability/rollback/async/migration/edge cases), test gates (assertion density, exception/async paths, mutation targets, observability assertions), adversarial gate (mutation scoring, invalid states, breadth), reviewer gate (drift, suppressions, TODOs, migration risk), learning gate (prevent codifying hacks/violations).

# Scope

- Implement deterministic checks that can run with only artifacts (markdown specs, test files, coverage artifacts where available).
- Add stage-specific gate modules callable by name from the gate framework.
- Where metrics are not yet available (e.g., mutation coverage), implement placeholders that emit WARN with explicit “not configured” reasons rather than fake PASS.

# Acceptance Criteria

- Each listed stage has a documented checklist + at least one automated check OR an explicit WARN placeholder with a ticket reference to future work.
- Planner gate can detect obvious cyclic ticket dependency graphs within a milestone folder when dependencies are machine-readable.
- Spec gate validates presence of required headings/sections defined by `spec-exit-gate` skill or repo spec template (choose one canonical template and reference it).
- Test gate computes simple metrics (assertions per test file, async test markers) without requiring external services.
- Reviewer gate scans for new `TODO`/`FIXME` in diff scope and for new broad lint suppressions.
- Learning gate checks learning output for forbidden phrases/patterns defined by policy (config-driven list).

# Agent Execution Prompt

Upgrade per-stage gates according to the MVP lists.

Goal: Extend the gate runner with stage-specific modules and wire them into the appropriate workflow entrypoints (autopilot scripts, lefthook optional stage, or manual commands).

Constraints:
- Do not rewrite historical checkpoints; gates operate on current artifacts and git diffs as configured.
- Prefer small, testable scripts.

Expected output:
- Stage gate scripts + tests + short operator documentation.

# Failure Handling Prompt

If blocked, ask:

- What dependency is missing? (git diff unavailable, no spec template)
- What assumption cannot be verified? (dependency graph format inconsistent)
- What ambiguity prevents completion? (mutation tooling not installed)

# Clarification Prompt

If unclear, ask:

- What specific ambiguity exists about the canonical spec template?
- What decision needs to be made about diff scope (staged vs HEAD)?
- What are the possible interpretations of “mutation target validation” in this repo?

# Dependencies

- Validation gate framework for multi-agent handoffs (orchestration, routing, remediation)
- Handoff metadata schema and risk-based escalation (PASS/WARN/FAIL/ESCALATE)

# Definition of Done

- All stages covered by automated checks or explicit WARN placeholders with tracked follow-ups.
- Stage gates runnable individually by name.

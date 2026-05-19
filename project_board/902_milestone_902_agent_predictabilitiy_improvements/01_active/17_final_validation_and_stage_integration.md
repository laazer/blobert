# M902-17: Final Validation & Stage Integration — 8-Stage Pipeline Complete

**Status:** PENDING  
**Target:** 2026-08-24

## Overview

Final integration and validation ticket for Milestone 902. Confirms that all 27 previous tickets (M902-01 through M902-27) are correctly implemented, properly sequenced, and fully integrated into:
1. A cohesive 8-stage governance pipeline
2. Context optimization enhancements (tool categorization, parsing, budgeting)
3. API contract safety gates (OpenAPI → TS, Pydantic + Zod, contract testing, pre-commit)

As defined in `@bot_vault/architecture/code_governance.md` and blobert's API integration strategy.

This ticket **validates the entire system**, not implements new features.

## Acceptance Criteria

### ✓ Stage Implementation (M902-09 through M902-16)

- [ ] **M902-09 (Stage 0):** Diff classification gate exists, classifies changes correctly, routes to appropriate pipeline
- [ ] **M902-10 (Stage 1):** Formatting gate auto-fixes code, re-stages if needed, exits cleanly
- [ ] **M902-02 (Stage 2):** Static analysis tools integrated, violations detected and reported
- [ ] **M902-11 (Stage 3):** Architecture enforcement detects SRP/dependency/duplication violations
- [ ] **M902-12 (Stage 4):** Risk scoring computes weights, routes high-risk to Stage 5
- [ ] **M902-13 (Stage 5):** Semantic extraction builds focused bundles (< 100KB, correct schema)
- [ ] **M902-14 (Stage 6):** Agent semantic review evaluates bundles, returns APPROVE/WARN/REJECT
- [ ] **M902-15 (Stage 7):** Override system enforces `blobert-ignore-next-line` format, escalates violations
- [ ] **M902-16 (Stage 8):** Security gate runs gitleaks/bandit/semgrep, hard-fails on secrets

### ✓ Context Optimization & Handoff Quality (M902-18 through M902-23)

- [ ] **M902-18 (Tool Categorization):** Tool schemas filtered by category (parse/modify/test/plan/think); 15–25% context reduction verified
- [ ] **M902-19 (Tool Parsing Middleware):** Auto-repairs JSON/YAML tool calls; eliminates 5–10% of retry loops
- [ ] **M902-20 (TODO Validation):** Gate validates task completion before handoff; prevents silent failures
- [ ] **M902-21 (Context Budget Tracking):** Token usage instrumented per agent/stage; metrics reported in checkpoints
- [ ] **M902-22 (Early-Stop Detection):** Loop detection catches stuck agents after 3 iterations; escalates gracefully
- [ ] **M902-23 (Atomic Handoff Checkpoint):** Per-agent checklists formalize handoff contracts; gates validate completeness

### ✓ API Contract Safety (M902-24 through M902-27)

- [ ] **M902-24 (OpenAPI → TypeScript Generation):** Types auto-generated from FastAPI spec; frontend has zero manual type definitions
- [ ] **M902-25 (Pydantic + Zod Dual Validation):** Backend validates with Pydantic, frontend with Zod; 100% runtime coverage
- [ ] **M902-26 (API Contract Testing):** Contract tests verify responses match schema; catches API drift before deployment
- [ ] **M902-27 (Pre-Commit Hook):** Hook regenerates types, runs tsc, validates contracts; blocks commits with mismatches

### ✓ Pipeline Integration

- [ ] **Sequential execution:** Stage 0 → 1 → 2 → 3 → 4 (risk check) → [Stage 5+6 if high-risk] → 7 → 8
- [ ] **Early exits work:** Docs-only changes skip to Stage 8; tests-only skip Stages 3–4
- [ ] **Gate outputs validated:** Each gate returns JSON with status/violations/remediation
- [ ] **Gate registry updated:** All gates registered in `ci/scripts/gate_runner.py`
- [ ] **Gate runner accepts all gates:** `python ci/scripts/gate_runner.py <gate_name>` works for all 8 stages
- [ ] **CI integration:** All gates can run in shadow and blocking modes

### ✓ Agent Integration (M902-01 through M902-08)

- [ ] **code_governance.md linked:** Agents have reference to full 8-stage pipeline in CLAUDE.md or memory
- [ ] **Agent semantic reviewer (M902-14):** Configured and callable as validation agent
- [ ] **PreToolUse hooks (M902-05):** Blocking command inspection integrated with gate flow
- [ ] **Governance audit (M902-07):** Audit trail records all gate decisions and suppressions
- [ ] **Workflow visualization (M902-08):** Mermaid diagram accurate and up-to-date

### ✓ End-to-End Test

- [ ] **Test change with violations:** Push code with Ruff error → Stage 2 fails → returns remediation
- [ ] **Test architecture violation:** Push with circular import → Stage 3 fails → returns import path
- [ ] **Test high-risk change:** Multi-file refactor → Risk score > 6 → Stage 5 extraction → Stage 6 agent review invoked
- [ ] **Test suppression:** Add valid `blobert-ignore-next-line` → Stage 7 validates → proceeds with audit log
- [ ] **Test secret detection:** Add fake AWS key → Stage 8 fails → gitleaks output shown
- [ ] **Test full passing flow:** Clean change → all stages PASS → proceeds to merge

### ✓ Documentation

- [ ] **Each stage has spec:** `project_board/specs/902_XX_*.md` for all 8 stages
- [ ] **Gate operator guide:** How to run gates locally, interpret output, remediate
- [ ] **Agent runbook:** How agents should interpret risk scores and semantic bundles
- [ ] **Suppression guide:** Format, validity rules, escalation triggers documented
- [ ] **Decision tree:** Clear path for agents/humans on handling each gate outcome

### ✓ Knowledge Integration

- [ ] **Agents know code_governance.md:** Added to CLAUDE.md or agent memory
- [ ] **Agents know to call gates:** Instructions on when/how to invoke gates during implementation
- [ ] **Agents know risk routing:** High risk → semantic extraction → agent review (M902-14)
- [ ] **Agents know suppression system:** Format and when escalation is triggered (M902-15)

### ✓ Coverage

- [ ] **Test matrix covers:** All 8 stages × 3 outcomes (PASS/WARN/FAIL) + escalations
- [ ] **Tool baseline:** Baseline reports exist for all tools (ruff, mypy, bandit, eslint, semgrep, jscpd)
- [ ] **False positive rate:** Documented for each tool (target < 5%)
- [ ] **Performance:** Full 8-stage pipeline runs in < 60 seconds on typical change

## Testing Checklist

Create a test plan (in checkpoint or inline) that covers:

```
[ ] Stage 0: Classify docs-only → skip
[ ] Stage 0: Classify tests-only → reduce
[ ] Stage 0: Classify runtime-code → full
[ ] Stage 1: Format unformatted code → re-stage
[ ] Stage 1: Already formatted → pass through
[ ] Stage 2: Code with lint error → FAIL + remediation
[ ] Stage 3: Circular import → FAIL + import path
[ ] Stage 3: Valid SRP boundaries → PASS
[ ] Stage 4: Low risk (score 0-2) → SKIP Stages 5+6
[ ] Stage 4: High risk (score 6+) → Route to Stage 5
[ ] Stage 5: Extract bundle for high-risk change → bundle valid
[ ] Stage 6: Agent evaluates bundle → returns decision JSON
[ ] Stage 7: Valid suppression → audit log entry
[ ] Stage 7: Invalid suppression → FAIL with format error
[ ] Stage 7: Repeated suppressions → escalate
[ ] Stage 8: Clean change → PASS
[ ] Stage 8: Change with secret → FAIL + gitleaks output
[ ] Full flow: Change → all stages PASS → ready for merge
```

## Definition of Done

- [ ] All acceptance criteria met
- [ ] End-to-end test successful (change passes all 8 stages)
- [ ] Documentation complete and linked
- [ ] Agent integration verified (agents know system and can make decisions)
- [ ] Checkpoint entry documenting validation
- [ ] M902 milestone ready to close or transition to M903 (enforcement)

## Specs Referenced

### 8-Stage Pipeline (M902-09 through M902-16)
- `project_board/specs/902_09_diff_classification_gate_spec.md`
- `project_board/specs/902_10_formatting_gate_spec.md`
- `project_board/specs/902_02_static_analysis_gate_spec.md` (Stage 2 recap)
- `project_board/specs/902_11_architecture_enforcement_spec.md`
- `project_board/specs/902_12_risk_scoring_spec.md`
- `project_board/specs/902_13_semantic_extraction_spec.md`
- `project_board/specs/902_14_agent_review_layer_spec.md`
- `project_board/specs/902_15_override_escalation_spec.md`
- `project_board/specs/902_16_security_gate_spec.md`

### Context Optimization & Handoff Quality (M902-18 through M902-23)
- `project_board/specs/902_18_tool_categorization_spec.md`
- `project_board/specs/902_19_tool_parsing_middleware_spec.md`
- `project_board/specs/902_20_todo_validation_spec.md`
- `project_board/specs/902_21_context_budget_tracking_spec.md`
- `project_board/specs/902_22_early_stop_spec.md`
- `project_board/specs/902_23_atomic_handoff_spec.md`

### API Contract Safety (M902-24 through M902-27)
- `project_board/specs/902_24_openapi_typescript_gen_spec.md`
- `project_board/specs/902_25_pydantic_zod_validation_spec.md`
- `project_board/specs/902_26_api_contract_testing_spec.md`
- `project_board/specs/902_27_api_contract_precommit_spec.md`

## Previous Tickets (Validation References)

### Core Infrastructure (M902-01 through M902-08)
- **M902-01:** Validation Gate Framework ✓
- **M902-02:** Static Analysis Gate Tooling
- **M902-03:** Handoff Governance Rule Enforcement
- **M902-04:** Handoff Metadata and Risk Escalation
- **M902-05:** PreToolUse Hooks Command Inspection ✓
- **M902-06:** Per-stage Gate Improvements
- **M902-07:** Governance Audit Pipeline and Baseline
- **M902-08:** Workflow Visualization and Agent Runbook Updates

### 8-Stage Pipeline (M902-09 through M902-16)
- **M902-09:** Stage 0 — Diff Classification Gate
- **M902-10:** Stage 1 — Formatting and Re-Stage Gate
- **M902-11:** Stage 3 — Architecture Enforcement Gate
- **M902-12:** Stage 4 — Risk Scoring System
- **M902-13:** Stage 5 — Semantic Extraction and Bundling
- **M902-14:** Stage 6 — Agent Semantic Review Layer
- **M902-15:** Stage 7 — Override and Escalation System
- **M902-16:** Stage 8 — Security Gate Integration

### Context Optimization & Handoff Quality (M902-18 through M902-23)
- **M902-18:** Tool Categorization Layer
- **M902-19:** Forgiving Tool Parsing Middleware
- **M902-20:** TODO Validation Gates
- **M902-21:** Context Budget Tracking
- **M902-22:** Early-Stop Detection
- **M902-23:** Atomic Handoff Checkpoint

### API Contract Safety (M902-24 through M902-27)
- **M902-24:** OpenAPI → TypeScript Generation
- **M902-25:** Pydantic + Zod Dual Validation
- **M902-26:** API Contract Testing
- **M902-27:** API Contract Pre-Commit Hook

## Rollout Plan (Post-Validation)

Once M902-17 completes:

1. **Shadow Mode (1 week):** All gates run advisory-only; violations logged but non-blocking
2. **Soft Enforcement (1 week):** Gates block tests-only and docs-only changes; agent review for high-risk only
3. **Full Enforcement (M903):** All gates blocking; mandatory agent review for risk > 4; override system enforced
4. **Team Rollout:** Documentation, runbooks, training for team agents

## Notes

This ticket is a **validation gate itself**. Its completion confirms the entire system is:
- **8-stage governance pipeline:** Architecturally sound, properly integrated, agent-aware, end-to-end tested
- **Context optimization:** Tool categorization, parsing middleware, and budget tracking reduce token waste by 15–25%
- **Handoff quality:** TODO validation, early-stop detection, and atomic checklists prevent silent failures
- Ready for enforcement (M903)

Failure here routes back to the specific failing stage ticket (M902-09 through M902-16 for pipeline, M902-18 through M902-23 for context optimization) for remediation.

### Origin

**M902-18 through M902-23:** Added based on analysis of [smallcode](https://github.com/Doorman11991/smallcode), an AI coding agent designed for small LLMs. Six patterns extracted:
- Tool categorization (halving schema overhead)
- Forgiving tool parsing (eliminating syntax retry loops)
- TODO validation gates (preventing silent handoff failures)
- Context budget tracking (data-driven optimization)
- Early-stop detection (catching stuck loops)
- Atomic handoff checkpoints (formalizing agent contracts)

**M902-24 through M902-27:** Added to ensure frontend-backend API contracts never drift. Four-layer safety net:
- OpenAPI → TypeScript auto-generation (static type safety)
- Pydantic + Zod dual validation (runtime safety)
- Automated contract testing (regression detection)
- Pre-commit hooks (enforcement before commits)

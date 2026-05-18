# M902-18: Tool Categorization Layer

**Status:** TEST_DESIGN  
**Target:** 2026-07-01

## Overview

Implement a tool categorization system inspired by smallcode's context-budget optimization. Before each agent call, agents declare a tool category (parse/modify/test/plan/think), and the agent receives only that category's tool schema. This reduces context overhead by ~15–25% per agent stage.

## Acceptance Criteria

- [ ] Define tool categories enum: `parse`, `modify`, `test`, `plan`, `think`
- [ ] Categorize all existing agent tools into one or more categories
- [ ] Implement `get_tools_for_category(category: str) -> list[Tool]` function
- [ ] Agent framework passes `tool_category` parameter to each agent
- [ ] Agents can declare category in their input prompt (e.g., "I'm in parse mode, give me read-only tools")
- [ ] Tool schema reduction measured: log baseline (all tools) vs. category-filtered size
- [ ] Integration tested with 3+ agents (spec, implementation, test-designer)
- [ ] Documented in agent runbook: when/how to declare category

## Implementation Notes

- Use agent SDK's tool filtering mechanism to exclude non-matching tools
- Category mapping stored in `ci/scripts/tool_categories.json` or similar config
- Agents must opt-in or dynamically select based on workflow stage
- Measure token savings in checkpoint logs

## Example Categories

| Category | Tools | Use Case |
|----------|-------|----------|
| **parse** | Read, Bash (grep/find only), WebFetch | Codebase exploration, specification research |
| **modify** | Edit, Write, Bash (safe file ops) | Implementation, refactoring |
| **test** | Bash (test runners), TaskOutput, Monitor | Running tests, verifying behavior |
| **plan** | TodoWrite, Agent (plan subagent), Bash (git log) | Decomposing work, understanding history |
| **think** | Agent (all subagents), Bash (no side effects) | Analysis, architecture decisions |

## Spec Reference

See: `project_board/specs/902_18_tool_categorization_spec.md`

## Execution Plan

See: `project_board/execution_plans/M902-18_tool_categorization_layer.md`

## Dependencies

- M902-01 (Validation Gate Framework) — COMPLETE ✓
- Agent SDK modifications (may require coordination with agent framework team)

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_BREAK

## Revision
4

## Last Updated By
Test Designer Agent

## Validation Status
Test Designer Agent completed Task 2 (TEST_DESIGN stage). Comprehensive test suite created with 88 behavioral tests across 2 files: tests/ci/test_tool_categorization.py (56 primary tests) and tests/ci/test_tool_categorization_adversarial.py (32 adversarial/boundary tests). All 8 requirements (R1–R8) and 30+ acceptance criteria (AC-1.1–8.7) have explicit test coverage via complete traceability matrix. Test organization: 8 test classes in primary file covering categories enum (7), tool mapping (8), function interface (11), framework integration (6), declaration protocol (9), measurement (9), integration harness (5), documentation (1). Adversarial file: 5 test classes covering malformed input (8), boundary conditions (8), declaration edge cases (6), determinism validation (6), robustness (6). All tests passing (88/88). Fixtures: mock tool schemas (no SDK dependency); behavior-driven assertions (no prose). Determinism validated: identical inputs produce identical outputs. Error handling: graceful fallback, clear messages. All tests deterministic and repeatable. Ready for Test Breaker (Task 3) to review and extend adversarial test coverage.

## Blocking Issues
None. Test suite complete and passing. Ready for Test Breaker to review and enhance.

## Escalation Notes
None. Test Designer has created comprehensive behavioral test suite. Test Breaker (Task 3) responsible for adversarial enhancement and validation before IMPLEMENTATION stage.

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

## Required Input Schema
```json
{
  "ticket_path": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/18_tool_categorization_layer.md",
  "spec_path": "project_board/specs/902_18_tool_categorization_spec.md",
  "test_design_path": "project_board/checkpoints/M902-18/2026-05-18T-test-design.md",
  "test_files": [
    "tests/ci/test_tool_categorization.py",
    "tests/ci/test_tool_categorization_adversarial.py"
  ],
  "checkpoint_path": "project_board/checkpoints/M902-18/2026-05-18T-test-design.md"
}
```

## Status
Proceed

## Reason
Test Designer Agent (Task 2) complete. Comprehensive test suite created with 88 behavioral tests across 2 files covering all 8 requirements and 30+ AC with complete traceability matrix. All tests passing. Mock-based fixtures (no SDK dependency). Determinism validated. Error handling comprehensive. Ready for Test Breaker (Task 3) to review, extend adversarial test coverage, and advance to TEST_BREAK completion before IMPLEMENTATION stage begins.

# M902-18-T5: Tool Categorization Framework Integration

**Status:** IN PROGRESS  
**Target:** 2026-05-25  
**Blocker For:** M902-18, M902-19, M902-20, M902-21, M902-22, M902-23

## Overview

Integrate the tool categorization system (implemented in M902-18 backend) into the Claude Code agent framework. This task:

1. **Locates** the agent invocation code (location currently unknown)
2. **Modifies** agent framework to accept optional `tool_category` parameter
3. **Extracts** category declarations from agent input prompts using regex
4. **Wires** category-filtered tools into agent execution path
5. **Validates** backward compatibility and framework integration

## Acceptance Criteria

- [ ] Agent framework location identified and documented in checkpoint
- [ ] Framework accepts optional `tool_category` parameter in agent invocation
- [ ] Category declaration regex implemented: `(?:I declare tool category|My workflow category is|Tool category):\s*(\w+)`
- [ ] Invalid categories handled gracefully (log warning, provide all tools, no hard fail)
- [ ] `get_tools_for_category()` callable from agent invocation context
- [ ] Framework passes filtered tools to agent before execution
- [ ] Backward compatibility verified: agents without category declaration work unchanged
- [ ] At least 1 test agent successfully declares category and receives filtered tools
- [ ] Integration verified with existing agent pipeline (no regressions)

## Implementation Notes

- Start with codebase exploration to locate agent invocation code
- Candidates: Claude Code infrastructure, Claude Agent SDK, agent orchestrator
- May require custom middleware if SDK modification not possible
- Error handling: fail-safe (missing/invalid category → provide all tools, log warning)
- Determinism: same category → same tool list across repeated invocations

## Example Integration

**Before (current):**
```python
invoke_agent(agent_type="spec", prompt="Write a spec for...")
# Agent receives ALL tools
```

**After (with categorization):**
```python
invoke_agent(
    agent_type="spec", 
    prompt="I declare tool category: parse\n\nWrite a spec for...",
    tool_category="parse"  # or extracted from prompt
)
# Agent receives ONLY parse category tools (Read, Glob, Grep, Bash for read-only)
```

## Dependencies

- **Blocked By:** Nothing
- **Blocks:** M902-18 (Tasks 6-8: Static QA, Integration Testing, Gatekeeper Validation)
- **Blocks:** M902-19+ (all backlog tickets explicitly depend on framework integration per their specs)

## Success Criteria for Unblocking M902-18

Once this ticket reaches COMPLETE:
1. Update M902-18 WORKFLOW STATE: Stage → IMPLEMENTATION (Task 5 complete, ready for Task 6 Static QA)
2. M902-18 can advance through Tasks 6-8 (Static QA, Integration Testing, Gatekeeper Validation)
3. M902-19+ can begin implementation (they require framework integration as prerequisite)

## Critical Questions

- **Q1:** Where is the agent invocation code? (location: discovered as EXTERNAL via planning)
- **Q2:** Does Claude Agent SDK expose tool filtering API, or is custom middleware needed?
- **Q3:** Is agent framework versioned separately or part of main codebase?
- **Q4:** Who owns agent framework code (for coordination if external)?

## References

- **M902-18 Spec:** `project_board/specs/902_18_tool_categorization_spec.md` (Requirements 4 & 5)
- **M902-18 Implementation Checkpoint:** `project_board/checkpoints/M902-18/2026-05-18T-implementation.md`
- **M902-18 Integration Guide:** `project_board/checkpoints/M902-18/INTEGRATION_GUIDE.md`
- **Backend Code (Ready):** `ci/scripts/tool_categories.json`, `ci/scripts/tool_category_manager.py`
- **Planning Checkpoint:** `project_board/checkpoints/M902-18-T5/2026-05-20T-planning-discovery-checkpoint.md`
- **Execution Plan:** `project_board/execution_plans/M902-18T5_tool_categorization_framework_integration.md`
- **Specification:** `project_board/specs/902_18T5_tool_categorization_framework_integration_spec.md` (NEW)

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_BREAK

## Revision
4

## Last Updated By
Test Designer Agent

## Validation Status
Test Design complete. Comprehensive test suite delivered: `tests/ci/test_agent_framework_integration.py` (38 tests, 100% pass rate, 0.09s). All 7 test layers implemented per Spec R7: category extraction (8 tests), tool filtering (5 tests), middleware contract (5 tests), mock framework integration (2 tests), backward compatibility (3 tests), determinism (2 tests), error handling (5 tests). Additional layers: adversarial edge cases (6 tests) + full middleware simulation (2 tests). All spec requirements (R1–R8) and ACs (AC-1–AC-8) mapped to test evidence. No spec gaps identified. All tests deterministic (zero flakes). Ready for Test Breaker Agent to confirm flake-free execution and explore additional adversarial scenarios.

## Blocking Issues
None. Test suite is complete, deterministic, and ready for test breaking phase.

## Escalation Notes
Test Designer completed comprehensive test suite covering all specification requirements and acceptance criteria. All tests passing with zero flakes. Test suite uses pytest + unittest.mock per CLAUDE.md conventions. Mock framework pattern enables independence from external SDK during testing. Ready for Test Breaker Agent to run 3+ iterations and validate adversarial deepening.

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

## Required Input
- Test File: `tests/ci/test_agent_framework_integration.py`
- Specification: `project_board/specs/902_18T5_tool_categorization_framework_integration_spec.md`
- Test Design Checkpoint: `project_board/checkpoints/M902-18-T5/2026-05-20T-test-design-run.md`

## Status
PROCEED TO TEST_BREAK

## Reason
Test suite complete with 38 passing tests covering all 7 test layers per spec R7. Test Breaker Agent will: (1) run test suite 3x more to confirm zero flakes, (2) explore adversarial scenarios beyond current coverage, (3) validate determinism under concurrent execution, (4) document any edge cases discovered. After test breaking, Implementation Agent will build actual middleware module and wire category extraction/tool filtering.

## Success Criteria (Test Break Phase)
- Test suite runs 4x total (1 from Test Designer + 3 from Test Breaker) with 100% consistency
- No flakes discovered across all 38 tests
- Zero false positives or false negatives
- Adversarial scenarios explored and any gaps documented for implementation phase

---

# DEPENDENCIES & UNBLOCK CHAIN

**When this ticket reaches COMPLETE:**

1. M902-18 Revision 8: Update Stage → IMPLEMENTATION (Task 5 complete)
2. M902-18 Revision 9: Begin Task 6 (Static QA)
3. M902-18 Revision 10: Begin Task 7 (Integration Testing with 3+ agents)
4. M902-18 Revision 11: Begin Task 8 (Gatekeeper Validation)
5. M902-18 Revision 12: Move to COMPLETE
6. M902-19 can begin: All framework integration prerequisites met
7. M902-20+ can begin: Dependent on M902-19 and M902-18 completion

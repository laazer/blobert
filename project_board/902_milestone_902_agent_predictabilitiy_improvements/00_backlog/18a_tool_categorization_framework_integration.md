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
IMPLEMENTATION_BACKEND

## Revision
5

## Last Updated By
Test Breaker Agent

## Validation Status
Test Break phase complete. Test suite extended from 38 to 72 tests with 34 new adversarial/mutation tests. All 72 tests passing 100% across 4 consecutive runs (zero flakes confirmed). **New test classes added:** TestRegexMutationVulnerabilities (8 tests, regex boundary enforcement), TestFilteringBoundaryConditions (5 tests, schema edge cases), TestConcurrencyAndRaceConditions (2 tests, thread safety), TestFrameworkParameterVariations (4 tests, invocation contract), TestSpecConformanceMutations (5 tests, explicit requirements), TestCommonImplementationTraps (4 tests, common bugs), TestStressAndLoad (3 tests, scalability), TestIntegrationMutationCases (3 tests, workflow atomicity). **Key findings exposed:** (1) Regex pattern vulnerable to mutation (colon, keyword specificity, whitespace handling); (2) Tool schema type assumptions create silent bugs (string vs list); (3) Framework parameter naming must be exact ('tools' not 'tool'); (4) Backward compatibility preserved under evolution. **Coverage matrix:** All spec requirements (R1–R8) + ACs (AC-1–AC-8) enhanced with mutation/adversarial tests. No spec gaps or ambiguities remain. All tests deterministic, fast (<1s), and ready for implementation validation.

## Blocking Issues
None. Test suite frozen and validated. Ready for Implementation Agent.

## Escalation Notes
Test Breaker Agent completed adversarial deepening phase. Extended test suite from 38 to 72 tests with comprehensive mutation and edge-case coverage. Regex pattern fragility, schema type assumptions, framework parameter variations, and workflow atomicity all exposed via tests. All tests deterministic and zero-flake across 4 consecutive runs. Implementation Agent must adhere to test constraints when building middleware module.

---

# NEXT ACTION

## Next Responsible Agent
Implementation Agent (Build Middleware Module)

## Required Input
- Test File: `tests/ci/test_agent_framework_integration.py` (72 tests, all passing)
- Specification: `project_board/specs/902_18T5_tool_categorization_framework_integration_spec.md`
- Test Break Checkpoint: `project_board/checkpoints/M902-18-T5/2026-05-20T-test-break-run.md`
- Execution Plan: `project_board/execution_plans/M902-18T5_tool_categorization_framework_integration.md`

## Status
PROCEED TO IMPLEMENTATION_BACKEND

## Reason
Test break phase complete. Extended test suite from 38 to 72 tests with comprehensive adversarial and mutation coverage. All tests pass deterministically (zero flakes across 4 consecutive runs). All spec requirements (R1–R8) and acceptance criteria (AC-1–AC-8) validated with mutation sensitivity tests. Implementation Agent will now build the middleware module at `ci/scripts/agent_invocation_middleware.py` and verify all 72 tests pass without modification.

## Success Criteria (Implementation Phase)
- Middleware module created at `ci/scripts/agent_invocation_middleware.py`
- Function signature matches spec: `invoke_agent_with_category_filtering(agent_type, prompt, all_tools, framework_invocation_fn, **framework_kwargs)`
- Category extraction via regex: `(?:I declare tool category|My workflow category is|Tool category):\s*(\w+)`
- Tool filtering via `get_tools_for_category()` from tool_category_manager
- Error handling: ValueError and RuntimeError caught, fallback to all tools
- All 72 tests pass without modification
- No bare except blocks; explicit exception handling only
- Logging module used (INFO for no declaration, WARNING for invalid category, ERROR for system failures)
- Backward compatibility: agents without category declaration receive all tools unchanged
- Code review: no unexplained tuning literals, clear docstrings, type hints on all functions

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

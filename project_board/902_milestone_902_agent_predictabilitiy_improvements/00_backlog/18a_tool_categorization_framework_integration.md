# M902-18-T5: Tool Categorization Framework Integration

**Status:** PENDING  
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

- **Q1:** Where is the agent invocation code? (location: unknown, to be discovered)
- **Q2:** Does Claude Agent SDK expose tool filtering API, or is custom middleware needed?
- **Q3:** Is agent framework versioned separately or part of main codebase?
- **Q4:** Who owns agent framework code (for coordination if external)?

## References

- **M902-18 Spec:** `project_board/specs/902_18_tool_categorization_spec.md` (Requirements 4 & 5)
- **M902-18 Implementation Checkpoint:** `project_board/checkpoints/M902-18/2026-05-18T-implementation.md`
- **M902-18 Integration Guide:** `project_board/checkpoints/M902-18/INTEGRATION_GUIDE.md`
- **Backend Code (Ready):** `ci/scripts/tool_categories.json`, `ci/scripts/tool_category_manager.py`

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
PLANNING

## Revision
1

## Last Updated By
Claude Code

## Validation Status
Ticket created. Awaiting discovery of agent framework location. Backend implementation (M902-18 Tasks 1-4) complete with 180 tests passing. Framework integration is architectural dependency blocking M902-18 Tasks 6-8 and all M902-19+ tickets.

## Blocking Issues
Agent framework location unknown. This is the critical blocker for Task 5 execution. Once framework code is located, implementation can proceed.

## Escalation Notes
This ticket exists to formalize the work required to unblock M902-18 and all downstream tickets (M902-19 through M902-27). Framework discovery is the immediate prerequisite. Consider assigning to agent/team with knowledge of Claude Code infrastructure or Claude Agent SDK architecture.

---

# NEXT ACTION

## Next Responsible Agent
Planner Agent (or Human) — Framework Discovery Phase

## Required Input
- Location of agent invocation code in codebase or SDK
- Access to agent framework documentation
- Owner/team for coordination if framework is external

## Status
PENDING DISCOVERY

## Reason
M902-18 backend is production-ready (180 tests passing, all 4 early ACs satisfied). Framework integration cannot proceed without discovering where agents are invoked in the orchestrator/SDK. This ticket formalizes that discovery work and subsequent integration task.

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

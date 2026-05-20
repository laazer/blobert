# M902-18-T5: Tool Categorization Framework Integration — Planning Checkpoint

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/00_backlog/18a_tool_categorization_framework_integration.md`

**Run Date:** 2026-05-20  
**Stage:** PLANNING  
**Agent:** Planner Agent (Autonomous Mode)

---

## Discovery Summary

### 1. Backend Implementation Status (M902-18 Tasks 1-4)
- ✅ **Complete:** `ci/scripts/tool_categories.json` (5 categories: parse, modify, test, plan, think; 8 tools mapped)
- ✅ **Complete:** `ci/scripts/tool_category_manager.py` (functions: `get_tools_for_category()`, `measure_tool_schema_reduction()`)
- ✅ **Tested:** 180 tests PASSING (100% pass rate)
- ✅ **Documented:** INTEGRATION_GUIDE.md provides clear handoff instructions

### 2. Agent Framework Location Discovery

**Finding:** Agent framework is **EXTERNAL** to the blobert codebase.

**Evidence:**
1. No `agent_context/**/*.py` files exist (agent infrastructure not in repo)
2. No `invoke_agent()` or similar invocation code found in codebase
3. Agent invocation happens via **Claude Code** or **Claude Agent SDK** (external systems)
4. Agents (Planner, Spec, Test Designer, etc.) are invoked from orchestration layer outside this repo
5. Tool filtering must occur at **agent invocation boundary** (not in blobert codebase itself)

**Key Files Searched:**
- `ci/scripts/` (gate_runner.py, validation scripts) — No agent invocation code
- `agent_context/` — Documentation only; no invocation framework
- Test files — Integration tests reference gates, not agent invocation
- CLAUDE.md — References "Claude Code" as external system

### 3. Integration Requirements (Per Spec & Integration Guide)

From `project_board/specs/902_18_tool_categorization_spec.md` (Requirements 4 & 5):

**Requirement 4 (Agent Framework Integration):**
- Framework must accept optional `tool_category` parameter
- Framework must pass `tool_category` to invocation context
- Framework must call `get_tools_for_category(tool_category)` before agent execution
- Framework must filter tools in schema before agent sees them

**Requirement 5 (Agent Declaration Protocol):**
- Regex pattern: `(?:I declare tool category|My workflow category is|Tool category):\s*(\w+)`
- Extract category from agent input prompt
- Invalid categories: fail-safe (log warning, provide all tools)
- Backward compatible (agents without declaration get all tools)

**From Integration Guide (Success Criteria):**
- Framework accepts `tool_category` parameter (optional, backward compatible)
- Regex extraction works
- Invalid categories fall back gracefully
- At least 1 agent invocation successfully uses filtered tools
- M902-08 runbook updated (reference not found in this run; TBD for Spec Agent)

### 4. Implementation Constraints

| Constraint | Impact | Approach |
|-----------|--------|----------|
| Framework is external | Cannot modify SDK directly in this repo | Create middleware layer in blobert codebase OR document required SDK changes |
| Tool filtering must happen before agent sees tools | Agent contract must be transparent | Middleware intercepts tool list before framework invokes agent |
| Backward compatibility required | Existing agents (no category declaration) must work | Default behavior: if no category extracted, provide all tools |
| Determinism required | Same category → same tool list every time | Use `tool_category_manager.get_tools_for_category()` directly (already deterministic) |
| Regex extraction from prompt | Agent declares category in prompt text | Implement regex pattern as middleware function |

### 5. Critical Ambiguities Requiring Spec Agent Clarification

| # | Ambiguity | Assumption Made | Confidence |
|---|-----------|-----------------|-----------|
| A1 | Where exactly is the agent invocation code (specific file/framework)? | Agent framework is external (Claude Code/SDK); blobert will create **middleware layer** or **invocation wrapper** in repo | LOW (must be confirmed by Spec Agent or orchestration owner) |
| A2 | Is "framework modification" in ticket scope, or integration-only? | Scope is **integration in blobert codebase only**; if SDK modification is needed, that's external and out of scope | MEDIUM |
| A3 | What tool schema format does framework use? | Opaque JSON-serializable dicts (per M902-18 spec); `tool_category_manager.py` returns `list[dict[str, Any]]` | MEDIUM-HIGH |
| A4 | Should filtered tools go into a separate agent param, or replace the main tools param? | Replace main tools param (agent sees only category-filtered schema) | MEDIUM |
| A5 | Where should middleware live in blobert codebase? | `ci/scripts/agent_invocation_middleware.py` (new module) OR `ci/scripts/tool_category_manager.py` (extend existing) | MEDIUM (Spec Agent decides) |

---

## Execution Plan Overview

**Three Phases:**

### Phase 1: Specification (Spec Agent — Task 1)
- **Objective:** Formalize the exact integration approach and API contract
- **Inputs:** This checkpoint, M902-18 spec, integration guide, tool_category_manager.py
- **Outputs:** 
  - `project_board/specs/902_18T5_tool_categorization_framework_integration_spec.md`
  - Spec defines: middleware location, invocation contract, error handling, test strategy
- **Success Criteria:** Spec unambiguously answers all 5 ambiguities (A1–A5)

### Phase 2: Test Design (Test Designer — Task 2)
- **Objective:** Write tests that verify framework integration end-to-end
- **Inputs:** Spec from Phase 1, existing tool_categorization tests as reference
- **Outputs:** `tests/ci/test_agent_framework_integration.py`
- **Test Scenarios:**
  1. Agent declares category in prompt → receives filtered tools
  2. Agent omits category declaration → receives all tools (backward compatible)
  3. Invalid category declaration → falls back to all tools with warning
  4. Regex extraction from various prompt formats
  5. Tool filtering determinism (same category across runs)
  6. Integration with existing agent pipeline

### Phase 3: Implementation (Integration Agent — Task 3)
- **Objective:** Implement middleware/wrapper to wire framework to tool categorization
- **Inputs:** Spec + tests from Phases 1–2, tool_category_manager.py
- **Outputs:** 
  - Middleware module (location TBD by Spec Agent)
  - Framework integration integration test passing
  - At least 1 agent invocation successfully filters tools
  - Backward compatibility verified
- **Success Criteria:** All AC from ticket satisfied, tests passing

### Phase 4: Validation & Runbook (Documentation — Task 4)
- **Objective:** Document integration and update M902-08 runbook
- **Outputs:** Updated `project_board/checkpoints/M902-18/INTEGRATION_GUIDE.md` with framework integration section
- **Success Criteria:** Future agents can declare categories and use filtered tools

---

## Risk & Assumptions Summary

### Risks (R)

| # | Risk | Impact | Mitigation |
|---|------|--------|-----------|
| R1 | Agent framework location never discovered (framework is proprietary/closed) | Cannot integrate; task blocks all downstream tickets | **Spec Agent must investigate:** Can framework accept tool filtering? Escalate to orchestration owner if unclear. Document findings in spec. If framework cannot be modified, define workaround (e.g., pre-invocation filtering at a different layer). |
| R2 | Framework tool schema format incompatible with tool_category_manager output | Tools don't filter correctly; agents get wrong tools | Tool category manager is flexible (returns `list[dict]`); can adapt output format in middleware if needed. Test Designer creates compatibility tests. |
| R3 | Regex extraction fails for legitimate agent prompts | Category declaration not recognized; agents don't get filtered tools | Regex pattern from spec is comprehensive; test multiple formats. Fallback to all tools (not hard fail). |
| R4 | Backward compatibility broken (agents without categories lose tools) | Regression in agent capability; failures in M902-19+ | **Non-negotiable:** Default behavior must be "all tools" if no category detected. Tests explicitly validate backward compat. |
| R5 | Integration test cannot access actual agent framework (external system) | Cannot verify real agent receives filtered tools | Test Designer creates **mock/simulated agent** tests. Real agent integration deferred to live testing in M902-19+ (per M902-18 AC-7 design). |

### Assumptions (As)

| # | Assumption | Rationale | Confidence |
|----|-----------|-----------|-----------|
| As1 | Framework accepts optional parameter or can be wrapped with middleware | Otherwise integration is impossible. Spec Agent must validate this. | LOW |
| As2 | Tool schema format is JSON-serializable dict or compatible | M902-18 spec and all tests use this format; framework likely compatible. | MEDIUM-HIGH |
| As3 | Regex extraction from prompt text is sufficient for category declaration | Spec (Req 5) freezes regex pattern; tests can validate extraction. | MEDIUM-HIGH |
| As4 | Determinism of tool_category_manager is sufficient (no randomization needed) | Already proven in 180 tests; same category always returns same tools. | HIGH |
| As5 | Integration scope is blobert codebase only; external SDK changes are out of scope | Ticket explicitly says "Modify agent framework" but context suggests integration within blobert. Spec Agent must clarify. | MEDIUM |

---

## Next Steps & Handoff

### Immediate (Before Spec Agent Starts)

1. **Route this checkpoint to Spec Agent**
   - File path: `project_board/checkpoints/M902-18-T5/2026-05-20T-planning-discovery-checkpoint.md`
   - Context: Agent framework is external; integration must happen via blobert middleware/wrapper

2. **Spec Agent's Primary Task**
   - Read this checkpoint + ticket + M902-18 spec
   - Investigate agent framework invocation mechanism (may require orchestration team input)
   - Resolve ambiguities A1–A5 in specification
   - Define exact middleware location and API contract
   - Freeze specification

### Decision Points for Spec Agent

**If framework is modifiable in blobert codebase:**
- Location: `ci/scripts/agent_invocation_wrapper.py` (new) or extend `gate_runner.py`
- Approach: Modify invocation code to accept `tool_category` param

**If framework is external (Claude Code/SDK):**
- Location: `ci/scripts/agent_invocation_middleware.py` (new) — thin adapter layer
- Approach: Middleware intercepts agent call, extracts category from prompt, filters tools, passes filtered tools to framework

**If framework cannot be modified:**
- Escalate: Route to Human with "Framework integration impossible without external changes"
- Document: In spec, with evidence (framework version, constraints, SDK version)
- Fallback: Plan M902-18-T5-v2 for workaround approach

---

## Files & References

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/00_backlog/18a_tool_categorization_framework_integration.md`

**Specification (for context):** `project_board/specs/902_18_tool_categorization_spec.md` (Requirements 4 & 5)

**Integration Guide:** `project_board/checkpoints/M902-18/INTEGRATION_GUIDE.md`

**Implementation (ready):** 
- `ci/scripts/tool_categories.json`
- `ci/scripts/tool_category_manager.py`
- `tests/ci/test_tool_categorization*.py` (180 tests, reference patterns)

**Execution Plan (to be generated):** 
- `project_board/execution_plans/M902-18T5_tool_categorization_framework_integration.md` (Planner responsibility in subsequent run)

---

## Conclusion

**Discovery Complete. Framework is External. Ready for Spec Agent.**

The tool categorization backend (M902-18 Tasks 1-4) is production-ready with 180 passing tests. Task 5 (framework integration) cannot proceed without discovering the exact agent invocation mechanism. Evidence strongly suggests the framework is external (Claude Code or Claude Agent SDK), requiring a middleware integration approach in blobert codebase. Spec Agent must validate this assumption and define the integration contract. Once specification is frozen, remaining tasks (Test Design, Implementation, Documentation) can proceed in parallel.

**Confidence in Discovery:** MEDIUM-HIGH (framework location is external, but exact integration approach TBD by Spec Agent)

**Blocker Status:** None yet. Framework discovery is the prerequisite. If framework is inaccessible, this will become a blocker.

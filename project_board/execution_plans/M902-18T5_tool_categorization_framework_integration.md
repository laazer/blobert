# Execution Plan: M902-18-T5 Tool Categorization Framework Integration

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/00_backlog/18a_tool_categorization_framework_integration.md`

**Status:** PLANNING COMPLETE  
**Revision:** 1  
**Date:** 2026-05-20  
**Next Agent:** Spec Agent  
**Checkpoint:** `project_board/checkpoints/M902-18-T5/2026-05-20T-planning-discovery-checkpoint.md`

---

## Executive Summary

**Objective:** Integrate the tool categorization system (implemented in M902-18 Tasks 1-4) into the Claude agent framework. This is a two-part discovery + integration challenge:

1. **Discovery Phase:** Locate agent invocation code (currently unknown location; likely external)
2. **Integration Phase:** Modify framework to accept tool_category parameter, extract categories from prompts, wire filtered tools into execution

**Scope Clarification:** The agent framework appears to be external (Claude Code / Claude Agent SDK). Integration will likely require a middleware layer in the blobert codebase. Spec Agent must validate this assumption and define the exact integration approach.

**Key Blockers:** Agent framework location is unknown. Cannot proceed to implementation without Spec Agent clarifying framework accessibility and invocation mechanism.

---

## Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| **1** | **Specification: Formalize Framework Integration Approach** | Spec Agent | M902-18 ticket, this execution plan, discovery checkpoint, M902-18 spec (Req 4 & 5), integration guide, tool_category_manager.py, existing test patterns | Specification document: `project_board/specs/902_18T5_tool_categorization_framework_integration_spec.md` with: (a) Framework location identified or escalation documented, (b) Invocation contract frozen (params, return values, error handling), (c) Middleware location defined (if needed), (d) Category extraction regex finalized, (e) Tool filtering API contract, (f) Backward compatibility strategy, (g) Error handling policy, (h) Test strategy outline. | None (start here) | Spec unambiguously answers: Where is agent invocation code? Is framework modifiable? What is tool schema format? Where should middleware live? Can framework be wrapped? All 5 ambiguities (A1–A5 from checkpoint) resolved with medium+ confidence. **AC Exit Gate:** `python ci/scripts/spec_completeness_check.py <spec_path> --type api` must pass. | **A1 (Framework location unknown):** Spec Agent must investigate Claude Code / Claude Agent SDK. If external and closed, document constraints and escalate. **A2 (SDK modification scope):** Clarify if scope is blobert-only or if external changes needed. **A3 (Tool schema format):** Confirm format compatibility. **A4 (Filtered tools param):** Define exact integration point. **A5 (Middleware location):** Decide on codebase structure. Confidence: LOW → MEDIUM-HIGH after Spec completion. |
| **2** | **Test Design: Write Framework Integration Tests** | Test Designer | Specification from Task 1, existing tool_categorization tests (reference patterns), test_agent_review_integration.py (gate framework example) | Test file: `tests/ci/test_agent_framework_integration.py` with: (a) 6+ test cases covering category declaration, regex extraction, invalid categories, backward compatibility, determinism, integration, (b) Mock/simulated agent framework (cannot test real framework externally), (c) Coverage of all AC from ticket (especially AC-3, AC-4, AC-5), (d) Adversarial tests for boundary conditions (malformed prompts, multiple category declarations, etc.), (e) Performance baselines. | Task 1 (Spec complete) | All test cases executable. Test file imports and runs successfully. Covers all code paths in future middleware. Zero flakes (deterministic). **Confidence:** Tests verify behavior, not documentation prose (per workflow_enforcement_v1.md). | **R5 (Cannot test real framework):** Design tests for mock/simulated agent. Real integration testing deferred to M902-19+ (per spec AC-7 design). **Determinism:** Tests validate same category returns same tools across runs. |
| **3** | **Implementation: Build Middleware & Wire Framework** | Integration Agent (aka Implementation Agent for generalist work) | Specification (Task 1), tests (Task 2), tool_category_manager.py, M902-18 spec (Req 4 & 5) | Middleware module (location per spec): (a) Module accepting agent invocation params (prompt, agent_type, existing tools), (b) Regex extraction function implementing pattern from spec (Req 5), (c) Invocation wrapper that: (i) extracts category from prompt, (ii) calls `get_tools_for_category(category)` if valid, (iii) filters tools, (iv) passes filtered tools to framework, (v) falls back to all tools if category invalid (fail-safe), (d) All tests from Task 2 passing, (e) Backward compatibility verified (agents without category declaration get all tools), (f) Integration test showing at least 1 agent successfully receives filtered tools, (g) No regressions in existing agent invocations. **Artifact**: Commit message documenting middleware purpose & integration point. | Task 1 (Spec), Task 2 (Tests) | All code follows CLAUDE.md (Python style: typed, documented, no bare except). All tests passing. No errors in tool filtering logic. Determinism verified (same category → same tools across 5+ runs). Code review clean. Diff-cover passes (python test coverage gate). | **R2 (Schema incompatibility):** Middleware adapts output format if needed. Tests validate compatibility. **R4 (Backward compat broken):** Strict: Default = all tools if no category. Tests enforce this. **As1 (Framework wrappable):** Implementation assumes middleware can intercept and modify tools before framework invokes agent. If false, escalate. |
| **4** | **Documentation & Runbook Update** | Integration Agent (or Documenter) | Specification (Task 1), implementation code (Task 3), M902-18 integration guide | Updated INTEGRATION_GUIDE.md at `project_board/checkpoints/M902-18/INTEGRATION_GUIDE.md` with new section: **Task 5 Integration Summary** including: (a) Framework integration location (middleware file), (b) API contract (how agents declare categories), (c) Regex pattern reference, (d) Example agent prompts showing category declaration, (e) Fallback behavior (invalid category = all tools), (f) Test execution instructions, (g) Runbook for M902-08 (referenced in ticket AC; TBD: confirm M902-08 exists and update if needed), (h) Next steps for M902-19+ (how to use categorized tools). **Artifact:** Markdown file with clear examples. | Task 3 (Implementation complete) | Document is accurate (reflects actual implementation), clear to future agents, includes working examples, references spec sections. No dead links. | Integration Guide is internal docs (not a test artifact). Update is contextual (explains integration to downstream readers). No ambiguity for M902-19+ readers. |
| **5** | **Acceptance Criteria Validation (AC Gatekeeper)** | AC Gatekeeper Agent | All prior task outputs (Tasks 1–4), ticket acceptance criteria | Validation report: AC checklist with 8/8 ACs marked PASS or BLOCKED with evidence. Each AC mapped to: (a) Code location, (b) Test file + line number, (c) Test execution result, (d) Evidence artifact (checkpoint, test output, code review). | Tasks 1–4 complete | All 8 ACs from ticket satisfied: ✅ Framework location identified, ✅ Framework accepts tool_category parameter, ✅ Category declaration regex implemented, ✅ Invalid categories handled gracefully, ✅ get_tools_for_category() callable from context, ✅ Framework passes filtered tools to agent, ✅ Backward compatibility verified, ✅ At least 1 test agent successfully declares category. | **R1 (Framework inaccessible):** If AC-1 (framework location) cannot be satisfied, escalate to BLOCKED. Mark blocking issues in ticket. Do not mark COMPLETE if framework location is unknown. |

---

## Detailed Task Specifications

### Task 1: Specification — Framework Integration Approach

**Objective:** Formalize where and how tool categorization integrates with agent invocation.

**Critical Questions to Answer:**

1. **Q1 (Framework Location):** Where is the agent invocation code?
   - Claude Code IDE integration?
   - Claude Agent SDK in external library?
   - Custom orchestrator in blobert?
   - Unknown?
   - **Evidence needed:** File path, module name, framework version.

2. **Q2 (Modifiability):** Can the framework be modified in blobert, or is it external?
   - If in blobert: Modify existing invocation code directly.
   - If external: Create middleware wrapper layer.
   - If closed/inaccessible: Escalate and document constraints.

3. **Q3 (Tool Schema Format):** What format does framework use for tools?
   - JSON dict (per M902-18 spec assumption)?
   - Opaque Tool type?
   - Other?
   - **Evidence needed:** Framework API docs or code inspection.

4. **Q4 (Invocation API):** How does framework accept parameters?
   - Parameters: `invoke_agent(agent_type, prompt, tools, ...)`?
   - Keyword args?
   - Context object?
   - **Evidence needed:** Framework API signature or usage example.

5. **Q5 (Integration Point):** Where should category filtering happen?
   - Pre-invocation (filter tools before passing to framework)?
   - Post-invocation (intercept after framework, before agent sees tools)?
   - Inline (middleware layer)?

**Spec Output Format:** Use template structure (similar to M902-18 spec or M902-17 spec). Must include:

- **Requirement 1:** Framework Location & Accessibility
  - Where invocation code lives
  - How it's invoked
  - Whether it can be modified
  
- **Requirement 2:** Invocation Contract
  - Framework API signature
  - Parameters (including new tool_category param)
  - Return values
  - Error handling
  
- **Requirement 3:** Tool Filtering API
  - Integration with tool_category_manager.py
  - Tool schema transformation
  - Determinism guarantees
  
- **Requirement 4:** Category Extraction
  - Regex pattern (from spec: `(?:I declare tool category|My workflow category is|Tool category):\s*(\w+)`)
  - Extraction function contract
  - Error handling (invalid category → all tools, log warning)
  
- **Requirement 5:** Backward Compatibility
  - Agents without category declaration must work unchanged
  - Default behavior (no category = all tools)
  - Version compatibility
  
- **Requirement 6:** Implementation Approach
  - Middleware location (if needed)
  - Code structure
  - Dependencies
  
- **Requirement 7:** Test Strategy
  - Approach for testing external framework (mock/simulate)
  - Coverage targets
  - Integration points
  
- **Acceptance Criteria:** 8 ACs (from ticket) mapped to spec requirements

**Spec Exit Gate:** Must pass `spec_completeness_check.py --type api` before Test Designer begins. If framework location is unknown, spec can document this as a blocker, but must include clear escalation path.

---

### Task 2: Test Design — Framework Integration Test Suite

**Objective:** Write comprehensive tests for framework integration, including mock/simulated agent framework.

**Test Scenarios:**

| Scenario | Test Name | Input | Expected Behavior | Reference |
|----------|-----------|-------|-------------------|-----------|
| **1** | Category declaration extracted & filtered | Prompt: "I declare tool category: parse\n\nWrite a spec..." | Agent receives only parse tools (read, glob, grep) | Spec Req 4, AC-3 |
| **2** | Multiple category formats accepted | Prompts: "I declare tool category: test", "My workflow category is: modify", "Tool category: plan" | All three formats extract correctly | Spec Req 5, AC-5 |
| **3** | Invalid category falls back gracefully | Prompt: "I declare tool category: invalid_category" | Warning logged, all tools provided (fail-safe) | Spec Req 4, AC-4 |
| **4** | No category declaration → backward compatible | Prompt: "Write a spec..." (no category) | All tools provided unchanged | Spec Req 4, AC-2 |
| **5** | Category extraction determinism | Repeat 5x: extract "parse" from same prompt | All 5 extractions identical | Spec Req 4, AC-1 |
| **6** | Tool filtering determinism | Repeat 5x: filter tools for "modify" category | All 5 tool lists identical (same order, content) | Spec Req 3, AC-1 |
| **7** | Framework integration contract | Mock framework receives filtered tools | Mock agent sees only category tools in schema | Spec Req 2, AC-3 |
| **8** | get_tools_for_category() callable from context | Middleware calls `get_tools_for_category(category)` | Function called successfully, returns filtered list | Spec Req 3, AC-3 |
| **9** | Malformed prompt edge case | Prompt: "I declare tool category: " (no category name) | Handled gracefully (warning, all tools) | Spec Req 5, AC-4 |
| **10** | Multiple category declarations | Prompt: "I declare tool category: parse\nI declare tool category: modify" | First occurrence wins OR error (spec must define) | Spec Req 5, AC-5 |
| **11** | Case sensitivity test | Prompts: "parse" vs "Parse" vs "PARSE" | Only lowercase "parse" matches (per spec) | Spec Req 5, AC-5 |
| **12** | Integration with existing agent pipeline | Invoke agent via middleware, verify no breakage | Existing agent invocations continue to work | Spec Req 4, AC-2 |

**Test File Structure:**

```python
# tests/ci/test_agent_framework_integration.py

import pytest
from unittest.mock import MagicMock, patch

# Import functions to test
from ci.scripts.tool_category_manager import get_tools_for_category
# (and any new middleware functions per Task 3 implementation)

class TestCategoryExtraction:
    """Test regex pattern and category extraction from prompts."""
    
    def test_standard_declaration_format(self) -> None:
        """Test: 'I declare tool category: parse' extraction."""
        # Implementation: extract category from prompt, assert == "parse"
        pass
    
    def test_alternative_declaration_format(self) -> None:
        """Test: 'My workflow category is: test' extraction."""
        pass
    
    # ... more extraction tests

class TestToolFiltering:
    """Test tool schema filtering by category."""
    
    def test_parse_category_returns_correct_tools(self) -> None:
        """Test: parse category returns read, glob, grep."""
        tools = get_tools_for_category("parse")
        tool_names = [t["name"] for t in tools]
        assert "read" in tool_names
        assert "write" not in tool_names  # write is modify-only
        pass
    
    # ... more filtering tests

class TestFrameworkIntegration:
    """Test middleware integration with mock framework."""
    
    def test_middleware_filters_tools_before_framework(self) -> None:
        """Test: Middleware intercepts and filters tools before framework sees them."""
        # Mock framework
        mock_framework = MagicMock()
        
        # Call middleware with category declaration
        middleware_result = invoke_via_middleware(
            prompt="I declare tool category: parse\n\nWrite spec",
            agent_type="spec",
            framework=mock_framework
        )
        
        # Verify framework received filtered tools
        # (assertions depend on Task 3 implementation)
        pass
    
    def test_backward_compatibility_no_category(self) -> None:
        """Test: Agents without category declaration get all tools."""
        mock_framework = MagicMock()
        
        middleware_result = invoke_via_middleware(
            prompt="Write spec",  # No category declaration
            agent_type="spec",
            framework=mock_framework
        )
        
        # Verify framework received all tools (unchanged behavior)
        pass
    
    # ... more integration tests

class TestErrorHandling:
    """Test graceful degradation on errors."""
    
    def test_invalid_category_provides_all_tools(self) -> None:
        """Test: Invalid category falls back to all tools with warning."""
        # Extract "invalid_cat" from prompt
        # Verify: all tools provided, warning logged
        pass
    
    # ... more error handling tests
```

**Coverage Target:** 6+ scenarios, 12+ test cases, zero flakes (deterministic).

**Test Execution:** `pytest tests/ci/test_agent_framework_integration.py -v`

---

### Task 3: Implementation — Middleware & Framework Integration

**Objective:** Build the middleware/wrapper code to filter tools before agent invocation.

**Implementation Location:** (Determined by Spec Agent in Task 1)

**Option A (If framework modifiable in blobert):**
- Modify existing `ci/scripts/gate_runner.py` or similar invocation code
- Add `tool_category` parameter
- Add category extraction logic
- Add tool filtering before agent invocation

**Option B (If framework is external):**
- Create new file: `ci/scripts/agent_invocation_middleware.py`
- Middleware function: `invoke_agent_with_categories(prompt, agent_type, tools, ...)`
- Extract category from prompt
- Filter tools via `get_tools_for_category()`
- Pass filtered tools to framework

**Option C (If framework is inaccessible):**
- Document constraints in spec
- Escalate as BLOCKED
- Do not attempt implementation

**Pseudocode (Option B Middleware):**

```python
# ci/scripts/agent_invocation_middleware.py

import re
from typing import Any
from tool_category_manager import get_tools_for_category, VALID_CATEGORIES

CATEGORY_PATTERN = r"(?:I declare tool category|My workflow category is|Tool category):\s*(\w+)"

def extract_category_from_prompt(prompt: str) -> str | None:
    """Extract tool category from agent prompt.
    
    Returns:
        Category name if found and valid, None otherwise.
    """
    match = re.search(CATEGORY_PATTERN, prompt, re.IGNORECASE)
    if match:
        category = match.group(1).lower()
        if category in VALID_CATEGORIES:
            return category
        else:
            # Invalid category: log warning, return None (fall back to all tools)
            import logging
            logging.warning(f"Invalid tool category declared: {category}. Valid: {VALID_CATEGORIES}")
            return None
    return None

def invoke_agent_with_categories(
    agent_type: str,
    prompt: str,
    all_tools: list[dict[str, Any]],
    framework_invoke_fn,  # Framework's actual invocation function
    **framework_kwargs
) -> Any:
    """Invoke agent with tool category filtering.
    
    Args:
        agent_type: Type of agent (spec, test_designer, etc.)
        prompt: Agent input prompt (may contain category declaration)
        all_tools: All available tools (before filtering)
        framework_invoke_fn: Framework's actual invoke function
        **framework_kwargs: Additional framework parameters
    
    Returns:
        Framework result (opaque)
    """
    # Extract category from prompt
    category = extract_category_from_prompt(prompt)
    
    # Filter tools or use all tools
    if category:
        tools_to_use = get_tools_for_category(category)
        import logging
        logging.info(f"Agent {agent_type} declared category {category}: using {len(tools_to_use)} tools")
    else:
        tools_to_use = all_tools
        import logging
        logging.info(f"Agent {agent_type} using all {len(all_tools)} tools (no category declaration)")
    
    # Invoke framework with filtered tools
    return framework_invoke_fn(
        agent_type=agent_type,
        prompt=prompt,
        tools=tools_to_use,
        **framework_kwargs
    )
```

**Key Implementation Details:**

1. **Regex Pattern:** Implement from spec (Req 5)
2. **Category Validation:** Check against `VALID_CATEGORIES` from tool_category_manager
3. **Error Handling:** Invalid category → log warning, use all tools (fail-safe, not fail-hard)
4. **Backward Compatibility:** If no category in prompt, use all tools (unchanged)
5. **Logging:** Info-level for category extraction, warning-level for invalid categories
6. **Type Hints:** All functions typed per CLAUDE.md (Python style)
7. **Docstrings:** Clear purpose, args, returns, exceptions
8. **Testing:** All Task 2 tests must pass

**Acceptance Criteria Implementation:**

- ✅ AC-1 (Framework location identified): Code location documented
- ✅ AC-2 (Framework accepts tool_category param): Middleware accepts and uses parameter
- ✅ AC-3 (Regex implemented): Pattern from spec
- ✅ AC-4 (Invalid categories handled gracefully): Log warning, fall back to all tools
- ✅ AC-5 (get_tools_for_category() callable): Direct call in middleware
- ✅ AC-6 (Framework passes filtered tools): Middleware ensures this
- ✅ AC-7 (Backward compatibility verified): No category → all tools
- ✅ AC-8 (At least 1 agent successfully declares): Test case verifies

**Code Review Checklist:**
- No bare except blocks
- All exceptions logged or re-raised
- Type hints complete
- Docstrings clear and complete
- No side effects (pure functions)
- CLAUDE.md style conformance

---

### Task 4: Documentation — Integration Guide & Runbook

**Objective:** Update documentation for future agents (M902-19+) to understand and use categorized tools.

**Files to Update:**

1. **Primary:** `project_board/checkpoints/M902-18/INTEGRATION_GUIDE.md`
   - Add new section: **Task 5 Integration Complete**
   - Explain middleware location
   - Show example agent prompts with category declaration
   - Reference spec and implementation
   - Show how M902-19+ agents will use this

2. **Secondary (TBD):** M902-08 runbook (referenced in ticket AC-8)
   - Confirm M902-08 exists and path
   - Add section on framework integration
   - Link to tool categorization spec
   - Show category selection guide

**Documentation Template:**

```markdown
## Task 5 Integration Complete

**Date:** 2026-05-20 (or actual completion date)  
**Implementation:** Framework integration via middleware layer

### How Agents Declare Tool Categories

Agents can now declare which tools they need by including a category declaration in their input prompt:

**Format:**
```
I declare tool category: <category>

[Rest of agent prompt...]
```

**Valid Categories:**
- `parse`: Read-only code exploration (Read, Glob, Grep, safe Bash)
- `modify`: File creation and modification (Write, Edit, safe Bash)
- `test`: Test execution and verification (Bash, test runners)
- `plan`: Task decomposition and history (Bash git operations, planning)
- `think`: Analysis and synthesis (Read, Glob, Grep, Bash, Agent delegation)

### Example Agent Prompts

**Spec Agent (declares "parse"):**
```
I declare tool category: parse

You are the Spec Agent. Your task is to write a detailed specification for ticket M902-19.
Read the existing codebase, search for related patterns, and synthesize requirements.
```
→ Agent receives: Read, Glob, Grep, safe Bash

**Implementation Agent (declares "modify"):**
```
I declare tool category: modify

You are the Implementation Agent. Implement the feature specified in the attached spec.
You can write new files and modify existing code.
```
→ Agent receives: Write, Edit, safe Bash

**Test Designer (declares "test"):**
```
I declare tool category: test

You are the Test Designer. Write comprehensive tests for the implementation.
You can execute test commands to validate behavior.
```
→ Agent receives: Bash (test runners), task management

### Fallback Behavior

If an agent **does not** declare a category, or declares an **invalid** category:
- Warning is logged (info level)
- Agent receives **all tools** (backward compatible)
- No failure; agent can proceed normally

### Implementation Details

**Middleware Location:** `ci/scripts/agent_invocation_middleware.py`

**Function:** `invoke_agent_with_categories(agent_type, prompt, all_tools, framework_invoke_fn, **kwargs)`

**Regex Pattern:** `(?:I declare tool category|My workflow category is|Tool category):\s*(\w+)`

**Tool Filtering:** Uses `tool_category_manager.get_tools_for_category(category)`

### For M902-19+ Implementers

When implementing downstream tickets:

1. **Declare your agent's category** in the prompt (optional, but recommended)
2. **Rely on filtered tools** for your task (category-specific subset)
3. **Verify in checkpoint logs** that your declared category was extracted
4. **Measure context reduction** using `tool_category_manager.measure_tool_schema_reduction(category)`
5. **Report baseline/filtered bytes** in your implementation checkpoint

### Reference

- **Specification:** `project_board/specs/902_18_tool_categorization_spec.md` (Req 4 & 5)
- **Implementation:** `ci/scripts/agent_invocation_middleware.py`
- **Tool Manager:** `ci/scripts/tool_category_manager.py`
- **Tests:** `tests/ci/test_agent_framework_integration.py`
- **Category Config:** `ci/scripts/tool_categories.json`
```

---

### Task 5: Acceptance Criteria Validation (AC Gatekeeper)

**Objective:** Verify all 8 ticket ACs are satisfied with evidence.

**AC Checklist:**

| # | AC | Evidence | Status |
|---|----|-----------|----|
| 1 | Agent framework location identified and documented in checkpoint | File path in Task 1 spec; checkpoint explaining location | ✅/❌ |
| 2 | Framework accepts optional `tool_category` parameter in agent invocation | Code in Task 3; test in Task 2 | ✅/❌ |
| 3 | Category declaration regex implemented: pattern from spec | Code in Task 3; pattern matches spec; tests | ✅/❌ |
| 4 | Invalid categories handled gracefully (log warning, provide all tools, no hard fail) | Code in Task 3; test case in Task 2; log output | ✅/❌ |
| 5 | `get_tools_for_category()` callable from agent invocation context | Code in Task 3 calls function; tests verify | ✅/❌ |
| 6 | Framework passes filtered tools to agent before execution | Integration test in Task 2; mock framework verifies | ✅/❌ |
| 7 | Backward compatibility verified: agents without category declaration work unchanged | Test case in Task 2; behavior matches pre-Task 5 | ✅/❌ |
| 8 | At least 1 test agent successfully declares category and receives filtered tools | Test case in Task 2; test passes; checkpoint logged | ✅/❌ |

**Validation Report Format:**

```markdown
# M902-18-T5: Tool Categorization Framework Integration — AC Validation Report

**Date:** [Completion date]  
**Validator:** AC Gatekeeper  
**Status:** ✅ ALL ACs PASSED (8/8) OR ❌ BLOCKED (N/8)

## AC Evidence Matrix

| AC | Status | Evidence File | Line(s) | Test Result | Notes |
|----|--------|---------------|---------|-------------|-------|
| 1 | ✅/❌ | project_board/checkpoints/M902-18-T5/... | ... | PASS/FAIL | ... |
| 2 | ✅/❌ | ci/scripts/agent_invocation_middleware.py | ... | PASS/FAIL | ... |
| ... | ... | ... | ... | ... | ... |
| 8 | ✅/❌ | tests/ci/test_agent_framework_integration.py | ... | PASS/FAIL | ... |

## Summary

**All 8 ACs Satisfied:** ✅
**Integration Complete:** ✅
**Ready for M902-18 Task 6 (Static QA):** ✅
**Ready for M902-19+ Unblocking:** ✅
```

**Blocking Criteria:**

If any AC cannot be satisfied:
- Set Stage to `BLOCKED` in ticket
- Document blocking issue in "Blocking Issues" field
- Provide clear remediation path
- Route to Human for decision (continue work to resolve, or escalate)

---

## Critical Success Factors

1. **Framework Location Must Be Found:** Without knowing where agents are invoked, integration is impossible. Spec Agent's primary responsibility.

2. **Regex Extraction Must Be Robust:** Pattern must match all valid declaration formats from spec and degrade gracefully on malformed input.

3. **Backward Compatibility Non-Negotiable:** Agents without category declaration MUST get all tools unchanged. No regression.

4. **Determinism Proven:** Same category declaration must always return identical tool list. Verified via repeated invocations.

5. **Fail-Safe Error Handling:** Invalid categories must not break agent execution. Log warning, provide all tools.

---

## Risk Mitigation Summary

| Risk | Mitigation | Owned By |
|------|-----------|----------|
| **R1: Framework inaccessible** | Spec Agent investigates & documents constraints. Escalate if needed. | Spec Agent |
| **R2: Schema incompatibility** | Middleware adapts output format. Tests validate. | Integration Agent + Test Designer |
| **R3: Regex extraction fails** | Comprehensive regex pattern from spec. Adversarial tests (malformed prompts). | Test Designer + Integration Agent |
| **R4: Backward compat broken** | Default = all tools if no category. Tests strictly enforce. | Integration Agent + AC Gatekeeper |
| **R5: Cannot test real framework** | Mock/simulated agent tests. Real integration deferred to M902-19+. | Test Designer |

---

## Timeline & Handoff

### Phase 1: Specification (Task 1 — Spec Agent)
- **Input:** This execution plan + discovery checkpoint
- **Output:** `project_board/specs/902_18T5_tool_categorization_framework_integration_spec.md`
- **Duration:** 1 run (typical)
- **Exit Gate:** `spec_completeness_check.py --type api` passes

### Phase 2: Test Design (Task 2 — Test Designer)
- **Input:** Spec from Phase 1
- **Output:** `tests/ci/test_agent_framework_integration.py` (6+ scenarios, 12+ tests)
- **Duration:** 1 run (typical)
- **Gate:** No exit gate; ready for Phase 3

### Phase 3: Implementation (Task 3 — Integration Agent)
- **Input:** Spec + tests from Phases 1–2
- **Output:** Middleware module + passing tests + backward compat verified
- **Duration:** 1–2 runs (depends on framework complexity)
- **Gate:** All tests passing, diff-cover gate passes

### Phase 4: Documentation (Task 4 — Documentation Agent)
- **Input:** Implementation from Phase 3
- **Output:** Updated INTEGRATION_GUIDE.md
- **Duration:** 1 run (typical)
- **Gate:** None; informational

### Phase 5: Validation (Task 5 — AC Gatekeeper)
- **Input:** All prior task outputs
- **Output:** AC validation report
- **Duration:** 1 run (typical)
- **Gate:** All ACs must pass; if blocked, route to Human

---

## Unblocking M902-18

**When Task 5 completes successfully:**

1. Ticket M902-18 advances to `Stage = IMPLEMENTATION` (Task 5 complete, ready for Task 6 Static QA)
2. M902-19, M902-20, ... can begin implementation (framework integration prerequisite satisfied)
3. All downstream agents can declare tool categories in their prompts
4. Tool categorization feature is production-ready

---

## Files & Resources

### Existing (Ready to Use)
- `ci/scripts/tool_categories.json` — Normative tool-to-category mappings
- `ci/scripts/tool_category_manager.py` — `get_tools_for_category()` and measurement functions
- `tests/ci/test_tool_categorization*.py` — 180 passing tests (reference patterns)
- `project_board/checkpoints/M902-18/INTEGRATION_GUIDE.md` — Initial integration guide

### To Be Created (By Tasks 1–4)
- `project_board/specs/902_18T5_tool_categorization_framework_integration_spec.md` (Task 1)
- `tests/ci/test_agent_framework_integration.py` (Task 2)
- `ci/scripts/agent_invocation_middleware.py` or modified existing file (Task 3)
- Updated `project_board/checkpoints/M902-18/INTEGRATION_GUIDE.md` (Task 4)

### Checkpoints & Evidence
- `project_board/checkpoints/M902-18-T5/2026-05-20T-planning-discovery-checkpoint.md` (Planner, this run)
- `project_board/checkpoints/M902-18-T5/` (Spec, Test, Implementation, AC Gatekeeper checkpoints to follow)

---

## Approval & Status

**Execution Plan Status:** ✅ APPROVED & READY FOR EXECUTION

**Assigned To:** Spec Agent (Task 1)

**Next Action:** Spec Agent reads this plan + discovery checkpoint + referenced tickets and begins formalization of framework integration approach.

**Confidence Level:** MEDIUM-HIGH (framework discovery is the primary unknown; all other tasks are well-defined once spec is frozen)

---

**Plan Author:** Planner Agent  
**Date:** 2026-05-20  
**Revision:** 1

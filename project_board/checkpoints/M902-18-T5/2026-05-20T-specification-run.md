# M902-18-T5: Tool Categorization Framework Integration — Specification Run

**Ticket:** M902-18-T5 (Stage: SPECIFICATION)

**Run Date:** 2026-05-20  
**Stage:** SPECIFICATION  
**Agent:** Spec Agent (Autonomous Mode)

---

## Ambiguity Resolutions (A1–A5)

Based on planning checkpoint, discovery evidence, and M902-18 specification context.

### A1: Is Framework Modifiable or Must Middleware Wrap It?

**Would have asked:** Can the external Claude Code / Claude Agent SDK accept tool filtering parameters, or must we create a wrapper layer in blobert?

**Assumption made:** Framework is external and **not directly modifiable within blobert scope**. Integration approach: Create middleware layer (`ci/scripts/agent_invocation_middleware.py`) that:
1. Intercepts agent invocation calls (at the blobert → external framework boundary)
2. Extracts category from prompt
3. Filters tools via `get_tools_for_category()`
4. Passes filtered tools to framework

This layer sits in blobert codebase and can be tested/mocked without access to external framework internals. External framework receives pre-filtered tools as standard parameter.

**Confidence:** HIGH (framework is external per discovery checkpoint; middleware approach is pragmatic and testable)

---

### A2: What Tool Schema Format Does Framework Expect?

**Would have asked:** Does the framework accept `list[dict[str, Any]]` (JSON-like) or a proprietary Tool type?

**Assumption made:** Framework accepts **opaque JSON-serializable structures** (dict-like or native SDK Tool objects). The `tool_category_manager.py` already returns `list[dict[str, Any]]`, which is compatible with JSON serialization. Middleware will pass this directly to framework; if framework wraps in SDK types, that's framework's responsibility, not blobert's.

**Confidence:** MEDIUM-HIGH (M902-18 spec and 180 passing tests use `list[dict[str, Any]]` format; safe assumption)

---

### A3: Can We Hook Into Agent Invocation or Must We Wrap Externally?

**Would have asked:** Where exactly is the agent invocation boundary—is it a function call, an API, a configuration setting?

**Assumption made:** Since framework is external (Claude Code / Claude Agent SDK), blobert cannot directly hook into framework internals. Instead, **middleware wraps at the blobert → framework boundary**. This means:
- Agents in blobert code path (not directly here, but future tickets) will call middleware function
- Middleware extracts category, filters tools, then delegates to framework invocation
- Framework never needs modification; it just sees pre-filtered tools

**Confidence:** MEDIUM (framework boundary is somewhat opaque, but wrapping approach is standard and testable)

---

### A4: How Does Filtered Tool List Get Passed to Agent Runtime?

**Would have asked:** Is there a separate `tool_category` parameter, or does filtered list replace the main tools param?

**Assumption made:** Filtered tools **replace the main tools parameter** in the framework invocation. Middleware's responsibility:
1. Extract category from prompt
2. Call `get_tools_for_category(category)` to get filtered list
3. Pass filtered list as the `tools` parameter to framework (replacing default all-tools list)
4. If no category declared, pass all tools (backward compatible)

Framework receives tools in the same format it normally does; it never knows category filtering happened.

**Confidence:** HIGH (this is the simplest and most compatible approach; matches M902-18 design intent)

---

### A5: Where Does Filtered Tool List Get Extracted—At What Layer?

**Would have asked:** Should category extraction happen in middleware, in agent code, or in framework?

**Assumption made:** Category extraction happens in **middleware** (not in external framework, not in blobert agent code). Middleware implements:
- Regex pattern: `(?:I declare tool category|My workflow category is|Tool category):\s*(\w+)`
- Pattern matching on agent input prompt
- Lowercasing and validation
- Graceful fallback to all tools if invalid

This keeps extraction logic in blobert (testable, maintainable) and external to framework (no SDK modification needed).

**Confidence:** HIGH (aligns with M902-18 Requirement 5 design; regex is well-defined and testable)

---

## Specification Output

**File:** `project_board/specs/902_18T5_tool_categorization_framework_integration_spec.md`

**Status:** COMPLETE (sections below)

All 8 ACs will be mapped explicitly in spec to requirements and test strategy.

---

## Checkpoint Log Summary

| Assumption | Confidence | Rationale |
|-----------|-----------|-----------|
| A1: Middleware layer (not SDK modification) | HIGH | Framework is external; middleware is pragmatic and testable |
| A2: Tool schema is JSON-serializable dict | MEDIUM-HIGH | M902-18 spec and tests confirm this format |
| A3: Wrap at blobert → framework boundary | MEDIUM | Standard approach; handles external system opacity |
| A4: Filtered tools replace main param | HIGH | Simplest integration; backward compatible |
| A5: Extract category in middleware | HIGH | Testable, maintainable; aligns with M902-18 Req 5 |

**Overall confidence in proceeding to Test Design:** HIGH-MEDIUM

Specification will be deterministic and directly actionable by Test Designer and Implementation agents.

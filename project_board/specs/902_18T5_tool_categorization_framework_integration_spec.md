# Spec: Tool Categorization Framework Integration

**Ticket:** M902-18-T5 (Tool Categorization Framework Integration)

**Milestone:** 902 — Agent Predictability Improvements

**Agent:** Spec Agent

**Date:** 2026-05-20

**Status:** SPECIFICATION

**Revision:** 1

---

## Executive Summary

This specification defines the integration of the tool categorization system (M902-18 Tasks 1–4, backend-complete) into the **external Claude Code / Claude Agent SDK** framework. The specification resolves five critical ambiguities from the planning phase and establishes a deterministic, testable middleware layer (`agent_invocation_middleware.py`) that:

1. **Extracts tool categories** from agent input prompts using regex
2. **Filters tools** via `get_tools_for_category()` from the production-ready tool_category_manager
3. **Passes filtered tools** to the external framework before agent invocation
4. **Handles errors gracefully** (invalid categories → all tools, log warning)
5. **Maintains backward compatibility** (agents without category declaration receive all tools)

The specification is **independent of external framework implementation details** (framework location, version, or modification scope) and focuses entirely on blobert's responsibility: the middleware layer that sits at the blobert → external framework boundary.

All 8 acceptance criteria are mapped to specific requirements and test strategy.

---

## Assumptions and Checkpoint Resolutions

| # | Ambiguity | Assumption | Confidence |
|---|-----------|-----------|-----------|
| A1 | Is framework modifiable or must middleware wrap it? | Framework is external; middleware layer in blobert wraps invocation boundary | HIGH |
| A2 | What tool schema format does framework expect? | JSON-serializable dicts (`list[dict[str, Any]]`); compatible with tool_category_manager output | MEDIUM-HIGH |
| A3 | Can we hook into agent invocation or must we wrap externally? | Wrap at blobert → framework boundary; framework never modified | MEDIUM |
| A4 | How does filtered tool list get passed to agent runtime? | Filtered list replaces main tools parameter; framework sees pre-filtered schema | HIGH |
| A5 | Where should middleware live in blobert codebase? | `ci/scripts/agent_invocation_middleware.py` (new module, imported by future invocation code) | HIGH |

All assumptions are conservative and testable without access to external framework internals.

---

## Requirement 1: Middleware Location and Integration Architecture

### 1. Spec Summary

**Description:** A middleware module in the blobert codebase that sits at the invocation boundary between blobert and the external Claude Code / Claude Agent SDK. The middleware intercepts agent invocation parameters, extracts category declarations from prompts, filters tools, and delegates to the external framework with filtered tools.

**Key architectural decisions:**
1. **Invocation boundary:** Middleware operates at the point where blobert prepares to call the external framework (exact framework location is external; blobert creates a wrapper that framework integrators can use).
2. **Non-invasive:** Middleware does not require modification to the external framework; it wraps at a logical boundary that framework integrators can adopt.
3. **Testability:** Middleware can be tested with mock frameworks; real framework integration is verified in downstream tickets (M902-19+).

**Constraints:**
- Middleware is **created within blobert codebase only**; no external SDK modification is in scope for this ticket.
- Middleware must handle the case where it cannot access the external framework (graceful degradation or escalation to error handling).
- Middleware is a thin adapter layer, not a full agent reimplementation.

**Assumptions:** 
- External framework accepts a `tools` parameter (or equivalent) in invocation.
- Middleware can be injected or called as a wrapper function in the agent invocation path.
- If framework integration cannot be completed in this ticket, the middleware is still produced and documented for integration in a future ticket.

**Scope:** Applies to all agent invocations in blobert that wish to use tool categorization (M902-18-T5 framework integration, M902-19+).

### 2. Acceptance Criteria

- **AC-1.1:** Middleware module created at `ci/scripts/agent_invocation_middleware.py` with clear docstrings explaining purpose and invocation boundary.
- **AC-1.2:** Middleware exports a primary function: `invoke_agent_with_category_filtering(agent_type, prompt, all_tools, framework_invocation_fn, **framework_kwargs) -> Any` with full type hints.
- **AC-1.3:** Function signature is well-defined: accepts agent type, prompt (may contain category declaration), all tools (before filtering), external framework function (to delegate to), and variable framework kwargs.
- **AC-1.4:** Middleware documentation includes example usage showing how framework integrators should import and call the function.
- **AC-1.5:** Middleware location (`ci/scripts/agent_invocation_middleware.py`) is documented in execution plan and checkpoint logs for future integration by M902-19+ agents.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R1.1:** Framework location is unknown or framework is inaccessible | Integration cannot proceed; Task 5 may be blocked | Spec clarifies: middleware is created in blobert; integration point is framework's responsibility. Middleware is ready to use; blocking issue escalated only if framework cannot be reached. |
| **R1.2:** Framework invocation signature differs from assumption (e.g., class method vs. function) | Middleware may not work with actual framework | Spec provides middleware as a flexible wrapper; framework integrators adapt the wrapper to their invocation pattern. Documentation includes adaptation examples. |
| **R1.3:** Middleware bloat (becomes too complex) | Difficult to test and maintain | Spec: middleware is a thin layer. All complex logic (category extraction, tool filtering) is delegated to purpose-built functions in tool_category_manager.py. |

### 4. Clarifying Questions

- **Q1:** Should middleware be a standalone function or a class with state? *Assumption: Standalone function (simplicity, stateless, composable with various frameworks).*
- **Q2:** Should middleware log every invocation or only errors/warnings? *Assumption: Log info-level category extraction (category found/not found) and warning-level errors (invalid category); agents can later reduce verbosity if needed.*

---

## Requirement 2: Category Extraction Function

### 1. Spec Summary

**Description:** A function that extracts tool category declarations from agent input prompts using a well-defined regex pattern. The function is deterministic, robust to malformed input, and integrates seamlessly with the middleware.

**Regex pattern (normative):**
```
(?:I declare tool category|My workflow category is|Tool category):\s*(\w+)
```

This pattern matches three declaration formats (all case-insensitive):
1. `I declare tool category: parse`
2. `My workflow category is: modify`
3. `Tool category: test`

The pattern is case-insensitive at the declaration level but extracted category is normalized to lowercase.

**Constraints:**
- Pattern must be case-insensitive for declaration keywords.
- Extracted category name is validated against `VALID_CATEGORIES` from tool_category_manager.
- If multiple declarations exist in the same prompt, **first match wins** (fail-fast, deterministic).
- If no match, function returns `None` (no category declared).
- Malformed declarations (e.g., `I declare tool category:` with no category name) are treated as no declaration.

**Assumptions:** 
- Prompts are text strings (no binary data).
- Category names in prompts are single word (alphanumeric + underscore, `\w+`).
- Regex is applied once per prompt per invocation (not iteratively).

**Scope:** Used by middleware to extract categories; also testable independently.

### 2. Acceptance Criteria

- **AC-2.1:** Function `extract_category_from_prompt(prompt: str) -> str | None` is defined in `ci/scripts/agent_invocation_middleware.py`.
- **AC-2.2:** Function uses the normative regex pattern (case-insensitive declaration, lowercase category extraction).
- **AC-2.3:** For valid declarations (e.g., "I declare tool category: parse"), function returns lowercase category name ("parse").
- **AC-2.4:** For multiple declarations in same prompt, first match is returned (deterministic, reproducible).
- **AC-2.5:** For malformed declarations (missing category name, e.g., "I declare tool category:"), function returns `None`.
- **AC-2.6:** For no declaration in prompt, function returns `None`.
- **AC-2.7:** For valid category name (one of parse/modify/test/plan/think), function validates via VALID_CATEGORIES and returns category if valid.
- **AC-2.8:** For invalid category name (not in VALID_CATEGORIES), function returns `None` (category extraction fails; middleware falls back to all tools per Requirement 4).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R2.1:** Regex too loose (false positives) | Legitimate text mistakenly parsed as category declaration | Regex requires exact keywords (I declare, My workflow, Tool category) and colon. Test includes negative cases (e.g., "My workflow category is excellent" → no match). |
| **R2.2:** Regex too strict (legitimate declarations not matched) | Agents cannot declare categories; fallback to all tools always | Regex is tested against all three declaration formats from spec. Test includes alternative whitespace variations (e.g., extra spaces). |
| **R2.3:** Case sensitivity breaks declarations | Agent writes "PARSE" but system expects "parse" | Extraction normalizes to lowercase. Case-insensitive flag in regex; validation is case-sensitive (spec freeze: categories are always lowercase). |
| **R2.4:** Determinism breaks (same prompt extracts different categories on retry) | Tests become flaky | Regex is stateless, deterministic. Python `re.search()` is deterministic. Test validates: extract same prompt 5x → same result. |

### 4. Clarifying Questions

- **Q3:** Should multi-line prompts be supported? *Assumption: Yes, regex is applied across entire prompt (MULTILINE mode in Python regex). Category declaration can be anywhere in prompt.*
- **Q4:** Should extracted category be lowercased even if agent writes "Parse"? *Assumption: Yes, always normalize to lowercase for matching against VALID_CATEGORIES.*

---

## Requirement 3: Tool Filtering Integration

### 1. Spec Summary

**Description:** The middleware integrates with `tool_category_manager.get_tools_for_category()` to filter tools based on extracted category. This requirement specifies the contract and error handling.

**Integration flow:**
1. Middleware extracts category from prompt (via Requirement 2)
2. If category is not None:
   - Call `get_tools_for_category(category)` from tool_category_manager
   - Validate return value (should be list of dicts)
   - Use returned tools as filtered tool schema
3. If category is None or extraction fails:
   - Use all tools (backward compatible)
   - Log info-level message (no category declared) or warning-level (invalid category)
4. Pass filtered tools to external framework

**Constraints:**
- Middleware must not modify tools after filtering (pass as-is from tool_category_manager).
- Tool filtering is deterministic: same category → same tool list (guaranteed by tool_category_manager).
- Filtering must occur **before framework invocation** (not after).
- Error handling is fail-safe: invalid category does not break agent execution.

**Assumptions:**
- `get_tools_for_category()` is production-ready (180 tests, 100% pass rate per M902-18).
- Tool format returned by tool_category_manager is compatible with framework's expected tool schema.
- Framework accepts a `tools` parameter (or middleware adapts the parameter name if needed).

**Scope:** Middleware invokes tool_category_manager; all tool filtering logic already exists and is frozen.

### 2. Acceptance Criteria

- **AC-3.1:** Middleware calls `get_tools_for_category(category)` when valid category is extracted from prompt.
- **AC-3.2:** Return value from `get_tools_for_category()` is passed directly to framework without modification.
- **AC-3.3:** If `get_tools_for_category()` raises `ValueError` (invalid category), middleware logs warning and falls back to all tools.
- **AC-3.4:** If `get_tools_for_category()` raises `RuntimeError` (config error), middleware logs error and falls back to all tools (fail-safe, not fail-hard).
- **AC-3.5:** Filtered tool list is passed to framework as the `tools` parameter (or equivalent, depending on framework signature).
- **AC-3.6:** If no category extracted (None), middleware passes all tools unchanged (backward compatible).
- **AC-3.7:** Tool filtering determinism is verified: same category extraction → identical tool list across repeated invocations.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R3.1:** Tool format incompatibility (middleware returns dict, framework expects different type) | Tools not recognized by framework; agent fails | Middleware passes tools as-is from tool_category_manager (which is compatible with JSON serialization). Test validates format. Framework integration adapts if needed. |
| **R3.2:** Exception handling incomplete (uncaught exception from get_tools_for_category) | Agent execution crashes | Middleware catches both ValueError and RuntimeError from tool_category_manager. Spec defines fail-safe behavior: fall back to all tools. |
| **R3.3:** Filtering performance degrades (get_tools_for_category is slow) | Agent invocation latency increases | tool_category_manager is already tested for performance (<10ms per spec AC). Middleware adds negligible overhead (single function call). |

### 4. Clarifying Questions

- **Q5:** Should middleware cache get_tools_for_category results? *Assumption: No caching in this ticket (freshness). Caching deferred to M903 performance optimization.*

---

## Requirement 4: Middleware Invocation Contract

### 1. Spec Summary

**Description:** The middleware's primary function signature, parameters, return values, and integration protocol.

**Primary function (normative):**
```python
def invoke_agent_with_category_filtering(
    agent_type: str,
    prompt: str,
    all_tools: list[dict[str, Any]],
    framework_invocation_fn: Callable[..., Any],
    **framework_kwargs: Any
) -> Any:
    """
    Invoke agent with tool category filtering.
    
    Extracts tool category from prompt, filters tools, and delegates to framework.
    
    Args:
        agent_type: Type of agent (e.g., "spec", "implementation", "test_designer")
        prompt: Agent input prompt (may contain category declaration)
        all_tools: All available tools before filtering
        framework_invocation_fn: Callable (function or method) that invokes the external framework
        **framework_kwargs: Additional kwargs to pass to framework_invocation_fn
    
    Returns:
        Result from framework_invocation_fn (opaque to middleware)
    
    Raises:
        Any exception raised by framework_invocation_fn is propagated as-is.
    """
```

**Invocation protocol:**
1. Middleware is imported and called by agent setup code (location TBD by implementation).
2. Agent setup code passes:
   - Agent type (string identifier)
   - Prompt (full agent input, possibly containing category declaration)
   - All available tools (default schema, pre-filtering)
   - Framework invocation function (callable that actually invokes the external framework)
   - Framework kwargs (any additional parameters the framework expects)
3. Middleware returns result from framework (opaque).
4. Calling code uses result as if it came directly from framework (transparent delegation).

**Backward compatibility mode:**
```python
# If framework integration not yet available, this should still work:
tools_to_use = all_tools  # No filtering
result = framework_invocation_fn(
    agent_type=agent_type,
    prompt=prompt,
    tools=tools_to_use,
    **framework_kwargs
)
```

**Constraints:**
- Middleware does not assume specific framework function signature; it's flexible and accepts **kwargs.
- Middleware must handle case where framework_invocation_fn is not callable (logs error, raises TypeError).
- Middleware must not modify prompt before passing to framework (category declaration remains intact for framework's awareness if needed).
- Framework result is returned as-is (no post-processing).

**Assumptions:**
- Framework function signature accepts `tools` as a parameter (or integration code adapts the parameter name).
- Calling code knows how to prepare all_tools and framework_invocation_fn correctly.

**Scope:** Defines the invocation boundary; integration code (in M902-19+) will adapt this to specific framework patterns.

### 2. Acceptance Criteria

- **AC-4.1:** Function `invoke_agent_with_category_filtering()` is defined with the exact signature above (type hints, docstring, parameters).
- **AC-4.2:** Function accepts `agent_type` (string), `prompt` (string), `all_tools` (list of dicts), `framework_invocation_fn` (callable), and `**framework_kwargs`.
- **AC-4.3:** Function extracts category from prompt using extract_category_from_prompt().
- **AC-4.4:** If category extracted and valid, function calls get_tools_for_category() and uses filtered tools.
- **AC-4.5:** If category not extracted or invalid, function uses all_tools unchanged.
- **AC-4.6:** Function calls framework_invocation_fn with parameters: agent_type, prompt, tools (filtered or all), plus framework_kwargs.
- **AC-4.7:** Function returns result from framework_invocation_fn without modification.
- **AC-4.8:** Function includes logging: info-level for category extraction (found/not found), warning-level for invalid categories.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R4.1:** Framework function signature incompatible (doesn't accept tools parameter) | Middleware cannot pass filtered tools correctly | Integration code (M902-19+) is responsible for adapting the signature. Middleware is flexible with **kwargs. If adapter is needed, it wraps the actual framework function. |
| **R4.2:** Calling code doesn't import middleware (continues using old invocation pattern) | Tool categorization is not used; no filtering happens | Spec defines middleware as a library function; M902-19+ agents must import and use it. Test suite validates usage. Documentation emphasizes adoption. |
| **R4.3:** Framework invocation fails (framework_invocation_fn raises exception) | Middleware propagates exception (expected) but doesn't mask error | Spec: middleware propagates framework exceptions as-is. No error suppression. Logging happens before invocation, so logs are available for debugging. |

### 4. Clarifying Questions

- **Q6:** Should middleware validate framework_invocation_fn is callable before calling it? *Assumption: Yes, middleware should check `callable(framework_invocation_fn)` and raise TypeError if not.*
- **Q7:** Should middleware catch and log framework exceptions before re-raising? *Assumption: No, let exceptions propagate; logging is handled pre-invocation (category extraction).*

---

## Requirement 5: Backward Compatibility and Default Behavior

### 1. Spec Summary

**Description:** Agents that do not declare a tool category must continue to work exactly as before, receiving all tools unchanged. This is a non-negotiable constraint.

**Default behavior (no category declaration):**
1. Prompt arrives without category declaration (or with invalid category).
2. Middleware extracts category → returns None.
3. Middleware logs info-level message: "Agent [agent_type] using all [N] tools (no category declaration)" or "Agent [agent_type] declared invalid category [X]; falling back to all tools."
4. Middleware passes all_tools to framework unchanged.
5. Framework receives all tools in schema (identical to pre-feature behavior).
6. Agent executes normally; category filtering is transparent.

**Constraints:**
- No breaking changes to agent invocation contracts.
- Agents without category declaration must behave identically to pre-feature agents.
- Category extraction must not pollute or modify agent output/reasoning.
- Opt-in adoption: agents adopt category declarations incrementally, not forced migration.

**Assumptions:**
- Existing agent prompts do not accidentally contain category declarations (unlikely; declaration syntax is specific).
- Framework is already tested with all tools; no regression expected when tools are filtered.

**Scope:** All agents, all invocations, all stages.

### 2. Acceptance Criteria

- **AC-5.1:** Test case exists: invoke middleware with prompt that has no category declaration → all tools passed to framework.
- **AC-5.2:** Test case exists: invoke middleware with prompt containing invalid category (e.g., "I declare tool category: invalid_cat") → warning logged, all tools passed.
- **AC-5.3:** Test case exists: pre-feature agent invocation (no middleware) works unchanged; if middleware is wrapped around it, result is identical.
- **AC-5.4:** Logging shows clear distinction: info-level for "no category" vs. warning-level for "invalid category".
- **AC-5.5:** No changes to agent code required to opt-in to backward compatibility; it is the default.
- **AC-5.6:** Test validates: 100 agents without category declarations → all receive all tools, no failures.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R5.1:** Backward compatibility broken (agents fail after middleware introduction) | Regression; deployment blocked | Test suite explicitly validates backward compatibility. Middleware default is all tools. No category = all tools. |
| **R5.2:** Category declaration accidentally triggers in old prompts | Unintended tool filtering breaks agents | Declaration syntax is specific and unlikely to appear naturally. Test includes negative cases: "My workflow category is excellent" should not trigger. |
| **R5.3:** Agents forced to adopt categories before ready | Adoption friction, slow rollout | Categories are optional. Runbook emphasizes opt-in. Early adopters (M902-18 agents) declare categories; others continue unchanged. |

### 4. Clarifying Questions

- **Q8:** Should middleware print to stdout/stderr or use logging module? *Assumption: Use Python logging module (standard, configurable, integrates with larger logging infrastructure).*

---

## Requirement 6: Error Handling and Fail-Safe Degradation

### 1. Spec Summary

**Description:** Middleware handles errors gracefully. Invalid categories, missing config, and framework errors do not break agent execution. Errors are logged at appropriate levels (warning for user errors, error for system errors).

**Error scenarios and handling:**

| Scenario | Error Type | Handler | Log Level | Outcome |
|----------|-----------|---------|-----------|---------|
| Invalid category (not in VALID_CATEGORIES) | ValueError from tool_category_manager | Catch, log, fall back | WARNING | All tools provided; agent continues |
| Config file missing (tool_categories.json) | RuntimeError from tool_category_manager | Catch, log, fall back | ERROR | All tools provided; agent continues |
| Config malformed (invalid JSON) | RuntimeError from tool_category_manager | Catch, log, fall back | ERROR | All tools provided; agent continues |
| Malformed prompt (regex doesn't match) | None (extraction returns None) | Handle normally | INFO | All tools provided; agent continues |
| framework_invocation_fn not callable | TypeError (middleware check) | Catch, log, re-raise | ERROR | Agent invocation fails; not masked |
| framework_invocation_fn raises exception | Any exception from framework | Log pre-invocation info, propagate | WARNING/ERROR | Framework exception propagates (transparent) |

**Constraints:**
- Category filtering errors do not break agent execution (fail-safe for category layer).
- Framework errors are **not masked** (framework is responsible for its own error handling).
- Logging must be informative for debugging but not verbose by default.
- All exceptions are logged or re-raised; no silent failures.

**Assumptions:**
- Logging module is available (standard library).
- Calling code has access to logging configuration (agents can adjust verbosity if needed).

**Scope:** All error paths in middleware.

### 2. Acceptance Criteria

- **AC-6.1:** Test case exists: invalid category declared → ValueError caught, warning logged, all tools provided.
- **AC-6.2:** Test case exists: config file missing → RuntimeError caught, error logged, all tools provided.
- **AC-6.3:** Test case exists: config malformed JSON → RuntimeError caught, error logged, all tools provided.
- **AC-6.4:** Test case exists: framework_invocation_fn is not callable → TypeError raised with clear message.
- **AC-6.5:** Test case exists: framework_invocation_fn raises exception → middleware logs pre-invocation info, exception propagates unchanged.
- **AC-6.6:** Log messages include agent_type and category (if extracted) for debugging.
- **AC-6.7:** No bare `except` blocks; all exceptions are explicitly caught and handled.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R6.1:** Errors logged but not visible (logging not configured) | Silent failures; debugging difficult | Calling code is responsible for logging configuration. Spec recommends logging at WARNING level for user errors (invalid category) and ERROR level for system errors (config missing). |
| **R6.2:** Error messages too vague (don't help debugging) | Hard to troubleshoot | Spec: log messages must include agent_type, extracted category (if any), error details, and fallback behavior. |
| **R6.3:** Fail-safe behavior masks real problems | Bugs in config are not caught in development | Tests validate: config file exists, JSON is valid, all categories are present, all tools are mapped. Validators run in test suite and CI. |

### 4. Clarifying Questions

- **Q9:** Should middleware validate all_tools parameter format before using? *Assumption: Minimal validation (must be list-like); detailed validation is framework's responsibility.*

---

## Requirement 7: Test Strategy and Coverage

### 1. Spec Summary

**Description:** Comprehensive test approach for middleware, including unit tests, integration tests, and mock agent framework validation.

**Test layers:**

**Layer 1: Unit Tests (extract_category_from_prompt)**
- Valid declaration formats (all three syntax variations)
- Case insensitivity
- Multiple declarations (first wins)
- Malformed declarations (no category name)
- Invalid categories (not in VALID_CATEGORIES)
- Negative cases (no false positives)
- Determinism (same prompt → same extraction)

**Layer 2: Unit Tests (tool filtering)**
- get_tools_for_category() called correctly
- Return value passed unchanged
- Exception handling (ValueError, RuntimeError)
- Fallback to all tools on error
- Determinism (same category → same tools)

**Layer 3: Unit Tests (middleware invocation)**
- Function signature matches spec
- Parameters accepted and validated
- Framework function called correctly
- Return value propagated
- Exception handling and logging

**Layer 4: Integration Tests (simulated agent framework)**
- Mock framework receives filtered tools
- Category extraction → tool filtering → framework invocation
- Backward compatibility (no category → all tools)
- Error scenarios (invalid category, config error)
- Determinism across repeated invocations

**Layer 5: Adversarial Tests**
- Edge cases: empty category name, whitespace-only prompt
- Boundary conditions: very large prompt, 1000+ tools
- Concurrency: multiple agents invoking middleware simultaneously
- Schema variations: different JSON serialization

**Constraints:**
- Tests must not require access to external framework (use mock).
- Tests must be deterministic (no flakes).
- Tests must be fast (<1s for full suite).
- Real framework integration is deferred to M902-19+ (out of scope for this ticket).

**Assumptions:**
- Python unittest.mock is available.
- Tool schema is JSON-serializable.

**Scope:** All middleware functionality, error paths, and edge cases.

### 2. Acceptance Criteria

- **AC-7.1:** Test file `tests/ci/test_agent_framework_integration.py` exists with 6+ test classes covering all layers.
- **AC-7.2:** Unit tests for extract_category_from_prompt cover all declaration formats, case variations, and malformed input.
- **AC-7.3:** Unit tests for tool filtering validate get_tools_for_category() invocation, error handling, and fallback behavior.
- **AC-7.4:** Unit tests for middleware contract validate function signature, parameter handling, and logging.
- **AC-7.5:** Integration tests validate category extraction → tool filtering → framework invocation with mock framework.
- **AC-7.6:** Integration tests verify backward compatibility (no category declaration → all tools).
- **AC-7.7:** Integration tests verify determinism: same invocation parameters → identical tools passed to framework.
- **AC-7.8:** Adversarial tests cover edge cases: empty category, whitespace, very large prompts, malformed scenarios.
- **AC-7.9:** All tests pass deterministically (run 3x → same results, zero flakes).
- **AC-7.10:** Test coverage includes error paths: invalid category, missing config, framework errors.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R7.1:** Mock framework doesn't accurately represent real framework | Tests pass but real integration fails | Spec provides mock framework pattern. Implementation Agent (M902-19+) validates against real framework. This ticket's tests are sufficient for middleware verification. |
| **R7.2:** Tests become flaky (randomness in mocks, timing issues) | CI failures, slow iterations | Middleware is deterministic. Tests use unittest.mock (deterministic). No sleep() or threading. Determinism explicitly tested. |
| **R7.3:** Test coverage incomplete (edge cases missed) | Bugs found in production (M902-19+) | Spec lists adversarial test scenarios. Test Designer uses this as checklist. Coverage target: all error paths, all declaration formats, all categories. |

### 4. Clarifying Questions

- **Q10:** Should test framework be pytest or unittest? *Assumption: pytest (modern, flexible, consistent with M902-18 test suite).*
- **Q11:** Should tests measure performance? *Assumption: Basic latency check (<10ms per invocation); detailed performance testing deferred to M903.*

---

## Requirement 8: Integration Documentation and Runbook

### 1. Spec Summary

**Description:** Clear documentation for framework integrators (M902-19+ agents and future implementation teams) on how to use middleware and integrate with external framework.

**Documentation content:**

1. **Framework Integration Overview**
   - What middleware does (extracts categories, filters tools)
   - Where middleware fits in agent invocation pipeline
   - When to use middleware vs. direct framework invocation

2. **API Usage Examples**
   - Importing middleware function
   - Calling with valid parameters
   - Handling results and errors
   - Backward compatibility (no category declaration)

3. **Integration Patterns**
   - Pattern A: Direct invocation (framework function passed as callable)
   - Pattern B: Wrapper adapter (if framework signature incompatible)
   - Pattern C: Configuration-based (if framework supports config overrides)

4. **Category Selection Guide**
   - Decision tree for choosing category
   - Example agent types and their categories
   - Fallback guidance (if category blocks needed tools)

5. **Troubleshooting**
   - Common issues (invalid category, config missing)
   - How to debug (enable logging, check category extraction)
   - When to escalate (framework issues)

6. **Metrics and Logging**
   - How to interpret log messages
   - How to measure context reduction
   - How to report results in checkpoint logs

**Constraints:**
- Documentation must be concise (< 5 pages) and actionable.
- Examples must be copy-paste-ready.
- Runbook must be in sync with code (updated if signature changes).

**Assumptions:**
- Framework integrators have access to INTEGRATION_GUIDE.md.
- Agents understand Python function calls and imports.

**Scope:** Applies to M902-19+ and any future agent that uses tool categorization.

### 2. Acceptance Criteria

- **AC-8.1:** Documentation file `project_board/checkpoints/M902-18/INTEGRATION_GUIDE_T5.md` (or section in existing INTEGRATION_GUIDE.md) exists.
- **AC-8.2:** Documentation includes "API Usage" section with function signature and example invocation.
- **AC-8.3:** Documentation includes "Integration Patterns" section showing how to call middleware.
- **AC-8.4:** Documentation includes "Category Selection Guide" with decision tree.
- **AC-8.5:** Documentation includes "Example Prompts" for different agent types declaring categories.
- **AC-8.6:** Documentation includes "Troubleshooting" section for common errors.
- **AC-8.7:** Documentation references specification (project_board/specs/902_18T5_tool_categorization_framework_integration_spec.md) for detailed requirements.
- **AC-8.8:** Documentation is clear and actionable (agents can integrate without asking clarifying questions).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R8.1:** Documentation is outdated (spec or code changes, docs not updated) | Agents follow wrong patterns, integration fails | Spec and docs are version-controlled. Changes must update both. Review checklist: spec change → docs update required. |
| **R8.2:** Examples don't work (copy-paste fails) | Agents waste time debugging | Examples are tested (included in test suite or manually validated). Code review checks example accuracy. |
| **R8.3:** Documentation is hard to find (agents don't know where to look) | Low adoption, integration delayed | Documentation location: project_board/checkpoints/M902-18/ (same location as other M902-18 artifacts). CHECKPOINTS.md index points to documentation. |

### 4. Clarifying Questions

- **Q12:** Should documentation include benchmark results? *Assumption: Basic reduction percentages (15–25% target); detailed benchmarking in M902-19+ integration checkpoints.*

---

## Non-Functional Requirements

### NFR-1: Determinism

**Description:** Tool categorization must be deterministic and repeatable.

**Criteria:**
- Same prompt + same all_tools → same filtered tools across multiple invocations.
- Same category name → same tool list in same order (consistent JSON serialization via tool_category_manager).
- No randomness in extraction, filtering, or invocation.
- Verified by test: extract category from same prompt 5x → identical results each time.

### NFR-2: Performance

**Description:** Middleware introduces minimal overhead to agent invocation.

**Criteria:**
- Category extraction (<1ms): single regex search.
- Tool filtering (<5ms): single function call to tool_category_manager.
- Total middleware overhead <10ms per invocation.
- No blocking I/O unless accessing config file (which tool_category_manager does, already <10ms).
- Verified by test: measure invocation time, assert <10ms.

### NFR-3: Backward Compatibility

**Description:** Agents without category declarations continue to work unchanged.

**Criteria:**
- No changes required to existing agent code.
- Existing agent invocations work with or without middleware.
- Fallback to all tools if no category declared.
- Verified by test: agents without category declaration receive all tools.

### NFR-4: Error Handling

**Description:** Graceful error handling; no silent failures or unmasked exceptions.

**Criteria:**
- All exceptions logged or re-raised.
- No bare `except` blocks.
- Invalid categories logged as warning, not error (fail-safe).
- Framework errors propagate unchanged.
- Verified by test: all error paths covered, logs validated.

### NFR-5: Logging

**Description:** Informative logging for debugging and monitoring.

**Criteria:**
- Info-level: category extraction (found/not found).
- Warning-level: invalid category, config issues.
- Error-level: system failures (framework errors).
- Log messages include agent_type, category (if extracted), and action taken.

### NFR-6: Testability

**Description:** Middleware is fully testable with mock frameworks; real framework integration is deferred.

**Criteria:**
- All functions independently testable.
- Dependency injection (framework_invocation_fn is parameter).
- No hard-coded external framework references.
- Mock framework can validate tool filtering.
- Verified by test: mock framework receives expected tools.

---

## Acceptance Criteria Coverage Matrix

| AC # | Ticket AC | Specification Requirement(s) | Test Strategy | Evidence Artifact |
|------|-----------|------------------------------|---------------|-------------------|
| AC-1 | Agent framework location identified and documented | Req 1 (Middleware Location) | Documentation + checkpoint | Checkpoint: `2026-05-20T-specification-run.md`; Spec: Req 1 |
| AC-2 | Framework accepts optional `tool_category` parameter | Req 4 (Invocation Contract) + Req 5 (Backward Compat) | Integration test: mock framework receives `tool_category` | Test: `test_invoke_with_category.py` |
| AC-3 | Category declaration regex implemented | Req 2 (Category Extraction) | Unit test: regex extraction + validation | Test: `test_extract_category_from_prompt.py` |
| AC-4 | Invalid categories handled gracefully | Req 6 (Error Handling) + Req 5 (Backward Compat) | Unit test: invalid category → warning + all tools | Test: `test_invalid_category_fallback.py` |
| AC-5 | `get_tools_for_category()` callable from context | Req 3 (Tool Filtering Integration) | Integration test: middleware calls function successfully | Test: `test_tool_filtering.py` |
| AC-6 | Framework passes filtered tools to agent | Req 4 (Invocation Contract) | Integration test: mock framework receives filtered tools | Test: `test_framework_integration.py` |
| AC-7 | Backward compatibility verified | Req 5 (Backward Compatibility) | Unit test: no category → all tools | Test: `test_backward_compat.py` |
| AC-8 | At least 1 test agent declares category and receives filtered tools | Req 7 (Test Strategy) | Integration test: simulated agent with category declaration | Test: `test_category_declaration_integration.py` |

---

## Implementation Notes

### For Implementation Agent (Task 3)

1. **Create middleware file:** `ci/scripts/agent_invocation_middleware.py`

2. **Import requirements:**
   ```python
   import re
   import logging
   from typing import Any, Callable
   from tool_category_manager import get_tools_for_category, VALID_CATEGORIES
   ```

3. **Implement three functions:**
   - `extract_category_from_prompt(prompt: str) -> str | None`
   - `invoke_agent_with_category_filtering(...) -> Any`
   - Helper for logging configuration (optional)

4. **Type hints:** All parameters and returns must be typed per CLAUDE.md Python style.

5. **Docstrings:** Clear, include Args, Returns, Raises, Examples.

6. **Error handling:** No bare `except` blocks. Catch ValueError and RuntimeError from tool_category_manager explicitly.

7. **Logging:** Use Python logging module; import at module level.

8. **Testing:** Run full test suite before submitting (must pass all tests).

### For Test Designer (Task 2)

1. **Test file:** `tests/ci/test_agent_framework_integration.py`

2. **Test structure:**
   ```python
   class TestCategoryExtraction:
       # Tests for extract_category_from_prompt
   
   class TestToolFiltering:
       # Tests for get_tools_for_category integration
   
   class TestMiddlewareInvocation:
       # Tests for invoke_agent_with_category_filtering
   
   class TestIntegration:
       # End-to-end tests with mock framework
   
   class TestErrorHandling:
       # Error path tests
   
   class TestBackwardCompatibility:
       # Backward compat tests
   ```

3. **Mock setup:**
   ```python
   from unittest.mock import MagicMock
   
   mock_framework = MagicMock(return_value={"status": "ok"})
   result = invoke_agent_with_category_filtering(
       agent_type="spec",
       prompt="I declare tool category: parse\n\nWrite spec...",
       all_tools=[...],
       framework_invocation_fn=mock_framework
   )
   mock_framework.assert_called_once()
   ```

4. **Determinism tests:** Run extraction/filtering 5x with same inputs; assert identical results.

5. **Coverage targets:** All paths, all declaration formats, all error scenarios.

---

## Specification Status & Handoff

**Status:** SPECIFICATION COMPLETE

**Revision:** 1 (Initial)

**Specification Date:** 2026-05-20

**Checkpoint Log:** `project_board/checkpoints/M902-18-T5/2026-05-20T-specification-run.md`

**Next Stage:** TEST_DESIGN

**Next Responsible Agent:** Test Designer Agent

**Required Gate:** `python ci/scripts/spec_completeness_check.py project_board/specs/902_18T5_tool_categorization_framework_integration_spec.md --type api` must pass before advancing to TEST_DESIGN.

**Spec Exit Criteria:**
- [ ] All 8 ACs explicitly mapped to requirements
- [ ] All 5 ambiguities (A1–A5) resolved with confidence level documented
- [ ] Function signatures fully specified with type hints
- [ ] Error handling documented for all paths
- [ ] Test strategy clear and actionable
- [ ] Documentation requirements defined
- [ ] Spec completeness check passes

---

## References

- **Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/00_backlog/18a_tool_categorization_framework_integration.md`
- **M902-18 Specification:** `project_board/specs/902_18_tool_categorization_spec.md` (Requirements 4 & 5)
- **M902-18 Integration Guide:** `project_board/checkpoints/M902-18/INTEGRATION_GUIDE.md`
- **Execution Plan:** `project_board/execution_plans/M902-18T5_tool_categorization_framework_integration.md`
- **Planning Checkpoint:** `project_board/checkpoints/M902-18-T5/2026-05-20T-planning-discovery-checkpoint.md`
- **Ambiguity Resolution Checkpoint:** `project_board/checkpoints/M902-18-T5/2026-05-20T-specification-run.md` (THIS RUN)
- **Tool Category Manager:** `ci/scripts/tool_category_manager.py`
- **Tool Categories Config:** `ci/scripts/tool_categories.json`
- **Workflow Enforcement:** `agent_context/agents/common_assets/workflow_enforcement_v1.md`
- **Checkpoint Protocol:** `agent_context/agents/common_assets/checkpoint_protocol_v1.md`

---

**Spec Author:** Spec Agent (Autonomous Mode)  
**Date:** 2026-05-20  
**Revision:** 1

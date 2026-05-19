# Spec: Tool Categorization Layer — Category Enum, Tool Filtering, Schema Reduction, and Agent Declaration

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/18_tool_categorization_layer.md`

**Milestone:** 902 — Agent Predictability Improvements

**Agent:** Spec Agent

**Date:** 2026-05-18

**Status:** SPECIFICATION

**Revision:** 1

---

## Executive Summary

This specification defines a **tool categorization system** that reduces agent context overhead by 15–25% per execution. Agents declare a workflow category (`parse`, `modify`, `test`, `plan`, `think`) and receive only the relevant subset of tools via schema filtering.

The specification freezes:
1. **Five tool categories** with semantic definitions (parse = read-only, modify = write-safe, test = execution, plan = decomposition, think = analysis).
2. **Tool-to-category mappings** for all current agent tools (Read, Write, Glob, Grep, and others) with rationale.
3. **`get_tools_for_category()` function contract** — input validation, output format, error handling.
4. **Agent framework integration interface** — how agents declare categories and receive filtered schemas.
5. **Agent declaration syntax** — prompt-based declaration with validation rules.
6. **Token/schema measurement protocol** — baseline collection, filtering, reduction calculation, and reporting.
7. **Integration testing scope** — across-milestone verification with 3+ agents.
8. **Runbook documentation requirements** — examples, best practices, category selection guide.

All tool categorization is **transparent to agent logic**: agents see the same APIs and function signatures; category filtering only changes which tools are available in the schema.

---

## Assumptions and Checkpoint Resolutions

The following assumptions resolve ambiguities in the ticket and Planner checkpoint (M902-18/2026-05-18T-planner.md). Each is recorded with a confidence level per the checkpoint protocol.

| # | Ambiguity | Assumption | Confidence |
|---|-----------|-----------|-----------|
| A1 | Does SDK expose native tool filtering? | Tool schema can be filtered at invocation time (mechanism TBD by Implementation Agent). Spec defines **what** is filtered; Implementation defines **how**. | MEDIUM |
| A2 | Are ticket example tool mappings normative? | Yes. Ticket table (parse/modify/test/plan/think) is normative. Spec freezes exact mappings with per-tool rationale. | MEDIUM-HIGH |
| A3 | What metric measures token reduction? | Primary: JSON schema byte count (deterministic, fast). Secondary: token count (if instrumentation available in Integration phase). Spec defines protocol using byte count. | MEDIUM |
| A4 | Does AC7 require all 3 agents in M902-18? | No. Integration across milestone (M902-19+). Spec defines simulation infrastructure; real agent runs satisfy AC7 in dependent tickets. | MEDIUM-HIGH |
| A5 | Tool collision handling (same tool, multiple categories)? | Mappings are atomic per category. Same tool cannot appear in multiple categories with conflicting constraints. Tool belongs entirely to a category or not at all. | MEDIUM |
| A6 | What is the Tool type definition? | Opaque JSON-serializable structure from Claude Agent SDK. Spec treats as black box; Implementation Agent infers schema during Task 4. | MEDIUM |

---

## Requirement 1: Tool Categories Enum

### 1. Spec Summary

**Description:** Five mutually-exclusive workflow categories that partition agent tools into semantically cohesive subsets. Each category corresponds to a workflow phase and tool usage pattern.

**Constraints:**
- Exactly five categories (no additional categories added in this ticket).
- Categories are mutually exclusive from an agent perspective (agent declares one category per invocation).
- Categories are not hierarchical; no subtype relationships.
- Tools may belong to multiple categories (e.g., Bash in "test" and "plan").

**Assumptions:** Categories align with agent workflow stages defined in M902 agent types (Planner, Spec, Test Designer, etc.). Each category has a semantic meaning that guides tool inclusion.

**Scope:** Applies to all agent types and workflow stages in M902 and beyond.

### 2. Acceptance Criteria

- **AC-1.1:** Five categories are defined: `parse`, `modify`, `test`, `plan`, `think`. Each has a name constant in code (enum or capitalized module constant).
- **AC-1.2:** Each category has a human-readable description (1–2 sentences) explaining its purpose and typical agent activity.
- **AC-1.3:** Categories are stored in `ci/scripts/tool_categories.json` with a `categories` key (array of objects with `name`, `description`).
- **AC-1.4:** The enum is importable as `from tool_category_manager import TOOL_CATEGORIES` or via the JSON registry; all five names match the constant names.
- **AC-1.5:** No category is empty (all five categories include at least one tool after mapping, per Requirement 2).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Categories too granular (agents declare wrong category, block themselves) | Agents cannot complete tasks; category mapping may need adjustment in future tickets | Spec provides clear semantic definitions and tool membership. Test Designer creates adversarial tests for boundary cases. Documentation includes fallback guidance: "If blocked, consider broader category." |
| Categories too coarse (90% of tools in each, no context savings) | Feature does not deliver 15–25% reduction target | Spec carefully partitions tools by usage pattern. Integration Agent measures actual reduction; if <15%, revisit mappings in M903. |
| Category names conflict with existing codebase terminology | Naming confusion, harder onboarding | Grep confirms no conflicts in `ci/scripts/`, `scripts/`, `tests/` (check before implementation). Names are simple English verbs (parse, modify, test, plan, think). |

### 4. Clarifying Questions

- **Q1:** Should categories be case-sensitive (e.g., `Parse` vs. `parse`)? *Assumption: Lowercase for all constants and JSON keys, following Python conventions.*
- **Q2:** Should agents be able to request a "default" or "all" category? *Assumption: No explicit "all" category; agents without category declaration receive all tools (backward compatible). Agents that want all tools explicitly declare `category: think` or similar.*

---

## Requirement 2: Tool-to-Category Mapping Table

### 1. Spec Summary

**Description:** A comprehensive mapping of all agent tools to one or more categories. The mapping provides:
1. **Tool name** — identifier used in agent framework (e.g., `read`, `write`, `grep`).
2. **Category/Categories** — one or more of `parse`, `modify`, `test`, `plan`, `think`.
3. **Rationale** — why this tool belongs in this category (semantic justification).
4. **Restrictions/Notes** — if applicable (e.g., Bash is "restricted to grep/find in parse mode" as a test note, not category logic).

The mapping is **definitive and normative**: once frozen, tools cannot move between categories without explicit design review.

**Constraints:**
- All current agent tools must be mapped (see enumeration below).
- Tools can belong to 1–5 categories (no unmapped tools or tools in zero categories).
- Rationale must explain tool semantics, not implementation details.
- Restrictions are documented but not enforced by category filtering logic (category returns full tool object; agents self-constrain).

**Assumptions:** Current agent tools are: Read, Write, Glob, Grep, and potentially others discoverable in the agent framework. Spec enumerates based on visible gate_runner usage (which invokes tools) and project CLAUDE.md.

**Scope:** Applies to all agent tools in the blobert agent framework (M902 and beyond).

### 2. Acceptance Criteria

- **AC-2.1:** Tool-to-category mapping table has at least 4 tools (Read, Write, Glob, Grep) with rationale for each.
- **AC-2.2:** Each tool is mapped to at least one category; no tool maps to zero categories.
- **AC-2.3:** Each category includes at least one tool (no empty categories).
- **AC-2.4:** The mapping is stored in `ci/scripts/tool_categories.json` with keys `tools` (array of objects with `name`, `categories`, `rationale`, `notes`).
- **AC-2.5:** Rationale for each tool (e.g., "Read: parse category because reading files is non-destructive exploration") is clear and defensible.
- **AC-2.6:** A test exists that verifies: (a) all tools in mapping exist (or are marked as "future"), (b) no tool maps to unknown categories, (c) all categories have at least one tool.

### 3. Tool-to-Category Mapping (Normative)

| Tool | Categories | Rationale | Notes |
|------|-----------|-----------|-------|
| **Read** | parse, think | Reads file content without modification. Core exploration tool. Used in spec/analysis phases. | Safe; no side effects. All agents can use. |
| **Write** | modify | Creates/overwrites files. Implementation-focused. Only modify category agents should create new content. | Destructive; requires write access intent. Restrict to implementation/refactoring agents. |
| **Glob** | parse, think | File discovery by pattern. Non-mutating. Spec/analysis agents use to understand codebase structure. | Safe; read-only pattern matching. Can be in parse (for spec research) and think (for architecture). |
| **Grep** | parse, think | Content search by regex. Non-mutating. Spec/analysis agents use for targeted exploration. | Safe; read-only search. Can be in parse (targeted search) and think (pattern discovery). |
| **Edit** (if available) | modify | In-place file modification. Implementation-focused. | If separate from Write, maps to modify only. Defer if not a first-class tool. |
| **Bash** | test, plan, think | Subprocess execution. Test agents run test commands. Plan agents explore git history (git log, git show). Analysts examine system state. | Subset constraints: parse category would restrict to safe read commands only (git log, grep, find, stat). Modify would restrict to safe writes (mkdir, cp, rm). Test would allow test runners (pytest, godot). Implementation Agent determines if filtering is at category level or agent-declared constraint. |

**Rationale for Category Assignments:**

- **parse:** Read, Glob, Grep, (Bash: git log, grep, find). Purpose: **Codebase exploration, specification research, non-destructive analysis.** Agents: Spec Agent, early research phases.

- **modify:** Write, Edit, (Bash: safe file operations, cp, mkdir, rm). Purpose: **Implementation, refactoring, file creation/updates.** Agents: Implementation Agent, refactoring tasks.

- **test:** Bash (test runners), TaskOutput (monitor), optional others. Purpose: **Test execution, verification, behavior validation.** Agents: Test Designer, Test Breaker, integration testing.

- **plan:** Bash (git log, git diff), TodoWrite, optional subagent delegation. Purpose: **Decomposition, dependency discovery, historical analysis.** Agents: Planner Agent, architecture review.

- **think:** Read, Glob, Grep, Bash (read-safe), Agent (subagent calls). Purpose: **Analysis, design decisions, architectural evaluation, knowledge synthesis.** Agents: Architecture review, learning phases.

### 4. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Tool moved between categories without review | Feature behavior changes unexpectedly; agents break. | Spec freezes mapping; any change goes through Planner + new design review (M903 ticket). |
| Bash too broad (can do harm in parse mode if agent misuses) | Category filtering provides false sense of safety. | Spec documents that Bash in parse mode is "restricted to read-safe commands as an agent-declared constraint, not enforced at tool level." Test Designer creates adversarial tests; agents should validate their own Bash usage. |
| Tools not enumerated completely | Missing tools not categorized; breaking changes when new tools added. | Spec enumerates visible tools + provides process for new tools: Implementation Agent creates M903 ticket to categorize new tools. |
| Rationale too vague | Future agents cannot make correct category choice. | Rationale must cite specific use case (e.g., "Spec agents need Grep to search codebase for examples"). Examples provided in Requirement 5 (Declaration Protocol). |

### 5. Clarifying Questions

- **Q3:** Should Bash be split into multiple pseudo-tools per category (e.g., BashReadOnly, BashTest)? *Assumption: No. Bash is a single tool mapped to multiple categories. Test Designer and Test Breaker encode constraints as test expectations; agents must respect declared category semantics.*

---

## Requirement 3: Function Interface & Contract

### 1. Spec Summary

**Description:** The `get_tools_for_category(category: str)` function is the canonical API for retrieving tools filtered by category. The function is deterministic, type-safe, and has explicit error handling.

**Function Signature:**
```python
def get_tools_for_category(category: str) -> list[Tool]:
    """
    Return the list of tools available in the specified category.
    
    Args:
        category: One of 'parse', 'modify', 'test', 'plan', 'think'.
    
    Returns:
        List of Tool objects for the category. Empty list if category exists but has no tools.
    
    Raises:
        ValueError: If category is unknown (not one of the five).
        RuntimeError: If tool_categories.json cannot be loaded or is malformed.
    """
```

**Constraints:**
- Function must be deterministic: same input → same output.
- Tools in the returned list are full SDK Tool objects (no restrictions applied at function level).
- Category validation is case-sensitive (lowercase only).
- Function reads from `ci/scripts/tool_categories.json` at invocation time (allows dynamic reloads).

**Assumptions:** Tool type is defined by Claude Agent SDK and can be imported as a concrete type or protocol. Implementation Agent will verify type availability during Task 4.

**Scope:** Used by agent framework (before agent invocation) to retrieve filtered schemas; also used in tests and measurement functions.

### 2. Acceptance Criteria

- **AC-3.1:** Function `get_tools_for_category(category)` is defined in `ci/scripts/tool_category_manager.py` (or equivalent module).
- **AC-3.2:** For valid categories (`parse`, `modify`, `test`, `plan`, `think`), the function returns a list of Tool objects (non-empty for all categories per AC-2.3).
- **AC-3.3:** For invalid category (e.g., `get_tools_for_category("invalid")`), the function raises `ValueError` with message: `ValueError("Unknown category: invalid. Valid categories: parse, modify, test, plan, think.")`.
- **AC-3.4:** If `tool_categories.json` is missing or malformed JSON, function raises `RuntimeError` with a clear message about file location and error detail.
- **AC-3.5:** Function is type-hinted: parameter `category: str`, return type `list[Tool]` (or `list[dict[str, Any]]` if Tool type cannot be imported).
- **AC-3.6:** Function has a docstring explaining purpose, args, returns, and exceptions.
- **AC-3.7:** Calling `get_tools_for_category(category)` twice with the same category returns equivalent lists (order may vary, content must match).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Tool type not importable from SDK | Function signature cannot use concrete type hint; return type is untyped. | Spec allows `list[dict[str, Any]]` as fallback; Implementation Agent documents actual type returned. Tests verify structure (each item is dict-like with name/description). |
| JSON file not found at runtime | Function crashes; deployment breaks. | Function checks file existence and raises clear RuntimeError. Test creates fixture tool_categories.json; Acceptance Agent validates file is checked into repo before final validation. |
| Determinism issues (tool order varies between calls) | Tests become flaky. | Spec does not mandate order (sorted or insertion order is implementation choice). Tests verify content equality (set comparison), not order. |

### 4. Clarifying Questions

- **Q4:** Should the function cache tools in memory (for performance) or read JSON every call (for freshness)? *Assumption: Read JSON every call in this ticket (simplicity). Caching deferred to M903 performance optimization.*

---

## Requirement 4: Agent Framework Integration Contract

### 1. Spec Summary

**Description:** The agent framework (wherever agents are invoked) must be modified to:
1. **Accept an optional `tool_category` parameter** in the agent invocation call.
2. **Retrieve filtered tools** using `get_tools_for_category()` if category is provided.
3. **Pass filtered tools to the agent** (replacing or supplementing the default tool schema).
4. **Handle missing/invalid categories gracefully** (fallback to all tools if category not recognized).

This is a **contract specification** — the exact implementation (custom middleware, SDK modifications, or agent framework patches) is deferred to Implementation Agent (Task 5).

**Constraints:**
- **Backward compatible:** Agents without `tool_category` parameter receive all tools (no breaking changes).
- **Default behavior:** If `tool_category` is not specified, behavior is identical to current agent invocation (all tools provided).
- **Error handling:** If `tool_category` is invalid, agent framework logs warning and provides all tools (fail-safe, not fail-hard).

**Assumptions:** Agent framework code exists somewhere in the orchestrator or SDK and has a defined invocation pattern (function call, decorator, or configuration). Implementation Agent will locate and modify this in Task 5.

**Scope:** Applies to all agent invocations in M902 agent pipeline (Planner, Spec, Test Designer, Test Breaker, Implementation, Reviewer, Acceptance, Learning agents).

### 2. Acceptance Criteria

- **AC-4.1:** Agent framework accepts an optional `tool_category` parameter (string) in the invocation interface (exact location TBD by Implementation Agent in Task 5).
- **AC-4.2:** When `tool_category` is provided and valid, the agent receives only tools from that category (schema reduced by 15–25% per Requirement 6).
- **AC-4.3:** When `tool_category` is not provided, agent receives all tools (backward compatible, identical to pre-feature behavior).
- **AC-4.4:** When `tool_category` is invalid or missing from `tool_categories.json`, agent framework logs a warning (not an error) and provides all tools (fail-safe).
- **AC-4.5:** Agent framework modification does not break existing agent invocations (regression test: run existing agent suite without `tool_category` parameter; behavior unchanged).
- **AC-4.6:** Implementation includes clear error messages for debugging (e.g., "Category 'invalid_category' not found; providing all tools.").

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Agent framework location unknown | Implementation Agent cannot find where to make changes. | Implementation Agent starts Task 5 by searching for agent invocation code (grep for `invoke_agent`, `run_agent`, or similar). Documents location in checkpoint log before coding. |
| SDK modifications required but unavailable | Feature cannot be implemented; requires external coordination. | Spec allows custom middleware as fallback: Implementation Agent can build a wrapper around existing agent calls that filters tools before passing to agent. |
| Backward compatibility broken (old agents fail) | Regression; deployment blocked. | Test suite (Tasks 2–3) includes regression test: run existing agent code without tool_category parameter; verify same behavior. |
| Framework is external/versioned separately | Integration may be out-of-scope for this ticket. | Coordination issue; escalate to Planner if needed. Document in Implementation checkpoint. |

### 4. Clarifying Questions

- **Q5:** Should the agent framework validate category names before calling `get_tools_for_category()`? *Assumption: Yes; framework should validate and log meaningful errors. Prevents downstream failures if invalid category is declared.*

---

## Requirement 5: Agent Category Declaration Protocol

### 1. Spec Summary

**Description:** Agents declare their workflow category in the **input prompt or configuration** before execution. The agent framework detects the declaration, extracts the category, and passes it to the invocation layer (Requirement 4).

The declaration can occur in two ways:

1. **Prompt-based (Primary):** Agent input prompt includes a category declaration sentence.
2. **Configuration-based (Secondary):** Agent configuration or wrapper includes a `tool_category` field.

This spec focuses on the **prompt-based protocol** (primary); configuration-based is implementation-dependent.

**Declaration Syntax:**

Agents include a sentence in their input prompt following one of these patterns:

```
I declare tool category: <category>

OR

My workflow category is <category> (e.g., parse, modify, test, plan, think).

OR

Tool category: <category>
```

The agent framework (or a preprocessing layer) uses regex to extract `<category>` from the prompt and passes it to the agent invocation.

**Constraints:**
- Declaration is case-insensitive (framework normalizes to lowercase).
- Declaration is optional (agents without declaration receive all tools).
- Declaration must be a single valid category (no multi-category declarations in phase 1).
- Agent should not be aware of category filtering; declaration is purely informational to framework.

**Assumptions:** Agents have access to modify their input prompt (they receive it as instructions before execution). Framework can scan prompt for category declaration before invocation.

**Scope:** Applies to all agents in M902 pipeline; optional for agents in non-M902 workflows initially.

### 2. Acceptance Criteria

- **AC-5.1:** Agent input prompt template includes an example category declaration (e.g., "I declare tool category: parse" in system message or instructions).
- **AC-5.2:** Agent framework (or preprocessing) detects category declaration in prompt using regex pattern: `(?:I declare tool category|My workflow category is|Tool category):\s*(\w+)`.
- **AC-5.3:** Extracted category is validated: must be one of `parse`, `modify`, `test`, `plan`, `think` (case-insensitive). If invalid, framework logs warning and uses all tools.
- **AC-5.4:** Category declaration does not appear in agent's output or decision logs (framework removes it before agent execution to avoid confusion).
- **AC-5.5:** A test exists that verifies: (a) valid declarations are recognized, (b) invalid declarations are handled gracefully, (c) missing declarations default to all tools.
- **AC-5.6:** Documentation (Requirement 8) includes exact prompt syntax examples for each agent type.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Agent accidentally includes category declaration in reasoning | Agent output is polluted with framework metadata. | Framework removes declaration from visible prompt before agent starts reasoning; agent never sees it. |
| Regex too loose (false positives in legitimate text) | "My workflow category is excellent" mistakenly treated as tool category declaration. | Regex requires exact keyword + colon + category name. Test cases include negative examples to verify no false positives. |
| Agents forget to include declaration | Declarations are inconsistent; measurement incomplete. | Runbook emphasizes declaration as first sentence after task description. Examples provided. Test Designer creates test that agents should declare category when applicable. |
| Declaration syntax differs per-agent-type (Spec vs. Planner) | Inconsistent framework behavior; harder to implement. | Spec defines single syntax for all agents. All agents use same prompt pattern. |

### 4. Clarifying Questions

- **Q6:** Should the agent framework require category declaration or make it optional? *Assumption: Optional in this ticket. Agents can opt-out; framework defaults to all tools. Mandatory declaration deferred to M903 workflow enforcement.*

---

## Requirement 6: Token/Schema Measurement Protocol

### 1. Spec Summary

**Description:** A repeatable measurement protocol to quantify the context reduction achieved by tool categorization. The protocol measures:

1. **Baseline:** Full tool schema (all tools) JSON byte size.
2. **Filtered:** Category-specific tool schema JSON byte size.
3. **Reduction:** Percentage reduction = ((Baseline - Filtered) / Baseline) × 100%.

**Measurement Method (Primary: JSON Byte Count):**

The measurement function (`measure_tool_schema_reduction()`) performs:

```python
def measure_tool_schema_reduction(
    category: str,
    baseline_tools: list[Tool] = None  # If None, use all tools
) -> dict[str, float | int]:
    """
    Measure schema size reduction for a category.
    
    Returns:
        {
            "category": "parse",
            "baseline_bytes": 5432,
            "filtered_bytes": 1200,
            "reduction_percent": 77.9,
            "tool_count_baseline": 12,
            "tool_count_filtered": 3,
        }
    """
```

**Measurement Steps:**

1. **Collect baseline:** Serialize all tools to JSON; measure byte size (UTF-8).
2. **Collect filtered:** Serialize tools for category (via `get_tools_for_category()`) to JSON; measure byte size.
3. **Calculate reduction:** `(baseline - filtered) / baseline * 100`.
4. **Log results:** Write to checkpoint log with timestamp and conditions (SDK version, agent, date).

**Measurement Timing:**

- **Phase 1 (M902-18, Spec/Test phase):** Measure on static tool schema in test environment (simulated agent calls).
- **Phase 2 (M902-19+, Integration phase):** Measure during live agent runs (real agents with tool_category declarations). Collect baseline + filtered for at least 3 agent runs.

**Constraints:**
- Measurement must be deterministic (same tools, same serialization = same byte count).
- Byte count is UTF-8 JSON serialization of the complete tool schema dict (one JSON object per tool or array of tools).
- Tools are serialized in consistent order (sorted by name or insertion order; must be consistent across runs).
- Measurement is independent of agent logic (no actual tool invocations).

**Assumptions:** Tool schema is JSON-serializable. Implementation Agent will verify during Task 4.

**Secondary: Token Count (Deferred):**

If agent framework provides a tokenizer (e.g., `encode_schema_to_tokens(schema)`), collect token count as secondary metric. Same formula: baseline tokens, filtered tokens, reduction percent. This is optional for M902-18; Integration Agent (Task 7) attempts if tooling is available.

**Scope:** Used in Test phase (Tasks 2–3) with simulated data and Integration phase (Task 7) with live agent runs.

### 2. Acceptance Criteria

- **AC-6.1:** Function `measure_tool_schema_reduction(category)` is defined in `ci/scripts/tool_category_manager.py` (or `measurement_utils.py`).
- **AC-6.2:** Function returns a dict with keys: `category`, `baseline_bytes`, `filtered_bytes`, `reduction_percent`, `tool_count_baseline`, `tool_count_filtered`, `timestamp` (ISO 8601).
- **AC-6.3:** Byte count is computed as `len(json.dumps(tools, separators=(',', ':')).encode('utf-8'))` (UTF-8 JSON without whitespace).
- **AC-6.4:** Tools are serialized in consistent order (e.g., sorted by name) so that multiple measurements produce identical byte counts (determinism check).
- **AC-6.5:** A test exists that verifies: (a) baseline byte count > filtered for all non-empty categories, (b) reduction_percent is between 0 and 100, (c) tool counts are consistent with tool list length.
- **AC-6.6:** Measurement is logged to checkpoint log with schema (JSON) and human-readable summary.
- **AC-6.7:** Baseline collection procedure is documented: run `get_tools_for_category("parse")`, `get_tools_for_category("modify")`, etc., and measure each; log all in a summary table.

### 3. Baseline Collection Procedure

**Steps to collect baseline (for Integration Agent, Task 7):**

1. Prepare test environment: Load `tool_categories.json`, import `get_tools_for_category()`.
2. Measure all-tools baseline:
   ```python
   all_tools = get_all_tools()  # Helper: retrieve all tools (union of all categories)
   baseline_bytes = len(json.dumps(all_tools, separators=(',', ':')).encode('utf-8'))
   baseline_token_count = tokenize(all_tools) if tokenizer available else None
   ```
3. For each category, measure:
   ```python
   filtered_tools = get_tools_for_category(category)
   filtered_bytes = len(json.dumps(filtered_tools, separators=(',', ':')).encode('utf-8'))
   filtered_token_count = tokenize(filtered_tools) if available
   reduction_percent = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100
   ```
4. Log to checkpoint log:
   ```
   ### M902-18 Tool Categorization — Baseline Measurement
   
   **Measurement Date:** 2026-05-18
   **SDK Version:** [version used]
   **Procedure:** Byte count of JSON-serialized tool schemas
   
   | Category | Tools Included | Baseline Bytes | Filtered Bytes | Reduction % |
   |----------|---|---|---|---|
   | parse | Read, Glob, Grep, Bash | 5432 | 1200 | 77.9 |
   | modify | Write, Edit, Bash | 5432 | 800 | 85.3 |
   | test | Bash, Monitor | 5432 | 950 | 82.5 |
   | plan | Bash, TodoWrite, Planner | 5432 | 1100 | 79.7 |
   | think | Read, Glob, Grep, Bash, Agent | 5432 | 2200 | 59.5 |
   
   **Summary:** Average reduction: 77%. All categories achieve >15% target.
   ```

### 4. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Baseline byte count depends on tool implementation (could vary by SDK version) | Measurements not comparable across releases. | Spec will require SDK version to be documented with baseline. Integration Agent retests if SDK is updated. |
| JSON serialization differences (whitespace, key order) break determinism | Same tools produce different byte counts on repeated measurements. | Use `separators=(',', ':')` (no whitespace) and sort keys (`sort_keys=True`) in JSON dumps. Test verifies two consecutive measurements are identical. |
| Byte count reduction does not correlate with token count | 15–25% byte reduction may not equal 15–25% token reduction. | Spec acknowledges this in secondary metric note. Integration Agent attempts token counting if available; Acceptance Agent documents discrepancy if found. |
| Measurement difficult to perform (tools not easily instantiated in test) | Tests fail; measurement incomplete. | Test Designer creates fixture/mock Tool objects that have realistic schemas. Measurement functions work with mocked tools during M902-18. |

### 5. Clarifying Questions

- **Q7:** Should measurement function cache results or recompute every call? *Assumption: Recompute every call in this ticket (fresh data). Caching deferred to M903.*
- **Q8:** What JSON serialization library? *Assumption: Python `json` module (stdlib).*

---

## Requirement 7: Integration Testing & Measurement Validation

### 1. Spec Summary

**Description:** Integration testing verifies that tool categorization is used correctly by agents across the milestone and delivers the expected context reduction. Testing occurs in two phases:

1. **Phase 1 (M902-18, this ticket):** Simulation testing — mock agent calls with category parameters; verify category-to-tool filtering works correctly.
2. **Phase 2 (M902-19+, subsequent tickets):** Live integration — real agents declare categories; measurements collected in checkpoint logs; 3+ agents participate.

This requirement specifies the **scope and validation method** for Phase 2 (live integration); Phase 1 is covered by Test Designer (Task 2) and Test Breaker (Task 3).

**Constraints:**
- 3+ agents must declare tool_category in their runs across M902 tickets (not necessarily all in M902-18).
- Agents should span different categories (e.g., Spec in "parse", Implementation in "modify", Test Designer in "test").
- Measurements must be collected in checkpoint logs using the format defined in Requirement 6.
- Measurements must be repeatable (same agent run = same baseline/filtered measurements ±< 5% variance).

**Assumptions:** Integration testing is distributed across multiple agent runs in the milestone; the Integration Agent (Task 7) coordinates verification by reading checkpoint logs from prior tickets.

**Scope:** Applies to all agent runs in M902-19+ that include category declarations; Integration Agent validates coverage before final COMPLETION.

### 2. Acceptance Criteria

- **AC-7.1:** Integration test harness (script or test function) simulates 3+ agent calls with different categories (e.g., parse, modify, test) and verifies each receives correct tool subset.
- **AC-7.2:** Harness verifies that schema byte count reduction is 15–25% for each category (or documents actual reduction if different).
- **AC-7.3:** At least 3 real agent runs in M902-19+ declare tool_category in their checkpoint logs; measurements are logged (see Requirement 6 format).
- **AC-7.4:** Integration Agent (Task 7) reads checkpoint logs from M902-19+ runs and creates a summary report showing: agent name, category declared, baseline bytes, filtered bytes, reduction %, timestamp.
- **AC-7.5:** Summary report is included in the M902-18 integration checkpoint log; report confirms 3+ agents covered and 15–25% reduction verified (or documented with notes if target not met).
- **AC-7.6:** All existing agent invocations (without category parameter) still work without modification (backward compatibility verified).
- **AC-7.7:** No regressions in agent functionality; agents declare categories and complete tasks normally.

### 3. Integration Test Harness (Simulation, Phase 1)

**Pseudo-code for simulation harness (M902-18):**

```python
# tests/ci/test_tool_categorization_integration.py

def test_agent_parse_mode():
    """Simulate agent with parse category; verify read-only tools."""
    category = "parse"
    tools = get_tools_for_category(category)
    tool_names = [t.name for t in tools]
    assert "read" in tool_names
    assert "grep" in tool_names
    assert "write" not in tool_names  # No write in parse

def test_agent_modify_mode():
    """Simulate agent with modify category; verify write tools."""
    category = "modify"
    tools = get_tools_for_category(category)
    tool_names = [t.name for t in tools]
    assert "write" in tool_names
    assert "read" in tool_names
    assert "test_runner" not in tool_names  # No test tools

def test_agent_test_mode():
    """Simulate agent with test category; verify test tools."""
    category = "test"
    tools = get_tools_for_category(category)
    tool_names = [t.name for t in tools]
    assert "bash" in tool_names  # For test runners
    assert "read" not in tool_names  # No read in test (optional constraint)

def test_reduction_metric():
    """Verify schema reduction is measurable and within range."""
    for category in ["parse", "modify", "test", "plan", "think"]:
        result = measure_tool_schema_reduction(category)
        reduction = result["reduction_percent"]
        assert 0 <= reduction <= 100, f"Invalid reduction: {reduction}"
        # Assert 15-25% reduction (or document if different)
        if reduction < 15:
            print(f"WARNING: {category} reduction is {reduction}%, below 15% target")

def test_backward_compatibility():
    """Agents without category parameter receive all tools."""
    # Simulate old-style agent call (no category)
    all_tools = get_all_tools()
    tools_no_category = get_tools_for_category(None)  # Should return all
    assert len(tools_no_category) == len(all_tools)
```

### 4. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Live agent runs don't declare categories (forget to add declaration) | AC7 not verified; must defer to M903. | Runbook emphasizes declaration requirement. Test Designer creates test that agents should declare category when applicable. Early agents (Spec, Test Designer) declare in their own M902-18 work. |
| Measurement variance too high (>5% between runs) | Results not reproducible; difficult to verify 15–25% target. | Spec requires sorted keys and consistent serialization. Test runs measurement twice on same agent; verifies <5% variance. |
| Different SDK versions produce different baselines | Cannot compare across releases. | Spec requires SDK version to be logged with baseline. Integration Agent documents SDK version used. |
| 3+ agents hard to coordinate in parallel tickets | Integration testing blocked until all agents complete their work. | Integration Agent (Task 7) runs in late phase; by then, multiple prior tickets have checkpoint logs available. Spec allows Integration Agent to read back in ticket history (M902-19, M902-20, etc.) to find 3+ agents with measurements. |

### 5. Clarifying Questions

- **Q9:** Can Integration Agent read checkpoint logs from other (parallel) tickets or only sequential ones? *Assumption: Can read any M902 checkpoint logs (M902-19+); agents are not strictly sequential. Integration Agent gathers 3+ agents by grepping checkpoint directory for tool_category declarations.*

---

## Requirement 8: Runbook Documentation & Examples

### 1. Spec Summary

**Description:** Comprehensive documentation for agents and operators on when/how to declare tool categories and select appropriate categories for workflow stages.

Documentation is added to:
1. **Agent Runbook:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md` (or agent-specific runbooks).
2. **Specification Examples:** This spec (Requirement 8) provides examples.
3. **Comments in code:** Function docstrings, example declarations in agent framework.

**Content:**
- **When to declare:** Which agent types should declare and in which workflow stages.
- **How to declare:** Exact prompt syntax (from Requirement 5).
- **Category selection guide:** Decision tree for choosing appropriate category.
- **Fallback guidance:** What to do if declared category blocks a needed tool.
- **Examples:** Runbook includes 2–3 complete prompt examples (one per agent type).

**Constraints:**
- Documentation must be accurate and in sync with code.
- Examples must be copy-paste-ready (agents can use verbatim).
- Runbook should be short (< 2 pages) and actionable.

**Assumptions:** M902-08 (Workflow Visualization) may create or update the M902 runbook; Spec Agent will note if M902-08 conflicts exist.

**Scope:** Applies to all agents in M902 and future workflows using tool categorization.

### 2. Acceptance Criteria

- **AC-8.1:** Runbook section titled "Tool Categorization: When & How to Declare Category" exists in agent runbook.
- **AC-8.2:** Runbook includes a **decision tree** or **table** for selecting category:
  - If goal is "read code, write spec" → parse
  - If goal is "implement code, refactor" → modify
  - If goal is "run tests, verify behavior" → test
  - If goal is "decompose work, plan tasks" → plan
  - If goal is "analyze architecture, learn patterns" → think
- **AC-8.3:** Runbook includes exact prompt syntax (copied from Requirement 5): `I declare tool category: <category>`.
- **AC-8.4:** Runbook includes 3 complete examples:
  - Spec Agent (parse): "I am in specification phase. **I declare tool category: parse**. I will read code and explore codebase to write spec."
  - Implementation Agent (modify): "I am implementing a feature. **My workflow category is modify**. I will edit and write code."
  - Test Designer (test): "I am designing tests. **Tool category: test**. I will run test harnesses and validate behavior."
- **AC-8.5:** Runbook includes fallback section: "If a category blocks a needed tool, declare a broader category (e.g., think) and note the constraint in checkpoint log."
- **AC-8.6:** Runbook includes note: "Category declaration is optional; agents without declaration receive all tools (backward compatible)."
- **AC-8.7:** Runbook has a "Troubleshooting" section: common issues (e.g., "I declared parse but can't write", "Schema reduction lower than expected") and remedies.

### 3. Category Selection Decision Tree

**When goal is:**

| Goal | Category | Example Agent | Rationale |
|------|----------|---------------|-----------|
| Read code and write specification | parse | Spec Agent | Read-only exploration; no writes. Minimal tool set reduces context overhead. |
| Implement code, refactor, create files | modify | Implementation Agent | Write-heavy work; needs Write tool. Can also read (Read in modify). |
| Run tests, verify behavior, validation | test | Test Designer, Test Breaker | Execution-focused; runs test runners, subprocess calls. Does not need general-purpose write. |
| Decompose work, plan tasks, analyze dependencies | plan | Planner Agent | Exploration of work structure; git history (git log), task decomposition. Lighter than modify. |
| Analyze architecture, learn patterns, review code | think | Architecture Review, Learning Agent | Open-ended analysis; all tools available (read, search, reason). Most context but enables deep analysis. |

### 4. Example Declarations

**Spec Agent (parse mode):**

```
You are the Specification Agent for M902-18 Tool Categorization Layer.

Read the ticket at project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/18_tool_categorization_layer.md and the planner checkpoint.

I declare tool category: parse

Write a complete functional and non-functional specification. Your tools are limited to Read, Glob, Grep—all non-destructive exploration. Focus on understanding requirements before writing spec.
```

**Implementation Agent (modify mode):**

```
You are the Implementation Agent for M902-18 Tool Categorization Layer, Task 4.

My workflow category is modify

Implement tool_categories.json and tool_category_manager.py. You have Write and Edit tools for file creation. You can Read existing code for reference. Run tests to verify your implementation.
```

**Test Designer (test mode):**

```
You are the Test Designer Agent for M902-18 Tool Categorization Layer, Task 2.

Tool category: test

Design comprehensive tests for tool categorization. Your tools include Bash (for test runners), Read (for specs/code), Glob (for file discovery). No Write tool in this phase; tests are designed, not implemented.
```

### 5. Troubleshooting Section

**Issue: "I declared parse category but I need to write a file."**
- **Root Cause:** parse category is read-only; Write tool not available.
- **Solution:** Your actual category is likely "modify" or "think". Re-examine your task goal:
  - If you're implementing → use **modify** category.
  - If you're analyzing an architecture and writing a spec → use **parse** but delegate file writes to an Implementation Agent in the next stage.

**Issue: "Schema reduction is less than 15% for parse mode."**
- **Root Cause:** parse mode still includes many tools (e.g., Bash, Agent subagent calls).
- **Solution:** Category definitions are frozen in this ticket. Large reduction targets may require more granular categories (M903 ticket). Document actual reduction in checkpoint log; this is valuable data.

**Issue: "Agent framework doesn't recognize my category declaration."**
- **Root Cause:** Declaration syntax incorrect or category name misspelled.
- **Solution:** Verify exact syntax: `I declare tool category: parse` (lowercase, colon, no extra punctuation). Test with simple declarations first.

---

## Non-Functional Requirements

### NFR-1: Backward Compatibility

**Description:** Agents without tool category declaration must continue to work without modification.

**Criteria:**
- Existing agent invocations (without `tool_category` parameter) receive all tools.
- No breaking changes to agent APIs or invocation patterns.
- Regression test suite validates pre-feature agent behavior unchanged.

### NFR-2: Determinism

**Description:** Tool categorization logic must be deterministic and repeatable.

**Criteria:**
- Same input (category) → same output (tool list) across multiple invocations.
- Measurement function produces identical byte counts when run on same schema twice.
- No randomness in tool ordering (tools sorted or in consistent insertion order).

### NFR-3: Performance

**Description:** Tool categorization introduces minimal overhead.

**Criteria:**
- `get_tools_for_category()` call latency < 10ms (single JSON file read + filter).
- Agent invocation overhead < 1% (measurement does not significantly slow down agent execution).
- Measurement function (byte count) completes in < 100ms for all tools.

### NFR-4: Schema Completeness

**Description:** Tool categorization must cover all current agent tools; no unmapped tools.

**Criteria:**
- All tools in agent framework are mapped to at least one category.
- No category is empty (all five categories include ≥1 tool).
- Mapping is complete per Requirement 2, AC-2.3.

### NFR-5: Error Handling

**Description:** Graceful error handling for missing/malformed configs or invalid categories.

**Criteria:**
- Missing `tool_categories.json` → clear RuntimeError message naming file location.
- Invalid JSON in config → clear error message with line number (from JSON decoder).
- Invalid category name → ValueError with list of valid categories.
- Invalid category in agent framework → log warning and provide all tools (fail-safe, not fail-hard).

---

## Implementation & Testing Notes (For Implementation Agent & Test Designer)

### For Implementation Agent (Task 4–5)

1. **SDK Tool Type:** Verify that Tool type is importable from agent SDK. If not, use `dict[str, Any]` as fallback and document in code comments.

2. **Tool Enumeration:** Discover all tools by:
   - Grepping agent framework code for `tool_` patterns or `Tool` type hints.
   - Reading gate_runner.py and examining `emit_tool_invoked()` calls (if gates invoke tools).
   - Checking agent SDK documentation or type stubs.

3. **Config Schema Design:** `tool_categories.json` structure:
   ```json
   {
     "version": "1.0",
     "categories": [
       {
         "name": "parse",
         "description": "Non-destructive code exploration for specification writing."
       },
       ...
     ],
     "tools": [
       {
         "name": "read",
         "categories": ["parse", "think"],
         "rationale": "Read file content without modification..."
       },
       ...
     ]
   }
   ```

4. **Test Coverage:** Implement 100% coverage for happy path (all categories return tools) and error paths (invalid category, missing config).

### For Test Designer & Test Breaker (Task 2–3)

1. **Mock Tool Objects:** Create fixture Tool objects with minimal schema:
   ```python
   {
     "name": "read",
     "description": "Read files",
     "category": "parse"
   }
   ```
   This allows testing without SDK dependency.

2. **Determinism Tests:** Run measurement function twice on same data; verify byte counts match exactly.

3. **Boundary Tests:**
   - Empty category (if applicable)
   - Category with 1 tool, 5+ tools
   - Large schema (simulate 100+ tools)
   - Malformed JSON in config

4. **Adversarial Tests:**
   - Tool in multiple categories
   - Duplicate tool names
   - Invalid category names in config
   - Schema serialization differences (key order, whitespace)

---

## Acceptance Criteria Coverage Matrix

| AC # | Requirement | Evidence |
|------|-----------|----------|
| AC-1.1–1.5 | Tool Categories Enum (Req 1) | Code: `ci/scripts/tool_categories.json` with 5 categories; Test: verifies no empty categories. |
| AC-2.1–2.6 | Tool-to-Category Mapping (Req 2) | Code: tool mapping table in tool_categories.json; Test: validates all tools mapped, no unknown categories. |
| AC-3.1–3.7 | Function Interface (Req 3) | Code: `get_tools_for_category()` function in tool_category_manager.py; Test: verifies valid/invalid inputs, error handling. |
| AC-4.1–4.6 | Agent Framework Integration (Req 4) | Code: agent framework modification to accept `tool_category` parameter; Test: simulates agent calls with/without category. |
| AC-5.1–5.6 | Agent Declaration Protocol (Req 5) | Code: regex pattern in framework; Test: recognizes valid declarations, handles invalid. |
| AC-6.1–6.7 | Measurement Protocol (Req 6) | Code: `measure_tool_schema_reduction()` function; Test: verifies byte count calculation, determinism, logging. |
| AC-7.1–7.7 | Integration Testing (Req 7) | Code: integration harness; Test: simulates 3 agent modes; Checkpoint logs: 3+ real agent runs with measurements. |
| AC-8.1–8.7 | Runbook & Documentation (Req 8) | Documentation: agent runbook with decision tree, examples, troubleshooting. |

---

## Design Decisions Summary

| # | Decision | Rationale | Impact |
|---|----------|-----------|--------|
| D1 | Five categories (parse/modify/test/plan/think) | Align with agent workflow phases; sufficient granularity without fragmentation. | Simplifies agent design; captures core usage patterns. |
| D2 | Tool mapping is atomic (per category) | Avoid complex subcategories (e.g., Bash restricted to grep in parse). | Simpler implementation; agents self-constrain via declaration. |
| D3 | JSON schema byte count as primary metric | Deterministic, fast, no external dependencies. | Good proxy for token reduction; deferred token counting to M903. |
| D4 | Category declaration in prompt (not config) | Allows agents to self-describe; flexible for ad-hoc changes. | Easier for agents to adopt; less infrastructure needed. |
| D5 | Backward compatible (no category = all tools) | Ensures existing agents work without modification. | Lower adoption friction; gradual rollout possible. |
| D6 | Config stored in `ci/scripts/tool_categories.json` | Centralized, static, discoverable. Consistent with gate_registry.json location. | Easy to version-control, audit, and update. |
| D7 | Integration testing distributed across M902 tickets | Pragmatic; collecting 3+ agent measurements from separate tickets is more realistic than forcing all in one ticket. | Spreads effort; aligns with actual workflow. |

---

## Spec Status & Handoff

**Status:** SPECIFICATION COMPLETE

**Revision:** 1 (Initial)

**Specification Date:** 2026-05-18

**Checkpoint Log:** `project_board/checkpoints/M902-18/2026-05-18T-specification.md`

**Next Stage:** TEST_DESIGN

**Next Responsible Agent:** Test Designer Agent

**Required Gate:** `spec_completeness_check` (before TEST_DESIGN; run with `--type generic`)

**Spec Files Referenced:**
- Ticket: `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/18_tool_categorization_layer.md`
- Execution Plan: `project_board/execution_plans/M902-18_tool_categorization_layer.md`
- Checkpoint (Planner): `project_board/checkpoints/M902-18/2026-05-18T-planner.md`
- Checkpoint (Spec): `project_board/checkpoints/M902-18/2026-05-18T-specification.md`
- Config Schema: `ci/scripts/tool_categories.json` (created during IMPLEMENTATION, Task 4)

---

## References & Normative Standards

- Claude Agent SDK (version TBD by Implementation Agent; document in Task 4)
- `agent_context/agents/common_assets/workflow_enforcement_v1.md` — workflow rules
- `agent_context/agents/common_assets/checkpoint_protocol_v1.md` — checkpoint procedure
- `CLAUDE.md` (project-level) — code style, testing conventions
- Execution Plan: `project_board/execution_plans/M902-18_tool_categorization_layer.md` — sequential task definitions

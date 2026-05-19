# M902-18 Tool Categorization Layer — Specification Stage

**Ticket Path:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/18_tool_categorization_layer.md`

**Run Date:** 2026-05-18  
**Stage:** SPECIFICATION  
**Agent:** Spec Agent

---

## Clarifying Questions Resolution

### Q1: SDK Tool Filtering API Availability (CRITICAL)

**Would have asked:** Does Claude Agent SDK expose a native tool filtering API? If not, will custom middleware be built or is this a blocking assumption?

**Assumption made:** The Claude Agent SDK does not currently expose a public `tool_filtering` or `exclude_tools` API at the agent invocation level. However, the specification assumes that:
1. **Tool schema can be filtered at invocation time** — either via SDK modifications, custom middleware wrapping agent calls, or direct schema manipulation before agent invocation.
2. **The filtering is applied in the agent framework** (wherever agents are invoked in the orchestrator), not in individual agents.
3. **The `get_tools_for_category()` function is a utility** that returns filtered tool lists; the integration mechanism (how this list reaches the agent) is the responsibility of the Implementation Agent (Task 5).

**Confidence:** MEDIUM

**Rationale:** The execution plan explicitly anticipates this uncertainty (Task 5: "Agent framework integration — modify agent invocation to accept optional `tool_category` parameter") and delegates to the Implementation Agent. This spec will freeze the tool filtering contract (what tools each category gets) but leaves the SDK integration mechanism (how tools are excluded) to Implementation. Spec will define the expected interface without assuming SDK internals.

---

### Q2: Tool-to-Category Mappings (Normative vs. Example)

**Would have asked:** Are the example tool assignments in the ticket (parse = Read/Bash-grep/WebFetch) normative or heuristic suggestions?

**Assumption made:** The ticket's example table is **normative** — it defines the categories and provides reasonable tool assignments. The Spec Agent will:
1. Enumerate all current tools available to agents (Read, Write, Glob, Grep, and potentially others in the agent framework).
2. Assign each tool to one or more categories using the ticket's example table as a template and rationale.
3. Document the rationale for each tool-to-category assignment (why Read is in "parse" vs. "modify").
4. Allow tools to belong to multiple categories if semantically appropriate (e.g., Bash can be in "test", "plan", and "think" with different restricted subsets).

**Confidence:** MEDIUM-HIGH

**Rationale:** The ticket explicitly states the example table and the execution plan (Design Decision #2) says "Spec Agent will freeze exact mappings." The example gives clear guidance; this spec will operationalize it.

---

### Q3: Token Measurement Metric (Byte Count vs. Token Count)

**Would have asked:** Does "tool schema reduction measured" mean JSON schema byte count, API token count, or another metric?

**Assumption made:** The specification will define **two measurement approaches** (with preference for byte count as the primary metric):

1. **Primary: JSON Schema Byte Count**
   - Measure the UTF-8 byte size of the JSON tool schema returned by `get_tools_for_category(category)`.
   - Baseline = byte size of all tools (full schema).
   - Filtered = byte size for each category.
   - Reduction = ((Baseline - Filtered) / Baseline) * 100%.
   - Rationale: Deterministic, fast, no external API calls, and a good proxy for context reduction (larger schema = more tokens).

2. **Secondary: Token Count (If Instrumentation Available)**
   - If the agent framework or SDK provides token counting (e.g., via a tokenizer), measure actual token count of each schema.
   - Use the same baseline/filtered/reduction formula.
   - This is deferred to Implementation/Integration if feasible.

**Confidence:** MEDIUM

**Rationale:** Byte count is immediately implementable without SDK modifications. Token count requires additional instrumentation and may depend on model-specific tokenizers. The spec will define baseline collection using byte count; Integration Agent (Task 7) can attempt token counting if tooling is available.

---

### Q4: Integration Testing Scope (Single Ticket vs. Across Milestone)

**Would have asked:** Does AC7 require all 3 agents to run in M902-18, or can the feature be tested across other M902 tickets?

**Assumption made:** Integration testing is **across the milestone**, not confined to M902-18:

1. **This ticket (M902-18):** Implements tool categorization infrastructure. Includes basic integration tests that simulate agent calls with tool_category parameters.

2. **Subsequent tickets (M902-19+):** Real agent runs (Spec Agent, Implementation Agent, Test Designer) will declare tool_category in their input prompts and collect measurements. These runs satisfy AC7.

3. **Checkpoint logs:** Tool category declarations and measurements must appear in checkpoint logs for at least 3 distinct agent roles across the milestone (e.g., Spec Agent in M902-19, Implementation Agent in M902-20, Test Designer in M902-21).

**Confidence:** MEDIUM-HIGH

**Rationale:** The execution plan (Task 7, Risk Area) acknowledges this: "Assign early agents (Spec, Test Designer) to declare categories during their runs; log measured overhead in checkpoints. Verify 3-agent coverage before IMPLEMENTATION." This is pragmatic for a milestone that spans weeks; requiring all 3 agents in one ticket is infeasible.

---

### Q5: Spec Reference File Path

**Would have asked:** The ticket references a non-existent spec file. Should this spec be created?

**Assumption made:** **Yes**. This specification will be written to:
```
project_board/specs/902_18_tool_categorization_spec.md
```

**Confidence:** HIGH

**Rationale:** The ticket explicitly cites this path; workflow enforcement (spec_completeness_check gate) requires it before TEST_DESIGN.

---

## Additional Ambiguities Resolved in Spec

### Tool Collision Handling

**Scenario:** What if the same tool (e.g., Bash) belongs to multiple categories with different constraints (e.g., "parse" allows grep/find only; "modify" allows all Bash)?

**Assumption made:** The spec will define **tool-category mappings as atomic** — each tool is either fully included or fully excluded per category. Subcategories of tool restrictions (e.g., "Bash restricted to grep") are **deferred to Test Designer** (Task 2) as adversarial test constraints, not implemented as category logic.

**Rationale:** Simplicity. The `get_tools_for_category()` function returns a list of tools; filtering which Bash operations are allowed is an agent-level concern (agents should self-constrain based on their category declaration), not a tool filtering concern.

**Confidence:** MEDIUM

---

### Tool Schema Structure

**Assumption made:** The spec will assume tools have a **tool schema JSON structure** (name, description, parameters, etc.) as defined by the Claude Agent SDK. The exact schema is not defined in this ticket; the spec references the SDK tool type by its canonical name and assumes it can be serialized to JSON for size measurement.

**Confidence:** MEDIUM

**Rationale:** Without access to the SDK internals, the spec treats the Tool type as an opaque data structure that has a JSON serialization. Implementation Agent can inspect and confirm during Task 4.

---

## Acceptance Criteria Mapping (AC Coverage in Spec)

| AC # | Acceptance Criterion | Spec Section |
|------|---------------------|--------------|
| 1 | Define tool categories enum: `parse`, `modify`, `test`, `plan`, `think` | Requirement 1: Tool Categories Enum |
| 2 | Categorize all existing agent tools into one or more categories | Requirement 2: Tool-to-Category Mapping Table |
| 3 | Implement `get_tools_for_category(category: str) -> list[Tool]` function | Requirement 3: Function Interface & Contract |
| 4 | Agent framework passes `tool_category` parameter to each agent | Requirement 4: Agent Framework Integration Contract |
| 5 | Agents can declare category in input prompt | Requirement 5: Agent Category Declaration Protocol |
| 6 | Tool schema reduction measured: baseline vs. category-filtered size | Requirement 6: Token/Schema Measurement Protocol |
| 7 | Integration tested with 3+ agents | Requirement 7: Integration Testing & Measurement Validation |
| 8 | Documented in agent runbook: when/how to declare category | Requirement 8: Runbook Documentation & Examples |

---

## Design Decisions Frozen

1. **Tool Schema Measurement Method:** Byte count of JSON serialized tool schema (primary); token count (secondary, if instrumentation available).

2. **Default Behavior (Backward Compatibility):** Agents without category declaration receive all tools (no breaking changes).

3. **Tool Collision Policy:** Same tool cannot belong to multiple categories with incompatible constraints; spec maps tools atomically per category.

4. **Category Scope:** Five categories (`parse`, `modify`, `test`, `plan`, `think`) are finalized per ticket.

5. **Config File Location:** `ci/scripts/tool_categories.json` (per ticket).

6. **Function Signature:** `get_tools_for_category(category: str) -> list[Tool]` (per ticket and execution plan).

---

**Specification Stage: READY TO PROCEED**

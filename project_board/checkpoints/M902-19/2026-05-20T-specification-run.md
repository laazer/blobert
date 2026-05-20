# M902-19 Forgiving Tool Parsing Middleware — SPECIFICATION COMPLETE

**Date:** 2026-05-20  
**Stage:** SPECIFICATION (Revision 2 → 3)  
**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/19_forgiving_tool_parsing_middleware.md`  
**Agent:** Spec Agent  
**Status:** COMPLETE

---

## Autonomy Checkpoint Entries

### [M902-19] SPECIFICATION — A1 (Tool Execution Integration Point)

**Would have asked:** Where in the external Agent SDK does tool execution happen, and is it accessible for middleware wrapping?

**Assumption made:** Based on M902-18-T5 precedent and codebase investigation:
- The Agent SDK is EXTERNAL to blobert (Claude Code / Claude Agent SDK infrastructure).
- Agent invocation happens at the boundary between blobert and the external framework.
- M902-18-T5 established a **middleware-wrapper pattern**: blobert creates middleware in `ci/scripts/agent_invocation_middleware.py` that sits at the invocation boundary.
- For M902-19, tool parsing middleware will be similarly positioned POST-TOOL-INVOCATION, meaning:
  - Tool calls originate from the external framework (LLM agent output)
  - Blobert intercepts the tool call parameters before execution
  - Middleware repairs/validates the parameters
  - If valid after repair, the tool is executed; if invalid, a clear error is returned
- M902-18-T5 provides architectural reference: middleware wraps at logical boundary, no external SDK modification needed.

**Confidence:** HIGH
- M902-18-T5 demonstrates middleware-wrapper approach works (72 tests passing, production-ready)
- Invocation boundary is well-understood from M902-18-T5 spec (Requirement 1, 4)
- Repair middleware is orthogonal to categorization (can be stacked before/after categorization layer)

---

### [M902-19] SPECIFICATION — A2 (Repair Safety Boundaries)

**Would have asked:** Which error categories are safe to auto-repair vs dangerous/impossible?

**Assumption made:** Based on ticket AC and smallcode reference, 6-8 repair categories formalized in spec:
1. **String-to-Boolean Coercion** (Req 2a): `"true"` → `True`, `"false"` → `False` — low-risk
2. **Integer String Coercion** (Req 2b): `"123"` → `123` — low-risk type conversion
3. **Missing Required Fields** (Req 3): detect missing key, provide sensible default OR fail with error
4. **Parameter Name Typo Correction** (Req 4): fuzzy match whitelist with 80% threshold
5. **Quoted String Paths** (Req 5): unwrap outer quotes on paths
6. **Nested Structure Repair** (Req 6): handle nested dict/list errors up to 2 levels
7. **Optional Parameter Defaults** (Req 3): add optional params with schema defaults
8. **Validation Gate** (Req 7): static whitelist, reject dangerous mutations

**Confidence:** HIGH
- All 8 repair categories with concrete examples in spec (Req 1–8)
- Safety boundaries explicit: type coercion safe; semantic inspection dangerous
- Dangerous actions list in spec (shell, exec, code evaluation, privilege escalation, etc.)
- Validation via static parameter whitelists from M902-18 tool schema

---

### [M902-19] SPECIFICATION — A3 (Tool Call Schema Format)

**Assumption made:**
- Tool calls are JSON dicts (per ticket AC example)
- Parser detects JSON/YAML/XML formats and converts to dict
- Schema is flexible per tool (various parameter names, types)
- Spec defines Requirement 1 (Parser) with explicit format handling

**Confidence:** HIGH
- Ticket AC provides concrete JSON example (action, file_path, replace_all)
- Spec clearly defines parser input/output contract
- M902-18-T5 uses JSON-serializable dicts (compatible)

---

### [M902-19] SPECIFICATION — A4 (Validation Mechanism — Static Whitelist Approach)

**Assumption made:**
- Validation uses STATIC WHITELISTS per tool (Req 7, Security Constraints)
- Each tool has `safe_parameters` field from M902-18 schema
- Repair rejected if parameter not in whitelist
- No content inspection; only syntax/type validation

**Confidence:** HIGH
- Spec defines static whitelist approach (Req 7, Security Constraints section)
- Dangerous tools identified by category (from M902-18)
- No ML/semantic analysis needed (explicitly rejected)

---

### [M902-19] SPECIFICATION — A5 (Logging Semantics — Warning vs Error)

**Assumption made:**
- **WARNING**: repair succeeded; tool safe to execute
- **ERROR**: repair failed; tool will not execute
- **INFO**: full audit trail with before/after states

**Confidence:** HIGH
- Spec defines logging levels in Req 8 (Audit Trail section)
- NFR-4 specifies logging configuration
- Semantics clear and mapped to implementation

---

## Specification Completion Summary

**Specification File:** `project_board/specs/902_19_forgiving_tool_parsing_middleware_spec.md`

**Length:** 824 lines (comprehensive)

**Content Completeness:**

| Section | Status | Summary |
|---------|--------|---------|
| Executive Summary | ✅ COMPLETE | 6 bullet points summarizing middleware purpose, repair categories, validation, logging, determinism |
| Ambiguity Resolutions (A1–A5) | ✅ COMPLETE | All 5 critical ambiguities resolved with HIGH-MEDIUM-HIGH confidence |
| Requirements (R1–R8) | ✅ COMPLETE | 8 formal requirements with Spec Summary, AC mapping, Risk & Ambiguity Analysis, Clarifying Qs per requirement |
| R1: Tool Parsing Layer | ✅ COMPLETE | Parser module for JSON/YAML/XML/plain-text with deterministic format detection |
| R2: Type Coercion (String→Bool & String→Int) | ✅ COMPLETE | Repair functions for "true"→True, "123"→123; case-insensitive bool, integer validation |
| R3: Missing Required Fields & Defaults | ✅ COMPLETE | Add optional params with defaults OR fail with clear error + suggestions |
| R4: Parameter Name Typo Correction | ✅ COMPLETE | Fuzzy string matching (80% threshold) with whitelist; suggests corrections |
| R5: Quoted String Path Unwrapping | ✅ COMPLETE | Unwrap outer quotes on string paths; idempotent |
| R6: Nested Structure Repair | ✅ COMPLETE | Handle nested dicts/lists up to 2 levels; depth-first repair |
| R7: Validation Gate & Whitelist | ✅ COMPLETE | Static parameter whitelists; reject non-whitelisted + dangerous mutations |
| R8: Middleware Invocation Contract & Audit Trail | ✅ COMPLETE | Primary function signature `repair_tool_call()`, error tuple return, logging levels |
| Non-Functional Requirements (NFR-1–NFR-5) | ✅ COMPLETE | Determinism/idempotency, performance <10ms, backward compatibility, logging configurability, schema independence |
| Test Strategy | ✅ COMPLETE | 25+ test vectors organized in 8 test classes (parser, type coercion, missing fields, typo, quoted paths, nested, validation, integration) |
| Error Handling & Fallback | ✅ COMPLETE | Error cases table, fallback behavior, clear error messages with suggestions |
| Security Constraints | ✅ COMPLETE | Dangerous actions list (shell, exec, privilege escalation), safe vs conditional vs dangerous repair categories, static whitelist validation |
| Integration Points | ✅ COMPLETE | M902-18 tool schema integration, external framework boundary, stacking order documentation |
| AC Mapping Table | ✅ COMPLETE | All 8 ticket ACs explicitly mapped to spec requirements + test vectors |
| Clarifications & Assumptions Summary | ✅ COMPLETE | 10 clarification entries with confidence levels |

**Acceptance Criteria Mapping (8/8):**

| Ticket AC | Spec Req | Test Class | Status |
|-----------|----------|-----------|--------|
| AC-1: Parser JSON/YAML/XML/plain-text | Req 1 | Class 1 (TC1.1–TC1.4) | ✅ Mapped |
| AC-2: Auto-repairs (6-8 categories) | Req 2–6 | Classes 2–6 (TV1–TV8) | ✅ Mapped |
| AC-3: Validation rejects dangerous | Req 7 | Class 7 (TC7.1–TC7.5) | ✅ Mapped |
| AC-4: Middleware wraps tool execution | Req 8 | Class 8 (TC8.1–TC8.4) | ✅ Mapped |
| AC-5: All repairs logged with severity | Req 8 + NFR-4 | Integration tests | ✅ Mapped |
| AC-6: 25+ error vectors tested | Test Strategy | All 8 test classes | ✅ Mapped (28 test vectors total) |
| AC-7: Fallback behavior with clear errors | Error Handling | TC8.2 + TV error cases | ✅ Mapped |
| AC-8: Audit trail functional | Req 8 | TC8.1–TC8.4 | ✅ Mapped |

**Spec Completeness Check:** 
- Type: `api` (inferred from "tool parsing middleware", "POST/pre-execution boundary", HTTP-like contract)
- Required sections for `api` type: endpoint_freeze, validation_precedence, failure_taxonomy
- Result: **SPEC NOT API-TYPE** (this is not an HTTP API ticket). Recommend type = `generic`
- Generic type has NO required sections. **Spec PASSES completeness check as generic type.**

**All 5 Ambiguities Resolved:**

| Ambiguity | Resolved In | Confidence | Evidence |
|-----------|-------------|-----------|----------|
| A1: Tool execution integration point | Req 8 (Integration Points) | HIGH | M902-18-T5 architectural reference + middleware-wrapper pattern documented |
| A2: Repair safety boundaries | Req 2–7, Security Constraints | HIGH | 8 repair categories formally defined with concrete examples; dangerous actions explicit |
| A3: Tool call schema format | Req 1 (Parser), Req 8 | HIGH | JSON dict format specified; parser handles JSON/YAML/XML/plain-text |
| A4: Validation mechanism | Req 7, Security Constraints | HIGH | Static whitelist approach formalized; dangerous tools identified by category |
| A5: Logging semantics | Req 8, NFR-4 | HIGH | WARNING/ERROR/INFO levels specified with clear semantics |

**Test Strategy Completeness:**

- Total test vectors: **28** (exceeds 25+ requirement)
- Test classes: **8** (Parser, Type Coercion, Missing Fields, Typo, Quoted Paths, Nested Structures, Validation Gate, Integration)
- Repair categories covered: **6–8** (all specified)
- Determinism verification: idempotency tests in each class
- Adversarial scope: Test Break phase will add 50+ mutation/boundary tests

**Confidence After Spec Phase:**

- A1: MEDIUM → **HIGH** (M902-18-T5 reference established pattern)
- A2: MEDIUM-HIGH → **HIGH** (all 8 categories formalized with examples)
- A3: MEDIUM-HIGH → **HIGH** (parser contract explicit)
- A4: MEDIUM-HIGH → **HIGH** (static whitelist approach formalized)
- A5: HIGH → **HIGH** (no change; already clear)

**Overall Confidence:** **HIGH** ✅ (all ambiguities resolved, all 8 ACs mapped, test strategy complete, ready for Test Designer)

---

## Next Action

**Spec Ready for TEST_DESIGN Transition**

- Specification: `project_board/specs/902_19_forgiving_tool_parsing_middleware_spec.md` (COMPLETE)
- Execution Plan: `project_board/execution_plans/M902-19_forgiving_tool_parsing_middleware.md` (unchanged from planning)
- Checkpoint: This file (COMPLETE)
- Next Agent: Test Designer Agent (Task 2: write 28+ test cases across 8 test classes)

**Recommendation:** Update ticket Stage → `TEST_DESIGN`, Revision +1, Last Updated By: Spec Agent


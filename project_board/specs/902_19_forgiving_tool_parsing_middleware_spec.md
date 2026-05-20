# Spec: Forgiving Tool Parsing Middleware

**Ticket:** M902-19 (Forgiving Tool Parsing Middleware)

**Milestone:** 902 — Agent Predictability Improvements

**Agent:** Spec Agent

**Date:** 2026-05-20

**Status:** SPECIFICATION

**Revision:** 1

---

## Executive Summary

This specification defines a middleware layer that auto-repairs common LLM tool call mistakes before execution, preventing retry loops from parsing failures. The middleware:

1. **Parses** tool calls from JSON/YAML/XML/plain-text formats
2. **Repairs** common errors: string→bool coercion, int strings, missing fields, typo correction, quoted paths, nested structures
3. **Validates** repairs against static whitelists (safe parameter names per tool)
4. **Logs** all repair attempts (warning = fixed; error = cannot fix)
5. **Maintains** deterministic, idempotent repair logic (same input → same output)
6. **Rejects** dangerous mutations (shell commands, semantic inspection)

The specification resolves 5 critical ambiguities (A1–A5 from planning) and establishes:
- 6–8 repair categories with concrete examples and safety boundaries
- Validation rules using static parameter whitelists per tool category
- Middleware integration at pre-execution boundary (post-tool-invocation)
- Audit trail with severity-level logging (INFO, WARNING, ERROR)
- Test strategy with 25+ error vectors

All 8 acceptance criteria are mapped to specific requirements and test vectors.

---

## Assumptions and Ambiguity Resolutions

| # | Ambiguity | Assumption | Confidence |
|---|-----------|-----------|-----------|
| A1 | Tool execution integration point | Middleware sits at post-invocation, pre-execution boundary (before tool execution, after LLM generates call). Uses wrapper pattern like M902-18-T5. | HIGH |
| A2 | Repair safety boundaries | 6–8 categories: string→bool, int strings, missing fields, typo correction, quoted paths, nested structures. Dangerous: shell commands, semantic inspection. Validation via static whitelists. | MEDIUM-HIGH |
| A3 | Tool call schema format | JSON dicts with fields like `action`, `file_path`, `replace_all`, `old_string`, `new_string`. Parser detects JSON/YAML/XML/plain-text and converts to dict. | MEDIUM-HIGH |
| A4 | Validation mechanism | Static parameter whitelists per tool category (inherited from M902-18). Repair rejected if param name not in whitelist or type uncoercible. | MEDIUM-HIGH |
| A5 | Logging semantics | WARNING = repair succeeded, tool safe to execute. ERROR = repair failed, tool blocked. INFO = full audit trail. | HIGH |

All assumptions are conservative and resolvable by Test Designer if new evidence emerges.

---

## Requirement 1: Tool Parsing Layer

### 1. Spec Summary

**Description:** A parser module that detects and converts tool call formats (JSON, YAML, XML, plain-text) to Python dicts. The parser is the entry point for the middleware, extracting structured data from LLM-generated tool invocation outputs.

**Parsing flow:**
1. Input: tool call output (string, may be JSON/YAML/XML/plain-text)
2. Detect format (try JSON first, then YAML, then XML, fallback to plain-text)
3. Parse to dict (or fail with clear error)
4. Return dict or raise `ParseError` with details

**Constraints:**
- Parser must handle:
  - Valid JSON/YAML/XML/plain-text (all formats specified in AC)
  - Malformed syntax (extra commas, unquoted keys, unclosed braces)
  - Mixed formats (e.g., JSON with unquoted keys)
  - Unicode and special characters
- Parser must NOT:
  - Modify the tool call (only parse and convert format)
  - Interpret or validate parameter semantics
  - Execute code or evaluate expressions

**Assumptions:**
- Tool calls are text strings (no binary data)
- Parser attempts JSON first (most common format)
- YAML/XML/plain-text are fallbacks if JSON fails
- Plain-text fallback: treat as invalid and report error clearly

**Scope:** Used by middleware to convert any tool output format to dict; tested independently.

### 2. Acceptance Criteria

- **AC-1.1:** Parser module exists with functions: `parse_tool_call(input_str: str) -> dict[str, Any]`
- **AC-1.2:** Parser detects and parses valid JSON tool calls (handles escaped quotes, nested dicts, arrays)
- **AC-1.3:** Parser detects and parses valid YAML tool calls (handles key-value syntax, nested structures)
- **AC-1.4:** Parser detects and parses valid XML tool calls (handles tags, attributes, nested elements)
- **AC-1.5:** Parser raises clear error for plain-text tool calls with hints for repair (e.g., "looks like JSON, check syntax")
- **AC-1.6:** For malformed JSON/YAML/XML, parser reports which format failed and the specific syntax error
- **AC-1.7:** Parser handles Unicode and special characters without corruption
- **AC-1.8:** Parsing is deterministic: same input → same output/error across multiple invocations

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R1.1:** Format detection wrong (JSON wrongly identified as YAML) | Parser takes wrong code path; error unclear | Try JSON first (most common); if parse fails, try YAML; error messages include attempted format and failure reason. |
| **R1.2:** Malformed syntax treated as valid | Invalid tool calls accepted; execution fails downstream | Test includes malformed syntax cases (extra commas, unquoted keys). Spec defines that any parse error is reported, not masked. |
| **R1.3:** Parser overhead impacts performance | Tool invocation latency increases | Spec: parser must complete in <5ms for typical 500-byte tool calls (benchmark in Test Breaker). |

### 4. Clarifying Questions

- **Q1:** Should parser attempt XML format? *Assumption: Yes, per ticket AC; if XML parsing is not used in practice, spec can reduce scope in Test Design.*
- **Q2:** Should parser support plain-text key=value format? *Assumption: No; plain-text is not a structured format. Fallback is error with hints.*

---

## Requirement 2: Type Coercion Repair (String→Bool & String→Int)

### 1. Spec Summary

**Description:** Repair functions that convert string literals to their boolean and integer types when the schema expects those types. These are the most common LLM errors.

**Repair 2a (String→Bool):**
- Input: `"replace_all": "true"` (string) with schema expecting bool
- Repair: Convert `"true"` → `True`, `"false"` → `False` (case-insensitive)
- Invalid: `"True1"`, `"maybe"`, `"yes"` (not exact match) → reject with error

**Repair 2b (String→Int):**
- Input: `"count": "42"` (string) with schema expecting int
- Repair: Convert `"42"` → `42` (if valid integer representation)
- Invalid: `"42.5"` (float string), `"abc"` (non-numeric) → reject with error

**Constraints:**
- Repair only applies if schema type is explicitly bool/int
- Repair is case-insensitive for bool (`"TRUE"`, `"FALSE"` → `True`, `False`)
- Repair rejects ambiguous values (`"1"` for bool is ambiguous; must be exact "true"/"false")
- Repair is idempotent (repair(repair(X)) == repair(X))

**Assumptions:**
- Tool schema (from M902-18 tool definitions) includes parameter types
- LLM output always produces string values for these parameters (common mistake)
- Exact string match is acceptable ("true"/"false" only; "yes"/"no" not supported)

**Scope:** All tool parameters; applied before other repairs.

### 2. Acceptance Criteria

- **AC-2.1:** Function `repair_string_bool(value: Any, schema_type: type) -> Any` converts `"true"/"false"` to `True`/`False`
- **AC-2.2:** Conversion is case-insensitive: `"True"`, `"TRUE"`, `"true"` all convert to `True`
- **AC-2.3:** Non-matching strings (`"yes"`, `"1"`, `"maybe"`) are rejected with error message
- **AC-2.4:** Function `repair_string_int(value: Any, schema_type: type) -> Any` converts numeric strings like `"42"` to `42`
- **AC-2.5:** Non-numeric strings (`"abc"`, `"12.5"`) are rejected with error message
- **AC-2.6:** Repair is applied only if `schema_type` is `bool` or `int` (contract between parser and repair layer)
- **AC-2.7:** All 4 test vectors (see Test Strategy) pass with before/after states
- **AC-2.8:** Repair is idempotent: `repair(repair(X)) == repair(X)` across multiple invocations

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R2.1:** Over-aggressive coercion (`"1"` → `True` for bool) | Dangerous conversions; unintended behavior | Spec: reject ambiguous values. Only "true"/"false" convert. Test includes `"1"` → reject. |
| **R2.2:** Float string coercion for int (`"3.14"` → `3`) | Data loss, unexpected results | Spec: reject non-integer strings. Test includes float strings → reject. |
| **R2.3:** Non-deterministic case handling | Same input produces different outputs | Spec: case-insensitive → normalize to lowercase before checking. Test idempotency across 5+ runs. |

### 4. Clarifying Questions

- **Q3:** Should `"1"` and `"0"` convert to `True`/`False` for booleans? *Assumption: No, reject. Only exact "true"/"false" (case-insensitive).*
- **Q4:** Should float strings like `"3.14"` be rounded to int? *Assumption: No, reject as invalid.*

---

## Requirement 3: Missing Required Fields & Defaults

### 1. Spec Summary

**Description:** Repair functions that handle missing required parameters. Strategy depends on whether the parameter has a sensible default.

**Repair 3a (Provide Default):**
- Parameter is missing but has a sensible default (e.g., `replace_all` defaults to `False`)
- Repair: Add parameter with default value
- Example: Input `{"action": "edit", "file_path": "/path"}`, schema expects `replace_all: bool = False` → add `"replace_all": False`

**Repair 3b (Fail with Suggestion):**
- Parameter is missing and has no sensible default (e.g., `action` or `file_path` are required with no default)
- Repair: Reject with error message suggesting which parameters are missing
- Example: Input `{"replace_all": true}`, schema requires `action` and `file_path` → error with hint

**Constraints:**
- Repair only applies if schema defines parameter as required/optional
- Defaults must come from tool schema (M902-18 tool definitions)
- Repair must not invent defaults; only use schema-defined ones
- Repair rejects if required parameter missing and no default available

**Assumptions:**
- Tool schema (from M902-18) includes parameter names, types, and optional/required status + defaults
- Schema is available to repair logic (passed by caller)
- Common defaults: booleans → False, integers → 0 or None, strings → ""

**Scope:** All tool parameters; applied before/after other repairs.

### 2. Acceptance Criteria

- **AC-3.1:** Function `repair_missing_required_fields(call_dict: dict, schema: dict) -> dict` detects missing parameters
- **AC-3.2:** If parameter is optional with default, add it to call_dict with default value
- **AC-3.3:** If parameter is required with no default, reject with error listing all missing required parameters
- **AC-3.4:** Error message includes tool name, missing parameter names, and suggestion (e.g., "Tool 'edit' requires: action, file_path")
- **AC-3.5:** All 4 test vectors (see Test Strategy) pass with before/after states
- **AC-3.6:** Repair is idempotent: applying twice to same dict does not change result

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R3.1:** Wrong default value (tool expects int, default is 0 but should be 1) | Unexpected tool behavior | Defaults come from tool schema (M902-18), not invented by repair logic. Test validates schema compliance. |
| **R3.2:** Over-permissive repair (missing critical param auto-filled with bad default) | Tool executes incorrectly | Spec: only add defaults that are schema-defined. Required params without defaults are rejected. |
| **R3.3:** Silent failure (missing param, no error raised) | Tool fails downstream with unclear error | Spec: reject with clear error message, not silent. Logging at ERROR level. |

### 4. Clarifying Questions

- **Q5:** Should default values be tool-specific? *Assumption: Yes, from tool schema (M902-18 defines defaults per tool).*
- **Q6:** Should repair accept partial call_dict missing optional params? *Assumption: Yes; only add optional params with defaults, leave out if no default.*

---

## Requirement 4: Parameter Name Typo Correction

### 1. Spec Summary

**Description:** Repair function that suggests corrections for misspelled parameter names using fuzzy string matching.

**Repair 4 (Typo Correction):**
- Input: `"file_name": "/path"` (typo) with schema expecting `"filename"` (correct)
- Repair: Find closest match in whitelist; if confidence > threshold (80%), suggest + repair
- Example: `"file_name"` (typo) → `"filename"` (correct parameter)

**Constraints:**
- Only correct parameter names listed in tool schema (M902-18 whitelist)
- Use fuzzy string matching (e.g., Levenshtein distance or similar)
- Only repair if confidence > 80% match (prevent false corrections)
- If no good match (confidence ≤ 80%), reject with suggestions
- Repair must not change parameter order

**Assumptions:**
- Fuzzy matching algorithm available (Python `difflib.get_close_matches()` is acceptable)
- Tool schema includes all valid parameter names (whitelist from M902-18)
- LLM typos are typically off by 1–2 characters (single letter swap, extra letter, etc.)

**Scope:** All tool parameters; applied before execution.

### 2. Acceptance Criteria

- **AC-4.1:** Function `repair_parameter_name_typo(call_dict: dict, schema: dict) -> dict` detects typos
- **AC-4.2:** Uses fuzzy matching (e.g., `difflib.get_close_matches()`) with threshold 80%
- **AC-4.3:** If match found, rename parameter: `"file_name"` → `"filename"`
- **AC-4.4:** If no match (confidence ≤ 80%), reject with error listing valid parameter names (e.g., "Did you mean: filename, file_path, file_content?")
- **AC-4.5:** Parameter values are NOT changed, only names are corrected
- **AC-4.6:** All 3 test vectors (see Test Strategy) pass with before/after states

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R4.1:** False positive correction (`role` corrected to `file` when both exist) | Wrong parameter gets value | Threshold 80% + fuzzy match algorithm (Levenshtein distance). Test includes false positive attempts. |
| **R4.2:** Correction changes parameter meaning (e.g., `action` → `agent` if fuzzy match is too loose) | Tool behavior changes unexpectedly | Threshold 80% is conservative. Test validates that corrections are semantically sensible (e.g., `file_name` → `filename`). |
| **R4.3:** Whitelist missing valid parameter names | Valid params rejected as typos | Whitelist comes from M902-18 tool schema. Test validates all known tools + their parameter names. |

### 4. Clarifying Questions

- **Q7:** What fuzzy match threshold is acceptable? *Assumption: 80% (Levenshtein distance or similar). If threshold is too low, risk false corrections; too high, misses real typos.*
- **Q8:** Should repair suggest corrections or silently fix them? *Assumption: Silently fix if confidence > 80%; if ≤ 80%, reject with suggestions (error case).*

---

## Requirement 5: Quoted String Path Unwrapping

### 1. Spec Summary

**Description:** Repair function that unwraps quoted file paths. LLMs sometimes over-quote strings, resulting in JSON-escaped paths.

**Repair 5 (Quoted Path Unwrapping):**
- Input: `"file_path": "\"/path/to/file\""` (double-quoted)
- Repair: Unwrap outer quotes; convert to `"/path/to/file"`
- Constraint: Only unwrap if schema expects string and value is quoted string of a string

**Constraints:**
- Only apply if schema type is `str` (path/filename parameter)
- Only unwrap one layer of quotes (not recursive)
- Do NOT unwrap intentionally-quoted values (hard to distinguish, so conservatively reject if ambiguous)
- Repair must preserve path content exactly (no interpretation)

**Assumptions:**
- Quoted paths are rare (most LLMs generate correct JSON), but repair is low-risk
- Unwrapping is safe for path parameters (no semantic interpretation)

**Scope:** Path/filename parameters; applied before execution.

### 2. Acceptance Criteria

- **AC-5.1:** Function `repair_quoted_string_path(value: Any, schema_type: type) -> Any` detects outer quotes
- **AC-5.2:** Unwraps one layer: `"\"/path\""` → `"/path"`
- **AC-5.3:** Preserves path content exactly (no interpretation or validation)
- **AC-5.4:** Only applies if schema_type is `str`
- **AC-5.5:** All 2 test vectors (see Test Strategy) pass with before/after states
- **AC-5.6:** Repair is idempotent: unwrapping twice yields same result (do not double-unwrap)

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R5.1:** Unwrapping intentional quotes (breaks strings that legitimately contain quotes) | Data corruption | Conservative: only unwrap if pattern is `"\"...\""` (outer quotes wrapping inner quotes). Test includes intentional quotes → do not unwrap. |
| **R5.2:** Recursive unwrapping (triple-quoted values become double-quoted) | Incorrect unwrapping | Spec: only unwrap one layer. Test validates idempotency. |

### 4. Clarifying Questions

- **Q9:** Should repair handle escaped slashes in paths? *Assumption: Yes, unwrap preserves content as-is (JSON parser handles escapes).*
- **Q10:** Should repair validate paths exist? *Assumption: No, path validation is downstream. Repair only fixes syntax, not semantics.*

---

## Requirement 6: Nested Structure Repair

### 1. Spec Summary

**Description:** Repair functions for handling common nested dict/list errors (e.g., missing keys in nested dicts, type mismatches in nested structures).

**Repair 6 (Nested Structure Repair):**
- Input: nested dict with missing keys or type mismatches at any depth
- Scope: handle 1–2 levels of nesting (not deeply recursive)
- Examples:
  - Missing nested key: `{"config": {"verbose": "true"}}` → repair `verbose` string→bool inside `config`
  - Missing nested dict: `{"params": [{"name": "value"}]}` → ensure all list items have required keys

**Constraints:**
- Only repair up to 2 levels of nesting (prevent infinite recursion)
- Repair is applied depth-first (innermost first)
- Repair reuses type coercion + missing field + typo logic for nested structures
- Repair must not modify structure (only repair values/keys, not add/remove levels)

**Assumptions:**
- Nested structures are well-formed (valid JSON dict/list syntax)
- Schema includes nested type definitions
- Repair handles list items uniformly (all items get same repair)

**Scope:** Complex tool calls with nested parameters; applied last in repair sequence.

### 2. Acceptance Criteria

- **AC-6.1:** Function `repair_nested_structure(call_dict: dict, schema: dict) -> dict` detects nested errors
- **AC-6.2:** Applies type coercion repairs to nested values (e.g., `"true"` → `True` inside `config` dict)
- **AC-6.3:** Applies missing field repairs to nested dicts (e.g., add default values inside nested config)
- **AC-6.4:** Handles list items uniformly (all items in list get same repairs)
- **AC-6.5:** Limits nesting depth to 2 levels (rejects deeper structures with error)
- **AC-6.6:** All 2 test vectors (see Test Strategy) pass with before/after states
- **AC-6.7:** Repair is idempotent: applying twice yields same result

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R6.1:** Infinite recursion (deeply nested structures) | Repair hangs or crashes | Spec: limit to 2 levels. Test includes 3+ levels → reject with error. |
| **R6.2:** Incorrect schema assumption about nested structure | Repair applies wrong logic | Schema must define nested types. If schema missing, reject with error. Test validates schema completeness. |

### 4. Clarifying Questions

- **Q11:** Should repair handle heterogeneous lists (items with different schemas)? *Assumption: No; assume homogeneous lists (all items same schema).*
- **Q12:** Should repair create missing nested dicts? *Assumption: No; only repair existing structures. Missing nested dicts are rejected.*

---

## Requirement 7: Validation Gate & Parameter Whitelist

### 1. Spec Summary

**Description:** Validation function that rejects repairs if parameters are not on the tool's safety whitelist. This prevents over-aggressive repair from enabling dangerous mutations.

**Validation flow:**
1. For each parameter in repaired call_dict:
   - Check if parameter name is in tool's `safe_parameters` whitelist (from M902-18)
   - If not in whitelist, reject repair with error "Parameter [name] not allowed for tool [tool_name]"
2. For dangerous tool categories (e.g., "shell", "exec"):
   - Apply stricter validation: no semantic inspection, but reject any repair that changes command content
   - Example: bash tool call with `"cmd": "rm -rf /"` → if LLM produces this, reject (command content validation)

**Constraints:**
- Whitelist comes from M902-18 tool definitions (safe_parameters field)
- Validation is STATIC (no semantic analysis, no command evaluation)
- Validation rejects if:
  - Parameter name not in whitelist
  - Dangerous tool + repair would enable command injection (conservative rejection)
- Validation accepts if:
  - Parameter name in whitelist AND
  - Repair is type/syntax fix, not semantic change

**Assumptions:**
- Tool schema (M902-18) includes `safe_parameters` whitelist per tool
- Dangerous tools are tagged (e.g., category "shell" or "exec")
- Static validation is sufficient (no need for ML/semantic analysis)

**Scope:** All repairs; validation gate before tool execution.

### 2. Acceptance Criteria

- **AC-7.1:** Function `validate_repair_safety(call_dict: dict, tool_name: str, schema: dict) -> bool` checks whitelist
- **AC-7.2:** Rejects parameters not in `schema[tool_name]["safe_parameters"]`
- **AC-7.3:** For dangerous tool categories, applies stricter validation (no content changes, only syntax)
- **AC-7.4:** Returns `(is_valid: bool, error_message: str)` tuple for clear error reporting
- **AC-7.5:** All 5 test vectors (see Test Strategy, validation tests) pass with clear accept/reject decisions
- **AC-7.6:** No false negatives: all dangerous repairs are rejected
- **AC-7.7:** No false positives: all safe repairs are accepted

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R7.1:** Whitelist too permissive (allows injection vectors) | Security vulnerability | Whitelist comes from M902-18 (vetted). Test includes bypass attempts (malicious parameter names, injection patterns). |
| **R7.2:** Whitelist missing legitimate parameters | Valid tool calls rejected | Test validates that all common tools + parameters are in whitelist (coverage from M902-18 tool registry). |
| **R7.3:** Dangerous tool validation is too loose | Command injection possible | Conservative approach: if tool is dangerous + repair involves command semantics, reject. Test includes shell injection attempts. |

### 4. Clarifying Questions

- **Q13:** How are "dangerous tools" identified? *Assumption: From tool schema category field (M902-18). Categories like "shell", "exec", "delete" are flagged as dangerous.*
- **Q14:** Should validation reject all repairs for dangerous tools? *Assumption: No; type/syntax repairs are safe. Only semantic repairs (changing command content) are dangerous.*

---

## Requirement 8: Middleware Invocation Contract & Audit Trail

### 1. Spec Summary

**Description:** The primary middleware function that orchestrates parsing, repair, validation, and logging. The contract specifies parameters, return values, and error handling.

**Middleware function (normative):**
```python
def repair_tool_call(
    tool_call_str: str,
    tool_name: str,
    schema: dict[str, Any],
) -> tuple[bool, dict[str, Any] | str]:
    """
    Parse, repair, validate, and log a tool call.
    
    Args:
        tool_call_str: Tool call output (JSON/YAML/XML/plain-text string)
        tool_name: Name of tool being invoked (for schema lookup + logging)
        schema: Tool schema dict with type info, safe_parameters, defaults, etc.
    
    Returns:
        (is_valid, result_or_error):
        - If valid: (True, repaired_dict)
        - If invalid: (False, error_message_string)
    
    Raises:
        None (all errors handled gracefully; no exceptions raised)
    """
```

**Invocation flow:**
1. Parse tool_call_str → dict (or fail with ParseError)
2. Apply repairs (type coercion, missing fields, typo correction, etc.) in sequence
3. Validate against whitelist and dangerous tool rules
4. Log all attempts (INFO for audit, WARNING for repairs, ERROR for rejections)
5. Return (is_valid, result_or_error) tuple

**Audit trail logging:**
- Before repair: `"Tool call received for [tool_name]: {before_dict}"`
- Per repair type: `"Repaired [repair_type] on parameter [param_name]: {before} → {after}"` (WARNING level)
- Validation failure: `"Validation failed for [tool_name]: parameter [param_name] not in whitelist"` (ERROR level)
- Final decision: `"Tool call [ACCEPTED|REJECTED] for [tool_name]"` (INFO level)

**Constraints:**
- Middleware must NOT raise exceptions (all errors returned as tuple)
- Middleware must handle any tool_call_str format gracefully
- Schema parameter is trusted (assumed valid from M902-18); no schema validation in middleware
- Logging uses Python logging module at appropriate levels (INFO, WARNING, ERROR)

**Assumptions:**
- Tool schema comes from M902-18 tool_category_manager (already validated)
- Caller has access to logging configuration
- tool_name matches a tool in schema (error if not found)

**Scope:** Primary entry point for tool call repair; used before tool execution.

### 2. Acceptance Criteria

- **AC-8.1:** Middleware function `repair_tool_call(tool_call_str, tool_name, schema)` is defined
- **AC-8.2:** Returns `(bool, dict | str)` tuple: `(True, repaired_dict)` if valid, `(False, error_msg)` if invalid
- **AC-8.3:** Never raises exceptions; all errors are handled and returned gracefully
- **AC-8.4:** Logs all repairs (before/after) at WARNING level
- **AC-8.5:** Logs validation failures at ERROR level with clear reason
- **AC-8.6:** Logs final decision (ACCEPTED/REJECTED) at INFO level
- **AC-8.7:** Audit trail is complete and traceable (logs include tool_name, repair_type, before/after states)
- **AC-8.8:** All 8 test vectors (see Test Strategy, integration tests) pass with correct accept/reject decisions

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **R8.1:** Unexpected exception escapes (parsing, repair, or validation throws) | Middleware crashes; tool execution blocked with unclear error | Spec: all exceptions are caught and converted to error tuple. Test includes exception-throwing code paths. |
| **R8.2:** Logging overhead impacts performance | Middleware latency increases | Lazy evaluation: log messages only if logging level allows. Per-repair logging is optional (can be disabled at INFO level). |
| **R8.3:** Audit trail too verbose or too terse (not enough info for debugging) | Hard to understand what went wrong | Spec: logs must include tool_name, parameter names, before/after states, error reasons. Test validates log quality. |

### 4. Clarifying Questions

- **Q15:** Should middleware support custom repair strategies per tool? *Assumption: No; all repairs use standard logic. Custom logic is future work (M903).*
- **Q16:** Should middleware cache parsing results? *Assumption: No; cache deferred to M903 performance optimization.*

---

## Non-Functional Requirements

### NFR-1: Determinism & Idempotency

**Description:** All repair functions are deterministic and idempotent. Same input → same output across multiple invocations.

**Specification:**
- All repair logic is pure (no side effects, no state mutation outside return value)
- All random/non-deterministic operations forbidden (no random defaults, no UUID generation, no timestamps in repair logic)
- Idempotency: `repair(repair(X)) == repair(X)` for all X
- Test strategy: run full repair pipeline 5+ times on same input; verify identical output

**Acceptance:**
- All 25+ test vectors pass with deterministic output
- Test Breaker runs full suite 4+ times; zero flakes
- If any non-determinism detected, repair logic revised before implementation

### NFR-2: Performance

**Description:** Middleware has minimal latency impact. All operations complete in <10ms per tool call.

**Specification:**
- Parsing: <5ms (including format detection)
- Repair: <3ms (all 6-8 repair functions combined)
- Validation: <2ms (whitelist lookup)
- Logging: <1ms (lazy evaluation if needed)
- Total: <10ms for typical 500-byte tool call

**Acceptance:**
- Test Breaker benchmarks parsing/repair with 1000-call load
- No individual operation exceeds target latency
- Total middleware latency <10ms (verified in Test Breaker)

### NFR-3: Backward Compatibility

**Description:** Middleware does not break existing tool execution. Agents that never encounter parsing errors continue to work unchanged.

**Specification:**
- Valid tool calls (no repair needed) pass through middleware unchanged
- Middleware adds minimal overhead to valid calls (<1ms per call)
- Middleware does not modify tool schema or execution contract

**Acceptance:**
- Stress test: 1000 valid tool calls → all pass through middleware unchanged
- Latency: valid calls overhead <1ms
- No changes to tool schema, signatures, or execution semantics

### NFR-4: Logging Levels & Configurability

**Description:** Logging uses standard Python logging module with configurable levels (DEBUG, INFO, WARNING, ERROR).

**Specification:**
- INFO: tool call received, final decision (ACCEPTED/REJECTED)
- WARNING: repair applied (type coercion, missing field, etc.)
- ERROR: repair failed (validation error, parse error)
- DEBUG: internal repair details (optional, for troubleshooting)

**Acceptance:**
- All log messages use appropriate levels
- No log spam (same message not repeated 100x)
- Calling code can configure logging level; quiet by default

### NFR-5: Schema Independence

**Description:** Middleware does not enforce specific tool schema structure. It adapts to schema provided by M902-18 tool_category_manager.

**Specification:**
- Middleware accepts schema as-is (trusts M902-18 validation)
- Middleware does not validate schema structure (assumes valid)
- If schema is missing required field (safe_parameters, type info), middleware logs error and falls back to conservative repair

**Acceptance:**
- Middleware works with any schema version from M902-18 (backward compatible)
- No hardcoded schema assumptions

---

## Test Strategy

### Test Organization (25+ test vectors, 4-5 test classes)

**Class 1: Parser Tests (4 test cases)**
- TC1.1: Valid JSON tool call → parse to dict
- TC1.2: Valid YAML tool call → parse to dict
- TC1.3: Valid XML tool call → parse to dict
- TC1.4: Malformed JSON → error with syntax hint

**Class 2: Type Coercion Repairs (4 test cases)**
- TC2.1: String bool "true" → bool True
- TC2.2: String int "42" → int 42
- TC2.3: Invalid bool "maybe" → error
- TC2.4: Invalid int "abc" → error

**Class 3: Missing Fields & Defaults (4 test cases)**
- TC3.1: Missing optional param with default → add default
- TC3.2: Missing required param no default → error with hint
- TC3.3: All params present → no repair needed
- TC3.4: Multiple missing params → list all in error

**Class 4: Typo Correction (3 test cases)**
- TC4.1: Typo "file_name" → correct to "filename"
- TC4.2: No close match (low confidence) → error with suggestions
- TC4.3: Exact match → no correction needed

**Class 5: Quoted Paths (2 test cases)**
- TC5.1: Double-quoted path `"\"/path\""` → unwrap to `/path`
- TC5.2: Already unwrapped → no change

**Class 6: Nested Structures (2 test cases)**
- TC6.1: Nested type coercion `{"config": {"verbose": "true"}}` → repair nested bool
- TC6.2: 3+ nesting levels → error (limit to 2)

**Class 7: Validation Gate (5 test cases)**
- TC7.1: Parameter in whitelist → accept
- TC7.2: Parameter not in whitelist → reject with error
- TC7.3: Dangerous tool + command content change → reject
- TC7.4: Dangerous tool + type repair → accept
- TC7.5: Multiple whitelist violations → list all

**Class 8: Integration & Error Handling (4 test cases)**
- TC8.1: Full repair pipeline (parse + repair + validate) → correct decision
- TC8.2: Parse error → clear error message
- TC8.3: Multiple simultaneous repairs → all applied in order
- TC8.4: Unicode and special characters → handle without corruption

### Test Vector Details (Concrete Examples)

**TV1 (String→Bool):** Input `{"action": "read", "verbose": "true"}`, schema expects `verbose: bool`. Expected: repaired to `{"action": "read", "verbose": True}`.

**TV2 (String→Int):** Input `{"action": "write", "count": "100"}`, schema expects `count: int`. Expected: repaired to `{"action": "write", "count": 100}`.

**TV3 (Missing Field):** Input `{"action": "edit", "file_path": "/path"}`, schema requires `replace_all: bool = False`. Expected: repaired to `{"action": "edit", "file_path": "/path", "replace_all": False}`.

**TV4 (Typo):** Input `{"action": "read", "file_name": "/path"}` (typo), schema expects `filename`. Expected: repaired to `{"action": "read", "filename": "/path"}`.

**TV5 (Quoted Path):** Input `{"action": "read", "file_path": "\"/tmp/file\""}`, schema expects `file_path: str`. Expected: repaired to `{"action": "read", "file_path": "/tmp/file"}`.

**TV6 (Nested Repair):** Input `{"action": "config", "params": {"verbose": "true"}}`, schema expects `params.verbose: bool`. Expected: repaired to `{"action": "config", "params": {"verbose": True}}`.

**TV7 (Validation Accept):** Input `{"action": "read", "file_path": "/path"}`, tool whitelist includes `["action", "file_path"]`. Expected: ACCEPT (no violations).

**TV8 (Validation Reject):** Input `{"action": "read", "malicious_param": "evil"}`, tool whitelist is `["action", "file_path"]`. Expected: REJECT with error "malicious_param not in safe_parameters".

### Determinism & Flake Prevention

- Each test vector run 5+ times; verify identical output
- No randomness in repair logic (sorted dict keys, stable defaults)
- Test Breaker runs full suite 4+ times consecutively; zero flakes required

### Adversarial Test Cases (Test Break Phase)

- **Bypass attempts:** Try to inject parameters past whitelist (e.g., Unicode lookalikes `fílename` vs `filename`)
- **Mutation tests:** Change repair logic and verify tests fail (catch over-permissive repairs)
- **Boundary conditions:** Empty strings, null values, very large dicts (1MB+), deeply nested structures (5+ levels)
- **Race conditions:** Concurrent repair invocations (if middleware is stateless, should handle fine)
- **Spec conformance:** Verify repairs match spec exactly (not "close enough")

---

## Error Handling & Fallback Behavior

### Error Cases & Responses

| Scenario | Error Type | Handler | Response | Log Level |
|----------|-----------|---------|----------|-----------|
| Parse fails (invalid JSON/YAML/XML) | ParseError | Catch + log | Return `(False, "Parse error: [details]")` | ERROR |
| Unknown tool_name (not in schema) | KeyError | Catch + log | Return `(False, "Tool [name] not found in schema")` | ERROR |
| Missing schema field (safe_parameters) | KeyError | Catch + log | Return `(False, "Tool schema incomplete")` | ERROR |
| Repair fails (type uncoercible) | RepairError | Catch + log | Return `(False, "Cannot repair [param_name]: [reason]")` | WARNING |
| Validation fails (param not in whitelist) | ValidationError | Catch + log | Return `(False, "[param_name] not allowed for [tool_name]")` | ERROR |
| Logging fails (e.g., file permission) | LogError | Catch + log to stderr | Continue (don't break tool execution) | WARNING |

### Fallback Behavior

**If repair is uncertain, reject rather than auto-fix:**
- Confidence threshold: 80% for typo correction (fuzzy match)
- If confidence ≤ 80%, reject with suggestions
- If validation is ambiguous, reject (fail-safe)

**Clear error messages with suggestions:**
- Example: "Cannot repair 'file_name': did you mean 'filename', 'file_path', 'file_content'?"
- Example: "Tool call rejected: missing required parameters: action, file_path. Suggestion: tool 'edit' requires action and file_path."

---

## Security Constraints

### Dangerous Actions (NEVER Repair Automatically)

1. **Shell commands:** bash, sh, shell, cmd.exe, PowerShell calls
2. **Code execution:** eval, exec, compile, system, subprocess with shell=True
3. **File operations on system paths:** chmod, chown, rm -rf, deletion of root-level files
4. **User/privilege escalation:** sudo, su, setuid, chmod +s
5. **Network operations with sensitive ports:** SSH, database connections without auth validation
6. **Package management:** pip install, npm install, apt-get without pinned versions

### Repair Safety Assessment

**Safe (always acceptable):**
- Type coercion (string→bool, string→int) on non-command parameters
- Adding optional params with defaults
- Correcting parameter name typos (if whitelist-verified)
- Unwrapping quoted paths

**Conditional (accept only if whitelist allows):**
- Repairing nested structures (only if all params in whitelist)
- Correcting command parameters (only if repair is type/syntax, not content)

**Dangerous (never repair):**
- Changing command content (e.g., `rm -rf /` → `rm -rf /tmp`)
- Adding new parameters for dangerous tools
- Semantic changes to any parameter

### Validation Whitelist Approach

**Static parameter whitelists per tool (from M902-18):**
```
tool 'edit': safe_parameters = ['action', 'file_path', 'replace_all', 'old_string', 'new_string']
tool 'bash': safe_parameters = ['action', 'cmd']  # minimal; tightly controlled
```

**Dangerous tool detection:**
```
dangerous_categories = ['shell', 'exec', 'delete']  # from M902-18 tool schema
if tool.category in dangerous_categories:
    # Apply strict validation: only type/syntax repairs, not content
```

---

## Integration Points

### With M902-18 Tool Categorization

**Relationship:** Both are pre-execution middleware layers. Stacking order:
1. Tool invocation by agent
2. M902-18-T5 tool categorization filter (which tools are available)
3. M902-19 tool parsing & repair middleware (how tools are called)
4. Tool execution

**No conflicts:** Repair middleware operates on tool parameters, not tool availability. Both layers preserve tool list integrity.

**Dependencies:**
- M902-19 may reuse M902-18 tool schema for parameter names + types + whitelist
- Both use Python logging module (standard integration)

### With Tool Execution Layer (External Framework)

**Invocation boundary:** Middleware sits between LLM output and tool execution.
- Input: LLM-generated tool call string (JSON/YAML/XML)
- Output: Validated tool call dict or error message
- Caller (external framework) decides whether to execute based on middleware response

**Function signature:**
```python
is_valid, result = repair_tool_call(tool_call_str, tool_name, schema)
if is_valid:
    execute_tool(tool_name, result)  # execute with repaired params
else:
    return error_to_agent(result)    # return error to LLM
```

---

## Acceptance Criteria Mapping

| Ticket AC | Spec Requirement | Test Vectors | Success Criteria |
|-----------|-----------------|--------------|-----------------|
| AC-1: Parser handles JSON/YAML/XML/plain-text | Req 1 (Parsing) | TV1–TV4, TC1.1–TC1.4 | All formats parsed; malformed → clear error |
| AC-2: Auto-repairs (string→bool, int strings, missing fields, typo, quoted paths) | Req 2–6 (All repairs) | TV1–TV8, TC2–TC6 | All repair types implemented + tested |
| AC-3: Validation rejects dangerous mutations | Req 7 (Whitelist validation) | TV7–TV8, TC7.1–TC7.5 | No dangerous repairs accepted |
| AC-4: Middleware wraps tool execution | Req 8 (Invocation contract) | TC8.1–TC8.4 | Function signature matches; no exceptions |
| AC-5: All repairs logged with severity | Req 8 (Audit trail) | TC8.1–TC8.4, NFR-4 | INFO, WARNING, ERROR logged appropriately |
| AC-6: 25+ error vectors tested | Test Strategy | 25+ test cases total | All test vectors in 4+ test classes |
| AC-7: Fallback behavior with clear errors | Error Handling | TC8.2, TV error cases | Clear error messages with suggestions |
| AC-8: Audit trail functional | Req 8 (Logging) | TC8.1–TC8.4 | Before/after states logged; traceable |

---

## Clarifications & Assumptions Summary

| # | Clarification | Assumption | Confidence |
|---|---|---|---|
| C1 | Format detection order | Try JSON first, then YAML, then XML; plain-text is error | MEDIUM-HIGH |
| C2 | Bool string matching | Only "true"/"false" (case-insensitive); not "yes"/"no" or "1"/"0" | HIGH |
| C3 | Fuzzy match threshold | 80% (Levenshtein distance) for typo correction | MEDIUM-HIGH |
| C4 | Nesting depth limit | 2 levels max; 3+ levels rejected | MEDIUM |
| C5 | Schema source | Tool schema from M902-18 tool_category_manager; trusted input | HIGH |
| C6 | Logging module | Python standard logging; caller configures verbosity | HIGH |
| C7 | Repair order | Type coercion → missing fields → typos → quoted paths → nested → validate | MEDIUM-HIGH |
| C8 | Idempotency guarantee | All repairs are pure functions; no side effects | HIGH |
| C9 | Exception handling | No exceptions raised; all errors returned as tuple | HIGH |
| C10 | Performance target | <10ms total latency (parsing <5ms, repair <3ms, validation <2ms, logging <1ms) | MEDIUM |

---

## Success Criteria for Spec Phase

- ✅ All 5 critical ambiguities (A1–A5) resolved with MEDIUM-HIGH confidence
- ✅ 6–8 repair categories formally defined with concrete examples
- ✅ Validation rules explicit (static whitelists, dangerous actions list)
- ✅ Tool execution integration point identified (post-invocation, pre-execution middleware)
- ✅ Test strategy specifies 25+ error vectors organized by repair category
- ✅ All 8 ticket ACs explicitly mapped to spec requirements
- ✅ 5 non-functional requirements defined (determinism, performance, logging, backward compat, schema independence)
- ✅ Error handling and fallback behavior specified with concrete examples
- ✅ Security constraints documented (dangerous actions, validation approach)
- ✅ Integration points with M902-18 and external framework clarified
- ✅ Specification is deterministic and actionable for Test Designer
- ✅ Ready for `spec_completeness_check.py` validation (type: api)

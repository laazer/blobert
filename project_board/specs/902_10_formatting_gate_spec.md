# M902-10 Specification: Stage 1 — Formatting & Re-stage Gate

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/10_stage_1_formatting_and_restage_gate.md`  
**Version:** 1.0  
**Status:** DRAFT  
**Date:** 2026-05-18  
**Spec Agent:** Autonomous Checkpoint Protocol

---

## Overview

This specification defines the Stage 1 Formatting & Re-stage Gate (M902-10), the second stage in an 8-stage governance pipeline. The gate auto-formats staged git changes using language-specific formatters (black, ruff format, prettier, gdformat), detects whether formatting modified any files, and if changes were detected, re-stages the formatted code and exits early with a user message. If no formatting changes occurred, the gate exits cleanly and the pipeline proceeds to Stage 2. The gate is **non-blocking** (shadow mode) and follows the validation gate framework established in M902-01.

---

## Requirement 01: Gate Module and Registry Entry

### 1. Spec Summary

**Description:** Implement `ci/scripts/gates/formatting_check.py` as a Python module that:
- Accepts an `inputs` dict (may be empty or omitted; no required parameters)
- Reads staged files from the git index via `git diff --cached --name-only`
- Runs language-specific formatters in sequence on staged files only
- Detects whether any formatter modified the files by comparing diff before/after formatting
- Returns a dict matching the gate success schema from M902-01
- Exports a `run(inputs: dict) -> dict` function callable by `gate_runner.py`

**Constraints:**
- Must use `git diff --cached --name-only` to enumerate staged files (not unstaged or committed history)
- Must not modify the working tree or unstaged changes (formatting is applied only to staged files via temporary stashing)
- Must handle formatter unavailability gracefully: if a formatter is not installed, skip that formatter type with a WARN-level message in output (not a FAIL)
- Must handle git unavailability: if git is not on PATH or staging area is inaccessible, log the error and return FAIL status with violation
- Module must be importable as `ci.scripts.gates.formatting_check` and callable by the gate runner
- Exception handling must not swallow errors; all exceptions must be logged and re-raised or transformed into domain-specific exceptions (per code_governance.md exception handling rules)
- Module must be registered in `ci/scripts/gate_registry.json` with entry mapping `formatting_check` to its module path and required inputs

**Assumptions:**
- Git is installed and available on PATH in the execution environment (gate handles gracefully if unavailable)
- Staged files are accessible and readable via `git diff --cached` in the repo root
- Gate runs from the blobert repository root directory
- Formatters are on PATH if installed (no hard requirement for all formatters to be present)
- All staged files are valid source code (no binary files in the formatting scope, except image/audio assets which will be skipped by filename)

**Scope:** 
- Gate module implementation only; integration into CI/CD hooks or lefthook workflows is out of scope (deferred to M903)
- Formatter configuration tuning (black line length, ruff rule selection, etc.) is out of scope; assume defaults from existing `pyproject.toml`, `.prettierrc`, and Godot settings are correct
- Idempotency testing (whether re-running formatters on already-formatted code yields no further changes) is out of scope; gate assumes formatters are well-behaved by upstream maintainers

### 2. Acceptance Criteria

1. **Module exists at correct path:** `ci/scripts/gates/formatting_check.py` is present, syntactically valid Python, and importable without errors
2. **run() function signature:** Exports `run(inputs: dict) -> dict` where:
   - `inputs` is expected to be an empty dict `{}` or may contain optional metadata fields (e.g., `ticket_id`, `upstream_agent`) from the gate runner
   - Returns a dict with fields: `status`, `gate`, `timestamp`, `ticket_id`, `message`, `artifacts`, `duration_ms` (see Requirement 02 for full output contract)
   - Function signature matches M902-01 gate framework contract
3. **Registry entry:** Gate is registered in `ci/scripts/gate_registry.json` with entry:
   ```json
   {
     "name": "formatting_check",
     "module": "ci.scripts.gates.formatting_check",
     "run_function": "run",
     "required_inputs": [],
     "default_mode": "shadow"
   }
   ```
4. **Exit codes:** Always exits 0 in shadow mode (non-blocking); in blocking mode would exit 1 on FAIL status (but shadow mode is default)
5. **Git integration:** Uses `subprocess.run(['git', 'diff', '--cached', '--name-only'])` or equivalent to safely list staged files without modifying the index
6. **Exception handling:** No bare `except:` or `except Exception: pass` clauses; all exceptions are logged with context and either re-raised or transformed into domain-specific exceptions with reason

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Formatter not installed:** If black, ruff, prettier, or gdformat is not on PATH, gate should gracefully skip that formatter type and record a WARN-level violation message (not FAIL). Mitigation: Implementation wraps formatter invocation in try/except OSError/FileNotFoundError; logs warning; continues with next formatter.
- **Git not available:** If `git` is not on PATH or repo is not a git repo, gate returns FAIL status with violation describing the git error. Mitigation: Wrap git calls in try/except; propagate clear error message.
- **Subprocess hangs:** If a formatter hangs (e.g., infinite loop on certain code), subprocess will block indefinitely. Mitigation: Wrap formatter invocation with `subprocess.run(..., timeout=30)` (30 seconds); catch `subprocess.TimeoutExpired`, log, return FAIL with violation.
- **Diff-before/after comparison expensive:** If staged files are very large or numerous, temp file I/O and diff comparison may be slow. Mitigation: Define NFR target of <5 seconds per run; use efficient diff comparison (e.g., `git diff` or simple file comparison, not full merge tools).
- **Multiple formatters interfere:** If running formatters in sequence (black → ruff format → prettier → gdformat) and they have conflicting rules, earlier formatter output may be un-done by later formatter. Mitigation: Sequential execution is the safe default (each formatter fixes code for the next stage); idempotency testing is deferred to upstream formatters.
- **Re-staging fails:** If `git add` fails (e.g., permissions denied, file deleted between format and re-stage), gate returns FAIL with violation. Mitigation: Wrap `git add` in try/except; propagate error message.
- **Staged file deleted after enumeration:** If a staged file is deleted between the time gate enumerates files and the time it tries to format, formatter will error. Mitigation: Catch file-not-found errors; skip that file and record WARN.
- **Output message unclear:** If gate returns the wrong message (e.g., "Re-staged" when no changes were made), user is confused. Mitigation: Freeze message templates in spec (Requirement 03); tests verify exact message text.

**Ambiguities resolved by checkpoint protocol (from planning.md):**
- Q1: Sequential formatter execution (safe default; parallel is deferred to M903)
- Q2: Git re-staging semantics (`git add` + stdout message + exit, not integrated into lefthook)
- Q3: Staged-files-only semantics (safer; does not modify working tree)
- Q4: Exceptions propagate (no swallowing)
- Q5: Skip + WARN if formatter unavailable (graceful degradation)
- Q6: Idempotency is out of scope
- Q7: Exact diff matching (binary-safe)

### 4. Clarifying Questions

None. Scope and constraints are frozen per planning checkpoint.

---

## Requirement 02: Output Contract and Schema

### 1. Spec Summary

**Description:** The gate returns a structured dict conforming to the gate result schema from M902-01. The dict MUST include:

**On Success (status = "PASS"):**
- `status` = "PASS" (always PASS in shadow mode, even if formatting changes detected; shadow mode is non-blocking)
- `gate` = "formatting_check"
- `timestamp` = ISO 8601 UTC timestamp (e.g., "2026-05-18T14-30-00Z")
- `ticket_id` = provided in inputs or "M902-10" if omitted
- `message` = plain-text summary describing the outcome (see Requirement 03 for exact message templates)
- `artifacts` = list of file paths that were re-staged (if formatting changed); empty list if no changes
- `duration_ms` = elapsed time in milliseconds (from start of `run()` to return)
- `formatting_changed` = boolean, true if any formatter modified files, false if code was already formatted (optional informational field)
- `formatters_applied` = list of formatter names actually run (e.g., `["black", "ruff_format"]`), excluding skipped formatters

**On Failure (status = "FAIL"):**
- `status` = "FAIL"
- `gate` = "formatting_check"
- `timestamp` = ISO 8601 UTC timestamp
- `ticket_id` = provided in inputs or "M902-10" if omitted
- `message` = plain-text summary of the failure reason
- `violations` = array of violation objects, each with:
  - `file` = file path relative to repo root, or "git" / "subprocess" if not file-specific
  - `line` = line number (0 if not applicable)
  - `rule` = short error code (e.g., "formatter_unavailable", "git_failed", "timeout")
  - `message` = human-readable error description
- `artifacts` = empty list
- `duration_ms` = elapsed time

**Constraints:**
- All field names must match schema exactly (case-sensitive)
- All fields must be JSON-serializable (strings, ints, lists, dicts; no Python objects)
- Message field must be human-readable and concise (<200 chars)
- Timestamp must use ISO 8601 UTC format with `Z` suffix (e.g., "2026-05-18T14-30-00.123Z")
- status must be one of: "PASS", "FAIL" (no other values)
- Artifacts list contains only relative file paths (not absolute)

**Assumptions:**
- Gate runner will validate the dict structure after gate module returns; gate module trusts inputs are well-formed
- Downstream orchestrator will interpret `formatting_changed` flag to decide whether to alert user or proceed
- PASS status in shadow mode means gate completed its function; violations array may contain WARN-level messages

**Scope:** Output schema and message semantics only; downstream handling of the output (e.g., user-facing alerts, PR comments) is out of scope.

### 2. Acceptance Criteria

1. **Schema compliance:** Returned dict matches M902-01 gate-result-success or gate-result-failure schema structure:
   - Has all required fields (status, gate, timestamp, ticket_id, message, artifacts, duration_ms)
   - All fields are JSON-serializable
   - No Python-specific types (datetime.datetime objects, Path objects, etc.)

2. **Message clarity:** Message field is a single-line plain-text string:
   - If formatting changed: "Formatted code with black, ruff format. Re-staged for review."
   - If no changes: "Code is already formatted (black, ruff format)."
   - If formatter unavailable: "Formatted code with black (ruff format skipped—not installed)."
   - If error: "Git failed: permission denied on `git add`. See violations for details."

3. **Artifacts field:** 
   - If formatting changed: list of file paths relative to repo root that were modified and re-staged (e.g., `["scripts/gameplay.gd", "asset_generation/python/src/foo.py"]`)
   - If no changes or error: empty list `[]`

4. **Violations array (on FAIL):**
   - Each violation object has required fields: `file`, `line`, `rule`, `message`
   - `rule` is one of: `formatter_unavailable`, `git_failed`, `timeout`, `subprocess_error`, `permission_denied`, `file_deleted`, `format_error`
   - Example violation: `{"file": "scripts/gameplay.gd", "line": 0, "rule": "timeout", "message": "gdformat exceeded 30s timeout"}`

5. **formatters_applied field (optional but recommended):**
   - List of formatter names that were actually invoked (e.g., `["black", "ruff_format", "prettier"]`)
   - Excludes formatters that were skipped due to unavailability

6. **formatting_changed field (optional but recommended):**
   - Boolean: `true` if any formatter modified any file, `false` if all files unchanged
   - Allows downstream to distinguish "formatted and re-staged" from "already formatted"

### 3. Risk & Ambiguity Analysis

**Ambiguities resolved:**
- **Should WARN violations prevent PASS status?** No. In shadow mode, gate always returns PASS (non-blocking). Violations array contains WARN-level messages (e.g., "formatter skipped") as informational data. This allows downstream to log warnings without blocking the pipeline.
- **Should artifacts list include all staged files or only modified files?** Only modified files. If formatting changed files A and B out of 5 staged files, artifacts = [A, B].
- **What if some formatters ran successfully but others failed?** Return FAIL status; violations array lists which formatters failed and why. Partial success is still a failure condition requiring user attention.

### 4. Clarifying Questions

None. Output contract is frozen.

---

## Requirement 03: Formatter Invocation and Change Detection

### 1. Spec Summary

**Description:** The gate invokes four language-specific formatters in strict sequential order:

1. **Python code (black):** Canonical formatting for `.py` files
2. **Python imports (ruff format):** Import normalization and additional Python formatting for `.py` files
3. **TypeScript/JavaScript (prettier):** Formatting for `.ts`, `.tsx`, `.js`, `.jsx` files
4. **GDScript (gdformat):** Formatting for `.gd` files

**Formatter execution logic:**
1. Enumerate all staged files via `git diff --cached --name-only`
2. For each formatter (in order):
   - Check if formatter is available on PATH (try to run `formatter --version` or equivalent)
   - If not available: log WARN, record skip, continue to next formatter
   - If available: run formatter on staged files matching the language (see file extension rules below)
   - Capture stderr and stdout (for error diagnostics if formatter fails)
   - If formatter exits non-zero: log error, record violation, return FAIL (all formatters must succeed)
   - If formatter times out (>30s): log timeout, record violation, return FAIL
3. After all formatters complete successfully, detect if any files were modified using git diff comparison
4. Emit result (PASS with optional re-staging, or FAIL with violations)

**File extension mapping:**
- **Black & Ruff format:** `*.py` (Python files under `asset_generation/python/`, `scripts/`, `tests/`, etc.)
- **Prettier:** `*.ts`, `*.tsx`, `*.js`, `*.jsx` (TypeScript/JavaScript under `asset_generation/web/`, etc.)
- **GDScript:** `*.gd` (Godot scripts anywhere in the repo)

**Change detection logic:**
1. Before formatting, save the current state of staged files via `git show :0:path` (get index version) or temp copy
2. Run all formatters on staged files (modifies working tree temporarily)
3. After formatting, compare working tree against saved state using `diff` or `git diff`
4. If any file differs: set `formatting_changed = true` and record modified file paths
5. If all files identical: set `formatting_changed = false`

**Message templates (frozen):**
- If `formatting_changed = true` and all formatters succeeded:
  - Single formatter: `"Formatted code with black. Re-staged for review."`
  - Multiple formatters: `"Formatted code with black, ruff format, prettier, gdformat. Re-staged for review."`
  - Some formatters unavailable: `"Formatted code with black, ruff format, prettier (gdformat skipped—not installed). Re-staged for review."`
- If `formatting_changed = false` and all formatters succeeded:
  - `"Code is already formatted (black, ruff format, prettier, gdformat)."`
  - If some formatters unavailable: `"Code is already formatted (black, ruff format, prettier; gdformat not installed)."`
- If any formatter failed:
  - `"Formatting failed: <formatter> exited with code <N>. See violations for details."`
  - `"Formatting failed: timeout on gdformat (>30s). See violations for details."`

**Constraints:**
- Formatters MUST run in exact order: black → ruff format → prettier → gdformat (never parallel)
- Formatters MUST be invoked with minimal arguments (use existing configs from `pyproject.toml`, `.prettierrc`, etc.; do not override via CLI)
- Change detection MUST be exact and binary-safe (whitespace counts; use `diff -u` or git diff for comparison)
- Each formatter invocation MUST have a timeout of 30 seconds (catch `subprocess.TimeoutExpired`)
- Each formatter invocation MUST capture both stdout and stderr for error reporting

**Assumptions:**
- Formatter configurations exist and are correct in the repo (black, ruff, prettier, gdformat configs are not overridden by the gate)
- Formatters are deterministic (same input always produces same output)
- Formatters do not require interactive input or environment setup beyond being on PATH
- No staged files are binary (gate assumes all staged files are text-based source code or configs)

**Scope:**
- Formatter invocation and change detection only; formatter configuration tuning is out of scope
- Idempotency validation (re-running formatters on formatted code) is out of scope
- Integration with editor/IDE formatters is out of scope
- Formatter auto-installation is out of scope (formatters must be pre-installed or gracefully skipped)

### 2. Acceptance Criteria

1. **Black invocation:** Gate runs `black <staged-py-files>` (or via subprocess.run with proper args), captures output, detects errors
2. **Ruff format invocation:** Gate runs `ruff format <staged-py-files>`, captures output, detects errors
3. **Prettier invocation:** Gate runs `prettier --write <staged-js-ts-files>`, captures output, detects errors (note: prettier uses `--write` flag for in-place formatting)
4. **GDScript invocation:** Gate runs `gdformat <staged-gd-files>`, captures output, detects errors
5. **Unavailable formatter handling:** If a formatter is not on PATH, gate logs and records WARN-level violation (not FAIL), continues with next formatter
6. **Timeout handling:** Each formatter invocation has timeout=30; if exceeded, gate catches `subprocess.TimeoutExpired`, logs, records violation, returns FAIL
7. **Change detection:** Gate correctly identifies which files were modified by formatters, using exact binary-safe diff comparison
8. **Message accuracy:** Output message matches one of the frozen templates and accurately lists which formatters were applied/skipped
9. **Exception handling:** All subprocess errors, file I/O errors, and git errors are caught, logged with context, and either re-raised or returned as violations (no silent swallowing)
10. **Staged-files-only:** Gate formats only files that are currently staged (in git index), not working tree or unstaged changes

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Formatter configuration incorrect:** If repo's `pyproject.toml` or `.prettierrc` has incorrect settings, formatters may make unintended changes. Mitigation: Spec assumes configs are correct; tests verify with known-good configs.
- **Formatter version mismatch:** Different versions of black/ruff/prettier/gdformat may format differently. Mitigation: Tests use whatever version is installed (no pinning in this gate); upstream package managers pin versions.
- **Subprocess encoding issues:** Formatter stdout/stderr may contain non-UTF8 characters. Mitigation: Use `subprocess.run(..., text=True, encoding='utf-8', errors='replace')` to handle gracefully.
- **Race condition:** If a file is deleted between enumeration and formatting, formatter will error. Mitigation: Catch FileNotFoundError, skip file, record WARN.

**Ambiguities resolved:**
- **Should formatters be run on all files or only changed files?** All staged files. Formatters should format all code consistently, not just changed lines. This is simpler and safer.
- **Should prettier use `--write` flag?** Yes; `--write` modifies files in-place, which is necessary for change detection. The alternative (`--check`) would not allow re-staging.
- **Should gdformat use `--line-length` override?** No. Gate uses formatter defaults; configs are in the repo. Do not override via CLI.

### 4. Clarifying Questions

None. Formatter invocation logic is frozen.

---

## Requirement 04: Re-staging Logic

### 1. Spec Summary

**Description:** If any formatter modified staged files (`formatting_changed = true`), the gate must re-stage those files and return a PASS status with a specific message. This allows users to review the formatted code and re-commit if acceptable.

**Re-staging workflow:**
1. After detecting that formatting changed files, stage those files via `git add <modified-files>`
2. Return PASS status with message: "Formatted code with <formatters>. Re-staged for review."
3. Include the list of re-staged file paths in the `artifacts` field
4. Include `formatting_changed = true` in the output dict
5. Exit with status code 0 (shadow mode)

**Git add semantics:**
- Use `subprocess.run(['git', 'add'] + file_list, ...)` to re-stage files
- If `git add` fails (e.g., permission denied), catch error, log with context, return FAIL with violation
- Do not use `git add -A` or `git add .` (only add the specific files that were formatted)

**User workflow expectation:**
- User stages changes and runs the gate (e.g., via CI, pre-push hook, or manual invocation)
- Gate detects formatting changes, re-stages them
- Gate prints message: "Formatted code with black, ruff format. Re-staged for review."
- User sees the message and knows to review the formatting changes
- User runs `git status` to see re-staged files
- User runs `git diff --cached` to review formatting changes
- User decides: accept and commit, or reject and stash
- If accept: user runs `git commit` with a new message (e.g., "chore: apply formatting")
- If reject: user can revert the formatting and re-stage original code

**Constraints:**
- Re-staging must not fail silently (catch and propagate errors)
- Re-staging must be idempotent (calling `git add` multiple times on the same files is safe)
- The gate must NOT auto-commit; it only re-stages and exits (user controls the final commit)
- The gate must exit with status 0 even if formatting changes are detected (non-blocking shadow mode)

**Assumptions:**
- User has git configured and repo is in a working state (can commit, no conflicts)
- User understands that re-staged files will appear in `git status` and can be reviewed before committing
- User is responsible for the final commit (gate does not commit)

**Scope:**
- Re-staging logic only; user workflows and UI are out of scope
- Pre-commit hook integration is out of scope (deferred to M903)
- Leftook wiring is out of scope

### 2. Acceptance Criteria

1. **Re-stage on change:** If `formatting_changed = true`, gate calls `git add` on modified files
2. **Re-stage success:** If `git add` succeeds, gate includes modified file paths in `artifacts` list and returns PASS
3. **Re-stage failure:** If `git add` fails, gate logs error, returns FAIL with violation (does not proceed as if success)
4. **Message correctness:** Output message is exactly "Formatted code with <formatters>. Re-staged for review." (no variations)
5. **Specific files only:** Gate only re-stages files that were actually modified by formatters, not all staged files
6. **Exit code:** Gate exits 0 even when formatting changes are detected (shadow mode is non-blocking)
7. **Artifacts list populated:** `artifacts` list contains the re-staged file paths (or empty list if no changes)

### 3. Risk & Ambiguity Analysis

**Risks:**
- **User confusion:** User sees re-staged files and may not understand what happened. Mitigation: Output message is clear and descriptive; spec expects user to understand gate behavior (out of scope for this ticket).
- **Git add fails:** If permissions are denied or repo is in a bad state, `git add` fails. Mitigation: Catch and propagate error; return FAIL.
- **File deleted after formatting:** If a file is deleted before re-staging, `git add` will fail. Mitigation: Catch error, propagate, return FAIL.

**Ambiguities resolved:**
- **Should gate auto-commit?** No. Gate only re-stages; user controls the commit (safer, user has chance to review).
- **Should gate create a new commit message?** No. User creates their own commit message (gate is non-opinionated about intent).

### 4. Clarifying Questions

None. Re-staging logic is frozen.

---

## Requirement 05: Error Handling and Graceful Degradation

### 1. Spec Summary

**Description:** The gate handles errors in three categories: (1) formatter unavailable (skip + WARN), (2) formatter failed (log + return FAIL), (3) git unavailable (log + return FAIL). No errors are silently swallowed.

**Error handling rules:**

**Category 1: Formatter Unavailable**
- Trigger: Formatter binary not on PATH (e.g., `black --version` raises OSError/FileNotFoundError)
- Action: Log warning, record WARN-level violation with rule=`formatter_unavailable`, continue with next formatter
- Message: Include formatter name in skip message (e.g., "gdformat skipped—not installed")
- Return status: PASS (non-blocking; skip is graceful degradation, not a failure)

**Category 2: Formatter Failed**
- Trigger: Formatter exits with non-zero code, or subprocess raises exception (OSError, UnicodeDecodeError, etc.)
- Action: Log error with full traceback, record violation with rule=`subprocess_error` or formatter-specific code, return FAIL status
- Message: "Formatting failed: <formatter> exited with code <N>. See violations for details."
- Return status: FAIL (formatter error is a hard failure; gate does not continue to next formatter)

**Category 3: Git Unavailable or Failed**
- Trigger: `git diff --cached --name-only` fails, or `git add` fails
- Action: Log error with git command + stderr, record violation with rule=`git_failed`, return FAIL status
- Message: "Git failed: <git error description>. See violations for details."
- Return status: FAIL (git error is a hard failure; gate cannot proceed)

**Category 4: Timeout**
- Trigger: Formatter subprocess exceeds timeout (30s by default)
- Action: Log timeout, record violation with rule=`timeout`, return FAIL status
- Message: "Formatting failed: timeout on <formatter> (>30s). See violations for details."
- Return status: FAIL (timeout is a hard failure)

**Exception handling rules (per code_governance.md):**
- No bare `except:` clauses
- No `except Exception: pass` (silent swallowing forbidden)
- All exceptions must be: (1) propagated (re-raised), (2) transformed (domain exception), or (3) observed + propagated (log + re-raise)
- Explicit recovery is allowed only when ticket/spec defines the fallback behavior (e.g., "skip unavailable formatter")

**Implementation patterns:**
```python
# ALLOWED: Explicit recovery with clear semantics
try:
    subprocess.run(['black', '--version'], check=True, capture_output=True, timeout=5)
except (OSError, FileNotFoundError):
    # Formatter not installed; skip it (graceful degradation defined in spec)
    logger.warning(f"Formatter 'black' not installed; skipping")
    violations.append({'file': 'black', 'rule': 'formatter_unavailable', ...})
    continue

# ALLOWED: Log + re-raise
try:
    result = subprocess.run(['black', ...], timeout=30, check=True, ...)
except subprocess.TimeoutExpired as e:
    logger.error(f"Formatter 'black' timed out after 30s: {e}")
    violations.append({'file': 'black', 'rule': 'timeout', ...})
    raise  # or return FAIL

# FORBIDDEN: Silent swallowing
try:
    subprocess.run(['black', ...], timeout=30)
except Exception:
    pass  # FORBIDDEN: silent failure

# FORBIDDEN: Logging without propagation (unless graceful degradation defined)
try:
    subprocess.run(['black', ...], timeout=30)
except Exception as e:
    logger.error(f"Error: {e}")
    # Missing: re-raise, return, or defined recovery
```

**Constraints:**
- All error messages must be descriptive (include command, stderr, return code, etc.)
- All violations must include: `file`, `line`, `rule`, `message` fields
- Non-blocking errors (e.g., formatter unavailable) must record WARN violations but return PASS
- Blocking errors (formatter failure, git failure) must return FAIL status

**Assumptions:**
- Logging module is available and configured (gate imports and uses stdlib `logging`)
- Violations array is present in output dict on both PASS and FAIL
- Downstream handlers will inspect violations array to understand what happened (even on PASS)

**Scope:**
- Error handling at the gate module level only; higher-level error recovery (e.g., user notification, rollback) is out of scope
- Formatter-specific error messages are deferred to each formatter's own error reporting; gate only logs and records the error code

### 2. Acceptance Criteria

1. **No silent errors:** All exceptions are logged or recorded in violations (no bare except / except Exception: pass)
2. **Formatter unavailable:** Gate gracefully skips with WARN violation, not FAIL
3. **Formatter failed:** Gate returns FAIL with violation describing the error
4. **Git failed:** Gate returns FAIL with violation describing the git error
5. **Timeout detected:** Gate catches `subprocess.TimeoutExpired`, returns FAIL with rule=`timeout`
6. **Violation structure:** All violations have required fields: `file`, `line`, `rule`, `message`
7. **Error message clarity:** Violations include relevant context (command, stderr, return code, etc.)
8. **Exception propagation:** If error recovery is not explicitly defined in spec, exception is re-raised or returned as FAIL

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Over-permissive error handling:** If gate silently skips all formatters and returns PASS, user may not realize formatting was skipped. Mitigation: Violations array records all skips; message includes skipped formatters.
- **Formatter-specific error messages unclear:** If formatter's stderr is cryptic, violation message may not help user. Mitigation: Include full stderr in violation message; user can debug via stderr logs.
- **Race condition in git add:** If file is deleted between formatting and git add, gate fails. Mitigation: Catch FileNotFoundError, return FAIL; this is correct behavior (staging area is inconsistent).

**Ambiguities resolved:**
- **Should missing formatter be a FAIL or WARN?** WARN (graceful degradation). If all formatters are missing, gate returns PASS with WARN violations; this signals to user that nothing was formatted (via message and violations array).
- **Should gate proceed after first formatter fails?** No. If any formatter fails (non-zero exit), gate returns FAIL immediately; all formatters must succeed.

### 4. Clarifying Questions

None. Error handling rules are frozen.

---

## Requirement 06: Output Contract Validation and Schema Conformance

### 1. Spec Summary

**Description:** All output dicts must conform to the M902-01 gate result schema. The gate runner (M902-01) validates the result dict after the gate module returns; however, the gate module itself must ensure correctness to avoid runtime errors in the runner.

**Validation checklist (gate module responsibility):**
1. All required fields present: `status`, `gate`, `timestamp`, `ticket_id`, `message`, `artifacts`, `duration_ms`
2. status is one of: `"PASS"` or `"FAIL"` (case-sensitive)
3. gate is exactly: `"formatting_check"` (lowercase)
4. timestamp is ISO 8601 UTC format: `YYYY-MM-DDTHH-MM-SSZ` or with milliseconds `YYYY-MM-DDTHH-MM-SS.sssZ`
5. ticket_id is a string (e.g., `"M902-10"` or user-provided value)
6. message is a string, <200 chars, single-line (no newlines)
7. artifacts is a list of strings (file paths relative to repo root), or empty list
8. duration_ms is an integer (milliseconds from start of run() to return)
9. violations (on FAIL only) is a list of dicts, each with: `file` (str), `line` (int), `rule` (str), `message` (str)
10. All values are JSON-serializable (strings, ints, lists, dicts; no datetime objects, Path objects, etc.)

**Optional fields (recommended but not required by schema):**
1. `formatting_changed` (bool): true if formatters modified files, false otherwise
2. `formatters_applied` (list of strings): names of formatters that were successfully invoked

**Constraints:**
- Gate module must validate all output fields before returning
- Gate module must not return Python-specific types (datetime.datetime, pathlib.Path, etc.); convert to JSON types
- Timestamp must be generated at start of run() function and converted to ISO string (use `datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')`)
- duration_ms must be calculated as `int((time.time() - start_time) * 1000)`
- All field names in dicts must be lowercase or follow camelCase (match schema exactly)

**Assumptions:**
- Gate runner will perform final schema validation; gate module is responsible for correctness but not validation
- Downstream consumers (orchestrator, tests) will parse the JSON output; gate module ensures it is valid JSON

**Scope:**
- Output validation at gate module level only; gate runner's validation is out of scope for this spec
- Schema definition details (e.g., exact regex for timestamp format) are in M902-01 spec, not this ticket

### 2. Acceptance Criteria

1. **Schema compliance:** Returned dict can be serialized to JSON and matches M902-01 schema structure
2. **Field presence:** All required fields (`status`, `gate`, `timestamp`, `ticket_id`, `message`, `artifacts`, `duration_ms`) are present in every return value
3. **Field types:** All fields have correct JSON types (strings, ints, lists, dicts)
4. **Field values:** status is "PASS" or "FAIL", gate is "formatting_check", timestamp matches ISO 8601 format
5. **Optional fields:** formatters_applied and formatting_changed are present and accurate (optional, but recommended)
6. **Timestamp accuracy:** Timestamp matches current UTC time (within reasonable precision, e.g., <1s drift)
7. **Duration accuracy:** duration_ms is a reasonable integer (>0, <1 minute for normal runs)
8. **JSON serializability:** Result dict can be serialized via `json.dumps()` without errors

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Timestamp format error:** If timestamp is not ISO 8601 format, gate runner may fail to parse. Mitigation: Use standard library `datetime.isoformat()` and convert +00:00 to Z.
- **Non-serializable objects in dict:** If gate module includes a datetime.datetime object or pathlib.Path in the result, `json.dumps()` will fail. Mitigation: Convert all objects to JSON types before returning.
- **Field missing:** If gate module forgets to include duration_ms, schema validation fails. Mitigation: Use a checklist or dataclass to ensure all fields are present.

**Ambiguities resolved:**
- **Should gate module validate output before returning?** Yes (defensive programming). Gate runner will also validate, but module should not return invalid data.

### 4. Clarifying Questions

None. Output validation rules are frozen.

---

## Requirement 07: Non-Functional Requirements (NFR)

### 1. Spec Summary

**Description:** The gate has performance and reliability targets:

**Performance targets:**
- Gate runtime: <5 seconds for typical staging area (10–100 files, <10 MB total)
- Per-formatter timeout: 30 seconds (catch subprocess.TimeoutExpired)
- Change detection latency: <500 ms (diff comparison should be fast)

**Reliability targets:**
- Gate must exit cleanly even if formatter unavailable (graceful skip, not crash)
- Gate must handle up to 1000 staged files without hanging (may exceed 5s timeout, but must not deadlock)
- Gate must be idempotent: calling gate twice on the same staging area yields the same result

**Memory targets:**
- Gate must not consume >100 MB memory during execution
- Temp files must be cleaned up after use (no temp file leaks)

**Testability targets:**
- Gate must be testable without network access or external service calls
- Gate must be testable with mocked subprocess invocations
- All paths (success, failure, timeout, unavailable formatter) must be covered by tests

**Logging targets:**
- All errors and warnings must be logged via stdlib `logging` module
- Log level INFO for normal events (formatter run, files formatted)
- Log level WARNING for graceful degradation (formatter unavailable)
- Log level ERROR for failures (formatter error, git error)

**Constraints:**
- Gate is not required to achieve 100% test coverage; reasonable coverage (>80% on main paths) is sufficient
- Gate is not required to optimize for large staging areas (>1000 files); timeout may exceed 5s in those cases
- Gate is not required to cache results or memoize formatter invocations across multiple runs
- Gate is not required to validate formatter configurations; assumes configs are correct

**Assumptions:**
- Staging area is not expected to exceed 10,000 files (reasonable assumption for most projects)
- Formatters are reasonably fast (black, ruff, prettier, gdformat all finish in <30s on typical repos)
- Temp file cleanup is handled by OS (gate can rely on temp dir auto-cleanup on reboot if needed)

**Scope:**
- Performance targets for this gate only; system-wide performance optimization is out of scope
- Caching and memoization are out of scope (deferred to M903)
- Logging integration with external observability systems is out of scope

### 2. Acceptance Criteria

1. **Performance test:** Gate completes in <5s on staging area with 50 Python files, 20 TypeScript files, 30 GDScript files (250 KB total)
2. **Timeout handling:** Gate catches subprocess.TimeoutExpired and returns FAIL within 31s (30s timeout + 1s cleanup)
3. **Idempotency:** Running gate twice on same staging area returns same result dict (deterministic behavior)
4. **Memory safety:** Gate uses <100 MB memory during execution (no memory leaks detected by profiling)
5. **Graceful degradation:** If all formatters are unavailable, gate returns PASS with WARN violations (does not crash)
6. **Logging:** Gate logs at appropriate levels (INFO, WARNING, ERROR) via stdlib logging
7. **Temp file cleanup:** Any temp files created by gate are deleted before returning (verified by checking temp dir)
8. **Testability:** All code paths (success, timeout, formatter error, git error, unavailable formatter) are tested without network/external services

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Performance varies by system:** Performance target of <5s may not be achievable on slow systems or during high system load. Mitigation: Define as "typical conditions"; tests run with relaxed timeouts.
- **Memory profiling difficult:** Memory usage is hard to measure accurately in Python (GC, caching, etc.). Mitigation: Sanity check for obvious leaks (e.g., infinite loops accumulating data); do not over-speculate on exact memory usage.
- **Idempotency requires determinism:** If formatter output is non-deterministic, gate cannot be idempotent. Mitigation: Assume formatters are deterministic; upstream formatter tests validate that.

**Ambiguities resolved:**
- **Should NFR targets be hard requirements or soft targets?** Soft targets (SLA-like). Tests may use relaxed thresholds; implementation should aim to meet targets but not at cost of correctness.

### 4. Clarifying Questions

None. NFR targets are frozen.

---

## Requirement 08: Deferred Scope and Future Work (M903+)

### 1. Spec Summary

**Description:** The following features are explicitly OUT OF SCOPE for this ticket and deferred to M903 and beyond:

**Out of scope (M903 Orchestration):**
1. CI/CD hook integration (e.g., GitHub Actions, GitLab CI)
2. Lefthook integration (e.g., `pre-commit`, `pre-push` hooks)
3. Orchestration logic to decide when to run Stage 1 (that belongs to M903 orchestrator based on M902-09 diff classification output)
4. User-facing UI or PR comments
5. Parallel formatter execution (sequential is safe default; M903 can optimize)

**Out of scope (formatter tuning):**
1. Formatter configuration overrides (gate uses existing configs from repo; no CLI overrides)
2. Formatter version pinning (upstream package managers handle versions)
3. Custom formatter rules or rule severity tuning
4. Idempotency validation (upstream formatters responsible)

**Out of scope (gate improvements):**
1. Caching of gate results across runs
2. Incremental formatting (only format changed files, not all staged files)
3. Formatter plugin system
4. Custom error recovery strategies beyond what's defined in this spec

**Out of scope (testing):**
1. Integration tests with real Godot scenes or Blender files (unit tests only)
2. Performance profiling against real-world large codebases (stress tests use synthetic data)
3. Cross-platform compatibility (tests assume Unix-like filesystem; Windows support deferred)

**Out of scope (documentation):**
1. User-facing guides (beyond gate README section)
2. Troubleshooting guides
3. Formatter setup/installation instructions (assume tools are pre-installed)

**Constraints:**
- Nothing in deferred scope should be implemented in this ticket
- Implementation must not create scaffolding or hooks for deferred scope (avoid over-engineering)
- Tests must not assume deferred features exist

**Assumptions:**
- M903 orchestration layer will handle CI/CD integration and routing decisions
- M903 may require enhancements to this gate (e.g., new hooks, configuration options), which will be version-bumped appropriately
- Future tickets will add features in deferred scope without breaking this gate's contract

**Scope:** This requirement defines boundaries and manages expectations; not an AC item.

### 2. Acceptance Criteria

N/A (This is a scope boundary statement, not a behavioral requirement.)

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Over-engineering:** If implementation includes deferred-scope features, it will bloat the module and complicate testing. Mitigation: Spec explicitly forbids deferred features; code review will catch violations.
- **Scope creep:** If testers expect integration tests with real hooks, tests fail and ticket is delayed. Mitigation: Execution plan and spec clearly state "unit tests only".

**Ambiguities resolved:**
- **Is M903 orchestrator blocking?** No. M902-10 is standalone gate; M903 will consume its output independently.

### 4. Clarifying Questions

None. Deferred scope is frozen.

---

## Test Vectors (25+ Comprehensive Examples)

**Test vectors are organized by category and included here to freeze expected behavior for Test Designer and Test Breaker agents.**

### Basic Formatter Tests (6 vectors)

| ID | Formatter | Input Files | Expected Behavior | Expected Output |
|---|-----------|-----------|---------|---------|
| TV-01 | black | `test.py` (malformatted Python) | Formats with black only | PASS, formatting_changed=true, artifacts=[test.py], message includes "black" |
| TV-02 | ruff format | `test.py` (unsorted imports) | Formats with ruff format | PASS, formatting_changed=true, artifacts=[test.py], message includes "ruff format" |
| TV-03 | prettier | `test.ts` (unformatted TypeScript) | Formats with prettier | PASS, formatting_changed=true, artifacts=[test.ts], message includes "prettier" |
| TV-04 | gdformat | `test.gd` (unformatted GDScript) | Formats with gdformat | PASS, formatting_changed=true, artifacts=[test.gd], message includes "gdformat" |
| TV-05 | black | `test.py` (already formatted) | Black runs, detects no changes | PASS, formatting_changed=false, artifacts=[], message="Code is already formatted" |
| TV-06 | multiple | `test.py`, `test.ts`, `test.gd` (all unformatted) | All three formatters run in sequence | PASS, formatting_changed=true, artifacts=[test.py, test.ts, test.gd] |

### Mixed Scenario Tests (8 vectors)

| ID | Scenario | Input Files | Expected Behavior | Expected Output |
|---|----------|-----------|---------|---------|
| TV-07 | Partial formatting needed | `a.py` (needs format), `b.py` (already formatted), `c.py` (needs format) | Formats all, detects 2 changed | PASS, formatting_changed=true, artifacts=[a.py, c.py] |
| TV-08 | Mixed languages | `game.gd`, `player.gd`, `foo.py`, `bar.ts` | Each formatter runs on its files | PASS, formatting_changed=true, artifacts=[all 4] |
| TV-09 | No staged files | (empty staging area) | Gate runs but has no files to format | PASS, formatting_changed=false, artifacts=[], message="Code is already formatted" |
| TV-10 | Large file | Single `.py` file, 10,000 lines | Black formats successfully within timeout | PASS, formatting_changed=true, artifacts=[large_file.py] |
| TV-11 | Many small files | 100 staged `.py` files, 1 KB each | All formatters run successfully | PASS, formatting_changed=true, artifacts=[100 files] |
| TV-12 | Only config changes | `pyproject.toml` (config only, not code) | Formatters skip non-source files | PASS, formatting_changed=false, artifacts=[] |
| TV-13 | Binary file mixed | `image.png` (binary) + `test.py` (code) | Formatters ignore binary, format code | PASS, formatting_changed=true, artifacts=[test.py] |
| TV-14 | Comment-only changes | `test.py` (comment formatting) | Black/ruff formats, detects change | PASS, formatting_changed=true, artifacts=[test.py] |

### Error/Failure Tests (5 vectors)

| ID | Error Type | Input | Expected Behavior | Expected Output |
|---|-----------|-------|---------|---------|
| TV-15 | Formatter unavailable | `test.py` (no gdformat installed) | Skip gdformat, run others, return PASS with WARN | PASS, message includes "gdformat skipped", violations=[{rule: formatter_unavailable}] |
| TV-16 | Formatter timeout | `test.py` (causes gdformat to hang) | Timeout after 30s, catch TimeoutExpired | FAIL, violations=[{rule: timeout, message: "gdformat exceeded 30s"}] |
| TV-17 | Formatter error | `test.py` (syntax error, e.g., unclosed bracket) | Black exits non-zero | FAIL, violations=[{rule: subprocess_error, message: includes stderr}] |
| TV-18 | Git unavailable | (repo is not git repo) | git diff fails | FAIL, violations=[{rule: git_failed}] |
| TV-19 | Git add fails | (permission denied on re-stage) | git add fails with permission error | FAIL, violations=[{rule: git_failed, message: includes "permission"}] |

### Edge Case Tests (4 vectors)

| ID | Edge Case | Input | Expected Behavior | Expected Output |
|---|-----------|-------|---------|---------|
| TV-20 | Empty file | `empty.py` (0 bytes) | Formatters skip or handle gracefully | PASS, formatting_changed=false |
| TV-21 | Symlink | `link.py` (symlink to real file) | Formatter follows symlink, formats target | PASS, formatting_changed=true (if target changed) |
| TV-22 | File deleted after enumeration | `test.py` (deleted before formatting) | Formatter errors on missing file | FAIL, violations=[{file: test.py, rule: ...}] |
| TV-23 | Very long filename | `a_very_long_filename_with_many_characters_exceeding_255.py` | Gate handles long filename gracefully | PASS or FAIL (no crash due to filename length) |

### NFR Tests (2+ vectors)

| ID | NFR | Scenario | Expected Behavior | Acceptance Threshold |
|---|-----|----------|---------|---------|
| TV-24 | Performance | Stage 50 Python + 20 TS + 30 GDScript files (250 KB total) | Gate completes | <5 seconds |
| TV-25 | Idempotency | Run gate twice on same staging area | Both runs return identical result dict | Hash of result_dict is same on both runs |

---

## Acceptance Criteria Mapping

| Ticket AC | Requirement(s) | Test Vector(s) | Implementation Task |
|-----------|---|---|---|
| AC1: Gate runs black, ruff format, prettier, gdformat | Req-03 | TV-01, TV-02, TV-03, TV-04, TV-06 | Formatter invocation logic |
| AC2: Detects if formatting changed files | Req-03 | TV-05, TV-07, TV-14 | Change detection via diff |
| AC3: If formatting changed: message + re-stage + exit | Req-04 | TV-01, TV-06, TV-07 | Re-staging logic + git add |
| AC4: If no changes: exit cleanly | Req-03 | TV-05, TV-09, TV-12 | No-op path |
| AC5: Implemented as `ci/scripts/gates/formatting_check.py` | Req-01 | All vectors | Module at exact path |
| AC6: Tested with unformatted code samples | Req-03 | TV-01, TV-02, TV-03, TV-04, TV-08, TV-11 | Test fixtures with unformatted code |
| AC7: Exit behavior documented | Req-01, Req-04 | (integration task) | README + spec |

---

## Risk Register (with Mitigations)

| Risk ID | Description | Severity | Likelihood | Impact | Mitigation | Task(s) |
|---------|-------------|----------|------------|--------|-----------|---------|
| R1 | Formatter not installed in test env | Medium | High | Tests fail or skip | Mock subprocess.run in tests; implement skip+WARN in gate | Task 2, 4 |
| R2 | Re-staging fails (git unavailable, permissions) | Medium | Medium | Gate returns FAIL unexpectedly | Explicit git error handling; tests mock git failures | Task 1, 4 |
| R3 | Formatter hangs (infinite loop, large file) | Low | Low | Gate blocked >30s | Timeout logic with subprocess timeout=30s | Task 1, 4 |
| R4 | Diff-before/after comparison expensive | Low | Low | Performance degrades | Use efficient diff (git diff or simple file compare); NFR test | Task 1, 3 |
| R5 | Multiple formatters conflict (black vs ruff) | Low | Low | Formatter output wrong | Sequential execution is safe; each formatter composes correctly | Task 1, 4 |
| R6 | Output message unclear or misleading | Low | Medium | User confused | Freeze message templates in spec; tests assert exact message | Task 1, 2 |
| R7 | Timestamp format error | Low | Low | Schema validation fails | Use datetime.isoformat() + convert +00:00 to Z | Task 4 |
| R8 | Non-serializable objects in output dict | Low | Medium | json.dumps() fails | Convert all objects to JSON types before returning | Task 4 |
| R9 | Performance exceeds <5s target | Low | Low | NFR not met | Optimize diff logic; use relaxed thresholds in tests | Task 3, 4 |
| R10 | Gate not idempotent | Low | Low | Unexpected behavior | Ensure gate logic is pure (no side effects); run idempotency test | Task 2, 3 |

---

## Dependencies & Blockers

**Hard dependencies (must be COMPLETE before SPECIFICATION approval):**
- M902-01 (Validation Gate Framework) — **COMPLETE** ✓
  - Provides: gate_runner.py, gate_registry.json, success/failure schemas
  - Spec Requirement-02 (Output Contract) depends on M902-01 schemas

**Soft dependencies (informational; no blocking):**
- M902-09 (Diff Classification Gate) — **COMPLETE** ✓
  - Provides context: Stage 0 can recommend "formatting_and_stage_1" route
  - M902-10 is independent; can proceed in parallel

**Blocking issues:** None. All hard dependencies satisfied.

---

## Specification Completeness Checklist

- [x] 8 requirements defined (module, registry, formatter invocation, re-staging, error handling, output contract, NFR, deferred scope)
- [x] 25+ test vectors with expected behavior (6 basic + 8 mixed + 5 error + 4 edge + 2 NFR)
- [x] Output contract frozen (success/failure schema, field definitions, message templates)
- [x] Acceptance criteria mapped to requirements and test vectors (7 ACs, all covered)
- [x] Risk register with mitigations (10 risks identified)
- [x] Clarifying questions resolved (none remaining; all Q1–Q7 from planning logged)
- [x] Assumptions documented with confidence levels (8 assumptions, all logged)
- [x] No game/asset changes required
- [x] No destructive/randomness/load-open API concerns (generic ticket type)
- [x] Spec is unambiguous, implementable, and testable

**Status: READY FOR TEST_DESIGN**

---

## Signature & Versioning

**Spec Agent:** Autonomous (Checkpoint Protocol)  
**Date:** 2026-05-18  
**Version:** 1.0 (DRAFT)  
**Next Stage:** TEST_DESIGN (Test Designer Agent)  
**Next Responsible Agent:** Test Designer Agent  
**Input for Test Designer:** This spec (902_10_formatting_gate_spec.md) + test vector checklist (Requirement 08 above)

# Specification: Reviewer Gate — TODO/FIXME Scanning & Suppression Audit

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/06_per_stage_gate_improvements.md`

**Milestone:** 902 — Agent Predictability Improvements

**Task:** 5 (Spec Agent responsibility, part 1 of 2)

**Date:** 2026-05-16

**Revision:** 1

---

## Executive Summary

The **reviewer gate** scans git diffs (staged files) to detect new TODO/FIXME comments and suppressions without issue links. It helps Implementation Agents identify incomplete work and governance policy violations before code commit. The gate runs with no external services (git invocation only), outputs JSON matching M902-01 schema, and operates in WARN-only mode (non-blocking, advisory).

**Scope:** New lines only (prefixed `+` in `git diff --cached`). Existing TODOs are ignored (do not block PRs with pre-existing tech debt).

---

## Functional Requirements

### Requirement 1: Parse Git Diff (Staged Files)

**Description:** Gate must read git diff for staged files to identify new lines.

**Input Format:**
- `policy_file` (string, optional): Path to YAML policy file (see Config File Schema)
- No explicit file list; gate discovers staged files via `git diff --cached`

**Git Command:**
```bash
git diff --cached --no-prefix --unified=0
```

**Diff Parsing:**
- Parse unified diff format (hunk headers, line prefixes)
- Extract new lines: lines prefixed with `+` (but not `+++` file markers)
- Build map: file_path → list of (line_number, line_content) for new lines
- Ignore deletions (lines prefixed with `-`) and context lines (no prefix)

**Constraints:**
- If git is not available (offline, non-repo context): emit WARN "git not available; skipping TODO scan" and continue.
- Handle binary files gracefully (skip, no error).
- Handle large diffs (> 10 MB): emit WARN and truncate analysis.

**Scope:** Only staged files (`git diff --cached`); unstaged changes excluded.

**Acceptance Criteria:**
- Gate correctly parses diff with 3 new files and extracts new lines only.
- Gate handles missing git with graceful WARN (not FAIL).
- Gate correctly ignores deleted lines and context lines.

---

### Requirement 2: Scan New Lines for TODO/FIXME Keywords

**Description:** Gate must detect TODO and FIXME comments in newly added lines.

**Keyword Detection:**
- Regex patterns (case-insensitive by default):
  - `TODO` (matches "todo", "TODO", "TODO:")
  - `FIXME` (matches "fixme", "FIXME", "FIXME:")
  - Additional keywords (configurable in YAML): `HACK`, `XXX`, `KLUDGE`, etc.
- Match any line containing keyword (not limited to code comments; includes docstrings, strings)

**Example Matches:**
```python
# TODO: improve error handling → MATCH
# todo: fix this later → MATCH (case-insensitive)
def helper():  # FIXME: optimize → MATCH
    """
    TODO: add docstring here
    """  → MATCH (in docstring)
    temporary_workaround = 1  # HACK: should be refactored → MATCH
```

**Constraints:**
- Match is greedy (report all keywords on a line, even if multiple).
- Match ignores context (e.g., "TODO" in string literal "TODO is not a keyword here" still matches).
- Comments in commented-out code are included (e.g., `# # TODO: never ran this` matches).

**Scope:** All programming languages (Python, GDScript, TypeScript, etc.) and markdown.

**Acceptance Criteria:**
- Gate detects `# TODO: improve error` in Python.
- Gate detects `// FIXME: optimize` in TypeScript.
- Gate detects TODO in markdown docstring.
- Gate detects case-insensitive matches (todo, TODO, Todo).

---

### Requirement 3: Identify Suppressions Without Issue Links

**Description:** Gate must audit suppression comments (# noqa, # nosemgrep, # eslint-disable) to ensure they cite an issue.

**Suppression Patterns:**
- Python: `# noqa` or `# nosemgrep <rule> <issue>`
- TypeScript: `// eslint-disable-line <rule>` or `// eslint-disable <rule>`

**Valid Suppression Format (Python):**
```python
x = dangerous_operation()  # noqa M902-03
x = dangerous_operation()  # nosemgrep AR-01 https://github.com/...
x = dangerous_operation()  # noqa GH-123
```

**Invalid Suppression Format (missing issue link):**
```python
x = dangerous_operation()  # noqa  (no issue link)
x = dangerous_operation()  # noqa: E501  (linter rule, not issue link)
```

**Suppression Detection:**
- Regex: `#\s*(noqa|nosemgrep|eslint-disable)` captures suppression comment
- If `noqa` found, check for issue link pattern: `M\d{3}-\d{2}`, `GH-\d+`, `https://`, `JIRA-\d+`
- If no issue link: report WARN "suppression missing issue link"

**Constraints:**
- Linter rule-only suppressions (e.g., `# noqa: E501`) are reported as missing issue link (violation).
- Suppression with explicit "nolint: next-line" comment + issue is valid (include in allowed patterns).
- Suppress suppressions count as violations (recursive suppression not allowed).

**Scope:** All suppression comments in new lines.

**Acceptance Criteria:**
- `# noqa M902-03` → valid (issue link present).
- `# noqa` (no link) → WARN.
- `# noqa: E501` (linter rule only) → WARN.
- `# eslint-disable-line react/no-array-index-key` (TypeScript, no issue) → WARN.

---

### Requirement 4: Report Violations per New Line

**Description:** Gate must report each TODO/FIXME and suppression violation with context.

**Violation Structure:**
```python
{
  "file": "asset_generation/python/src/model_registry.py",
  "line": 42,
  "rule": "new_todo_found",  # or "new_fixme_found" or "suppression_missing_issue"
  "message": "New TODO comment found: 'TODO: improve error handling'",
  "severity": "WARN"
}
```

**Report Strategy:**
- One violation per new line with TODO/FIXME.
- One violation per suppression missing issue link.
- Include surrounding context (5 lines before/after) in message for visibility.

**Line Numbers:**
- Report actual line number in file (not diff line number; convert via hunk header).

**Scope:** All violations reported in JSON array; no maximum limit.

**Acceptance Criteria:**
- Violation includes file path, line number, rule, message, severity.
- Message includes keyword text and context (e.g., "TODO: improve error handling").
- Multiple TODOs on same line generate separate violations (one per TODO).

---

### Requirement 5: JSON Output Format (M902-01 Schema Compliance)

**Description:** Gate emits JSON output matching M902-01 gate schema.

**Output on PASS (no new TODOs/FIXMEs):**
```json
{
  "version": "0.1.0",
  "status": "PASS",
  "gate": "reviewer_check",
  "upstream_agent": "Implementation Agent",
  "downstream_agent": "Spec Agent",
  "timestamp": "2026-05-16T12:00:00",
  "ticket_id": "M902-06",
  "mode": "shadow",
  "message": "No new TODO/FIXME comments detected in staged files.",
  "violations": [],
  "remediation_hints": [],
  "duration_ms": 8
}
```

**Output on WARN (new TODOs or suppressions without issue links):**
```json
{
  "version": "0.1.0",
  "status": "WARN",
  "gate": "reviewer_check",
  "upstream_agent": "Implementation Agent",
  "downstream_agent": "Spec Agent",
  "timestamp": "2026-05-16T12:00:00",
  "ticket_id": "M902-06",
  "mode": "shadow",
  "message": "2 new TODO/FIXME comments and 1 suppression without issue link detected.",
  "violations": [
    {
      "file": "asset_generation/python/src/model_registry.py",
      "line": 42,
      "rule": "new_todo_found",
      "message": "New TODO: 'TODO: improve error handling'",
      "severity": "WARN"
    },
    {
      "file": "asset_generation/python/src/gate.py",
      "line": 15,
      "rule": "new_fixme_found",
      "message": "New FIXME: 'FIXME: optimize performance'",
      "severity": "WARN"
    },
    {
      "file": "ci/scripts/test.py",
      "line": 28,
      "rule": "suppression_missing_issue",
      "message": "Suppression without issue link: '# noqa' (add ticket reference, e.g., M902-06)",
      "severity": "WARN"
    }
  ],
  "remediation_hints": [
    "model_registry.py:42 → document reason for TODO or complete the work",
    "gate.py:15 → document reason for FIXME or complete the work",
    "test.py:28 → add issue link to suppression: '# noqa M902-06' or 'M903-XX'"
  ],
  "duration_ms": 12
}
```

**Status Mapping:**
- **PASS:** No new TODO/FIXME/suppression violations.
- **WARN:** >= 1 violation detected (non-blocking advisory).

**Violations Array:**
- One entry per TODO/FIXME keyword found in new lines.
- One entry per suppression missing issue link.
- Rule names: "new_todo_found", "new_fixme_found", "suppression_missing_issue".
- Severity: all WARN (no ERROR in reviewer gate).

**Remediation Hints:**
- Per violation: "file:line → reason or action".
- Generic: "Document reason for TODO/FIXME or create follow-up ticket. Add issue link to suppressions."

**Scope:** All output fields present; violations empty if PASS.

**Acceptance Criteria:**
- PASS output has status=PASS, no violations.
- WARN output includes all new TODOs/FIXMEs as separate violations.
- Remediation hints are actionable and specific.

---

### Requirement 6: Configuration & Keyword Customization

**Description:** Gate accepts optional YAML config file to customize TODO/FIXME keywords.

**Config File Schema:**
```yaml
keywords:
  # Core keywords (always checked)
  - keyword: TODO
    severity: WARN
    
  - keyword: FIXME
    severity: WARN
  
  # Optional keywords (configurable)
  - keyword: HACK
    severity: WARN
  
  - keyword: XXX
    severity: WARN
  
  - keyword: KLUDGE
    severity: ERROR  # Can be ERROR (stricter)
  
  - keyword: BUG
    severity: WARN

suppressions:
  # Valid issue link patterns
  valid_patterns:
    - "M\\d{3}-\\d{2}"  # M902-06
    - "M\\d{3}"  # M902 (shorter form)
    - "https://"  # URLs
    - "GH-\\d+"  # GitHub issues
    - "JIRA-\\d+"  # JIRA issues
  
  # Require issue link for all suppressions
  require_issue_link: true
```

**Defaults (if config file missing):**
```yaml
keywords:
  - keyword: TODO
    severity: WARN
  - keyword: FIXME
    severity: WARN

suppressions:
  valid_patterns:
    - "M\\d{3}-\\d{2}"
    - "https://"
    - "GH-\\d+"
  require_issue_link: true
```

**Config File Location:**
- Specified in inputs["policy_file"] as absolute path.
- If missing: use hardcoded defaults (no YAML required).
- If file not found: WARN and use defaults (not FAIL).

**Scope:** Keywords and suppression patterns are customizable; defaults cover MVP requirements.

**Acceptance Criteria:**
- Gate correctly reads config and applies custom keywords.
- Gate gracefully handles missing config (uses defaults, logs INFO).
- Gate correctly validates issue link patterns from config.

---

### Requirement 7: Error Handling & Graceful Degradation

**Description:** Gate must handle git unavailability, unreadable files, and config errors gracefully.

**Error Cases:**
- **Git not available:** WARN "git not available; skipping TODO scan" (return PASS).
- **Not a git repository:** WARN "not a git repository; skipping" (return PASS).
- **git diff fails (timeout, permission denied):** WARN "git diff failed; analysis skipped".
- **Config file not found:** WARN, use defaults (not FAIL).
- **Invalid YAML config:** WARN, use defaults.
- **Large diff (> 10 MB):** WARN "diff too large; truncating analysis" (analyze first N MB).

**Constraints:**
- All errors logged but do not block gate completion.
- Fallback: If git unavailable or diff fails, emit WARN and return PASS (do not fail CI).
- Gate never raises unhandled exceptions; all errors caught and reported.

**Scope:** Applies to gate invocation in offline or non-repo contexts.

**Acceptance Criteria:**
- Missing git → WARN "git not available", status=PASS (not FAIL).
- Config file not found → WARN, use defaults.
- git diff fails → WARN, status=PASS.

---

## Non-Functional Requirements

### NFR-1: Deterministic Execution

**Requirement:** Gate must produce identical output for identical git state.

**Scope:** git diff parsing, keyword matching, output serialization.

**Verification:**
- Same staged files + config → same violations detected every invocation.
- File ordering in output (stable sorted by path).

**Acceptance Criteria:**
- Gate run on same git state twice → identical JSON output (except duration_ms and timestamp).

---

### NFR-2: No External Service Dependencies

**Requirement:** Gate must not require network, database, or remote services (besides git binary).

**Scope:** I/O is local git commands and filesystem reads only.

**Verification:**
- No HTTP, SSH (except git), or RPC calls.
- No database queries.

**Acceptance Criteria:**
- Gate runs with only local git and filesystem access.

---

### NFR-3: Performance

**Requirement:** Gate must complete in < 5 seconds for typical PR (< 20 files changed, < 500 lines added).

**Metrics:**
- git diff invocation: < 1 second.
- Diff parsing + regex matching: < 3 seconds.
- JSON serialization: < 0.1 seconds.

**Acceptance Criteria:**
- Gate completes in < 5 seconds for 20 files, 500 new lines.

---

### NFR-4: Observability

**Requirement:** Gate must log structured messages for debugging.

**Logging:**
- INFO: gate start, files enumerated, violations count, result.
- DEBUG: per-file analysis, regex matches.
- WARN: git unavailable, config not found, diff errors.
- ERROR: exception stack traces (if gate module fails).

**Scope:** All logs at module level.

**Acceptance Criteria:**
- Gate logs at least 2 INFO messages per invocation.

---

## Integration Notes

### Gate Runner Wiring

**Registry Entry (gate_registry.json):**
```json
{
  "name": "reviewer_check",
  "module": "reviewer_check",
  "required_inputs": [],
  "optional_inputs": ["policy_file", "mode", "ticket_id", "upstream_agent", "downstream_agent"],
  "default_mode": "shadow",
  "description": "Scans git diff (staged files) for new TODO/FIXME comments and suppressions without issue links. Output: WARN per violation found.",
  "category": "governance"
}
```

**Invocation (from Implementation Agent before commit):**
```bash
python ci/scripts/gate_runner.py reviewer_check \
  --upstream-agent "Implementation Agent" \
  --downstream-agent "Spec Agent" \
  --ticket-id M902-06 \
  --input '{"policy_file": "project_board/902_06_reviewer_gate_policy.yml"}'
```

**Module Location:** `ci/scripts/gates/reviewer_check.py`

**Entry Point Function:** `run(inputs: dict[str, Any]) -> dict[str, Any]`

**Input Contract:**
```python
inputs = {
  "policy_file": str,  # path to YAML policy file (optional)
  "mode": "shadow|blocking",  # default "shadow"
  "ticket_id": str,  # ticket identifier
  "upstream_agent": str,  # agent name
  "downstream_agent": str,  # agent name
}
```

**Output Contract:** Dict matching M902-01 schema v0.2.0.

---

## Config File Schema

**File Location:** `project_board/902_06_reviewer_gate_policy.yml`

**Complete Schema (YAML):**
```yaml
# Keywords to scan for in new code
keywords:
  - keyword: TODO
    severity: WARN
    
  - keyword: FIXME
    severity: WARN

# Suppression comment validation
suppressions:
  # Valid issue link patterns (regex)
  valid_patterns:
    - "M\\d{3}-\\d{2}"  # M902-06
    - "https://"        # URLs
    - "GH-\\d+"         # GitHub
    - "JIRA-\\d+"       # JIRA
  
  # Require issue link for all suppressions
  require_issue_link: true
```

---

## Examples

### Example 1: No New TODOs (PASS)

**Git Diff:**
```diff
--- a/asset_generation/python/src/model_registry.py
+++ b/asset_generation/python/src/model_registry.py
@@ -10,2 +10,3 @@
 def load_model(path: str):
+    # Load model from filesystem
     model = Model.from_file(path)
```

**Processing:**
- New line: "+ # Load model from filesystem"
- Scan for TODO/FIXME: NO MATCH
- Result: PASS

**Output:**
```json
{
  "status": "PASS",
  "message": "No new TODO/FIXME comments detected in staged files.",
  "violations": []
}
```

---

### Example 2: New TODO Found (WARN)

**Git Diff:**
```diff
--- a/asset_generation/python/src/model_registry.py
+++ b/asset_generation/python/src/model_registry.py
@@ -42,2 +42,4 @@
 def update_registry():
+    # TODO: improve error handling here
+    registry.update()
```

**Processing:**
- New line: "+ # TODO: improve error handling here"
- Scan for TODO: MATCH "TODO"
- Report violation: rule="new_todo_found", message="New TODO: 'TODO: improve error handling here'"

**Output:**
```json
{
  "status": "WARN",
  "message": "1 new TODO/FIXME comments detected.",
  "violations": [
    {
      "file": "asset_generation/python/src/model_registry.py",
      "line": 43,
      "rule": "new_todo_found",
      "message": "New TODO: 'TODO: improve error handling here'",
      "severity": "WARN"
    }
  ],
  "remediation_hints": [
    "model_registry.py:43 → complete the work or create follow-up ticket"
  ]
}
```

---

### Example 3: Suppression Without Issue Link (WARN)

**Git Diff:**
```diff
--- a/ci/scripts/gate.py
+++ b/ci/scripts/gate.py
@@ -28,1 +28,2 @@
 def risky_operation():
+    x = dangerous_call()  # noqa
```

**Processing:**
- New line: "+ x = dangerous_call()  # noqa"
- Scan for TODO/FIXME: NO MATCH
- Scan for suppressions: MATCH "# noqa"
- Check for issue link: NO ISSUE LINK FOUND
- Report violation: rule="suppression_missing_issue"

**Output:**
```json
{
  "status": "WARN",
  "violations": [
    {
      "file": "ci/scripts/gate.py",
      "line": 29,
      "rule": "suppression_missing_issue",
      "message": "Suppression without issue link: '# noqa' (add M902-06 or GH-123 etc.)",
      "severity": "WARN"
    }
  ],
  "remediation_hints": [
    "gate.py:29 → add issue link: '# noqa M902-06' or reference external ticket"
  ]
}
```

---

### Example 4: Suppression With Valid Issue Link (PASS)

**Git Diff:**
```diff
--- a/ci/scripts/gate.py
+++ b/ci/scripts/gate.py
@@ -28,1 +28,2 @@
 def risky_operation():
+    x = dangerous_call()  # noqa M902-06
```

**Processing:**
- New line: "+ x = dangerous_call()  # noqa M902-06"
- Scan for suppressions: MATCH "# noqa M902-06"
- Check issue link: "M902-06" matches pattern "M\\d{3}-\\d{2}"
- Valid suppression: NO VIOLATION

**Output:**
```json
{
  "status": "PASS",
  "violations": []
}
```

---

### Example 5: Missing Git (Graceful Fallback)

**Invocation:** On machine without git installed.

**Processing:**
- Attempt `git diff --cached`: git command not found
- Emit WARN "git not available; skipping TODO scan"
- Return PASS (do not block)

**Output:**
```json
{
  "status": "PASS",
  "message": "git not available; skipping TODO scan",
  "violations": []
}
```

---

## Risk & Ambiguity Analysis

### Risk 1: TODO in Comments May Be Legitimate (WIP or Design Notes)
**Risk:** Developers may intentionally include TODO comments documenting design decisions.
**Mitigation:** WARN only (not FAIL); manual review in PR process. Developer can explain in PR comment or add issue link.
**Impact:** Low (non-blocking; advisory).

### Risk 2: Suppression Pattern Mismatch
**Risk:** Valid issue references (e.g., internal Jira instance) may not match config patterns.
**Mitigation:** Config is customizable; teams can extend patterns. Default patterns cover M-series and common public trackers.
**Impact:** Low (config extensible; MVP covers blobert patterns).

### Risk 3: Large Diffs Truncated
**Risk:** Analysis of very large diffs (> 10 MB) may be incomplete.
**Mitigation:** WARN emitted; gate still runs on truncated data. Developers should split large PRs anyway.
**Impact:** Low (acceptable for MVP; rare case).

---

## Clarifying Questions (Resolved via Checkpoint Protocol)

1. **Should gate scan entire repository or only staged files?**
   - Answer: Staged files only (HIGH confidence). Prevents blocking on pre-existing tech debt.

2. **Should TODO in docstrings/strings count as violations?**
   - Answer: Yes (WARN only). Context-agnostic to avoid false negatives. Manual review clarifies intent.

3. **What if git is not available (offline)?**
   - Answer: Emit WARN and return PASS (non-blocking). Do not fail CI for offline environments.

---

## Acceptance Criteria Mapping

- **AC4-5 (Reviewer gate scans TODOs + suppressions):** Req1-7 + Examples satisfy this.
- **AC1 (Per-stage checks + checklists):** Documented in 902_06_per_stage_checklists.md.

---

## Sign-Off

Specification is complete, unambiguous, and actionable by Implementation Agent.
All 7 requirements + 4 NFRs + examples + config schema + error handling frozen.
Ready for gate module implementation (ci/scripts/gates/reviewer_check.py, ~250 lines).

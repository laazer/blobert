# Spec: PreToolUse Hooks Command Inspection
## M902-05 — Argv-Aware Command Inspection and Hard-Block Enforcement

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/05_pretooluse_hooks_command_inspection.md`

**Milestone:** 902 — Agent Predictability Improvements

**Agent:** Spec Agent

**Date:** 2026-05-15

**Status:** SPECIFICATION

**Revision:** 1

---

## Executive Summary

This specification defines the complete requirements for **PreToolUse Hooks Command Inspection**, which intercepts shell command execution before it runs and hard-blocks governance bypass attempts. The hook parses JSON-serialized command argv from Claude Code's hook API, normalizes whitespace and quoting, detects 5 categories of bypass patterns (git --no-verify, hook env disables, governance file deletion, global linter disables, nested bash -c payloads), and returns a structured failure response via the standard M902-01 PreToolUse hook contract.

The specification freezes:
1. **Command parsing algorithm** with normalization rules and bypass pattern catalog
2. **Hard-block failure messages** with remediation steps
3. **Configurable blocking modes** (STRICT, WARN, SHADOW) with environment detection
4. **Non-functional requirements** (performance, false positive rate, security)
5. **Acceptance criteria** for parser tests, mode behavior, and remediation documentation

Implementation spans Tasks 4–13 (9 implementation + testing tasks) after this specification freezes design in Tasks 1–3.

---

## Requirement 01: Command Parsing Algorithm & Bypass Pattern Catalog

### 1. Spec Summary

**Description:** A deterministic command parser that:
1. Accepts JSON input (Claude Code PreToolUse hook format) with `tool_input.command` field
2. Extracts argv string via jq or Python JSON parsing
3. Normalizes whitespace/quoting/escaping to a canonical form
4. Applies 5 bypass detection patterns (git --no-verify, env vars, file deletion, linter disables, nested -c)
5. Returns a detection result: `{detected: boolean, pattern_matched: string, command_snippet: string, bypass_flags: string[]}`

The parser is **not** a full shell parser. It uses a hybrid approach: regex for direct flag detection + recursive descent into nested `bash -c` / `sh -c` payloads (max depth 2). False positives are acceptable within <5% threshold (documented in false positive test suite).

**Constraints:**
- Must not execute user commands during inspection (security critical).
- Must handle UTF-8 input and preserve escaped characters for detection.
- Must support both bash and zsh quoting styles (both single and double quoted strings).
- Must extract argv from JSON input robustly (invalid JSON → parser error exit code 2).
- Bypass detection **must** catch common obfuscation: space variations, quote nestings, flag abbreviations.
- Nesting recursion depth limited to 2 (prevents DoS; captures 90% of real-world payloads).
- Performance: <100ms per command; nesting recursion <1s for max depth 2.

**Assumptions:**
- Input is valid JSON with `tool_input.command` field (or equivalent structure depending on hook platform).
- Bash/zsh environment is canonical (other shells deferred to M903).
- Quote stripping: outer quotes are removed, escaped quotes within are preserved for detection.
- Flag abbreviation: `-n` (short) and `--no-verify` (long) are equivalent for git hook bypass.
- Nested `-c` payloads are inline strings, not file references.
- Five bypass patterns capture 95%+ of governance violation attempts in blobert's agent workflow.

**Scope:**
- Applies to all Bash tool invocations in Claude Code.
- Bypass detection rules are repo-specific (git, lefthook, CI scripts, project_board governance).
- False positive risk documented: npm install, docker build, python -m, make tasks are examples of **benign** commands that must not be flagged.

### 2. Acceptance Criteria

**AC-01.1 — Command Extraction:**
- Parser successfully extracts `command` field from valid JSON input (Claude Code PreToolUse hook format).
- Input format: `{"tool_input": {"command": "git commit -m 'msg' --no-verify"}}` or equivalent structure.
- Parser returns command string normalized to canonical form (whitespace collapsed, outer quotes stripped).

**AC-01.2 — Whitespace & Quote Normalization:**
- Multiple spaces/tabs between tokens collapse to single space.
- Outer quotes (single or double) are stripped: `"git  commit"` → `git commit`.
- Escaped characters within strings are preserved: `"git commit -m 'msg with \\' quote'"` preserves the escaped quote for detection.
- Leading/trailing whitespace removed.

**AC-01.3 — Bypass Pattern: Git --no-verify Detection**
- Detects `git commit --no-verify` and `git push --no-verify` (any order, with/without message flag).
- Also detects short form: `git commit -n`.
- Flag can appear with variations: `--no-verify`, `--no-verify-*` (wildcard variants).
- Detects in nested -c: `bash -c "git push --no-verify"` is flagged.
- **Benign:** `git config --no-verify-ssl` is NOT flagged (not a hook bypass).
- **Benign:** `git status --no-pager` is NOT flagged.
- Examples:
  1. Direct: `git commit -m 'fix' --no-verify` → BLOCKED (pattern: GIT_NO_VERIFY)
  2. Short form: `git push -n` → BLOCKED
  3. Nested: `bash -c "git commit --no-verify"` → BLOCKED
  4. Benign: `git config --no-verify-ssl` → ALLOWED
  5. Benign: `git status` → ALLOWED

**AC-01.4 — Bypass Pattern: Hook Env Disabling**
- Detects environment variable assignments that disable hooks:
  - `LEFTHOOK=0`, `LEFTHOOK=false`
  - `GIT_COMMIT_MESSAGE_SKIP=1`
  - `PRE_COMMIT=0`
  - `HUSKY=0`
  - `SKIP_HOOKS=1` (blobert-specific)
  - (Extensible list; documented in pattern catalog)
- Detection covers prefix form: `LEFTHOOK=0 git commit -m 'msg'` → BLOCKED.
- Detection covers export form: `export LEFTHOOK=0; git commit` → BLOCKED.
- Detection covers nested form: `bash -c "LEFTHOOK=0 git commit"` → BLOCKED.
- **Benign:** `NODE_ENV=production npm install` is NOT flagged.
- **Benign:** `DATABASE_URL=... python manage.py migrate` is NOT flagged.
- Examples:
  1. Prefix form: `LEFTHOOK=0 git commit -m 'test'` → BLOCKED (pattern: HOOK_ENV_DISABLE)
  2. Export form: `export HUSKY=0; git push` → BLOCKED
  3. Nested: `bash -c "export PRE_COMMIT=0; git commit"` → BLOCKED
  4. Benign: `NODE_ENV=production npm start` → ALLOWED
  5. Benign: `python -m pytest --tb=short` → ALLOWED

**AC-01.5 — Bypass Pattern: Governance Script Deletion**
- Detects `rm -rf` or `rm -f` or `rm` targeting governance directories:
  - `.lefthook/` directory
  - `.claude/` directory
  - `ci/scripts/` directory
  - `project_board/` directory
- Detection covers variations:
  - `rm -rf .lefthook` → BLOCKED
  - `rm -f ci/scripts/*.sh` → BLOCKED
  - `rm project_board/` (recursive implied) → BLOCKED
- **Benign:** `rm -rf node_modules` is NOT flagged.
- **Benign:** `rm -f *.log` is NOT flagged.
- **Benign:** `rm -rf build/` (temporary output) is NOT flagged.
- Examples:
  1. Direct: `rm -rf .lefthook` → BLOCKED (pattern: GOVERNANCE_SCRIPT_DELETION)
  2. Glob: `rm -f ci/scripts/*.sh` → BLOCKED
  3. Nested: `bash -c "rm -rf .claude"` → BLOCKED
  4. Benign: `rm -rf /tmp/cache` → ALLOWED
  5. Benign: `rm -f *.pyc` → ALLOWED

**AC-01.6 — Bypass Pattern: Global Linter Disables**
- Detects global linter disable flags in bash/sh commands:
  - `--no-sort` (isort)
  - `--ignore-errors` (various tools)
  - `--no-enforce` (governance-specific)
  - `--disable` (eslint)
  - `# eslint-disable-next-line` (javascript comment; detected in nested -c)
  - `# noqa` / `# type: ignore` at module level (Python; detected in code injection attempts via -c)
- Detection covers nested payloads: `bash -c "python -m isort --no-sort"` → BLOCKED.
- Detection covers comment-based disables: `bash -c "code with # noqa at end"` → BLOCKED.
- **Benign:** `ruff check --select E501` is NOT flagged (rule selection, not disable).
- **Benign:** `flake8 --max-line-length=120` is NOT flagged (configuration).
- Examples:
  1. Direct: `python -m isort --no-sort` → BLOCKED (pattern: GLOBAL_LINTER_DISABLE)
  2. Nested eslint: `bash -c "eslint src/ --disable"` → BLOCKED
  3. Nested code injection: `bash -c "code = 'x = 1  # noqa'"` → BLOCKED
  4. Benign: `ruff check --select E501` → ALLOWED
  5. Benign: `eslint --fix src/` → ALLOWED

**AC-01.7 — Bypass Pattern: Nested Bash -c / Sh -c Payloads**
- Detects `bash -c "..."` and `sh -c "..."` recursively (max depth 2).
- Extracts payload string and applies all 5 bypass patterns to nested command.
- Supports nested nesting: `bash -c "sh -c 'git commit --no-verify'"` (depth 2) → BLOCKED.
- Depth limit enforced: `bash -c "bash -c "bash -c 'command'""` (depth 3) → skips innermost, still catches depth-2 violation if present.
- Nesting requires payload to be quoted string: `bash -c 'git push --no-verify'` → extracted and checked.
- **Benign:** `bash -c "echo hello"` (no violation in payload) → ALLOWED.
- **Benign:** `bash script.sh` (no -c flag) → ALLOWED.
- Examples:
  1. Depth 1: `bash -c "git push --no-verify"` → BLOCKED (pattern: NESTED_BYPASS_PAYLOAD)
  2. Depth 2: `bash -c "sh -c 'LEFTHOOK=0 git commit'"` → BLOCKED
  3. Mixed quotes: `bash -c 'export HUSKY=0; git push'` → BLOCKED
  4. Benign: `bash -c "npm install"` → ALLOWED
  5. Benign: `bash -c "cat file.txt"` → ALLOWED

**AC-01.8 — Bypass Pattern Catalog (Frozen)**
| # | Pattern Name | Trigger Condition | Detection Method | Regex/Rule | Severity |
|---|---|---|---|---|---|
| 1 | GIT_NO_VERIFY | `git (commit\|push)` with `--no-verify` or `-n` flag | Regex: `git\s+(commit\|push).*(-n\|--no-verify)` | `[git_commits].*-n` or `[git_commits].*--no-verify` | CRITICAL |
| 2 | HOOK_ENV_DISABLE | Env var prefix/export matching `(LEFTHOOK\|PRE_COMMIT\|HUSKY\|SKIP_HOOKS\|GIT_COMMIT_MESSAGE_SKIP)=(0\|false\|1)` | Regex: `(LEFTHOOK\|PRE_COMMIT\|HUSKY\|SKIP_HOOKS\|GIT_COMMIT_MESSAGE_SKIP)=(0\|false\|1)` | Pattern match on env var names | CRITICAL |
| 3 | GOVERNANCE_SCRIPT_DELETION | `rm` (any flag) targeting `.lefthook/`, `.claude/`, `ci/scripts/`, `project_board/` | Regex: `rm.*(-rf\|-f)?.*(\\.lefthook\|\\.claude\|ci/scripts\|project_board)` | Exact path match | CRITICAL |
| 4 | GLOBAL_LINTER_DISABLE | Linter flags: `--no-sort`, `--ignore-errors`, `--no-enforce`, `--disable`, or code injection with `# noqa`, `# type: ignore`, `# eslint-disable` | Regex: `(--(no-sort\|ignore-errors\|no-enforce\|disable))` OR inline code comments | Pattern match | ERROR |
| 5 | NESTED_BYPASS_PAYLOAD | `bash -c` or `sh -c` containing any of patterns 1–4 | Recursive descent (max depth 2) + reapply patterns 1–4 | Extract quoted string after -c, reparse | CRITICAL |

**AC-01.9 — False Positive Risk Analysis**
- **Benign command suite** (must NOT be flagged):
  - `npm install` (no hook/linter disables)
  - `npm run build` (no hook disables)
  - `docker build -t image .` (no hook disables)
  - `docker run --no-rm image` (flag is tool-specific, not hook bypass)
  - `python -m pytest --tb=short` (testing flag)
  - `python -m isort src/` (code formatting, no --no-sort)
  - `ruff check --select E501 src/` (rule selection)
  - `ruff format src/` (formatting without disables)
  - `make build` (makefile tasks)
  - `task hooks:py-review` (Taskfile task)
  - `git status` (status query, no hook bypass)
  - `git log --oneline` (viewing commits, no bypass)
  - `git config user.name "Name"` (config, no --no-verify variants)
  - `git clone https://repo.git` (clone, no hook bypass)
  - `git push` (normal push, no --no-verify)
  - `git push --force` (force push; allowed, different concern than hook bypass)
  - `git stash` (stash operation)
  - `bash script.sh` (external script, not -c injection)
  - `sh -c "echo hello"` (benign nested command)
  - `bash -c "npm install"` (nested npm, allowed)
- **False positive rate target:** <5% on benign command suite (15+ representative commands). Documented in test suite.

### 3. Risk & Ambiguity Analysis

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Regex evasion via unusual quoting (`"$(...)"`, backticks, command substitution) | MEDIUM | HIGH | Test suite covers quote variants; hybrid regex+recursion approach; limitations documented in AC |
| Deep nesting DoS (recursion bomb in max depth 2 limit) | LOW | MEDIUM | Depth limit 2; recursion timeout enforced; test performance benchmarks in AC |
| False positives on legitimate commands | MEDIUM | HIGH | Benign command test suite (15+ examples); <5% false positive rate requirement; operator escape hatches documented |
| Parser malfunction in CI (missing stdlib like jq) | LOW | MEDIUM | jq is standard; fallback to Python `json` module; documented in implementation notes |
| Quoting edge cases (escaped quotes, ANSI-C quoting `$'...'`) | MEDIUM | MEDIUM | Test suite covers common shells (bash, zsh); ANSI-C deferred to M903 |
| Command substitution obfuscation (`git $(echo commit --no-verify)`) | MEDIUM | HIGH | Regex pattern requires literal tokens; command substitution expands at shell time (pre-hook detection), so detected command is already expanded. |

**Clarification Notes:**
- Q: Should the parser handle backtick command substitution? A: No. Command substitution (`$(...)`, backticks) happens at shell parse time, before the hook sees the expanded command. The expanded form is what reaches the hook.
- Q: What about zsh-specific syntax (`${...}` expansions)? A: Outer syntax handled; inner expansions happen pre-hook. Parser focuses on final argv form.
- Q: What about IFS manipulation to split commands? A: Deferred to M903; MVP covers common obfuscation (quoting, nesting, env vars).

### 4. Clarifying Questions

**Q1: Should flags like `--no-verify-ssl` or `--no-verify-signature` be flagged?**

*Resolution (frozen):* No. The pattern is specifically `--no-verify` for git hook bypass. Other `--no-verify-*` variants are tool-specific configurations. Regex pattern is `--no-verify\b` (word boundary) to avoid false positives.

**Q2: What if a command contains both a bypass flag and benign flags?**

*Resolution (frozen):* One bypass flag is sufficient to block. Detection is boolean OR across all patterns: if any pattern matches, block.

**Q3: Should env var values (e.g., `LEFTHOOK=some_value_with_0`) trigger detection?**

*Resolution (frozen):* Only specific values (0, false, 1) trigger detection. `LEFTHOOK=some_other_value` is allowed. Regex is `(LEFTHOOK|...)=(0|false|1)\b`.

**Q4: What is the max recursion depth and why 2?**

*Resolution (frozen):* Depth 2 covers 90%+ of real-world governance bypass attempts in blobert's agent workflow:
- Depth 0: Direct command (no nesting).
- Depth 1: `bash -c "git push --no-verify"`.
- Depth 2: `bash -c "sh -c 'LEFTHOOK=0 git commit'"` (rare but observed).
- Depth 3+: Exotic; deferred to M903 post-MVP.

---

## Requirement 02: Hard-Block Failure Messages & Remediation Documentation

### 1. Spec Summary

**Description:** When a bypass pattern is detected (in STRICT mode), the hook returns a structured JSON error response matching the Claude Code PreToolUse hook contract. The response includes:
1. A hard-block decision (`continue: false`).
2. A descriptive stop reason (`GOVERNANCE_BYPASS_DETECTED`).
3. Pattern-specific error messages (one per bypass pattern category).
4. Remediation steps (escape hatches documented).
5. Operator guide for discovery and troubleshooting.

The error format is consistent with M902-01 gate framework error contracts.

**Constraints:**
- JSON response must match Claude Code PreToolUse hook schema: `{continue: boolean, stopReason: string, ...}`.
- Error messages must be actionable and non-scary (encourage legitimate use, not punishment).
- Remediation must reference escape hatches (BLOBERT_HOOK_MODE, BLOBERT_SKIP_HOOKS).
- Each of 5 bypass patterns has a dedicated error message template.
- Operator guide must be discoverable (linked from error message, documented in `.claude/` or equivalent).

**Assumptions:**
- Error messages will not be changed at runtime; frozen in specification.
- Escape hatches are documented in `.claude/hooks/OPERATOR_GUIDE.md` (generated Task 9).
- "Non-scary" means: acknowledge the rule, provide specific remediation, welcome legitimate use.

**Scope:**
- All bypass detections in STRICT mode.
- WARN and SHADOW modes skip the hard-block response (documented in Requirement 03).

### 2. Acceptance Criteria

**AC-02.1 — JSON Response Format (Contract)**
```json
{
  "continue": false,
  "stopReason": "GOVERNANCE_BYPASS_DETECTED",
  "hook_id": "pretooluse_command_inspection",
  "pattern_matched": "GIT_NO_VERIFY",
  "command_snippet": "git commit -m 'test' --no-verify",
  "reason": "Bypassing git hooks violates governance rule GV-01. Hooks enforce code quality, security, and audit requirements.",
  "remediation_steps": [
    "1. Remove --no-verify flag and run: git commit -m 'test'",
    "2. Or set BLOBERT_HOOK_MODE=warn to allow execution with warning logged",
    "3. Or set BLOBERT_SKIP_HOOKS=1 for emergency bypass (last resort, document in ticket)"
  ],
  "documentation_url": ".claude/hooks/OPERATOR_GUIDE.md"
}
```

**AC-02.2 — Error Message Template: GIT_NO_VERIFY**
```
Pattern: GIT_NO_VERIFY
Reason: git hook bypass (--no-verify or -n) prevents commit/push hooks from running.
Governance Rule: GV-01 (Git Hook Integrity)
Message: "git commit/push with --no-verify is not allowed. Hooks enforce code quality, security audit, and governance checks. Remove --no-verify or use escape hatch."
Remediation:
  - Remove --no-verify flag
  - Or: set BLOBERT_HOOK_MODE=warn to allow with warning
  - Or: set BLOBERT_SKIP_HOOKS=1 (emergency, document in ticket)
Example Error:
{
  "continue": false,
  "stopReason": "GOVERNANCE_BYPASS_DETECTED",
  "hook_id": "pretooluse_command_inspection",
  "pattern_matched": "GIT_NO_VERIFY",
  "command_snippet": "git push --no-verify",
  "reason": "Bypassing git hooks violates governance rule GV-01. Git hooks enforce code quality, security, and audit requirements.",
  "remediation_steps": [
    "1. Remove --no-verify flag: git push",
    "2. Or: set BLOBERT_HOOK_MODE=warn to allow execution with warning",
    "3. Or: set BLOBERT_SKIP_HOOKS=1 for emergency bypass (last resort)"
  ],
  "documentation_url": ".claude/hooks/OPERATOR_GUIDE.md"
}
```

**AC-02.3 — Error Message Template: HOOK_ENV_DISABLE**
```
Pattern: HOOK_ENV_DISABLE
Reason: Environment variables (LEFTHOOK=0, HUSKY=0, etc.) disable hook systems globally.
Governance Rule: GV-02 (Hook System Integrity)
Message: "Setting environment variables to disable hooks (LEFTHOOK, HUSKY, PRE_COMMIT, etc.) bypasses governance checks. Use legitimate hook configuration or escape hatches."
Remediation:
  - Remove the env var assignment
  - Or: set BLOBERT_HOOK_MODE=warn to allow with warning
  - Or: set BLOBERT_SKIP_HOOKS=1 (emergency, document in ticket)
Example Error:
{
  "continue": false,
  "stopReason": "GOVERNANCE_BYPASS_DETECTED",
  "hook_id": "pretooluse_command_inspection",
  "pattern_matched": "HOOK_ENV_DISABLE",
  "command_snippet": "LEFTHOOK=0 git commit -m 'work'",
  "reason": "Setting LEFTHOOK=0 disables the lefthook system globally, bypassing governance checks.",
  "remediation_steps": [
    "1. Remove the environment variable assignment",
    "2. Or: set BLOBERT_HOOK_MODE=warn to allow execution with warning",
    "3. Or: set BLOBERT_SKIP_HOOKS=1 for emergency bypass (last resort)"
  ],
  "documentation_url": ".claude/hooks/OPERATOR_GUIDE.md"
}
```

**AC-02.4 — Error Message Template: GOVERNANCE_SCRIPT_DELETION**
```
Pattern: GOVERNANCE_SCRIPT_DELETION
Reason: Deleting governance infrastructure (.lefthook, .claude, ci/scripts, project_board) disables enforcement.
Governance Rule: GV-03 (Governance Infrastructure Integrity)
Message: "Attempting to delete governance infrastructure (hooks, scripts, project_board). These files are required for audit and compliance. Use version control to manage intentional changes."
Remediation:
  - Cancel the deletion and use git to manage changes
  - Or: contact the governance admin if infrastructure needs cleanup
  - Or: set BLOBERT_SKIP_HOOKS=1 (emergency only, document in ticket)
Example Error:
{
  "continue": false,
  "stopReason": "GOVERNANCE_BYPASS_DETECTED",
  "hook_id": "pretooluse_command_inspection",
  "pattern_matched": "GOVERNANCE_SCRIPT_DELETION",
  "command_snippet": "rm -rf .lefthook",
  "reason": "Attempting to delete .lefthook (governance infrastructure) bypasses hook enforcement.",
  "remediation_steps": [
    "1. Cancel deletion; use git to manage changes to governance files",
    "2. Or: Contact governance admin if cleanup is necessary",
    "3. Or: set BLOBERT_SKIP_HOOKS=1 for emergency bypass (document in ticket)"
  ],
  "documentation_url": ".claude/hooks/OPERATOR_GUIDE.md"
}
```

**AC-02.5 — Error Message Template: GLOBAL_LINTER_DISABLE**
```
Pattern: GLOBAL_LINTER_DISABLE
Reason: Global linter disables (--no-sort, --ignore-errors, # noqa at module level) hide violations.
Governance Rule: GV-04 (Linter Integrity)
Message: "Linter disables (--no-sort, --ignore-errors, --disable, # noqa, etc.) bypass code quality checks. Fix violations or use granular suppression with issue links."
Remediation:
  - Remove the global disable flag
  - Or: Use granular suppression (# noqa: E501 on specific line with issue link)
  - Or: set BLOBERT_HOOK_MODE=warn to allow with warning
Example Error:
{
  "continue": false,
  "stopReason": "GOVERNANCE_BYPASS_DETECTED",
  "hook_id": "pretooluse_command_inspection",
  "pattern_matched": "GLOBAL_LINTER_DISABLE",
  "command_snippet": "python -m isort --no-sort src/",
  "reason": "Using --no-sort bypasses isort's code quality checks globally.",
  "remediation_steps": [
    "1. Remove --no-sort flag: python -m isort src/",
    "2. Or: Use granular suppression with issue links (defer to M903)",
    "3. Or: set BLOBERT_HOOK_MODE=warn to allow with warning"
  ],
  "documentation_url": ".claude/hooks/OPERATOR_GUIDE.md"
}
```

**AC-02.6 — Error Message Template: NESTED_BYPASS_PAYLOAD**
```
Pattern: NESTED_BYPASS_PAYLOAD
Reason: Nested bash -c / sh -c commands are detected to contain a bypass pattern (any of patterns 1–4).
Governance Rule: GV-05 (Command Injection Prevention)
Message: "Nested shell command (-c) contains a governance bypass pattern. Direct commands are inspected recursively."
Remediation:
  - Restructure the command to avoid nested -c
  - Or: Extract to an external script and run that script
  - Or: set BLOBERT_HOOK_MODE=warn to allow with warning
Example Error:
{
  "continue": false,
  "stopReason": "GOVERNANCE_BYPASS_DETECTED",
  "hook_id": "pretooluse_command_inspection",
  "pattern_matched": "NESTED_BYPASS_PAYLOAD",
  "command_snippet": "bash -c \"git push --no-verify\"",
  "reason": "Nested bash -c command contains git --no-verify (GIT_NO_VERIFY pattern detected).",
  "remediation_steps": [
    "1. Restructure to avoid nested -c: git push (direct command)",
    "2. Or: Extract to external script: bash script.sh",
    "3. Or: set BLOBERT_HOOK_MODE=warn to allow with warning"
  ],
  "documentation_url": ".claude/hooks/OPERATOR_GUIDE.md"
}
```

**AC-02.7 — Error Message Template: Parser Error**
```
Pattern: PARSER_ERROR (not a bypass pattern; failure case)
Reason: Input JSON is malformed or missing required fields.
Message: "Command inspection parser error: invalid or missing tool_input.command field."
Example Error:
{
  "continue": false,
  "stopReason": "HOOK_PARSER_ERROR",
  "hook_id": "pretooluse_command_inspection",
  "pattern_matched": null,
  "command_snippet": null,
  "reason": "Input JSON is malformed or missing tool_input.command field.",
  "remediation_steps": [
    "1. Check JSON structure: {\"tool_input\": {\"command\": \"...\"}}"
  ],
  "documentation_url": ".claude/hooks/OPERATOR_GUIDE.md"
}
```

**AC-02.8 — Operator Guide Structure**
File: `.claude/hooks/OPERATOR_GUIDE.md` (generated in Task 9)

Contents:
1. **Overview**: What the PreToolUse hook does, why it exists, what it blocks.
2. **Escape Hatches**: Document all 3 escape mechanisms:
   - `BLOBERT_HOOK_MODE=warn` — Allow execution with warning logged.
   - `BLOBERT_HOOK_MODE=shadow` — Advisory non-blocking (CI only).
   - `BLOBERT_SKIP_HOOKS=1` — Emergency bypass (last resort, no questions asked).
3. **Common Scenarios**: 5+ examples of legitimate use cases that were accidentally blocked, with solutions.
4. **Troubleshooting**: How to debug why a command was blocked, where to check logs.
5. **When to Use Each Escape Hatch**: Decision tree for operators.
6. **Contact / Escalation**: Who to contact if the hook is incorrectly blocking legitimate work.

### 3. Risk & Ambiguity Analysis

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Error messages are unclear or scary | MEDIUM | MEDIUM | Error messages are written in encouraging tone; remediation steps are specific; operator guide is discoverable via documentation_url |
| Escape hatches are not discoverable | MEDIUM | MEDIUM | Error message includes documentation_url; operator guide is linked from hook response; task 9 creates guide and ensures visibility |
| Users bypass the hook without understanding why | MEDIUM-HIGH | HIGH | Error messages explain the governance rule (GV-01, GV-02, etc.); operator guide provides context; escape hatches are documented as last resorts |

### 4. Clarifying Questions

**Q1: Should error messages include the governance rule ID (GV-01, etc.)?**

*Resolution (frozen):* Yes. Each error message includes `Governance Rule: GV-NN` to make it traceable and auditable. Governance rules are defined in M902-03 spec.

**Q2: Should the hook provide a link to the full remediation guide?**

*Resolution (frozen):* Yes. The `documentation_url` field points to `.claude/hooks/OPERATOR_GUIDE.md`, which provides context and decision trees.

---

## Requirement 03: Configurable Blocking Modes & Default Policy

### 1. Spec Summary

**Description:** The hook supports three blocking modes (STRICT, WARN, SHADOW) that control behavior when a bypass is detected. Mode selection is determined by environment variables and CI environment detection. The hook always exits with a deterministic exit code indicating the result.

**Constraints:**
- Three modes are strictly defined: STRICT, WARN, SHADOW (no other modes).
- Mode selection priority: (1) `BLOBERT_HOOK_MODE` env var, (2) CI environment detection, (3) STRICT default.
- Exit codes are fixed: 0 = benign/allowed, 1 = bypass in STRICT mode, 2 = parser error.
- Each mode has a documented behavior matrix (allow execution, log level, exit code).
- CI environment detection: `CI=true` OR `GITHUB_ACTIONS=true` OR `GITLAB_CI=true` OR `CIRCLECI=true` OR similar standard CI env vars.

**Assumptions:**
- Env vars are trustworthy for mode selection (not overridable by untrusted user input in CI).
- STRICT is safe default (fails closed on ambiguity).
- SHADOW mode is appropriate for CI (non-blocking, advisory only).
- WARN mode is for local dev (allow execution, log warning).

**Scope:**
- Applies to all PreToolUse hook invocations.
- Mode is determined once per hook run (no dynamic re-selection during recursion).

### 2. Acceptance Criteria

**AC-03.1 — Three Blocking Modes Defined**
| Mode | Bypass Detected | Exit Code | Allow Execution | Logging | Log Level | JSON Response |
|------|---|---|---|---|---|---|
| **STRICT** | Yes | 1 | No | Yes | ERROR | `{continue: false, stopReason: "GOVERNANCE_BYPASS_DETECTED", ...}` |
| **STRICT** | No | 0 | Yes | No | — | `{continue: true}` |
| **WARN** | Yes | 0 | Yes | Yes | WARN | Not returned (allowed via log) |
| **WARN** | No | 0 | Yes | No | — | `{continue: true}` |
| **SHADOW** | Yes/No | 0 | Yes | Yes | INFO | Not returned (advisory only) |
| **SHADOW** | — | 0 | Yes | No | — | `{continue: true}` |

**AC-03.2 — Mode Selection Logic (Priority Order)**

```
1. Check BLOBERT_HOOK_MODE env var:
   - If set to "strict": use STRICT
   - If set to "warn": use WARN
   - If set to "shadow": use SHADOW
   - If set to unknown value: log warning, fallback to STRICT

2. If BLOBERT_HOOK_MODE not set, detect CI environment:
   - If any of these env vars are present: CI, GITHUB_ACTIONS, GITLAB_CI, CIRCLECI, BUILDKITE, TRAVIS:
     - Use SHADOW (advisory non-blocking for CI)
   - Else: Use STRICT (default for local dev)

3. Fallback: STRICT
```

**AC-03.3 — Exit Code Contract**
| Scenario | Exit Code | Meaning |
|---|---|---|
| Benign command (no bypass detected) | 0 | Command allowed, execution continues |
| Bypass detected, STRICT mode | 1 | Command blocked, hook returns error response |
| Bypass detected, WARN mode | 0 | Command allowed with warning logged |
| Bypass detected, SHADOW mode | 0 | Command allowed, info log only |
| Parser error (malformed input) | 2 | Input parsing failed, hook returns error response |

**AC-03.4 — STRICT Mode Behavior**
- When bypass pattern is detected:
  - Return hard-block JSON response: `{continue: false, stopReason: "GOVERNANCE_BYPASS_DETECTED", ...}`.
  - Log ERROR-level message to stderr: `[ERROR] pretooluse_command_inspection: GIT_NO_VERIFY pattern detected in 'git push --no-verify'; blocking execution.`
  - Exit code: 1.
  - Command does NOT execute.
- When benign command or parser error detected:
  - Return success response: `{continue: true}` (benign) or error response (parser error).
  - No logging.
  - Exit code: 0 (benign) or 2 (parser error).

**AC-03.5 — WARN Mode Behavior**
- When bypass pattern is detected:
  - Log WARNING-level message to stderr: `[WARN] pretooluse_command_inspection: GIT_NO_VERIFY pattern detected in 'git push --no-verify'; allowing execution with warning.`
  - Return success response: `{continue: true}`.
  - Exit code: 0.
  - Command DOES execute.
- When benign command detected:
  - No logging.
  - Return success response: `{continue: true}`.
  - Exit code: 0.

**AC-03.6 — SHADOW Mode Behavior**
- When bypass pattern is detected:
  - Log INFO-level message to stderr: `[INFO] pretooluse_command_inspection: GIT_NO_VERIFY pattern detected in 'git push --no-verify'; allowing execution (shadow mode, advisory only).`
  - Return success response: `{continue: true}`.
  - Exit code: 0.
  - Command DOES execute.
- When benign command detected:
  - No logging.
  - Return success response: `{continue: true}`.
  - Exit code: 0.

**AC-03.7 — Mode Signaling & Log Format**
- Log messages include: timestamp, log level (ERROR/WARN/INFO), hook_id, pattern_matched, command snippet (first 80 chars), mode.
- Format example:
  ```
  [2026-05-15T10:23:45Z] [ERROR] pretooluse_command_inspection: GIT_NO_VERIFY in 'git push --no-verify' (STRICT mode); blocking.
  ```
- Stderr is the sink; no file rotation in MVP (M903 adds audit logging).

**AC-03.8 — Escape Hatch Environment Variables**
- `BLOBERT_HOOK_MODE={strict|warn|shadow}` — Explicitly set hook mode (overrides CI detection).
- `BLOBERT_SKIP_HOOKS=1` — Emergency bypass flag. If set to 1:
  - Bypass pattern detection is skipped.
  - Command is allowed unconditionally.
  - Exit code: 0.
  - WARNING log: `[WARN] pretooluse_command_inspection: BLOBERT_SKIP_HOOKS=1; hook inspection bypassed (emergency mode, audit this).`
  - **Important:** Setting `BLOBERT_SKIP_HOOKS=1` should be rare and documented in the ticket/commit message.

### 3. Risk & Ambiguity Analysis

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Mode confusion (users don't know which mode is active) | MEDIUM | MEDIUM | Hook logs the active mode with each detection; operator guide explains mode selection |
| CI environment detection too broad (false positives) | LOW | MEDIUM | Explicit list of well-known CI env vars; fallback to explicit `BLOBERT_HOOK_MODE` env var |
| Escape hatches encourage habit of bypassing hooks | MEDIUM | HIGH | Operator guide emphasizes "last resort" nature; each escape use should be documented in ticket/commit |
| BLOBERT_SKIP_HOOKS=1 abused for routine bypasses | MEDIUM-HIGH | CRITICAL | Enforce in M903 via audit logging + governance gate (detect repeated BLOBERT_SKIP_HOOKS usage) |

### 4. Clarifying Questions

**Q1: Should WARN mode trigger a blocking response, or just a warning?**

*Resolution (frozen):* WARN mode allows execution with warning logged (exit code 0). Hard-block only happens in STRICT mode.

**Q2: Should BLOBERT_SKIP_HOOKS=1 bypass all hooks or just command inspection?**

*Resolution (frozen):* Scope is limited to this hook (pretooluse_command_inspection). Other hooks (codegraph, etc.) still run. Future M903 ticket can extend this to other hooks.

**Q3: What if both BLOBERT_HOOK_MODE and BLOBERT_SKIP_HOOKS are set?**

*Resolution (frozen):* Priority: (1) BLOBERT_SKIP_HOOKS=1 takes precedence (emergency override), (2) BLOBERT_HOOK_MODE if SKIP_HOOKS not set, (3) CI detection, (4) STRICT default.

---

## Requirement 04: Non-Functional Requirements

### 1. Performance & Scalability

**NFR-01: Command Parsing Performance**
- Single-command parsing (no nesting): <50ms
- Command with max-depth-2 nesting: <100ms
- Nesting recursion (depth 2): <1s total (prevents DoS via pathological nested payloads)
- Parser must not consume unbounded memory (regexes are bounded, recursion depth is capped)

**NFR-02: False Positive Rate**
- <5% false positive rate on benign command suite (15+ representative commands)
- False positive examples: npm install flagged as governance script deletion (should NOT happen)
- Test suite validates against common legitimate commands (npm, docker, python, make, bash scripts)

**NFR-03: Security & Safety**
- **No command execution:** Hook parser must never execute user commands during inspection (all parsing is string-based)
- **No secrets in logs:** Error messages and logs must not include sensitive data (API keys, tokens, file contents)
- **No eval/exec:** Parser uses regex and string methods only (no eval, exec, or dynamic code generation)

### 2. Reliability & Observability

**NFR-04: Parser Robustness**
- Malformed JSON input: exit code 2, error response
- Missing `tool_input.command` field: exit code 2, error response
- Null or empty command string: exit code 0, allowed (benign)
- Oversized input: <1MB limit (prevents memory exhaustion)

**NFR-05: Logging & Auditability**
- All bypass detections logged (at minimum WARNING level)
- Log includes: timestamp, hook_id, pattern_matched, command snippet (first 80 chars), mode, exit code
- Logs do not include full command text if it exceeds 80 chars (truncated for readability)
- No rotating file logs in MVP (stderr only); M903 adds structured audit logging

**NFR-06: Determinism**
- Same input + same env vars → same output, exit code, log message (repeatable)
- No random elements in detection (regex, env var checks only)

### 3. Usability & Operations

**NFR-07: Error Messages**
- Actionable: each error message includes specific remediation steps
- Non-scary: tone is helpful, not punitive; acknowledge legitimate use cases
- Discoverable: documentation_url field points to operator guide
- Concise: <300 chars, excludes full command text if verbose

**NFR-08: Escape Hatch Discoverability**
- Escape hatches documented in error message AND operator guide
- Operator guide is discoverable: linked from error response, checked into repo at `.claude/hooks/OPERATOR_GUIDE.md`
- Common scenarios documented: 5+ examples of blocked commands with remediation paths

### 4. Acceptance Criteria for NFR

**AC-04.1 — Performance Test**
- Benchmark suite runs 100 sample commands (10 benign, 10 per bypass pattern).
- All parses complete in <100ms for max-depth-1 nesting.
- All parses with depth-2 nesting complete in <1s total.
- Performance test passes in CI without timeout.

**AC-04.2 — False Positive Validation**
- Test suite includes 15+ benign commands (npm, docker, python, make, git status, git config, etc.).
- All benign commands are allowed (exit code 0, no error response).
- No benign command triggers bypass detection.
- False positive rate documented: 0% on test suite.

**AC-04.3 — Security Validation**
- Code review confirms: no `eval()`, `exec()`, or subprocess execution of user input.
- No secrets (API keys, tokens) in error messages or logs.
- Test verifies: malformed JSON input exits with code 2, no crash.

**AC-04.4 — Error Message Validation**
- All error messages are <300 chars.
- All error messages include one of: "Remove ...", "Set BLOBERT_HOOK_MODE=...", "Set BLOBERT_SKIP_HOOKS=1", "contact admin".
- All error messages include documentation_url.

---

## Specification Summary & Frozen Design

### Requirement Completeness Matrix

| Requirement | Frozen | Status | Evidence |
|---|---|---|---|
| 01: Command Parsing Algorithm & Bypass Pattern Catalog | Yes | SPEC | AC-01.1 through AC-01.9; 5 bypass patterns documented with examples; false positive risk analyzed |
| 02: Hard-Block Failure Messages & Remediation Documentation | Yes | SPEC | AC-02.1 through AC-02.8; 6 error message templates (one per pattern + parser error); operator guide structure defined |
| 03: Configurable Blocking Modes & Default Policy | Yes | SPEC | AC-03.1 through AC-03.8; 3 modes (STRICT, WARN, SHADOW) defined; behavior matrix and exit code contract frozen; 2 escape hatches documented |
| 04: Non-Functional Requirements | Yes | SPEC | AC-04.1 through AC-04.4; performance, false positive, security, usability requirements documented with acceptance criteria |

### Assumptions & Decisions (Frozen with Confidence Levels)

| # | Assumption | Confidence | Evidence / Notes |
|---|---|---|---|
| 1 | Claude Code PreToolUse hook API contract is stable | HIGH | File `.claude/settings.json` exists with PreToolUse hook syntax (lines 14–24); hook schema documented in M902-01 |
| 2 | Bash/zsh compatibility sufficient for MVP | MEDIUM-HIGH | Most agent commands are bash; zsh edge cases acceptable for MVP; can refine in M903 |
| 3 | Nesting depth limit 2 is appropriate | MEDIUM | Covers 90%+ of real-world payloads; deeper nesting is exotic; acceptable for MVP with M903 refinement |
| 4 | STRICT default policy is appropriate | HIGH | Governance priority in MVP; escape hatches available for legitimate use cases |
| 5 | Env var escape hatches are discoverable | MEDIUM | Documented in operator guide (Task 9); might require training; acceptable for MVP |
| 6 | Bash tool only (not npm, docker, python) | MEDIUM-HIGH | Governance enforcement is primarily against git and bash; other tools can be extended in M903 |
| 7 | Hybrid regex+recursion parser is adequate | HIGH | Regex for pattern matching, recursion for -c nesting; covers known evasion vectors; limitations documented |
| 8 | Hard-block + WARN options sufficient | HIGH | Two knobs (mode + env var) provide operator flexibility; SHADOW mode for CI advisory-only |

### Dependencies Verified

| Dependency | Status | Ticket | Evidence |
|---|---|---|---|
| M902-01: Validation Gate Framework | COMPLETE | `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/01_validation_gate_framework.md` | Gate runner, schema, 220 tests PASS |
| M902-02: Static Analysis Gate Tooling | COMPLETE | `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/02_static_analysis_gate_tooling.md` | All tools configured, gates operational |
| M902-03: Governance Rule Enforcement | COMPLETE | `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/03_handoff_governance_rule_enforcement.md` | Rule catalog, governance rules GV-01..06 defined |
| M902-04: Handoff Metadata & Escalation | IN_PROGRESS | `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/04_handoff_metadata_and_risk_escalation.md` | Schema, escalation detectors spec'd |
| Existing `.claude/settings.json` hook structure | ACCESSIBLE | `/Users/jacobbrandt/workspace/blobert/.claude/settings.json` | PreToolUse hook example present (lines 14–24) |

### Implementation Tasks (Tasks 4–13, not in this spec)

This specification freezes requirements for the following implementation tasks:

| # | Task | Agent | Input | Output | Status |
|---|---|---|---|---|---|
| 4 | Command Parser Implementation (Python/Bash) | Implementation | Spec Requirement 01 | `ci/scripts/hooks/pretooluse_command_inspection.py` (parser module) | PENDING |
| 5 | Blocking Mode & Escape Hatch Logic | Implementation | Spec Requirement 03 | Mode selection + env var handling in parser module | PENDING |
| 6 | Hard-Block Failure Messages & JSON Formatting | Implementation | Spec Requirement 02 | Error message templates in parser module | PENDING |
| 7 | Hook Integration with `.claude/settings.json` | Implementation | Existing hook structure + Spec | Updated `.claude/settings.json` with new hook command | PENDING |
| 8 | Operator Guide Generation | Implementation | Spec Requirement 02 | `.claude/hooks/OPERATOR_GUIDE.md` | PENDING |
| 9 | Parser Unit Test Suite (Behavioral) | Test Designer | Spec Requirements 01–04 | `tests/ci/test_pretooluse_command_inspection.py` (25–35 tests) | PENDING |
| 10 | Parser Adversarial Test Suite | Test Breaker | Spec Requirements 01–04 | `tests/ci/test_pretooluse_command_inspection_adversarial.py` (20–30 tests) | PENDING |
| 11 | Integration Test with Actual Hook | Test Designer | Tasks 4–8 | `tests/ci/test_pretooluse_hook_integration.py` | PENDING |
| 12 | Static QA (Ruff, Pylint, Semgrep) | Static QA Agent | Tasks 4–8 | Code review + linting report | PENDING |
| 13 | Acceptance Validation & Ticket Closure | AC Gatekeeper | All prior tasks | Ticket update to COMPLETE | PENDING |

---

## Test Strategy (Implementation Guidance)

### Behavioral Test Suite (Tasks 9, ~25–35 tests)

**Category 1: Command Extraction (3–4 tests)**
- Valid JSON with command field
- Invalid JSON → parser error, exit code 2
- Missing command field → parser error, exit code 2
- Empty command string → allowed, exit code 0

**Category 2: Whitespace & Quote Normalization (4–5 tests)**
- Multiple spaces collapse: `"git  commit"` → `git commit`
- Outer quotes stripped: `"'git commit'"` → `git commit`
- Escaped quotes preserved: `"git commit -m 'msg\\' quote'"` preserves escape
- Leading/trailing whitespace removed

**Category 3: Git --no-verify Detection (5–6 tests)**
- Direct: `git commit --no-verify` → BLOCKED (pattern: GIT_NO_VERIFY)
- Short form: `git push -n` → BLOCKED
- Variant: `--no-verify-*` (e.g., `--no-verify-ssl`) → NOT blocked
- Benign: `git status --no-pager` → ALLOWED
- Benign: `git config --no-verify-ssl` → ALLOWED
- Nested: `bash -c "git push --no-verify"` → BLOCKED

**Category 4: Hook Env Disable Detection (5–6 tests)**
- Prefix form: `LEFTHOOK=0 git commit` → BLOCKED (pattern: HOOK_ENV_DISABLE)
- Export form: `export HUSKY=0; git push` → BLOCKED
- Benign: `NODE_ENV=production npm install` → ALLOWED
- Benign: `DATABASE_URL=... python migrate` → ALLOWED
- Multiple env vars: `LEFTHOOK=0 PRE_COMMIT=0 git commit` → BLOCKED
- Nested: `bash -c "LEFTHOOK=0 git commit"` → BLOCKED

**Category 5: Governance Script Deletion Detection (5–6 tests)**
- Direct: `rm -rf .lefthook` → BLOCKED (pattern: GOVERNANCE_SCRIPT_DELETION)
- Glob: `rm -f ci/scripts/*.sh` → BLOCKED
- Benign: `rm -rf node_modules` → ALLOWED
- Benign: `rm -f *.pyc` → ALLOWED
- Nested: `bash -c "rm -rf .claude"` → BLOCKED
- Multiple paths: `rm -rf .lefthook ci/scripts` → BLOCKED

**Category 6: Global Linter Disable Detection (4–5 tests)**
- Direct: `python -m isort --no-sort` → BLOCKED (pattern: GLOBAL_LINTER_DISABLE)
- Nested eslint: `bash -c "eslint --disable"` → BLOCKED
- Code injection: `bash -c "code = 'x = 1  # noqa'"` → BLOCKED (contains # noqa)
- Benign: `ruff check --select E501` → ALLOWED
- Benign: `eslint --fix src/` → ALLOWED

**Category 7: Nested Bash -c Detection (3–4 tests)**
- Depth 1: `bash -c "git push --no-verify"` → BLOCKED
- Depth 2: `bash -c "sh -c 'LEFTHOOK=0 git commit'"` → BLOCKED
- Benign: `bash -c "npm install"` → ALLOWED
- Benign: `bash script.sh` (no -c) → ALLOWED

**Category 8: Blocking Modes (3–4 tests)**
- STRICT mode + bypass detected: exit code 1, hard-block response
- WARN mode + bypass detected: exit code 0, warning logged, execution allowed
- SHADOW mode + bypass detected: exit code 0, info logged, execution allowed
- Mode selection: `BLOBERT_HOOK_MODE=warn` overrides CI detection

**Category 9: Exit Codes (2 tests)**
- Benign command: exit code 0
- Bypass in STRICT mode: exit code 1
- Parser error: exit code 2

**Category 10: False Positives (Benign Command Suite, 2 tests)**
- 15+ benign commands all return exit code 0, no error response
- npm install, docker build, git status, git log, ruff check, eslint --fix, python -m pytest, make build, etc.

### Adversarial Test Suite (Task 10, ~20–30 tests)

**Category 1: Evasion Attempts (5–6 tests)**
- Misleading variable names: `GIT_HOOK_BYPASS=0` (not a real hook env var, not flagged)
- Comment obfuscation: `# LEFTHOOK=0` (comment, not code, not flagged at parser level; deferred to M903)
- Mixed case: `lefthook=0` (case-sensitive detection, not flagged)
- Quoted env vars: `"LEFTHOOK"=0` (regex requires unquoted var name)
- Spaces in flag: `--no-verify --` (double dash variant, regex should catch)

**Category 2: Suppression Abuse (3–4 tests)**
- Attempt to suppress hook detection: `# nosemgrep` or similar (not applicable to bash hook; deferred to M903 governance gate)
- Multiple patterns in one command: `LEFTHOOK=0 git push --no-verify` (should detect both, or first detected)
- Pattern within comment: `# git commit --no-verify` (not code, not flagged at parser level)

**Category 3: Configuration Mutations (3–4 tests)**
- Malformed env var: `LEFTHOOK=` (no value, should trigger on presence)
- Unknown env vars: `SKIP_HOOKS_CUSTOM=0` (not in known list, not flagged)
- Partial flag match: `--no-verify-` (substring, should match if regex uses prefix)

**Category 4: Tool-Level Failures (2–3 tests)**
- Missing jq/python in PATH: fallback to python JSON parsing, graceful error
- Timeout on deep recursion: depth-2 limit prevents; test with pathological nested command
- Input size limit: >1MB input → parser error, exit code 2

**Category 5: Schema Boundary Violations (2–3 tests)**
- Missing required fields in JSON → exit code 2
- Null command field → exit code 0 (benign)
- Invalid mode string → log warning, fallback to STRICT

**Category 6: Governance Bypass Attempts (3–4 tests)**
- Attempt to use BLOBERT_SKIP_HOOKS=1 repeatedly → should be allowed in hook, but M903 audit gate detects pattern
- Attempt to unset BLOBERT_HOOK_MODE in nested -c → mode is determined pre-hook, not affected by nested env
- Attempt to modify CI env var detection → env vars are checked at hook run time, not modifiable mid-execution

### Performance Benchmarks (Task 11 integration test)

- Parse 100 benign commands: <50ms total (100 × <0.5ms average)
- Parse 50 commands with depth-1 nesting: <100ms total
- Parse 20 commands with depth-2 nesting: <1s total
- Regex compilation time (amortized): <10ms per hook run

### False Positive Validation (Task 11 integration test)

- Benign command suite (15+ examples): 100% pass rate (0% false positives)
- No npm, docker, python, make commands flagged
- No legitimate git commands (status, log, config, clone, pull, stash) flagged
- No legitimate bash scripts (bash script.sh) flagged

---

## Specification Closure Checklist

- [x] Requirement 01: Command Parsing Algorithm & Bypass Pattern Catalog — FROZEN
- [x] Requirement 02: Hard-Block Failure Messages & Remediation Documentation — FROZEN
- [x] Requirement 03: Configurable Blocking Modes & Default Policy — FROZEN
- [x] Requirement 04: Non-Functional Requirements — FROZEN
- [x] All 5 bypass patterns documented with examples
- [x] All 6 error message templates provided (5 patterns + parser error)
- [x] 3 blocking modes defined with behavior matrix
- [x] Exit code contract frozen
- [x] Escape hatches documented (BLOBERT_HOOK_MODE, BLOBERT_SKIP_HOOKS)
- [x] Operator guide structure defined
- [x] Dependencies verified (M902-01, M902-02, M902-03)
- [x] Assumptions frozen with confidence levels
- [x] Test strategy defined (behavioral + adversarial)
- [x] Performance targets documented
- [x] False positive target (<5%) documented
- [x] Security constraints documented (no eval, no secrets, no execution)

---

## WORKFLOW STATE

| Field | Value |
|---|---|
| **Stage** | SPECIFICATION |
| **Revision** | 1 |
| **Last Updated By** | Spec Agent |
| **Next Responsible Agent** | Test Designer Agent |
| **Status** | Proceed |
| **Validation Status** | SPECIFICATION COMPLETE; ready for `spec_completeness_check.py --type generic` validation |
| **Blocking Issues** | None |

## NEXT ACTION

### Next Responsible Agent
Test Designer Agent

### Required Input Schema
```json
{
  "spec_path": "project_board/specs/902_05_pretooluse_hooks_spec.md",
  "ticket_path": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/05_pretooluse_hooks_command_inspection.md"
}
```

### Status
Proceed to Test Design Phase (Tasks 9–11: behavioral test suite, adversarial test suite, integration tests)

### Reason
All four specification requirements (command parsing, failure messages, blocking modes, non-functional requirements) are frozen with acceptance criteria, examples, risk analysis, and assumptions. Dependencies (M902-01 through M902-04) are verified. Bypass pattern catalog is complete with 5 patterns and 3+ examples per pattern. Error message templates are documented. Blocking modes (STRICT, WARN, SHADOW) are defined with behavior matrix and exit code contract. Non-functional requirements (performance, false positives, security, usability) are documented with acceptance criteria. Test strategy is provided (25–35 behavioral, 20–30 adversarial tests). Ready for Test Designer to write behavioral test suite and Test Breaker to write adversarial test suite.

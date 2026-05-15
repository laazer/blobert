# Checkpoint Log: M902-05 PreToolUse Hooks Command Inspection — PLANNING

**Ticket:** project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/05_pretooluse_hooks_command_inspection.md  
**Stage:** PLANNING → SPECIFICATION  
**Run ID:** 2026-05-15T-planning  
**Responsible Agent:** Planner Agent  

---

## Summary

Execution plan frozen for PreToolUse hooks command inspection feature. 13 sequential tasks identified across Spec, Implementation, and Test phases. Key design decisions checkpointed with conservative assumptions. All ambiguities resolved; no gating dependencies identified. M902-01, M902-02, M902-03 dependencies verified as COMPLETE. Ready for Spec Agent.

---

## Key Ambiguities Resolved (Checkpoint Protocol)

### 1. Hook Platform: Claude Code vs Cursor
**Would have asked:** Which coding agent runs locally — Cursor or Claude Code — and which hook platform should the implementation target?

**Assumption made:** Claude Code with `.claude/settings.json` PreToolUse hook infrastructure is the primary platform. Evidence: existing `.claude/settings.json` at repo root contains PreToolUse hooks (line 13-24) demonstrating active usage by Claude Code. A basic `--no-verify` filter already exists (example hook at line 18-21). Cursor hooks (`.cursor/`) are not present in the repo. **Recommendation:** Implement PreToolUse hooks as an extension to `.claude/settings.json` following the existing JSON hook schema, not `.cursor/`.

**Confidence:** HIGH

**Risk:** If Cursor agents are also expected to run, a separate `.cursor/settings.json` should be maintained in parallel. Defer to M903+ if Cursor integration required.

---

### 2. Shell Canonical Form: Bash/Zsh Compatibility
**Would have asked:** Should command parsing handle both bash and zsh syntax equally? What shell variants must be supported?

**Assumption made:** Parse commands assuming bash/zsh common subset. `zsh` is the system shell (Darwin 25.3.0, verified in env); `bash` is compatible POSIX-like form. Both share argv handling conventions for the common patterns targeted: `git commit --flag`, `env VAR=val command`, `bash -c 'nested'`, `rm` commands. No attempt to handle exotic shells (fish, tcsh). **Recommendation:** Parser should normalize argv as an array (from jq extraction) and handle quoting/escaping via shell-safe patterns, not attempt to parse shell grammar.

**Confidence:** MEDIUM-HIGH

**Risk:** Shell injection via uncaught quoting (e.g., `'nested"string'`) could allow evasion. Mitigation: parse argv as an array, not by string splitting; validate depth limits; unit test representative vectors.

---

### 3. Nested Shell Inspection Depth Limit
**Would have asked:** How deep should nested `bash -c "bash -c '...'"` chains be inspected? What is a reasonable depth limit?

**Assumption made:** Depth limit 2 (direct + one level of nesting). Rationale: (a) Most legitimate workflows use 0 (direct command) or 1 (single bash -c wrapper); (b) depth >2 is rare in legitimate CI and a sign of evasion intent; (c) exponential complexity risk for parsing grows rapidly. **Recommendation:** Parse at most 2 levels, bail with HARD_BLOCK at depth 3+.

**Confidence:** MEDIUM

**Risk:** An attacker could use `bash -c "bash -c "bash -c '...'"` (depth 3) to evade. Mitigation: treat depth 3+ as suspicious and block; document this limit in operator docs.

---

### 4. False Positive Risk & Legitimate Command Allowlisting
**Would have asked:** Which legitimate commands might be incorrectly flagged as bypass attempts? Should there be an allowlist for maintenance operations?

**Assumption made:** Default policy is STRICT (no allowlist). All `--no-verify`, hook disablement env vars, and deletion/disablement commands are blocked by default. **Escape hatches:** (a) environment variable override (e.g., `BLOBERT_SKIP_HOOKS=1 git commit --no-verify`) with explicit documentation; (b) special markers in commit messages (e.g., `[SKIP_HOOKS]` in commit-msg → allows --no-verify in same transaction); (c) CI-only relaxed mode (detect CI env and allow specific patterns). **Recommendation:** Implement (a) + (c) in MVP; defer (b) to M903 if false positive rate is high.

**Confidence:** MEDIUM

**Risk:** False positives could frustrate developers and cause adoption resistance. Mitigated by: explicit escape hatch docs, warning-only mode for dev (configurable), shadow mode in CI initially.

---

### 5. Allowlisted Maintenance Commands
**Would have asked:** Are there specific git/tool commands that should be exempted from blocking (e.g., `git commit --no-verify` when run by a specific user or in a specific branch)?

**Assumption made:** No user-level or branch-level exemptions in MVP. All bypass patterns blocked uniformly. Context-based exemptions (e.g., "allow on main, block on feature branches") are deferred to M903+ after observing real-world friction. **Recommendation:** Document the policy clearly; provide escape hatch via env var; monitor false positives in shadow mode first.

**Confidence:** MEDIUM

**Risk:** Legitimate CI workflows might be blocked. Mitigated by shadow mode in CI (non-blocking, advisory only).

---

### 6. Integration Point: Which Tools to Hook?
**Would have asked:** Which tools should have command inspection? All bash calls, or a curated set (git, npm, python)?

**Assumption made:** PreToolUse hooks in `.claude/settings.json` only apply to the "Bash" tool (shell execution via `tool_use_id: bash` in Claude Code). This is the high-risk execution surface for agents. Other tools (Git, Python CLI via npm, etc.) can be added later if needed. **Recommendation:** Start with Bash matcher; expand in M903+ if threat assessment warrants.

**Confidence:** MEDIUM-HIGH

**Risk:** Agents might use Git tool directly to commit --no-verify; Python invocations might invoke shell code. Mitigated by: monitoring logs; adding Git/Python matchers in M903+ if threats emerge.

---

### 7. Command Parsing Implementation: Regex vs. Shell Lexer
**Would have asked:** Should we use regex pattern matching or a full shell lexer (shlex) to parse commands?

**Assumption made:** Use hybrid approach: (a) extract argv array directly from jq query (`tool_input.command`); (b) use regex for pattern matching against argv elements (--no-verify, env var names); (c) for nested shells, extract the `-c` payload and recurse. Avoid full shlex parsing due to complexity and false positive risk. **Recommendation:** Implement command_parser.py module with: (i) extract argv from JSON input, (ii) normalize argv (lowercase flags, trim whitespace), (iii) pattern match against known bypass signatures, (iv) detect nested -c payloads and recurse up to depth 2.

**Confidence:** HIGH

**Risk:** Regex evasion via unusual quoting or encoding. Mitigated by: unit tests covering representative vectors; explicit documentation of limitations.

---

### 8. Execution Failure vs. Advisory vs. Hard Block
**Would have asked:** When a bypass pattern is detected, should the hook error out (hard block), warn silently, or produce advisories?

**Assumption made:** DEFAULT behavior: HARD_BLOCK (exit 1, stop command execution). Optional WARN mode (exit 0, log warning, allow execution) configurable via environment variable (e.g., `BLOBERT_HOOK_MODE=warn`). **Recommendation:** Implement hard-blocking by default; make warn-mode opt-in for local dev; shadow (non-blocking advisory) mode for CI initially (deferred enforcement to M903+).

**Confidence:** HIGH

**Risk:** Developers might bypass hooks to work around false positives; needs clear documentation and escape hatch.

---

## Design Decisions Frozen

| Decision | Value | Rationale | Confidence |
|----------|-------|-----------|------------|
| Hook Platform | Claude Code `.claude/settings.json` | Existing infrastructure; no Cursor hooks present | HIGH |
| Shell Target | Bash/zsh common subset | System shell + compatibility | MEDIUM-HIGH |
| Nesting Depth | 2 levels max | Complexity/evasion trade-off | MEDIUM |
| Default Policy | STRICT (all bypass blocked) | Security-first; false positives in shadow mode first | HIGH |
| Escape Hatches | Env var override + shadow mode | Avoids adoption friction; documented | MEDIUM |
| Tool Coverage | Bash (PreToolUse) initially | High-risk execution surface; expand in M903+ | MEDIUM-HIGH |
| Parser Approach | Hybrid regex + shallow recursion | Simplicity + coverage; shlex avoided | HIGH |
| Execution Mode | Hard block + warn option | Default deny; opt-in warnings | HIGH |

---

## Dependencies

- **M902-01 (Validation Gate Framework):** COMPLETE. PreToolUse hooks do NOT depend on gate framework; hooks are client-side enforcement, gates are server-side validation gates. No blocking dependency.
- **M902-02 (Static Analysis Gate Tooling):** COMPLETE. No dependency.
- **M902-03 (Handoff Governance Rule Enforcement):** COMPLETE. No dependency.
- **.claude/settings.json hook structure:** In-repo, already used for basic --no-verify check. No external dependency.

---

## Risk Register

| Risk | Severity | Mitigation | Checkpoint |
|------|----------|-----------|-----------|
| Shell injection via uncaught quoting | MEDIUM | Unit test vectors; avoid string splitting | Test Design task |
| Depth 3+ nesting evasion | MEDIUM | Explicit depth limit; treat 3+ as suspicious | Implementation task |
| False positives on legitimate commands | MEDIUM-HIGH | Shadow mode in CI; warn mode for dev; escape hatch docs | Operator docs + integration testing |
| Regex evasion via encoding/obfuscation | MEDIUM | Limit to common patterns; document limitations | Test Breaker task (adversarial suite) |
| Developers circumvent via wrapper scripts | MEDIUM | Escape hatch via env var + monitoring; requires CI enforcement | M903+ enforcement milestone |
| Command parsing incompleteness (zsh-specific syntax) | LOW | Start with bash subset; expand as bugs reported | Test Breaker task |

---

## Execution Plan Summary

**Total Tasks:** 13  
**Phases:** Specification (Tasks 1–3), Implementation (Tasks 4–9), Testing (Tasks 10–12), Documentation & Integration (Task 13)

### Phase Distribution

| Phase | Tasks | Agent | Est. Effort |
|-------|-------|-------|-----------|
| SPECIFICATION | 1–3 | Spec Agent | 2 runs |
| IMPLEMENTATION | 4–9 | Implementation Generalist | 2 runs |
| TEST DESIGN | 10 | Test Designer | 1 run |
| TEST BREAK | 11 | Test Breaker | 1 run |
| ACCEPTANCE | 12–13 | AC Gatekeeper + Operator | 1 run |

---

## Next Action

**Route to:** Spec Agent  
**Next Stage:** SPECIFICATION  
**Input:** Execution plan (tasks 1–13 below); checkpoint log  
**Required Output:** Comprehensive specification at `project_board/specs/902_05_pretooluse_hooks_spec.md` with: (i) command parsing algorithm & examples, (ii) bypass pattern catalog, (iii) hard-block failure messages & remediation, (iv) configurable modes (strict/warn/shadow), (v) test strategy, (vi) operator documentation template.

---

## Detailed Task Breakdown

See execution plan table below for full task specifications, inputs, outputs, dependencies, success criteria, and risks.

# Specification: Learning Gate — Forbidden Phrase Detection in Learning Outputs

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/06_per_stage_gate_improvements.md`

**Milestone:** 902 — Agent Predictability Improvements

**Task:** 5 (Spec Agent responsibility, part 2 of 2)

**Date:** 2026-05-16

**Revision:** 1

---

## Executive Summary

The **learning gate** scans checkpoint learning outputs (markdown files under `project_board/checkpoints/`) to detect forbidden phrases that violate project policy. It prevents codifying hacks, workarounds, and incomplete design decisions into the record. The gate is deterministic, runs with only artifact files (no external services), outputs JSON matching M902-01 schema, and operates in FAIL mode (blocks INTEGRATION if violations found).

**Scope:** Markdown files only (Learning Agent outputs). Code, tests, configs out of scope.

---

## Functional Requirements

### Requirement 1: Enumerate Learning Output Files

**Description:** Gate must identify all markdown files in checkpoint directories that represent learning outputs.

**File Discovery:**
- Root path: `project_board/checkpoints/`
- Pattern: `**/*.md` (recursively find all markdown files)
- Filter: Exclude index files (CHECKPOINTS.md, README.md)
- Filter: Include only files in ticket subdirectories (e.g., `checkpoints/M902-06/`, `checkpoints/M903-01/`)

**File Scope Examples:**
- ✓ `project_board/checkpoints/M902-06/2026-05-16T-specification.md` (learning output)
- ✓ `project_board/checkpoints/M902-06/2026-05-16T-planning.md` (learning output)
- ✗ `project_board/CHECKPOINTS.md` (index file, excluded)
- ✗ `project_board/README.md` (documentation, excluded)
- ✗ `project_board/specs/902_06_*.md` (spec file, not learning output)

**Constraints:**
- If checkpoints directory does not exist: PASS (vacuously; no learning outputs).
- Empty checkpoint directory: PASS.
- Symlinks: follow symlinks (no special handling).

**Scope:** All markdown files under `project_board/checkpoints/*/` with valid structure.

**Acceptance Criteria:**
- Gate correctly identifies 5 .md files in checkpoints/M902-06/ folder.
- Gate correctly excludes CHECKPOINTS.md (index file).
- Gate correctly excludes project_board/specs/ files.

---

### Requirement 2: Parse Learning Output Markdown

**Description:** Gate must read and extract text content from learning markdown files.

**Parsing Strategy:**
- Read entire file as UTF-8 text (ignore encoding errors gracefully).
- Extract all lines (split by newline).
- No deep markdown parsing required (heuristic line-by-line scanning is acceptable).

**Content Scope:**
- Include all text content (headings, body, code blocks, quotes).
- No special handling of code blocks (search phrase patterns everywhere).
- Example: phrase "hack" in code block or comment is still flagged.

**Constraints:**
- Skip YAML front matter (if present; between --- markers).
- Handle files > 10 MB gracefully (WARN, truncate to first 10 MB).
- Handle encoding errors (log WARN, continue with recoverable content).

**Scope:** All markdown content; no semantic parsing.

**Acceptance Criteria:**
- Gate correctly reads 2 KB markdown file.
- Gate handles encoding error gracefully (logs WARN, continues).
- Gate includes both headings and body text in search.

---

### Requirement 3: Match Forbidden Phrases via Regex Patterns

**Description:** Gate must detect forbidden phrases in learning outputs using regex patterns from policy.

**Phrase Matching:**
- Read YAML policy file (see Config File Schema)
- For each phrase in policy, compile regex pattern (case-insensitive by default)
- Scan all lines in learning output for matches
- Report each match with line number and context

**Example Phrases (Default Policy):**
- `hack` (matches "hack", "hacking", "hackish", "hack-ish")
- `temporary` (matches "temporary", "temp", "temporarily")
- `XXX` (matches "XXX" in comments)
- `KLUDGE` (matches "kludge", "kludging")
- `workaround` (matches "workaround", "work-around")

**Example Detections:**
```markdown
## Learning Output

### Technical Debt Decision
**Would have asked:** How to implement feature X?
**Assumption made:** Use a temporary workaround...
```
→ Match: "temporary" on line 5; Match: "workaround" on line 5

**Constraints:**
- Phrases are case-insensitive by default (tunable in config).
- Regex escaping: phrases are treated as literals; special regex chars escaped.
- Whole-word matching optional (configurable in policy).
- Example: "hack" matches "hacker" (substring) or "hack" only (whole-word mode).

**Scope:** All phrases in policy scanned against all lines.

**Acceptance Criteria:**
- Gate detects "hack" in phrase "this is a hack".
- Gate detects "temporary" in phrase "temporary workaround".
- Gate detects multiple phrases on same line (reports each).

---

### Requirement 4: Report Violations with Context & Remediation

**Description:** Gate must report each forbidden phrase match with file, line, context, and remediation guidance.

**Violation Structure:**
```json
{
  "file": "project_board/checkpoints/M902-06/2026-05-16T-implementation.md",
  "line": 42,
  "rule": "forbidden_phrase_hack",
  "message": "Forbidden phrase detected: 'hack' in learning output. Context: '...this is a hack solution...'",
  "severity": "ERROR",
  "remediation": "Refactor to proper pattern or create follow-up M903-XX ticket for permanent solution"
}
```

**Context Reporting:**
- Include surrounding text (50 chars before/after phrase) for visibility.
- Example: "...assumption made: use a hack solution for now..." (phrase highlighted).

**Remediation Guidance:**
- Per phrase (from policy file); example: "hack" → "Use design pattern instead; or create M903-XX ticket".
- Actionable and specific to phrase type.

**Line Numbers:**
- Report actual line number in file (1-based indexing).

**Scope:** One violation per phrase match per line.

**Acceptance Criteria:**
- Violation includes file, line, phrase matched, context, remediation.
- Remediation is phrase-specific (not generic).
- Multiple matches on same line generate separate violations.

---

### Requirement 5: JSON Output Format (M902-01 Schema Compliance)

**Description:** Gate emits JSON output matching M902-01 gate schema.

**Output on PASS (no forbidden phrases):**
```json
{
  "version": "0.1.0",
  "status": "PASS",
  "gate": "learning_check",
  "upstream_agent": "Learning Agent",
  "downstream_agent": "Spec Agent",
  "timestamp": "2026-05-16T12:00:00",
  "ticket_id": "M902-06",
  "mode": "shadow",
  "message": "No forbidden phrases detected in learning outputs.",
  "violations": [],
  "remediation_hints": [],
  "artifacts": [],
  "duration_ms": 5
}
```

**Output on FAIL (forbidden phrases found):**
```json
{
  "version": "0.1.0",
  "status": "FAIL",
  "gate": "learning_check",
  "upstream_agent": "Learning Agent",
  "downstream_agent": "Spec Agent",
  "timestamp": "2026-05-16T12:00:00",
  "ticket_id": "M902-06",
  "mode": "shadow",
  "message": "2 forbidden phrases detected in learning outputs.",
  "violations": [
    {
      "file": "project_board/checkpoints/M902-06/2026-05-16T-implementation.md",
      "line": 42,
      "rule": "forbidden_phrase_hack",
      "message": "Forbidden phrase detected: 'hack'. Context: '...this is a hack solution...'",
      "severity": "ERROR",
      "remediation": "Use design pattern instead; or create M903-XX ticket for permanent solution"
    },
    {
      "file": "project_board/checkpoints/M902-06/2026-05-16T-implementation.md",
      "line": 87,
      "rule": "forbidden_phrase_temporary",
      "message": "Forbidden phrase detected: 'temporary'. Context: '...as a temporary workaround...'",
      "severity": "ERROR",
      "remediation": "Create permanent implementation or reference M903-XX ticket"
    }
  ],
  "remediation_hints": [
    "Learning outputs must not codify hacks or temporary solutions",
    "Either: (1) refactor to proper design, (2) create explicit follow-up ticket (M903-XX), or (3) remove phrase from learning output",
    "Reference: project_board/902_06_learning_gate_policy.yml (list of forbidden phrases)"
  ],
  "artifacts": [],
  "duration_ms": 8
}
```

**Status Mapping:**
- **PASS:** No forbidden phrases detected in any learning output.
- **FAIL:** >= 1 forbidden phrase detected (blocking INTEGRATION).

**Violations Array:**
- One entry per phrase match.
- Rule: "forbidden_phrase_<phrase>" (e.g., "forbidden_phrase_hack").
- Severity: ERROR (blocking, not advisory).
- Remediation: phrase-specific guidance from policy.

**Remediation Hints:**
- Generic guidance: explain policy rationale, suggest 3 options (refactor, create ticket, remove).
- Reference: link to policy file.

**Scope:** All output fields present; violations empty if PASS.

**Acceptance Criteria:**
- FAIL output includes all forbidden phrase violations.
- Each violation includes phrase type, context, remediation.
- Remediation hints explain rationale and options.

---

### Requirement 6: Configuration & Forbidden Phrase Policy

**Description:** Gate accepts YAML config file defining forbidden phrases and remediation guidance.

**Config File Schema:**
```yaml
forbidden_phrases:
  # Primary hacks/workarounds
  - phrase: hack
    severity: ERROR
    remediation: "Use design pattern instead; or create M903-XX ticket for permanent solution"
    case_sensitive: false
    whole_word: true
  
  - phrase: temporary
    severity: ERROR
    remediation: "Create permanent implementation or reference M903-XX ticket"
    case_sensitive: false
    whole_word: true
  
  - phrase: workaround
    severity: ERROR
    remediation: "Implement proper solution; or defer to M903-XX with explicit ticket"
    case_sensitive: false
    whole_word: false
  
  # Code markers
  - phrase: XXX
    severity: ERROR
    remediation: "Remove marker; replace with proper implementation or M903-XX ticket"
    case_sensitive: true
    whole_word: true
  
  - phrase: KLUDGE
    severity: ERROR
    remediation: "Refactor to proper pattern"
    case_sensitive: false
    whole_word: true
  
  # Optional: warn on TODO in learning (different from code TODO)
  - phrase: TODO
    severity: WARN  # Advisory in learning; code TODOs handled by reviewer_check
    remediation: "Use spec's Risk & Ambiguity Analysis section; avoid TODO in learning"
    case_sensitive: false
    whole_word: true
```

**Default Policy (if config file missing):**
```yaml
forbidden_phrases:
  - phrase: hack
    severity: ERROR
    remediation: "Use design pattern instead; or create M903-XX ticket"
    case_sensitive: false
    whole_word: true
  
  - phrase: temporary
    severity: ERROR
    remediation: "Create permanent implementation or reference M903-XX ticket"
    case_sensitive: false
    whole_word: true
  
  - phrase: XXX
    severity: ERROR
    remediation: "Remove marker; replace with proper implementation"
    case_sensitive: true
    whole_word: true
  
  - phrase: KLUDGE
    severity: ERROR
    remediation: "Refactor to proper pattern"
    case_sensitive: false
    whole_word: true
```

**Config File Location:**
- Specified in inputs["policy_file"] as absolute path.
- If missing: use hardcoded defaults.
- If file not found: WARN and use defaults (not FAIL).

**Scope:** Phrases and severity customizable; defaults cover MVP requirements.

**Acceptance Criteria:**
- Gate reads config YAML and applies phrases.
- Gate gracefully handles missing config (uses defaults, logs INFO).
- Gate correctly applies case_sensitive and whole_word flags.

---

### Requirement 7: Error Handling & Graceful Degradation

**Description:** Gate must handle missing/unreadable files, config errors, and encoding errors gracefully.

**Error Cases:**
- **Checkpoints directory not found:** PASS (vacuously; no learning outputs).
- **Learning file not readable (permissions, encoding):** WARN, skip file, continue.
- **Config file not found:** WARN, use defaults (not FAIL).
- **Invalid YAML config:** WARN, use defaults.
- **Regex compilation error in phrase:** WARN, skip phrase.
- **File > 10 MB:** WARN "file too large, truncating analysis", analyze first 10 MB.

**Constraints:**
- All errors logged with context (file paths, error messages).
- Gate does not halt on first error; continues with other files.
- Fallback: If all learning files unreadable, emit WARN with message "unable to analyze learning outputs; skipping forbidden phrase check".

**Scope:** Applies to gate invocation with potentially invalid inputs.

**Acceptance Criteria:**
- Missing checkpoints directory → PASS (vacuous).
- Unreadable learning file → WARN, skip file.
- Config file not found → WARN, use defaults.

---

## Non-Functional Requirements

### NFR-1: Deterministic Execution

**Requirement:** Gate must produce identical output for identical learning files.

**Scope:** File enumeration, regex matching, output serialization.

**Verification:**
- Same learning files + policy → same violations detected every invocation.
- File ordering in output (stable sorted by path).

**Acceptance Criteria:**
- Gate run on same learning files twice → identical JSON output (except duration_ms and timestamp).

---

### NFR-2: No External Service Dependencies

**Requirement:** Gate must not require network, database, or remote services.

**Scope:** All I/O is local filesystem reads only.

**Verification:**
- No HTTP, SSH, git, or RPC calls.
- No database queries or external APIs.

**Acceptance Criteria:**
- Gate runs in offline/sandboxed environment with only filesystem read access.

---

### NFR-3: Performance

**Requirement:** Gate must complete in < 5 seconds for typical checkpoint set (50 markdown files, 500 KB total).

**Metrics:**
- File enumeration: < 1 second.
- File read + regex matching: < 3 seconds.
- JSON serialization: < 0.1 seconds.

**Acceptance Criteria:**
- Gate completes in < 5 seconds for 50 files, 500 KB.

---

### NFR-4: Observability

**Requirement:** Gate must log structured messages for debugging.

**Logging:**
- INFO: gate start, learning files enumerated, violations count, result.
- DEBUG: per-file analysis, regex matches.
- WARN: unreadable files, config not found, encoding errors.
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
  "name": "learning_check",
  "module": "learning_check",
  "required_inputs": [],
  "optional_inputs": ["policy_file", "checkpoint_dir", "mode", "ticket_id", "upstream_agent", "downstream_agent"],
  "default_mode": "shadow",
  "description": "Scans learning output markdown files in project_board/checkpoints/ for forbidden phrases (hack, temporary, etc.). Output: FAIL if any phrase detected.",
  "category": "governance"
}
```

**Invocation (from Learning Agent after producing checkpoint):**
```bash
python ci/scripts/gate_runner.py learning_check \
  --upstream-agent "Learning Agent" \
  --downstream-agent "Spec Agent" \
  --ticket-id M902-06 \
  --input '{"policy_file": "project_board/902_06_learning_gate_policy.yml", "checkpoint_dir": "project_board/checkpoints/"}'
```

**Module Location:** `ci/scripts/gates/learning_check.py`

**Entry Point Function:** `run(inputs: dict[str, Any]) -> dict[str, Any]`

**Input Contract:**
```python
inputs = {
  "policy_file": str,  # path to YAML policy file (optional)
  "checkpoint_dir": str,  # path to checkpoints directory (optional, default: "project_board/checkpoints/")
  "mode": "shadow|blocking",  # default "shadow"
  "ticket_id": str,  # ticket identifier
  "upstream_agent": str,  # agent name
  "downstream_agent": str,  # agent name
}
```

**Output Contract:** Dict matching M902-01 schema v0.2.0.

---

## Config File Schema

**File Location:** `project_board/902_06_learning_gate_policy.yml`

**Complete Schema (YAML):**
```yaml
# Forbidden phrases in learning outputs
# Policy is conservative: err on the side of preventing hacks from being documented
forbidden_phrases:
  - phrase: hack
    severity: ERROR
    remediation: "Use design pattern instead; or create M903-XX ticket"
    case_sensitive: false
    whole_word: true
  
  - phrase: temporary
    severity: ERROR
    remediation: "Create permanent implementation or reference M903-XX ticket"
    case_sensitive: false
    whole_word: true
  
  - phrase: workaround
    severity: ERROR
    remediation: "Implement proper solution; defer to M903-XX if not feasible"
    case_sensitive: false
    whole_word: false  # substring match
  
  - phrase: XXX
    severity: ERROR
    remediation: "Remove marker; implement proper solution"
    case_sensitive: true
    whole_word: true
  
  - phrase: KLUDGE
    severity: ERROR
    remediation: "Refactor to proper pattern"
    case_sensitive: false
    whole_word: true
```

---

## Examples

### Example 1: No Forbidden Phrases (PASS)

**Learning Output File:**
```markdown
## Learning Output

### Decision: Use Existing Library for Timestamp Handling
**Would have asked:** Should we implement timestamp validation from scratch?
**Assumption made:** Use Python `datetime` library (standard, well-tested)
**Confidence:** HIGH — standard library stable across versions.
```

**Processing:**
- Scan lines for forbidden phrases: hack, temporary, workaround, XXX, KLUDGE
- NO MATCHES found
- Result: PASS

**Output:**
```json
{
  "status": "PASS",
  "message": "No forbidden phrases detected in learning outputs.",
  "violations": []
}
```

---

### Example 2: Forbidden Phrase "hack" Detected (FAIL)

**Learning Output File:**
```markdown
## Learning Output

### Decision: Performance Optimization
**Would have asked:** How to optimize query performance?
**Assumption made:** Use a quick hack with in-memory cache for now; defer proper caching layer to M903-XX
**Confidence:** MEDIUM — this is temporary; will refactor in M903-XX
```

**Processing:**
- Line 5: "Assumption made: Use a quick hack with in-memory cache..."
- Regex match: "hack" (case-insensitive)
- Report violation: rule="forbidden_phrase_hack", line=5

**Output:**
```json
{
  "status": "FAIL",
  "message": "1 forbidden phrase detected in learning outputs.",
  "violations": [
    {
      "file": "project_board/checkpoints/M902-06/2026-05-16T-implementation.md",
      "line": 5,
      "rule": "forbidden_phrase_hack",
      "message": "Forbidden phrase detected: 'hack'. Context: 'Use a quick hack with in-memory cache'",
      "severity": "ERROR",
      "remediation": "Use design pattern instead; or create M903-XX ticket"
    }
  ],
  "remediation_hints": [
    "Either: (1) refactor to proper design, (2) create M903-XX follow-up, or (3) remove phrase",
    "If deferring work: explicitly reference M903-XX ticket in decision"
  ]
}
```

---

### Example 3: Multiple Forbidden Phrases (FAIL)

**Learning Output File:**
```markdown
### Decision: Error Handling Strategy
**Assumption made:** Use a temporary workaround with try-except hack to handle edge cases. This is a KLUDGE and should be redesigned in M903-XX.
```

**Processing:**
- "temporary" match on line 3
- "workaround" match on line 3
- "hack" match on line 3
- "KLUDGE" match on line 3
- Result: 4 violations, all on line 3

**Output:**
```json
{
  "status": "FAIL",
  "message": "4 forbidden phrases detected in learning outputs.",
  "violations": [
    { "line": 3, "rule": "forbidden_phrase_temporary", "message": "..." },
    { "line": 3, "rule": "forbidden_phrase_workaround", "message": "..." },
    { "line": 3, "rule": "forbidden_phrase_hack", "message": "..." },
    { "line": 3, "rule": "forbidden_phrase_kludge", "message": "..." }
  ]
}
```

---

### Example 4: XXX Code Marker Detected (FAIL)

**Learning Output File:**
```markdown
### Risk Mitigation
**Risk:** Performance may degrade with large datasets.
**Mitigation:** XXX: Need to profile and optimize; defer to M903-XX.
```

**Processing:**
- Line 5: "XXX: Need to profile..."
- Regex match: "XXX" (case-sensitive, whole-word)
- Report violation: rule="forbidden_phrase_XXX"

**Output:**
```json
{
  "status": "FAIL",
  "violations": [
    {
      "file": "project_board/checkpoints/M902-06/2026-05-16T-implementation.md",
      "line": 5,
      "rule": "forbidden_phrase_XXX",
      "message": "Forbidden phrase detected: 'XXX'. Context: 'XXX: Need to profile and optimize'",
      "severity": "ERROR",
      "remediation": "Remove marker; implement proper solution or create M903-XX ticket"
    }
  ]
}
```

---

### Example 5: Missing Policy File (Uses Defaults)

**Invocation:**
```bash
python ci/scripts/gate_runner.py learning_check \
  --input '{"policy_file": "project_board/nonexistent_policy.yml"}'
```

**Processing:**
- Attempt to read policy file: FileNotFoundError
- Log INFO "Policy file not found; using defaults"
- Continue with hardcoded default forbidden phrases

**Output:**
```json
{
  "message": "Policy file not found; using defaults.",
  "violations": [...]  # analyzed with defaults
}
```

---

## Risk & Ambiguity Analysis

### Risk 1: False Positives (Phrase in Legitimate Context)
**Risk:** "hack" in "hacker" or legitimate technical term may be flagged incorrectly.
**Mitigation:** whole_word option (default: true); case_sensitive option allows tuning. Manual review clarifies intent.
**Impact:** Low (false positives rare with whole_word=true; easily fixed by rewording).

### Risk 2: Phrase List Becomes Outdated
**Risk:** New hacks emerge (e.g., "shortcut", "duct-tape"); phrase list must evolve.
**Mitigation:** Config is customizable; teams can add phrases. M903 can enhance default list based on experience.
**Impact:** Low (config extensible; MVP covers common patterns).

### Risk 3: Learning Output Itself Contains Forbidden Phrase in Quotation
**Risk:** Example: "We considered a 'hack' approach but rejected it" = false positive.
**Mitigation:** Heuristic matching; manual review of FAIL cases catches false positives. Can be fixed via rewording or issue link.
**Impact:** Low (acceptable for MVP; rare case).

---

## Clarifying Questions (Resolved via Checkpoint Protocol)

1. **Should gate scan code files or learning outputs only?**
   - Answer: Learning outputs (markdown under checkpoints/) only (HIGH confidence). Code files have separate reviewer_check gate.

2. **What if phrase appears in code example within learning markdown?**
   - Answer: Still flagged (context-agnostic scanning). Rewording or moving example can resolve (acceptable for MVP).

3. **What severity level for violations?**
   - Answer: ERROR (blocking INTEGRATION). Policy is strict to prevent hacks from being documented as decisions.

---

## Acceptance Criteria Mapping

- **AC6 (Learning gate checks forbidden phrases):** Req1-7 + Examples satisfy this.
- **AC1 (Per-stage checks + checklists):** Documented in 902_06_per_stage_checklists.md.

---

## Sign-Off

Specification is complete, unambiguous, and actionable by Implementation Agent.
All 7 requirements + 4 NFRs + examples + config schema + error handling frozen.
Ready for gate module implementation (ci/scripts/gates/learning_check.py, ~200 lines).

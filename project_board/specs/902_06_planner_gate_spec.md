# Specification: Planner Gate — Cyclic Dependency Detection

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/06_per_stage_gate_improvements.md`

**Milestone:** 902 — Agent Predictability Improvements

**Task:** 2 (Spec Agent responsibility)

**Date:** 2026-05-16

**Revision:** 1

---

## Executive Summary

The **planner gate** validates ticket dependency graphs to detect cyclic edges that would block workflow progression. It parses machine-readable YAML dependencies fields from milestone ticket files, executes a depth-first search (DFS) algorithm to find cycles, and emits structured JSON output (PASS if acyclic, WARN if cycle detected).

The gate is deterministic, runs with only artifact files (no external services), and integrates with the M902-01 gate framework. All cycle detection is performed at ticket-dependency graph level, not at implementation level.

**Scope:** This gate operates on **planning-phase artifacts only** — ticket markdown files with explicit YAML `dependencies:` fields. Prose references and inferred dependencies are out of scope (MVP).

---

## Functional Requirements

### Requirement 1: Parse Ticket Dependencies from YAML

**Description:** Gate must extract machine-readable dependency lists from ticket markdown files.

**Input Format:** Ticket file contains a YAML-structured `dependencies:` field (see example below).

**Constraints:**
- Field name must be exactly `dependencies:` (case-sensitive).
- Value is a YAML list of ticket IDs (strings).
- Tickets are identified by their short IDs (e.g., `M902-01`, `M903-01`) or full paths.
- If field is missing, treat as zero dependencies (acyclic by definition).
- If YAML is malformed, emit FAIL with detailed error message.

**Assumptions:**
- Ticket IDs are unique within a milestone folder.
- Dependency list refers to tickets in same milestone or higher milestones (no forward references).

**Scope:** All ticket files under `project_board/<milestone>/*/` (backlog, in_progress, done folders).

**Acceptance Criteria:**
- Gate correctly parses `dependencies: [M902-01, M902-02]` as list with 2 items.
- Gate correctly handles empty `dependencies: []` as acyclic.
- Gate correctly rejects `dependencies: invalid yaml` with FAIL + error message.
- Gate correctly identifies missing `dependencies:` field as zero dependencies.

---

### Requirement 2: Build Directed Graph from Dependencies

**Description:** Gate constructs a directed graph where nodes are ticket IDs and edges are dependency relationships.

**Input:** Parsed dependencies lists from all tickets in scope.

**Graph Construction:**
- For each ticket T with dependencies [D1, D2, ...], create edges: T → D1, T → D2, ...
- Semantics: "T depends on D1" means D1 must complete before T can proceed.
- Nodes with no outgoing edges are leaf nodes (no dependencies).
- Nodes with no incoming edges are root nodes (no dependents).

**Constraints:**
- Graph must be representable as adjacency list (dict[ticket_id, list[ticket_id]]).
- Self-loops (T → T) are explicitly forbidden; emit FAIL if detected.
- Isolated nodes (no dependencies, no dependents) are acyclic.

**Scope:** Ticket scope is frozen at gate invocation time (milestone folder specified in inputs).

**Acceptance Criteria:**
- Gate builds graph from 6 tickets with dependencies: M902-01 (no deps), M902-02 (→M902-01), M902-03 (→M902-02), etc.
- Graph is representable as dict with 6 keys and 5 edges.
- Self-loop detection correctly identifies M902-02 → M902-02 as ERROR.

---

### Requirement 3: Detect Cycles via DFS

**Description:** Gate executes depth-first search (DFS) to detect all cycles in the graph.

**Algorithm:**
```
VISITED = set()
REC_STACK = set()
CYCLES = []

function dfs(node, graph, path=[]):
  if node in REC_STACK:
    # Cycle detected; extract cycle from path
    cycle_start = path.index(node)
    cycle = path[cycle_start:] + [node]
    CYCLES.append(cycle)
    return
  if node in VISITED:
    return
  
  VISITED.add(node)
  REC_STACK.add(node)
  path.append(node)
  
  for neighbor in graph[node]:
    dfs(neighbor, graph, path)
  
  REC_STACK.remove(node)
  path.pop()

for node in graph:
  if node not in VISITED:
    dfs(node, graph)
```

**Constraints:**
- DFS must track both VISITED set (completed nodes) and REC_STACK (recursion stack) to distinguish back edges from forward/cross edges.
- All cycles must be reported (not just first detected).
- Cycle reporting format: [ticket_1, ticket_2, ..., ticket_1] (includes endpoint twice for clarity).

**Scope:** DFS operates only on graph nodes reachable from root tickets.

**Acceptance Criteria:**
- Gate correctly identifies acyclic graph with 5 nodes and 4 edges → PASS.
- Gate correctly identifies 2-node cycle (A → B → A) → WARN with cycle=[A, B, A].
- Gate correctly identifies 3-node cycle (A → B → C → A) → WARN with cycle=[A, B, C, A].
- Gate correctly identifies multiple disjoint cycles → WARN with all cycles listed.

---

### Requirement 4: Handle Orphaned & Duplicate Dependencies

**Description:** Gate must handle edge cases in dependency declarations.

**Cases:**
- **Orphaned dependency:** Ticket T lists dependency D, but D does not exist in scope.
  - Action: Emit WARN "Orphaned dependency detected: T → D (D not found)".
  - Continue processing without blocking.
- **Duplicate entries:** Ticket T lists dependency D twice.
  - Action: Deduplicate silently (graph edge de-duped).
- **Transitive dependencies:** Ticket T lists both M902-02 (direct) and M902-01 (which M902-02 already depends on).
  - Action: Accept as-is (no simplification); DFS will not re-traverse already-visited nodes.

**Constraints:**
- Orphaned dependencies must not cause graph construction failure; emit WARN and continue.
- Ticket lookup is case-insensitive (M902-01, m902-01, M902_01 all refer to same ticket).

**Scope:** Applies to all tickets parsed from milestone folder.

**Acceptance Criteria:**
- Gate accepts orphaned dependency D → non-existent-ticket with WARN (no FAIL).
- Gate correctly de-duplicates [M902-01, M902-01] to single edge.
- Gate correctly processes transitive dependencies without infinite loops.

---

### Requirement 5: JSON Output Format (M902-01 Schema Compliance)

**Description:** Gate emits JSON output matching the M902-01 gate schema.

**Output Structure:**
```json
{
  "version": "0.1.0",
  "status": "PASS|WARN|FAIL",
  "gate": "planner_check",
  "upstream_agent": "Planner Agent",
  "downstream_agent": "Spec Agent",
  "timestamp": "2026-05-16T12:00:00",
  "ticket_id": "M902-06",
  "mode": "shadow",
  "violations": [
    {
      "file": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/03_*.md",
      "line": 0,
      "rule": "cyclic_dependency",
      "message": "Cyclic dependency detected: [M902-02, M902-03, M902-02]",
      "severity": "WARN"
    }
  ],
  "remediation_hints": [
    "Break cycle by reordering dependencies or splitting tickets",
    "Ticket M902-03 should not depend on M902-02 if M902-02 depends on M902-03"
  ],
  "artifacts": ["gate-results/planner_check_20260516T120000Z.json"],
  "duration_ms": 15
}
```

**Status Mapping:**
- **PASS:** Graph is acyclic; no orphaned dependencies; no validation errors.
- **WARN:** Graph has cycles OR orphaned dependencies detected; processing continues.
- **FAIL:** YAML parse error; malformed ticket structure; graph construction error.

**Violations Array:**
- Each cycle reported as one violation entry.
- Orphaned dependencies reported as separate violations.
- Self-loops reported as ERROR severity (cyclic_dependency rule).

**Artifacts:**
- Include gate output JSON file path.
- Optionally include dot/graphviz representation of graph for visualization.

**Scope:** All output fields must be present; null/empty arrays acceptable if no violations.

**Acceptance Criteria:**
- Acyclic graph → JSON with status=PASS, violations=[], no remediation hints.
- Cyclic graph → JSON with status=WARN, violations=[{rule: cyclic_dependency, message: cycle list}], remediation hints present.
- YAML error → JSON with status=FAIL, violations=[{rule: yaml_parse, severity: ERROR}].

---

### Requirement 6: Error Handling & Graceful Degradation

**Description:** Gate must handle missing files, encoding errors, and I/O failures gracefully.

**Error Cases:**
- **Missing ticket file:** Ticket referenced in another's dependencies, file not found → WARN, skip file.
- **Unreadable file:** Permission denied, encoding error → FAIL with detailed error message.
- **Empty milestone folder:** No tickets found → PASS (vacuously true, no cycles).
- **Timeout:** git operation or file enumeration timeout → WARN "timeout during file enumeration".

**Constraints:**
- All errors must be logged with file paths and line numbers where applicable.
- No silent failures; all errors reported in JSON violations array.
- Fallback: If graph construction fails, emit WARN with message "unable to construct full dependency graph; cycle detection skipped".

**Scope:** Applies to gate invocation with milestone folder that may have I/O constraints.

**Acceptance Criteria:**
- Missing ticket file → WARN (not FAIL).
- Unreadable file due to permissions → FAIL.
- Empty folder → PASS (vacuously acyclic).
- Timeout after 30 seconds → WARN "timeout during enumeration".

---

## Non-Functional Requirements

### NFR-1: Deterministic Execution

**Requirement:** Gate must produce identical output for identical inputs (no randomness, no external state).

**Scope:** Graph construction, DFS algorithm, output serialization.

**Verification:**
- Same ticket files + dependencies → same cycle detection results.
- DFS algorithm uses stable node ordering (alphabetical ticket IDs) for reproducible traversal.
- JSON output includes no timestamps (except gate-level timestamp in schema).

**Acceptance Criteria:**
- Gate run on M902 milestone twice → identical JSON output (except duration_ms).

---

### NFR-2: No External Service Dependencies

**Requirement:** Gate must not require network calls, external databases, or remote services.

**Scope:** All I/O is local filesystem reads only.

**Verification:**
- No HTTP, SSH, git remote, or RPC calls.
- All graph data is in-memory; no database queries.

**Acceptance Criteria:**
- Gate runs in offline/sandboxed environment with only filesystem access.

---

### NFR-3: Performance

**Requirement:** Gate must complete in < 5 seconds for typical milestone (6-12 tickets).

**Metrics:**
- File enumeration: < 1 second (glob + filter).
- YAML parsing: < 1 second (all files combined).
- DFS algorithm: O(V + E) = O(n^2) worst case for n tickets; < 2 seconds for n=50.
- JSON serialization: < 0.1 seconds.

**Acceptance Criteria:**
- Gate completes in < 5 seconds for 50-ticket milestone.

---

### NFR-4: Observability & Logging

**Requirement:** Gate must emit structured logs for debugging and audit.

**Logging:**
- INFO: gate start, tickets enumerated count, graph size (V, E).
- DEBUG: each ticket parsed, each edge added, DFS progress.
- WARN: orphaned dependencies, malformed YAML, skipped files.
- ERROR: file I/O errors, timeout, exception stack traces.

**Scope:** All logs at module level (logger = logging.getLogger(__name__)).

**Acceptance Criteria:**
- Gate logs at least 3 INFO messages per invocation (start, summary, completion).
- Each cycle detection logs DEBUG message with cycle path.

---

## Integration Notes

### Gate Runner Wiring

**Registry Entry (gate_registry.json):**
```json
{
  "name": "planner_check",
  "module": "planner_check",
  "required_inputs": ["milestone_folder"],
  "optional_inputs": ["mode", "ticket_id", "upstream_agent", "downstream_agent"],
  "default_mode": "shadow",
  "description": "Detects cyclic ticket dependency edges within a milestone via DFS. Input: milestone folder path. Output: PASS if acyclic, WARN if cycles detected.",
  "category": "workflow"
}
```

**Invocation:**
```bash
python ci/scripts/gate_runner.py planner_check \
  --upstream-agent "Planner Agent" \
  --downstream-agent "Spec Agent" \
  --ticket-id M902-06 \
  --input '{"milestone_folder": "project_board/902_milestone_902_agent_predictabilitiy_improvements/"}'
```

**Module Location:** `ci/scripts/gates/planner_check.py`

**Entry Point Function:** `run(inputs: dict[str, Any]) -> dict[str, Any]`

**Input Contract:**
```python
inputs = {
  "milestone_folder": str,  # path to milestone folder (required)
  "mode": "shadow|blocking",  # default "shadow"
  "ticket_id": str,  # ticket identifier
  "upstream_agent": str,  # agent name
  "downstream_agent": str,  # agent name
}
```

**Output Contract:** Dict matching M902-01 schema v0.2.0 with fields: version, status, gate, upstream_agent, downstream_agent, timestamp, ticket_id, mode, violations[], remediation_hints[], artifacts[], duration_ms.

---

## Config File Schema

No config file required; gate behavior is frozen. Future enhancements (M903) may add tuning:
- Maximum cycle length to report (default: report all)
- Severity level for orphaned dependencies (default: WARN)
- DFS timeout (default: 30 seconds)

---

## Examples

### Example 1: Acyclic Dependencies (PASS)

**Input:** Milestone folder with 6 tickets:
```
project_board/902_milestone_902_agent_predictabilitiy_improvements/
├── 01_active/
│   ├── 01_validation_gate_framework.md (dependencies: [])
│   ├── 02_static_analysis_gate_tooling.md (dependencies: [M902-01])
│   ├── 03_handoff_governance_rule_enforcement.md (dependencies: [M902-01, M902-02])
│   ├── 04_handoff_metadata_and_risk_escalation.md (dependencies: [M902-01, M902-02, M902-03])
│   ├── 05_pretooluse_hooks_command_inspection.md (dependencies: [M902-01, M902-04])
│   └── 06_per_stage_gate_improvements.md (dependencies: [M902-01, M902-02, M902-03, M902-04, M902-05])
```

**Graph:**
```
M902-01 → (no dependencies)
M902-02 → M902-01
M902-03 → M902-01, M902-02
M902-04 → M902-01, M902-02, M902-03
M902-05 → M902-01, M902-04
M902-06 → M902-01, M902-02, M902-03, M902-04, M902-05
```

**DFS Traversal:** No back edges encountered; all nodes visited exactly once.

**Output:**
```json
{
  "version": "0.1.0",
  "status": "PASS",
  "gate": "planner_check",
  "message": "No cyclic dependencies detected in milestone.",
  "violations": [],
  "remediation_hints": [],
  "artifacts": [],
  "duration_ms": 12
}
```

---

### Example 2: Cyclic Dependencies (WARN)

**Input:** Milestone folder with problematic dependencies:
```
M902-02: dependencies: [M902-03]
M902-03: dependencies: [M902-02]
```

**Graph:**
```
M902-02 → M902-03
M902-03 → M902-02
```

**DFS Traversal:**
- Start at M902-02: add to VISITED, REC_STACK; visit M902-03
- At M902-03: add to VISITED, REC_STACK; visit M902-02
- M902-02 already in REC_STACK → **cycle detected**: [M902-02, M902-03, M902-02]
- Backtrack; no more neighbors

**Output:**
```json
{
  "version": "0.1.0",
  "status": "WARN",
  "gate": "planner_check",
  "message": "Cyclic dependency detected in milestone.",
  "violations": [
    {
      "file": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/02_static_analysis_gate_tooling.md",
      "line": 0,
      "rule": "cyclic_dependency",
      "message": "Cyclic dependency detected: [M902-02, M902-03, M902-02]",
      "severity": "WARN"
    }
  ],
  "remediation_hints": [
    "Break the cycle by removing one edge: either M902-02 → M902-03 or M902-03 → M902-02",
    "Alternative: Refactor to split one ticket into sub-tasks with clear ordering"
  ],
  "artifacts": [],
  "duration_ms": 8
}
```

---

### Example 3: Three-Node Cycle (WARN)

**Input:** Milestone with 3-node cycle:
```
M902-02: dependencies: [M902-03]
M902-03: dependencies: [M902-04]
M902-04: dependencies: [M902-02]
```

**Graph:**
```
M902-02 → M902-03 → M902-04 → M902-02
```

**DFS Result:** Cycle = [M902-02, M902-03, M902-04, M902-02]

**Output:**
```json
{
  "version": "0.1.0",
  "status": "WARN",
  "gate": "planner_check",
  "violations": [
    {
      "file": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/02_static_analysis_gate_tooling.md",
      "line": 0,
      "rule": "cyclic_dependency",
      "message": "Cyclic dependency detected: [M902-02, M902-03, M902-04, M902-02]",
      "severity": "WARN"
    }
  ],
  "remediation_hints": [
    "Cycle involves 3 tickets: M902-02 → M902-03 → M902-04 → M902-02",
    "Option 1: Remove M902-04 → M902-02 edge (M902-04 depends on M902-02 output)",
    "Option 2: Merge tickets to eliminate cyclic dependency",
    "Option 3: Introduce intermediary milestone boundary"
  ],
  "duration_ms": 10
}
```

---

### Example 4: Orphaned Dependency (WARN)

**Input:** Ticket M902-05 lists dependency M902-99, which does not exist:
```
M902-05: dependencies: [M902-01, M902-99]
```

**Processing:**
- M902-01 found; edge added.
- M902-99 not found in milestone folder.
- Emit WARN "orphaned dependency"; add to violations; continue.

**Output:**
```json
{
  "version": "0.1.0",
  "status": "WARN",
  "gate": "planner_check",
  "violations": [
    {
      "file": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/05_pretooluse_hooks_command_inspection.md",
      "line": 15,
      "rule": "orphaned_dependency",
      "message": "Orphaned dependency: M902-05 → M902-99 (M902-99 not found in milestone)",
      "severity": "WARN"
    }
  ],
  "remediation_hints": [
    "Verify that M902-99 exists in the milestone folder",
    "If M902-99 is in a different milestone, update the dependency reference",
    "If M902-99 is not needed, remove it from the dependencies list"
  ],
  "duration_ms": 9
}
```

---

### Example 5: Malformed YAML (FAIL)

**Input:** Ticket with invalid YAML:
```yaml
dependencies: [M902-01 M902-02]  # Missing comma
```

**Processing:**
- YAML parser raises error: "expected ',' but found 'M'".
- Emit FAIL with error details.

**Output:**
```json
{
  "version": "0.1.0",
  "status": "FAIL",
  "gate": "planner_check",
  "violations": [
    {
      "file": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/06_per_stage_gate_improvements.md",
      "line": 125,
      "rule": "yaml_parse_error",
      "message": "YAML parse error: expected ',' but found 'M' at line 125",
      "severity": "ERROR"
    }
  ],
  "remediation_hints": [
    "Fix YAML syntax: use [M902-01, M902-02] with commas between items",
    "Valid YAML list formats: [item1, item2] or newline-separated with dashes"
  ],
  "duration_ms": 5
}
```

---

## Risk & Ambiguity Analysis

### Risk 1: Ticket ID Normalization
**Risk:** Ticket IDs may be referenced in different formats (M902-01, m902-01, M902_01).
**Mitigation:** Normalize to uppercase; treat `-`, `_`, no-separator variants as equivalent.
**Impact:** Low (handles edge case gracefully).

### Risk 2: Transitive Dependency Chains
**Risk:** Long dependency chains (A→B→C→D) may cause DFS to be inefficient.
**Mitigation:** DFS is O(V+E); acceptable for < 50 tickets. If performance degrades, optimize graph traversal (not in MVP).
**Impact:** Low (acceptable performance for MVP scope).

### Risk 3: Orphaned Dependencies Not Causing Failure
**Risk:** Typos in dependency references (M902-99 instead of M902-09) may not be caught immediately.
**Mitigation:** WARN emitted; manual review during planning stage catches most errors.
**Impact:** Medium (typos can cause confusion; but WARN is sufficient for MVP).

### Risk 4: Multiple Cycles in Graph
**Risk:** Graph with multiple disjoint cycles requires reporting all cycles; algorithm complexity may increase.
**Mitigation:** DFS traverses all nodes; all back edges are reported. No exponential blowup.
**Impact:** Low (algorithm handles multiple cycles correctly).

---

## Clarifying Questions (Resolved via Checkpoint Protocol)

1. **Should cycle detection traverse only explicit YAML deps or infer from prose?**
   - Answer: Only explicit YAML `dependencies:` field (HIGH confidence). Prose references are not machine-readable and out of scope for MVP.

2. **What if a ticket is in backlog vs in_progress vs done?**
   - Answer: All folder states are included in scope; graph is built from all tickets in milestone.

3. **What is acceptable status for orphaned dependencies?**
   - Answer: WARN (non-blocking). Manual review during planning catches most errors.

4. **Should the gate block workflow progression?**
   - Answer: No (MVP shadow mode). WARN is advisory. M903 may add blocking enforcement.

---

## Acceptance Criteria Mapping

- **AC2 (Planner gate can detect cyclic deps):** Req1-6 + Examples 2-5 satisfy this.
- **AC1 (Per-stage checks + checklists):** Checklist documented in 902_06_per_stage_checklists.md.
- **Integration:** Gate module wired into gate_runner.py via gate_registry.json.

---

## Sign-Off

Specification is complete, unambiguous, and actionable by Implementation Agent (Tasks 6–8).
All 6 requirements + 4 NFRs + examples + error handling frozen.
Ready for gate module implementation (ci/scripts/gates/planner_check.py).

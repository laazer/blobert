# Deferred Work Protocol

**Status:** ADOPTED (from M902-18 learnings)  
**Effective:** 2026-05-18  
**Applies to:** All agents in autopilot pipeline

---

## The Problem

When an agent defers work (AC, implementation, testing) to a future task, that deferred work is **invisible to the downstream task** unless explicitly documented in the downstream ticket.

**Example (from M902-18):**
- M902-18 AC-4, AC-5 are deferred to "Task 5 (Integration Agent)"
- But "Task 5" is documented in M902-18's execution plan and checkpoints
- M902-09–M902-17 active tickets have no idea they have inherited work
- M902-19 backlog ticket doesn't know M902-18 framework integration is a prerequisite

**Result:** Downstream tasks proceed without knowing they're blocked or have dependencies.

---

## The Rule (Mandatory)

**When any agent defers work to a future task, BOTH tickets must be updated immediately.**

### Pattern: Upstream Task (M902-18)

In the ticket's WORKFLOW STATE and NEXT ACTION, **document what's deferred and why:**

```markdown
## Blocking Issues
AC-4, AC-5, AC-7, AC-8 are not satisfied in this phase because they require 
architectural dependencies (framework integration, live agent testing, runbook updates).
These are correctly sequenced as downstream tasks (Task 5, Task 7 per execution plan).
Not a blocker; design is intentional.

---

# NEXT ACTION

## Next Responsible Agent
Integration Agent (Task 5: Framework Integration)

## Required Input
- ticket_path: M902-18 ticket
- implementation_checkpoint: project_board/checkpoints/M902-18/2026-05-18T-implementation.md
- spec_path: project_board/specs/902_18_tool_categorization_spec.md
- [List files that are ready to be integrated]

## Status
**Proceed to Task 5.**

**Framework Integration Prerequisite:** Before M902-19 (and all downstream tasks) can proceed, 
Task 5 must complete framework wiring. See INTEGRATION_GUIDE.md for details.
```

### Pattern: Downstream Task (M902-19)

In the ticket's DEPENDENCIES section, **document what's deferred from upstream:**

```markdown
## Dependencies & Integration Notes

### M902-18 Framework Integration (BLOCKER) ⚠️

M902-18 (Tool Categorization Layer) provides backend implementation (ready now in ci/scripts/).
However, **framework integration (AC-4, AC-5) MUST complete before M902-19 implementation begins.**

**Current Status:**
- M902-18 backend: ✅ COMPLETE (180 tests passing)
- M902-18 framework integration (Task 5): ⏳ PENDING

**You are blocked until Task 5 completes.**

See: project_board/checkpoints/M902-18/INTEGRATION_GUIDE.md

**Before starting M902-19 implementation:**
1. Verify Task 5 has completed framework wiring
2. Confirm agents can declare tool categories: "I declare tool category: parse"
3. Verify `get_tools_for_category()` is callable from agent context
```

---

## Execution Pattern (For Orchestrator)

When autopilot processes a ticket and an agent defers work:

1. **Deferral occurs** (e.g., AC Gatekeeper defers AC-4, AC-5 to Task 5)
2. **Upstream ticket is updated** by the agent (documented above)
3. **Orchestrator checks:** Is a downstream ticket in in_progress/ or backlog/ that needs to know about this?
4. **Downstream ticket is updated** by orchestrator with explicit cross-reference
5. **Integration guide is created** (if distributed work across 3+ phases)
6. **Index is updated** (CHECKPOINTS.md, DEPENDENCIES.md, or similar)

---

## Integration Guide Template

For distributed work (backend + framework + live testing), create `INTEGRATION_GUIDE.md` in the checkpoint directory:

```markdown
# M902-XX Integration Guide

## For Task Y (Next Downstream Task)

Your job: [one sentence]

### What You're Integrating With
- [List files that are ready]
- [Spec sections to read]
- [Checkpoint references]

### What You Need to Do
1. [Step 1]
2. [Step 2]
...

### Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## For M902-ZZ+ (Later Backlog)

**Wait for Task Y to complete before starting.**

### What You Can Do Now
- [Preparatory work]

### What You Can't Do Yet
- [Blocked by Task Y]

### When Unblocked
[What becomes possible after Task Y]
```

---

## Checklist: Ensuring Downstream Awareness

Use this checklist when an agent defers work:

- [ ] **Upstream ticket updated** with explicit "deferred to Task X" and checkpoint reference
- [ ] **Downstream ticket identified** (Task X, M902-ZZ, etc.)
- [ ] **Downstream ticket updated** with explicit "depends on Task X" and upstream reference
- [ ] **CHECKPOINTS.md updated** with dependency pointer
- [ ] **Integration guide created** (if 3+ phases of work)
- [ ] **Bidirectional pointers verified:** upstream → downstream AND downstream → upstream
- [ ] **Next responsible agent clearly named** with file paths and requirements

---

## Examples

### Good (M902-18 → Task 5)
✅ M902-18 ticket NEXT ACTION explicitly names "Integration Agent (Task 5)" with file paths  
✅ M902-19 ticket DEPENDENCIES section explicitly references M902-18 framework integration blocker  
✅ INTEGRATION_GUIDE.md created at `project_board/checkpoints/M902-18/INTEGRATION_GUIDE.md`  
✅ CHECKPOINTS.md updated with "Dependency Flag: M902-19 has explicit cross-reference"

### Bad (Hypothetical)
❌ M902-18 defers work to "Task 5" but doesn't update M902-18 NEXT ACTION with task name  
❌ M902-19 has no DEPENDENCIES section; no cross-reference to M902-18  
❌ Task 5 work is only documented in M902-18 execution plan checkpoint  
❌ M902-19 proceeds unaware of blocker and discovers it only when it fails to import tool_category_manager

---

## For Agents (Prompt Inclusion)

**Add to relevant agent instructions:**

### Spec Agent
When deferring SDK/framework dependencies to Implementation or Integration Agent:
```
When you defer work to downstream agents/tasks, you must also update the 
downstream ticket's description with an explicit DEPENDENCIES section. Include:
1. What is deferred from this spec
2. Why (external dependency, architectural sequencing, etc.)
3. Where to find implementation (checkpoint path, spec path)
4. Integration guide link if available
Do not leave downstream tasks guessing.
```

### AC Gatekeeper
When deferring ACs to future tasks due to architectural dependencies:
```
When setting Stage to INTEGRATION/BLOCKED due to deferred ACs, immediately 
identify downstream tickets that inherit this work. Update their DEPENDENCIES 
section with:
1. What AC is deferred from upstream (M902-18 AC-4, AC-5)
2. Why (framework integration is architectural dependency)
3. Checkpoint and spec paths for context
4. Integration guide path
This ensures downstream agents know they're blocked and why.
```

### Orchestrator (autopilot/ap-continue)
After any stage where work is deferred:
```
After any agent defers work to another task, verify that the downstream 
ticket (if it exists in backlog or in_progress) has been explicitly updated 
with the deferred requirement. If not, update it now to create bidirectional 
pointers. This prevents invisible dependencies.
```

---

## Enforcement

**This protocol is mandatory for all tickets with deferred work.**

Violations (deferred work not reflected in downstream tickets) are findings for:
- AC Gatekeeper review
- Learning extraction
- Future ticket planning

---

## Related Learning

See: `project_board/LEARNINGS.md` → M902-18 → "Deferred Work Requires Explicit Downstream Ticket Updates"

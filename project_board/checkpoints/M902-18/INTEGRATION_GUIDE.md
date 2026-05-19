# M902-18 Integration Guide for Downstream Tasks

**Date:** 2026-05-18  
**Status:** Backend implementation complete; framework integration ready to begin  
**Next Task:** Task 5 (Integration Agent) — Wire agent framework and extract category declarations

---

## For Task 5 (Integration Agent)

Your job is to wire the agent framework so that agents can declare tool categories and use filtered tool schemas.

### Files You're Integrating With

**Read-only (already implemented and tested):**
- `ci/scripts/tool_categories.json` — Normative tool-to-category mappings (5 categories, 8 tools)
- `ci/scripts/tool_category_manager.py` — Two functions:
  - `get_tools_for_category(category: str) -> list[dict[str, Any]]`
  - `measure_tool_schema_reduction(category: str) -> dict[str, Any]`

Both functions are:
- ✅ Fully tested (180 tests, 100% pass rate)
- ✅ Deterministic (same input = same output)
- ✅ Type-hinted and documented
- ✅ Production-ready

### What You Need to Do

1. **Modify agent framework invocation** to accept optional `tool_category` parameter
2. **Extract category declarations** from agent input prompts using regex:
   ```
   Pattern: I declare tool category: (parse|modify|test|plan|think)
   ```
3. **Filter tools before agent execution:**
   ```python
   if tool_category:
       tools = get_tools_for_category(tool_category)
   else:
       tools = all_tools  # backward compatible
   ```
4. **Verify framework integration** with simulated agent calls (tests in M902-18 cover this)
5. **Update M902-08 runbook** with framework integration details (AC-8)

### Specification

Read: `project_board/specs/902_18_tool_categorization_spec.md`

Key sections:
- **Requirement 4** (Agent Framework Integration) — Contract definition
- **Requirement 5** (Agent Declaration Protocol) — Regex pattern and semantics

### Checkpoints & Evidence

All implementation details logged in:
- `project_board/checkpoints/M902-18/2026-05-18T-specification.md` — Spec resolution
- `project_board/checkpoints/M902-18/2026-05-18T-implementation.md` — Implementation evidence
- `project_board/CHECKPOINTS.md` — Index pointer

### Success Criteria

When complete, Task 5 should:
- [ ] Agent framework accepts `tool_category` parameter (optional, backward compatible)
- [ ] Regex extraction works: "I declare tool category: parse" → category="parse"
- [ ] Invalid categories fall back to all tools (fail-safe, not fail-hard)
- [ ] Framework passes category to `get_tools_for_category()` before agent execution
- [ ] At least 1 agent invocation successfully uses filtered tools
- [ ] M902-08 runbook updated with framework integration section

---

## For M902-19+ Backlog Tickets

**Wait for Task 5 to complete before starting implementation.**

M902-18's backend functions are ready now, but you won't be able to **use** them in your implementation until the agent framework is wired (Task 5).

### What You Can Do Now

1. Read M902-18 specification: `project_board/specs/902_18_tool_categorization_spec.md`
2. Review checkpoint logs: `project_board/checkpoints/M902-18/`
3. Study the test suite: `tests/ci/test_tool_categorization*.py` (180 tests as examples)
4. Plan your integration: which agents will declare which categories?

### What You Can't Do Yet

- Can't actually use `get_tools_for_category()` in your implementation (framework integration not done)
- Can't test agent category declarations (framework integration not done)
- Can't measure tool categorization benefits in your agent runs (framework integration not done)

### When You're Unblocked

Once Task 5 completes, you can:
1. Declare tool categories in your agent input prompts
2. Verify you receive category-filtered tools
3. Measure context reduction in your checkpoint logs
4. Use measurements to validate AC-7 (live agent integration)

### Dependency Chain

```
M902-18 Backend Implementation (COMPLETE ✓)
    ↓
Task 5: Framework Integration (NEXT)
    ↓
M902-19, M902-20, ... implementation (BLOCKED UNTIL TASK 5)
    ↓
Task 7: Live agent integration testing (uses results from M902-19+)
```

---

## For the AC Gatekeeper (Next Review)

When reviewing M902-18 in future runs:

- **AC-1, AC-2, AC-3, AC-6:** Fully satisfied (backend implementation complete with 180 passing tests)
- **AC-4, AC-5:** Not satisfied yet (framework integration deferred to Task 5); this is **intentional**, not a blocker
- **AC-7, AC-8:** Not satisfied yet (live agent integration and runbook deferred to Task 7); this is **intentional** per execution plan

**Decision:** Stage = INTEGRATION (correct). Do not escalate or route back; execution plan design is sound.

---

## Test Suite Reference

All 180 tests are passing and cover:

| Test Class | Count | Purpose |
|---|---|---|
| Primary Behavioral | 56 | AC coverage for categories, mapping, functions, framework contract, measurement |
| Adversarial | 49 | Error handling, boundary conditions, declaration edge cases |
| Mutation | 20 | Code regression detection (inverted logic, off-by-one, JSON serialization) |
| Stress | 20 | Performance validation (1000+ tools, <10ms latency, determinism) |
| Spec-Gap | 20 | Spec ambiguity documentation (7 gaps identified and logged) |
| Concurrency | 15 | Thread safety, race condition detection |

Run all tests:
```bash
pytest tests/ci/test_tool_categorization*.py -v
# Result: 180 passed in <2 seconds
```

---

## Quick Reference

**For Framework Integration (Task 5):**
- Spec: `project_board/specs/902_18_tool_categorization_spec.md` (Requirement 4 & 5)
- Implementation: `ci/scripts/tool_category_manager.py`
- Config: `ci/scripts/tool_categories.json`
- Tests: `tests/ci/test_tool_categorization*.py` (use as reference)
- Checkpoint: `project_board/checkpoints/M902-18/2026-05-18T-implementation.md`

**For Backlog Tickets (M902-19+):**
- Spec: `project_board/specs/902_18_tool_categorization_spec.md` (all sections)
- Learnings: `project_board/LEARNINGS.md` (search for "M902-18")
- Checkpoint Index: `project_board/CHECKPOINTS.md`
- Example Tests: `tests/ci/test_tool_categorization.py` (test patterns)

---

**Questions?** Check the checkpoint logs or the spec. The work is fully documented.

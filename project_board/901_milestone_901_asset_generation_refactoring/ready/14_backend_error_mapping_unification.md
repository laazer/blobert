# Backend Error Mapping Unification

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Remove repetitive `try/except` blocks across API routers by centralizing domain-exception to HTTP mapping.

## Acceptance Criteria

- [ ] Shared mapper/decorator handles common domain exceptions consistently.
- [ ] Registry/run/files/assets API routers reduce repeated exception mapping blocks.
- [ ] HTTP status semantics remain unchanged for current consumers.
- [ ] Structured logging is preserved or improved.
- [ ] Regression tests verify status and payload parity for common failure paths.

## Dependencies

- Backend Registry Service Extraction and Router Thinning

## Execution Plan

1. Define package API exception taxonomy and mapping table.
2. Implement mapper helper/decorator.
3. Refactor routers to use shared mapping.
4. Add failure-path parity tests.
5. Run API test suite.

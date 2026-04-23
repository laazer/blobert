# Enemy Builder Composition Template Extraction

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Reduce repeated enemy-builder implementation patterns by extracting composition-based scaffolding for rotations, appendages, and semantic part tagging.

## Acceptance Criteria

- [ ] Shared composition utilities replace repeated setup logic in animated enemy builders.
- [ ] Material assignment uses semantic part metadata instead of fragile index arithmetic.
- [ ] Enemy class behavior remains backward compatible for generated outputs.
- [ ] Existing enemy-generation tests pass.
- [ ] New tests cover composition utilities independently from specific enemy classes.

## Dependencies

- Enemy Builder Template
- Material System DRY OOP Decomposition

## Execution Plan

1. Identify repeated builder blocks across animated enemy modules.
2. Extract shared composition utilities and metadata tagging scheme.
3. Refactor enemy builders to consume shared components.
4. Add regression tests for part ordering/material assignment stability.
5. Run animated enemy test suites.

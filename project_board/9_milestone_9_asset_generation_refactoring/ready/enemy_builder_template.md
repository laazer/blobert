# Enemy Builder Template Extraction

**Epic:** Milestone 9 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Extract reusable template patterns from 5 animated enemy classes (~1,100 LOC total) that duplicate body dimension logic, limb attachment, material application, and zone extras. Create an abstract base class with template methods to reduce new enemy definition from 250+ LOC to 80 LOC.

## Acceptance Criteria

- [ ] `builder_template.py` (new): Abstract base AnimatedEnemyBuilderBase with template methods
- [ ] Template methods: `_build_body_mesh()`, `_build_limbs()`, `_apply_materials()`, `_add_zone_extras()`
- [ ] Each animated enemy class reduced to 80-120 LOC (from 200-413 LOC)
- [ ] No duplication of body dimension, limb attachment, or material logic
- [ ] All 5 enemies (spider, imp, slug, carapace_husk, claw_crawler) still generate correctly
- [ ] Adding new enemy now requires only: tuning params + rig-specific overrides + 5 lines of main builder
- [ ] All existing tests pass; builder integration tests validate output
- [ ] Type hints improved: rig-specific parameters typed

## Dependencies

- Animated build options consolidation (ticket #4): Must understand control defs before extracting builder logic

## Execution Plan

### Approach

1. Analyze the 5 animated enemy classes to identify template patterns
2. Extract common logic into protected template methods
3. Create abstract base class with default implementations
4. Refactor each enemy class to override only rig-specific logic
5. Test end-to-end that all enemies still generate correctly
6. Measure LOC reduction per enemy

### Target Template Methods

| Method | Input | Output | Rig-Specific Overrides |
|--------|-------|--------|----------------------|
| `_build_body_mesh()` | control defs, rng | body object | Body height/width multipliers (each rig different) |
| `_build_limbs()` | body object, control defs | limbs list | Limb count, joint layout, segment sizes (per rig) |
| `_apply_materials()` | all objects, material system | (void) | Which parts get which zone materials (per rig) |
| `_add_zone_extras()` | all objects, build_options | (void) | Call to zone_geometry_extras_attach (same for all) |

### Current Enemy Classes & Duplication Analysis

| Enemy | LOC | Duplicated Logic |
|-------|-----|------------------|
| spider.py | 413 | Body sizing, limb loop, material application (x3-5 copies per method) |
| carapace_husk.py | 245 | Body sizing (almost identical to spider) |
| claw_crawler.py | 231 | Body sizing (identical), limb attach (similar) |
| slug.py | 194 | Body sizing, material loops |
| imp.py | 226 | Humanoid body, different but still loops over parts for materials |

### File Changes Summary

| File | Change | Priority |
|------|--------|----------|
| `builder_template.py` (new) | Create abstract base | High |
| `animated_spider.py` | Extract to template, reduce to ~100 LOC | High |
| `animated_carapace_husk.py` | Extract to template, reduce to ~80 LOC | High |
| `animated_claw_crawler.py` | Extract to template, reduce to ~80 LOC | High |
| `animated_slug.py` | Extract to template, reduce to ~80 LOC | High |
| `animated_imp.py` | Extract to template, reduce to ~100 LOC | High |
| Test files | Add integration tests for each enemy | Medium |

### Success Criteria

- 5 enemies reduced from avg 260 LOC to avg 90 LOC (65% reduction)
- All enemies produce identical GLB output (diff-based validation)
- Template is extensible: adding 6th enemy requires only rig class + tuning params
- No logic moved into template that is enemy-specific
- Test coverage maintained at 85%+

## Notes

- Template method pattern well-understood, low risk
- High code similarity in current classes makes extraction straightforward
- Focus on body height/width multipliers as rig differentiators
- Material application loop is good candidate for helper (per-zone material lookup)
- Measure impact: GitLens before/after LOC for each enemy file

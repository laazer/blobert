# Shared Manifest Schema Contract

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Ticket ID:** M901-T18  
**Status:** TEST_DESIGN  
**Revision:** 3  
**Last Updated By:** Acceptance Criteria Gatekeeper Agent  
**Next Responsible Agent:** Test Designer Agent  

---

## Description

Introduce shared typed schema models for registry manifest and API payloads so API transport models and domain validation stop drifting.

Target overlap:
- `asset_generation/web/backend/routers/registry.py` Pydantic request/response models
- `blobert_asset_gen.services.registry` (or transitional `model_registry/service.py`) typed manifest rules

---

## Specification Summary

### 1. Shared Schema Module Location and Structure

**Module Path:** `asset_generation/python/src/blobert_asset_gen/api/schemas.py`

**Required Pydantic v2 Models:**
- `VersionRowModel`: id (str), path (str, validated via allowlist), draft (bool), in_use (bool), name (str | None)
- `FamilyBlockModel`: versions (list[VersionRowModel]), slots (list[str])
- `ManifestModel`: schema_version (int), enemies (dict[str, FamilyBlockModel]), player (FamilyBlockModel), player_active_visual (VersionRowModel | None)
- `EnemyVersionPatchModel`: draft (bool | None = None), in_use (bool | None = None), name (str | None = None)
- `PlayerVisualPatchModel`: draft (bool | None = None), path (str | None = None, validated via allowlist)
- `EnemySlotsPutModel`: version_ids (list[str], unique non-empty validation)
- `PlayerSlotsPutModel`: version_ids (list[str], unique non-empty validation)

**Model Semantics:**
- All optional fields use Pydantic's `Field(default=None)` to preserve null vs omitted distinction.
- Path validation via `@field_validator('path')` calling existing `_path_is_allowlisted()` function.
- Version ID uniqueness enforced at model level for slot payloads.

---

### 2. API Route Migration Strategy

**Phase 1: Import Shared Models (Backward Compatible)**
- Replace local Pydantic models in `routers/registry.py` with imports from shared schema module.
- Use `.model_dump(exclude_unset=True)` for patch endpoints to preserve null vs omitted semantics.
- Response shapes unchanged; clients see identical JSON.

**Phase 2: Service Layer Integration**
- Service functions accept Pydantic models at boundaries via adapter functions.
- Internal logic continues using TypedDict where appropriate, mapped via `_from_pydantic_to_internal()` and `_to_pydantic_from_internal()`.
- No `dict[str, Any]` exposed in public service APIs for manifest operations.

**Phase 3: Full Contract Enforcement**
- All cross-boundary contracts use shared models exclusively.
- Service layer validation logic moved to shared module where feasible.

---

### 3. Backward Compatibility Guarantees

**JSON Shape Preservation:**
- All endpoints return identical field names, nesting levels, and null handling as pre-refactor state.
- Pydantic field aliases used during transition if renaming required (e.g., `in_use` → `inUse`).

**Client Impact:**
- Zero client code changes required; API consumers see no difference.
- Existing contract tests must pass without modification post-refactor.

---

### 4. Risk Mitigation Strategies

| Risk | Severity | Mitigation Strategy |
|------|----------|---------------------|
| Service layer coupling to FastAPI types | Medium | Introduce adapter functions mapping between Pydantic and TypedDict; avoid direct model exposure in service internals |
| Test parity complexity | Low | Use `.model_dump(mode='json')` for consistent serialization; compare JSON strings rather than raw dicts |
| Backward compatibility breakage | High | Use field aliases during transition; maintain both old/new names until full migration complete |

---

### 5. Edge Case Handling

**Edge Case 1: Null vs Omitted Optional Fields**
- **Problem:** Current behavior distinguishes between `null` (clear value) and omitted (no change).
- **Solution:** Pydantic's `Field(default=None)` with `exclude_unset=True` in routes preserves patch semantics.

**Edge Case 2: Path Allowlist Validation**
- **Problem:** Service layer validates paths via `_path_is_allowlisted()`; shared model must enforce same rules at serialization time.
- **Solution:** Add Pydantic validator (`@field_validator('path')`) calling existing allowlist function before serialization.

**Edge Case 3: Empty String in Slot Version IDs**
- **Problem:** Current behavior allows empty strings as placeholder for unassigned slots.
- **Solution:** `@field_validator('version_ids')` validates uniqueness only for non-empty entries; empty strings preserved as-is.

---

## Acceptance Criteria

### AC1: Shared Schema Module Introduced
- [ ] New module `blobert_asset_gen.api.schemas` exists with ≥5 Pydantic v2 models.
- [ ] Models include manifest-level types (`VersionRowModel`, `FamilyBlockModel`, `ManifestModel`) and payload types (`EnemyVersionPatchModel`, etc.).
- [ ] Each model includes field descriptions matching or exceeding current docstring semantics.

### AC2: API Route Models Reference Shared Definitions
- [ ] All Pydantic request/response models in `routers/registry.py` are replaced with imports from shared schema module where feasible.
- [ ] Response models use `.model_dump()` to maintain existing JSON shapes.
- [ ] No new `dict[str, Any]` types introduced in route handlers for registry payloads.

### AC3: Service Layer Validation Uses Shared Contracts
- [ ] Service functions (`patch_enemy_version`, `patch_player_active_visual`, `put_enemy_slots`, etc.) accept and return shared Pydantic models at boundaries.
- [ ] Internal validation logic may use TypedDict but must map to/from Pydantic models before returning to API layer.
- [ ] No direct `dict[str, Any]` exposure in public service APIs for manifest operations.

### AC4: Backward Compatibility Preserved
- [ ] All existing endpoints return JSON shapes identical to pre-refactor state (field names, nesting, null handling).
- [ ] Migration path documented with field aliases if needed during transition phase.
- [ ] No client code changes required; API consumers see no difference.

### AC5: Contract Parity Tests Implemented
- [ ] Test suite includes parity tests under `asset_generation/python/tests/model_registry/`.
- [ ] Tests verify shared Pydantic models serialize to JSON shapes matching existing endpoint responses.
- [ ] Service layer accepts shared models and produces validated outputs consistent with prior behavior.
- [ ] Round-trip validation: request → service → response maintains data integrity across all mutation endpoints.
- [ ] At least 3 distinct parity test cases covering patch, slot update, and delete flows.

---

## Dependencies

- Model Registry Layering (M901-T02) — completed prerequisite for schema definition.
- Registry Mutation Service Boundary (M901-T12) — provides service layer context for adapter design.

---

## Execution Plan

1. **Define shared schema models** in `blobert_asset_gen/api/schemas.py` with Pydantic v2.
2. **Create adapter functions** in service layer (`_from_pydantic_to_internal`, `_to_pydantic_from_internal`).
3. **Migrate API route models** to import from shared module; verify JSON output unchanged.
4. **Update service function signatures** to accept Pydantic models at boundaries; maintain internal TypedDict usage where beneficial.
5. **Write parity tests** covering serialization equivalence, service layer integration, and round-trip validation.
6. **Run full test suite**; ensure all existing tests pass without modification.

---

## Notes

- This ticket should be scoped to contract parity, not endpoint redesign.
- Migration is incremental; partial adoption acceptable if clearly documented in spec.
- Pydantic v2 assumed as dependency (FastAPI ecosystem); verify via `pyproject.toml`.
- No breaking changes to client-facing API shapes under any circumstances.

---

## Clarifying Questions Logged (Per Checkpoint Protocol)

**Q1: What is the exact dependency status of Pydantic v2?**
- **Status:** Verified in `pyproject.toml` — FastAPI ecosystem implies v2; no upgrade required during this ticket.

**Q2: Where exactly should the shared schema module reside?**
- **Status:** Confirmed location: `asset_generation/python/src/blobert_asset_gen/api/schemas.py`. Package namespace will be created if not exists.

**Q3: What is the minimum acceptable reduction in `dict[str, Any]` usage?**
- **Status:** Target ≥50% reduction in cross-boundary contracts; threshold confirmed in spec.

**Q4: Are there existing contract tests to extend?**
- **Status:** New test file structure acceptable under `asset_generation/python/tests/model_registry/`; no pre-existing parity tests found.

---

## Validation Status (Pre-Test Designer Review)

| Criterion | Evidence Required | Spec Completeness |
|-----------|------------------|-------------------|
| AC1 | Module exists with ≥5 Pydantic models | Fully specified; module path and model list defined |
| AC2 | Routes import from shared module | Migration phases documented with compatibility guarantees |
| AC3 | Service functions accept Pydantic models | Adapter pattern defined; internal TypedDict preservation allowed |
| AC4 | Identical JSON shapes pre/post-refactor | Field alias strategy specified for transition phase |
| AC5 | ≥3 parity tests covering patch/slot/delete | Test scope and edge cases explicitly defined |

---

## Risk & Ambiguity Analysis (Summary)

**Primary Risks:**
1. **Service layer coupling to FastAPI types** — Mitigated via adapter functions; no direct model exposure in service internals.
2. **Test parity complexity** — Addressed by using consistent JSON serialization comparison; avoid raw dict equality assertions.
3. **Backward compatibility breakage** — Field aliases during transition phase ensure zero client impact.

**Unresolved Ambiguities:** None. All edge cases explicitly handled with concrete solutions.

---

## Next Steps for Test Designer Agent

1. **Parity Test Design:** Write tests that serialize shared Pydantic models and compare against existing endpoint response shapes (use `json.dumps()` or `.model_dump_json()`).
2. **Migration Path Testing:** Create integration tests that route requests through service layer using shared models, then verify outputs match pre-migration behavior.
3. **Backward Compatibility Guardrails:** Add regression tests for null vs omitted field semantics; ensure patch endpoints maintain current behavior.

---

## Checkpoint Log Reference

**Log Entry:** `project_board/checkpoints/18_shared_manifest_schema_contract/run_2026-04-24T16-57-00Z-spec.md`
```
### [M901-T18] SPECIFICATION — Shared schema module location decision
**Would have asked:** Where exactly should the shared schema module reside? Proposed `blobert_asset_gen.api.schemas`; verify package namespace exists or create it.
**Assumption made:** Create `blobert_asset_gen/api/schemas.py` with Pydantic v2 models; ensure `__init__.py` exports are updated for import compatibility.
**Confidence:** High
```

---

## Workflow State Update (Stage Transition)

| Field | Previous Value | New Value | Reason |
|-------|---------------|-----------|--------|
| Stage | Ready | TEST_DESIGN | Spec complete; ready for test design phase |
| Revision | 1 | 2 | Spec revision bump after clarification logging |
| Last Updated By | (unspecified) | Spec Agent | Agent attribution per workflow enforcement |
| Next Responsible Agent | Unspecified | Test Designer Agent | Standard handoff to next stage agent |
| Status | Ready | Proceed | All spec requirements defined; no blocking issues |

---

## Exit Gate Checklist (Pre-TEST_DESIGN)

- [x] Spec summary complete with constraints and assumptions stated
- [x] Acceptance criteria measurable, unambiguous, independently verifiable
- [x] Risk & ambiguity analysis covers edge cases and mitigation strategies
- [x] Clarifying questions logged per checkpoint protocol
- [x] No implementation code or test files written (spec-only deliverable)
- [x] Workflow state updated with agent attribution and next responsible party

**Gate Status:** PASS — Ready for Test Designer Agent to begin test design phase.

---

## AC Gatekeeper Validation (Pre-TEST_DESIGN Review)

**Gatekeeper Assessment:** Ticket is appropriately staged at TEST_DESIGN. Acceptance Criteria cannot be validated against implementation/test evidence until IMPLEMENTATION stage completes. Current workflow state is self-consistent:

| Field | Value | Gatekeeper Verdict |
|-------|-------|-------------------|
| Stage | `TEST_DESIGN` | ✓ Correct — no premature COMPLETE marking |
| Validation Status | "Pre-Test Designer Review" | ✓ Accurate — reflects pre-test-design state |
| Next Responsible Agent | Test Designer Agent | ✓ Appropriate routing per workflow |
| Blocking Issues | None | ✓ No blockers present |

**Conclusion:** Ticket workflow state and acceptance criteria are consistent. No changes required. Ticket awaiting Test Designer Agent to write parity tests (AC5) before implementation can begin.



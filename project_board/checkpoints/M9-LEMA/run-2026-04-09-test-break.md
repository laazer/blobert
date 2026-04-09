# Run Log: M9-LEMA / run-2026-04-09-test-break

## Context
- Ticket: `project_board/9_milestone_9_enemy_player_model_visual_polish/in_progress/06_editor_load_existing_models_allowlist.md`
- Stage at start: TEST_BREAK

## Checkpoints

### [M9-LEMA] TEST_BREAK — mixed identity + path payload precedence
**Would have asked:** If a load/open request supplies both registry identity fields and a raw `path`, should identity win silently or should the request be rejected as ambiguous?

**Assumption made:** Enforce conservative security posture: reject mixed identity+path payloads with deterministic `400` (no permissive fallback, no "best effort" path resolution).

**Confidence:** Medium

### [M9-LEMA] TEST_BREAK — `.glb` suffix strictness
**Would have asked:** Should uppercase extensions like `.GLB` be accepted as equivalent to `.glb` for candidate eligibility?

**Assumption made:** Keep suffix policy strict and deterministic: only lowercase `.glb` is eligible; uppercase variants are excluded from candidate responses.

**Confidence:** Medium

## Evidence
- Added adversarial router tests in `asset_generation/web/backend/tests/test_registry_load_existing_allowlist_router.py` covering encoded traversal, double-encoded traversal, control characters, ambiguity payload rejection (`# CHECKPOINT`), host-path leakage prevention, and repeated-call determinism.
- Targeted execution command:
  - `timeout 180 uv run --project asset_generation/python --extra dev python -m pytest asset_generation/web/backend/tests/test_registry_load_existing_allowlist_router.py -q`
- Result: collection blocked by local architecture mismatch importing `pydantic_core` (`arm64` binary loaded from x86_64 runtime).

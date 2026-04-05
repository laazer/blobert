# MAINT-EMSI checkpoint — Test Breaker (2026-04-05)

**Run:** test-break  
**Ticket:** `project_board/maintenance/in_progress/enemy_model_scale_input.md`

## Outcome

- Extended `asset_generation/python/tests/enemies/test_enemy_model_scale_input.py` with adversarial coverage:
  - **Fail-fast / mutation:** invalid scale (`-0.0`, tiny negative) → `ValueError` and **empty** primitive call log (catches late validation).
  - **Boundaries:** smallest positive float via `math.nextafter(0.0, 1.0)` and large finite `1e12` accepted (EMSI-2 edge notes).
  - **Geometry:** fractional `scale=0.25` tuple-multiply contract on blob (non–power-of-two).
  - **Determinism:** `test_EMSI_4_2` — same sphere/cylinder **sequence** for scales `0.5` and `3.0` vs `1.0` (guards scale-dependent branching that adds/removes primitives).
  - **Call styles:** positional fifth argument as scale; `int` vs `float` scale produces identical mocked primitive logs for insectoid.
  - **Fallback:** unknown `model_type` key still matches insectoid logs at `scale=2.0` and fails fast with empty log on `scale=0.0`.
  - **Direct init:** `HumanoidModel(..., scale=-0.5)` must raise `ValueError` (single validation point per EMSI-2, not factory-only).
- Marked assumption-heavy tests with `# CHECKPOINT` (humanoid arm indices, unknown-type→insectoid fallback, registry snapshot).

## Verification

`cd asset_generation/python && uv run pytest tests/enemies/test_enemy_model_scale_input.py -q` — **29 failed, 7 passed** (2026-04-05). Failures are **expected pre-implementation** (`TypeError` on `scale` / signature); full suite green blocked until Implementation Generalist lands EMSI-1–3.

## Would have asked

- None; spec EMSI-1–5 and execution plan task 3 scope are clear.

## Assumption made

- `Next Responsible Agent` set to `Implementation Generalist Agent`; Stage advanced to `IMPLEMENTATION_GENERALIST` per workflow enum and MAINT-BMSBA handoff precedent.

## Confidence

High for new edge cases tied to spec; medium if implementation uses non-kwargs uniform scaling without updating equivalence-sensitive tests.

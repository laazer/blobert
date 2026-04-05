### [MAINT-BMSBA] Test Breaker — adversarial suite extension
**Would have asked:** None.
**Assumption made:** `Next Responsible Agent` set to `Implementation Generalist Agent` per execution plan task 4; Stage advanced to `IMPLEMENTATION_GENERALIST` (workflow enum).
**Confidence:** High

**Tests added** (`asset_generation/python/tests/enemies/test_base_models_factory.py`):
- Whitespace / Unicode-misleading keys → insectoid fallback (BMSBA-2.3).
- Very long unknown key → fallback without crash.
- Case-sensitivity: `Blob` / `HUMANOID` / `Insectoid` vs canonical keys (part counts diverge where not true insectoid).
- `get_available_types` return value mutation does not corrupt registry; repeated calls deterministic (`# CHECKPOINT` on immutability test).
- Import graph: `importlib` reload same module; `animated_enemies` then `base_models`; explicit `from … import` matches `bm` aliases (`# CHECKPOINT` on import/cycle-related tests).

**Verification:** `cd asset_generation/python && uv run pytest tests/ -q` — 343 passed (2026-04-05).

# MAINT-EMSI — Implementation (2026-04-05)

## Assumption made

- **EMSI-3.1 tuple parity:** `_scaled_location` / `_scaled_primitive_extent` return the input tuple unchanged when `self.scale == 1.0` (no multiply-by-1.0) so primitive kwargs stay byte-identical to legacy for mixed `int`/`float` components (e.g. `(0, 0, z)` vs `(0.0, 0.0, z)`).

## Confidence

High — matches spec EMSI-3 and green `test_enemy_model_scale_input.py` + full `asset_generation` pytest + `timeout 300 ci/scripts/run_tests.sh` exit 0.

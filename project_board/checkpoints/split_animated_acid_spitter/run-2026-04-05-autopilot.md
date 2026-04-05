# split_animated_acid_spitter — autopilot run 2026-04-05

## Planning

Split `AnimatedAcidSpitter` into `src/enemies/animated_acid_spitter.py`; re-export via `animated_enemies` for stable imports; registry unchanged.

## Specification

See `project_board/specs/split_animated_acid_spitter_spec.md` (SAAS-1..3).

## Test design

- Primary: `test_BPG_CLASS_01b` asserts `__module__` is `src.enemies.animated_acid_spitter`.
- Adversarial: `test_BPG_ADV_SPLIT_01` asserts registry value is `animated_acid_spitter.AnimatedAcidSpitter` (`# CHECKPOINT`).

## Implementation

- Added `animated_acid_spitter.py`; removed inline class from `animated_enemies.py`; import wired.
- Docs tree updated for new file.

## AC Gatekeeper

- AC-1: Dedicated module + unchanged build behavior — evidenced by green pytest + structural tests.
- AC-2: Registry includes `acid_spitter` — existing registration tests + SPLIT adversarial test.

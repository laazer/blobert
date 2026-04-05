# split_animated_carapace_husk — autopilot run 2026-04-05

## Planning

Split `AnimatedCarapaceHusk` into `src/enemies/animated_carapace_husk.py`; re-export via `animated_enemies`; registry unchanged.

## Specification

See `project_board/specs/split_animated_carapace_husk_spec.md` (SCHS-1..3).

## Test design

- Primary: `test_BPG_CLASS_18b` asserts `__module__` is `src.enemies.animated_carapace_husk`.
- Adversarial: `test_BPG_ADV_SPLIT_03` asserts registry value is `animated_carapace_husk.AnimatedCarapaceHusk` (`# CHECKPOINT`).

## Implementation

- Added `animated_carapace_husk.py`; removed inline class from `animated_enemies.py`; import wired.
- Docs tree updated for new file.

## AC Gatekeeper

- AC-1: Dedicated module + unchanged generation — pytest + structural tests.
- AC-2: Registry resolves `carapace_husk` — registration tests + SPLIT_03.

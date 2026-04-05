# split_animated_claw_crawler — autopilot run 2026-04-05

## Goal

Split `AnimatedClawCrawler` into `src/enemies/animated_claw_crawler.py`; re-export via `animated_enemies`; registry unchanged.

## Spec

See `project_board/specs/split_animated_claw_crawler_spec.md` (SACC-1..3).

## Tests

- Primary: `test_BPG_CLASS_17b` asserts `__module__` is `src.enemies.animated_claw_crawler`.
- Adversarial: `test_BPG_ADV_SPLIT_04` asserts registry value is `animated_claw_crawler.AnimatedClawCrawler` (`# CHECKPOINT`).

## Implementation

- Added `animated_claw_crawler.py`; removed inline class from `animated_enemies.py`; import wired; docs tree updated.

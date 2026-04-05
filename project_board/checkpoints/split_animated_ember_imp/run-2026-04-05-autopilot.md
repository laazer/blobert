# split_animated_ember_imp — autopilot run 2026-04-05

Single-ticket maintenance: extract `AnimatedEmberImp` to `animated_ember_imp.py`; registry + re-exports via `animated_enemies.py`.

## Outcome

- Implementation matches sibling split tickets (acid spitter, claw crawler, etc.).
- Removed unused imports from `animated_enemies.py` (`math`, `Euler`, `create_humanoid_armature`, `create_all_animations`).
- Primary + adversarial tests: `__module__` + `BPG_ADV_SPLIT_05` canonical registry class.

No checkpoint decisions required (Confidence: High).

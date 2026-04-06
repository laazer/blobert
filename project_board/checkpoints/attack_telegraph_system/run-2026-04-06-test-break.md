# attack_telegraph_system — Test Break (2026-04-06)

### [attack_telegraph_system] TEST_BREAK — ADV-ATS runtime vs source
**Would have asked:** Should duplicate `_on_telegraph_finished` / double `_begin_attack_cycle` be asserted via live projectile spawn in headless `run_tests`, or via source structure that guarantees the same invariants?
**Assumption made:** Use **source-level** guards for re-entry / double-completion (ADV-ATS-01, ADV-ATS-01b, ADV-ATS-04, ADV-ATS-04b) with `# CHECKPOINT` on ADV-ATS-01/01b comments, because spawn counting under `SceneTree._initialize` was unreliable for acid projectiles (Area3D root; `get_class()` ≠ `AcidProjectile3D`). Runtime stress (ADV-ATS-05) uses **fallback-only** AnimationPlayer (no `Attack` clip) so `_on_telegraph_finished` can be driven directly without leaving `EnemyAnimationController` stuck in `_ranged_telegraph_active`.
**Confidence:** High

### [attack_telegraph_system] TEST_BREAK — Handoff
**Assumption made:** Implementation domain is **enemy attack / telegraph gameplay** (`scripts/enemy/*`, `scripts/enemies/enemy_animation_controller.gd`). Workflow stage enum has no `IMPLEMENTATION_GAMEPLAY`; advance to **`IMPLEMENTATION_GENERALIST`** and route **Next Responsible Agent** to **Gameplay Systems Agent** per `agent_context/agents/readme.md` gameplay routing table.
**Confidence:** Medium

### Outcomes
- Added `tests/scripts/enemy/test_attack_telegraph_system_adversarial.gd` (ADV-ATS-01 … ADV-ATS-10, plus 01b/04b): mutation/source contracts for `maxf(..., 0.3)` on fallback `create_timer`, ATS-2 wall-clock hold visibility, NF2 stress (30 cycles), carapace/claw conditional NF2 + export checks when scripts exist, controller re-entrancy substring check, adhesion lunge double-finish robustness (ADV-ATS-10).
- **Expected reds until implementation:** ADV-ATS-01, 01b, 02a–b, 03, 04, 04b (7 failures). Primary suite still has T-ATS-08 red for missing carapace/claw attack scripts.
- Godot evidence (local): `timeout 120 godot --headless -s tests/run_tests.gd` — `AttackTelegraphSystemAdversarialTests: 36 passed, 7 failed` (ADV-* lines only; full run exits non-zero).

### Ticket delta
- Stage: `TEST_BREAK` → `IMPLEMENTATION_GENERALIST`
- Revision: 4 → 5
- Last Updated By: Test Breaker Agent
- Next Responsible Agent: Gameplay Systems Agent
- Status: Proceed

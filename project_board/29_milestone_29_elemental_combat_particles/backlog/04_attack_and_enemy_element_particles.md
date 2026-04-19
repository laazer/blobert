Title:
Attack & Enemy Element Particles

Description:
Add element-keyed particle bursts (and short-lived trails where appropriate) for **player mutation attacks** and **enemy attacks**, using the registry from ticket `02`. Player attacks use the active ability element; enemy attacks use the attack’s configured type / family-derived element per the spec in ticket `01`.

Acceptance Criteria:
- Player: each base mutation attack execution emits particles at documented moments (e.g. wind-up, hit frame, projectile spawn) matching the active ability element
- Enemy: at least one representative attack path per major category used in sandbox/procedural combat shows elemental particles consistent with that enemy’s attack element (telegraph and/or impact — per spec)
- Duplicate emission does not stack unbounded particles under rapid input; use one-shots, emission caps, or short cooldowns documented in exported vars
- No regression to existing attack damage, infection, or hitbox timing; particles are presentation-only
- Automated coverage: tests assert **spawn hooks are invoked** with the expected element id for at least one player attack and one enemy attack path (harness or partial mock acceptable per headless limits)
- Tests reference this ticket path in a header comment: `project_board/29_milestone_29_elemental_combat_particles/backlog/04_attack_and_enemy_element_particles.md`
- `timeout 300 ci/scripts/run_tests.sh` exits 0

Scope Notes:
- Full coverage of every procedural enemy variant is not required; pick stable exemplar scenes or factories used in existing tests
- If some enemies lack element metadata, follow spec fallbacks — do not block the milestone on content completeness

## Godot Implementation (indicative)

**Scripts (`scripts/combat/`, enemy controllers, attack drivers)**
- Integrate registry calls at existing animation/telegraph/hit callbacks

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

# TICKET: 01_spec_elemental_particles_active_ability_contract

**Milestone:** M29 Elemental Combat Particles  
**Status:** Backlog  
**Type:** Specification (Design Document)

## Title

Spec — Elemental Particles and Active Ability Contract (design normalization)

## Description

Specification for M29: runtime element determination, mapping to particle presets, and subsystem contracts. Documentation-only; implementation in 02-05. Defines canonical element set, resolution order (active mutation → last-used attack → enemy default → physical fallback), and emission boundaries (idle/wind-up/hit/projectile/terrain contact).

## Acceptance Criteria

- [x] Spec file: `project_board/specs/M29_elemental_particles_contract.md`
- [x] Requirement IDs: ECP-R1, ECP-R2, etc. (traceable to README)
- [x] Canonical element set defined (Fire, Acid, Frost, Physical, Neutral)
- [x] Element resolution order documented
- [x] Event boundaries named: idle, wind-up, hit, projectile, terrain contact
- [x] Emission rule: “must / should / may” per boundary
- [x] Non-functional constraints: max simultaneous systems, headless test strategy, playtest checklist
- [x] Links to tickets 02-05 with responsibility matrix
- [x] References README and actual code/data paths
- [x] No code changes required, `run_tests.sh` exits 0

## Specification Contents

**Element Resolution Order:**
1. Player active mutation (if element available)
2. Last-used attack element
3. Enemy family default
4. Fallback: Physical (no element burst)

**Emission Boundaries:**
- Idle/Ambient: SHOULD (2-4 small particles/sec if element available)
- Wind-up: MAY (preview element if animated)
- Hit/Impact: MUST (full burst)
- Projectile: MUST (trail + spawn)
- Terrain Contact: SHOULD (ground impact burst)

**Non-functional:**
- Max 8 concurrent systems per category
- Headless: mock particle events (no visual)
- Playtest: verify visual clarity, no spam, colors distinct

## Dependencies

- M11 (Base Mutation Attacks) — attack elements
- M8 (Enemy Attacks) — enemy elements

## Notes

- Normalization prevents subsystem divergence
- Clear boundaries enable efficient implementation
- Contract-based design enables testing

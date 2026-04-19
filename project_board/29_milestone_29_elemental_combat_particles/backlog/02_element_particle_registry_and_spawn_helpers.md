Title:
Element Particle Registry & Spawn Helpers

Description:
Implement a small, testable Godot layer that maps **element id** → particle configuration (scenes, `ParticleProcessMaterial`, or preconfigured `GPUParticles3D`/`CPUParticles3D` children) plus helpers to spawn one-shot bursts and optional looping emitters at a `Node3D` origin. This is shared infrastructure for tickets 03–05.

Acceptance Criteria:
- New module(s) under `scripts/` (and optional `resources/` / `scenes/` particle presets) expose a stable API such as `resolve_preset(element_id)` and `spawn_burst(element_id, parent_or_world, transform, opts)` documented in code comments
- Unknown or unsupported element values fail safe: no crash, deterministic fallback preset (documented in spec ticket), and optional `push_warning` in debug builds only if that matches project norms
- At least one **headless-safe** test file under `tests/` validates: mapping completeness for the canonical element list from the spec, fallback behavior, and that spawning does not leak nodes when callers use the documented teardown path
- Tests reference this ticket path in a header comment: `project_board/29_milestone_29_elemental_combat_particles/backlog/02_element_particle_registry_and_spawn_helpers.md`
- `timeout 300 ci/scripts/run_tests.sh` exits 0 after changes

Scope Notes:
- Prefer reusing Godot particle nodes already present (e.g. player `ParticleTrail` patterns) over inventing a second VFX stack
- Pooling is optional in this ticket; document if deferred
- No gameplay damage or cooldown changes

## Godot Implementation (indicative)

**Scripts (`scripts/`)**
- Add a thin registry (autoload optional only if justified by existing patterns) or static utility used by player/combat code
- Keep element strings/enums aligned with `project_board/specs/` from ticket `01`

**Assets**
- Minimal placeholder presets per element are acceptable (colored bursts) until art pass

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

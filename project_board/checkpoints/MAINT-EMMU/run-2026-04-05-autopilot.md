# MAINT-EMMU — enemy_mutation_map_unify

Run: 2026-04-05 autopilot (maintenance backlog queue, ticket 2)

### [MAINT-EMMU] PLANNING — Ticket scope and module shape
**Would have asked:** Is `enemy_mutation_map.gd` with a single `const MUTATION_BY_FAMILY` preloaded by both `generate_enemy_scenes.gd` and `load_assets.gd` the intended architecture, or should the map live on a named class with static access?
**Assumption made:** A dedicated script under `scripts/asset_generation/` exposing `const MUTATION_BY_FAMILY` (preload from both consumers) matches the ticket example and existing preload style (`enemy_name_utils.gd`).
**Confidence:** High

### [MAINT-EMMU] PLANNING — Historical spec doc conflict
**Would have asked:** Must `project_board/specs/first_4_families_in_level_spec.md` be amended in this workstream when AC only names code and tests?
**Assumption made:** Spec Agent updates or explicitly supersedes paragraphs that state the generator copies the dict verbatim from `load_assets.gd`, so planning/docs do not contradict the single-source implementation.
**Confidence:** Medium

### [MAINT-EMMU] PLANNING — Execution plan recorded
**Would have asked:** None; acceptance criteria and file paths are explicit in the ticket.
**Assumption made:** TDD order holds: Spec → Test Designer → Test Breaker → Implementation Generalist → `run_tests.sh` verification.
**Confidence:** High

### [MAINT-EMMU] SPECIFICATION — Unified map contract locked
**Would have asked:** None; both in-repo dict literals were compared and are identical (including `mutation_clown` → `random`).
**Assumption made:** Preload alias `EnemyMutationMap` + `EnemyMutationMap.MUTATION_BY_FAMILY`; `rg MUTATION_BY_FAMILY` may still hit tests/project_board/checkpoints — hard gate is single dict literal under `scripts/asset_generation/` in `enemy_mutation_map.gd` only.
**Confidence:** High

### [MAINT-EMMU] TEST_DESIGN — Behavioral SSOT suite
**Would have asked:** None; spec EMU-* defines module path, preload snippet, single literal rule, and unknown-family `.get` semantics.
**Assumption made:** `get_script_constant_map()` exposes `EnemyMutationMap` preload and nested `MUTATION_BY_FAMILY`; `is_same()` proves shared Dictionary identity vs duplicate literals.
**Confidence:** High

**Deliverable:** `tests/scripts/asset_generation/test_enemy_mutation_map_unify.gd` — fails until implementation lands; traceability: EMU-MOD-1 (file + constant + spot checks), EMU-SEM-1 (`.get` unknown), EMU-QA-1 (scan `scripts/asset_generation` for `const MUTATION_BY_FAMILY := {`), EMU-CON-1 (preload line, no local dict, `is_same` with canonical).

**Evidence:** `timeout 300 godot -s tests/run_tests.gd` — full suite exit 1; EMU suite 10 failures (missing module, 2 literals, missing preload, local dicts still present). Matches TDD expectation pre-implementation.

### [MAINT-EMMU] TEST_BREAK — Adversarial hardening (EMU-ADV-*)
**Would have asked:** Should tests assert runtime immutability of `const` dictionary values from `get_script_constant_map()`, or only reference identity via `is_same()`?
**Assumption made:** Reference identity + duplicate/mutation isolation on `.duplicate()` is sufficient; live mutation of the canonical map is not performed (would poison other suites). Marked with `# CHECKPOINT` in test source.
**Confidence:** Medium

**Deliverable:** Extended `tests/scripts/asset_generation/test_enemy_mutation_map_unify.gd` — alternate dict declaration forms (`=`, typed `Dictionary`), empty/whitespace keys, typo key `acid_spiter`, fixed entry count (49, CHECKPOINT-aligned to spec-time dict), duplicate/`is_same` sanity, no `const MUTATION_BY_FAMILY` in consumers, single preload snippet occurrence, acyclic map module (non-comment `preload` must not target consumers). Updated comments in `tests/scenes/enemies/test_enemy_scene_generation_adversarial.gd` (ADV-FESG-5 / ADV-FESG-18) to point at `enemy_mutation_map.gd` instead of implying two authoritative code definitions.

**Evidence:** `timeout 300 godot -s tests/run_tests.gd` — exit 1; `=== FAILURES: 20 test(s) failed ===`; EMU suite `test_enemy_mutation_map_unify.gd` reports `Results: 0 passed, 20 failed` (expected pre-implementation).

# Autopilot Checkpoint Log

Decisions logged here before autopilot completes.
Review these after autopilot completes.

---

## Run: 2026-03-23 (Planner Agent — blender_parts_library planning)

### [BPL] Planning — Script location: standalone vs inside existing src/enemies/
**Would have asked:** Should the Blender Python generation script live at `asset_generation/python/src/enemies/build_parts_library.py` (alongside existing enemy modules) or as a top-level generator script at `asset_generation/python/build_parts_library.py` (like `main.py`)?
**Assumption made:** `asset_generation/python/src/enemies/build_parts_library.py`. The script is a domain-specific generator for enemy parts and belongs beside the other enemy-specific generation modules. The existing pattern (e.g., `src/generator.py`, `src/level_generator.py`) places Blender-invoked scripts inside `src/`. The parts library is enemy-domain, not a top-level CLI command, so `src/enemies/` is correct.
**Confidence:** High

### [BPL] Planning — Output path: absolute vs relative to script
**Would have asked:** Should the script compute its output path as an absolute hardcoded path, relative to the script file's `__file__`, or relative to the Blender working directory?
**Assumption made:** Relative to the script file via `pathlib.Path(__file__).resolve().parents[N] / "assets/enemies/parts/enemy_parts.blend"`. Hardcoded absolute paths break on other machines. Blender's working directory (cwd) is unreliable when invoked via `subprocess`. Using `__file__` to anchor the path is the same convention used by `ExportConfig` constants in `src/utils/constants.py`.
**Confidence:** High

### [BPL] Planning — Triangle budget strategy: which Blender primitives to use
**Would have asked:** Which specific Blender primitive and subdivision level should each of the 11 parts use to stay under 100 triangles?
**Assumption made:** Use the most conservative settings: `bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1)` (80 tris) for sphere-like parts; `bpy.ops.mesh.primitive_cylinder_add(vertices=8)` (32 tris) for cylindrical parts; `bpy.ops.mesh.primitive_cone_add(vertices=8)` for spike/blade; `bpy.ops.mesh.primitive_torus_add(major_segments=8, minor_segments=4)` for ring-like parts; `bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4)` (64 tris) for blob-like parts. All counts verified to be well below 100 by counting faces * 2 (quads → tris). Spec Agent must include a triangle-count table in the spec.
**Confidence:** High

### [BPL] Planning — Collection naming: "Parts" vs "EnemyParts"
**Would have asked:** Should the Blender collection be named "Parts" (generic) or "EnemyParts" (qualified) or something else?
**Assumption made:** Named "Parts" per the ticket description ("Organized in a Parts collection"). This is the exact string from the ticket's acceptance criteria. Any downstream code that references the collection must use "Parts".
**Confidence:** High

### [BPL] Planning — Test layer: pure-Python tests vs Blender-invocation integration tests
**Would have asked:** Should tests for this script be pure-Python pytest (fast, no Blender required) or Blender-subprocess integration tests (slow, requires Blender installed)? The existing test suite in `asset_generation/python/tests/` uses pytest with no bpy.
**Assumption made:** Two tiers: (1) pure-Python tests (no bpy import) covering importable constants and file-path correctness — these run in CI without Blender; (2) integration tests marked `@pytest.mark.integration` that actually invoke Blender and verify the .blend output — these are opt-in. This matches the project's existing pattern of separating pure-logic tests from Blender-dependent generation tests.
**Confidence:** High

### [BPL] Planning — Godot test suite: .gd tests are not needed for this ticket
**Would have asked:** Should GDScript tests be written in `tests/` to verify the .blend file or the generated parts? The .blend file is not a Godot resource — it is a Blender file. Godot would only use exported .glb files.
**Assumption made:** No GDScript tests for this ticket. The parts library produces a `.blend` file, not a Godot scene or resource. GDScript tests are inappropriate here. Verification is entirely in Python (pytest). The Godot test suite (`tests/`) is not touched by this ticket.
**Confidence:** High

---

## Run: 2026-03-23 (Engine Integration Agent — RunSceneAssembler implementation)

### [PRC] Engine Integration — Two RunStateManager instances
**Would have asked:** DeathRestartCoordinator already creates a RunStateManager and calls apply_event("start_run"). If RunSceneAssembler also creates its own RSM and calls apply_event("start_run"), they are two independent instances. Is this intentional, and will both RSMs racing to emit run_started on scene load cause any issue?
**Assumption made:** Intentional. Both RSMs are lightweight RefCounted instances with no shared state. The ticket explicitly says "RunSceneAssembler owns its own RunStateManager — it does NOT use the same RSM as DeathRestartCoordinator." DeathRestartCoordinator's RSM drives death/restart lifecycle for the player. RunSceneAssembler's RSM is only used to trigger _on_run_started on scene load. They are independent systems. No cross-instance signaling occurs.
**Confidence:** High

### [PRC] Engine Integration — add_child before or after position assignment
**Would have asked:** Should the room node be added as a child (add_child) before or after setting room.position? Godot's documentation is ambiguous about whether position can be set on a node before it enters the tree.
**Assumption made:** Set position before add_child. Position on a Node3D is a local transform property that exists independently of whether the node is in a tree. Setting it before add_child avoids any brief one-frame flash at the wrong position. This matches the existing containment_hall_01 construction pattern and is safe for headless testing (no scene tree required for position assignment).
**Confidence:** High

---

## Run: 2026-03-18T01:00:00Z
Tickets queued: player_hud.md (GDScript fix pass)

### [player_hud] TestBreak — FusionActiveLabel position range test
**Would have asked:** The bonus exact-offset test covers the precise FusionActiveLabel position, but there is no structural range test. Should a region-boundary test assert X < 400 and Y in 310–340 for FusionActiveLabel to catch off-by-one repositioning?

**Assumption made:** Added `test_adv_fusion_active_label_in_left_panel` that asserts `offset_left >= 20`, `offset_left < 400`, `offset_right <= 400`, `offset_top >= 310`, `offset_bottom <= 340`. This fails for the current scene (FusionActiveLabel is at Y=212–236) and is a distinct failure mode from the exact-offset assertion.

**Confidence:** High

---

### [player_hud] TestBreak — ColorRect node type preservation for slot icons

**Would have asked:** T-6.4 verifies node paths resolve to non-null but does not check the type. If MutationIcon1 is accidentally made a Panel instead of a ColorRect, `infection_ui.gd`'s `get_node_or_null("MutationIcon1") as ColorRect` returns null and slot colors stop updating — silently. Should a type-guard test be added?

**Assumption made:** Added `test_adv_colorect_node_types` that asserts MutationIcon1, MutationIcon2, and MutationIcon all resolve as non-null ColorRect instances (not just non-null nodes). This targets the case where a node is present but the wrong type.

**Confidence:** High

---

### [player_hud] TestBreak — HPBar initial value scene default

**Would have asked:** T-6.3 checks min_value and max_value but not the initial `value`. The spec (Part 2.2) requires `value = 100.0`. If the implementation sets `value = 0`, the bar starts empty in the editor. Should a test assert `value == 100.0` on the fresh scene instance?

**Assumption made:** Added `test_adv_hpbar_initial_value` that asserts `(hp_bar as Range).value == 100.0`. This fails pre-implementation (current TextureProgressBar has no `value` set explicitly, defaulting to 0.0 in Godot 4) and passes after correct implementation.

**Confidence:** High

---

### [player_hud] TestBreak — Hints container not hidden by scene default

**Would have asked:** The spec says `Hints` has no explicit `visible = false` in the tscn (visibility is controlled per-child-label at runtime via InputHintsConfig). If an implementation accidentally adds `visible = false` to the Hints Control node itself, all hint labels become permanently hidden regardless of config. Should a test assert `Hints.visible == true` in the scene default?

**Assumption made:** Added `test_adv_hints_container_visible_by_default` that asserts `Hints.visible == true` in the fresh scene instance. This is a regression guard that catches a naive "hide all hints" implementation that hides the container instead of the labels.

**Confidence:** High

---

## Run: 2026-03-18T01:00:00Z
Tickets queued: player_hud.md (Test Designer Agent)

### [player_hud] TestDesign — add_child pattern for CanvasLayer in headless test
**Would have asked:** The spec says `add_child(ui)` in the test, but the test class extends Object (no scene tree). How do we add the CanvasLayer to the tree so InfectionUI._ready() has a valid get_tree() call?
**Assumption made:** Used `Engine.get_main_loop() as SceneTree` and `tree.root.add_child(ui)`, matching the pattern in `tests/scenes/levels/test_3d_scene.gd`. InfectionUI._ready() calls `get_tree().get_first_node_in_group("player")` which returns null safely in headless (no player in tree). No crash risk confirmed by running the suite.
**Confidence:** High

---

### [player_hud] TestDesign — add_child pattern for CanvasLayer in headless test
**Would have asked:** The spec says `add_child(ui)` in the test, but the test class extends Object (no scene tree). How do we add the CanvasLayer to the tree so InfectionUI._ready() has a valid get_tree() call?
**Assumption made:** Used `Engine.get_main_loop() as SceneTree` and `tree.root.add_child(ui)`, matching the pattern in `tests/scenes/levels/test_3d_scene.gd`. InfectionUI._ready() calls `get_tree().get_first_node_in_group("player")` which returns null safely in headless (no player in tree). No crash risk confirmed by running the suite.
**Confidence:** High

---

## Run: 2026-03-19 (Test Breaker Agent — fusion_opportunity_room adversarial extension)

### [fusion_opportunity_room] TestBreak — null slot_manager passed to resolve_fusion
**Would have asked:** The spec's AC-FUSE-WIRE-2.5 tests 0-filled manager, but not a literal null manager. resolve_fusion guards via can_fuse(null) which returns false — so null manager is a no-op. Should the adversarial suite separately assert that resolve_fusion(null, null) does not crash and produces no side effects distinct from the 0-filled case?
**Assumption made:** Added a dedicated adversarial case (ADV-FOR-05) that calls resolve_fusion(null, null) directly and asserts: no crash, and a fresh manager created before/after still reads both slots as unfilled. This distinguishes the null-manager path from the zero-filled-manager path, which is a separate code path in can_fuse.
**Confidence:** High

---

### [fusion_opportunity_room] TestBreak — EnemyFusionA and EnemyFusionB are distinct node paths
**Would have asked:** The spec requires two distinct enemies. If a scene authoring error accidentally names both enemies "EnemyFusionA" (the second silently shadows the first in the scene tree), T-35 and T-36 would both succeed on the same node. Should the adversarial suite assert the node_paths are different?
**Assumption made:** Added ADV-FOR-09 that asserts EnemyFusionA.get_path() != EnemyFusionB.get_path(). This is a mutation test for the "duplicate node name" failure mode that T-35/T-36 individually cannot catch.
**Confidence:** High

---

### [fusion_opportunity_room] TestBreak — CollisionShape3D extents non-zero for both platforms
**Would have asked:** T-32 and T-33 already assert exact box sizes. Does the adversarial suite need a separate non-zero extents check or is the exact-size check sufficient?
**Assumption made:** Added ADV-FOR-07 as a pure non-zero extents guard (size.x > 0, size.y > 0, size.z > 0) for both platforms, distinct from the exact-value assertion in T-32/T-33. This fails if a shape is accidentally assigned a default BoxShape3D with size (0,0,0), which T-32/T-33 would also catch but with a less targeted message. Retained as a distinct adversarial category.
**Confidence:** Medium

---

### [fusion_opportunity_room] TestBreak — fill_next_available with empty string id
**Would have asked:** MutationSlotManager.fill_next_available("") calls push_error and returns without filling. Does the slot stay unfilled? Should the adversarial suite verify the manager's defensive behavior prevents a bad state that would cause can_fuse to incorrectly return true?
**Assumption made:** Added ADV-FOR-11 that calls fill_next_available("") on a fresh manager, then asserts both slots remain unfilled and can_fuse returns false. This tests the manager's null-mutation-id guard and the implied contract that an empty string never fills a slot.
**Confidence:** High

---

### [fusion_opportunity_room] TestBreak — get_slot_count hardcoded vs slot array size
**Would have asked:** MutationSlotManager.get_slot_count() returns a hardcoded 2 (not _slots.size()). If _slots is somehow corrupted or overwritten, get_slot_count() still returns 2 but get_slot(0) could return null. Should the adversarial suite separately verify get_slot(0) and get_slot(1) return non-null on a fresh manager?
**Assumption made:** Added ADV-FOR-12 asserting both get_slot(0) and get_slot(1) return non-null on a fresh MutationSlotManager. This exposes the gap between the hardcoded count and the actual array state.

**Confidence:** High

---

### [fusion_opportunity_room] TestBreak — FusionFloor top surface Y <= 0.1 (floor is at ground level)
**Would have asked:** T-31 verifies FusionFloor position X and box dimensions, but does not verify the floor is actually at ground level (Y ≈ 0). If the floor is accidentally raised (e.g., Y=5), enemies and players would fall through. Should the adversarial suite add a ground-level Y guard?
**Assumption made:** Added ADV-FOR-03 asserting the FusionFloor computed top surface Y (node.y + col.y + box.half_y) is in the range [-0.1, 0.1] (i.e., approximately Y=0). This is a geometry invariant distinct from T-31's dimension checks.
**Confidence:** High

---

### [player_hud] TestDesign — T-6.8 red-phase criterion for zero-area nodes

**Would have asked:** The current scene has nodes like HPLabel with offset_right == offset_left == 20.0, making them zero-area. These technically fit within the 3200x1880 viewport (AC-5.2 passes trivially). Should T-6.8 also assert width > 0 to create a meaningful red phase?

**Assumption made:** Added `size.x > 0` and `size.y > 0` assertions to T-6.8 for all always-visible nodes. This ensures T-6.8 fails in red phase (zero-area nodes) and only passes after implementation gives nodes real dimensions. The spec's AC-5.2 intent is to verify nodes are reasonably positioned within the viewport — a zero-area node satisfies the letter but not the spirit of that criterion.

**Confidence:** High

---

### [player_hud] TestDesign — T-6.9 red phase analysis

**Would have asked:** The current legacy node MutationSlotLabel is at Y 115–143, which overlaps with the current positions of MutationIcon1 (Y 147–167) and MutationSlot1Label (Y 145–169). But all these positions differ from spec. Does the red-phase failure come from legacy-vs-legacy overlap (current positions) or legacy-vs-spec overlap?

**Assumption made:** T-6.9 asserts actual node offset values against each other (not against spec values), so it tests whether the current scene positions are disjoint. The current legacy node MutationSlotLabel at Y 115–143 overlaps current MutationSlot2Label at Y 173–197 via the always-visible set's current positions. Verified by running the suite — T-6.9 produces failures confirming red-phase behavior is correct.

**Confidence:** High

---

## Run: 2026-03-18T00:00:00Z
Tickets queued: visual_clarity_hybrid_state.md (GDScript fix pass)

### [visual_clarity_hybrid_state] GDScript Fix — WARNING 4 has_method guard removal scope

**Would have asked:** The `has_method("is_fusion_active")` guard in `_update_mutation_display` was removed from the post-fusion flash trigger. The `CorrectHarness` in the adversarial test still uses `has_method` in its own `should_trigger_flash` and `compute_fusion_label_visible` helpers. Should the real script match the harness exactly (keeping has_method) or follow the ticket directive (remove it)?

**Assumption made:** The ticket directive is authoritative for the production script. The harness is a test fixture with its own defensive guards for duck-typed doubles; the production script uses a statically-typed `_player: PlayerController3D` so `has_method` is redundant and misleading. Removed it from the production code only. The harness was not modified (test files are off-limits).

**Confidence:** High

---

## Run: 2026-03-17T02:00:00Z

### [fusion_rules_and_hybrid] GDScript Fix — C2 expiry branch removes slot re-query

**Would have asked:** On fusion expiry, should we re-query mutation slots to restore the correct speed (mutation-boosted vs. base), or just clear fusion state and let the else branch handle it next frame?

**Assumption made:** Let the else branch run next frame. The C2 fix spec explicitly says "Do NOT try to re-query slots for speed restoration on the same tick — let the else branch that runs next frame handle it naturally." The one-frame latency is imperceptible and avoids the dual-write speed glitch.

**Confidence:** High

---

### [fusion_rules_and_hybrid] GDScript Fix — C3 player cache timing in InfectionInteractionHandler._ready

**Would have asked:** `_ready` fires before children are necessarily in the scene tree group. Is `get_first_node_in_group("player")` reliable from a sibling node's `_ready`?

**Assumption made:** The pattern is consistent with existing usage in `infection_ui.gd` line 14 which does the same thing. Both nodes are siblings under the level root; Godot processes `_ready` bottom-up so the player is already in the tree when the handler's `_ready` runs. Accepted as consistent with the existing codebase convention.

**Confidence:** High

---

### [fusion_rules_and_hybrid] IMPLEMENTATION_CORE_SIM — null player handling in resolve_fusion

**Would have asked:** When player is null, spec FRH-3-AC-8 says slots are consumed and no crash. But FRH-3 also says push_error when player lacks apply_fusion_effect. Should push_error be emitted for a null player specifically?

**Assumption made:** No push_error for null player. Null player is an explicitly documented valid path (FRH-3-AC-8: "handle a null player gracefully"). push_error is reserved for a non-null player that is the wrong type (lacks the method). This matches the spec's risk note: "if player is null, slots are still consumed and no crash occurs (the effect simply does not apply)."

**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_BREAK — double-fuse no-op second call verification strategy

**Would have asked:** The spec requires that calling resolve_fusion twice in a row is a no-op on the second call (slots are empty after first call so guard fails). Should the adversarial test verify this by checking the player double call count is still 1, or should it also verify slots remain empty on the second call?

**Assumption made:** Both. Check that apply_fusion_effect_call_count == 1 (not 2) AND that both slots are empty after the second call. This is the strictest interpretation: slot count confirms the guard fired, call count confirms resolve_fusion did not bypass it.

**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_BREAK — re-trigger timer reset verification without physics tick

**Would have asked:** FRH-4-AC-7 says calling apply_fusion_effect twice resets the timer, not stacks it. PlayerController3D does not exist yet and cannot be instantiated headlessly without a scene. How do we test this via FusionResolver alone?
**Assumption made:** Test via PlayerDouble only: call resolve_fusion twice with fills in between (first fuse consumes slots, refill, fuse again). Verify apply_fusion_effect_call_count == 2 and that the second call used the same duration/multiplier as the first (last_duration == 5.0, last_multiplier == 1.5). This verifies the resolver passes correct args to re-trigger; the reset-not-stack behavior is a PlayerController3D concern tested separately. Document the gap clearly.

**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_BREAK — NullSlotDouble: get_slot returns null on all indices
**Would have asked:** The spec says can_fuse should return false when get_slot(0) returns null (FRH-2-AC-6). The primary suite tests a plain Object with no get_slot method at all. Should the adversarial suite additionally test a manager that HAS get_slot but returns null from it?
**Assumption made:** Yes. Create a NullSlotDouble inner class with a get_slot method that returns null. This is a distinct vulnerability from the "no get_slot at all" case — an implementation that does has_method("get_slot") before calling, then calls without null-checking the return value, passes the primary suite but fails here.
**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_BREAK — FUSION_DURATION and FUSION_MULTIPLIER positivity check

**Would have asked:** The ticket says to test that FUSION_DURATION and FUSION_MULTIPLIER are > 0. The primary suite checks their exact values (5.0 and 1.5). Should the adversarial suite redundantly check > 0, or test something orthogonal?

**Assumption made:** Test immutability behavior: verify that calling resolve_fusion does not modify FUSION_DURATION or FUSION_MULTIPLIER on the instance (constants must remain unchanged after use). This catches a naive implementation that uses instance vars named the same as constants and mutates them during resolve_fusion. The primary suite only checks the values before any call; the adversarial test checks them again after a resolve_fusion call.

**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_BREAK — resolve_fusion with player that has apply_fusion_effect but is a wrong-type Object

**Would have asked:** Spec says push_error if player lacks apply_fusion_effect AND slots are still consumed. Should the adversarial suite verify that slots are consumed even when the player is a plain Object with no apply_fusion_effect method?
**Assumption made:** Yes. Pass an Object that lacks apply_fusion_effect entirely. Verify: no crash, slots consumed (both empty after call). This is the exact path that triggers the push_error branch per spec FRH-3. The adversarial test documents this separately from the primary null-player test.

**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_DESIGN — PlayerDouble implementation strategy

**Would have asked:** Should the PlayerDouble for tracking `apply_fusion_effect` calls be a preloaded external script, an autoload, or an inner class on the test file?

**Assumption made:** Inner class on the test file (`class PlayerDouble extends Object`). This keeps the test file self-contained, avoids adding a new file to the repo, and matches GDScript's support for inner classes in headless test suites. The double extends `Object` (not `RefCounted`) to allow manual `free()` and avoid potential auto-free conflicts with the resolver.

**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_DESIGN — FRH-3-AC-11 call-order verification strategy

**Would have asked:** The spec mandates `apply_fusion_effect` is called before `consume_fusion_slots` (FRH-3-AC-11). How should this order be verified without a call-sequence interceptor?

**Assumption made:** Behavioral proxy: assert that `apply_fusion_effect_call_count >= 1` AND both slots are empty after `resolve_fusion`. These two facts can only co-exist if the effect was called (with slots still filled, which the internal guard checks) and then consume ran. No slot-state snapshot during the call is required. This conservative approach avoids adding complexity to the player double.

**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_DESIGN — FRH-2-AC-6 malformed manager simulation
**Would have asked:** FRH-2-AC-6 requires testing `can_fuse` when `get_slot(0)` returns null. MutationSlotManager never returns null for valid indices. How to simulate a malformed manager?

**Assumption made:** Pass a plain `Object.new()` (which has no `get_slot` method at all) to `can_fuse`. This is a strictly stricter case than a manager that returns null from `get_slot` — it tests the duck-typing null-safety guard more thoroughly. The spec says "malformed manager"; a missing method is the simplest headless-safe simulation of this.

**Confidence:** High

---

### [chunk_sticks_to_enemy] Test Break — double-attach same chunk to different enemies

**Would have asked:** If chunk_attached fires twice for the same chunk node (two different enemies contact the same in-flight chunk simultaneously), does the second attach overwrite the stored enemy reference, or is it silently ignored?

**Assumption made:** The second call to _on_enemy_chunk_attached fires the if/elif branch again (chunk == _chunk_node matches), so _chunk_stuck_enemy is overwritten to the second enemy. The stuck flag remains true. This means "last enemy wins." The absorb handler must match against the current _chunk_stuck_enemy reference.
**Confidence:** Medium

---

## Run: 2026-03-20 (Spec Agent — mutation_tease_room specification)

### [mutation_tease_room] Spec — MutationTeasePlatform X tolerance: ±2.0 vs ±1.0

**Would have asked:** The planning checkpoint notes Medium confidence on MutationTeasePlatform X ±2.0 m tolerance (scene shows X=0, ticket mentions X=3). Should the spec use ±1.0 m (matching MutationTeaseFloor) or ±2.0 m to account for potential future repositioning?
**Assumption made:** Used ±2.0 m for MutationTeasePlatform.position.x. The planning document explicitly chose a wider tolerance (Medium confidence) because the ticket's "X=3" description conflicts with the scene's X=0. The wider tolerance accommodates both the current scene value and the described intent without tightening to ±1.0 m prematurely. Scene value X=0.0 falls well within [-2.0, 2.0].
**Confidence:** Medium

### [mutation_tease_room] Spec — MTR-FLOW-1 uses <= not < for zone adjacency
**Would have asked:** MutationTeaseFloor right edge and FusionFloor left edge are both exactly 10.0. Should the flow assertion use <= (zones adjacent is valid) or < (strictly separated)?
**Assumption made:** Used <= for AC-MTR-FLOW-1.1. This is consistent with the ADV-MBA-06 resolution and Engine Integration Agent's relaxation of the mini-boss left-edge check for the same geometric reason: touching boundaries are valid zone adjacency, not overlap. Using < would produce a false failure on the current scene.
**Confidence:** High

### [mutation_tease_room] Spec — T-72 as traceability stub, not a real assertion

**Would have asked:** T-72 is listed in the test plan as covering MTR-GEO-1 collision_mask, but T-25 already covers this for all StaticBody3D nodes. Should T-72 emit a real assertion duplicating T-25, or be a stub?
**Assumption made:** T-72 is a stub only: calls _pass_test unconditionally with a NOTE comment pointing to T-25. This matches the T-43 NOTE and T-44 NOTE pattern established in the test suite. Emitting a real assertion would violate NFR-3 (no duplication with T-1 through T-62).
**Confidence:** High

### [mutation_tease_room] Spec — EnemyMutationTease distinctness check uses node.name not get_path()
**Would have asked:** T-70 / MTR-FLOW-2 must check that EnemyMutationTease is distinct from the other three enemies. Should it use node.name or node.get_path()? The mini-boss encounter spec uses node.name after discovering get_path() returns empty for non-tree nodes.
**Assumption made:** Used node.name for all distinctness comparisons in T-70 and ADV-MTR-04. This is consistent with the CHECKPOINT resolution for T-57 ([mini_boss_encounter] Implementation) and is documented in NFR-6 of this spec.
**Confidence:** High


### [mutation_tease_room] — OUTCOME: INTEGRATION
All 18 tests (T-63–T-72, ADV-MTR-01–06) passed first run with zero scene modifications. Ticket held at INTEGRATION pending human verification of AC-2 (visual tease clarity) and AC-5 (human-playable in-editor).

---
## Run: 2026-03-20T08:42:19-04:00
Queue mode: single ticket
Queue scope: project_board/4_milestone_4_prototype_level/in_progress/start_finish_flow.md

---
### [start_finish_flow] — OUTCOME: COMPLETE
Human verified full in-editor start-to-finish loop completed with no issues; ticket advanced to COMPLETE and moved to done.

---
## Run: 2026-03-20 (Planner Agent — start_finish_flow planning)

### [start_finish_flow] Planning — assumed completion path
**Assumption made:** `LevelExit` is treated as the completion trigger in the normal flow; the spec will not require that `EnemyMiniBoss` is dead unless code inspection shows `level_complete` is gated on mini-boss state.
**Confidence:** Medium

### [start_finish_flow] Planning — "critical UI/objectives" mapping
**Assumption made:** The human-playable clarity AC will be validated by observing existing in-scene UI prompts/labels: `AbsorbPromptLabel`, `FusePromptLabel`, `FusionActiveLabel`, and the mutation-slot labels/icons, plus infection visual feedback (enemy blinking / disappearing on dead). There is no dedicated "objective" system node in `containment_hall_01.tscn`, so objectives are represented by these UI cues.
**Confidence:** Medium

### [start_finish_flow] Planning — infect instruction risk
**Assumption made:** The UI currently does not display an explicit "infect" key hint (`infect` = `F` in `project.godot`); the flow-clarity spec will rely on enemy state feedback (blinking when weakened/infected) and the subsequent appearance of `AbsorbPromptLabel` after infect. If playtest shows confusion, a follow-up ticket should add an `InfectHint`/prompt.
**Confidence:** Medium

---
### [start_finish_flow] Spec — automated coverage vs manual-only ACs
**Assumption made:** This ticket's "start→finish flow" ACs are primarily validated via composition of existing automated suites (scene structural checks in `tests/levels/test_containment_hall_01.gd`, plus zone/UI suites for mutation tease, fusion opportunity, light skill check, and mini-boss). New headless tests for this ticket should therefore stay narrowly scoped to end-to-end wiring signals (UI prompt/hint presence + initial visibility, strict left-to-right zone ordering, respawn/exit trigger wiring).
**Assumption made:** "Objectives/clarity" has no dedicated objective system node in `containment_hall_01.tscn`; testable "objectives" are the existing UI cue nodes (`AbsorbPromptLabel`, `FusePromptLabel`, `FusionActiveLabel`, mutation-slot labels/icons) plus the always-present input hints.
**Assumption made:** The level-complete completion trigger is spatial (player entering `LevelExit`), and the spec will not require that `EnemyMiniBoss` is dead unless code inspection shows otherwise. As a result, "mini-boss is not skippable" must be checked during the required manual playthrough.
**Confidence:** Medium

---
## Run: 2026-03-20T17:33:59-04:00
Queue mode: single ticket
Queue scope: project_board/4_milestone_4_prototype_level/in_progress/mini_boss_encounter.md

### [mini_boss_encounter] INTEGRATION — Human verification required before COMPLETE
**Would have asked:** Did the human playtest satisfy AC-2 (winnable with movement + mutations, no softlock), AC-4 (defeat without mandatory fusion; difficulty not a barrier), and AC-5 (arena/boss/exit visually clear without debug overlays)?
**Assumption made:** None — ticket remains at `INTEGRATION` until explicit answers are recorded in the ticket `WORKFLOW STATE` / `Validation Status` (per Acceptance Criteria Gatekeeper rules).
**Confidence:** High

---

## Run: 2026-03-21T00:00:00Z (Autopilot resume — in_progress directory)
Queue mode: in_progress directory scan
Queue scope: project_board/4_milestone_4_prototype_level/in_progress/

### [start_finish_flow] — OUTCOME: COMPLETE
Ticket was already COMPLETE in done/ (completed during prior session). No further action needed.

---

## Run: 2026-03-21T12:00:00Z
Queue mode: all backlog (M5 + M6)
Queue scope: project_board/5_*/backlog/, project_board/6_*/backlog/

### [blender_parts_library] Planning — Blender not installed
**Would have asked:** Blender is not installed on this machine. Should we skip or block?
**Assumption made:** BLOCKED. No Blender = no .blend file authoring possible. Ticket set to BLOCKED.
**Confidence:** High

### [blender_python_generator] Planning — Blender not installed
**Would have asked:** Same as above — Blender required.
**Assumption made:** BLOCKED. Depends on Blender CLI. Ticket set to BLOCKED.
**Confidence:** High

### [godot_scene_generator_validation] Planning — No GLB assets exist
**Would have asked:** assets/enemies/generated_glb/ directory has no .glb files. Cannot validate the scene generator without input assets.
**Assumption made:** BLOCKED. Depends on blender_python_generator producing GLBs first.
**Confidence:** High

### [first_4_families_in_level] Planning — No GLB assets exist
**Would have asked:** Placing enemy variants requires generated .glb scenes that don't exist yet.
**Assumption made:** BLOCKED. Depends on godot_scene_generator_validation producing .tscn scenes first.
**Confidence:** High

---

## Run: 2026-03-21 (Planner Agent — enemy_base_script planning)

### [enemy_base_script] Planning — extends CharacterBody3D vs extends Node3D
**Would have asked:** load_assets.gd uses `USE_CHARACTER_BODY = true` and creates a CharacterBody3D root, then calls `root.set_script(script_res)`. Should enemy_base.gd extend CharacterBody3D directly, or extend Node3D (more general)?
**Assumption made:** enemy_base.gd extends CharacterBody3D. The ticket AC explicitly states "attaches cleanly to CharacterBody3D generated scenes" and load_assets.gd creates CharacterBody3D roots. Extending CharacterBody3D ensures @export vars are resolved at attach-time and the script is structurally correct for the generated scene root type. A Node3D base would lose type safety.
**Confidence:** High

### [enemy_base_script] Planning — State enum mapping to EnemyStateMachine string states
**Would have asked:** EnemyStateMachine uses String constants ("idle", "active", "weakened", "infected", "dead"). The ticket requires a State enum: NORMAL, WEAKENED, INFECTED. Should the enum map exactly to the ESM string states, or is it an independent display-layer enum?
**Assumption made:** The State enum is an independent display/gameplay layer enum on enemy_base.gd. It is NOT a replacement for EnemyStateMachine's internal string states. The three enum values (NORMAL, WEAKENED, INFECTED) map to the ESM-driven concept that external systems (procedurally generated enemies) care about: normal behavior, weakened, or infected/absorb-ready. The base script will expose a `set_state(state: State)` hook and a `get_base_state() -> State` accessor. The ESM continues to own lifecycle state internally; the base script enum is the public contract for procedural enemies.
**Confidence:** Medium

### [enemy_base_script] Planning — No class_name conflict with EnemyInfection3D
**Would have asked:** EnemyInfection3D extends BasePhysicsEntity3D (which extends CharacterBody3D). If enemy_base.gd also extends CharacterBody3D with class_name EnemyBase, is there a conflict?
**Assumption made:** No conflict. EnemyInfection3D extends BasePhysicsEntity3D, not EnemyBase. They are parallel hierarchies: existing enemies use BasePhysicsEntity3D; procedurally generated enemies use EnemyBase. No existing file is modified.
**Confidence:** High

### [enemy_base_script] Planning — Headless testability: CharacterBody3D instantiation in tests
**Would have asked:** CharacterBody3D requires a physics server RID. Can it be instantiated headlessly in tests/run_tests.gd without causing a crash or hang?
**Assumption made:** Yes — the project already instantiates CharacterBody3D headlessly in multiple test files (e.g., `test_3d_scene.gd` adds a full level with physics nodes to the tree). CharacterBody3D instantiation in headless mode allocates a physics RID but does not crash. Physics simulation does not run without a physics tick, so the character just stays at its spawn position. All existing test patterns confirm this is safe.
**Confidence:** High

---

## Run: 2026-03-21 (Spec Agent — soft_death_and_restart specification)

### [soft_death_and_restart] Spec — Slot manager object identity: RSM internal vs InfectionInteractionHandler
**Would have asked:** Is `RunStateManager._slot_manager` the same object reference as `InfectionInteractionHandler._slot_manager`? If so, RSM's `apply_event("player_died")` calling `clear_all()` would be sufficient. If not, the coordinator must also call `clear_all()` on the handler's manager.
**Assumption made:** They are distinct objects. Confirmed by reading both source files: `RunStateManager._init()` calls `_slot_manager = preload(...).new()` and `InfectionInteractionHandler._ready()` calls `_slot_manager = _MutationSlotManagerScript.new()`. Each creates a separate instance. The coordinator must explicitly call `handler_node.get_mutation_slot_manager().clear_all()` in `_reset_run()` to clear the scene's active slot manager. RSM's internal `clear_all()` only affects RSM's own instance (used for headless test verification only).
**Confidence:** High

### [soft_death_and_restart] Spec — RSM state after _reset_run: DEAD→START vs DEAD→ACTIVE
**Would have asked:** After `_reset_run()` fires, should RSM be in START state or ACTIVE state? The task prompt specifies only `apply_event("restart")`, which moves RSM DEAD→START. But for the next death cycle to be detectable, RSM must be ACTIVE.
**Assumption made:** `_reset_run()` must call both `apply_event("restart")` (DEAD→START) and `apply_event("start_run")` (START→ACTIVE). Both calls are required. Without `apply_event("start_run")`, the coordinator's `_process()` check (`_rsm.get_state() == ACTIVE`) would never re-arm, and the next death would not be detected. This is consistent with `_ready()` also calling `apply_event("start_run")` for initial activation.
**Confidence:** High

### [soft_death_and_restart] Spec — _on_player_died double-fire guard: RSM state guard vs _dead flag
**Would have asked:** The task prompt specifies `if _dead: return` inside `_on_player_died()`. Is this redundant given that `_process()` already guards on `_dead` before calling `apply_event("player_died")`?
**Assumption made:** Not redundant. The `_process()` guard prevents double `apply_event("player_died")` calls. The `if _dead: return` guard inside `_on_player_died()` prevents the callback itself from being executed twice (e.g., if the signal were connected multiple times or called from a code path other than `_process()`). Both guards serve distinct purposes and are both required.
**Confidence:** High

### [soft_death_and_restart] Spec — Tween ownership: player_node.create_tween() vs coordinator create_tween()
**Would have asked:** Should the dissolve tween be created on the coordinator (`self.create_tween()`) or on the player node (`player_node.create_tween()`)? The choice affects pause behavior and tween lifecycle.
**Assumption made:** Tween created on `player_node` via `player_node.create_tween()`. This binds the tween lifecycle to the player node, which is consistent with how all other juice tweens are created in `player_controller_3d.gd` (see `_juice_jump_stretch()`, `_juice_land_squash()`, etc.). The player node is never freed or paused in this ticket, so both approaches would behave identically at runtime. Using the player node follows the project's established pattern.
**Confidence:** High

---

## Run: 2026-03-21 (Test Designer Agent — soft_death_and_restart SDR-* + ADV-SDR-* test suites)

### [soft_death_and_restart] TestDesign — SDR-COORD-5 spec gap: _process_death_check vs _process
**Would have asked:** The task prompt defines SDR-COORD-5 as "RSM reaches DEAD state after `_process_death_check()` called with HP=0" but the spec defines no method named `_process_death_check()`. The actual detection method is `_process(delta)`. Should SDR-COORD-5 call `_process()` directly, or is there a separate private extraction?
**Assumption made:** Used direct RSM manipulation (`rsm.apply_event("player_died")`) to verify the DEAD state transition, rather than calling a non-existent `_process_death_check()`. This tests the same observable outcome (RSM in DEAD after player death signal) without depending on an internal method that the spec does not define. The SDR-PROC-1 test ID (calling `_process(0.016)`) is the correct spec-aligned test for the detection path; SDR-COORD-5 tests the RSM state contract.
**Confidence:** High

### [soft_death_and_restart] TestDesign — _on_player_died() requires SceneTree for get_tree().create_timer()
**Would have asked:** ADV-SDR-01 calls `_on_player_died()` twice. The first call invokes `get_tree().create_timer(1.5)`. Does this crash if the coordinator is not in a SceneTree? Should the test skip or add the coordinator to tree.root?
**Assumption made:** Added the coordinator to `tree.root` before calling `_on_player_died()` in ADV-SDR-01. This follows the same pattern used in `tests/scenes/levels/test_3d_scene.gd` for physics-requiring tests. If `Engine.get_main_loop()` returns null (non-SceneTree context), the test prints a SKIP message instead of crashing. The timer created by the first call is harmless in the test context because `_reset_run()` (the timer callback) requires a player NodePath which is not configured.
**Confidence:** High

### [soft_death_and_restart] TestDesign — test file name: test_soft_death_and_restart.gd vs test_death_restart_coordinator.gd
**Would have asked:** The task prompt specifies the output path as `tests/system/test_soft_death_and_restart.gd` but the ticket NEXT ACTION block shows `tests/system/test_death_restart_coordinator.gd`. Which name governs?
**Assumption made:** Used `tests/system/test_soft_death_and_restart.gd` per the explicit task prompt instruction ("Write: tests/system/test_soft_death_and_restart.gd"). The ticket NEXT ACTION appears to be an earlier draft that was superseded. The file covers both the coordinator tests and the broader SDR-* test matrix, making the broader name more accurate.
**Confidence:** High

### [soft_death_and_restart] TestDesign — PlayerController3D global_position requires SceneTree
**Would have asked:** reset_position() tests (SDR-P1-4, SDR-P1-5, ADV-SDR-02) assign `global_position` which requires the node to be inside a SceneTree. The task prompt says to use `Engine.get_main_loop().root.add_child(player)`. Does this work in headless Object-based tests (not SceneTree-based tests)?
**Assumption made:** Yes — the test runner runs as a SceneTree (`run_tests.gd extends SceneTree`), so `Engine.get_main_loop() as SceneTree` returns a valid tree in all test runs. Pattern confirmed by `tests/scenes/levels/test_3d_scene.gd` lines 201-213. All three position tests use the add_child/remove_child/free cleanup cycle.
**Confidence:** High

---

## Run: 2026-03-21 (Planner Agent — room_template_system planning)

### [RTS] Planning — Room scene directory
**Would have asked:** Where should room scenes live — `scenes/rooms/` (flat), `scenes/levels/rooms/` (under levels), or another path?
**Assumption made:** `scenes/rooms/` as a sibling of `scenes/levels/`. Rooms are reusable building blocks, not individual levels. Keeping them separate from `scenes/levels/` (which contains monolithic prototype levels) prevents naming conflicts and signals the procedural-vs-hand-authored distinction. The procedural_room_chaining system will reference this path directly.
**Confidence:** High

### [RTS] Planning — Standard room width
**Would have asked:** What is the canonical room width in world units? The containment_hall_01 zones range from 15 to 25 units wide. Should all rooms be the same width, or can it vary by category?
**Assumption made:** Standard width is 30 units for all rooms. Rationale: the largest zone (MiniBossFloor, FusionFloor) is 25 units; 30 units provides comfortable margin without being too large. Entry marker at X=0, Exit marker at X=30 for all rooms. The boss room may be wider (40 units) to allow arena maneuvering — this is the only permitted exception, documented in the spec.
**Confidence:** Medium

### [RTS] Planning — Entry and Exit Marker3D positions within each room
**Would have asked:** Should Entry be at X=0 or at the left edge of the room floor? Should Exit be at X=room_width or at the right edge of the room floor?
**Assumption made:** Entry Marker3D at local position (0, 1, 0) — X=0 is the left edge of the room, Y=1 places the player 1m above the floor top surface (consistent with SpawnPosition in containment_hall_01). Exit Marker3D at (30, 1, 0) for standard rooms, (40, 1, 0) for boss room. Both markers are direct children of the room root node. Floor top surface at world Y=0, so Y=1 for markers is consistent with the existing SpawnPosition convention.
**Confidence:** High

### [RTS] Planning — What nodes rooms should NOT contain
**Would have asked:** Should rooms contain RespawnZone, Player3D, InfectionInteractionHandler, WorldEnvironment, or GameUI? These are present in containment_hall_01 but would be redundant (or conflict with) the level controller's scene.
**Assumption made:** Rooms are minimal self-contained geometry+enemy containers. They must NOT include: Player3D, RespawnZone, InfectionInteractionHandler, GameUI/InfectionUI. They MUST include: Entry Marker3D, Exit Marker3D, floor geometry (StaticBody3D), WorldEnvironment, DirectionalLight3D (so rooms are visually correct when previewed standalone), and any enemies appropriate to the category. The level controller injects player and systems when assembling the run. WorldEnvironment and DirectionalLight3D are kept in room scenes for standalone editor previewing; the level controller can suppress duplicates if needed.
**Confidence:** Medium

### [RTS] Planning — Minimum room set required by this ticket
**Would have asked:** The ticket says minimum 1 intro, 2 combat, 1 mutation_tease, 1 boss. The description says categories: intro (1), combat (3+), mutation_tease (2), fusion_opportunity (1), cooldown (1), boss (1). Should we target the minimum or the full set?
**Assumption made:** Target the minimum required by the ticket Acceptance Criteria: 1 intro, 2 combat, 1 mutation_tease, 1 boss — 5 rooms total. Additional rooms (fusion_opportunity, cooldown, 3rd combat) are deferred to follow-up tickets or future iterations. This minimizes implementation scope while satisfying all ACs and unblocking procedural_room_chaining.
**Confidence:** High

### [RTS] Planning — Room naming convention
**Would have asked:** What file naming convention should rooms follow? `room_combat_01.tscn`? `combat_room_01.tscn`? Something else?
**Assumption made:** File naming: `room_<category>_<variant_number>.tscn` in lowercase with underscores. Examples: `room_intro_01.tscn`, `room_combat_01.tscn`, `room_combat_02.tscn`, `room_mutation_tease_01.tscn`, `room_boss_01.tscn`. Root node name mirrors the file name in PascalCase: `RoomIntro01`, `RoomCombat01`, etc. This is consistent with the project's existing scene naming (e.g., `containment_hall_01.tscn` → root `ContainmentHall01`).
**Confidence:** High

### [RTS] Planning — Test file location
**Would have asked:** Where should room template tests live — `tests/rooms/` (new directory), `tests/levels/` (alongside containment_hall tests), or `tests/scenes/`?
**Assumption made:** `tests/rooms/` as a new top-level test subdirectory. This mirrors the source structure (`scenes/rooms/`), keeps room tests separate from level tests, and the test runner auto-discovers all `test_*.gd` files recursively from `tests/` so no runner change is needed.
**Confidence:** High

### [RTS] Planning — Whether rooms need enemies at all
**Would have asked:** The intro room should be enemy-free (safety zone). The combat rooms need enemies. Should enemy instances be authored directly into room scenes, or should they be spawned at runtime by a room controller script?
**Assumption made:** Enemies authored directly into room `.tscn` files as instanced sub-scenes (same pattern as containment_hall_01). No room controller script is needed for this ticket — runtime enemy spawning is a future concern. The intro room has no enemies. Combat rooms have 1 enemy each. Mutation tease has 1 enemy on an elevated platform (mirrors MutationTeasePlatform pattern). Boss has 1 boss enemy (scaled like EnemyMiniBoss in containment_hall_01).
**Confidence:** High

---

## Run: 2026-03-21 (Spec Agent — room_template_system specification)

### [RTS] Spec — Enemy scene path: scenes/enemy_infection_3d.tscn vs scenes/enemy/enemy_infection_3d.tscn
**Would have asked:** Two files exist on disk: `scenes/enemy_infection_3d.tscn` (root-level) and `scenes/enemy/enemy_infection_3d.tscn` (subdirectory). `containment_hall_01.tscn` references `res://scenes/enemy/enemy_infection_3d.tscn`. The ticket Task 3 also specifies `res://scenes/enemy/enemy_infection_3d.tscn`. Which path is canonical for new room scenes?
**Assumption made:** `res://scenes/enemy/enemy_infection_3d.tscn` is canonical. Both `containment_hall_01.tscn` (existing level) and the ticket's Task 3 instructions agree on this path. The root-level `scenes/enemy_infection_3d.tscn` is likely a stale duplicate or un-relocated copy. All new room scenes must use `res://scenes/enemy/enemy_infection_3d.tscn`.
**Confidence:** High

---

## Run: 2026-03-21 (Test Designer Agent — room_template_system RTS-* test suites)

### [RTS] TestDesign — RTS-ENC enemy scene path: runtime property vs .tscn file text
**Would have asked:** After `PackedScene.instantiate()`, there is no standard runtime API to read an instanced node's source .tscn path. The spec (RTS-ENC risk section) says to use `FileAccess.open` to read the .tscn as text and check for `enemy_infection_3d.tscn`. Is this acceptable, or should the test use indirect behavioral evidence (e.g., checking for a script method that only the enemy scene provides)?
**Assumption made:** Used `FileAccess.open` + substring search for `"enemy_infection_3d.tscn"` in the room's .tscn file text. This is the approach explicitly recommended by the spec. It is headless-safe, deterministic, and directly verifies the ext_resource declaration without depending on a specific script API that could change. The check runs after `root.free()` so it does not conflict with the live instantiation.
**Confidence:** High

### [RTS] TestDesign — RTS-ADV-6 scope: direct children only vs full recursive walk
**Would have asked:** The spec's RTS-ADV-6 risk note says to restrict the collision_mask check to StaticBody3D nodes that are direct children of the room root, not nodes inside instanced enemy sub-scenes. However, the primary acceptance criteria says "every StaticBody3D node in the tree". Which governs?
**Assumption made:** The risk note governs. The spec explicitly calls out that enemy sub-scenes have their own collision_mask contract and restricts the room-level check to direct children. Using a full recursive walk would cause false failures if the enemy scene uses a different collision_mask (e.g., 2 for the enemy layer). The adversarial test uses `_get_direct_static_bodies(root)` which iterates only `root.get_child(i)`.
**Confidence:** High

### [RTS] TestDesign — RTS-ADV-1/2 duplicate pass record when all_pass is true
**Would have asked:** The per-room loop records individual pass/fail, then a second _pass_test is recorded at the end if all_pass is true. This means a fully-passing run records both per-room passes and an "all rooms" summary pass. Is double-counting acceptable?
**Assumption made:** Acceptable. The per-room pass records are granular diagnostic output (useful for debugging partial failures). The summary pass record is a single contract assertion matching the spec's "for all 5 rooms" language. This matches the pattern used in other suites (e.g., test_containment_hall_01.gd T-25 records per-node passes inside the loop plus a summary). The _pass_count inflation is harmless — only _fail_count is returned.
**Confidence:** High

---

## Run: 2026-03-21 (Planner Agent — procedural_room_chaining planning)

### [PRC] Planning — Sequence mismatch: "fusion room" in AC not present in room pool
**Would have asked:** The ticket description says "intro → N combat rooms → mutation tease → fusion room → boss" but the available room template pool has no fusion room scene. The room_template_system produced: 1 intro, 2 combat, 1 mutation_tease, 1 boss. Should the sequence include a fusion room slot (blocking until a scene is authored), or treat the current sequence as intro → combat (2) → mutation_tease → boss?
**Assumption made:** Treat the sequence as intro (1) → combat (2) → mutation_tease (1) → boss (1), totaling 4 rooms. The "fusion room" in the ticket description refers to a room type that does not yet exist in the template pool. The PRC system must be built against the 4-room sequence that is actually available. A follow-up ticket (add fusion room template + extend sequence) will address this. This decision is logged here as a CHECKPOINT and referenced in the spec so Spec Agent documents it explicitly.
**Confidence:** High

### [PRC] Planning — RoomChainGenerator scope: pure list vs scene instantiation
**Would have asked:** Should `RoomChainGenerator` (extends RefCounted) only produce an Array of scene-path records (pure logic, no SceneTree API), or should it also call `ResourceLoader.load()` and return PackedScenes?
**Assumption made:** `RoomChainGenerator` produces only an `Array[Dictionary]` of records — each record contains `{ "scene_path": String, "category": String }`. It does NOT call `ResourceLoader.load()`, does NOT instantiate scenes, and does NOT touch the SceneTree. All scene loading and Node3D positioning is the responsibility of a separate engine-integration layer (a `RunSceneAssembler` Node that consumes the array). This preserves headless testability of the pure-logic class.
**Confidence:** High

### [PRC] Planning — Invocation point: DeathRestartCoordinator vs new RunManager
**Would have asked:** Where is `RoomChainGenerator` invoked — inside `DeathRestartCoordinator._reset_run()` (adding to an existing node), or by a new `RunManager` Node that owns the room chain lifecycle?
**Assumption made:** Invoked by a new `RunSceneAssembler` Node (not `DeathRestartCoordinator`). Reasoning: `DeathRestartCoordinator` already has a well-defined single responsibility (death detection and player reset). Adding room chain assembly to it would violate SRP and require modifying a stable, tested file. The new `RunSceneAssembler` is a separate Node in the level scene that listens to `RunStateManager.run_started` and triggers room assembly. `DeathRestartCoordinator._reset_run()` emits the restart event via RSM; `RunSceneAssembler` listens and rebuilds rooms. This keeps each component's blast radius minimal.
**Confidence:** Medium

### [PRC] Planning — "No room repeated" test strategy with only 2 combat rooms drawing 2
**Would have asked:** The AC says "no room repeated in a single run." The combat pool has exactly 2 rooms and we draw exactly 2. With only 2 items in the pool, deduplication is trivially guaranteed — there is literally no other option. Should the test be: (a) a pure unit test that verifies the generator uses shuffle+take-without-replacement, or (b) a property-based test that runs the generator with a custom 3-room pool and verifies no repeats appear when drawing 2?
**Assumption made:** Both. PRC-SEQ-4 tests the actual 2-room pool (all 2 combat rooms appear, no repeat possible). PRC-ADV-3 tests the deduplication logic with a synthetic 4-room combat pool where a naive random.randi_range implementation WOULD produce repeats, verifying the shuffle-without-replacement algorithm is correct independently of pool size. This separates the correctness of the sequence (PRC-SEQ) from the correctness of the deduplication algorithm (PRC-ADV).
**Confidence:** High

### [PRC] Planning — Room positioning: Exit.x as anchor for next room Entry.x
**Would have asked:** All rooms have Entry at local (0,1,0) and the room root is a Node3D. The context says "Room N's Exit.x position defines where Room N+1's Entry.x starts." In practice: room_root_N+1.position.x = room_root_N.position.x + exit_N.position.x. Is this the correct formula, and does it assume Entry is always at local x=0?
**Assumption made:** Yes. The formula for placing Room N+1 is: `room_root_N1.position.x = room_root_N.position.x + exit_N_local.position.x`. Since Entry for all rooms is at local (0,1,0), placing the root at the world X where the previous room's Exit lands is sufficient. The y-axis placement follows the same pattern (room roots at Y=0 so Entry at world Y=1). This is documented in the spec as an invariant.
**Confidence:** High

---

## Run: 2026-03-21 (Spec Agent — procedural_room_chaining specification)

### [PRC] Spec — Sequence length 4 vs 5
**Would have asked:** The ticket description prose says "4 rooms total" but the Required Input Schema lists `run_sequence: ["intro","combat","combat","mutation_tease","boss"]` which has 5 elements. Which is authoritative?
**Assumption made:** The `run_sequence` array in the Required Input Schema is authoritative — 5 elements, 5 rooms. The prose "4 rooms total" was counting 4 distinct template categories (intro pool, combat pool, mutation_tease pool, boss pool) rather than 5 slots. All spec requirements use 5 as the run length. `generate()` returns an Array of length 5.
**Confidence:** High

### [PRC] Spec — RSM ownership: RunSceneAssembler creates its own RSM
**Would have asked:** `DeathRestartCoordinator` owns a private `_rsm: RunStateManager` instance that is inaccessible. `RunSceneAssembler` needs to connect to `run_started` and `run_restarted`. Should it share the DRC's RSM (requires modifying DRC), or create its own?
**Assumption made:** `RunSceneAssembler` creates its own `RunStateManager` instance in `_ready()`. Modifying `DeathRestartCoordinator` is explicitly prohibited. The two RSMs are independent lifecycles: DRC manages death/restart state; RSA manages room assembly state. Integration between DRC restart and RSA room rebuild is deferred to a future integration ticket. The `rsm_path` export is retained as a future hook but is unused in the initial implementation.
**Confidence:** Medium

### [PRC] Spec — Node strip strategy: free() before add_child vs queue_free() after add_child
**Would have asked:** Should WorldEnvironment and DirectionalLight3D be stripped from room instances before or after adding them to the SceneTree? Before (using free()) avoids any brief period where duplicate lights exist; after (using queue_free()) is safer if the node needs to be in-tree first.
**Assumption made:** Strip before add_child using `free()` (synchronous, immediate). The nodes are freshly instantiated and not yet in any tree, so `free()` is safe and avoids any single-frame duplicate-WorldEnvironment state. This is the conservative approach specified in the task prompt.
**Confidence:** High

### [PRC] Spec — Exit marker fallback value: 30.0 units
**Would have asked:** If a room instance has no "Exit" Marker3D child (e.g., due to a future malformed room scene), what should `cumulative_x` advance by?
**Assumption made:** Fall back to 30.0 world units (the standard room width confirmed for 4 of 5 existing rooms) and emit `push_warning()`. This prevents silent zero-advancement that would cause all rooms to stack at the same X position. The fallback is documented in the spec and the implementer must emit the warning.
**Confidence:** High

---

## Run: 2026-03-22 (Spec Agent — procedural_room_chaining specification revision 2)

### [PRC] Spec Rev2 — API signature changed: generate(sequence, pool, seed) replaces generate(seed)
**Would have asked:** Revision 1 specified `generate(seed: int) -> Array` returning Dicts. The ticket's current Required Input Schema specifies `generate(sequence: Array[String], pool: Dictionary, seed: int) -> Array[String]`. Which is authoritative when the two specs conflict?
**Assumption made:** The ticket's Required Input Schema governs. Revision 1 was written before the schema was finalized. Revision 2 supersedes Revision 1 entirely. The new signature accepts sequence and pool as parameters (caller-supplied) rather than having them hardcoded in the class. This makes `RoomChainGenerator` more reusable and testable in isolation. The return type is `Array[String]` (scene paths only, no Dicts). All Revision 1 test IDs (PRC-SEQ-*, PRC-DEDUP-*, PRC-SCHEMA-*, PRC-POOL-*) are superseded by PRC-GEN-*, PRC-SEED-*, PRC-ADV-*.
**Confidence:** High

### [PRC] Spec Rev2 — Input validation: empty category returns [] vs partial array
**Would have asked:** When a pool category is empty (or missing), should `generate()` return `[]` (abort entirely) or the partial array built before the error was encountered?
**Assumption made:** Two distinct behaviors: (a) empty/missing pool category discovered during the initial validation phase (before any draws happen) → return `[]`. (b) pool exhaustion discovered during draw phase (after some items have been drawn) → return partial array. This distinction allows callers to distinguish "invalid pool" from "pool ran out mid-sequence." Both cases emit `push_error`.
**Confidence:** Medium

### [PRC] Spec Rev2 — rsm_path export removed from RunSceneAssembler
**Would have asked:** Revision 1 kept `rsm_path: NodePath` as a "future integration hook" on RunSceneAssembler. The new ticket schema does not mention this export. Should it be retained for future compatibility, or removed to keep the API minimal?
**Assumption made:** Removed in Revision 2. The export was never used (assembler creates its own RSM internally) and added confusion about what the export does. Keeping unused exports violates the project's code style of minimal, purposeful declarations. Future integration will add the export back when it has a concrete use case.
**Confidence:** High

### [PRC] Spec Rev2 — PRC-SEED-2 seed pair validity (seeds 1 and 999999)
**Would have asked:** The ticket specifies seeds 1 and 999999 as the concrete test pair for PRC-SEED-2 (different seeds produce different outputs). With a 2-item combat pool, there is ~50% probability these two seeds produce the same output. Are seeds 1 and 999999 guaranteed to diverge?
**Assumption made:** Declared the seed pair as provisional — the Test Designer Agent must verify at implementation time by running `RoomChainGenerator.new().generate(SEQUENCE, POOL, 1)` and `RoomChainGenerator.new().generate(SEQUENCE, POOL, 999999)` and confirming divergence. If they converge, the agent must file a CHECKPOINT with an alternate pair. The spec uses seeds 1 and 999999 per the ticket instruction but explicitly calls this out as a pre-computation requirement.
**Confidence:** Medium

---

## Run: 2026-03-22 (Test Designer Agent — procedural_room_chaining test suite)

### [PRC] Test Design — PRC-GEN-7 definition conflict between task brief and spec Rev2
**Would have asked:** The task brief maps PRC-GEN-7 to "pool has category with empty array [] → generate() returns []". The authoritative spec Rev2 maps PRC-GEN-7 to "pool has 1 combat item, sequence requests it twice → partial array + push_error" (pool exhaustion mid-draw). The task brief's PRC-GEN-7 behavior (empty array → []) is actually covered by PRC-GEN-6 in the spec. Which definition governs?
**Assumption made:** The authoritative spec Rev2 governs. PRC-GEN-7 tests the pool-exhaustion mid-sequence partial-return behavior. The task brief appears to have an off-by-one shift in test ID assignments for error cases. The empty-array-returns-[] case is covered by PRC-GEN-6 (which matches both the task brief and the spec). PRC-GEN-7 follows the spec's definition for pool exhaustion → partial array.
**Confidence:** High

### [PRC] Test Design — PRC-SEED-2 seed pair cannot be pre-computed (red phase)
**Would have asked:** The spec and Spec Agent's checkpoint both require the Test Designer Agent to pre-compute whether seeds 1 and 999999 produce diverging combat orderings before writing PRC-SEED-2. Since `RoomChainGenerator` does not exist yet (red phase), this pre-computation is impossible.
**Assumption made:** The test is written with seeds 1 and 999999 per the task spec. If both seeds happen to produce the same combat ordering on a correct implementation, the Test Breaker Agent or Implementation Agent must identify the collision and file a new CHECKPOINT with a confirmed diverging seed pair. The test includes a comment documenting this theoretical ~50% false-failure risk for 2-item pools.
**Confidence:** Medium

### [PRC] Test Design — PRC-ADV-10 acceptance: [] vs partial both valid
**Would have asked:** PRC-ADV-10 says "returns [] or partial (no crash)". The spec's validation phase logic states missing key returns [] (not partial). Should the test assert exactly [] or accept both outcomes?
**Assumption made:** The test accepts any non-null Array (including []) as a passing outcome. The primary observable requirement is no crash. If the implementation Agent produces exactly [] (per spec validation-phase abort), the test passes. If it produces a partial array due to a different implementation strategy, the test also passes — the no-crash contract is met. A stricter assertion of exactly [] would be a PRC-ADV-10b test that the Test Breaker Agent can add.
**Confidence:** Medium


## Run: 2026-03-23T00:00:00Z — Autopilot M5 Procedural Enemy Generation
Queue mode: milestone directory
Queue scope: project_board/5_milestone_5_procedural_enemy_generation/backlog/

### [M5-INIT] Step 0 — Stale backlog stub
**Would have asked:** backlog/enemy_base_script.md is a short stub with no WORKFLOW STATE; done/enemy_base_script.md is COMPLETE (Stage: COMPLETE, 253/253 tests passing). Should the stub be deleted?
**Assumption made:** The backlog stub is superseded. Left in place but skipped by autopilot (no WORKFLOW STATE block = already handled). Processing begins at blender_parts_library.
**Confidence:** High

### [M5-INIT] Step 0 — Unblocking Blender tickets
**Would have asked:** blender_parts_library and blender_python_generator were BLOCKED on Blender installation. Now that Blender is installed, should they move to backlog?
**Assumption made:** Yes — moved both to backlog/. godot_scene_generator_validation and first_4_families_in_level remain in blocked/ because they depend on GLB outputs that don't exist yet. They will be moved to backlog/ after blender_python_generator completes.
**Confidence:** High

---

## Run: 2026-03-23 (Spec Agent — blender_parts_library specification)

### [BPL] Spec — ico_sphere subdivisions=2 would exceed triangle budget
**Would have asked:** `primitive_ico_sphere_add(subdivisions=2)` produces 320 triangles (20 base * 4^2 = 320), which far exceeds `MAX_TRIANGLES_PER_PART = 100`. The Planner's planning checkpoint listed `subdivisions=1` (80 tris) as the conservative setting. Should `OrbCore` use `subdivisions=1` (same as `BaseSphere`) or a different primitive to visually differentiate the two parts?
**Assumption made:** Both `BaseSphere` and `OrbCore` use `primitive_ico_sphere_add(subdivisions=1)`. They are visually identical at the mesh level but are distinct named objects in the collection. Their visual differentiation is a material/transform concern for downstream usage, not a geometry concern for the parts library. Using identical geometry for two logically different parts is acceptable in a library that is a building block for further procedural assembly. The spec documents this explicitly as a known simplification.
**Confidence:** High

### [BPL] Spec — parents[4] depth: confirmed for asset_generation/python/src/enemies/ path
**Would have asked:** The `OUTPUT_PATH` resolution uses `Path(__file__).resolve().parents[4]` to reach the repo root. Is this the correct depth for the path `asset_generation/python/src/enemies/build_parts_library.py`?
**Assumption made:** `parents[4]` is correct. The path from repo root: `asset_generation/` (parents[3]) / `python/` (parents[2]) / `src/` (parents[1]) / `enemies/` (parents[0]) / `build_parts_library.py` (__file__). So `parents[4]` = repo root (`blobert/`). Verified by counting: `parents[0]` = enemies dir, `parents[1]` = src dir, `parents[2]` = python dir, `parents[3]` = asset_generation dir, `parents[4]` = repo root. Correct.
**Confidence:** High

### [BPL] Spec — tests/enemies/ __init__.py: required for pytest package discovery
**Would have asked:** Does `asset_generation/python/tests/enemies/` need an `__init__.py` file to allow `from src.enemies.build_parts_library import ...` imports in pytest? The existing test directories (combat/, animations/, level/, player/, prefabs/) all have `__init__.py` files.
**Assumption made:** Yes, `__init__.py` is required. Confirmed by inspection: every existing subdirectory under `asset_generation/python/tests/` has an `__init__.py`. The `pyproject.toml` sets `pythonpath = ["."]` which resolves `from src.enemies...` but the test package itself needs `__init__.py` for proper collection. Spec mandates creation of `asset_generation/python/tests/enemies/__init__.py`.
**Confidence:** High

### [BPL] Spec — torus triangulation formula: major_segments * minor_segments * 2
**Would have asked:** The torus primitive `primitive_torus_add(major_segments=8, minor_segments=4)` creates 8*4=32 quads. Each quad becomes 2 triangles in the fan-triangulation formula `sum(len(p.vertices)-2 for p in polygons)` — for a quad, `4-2=2`. So total is 32*2=64 triangles. Is this correct?
**Assumption made:** Yes — 32 quads * 2 = 64 triangles. This is well under 100. Confirmed by the formula: each polygon in a torus from `primitive_torus_add` is a quad (4 vertices), and `len([v0,v1,v2,v3]) - 2 = 2` per polygon. Torus with major_segments=8, minor_segments=4 has 8*4=32 quad faces = 64 triangles.
**Confidence:** High

### [BPL] Spec — Wing plane triangle count: 1 quad = 2 triangles
**Would have asked:** `primitive_plane_add(size=2.0)` creates a single quad polygon (4 vertices, 1 face). The fan-triangulation formula gives `4-2=2` triangles. Does Blender's plane add additional subdivisions by default?
**Assumption made:** No subdivisions by default — `primitive_plane_add` with no `subdivisions_x`/`subdivisions_y` arguments creates a single quad face (1 polygon). Triangle count = 2. If subdivision arguments are accidentally added, the count changes. The spec mandates the call `primitive_plane_add(size=2.0)` with no subdivision arguments.
**Confidence:** High

---

## Run: 2026-03-23 (Test Designer Agent — BPL test authoring)

### [BPL] Test Design — Integration test Blender invocation cwd
**Would have asked:** When the integration test calls `blender --background --python <script>`, what should the subprocess working directory be? The script uses `__file__`-relative path resolution, so cwd should not matter — but the test must confirm this.
**Assumption made:** Set subprocess cwd to the repo root (`Path(__file__).resolve().parents[5]` from the test file location at `asset_generation/python/tests/enemies/`). This is the safest choice and matches how `blender --background` would naturally be invoked from the project. The script's `OUTPUT_PATH` uses `__file__`-anchored resolution, so cwd is irrelevant to correctness, but explicit cwd avoids ambiguity.
**Confidence:** High

### [BPL] Test Design — pytest markers: integration marker registration
**Would have asked:** The project has no existing `@pytest.mark.integration` usage or marker registration in pyproject.toml. Should the integration test register the marker to avoid pytest warnings, or add it to pyproject.toml?
**Assumption made:** Add `filterwarnings` and `markers` config to pyproject.toml is out of Test Designer scope (that's a project config change). Instead, use `pytestmark` at the module level, and note in a comment that the CI runner should pass `-m integration` to run them and `-m "not integration"` to skip. This is the minimal correct approach. The missing marker registration does not cause test failure — only a warning.
**Confidence:** Medium

### [BPL] Test Design — TestPartsCollectionVerification inline Blender script approach
**Would have asked:** Should `TestPartsCollectionVerification` use `--python-expr` (inline Python expression) or a temp file with `--python`? The spec says "inline via --python-expr or temp file". `--python-expr` is limited and awkward for multi-line logic.
**Assumption made:** Use a `tempfile.NamedTemporaryFile` with `.py` suffix containing the verification script, passed via `--python`. This is more readable, debuggable, and reliable than `--python-expr`. The temp file is cleaned up after the subprocess exits.
**Confidence:** High


### [M5-CORRECTION] Pipeline Discovery — blender_parts_library superseded
**Would have asked:** The blender_parts_library and blender_python_generator tickets assumed the enemy generation pipeline did not exist. In reality, asset_generation/python/ is a full pipeline with animated enemy classes, materials, and a CLI. Should the tickets be rewritten?
**Assumption made:** Yes. Deleted stale spec + test artifacts for blender_parts_library; marked it BLOCKED/superseded. Rewrote blender_python_generator to describe the actual remaining work: adding AnimatedAcidSpitter, AnimatedClawCrawler, AnimatedCarapaceHusk to the existing pipeline. Resumed autopilot on the revised blender_python_generator ticket.
**Confidence:** High

---

## Run: 2026-03-23 (Planner Agent — blender_python_generator animated enemy classes)

### [BPG] Planner — attack profile entries for 3 new enemies
**Would have asked:** The existing animated enemies (adhesion_bug, tar_slug, ember_imp) each have entries in `src/combat/enemy_attack_profiles.py`. Should the 3 new animated enemies (acid_spitter, claw_crawler, carapace_husk) also require new attack profile entries as part of this ticket?
**Assumption made:** No. Attack profiles are not part of the ticket's acceptance criteria. The ticket only requires: class definitions, builder registration, constants updates, material theme, GLB generation, and tests verifying those items. Adding attack profiles is a separate concern and would require modifying `enemy_attack_profiles.py` and its tests — outside the scope stated by the acceptance criteria. The existing `get_attack_profile()` function already returns `[]` for unknown types gracefully. Adding profiles is deferred to a follow-up ticket.
**Confidence:** High

### [BPG] Planner — body geometry for AnimatedAcidSpitter (BLOB type)
**Would have asked:** The ticket says AcidSpitter → BLOB body type. Should it reuse `create_blob_armature` (same as TarSlug) or differentiate itself with a custom body shape?
**Assumption made:** Reuse `create_blob_armature`. The BLOB body type is determined by `get_body_type()` returning `EnemyBodyTypes.BLOB`, which automatically drives the animation system. The body geometry is distinct (a pulsing sac shape using a sphere with different scale ratios than TarSlug), but the armature type is shared. This matches the `example_new_enemy.py` pattern where ExampleGhost reuses `create_blob_armature` with a different body shape.
**Confidence:** High

### [BPG] Planner — body geometry for AnimatedClawCrawler (QUADRUPED type)
**Would have asked:** ClawCrawler → QUADRUPED body type. Should it reuse the exact same 6-legged leg layout as AdhesionBug, or have a distinct body structure?
**Assumption made:** Distinct body structure — a low, flat body with prominent front claw appendages (2 thicker cylinder "claws" replacing front legs), plus 4 regular legs. It uses `create_quadruped_armature` (same armature type as AdhesionBug) but with visually different proportions. The claw cylinders are scaled wider and shorter than leg cylinders to visually differentiate the enemy.
**Confidence:** Medium

### [BPG] Planner — body geometry for AnimatedCarapaceHusk (HUMANOID type)
**Would have asked:** CarapaceHusk → HUMANOID body type. Should it be a direct copy of AnimatedEmberImp with different materials, or meaningfully different geometry?
**Assumption made:** Meaningfully different — a heavier, wider cylindrical body (larger body_width variance) with shorter legs and no hands (the arm "hands" become flat spike protrusions). It uses `create_humanoid_armature` (same as EmberImp). The body proportions emphasize bulk: body_height variance is smaller relative to body_width to convey a heavy, charge-type enemy per the ticket description.
**Confidence:** Medium

### [BPG] Planner — test runner for GLB generation tests
**Would have asked:** Verifying that `python main.py animated acid_spitter 3` produces 3 GLBs requires actually invoking Blender. The existing pytest tests in `asset_generation/python/tests/` are pure-Python (no Blender). Should GLB generation tests be integration tests (subprocess calls) or skipped in the test suite?
**Assumption made:** GLB generation tests are pure-Python only. The tests verify: class registration in `AnimatedEnemyBuilder.ENEMY_CLASSES`, `EnemyTypes.get_animated()` returns all 6 types, `MaterialThemes.has_theme()` returns True for all 3 new types, and `EnemyTypes.get_static()` no longer contains acid_spitter/claw_crawler. The actual `python main.py animated X 3` invocations are run as part of the acceptance check outside pytest (CI/human verification step). This matches the project's existing test tier separation: pure-Python pytest for logic, manual/CI run for Blender generation.
**Confidence:** High

---

## Run: 2026-03-23 (Spec Agent — BPG animated enemy classes specification)

### [BPG] Spec — carapace_husk material theme color ordering
**Would have asked:** The ticket suggests STONE_GRAY, BONE_WHITE, CHROME_SILVER for carapace_husk but does not specify which slot (body/head/limbs) each maps to. What is the correct assignment?
**Assumption made:** `[body=STONE_GRAY, head=BONE_WHITE, limbs=CHROME_SILVER]`. Rationale: (1) existing themes follow `[primary_body_color, secondary_head_color, limb_color]` order (confirmed from adhesion_bug, tar_slug, ember_imp entries); (2) STONE_GRAY reads as the carapace shell (large body area), BONE_WHITE as the pale dome head, CHROME_SILVER as the metallic arm/leg protrusions. This ordering is the most visually coherent for a heavy armoured enemy.
**Confidence:** High

### [BPG] Spec — CARAPACE_HUSK placement in get_static() vs get_animated()
**Would have asked:** CARAPACE_HUSK is a new constant. Should it be added only to get_animated() (since it has an animated class), or also to get_static() as a future-expansion placeholder?
**Assumption made:** Added ONLY to get_animated(). The ticket acceptance criteria explicitly state "EnemyTypes.get_animated() returns all 6 types" and there is no AC for get_static() including carapace_husk. Adding it to get_static() would also break BPG-CONST-10 (get_animated() and get_static() must be disjoint).
**Confidence:** High

### [BPG] Spec — AcidSpitter body proportions: distinguishable from TarSlug
**Would have asked:** Both AcidSpitter (BLOB) and TarSlug (BLOB) use create_blob_armature. How different should the body proportions be to ensure they are visually distinct?
**Assumption made:** AcidSpitter body is roughly spherical (X≈Y≈1.0, Z≈0.9) with near-equal XY dimensions. TarSlug is elongated (length≈2.0, width≈0.8, height≈0.6). The key differentiator is X:Y:Z ratio — AcidSpitter is compact and squat, TarSlug is elongated and flat. Additionally, AcidSpitter has two drip-tendrils hanging below (acid visual) vs TarSlug's eye-stalk appendages. These geometry differences are sufficient for visual distinctiveness.
**Confidence:** High

### [BPG] Spec — ClawCrawler leg count: 6 total (2 claws + 4 legs) matches quadruped armature
**Would have asked:** The quadruped armature (create_quadruped_armature) is designed for 6 legs. ClawCrawler has 2 front claws + 4 regular legs = 6 appendages total. Does this correctly bind to the armature's 6 bone slots?
**Assumption made:** Yes. The quadruped armature has 6 leg bones (leg_fl, leg_fr, leg_ml, leg_mr, leg_bl, leg_br) per BoneNames constants. ClawCrawler's 2 claws map to the front leg positions (fl/fr) and the 4 regular legs map to middle/back positions (ml/mr/bl/br). The bone binding is handled by bind_mesh_to_armature in blender_utils — it does not require exact geometry correspondence, only that the mesh is bound to the armature object. Geometry differentiation (wider claws) does not affect armature compatibility.
**Confidence:** High

### [BPG] Spec — CarapaceHusk arm rotation: Euler import required
**Would have asked:** CarapaceHusk's create_limbs method sets arm rotation via `arm.rotation_euler = Euler((0, 0, math.pi/2))`, matching EmberImp. `Euler` is imported from `mathutils` at the top of `animated_enemies.py` (line 6). Is this import safe for pure-Python tests?
**Assumption made:** The existing `from mathutils import Euler` at line 6 of animated_enemies.py is pre-existing and already handled by the test environment (tests currently pass per ticket). No new top-level Blender imports are added. BPG-NFR-1-AC1 applies only to NEW code added by this ticket.
**Confidence:** High

### [BPG] Spec — Test method for BPG-CLASS-*: inspect.getsource vs source_code attribute
**Would have asked:** Pure-Python tests cannot instantiate the new classes (create_body calls bpy functions). Should structural tests use inspect.getsource() (Python stdlib) or a source-code string read via open(__file__) on the source module?
**Assumption made:** Use `inspect.getsource(method)` for per-method source inspection. This is standard Python, works in pytest without Blender, and is used in the existing GDScript test suite (ADV-RSM-07 uses script.source_code for the same purpose). `inspect.getsource` works on any importable class method and does not require Blender.
**Confidence:** High

---

## Run: 2026-03-23 (Test Designer Agent — BPG animated enemy classes tests)

### [BPG] Test Design — bpy stub strategy for pure-Python test isolation
**Would have asked:** The spec requires tests to be importable without bpy, but `animated_enemies.py` imports `blender_utils` at module level, which does `import bpy` at its own module level. The existing spec checkpoint says "the test environment handles this" — but there is no conftest.py or bpy stub anywhere in the project. Should the Test Designer create a conftest.py bpy stub, or should the implementation agent be responsible for making animated_enemies.py importable without bpy?
**Assumption made:** Test Designer creates `tests/enemies/conftest.py` with a `sys.modules` stub for `bpy`, `bmesh`, and `mathutils` registered before collection. This is the canonical pytest pattern for Blender projects. It is scoped to `tests/enemies/` only so it does not affect any existing test suite. The stub installs `MagicMock` objects so that module-level attribute access on `bpy`, `mathutils.Euler`, etc. does not raise. This is a test-infrastructure concern, not a production code concern, so it falls within Test Designer's ownership.
**Confidence:** High

### [BPG] Test Design — Import path: from src.enemies.animated_enemies vs from src.enemies
**Would have asked:** The spec says classes are importable from `src.enemies.animated_enemies`. `src/enemies/__init__.py` re-exports from both `base_enemy` and `animated_enemies`. Should tests import directly from the submodule path or from the package root?
**Assumption made:** Import directly from `src.enemies.animated_enemies` and `src.enemies.base_enemy` (full submodule paths). This matches the spec's "importable from src.enemies.animated_enemies" wording and avoids triggering the `__init__.py` re-export chain which would also pull in bpy. After the conftest stub is installed, both paths work, but direct submodule imports are more precise.
**Confidence:** High

---

## Run: 2026-03-24 (Test Breaker Agent — BPG adversarial suite)

### [BPG] Test Breaker — Wrong-key absence checks in apply_materials
**Would have asked:** Should adversarial apply_materials tests assert absence of ALL five wrong keys (e.g. check for 'tar_slug', 'ember_imp', 'adhesion_bug', and the other two new keys) or only the most likely copy-paste sources?
**Assumption made:** Assert absence of all five wrong keys in every new class's apply_materials. This maximises mutation surface coverage at negligible cost — all five strings are literal and deterministic to check, and the test is clear about intent.
**Confidence:** High

### [BPG] Test Breaker — get_animated() return type: list vs Sequence
**Would have asked:** Should the return-type adversarial tests assert exactly `list`, or accept any `Sequence` (e.g. tuple)? The spec says "list" but existing code returns a list literal.
**Assumption made:** Assert exactly `list` via `assertIsInstance(result, list)`. The spec and existing implementation both use `list`. Accepting `tuple` or generator would widen the contract beyond what the spec defines, and the implementation agents should follow the spec strictly.
**Confidence:** High

### [BPG] Test Breaker — Abstract method check: __abstractmethods__ vs ABC registration
**Would have asked:** Is it safe to check `__abstractmethods__` to verify a class is concrete, given that BaseEnemy may not use `abc.ABC` formally?
**Assumption made:** Checking `getattr(cls, '__abstractmethods__', frozenset()) == frozenset()` is correct for both ABC and non-ABC classes. If BaseEnemy does not use ABC, `__abstractmethods__` will be absent, and the getattr default of `frozenset()` will correctly assert the class is concrete. The test is conservative and produces no false positives.
**Confidence:** High

---

## Run: 2026-03-24 (Engine Integration Agent — BPG animated enemy classes implementation)

### [BPG] Implementation — claw_crawler body_scale reference in create_armature
**Would have asked:** The spec does not specify whether to pass `self.body_width` or `self.body_height` to `create_quadruped_armature` for ClawCrawler.
**Assumption made:** Pass `self.body_width` as it is the dominant spatial dimension for a flat disc body, matching the pattern where AdhesionBug passes `self.body_scale` (its dominant dimension).
**Confidence:** High

### [BPG] Implementation — acid_spitter body Y scale inline vs stored
**Would have asked:** Should the Y scale of acid_spitter's sac body (computed as `body_scale * random_variance(...)`) be stored as a named attribute?
**Assumption made:** Y scale is not referenced by any other method. Only `self.body_scale` (X) and `self.height` (Z) are stored, as those are the only values that `create_armature` and `create_head` need.
**Confidence:** High

---

### [BPG] — OUTCOME: COMPLETE
Added AnimatedAcidSpitter, AnimatedClawCrawler, AnimatedCarapaceHusk to the existing pipeline. 91/91 new tests pass, 259/259 total. 9 GLBs generated in animated_exports/ with Blender 5.0.1. 9 critical geometry bugs caught and fixed by reviewer before final generation.

---

## Run: 2026-03-24 (Planner Agent — godot_scene_generator_validation planning)

### [GSV] Planner — _extract_family_name headless testability: EditorScript cannot be instantiated
**Would have asked:** `load_assets.gd` is `@tool extends EditorScript`. Calling `load("res://scripts/asset_generation/load_assets.gd").new()` headlessly will attempt to instantiate an EditorScript, which is only valid inside the editor and will crash or produce null in headless mode. How should `_extract_family_name` be tested headlessly?
**Assumption made:** The Spec Agent must specify that `_extract_family_name` logic is extracted into a new file `scripts/asset_generation/enemy_name_utils.gd` as a `static func extract_family_name(file_name: String) -> String`. `load_assets.gd` calls this util. The test loads `enemy_name_utils.gd` directly (it will be a plain `extends RefCounted` or `extends Object` with only static functions, which IS headlessly instantiable). This is the only architecture that allows headless unit testing of the family-name extraction logic without touching the EditorScript.
**Confidence:** High

### [GSV] Planner — GLB file availability: only 4 M5 families exist in animated_exports
**Would have asked:** The ticket lists 4 families with 3 variants each (12 files). The animated_exports directory contains those 12 files PLUS adhesion_bug_animated_00_integrated.glb, ember_imp_animated_00_integrated.glb, tar_slug_animated_00/01/02.glb, ember_imp_animated_00/01/02.glb, and several non-animated GLBs. Which files should be copied to assets/enemies/generated_glb/?
**Assumption made:** Copy ONLY the 12 canonical M5 family GLBs: adhesion_bug_animated_00/01/02.glb, acid_spitter_animated_00/01/02.glb, claw_crawler_animated_00/01/02.glb, carapace_husk_animated_00/01/02.glb. Do NOT copy _integrated variants, ember_imp, tar_slug, Small_Ice, Large_Fire, or Small_Toxic GLBs. The _integrated variants are Blender pipeline artifacts (not final exports). ember_imp and tar_slug are M5 families not listed in the 4 target families for this ticket. The non-animated GLBs (Small_Ice, etc.) are test assets unrelated to the enemy pipeline.
**Confidence:** High

### [GSV] Planner — Generated .tscn scene structure test: generator must run first
**Would have asked:** The ticket requires testing that generated .tscn files have required child nodes (Visual/Model, CollisionShape3D, Hurtbox, etc.). But the generator is an EditorScript that must be run in the Godot editor by a human. Can we test generated .tscn structure headlessly?
**Assumption made:** The .tscn structure test can only run if generated .tscn files exist on disk. Since the generator cannot be run headlessly, the spec must document this as a conditional test: if the generated .tscn files exist (i.e., the human has run the EditorScript in the editor), the test loads and inspects them; if the files do not exist, the test records a SKIP (not a FAIL). This is the conservative approach — the test validates structure when the artifact exists, but does not block the test suite when it does not. The Spec Agent must specify the SKIP behavior explicitly.
**Confidence:** High

### [GSV] Planner — Test file location: tests/asset_generation/ vs tests/scripts/asset_generation/
**Would have asked:** Should the new test file live in `tests/asset_generation/` (mirroring source path `scripts/asset_generation/`) or in `tests/scripts/asset_generation/` (strictly mirroring the scripts/ directory structure)?
**Assumption made:** `tests/asset_generation/` (new directory). The pattern in this project is: `tests/scripts/enemy/` mirrors `scripts/enemies/`, `tests/rooms/` mirrors `scenes/rooms/`. The test is for code in `scripts/asset_generation/`, so `tests/asset_generation/` is the parallel. The run_tests.gd runner discovers all test_*.gd files recursively from `tests/`, so no runner change is needed.
**Confidence:** High

## Resume: 2026-03-24T00:00:00Z
Ticket: project_board/5_milestone_5_procedural_enemy_generation/backlog/godot_scene_generator_validation.md
Resuming at Stage: SPECIFICATION
Next Agent: Spec Agent

### [GSV] ap-continue — ticket in backlog/ not in_progress/
**Would have asked:** The interrupted ticket is in backlog/ (was never moved to in_progress/ before rate limit hit). Scan found no in_progress/ tickets at agent-resumable stages. Should I still resume it?
**Assumption made:** Yes — this ticket was the active work item when the rate limit occurred. Resuming from backlog/ at Stage SPECIFICATION.
**Confidence:** High

---

## Run: 2026-03-24 (Spec Agent — godot_scene_generator_validation specification revision 5)

### [GSV] Spec Rev5 — preload vs global class_name for EnemyNameUtils in load_assets.gd
**Would have asked:** The prior spec revision (Revision 4) stated "No new imports or preload statements are required because class_name EnemyNameUtils is globally registered." The task prompt explicitly mandates `const EnemyNameUtils = preload("res://scripts/asset_generation/enemy_name_utils.gd")` at the top of load_assets.gd. Which approach governs?
**Assumption made:** The task prompt governs. The explicit preload approach is mandated. The preload is safer for a @tool EditorScript because class_name registration order is not guaranteed in the editor's class cache when the script first runs. An explicit preload makes the dependency deterministic. The spec is updated to require the preload declaration, and a new AC (GSV-LOADMOD-AC-5) and test (GSV-UTIL-18) are added to verify its presence.
**Confidence:** High

### [GSV] Spec Rev5 — ember_imp (no suffix) test case missing from prior spec
**Would have asked:** The task prompt specifies `"ember_imp"` (no numeric suffix, no infix) → `"ember_imp"` as a required test case, but the prior spec revision did not include it in the canonical table or in a dedicated test ID. Should it be added?
**Assumption made:** Yes. Added `"ember_imp"` → `"ember_imp"` to the canonical table, added GSV-UTIL-AC-9b, and added test GSV-UTIL-8b to the test ID table. This is a meaningful passthrough case because ember_imp has no animated variants in the M5 families (it is excluded from the 12 GLB copy manifest) and serves as a boundary condition for the algorithm.
**Confidence:** High

---

## Run: 2026-03-24 (Test Designer Agent — godot_scene_generator_validation test design)

### [GSV] Test Design — preload scope vs guard test behaviour
**Would have asked:** The spec says to use `const _EnemyNameUtils = preload(...)` at file scope, which means if `enemy_name_utils.gd` does not exist the test file itself fails to load. But GSV-UTIL-1 is described as a "guard test" that calls `load()` and bails early if null. If `preload` hard-fails, the guard pattern never runs. Should the file-scope const be a try-load or a hard preload?
**Assumption made:** Hard preload per spec R1: "If the file does not exist, the preload fails at load time and the test file itself fails to load — which is the correct failure mode." GSV-UTIL-1's guard (checking `load()` returns non-null) verifies the same file via `load()` call inside the test body, independent of the file-scope preload. The preload ensures the class is registered for static calls (GSV-UTIL-2 through GSV-UTIL-14). The guard test documents the requirement explicitly. Both can coexist.
**Confidence:** High

### [GSV] Test Design — GSV-UTIL-16/17/18 load_assets.gd not yet modified
**Would have asked:** GSV-UTIL-16, GSV-UTIL-17, and GSV-UTIL-18 inspect load_assets.gd source. That file has not yet been modified by the Implementation Agent. These tests will be RED (failing) because the old body exists and the delegation call does not. Is that the intended red-phase state?
**Assumption made:** Yes. The tests are RED before implementation, GREEN after. This is correct per the ticket's "Tests must be RED before enemy_name_utils.gd exists, GREEN after" instruction. The load_assets.gd modification tests are also part of the red phase for that implementation subtask.
**Confidence:** High

---

## Resume: 2026-03-24T00:01:00Z
Ticket: project_board/5_milestone_5_procedural_enemy_generation/backlog/godot_scene_generator_validation.md
Resuming at Stage: TEST_BREAK
Next Agent: Test Breaker Agent

---

## Run: 2026-03-24 (Test Breaker Agent — godot_scene_generator_validation adversarial tests)

### [GSV] Test Breaker — single-segment int expected output
**Would have asked:** Is `extract_family_name("00")` expected to return `"00"` (size guard preserves it) or `""` (stripped)? The spec algorithm says strip if `size >= 2 and last.is_valid_int()`. With a single segment "00", size == 1 so the guard blocks stripping.
**Assumption made:** Returns `"00"`. The size >= 2 guard is explicit in the original load_assets.gd implementation and in the spec algorithm step 2. Single-segment int is not stripped. This is the correct deterministic result per the spec.
**Confidence:** High

### [GSV] Test Breaker — negative int trailing segment behavior
**Would have asked:** The spec says is_valid_int() returns true for "-1". Is stripping a negative trailing integer intentional, or is it only for non-negative zero-padded variant indices?
**Assumption made:** Intentional per spec: "The algorithm does not special-case negative trailing segments; any valid int is stripped." GSV-ADV-12 tests this path. An implementation that checks `to_int() >= 0` instead of `is_valid_int()` is a mutation bug this test exposes.
**Confidence:** High

### [GSV] Test Breaker — "animated" in middle position (not prefix, not between int and family)
**Would have asked:** Is removing "animated" from middle position (e.g., "foo_animated_bar" → "foo_bar") an intended behavior, or is the spec only concerned with removal when "animated" appears as a penultimate segment before the trailing int?
**Assumption made:** Intended. The spec algorithm step 3 says "Scan the remaining segments; remove every segment that is exactly equal to 'animated'. All occurrences are removed." This is a general scan, not position-restricted. GSV-ADV-15 tests this. An implementation using a fixed-offset removal (only remove segments at index size-1) would fail.
**Confidence:** High

### [GSV] Test Breaker — underscore-only input ("_") expected output
**Would have asked:** "_" splits to ["", ""], neither segment is int or "animated", so re-joining gives "_". Is returning "_" for this pathological input acceptable, or should a normalization step reduce it?
**Assumption made:** Returns "_". The algorithm specifies no normalization step. No known filename uses "_" alone. The test verifies no crash and the algorithmically consistent result. The Implementation Agent is free to add normalization later; this test documents the current contract.
**Confidence:** Medium

---

## Run: 2026-03-25 (Engine Integration Agent — GSV implementation)

### [GSV] Implementation — pre-existing load_assets.gd parse errors
**Would have asked:** load_assets.gd has pre-existing Godot parse warnings (type inference on `local_aabb`, `xform`, `world_point` treated as errors in headless mode). These were present before my changes. The tests for GSV-UTIL-16/17/18 still read `.source_code` successfully and pass. Should I fix those pre-existing errors?
**Assumption made:** Out of scope. Those lines (292-297) are unchanged by this ticket and were failing before. The task spec explicitly says to only make two changes to `load_assets.gd`. The GSV test assertions all pass. Leaving pre-existing errors untouched.
**Confidence:** High

### [GSV] Implementation — exit code 1 from run_tests.sh
**Would have asked:** The test suite returns exit code 1 due to RSM-SIGNAL and ADV-RSM failures. These were failing before this ticket's changes. Should this block handoff?
**Assumption made:** Not a blocker. Confirmed by stash/restore comparison: RSM-SIGNAL and ADV-RSM failures existed in the baseline before any GSV changes. No regressions introduced. All 37 GSV tests (20 primary + 17 adversarial) pass 0 failures.
**Confidence:** High

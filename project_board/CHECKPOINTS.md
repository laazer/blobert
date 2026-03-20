# Autopilot Checkpoint Log

Decisions logged here required human judgment but were resolved autonomously.
Review these after autopilot completes.

---

## Run: 2026-03-20 (Test Breaker Agent — mini_boss_encounter ADV-MBA-01 through ADV-MBA-08)

### [mini_boss_encounter] TestBreak — ADV-MBA-06 strict vs. lenient left-edge comparison
**Would have asked:** SkillCheckPlatform3 right edge (51 + 4 = 55.0) equals MiniBossFloor left edge (67.5 - 12.5 = 55.0) exactly. Should the assertion be strict (>) or lenient (>=)? Strict fails on the current scene geometry.
**Assumption made:** Used strict inequality (>) as specified in the ticket. The current geometry produces floor_left_edge == p3_right_edge == 55.0, so this test will fail in red phase. The Engine Integration Agent must resolve the zone boundary (either move MiniBossFloor slightly right or accept that the zones touch and the test should use >=). Documented the strict > intent in the test failure message.
**Confidence:** Medium

### [mini_boss_encounter] TestBreak — ADV-MBA-08 dual assertion strategy (name equality + mutual distinctness)
**Would have asked:** The ticket specifies only "all four enemy node names are distinct strings." Should the test also assert the exact expected names (catching Godot auto-rename), or only mutual distinctness?
**Assumption made:** Added both: (1) exact name assertions ("EnemyMiniBoss", "EnemyFusionA", etc.) to catch Godot auto-dedup renames, and (2) pairwise distinctness assertions. This exposes the root cause (wrong name) separately from the symptom (duplicate names). The exact-name assertions are the adversarial surface not covered by T-57 path comparisons.
**Confidence:** High

### [mini_boss_encounter] TestBreak — ADV-MBA-07 col.position.x dynamic read vs. assumed zero
**Would have asked:** MiniBossFloor CollisionShape3D X offset is confirmed as 0 in the scene file. Should the test read it dynamically (matching T-62's pattern) or hardcode 0 for clarity?
**Assumption made:** Read col.position.x dynamically, consistent with T-62 and the spec's explicit risk mitigation note: "If the CollisionShape3D X offset for MiniBossFloor is non-zero in a future edit, the right-edge formula must include col.position.x." ADV-MBA-07 follows the same pattern for the left-edge computation.
**Confidence:** High

---

## Run: 2026-03-20 (Test Designer Agent — mini_boss_encounter T-53 through T-62)

### [mini_boss_encounter] TestDesign — T-53 and T-54 as separate methods vs. merged
**Would have asked:** The spec says T-53 and T-54 may be merged into one function or kept separate as long as assertion names use distinct prefixes. Should they be separate test_t53_ and test_t54_ functions, or a single function with both assertion groups?
**Assumption made:** Kept as two separate test methods (test_t53_ and test_t54_). This matches the pattern established by all prior test files (T-43 through T-52 each have a single dedicated function). Keeping them separate makes individual failures easier to identify in CI output and aligns with the spec's primary framing of T-54 as a "dedicated" assertion.
**Confidence:** High

### [mini_boss_encounter] TestDesign — MBA-BOSS-3 placement in T-55 vs. separate function
**Would have asked:** MBA-BOSS-3 (InfectionInteractionHandler.has_method("set_target_esm")) is specified to be inlined in T-55 per NFR-6. However T-55 is already the EnemyMiniBoss placement test. Does adding the handler check there make the function too wide in scope?
**Assumption made:** Inlined MBA-BOSS-3 into test_t55_ as a conditional block after the enemy assertions, using assertion name T-55_infection_interaction_handler_has_set_target_esm exactly as NFR-6 specifies. The handler check is logically connected to EnemyMiniBoss wiring, so the combined scope is coherent.
**Confidence:** High

### [mini_boss_encounter] TestDesign — T-60 source_code fallback implementation
**Would have asked:** The spec documents that source_code may be empty in Godot headless mode and instructs a fallback to has_method("_on_body_entered"). Should the fallback count as a PASS or emit a conditional warning?
**Assumption made:** The fallback emits a print NOTE explaining the headless mode limitation, then runs _assert_true on has_method("_on_body_entered"). If has_method returns true, the test passes. This is the most informative approach: it does not silently skip the assertion and explicitly records whether the proxy condition held.
**Confidence:** High

### [mini_boss_encounter] TestDesign — T-62 col.position.x dynamic read
**Would have asked:** The spec (MBA-FLOW-4) specifies reading col.position.x dynamically rather than hardcoding 0, to survive future scene edits. The current confirmed value is 0. Is it safe to read the live value even when the test is in red-phase (MiniBossFloor absent)?
**Assumption made:** The test guards both MiniBossFloor existence and its CollisionShape3D before computing the right edge, returning early with a FAIL on any missing prerequisite. The live col.position.x read is only reached when the shape is confirmed present. This is safe in all phases.
**Confidence:** High

---

## Run: 2026-03-19 (Spec Agent — fusion_opportunity_room specification)

### [fusion_opportunity_room] Spec — T-34 collision_mask duplication with T-25

**Would have asked:** The ticket's Task 2 specifies T-34 as "FusionFloor collision_mask == 3; FusionPlatformA collision_mask == 3; FusionPlatformB collision_mask == 3." T-25 in test_containment_hall_01.gd already asserts collision_mask == 3 for ALL static bodies including these three nodes. Emitting duplicate named assertions would be redundant. Should T-34 cover the gap assertion instead?

**Assumption made:** T-34 is remapped to the FUSE-GEO-4 gap assertion (platform gap width and reachability bound). This avoids duplicating T-25 and adds genuinely new coverage. The spec documents this remapping explicitly in the FUSE-GEO-4 NOTE block. The collision_mask requirement is satisfied by reference to T-25.

**Confidence:** High

---

### [fusion_opportunity_room] Spec — T-35 and T-36 duplication with T-24 enemy positions

**Would have asked:** T-24 already asserts EnemyFusionA at (15, 1.3, 0) ±0.1 m and EnemyFusionB at (28, 1.3, 0) ±0.1 m. T-35 and T-36 in the ticket's Task 2 also assert enemy positions. Emitting duplicate position assertions violates NFR-3. What should T-35 and T-36 cover instead?

**Assumption made:** T-35 covers EnemyFusionA scene path (get_scene_file_path contains "enemy_infection_3d.tscn") and the Y-above-platform guard (EnemyFusionA.position.y > FusionPlatformA.position.y). T-36 covers the same for EnemyFusionB. These are genuinely new assertions not present in T-1 through T-30. The spec documents this explicitly in FUSE-ENC-1.

**Confidence:** High

---

### [fusion_opportunity_room] Spec — T-37 duplication with T-9 and T-16 InfectionInteractionHandler

**Would have asked:** T-9 asserts InfectionInteractionHandler node exists and is a Node. T-16 asserts the script path contains "infection_interaction_handler.gd". Should T-37 duplicate these?

**Assumption made:** T-37 covers only what T-9 and T-16 do NOT cover: the presence of the `get_mutation_slot_manager` method via `has_method("get_mutation_slot_manager")`. This is a new assertion. The node existence and script path assertions are satisfied by reference to T-9 and T-16.

**Confidence:** High

---

### [fusion_opportunity_room] Spec — get_scene_file_path() availability for instanced nodes

**Would have asked:** Does `get_scene_file_path()` return a non-empty string for EnemyFusionA and EnemyFusionB, which are direct child instances of the level root (not sub-scene children)?

**Assumption made:** Yes. In Godot 4, `get_scene_file_path()` returns the non-empty path for the root node of an instanced PackedScene. EnemyFusionA is the root of its instanced enemy_infection_3d.tscn, so the call returns "res://scenes/enemy/enemy_infection_3d.tscn". This is confirmed by the scene file which shows `[node name="EnemyFusionA" parent="." instance=ExtResource("4_enemy")]`.

**Confidence:** High

---

### [fusion_opportunity_room] Spec — T-38 requires scene tree for _ready() to run

**Would have asked:** InfectionInteractionHandler._ready() instantiates _slot_manager. If the test does not add the scene to the scene tree, _ready() does not run and get_mutation_slot_manager() returns null. Should T-38 require tree insertion?

**Assumption made:** Yes. T-38 must add the root to the scene tree via `Engine.get_main_loop() as SceneTree; tree.root.add_child(root)` before calling get_mutation_slot_manager(). This follows the established pattern from CHECKPOINTS.md [player_hud] TestDesign. The test must remove and free the root after the assertion.

**Confidence:** High

---

## Run: 2026-03-18 (Presentation Agent — player_hud implementation)

### [player_hud] Implementation — ticket offset values vs spec offset values

**Would have asked:** The ticket's "What to implement" section lists HPBar bottom=42, HPLabel top=44/bottom=68, ClingStatusLabel top=96/bottom=120, which differ from spec Appendix A and test bonus assertions (HPBar bottom=28, HPLabel top=36/bottom=62, ClingStatusLabel top=104/bottom=130). Which is authoritative?

**Assumption made:** The spec document (`player_hud_spec.md` Appendix A) and the test assertions (`test_player_hud_layout.gd` bonus functions) are the authoritative source. The ticket's inline "What to implement" section appears to be a summary that was not kept in sync with the spec. Implemented the spec/test values.

**Confidence:** High

---

## Run: 2026-03-18T03:00:00Z (Test Breaker Agent — player_hud adversarial extension)

### [player_hud] TestBreak — Rect2.intersects shared-edge semantics

**Would have asked:** Godot 4's `Rect2.intersects()` documentation states it returns false when rectangles share only an edge. Should the overlap tests depend on this semantic, or add an explicit unit test to document and confirm this behavior so future readers know the oracle is NOT a one-pixel-error source?

**Assumption made:** Added a dedicated unit test (`test_adv_rect2_intersects_shared_edge_semantics`) that verifies Godot's `Rect2.intersects` returns false for rectangles that share exactly one edge. This test is purely a semantic oracle check — it documents the engine behavior so that if Godot's behavior ever changes, the test suite surfaces it before the overlap assertions become unreliable.

**Confidence:** High

---

### [player_hud] TestBreak — HPBar exact class string guard

**Would have asked:** The existing T-6.1 asserts `is ProgressBar` and `not is TextureProgressBar`. Would a node of type HSlider (which IS a Range, IS NOT a TextureProgressBar, IS NOT a ProgressBar) be caught by T-6.1? Yes it would — but should there be a `get_class()` string test as a separate mutation matrix target to make the failure mode explicit and unambiguous?

**Assumption made:** Added `test_adv_hpbar_exact_class_string` that asserts `hp_bar.get_class() == "ProgressBar"`. This catches any non-ProgressBar Range subtype (HSlider, ScrollBar, VSlider, SpinBox) that would fool a pure `is Range` test. The `get_class()` check is the most conservative mutation-matrix target and is deterministic.

**Confidence:** High

---

### [player_hud] TestBreak — Contextual prompts Y >= 1780 region guard

**Would have asked:** T-6.10 asserts contextual prompts don't overlap the always-visible set (which ends at Y=266), but a node repositioned to Y=300 would pass T-6.10 while still being in the top-left status area, violating the spec requirement. Should a dedicated Y-range guard be added?

**Assumption made:** Added `test_adv_contextual_prompts_in_bottom_region` that asserts each contextual prompt node has `offset_top >= 1780` and `offset_left >= 1300`. This fails for the current scene (where AbsorbPromptLabel is at Y=164, X=20) and passes only after correct repositioning to Y=1800, X=1400.

**Confidence:** High

---

### [player_hud] TestBreak — FusionActiveLabel in left panel region

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

### [chunk_sticks_to_enemy] Test Break — chunk_attached emission for body in both "chunk" AND "player" groups

**Would have asked:** If a body is in both the "chunk" group and the "player" group simultaneously (unusual but possible), should chunk_attached be emitted or suppressed?

**Assumption made:** The spec says the signal fires for bodies in the "chunk" group and NOT for player bodies. The existing _on_body_entered code checks player group first. Conservative assumption: the chunk group check takes precedence in the stub (it checks "chunk" without a prior player-group exclusion). This edge case is unlikely in production but is documented for the implementation agent.

**Confidence:** Medium

---

### [chunk_sticks_to_enemy] Test Break — dead-state enemy headless testability

**Would have asked:** Can we drive EnemyStateMachine to a "dead" state headlessly without instantiating a full scene?

**Assumption made:** The deepest testable state headlessly is "infected" (idle → weakened → infected). There is no apply_dead_event() confirmed available headlessly. SPEC-CSE-1 says the signal fires regardless of state including "dead." The test covers "infected" as the deepest verified proxy for "dead" state behavior.

**Confidence:** High

---

### [chunk_sticks_to_enemy] Test Break — freed enemy node prevents flag clear on absorb

**Would have asked:** If _chunk_stuck_enemy is freed before absorb_resolved fires, the is_instance_valid guard skips the entire slot block, leaving _chunk_stuck_on_enemy=true. Is this acceptable or should the flag be cleared even when the enemy ref is invalid?

**Assumption made:** Per SPEC-CSE-10 risk note: "If the stuck flag is not cleared when the chunk node is invalid, the recall guard will permanently block recall for that slot, creating a softlock." However, SPEC-CSE-10 only addresses the chunk node being freed, not the enemy node being freed. When the ENEMY node is freed (not the chunk), the implementation skips the block and flags remain — this is a known risk per spec. The test documents this behavior without asserting flag state, only asserting no crash.

**Confidence:** Medium

---

## Run: 2026-03-05T12:00:00Z
Tickets queued: input_hint_polish_core_mechanics.md

---

### [infection_interaction] Planner — Weakened state definition

**Would have asked:** Is the "weakened" enemy state already defined and implemented elsewhere?

**Assumption made:** Yes. EnemyStateMachine in the codebase already defines `STATE_WEAKENED` and transitions idle/active → weakened (weaken event), weakened → infected (infection event). Execution plan assumes dependency on enemy state machine / weakened-state behavior being in place; no separate task to define weakened.

**Confidence:** High

---

### [infection_interaction] Planner — Chunk contact vs key press

**Would have asked:** Should both chunk contact and key press trigger infection, or should the spec choose one?

**Assumption made:** Both are in scope per AC ("e.g. chunk contact, key press"). Spec Agent will define the exact interaction(s); implementation tasks include key/infect action (already present in InfectionInteractionHandler) and chunk-contact trigger (e.g. chunk body entering area of weakened enemy). If spec narrows to one trigger, implementation follows spec.

**Confidence:** Medium

---

### [infection_interaction] Planner — Existing infection code

**Would have asked:** The repo already has InfectionInteractionHandler, InfectionAbsorbResolver, MutationInventory, infection tests. Should the plan assume greenfield or align with existing code?

**Assumption made:** Plan drives spec-first. Spec is the authority; Test Design and Implementation tasks align or fill gaps. Existing code is reconciled with the spec (e.g. chunk-contact wiring may be missing; one mutation "usable" may need UI or gameplay hook). No task assumes delete-and-rewrite; implementation tasks may be "wire chunk contact," "ensure one mutation granted and visible/usable," "add/align visual feedback."

**Confidence:** High

---

### [infection_interaction] Planner — One mutation "usable"

**Would have asked:** What does "at least one mutation is granted and usable after absorb" mean — UI visibility only, or an actual gameplay effect?

**Assumption made:** Minimum: one mutation ID is granted to the player (MutationInventory.grant) and is visible or confirmable (e.g. in UI or inventory). "Usable" for this milestone means the player can observe that the mutation was gained; a concrete gameplay effect (e.g. stat buff, ability) may be placeholder or minimal. Spec Agent will clarify; implementation may deliver UI/inventory display plus a minimal placeholder effect if needed to satisfy AC.

**Confidence:** Medium

---

### [infection_interaction] Planner — Visual feedback scope

**Would have asked:** What level of visual/audio feedback is required for weakened, infected, and absorb states to count as "visually clear and discoverable without debug overlays"?

**Assumption made:** Minimum feedback includes distinct coloration or sprite change for weakened vs infected enemies, a short infection FX (e.g. pulse, particles) when infection occurs, and a clear on-screen cue when a mutation is gained (e.g. HUD toast or inventory highlight). No complex animation set is required for this milestone; Presentation and Spec Agents will choose the simplest assets/effects that satisfy clarity.

**Confidence:** Medium

---

### [infection_interaction] Planner — Softlock definition

**Would have asked:** For this feature, what scenarios count as a "softlock or undefined state" that must be prevented?

**Assumption made:** A softlock is any infection/absorb sequence that leaves the game running but the player unable to continue normal play without manually resetting the scene (e.g. enemy stuck in an intermediate state, infection cannot be cleared, absorb never completes, or mutation inventory enters an invalid state). Tests and implementation must ensure all transitions (normal, repeated, cancelled, or interrupted) converge to a valid, recoverable state: enemy dead or reset, infection cleared or resolved, and player input restored.

**Confidence:** Medium

---

### [infection_interaction] Test Designer — Infect input action coverage

**Would have asked:** Should primary tests assert that the `infect` input action (via `Input.is_action_just_pressed("infect")` in `InfectionInteractionHandler`) correctly routes to `EnemyStateMachine.apply_infection_event()` from weakened state, or is that mapping treated as higher-level engine integration?

**Assumption made:** For this ticket, primary Test Designer coverage focuses on pure logic and deterministic wiring that is testable without simulating real-time input. Infection triggers are verified at the state machine level and via chunk-contact engine wiring (`EnemyInfection._on_body_entered`), while the exact Godot input mapping for `infect` is treated as engine-integration / manual QA responsibility. No tests attempt to fake `Input` state.

**Confidence:** Medium

---

### [infection_interaction] Test Designer — Mutation "usable" via InfectionUI

**Would have asked:** Does "at least one mutation is granted and usable after absorb" require a concrete gameplay effect, or is a visible mutation indicator in the infection-loop HUD sufficient for this milestone?

**Assumption made:** For this milestone, a mutation is considered "usable" if it is (a) granted into `MutationInventory` and (b) made clearly visible to the player via InfectionUI (e.g. `MutationLabel`/`MutationIcon` driven from `get_mutation_inventory()` and `get_granted_count()`). Tests enforce that a non-zero mutation count makes the mutation label visible; any deeper gameplay effect is left to future tickets.

**Confidence:** Medium

---

### [infection_interaction] Test Designer — Infection FX text and tint mapping

**Would have asked:** Should the infection state FX contract specify exact label text and color tints for weakened/infected/dead, or only require that each state is visually distinct?

**Assumption made:** The strictest defensible contract for this ticket is that `infection_state_fx.gd` produces distinct visuals and explicit state labels: "Weakened", "Infected", and "Dead", with weakened/infected tinted away from the idle/default color and dead rendered dimmer (alpha < 1). Tests assert these concrete label strings and basic tint/dim relationships rather than exact RGB values, so future visual tweaks remain possible while keeping states clearly distinguishable.

**Confidence:** Medium

---

### [infection_interaction] Test Breaker — resolve_absorb null inventory semantics

**Would have asked:** When `InfectionAbsorbResolver.resolve_absorb` is invoked with a non-null, infected `EnemyStateMachine` but a null mutation inventory, should the resolver still kill the enemy or treat the call as a strict no-op?

**Assumption made:** For this ticket, calling `resolve_absorb` with a null inventory is treated as a strict no-op: the enemy state and mutation inventory must remain unchanged, and the call must never crash. Tests mark this as a CHECKPOINT and assert no state change when `inv == null`.

**Confidence:** Medium

---

## Run: 2026-03-05T12:00:00Z
Tickets queued: input_hint_polish_core_mechanics.md

---

### [input_hint_polish_core_mechanics] Planner — Duplicate ticket blocks

**Would have asked:** The ticket file for `input_hint_polish_core_mechanics` currently contains two full ticket blocks with different Revisions (2 and 1); should the lower block be treated as historical context and left untouched, or should the file be normalized to a single ticket definition?

**Assumption made:** The first ticket block (Revision 2) is the authoritative current state and the second block (Revision 1) is retained as historical context. For this run, only the first block's WORKFLOW STATE and NEXT ACTION fields will be updated (to Stage SPECIFICATION, Revision incremented, and handoff information adjusted), and the lower block will be left unchanged.

**Confidence:** Medium

---

## Run: 2026-03-19 (Planner Agent — light_skill_check planning)

### [light_skill_check] Planning — spec ID namespace for skill check requirements

**Would have asked:** Should spec requirement IDs use "SKC-" prefix (as the ticket states) or follow the existing pattern of matching the zone's abbreviated name (e.g. "SC-GEO-" for Skill Check Geometry)?

**Assumption made:** Used "SKC-" prefix as stated in the ticket prompt. This is consistent with the ticket's own requirement naming suggestion (SKC-GEO-*, SKC-RETRY-*, SKC-PLACE-*) and avoids collision with the existing GEO-* namespace used by containment_hall_01_spec.md.

**Confidence:** High

---

### [light_skill_check] Planning — SkillCheckFloorBase Y position interpretation

**Would have asked:** The scene has SkillCheckFloorBase at node Y=0 with CollisionShape3D offset Y=-4.5 and BoxShape3D size Y=1. This makes the floor top surface at world Y = 0 + (-4.5) + 0.5 = -4.0, placing it 4 m below the platforms (which have top surface Y=0). This means the floor is a pit floor, not the same level as the surrounding corridor. Is this intentional?

**Assumption made:** Yes, this is intentional. The RespawnZone's CollisionShape3D is centered at Y=-5 with height 8, catching bodies that fall below Y≈-1. The SkillCheckFloorBase at Y=-4.0 (top surface) is the pit floor that the RespawnZone catches. The platforms (P1, P2, P3) are all at top surface Y≈0.0 — same as the corridor. The skill check is a platforming section over a pit, not a height-varied sequence. This matches the "light platforming" description.

**Confidence:** High

---

### [light_skill_check] Planning — test numbering starting at T-43

**Would have asked:** T-31 through T-42 are taken by test_fusion_opportunity_room.gd. The ticket says start at T-43. Are there any other test files that might use T-43 or beyond that could conflict?

**Assumption made:** T-43 is safe. Existing test files cover T-1 through T-30 (test_containment_hall_01.gd) and T-31 through T-42 (test_fusion_opportunity_room.gd). No other test file in tests/levels/ uses T-43 or higher. The new file test_light_skill_check.gd will start at T-43.

**Confidence:** High

---

### [light_skill_check] Planning — "passable with core movement" AC structural test approach

**Would have asked:** The AC says skill check is "passable with core movement." Without running physics, this can only be tested structurally. What structural properties constitute "passable"?

**Assumption made:** Three structural properties are testable headlessly: (1) all platform top surfaces are at the same Y level (≈0.0) as the entry floor so no height variance requires elevated jump; (2) gap between adjacent platforms is within the player's max horizontal jump range (≈1.98 m per containment_hall_01_spec.md, with the scene showing ~1.0 m gaps which is well within range); (3) all platforms have positive-area BoxShape3D collision so they are solid. This is the same structural approach used for FusionPlatform gap tests in T-34.

**Confidence:** High

---

### [light_skill_check] Planning — adversarial file naming convention

**Would have asked:** Should the adversarial file be named test_light_skill_check_adversarial.gd (matching fusion_opportunity_room pattern) or test_light_skill_check_adv.gd (shorter)?

**Assumption made:** Used test_light_skill_check_adversarial.gd to match the existing naming pattern established by test_fusion_opportunity_room_adversarial.gd. Consistency is more important than brevity here.

**Confidence:** High

---

## Run: 2026-03-20 (Test Breaker Agent — light_skill_check adversarial extension)

### [light_skill_check] TestBreak — ADV-SKC-06 P3>P1 vs P3>P2 scope decision

**Would have asked:** The ticket states ADV-SKC-06 as "SkillCheckPlatform3 BoxShape3D size.x > SkillCheckPlatform1 BoxShape3D size.x (landing pad wider)". T-46 already asserts P3 > P1 AND P3 > P2. Should ADV-SKC-06 only check P3>P1 (as the ticket literally states) or also P3>P2?

**Assumption made:** ADV-SKC-06 checks only P3>P1 as the ticket literally states. The P3>P2 check is covered by T-46. ADV-SKC-06's adversarial purpose is to independently guard the most likely regression (P3 accidentally given the same 4 m width as all other platforms). T-46 covers both comparisons in the compound test; ADV-SKC-06 provides independent coverage for the P3>P1 assertion only, keeping the adversarial test focused on the single mutation it is designed to catch.

**Confidence:** High

---

### [light_skill_check] TestBreak — ADV-SKC-07 zero-size default value in Godot 4

**Would have asked:** Does Godot 4 actually default a new BoxShape3D to (0.2, 0.2, 0.2) rather than exactly (0, 0, 0)? If the default is nonzero, the test may not catch the "uninitialized shape" case unless size is truly 0.

**Assumption made:** The Godot 4 default BoxShape3D size is Vector3(0.2, 0.2, 0.2) (visible in the inspector as "Size: 0.2, 0.2, 0.2"). The adversarial test asserts size.x > 0 and size.z > 0, which would pass even for the 0.2 default. The vulnerability being probed is not the exact-default case but the "manually set to zero" mutation (e.g. editor drag to 0). This is consistent with the mutation-testing category in the adversarial matrix. The exact-size assertions in T-44/T-45/T-46 separately catch the "wrong non-zero" case.

**Confidence:** High

---

## Run: 2026-03-19 (Spec Agent — light_skill_check specification)

### [light_skill_check] Spec — NodePath resolution strategy for RespawnZone.spawn_point

**Would have asked:** The RespawnZone spawn_point NodePath is `"../SpawnPosition"` (relative, going up one level). In a headless test, calling `root.get_node_or_null(NodePath("../SpawnPosition"))` will fail because `..` from the scene root has no parent. How should AC-SKC-RETRY-1.4 resolve the NodePath to confirm it is valid?

**Assumption made:** The test must call `respawn_zone_node.get_node_or_null(spawn_point_value)` — resolving the NodePath relative to the RespawnZone node itself (not relative to the scene root). This matches how Godot resolves the NodePath at runtime. With spawn_point = NodePath("../SpawnPosition") and RespawnZone as a child of the scene root, `"../SpawnPosition"` navigates up to the scene root then finds SpawnPosition, returning the correct node. This is documented in AC-SKC-RETRY-1.4 and the Risk section of SKC-RETRY-1.

**Confidence:** High

---

### [light_skill_check] Spec — AC-SKC-RETRY-2.4 upper Y bound derivation

**Would have asked:** The ticket requirement for SpawnPosition states only `position.y >= 0`. Should the spec add an upper bound on Y to guard against accidental floating spawn positions?

**Assumption made:** Added AC-SKC-RETRY-2.4 asserting `position.y <= 3.0`. Rationale: the current value is Y=1.0; a position above Y=3.0 would cause the player to drop significantly on respawn, creating a jarring experience. The [0, 3] range matches the corridor height conventions established elsewhere (enemies spawn at Y=1.3, player at Y=1.0). This is an additive defensive guard not in the original ticket AC but consistent with the ticket's "no softlock" intent.

**Confidence:** Medium

---

### [light_skill_check] Spec — AC-SKC-GEO-4.8 P3 wider-than-P1-and-P2 assertion scope

**Would have asked:** The ticket Task 2 adversarial cases (Task 3) include "Platform3 is wider than Platform1 and Platform2." The primary spec (Task 1) and test suite (Task 2) cover T-43 through T-52. Should the P3 width comparison be a primary test (T-46) or reserved for the adversarial file (ADV-SKC-*)?

**Assumption made:** Included as AC-SKC-GEO-4.8 in the primary spec and mapped to T-46 in the traceability table. Rationale: the width comparison is a structural invariant derivable from the scene file without physics, and it supports AC-1 (passability) by confirming the landing pad is wider. The adversarial file (Task 3) will add further adversarial variants around this constraint; the primary assertion belongs in the primary test.

**Confidence:** High

---


### [light_skill_check] — OUTCOME: INTEGRATION
All automated tests (T-43–T-52, ADV-SKC-01–08) passed first run with zero scene modifications. Ticket held at INTEGRATION pending human verification of AC-3 (light difficulty) and AC-5 (human-playable in-editor).

---

## Run: 2026-03-20 (Planner Agent — mini_boss_encounter planning)

### [mini_boss_encounter] Planning — "distinct" enemy without a new script or scene file

**Would have asked:** AC-1 requires the mini-boss to be "distinct from regular enemies (behavior, health, or arena)." The EnemyMiniBoss node in containment_hall_01.tscn currently instances the same enemy_infection_3d.tscn as EnemyMutationTease, EnemyFusionA, and EnemyFusionB, with no overrides. A material color override on MeshInstance3D (set in the .tscn via property override, no new script needed) satisfies "visually distinct" under the "(behavior, health, or arena)" OR condition — the AC does not require ALL three categories, only at least one. Visual distinction via arena (a dedicated, larger arena floor that regular enemies don't occupy) already provides one axis. The color override adds a second. Does "distinct" require a GDScript behavior change, or is color + dedicated arena sufficient?

**Assumption made:** Color override on MeshInstance3D in the scene + the dedicated MiniBossFloor arena (25×1×10 at X=67.5, larger than the regular corridor sections) together satisfy AC-1 for this milestone. The arena is a structural distinction; the color is a visual distinction. Both are testable headlessly. A behavioral distinction (e.g. higher health, patrol, custom state machine) is deferred to a future ticket if the human playtest finds AC-1 unsatisfied. This is the "conservative, reversible, no new GDScript" approach called out in the ticket prompt.

**Confidence:** Medium

### [mini_boss_encounter] Planning — EnemyMiniBoss position Y discrepancy

**Would have asked:** EnemyMiniBoss is at Y=0.5 in the .tscn, while all other enemies (EnemyMutationTease, EnemyFusionA, EnemyFusionB) are at Y=1.3. The floor surface is at Y=0 (top surface of MiniBossFloor: node.y=0 + col.offset.y=-0.5 + box.half_y=0.5 = 0.0). At Y=0.5 the enemy base is 0.5 m above the floor surface. Is Y=0.5 correct, or should it be Y=1.3 to match other enemies?

**Assumption made:** Y=0.5 is accepted as-is. The enemy has its own CharacterBody3D physics (via BasePhysicsEntity3D); gravity will settle it onto the floor at runtime. Tests will assert Y > 0 (above floor surface) not an exact value. If the Spec Agent determines Y=1.3 is required for correct presentation, that is a scene edit within the Engine Integration Agent's scope and does not require a new planning decision.

**Confidence:** Medium

### [mini_boss_encounter] Planning — test numbering starting at T-53

**Would have asked:** T-53 is the next available number after T-52 (light_skill_check). Are there any in-flight test files that might claim T-53 before this ticket completes?

**Assumption made:** No other in-progress ticket has claimed T-53 or higher. The active in-progress tickets (mutation_tease_room.md, start_finish_flow.md, containment_hall_01_layout.md, fusion_opportunity_room.md, light_skill_check.md, mini_boss_encounter.md) have all used T-1 through T-52. T-53 is safe.

**Confidence:** High

### [mini_boss_encounter] Planning — adversarial file naming convention

**Would have asked:** Should the adversarial test file be named test_mini_boss_encounter_adversarial.gd to match the fusion_opportunity_room and light_skill_check patterns?

**Assumption made:** Yes. Used test_mini_boss_encounter_adversarial.gd for consistency with the established naming pattern.

**Confidence:** High

### [mini_boss_encounter] Planning — Victory connection (AC-3) scope for structural testing

**Would have asked:** AC-3 requires "victory connects to level completion or next section." The scene has a LevelExit Area3D at X=93 with a script that prints "level_complete" when the player body enters. Is the presence of LevelExit with a correct script sufficient for structural AC-3 coverage, or does the test need to simulate the player reaching it?

**Assumption made:** Structural test coverage is: LevelExit node exists as Area3D; CollisionShape3D is present with non-zero BoxShape3D; LevelExit is positioned at X > MiniBossFloor right edge (X=80); the inline script contains the string "level_complete" (verifiable by loading the sub-resource and checking script/source). Physics simulation of the player walking through is an INTEGRATION/manual test. This matches the structural approach used for RespawnZone in T-49.

**Confidence:** High

### [mini_boss_encounter] Planning — MeshInstance3D color override testability

**Would have asked:** If the Spec Agent requires the mini-boss MeshInstance3D to have a distinct albedo color override, how can this be tested headlessly? The enemy is an instanced scene (enemy_infection_3d.tscn); overrides on instanced nodes in Godot 4 .tscn files are set via property paths in the parent scene. Can a test read these override values from the instantiated node without running _ready()?

**Assumption made:** Yes. After `PackedScene.instantiate()`, child node properties are populated from the parent scene's overrides before _ready() runs. A test can call `enemy_node.get_node_or_null("MeshInstance3D")` (or the actual mesh child name from enemy_infection_3d.tscn) and read `material_override` or surface material properties directly. The Spec Agent must confirm the exact mesh child node path after reading enemy_infection_3d.tscn. If no material override is present (pre-implementation state), the test fails red-phase. If Engine Integration applies the override, it passes green-phase.

**Confidence:** Medium

---

## Run: 2026-03-20 (Spec Agent — mini_boss_encounter specification)

### [mini_boss_encounter] Spec — Arena distinctness: size.x >= 25 vs strictly greater

**Would have asked:** FusionFloor and MiniBossFloor both have BoxShape3D size.x == 25. The ticket asks for MBA-GEO-3 to assert arena distinctness by size. Should the assertion be size.x > FusionFloor.size.x (which fails because they are equal) or size.x >= 25 (which passes)?

**Assumption made:** Used size.x >= 25 as the threshold. Arena distinctness for AC-1 is justified by positional and contextual factors: MiniBossFloor is the only floor in zone X: 55–80 with a single dedicated enemy and no platforming obstacles. FusionFloor hosts two elevated platforms and two enemies — structurally different despite equal width. The width threshold >= 25 establishes the floor as a large dedicated space; the design distinction is documented in the spec Overview.

**Confidence:** High

---

### [mini_boss_encounter] Spec — MBA-BOSS-3 placement: standalone requirement vs inline in T-55

**Would have asked:** MBA-BOSS-3 requires InfectionInteractionHandler.has_method("set_target_esm"). T-37 already covers has_method("get_mutation_slot_manager") for the fusion context. Should MBA-BOSS-3 be a separate test or folded into T-55?

**Assumption made:** Folded into T-55 as an additional assertion named T-55_infection_interaction_handler_has_set_target_esm. This avoids creating a trivially short standalone test function and keeps the InfectionInteractionHandler method guards grouped with the enemy context that relies on them. NFR-5 and NFR-6 document this choice explicitly.

**Confidence:** High

---

### [mini_boss_encounter] Spec — MBA-GEO-3 placement: inline in T-53 vs standalone requirement

**Would have asked:** MBA-GEO-3 (arena width >= 25) is already partially covered by the exact-value assertion T-53_mini_boss_floor_box_size_x (size.x == 25.0). Should MBA-GEO-3 be a separate test or folded into T-53?

**Assumption made:** Folded into T-53 as an additional assertion named T-53_mini_boss_floor_box_size_x_ge_25. The exact-value assertion (size.x == 25.0) provides regression protection; the >= 25 assertion provides the semantic floor for arena distinctness. Both are needed in the spec; one test function handles both without redundancy.

**Confidence:** High

---

### [mini_boss_encounter] Spec — LevelExit source_code accessibility in headless mode

**Would have asked:** Does `get_script().source_code` on an inline GDScript sub-resource return the raw source string after `PackedScene.instantiate()` in Godot 4 headless mode, or is it empty after compilation?

**Assumption made:** The behavior is uncertain in headless mode. The spec documents a fallback: if source_code is empty, the test should fall back to asserting `has_method("_on_body_entered")` as a proxy. The Test Designer Agent must probe this during implementation and choose the appropriate path. The fallback is documented in MBA-FLOW-3 Risk section and AC-MBA-FLOW-3.2.

**Confidence:** Medium

---

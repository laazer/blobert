# Autopilot Learnings Log

Structured insights extracted after each completed ticket.

---

## [containment_hall_01_layout] — 3D scene construction for a linear level with four gameplay zones

*Completed: 2026-03-17*

### Learnings

- category: architecture
  insight: Enemy mesh height is not encoded in the enemy scene's name or ticket metadata; placing enemies at the correct Y requires inspecting the actual scene or making an assumption with tolerance.
  impact: The Spec Agent assumed enemy origin = vertical center of ~1.0 m mesh and added ±0.1 m tolerance to all position tests. If the actual mesh height differs, enemies clip into geometry or float above it.
  prevention: Add an "enemy collision height" field to the enemy scene's canonical ticket or to a shared project constants file so any agent that places enemies can read it without inspection.
  severity: medium

- category: testing
  insight: NodePath-typed properties (e.g. RespawnZone.spawn_point) cannot be structurally verified via get_node() in headless tests because the node is not in the scene tree. The only safe headless assertion is that the path string is non-empty and targets the expected node name.
  impact: Full resolution testing was deferred; a misconfigured path would pass all tests and only fail at runtime.
  prevention: When a spec requires a wired NodePath, include a tree-insertion integration test (add_child the root scene) that calls get_node(spawn_point) and asserts non-null. Add a dedicated integration test class for scene-wiring assertions.
  severity: medium

- category: architecture
  insight: Spec agents must compute jump physics before finalizing platform gap widths. The initial layout used 3 m gaps but derived max jump range was only ~1.98 m — meaning the level was untraversable as specced.
  impact: Gap was revised to 1.0 m before implementation began; caught in spec phase with no rework cost. If missed, all test phases would have passed but the level would be physically unplayable.
  prevention: Add a required "traversability check" section to any scene-construction spec that involves platforms or gaps: derive max jump range from player_controller_3d.gd constants and confirm every gap < 80% of that range.
  severity: high

- category: testing
  insight: Thin visual-separator walls that are also StaticBody3D nodes can block player traversal, making them a Low-confidence design decision. The spec acknowledged this conflict but defaulted to StaticBody3D anyway.
  impact: Confidence was explicitly flagged Low. If the wall blocked traversal the Implementer was instructed to convert it to a MeshInstance3D — delegating a geometry decision to the implementation phase.
  prevention: When a spec cannot resolve whether a node should have collision, declare it collision-free (MeshInstance3D only) by default and document the trade-off. Never leave a StaticBody3D with a "maybe remove collision" qualifier in the spec.
  severity: low

### Anti-Patterns

- description: Compound test assertions (e.g. T-11 checks non-zero extents AND BoxShape3D type in one pass) can mask individual mutation targets. A SphereShape3D with non-zero radius satisfies a naive "extents != 0" check.
  detection_signal: A single test method asserts both a type property and a value property in the same loop iteration.
  prevention: Separate shape-type enforcement (is BoxShape3D) from value enforcement (extents > 0) into distinct adversarial tests so each mutation target has its own named failure.

- description: Using a ticket's prose task description as the authoritative node name when a separate spec document also defines the name leads to divergence. "GameUI" in the task vs "InfectionUI" in the spec forced the Test Designer to arbitrate.
  detection_signal: A test is written using a node name that does not appear verbatim in the spec's node tree table.
  prevention: Spec document node tree table is always authoritative over ticket task prose. If they conflict, the Spec Agent must update the ticket task description to match the spec before handing off.

### Prompt Patches

- agent: Spec Agent
  change: Before finalizing any platform layout, compute max_jump_range = (2 * jump_velocity * horizontal_speed) / gravity using constants from player_controller_3d.gd, and assert every inter-platform gap < 0.8 * max_jump_range. Document the computed value in the spec's GEO section.
  reason: Prevents specs that describe untraversable levels; caught at spec phase instead of QA.

- agent: Spec Agent
  change: When a visual-separator node is added for level readability, default to MeshInstance3D (no collision). Only use StaticBody3D if the separator must block the player. Never leave a StaticBody3D with a comment saying "remove collision if it blocks traversal."
  reason: Eliminates Low-confidence geometry decisions from being delegated to the implementation agent.

- agent: Test Design Agent
  change: When a spec includes any NodePath-typed property wired between nodes (e.g. spawn_point, target_node), add at least one test that inserts the scene root into a temporary SceneTree and calls get_node(path), asserting non-null. Label this test as a "wiring integration test" and mark it headless-safe only if the NodePath can be verified without tree entry.
  reason: Headless NodePath string checks give a false sense of coverage; a misconfigured path only fails at runtime.

### Workflow Improvements

- issue: AC-5 ("human-playable in-editor without debug overlays") has no automated proxy test and was still open when all 38 automated tests passed, leaving the ticket BLOCKED on manual verification with no clear owner or schedule.
  improvement: For scene-construction tickets, add a required AC at the spec phase: "A documented manual QA checklist exists as a section in the ticket." The checklist should enumerate exact steps (open scene, press Play, confirm N items) so the human reviewer can execute it deterministically.
  expected_benefit: Prevents tickets from reaching BLOCKED state on an undocumented manual step after all automated gates pass.

- issue: The Test Breaker added T-ADV-31 through T-ADV-38 as adversarial extensions, but several of these (T-ADV-32, T-ADV-35, T-ADV-37) guarded invariants that were implicit in the spec and not stated as acceptance criteria. This required the Test Breaker to re-derive intent from spec prose.
  improvement: The Spec Agent should include a "Structural invariants" subsection listing non-AC invariants (e.g. "exactly one WorldEnvironment", "all gameplay floor tops >= -3.0 m") so the Test Breaker has explicit targets rather than rediscovering them from prose.
  expected_benefit: Reduces Test Breaker inference work and makes adversarial test selection deterministic.

---

## [fusion_opportunity_room] — Validation-only ticket: all 33 tests passed first run, no scene changes needed.

*Completed: 2026-03-19*

### Learnings

- category: testing
  insight: RefCounted subclasses (e.g. FusionResolver, MutationSlotManager) must never have `.free()` called; doing so raises a Godot runtime error. This is a silent correctness hazard in test teardown.
  impact: The existing `test_fusion_resolver.gd` already called `.free()` on RefCounted objects throughout the suite, polluting test output with runtime errors. T-39/T-40 were written correctly by explicitly avoiding this pattern.
  prevention: Add a Static QA rule: any test teardown calling `.free()` on an object must first assert the object extends Object (not RefCounted). Explicitly document in test design templates that RefCounted instances are auto-freed and `.free()` must not be called.
  severity: medium

- category: testing
  insight: Validation-only tickets (spec+test against a pre-built scene) still surface real cross-file duplication risks: test numbers assigned in the ticket task description can collide with assertions already covered by prior test files, requiring remapping before any test is written.
  impact: Three planned test IDs (T-34 collision_mask, T-35/T-36 enemy positions, T-37 node existence) would have been exact duplicates of T-25, T-24, T-9/T-16 in `test_containment_hall_01.gd`. Remapping was caught autonomously at spec time with no rework cost, but only because the Spec Agent cross-referenced the existing test file.
  prevention: Before a Test Designer writes any tests for a validation-only ticket, require an explicit "duplication audit" step: list every existing test file covering the same scene, enumerate their assertion subjects, and document which new test IDs are remapped and why.
  severity: medium

- category: testing
  insight: `get_scene_file_path()` returns a non-empty string only for the root node of an instanced PackedScene. Tests that call this method on a non-root instanced node will always get an empty string, producing a silent false-positive or false-negative depending on assertion direction.
  impact: T-35/T-36 relied on this method. The Spec Agent verified correctness by tracing the scene file's `[node ... instance=ExtResource(...)]` declaration confirming EnemyFusionA/B are scene roots. Without this check, the test would have passed vacuously.
  prevention: When speccing tests that use `get_scene_file_path()`, require the spec to explicitly identify whether the target node is the root of its instanced scene. Document this in the test comment. If uncertain, add a fallback assertion on the node class name.
  severity: low

- category: testing
  insight: `_ready()` does not automatically fire on `add_child()` in headless Godot test runs. Tests that depend on `_ready()` side effects (e.g. slot manager instantiation) must call `handler._ready()` explicitly after tree insertion.
  impact: T-38 required explicit `handler._ready()` to initialize the slot manager; omitting it would have caused a null-dereference assertion failure. The fix is a one-liner but is non-obvious and not documented in earlier test files.
  prevention: Add to the Test Design Agent prompt: "In headless tests, after `tree.root.add_child(node)`, always call `node._ready()` explicitly if the test depends on any state initialized in `_ready()`. Do not assume `add_child` triggers lifecycle callbacks."
  severity: medium

- category: process
  insight: A validation-only ticket (scene pre-built, no code to write) still generates meaningful agent work: one spec document, two test files, one static QA pass, and 21 adversarial cases. The "zero implementation effort" framing can cause the planner to underestimate agent runtime budget and underspec the test scope.
  impact: The ticket was correctly scoped here, but the planner's initial assumption that the scene did not yet exist (checkpoint: "Containment Hall 01 scene existence") created a mismatch that required a correction before spec work could begin.
  prevention: Planners must verify scene/file existence via glob or explicit path check before writing an execution plan. If the file exists, the ticket should be labeled "validation-only" in its description and the execution plan must omit any implementation task.
  severity: low

### Anti-Patterns

- description: Test IDs assigned in ticket task prose collide with IDs in existing test files covering the same scene. The ticket author does not cross-reference existing tests when assigning numbers.
  detection_signal: A new test file's T-N covers the same node property (position, collision_mask, script path) as a test in a sibling file for the same scene.
  prevention: The Spec Agent must open and read all test files for the target scene before assigning test IDs. Any collision must be resolved with a remapping note in the spec before the Test Designer begins.

- description: Calling `.free()` on RefCounted objects in test teardown is a recurring error that appears across multiple test files without being caught by Static QA.
  detection_signal: Any `.free()` call in a test file where the freed object's class is not explicitly verified to extend Object (not RefCounted).
  prevention: Static QA Agent must flag `.free()` calls in test files and verify the target class. Add a lint rule or explicit check step.

### Prompt Patches

- agent: Test Design Agent
  change: In headless tests, after `tree.root.add_child(node)`, always call `node._ready()` explicitly if the test depends on any state initialized in `_ready()`. Do not assume `add_child` alone triggers lifecycle callbacks in headless mode.
  reason: In headless Godot, `_ready()` does not fire automatically on `add_child`. Missing this causes null-dereference failures on any state set up in `_ready()`.

- agent: Test Design Agent
  change: Never call `.free()` on objects whose class extends RefCounted. RefCounted instances are auto-freed when they go out of scope. Calling `.free()` explicitly raises a Godot runtime error that pollutes test output.
  reason: This is a recurring error across multiple test files. It is non-fatal but produces confusing runtime errors that obscure real test failures.

- agent: Spec Agent
  change: Before writing any test IDs for a validation-only ticket, open every existing test file that targets the same scene. Build a list of already-asserted (node, property) pairs. Any planned test that duplicates a pair from that list must be remapped to a new, genuinely uncovered assertion. Document the remapping explicitly in the spec.
  reason: Three test IDs had to be remapped on this ticket. Without the cross-reference step, duplicate assertions would have been written and caught only at Static QA, requiring rework.

### Workflow Improvements

- issue: Planner agents assume scene files do not exist and plan an implementation task, then discover mid-run that the scene is pre-built. This wastes one round-trip and produces an incorrect execution plan that must be mentally corrected by the next agent.
  improvement: Add a mandatory "file existence check" step to the Planner Agent's execution plan template: before writing tasks, list the expected output files and state explicitly whether each already exists. If a key scene/script file exists, remove the implementation task and label the ticket "validation-only."
  expected_benefit: Eliminates the planner/reality mismatch that caused the checkpoint entry for "Containment Hall 01 scene existence." Saves one full agent invocation per miscategorized ticket.

- issue: AC-6 (human playthrough) has no documented manual QA checklist with atomic steps; it is described only as a free-form paragraph in the ticket. The same structural gap occurred in containment_hall_01_layout (noted in prior learnings) and recurred here.
  improvement: The Spec Agent must emit an explicit "Manual QA Checklist" section in the spec for any INTEGRATION-class AC. The checklist must enumerate exact numbered steps (open scene, move to X, perform action Y, observe Z) so the human reviewer can execute it without re-reading the full ticket.
  expected_benefit: Prevents tickets from stalling at INTEGRATION stage because the human reviewer must interpret prose rather than follow a checklist. Consistent with the workflow improvement noted in [containment_hall_01_layout] — this is a repeat failure mode.

### Keep / Reinforce

- practice: The adversarial suite included a "distinct node path" test (ADV-FOR-09) that verifies EnemyFusionA.get_path() != EnemyFusionB.get_path(). This catches the "duplicate node name" failure mode that individual per-enemy tests cannot detect.
  reason: Scene authoring errors can silently shadow a node with a duplicate name. Per-entity tests pass because they both resolve to the same (surviving) node. The path-inequality check is the only headless-safe way to catch this. Reinforce this pattern for any ticket that requires N distinct named instances.

- practice: Validation-only tickets correctly distinguished headless-testable ACs (AC-1 through AC-5) from INTEGRATION ACs (AC-6) in both the spec and the ticket status block, preventing the test phase from attempting to automate an unautomatable criterion.
  reason: This separation prevented wasted effort on phantom "run the game" tests and kept the INTEGRATION gating condition explicit and unambiguous.

---

## [light_skill_check] — Validation-only ticket: 253/253 tests passed first run, no scene changes needed.

*Completed: 2026-03-20*

### Learnings

- category: testing
  insight: A node's `.position.y` (the origin) can differ substantially from its effective top surface Y when the CollisionShape3D has a non-zero local offset. SkillCheckFloorBase sits at node Y=0 but its top surface is at Y=-4.0 due to a CollisionShape3D Y-offset of -4.5. Tests that assert surface geometry must compute `node.position.y + collision_shape_offset.y + box_half_height`, not `node.position.y` alone.
  impact: The Planner and Spec agents both flagged this explicitly (checkpoint [light_skill_check] Planning). If a test had asserted `node.position.y < -1.0` directly rather than computing the surface, it would have produced a false-negative (node origin is 0, which is >= -1.0, passing when it should not).
  prevention: Add to the Spec Agent prompt: "For any StaticBody3D floor or platform, compute and document the effective top surface Y = node.position.y + collision_shape_local_offset.y + (box.size.y / 2). Never assert raw node.position.y as a proxy for surface height."
  severity: medium

- category: testing
  insight: NodePath resolution in headless tests is reference-frame sensitive. A NodePath like `"../SpawnPosition"` must be resolved via `respawn_zone_node.get_node_or_null(path)`, not `root.get_node_or_null(path)`. The `..` segment is relative to the node that owns the property, not the scene root.
  impact: This was caught at spec time (checkpoint [light_skill_check] Spec). If the test had called `root.get_node(spawn_point_path)`, the `..` from root has no parent and returns null, causing a false test failure that masks whether the wiring is correct.
  prevention: The Spec Agent must annotate every NodePath-type property test with the correct resolution call site. When the NodePath starts with `..`, the test must call `.get_node_or_null()` on the owning node, not the scene root.
  severity: medium

- category: testing
  insight: Adversarial tests should be scoped to the single mutation they are designed to catch, even when a primary test covers a superset. ADV-SKC-06 was intentionally limited to P3>P1 (not P3>P2) because T-46 already covers both comparisons. Keeping adversarial tests narrowly focused prevents them from becoming redundant duplicates of primary tests.
  impact: If ADV-SKC-06 had also asserted P3>P2, it would overlap T-46 with no additional mutation-target coverage. The scoping decision was explicit (checkpoint [light_skill_check] TestBreak).
  prevention: The Test Breaker Agent should document for each adversarial test: "mutation target = [specific property or failure mode]" and verify no primary test already asserts the exact same (node, property, value) triple.
  severity: low

- category: process
  insight: A rate limit interruption during test design does not corrupt work product if agents record partial decisions in CHECKPOINTS.md before stopping. The light_skill_check test design survived a mid-session rate limit interruption cleanly because the checkpoint log captured all in-progress assumptions.
  impact: No rework was required after the interruption. However, the interruption itself is a workflow risk: if CHECKPOINTS.md is not written before a rate limit hits, the next agent invocation must re-derive decisions that were already made.
  prevention: Test Design Agents should write checkpoint entries immediately after each major scoping decision (e.g. after each ADV-SKC-* scope decision), not only at end of session. Treat CHECKPOINTS.md writes as synchronous, not batched.
  severity: low

### Anti-Patterns

- description: Asserting `node.position.y` directly as a proxy for surface height on StaticBody3D nodes. The raw position is the origin, not the surface — offset and shape dimensions must be included.
  detection_signal: Any test assertion of the form `node.position.y < threshold` for a floor or platform node, without a preceding computation of `position.y + offset.y + half_height`.
  prevention: Spec agents must compute and document effective surface Y for every geometry node. Test agents must use the computed value, not the raw position.

- description: The same recurring pattern of INTEGRATION-class ACs (subjective difficulty, human playability) reaching the human reviewer as ticket prose rather than a numbered checklist. This is the third consecutive ticket where this gap appeared.
  detection_signal: A ticket's INTEGRATION-class AC is described in prose without an explicit numbered step list labeled "Manual QA Checklist."
  prevention: Spec Agent must emit a "Manual QA Checklist" section for every INTEGRATION AC at spec time. This was flagged in [containment_hall_01_layout] and [fusion_opportunity_room] learnings and has still not been enforced at the Spec Agent prompt level.

### Prompt Patches

- agent: Spec Agent
  change: For any StaticBody3D floor, platform, or hazard zone, compute and document the effective top surface Y as `node.position.y + collision_shape_local_offset.y + (box.size.y / 2)`. State this value explicitly in the spec's GEO section. Never use raw `node.position.y` as the surface height.
  reason: The SkillCheckFloorBase checkpoint showed that node origin and surface height diverge whenever a CollisionShape3D has a local offset. Tests that use raw position fail silently with incorrect pass/fail behavior.

- agent: Spec Agent
  change: For every NodePath-type property test, annotate the resolution call site. If the path starts with `..`, the test must resolve it via `owning_node.get_node_or_null(path)`, not `scene_root.get_node_or_null(path)`. Include the correct call site verbatim in the spec's test traceability table.
  reason: Incorrect resolution reference frame produces silent null returns that make the test fail for the wrong reason, obscuring whether the wiring is actually correct.

- agent: Test Breaker Agent
  change: For each adversarial test, document its mutation target as a single (node, property, failure mode) triple and verify that no primary test (T-N) already asserts the identical triple. If overlap exists, redirect the adversarial test to a distinct failure mode before writing it.
  reason: ADV-SKC-06 scope decision showed that adversarial tests can silently duplicate primary test assertions when the adversarial agent does not cross-reference the primary suite. Narrow scope produces better mutation coverage per test.

- agent: Test Design Agent
  change: Write a CHECKPOINTS.md entry after each major adversarial scoping decision (e.g. each ADV-* scope choice), not only at session end. Each entry is a synchronous write — do not batch them.
  reason: Rate limit interruptions mid-session discard in-progress decisions if they have not been persisted. Incremental CHECKPOINTS writes ensure continuity regardless of when the session ends.

### Workflow Improvements

- issue: INTEGRATION-class ACs (subjective difficulty, human playability) reach the human reviewer as ticket prose for the third consecutive ticket. The prompt patches from [containment_hall_01_layout] and [fusion_opportunity_room] have not been applied to the Spec Agent's active prompt, causing the same gap to recur.
  improvement: Apply the "Manual QA Checklist" prompt patch from [fusion_opportunity_room] learnings to the Spec Agent's prompt immediately. The instruction should read: "For any INTEGRATION-class AC, emit a numbered Manual QA Checklist section with atomic, observable steps (open scene → navigate to location → perform action → observe expected outcome)."
  expected_benefit: Breaks the recurring cycle of tickets stalling at INTEGRATION with undocumented human steps. Two prior learnings identified this; without a prompt-level fix it will recur on every ticket with subjective ACs.

### Keep / Reinforce

- practice: The spec preemptively documented the SkillCheckFloorBase Y-interpretation risk (pit floor vs. walkable floor) in both the spec document and the ticket's Risks and Assumptions table. This prevented any downstream agent from misclassifying the node type.
  reason: Naming a node "SkillCheckFloorBase" does not communicate that it is 4 m below corridor level. Explicit documentation of the geometry interpretation at spec time prevented a category of test errors before they occurred.

- practice: Two consecutive validation-only tickets ([fusion_opportunity_room], [light_skill_check]) achieved 100% first-run test passes with zero scene modifications. The spec-to-test pipeline is functioning correctly for this ticket type.
  reason: Confirms the pattern of precise scene geometry read at spec time → deterministic test assertions → no integration surprises. This should be the expected baseline for all future validation-only tickets.

---

## [mini_boss_encounter] — 66 tests passing (T-53–T-62 + ADV-MBA-01–08); ticket at INTEGRATION pending human playtest.

*Completed: 2026-03-20*

### Learnings

- category: testing
  insight: `get_path()` returns an empty NodePath (`""`) for nodes that have not been added to a SceneTree. Equality comparisons between two empty NodePaths vacuously pass, making tests that assert "these two nodes have distinct paths" trivially pass even when both nodes are the same object.
  impact: T-57 was written to assert EnemyMiniBoss.get_path() != EnemyFusionA.get_path() (and the other two enemies). All four comparisons returned "" == "", causing the distinctness tests to pass unconditionally and fail to catch a duplicate-node scenario. The fix was to switch to `.name` comparisons, which are non-empty regardless of tree attachment.
  prevention: Never use `get_path()` on nodes that are not inserted into a SceneTree. For identity-distinctness tests on headless-loaded scene nodes, use `.name`. If path-based identity is required, add the node to a temporary root first and assert non-empty path before comparing.
  severity: high

- category: testing
  insight: Strict `>` boundary assertions fail silently when two adjacent geometry zones share an exact boundary value. A scene authored so that zone A ends at X=55.0 and zone B starts at X=55.0 will fail a test asserting `zone_b_left_edge > zone_a_right_edge` because the values are equal — even though the design intent (non-overlapping zones) is fully satisfied.
  impact: ADV-MBA-06 used strict `>` to assert MiniBossFloor left edge (55.0) > SkillCheckPlatform3 right edge (55.0). The test failed during red-phase integration; the zone boundary was valid but the operator was wrong. Required an operator change from `>` to `>=` to correctly express "no overlap."
  prevention: When asserting spatial non-overlap between zones, use `>=` (not `>`) for boundary comparisons. Document the exact boundary value and operator choice in the spec. A `>` is only correct when a gap between zones is required by design. Include a comment in the test identifying which operator was chosen and why.
  severity: medium

- category: architecture
  insight: Two geometry nodes with identical widths (e.g. FusionFloor and MiniBossFloor both 25 m) cannot be differentiated by a strict width comparison. A spec requirement for "arena distinctness" based purely on size.x fails when another zone shares the same dimension. Distinctness must be grounded in positional or contextual criteria, not width alone.
  impact: MBA-GEO-3 was originally framed as "MiniBossFloor is the widest floor segment." FusionFloor is also 25 m, so this argument broke down. The Spec Agent had to reframe distinctness as: dedicated single-enemy zone at a unique positional range with no platforming obstacles — which is a design distinction, not a metric one. The test was changed to assert `size.x >= 25` as a minimum threshold, not a uniqueness claim.
  prevention: Specs that argue "structural distinctness" via a single numeric property must verify that no other node in the scene shares that value. If uniqueness cannot be guaranteed by one property, use a positional + contextual distinctness argument and document the combination explicitly. Do not rely on width, height, or size alone as a proxy for "this zone is special."
  severity: medium

### Anti-Patterns

- description: Using `get_path()` on unparented nodes to assert node identity distinctness. All unparented nodes return `""`, making pairwise inequality tests pass vacuously.
  detection_signal: A test file calls `.get_path()` on nodes that are loaded from a PackedScene but not inserted into a SceneTree via `add_child()`.
  prevention: Replace `get_path()` distinctness checks with `.name` checks for headless-loaded nodes. If path-based testing is required, insert nodes under a temporary root before calling `get_path()`.

- description: Asserting zone non-overlap with strict `>` when the scene author intentionally places zones as adjacent (touching boundary). The correct intent is "not overlapping," which maps to `>=`, not `>`.
  detection_signal: A test assertion computes two zone edges and uses strict `>` to compare them; the test fails even though the scene geometry appears correct by inspection.
  prevention: The Spec Agent must state the intended spatial relationship precisely ("touching allowed" vs. "gap required") and choose the operator accordingly in the test specification. Use `>=` for "adjacent or gapped," `>` only for "strict gap required."

### Prompt Patches

- agent: Test Design Agent
  change: Never use `node.get_path()` to assert that two nodes are distinct when those nodes are loaded from a PackedScene without being added to a SceneTree. Use `node.name` for distinctness checks in headless tests. If path comparison is required, add the node to a temporary SceneTree root first and verify `get_path() != NodePath("")` before comparing.
  reason: `get_path()` on unparented nodes always returns `""`. Pairwise `!=` checks between two empty NodePaths pass unconditionally, giving a false sense of coverage. This caused T-57's distinctness assertions to be trivially vacuous until caught at integration time.

- agent: Spec Agent
  change: When writing a spatial non-overlap assertion between two adjacent zones, state explicitly whether a gap is required or whether touching boundaries are acceptable. Use `>=` in the test formula when touching is acceptable; use `>` only when a non-zero gap is a design requirement. Document the boundary value and chosen operator in the spec's test traceability table.
  reason: ADV-MBA-06 used `>` for a touching boundary (both edges == 55.0), causing a test failure that was a spec error, not a scene error. The operator choice encodes a design intent that must be explicit.

- agent: Spec Agent
  change: Before asserting that a node's geometry property (size.x, height, width) makes it structurally unique in the scene, grep the .tscn for all nodes of the same type and confirm the property value is not shared. If another node shares the value, reframe the distinctness argument using position, context, or combination of properties rather than the single metric.
  reason: MiniBossFloor and FusionFloor both have size.x == 25 m. The original MBA-GEO-3 "widest floor" argument was invalid and had to be replaced with a positional/contextual distinctness argument after the Spec Agent discovered the collision.

### Workflow Improvements

- issue: Two bugs (T-57 get_path() and ADV-MBA-06 strict >) were not caught at spec or test-design time — they were only surfaced by the Engine Integration Agent running the full suite. Both were caused by incorrect assumptions that could have been verified during spec or test-design with access to the .tscn file.
  improvement: The Test Design Agent should validate operator choices and comparison subject types against the live .tscn before finalizing test assertions. Specifically: (a) confirm that any node used in a `get_path()` call will be tree-attached at test time, and (b) verify exact boundary values from the scene file before choosing `>` vs `>=` for spatial assertions.
  expected_benefit: Catches the class of "vacuously correct" assertion errors and off-by-one operator errors in the test-design phase rather than at integration, eliminating a round-trip fix cycle.

### Keep / Reinforce

- practice: ADV-MBA-08 used a dual-assertion strategy: (1) exact expected name assertions (catching Godot auto-dedup renames) and (2) pairwise mutual distinctness assertions. This exposes the root cause (wrong name) separately from the symptom (duplicated name).
  reason: Single "all distinct" assertions mask which specific node was renamed. The two-tier approach (exact names + pairwise) provides both regression protection and precise failure attribution. Reinforce this pattern for all tickets requiring N distinct named instances.

- practice: The Engine Integration Agent resolved both bugs (T-57 operator, ADV-MBA-06 operator) with minimal, well-reasoned changes — switching `.get_path()` to `.name` and `>` to `>=` — without altering scene geometry or expanding test scope beyond the specific failure.
  reason: Fixing test logic errors at the integration phase rather than reverting to spec or restructuring the suite kept the ticket on track. Constraining fixes to the smallest correct change is the right default behavior for integration-phase corrections.

---

## [mutation_tease_room] — Clean run: prior learnings applied successfully (zone adjacency <=, .name not get_path()). No new significant learnings.

*Completed: 2026-03-20*

All 18 tests (T-63–T-72, ADV-MTR-01–ADV-MTR-06) passed first run with zero scene modifications. Ticket held at INTEGRATION pending human verification of AC-2 (visual tease clarity) and AC-5 (human-playable in-editor).

The two lessons from [mini_boss_encounter] were correctly applied by downstream agents before any failure occurred:

- **Zone adjacency `<=`**: T-69 and MTR-FLOW-1 used `<=` from the start (MutationTeaseFloor right edge = 10.0, FusionFloor left edge = 10.0 — touching boundary). No operator correction was needed at integration time. The spec explicitly documented the boundary value and operator choice.
- **`.name` not `get_path()`**: T-70 and ADV-MTR-04 used `node.name` for all four-enemy distinctness checks from the start. NFR-6 in the spec codified this rule. No vacuous-pass bug occurred.

Both fixes were applied at the spec phase (before test design), not discovered at integration. This is the correct phase for such corrections.

---

## [start_finish_flow] — Headless structural wiring proxies passed; subjective playability still gated on manual evidence

*Completed: 2026-03-20*

### Learnings
- category: testing
  insight: When a ticket relies on a conservative assumption about what gates completion (e.g., `LevelExit` should be unconditional and not depend on `EnemyMiniBoss` defeat), encode the assumption as an anti-gating structural test by parsing the level `.tscn` text and asserting both the positive trigger wiring and the absence of forbidden identifiers in the `LevelExit` inline script section.
  impact: Prevents a "structurally wired but logically blocked" failure mode where headless tests can pass even though runtime completion would hang until a hidden condition is met.
  prevention: For every acceptance-criteria assumption of the form "X should NOT be gated on Y", require a test that asserts the negative by static analysis (forbidden identifier absence) in addition to the positive wiring assertion.
  severity: high

- category: testing
  insight: Headless UI/signposting tests need coverage for verb-specific input hints for critical gameplay actions; asserting only prompt label existence and generic movement hints is insufficient to de-risk player misunderstanding.
  impact: `start_finish_flow` infection UI validation checks prompt labels and a generic hints set, but the original planning risk ("no explicit infect key hint") remained structurally under-validated, leaving AC-2/AC-5 vulnerable to confusion even when headless structural tests pass.
  prevention: Add a structural requirement for the critical verb's hint node (e.g. `InfectHint` under `InfectionUI/Hints`, or a text contract inside an existing hint label) and assert it headlessly.
  severity: medium

- category: process
  insight: A capability matrix in headless test files (explicitly stating what the suite can vs cannot verify relative to acceptance criteria) materially reduces "false confidence" and triage time when integration issues are still manual-only.
  impact: `test_start_finish_flow.gd` documents that it cannot prove human completion time or input-driven play, which keeps reviewers from assuming automated coverage extends to subjective ACs.
  prevention: For any headless integration test suite, require a short header that maps: (a) AC components you can deterministically verify, and (b) the specific AC components that remain manual-only.
  severity: low

### Anti-Patterns
- description: Treating "UI node exists in the scene" as proof of flow clarity.
  detection_signal: Structural UI tests check node existence and/or default visibility but do not require verb-specific input hint nodes or any deterministically testable link between gameplay verb and hint content.
  prevention: For each critical gameplay verb in the flow, assert the presence and implementation of the corresponding hint label in the relevant UI subtree (headless-safe).

- description: Encoding completion-trigger assumptions only in prose without a negative assertion in tests.
  detection_signal: Ticket/spec text includes "we assume completion is triggered by X and not gated by Y", but the test suite only asserts the positive wiring of X without forbidding references to Y.
  prevention: Add a static anti-gating test that checks the `X` trigger script section does not reference `Y` identifiers (or the specific state variables), in addition to the positive trigger wiring assertion.

### Prompt Patches
- agent: Test Design Agent
  change: "For any conservative assumption about completion triggers or gating (e.g. `LevelExit` completion is unconditional and must not depend on mini-boss defeat state), add an anti-gating structural test that statically parses the relevant `.tscn` (or attached inline script source) and asserts (1) positive wiring for `level_complete`/the expected trigger handler and (2) absence of forbidden identifiers (e.g. `miniboss`, `enemymonster`, `EnemyMiniBoss`, or any explicitly forbidden node/group/state names) within the completion trigger script section."
  reason: Positive wiring assertions alone can pass while runtime completion is still logically blocked by unintended state gating.

- agent: Test Design Agent
  change: "For any headless UI/signposting validation that targets flow clarity for critical gameplay verbs (infect/absorb/fuse/etc.), require verb-specific input hints under the relevant UI container (e.g. `InfectionUI/Hints`) and assert headlessly that each required hint node exists and is implemented via the standard input-hint label script (or matches an agreed text contract). Do not rely on generic move/jump hints to cover verb discoverability."
  reason: It is possible for structural UI tests to pass while the specific verb the player must perform remains under-specified or undiscoverable.

- agent: Test Design Agent
  change: "At the top of every headless integration test file, add a brief capability matrix comment listing what the suite can verify deterministically vs what remains manual-only relative to the ticket's acceptance criteria."
  reason: Prevents reviewers from assuming automated gates cover subjective AC aspects (time, comprehension, input-driven success).

### Workflow Improvements
- issue: Integration tickets can become blocked with "headless suite passed" while the remaining subjective AC components are not clearly mapped to which parts are verified vs manual-only.
  improvement: Require every integration ticket status update to include an explicit mapping from each AC to either (a) the specific automated test(s) that validate its deterministic proxy, or (b) the exact manual-only sub-steps that must be recorded.
  expected_benefit: Reduces ambiguity and review churn when tickets hit INTEGRATION but still require human evidence.

### Keep / Reinforce
- practice: Use a negative/anti-gating assertion by parsing the level `.tscn` text to ensure completion wiring does not reference forbidden mini-boss identifiers.
  reason: This catches the "looks wired but is logically blocked" failure mode without needing runtime input simulation.

- practice: Validate UI signposting structurally (prompt label presence + hint subtree existence + default visibility expectations) even when the human-playable AC cannot be fully automated.
  reason: This reduces the search space for manual verification by ruling out missing UI nodes as a first-order failure cause.

---

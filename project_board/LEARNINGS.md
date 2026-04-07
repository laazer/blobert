# Autopilot Learnings Log

Structured insights extracted after each completed ticket.

---

## [M19-ARGLB] — Path-jail hardening and clip-state ownership must be explicitly tested

*Completed: 2026-04-07*

### Learnings

- category: testing
  insight: HTTP client normalization can hide traversal payloads before the app handler runs, so security assertions tied to literal `..` URLs are not reliable as primary evidence.
  impact: Literal traversal tests produced route-level misses while encoded traversal cases exposed the real guard behavior; this created rework in test intent and interpretation.
  prevention: Treat encoded traversal vectors as the canonical app-layer security tests, and keep literal-dot requests as transport-behavior documentation only.
  severity: high

- category: architecture
  insight: Path-jail guards must wrap both path resolution and file-type checks, not only ancestry checks, because error modes occur before or after `relative_to` in real payloads.
  impact: Null-byte and directory-path inputs triggered unhandled exceptions until `resolve()` guarding and explicit `is_file()` handling were added.
  prevention: Standardize secure file-serving guard order as: resolve safely -> enforce jail ancestry -> enforce allowed top-level directory -> enforce `is_file()` -> serve.
  severity: high

- category: process
  insight: Pre-scaffolded tickets still need full spec-and-test passes because "mostly implemented" code hides contractual drift and state-model mistakes.
  impact: A functional UI path still had incorrect clip-state ownership (`setAvailableClips` behavior conflated with active animation), discovered only during gap analysis.
  prevention: For scaffold-first tickets, require a mandatory gap table that validates state ownership, not just acceptance-criteria surface behavior.
  severity: medium

### Anti-Patterns

- description: Using literal `..` requests as the sole traversal proof in ASGI/httpx tests.
  detection_signal: Traversal tests fail with route misses/non-200 while encoded-path tests exercise handler logic and produce different status semantics.
  prevention: Pair every traversal test set with encoded equivalents and label which layer (client normalization vs app guard) each test validates.

- description: Collapsing "available options" and "selected option" into one UI store field.
  detection_signal: New model loads force a default selection regardless of actual loaded data, or controls render fallback options despite real runtime data existing.
  prevention: Keep separate store slices/actions for inventory/exposure (`availableClips`) versus selection (`activeAnimation`) and test both transitions.

### Prompt Patches

- agent: Test Designer Agent
  change: "For path traversal/security routes tested through httpx/ASGITransport, include both literal-dot and percent-encoded traversal cases, and annotate each test with the validation layer it targets (transport normalization vs app guard)."
  reason: Prevents false confidence from client-side URL normalization.

- agent: Implementation Agent
  change: "When implementing file-serving path jails, guard `resolve()` exceptions and enforce `is_file()` before `FileResponse`; do not rely solely on `relative_to` ancestry checks."
  reason: Captures common real-world failure paths that bypass naive jail logic.

- agent: Planner Agent
  change: "If a ticket starts from pre-existing scaffold code, add an explicit 'state ownership and data-flow gap audit' task before implementation, even when ACs appear mostly covered."
  reason: Reduces late-cycle discovery of architectural miswiring hidden by superficially working behavior.

### Workflow Improvements

- issue: Security tests initially mixed transport-normalization behavior and app-guard behavior under one expectation.
  improvement: Add a workflow convention that security-related test IDs must declare the layer under test in test comments and AC mapping notes.
  expected_benefit: Faster debugging and fewer red/green misreads during Test Design and Test Breaker stages.

- issue: "Preferred" vs "required" status-code semantics for directory-path handling created inconsistent assertions until implementation tightened behavior.
  improvement: During spec stage, convert ambiguous status-code language into mandatory or optional clauses with explicit test strategy (strict vs permissive assertions).
  expected_benefit: Fewer assertion rewrites and cleaner handoff from spec to test suites.

### Keep / Reinforce

- practice: Adversarial expansion beyond happy-path ACs (null-byte, double-encoded traversal, case-variant extensions, stress list cardinality).
  reason: Exposed implementation gaps quickly and produced durable regression coverage.

- practice: AC gatekeeping that ties each acceptance criterion to concrete test evidence or explicit manual-verification notes.
  reason: Enables honest completion decisions without claiming unproven browser behavior.

---

## [carapace_enemy_attack] — Telegraph floor extended via optional parameter

*Completed: 2026-04-06*

### Learnings

- category: gameplay
  insight: `ATS2_MIN_TELEGRAPH` (0.3s) is a global floor for all ranged telegraphs; families that need a longer wind-up (carapace 0.6s) should pass `min_hold_seconds` into `begin_ranged_attack_telegraph` so the controller stores `_telegraph_min_hold_sec = max(ATS2_MIN_TELEGRAPH, requested)` without duplicating timer logic in each attack script.
  impact: Acid/adhesion default call sites unchanged; carapace meets AC without a second post-signal timer.
  prevention: When adding a third telegraphed attack with a custom minimum hold, use the same parameter rather than stacking SceneTreeTimers on the attack node.
  severity: low

- category: engine_integration
  insight: The adhesion `enemy_writes_velocity_x_this_frame` gate on `EnemyInfection3D` composes additively: a second attack family (carapace) needs the same check so horizontal velocity from charge/decel is not cleared before `move_and_slide()`.
  impact: Any future dash attack must register in this gate or extract a single helper that ORs child overrides.
  severity: low

---

## [hitbox_and_damage_system] — Tests cannot reference `class_name` before global registration

*Completed: 2026-04-06*

### Learnings

- category: testing
  insight: Godot test scripts loaded by `run_tests.gd` may parse before global `class_name` symbols from other scripts are visible, producing "Could not find type X in the current scope" even when the implementation script exists.
  impact: Primary hitbox tests failed to load until `EnemyAttackHitbox` references were replaced with `preload("res://scripts/enemies/enemy_attack_hitbox.gd").new()` and `Area3D`-typed locals.
  prevention: For new `class_name` types consumed only from tests, prefer `preload` + `.new()` or defer typed hints until the type is guaranteed registered.
  severity: medium

---

## [adhesion_enemy_attack] — Enemy body must cooperate with child-driven lunge velocity

*Completed: 2026-04-07*

### Learnings

- category: engine_integration
  insight: `EnemyInfection3D._physics_process` unconditionally zeroed `velocity.x` every frame, so any child attack script could not move the enemy horizontally without changing the base class. A narrow gate (`enemy_writes_velocity_x_this_frame` on `AdhesionBugLungeAttack` + lower `process_physics_priority`) lets the child set `velocity.x` before `move_and_slide()` without forking the enemy scene per attack type.
  impact: Lunge works with existing generated enemy scenes; acid spitter unchanged.
  prevention: Future melee dashes should reuse the same pattern or extract a small “locomotion override” API on the enemy body.
  severity: medium

- category: gameplay
  insight: Player “root” is implemented as zero horizontal input, blocked jump press for the window, and `velocity.x = 0` after `simulate` and after `move_and_slide`, with a monotonic timer decremented at end of `_physics_process` so the full frame is rooted.
  impact: Avoids friction-only drift and avoids consuming the root timer before movement logic runs.
  prevention: If wall-cling or knockback is added, re-validate that rooted frames cannot gain horizontal speed from non-input sources.
  severity: low

---

## [acid_enemy_attack] — DoT tick count vs time_left; integrate acid attack after GLB animation wiring

*Completed: 2026-04-06*

### Learnings

- category: gameplay
  insight: Modeling enemy acid DoT as `time_left` plus `accum` with a `while` loop risks an off-by-one on the final tick (sixth 0.5s tick in a 3s window) and, with pathological `delta`/`interval` values, an unbounded inner loop. A `ticks_remaining` budget derived from `round(duration / interval)` is deterministic and matches the AC wording.
  impact: AEAA-02 initially failed until the tick-count model replaced time-window gating on the last tick.
  prevention: For interval-based effects over a fixed duration, prefer explicit tick budgets or integration tests that assert total tick count, not only total damage.
  severity: medium

- category: engine_integration
  insight: Spawning the acid attack controller in `EnemyInfection3D._ready()` runs before GLB libraries are merged onto the root `AnimationPlayer`, so `Attack` may be missing and telegraph falls back to a timer. Deferring attachment to `_wire_and_notify_animation()` ensures `begin_ranged_attack_telegraph()` can use the real clip when present.
  impact: Reliable telegraph in generated acid spitter scenes; gobot placeholder still uses fallback if `Attack` is absent.
  prevention: Any feature that depends on post-import animation libraries should wire after the same deferred path that copies libraries to the root player.
  severity: medium

---

## [death_animation_playthrough] — Completion-gated despawn must handle missing clips; `_ready`/`get_tree` guards for testable handlers

*Completed: 2026-04-04*

### Learnings

- category: architecture
  insight: Any lifecycle that waits on `animation_finished` (or similar) after latching “death” state must still call `play()` on a real clip, or the signal never fires and the entity can remain in a half-torn-down state (e.g. collision cleared, never freed).
  impact: GDScript review flagged a critical bug: missing `Death` clip left collision-disabled enemies stuck in the tree until review added an immediate `queue_free` path when `has_animation(&"Death")` is false.
  prevention: For completion-driven teardown, branch explicitly: if the clip does not exist, run the same post-death cleanup and despawn synchronously; do not assume assets always contain the clip.
  severity: high

- category: testing
  insight: In Godot 4.6.x headless tests, lambdas capturing a plain `int` may not observe increments across concurrent `animation_finished`-style emissions; mutable state for demos should live in a `RefCounted` helper, `Array`, or `Dictionary` that the closure closes over by reference.
  impact: Test Breaker’s concurrent-signal adversarial case needed a non-primitive capture pattern to assert ordering reliably.
  prevention: When authoring multi-emission signal tests, use reference types or documented container captures; avoid primitive-only closure state for mutation across frames.
  severity: medium

- category: architecture
  insight: `Node._ready()` that calls `get_tree()` without checking `is_inside_tree()` produces engine errors and brittle behavior when the node is constructed for unit tests that call `_ready()` before `add_child`.
  impact: Checkpoint noted orphan-handler noise; implementation added `is_inside_tree()` guard so headless infection/absorb suites stay clean.
  prevention: Guard `get_tree()` / tree queries in `_ready()` with `is_inside_tree()`, or defer tree access to `NOTIFICATION_ENTER_TREE` / first frame.
  severity: medium

- category: process
  insight: Spec left “end of Death play” as abstract completion semantics; behavior was locked by tests + implementation binding to `animation_finished`. Naming the concrete signal in the spec would reduce implementer ambiguity.
  impact: Low rework cost here, but increases review surface until tests exist.
  prevention: When AC is “plays to completion,” spec should cite the bound Godot API (signal or method) once the engine version is fixed.
  severity: low

### Anti-Patterns

- description: Latching a disabled-collision or no-interaction “dying” state then awaiting a completion signal without guaranteeing `play()` runs for that animation.
  detection_signal: Enemy never freed after death; `animation_finished` never logged; assets missing the expected clip name.
  prevention: Pair latch with `has_animation` check and a synchronous fallback teardown path.

- description: `_ready()` assumes the node is already in the scene tree.
  detection_signal: Headless test logs show `get_tree()` on orphan node; handler tests use manual `_ready()` before `add_child`.
  prevention: `is_inside_tree()` guard or defer tree coupling.

### Prompt Patches

- agent: Engine Integration Agent
  change: Whenever despawn or teardown is gated on `AnimationPlayer` completion signals, require a documented branch: if the target animation name is missing from the player, perform the same collision/targeting teardown and schedule `queue_free()` immediately—never wait for a signal that cannot fire.
  reason: Prevents stuck half-dead entities when clips or exports are incomplete.

- agent: GDScript Reviewer Agent
  change: Flag `_ready()` implementations that call `get_tree()` (or other tree APIs) without `is_inside_tree()` when the class appears in unit tests or may be instanced off-tree.
  reason: Matches headless test patterns and avoids error-level noise masking real failures.

- agent: Test Breaker Agent
  change: For adversarial tests that simulate concurrent or repeated completion signals, prefer closure capture over `Array`, `Dictionary`, or small `RefCounted` helpers when mutating counters across emissions; document if primitives are insufficient for the engine version.
  reason: Reduces flaky or false-green concurrent-signal tests in headless Godot.

### Workflow Improvements

- issue: Animation-completion ACs sometimes stay API-agnostic in spec while tests mandate a specific binding.
  improvement: After spec freeze, add a single “Bound API” line (signal name + disconnect/cleanup rules) for animation-driven lifecycles.
  expected_benefit: Faster implementation alignment and fewer review iterations on “which signal?”

### Keep / Reinforce

- practice: GDScript review escalated missing-clip teardown to CRITICAL and blocked shipping a collision-disabled zombie state.
  reason: Lifecycle bugs that strand invisible collider-off actors are high player-visible impact; severity matches.

- practice: Splitting coverage into scene/EAC tests, infection/handler tests, and a dedicated adversarial file mapped cleanly to DAP clusters and CHECKPOINTS index.
  reason: Makes AC traceability and gatekeeper validation straightforward.

---

## [wire_animations_to_generated_scenes] — Root AnimationPlayer wired from GLB; Godot lifecycle and `run_tests.sh` import hang

*INTEGRATION (manual AC pending): 2026-04-03*

### Learnings

- category: testing
  insight: After `add_child`, Godot runs `_ready()` deferred; assertions that read script state immediately after `add_child` see pre-`_ready()` values unless the test calls `_ready()` once or awaits a frame.
  impact: WAGS tests initially failed on `_ready_ok` / `animation_player` despite correct scene structure; resolution required aligning test timing with engine semantics.
  prevention: For “controller wired at load” tests, either await `process_frame` (async runner) or call `_ready()` explicitly after tree insertion when the suite is synchronous.
  severity: medium

- category: architecture
  insight: In GDScript 2 on Godot 4.6.x, comparing `what == NOTIFICATION_ENTER_TREE` inside `_notification` can fail even when the engine sends `what == 24`; use an explicit numeric constant (or verify the enum resolves) when enter-tree side effects must run.
  impact: AnimationPlayer resolution never ran; all WAGS controller checks failed until equality used literal `24`.
  prevention: When depending on `Object` notification IDs in `_notification`, log or unit-check the constant once per engine version or use documented `Object.NOTIFICATION_*` only after confirming it matches runtime.
  severity: high

- category: infra
  insight: `godot --import` without a timeout can block CI and local scripts indefinitely; wrapping it preserves the “reimport before tests” intent without hanging the pipeline.
  impact: `ci/scripts/run_tests.sh` appeared stuck; AC “run_tests.sh exits 0” was not reliably testable.
  prevention: Always bound import and test invocations with `timeout` (and prefer `--headless` for CI) per project CLAUDE guidance.
  severity: medium

### Anti-Patterns

- description: Treating `NOTIFICATION_ENTER_TREE` and unqualified `NOTIFICATION_ENTER_TREE` as identical in GDScript without verifying the numeric value.
  detection_signal: `_notification` body never runs the expected branch; headless logs show `what=24` but no side effects.
  prevention: Use a class-level `const _NOTIF_ENTER_TREE := 24` (with engine-version comment) or assert equality once in a tiny diagnostic script.

### Prompt Patches

- agent: Test Designer Agent
  change: For any test that `add_child`s a PackedScene root and reads `_ready()`-initialized state, document whether the suite is sync or async; if sync, require an explicit `_ready()` call or a documented one-frame pump after add_child.
  reason: Avoid false failures from deferred ready semantics.

### Workflow Improvements

- issue: Tickets mix “in-editor visual” ACs with headless-only automation; Gatekeeper correctly blocks COMPLETE without human evidence, leaving the ticket in INTEGRATION with an easy-to-miss next step.
  improvement: Add a one-line “Manual QA” subsection template on tickets that require editor verification, with checkbox and date field for the human signer-off.
  expected_benefit: Clear closure path and fewer stalled INTEGRATION tickets.

### Keep / Reinforce (closure)

- practice: After human confirms the editor AC, AC Gatekeeper immediately promoted ticket to `COMPLETE`, recorded sign-off in `Validation Status`, and `git mv` to `done/` — no extra spec churn.
  reason: Closes the loop the gatekeeper opened at INTEGRATION without leaving orphan “pending manual” state.

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

## [procedural_room_chaining] — Spec API churn and ticket description drift caused full test suite invalidation mid-cycle
*Completed: 2026-03-25*

### Learnings

- category: process
  insight: A ticket description that references an artifact (the "fusion room") that does not exist in the project forces a planning pivot that propagates a corrected scope to every downstream agent. The correction is cheap individually but compounds if it reaches the Spec Agent before validation.
  impact: The Planner had to file a checkpoint, annotate the ticket description, and document the corrected sequence. Any downstream agent that had not read the checkpoint would spec or test against the wrong sequence.
  prevention: Before the Planner writes an execution plan, require an explicit "dependency artifact check": verify that every scene, script, or asset named in the ticket description exists at the stated path. Treat any missing artifact as a spec gap that must be resolved in the planning document before execution begins.
  severity: high

- category: process
  insight: A mid-cycle API redesign (Spec Rev2 replacing Rev1) that changes function signature and return type voids every previously planned test ID. All PRC-SEQ-*, PRC-DEDUP-*, PRC-SCHEMA-*, PRC-POOL-* IDs from Rev1 were superseded, requiring the Test Designer to start from a clean test map.
  impact: This caused a full re-spec and re-test-design cycle. The root cause was that Rev1 was written against the ticket's prose schema ("generate(seed)") without validating consistency against the broader architecture spec that defined the authoritative API.
  prevention: The Spec Agent must resolve the authoritative API signature in the first revision pass, cross-checking the ticket's Required Input Schema against any referenced system spec documents. If a conflict exists between prose and schema, file a checkpoint and resolve before publishing Rev1. A second revision cycle is a workflow smell that indicates insufficient upfront API arbitration.
  severity: high

- category: testing
  insight: Randomized deduplication tests on small pools (e.g. exactly 2 items drawn from a 2-item combat pool) have an irreducible false-certainty problem: the no-repeat property is structurally guaranteed by pool exhaustion, not by the algorithm. A naive implementation would also pass.
  impact: PRC-GEN-3 ("no duplicate paths") passes even with a broken Fisher-Yates implementation because there are only 2 combat items. PRC-ADV-3 was added to test with a synthetic 4-item pool where a naive randi_range implementation would produce repeats, providing the only real coverage of the deduplication algorithm.
  prevention: When the production pool size equals the draw count for any category, the Test Designer must add a synthetic-pool adversarial test that uses a larger pool (e.g. 4 items, draw 2) to ensure the deduplication algorithm is independently verified. Document this as a mandatory companion test whenever pool_size == draw_count.
  severity: medium

- category: testing
  insight: Headless GDScript test runners cannot capture stdout, so any AC that requires observing console output (e.g. "RNG seed printed to console") cannot be verified by automated tests and must fall back to code inspection as its sole evidence basis.
  impact: PRC AC "RNG seed printed to console" was evidenced only by code review of the unconditional `print()` call. If the print is ever moved behind a conditional or removed, all existing tests continue to pass and the AC silently regresses with no detection.
  prevention: For any AC that requires observable console output, either: (a) add a testable side effect (e.g. expose a `last_seed` property on the class so tests can assert the value without stdout), or (b) explicitly label the AC as "code-inspection-only" in the ticket validation status and document the exact file and line number that satisfies it. Option (a) is preferred and should be spec'd as an explicit property on pure-logic classes.
  severity: medium

- category: architecture
  insight: When two coordinating systems (DeathRestartCoordinator and RunSceneAssembler) each own independent instances of the same state machine (RunStateManager), the two lifecycles are silently decoupled. A restart signal from DRC does not propagate to RSA; the room chain does not rebuild on run restart.
  impact: Integration between DRC restart and RSA room rebuild was explicitly deferred to a future ticket. This means the "restart" flow is architecturally incomplete — the room chain only assembles on first load, not on each run. The deferral was a reasonable short-term decision but creates a gap that is invisible to automated tests.
  prevention: When a spec makes a "defer integration to future ticket" decision that leaves a partial behavior (e.g. "room chain does not rebuild on restart"), the Spec Agent must add a concrete follow-up ticket reference or a failing test stub that documents the missing behavior. Deferral decisions without a test stub are invisible debt.
  severity: medium

### Anti-Patterns

- description: Ticket prose names a specific artifact (scene, resource, node name) that does not exist in the project at planning time. This causes a scope correction that must be manually propagated to every subsequent agent in the chain.
  detection_signal: Any artifact path or scene name in the ticket description that cannot be resolved by a glob or file check at planning time.
  prevention: Planner Agent must glob-check every artifact named in the ticket description before writing the execution plan. Unresolved artifacts must be flagged as blocking gaps — not silently worked around.

- description: An API spec revision that changes the function signature and return type mid-cycle, without a mechanism to invalidate or version-lock downstream test plans that referenced the old API.
  detection_signal: A checkpoint entry saying "Spec RevN supersedes RevM; all prior test IDs are voided."
  prevention: The Spec Agent must resolve the canonical API in Rev1 by explicitly cross-referencing the ticket schema, any referenced architecture documents, and existing implementations. Rev2 rewrites are a signal that Rev1 was published too early.

- description: Using a provisional (unverified) seed pair in a deterministic-output test when the pool is small enough that the seeds may collide, without a verification step at any stage of the pipeline.
  detection_signal: A test comment noting that the seed pair has "~50% false-failure risk" or "provisional — must be verified at implementation."
  prevention: The Spec Agent must mark provisional seed pairs with a blocking TODO for the Implementation Agent or Test Breaker Agent to verify. If the agent cannot pre-compute the seed collision at spec time (red phase), the CHECKPOINTS.md must record the seed pair as unconfirmed with an explicit resolution gate.

### Prompt Patches

- agent: Planner Agent
  change: Before writing the execution plan, run a dependency artifact check: for every scene path, script path, and named resource in the ticket description, confirm the file exists at the stated location. If any artifact is missing, add a "missing artifact" section to the planning document that names the gap, blocks execution of dependent tasks, and proposes a resolution (add artifact, remove reference, or create follow-up ticket). Do not proceed to execution planning until all missing artifacts are resolved or explicitly scoped out.
  reason: The "fusion room" gap required a mid-cycle correction that propagated to spec, test, and checkpoint. An upfront artifact check at planning time eliminates this class of scope drift entirely.

- agent: Spec Agent
  change: When writing the first spec revision for a system ticket, resolve the authoritative function signature before publishing. Cross-check: (1) the ticket's Required Input Schema, (2) any referenced architecture or design documents, (3) any existing callers in the codebase. If two sources conflict, file a checkpoint with the conflict and resolution before publishing the spec. Do not publish a spec with an unresolved API conflict — a second revision that changes the signature and voids all prior test IDs is a workflow failure, not a refinement.
  reason: The PRC Rev1 → Rev2 API change voided all test IDs and required a full re-spec. The conflict between the ticket prose API and the Required Input Schema should have been resolved before Rev1 was published.

- agent: Spec Agent
  change: When a spec decision defers integration between two systems to a future ticket (e.g. "RSA does not rebuild on DRC restart — deferred"), add a failing test stub to the test suite that documents the missing behavior. Name the stub "TODO_[description]" and mark it with `pending()` or equivalent. This stub is not a test to be implemented now — it is executable documentation of the integration gap.
  reason: Deferral decisions without a test stub are invisible architectural debt. The PRC deferral of DRC-RSA restart integration left the behavior gap undocumented and undetectable by the test suite.

### Workflow Improvements

- issue: The INTEGRATION-class AC "Transitions between rooms feel seamless (no visible load pop)" was not accompanied by a Manual QA Checklist at spec time. This is the fourth consecutive ticket where this gap occurred. The prompt patches from [containment_hall_01_layout], [fusion_opportunity_room], and [light_skill_check] have not been applied to the Spec Agent's active prompt.
  improvement: The "Manual QA Checklist" prompt patch identified in [fusion_opportunity_room] learnings must be applied to the Spec Agent's prompt as a standing rule. The instruction must be: "For any AC that requires human observation (visual, audio, runtime behavior), emit a numbered Manual QA Checklist section with atomic steps in the format: open [scene] → trigger [action] → observe [exact expected output]. The checklist must appear in the spec document, not only in the ticket's Next Action block."
  expected_benefit: This has recurred on every ticket with a visual AC. A prompt-level rule is the only fix — individual learning entries have not stopped the recurrence.

- issue: The seed pair for PRC-SEED-2 was declared provisional at spec time, acknowledged as unverifiable in red phase, and passed through test design with a comment noting the risk. No agent in the chain was assigned ownership of resolving the provisional status before the test was finalized.
  improvement: When a spec creates a provisional assumption (seed pair, threshold value, path string) that requires verification at a later phase, the CHECKPOINTS.md entry must include an explicit "resolution owner" field naming the agent responsible for confirming or correcting the assumption. The Implementation Agent or Static QA Agent must check all open provisional assumptions before signing off.
  expected_benefit: Prevents provisional values from being silently locked in by the time the implementation is complete, where changing them requires a test suite update and a new checkpoint.

### Keep / Reinforce

- practice: Separating RoomChainGenerator (pure RefCounted, no SceneTree) from RunSceneAssembler (Node, SceneTree caller) allowed the entire generation logic to be tested headlessly with 34 tests, zero SceneTree dependencies, and high confidence in the algorithm's correctness.
  reason: This architectural split is a strong pattern for any system where a pure-logic computation must be combined with Godot scene graph operations. The pure layer is testable; the integration layer is audited by code review and manual playtest. Reinforce this pattern for all future systems that combine data generation with scene assembly.

- practice: The Fisher-Yates shuffle with a seeded RandomNumberGenerator, constructed fresh per call, guarantees cross-instance determinism without shared state. This was explicitly called out in the implementation notes and verified by the adversarial seed tests.
  reason: Shared RNG state across instances is a common source of non-determinism in procedural generation. The per-call construction pattern prevents this class of bug and should be the default for any new seeded random system in the project.

---

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

## [soft_death_and_restart] — 21 SDR-* tests passing; ticket at INTEGRATION pending scene wiring and human visual verification.

*Completed (headless phase): 2026-03-21*

### Learnings

- category: testing
  insight: In Godot 4.6.1 headless mode, `global_position` getter and setter are unreliable on CharacterBody3D nodes even when the node is added to a Node3D scene tree via `add_child()`. The property appears to read/write a stale or zero transform. `position` is fully reliable in the same context when the parent node has an identity transform (position == global_position when parent = identity).
  impact: SDR-CORE-6 (`reset_position()` asserts player position equals spawn position) required a fallback from `global_position` to `position`. If undetected, the test would have passed vacuously (global_position always returning Vector3.ZERO, matching a zero spawn point), masking a real implementation defect.
  prevention: In headless tests that verify node position after a reset, always use `position` when the parent's transform is identity. Never use `global_position` in headless test assertions for CharacterBody3D or similar physics nodes. Document this in a comment in the test file.
  severity: high

- category: testing
  insight: GDScript 4.6.1 lambda capture semantics for primitive types (`bool`, `int`, `float`) prevent lambdas from updating outer local variables. A lambda like `func(): fired = true` captures the value of `fired` at creation time — it does not hold a reference to the outer variable. The outer variable is never mutated.
  impact: Pre-existing RSM-SIGNAL-* tests in `test_run_state_manager.gd` use this pattern to assert signal emission by checking a `fired` bool after `await`. All 7 RSM-SIGNAL-* tests fail for this reason — not because RunStateManager is broken. These failures were misread as regressions when first encountered during the SDR ticket, causing diagnostic effort before the root cause was confirmed as a known GDScript limitation.
  prevention: Never use `func(): local_bool = true` to test signal emission in GDScript 4. Use a counter on an Object (`class Counter extends RefCounted: var n = 0`) or connect to a method on a RefCounted that mutates an array/dict (reference types are captured by reference). Document this constraint in the Test Design Agent prompt.
  severity: high

- category: testing
  insight: Calling `.free()` on a RefCounted object generates a "Can't free a RefCounted object" runtime error in Godot. In `test_run_state_manager.gd`, `rsm.free()` was called in teardown despite RunStateManager extending RefCounted. The error fires after test assertions and therefore does not flip any test from pass to fail, but it pollutes output and delays diagnosis of real failures.
  impact: Noise in test output caused confusion during SDR ticket integration phase when 7 pre-existing failures appeared alongside this error. The error had appeared in prior runs but was not cleaned up, compounding across tickets.
  prevention: Static QA Agent must flag any `.free()` call in test files where the freed object's class extends RefCounted (not Object). This pattern was already documented in [fusion_opportunity_room] learnings but the existing test file was not corrected. Add a one-time cleanup task for `test_run_state_manager.gd` teardown.
  severity: medium

- category: architecture
  insight: RSM's internal MutationSlotManager and the scene InfectionInteractionHandler's MutationSlotManager are separate object instances with independent state. A reset that calls `rsm.apply_event("restart")` only clears RSM's internal slot manager; the handler's slots remain dirty until explicitly cleared via `handler_node.get_mutation_slot_manager().clear_all()`.
  impact: This caused a spec-phase escalation. If the coordinator had only cleared the RSM internal instance, mutation UI would have appeared empty to the logic layer but visually populated to the player after restart. The Spec Agent caught and resolved this before any test was written.
  prevention: When a feature creates multiple instances of the same service class (e.g. slot manager) with no shared reference, document all instance boundaries explicitly in the spec's Architecture section. Any "reset" or "clear" operation must enumerate which instances it touches — not just the one accessible through the primary coordinator path.
  severity: medium

- category: process
  insight: Ticket revision numbers reaching 6+ with INTEGRATION-blocking issues remaining at scene-wiring (Engine Integration Agent not yet invoked) indicate a workflow sequencing gap. The headless phase completed correctly but the ticket has no mechanism to automatically hand off to the Engine Integration Agent; it waits in INTEGRATION status with a documented "Next Responsible Agent" that must be invoked externally.
  impact: SDR ticket is structurally complete at headless scope but not progressing. Human visual verification cannot begin until scene wiring is done, and scene wiring cannot begin until the Engine Integration Agent is invoked. Each waiting step adds latency with no automated trigger.
  prevention: When a ticket's NEXT ACTION names a specific agent, the Acceptance Criteria Gatekeeper should explicitly tag the ticket for that agent's queue rather than leaving it in a generic INTEGRATION status. The project board should distinguish "INTEGRATION — waiting for Engine Integration Agent" from "INTEGRATION — waiting for human."
  severity: low

### Anti-Patterns

- description: Using `global_position` in headless CharacterBody3D tests to assert reset behavior. The property is unreliable in headless mode even with a valid scene tree parent.
  detection_signal: A test for a position-reset method asserts `node.global_position == expected_vector` on a CharacterBody3D that was added to a Node3D root, but the assertion always passes even with the reset logic commented out.
  prevention: Replace `global_position` with `position` in headless position assertions when the parent has an identity transform. Add a comment citing Godot 4.6.1 headless compatibility as the reason.

- description: Lambda-based signal detection (`func(): fired = true`) for bool variables in GDScript 4.6.1. The lambda captures the primitive value, not a reference to the outer variable. Signal emissions are silently missed.
  detection_signal: A test asserts `assert(fired == true)` after `await some_signal` but the assertion fails intermittently or always, even though the signal is confirmed to be emitted by other means.
  prevention: Use a reference-type counter (RefCounted with a field, or an Array with one element) for signal detection in lambdas. Never use a bare bool/int local variable as the capture target.

### Prompt Patches

- agent: Test Design Agent
  change: "In headless tests that assert node position after a reset, use `node.position` instead of `node.global_position` for CharacterBody3D nodes. `global_position` getter and setter are unreliable in Godot 4.6.1 headless mode even when the node is added to a Node3D parent. This equivalence holds when the parent has an identity transform. Add a comment: # global_position unreliable in headless (Godot 4.6.1); use position when parent = identity."
  reason: SDR-CORE-6 required this fallback at test-write time. Without this rule, position tests pass vacuously in headless mode, masking real implementation defects.

- agent: Test Design Agent
  change: "Never use a `bool`, `int`, or `float` local variable as the capture target in a GDScript lambda to detect signal emission. GDScript 4.6.1 lambdas capture primitive types by value, not by reference. The outer variable is never mutated. Use instead: `var counter = [0]` (array) and `func(): counter[0] += 1` inside the lambda, then assert `counter[0] == expected_count`."
  reason: RSM-SIGNAL-* failures in test_run_state_manager.gd are all caused by this exact pattern. 7 tests are permanently broken because of it. The fix is a one-line pattern change.

- agent: Static QA Agent
  change: "When reviewing test files, flag any `.free()` call where the target object's class (or its ancestor) extends RefCounted. RefCounted objects must not be manually freed. Add a Static QA check: grep test files for `.free()` and verify the freed object's class hierarchy. Report any RefCounted `.free()` call as a defect even if it does not flip test pass/fail."
  reason: RefCounted `.free()` errors are non-fatal but generate persistent noise in test output that obscures real failures. The error has appeared across multiple tickets without being cleaned up.

### Workflow Improvements

- issue: The ticket reached INTEGRATION state with headless coverage complete, but no automated mechanism exists to invoke the Engine Integration Agent. The "Next Responsible Agent" field in the ticket is documentation only — it does not trigger any action.
  improvement: When a ticket transitions to INTEGRATION with a named Next Responsible Agent, the project board workflow should create an explicit task entry or flag in the agent queue for that agent. The distinction between "waiting for Engine Integration Agent" and "waiting for human" should be reflected in the ticket's Stage field (e.g. INTEGRATION:engine-wiring vs INTEGRATION:human-verification).
  expected_benefit: Prevents tickets from sitting in INTEGRATION indefinitely with completed headless coverage. Reduces latency between headless completion and scene wiring.

- issue: Pre-existing test failures (RSM-SIGNAL-*) in sibling test files were encountered during the SDR integration run and required diagnostic effort to confirm they were pre-existing and unrelated, not regressions introduced by SDR changes.
  improvement: The test runner output should include a comparison against a known-failing baseline list. Pre-existing failures should be annotated as such in the run report so the Integration Agent does not need to re-diagnose them on each ticket. The known-failing list should be maintained in a file (e.g. `tests/known_failures.txt`) with a brief note per entry.
  expected_benefit: Eliminates recurring diagnostic effort for the same pre-existing failures. Keeps Integration Agent focus on net-new failures only.

### Keep / Reinforce

- practice: The coordinator node uses a `_dead` flag guard on the death detection path to prevent double-fire when `_on_player_died()` is called from both the polling path and an external caller during the same frame.
  reason: Without the guard, two rapid HP=0 frames could trigger two restart cycles, resulting in corrupted state. The double-fire guard was explicitly tested (SDR-CORE-8 / ADV-SDR-01) and passed. This pattern should be reused in any state transition coordinator that detects conditions via polling.

- practice: The ticket explicitly staged the visual (tween/dissolve) work as Part 2 after the core logic was verified headlessly, and the integration test plan enumerated exactly which ACs are headless-testable vs human-only. This clean separation prevented wasted effort automating unautomatable criteria.
  reason: Consistent with the pattern established in [fusion_opportunity_room] and [light_skill_check]. The separation is working and should be enforced as a default for all tickets with mixed headless/visual ACs.

---

## [room_template_system] — 5 room .tscn files authored; all primary RTS-* tests pass; RTS-ADV-16 revealed a test design defect in recursive node-name counting.

*Completed (headless phase): 2026-03-21*

### Learnings

- category: testing
  insight: Recursive scene-tree searches for a node-name substring (e.g. `find_nodes("*Enemy*")`) false-positive when instanced sub-scenes contain child nodes whose names also match the substring. In this ticket, `enemy_infection_3d.tscn` has a child named `EnemyVisual`; a recursive count of "Enemy" in the room tree returned 2 instead of the expected 1 per combat/boss room.
  impact: RTS-ADV-16 failed for all 4 rooms that contain enemies. The rooms were correctly authored per spec; the defect was entirely in the test. This was not caught by the Test Designer Agent because the internal structure of the enemy sub-scene was not examined before writing the count assertion.
  prevention: When writing node-count assertions for instanced sub-scenes, restrict the search to direct children of the query root (e.g. iterate `root.get_child(i)` and check name, rather than using `find_nodes` or recursive `get_all_children`). Before finalizing a count assertion, inspect the target sub-scene to identify any child nodes whose names would match the search pattern.
  severity: high

- category: testing
  insight: The RTS-ADV-6 collision_mask check was correctly scoped to direct StaticBody3D children of the room root (not a full recursive walk) because the enemy sub-scene has its own StaticBody3D nodes with a different collision_mask contract. The spec's risk note explicitly governed over the general "every StaticBody3D in the tree" language in the acceptance criteria.
  impact: If the full recursive walk had been used, every room with an enemy would have generated a false failure on RTS-ADV-6 because the enemy's collision layers differ from the floor's. The correct direct-child scoping was used and all RTS-ADV-6 assertions passed.
  prevention: Any spec that mixes room-geometry nodes with instanced enemy sub-scenes must explicitly state whether structural assertions (collision_mask, node type, count) apply to the full tree or only to direct children. The risk note takes precedence; the Test Design Agent must read spec risk notes before writing structural count or property assertions.
  severity: medium

- category: architecture
  insight: Instanced sub-scenes introduce invisible child nodes into the parent scene's runtime tree. Node names, collision properties, and script attachments from the sub-scene's interior are present at runtime even though they are not authored as direct children of the parent. Test assertions that assume a flat tree silently include these inherited nodes.
  impact: Across this ticket and prior ones, the sub-scene interior has caused false failures in count assertions, collision assertions, and name-substring checks. The pattern recurs whenever a new sub-scene type is introduced.
  prevention: When authoring tests for any scene that instances a sub-scene, first enumerate the sub-scene's complete node tree and identify all nodes whose properties (name, type, script, collision_mask) could satisfy a search condition intended only for the parent scene's own nodes. Explicitly scope all assertions to the correct tree depth.
  severity: high

- category: process
  insight: The Test Designer Agent used `FileAccess.open` + text substring search on the .tscn source file to verify enemy scene path (RTS-ENC). This is the only headless-safe method since no runtime API exposes an instanced node's source .tscn path. The approach was explicitly recommended by the spec and worked correctly.
  impact: RTS-ENC-2 through RTS-ENC-5 all passed in green phase. The file-text approach is deterministic and does not require physics ticks or scene tree wiring.
  prevention: Document this pattern as the canonical approach for verifying instanced sub-scene identity in headless tests. Do not attempt to infer scene path from runtime node properties (class name, script methods) — these are indirect and can be shared across scene variants.
  severity: low

### Anti-Patterns

- description: Using `find_nodes("*Substring*")` or any recursive name-search to count expected nodes when the target nodes are instances of a sub-scene that has children with overlapping name patterns.
  detection_signal: A count assertion for N expected instances of a node type returns N*K where K > 1 — the extra counts come from children inside the sub-scene's interior. The rooms are correctly authored but the test fails.
  prevention: Replace `find_nodes` with a direct-child iteration (`for i in root.get_child_count(): var c = root.get_child(i)`) and apply the name/type filter only at depth 1. Add a comment explaining the scope restriction and which sub-scene prompted it.

- description: Writing structural property assertions (collision_mask, node type, count) for scenes with instanced sub-scenes without first auditing the sub-scene's internal node tree.
  detection_signal: A test passes in isolation when the sub-scene is absent but fails after the sub-scene is instanced into the parent. The test failure message shows unexpected extra nodes or unexpected property values that were not authored in the parent scene.
  prevention: Before finalizing any structural test for a scene that instances sub-scenes, open each sub-scene and list all nodes at all depths. Tag which assertions need depth scoping. This step takes under 2 minutes and prevents rework.

### Prompt Patches

- agent: Test Design Agent
  change: "Before writing any `find_nodes`, recursive tree walk, or node-count assertion for a scene that instances sub-scenes, read each sub-scene file and list its complete node tree. If any child node's name, type, or property would satisfy the search condition, restrict the assertion to direct children only using `root.get_child(i)` iteration instead of `find_nodes`. Add a comment explaining the depth restriction and citing the sub-scene that prompted it."
  reason: RTS-ADV-16 failed for 4 rooms because the Test Designer Agent did not inspect `enemy_infection_3d.tscn` before writing the recursive "Enemy" substring count. The rooms were correctly authored; only the test was wrong. This added a blocker that required escalation to the Acceptance Criteria Gatekeeper.

- agent: Test Design Agent
  change: "To verify that a room scene instances a specific sub-scene (e.g. an enemy), use `FileAccess.open(room_path, FileAccess.READ).get_as_text()` and check for the sub-scene filename as a substring. Do not attempt to infer sub-scene identity from runtime node class names, script methods, or exported properties — these are indirect and non-deterministic. Call this pattern 'file-text scene-path verification'."
  reason: There is no runtime API in Godot 4 that returns an instanced node's source .tscn path. The file-text approach is the only headless-safe, deterministic method confirmed to work in this project.

- agent: Spec Agent
  change: "For every structural assertion in a spec (count, property, collision_mask), explicitly state the tree depth scope: 'direct children of room root only' or 'full recursive tree'. When the assertion targets parent-scene nodes that could be confused with sub-scene interior nodes, mandate direct-child-only scope in the test requirement and add a risk note naming the sub-scene and its conflicting child node names."
  reason: RTS-ADV-6 was correctly scoped because the spec's risk note explicitly governed; RTS-ADV-16 was not because the spec lacked an explicit depth scope for the enemy count. Explicit scoping in the spec prevents the Test Design Agent from defaulting to recursive search.

### Workflow Improvements

- issue: The Test Designer Agent wrote RTS-ADV-16 with a recursive count assertion without auditing the enemy sub-scene structure. This was only discovered after Engine Integration authored all 5 rooms and ran the full test suite — late in the pipeline.
  improvement: Add a mandatory pre-write step to the Test Design Agent workflow: for each test involving an instanced sub-scene, read the sub-scene file and enumerate its node tree before writing the assertion. This should be documented as a checklist item in the Test Design Agent prompt, not left to judgment.
  expected_benefit: Catches the recursive-count false-positive pattern before any implementation work begins. Eliminates a class of test design defects that only surface at green-phase validation.

- issue: RTS-ADV-16's test design defect required escalation to the Acceptance Criteria Gatekeeper Agent to resolve. Neither the Test Designer nor the Engine Integration Agent had authority to fix the test (Engine Integration must not modify existing files; Test Designer had already handed off). This created an unnecessary escalation step for a simple fix.
  improvement: Define a "test defect fix" authority rule: if a test assertion is demonstrably wrong (not an implementation issue), the Acceptance Criteria Gatekeeper Agent is authorized to fix the test directly without a full re-run of the Test Design Agent. Document this authority in the Acceptance Criteria Gatekeeper Agent prompt.
  expected_benefit: Reduces escalation latency. A one-line fix to a broken assertion should not require re-invoking the full Test Design Agent pipeline.

### Keep / Reinforce

- practice: Using `FileAccess.open` + text substring search on the .tscn source file to verify enemy scene path in headless tests (RTS-ENC). No runtime API equivalent exists; this is the only deterministic method.
  reason: RTS-ENC-2 through RTS-ENC-5 passed cleanly. The pattern is reusable for any ticket that needs to verify which sub-scene is instanced inside a room or level .tscn file without running physics.

- practice: Scoping collision_mask assertions to direct children of the room root only, not the full recursive tree, when the room contains instanced enemy sub-scenes with their own collision layer contract.
  reason: RTS-ADV-6 passed for all 5 rooms because of this correct scoping. Had the recursive walk been used, every room with an enemy would have generated a false failure. Direct-child scoping is the safe default for any room-geometry structural assertion.

---

## [BPG] — Read existing infrastructure before planning; reviewer catches copy-paste geometry bugs; AC Gatekeeper requires filesystem access
*Completed: 2026-03-24*

### Learnings

- category: process
  insight: Autopilot ran three full pipeline stages (Planner, Spec, Test Designer) on blender_parts_library before discovering the pipeline already existed in asset_generation/python. The root cause was that the Planner Agent did not read the existing directory structure before generating a plan. READMEs and existing source trees are the ground truth for "what already exists" — not the ticket description.
  impact: Stale spec and test artifacts were generated and then deleted. Three agent stages of work were wasted. The ticket had to be rewritten entirely.
  prevention: The Planner Agent must read the project's relevant directory tree and any README before authoring a plan for a ticket that involves adding to an existing system. If a README exists, it must be read first.
  severity: high

- category: testing
  insight: The Code Reviewer caught 9 critical geometry bugs (copy-paste errors, wrong primitive parameters) in AnimatedClawCrawler and AnimatedCarapaceHusk. These bugs would have silently produced wrong GLB outputs because Blender does not error on malformed geometry — it simply renders incorrectly. The pure-Python test suite could not catch them because tests were isolated from bpy and only verified structural registration, not rendered output.
  impact: If the reviewer stage had been skipped, 6 of 9 GLBs would have had incorrect geometry shipped to the game pipeline with no automated signal of failure.
  prevention: For code that generates binary assets (GLBs, blend files, images), the reviewer stage is mandatory even when all pure-Python tests pass. Test isolation from the rendering backend (bpy stubs) creates a coverage gap for geometry-correctness — reviewer inspection is the only in-pipeline safeguard before generation.
  severity: high

- category: infra
  insight: The AC Gatekeeper Agent issued a false BLOCKED verdict because it ran in a sandboxed context where it could not see GLB files that were confirmed on disk. The Gatekeeper was checking for file existence as part of AC verification, but its filesystem access was restricted. This produced a false negative that required orchestrator override.
  impact: A false BLOCKED created an unnecessary override step and undermined confidence in the Gatekeeper's verdict. If the override mechanism did not exist, the ticket would have stalled.
  prevention: The AC Gatekeeper must not issue a BLOCKED verdict based solely on file-not-found results when its filesystem access is sandboxed or restricted. It should log the access limitation as a CHECKPOINT and request human confirmation for filesystem-dependent ACs, rather than treating a failed file lookup as an AC failure.
  severity: high

- category: process
  insight: The blender_parts_library ticket described work that had already been done differently. The ticket backlog was based on an outdated picture of the codebase — the pipeline had been built independently of the ticket system. No agent checked whether the ticket's described deliverables already existed before starting pipeline execution.
  impact: Wasted three agent stages, required a ticket rewrite, and produced artifacts that had to be cleaned up. Discovery only happened when the Orchestrator intervened mid-run.
  prevention: Add a mandatory "existence check" step at the start of any implementation run: before the Planner Agent runs, verify that the primary deliverable files listed in the ticket's "Files to Modify / Create" section do not already exist with conflicting content. If they do, flag for human review before proceeding.
  severity: critical

### Anti-Patterns

- description: Planning and speccing a system that already exists. The pipeline proceeded through three stages generating plans and tests for blender_parts_library without any agent confirming whether the described pipeline was already present in the codebase.
  detection_signal: Ticket describes creating files that already exist in the codebase at the named paths, OR ticket describes functionality that is already exercised by existing tests.
  prevention: Planner Agent must run a targeted file existence check on all "Files to Create" entries before authoring any plan. If a named file already exists, halt and log a CHECKPOINT before proceeding.

- description: Using bpy stubs in pure-Python tests creates a false sense of test coverage for geometry-producing code. All structural tests pass even when the underlying Blender calls contain copy-paste bugs that produce visually wrong output.
  detection_signal: Test suite achieves full pass rate against bpy-mocked classes, but no test exercises actual rendered geometry dimensions or primitive parameter values.
  prevention: For each new enemy class or Blender geometry generator, require at least one source-inspection test (via inspect.getsource) that asserts the specific primitive type and scale parameters expected — not just that the method exists.

- description: AC Gatekeeper treating a file-not-found lookup failure as an AC failure when running in a restricted/sandboxed environment. The absence of a file in the Gatekeeper's view does not mean the file is absent on disk.
  detection_signal: AC Gatekeeper issues BLOCKED for a filesystem-existence AC, but there is no corroborating evidence (e.g., no build error, no generation error logged) that the file was not produced.
  prevention: AC Gatekeeper should cross-reference filesystem AC failures against the implementation agent's own logged evidence. A BLOCKED verdict for a file-existence AC requires at least one corroborating source beyond the Gatekeeper's own lookup.

### Prompt Patches

- agent: Planner Agent
  change: "Before authoring any plan for a ticket that adds to an existing system, read the project's relevant directory tree and any README file in that directory. If the README or existing source files describe functionality that overlaps with the ticket's deliverables, log a CHECKPOINT before proceeding. Do not generate a plan that assumes the described pipeline does not exist without first verifying."
  reason: The blender_parts_library autopilot ran 3 full stages before discovering the pipeline already existed. A pre-plan existence check would have prevented all wasted work.

- agent: AC Gatekeeper Agent
  change: "When verifying a filesystem-existence AC (e.g., 'file X exists on disk'), do not issue BLOCKED solely based on a failed file lookup. If your environment may be sandboxed or have restricted filesystem access, log the limitation as a CHECKPOINT and request human confirmation. A file-not-found result is only a valid BLOCKED signal if the implementation agent's own output also reported a generation failure."
  reason: The AC Gatekeeper issued a false BLOCKED for GLB file presence because it could not access the filesystem where the files were confirmed to exist. This required orchestrator override and undermined trust in the Gatekeeper verdict.

- agent: Code Reviewer Agent
  change: "For any code that invokes Blender geometry primitives (primitive_sphere_add, primitive_cylinder_add, primitive_cube_add, etc.), inspect each call site for copy-paste errors: verify that parameter values (radius, vertices, scale) are semantically correct for the named body part, not carried over from a similar-looking method in an adjacent class. Flag any call where the parameter values are identical to those in a sibling class that represents a visually distinct enemy part."
  reason: 9 geometry bugs in AnimatedClawCrawler and AnimatedCarapaceHusk were copy-paste errors where primitive parameters were not updated from the source class. The Reviewer catching these before GLB generation was the only in-pipeline safeguard.

### Workflow Improvements

- issue: No pipeline step verified whether the primary deliverables of a ticket already existed before Planner, Spec, and Test Designer ran. The discovery that blender_parts_library was superseded happened only when the Orchestrator intervened mid-run after three wasted stages.
  improvement: Add a pre-flight existence check as step 0 of autopilot execution for any ticket with a "Files to Create" section. The Orchestrator should confirm that the named files do not already exist with conflicting content before handing off to the Planner Agent. If they do, the ticket should be flagged NEEDS_REVIEW before any agent runs.
  expected_benefit: Prevents multiple agent stages of wasted work when the codebase has diverged from the ticket backlog. Saves time and eliminates stale artifact cleanup.

- issue: The AC Gatekeeper cannot reliably verify filesystem-existence ACs when running in a sandboxed context, but it issues definitive verdicts (BLOCKED) regardless. There is no mechanism for the Gatekeeper to signal "I could not verify this AC due to environment limitations."
  improvement: Add a CANNOT_VERIFY verdict state to the AC Gatekeeper's vocabulary. When a filesystem check fails in a context where sandbox restrictions may be present, the Gatekeeper issues CANNOT_VERIFY with a note, rather than BLOCKED. The Orchestrator then routes CANNOT_VERIFY items to human confirmation before deciding to block.
  expected_benefit: Eliminates false BLOCKED verdicts caused by environment restrictions. Keeps the BLOCKED signal meaningful — reserved for cases where the Gatekeeper has positive evidence of failure.

### Keep / Reinforce

- practice: Having the Code Reviewer Agent inspect Blender geometry generator classes before GLB generation runs. In this ticket, 9 critical bugs were caught that pure-Python tests could not detect due to bpy stub isolation.
  reason: Blender geometry code has a silent-failure mode: wrong primitive parameters produce wrong shapes but no error. The reviewer is the only agent in the pipeline that reads the source holistically and can catch copy-paste parameter errors across sibling classes.

- practice: Using inspect.getsource() in pure-Python tests to verify structural properties of bpy-dependent methods without invoking Blender. This is the correct tool for asserting that a method references a particular primitive type or key string when bpy is mocked.
  reason: BPG test suite used this pattern successfully for apply_materials and class registration checks. It provides meaningful structural coverage that complements the bpy-mocked isolation boundary.

---

## [MAINT-TUC] — GDScript 4 static analysis breaks spec-mandated dynamic dispatch; smoke/adversarial infra creates circular-extend trap
*Completed: 2026-03-28*

### Learnings

- category: architecture
  insight: GDScript 4 validates all referenced identifiers at parse time, not at runtime. A base class that references `_pass_count`/`_fail_count` without declaring them fails to load even if every subclass declares those variables. The spec's assumption that "GDScript resolves them via dynamic dispatch at runtime" is incorrect for the current GDScript 4 parser.
  impact: The spec mandated AC-3.1 (no `_pass_count`/`_fail_count` in `test_utils.gd`) and simultaneously required that base class helpers call those variables. The Implementation Agent had to use `get()`/`set()` as a workaround, which itself broke when `Object.set()` on an undeclared property was not retrievable via `Object.get()`. This required a second design pivot — declaring the counters in the base — which directly violated AC-3.1 and forced a spec revision.
  prevention: Before speccing any base class that references variables expected to live in subclasses, verify with a minimal test whether GDScript 4's parser accepts the reference. Do not assume runtime dynamic dispatch applies to identifier resolution at parse time. The safe design is either: (a) declare the variable in the base with a default, or (b) use a virtual getter method pattern (`func _get_pass_count() -> int: return 0`) that subclasses override.
  severity: high

- category: testing
  insight: Smoke and adversarial test files that test the utility file itself cannot extend the utility they are testing. Extending `test_utils.gd` from within `test_utils_smoke.gd` would create a circular dependency that makes the smoke suite responsible for calling `_pass`/`_fail` via the very file it is verifying. These files must `extends Object` and define their own local `_pass`/`_fail` helpers — which means they will appear in the `grep -r "func _pass\b" tests/` output and literally violate the letter of AC-4.1/4.2.
  impact: AC-4.1 and AC-4.2 stated that `func _pass` must appear ONLY in `test_utils.gd`. The smoke/adversarial infrastructure files were a structural exception that made these ACs unverifiable as written. The AC Gatekeeper had to accept this as an "accepted structural exception" rather than a literal pass.
  prevention: When writing ACs for a self-testing utility ticket, anticipate the self-test infrastructure's extends constraint. AC-4.1 should have read: "After migration, no migrated production test file defines `func _pass`. The smoke and adversarial self-test files for `test_utils.gd` itself are exempt as they cannot extend the file they test." The "migrated production test file" scope qualification makes the AC objectively verifiable.
  severity: medium

- category: testing
  insight: GDScript 4 coerces types in Variant equality: `1 == "1"` returns `true`. A test asserting that `_assert_eq(1, "1")` fails (ADV-TU-28) contradicts GDScript's actual behavior. Similarly, IEEE-754 representation of `0.1` means `absf(0.0 - 0.1) <= 0.1` is not reliably true at the boundary — the stored value of `0.1` may be slightly above or below the mathematical value (ADV-TU-32 with the `<=` vs `<` boundary).
  impact: Both ADV-TU-28 and ADV-TU-32 were written based on incorrect assumptions about language and floating-point behavior. They required fixes after the checkpoint logged them as known failures, adding a rework iteration to an otherwise complete implementation pass.
  prevention: For any test that asserts cross-type equality behavior or floating-point boundary conditions, the Test Breaker Agent must verify the assertion against the actual GDScript 4 runtime before publishing the test. The specific rules: (1) `Variant == Variant` coerces ints and strings — never assume an int vs. string comparison fails. (2) For `<=` boundary tests on float literals, use a value that is representable exactly in binary (e.g. `0.5`, `0.25`) rather than a decimal like `0.1` whose IEEE-754 representation introduces rounding uncertainty.
  severity: medium

- category: process
  insight: When a spec is authored before the test files are written, the spec's ACs can be staleness-trapped: the AC text is written against an imagined test that has not been run, making the AC a hypothesis rather than a verifiable contract. ADV-TU-28 and ADV-TU-32 were both hypotheses that turned out to be wrong about the runtime.
  impact: The AC Gatekeeper encountered test failures that were not implementation bugs but were spec/test design errors that should have been caught at the Test Breaker phase. This required a checkpoint entry and explicit documentation that these are "inherent GDScript 4 behavioral properties" rather than bugs.
  prevention: The Test Breaker Agent must run each adversarial test against a known-correct stub implementation before publishing the test suite. A test that is supposed to fail should fail for the right reason. If a test can't be green-verified (e.g., it only makes sense in the red phase), the checkpoint must record its expected failure mechanism and the spec must acknowledge the runtime assumption being tested.
  severity: medium

### Anti-Patterns

- description: Spec asserting counter ownership (no declaration in base) and base-class helpers that reference those counters simultaneously, without verifying that GDScript 4's parser permits undeclared identifier references in base class method bodies.
  detection_signal: A spec AC says "base class MUST NOT declare variable X" and a separate AC says "base class helpers call X." The Implementation Agent files a checkpoint noting the parse failure.
  prevention: These two ACs are contradictory in GDScript 4. The spec must choose: (a) declare X in the base with a default value, or (b) use a virtual method pattern. Mandate the chosen resolution in the spec before implementation begins.

- description: Smoke and adversarial test files for a shared utility are treated as regular migrated test files when checking post-migration grep assertions. The circular-extend constraint forces them to redefine the very functions the production files should have removed.
  detection_signal: Post-migration grep for `func _pass` in `tests/` finds hits in files named `test_*_smoke.gd` or `test_*_adversarial.gd` that are self-testing the utility.
  prevention: Any grep-based AC that enforces function removal must explicitly carve out the self-test infrastructure files. Name the exempt files in the AC text, not in an "accepted structural exception" note added at gatekeeper time.

- description: Adversarial tests that assert GDScript type-coercion behavior without empirical verification of the runtime. Assuming `int != string` in Variant comparison, or assuming a decimal literal boundary behaves as its mathematical value, produces tests that are structurally wrong about the language.
  detection_signal: A test assertion says "this call should fail" for a cross-type comparison (e.g. `_assert_eq(1, "1")` should produce FAIL) but there is no checkpoint confirming this was tested against a running interpreter.
  prevention: Any adversarial test that relies on type system behavior or IEEE-754 edge cases must be empirically verified in a minimal GDScript script before being committed to the test suite.

### Prompt Patches

- agent: Spec Agent
  change: "When designing a base class that provides shared helpers referencing subclass-declared variables, do NOT assume GDScript 4 dynamic dispatch applies at parse time. GDScript 4 validates identifier references at parse time, not at runtime. If a base class method body references a variable (e.g. `_pass_count`) that is only declared in subclasses, the script will fail to load. You must either: (a) declare the variable in the base with a default value and document that subclasses shadow it, or (b) use a virtual accessor method pattern. Do not write ACs that simultaneously prohibit a variable declaration in the base and require that variable to be referenced in base class method bodies."
  reason: The AC-3.1 vs. counter-access contradiction required two checkpoint entries, a `get()`/`set()` workaround that itself failed, and a final design pivot that violated the original AC. A correct spec would have never generated this contradiction.

- agent: Test Breaker Agent
  change: "For any adversarial test that asserts a call should produce a FAIL result based on type mismatch behavior (e.g. int vs. string, float boundary), verify the assertion against a live GDScript 4 interpreter before publishing. Specifically: (1) Do not assume `Variant == Variant` comparisons fail for int vs. string — GDScript 4 coerces them. (2) For floating-point boundary assertions using `<=` or `<`, use only exact binary-representable values (powers of 2 or their fractions) as test inputs. Decimal literals like 0.1 have IEEE-754 representations that make boundary behavior non-deterministic. Record each such verification in CHECKPOINTS.md."
  reason: ADV-TU-28 and ADV-TU-32 were both based on incorrect runtime assumptions. They required a rework iteration that could have been eliminated with a one-minute verification step.

- agent: Spec Agent
  change: "When writing grep-based acceptance criteria that enforce the absence of a function definition (e.g. 'grep for func _pass returns only results from X'), explicitly name every file that is structurally exempt from the rule. Do not rely on an 'accepted structural exception' note added at gatekeeper time. The AC text itself must read: 'After migration, func _pass appears only in test_utils.gd and the following exempt self-test files: [list them].' "
  reason: AC-4.1 and AC-4.2 were technically violated by the smoke/adversarial infrastructure files but declared satisfied via an accepted exception. Had this been written into the AC from the start, the Gatekeeper could have confirmed it objectively rather than issuing a judgment call.

### Workflow Improvements

- issue: The spec's assumption that GDScript 4 permits base-class references to subclass-declared variables was not challenged at any workflow stage before implementation. The Spec Agent published the assumption as a fact; the Test Breaker and Static QA Agents did not verify it; the Implementation Agent discovered the parse failure at implementation time.
  improvement: Add a "GDScript runtime assumptions" verification step to the Static QA Agent's checklist: for any spec that asserts a GDScript language behavior (dynamic dispatch, type coercion, signal capture semantics), require a reference to a concrete checkpoint or prior learnings entry confirming the behavior. If no confirmation exists, the Static QA Agent must file a checkpoint before handing off to the Implementation Agent.
  expected_benefit: Surfaces incorrect language-behavior assumptions before they cause implementation-time rework. Prevents the pattern where a spec's "GDScript will resolve X at runtime" assumption goes unchallenged through three agent stages.

- issue: The post-migration AC verification for "func _pass appears only in test_utils.gd" could not be confirmed by a literal grep because the smoke/adversarial self-test infrastructure files are a structural exception. The Gatekeeper issued a judgment-call pass rather than an objective verification.
  improvement: When a ticket's primary deliverable is a shared utility that must also be self-tested, the Spec Agent must write the self-test infrastructure plan alongside the utility spec — not leave it for the Test Designer to discover. The self-test files' circular-extend constraint is foreseeable at spec time. Specifying it upfront allows the ACs to be written correctly from the start.
  expected_benefit: Eliminates late-stage "accepted structural exception" verdicts. Keeps all AC verifications objective.

### Keep / Reinforce

- practice: The Implementation Agent used `Object.get()`/`Object.set()` as a first attempt to resolve the undeclared-identifier parse error, discovered it did not work for dynamic property creation, filed a detailed checkpoint, and pivoted to declaring the counters in the base. This systematic "attempt → observe → checkpoint → pivot" loop produced a traceable decision history.
  reason: Complex infrastructure tickets with contradictory ACs benefit from explicit checkpoint entries at each design pivot. The checkpoint log for this ticket is a complete audit trail of why the final design differs from the original spec. Future agents working on similar base-class utility infrastructure can read those checkpoints rather than re-discovering the same GDScript 4 constraints.

- practice: Using a `run_all() -> int: return 0` no-op in the shared utility to satisfy the auto-discovery runner without modifying `run_tests.gd`. This required identifying the naming conflict proactively (the CRITICAL Risk note in the execution plan) before any implementation began.
  reason: The runner discovery pattern (`test_*.gd` → call `run_all()`) is a fixed constraint that cannot be changed. Any shared utility file under `tests/` must account for it. Proactive identification and resolution at the planning phase with an explicit no-op is the correct pattern. It should be the standard approach for any future shared infrastructure file placed under `tests/`.

---

## [godot_scene_generator_validation] — Extract pipeline-convention-sensitive logic to testable utilities before integration, not after
*Completed: 2026-03-25*

### Learnings

- category: architecture
  insight: When a naming convention is defined by one pipeline stage (Python asset exporter) and consumed by another (Godot scene generator), the consuming code's parsing assumptions are the most fragile part. Inline private functions are opaque to tests and the first place mismatch hides.
  impact: `_extract_family_name` inside `load_assets.gd` silently produced `"acid_spitter_animated"` instead of `"acid_spitter"` for the entire `_animated_` family of filenames — a naming convention that the Python pipeline introduced but the Godot side was never updated to match. The bug was only discovered when the ticket explicitly required validation against real GLB output.
  prevention: Any function that parses filenames or tokens produced by an upstream pipeline must live in a standalone, headlessly-testable utility class from its first commit. Do not inline parsing logic in @tool or EditorScript classes where it cannot be reached by the test runner.
  severity: high

- category: testing
  insight: `@tool extends EditorScript` classes are structurally untestable in a headless Godot test suite. Any business logic inside them — regardless of how simple — is invisible to automated tests until extracted to a `RefCounted`-based utility.
  impact: Three acceptance criteria (generator runs without errors, .tscn node structure correct, metadata set correctly) were permanently deferred to PENDING_MANUAL because the only entry point is `File > Run` in the Godot editor. There is no headless equivalent.
  prevention: Tickets that involve EditorScript deliverables must explicitly label any AC that depends on editor execution as PENDING_MANUAL from the spec phase, not discovered at gatekeeper time. All logic that can be extracted (parsing, path construction, data mapping) must be extracted, leaving only the editor lifecycle calls inside the EditorScript itself.
  severity: medium

- category: architecture
  insight: Introducing a utility wrapper function (e.g. `_extract_family_name` that only calls `EnemyNameUtils.extract_family_name`) adds a call-site indirection layer with no benefit and creates a code review finding that requires a fix iteration.
  impact: The Code Reviewer flagged the wrapper as unnecessary; the Implementation Agent had to remove it and wire the call site directly. This added a revision pass that would not have existed if the utility had been called directly at the single call site from the start.
  prevention: When refactoring inline logic to an external utility, replace every call site with the direct utility call. Do not preserve a private wrapper function as a "compatibility shim" unless there are multiple call sites that would benefit from a shared local alias.
  severity: low

- category: testing
  insight: The "animated" infix removal algorithm is position-agnostic (removes all segments exactly equal to "animated"), not position-restricted (only removes it when it is the penultimate segment). This is a broader contract than the primary use case suggests, and implementations that use a fixed-offset removal pass the primary suite but fail the adversarial suite.
  impact: Eight adversarial edge cases were required to pin the contract: "animated" as the sole segment, "animated" in prefix position, case-sensitive rejection ("Animated" is not removed), negative trailing integers, and single-segment inputs. Without these, a fixed-offset implementation would have passed all primary tests.
  prevention: For any parsing algorithm, the Test Breaker Agent must enumerate mutation classes: positional assumptions, case sensitivity, boundary segment counts (0, 1, 2), and off-by-one positions. Primary tests cover the happy path; adversarial tests must cover each of these classes explicitly.
  severity: medium

### Anti-Patterns

- description: Pipeline-convention mismatches (where one tool outputs names in format A and a consumer assumes format B) are invisible to unit tests until real pipeline output is used as test fixtures.
  detection_signal: A function parses filenames using a strip/split algorithm but is only tested with manually authored strings that match the expected format, not actual output from the upstream tool.
  prevention: At spec time, examine a representative sample of actual upstream tool output (e.g. the real .glb filenames in `asset_generation/python/animated_exports/`) and include at least one verbatim upstream filename as a primary test case.

- description: Keeping a private wrapper function in the host class after extracting logic to a utility. The wrapper provides no value when there is only one call site and creates a reviewer finding.
  detection_signal: A private function whose entire body is a single delegating call to an external utility function and has exactly one call site in the file.
  prevention: When extracting logic to a utility, inline the utility call directly. Remove the private wrapper in the same commit.

- description: PENDING_MANUAL ACs discovered at gatekeeper time rather than designated at spec time, causing surprise at the end of the ticket workflow.
  detection_signal: An AC that requires editor execution (EditorScript, @tool script, scene generation into the file system) is written as a standard verifiable AC without a PENDING_MANUAL label in the spec's AC table.
  prevention: The Spec Agent must classify each AC by verification method (HEADLESS, MANUAL, SKIPPED_UNTIL) in the AC table. Any AC that depends on `File > Run` in the editor must be labeled MANUAL from the spec phase.

### Prompt Patches

- agent: Spec Agent
  change: "When speccing a ticket that involves a @tool or EditorScript class, classify each acceptance criterion by verification method in the AC table: HEADLESS (runnable in headless test suite), MANUAL (requires running in the Godot editor), or SKIPPED_UNTIL (conditional on prior step). Never write a MANUAL AC without a 'PENDING_MANUAL' label and an explicit escalation note describing who runs it and what to observe."
  reason: Three ACs were discovered to be PENDING_MANUAL only at gatekeeper time. Pre-labeling at spec time prevents surprise deferrals and makes the human's manual verification responsibilities clear from the beginning of the ticket.

- agent: Implementation Agent
  change: "When replacing inline logic with an external utility call, replace every call site with the direct utility invocation. Do not preserve a private wrapper method that solely delegates to the utility. If there is exactly one call site, the wrapper is unnecessary and will be flagged by the Code Reviewer."
  reason: The `_extract_family_name` wrapper finding required an additional review-fix iteration that would not have been needed if the call site had been wired directly to `EnemyNameUtils.extract_family_name`.

- agent: Test Breaker Agent
  change: "For any parsing or string-manipulation function, enumerate these mutation classes before writing adversarial tests: (1) positional assumptions (does the algorithm assume the target segment is at a fixed index?), (2) case sensitivity (does the algorithm handle mixed-case versions of a sentinel string?), (3) boundary segment counts (empty input, single-segment input, two-segment input), (4) sentinel in prefix vs. suffix vs. middle position. Write at least one adversarial test per class unless the spec explicitly excludes the variant."
  reason: The GSV adversarial suite required 8 edge cases to fully pin the `extract_family_name` contract. Without a structured enumeration of mutation classes, it is easy to write adversarial tests that all target the same failure mode while leaving other mutation paths uncovered.

### Workflow Improvements

- issue: The ticket's "Known Issues to Fix" section identified the naming mismatch and the EditorScript testability gap before any agent ran, but these were described as pre-work rather than triggering immediate AC classification (HEADLESS vs MANUAL) at spec time.
  improvement: When a ticket's description includes a "Known Issues" section that mentions @tool, EditorScript, or editor-only workflows, the Spec Agent must classify all dependent ACs as MANUAL at the beginning of spec authoring, before writing any other AC. Do not wait until the AC table is complete to apply classification.
  expected_benefit: Prevents late-stage discovery of PENDING_MANUAL verdicts after three other agents have already run. Surfaces the manual verification scope to the human at the earliest possible point.

- issue: Pre-existing parse warnings in `load_assets.gd` were confirmed out of scope but have no tracking mechanism; future agents will re-confirm the same findings as out-of-scope on subsequent tickets.
  improvement: When an Implementation Agent encounters pre-existing test failures or parse warnings confirmed out of scope, append a one-line entry to `project_board/KNOWN_ISSUES.md` (creating it if absent) noting the file, line range, and nature of the defect.
  expected_benefit: Prevents repeated re-discovery of the same pre-existing issues. Creates a lightweight defect backlog without blocking the current ticket.

### Keep / Reinforce

- practice: Extracting testable pure logic (family name parsing) into a `RefCounted`-based utility class (`EnemyNameUtils`) so it can be covered by the headless test suite, even when the host class (`load_assets.gd`) cannot be instantiated headlessly.
  reason: This is the correct architectural response to @tool and EditorScript testability constraints. The pattern is generalizable: any EditorScript that contains non-trivial logic should delegate to a plain utility class. The 20 primary and 15 adversarial tests that resulted would not have been possible without this extraction.

- practice: The stash/restore baseline comparison method used by the Implementation Agent to confirm that pre-existing test failures (RSM-SIGNAL, ADV-RSM) predated the current changes and were not regressions.
  reason: This is a reliable, deterministic method for distinguishing pre-existing failures from regressions introduced by the current ticket. It produces strong evidence for the gatekeeper without requiring manual bisection. Should be reinforced as standard practice when `run_tests.sh` exits non-zero.

---

## [missing-movement-simulation-path] — preload path mismatch caused by directory restructure without global reference update
*Completed: 2026-03-25*

### Learnings

- category: infra
  insight: A GDScript `preload()` call using an absolute `res://` path silently becomes a parse-time crash when the target file is moved to a subdirectory, because GDScript evaluates `preload()` at parse time — before any frame runs. The error surfaces only when the scene chain that attaches the script is loaded, not when the script file itself is opened or edited.
  impact: The player controller failed to load in `containment_hall_01.tscn` entirely, not with a graceful runtime error. The bad path was present in HEAD while the fix existed only in the working tree, creating a confusing split state where on-disk code appeared correct but runtime behavior matched the committed (broken) version.
  prevention: Whenever a script file is moved to a subdirectory, run a codebase-wide search for the old path across all `.gd`, `.tscn`, and `.tres` files before committing the move. Treat the move commit and the reference-update commit as an atomic pair — never separate them.
  severity: high

- category: testing
  insight: No existing test covered the `preload` path in `player_controller_3d.gd`. The test suite passed green even though the committed file contained a broken import path, because tests that did not instantiate the player controller did not trigger the parse-time failure.
  impact: The bug was only discovered at runtime, not by `run_tests.sh`. A regression test using `load()` plus `source_code` inspection would have caught this in CI before the bad commit was visible to anyone.
  prevention: For every core script that uses `preload()` to depend on another script, add a headless regression test that: (1) loads the script via `load()` with a null-guard, (2) reads `source_code` to assert the correct path string is present, and (3) asserts the wrong path string is absent. This test costs approximately 5 lines and directly prevents this class of bug.
  severity: high

- category: infra
  insight: The `.godot/uid_cache.bin` binary file can carry a stale UID-to-path mapping that causes Godot to resolve the old path even after the preload string in source is corrected. Text grep cannot validate the full binary content; the only reliable remediation is `godot --import` to force a cache rebuild.
  impact: The ticket had to document `godot --import` as a recommended post-fix step rather than a confirmed AC item, because the binary cache state was not provably clean through text inspection alone.
  prevention: After any resource move or path fix, include `godot --import` as a mandatory step in the implementation runbook — not an optional recommendation. Treat a non-rebuilt UID cache as a blocking risk until a successful headless run confirms it.
  severity: medium

### Anti-Patterns

- description: Moving a script file to a new directory without updating all `preload()` and `load()` references atomically in the same commit. The working tree carried the fix but HEAD did not, producing a "works on my machine" state that misled any agent reading file contents directly.
  detection_signal: `git status` shows a core script modified-not-staged, while `run_tests.sh` passes — meaning tests do not exercise the broken committed version.
  prevention: Any file move that changes a `res://` path must be accompanied by a codebase-wide reference update in the same commit. Search for the old path before committing and verify zero remaining references.

- description: The test suite provided false confidence that the codebase was runnable because tests avoided instantiating the component that was broken. Green CI did not mean the game would launch.
  detection_signal: A script central to gameplay (player controller, core system) has no test that performs even a `load()` on it.
  prevention: Every script under `scripts/player/` and `scripts/system/` should have at least one headless smoke test that calls `load()` and asserts non-null. This catches parse-time failures before any integration step.

### Prompt Patches

- agent: Implementation Agent
  change: "Before committing any file move or directory restructure, search all `.gd`, `.tscn`, and `.tres` files for the old path string and confirm zero matches. If any match is found, update all references in the same commit as the move. Never commit a file move and defer reference updates to a follow-up commit."
  reason: This bug was caused by a move that left a stale `preload()` path in a committed file. A single search-before-commit check would have prevented the bad state from entering HEAD.

- agent: Test Breaker Agent
  change: "For any test suite covering a core script (player controller, system coordinator, scene assembler), include at least one test that calls `load(\"res://path/to/script.gd\")`, asserts the result is non-null, and — if `source_code` is non-empty — asserts that every explicit `preload()` path string in the source corresponds to a file that actually exists. This is the minimum viable regression guard against parse-time import errors."
  reason: The missing-movement-simulation-path bug had zero test coverage that would have caught it. A load-and-source-inspect test is the lowest-cost prevention for this entire class of failure.

### Workflow Improvements

- issue: The Spec Agent observed a discrepancy between HEAD and working-tree state: the fix existed on disk but not in git. This is easy to misread — an agent inspecting file contents may conclude the bug is already resolved while the committed version seen by CI is still broken.
  improvement: When `git status` shows a core script as modified-not-staged, the Spec Agent must explicitly identify the committed vs working-tree discrepancy in the diagnosis section and confirm whether the reported error reproduces against HEAD or the working tree. This distinction must appear in the ticket before any other agent proceeds.
  expected_benefit: Prevents an agent from declaring a bug resolved based on working-tree contents while the committed version remains broken in CI and for other developers.

- issue: The workflow enforcement module's stage enum did not include `IMPLEMENTATION_COMPLETE`, but a task instruction directed the Engine Integration Agent to use that exact stage name. This caused a checkpoint deviation that had to be resolved by assumption.
  improvement: The stage enum in the workflow enforcement module must be kept in sync with all stage names used across all agent task instructions. Any new stage label introduced in a task instruction must also be added to the enforcement enum in the same update cycle.
  expected_benefit: Eliminates spurious checkpoint deviations caused by stale enum definitions, reducing noise in CHECKPOINTS.md.

### Keep / Reinforce

- practice: Using `script.source_code` inspection in headless tests to assert both the presence of correct path strings and the absence of incorrect path strings. This pattern is established in `test_soft_death_and_restart.gd` and was correctly applied as the regression mechanism for this bug.
  reason: It is the only headless-safe method to catch parse-time `preload()` path errors without triggering them. The absence assertion is the critical half — it would have made this bug a CI failure before it ever reached HEAD.

- practice: The stash/restore baseline method used by the Implementation Agent to confirm that 7 pre-existing RSM-SIGNAL failures predated the current fix and were not regressions introduced by it.
  reason: Deterministic and low-cost. Produces unambiguous evidence for the gatekeeper without requiring manual bisection. Should remain standard practice whenever `run_tests.sh` exits non-zero after a fix is applied.

---

## [FEAT-20260326-procedural-run-scene] — Recursive sub-scene descent produced an irreconcilable test defect; source-code substring checks must exclude comment lines
*Completed: 2026-03-26*

### Learnings

- category: testing
  insight: A recursive geometry check that descends into packed-sub-scene internals cannot coexist with a spec requirement that a specific sub-scene (e.g. the player) must remain unmodified. The test PRS-GEO-2 asserted zero MeshInstance3D nodes anywhere in the instantiated tree; the player_3d.tscn sub-scene expanded at runtime, exposing its internal SlimeVisual/MeshInstance3D. Satisfying the test required either removing the mesh (violating PRS-NFR-4) or writing the test differently. The scene was correctly authored; only the test was wrong.
  impact: One test was ruled a design defect and marked for future remediation. The Acceptance Criteria Gatekeeper had to adjudicate, consuming an escalation step. This is the third ticket in sequence (RTS-ADV-16, room_template_system, now PRS-GEO-2) to produce a false failure from recursive descent into sub-scene internals.
  prevention: Geometry and node-type absence assertions must never use full recursive tree walks when the scene instances a sub-scene with known internal nodes. Restrict the walk to direct children of root using `for i in root.get_child_count()` — unless the spec explicitly states "recursively including sub-scene internals." This is a pattern reinforcement of the room_template_system learning that was not applied when writing the PRS geometry spec.
  severity: high

- category: testing
  insight: A source-code substring check (`source_code.contains("reload_current_scene")`) is fragile when the implementation file may contain comments that reference the forbidden pattern. ADV-PRS-09 passed only because the implementation comment on run_scene_assembler.gd line 12 deliberately used the paraphrase "scene reload method" instead of the literal forbidden identifier. If the implementation had written "# Does NOT call reload_current_scene" as a natural comment, the test would have failed as a false positive despite correct implementation.
  impact: The spec noted "Already resolved" — the implementation author was aware of the risk and worked around it — but the test itself has no scoping to exclude comment lines. A future developer adding a clarifying comment using the literal method name would silently break a passing test with no implementation change.
  prevention: When using `source_code.contains(forbidden_string)` as an absence assertion, strip comment lines (lines that begin with `#` after whitespace trimming) before applying the check. Alternatively, assert on the call-site pattern specifically (e.g., `get_tree().reload_current_scene(` rather than bare `reload_current_scene`) to reduce false-positive surface area. The test must include a comment explaining this risk.
  severity: medium

- category: process
  insight: A CRITICAL-flagged GDScript code review finding (NodePath export using Godot 3 style in death_restart_coordinator.gd) was correctly deferred as out of scope because the script was authored under a prior ticket. However, the deferral left no downstream task or backlog entry. Future reviewers encountering the same flag must re-derive the "out of scope / prior ticket" ruling from CHECKPOINTS.md, which is not a task queue.
  impact: The NodePath export style issue remained unresolved across at least two tickets with no ownership. Each checkpoint recorded the same finding and the same resolution without advancing toward remediation.
  prevention: Any time a CRITICAL finding is deferred, a backlog entry or labeled CHECKPOINTS section must name the specific file, the required change, and which ticket or milestone should own it. A CRITICAL finding that generates no downstream work item is not properly triaged.
  severity: low

- category: testing
  insight: Two runtime ACs (seed log line on scene run; 5-room child count after _ready()) are inherently unautomatable headlessly because they depend on SceneTree entry and physics initialization. Strong code-inspection proxy evidence was accepted in lieu of automation, but no documented standard governs what constitutes an acceptable proxy. Each gatekeeper must re-derive sufficiency from ticket prose.
  impact: The gatekeeper accepted the proxies and escalated both items to the human. The outcome was correct, but the reasoning had to be reconstructed per-ticket rather than derived from a standard.
  prevention: When a spec is authored, any AC that requires SceneTree entry should be tagged `[INTG-ONLY]` and the spec must list the specific code evidence that constitutes a headless proxy (e.g., "unconditional print() call at code line X is sufficient code-inspection proxy for the log AC"). This eliminates per-ticket gatekeeper adjudication for a predictable class of cases.
  severity: low

### Anti-Patterns

- description: Writing geometry-absence assertions using full recursive subtree walks when the scene instances a packed sub-scene with known internal mesh nodes. The test becomes irreconcilable with a spec requirement that the sub-scene must not be modified.
  detection_signal: A geometry-absence test fails after the scene is correctly authored, and passing the test would require modifying a sub-scene that a separate NFR explicitly forbids modifying.
  prevention: Scope all geometry-absence assertions to direct children of the stated root node. Never use `find_nodes` or unconstrained recursive iteration for geometry checks. This failure pattern has now occurred three times across three tickets.

- description: Using `source_code.contains(forbidden_identifier)` to enforce a "no call to X" requirement without stripping comment lines first. A natural documentation comment that uses the literal forbidden identifier will produce a false failure with no code change.
  detection_signal: An absence assertion passes, but only because the implementation author paraphrased the forbidden identifier in comments. A reviewer adding a clarifying comment with the literal name breaks the test.
  prevention: Strip comment lines from source_code before applying contains() absence checks, or use the full call-site pattern (e.g., `some_object.forbidden_method(`) instead of the bare identifier to reduce comment-line collision risk.

- description: Deferred CRITICAL code-review findings recorded only in CHECKPOINTS.md with no downstream task or backlog entry. Each subsequent ticket must rediscover the finding and re-derive the same "out of scope" ruling.
  detection_signal: The same CRITICAL flag appears across multiple ticket CHECKPOINTS entries with identical "out of scope for this ticket" resolution and no reference to an open backlog item or a ticket that owns the fix.
  prevention: Every deferred CRITICAL finding must generate a named backlog entry or a labeled CHECKPOINTS note with a specific file, required change, and suggested owning ticket. The checkpoint entry alone is not sufficient.

### Prompt Patches

- agent: Test Design Agent
  change: "When writing any geometry-type absence assertion (no MeshInstance3D, no StaticBody3D, no CSGBox3D, etc.) for a scene that instances one or more packed sub-scenes, restrict the check to direct children of the stated root node using `root.get_child(i)` iteration. Do not use `find_nodes` or any recursive walk for geometry-absence assertions. Add a comment: '# Depth-limited to direct children only — packed-sub-scene internals are excluded.' If the spec text says 'anywhere in the subtree', flag this as a potential spec defect before writing the test and confirm with the spec author."
  reason: PRS-GEO-2 and RTS-ADV-16 both produced irreconcilable false failures because recursive geometry walks descended into packed-sub-scene internals. The scenes were correctly authored in both cases; only the tests were wrong. This pattern has now occurred three times.

- agent: Test Design Agent
  change: "When writing a source_code absence assertion (e.g., `not source_code.contains('some_identifier')`), strip comment lines from source_code before applying the check. Use: `var stripped = \"\\n\".join(source_code.split(\"\\n\").filter(func(l): return not l.strip_edges().begins_with(\"#\")))`. Then assert `not stripped.contains(forbidden_identifier)`. Add a comment: '# Comment lines stripped before check to prevent false positives from documentation references to the forbidden identifier.'"
  reason: ADV-PRS-09 passed only because the implementation author avoided writing the literal forbidden identifier in comments. A documentation edit using the literal name would produce a false failure with no implementation change.

- agent: Static QA Agent
  change: "When a CRITICAL finding is deferred as out of scope for the current ticket, you must append a labeled entry to CHECKPOINTS.md: 'DEFERRED CRITICAL — File: <path>, Finding: <one-line description>, Suggested owner: <ticket-id or milestone>'. This entry is required output. A CRITICAL finding that generates no downstream work item is not properly triaged."
  reason: The NodePath export CRITICAL flag was correctly deferred but left no trace in any task queue. Future agents encountering the same finding must re-derive a ruling that has already been made, wasting time and producing duplicate checkpoint entries.

### Workflow Improvements

- issue: The spec for PRS-GEO-2 wrote "anywhere in the subtree" for the geometry-absence requirement without noting that the player packed-scene instantiated as a direct child of root would expose internal mesh nodes to a recursive walk. The spec defect was only discovered at Engine Integration phase after full scene authoring.
  improvement: The Spec Agent must, before finalizing any absence assertion with recursive scope, enumerate the direct children of the target root node and identify which are packed-scene instances. For each packed-scene instance, the spec must state whether its internal nodes are in scope. If a packed-scene instance must remain unmodified per an NFR, the assertion scope must explicitly exclude it.
  expected_benefit: Catches the recursive-descent spec defect at authoring time, before any test is written or scene implemented. Prevents the escalation cycle that occurred here and in room_template_system.

- issue: INTEGRATION-class ACs requiring SceneTree entry have no standard proxy-evidence format. Each ticket requires the gatekeeper to adjudicate whether code-inspection evidence is sufficient for sign-off, producing per-ticket reasoning that is not reusable.
  improvement: The Spec Agent must tag any AC requiring SceneTree entry as `[INTG-ONLY]` and list the specific code evidence that constitutes an acceptable headless proxy (e.g., "unconditional print() at line X confirmed by code inspection"). The gatekeeper can then apply the proxy standard without re-deriving it from ticket prose.
  expected_benefit: Reduces ticket revision count and gatekeeper adjudication time for a predictable and recurring class of integration-only ACs.

### Keep / Reinforce

- practice: The Acceptance Criteria Gatekeeper's ruling on PRS-GEO-2 named both the root cause (spec over-specified "anywhere in the subtree") and the exact remediation (restrict walk to direct children or explicitly exclude packed-sub-scene-internal nodes). The ruling cited both the failing test and the conflicting NFR.
  reason: A gatekeeper ruling that identifies root cause and remediation prevents the same defect from being regenerated in a future ticket. This format is the correct standard for all defect rulings.

- practice: The ticket's Escalation Notes section explicitly surfaced omissions from the original input schema (SpawnPosition NodePath, infection_handler export) rather than silently absorbing them as assumptions. Each was stated with the required action.
  reason: Surfacing input-schema omissions explicitly in escalation notes prevents them from becoming silent implementation defects. Future agents reading the ticket can confirm that out-of-spec wiring decisions were intentional and traceable.

---

## [AP-CONTINUE-2026-03-27] — 7 tickets correctly held at INTEGRATION; zero false completions; playtest-result-capture path is missing from the workflow
*Completed: 2026-03-27*

### Learnings

- category: process
  insight: All 7 in-progress tickets (5 M4 + 2 M6) are structurally complete — automated test suites pass, scene wiring is done, and the AC Gatekeeper correctly identified the sole remaining blocker on each as a human-only visual or runtime observation. The AC Gatekeeper's hold behavior is correct and should be treated as expected steady state for tickets with subjective ACs.
  impact: Zero false completions occurred. The Gatekeeper's conservative stance prevents premature COMPLETE advancement. However, the pipeline has no affordance for a human to record evidence inline — the tickets contain a Manual QA Checklist section and a documented task, but there is no standard handoff mechanism that routes the human to those instructions or captures their response back into the ticket file.
  prevention: The workflow needs an explicit "human verification handoff" mechanism: a short summary document or notification that lists all INTEGRATION-blocked tickets, their scene to open, and the exact numbered checklist steps. Without this, playtest evidence accumulates nowhere and tickets remain at INTEGRATION indefinitely despite correct automated coverage.
  severity: high

- category: process
  insight: The "Manual QA Checklist" prompt patch for the Spec Agent has been documented in learnings entries for [containment_hall_01_layout], [fusion_opportunity_room], [light_skill_check], [procedural_room_chaining], and [FEAT-20260326-procedural-run-scene] — five consecutive mentions — and the checklists are now appearing in tickets (mini_boss_encounter, soft_death_and_restart, procedural_room_chaining all have explicit numbered playtest task blocks). However, none of these tickets have been completed because the human has not performed and recorded the playtests. The spec-side fix is working; the human-response side is the remaining gap.
  impact: Playtest checklists exist and are well-formed. The blocker is not spec quality — it is that playtest results have no path back into the ticket. The workflow has no actor responsible for consuming the checklist and writing evidence into Validation Status.
  prevention: Distinguish the two distinct sub-problems: (a) checklist creation at spec time — now solved; (b) evidence capture after playtest — still unsolved. Future workflow improvements should focus exclusively on (b).
  severity: high

- category: process
  insight: When an ap-continue run processes multiple tickets and all are held at INTEGRATION by the same class of blocker (human visual verification), the run produces zero new code and zero ticket state transitions. From a pipeline efficiency perspective, an ap-continue run in this state is a no-op — it confirms the correct hold state but advances nothing. This is not a failure; it is a structural signal that the pipeline is waiting for an out-of-band human input.
  impact: Autopilot runtime was consumed confirming already-correct state across 7 tickets. No rework occurred. The AC Gatekeeper behaved correctly on all 7. If this pattern recurs, the Orchestrator should recognize "all in-progress tickets at INTEGRATION with visual-only remaining blocker" as a condition to short-circuit the run and surface the playtest queue directly to the human rather than cycling through each ticket.
  prevention: When the Orchestrator begins an ap-continue run and finds that all in-progress tickets have Stage: INTEGRATION and all blocking issues are labeled "human playtest required," it should emit a single "Playtest Queue" summary rather than re-running the AC Gatekeeper per ticket.
  severity: medium

- category: process
  insight: The persistent 7 RSM-SIGNAL-* pre-existing test failures appear in every run log across multiple tickets (SDR, MMSP, PRS, PRC). Each integration agent spends time confirming they are pre-existing using the stash/restore method. The `known_failures.txt` improvement (identified in [soft_death_and_restart] learnings) was never implemented. Every subsequent agent rediscovers and re-confirms the same failures.
  impact: Compounding diagnostic overhead. The stash/restore confirmation method is fast, but the effort is entirely duplicated across each ticket's Integration Agent. Across 7 recent tickets, this diagnostic has been performed 7+ times for the identical failures.
  prevention: Create `tests/known_failures.txt` with the 7 RSM-SIGNAL-* test names and a one-line explanation. This file should be checked before declaring any test failure a regression. This improvement was identified in [soft_death_and_restart] and has not been actioned.
  severity: medium

### Anti-Patterns

- description: Logging a workflow improvement about creating `tests/known_failures.txt` across multiple learning entries without it ever being created. Logged once in [soft_death_and_restart] and still absent as of this run — it became a recurring anti-pattern where the insight is re-derived rather than actioned.
  detection_signal: A learning entry's "prevention" step refers to creating a specific file, but that file does not exist after two or more ticket cycles have passed since the entry was written.
  prevention: When an improvement requires creating a new project-level file, the Learning Agent must note it as an open directive for the next agent that touches the relevant directory, not only log it in LEARNINGS.md.

- description: An autopilot run that confirms correct hold state across all tickets but has no short-circuit path — each ticket is processed fully even when the outcome is deterministic (all are INTEGRATION, all have human-only remaining blockers).
  detection_signal: All in-progress tickets have Stage: INTEGRATION and all Blocking Issues contain the phrase "human" or "playtest required" at the start of the run.
  prevention: The Orchestrator should check the Stage and Blocking Issues fields of all in-progress tickets at the start of an ap-continue run. If all are INTEGRATION with human-only blockers, emit the playtest queue and halt rather than cycling each through the AC Gatekeeper.

### Prompt Patches

- agent: AC Gatekeeper Agent
  change: "At the start of any ap-continue run, before processing individual tickets, check the Stage and Blocking Issues of every in-progress ticket. If all tickets have Stage: INTEGRATION and all Blocking Issues contain only human-observation requirements (visual, runtime, playtest), emit a 'Playtest Queue' block listing: ticket name, scene to open, and the exact numbered checklist steps from each ticket's Manual QA task. Then halt without cycling through each ticket's gatekeeper logic individually."
  reason: The 2026-03-27 ap-continue run consumed runtime confirming correct hold state on 7 tickets with zero state transitions possible. Short-circuiting this case reduces cycle time and surfaces the actionable items (playtests) directly to the human.

- agent: Planner Agent
  change: "When creating or reviewing a ticket that will reach INTEGRATION with human-only remaining ACs, append the ticket name and its playtest task to `project_board/PLAYTEST_QUEUE.md` (create the file if absent). Each entry must include: ticket name, scene path, and the numbered Manual QA Checklist steps. This file is the human's input queue for in-editor verification."
  reason: Playtest checklists now exist in individual tickets but there is no consolidated view. The human must open each ticket to find what needs verification. A dedicated queue file surfaces all pending playtests at a glance.

- agent: Spec Agent
  change: "When authoring the Manual QA Checklist section for an INTEGRATION-class AC, append a 'Playtest Result Recording' subsection with these four verbatim steps: (1) Update the relevant Validation Status row from 'NOT EVIDENCED' to 'PASS — [your initials] [date]'; (2) Clear the Blocking Issues section; (3) Set Stage to COMPLETE; (4) Run `git mv project_board/<milestone>/in_progress/<ticket>.md project_board/<milestone>/done/<ticket>.md`."
  reason: All 7 INTEGRATION-held tickets have well-formed checklists but no instructions for how the human records evidence back into the ticket file. Without the result-recording steps, the human has no clear path to close the ticket after a successful playtest.

### Workflow Improvements

- issue: After a human performs a playtest, there is no documented mechanism for recording the result and closing the ticket. All 7 INTEGRATION tickets have playtest task blocks but none have result-recording steps. This is the structural gap that prevents closure.
  improvement: Every ticket that enters INTEGRATION with a human-only blocking AC must include a "Playtest Result Recording" subsection in its Manual QA task block (see Spec Agent prompt patch above). The subsection must appear in the ticket before it transitions to INTEGRATION — not as an afterthought.
  expected_benefit: Converts playtest completion from an open-ended task into a deterministic 4-step procedure. Eliminates the ambiguity about what the human does after verifying the playtest.

- issue: The `tests/known_failures.txt` file improvement has appeared in LEARNINGS.md since the [soft_death_and_restart] entry and has not been created. Improvements requiring a new artifact do not self-execute; they need an explicit owner.
  improvement: The next agent that processes `tests/` files (Test Design Agent, Engine Integration Agent, or Static QA Agent) should treat the creation of `tests/known_failures.txt` as a mandatory pre-step, listing at minimum: RSM-SIGNAL-1 through RSM-SIGNAL-6 and ADV-RSM-02, each with a one-line note identifying the root cause (lambda primitive capture in GDScript 4.6.1) and the ticket where it was diagnosed ([soft_death_and_restart]).
  expected_benefit: Ends the recurring stash/restore diagnostic for known-broken tests. Reduces noise that obscures real regressions.

### Keep / Reinforce

- practice: The AC Gatekeeper held all 7 tickets at INTEGRATION without advancing any prematurely, even across multiple ap-continue runs. All blocking issues were accurately identified as human-observation-only.
  reason: This is the correct behavior. The Gatekeeper's conservative stance is working. The remaining gap is human-side evidence capture, not gatekeeper logic. Reinforce this hold behavior as the correct default for all tickets where any AC requires runtime visual confirmation.

- practice: Every blocked ticket has a well-formed Manual QA Checklist with numbered steps specifying the exact scene path, trigger action, and expected observable outcome. The spec-side fix for the recurring "checklist missing" anti-pattern is working.
  reason: Tickets now contain executable verification procedures. The problem is no longer checklist quality — it is that the human has no consolidated entry point to discover and act on the queue, and no instructions for recording results. The spec practice is sound; the workflow gap is the aggregation and result-capture layer.

---

## [FEAT-MUTATION-COLOR] — StandardMaterial3D sub-resource sharing, per-frame material write guard, and is_instance_valid() for RefCounted references

*Completed: 2026-03-28*

### Learnings

- category: architecture
  insight: A `StandardMaterial3D` declared as a sub-resource (`[sub_resource ...]`) in a `.tscn` file is a shared singleton across all instances of that scene. Mutating `albedo_color` directly on `mesh.material_override` at runtime without first calling `.duplicate()` corrupts the shared definition, affects every instance simultaneously, and can dirty the `.tscn` on disk when Godot auto-serializes scene state.
  impact: If duplication had been omitted, a second player instance or a run-restart would inherit whatever `albedo_color` was set at mutation time rather than the baseline. The spec caught this in MAC-2 before any implementation occurred.
  prevention: Any script that writes to a material property at runtime must call `material_override.duplicate()` in `_ready()` before the first write. A dedicated `_material: StandardMaterial3D` member variable should hold the duplicated reference so it is never re-fetched from the mesh hierarchy.
  severity: high

- category: performance
  insight: Accessing `mesh.material_override.albedo_color` as a property chain per `_process()` frame traverses two property lookups and one cast per tick. Caching the duplicated `StandardMaterial3D` in a typed `_material: StandardMaterial3D` member variable reduces this to a single direct field write, which is measurably faster at high frame rates and consistent with the project's convention for cached node references.
  impact: The implementation introduced a fifth member variable (`_material`) not listed in the spec's MAC-7 inventory. This created a spec inventory discrepancy noted by the AC Gatekeeper, but the variable was architecturally required by the MAC-8 performance constraint. The spec's member inventory was incomplete relative to its own performance requirement.
  prevention: When a spec mandates that `_process()` must not perform per-frame property traversal (MAC-8), the spec's member variable inventory (MAC-7) must also include the cached material reference. Performance constraints and member variable tables must be co-authored and cross-checked before publication.
  severity: medium

- category: architecture
  insight: A `_current_tinted: bool` cache that gates material writes so `_process()` only writes on state transitions — not on every frame — is the correct pattern for any `_process()` hook that drives visual state from a polling query. Without it, the material property is re-assigned every frame regardless of whether the state changed, producing unnecessary GPU state changes and GDScript property overhead.
  impact: The `_current_tinted` cache was explicitly required by MAC-6 and correctly applied. No rework was needed here. The lesson is to recognize this as a generalizable pattern for any poll-driven visual state driver.
  prevention: Any `_process()` that reads a binary query (`any_filled()`, `is_active()`, etc.) and drives a visual property should cache the last-known boolean result and gate writes behind an inequality check. The pattern is: `if should_state == _current_state: return` before any property write.
  severity: low

- category: architecture
  insight: `is_instance_valid()` is the correct guard for `Object` references that may have been freed externally, while `!= null` is only reliable for objects the caller knows to still be alive. For `RefCounted` objects, `is_instance_valid()` is technically equivalent to `!= null` (RefCounted objects are not freed until all references drop), but using it consistently as the null guard is safer than relying on the caller to remember which class the reference is.
  impact: No bug was caused here — the spec explicitly required `is_instance_valid()` on both `_mesh` and `_mutation_slot_manager`. The learning is about establishing the guard as a consistent default for any externally-owned reference, regardless of whether the concrete type is Node or RefCounted.
  prevention: For any member variable that caches a reference obtained from an external source (parent node, autoload, scene tree query), use `is_instance_valid()` as the null guard in `_process()` regardless of the concrete class. Annotate the comment: `# is_instance_valid covers both null and freed-object cases`.
  severity: low

### Anti-Patterns

- description: Writing to `material_override.albedo_color` at runtime without first calling `.duplicate()` on the material. Because `.tscn` sub-resources are shared, the write affects all scene instances simultaneously and can corrupt the authored scene file on disk via Godot's auto-serialization.
  detection_signal: A `_process()` or `_ready()` that assigns to `mesh.material_override.albedo_color` or `mesh.get_active_material(0).albedo_color` without a `.duplicate()` call visible in the same script's `_ready()`.
  prevention: Add a mandatory `_ready()` guard: resolve `material_override`, call `.duplicate()`, store the result in a typed member. All subsequent writes go through the cached duplicated reference.

- description: A spec's member variable inventory that lists only the variables required for behavioral contracts but omits the performance-optimization variable that its own non-functional requirement necessitates. This produces a spec inventory discrepancy that the AC Gatekeeper must adjudicate as a non-blocking deviation.
  detection_signal: A spec has a "Non-Functional — Performance" section that requires caching a reference (to avoid per-frame traversal) but the member variable table does not include the cache field.
  prevention: The Spec Agent must read every non-functional constraint and derive any member variables that are implicitly required by it, then add them to the member variable table. Behavioral and performance members must both appear in the inventory.

- description: Resolving `get_parent()` or any scene-tree query inside `_process()` to obtain a reference that could have been cached in `_ready()`. This is a per-frame scene-graph walk with no semantic value when the parent-child relationship is stable for the node's lifetime.
  detection_signal: A `_process()` method body contains `get_parent()`, `get_node()`, or `find_child()`.
  prevention: All reference resolution that is stable for the node's lifetime must happen in `_ready()`. A `_process()` method that calls `get_parent()` or `get_node()` is always a defect; flag it in Static QA.

### Prompt Patches

- agent: Spec Agent
  change: "When writing a Non-Functional — Performance requirement that mandates caching a reference (e.g. 'material must not be accessed per frame via property traversal'), immediately update the member variable inventory table to include the cache field. The inventory table and the performance constraints must be co-authored. An inventory that is missing a cache variable required by a performance constraint is a spec defect."
  reason: The MAC-7 member variable inventory listed four variables but omitted `_material: StandardMaterial3D`, which was architecturally required by the MAC-8 performance constraint. The omission produced an AC Gatekeeper discrepancy note for a fifth variable that was entirely foreseeable at spec time.

- agent: Implementation Agent
  change: "Before writing any runtime material property assignment (`albedo_color`, `roughness`, `metallic`, etc.), check whether the material was obtained from a `.tscn` sub-resource (check for `[sub_resource ...]` in the scene file). If it was, call `.duplicate()` on the material in `_ready()` and store the result in a typed `StandardMaterial3D` member variable. Never write to `mesh.material_override.albedo_color` directly — always write to the cached duplicated material reference."
  reason: StandardMaterial3D sub-resources are shared across all scene instances. Direct mutation corrupts the shared definition and can dirty the .tscn on disk. This class of bug is silent — no runtime error fires, and the corruption only becomes visible when a second instance is created or the scene is resaved.

- agent: Static QA Agent
  change: "Flag any `_process()` method body that calls `get_parent()`, `get_node()`, `find_child()`, or any other scene-tree traversal method. These are per-frame scene-graph queries that should be cached in `_ready()`. Report each occurrence as a defect with severity MEDIUM and the recommended fix: cache the result in a typed member variable in `_ready()` and read the member in `_process()`."
  reason: Per-frame node resolution is one of the most common `_process()` performance anti-patterns in Godot. Catching it at Static QA phase prevents it from reaching implementation review.

### Workflow Improvements

- issue: The spec's MAC-7 member variable inventory was published before all non-functional constraints were fully derived. The Performance constraint (MAC-8) implicitly required a fifth member that the inventory did not list. The AC Gatekeeper had to adjudicate this as an "accepted non-blocking discrepancy" rather than verifying an exact inventory.
  improvement: The Spec Agent should perform a final cross-check pass before publishing: for each Non-Functional requirement, enumerate any member variables it implies and verify they appear in the member variable inventory. This check takes approximately one minute and closes the class of inventory incompleteness.
  expected_benefit: Eliminates gatekeeper inventory discrepancy notes that are predictable from the spec's own content. Keeps the gatekeeper's verdict clean.

### Keep / Reinforce

- practice: Resolving all stable references (`_mesh`, `_mutation_slot_manager`) in `_ready()`, caching them in typed member variables, and reading the members in `_process()` without re-resolution. This is the established convention for all `_process()` hot paths in this project.
  reason: Every `_process()` node in the codebase follows this pattern. Consistent application eliminates an entire class of per-frame overhead and keeps `_process()` bodies trivially reviewable — they should contain only guards, comparisons, and property writes, never node queries.

- practice: Using `has_method("get_mutation_slot_manager")` (duck-typing via method presence) rather than `is PlayerController3D` when resolving a reference from a parent node in `_ready()`. This makes the child node compatible with test stubs that are plain `Node` objects and do not extend `PlayerController3D`.
  reason: Strict type checks in child-to-parent reference resolution couple the child to a concrete parent class, making headless tests require a full `PlayerController3D` instantiation. Method-presence checks allow lightweight stubs and preserve testability without any behavioral compromise.

---

## [run_state_manager] — Lambda primitive capture bug produced 7 persistent signal-test failures; AC Gatekeeper accepted implementation via code inspection while tests were broken
*Completed: 2026-03-28*

### Learnings

- category: testing
  insight: GDScript 4.6.1 lambda closures capture primitive types (`bool`, `int`, `float`) by value at creation time. A lambda `func(): fired = true` writes to a copy of `fired`, not the original outer variable. The outer variable is never mutated. All signal-emission tests written with this pattern silently fail regardless of whether the signal actually fires.
  impact: RSM-SIGNAL-1 through RSM-SIGNAL-6 and ADV-RSM-02 were broken from the moment they were written. The failures persisted across 7 subsequent tickets (SDR, MMSP, PRC, PRS, GSV, AP-CONTINUE, scene_state_machine), requiring stash/restore diagnostic effort on every Integration Agent run. The fix — using an Array capture `var flags := [false]` — was made in a human cleanup commit outside the pipeline, not by any agent.
  prevention: Never use a bare `bool`, `int`, or `float` local variable as the mutation target inside a GDScript signal-detection lambda. Always use `var flags := [false]` (single-element Array) and `func(): flags[0] = true`. This rule was documented in [soft_death_and_restart] learnings but not applied when the RSM test suite was written, because the Test Design Agent authored the tests before the rule was logged. Apply this rule at test-write time, before running.
  severity: critical

- category: process
  insight: The AC Gatekeeper accepted the RSM ticket as COMPLETE by verifying the implementation via code inspection ("signal emits at lines 48–49, state updates at lines 49/53/57") rather than by running the automated test suite. The gatekeeper's evidence was correct — the implementation was right — but the 7 failing signal tests were not treated as a blocking condition. The ticket was marked COMPLETE while 7 of its own test IDs were failing.
  impact: A pattern was established where an implementation can be gatekeeper-accepted while its dedicated test suite is broken. The tests' purpose (automated regression detection) was nullified for those 7 cases. Any future regression in signal emission would pass the suite without detection.
  prevention: The AC Gatekeeper must run the test suite against the specific ticket's test files and treat failures in those files as blocking unless explicitly diagnosed as pre-existing (with a stash/restore comparison confirming they predated the ticket's implementation). Code inspection is a supplementary method, not a substitute for a passing test run.
  severity: high

- category: architecture
  insight: The `extends RefCounted` pattern for a pure-logic state machine with parameterless signals produced a completely headless-testable, SceneTree-free implementation. Signal connections, state transitions, and slot manager integration were all verifiable via `load().new()` with zero scene setup.
  impact: All structural and transition tests (RSM-STRUCT, RSM-TRANS, RSM-RESET, RSM-NOOP) passed first run. The architecture imposed no friction on test setup or teardown. This confirms that pure-logic state machines should always extend RefCounted when headless testability is a requirement.
  prevention: No prevention needed — reinforce this as default architecture for state machines in this project.
  severity: low

- category: testing
  insight: Signal emission timing (emit-before-state-change contract) is a subtle but load-bearing invariant that is invisible in transition tests. The implementation correctly emits signals before updating `_state`, but this contract can only be verified by a lambda that captures state at emit time (RSM-SIGNAL-6). If the emit-before-state test is written with the broken lambda pattern, the contract can silently regress with no test detection.
  impact: RSM-SIGNAL-6 was broken along with the other 6 signal tests, meaning the emit-first contract had zero automated coverage for the duration of the failures. A regression that emitted after state change would have been undetectable.
  prevention: The emit-before-state test is the highest-value single signal test for any state machine. It should be treated as a mandatory primary test (not adversarial), and its lambda capture must use the Array pattern to be valid.
  severity: medium

### Anti-Patterns

- description: Writing a signal-detection lambda with a bare primitive capture (`var fired: bool = false; rsm.connect("signal_name", func(): fired = true)`) when the intent is to detect whether the signal fired.
  detection_signal: A signal test with `assert(fired)` after an `apply_event()` call always fails even though the signal is confirmed by code inspection to be emitted.
  prevention: Replace `var fired: bool = false` with `var flags := [false]` and `func(): fired = true` with `func(): flags[0] = true`. This is a one-for-one substitution with no semantic change except correct GDScript 2.0 capture semantics.

- description: Accepting a ticket as COMPLETE when the ticket's own test suite has failing tests, based solely on implementation code inspection as evidence. Tests that fail are not providing coverage; they are silently passing regardless of implementation correctness.
  detection_signal: An AC Gatekeeper verdict that says "AC verified by code inspection at lines X–Y" for an AC that has a corresponding automated test ID that is failing.
  prevention: Failing tests for the current ticket's ACs are a blocking condition. The Gatekeeper must treat any failure in `test_[ticket_name].gd` or `test_[ticket_name]_adversarial.gd` as blocking unless a stash/restore comparison demonstrates the failure predates the ticket. Code inspection supplements; it does not substitute.

### Prompt Patches

- agent: Test Design Agent
  change: When writing any GDScript signal-detection lambda to assert that a signal was emitted, use Array-based capture exclusively. The pattern is: `var flags := [false]` and `func(): flags[0] = true`, then assert `flags[0]`. Never use `var fired: bool = false` with `func(): fired = true`. GDScript 4.6.1 captures `bool`, `int`, and `float` primitives by value in lambdas; mutations inside the lambda do not affect the outer variable. This applies to all signal tests, including emit-before-state-change tests.
  reason: RSM-SIGNAL-1 through RSM-SIGNAL-6 and ADV-RSM-02 were all written with the broken primitive-capture pattern and all failed silently. Seven tests provided zero coverage for 7+ ticket cycles. The Array capture pattern was already documented in [soft_death_and_restart] but was not applied at test-write time for this ticket.

- agent: Acceptance Criteria Gatekeeper Agent
  change: Before issuing a COMPLETE verdict, run the test suite and check specifically for failures in `tests/scripts/system/test_[ticket_id].gd` and `tests/scripts/system/test_[ticket_id]_adversarial.gd` (or the appropriate test path for the ticket). Failures in the ticket's own test files are blocking unless a stash/restore comparison confirms they predate the implementation. Code inspection of the implementation is supplementary evidence only — it does not substitute for a passing test run against the ticket's own suite.
  reason: The RSM gatekeeper accepted the ticket as COMPLETE while RSM-SIGNAL-1..6 and ADV-RSM-02 were failing. The implementation was correct but the tests were broken, eliminating regression detection for all signal behavior. A passing test run is the definitive AC evidence for headlessly-testable criteria.

### Workflow Improvements

- issue: A test design defect (broken lambda primitive capture) that was already documented in [soft_death_and_restart] learnings was not applied when the RSM test suite was authored in a later session. The learning was logged but not injected into the Test Design Agent's active behavior.
  improvement: When a Test Design Agent begins writing signal-emission tests for any new class, it should explicitly check the most recent LEARNINGS.md for GDScript signal-testing rules before writing the first test. The lambda primitive capture rule must be consulted, not rediscovered.
  expected_benefit: Prevents a documented failure pattern from recurring on the next ticket with signal tests. The [soft_death_and_restart] entry was available but not consulted.

- issue: The stale RSM-SIGNAL failures persisted for 7+ tickets and were diagnosed from scratch each time using stash/restore. The `tests/known_failures.txt` improvement has now been logged in three separate learning entries ([soft_death_and_restart], [AP-CONTINUE-2026-03-27], now here) without being created.
  improvement: The RSM-SIGNAL failures are now resolved (fixed in commit 55129da). If any new known failures emerge, `tests/known_failures.txt` should be created immediately with the test name, root cause, and diagnosing ticket. The file's absence is now the correct state (no known failures); it should be created only if a new pre-existing failure is confirmed.
  expected_benefit: Closes the loop on a three-entry recurring improvement suggestion. The underlying problem (RSM-SIGNAL failures) is resolved; the process improvement (known_failures.txt) is only needed if a new pre-existing failure is introduced.

### Keep / Reinforce

- practice: Implementing the state machine as `extends RefCounted` with `_slot_manager` initialized in `_init()` (not `_ready()`), using parameterless signals for all transitions, and placing all logic in `apply_event()` with a match block. No SceneTree API anywhere in the file.
  reason: This produced a file that is loadable headlessly, testable without a SceneTree, and trivially instantiable by consumers with no wiring overhead. The pattern also allowed `DeathRestartCoordinator._ready()` to wire signals without any scene path lookups. Reinforce this as the canonical design for all lifecycle state machines in this project.

- practice: The emit-before-state-change contract (signal fires before `_state` is updated) being verified by RSM-SIGNAL-6 using a lambda that captures `rsm.get_state()` at emit time. This test type is the only headless-safe way to verify ordering between two synchronous side effects.
  reason: Emit-before-state ordering is a contract that consumers depend on (e.g., a signal handler that reads state to branch behavior gets the pre-transition state). This test type should exist for any state machine that has an emit-first guarantee. Once the Array capture pattern is used, this test is reliable and provides real protection.

---

## [scene_state_machine] — Stale BLOCKED ticket, cross-domain handoff noise, and `_init()` vs `_ready()` for headless-tested nodes

*Completed: 2026-03-27*

### Learnings

- category: process
  insight: A ticket can be marked BLOCKED based on a test-failure report that was accurate at the time of writing but stale by the time it is re-read. The implementation was already correct; the block was a snapshot of an earlier incomplete state.
  impact: The autopilot restarted the ticket from BLOCKED, rediscovered the correct implementation, and had to reason through whether the failure report was current before making progress. No code changed — only the ticket state was wrong.
  prevention: When an agent marks a ticket BLOCKED due to test failures, it must record the exact test run hash, timestamp, or commit SHA alongside the failure report. Any agent resuming the ticket must re-run the suite before accepting the prior failure report as current. A stale failure report without a re-run is not valid blocking evidence.
  severity: high

- category: architecture
  insight: When the Core Simulation Agent authors both the pure-logic module and the Node controller/wiring as part of its scope, the Engine Integration Agent finds the handoff artifact already complete and must decide whether to re-verify, re-author, or simply validate. This ambiguity causes unnecessary deliberation and a checkpoint entry.
  impact: The Engine Integration Agent correctly determined the wiring was complete and moved on, but the decision cost a checkpoint and an explicit deliberation pass that would not have been needed with clearer scope boundaries.
  prevention: The ticket handoff between Core Simulation and Engine Integration must explicitly state which artifacts are pre-authored and which require the Engine Integration Agent's attention. A "pre-authored artifacts" list in the ticket's WORKFLOW STATE block eliminates the ambiguity without requiring the receiving agent to re-inspect.
  severity: medium

- category: testing
  insight: Constructing a Node-based controller's owned state in `_ready()` makes the controller untestable headlessly: integration tests that instantiate the node without inserting it into a SceneTree never trigger `_ready()`, and any property initialized there remains null.
  impact: The integration tests called `get_state_machine()` and received null because `_ready()` had not fired. The fix was to move construction to `_init()`, which fires at instantiation time regardless of scene tree membership.
  prevention: For any Node subclass that owns a pure-logic object (RefCounted or Object) that must be accessible in headless tests, initialize that owned object in `_init()`, not `_ready()`. Reserve `_ready()` only for initialization that genuinely requires a live SceneTree (node queries, signal connections to other tree nodes, etc.).
  severity: high

- category: architecture
  insight: When a pure-logic class acts as the sole source of truth for event string constants (e.g. `EVENT_SELECT_*`), those constants belong on that class rather than on the consuming controller, even if the controller is the only current consumer. Splitting string literals across two files creates divergence risk.
  impact: The GDScript review correctly placed `EVENT_SELECT_*` constants on `SceneStateMachine` rather than on the controller. This eliminated the only magic-string duplication risk in the event dispatch path.
  prevention: For any pure-logic class that defines a transition protocol (events, states, or config keys), co-locate all string/enum constants for that protocol on the pure-logic class. Controllers reference constants via class qualifier (`SceneStateMachine.EVENT_SELECT_*`), never via inline literals.
  severity: medium

### Anti-Patterns

- description: Marking a ticket BLOCKED based on a test-failure report without recording a run timestamp or commit reference. A resuming agent accepts the report as current and spends deliberation budget before re-running to discover the block is stale.
  detection_signal: A BLOCKED ticket whose failure report contains no timestamp, commit SHA, or test-run identifier alongside the listed failures.
  prevention: Blocking evidence must be time-stamped. Any agent that resumes a BLOCKED ticket must re-run the test suite as its first action, before reading the prior failure report.

- description: Implementing AC gating behavior (AC-4: "feature systems gated on state") via a method with no consumers. `get_config()` existed and was correct, but nothing called it — meaning the AC was technically present in code but zero-impact at runtime.
  detection_signal: An AC that requires "system X gated on state Y" but no test or code path calls the gating method to make a behavioral decision.
  prevention: For any AC that requires state-dependent gating, the Gatekeeper must verify that at least one consumer of the gating method exists (either a runtime consumer or a headless query helper called by integration tests). A method with no callers does not satisfy a gating AC.

- description: An untyped parameter on a dispatch method (e.g. `apply_event(event_id)` without annotation) that relies solely on a runtime `typeof()` guard for type safety. Static analysis tools flag this and the annotation adds zero runtime cost.
  detection_signal: A GDScript review pass that flags untyped parameters on public dispatch methods.
  prevention: All public method parameters on pure-logic modules must have explicit type annotations (use `Variant` when the type is intentionally polymorphic). Runtime guards are not a substitute for static type annotations.

### Prompt Patches

- agent: Engine Integration Agent
  change: At the start of any handoff, check the ticket's WORKFLOW STATE block for a "Pre-authored artifacts" list. If such a list exists, treat those artifacts as already complete and limit your scope to the items explicitly assigned to Engine Integration. If no such list exists, file a checkpoint naming each artifact you found pre-authored and your basis for accepting or rejecting it, before proceeding.
  reason: The SSM handoff caused deliberation overhead because the scope boundary was implicit. An explicit pre-authored artifact list in the ticket eliminates the re-inspection pass.

- agent: Acceptance Criteria Gatekeeper Agent
  change: For any AC of the form "X is gated on state Y" or "X is enabled/disabled based on Z", verify that at least one consumer of the gating method exists — either a runtime caller in scene code or a headless integration test that calls the query helper and asserts a behavioral outcome. A method that exists but has no callers does not satisfy a gating AC.
  reason: AC-4 on the SSM ticket had `get_config()` implemented but with zero consumers until the Engine Integration Agent added feature-gate query helpers. The gating AC was satisfied in letter (method exists) but not in spirit (nothing used it to make a decision).

- agent: Core Simulation Agent
  change: For any Node subclass that owns a pure-logic object (e.g. a RefCounted state machine, manager, or resolver) that will be accessed in headless integration tests, initialize the owned object in `_init()`, not `_ready()`. Add a comment: "# Constructed in _init() so headless tests that skip scene tree insertion can still access this object."
  reason: The SSM `SceneVariantController` initialized its state machine in `_ready()`, causing null returns in headless tests. Moving construction to `_init()` is a one-line fix with no behavior change in production but eliminates an entire class of headless null-dereference failures.

### Workflow Improvements

- issue: The ticket spent a full deliberation cycle on a stale BLOCKED state before the blocking condition was re-evaluated. No workflow step required re-running the test suite before acting on the block.
  improvement: Add a mandatory first step to the autopilot's BLOCKED ticket restart procedure: "Before reading the prior failure report, re-run the test suite. If the suite passes, update the ticket stage and proceed. Only act on prior failure descriptions if the re-run confirms them."
  expected_benefit: Eliminates the class of false-BLOCKED tickets where a prior agent's incomplete run left a stale failure report. Converts a deliberation cost into a single test-run step.

- issue: The two-agent split (Core Simulation → Engine Integration) produced overlapping scope: Core Simulation authored the controller and wiring that Engine Integration was expected to produce. The handoff had no artifact inventory, so Engine Integration could not distinguish "pre-built by prior agent" from "I missed something."
  improvement: The ticket's WORKFLOW STATE block should include a "Pre-authored artifacts" section populated by each agent before handoff, listing every file it created or modified. The receiving agent reads this section to scope its own work without re-inspecting the full codebase.
  expected_benefit: Reduces per-handoff checkpoint entries from "figure out what was already done" to a direct scope check against an explicit inventory.

### Keep / Reinforce

- practice: The GDScript review pass caught untyped parameters and magic strings before the Gatekeeper evaluated AC coverage. Fixing these before the AC audit prevented the Gatekeeper from seeing a noisy warning list alongside substantive AC gaps.
  reason: Separating static-analysis cleanup from AC coverage evaluation keeps the Gatekeeper's decision clean. Static QA is a prerequisite to Gatekeeper review, not concurrent with it.

- practice: Extending `RefCounted` (not `Node`) for the pure-logic `SceneStateMachine` allowed 15 headless tests with zero SceneTree setup and no teardown risk. The entire state-machine contract was verified without any scene or process context.
  reason: This is the established pattern for pure-logic modules in this project (reinforced in [procedural_room_chaining]). It continues to eliminate the largest category of headless test friction. Every new system that is computation-only should extend RefCounted, not Node.

---

## [first_4_families_in_level] — EditorScript cannot be run headlessly; infection call chain gaps survive static analysis; Variant-to-String coercion caught by GDScript reviewer; position mismatch caused by Engine Integration Agent not reading spec coordinates; AC-5 playability gate is structurally unautomatable

*Completed: 2026-03-30*

### Learnings

- category: architecture
  insight: An `@tool extends EditorScript` script cannot be driven headlessly. The only way to automate its logic is to replicate that logic in a new `extends SceneTree` script with `func _init()` as the entry point. The replication is a permanent maintenance fork — the two files diverge from the moment of creation.
  impact: `load_assets.gd` (EditorScript) had to be partially replicated as `generate_enemy_scenes.gd` (SceneTree). Any future change to the asset-generation algorithm must be applied in both files or the generated output diverges from the editor-driven output.
  prevention: When a ticket depends on an EditorScript as a prior deliverable, the Planner must immediately flag that EditorScript as a PENDING_MANUAL dependency. If automation is required, the Spec Agent must design the replacement as a headless SceneTree script from scratch — not as a modification to the EditorScript — and document the maintenance fork explicitly. This extends the [godot_scene_generator_validation] learning that EditorScript logic should be extracted to RefCounted utilities; the corollary is that the EditorScript shell itself can never be the headless entry point.
  severity: high

- category: architecture
  insight: A per-family mutation drop system (`mutation_drop` export var plus per-instance override in the level scene) can coexist silently with a hardcoded default resolver (`infection_absorb_resolver.gd` using `DEFAULT_MUTATION_ID` unconditionally). The spec's own call chain analysis treated the export var as sufficient evidence that AC-3 was satisfied, but the resolver never read the export var. The two mechanisms existed independently with no wire between them until a second AC Gatekeeper invocation caught it.
  impact: AC-3 ("correct mutation on absorption") was initially marked as satisfied by the Spec Agent and the first AC Gatekeeper invocation. The second Gatekeeper invocation correctly identified that the resolver hardcoded the default and the export var was never consulted. This required a full implementation pass to thread `mutation_drop` through the call chain.
  prevention: When a spec verifies a call chain for correctness, it must trace each link to actual code — not infer that because an export var exists and a resolver exists, they are connected. Any AC that asserts "correct value X is passed to system Y" must name the exact line in each file where the handoff occurs. If no such line can be named, the AC is not satisfied.
  severity: high

- category: architecture
  insight: `Object.get("property_name")` returns `Variant`, not the property's declared type. Assigning that result directly to a typed `String` field causes an implicit coercion that GDScript strict mode treats as a type warning or error. Replacing `.get()` with direct typed property access on a narrowed-type variable both eliminates the coercion and makes the call site statically verifiable.
  impact: The GDScript reviewer caught this after initial tests passed, requiring a fix iteration. The fix also revealed that the field type (`_target_enemy`) could be narrowed from `Node3D` to `EnemyInfection3D`, improving static guarantees across the call chain.
  prevention: When a script reads a property from a dynamically-typed variable via `.get()`, the Code Reviewer Agent must flag it and require either: (a) narrowing the variable type to the concrete class so direct property access is valid, or (b) casting the `.get()` result explicitly with `as TypeName`. Bare `.get()` returning Variant assigned to a typed field is always a Static QA finding.
  severity: medium

- category: testing
  insight: The Engine Integration Agent placed two enemies at positions derived from its own spatial reasoning ("spread positions on X axis") rather than reading the spec's coordinate table. The spec defined `(0,1,4)` and `(0,1,-4)` (Z-axis spread); the implementation chose `(-6,1,0)` and `(6,1,0)` (X-axis spread). The tests encoded the spec's canonical coordinates and failed against the level file.
  impact: A second AC Gatekeeper invocation was required to identify the mismatch. The level positions then had to be corrected in a separate fix pass. The Engine Integration Agent's test run had passed only because the tests were written to the spec — the agent did not cross-check its authored positions against the spec before declaring implementation complete.
  prevention: The Engine Integration Agent must read the spec's position table and quote the exact coordinate values before editing any .tscn. After authoring, it must grep the node's transform origin in the .tscn text and confirm it matches the spec value verbatim before running tests.
  severity: medium

- category: process
  insight: AC-5 ("playable without debug tools") is structurally unverifiable headlessly. All structural proxies passed (no `@tool`, no debug-only nodes, valid enemy positions, no debug prints), but none confirm that the game is actually playable from the player's perspective. This AC class recurs on every ticket involving placed interactive content and will always require a human play session.
  impact: The ticket was held at BLOCKED awaiting human verification after all 54 automated tests passed. The AC Gatekeeper correctly declined to accept structural-only evidence for a playability AC, consistent with prior tickets. The blocking is correct behavior, not a workflow failure.
  prevention: Tickets with an AC containing the word "playable" or requiring subjective runtime experience should have that AC labeled `[MANUAL-ONLY]` at spec time with the exact Manual QA Checklist and the Playtest Result Recording steps. No structural proxy can satisfy a playability AC — this boundary is absolute.
  severity: low

### Anti-Patterns

- description: Verifying a data-flow AC by confirming that both the source (export var) and the sink (resolver) exist, without tracing the actual code path connecting them. Two systems that exist in parallel with no wire between them satisfy "both exist" trivially but fail "correct value flows end-to-end."
  detection_signal: An AC Gatekeeper or Spec Agent describes the call chain in prose but cannot cite a specific line in each intermediate file where the value is read and forwarded.
  prevention: For any AC asserting that a value produced at source A reaches consumer B, the gatekeeper must name the line in A where the value is produced, the function signature through which it is passed, and the line in B where it is consumed. If any link cannot be named, the AC is not satisfied.

- description: The Engine Integration Agent placing scene nodes at positions derived from spatial intuition rather than the spec's coordinate table. "Spread positions" is ambiguous — X-axis and Z-axis spreads are both valid interpretations.
  detection_signal: A position test (asserting a specific spec coordinate) fails against the authored level file even though the implementation agent reported a passing test run.
  prevention: The Engine Integration Agent must read the spec's position table and quote exact coordinate values before editing the .tscn. After editing, it must grep the authored transform origin and confirm it matches the spec before running tests.

- description: A headless `extends SceneTree` script that replicates an `@tool extends EditorScript` without a cross-reference comment in either file documenting the maintenance fork.
  detection_signal: Two files with overlapping generation logic (e.g. `load_assets.gd` and `generate_enemy_scenes.gd`) with no comment indicating they must be kept in sync.
  prevention: When a headless replication of an EditorScript is committed, add a comment at the top of both files: "MAINTENANCE NOTE: This file's generation logic is replicated from [other_file]. Changes to the generation algorithm must be applied to both files."

### Prompt Patches

- agent: Spec Agent
  change: "When verifying an AC that asserts a value flows from source A to consumer B (e.g., 'correct mutation is granted on absorption'), you must name the exact file and line where each intermediate handoff occurs. A prose description of the call chain is insufficient. If any link cannot be named with a file and line reference, mark the AC as NOT SATISFIED and document the missing link explicitly."
  reason: The AC-3 call chain (mutation_drop export var to resolver) was accepted as satisfied in prose by the first Gatekeeper invocation, but the resolver never read the export var. Requiring named line references for each link prevents this class of false positive.

- agent: Engine Integration Agent
  change: "When placing nodes in a level .tscn, read the spec's coordinate table and quote the exact Vector3 position values for each node before editing the file. After authoring the .tscn, search the file text for each node's transform origin and confirm it matches the spec's value verbatim. Do not derive positions from spatial reasoning — always use the spec's explicit coordinates."
  reason: ClawCrawlerEnemy and CarapaceHuskEnemy were placed at X-axis spread positions instead of the spec's Z-axis positions. The tests failed because they encoded the spec's correct coordinates. A pre-edit spec read and post-edit text confirmation would have caught the mismatch before running the test suite.

- agent: Code Reviewer Agent
  change: "Flag any `Object.get('property_name')` call whose return value is assigned to a typed variable without an explicit cast. GDScript strict mode treats implicit Variant-to-typed-field coercion as a warning or error. Require the caller to either: (a) narrow the receiving variable's type to the concrete class that declares the property and use direct field access, or (b) cast the result explicitly (e.g., `as String`). Report bare `.get()` assigned to a typed field as a Static QA defect."
  reason: `_target_enemy.get("mutation_drop")` returning Variant assigned to a String-typed field was caught by the reviewer but required a fix iteration. The fix also enabled narrowing the field type from Node3D to EnemyInfection3D, improving static verifiability across the call chain.

### Workflow Improvements

- issue: The AC Gatekeeper's first invocation accepted AC-3 based on the existence of both the `mutation_drop` export var and the resolver, without tracing the actual call path. The second invocation caught the hardcoded default. Two Gatekeeper invocations were needed because the first did not apply the "name every link" standard.
  improvement: The AC Gatekeeper prompt should require that for any data-flow AC (value produced at A, consumed at B), the verdict block must include a line-by-line call chain in the Evidence Matrix, not a prose summary. If the chain cannot be traced to specific lines, the AC must be marked NOT SATISFIED with a "missing link" note.
  expected_benefit: Eliminates the class of false-positive AC verdicts where a data flow is assumed connected because both endpoints exist. Reduces Gatekeeper invocation count for tickets with integration-heavy ACs.

- issue: The `extends SceneTree` replication of `load_assets.gd` is a permanent maintenance fork with no tracking mechanism. If the generation algorithm changes in `load_assets.gd`, `generate_enemy_scenes.gd` will silently diverge.
  improvement: When a headless replication of an EditorScript is committed, the Planner Agent should append a note to `project_board/KNOWN_ISSUES.md` flagging the maintenance fork, the two files involved, and the condition under which they must be kept in sync.
  expected_benefit: Prevents silent divergence between the editor-driven and headless-driven asset generation paths. Makes the maintenance obligation explicit and discoverable by future agents.

### Keep / Reinforce

- practice: The AC Gatekeeper's second invocation independently re-read the level .tscn and the resolver source code rather than forwarding the prior Gatekeeper's analysis. This re-reading found both the position mismatch and the hardcoded resolver that the first invocation missed.
  reason: Gatekeeper invocations should always re-read primary evidence files rather than deferring to prior verdicts. The second invocation's independent read produced a materially more accurate result. Each Gatekeeper run is an independent audit.

- practice: Threading `mutation_drop` through the call chain using optional/default parameters (`mutation_id: String = ""`) preserved backwards compatibility with all existing call sites. Zero existing tests regressed.
  reason: When adding a new data-flow parameter to an established API, defaulting it to a sentinel value allows all existing callers to be unmodified while new callers pass the real value. This is the correct pattern for threading optional context through a settled call chain without a breaking change.

---

## [M7-ACS] — @export + RefCounted serialization conflict and stale generated scenes caused a full impl-fix iteration
*Completed: 2026-03-31*

### Learnings

- category: architecture
  insight: In Godot 4.6.1, `@export` annotations are enforced at runtime in headless mode. Assigning a plain Object stub to an `@export var field: AnimationPlayer` raises "Invalid assignment" and leaves the property null, silently breaking all tests that depend on stub injection.
  impact: All 39 tests failed silently (controller returned early on null) after the initial implementation used `@export var animation_player: AnimationPlayer`. A full impl-fix iteration was required to remove the `@export` and resolve via `find_child()` + direct assignment bypass.
  prevention: For any Node-type dependency that must be injected by tests (not the editor inspector), declare the var as a plain `var field: Object = null` with no `@export`. Document the rationale in the spec. The Spec Agent must flag this pattern explicitly when the tested node type cannot be subclassed by test stubs.
  severity: high

- category: architecture
  insight: `RefCounted`-derived objects cannot be serialized through an `@export` in `.tscn` files. A `Node`-typed export rejects `RefCounted` assignment at runtime. The only correct injection pattern for a `RefCounted` dependency in a scene-file–instantiated Node is a `setup()` method or a plain `var` with `Object` typing.
  impact: `EnemyStateMachine extends RefCounted` caused the initial `@export var state_machine: EnemyStateMachine` spec to be incorrect. The spec had to be retroactively corrected after implementation discovered the constraint.
  prevention: The Spec Agent must check the inheritance chain of any dependency type before specifying it as `@export`. If the type extends `RefCounted` (not `Node`), the spec must require a `setup()` injection method or plain `var`, never `@export`.
  severity: high

- category: infra
  insight: The scene generator (`generate_enemy_scenes.gd`) was updated to add `EnemyAnimationController` and `AnimationPlayer` nodes to generated enemy scenes, but the generator was not re-run. The committed `.tscn` files were stale — they did not contain the new nodes. The AC Gatekeeper caught this by directly reading a `.tscn` file and finding the node absent.
  impact: The Gatekeeper correctly blocked completion and required an explicit re-run of the generator (commit 3bae3ea). Without the Gatekeeper's structural verification, the stale scenes would have shipped.
  prevention: Whenever a generator script is modified, the Implementation Agent must re-run it and commit the regenerated output files in the same changeset. A post-implementation checklist item must read: "If any generator script was modified, regenerate all outputs and include them in the commit."
  severity: high

- category: testing
  insight: A test file that statically types a variable as `EnemyAnimationController` will fail to parse if the implementation file does not yet exist, crashing the entire test runner and preventing all other suites from running.
  impact: The Test Designer recognized this and used dynamic `load("res://...")` instead of static class references, allowing the test file to parse cleanly and emit per-test failures rather than a runner crash.
  prevention: All test files for new scripts must use dynamic loading (`load(...).new()`) and untyped local vars when the target class file may not exist at test-break time. The Test Designer prompt should include this as an explicit requirement.
  severity: medium

- category: process
  insight: The spec's test file path (`tests/unit/test_enemy_animation_controller.gd`) did not match the actual project convention (`tests/scripts/enemy/`). The Test Designer had to resolve this ambiguity, creating a low-priority but persistent discrepancy documented in the final Gatekeeper verdict.
  impact: No test execution impact (the runner auto-discovers all `test_*.gd` files). However, the spec path was never corrected, leaving a documented inconsistency between spec and reality.
  prevention: The Spec Agent must verify that any explicitly named test file path matches an existing directory in the project before writing the spec. If `tests/unit/` does not exist, the spec must use the actual convention.
  severity: low

### Anti-Patterns

- description: Specifying `@export var field: SomeConcreteType` for a dependency that will be injected by unit test stubs, without verifying whether the concrete type is subclassable by test stubs or whether Godot 4 enforces the annotation at runtime.
  detection_signal: The spec lists a typed `@export` for any field that the ACS-8 "stub contract" section says must be assignable from a plain `Object` or inner class.
  prevention: When a spec simultaneously requires `@export` on a field and test stub injection into that same field, treat that as a contradiction and resolve it in the spec before handing off to implementation. The resolution is always: remove `@export`, use plain `var` with `Object` typing.

- description: Writing a spec that requires running a generator script but does not include "re-run the generator" as an explicit implementation step, leaving it implicit and easily skipped under time pressure.
  detection_signal: A spec section modifies a generator script's behavior but contains no explicit "regenerate outputs" step in the acceptance criteria.
  prevention: Any AC that modifies a generator script must pair with an AC that verifies the generated output files were regenerated, committed, and match the new generator behavior.

- description: The Impl Agent's first attempt used `@export var animation_player: Node` (weakened to Node) rather than removing the `@export` entirely. This was a partially correct fix — it resolved the type-enforcement crash but retained the serialization side-effect. Only the impl-fix pass, which used a plain `var`, produced the fully correct design.
  detection_signal: An impl-fix iteration that changes `@export var T` to `@export var Node` to unblock tests, rather than questioning whether `@export` is needed at all.
  prevention: When removing a typed `@export` to fix test injection, ask: "Does this field need to appear in the editor inspector or be serialized into the `.tscn`?" If no, remove `@export` entirely rather than weakening the type.

### Prompt Patches

- agent: Spec Agent
  change: "Before specifying any `@export` variable for a dependency that will be unit-tested via stubs: (1) check the dependency type's inheritance chain — if it extends `RefCounted`, the field must never be `@export`; (2) verify whether test stubs can subclass the declared type; (3) if tests must inject a plain Object stub, the field must be declared as `var field: Object = null` with no `@export`, and a `setup()` injection method must be provided. Document the rationale in the spec under 'Constraints'."
  reason: The root cause of the impl-fix iteration was a spec that required `@export var animation_player: AnimationPlayer` and `@export var state_machine: EnemyStateMachine` without accounting for Godot 4.6.1 runtime type enforcement and RefCounted serialization limits. An earlier spec-phase check would have avoided the full rework.

- agent: Implementation Agent
  change: "After modifying any generator script (`generate_enemy_scenes.gd` or equivalent), re-run the generator immediately and verify that all generated output files (`.tscn`, `.tres`, etc.) reflect the changes. Include the regenerated files in the same commit as the generator change. Do not submit for AC Gatekeeper review until the generated outputs have been regenerated."
  reason: The stale `.tscn` files (generator updated but not re-run) caused the Gatekeeper to block completion and required an additional commit. The fix is purely procedural: re-run the generator before closing the implementation stage.

- agent: Test Designer Agent
  change: "All test files for scripts that do not yet exist (test-break stage) must use dynamic loading: `var ScriptClass = load('res://path/to/script.gd')` and untyped vars (`var controller = ScriptClass.new()`). Never use static class-name references in test files for scripts that may not exist at test-break time. A parse error in one test file crashes the entire test runner and prevents all other suites from executing."
  reason: The Test Designer for M7-ACS correctly applied this pattern, preventing a runner crash. Encoding it as an explicit rule prevents future Test Designers from using static class references in test-break files.

### Workflow Improvements

- issue: The initial spec specified `@export` for both `animation_player` and `state_machine` without noting the Godot 4 runtime type enforcement constraint for headless test injection. The constraint was only discovered by the Implementation Agent at test-run time, requiring a full impl-fix pass and a retroactive spec-fix pass.
  improvement: Add a mandatory spec-phase check: for every `@export` field listed in the spec, confirm the type is either a primitive (float, int, String, bool) or a Node-subclass that test stubs can be assigned to without a runtime type error. If neither condition holds, remove `@export` from the spec before handoff.
  expected_benefit: Eliminates the class of impl-fix iterations caused by `@export` type mismatches discovered only at test time. The spec-fix pass (a second Spec Agent run) would also be unnecessary.

- issue: The spec explicitly named `tests/unit/test_enemy_animation_controller.gd` as the test file path, but this directory does not exist in the project. The Test Designer silently resolved this by using the correct convention, leaving the spec incorrect.
  improvement: The Spec Agent must verify that any named file path (especially test paths) resolves to an existing directory structure before emitting the spec. If the directory does not exist, either create it in scope or use an existing path.
  expected_benefit: Prevents spec-vs-reality discrepancies that future agents must silently work around, reducing compounding divergence across tickets.

### Keep / Reinforce

- practice: The AC Gatekeeper directly read a generated `.tscn` file to verify node structure rather than trusting that the generator had been re-run. This structural verification caught the stale scene files that implementation had missed.
  reason: For any ticket that modifies a generator and requires the output to contain specific nodes, the Gatekeeper must read the actual output file, not infer from the generator source. Generator "was updated" does not mean "was run."

- practice: The Test Designer added `play_call_count: int` to the stub class as a pure test-infrastructure additive that does not appear in the production ACS-8 spec. This allowed idempotency and latch tests to assert "no play() call was made" without modifying the production contract.
  reason: Augmenting test stubs with call-counting fields beyond the minimum required interface is the correct pattern for negative-assertion tests ("not called"). It is additive, does not contaminate production code, and makes test intent explicit.

## [split_animated_acid_spitter] — Module split: assert `__module__` and registry identity, not only re-export import path

*Completed: 2026-04-05*

### Learnings

- category: testing
  insight: After moving a class to a dedicated module while keeping a barrel import (`from animated_enemies import X`), existing tests that only check "import works" stay green even if the class body was accidentally duplicated or shadowed in the barrel file.
  impact: Added `AnimatedAcidSpitter.__module__ == 'src.enemies.animated_acid_spitter'` and `assertIs(ENEMY_CLASSES['acid_spitter'], animated_acid_spitter.AnimatedAcidSpitter)` to lock the split contract.
  prevention: For any "extract to module" refactor, add one test for defining `__module__` and one for object identity against the canonical module.
  severity: medium

## [split_animated_adhesion_bug] — No significant learnings identified.

*Completed: 2026-04-05* (same extract-and-register pattern as `split_animated_acid_spitter`; tests and spec followed the established template.)

## [split_animated_carapace_husk] — No significant learnings identified.

*Completed: 2026-04-05* (same pattern: `__module__` + `BPG_ADV_SPLIT_03` registry identity; docs and spec mirrored prior split tickets.)

## [split_animated_claw_crawler] — No significant learnings identified.

*Completed: 2026-04-05* (same pattern as prior animated splits: `test_BPG_CLASS_17b` for `__module__`, `BPG_ADV_SPLIT_04` for registry `is` identity; removed unused `create_quadruped_armature` and top-level `EnemyBodyTypes` import from `animated_enemies.py` after extraction.)

## [split_animated_ember_imp] — No significant learnings identified.

*Completed: 2026-04-05* (same extract-and-register pattern; added `TestEmberImpClass` + `BPG_ADV_SPLIT_05`; removed unused `math` / `Euler` / `create_humanoid_armature` / `create_all_animations` from `animated_enemies.py` after extraction.)

## [split_animated_tar_slug] — No significant learnings identified.

*Completed: 2026-04-05* (same pattern: `TestTarSlugClass` + `BPG_ADV_SPLIT_06`; `animated_enemies.py` reduced to factory + imports after removing unused `BaseEnemy` and geometry/material imports that only served the inlined class.)

---

# Learning Output — [animated_enemy_registry_cleanup]

## Learnings
- category: process
  insight: A ticket marked BLOCKED on stale dependency state blocks progress even when CHECKPOINTS.md and `maintenance/done/` already prove all deps complete; resuming autopilot should verify the filesystem gate before returning to Human.
  impact: Would have stopped at BLOCKED without advancing the pipeline.
  prevention: On `/ap-continue`, list `maintenance/done/` for named dependency slugs and reconcile with the ticket Blocking Issues field.
  severity: medium

- category: architecture
  insight: Placing `AnimatedEnemyBuilder` in `animated/registry.py` while leaf modules stay as `animated_<slug>.py` siblings preserves a one-way import graph (registry → leaves only).
  impact: Avoids circular imports if per-enemy modules ever need shared registry constants.
  prevention: Keep `animated/__init__.py` as re-exports only; do not import registry from leaf enemy modules.
  severity: low

## Anti-Patterns
- description: Leaving a long-lived shim module after migration duplicates the “source of truth” for imports and confuses docs/tests.
  detection_signal: Two public paths (`animated_enemies` vs `animated`) both documented as canonical.
  prevention: After grep-clean migration, delete the old module in the same change set as test/doc updates.

*Completed: 2026-04-05*

---

# Learning Output — [base_models_split_by_archetype]

## Learnings
- category: process
  insight: A ticket can sit at IMPLEMENTATION_GENERALIST while the refactor already exists only on disk; `/ap-continue` should diff against `git status` before redoing work.
  impact: Avoids duplicate edits and speeds closure to AC Gatekeeper + commit.
  prevention: On resume, run `git status` on spec paths and pytest before invoking implementation agents.
  severity: low

- category: infra
  insight: Spec BMSBA-5.3 mandates ruff on touched files, but the package may not ship ruff — document Static QA as skipped with evidence rather than blocking COMPLETE.
  impact: Unblocks closure when lint tool is absent.
  prevention: Align spec templates with `pyproject.toml` optional dev deps or add ruff to dev extras.
  severity: low

## Anti-Patterns
- description: Leaving a deleted monolith (`base_models.py`) and new package untracked while the ticket advances through test stages.
  detection_signal: `git status` shows `D base_models.py` and `?? base_models/` with green pytest.
  prevention: Commit implementation in the same session as IMPLEMENTATION_GENERALIST handoff or immediately on resume.

*Completed: 2026-04-05*

---

## [MAINT-EAPD] — Headless tests must not use `ClassDB` for GDScript `class_name`; defer tickets need explicit pipeline waiver alignment

*Completed: 2026-04-05*

### Learnings

- category: testing
  insight: In headless Godot runs (`run_tests.gd`), GDScript global classes registered via `class_name` are not reliably visible on `ClassDB` the same way as engine types.
  impact: A naive `ClassDB.class_exists("EnemyAnimationController")`-style assertion would be flaky or false relative to editor expectations.
  prevention: Assert canonical script identity by loading the `GDScript` resource, checking `get_global_name()`, and matching `resource_path` to the expected `res://` path.
  severity: medium

- category: process
  insight: Default autopilot stage progression (e.g. advancing to `TEST_DESIGN` after Spec) can contradict an execution plan that explicitly waives implementation and test stages for “defer-only” closure.
  impact: Agents operated under medium-confidence assumptions about which instruction wins until reconciled via `NEXT ACTION` / Reason text.
  prevention: For defer placeholders, the handoff Reason must state AC-1-only scope (policy + tests, no prod edits) and that waived stages are not closure gates.
  severity: medium

- category: testing
  insight: Maintenance suites that guard shared state→clip semantics may intentionally couple tests to private resolvers via `call()` / `has_method()` so silent mapping drift fails loudly.
  impact: Accepts brittleness to internal refactors in exchange for catching the intended regression class; future policy-injection work stays explicitly out of scope for that suite.
  prevention: When adding such tests, document in-suite (`# CHECKPOINT` or file header) which future ticket owns the alternative (e.g. AC-2) coverage.
  severity: low

### Anti-Patterns

- description: Using `ClassDB.class_exists()` as the sole proof that a project `class_name` exists in headless CI.
  detection_signal: Tests or specs mandate ClassDB checks for GDScript globals; green locally in editor but ambiguous or wrong under headless runner.
  prevention: Prefer loaded-script identity checks (`GDScript` + path + global name) for project scripts.

### Prompt Patches

- agent: Test Designer Agent
  change: "For headless test suites, do not use `ClassDB.class_exists()` alone to assert a GDScript `class_name` global exists; load the script resource, assert `GDScript.get_global_name()` and `resource_path` match the canonical `res://` file."
  reason: Avoids false negatives and editor/headless divergence for global class registration.

- agent: Autopilot / Orchestrator (or Planner Agent)
  change: "When the execution plan marks TEST_DESIGN, TEST_BREAK, and IMPLEMENTATION as waived for closing a defer-only ticket, set `NEXT ACTION` Reason to state explicitly that downstream agents run AC-1-only (documentation and allowed policy tests) and must not treat waived stages as mandatory code-change gates."
  reason: Resolves conflict between default stage FSM and ticket-specific closure rules without ad hoc per-run interpretation.

### Workflow Improvements

- issue: Spec-complete tickets that defer implementation still enter the full stage names in order, which reads like a full pipeline despite waiver.
  improvement: Add a maintenance/defer template flag (or standard Reason boilerplate) that names the first in-scope agent after Spec and labels others N/A for closure in one place.
  expected_benefit: Reduces medium-confidence checkpoint churn on “which pipeline wins.”

### Keep / Reinforce

- practice: Satisfying AC-1 on architecture deferrals with a focused maintenance test file that encodes policy invariants (path, exports, shared behavior contracts) without editing production scripts.
  reason: Gives traceable, CI-enforced evidence for “no preemptive refactor” decisions.

---

## [MAINT-EMMU] — SSOT maps need subtree scans and consumer parity; gatekeeper-before-review needs a GDScript safety pass

*Completed: 2026-04-05*

### Learnings

- category: testing
  insight: Enforcing “exactly one literal under `scripts/asset_generation/`” is stronger with a **recursive directory scan** (e.g. walk the tree and flag `const MUTATION_BY_FAMILY := {` patterns) than relying on a single known file or repo-wide `rg` without a scoped subtree rule—duplicates can land in sibling files under the same folder.
  impact: Catches second definitions if the map or copy-paste spreads within the generation subtree; aligns with EMU-QA-1 intent beyond the canonical module path.
  prevention: For SSOT-by-path ACs, encode tests that enumerate `DirAccess` (or equivalent) under the declared root and assert count/location of forbidden patterns.
  severity: medium

- category: architecture
  insight: **`load_assets.gd` and `generate_enemy_scenes.gd` must stay in strict-mode parity** for shared helpers (e.g. AABB aggregation, capsule-related mesh typing): typed `Array[MeshInstance3D]`, explicit `AABB` / `Transform3D` / `Vector3`, and the same collision-shape assumptions. Touching one consumer for a shared preload can surface parse or type errors in the other when headless loads the `@tool` script.
  impact: Implementation aligned AABB helpers so `load()` of the editor script parsed under strict mode; without parity, green mutation-map tests could mask a broken editor pipeline.
  prevention: When editing either consumer, diff helper signatures and typing against the twin script before handoff; add or extend a minimal parse/load test if the project already loads these scripts headless.
  severity: medium

- category: process
  insight: If **Acceptance Criteria Gatekeeper runs before GDScript Reviewer** in a given run, treat that as mis-ordered closure: schedule **GDScript review immediately after gatekeeper** (or reorder the pipeline) so strict-mode, typing, and lifecycle issues on touched scripts are not skipped after “suite green.”
  impact: Reduces risk of marking COMPLETE while review-only findings remain.
  prevention: Document the corrective order in autopilot resume notes when stage FSM does not match agent charter order.
  severity: low

### Anti-Patterns

- description: Asserting SSOT only by checking the new module file exists, without scanning the **whole** subtree named in the AC for duplicate map literals.
  detection_signal: AC says “under `scripts/asset_generation/`” but tests only open one path; a second file could reintroduce `const MUTATION_BY_FAMILY := {`.
  prevention: Recursive scan + assert single literal location; keep `is_same()` / preload identity checks for runtime reference sharing.

- description: Changing imports or constants in `load_assets.gd` without reconciling **typed helper parity** with `generate_enemy_scenes.gd`.
  detection_signal: Headless parse errors or Variant warnings only when the editor script is loaded; asymmetric `Array` typing or missing explicit geometry types.
  prevention: Pair-edit both consumers when they share generation geometry helpers.

### Prompt Patches

- agent: Test Designer Agent
  change: "For tickets that require a single const map literal under a directory subtree (e.g. `scripts/asset_generation/`), add a test that **recursively walks that directory** (via `DirAccess` or project equivalent) and fails if more than one forbidden pattern (e.g. `const MUTATION_BY_FAMILY := {`) appears outside the canonical file; combine with preload/`is_same()` assertions so behavior and filesystem SSOT both hold."
  reason: Prevents duplicate literals in sibling files that a one-file test would miss.

- agent: Implementation Generalist Agent
  change: "When modifying `load_assets.gd` or `generate_enemy_scenes.gd` for shared asset-generation data, **diff AABB/capsule/mesh helper blocks** between the two scripts and align typed arrays and explicit `AABB`/`Transform3D`/`Vector3` usage so both parse under project strict mode and headless `load()` of the `@tool` script matches the SceneTree generator."
  reason: Avoids editor-only parse failures after consumer-only edits.

- agent: Autopilot / Orchestrator (or Planner Agent)
  change: "If the pipeline orders **Acceptance Criteria Gatekeeper before GDScript Reviewer**, insert a **mandatory GDScript Reviewer pass after gatekeeper** (or reschedule gatekeeper after review) so COMPLETE is not issued without script review on all touched `.gd` files."
  reason: Corrects weak closure when automated stage order inverts the intended review-then-signoff sequence.

### Workflow Improvements

- issue: Stage FSM may advance to gatekeeper while GDScript review is still pending or ordered later, weakening “review before ship” intent.
  improvement: Define a single canonical order (Spec → tests → implementation → **GDScript review** → **gatekeeper**) or an explicit post-gatekeeper review exception with a logged reason.
  expected_benefit: Fewer COMPLETE states with unreviewed script diffs.

### Keep / Reinforce

- practice: SSOT tests that preload the canonical module and use **`is_same()`** to prove consumers share **dictionary identity**, not just equal contents.
  reason: Catches duplicate literals that happen to match byte-for-byte.

- practice: Test Breaker hardening for **alternate dict declaration forms** and acyclic preload graph checks on the map module.
  reason: Reduces bypass via syntax variants or accidental consumer preload from the SSOT file.

---

## [MAINT-ESEG] — Shared enemy root script resolver, dual-consumer wiring, and unsafe stem hardening

*Completed: 2026-04-05*

### Learnings

- category: architecture
  insight: Choosing which gameplay script attaches to generated enemy roots is **shared policy**: a single resolver module must be the only place that encodes override directory + fallback base path; consumer scripts should not embed override-path literals so drift is caught by tests.
  impact: Ticket AC named `generate_enemy_scenes.gd` explicitly; correct behavior still required the same resolution in `load_assets.gd` and a shared API both call before `set_script`.
  prevention: Centralize path rules in one preloadable module; add tests that fail if either consumer hard-codes `res://scripts/enemies/generated/` (or equivalent) instead of calling the resolver.
  severity: medium

- category: testing
  insight: **`ResourceLoader.exists` on a formatted path is not sufficient** for adversarial `family_name` values: stems with path separators or `..` can escape the intended single-file layout unless the resolver rejects or normalizes them.
  impact: Test Breaker stage extended the suite with unsafe-stem cases; implementation added sanitization and empty-stem → base behavior.
  prevention: For any resolver that builds `res://.../<user-derived-segment>.gd`, encode tests for empty stem, `/`, `\`, and `..`; require the resolver to fall back to the safe default path when input is unsafe.
  severity: medium

- category: architecture
  insight: When some call sites already pass `EnemyNameUtils.extract_family_name` output and others might pass a raw GLB basename, the **resolver boundary** should normalize using the same utility when input matches basename-shaped patterns, instead of assuming a single caller convention.
  impact: Avoids subtle “works in CLI, wrong override in editor” or vice versa if one pipeline passes a different string shape.
  prevention: Document accepted input shapes on the resolver; implement normalization once inside the resolver before `exists` + `load`.
  severity: medium

- category: process
  insight: Spec that allows **implementer-chosen module filename** but leaves the **public method name** implicit can create medium-confidence mismatch risk between Test Designer fixtures and Implementation unless names are aligned in the same revision.
  impact: Checkpoint noted method naming as implementer-facing; unnecessary churn if tests and code disagree on `resolve_*` spelling.
  prevention: Either fix the resolver’s public method name in the spec handoff or have Test Designer quote the exact callable expected by tests in WORKFLOW STATE / ticket so Implementation matches in one pass.
  severity: low

### Anti-Patterns

- description: Duplicating “if override exists use X else base” conditionals in `generate_enemy_scenes.gd` and `load_assets.gd` instead of a shared resolver.
  detection_signal: Two files both mention override directory logic or both format the same `res://` pattern; tests cannot assert a single implementation.
  prevention: One module, two call sites, tests assert both consumers invoke it.

- description: Treating **`exists(formatted_path)`** as the only guard when the formatted path incorporates caller-controlled segments.
  detection_signal: Resolver concatenates `family_name` into a path without validating characters; security or layout bugs on malicious or mistaken stems.
  prevention: Reject or normalize unsafe stems; test adversarial inputs explicitly.

### Prompt Patches

- agent: Planner Agent
  change: "When ticket AC names only `generate_enemy_scenes.gd` for enemy asset output but `project_board/LEARNINGS.md` documents **editor vs headless parity** with `load_assets.gd`, add **`load_assets.gd` to blast radius and success criteria** in the execution plan and require the Spec Agent to state both consumers must call the same resolver."
  reason: Prevents shipping resolver logic in only one pipeline because the AC line was incomplete.

- agent: Test Breaker Agent
  change: "For resolvers that build `res://scripts/.../<stem>.gd` from a string parameter, add cases for **empty stem**, path separators, and `..`; assert the resolver returns the **safe base script path** and never a path that escapes the single-file layout under the override directory."
  reason: `ResourceLoader.exists` alone does not substitute for input validation on formatted paths.

- agent: Implementation Generalist Agent
  change: "When wiring `enemy_root_script_resolver` (or equivalent), if callers may pass either a **raw GLB basename** or **`EnemyNameUtils.extract_family_name` output**, normalize inside the resolver using `EnemyNameUtils.extract_family_name` when the input matches basename-shaped patterns before override lookup."
  reason: Keeps CLI and `@tool` pipelines aligned without requiring every call site to pre-normalize identically.

- agent: Spec Agent
  change: "When introducing a new shared module with a single required entrypoint, either **name the public method** in REQ text (e.g. `resolve_enemy_root_script_path`) or explicitly state ‘Test suite defines the callable name; implementation must match tests’ to avoid spec vs test-design drift."
  reason: Reduces revision churn when filename is flexible but API surface is not.

### Workflow Improvements

- issue: Acceptance criteria can list one generator file while repo precedent mandates two consumers stay in lockstep for the same behavior.
  improvement: Maintenance ticket template or planner checklist: for `scripts/asset_generation/*` behavior, grep for **`load_assets.gd` + `generate_enemy_scenes.gd`** and require dual-consumer language in spec AC when both attach scripts or metadata to generated enemies.
  expected_benefit: Fewer “AC satisfied in one file only” handoffs.

### Keep / Reinforce

- practice: Tests that **forbid embedding** the override directory literal in consumer sources while asserting both call the shared resolver.
  reason: Makes duplicate path logic mechanically detectable in CI.

- practice: A minimal **`extends EnemyBase`** fixture under `scripts/enemies/generated/` used only to prove “override exists” path selection, without mass-regenerating committed `.tscn` files.
  reason: Verifies AC for present-override behavior without churning all generated scenes when defaults stay on `enemy_base.gd`.

---

## [MAINT-ETRP] — Leaf slug registry + shared accessors prevent CLI vs `get_*()` drift

*Completed: 2026-04-05*

### Learnings

- category: process
  insight: If `main.py` list/help paths and library helpers like `EnemyTypes.get_animated()` are allowed to carry **independent copies** of the same slug enumeration, the copies will eventually diverge when one path is updated and the other is not; the fix is a **single authoritative sequence** (registry tuples consumed by `EnemyTypes` and by any CLI or generation entrypoint).
  impact: Ticket acceptance criteria explicitly required list commands and smart generation to stay aligned; parallel literals would violate that silently.
  prevention: Wire listing and smart pipelines through the same module or `get_*()` accessors; lock equality with frozen pytest expectations and, when AC demands it, a CLI smoke that compares visible output to those accessors.
  severity: medium

- category: architecture
  insight: Extracting immutable slug lists into a **leaf** `enemy_slug_registry`-style module with a documented import DAG—registry **never** imports `constants`, while `constants.EnemyTypes` may import the registry—turns “avoid circular imports” from a hope into a structural constraint enforceable by review and tests.
  impact: REQ-ETRP-002 and adversarial AST checks made violations machine-detectable rather than latent load-order bugs.
  prevention: For any growing aggregator module, peel stable string tuples to a leaf file; document one-way imports; add static or AST guards against upward imports from the leaf.
  severity: medium

- category: testing
  insight: In-package pytest often uses a `sys.path` layout that differs from running `main.py`; a **fresh subprocess** import-order smoke that mirrors the real entrypoint can surface import graphs that pass under pytest but fail at CLI launch.
  impact: Checkpoint called out isolating `utils.*` loading from pytest’s `src.utils` behavior; REQ-ETRP-004 encoded subprocess import order.
  prevention: For import-DAG tickets, include a minimal subprocess test sequence specified in the spec (e.g. import `utils.constants` then `utils.enemy_slug_registry` without `ImportError`).
  severity: medium

### Anti-Patterns

- description: Maintaining slug enumerations as duplicate literals in `main.py` (choices, help, or manual loops) while `EnemyTypes.get_animated()` / `get_static()` remains the “real” list elsewhere.
  detection_signal: Grep shows string slugs or tuples in CLI-only code but not routed through `EnemyTypes` or `enemy_slug_registry`; new enemy added in one place only.
  prevention: Single source: registry tuples or `get_*()`; CLI and smart generation both consume that surface.

- description: Creating a “registry” module that still imports `constants` (or anything that transitively loads `constants`) for convenience.
  detection_signal: New file appears to centralize data but pulls in the fat constants package; intermittent circular import errors depending on entrypoint.
  prevention: Keep registry as data-only leaf; compose in `constants` or other aggregators; AST or lint rule forbidding registry → `constants` imports.

### Prompt Patches

- agent: Spec Agent
  change: "When acceptance criteria require CLI list commands and generation code to **agree on type lists**, add an REQ that names the **single source of truth** (e.g. `enemy_slug_registry` tuples and `EnemyTypes.get_animated()` / `get_static()`) and explicitly forbids maintaining a **second parallel enumeration** in `main.py` or argparse-only code."
  reason: Prevents main.py list drift vs `get_*()` at specification time.

- agent: Implementation Generalist Agent
  change: "When extracting registries from `constants.py`, implement **one-way imports only**: the registry module must not import `constants` or modules that transitively import it; add tests that **AST-scan the registry** for forbidden imports and a **subprocess import-order smoke** aligned with how `main.py` resolves `utils`."
  reason: Makes the registry extraction pattern repeatable and catches pytest-only green states.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "If the ticket AC requires CLI list behavior to match `EnemyTypes` / registry, treat **`main.py list` (or equivalent) exit 0 and output consistency** as blocking evidence before COMPLETE—not optional follow-up—unless an automated pytest harness is specified that exercises the same argparse path without Blender."
  reason: Autopilot deferred CLI smoke to gatekeeper; explicit blocking criteria avoids assuming someone will run the command later.

### Workflow Improvements

- issue: Multi-stage plans can mark “CLI list integration” as task 6 while an autopilot run stops at green pytest and assumes gatekeeper will run `main.py list`.
  improvement: Either fold a no-Blender CLI assertion into pytest (same wiring as `main.py list`) or require gatekeeper checklist item with logged output before marking COMPLETE.
  expected_benefit: AC “list commands still agree” is provably satisfied every time, not only when a human remembers the smoke.

### Keep / Reinforce

- practice: Immutable `ANIMATED_SLUGS` / `STATIC_SLUGS` tuples, `EnemyTypes` delegation, frozen snapshot contract tests, disjoint-set adversarial check, subprocess import-order smoke, and AST ban on registry importing `constants`.
  reason: Combines string freeze, DAG safety, and entrypoint-realistic imports in one maintainable bundle.

---

## [MAINT-EMSI] — Uniform model scale: preserve literal kwargs at multiplier 1.0; align mocks and fail-fast validation tests

*Completed: 2026-04-05*

### Learnings

- category: testing
  insight: A “no-op” uniform scale of `1.0` must not always flow through generic multiply helpers: multiplying tuple components by `1.0` can widen integer literals to floats and break strict backward-compatibility assertions on mocked primitive kwargs versus legacy code.
  impact: Implementation explicitly short-circuited scaling when `self.scale == 1.0` so call logs stay identical to pre-change behavior for mixed int/float geometry inputs.
  prevention: For default-multiplier APIs, add a fast path that returns inputs unchanged at `1.0` when tests or exporters assert byte- or tuple-level parity with legacy.
  severity: medium

- category: process
  insight: Early planning assumed a distinct instance field name (`geometry_scale` / `uniform_scale`) to avoid colliding with Blender object `scale`; the frozen spec chose `instance.scale` to match the ticket and EMSI-1, which is the right tradeoff but makes planning-only docs potentially misleading if read in isolation.
  impact: Low rework here (spec won), but it is an avoidable moment of ambiguity for implementers skimming checkpoints out of order.
  prevention: At spec freeze, add a one-line “resolution” when planning checkpoints assumed a different public name or shape than the REQ IDs.
  severity: low

- category: testing
  insight: Asserting an **empty** primitive call log for invalid scale catches validation that runs too late (after geometry calls), which a mere `ValueError` assertion might miss if order is wrong.
  impact: Test Breaker added fail-fast / mutation cases tied to EMSI-2.
  prevention: For validated builder/factory APIs backed by mocked side effects, pair domain errors with “no work performed” signals (empty logs, call counts) where the spec allows.
  severity: medium

- category: architecture
  insight: Observable contract for uniform scaling should pin whether parity is defined on **kwargs to primitives** vs a parent transform; an implementation that only applies a root empty still must satisfy the chosen observable or update tests with spec-backed equivalence.
  impact: Checkpoints flagged medium risk if implementation diverged from tuple-multiply reference without test updates.
  prevention: Spec should name the primary mock-observable (e.g. scaled `location` / primitive `scale` tuples) and treat alternate strategies as explicitly equivalent with adjusted tests.
  severity: low

### Anti-Patterns

- description: Implementing scale helpers as unconditional `component * scale` including when `scale == 1.0`, breaking int/float identity in asserted Blender primitive kwargs.
  detection_signal: Parity tests fail only on default scale with “expected (0, 0, z) got (0.0, 0.0, z)” or similar tuple drift.
  prevention: Short-circuit at `1.0` or preserve original tuple objects when the multiplier is exactly one and parity is required.

- description: Patching `create_sphere` / `create_cylinder` on a different import path than the archetype module under test, so mocks never fire and tests false-green or miss regressions.
  detection_signal: New test file passes but does not intercept calls; differs from sibling factory tests’ patch targets.
  prevention: Copy patch targets from the established factory test module for the same archetype package layout.

### Prompt Patches

- agent: Implementation Generalist Agent
  change: "When adding a default `scale` (or similar uniform multiplier) to geometry builders, if acceptance tests assert **kwargs parity with legacy at the default multiplier**, implement a **`scale == 1.0` short-circuit** that returns locations/extents unchanged so integer literals are not widened to floats by multiply-by-1.0."
  reason: Prevents spurious default-scale failures while keeping non-1.0 paths mathematically uniform.

- agent: Test Designer Agent
  change: "For Blender procedural tests that mock `create_sphere` / `create_cylinder`, state in the test module (or ticket notes) that patches must target the **same module attribute paths** as existing factory tests in `tests/enemies/` so mocks bind where archetypes invoke primitives."
  reason: Avoids silent non-intercepted mocks across package import boundaries.

- agent: Test Breaker Agent
  change: "For validated factory/builder APIs with mocked side effects, add at least one case where **invalid input yields both the specified exception and zero recorded primitive (or IO) calls**, to catch validation ordered after work."
  reason: Strengthens fail-fast guarantees beyond exception type alone.

### Workflow Improvements

- issue: Planning checkpoints can recommend API or field names that the spec later overrides without an explicit bridge note.
  improvement: Spec Agent adds a short “Planning resolution” bullet when REQ text contradicts the latest planning checkpoint assumption.
  expected_benefit: Implementers and reviewers do not treat stale planning confidence as authoritative.

### Keep / Reinforce

- practice: Adversarial additions—`math.nextafter` boundaries, large finite scale, fractional non-power-of-two scale, identical primitive **sequence** across scales for determinism, positional vs keyword `scale`, `int` vs `float` equivalence, unknown-type fallback with scale, and direct `HumanoidModel(..., invalid scale)` validation.
  reason: Small surface-area API changes still benefit from breadth without a full Blender render.

---

## [MAINT-HCSI] — Design-space vs global HUD tests; hybrid scaling when a single parent `scale` fails subtree uniformity

*Completed: 2026-04-05*

### Learnings

- category: testing
  insight: When a packaged HUD gains a scale transform or reparenting under `CanvasLayer`, tests that asserted raw scene `offset_*` on former direct children must distinguish **authoring/design space** from **`get_global_rect()` (transformed space)** so default-scale parity (HCSI-style ACs) stays meaningful without fighting the new root.
  impact: `test_player_hud_layout.gd` gained a design-space helper; `test_fusion_opportunity_room.gd` viewport bounds moved to global rects where the contract is on-screen geometry.
  prevention: For UI tickets that add scale or intermediate roots, plan coordinated updates: design-space helpers for scene-authored numbers, global rects for player-visible bounds and cross-widget ratios.
  severity: medium

- category: architecture
  insight: A single `Control.scale` on a container is not always enough for **uniform global-rect scale factors** across all descendants under `CanvasLayer` (e.g. a wide `Hints` strip with nested labels); a hybrid may be required—resize the container via scaled `offset_*` and apply `scale` to selected children so ratios match sibling HUD bars in tests.
  impact: Implementation checkpoint documents why parent-only scaling failed ratio checks for hints vs HPBar and how base pack dimensions must stay aligned with the scene at `hud_scale == 1.0`.
  prevention: Validate scale invariants using **multiple node roles** (top-level bar, nested label, container vs leaf) before locking a one-container approach; document any script constants that duplicate scene layout numbers.
  severity: medium

- category: testing
  insight: Adversarial cases for a float export—fractional scale, `1.0 → 2.0 → 1.0` idempotency, int-like `set()`, non-finite values, non-positive values, and a high stress ratio—surface clamp/validation gaps and “only tested at one multiplier” mutations quickly.
  impact: Test Breaker run reported expected pre-implementation failures; post-implementation suite green with explicit sanitization behavior.
  prevention: For designer-facing numeric exports on UI roots, mirror this breadth so setter semantics are pinned before reviewers assume a single happy-path multiplier is sufficient.
  severity: medium

- category: process
  insight: Early planning correctly flagged that `CanvasLayer` roots are not `Control`-scalable as-is, that reparenting risks `get_node` contracts in scripts, and that **non-`tests/ui/`** suites load the same packaged scene—those assumptions prevented silent breakage in fusion/start-flow tests.
  impact: Spec and test design explicitly extended level tests where viewport geometry mattered.
  prevention: For shared packaged scenes, keep a standing checklist: script path contracts, root type/name tests, and grep for `game_ui` (or equivalent) outside the primary UI test directory.
  severity: low

### Anti-Patterns

- description: Proving uniform HUD scale using only one widget class (e.g. a single progress bar) while `Hints`/labels live in a differently structured subtree.
  detection_signal: Global-rect width/height ratios diverge between bars and hint leaves at the same `hud_scale`.
  prevention: Add cross-role triangulation tests (implemented: `MutationIcon1` vs `HPBar`, `Hints` container vs `MoveHint`) before signing off on mechanism.

- description: Script constants for “base” layout sizes that can drift from the `.tscn` without a documented sync obligation.
  detection_signal: Scale `1.0` looks wrong only for one subtree after scene edits; tests pass on CI until someone opens the game.
  prevention: Comment or REQ that base width/height constants must match authoring offsets at default scale, or drive them from a single exported source.

### Prompt Patches

- agent: Implementation Frontend Agent
  change: "When implementing uniform HUD scale under `CanvasLayer`, verify **`get_global_rect()` scale ratios on representative leaves** (not only top-level bars). If parent-only `Control.scale` fails uniformity for a subtree (e.g. wide hint strips with nested labels), use a **documented hybrid** (e.g. scaled container `offset_*` plus per-child `scale`) and keep any script **base pack constants** aligned with the scene at default scale."
  reason: Avoids false confidence from a mechanism that looks uniform on one node type only.

- agent: Test Designer Agent
  change: "Before implementation lands, if layout tests assert scene `offset_*` on nodes that may be **reparented or scaled**, introduce or preserve helpers that read **design/authoring space** separately from **`get_global_rect()`**, and update **non-`tests/ui/`** consumers that assert viewport or HUD geometry to use the contract the spec defines for transformed space."
  reason: Preserves meaningful default-scale parity and prevents fusion/level tests from asserting the wrong coordinate space.

- agent: Planner Agent
  change: "When a ticket changes a **packaged UI scene** root or child structure, require an explicit inventory of **all test files** (not only `tests/ui/`) that instantiate or assert that scene, including **script `get_node` / path contracts**."
  reason: Catches level/integration tests that would otherwise break only after merge.

### Workflow Improvements

- issue: Adversarial tests for non-finite and non-positive float exports presuppose setter semantics (clamp vs reject) that the spec may only hint at.
  improvement: For UI scale REQ IDs, add one line in the spec: **expected behavior for non-finite and `≤ 0` writes** (even if defensive) so implementation and tests agree in one pass.
  expected_benefit: Fewer round-trips between Test Breaker expectations and implementer interpretation.

### Keep / Reinforce

- practice: Test Breaker’s fractional scale, order/idempotency, stress ratio, type coercion, and non-finite/non-positive cases on the same export.
  reason: Efficiently guards float UI knobs against narrow happy-path implementations.

- practice: Gatekeeper re-run of full `run_tests.sh` with AC matrix tied to named tests and script/scene evidence.
  reason: Clear closure traceability for maintenance HUD tickets.

---

## [MAINT-SLEEV] — Ticket `run/main_scene` prose vs repo; SLEEV-4.2 honest deferral; ADV ordering and source-scene guards

*Completed: 2026-04-05*

### Learnings

- category: process
  insight: Maintenance tickets can embed stale `project.godot` assumptions (e.g. `run/main_scene` target) that no longer match the repo; closure must not pretend the ticket prose is true.
  impact: Ticket Description/AC3 named `test_movement_3d.tscn` as main scene; repo had `procedural_run.tscn`. Spec **SLEEV-4.2** and Validation Status documented drift; tests enforced **SLEEV-4.1** only (main scene must not reference the new legacy duplicate).
  prevention: For any AC that pins `project.godot`, add a spec branch up front: exact equality, or documented actual value + narrowed automated contract + optional follow-up policy ticket.
  severity: medium

- category: testing
  insight: When a new scene is added by duplication, ordering ADV/source invariants before the “new file exists” gate keeps CI failing exactly once on the missing asset while still protecting the canonical scene and `run/main_scene` loadability.
  impact: Test Breaker ran source-sandbox GLB/`model_scene` guards and `project.godot` PackedScene checks before **SLEEV-1.1** so regressions surface alongside the single expected pre-implementation failure.
  prevention: For duplicate-scene maintenance, structure tests so source and global config assertions are not skipped behind a missing-file early return.
  severity: medium

- category: testing
  insight: Stricter file-text assertions than the normative spec bullets need an explicit trail so implementers do not treat failures as “spec bug.”
  impact: Tests forbade any `.glb` in `[ext_resource]` on the legacy level (stricter than four named paths); Test Designer documented this as intentional for devlog intent.
  prevention: When tests strengthen beyond REQ text, add a one-line comment or amend the spec so the contract is single-sourced.
  severity: low

### Anti-Patterns

- description: Validating a ticket by silently treating ticket `run/main_scene` prose as satisfied without reading `project.godot` or updating AC with traceability.
  detection_signal: Validation Status or docs claim parity with ticket Description while `grep`/`project.godot` shows a different path.
  prevention: Quote actual config in Validation Status and cite the spec clause that narrows or defers the assertion.

- description: Only asserting the new duplicate scene while dropping invariants on the original sandbox, allowing accidental removal of `model_scene` overrides on the live level.
  detection_signal: Legacy scene passes but `test_movement_3d.tscn` loses GLB `ext_resource` or `model_scene` lines.
  prevention: Keep **ADV-SLEEV-source_*** (or equivalent) checks on the canonical scene in the same test module.

### Prompt Patches

- agent: Planner Agent
  change: "Before finalizing a maintenance ticket plan, if Description or AC references `run/main_scene` or other `project.godot` keys as fixed, read `project.godot` (or require the Spec Agent to add an explicit sub-req: assert exact string **or** document actual value + deferred follow-up). Do not assume ticket prose matches repo."
  reason: Avoids planning and gatekeeping against a fictional baseline.

- agent: Spec Agent
  change: "Whenever requirements depend on `project.godot`, include a numbered escape hatch when ticket prose may disagree with repo (e.g. **X.Y**: closure allowed if actual value is documented, automated tests assert the minimal safe invariant such as ‘must not reference the new scene,’ and product intent is routed to a policy ticket)."
  reason: Preserves honest traceability without blocking shipping the scene work.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "If tests defer a full AC clause (e.g. exact `run/main_scene` match), Validation Status must state the real `project.godot` value, cite the spec deferral ID, and forbid silently editing Description/AC to match repo unless that edit is an explicit human/product decision."
  reason: Prevents false closure and preserves audit trail.

- agent: Test Designer Agent
  change: "If file-text or scene assertions are stricter than the spec’s enumerated paths (e.g. ‘no `.glb` in any `[ext_resource]`’ vs four named GLBs), document that tightening in the test file header or update the spec so failure messages map to an agreed REQ."
  reason: Reduces implementer confusion and spec-vs-test arguments.

### Workflow Improvements

- issue: Tickets copied from older workflow docs can assert `run/main_scene` targets that M6 or later policy has moved.
  improvement: For sandbox-only maintenance, add a one-line planner checklist: confirm `run/main_scene` in `project.godot` vs ticket; if mismatch, spec owns SLEEV-4.2-style resolution before TEST_DESIGN.
  expected_benefit: Fewer mid-pipeline spec/test/gatekeeper reconciliations.

### Keep / Reinforce

- practice: **SLEEV-4.2** pattern—document drift, assert minimal safe invariant, escalate product intent separately.
  reason: Honest validation without blocking useful duplicate scenes.

- practice: Test Breaker’s ordering so ADV and source-scene checks run even when **SLEEV-1.1** fails first.
  reason: One clear missing-file failure while canonical scene and `project.godot` stay guarded.

---

## [MAINT-TSGR] — Combined runner fail-fast; DRY lefthook/CI; static bash contract + pytest mirrors

*Completed: 2026-04-05*

### Learnings

- category: infra
  insight: Shell steps that use `|| true` or discard stderr on prerequisites (e.g. headless `--import`) can report success while the tree or cache is broken, so later tests run on a false premise.
  impact: The pre-ticket runner could mask import/reimport failures and still proceed to Godot tests.
  prevention: Treat bounded `timeout` + visible stderr + `set -e` on import and test invocations as default; any bypass must be narrow, commented, logged, and spec-approved.
  severity: high

- category: process
  insight: “Full CI” and “pre-push” hooks must invoke the same resolver and phase order or teams get two different definitions of green.
  impact: Python pytest lived under lefthook only while `run_tests.sh` was Godot-only, so a canonical full run could miss Python failures.
  prevention: Extend the documented canonical script to call the shared Python entry (e.g. `.lefthook/scripts/py-tests.sh`) rather than duplicating resolver logic inline.
  severity: medium

- category: testing
  insight: Orchestration requirements (order, `set -e`, no masking, doc pointers) are expensive to prove with live engine-crash tests; a small executable bash verifier plus pytest that shells out from repo root encodes most of the contract cheaply.
  impact: TSGR-1..6 gained automated regression signal before and after implementation; adversarial tests added cwd independence and hollow-verifier guards.
  prevention: For runner/CI shell ACs, plan a static verifier + thin pytest wrapper as the default verification path when integration stubs are out of scope.
  severity: medium

- category: infra
  insight: Line-order and substring-based static checks on shell sources are brittle if comments or headers contain trigger tokens (e.g. `pytest`) above an earlier required line.
  impact: Implementers must keep comment placement compatible with naive ordering probes unless the verifier is upgraded in the same change.
  prevention: Document forbidden comment patterns next to the verifier, or replace line-order checks with structured markers or a single parsed block.
  severity: low

### Anti-Patterns

- description: Using `|| true` or redirecting stderr away from import/reimport or other prerequisite commands in the combined test runner.
  detection_signal: Script continues after import errors; CI logs lack stderr for the failed phase; exit code 0 with broken `.godot` cache.
  prevention: Fail-fast defaults; logged, spec-scoped bypasses only.

- description: Running Python tests only in git hooks and Godot tests only in CI (or duplicated resolver logic in two places).
  detection_signal: `run_tests.sh` and `.lefthook/scripts/py-tests.sh` disagree on `uv`/`.venv`/fallback behavior or one path omits a suite entirely.
  prevention: One callable script for the Python phase; CI and lefthook both delegate to it.

### Prompt Patches

- agent: Implementation Generalist Agent
  change: "When editing `ci/scripts/run_tests.sh` or `.lefthook/scripts/godot-tests.sh` guarded by MAINT-TSGR-style static contract tests, do not place comment lines containing `pytest` or `py-tests` above the Godot `run_tests.gd` invocation unless you update `verify_tsgr_runner_contract.sh` and the pytest mirrors in the same change; keep ordering probes green."
  reason: Naive line-order checks treat documentation comments as structure.

- agent: Test Designer Agent
  change: "For combined-runner specs, list which clauses are covered by static shell verification vs full integration (e.g. `timeout` SIGTERM exit aggregation). If static proof is impossible, name the gap in the spec and reserve gatekeeper or optional stub-based tests so it is not mistaken for proven."
  reason: Prevents false confidence on TSGR-4.3-style behaviors.

- agent: Planner Agent
  change: "For maintenance tickets whose AC requires non-zero exits on failure, grep the current canonical runner and hook scripts for `|| true`, `2>/dev/null`, or stderr discard on import/test lines and treat hits as explicit rework scope in the execution plan."
  reason: Surfaces the dominant false-green pattern before implementation starts.

### Workflow Improvements

- issue: Static contract cannot prove shell exit behavior when `timeout` kills a child (noted as TSGR-4.3 gap in test-design checkpoints).
  improvement: Either add a documented gatekeeper manual check, a stubbed `timeout`/fake `godot` integration test, or accept the gap explicitly in the spec with a follow-up ID.
  expected_benefit: Clear boundary between proven runner shape and unproven signal semantics.

### Keep / Reinforce

- practice: Python phase in `ci/scripts/run_tests.sh` delegates to `.lefthook/scripts/py-tests.sh` (TSGR-3 DRY) so pre-push and full suite stay aligned.
  reason: One resolver path for `.venv` / `uv run` / `python3` fallback.

- practice: Authoritative `verify_tsgr_runner_contract.sh` plus Test Breaker pytest mirrors (cwd independence, hollow verifier, key grep mirrors).
  reason: Defense-in-depth without requiring fragile full-Godot crash harnesses for every orchestration rule.

---

## [attack_telegraph_system] — Death must preempt telegraph state; asymmetric family tests need explicit AC wording

*Completed: 2026-04-06*

### Learnings

- category: architecture
  insight: Controllers that combine telegraph timers, animation completion, and a terminal lifecycle (e.g. Death) need explicit precedence: entering Death must clear telegraph flags and cancel hold/wall-clock paths so Death is never deferred behind telegraph logic, and one-shot timer callbacks must tolerate cancellation after telegraph fields are cleared.
  impact: GDScript review caught ordering where telegraph could still run alongside or after Death; fix was to reset `_ranged_telegraph_*` and related state when taking the Death branch before collision disable / play.
  prevention: When adding interruptible phases, add a checklist item: “terminal state clears all in-progress phase timers and flags.”
  severity: high

- category: testing
  insight: Headless adversarial tests that count live projectile spawns or rely on `get_class()` on instanced roots can be unreliable (SceneTree phase, node type vs script name); source-level guarantees (e.g. re-entry guards, `CONNECT_ONE_SHOT`, substring checks with `# CHECKPOINT`) can prove the same invariants without a flaky runtime harness.
  impact: Test Breaker chose structure over spawn counting for duplicate `_on_telegraph_finished` / double `_begin_attack_cycle` cases.
  prevention: Prefer source contracts when runtime identity or tree phase is ambiguous; reserve runtime stress only for paths where the harness is proven stable.
  severity: medium

- category: process
  insight: “Works for all N enemy families” without a normative test depth per family forces gatekeepers to assume asymmetric coverage (full behavioral tests for some families, contract/export/wiring for stubs) unless the spec states it.
  impact: AC gatekeeper logged medium confidence on whether carapace/claw required T-ATS-04-style SceneTree tests.
  prevention: Spec or ticket should state parity expectations (full vs contract) when families are at different maturity levels.
  severity: medium

### Anti-Patterns

- description: Letting Death or other terminal transitions run while telegraph timers and flags remain active, so completion ordering or collision disable is wrong.
  detection_signal: Death mid-attack; telegraph `emit` or hold timer fires after `queue_free`; review comments on “telegraph vs Death ordering.”
  prevention: Clear telegraph state on the same code path that latches Death and guard timer callbacks with `if not _ranged_telegraph_active`.

- description: Asserting spawn counts or class identity in headless tests without validating that the instanced node matches the expected `class_name` / script type.
  detection_signal: `get_class()` != expected type; tests pass/fail depending on `SceneTree._initialize` ordering.
  prevention: Use documented source checks or assert on node path + script resource path.

### Prompt Patches

- agent: GDScript Reviewer Agent
  change: "For `EnemyAnimationController`/`AnimationPlayer`-driven flows: if telegraph uses timers or hold flags, verify that Death (or any irreversible despawn) clears those flags and cancels any pending telegraph semantics before collision disable and `play('Death')`, and that timer callbacks exit early if telegraph was cleared."
  reason: Prevents death-vs-telegraph ordering bugs that static tests often miss.

- agent: Test Breaker Agent
  change: "For duplicate-emission or double-entry adversarial cases on spawned gameplay nodes: if headless spawn counting or `get_class()` is unreliable, prefer source-level guards (`# CHECKPOINT` comments) and document the constraint in the checkpoint; do not block on a flaky runtime harness."
  reason: Matches ADV-ATS pattern and avoids false reds from tree phase quirks.

- agent: Spec Agent
  change: "When acceptance criteria say 'works for all N families' and some families are stub or minimal implementations, add a normative line: either require behavioral parity tests per family or explicitly allow contract tests (exports, script presence, wiring) for families without full combat."
  reason: Removes AC gatekeeper ambiguity and avoids scope creep late in the pipeline.

### Workflow Improvements

- issue: Workflow stage enum has no `IMPLEMENTATION_GAMEPLAY`; Test Breaker advanced to `IMPLEMENTATION_GENERALIST` with handoff to Gameplay Systems.
  improvement: Document in `agent_context/agents/readme.md` (or planner routing) a single canonical mapping: “telegraph / enemy attack implementation → gameplay systems” when the stage is generalist.
  expected_benefit: Fewer wrong-agent handoffs and fewer medium-confidence routing assumptions.

### Keep / Reinforce

- practice: ATS-2 wall-clock floor (min 0.3 s) enforced when the Attack clip ends early via hold timer + `maxf`/`max` on fallback timers, with adversarial tests for clamps.
  reason: Readable wind-up without hardcoding a single duration in all attack scripts.

- practice: Primary suite stays deterministic (no `await`/wall-clock in NF1); adversarial suite carries timing and stress cases.
  reason: Stable CI while still covering edge cases.

---

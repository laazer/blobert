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

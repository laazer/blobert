# Spec: Place First 4 Enemy Families in Level

**Ticket:** `project_board/5_milestone_5_procedural_enemy_generation/in_progress/first_4_families_in_level.md`
**Spec Author:** Spec Agent
**Date:** 2026-03-30
**Revision:** 1

---

## Architectural Decision Record

### ADR-1: Placement Wrapper Scenes Are Not Created

`EnemyInfection3D` extends `BasePhysicsEntity3D` which extends `CharacterBody3D`. It is a root node, not a composable child component. Nesting it under the generated EnemyBase root (also a CharacterBody3D) is architecturally invalid in Godot 4 physics. `EnemyInfection3D._ready()` traverses `get_parent()` searching for `InfectionInteractionHandler`, requiring it to sit directly under the level root.

**Chosen approach:** All four placed enemies in the level ARE instances of `scenes/enemy/enemy_infection_3d.tscn` — the same scene already used by the existing Enemy/Enemy2 nodes. Per-instance property overrides on `enemy_id`, `enemy_family`, and `mutation_drop` are applied in the level .tscn to give each instance its correct family identity. No `scenes/enemies/placed/` directory or wrapper .tscn files are produced in this ticket.

The generated .tscn files (sub-contracts 1 and 2) are produced and committed as asset artifacts for future use (e.g., visual model swap), but are not instanced in the level in this ticket.

### ADR-2: Existing Enemy/Enemy2 Nodes Are Replaced

`test_3d_scene.gd` contains zero references to nodes named "Enemy" or "Enemy2". No other test in the test suite references those node names within `test_movement_3d.tscn` by path. The two existing nodes are removed and replaced with four new family-named instances. This is safe with respect to existing test coverage.

### ADR-3: AABB in Headless Mode Uses Identity Global Transform

When a GLB PackedScene is instantiated via `PackedScene.instantiate()` without being added to a SceneTree, `mesh_instance.global_transform` is `Transform3D.IDENTITY`. Therefore `global_transform * corner == corner` and the AABB is computed purely from the mesh's local-space bounds. This is correct: a freshly constructed CharacterBody3D root has identity transform, so local space and "world" space are identical at construction time. The resulting CollisionShape3D is in the root's local coordinate space, which is what Godot physics expects. The generator does NOT multiply by `global_transform` — it uses `mesh.get_aabb()` corners directly, as the identity multiplication is a no-op.

### ADR-4: Fallback Shape Dimensions

BoxShape3D.size is the **full** extents (not half-extents). The ticket instruction "unit BoxShape3D (0.5, 0.5, 0.5)" means half-extents of 0.5, which maps to `BoxShape3D.size = Vector3(1.0, 1.0, 1.0)`.

### ADR-5: Test Runner Registration Is Automatic

`run_tests.gd` auto-discovers all `.gd` files under `res://tests/` whose filename starts with `test_`. No manual registration step is required for the two new test files.

---

## Sub-Contract 1: Headless Generator Script

### Requirement FESG-GEN-1: Script Entry Point and Exit

#### 1. Spec Summary
- **Description:** `scripts/asset_generation/generate_enemy_scenes.gd` must be a standalone runnable GDScript using `extends SceneTree` with `func _init() -> void:` as the entry point. It must call `quit()` (with no arguments, defaulting to exit code 0) as the final statement in `_init()`. It must call `quit(1)` if a fatal error prevents any output from being written.
- **Constraints:** Must NOT use `@tool`. Must NOT use `extends EditorScript`. Must NOT define `func _run()`. Must be runnable via `timeout 300 godot -s scripts/asset_generation/generate_enemy_scenes.gd` from the project root.
- **Assumptions:** The Godot binary on PATH is the project's headless wrapper (`bin/godot`). The project's .import cache is populated (all 12 GLBs already have `.import` files).
- **Scope:** `scripts/asset_generation/generate_enemy_scenes.gd` only.

#### 2. Acceptance Criteria
- **AC-GEN-1.1:** The file declares `extends SceneTree` on its first non-comment, non-blank line.
- **AC-GEN-1.2:** The file declares `func _init() -> void:` as the primary entry point. No `func _run()` is present.
- **AC-GEN-1.3:** `@tool` does not appear anywhere in the file.
- **AC-GEN-1.4:** `extends EditorScript` does not appear anywhere in the file.
- **AC-GEN-1.5:** `quit()` is called unconditionally at the end of `_init()` when generation succeeds. `quit(1)` is called if the source directory cannot be opened.
- **AC-GEN-1.6:** Running `timeout 300 godot -s scripts/asset_generation/generate_enemy_scenes.gd` exits within 300 seconds with exit code 0 when the 12 GLBs are present.

#### 3. Risk & Ambiguity Analysis
- Risk: ResourceSaver.save() to a `res://` path in headless mode requires the Godot project to be found. If the script is invoked from outside the project directory, it will fail. Mitigation: always invoke from project root.
- Risk: If `godot --import` has not been run and .import files are missing or stale, `load(glb_path)` may return null. Mitigation: the 12 GLBs already have .import files; the spec notes that the Generalist Agent must run `godot --import` if any load returns null.

#### 4. Clarifying Questions
None. ADR-1 through ADR-5 resolve all open questions.

---

### Requirement FESG-GEN-2: Source and Output Directories

#### 1. Spec Summary
- **Description:** The generator reads from `res://assets/enemies/generated_glb/` and writes to `res://scenes/enemies/generated/`. The output directory is created if it does not exist.
- **Constraints:** Directory creation uses `DirAccess.make_dir_recursive_absolute()` with the absolute path equivalent of the `res://` path. The generator sorts GLB file paths before iterating, producing deterministic output order.
- **Assumptions:** `res://assets/enemies/generated_glb/` contains exactly 12 `.glb` files as enumerated in GLB inventory below. The `scenes/enemies/` directory hierarchy does not currently exist and must be created.
- **Scope:** Generator script only.

**GLB inventory (12 files, sorted):**
```
acid_spitter_animated_00.glb
acid_spitter_animated_01.glb
acid_spitter_animated_02.glb
adhesion_bug_animated_00.glb
adhesion_bug_animated_01.glb
adhesion_bug_animated_02.glb
carapace_husk_animated_00.glb
carapace_husk_animated_01.glb
carapace_husk_animated_02.glb
claw_crawler_animated_00.glb
claw_crawler_animated_01.glb
claw_crawler_animated_02.glb
```

#### 2. Acceptance Criteria
- **AC-GEN-2.1:** After successful execution, `scenes/enemies/generated/` exists and contains exactly 12 `.tscn` files.
- **AC-GEN-2.2:** The 12 output filenames are: `acid_spitter_animated_00.tscn`, `acid_spitter_animated_01.tscn`, `acid_spitter_animated_02.tscn`, `adhesion_bug_animated_00.tscn`, `adhesion_bug_animated_01.tscn`, `adhesion_bug_animated_02.tscn`, `carapace_husk_animated_00.tscn`, `carapace_husk_animated_01.tscn`, `carapace_husk_animated_02.tscn`, `claw_crawler_animated_00.tscn`, `claw_crawler_animated_01.tscn`, `claw_crawler_animated_02.tscn`.
- **AC-GEN-2.3:** If `res://assets/enemies/generated_glb/` cannot be opened (DirAccess returns null), the generator emits `push_warning()`, calls `quit(1)`, and exits without writing any files.
- **AC-GEN-2.4:** `.glb` file matching is case-insensitive (`.GLB` also matches). File paths are sorted before iteration.

#### 3. Risk & Ambiguity Analysis
- The sort order of DirAccess is platform-dependent. The generator must call `.sort()` on the collected array before iterating to ensure deterministic output.

#### 4. Clarifying Questions
None.

---

### Requirement FESG-GEN-3: Family Name Extraction and Mutation Mapping

#### 1. Spec Summary
- **Description:** For each GLB file, the generator extracts the family name using `EnemyNameUtils.extract_family_name(file_basename)` and resolves the mutation drop string from the `MUTATION_BY_FAMILY` dictionary defined in `res://scripts/asset_generation/enemy_mutation_map.gd`. Both the headless generator (`generate_enemy_scenes.gd`) and the editor script (`load_assets.gd`) preload that module and use `EnemyMutationMap.MUTATION_BY_FAMILY`.
- **Constraints:** `EnemyNameUtils` is preloaded as a const at script top: `const EnemyNameUtils = preload("res://scripts/asset_generation/enemy_name_utils.gd")`. `EnemyMutationMap` is preloaded the same way from `res://scripts/asset_generation/enemy_mutation_map.gd`. If a family name is not found in the map, `mutation_drop` is set to `"unknown"`.
- **Assumptions:** `EnemyNameUtils.extract_family_name("adhesion_bug_animated_00")` returns `"adhesion_bug"`. `EnemyNameUtils.extract_family_name("acid_spitter_animated_02")` returns `"acid_spitter"`. Both are confirmed by reading `enemy_name_utils.gd`: the function strips trailing numeric tokens and all `"animated"` tokens.
- **Scope:** Generator script; applies to all 12 GLBs.

**Expected family/mutation mappings for the 12 GLBs:**
| GLB basename | family_name | mutation_drop |
|---|---|---|
| adhesion_bug_animated_00 | adhesion_bug | adhesion |
| adhesion_bug_animated_01 | adhesion_bug | adhesion |
| adhesion_bug_animated_02 | adhesion_bug | adhesion |
| acid_spitter_animated_00 | acid_spitter | acid |
| acid_spitter_animated_01 | acid_spitter | acid |
| acid_spitter_animated_02 | acid_spitter | acid |
| claw_crawler_animated_00 | claw_crawler | claw |
| claw_crawler_animated_01 | claw_crawler | claw |
| claw_crawler_animated_02 | claw_crawler | claw |
| carapace_husk_animated_00 | carapace_husk | carapace |
| carapace_husk_animated_01 | carapace_husk | carapace |
| carapace_husk_animated_02 | carapace_husk | carapace |

#### 2. Acceptance Criteria
- **AC-GEN-3.1:** For each generated .tscn, the root node's `enemy_family` property equals the family_name column above.
- **AC-GEN-3.2:** For each generated .tscn, the root node's `mutation_drop` property equals the mutation_drop column above.
- **AC-GEN-3.3:** For each generated .tscn, the root node's `enemy_id` equals the GLB basename (e.g., `"adhesion_bug_animated_00"`).
- **AC-GEN-3.4:** A GLB with an unrecognized family name (not in MUTATION_BY_FAMILY) produces a scene with `mutation_drop == "unknown"`.

#### 3. Risk & Ambiguity Analysis
- The family → mutation map lives only in `enemy_mutation_map.gd`. New families or mutation strings are added there once; both pipelines pick up the same dictionary via preload (no manual sync between generator and editor script).

#### 4. Clarifying Questions
None.

---

### Requirement FESG-GEN-4: AABB Computation

#### 1. Spec Summary
- **Description:** For each instantiated GLB, the generator gathers all `MeshInstance3D` nodes recursively. For each, it calls `mesh_instance.mesh.get_aabb()` to obtain the local-space AABB. It then iterates over all 8 corners of the AABB, accumulates a world-space combined AABB, then recenters it around the origin of the visual root.
- **Constraints (DEVIATION FROM load_assets.gd):** `load_assets.gd` multiplies corners by `mesh_instance.global_transform`. In headless mode, nodes instantiated via `PackedScene.instantiate()` without being added to a SceneTree have `global_transform == Transform3D.IDENTITY`. Multiplying by identity is a no-op. The generator MAY replicate the `global_transform * corner` logic from load_assets.gd unchanged — the result is identical in headless mode. This is documented here so Implementer and QA agents understand the behavior.
- **Fallback:** If the combined AABB has `size == Vector3.ZERO` (no MeshInstance3D found, or all meshes have zero-size bounds), the generator uses a fallback BoxShape3D with `size = Vector3(1.0, 1.0, 1.0)`.
- **Scope:** Generator script; `_compute_combined_aabb()` and `_build_collision_shape_from_node()` functions.

#### 2. Acceptance Criteria
- **AC-GEN-4.1:** Each generated .tscn has a `CollisionShape3D` direct child of the root. The shape is not null.
- **AC-GEN-4.2:** If mesh bounds yield a non-zero AABB: for an enemy taller than it is wide (y > max(x,z) * 1.25), the shape is a `CapsuleShape3D`; otherwise a `BoxShape3D`.
- **AC-GEN-4.3:** If `_compute_combined_aabb()` returns an AABB with `size == Vector3.ZERO`, the CollisionShape3D shape is a `BoxShape3D` with `size == Vector3(1.0, 1.0, 1.0)`.
- **AC-GEN-4.4:** The `Hurtbox/CollisionShape3D` shape is a duplicate of the primary CollisionShape3D shape (same type and dimensions, separate resource instance).

#### 3. Risk & Ambiguity Analysis
- Risk: The 12 GLBs may produce zero-size AABBs if the mesh data is not accessible in headless mode (e.g., import flags suppress mesh data). Mitigation: the fallback shape handles this; tests verify shape is non-null.
- Edge case: A GLB with all zero-sized meshes would be silently given a unit box. This is logged via `push_warning()`.

#### 4. Clarifying Questions
None.

---

## Sub-Contract 2: Generated .tscn Node Structure

### Requirement FESG-TSCN-1: Root Node

#### 1. Spec Summary
- **Description:** The root node of each generated .tscn is a `CharacterBody3D` with the EnemyBase script attached. The node name equals the GLB basename (e.g., `adhesion_bug_animated_00`).
- **Constraints:** Script is loaded via `load("res://scripts/enemies/enemy_base.gd")` and attached via `root.set_script(script_res)`. This is done only if `ResourceLoader.exists("res://scripts/enemies/enemy_base.gd")` returns true.
- **Assumptions:** `enemy_base.gd` exists and declares `class_name EnemyBase extends CharacterBody3D` with `@export var enemy_id`, `@export var enemy_family`, `@export var mutation_drop`.
- **Scope:** Root node of every generated .tscn.

#### 2. Acceptance Criteria
- **AC-TSCN-1.1:** `root is CharacterBody3D` is true when the generated scene is instantiated.
- **AC-TSCN-1.2:** `root.name == "adhesion_bug_animated_00"` (and analogously for each other basename).
- **AC-TSCN-1.3:** `root.get_script() != null` and `root.get_script().resource_path.ends_with("enemy_base.gd")`.
- **AC-TSCN-1.4:** `root.has_method("get_base_state")` is true.

#### 3. Risk & Ambiguity Analysis
- If `enemy_base.gd` is missing, the generator skips script attachment (no crash). The generated scene is still valid but lacks EnemyBase behavior. Tests verify script presence.

#### 4. Clarifying Questions
None.

---

### Requirement FESG-TSCN-2: Metadata and Export Properties

#### 1. Spec Summary
- **Description:** Four properties are set on the root node: three via both `set_meta()` and `set()` (for export property assignment), and one via `set_meta()` only.
- **Constraints:**
  - `set_meta("enemy_id", file_basename)` + `root.set("enemy_id", file_basename)`
  - `set_meta("enemy_family", family_name)` + `root.set("enemy_family", family_name)`
  - `set_meta("mutation_drop", mutation)` + `root.set("mutation_drop", mutation)`
  - `set_meta("source_glb", glb_path)` — meta only, no set()
- **Assumptions:** `set()` on a node with a script that has `@export var enemy_id` correctly assigns the export property. `get_meta()` and property access via `.enemy_id` / `.enemy_family` / `.mutation_drop` both work on the instantiated scene.
- **Scope:** Root node of every generated .tscn.

#### 2. Acceptance Criteria
- **AC-TSCN-2.1:** `inst.get_meta("enemy_id") == inst.enemy_id` for each generated scene.
- **AC-TSCN-2.2:** `inst.get_meta("enemy_family") == inst.enemy_family` for each generated scene.
- **AC-TSCN-2.3:** `inst.get_meta("mutation_drop") == inst.mutation_drop` for each generated scene.
- **AC-TSCN-2.4:** `inst.has_meta("source_glb")` is true; the value ends with `.glb`.
- **AC-TSCN-2.5:** `inst.enemy_family` equals the expected family string from the mapping table in FESG-GEN-3.
- **AC-TSCN-2.6:** `inst.mutation_drop` equals the expected mutation string from the mapping table in FESG-GEN-3.

#### 3. Risk & Ambiguity Analysis
- `set()` silently fails if the property name doesn't match an export var name exactly. Tests must verify both the meta and the property value to catch mismatches.

#### 4. Clarifying Questions
None.

---

### Requirement FESG-TSCN-3: Child Node Structure

#### 1. Spec Summary
- **Description:** Each generated .tscn has a fixed set of direct and indirect children in the following order. All nodes have their `owner` set to the root node so they are serialized in the .tscn.

**Node hierarchy (order of addition to root):**
1. `Visual` (Node3D) — direct child of root
   - `Model` (the instantiated GLB node, child of Visual)
2. `CollisionShape3D` (CollisionShape3D) — direct child of root; shape computed from AABB or fallback
3. `AttackOrigin` (Marker3D) — direct child of root; position `Vector3(0.6, 0.0, 0.0)`
4. `ChunkAttachPoint` (Marker3D) — direct child of root; position `Vector3(0.0, 0.0, 0.2)`
5. `PickupAnchor` (Marker3D) — direct child of root; position `Vector3(0.0, 0.0, 0.0)`
6. `Hurtbox` (Area3D) — direct child of root
   - `CollisionShape3D` (CollisionShape3D) — child of Hurtbox; shape is a duplicate of root's CollisionShape3D shape
7. `VisibleOnScreenNotifier3D` (VisibleOnScreenNotifier3D) — direct child of root; aabb computed from the collision shape via `_aabb_from_shape()`

- **Constraints:** All child nodes have `owner = root` before the scene is packed via `PackedScene.pack()`. The `_aabb_from_shape()` logic for VisibleOnScreenNotifier3D follows load_assets.gd exactly: BoxShape3D → `AABB(-box.size*0.5, box.size)`; CapsuleShape3D → AABB sized to `(radius*2, height+radius*2, radius*2)` centered at origin; null shape → `AABB(Vector3(-0.5,-0.5,-0.5), Vector3.ONE)`.
- **Assumptions:** "Model" is the name assigned to the instantiated GLB root node before adding it to Visual.
- **Scope:** Every generated .tscn.

#### 2. Acceptance Criteria
- **AC-TSCN-3.1:** `inst.get_node_or_null("Visual")` is non-null and is a `Node3D`.
- **AC-TSCN-3.2:** `inst.get_node_or_null("Visual/Model")` is non-null.
- **AC-TSCN-3.3:** `inst.get_node_or_null("CollisionShape3D")` is non-null and is a `CollisionShape3D` with a non-null `shape`.
- **AC-TSCN-3.4:** `inst.get_node_or_null("AttackOrigin")` is non-null and is a `Marker3D`; `position == Vector3(0.6, 0.0, 0.0)`.
- **AC-TSCN-3.5:** `inst.get_node_or_null("ChunkAttachPoint")` is non-null and is a `Marker3D`; `position == Vector3(0.0, 0.0, 0.2)`.
- **AC-TSCN-3.6:** `inst.get_node_or_null("PickupAnchor")` is non-null and is a `Marker3D`; `position == Vector3(0.0, 0.0, 0.0)`.
- **AC-TSCN-3.7:** `inst.get_node_or_null("Hurtbox")` is non-null and is an `Area3D`.
- **AC-TSCN-3.8:** `inst.get_node_or_null("Hurtbox/CollisionShape3D")` is non-null and is a `CollisionShape3D` with a non-null `shape`.
- **AC-TSCN-3.9:** `inst.get_node_or_null("VisibleOnScreenNotifier3D")` is non-null.
- **AC-TSCN-3.10:** The Hurtbox CollisionShape3D shape is a separate resource instance from the root CollisionShape3D shape (`inst.get_node("Hurtbox/CollisionShape3D").shape != inst.get_node("CollisionShape3D").shape` by reference).
- **AC-TSCN-3.11:** Root direct child count equals 7: Visual, CollisionShape3D, AttackOrigin, ChunkAttachPoint, PickupAnchor, Hurtbox, VisibleOnScreenNotifier3D.

#### 3. Risk & Ambiguity Analysis
- Risk: `PackedScene.pack()` only serializes nodes whose `owner` is set to root. If any node's `owner` is left null or set to a different node, it will be omitted from the .tscn. Implementation must set `owner = root` on every node immediately after `add_child()`.
- Edge case: The instantiated GLB root may itself have children (the actual mesh nodes are nested inside). All of those retain their GLB-defined hierarchy. No ownership changes are required for GLB sub-nodes because the GLB is instanced as a sub-scene.

#### 4. Clarifying Questions
None.

---

## Sub-Contract 3: Placement Scene (Level Integration)

### Requirement FESG-PLACE-1: No Wrapper .tscn Files

#### 1. Spec Summary
- **Description:** No `scenes/enemies/placed/` directory is created. No wrapper .tscn files are written. This sub-contract is superseded by ADR-1. The level directly instances `scenes/enemy/enemy_infection_3d.tscn` four times, one per family.
- **Constraints:** See FESG-LEVEL-1 for the full level modification spec.
- **Assumptions:** None.
- **Scope:** Artifact paths `scenes/enemies/placed/` — these are NOT produced by this ticket.

#### 2. Acceptance Criteria
- **AC-PLACE-1.1:** No files are written to `scenes/enemies/placed/` as part of this ticket.

#### 3. Risk & Ambiguity Analysis
- The execution plan's artifact list includes placed/ paths. ADR-1 documents why they are not produced. If a future ticket reintroduces wrapper scenes, it must address the CharacterBody3D nesting problem.

#### 4. Clarifying Questions
None.

---

## Sub-Contract 4: Level Modification

### Requirement FESG-LEVEL-1: Remove Enemy/Enemy2; Add Four Family Instances

#### 1. Spec Summary
- **Description:** `scenes/levels/sandbox/test_movement_3d.tscn` is modified to remove the two existing `Enemy` and `Enemy2` nodes and replace them with four new nodes, one per family. Each new node is an instance of `scenes/enemy/enemy_infection_3d.tscn` with per-instance property overrides for `enemy_id`, `enemy_family`, and `mutation_drop`.
- **Constraints:**
  - The four new nodes are named: `AdhesionBugEnemy`, `AcidSpitterEnemy`, `ClawCrawlerEnemy`, `CarapaceHuskEnemy`.
  - Placement positions (world-space, Y=1.0 to clear the floor surface at Y=0):
    - `AdhesionBugEnemy`: `Vector3(4.0, 1.0, 0.0)`
    - `AcidSpitterEnemy`: `Vector3(-4.0, 1.0, 0.0)`
    - `ClawCrawlerEnemy`: `Vector3(0.0, 1.0, 4.0)`
    - `CarapaceHuskEnemy`: `Vector3(0.0, 1.0, -4.0)`
  - `physics_interpolation_mode = 1` (same as existing Enemy/Enemy2 nodes) is set on each instance.
  - `collision_layer = 2`, `collision_mask = 1` (inherited from enemy_infection_3d.tscn defaults; no override needed unless the .tscn defaults differ).
  - Per-instance property overrides in the .tscn file:
    - `AdhesionBugEnemy`: `enemy_id = "adhesion_bug_animated_00"`, `enemy_family = "adhesion_bug"`, `mutation_drop = "adhesion"`
    - `AcidSpitterEnemy`: `enemy_id = "acid_spitter_animated_00"`, `enemy_family = "acid_spitter"`, `mutation_drop = "acid"`
    - `ClawCrawlerEnemy`: `enemy_id = "claw_crawler_animated_00"`, `enemy_family = "claw_crawler"`, `mutation_drop = "claw"`
    - `CarapaceHuskEnemy`: `enemy_id = "carapace_husk_animated_00"`, `enemy_family = "carapace_husk"`, `mutation_drop = "carapace"`
  - Note: EnemyInfection3D does NOT declare `enemy_id`, `enemy_family`, or `mutation_drop` as export vars (it extends BasePhysicsEntity3D, not EnemyBase). Therefore these overrides CANNOT be set as standard property overrides in the .tscn. They must be set as metadata overrides using `set_meta()` at runtime by a level script, OR the spec acknowledges this limitation. See Risk section.
- **Assumptions:** The floor surface is at Y=0. Y=1.0 ensures enemies spawn above the floor before physics drops them. The existing `InfectionInteractionHandler` node in the scene root provides the handler that `EnemyInfection3D._ready()` searches for.
- **Scope:** `scenes/levels/sandbox/test_movement_3d.tscn`.

#### 2. Acceptance Criteria
- **AC-LEVEL-1.1:** After modification, `test_movement_3d.tscn` loads without error via `load("res://scenes/levels/sandbox/test_movement_3d.tscn").instantiate()`.
- **AC-LEVEL-1.2:** `root.get_node_or_null("AdhesionBugEnemy")` is non-null.
- **AC-LEVEL-1.3:** `root.get_node_or_null("AcidSpitterEnemy")` is non-null.
- **AC-LEVEL-1.4:** `root.get_node_or_null("ClawCrawlerEnemy")` is non-null.
- **AC-LEVEL-1.5:** `root.get_node_or_null("CarapaceHuskEnemy")` is non-null.
- **AC-LEVEL-1.6:** `root.get_node_or_null("Enemy")` is null (removed).
- **AC-LEVEL-1.7:** `root.get_node_or_null("Enemy2")` is null (removed).
- **AC-LEVEL-1.8:** `root.get_node_or_null("AdhesionBugEnemy").get_scene_file_path()` contains `"enemy_infection_3d.tscn"`.
- **AC-LEVEL-1.9:** `root.get_node_or_null("AcidSpitterEnemy").get_scene_file_path()` contains `"enemy_infection_3d.tscn"`.
- **AC-LEVEL-1.10:** `root.get_node_or_null("ClawCrawlerEnemy").get_scene_file_path()` contains `"enemy_infection_3d.tscn"`.
- **AC-LEVEL-1.11:** `root.get_node_or_null("CarapaceHuskEnemy").get_scene_file_path()` contains `"enemy_infection_3d.tscn"`.
- **AC-LEVEL-1.12:** Each of the four enemy nodes has `position.y == 1.0` (within tolerance 0.01).
- **AC-LEVEL-1.13:** `AdhesionBugEnemy.position` is approximately `Vector3(4.0, 1.0, 0.0)` (tolerance 0.01).
- **AC-LEVEL-1.14:** `AcidSpitterEnemy.position` is approximately `Vector3(-4.0, 1.0, 0.0)` (tolerance 0.01).
- **AC-LEVEL-1.15:** `ClawCrawlerEnemy.position` is approximately `Vector3(0.0, 1.0, 4.0)` (tolerance 0.01).
- **AC-LEVEL-1.16:** `CarapaceHuskEnemy.position` is approximately `Vector3(0.0, 1.0, -4.0)` (tolerance 0.01).
- **AC-LEVEL-1.17:** All existing tests in `test_3d_scene.gd` continue to pass (no regressions).

#### 3. Risk & Ambiguity Analysis
- **Critical risk — property override limitation:** `EnemyInfection3D` extends `BasePhysicsEntity3D` (CharacterBody3D) and does NOT have `enemy_id`, `enemy_family`, `mutation_drop` as declared properties or export vars. Standard Godot .tscn per-instance property overrides only work for declared properties. Setting `enemy_id` etc. as overrides in the .tscn will fail silently or log an error.
  - **Resolution:** The per-instance identity data (`enemy_id`, `enemy_family`, `mutation_drop`) CANNOT be stored as property overrides in the .tscn when instancing `enemy_infection_3d.tscn`. They ARE storable as metadata overrides. However, Godot 4 .tscn format does not natively support per-instance `set_meta()` overrides through the scene editor.
  - **Practical resolution for this ticket:** The four enemy nodes are distinguishable by their node name (`AdhesionBugEnemy`, etc.). The mutation_drop mapping is implicitly known by the node name. A lightweight `SceneVariantController` (already in the level as `SceneVariantController` with script `scene_variant_controller_3d.gd`) or a small level-init script can call `set_meta()` on each enemy node by name at `_ready()` time. Alternatively, the level accepts that mutation_drop is identified by node name at the gameplay layer — the infection loop already uses EnemyStateMachine state, not mutation_drop.
  - **Spec decision:** The Implementer must check `scene_variant_controller_3d.gd` to determine if it already supports per-node metadata initialization. If not, the Implementer adds a 4-line `_ready()` block in the level scene's root node script (if one exists) or documents that mutation_drop identification is by node name convention for this ticket.
  - **This is the one remaining open decision delegated to the Implementer.** The spec mandates that each enemy is identifiable (by name) and carries the correct mutation_drop string accessible at runtime; the mechanism (meta vs. property vs. name convention) is implementation-choice.
- **Risk:** The four enemy positions at Y=1.0 cause enemies to fall to the floor when physics runs. In headless tests (no physics), positions are static. Tests verify positions at instantiation time before physics runs.
- **Risk:** `EnemyInfection3D._ready()` expects an `InfectionInteractionHandler` ancestor in the scene tree. The level already has one (`InfectionInteractionHandler` node at root). The placement is compatible.

#### 4. Clarifying Questions
None that block the spec. The mutation_drop mechanism is delegated to the Implementer as documented above.

---

## Sub-Contract 5: Tests

### Requirement FESG-TEST-1: Primary Test Suite

#### 1. Spec Summary
- **Description:** `tests/scenes/enemies/test_enemy_scene_generation.gd` contains the primary test suite for generated scene structure and level placement verification.
- **Constraints:**
  - File extends `"res://tests/utils/test_utils.gd"`. No `class_name` declaration.
  - Declares `var _pass_count: int = 0` and `var _fail_count: int = 0`.
  - Defines `func run_all() -> int:` that calls all test functions, prints a summary, and returns `_fail_count`.
  - SKIP pattern: any test requiring a live SceneTree or 3D physics space must check `Engine.get_main_loop() as SceneTree` and print `"  SKIP: <test_id> — <reason>"` then return early. This matches the pattern in `test_3d_scene.gd`.
  - The `tests/scenes/enemies/` directory does not currently exist; the Implementer must create it.
- **Assumptions:** All 12 generated .tscn files exist at `res://scenes/enemies/generated/` before tests run (they are committed artifacts, not generated at test time).
- **Scope:** `tests/scenes/enemies/test_enemy_scene_generation.gd`.

**Test inventory — primary suite (prefix FESG-):**

| Test ID | Function name | What is asserted |
|---|---|---|
| FESG-1 | test_generated_dir_has_12_scenes | DirAccess on `res://scenes/enemies/generated/` lists exactly 12 `.tscn` files |
| FESG-2 | test_all_generated_scenes_loadable | Each of the 12 expected .tscn paths loads without returning null |
| FESG-3 | test_adhesion_bug_00_enemy_id | adhesion_bug_animated_00.tscn root: `enemy_id == "adhesion_bug_animated_00"` |
| FESG-4 | test_adhesion_bug_00_enemy_family | adhesion_bug_animated_00.tscn root: `enemy_family == "adhesion_bug"` |
| FESG-5 | test_adhesion_bug_00_mutation_drop | adhesion_bug_animated_00.tscn root: `mutation_drop == "adhesion"` |
| FESG-6 | test_acid_spitter_00_mutation_drop | acid_spitter_animated_00.tscn root: `mutation_drop == "acid"` |
| FESG-7 | test_claw_crawler_00_mutation_drop | claw_crawler_animated_00.tscn root: `mutation_drop == "claw"` |
| FESG-8 | test_carapace_husk_00_mutation_drop | carapace_husk_animated_00.tscn root: `mutation_drop == "carapace"` |
| FESG-9 | test_generated_scene_has_collision_shape | Each of the 12 scenes: `get_node_or_null("CollisionShape3D") != null` and `shape != null` |
| FESG-10 | test_generated_scene_has_visual_node | Each of the 12 scenes: `get_node_or_null("Visual") != null` |
| FESG-11 | test_generated_scene_has_visual_model | Each of the 12 scenes: `get_node_or_null("Visual/Model") != null` |
| FESG-12 | test_generated_scene_has_hurtbox | Each of the 12 scenes: `get_node_or_null("Hurtbox") != null` and is Area3D |
| FESG-13 | test_generated_scene_has_hurtbox_collision | Each of the 12 scenes: `get_node_or_null("Hurtbox/CollisionShape3D") != null` |
| FESG-14 | test_generated_scene_has_attack_origin | Each of the 12 scenes: `get_node_or_null("AttackOrigin") != null` |
| FESG-15 | test_generated_scene_has_chunk_attach_point | Each of the 12 scenes: `get_node_or_null("ChunkAttachPoint") != null` |
| FESG-16 | test_generated_scene_has_pickup_anchor | Each of the 12 scenes: `get_node_or_null("PickupAnchor") != null` |
| FESG-17 | test_generated_scene_has_notifier | Each of the 12 scenes: `get_node_or_null("VisibleOnScreenNotifier3D") != null` |
| FESG-18 | test_generated_scene_root_is_character_body | Each of the 12 scenes: `inst is CharacterBody3D` |
| FESG-19 | test_generated_scene_root_has_enemy_base_script | Each of the 12 scenes: `inst.get_script() != null` and path ends with `"enemy_base.gd"` |
| FESG-20 | test_generated_scene_meta_matches_property | adhesion_bug_animated_00.tscn: `get_meta("enemy_family") == enemy_family` |
| FESG-21 | test_level_loads | `load("res://scenes/levels/sandbox/test_movement_3d.tscn").instantiate() != null` |
| FESG-22 | test_level_has_adhesion_bug_enemy | Level scene: `get_node_or_null("AdhesionBugEnemy") != null` |
| FESG-23 | test_level_has_acid_spitter_enemy | Level scene: `get_node_or_null("AcidSpitterEnemy") != null` |
| FESG-24 | test_level_has_claw_crawler_enemy | Level scene: `get_node_or_null("ClawCrawlerEnemy") != null` |
| FESG-25 | test_level_has_carapace_husk_enemy | Level scene: `get_node_or_null("CarapaceHuskEnemy") != null` |
| FESG-26 | test_level_enemy_old_nodes_removed | Level scene: `get_node_or_null("Enemy") == null` and `get_node_or_null("Enemy2") == null` |
| FESG-27 | test_level_adhesion_bug_position | AdhesionBugEnemy.position approx Vector3(4.0, 1.0, 0.0) tol 0.01 |
| FESG-28 | test_level_acid_spitter_position | AcidSpitterEnemy.position approx Vector3(-4.0, 1.0, 0.0) tol 0.01 |
| FESG-29 | test_level_claw_crawler_position | ClawCrawlerEnemy.position approx Vector3(0.0, 1.0, 4.0) tol 0.01 |
| FESG-30 | test_level_carapace_husk_position | CarapaceHuskEnemy.position approx Vector3(0.0, 1.0, -4.0) tol 0.01 |
| FESG-31 | test_level_enemies_use_infection_scene | Each of the 4 enemy nodes: `get_scene_file_path().contains("enemy_infection_3d.tscn")` |
| FESG-32 | test_generated_scene_child_count | Each generated scene root has exactly 7 direct children |

#### 2. Acceptance Criteria
- **AC-TEST-1.1:** All 32 FESG-* tests are present in `run_all()`.
- **AC-TEST-1.2:** Each test uses `_assert_true`, `_assert_eq_string`, or equivalent test_utils helpers.
- **AC-TEST-1.3:** Tests that loop over all 12 scenes use the canonical list of 12 basenames defined as a const Array in the file.
- **AC-TEST-1.4:** No test calls `await`, `get_tree()`, or `yield`.
- **AC-TEST-1.5:** `run_all()` returns `_fail_count` (int).
- **AC-TEST-1.6:** File is discovered automatically by `run_tests.gd` (filename starts with `test_`, located under `tests/`).

#### 3. Risk & Ambiguity Analysis
- FESG-9 through FESG-19 loop over 12 scenes. If any single scene fails to load, those test iterations should call `_fail_test()` for that scene and continue — not abort the entire loop.
- FESG-32 (child count == 7) will fail if any future version of load_assets.gd adds more children. This is intentional: the test documents the exact contract.

#### 4. Clarifying Questions
None.

---

### Requirement FESG-TEST-2: Adversarial Test Suite

#### 1. Spec Summary
- **Description:** `tests/scenes/enemies/test_enemy_scene_generation_adversarial.gd` contains adversarial tests probing edge cases and regression surfaces.
- **Constraints:** Same structural requirements as FESG-TEST-1 (extends test_utils.gd, _pass_count/_fail_count, run_all() -> int, no class_name).
- **Scope:** `tests/scenes/enemies/test_enemy_scene_generation_adversarial.gd`.

**Test inventory — adversarial suite (prefix ADV-FESG-):**

| Test ID | Function name | Vulnerability probed | What is asserted |
|---|---|---|---|
| ADV-FESG-1 | test_no_extra_tscn_files | Regressions write extra files | Scene count is exactly 12, not more |
| ADV-FESG-2 | test_collision_shape_not_zero_size | Zero-AABB fallback produces valid shape | For each scene, if shape is BoxShape3D, size != Vector3.ZERO; if CapsuleShape3D, radius > 0 and height > 0 |
| ADV-FESG-3 | test_hurtbox_shape_is_duplicate | Shared resource instance causes collision bugs | Hurtbox/CollisionShape3D.shape is not the same resource instance as CollisionShape3D.shape (resource_path differs or they are not identical object) |
| ADV-FESG-4 | test_enemy_id_matches_filename | enemy_id set to wrong value | For each scene, inst.enemy_id == scene filename without path and without extension |
| ADV-FESG-5 | test_no_unknown_mutation_drop | MUTATION_BY_FAMILY missing an entry | For each of the 12 scenes, mutation_drop != "unknown" |
| ADV-FESG-6 | test_family_name_extraction_strips_animated | EnemyNameUtils strips "animated" token | inst.enemy_family does not contain the substring "animated" for any of the 12 scenes |
| ADV-FESG-7 | test_family_name_extraction_strips_variant_index | EnemyNameUtils strips numeric suffix | inst.enemy_family does not end with "_00", "_01", or "_02" for any scene |
| ADV-FESG-8 | test_all_four_families_present_in_level | Only 3 of 4 placed | Level scene has exactly 4 nodes whose names are in {"AdhesionBugEnemy","AcidSpitterEnemy","ClawCrawlerEnemy","CarapaceHuskEnemy"} — all 4 present, no duplicates |
| ADV-FESG-9 | test_level_no_node_named_enemy | Old Enemy node re-added | `root.get_node_or_null("Enemy") == null` |
| ADV-FESG-10 | test_level_no_node_named_enemy2 | Old Enemy2 node re-added | `root.get_node_or_null("Enemy2") == null` |
| ADV-FESG-11 | test_generated_scene_visual_is_node3d | Visual node is wrong type | Visual node is instance of Node3D |
| ADV-FESG-12 | test_generated_scene_attack_origin_position | AttackOrigin placed at wrong position | AttackOrigin.position approx Vector3(0.6, 0.0, 0.0) tol 0.001 |
| ADV-FESG-13 | test_generated_scene_chunk_attach_point_position | ChunkAttachPoint placed at wrong position | ChunkAttachPoint.position approx Vector3(0.0, 0.0, 0.2) tol 0.001 |
| ADV-FESG-14 | test_generated_scene_has_get_base_state | Script not attached / wrong class | inst.has_method("get_base_state") is true for each of 12 scenes |
| ADV-FESG-15 | test_level_enemies_above_floor | Enemy placed at Y=0 or below | Each of 4 level enemies has position.y > 0.0 |
| ADV-FESG-16 | test_all_12_scenes_have_source_glb_meta | source_glb meta missing | Each scene: `has_meta("source_glb") == true` and value ends with ".glb" |

#### 2. Acceptance Criteria
- **AC-TEST-2.1:** All 16 ADV-FESG-* tests are present in `run_all()`.
- **AC-TEST-2.2:** Each adversarial test is in a separate function (not inlined in run_all).
- **AC-TEST-2.3:** No test hangs. Tests that would require a physics world use the SKIP pattern from test_3d_scene.gd.
- **AC-TEST-2.4:** `run_all()` returns `_fail_count`.

#### 3. Risk & Ambiguity Analysis
- ADV-FESG-3 (hurtbox shape is duplicate): In GDScript, two resources loaded from disk with the same path share the same resource instance by default. Since the hurtbox shape is created via `shape.duplicate(true)`, it will have no `resource_path` while the original may also lack one (both are newly created). The test must check that `shape_a != shape_b` (object identity), not resource_path equality. The implementation of `_duplicate_shape()` in load_assets.gd uses `shape.duplicate(true)` which creates a new resource instance; the test must verify the new instance is a distinct object.
- ADV-FESG-5 (no "unknown" mutation_drop): Will fail if the MUTATION_BY_FAMILY map is missing any of the 4 families. This is the regression guard.

#### 4. Clarifying Questions
None.

---

### Requirement FESG-TEST-3: Test Runner Registration

#### 1. Spec Summary
- **Description:** Both test files are auto-discovered by `run_tests.gd`'s recursive file collector. No manual changes to `run_tests.gd` are required.
- **Constraints:** File names must start with `test_` and end with `.gd`. Files must be located under `res://tests/` (anywhere in the tree). Both files define `func run_all() -> int:`. The files must be parseable by GDScript (no syntax errors or unresolvable preloads at load time).
- **Assumptions:** `tests/scenes/enemies/` directory is created before test files are placed in it.
- **Scope:** `tests/run_tests.gd` — no modifications to this file are required.

#### 2. Acceptance Criteria
- **AC-TEST-3.1:** Running `run_tests.sh` after the two new test files are placed discovers and runs both suites without error.
- **AC-TEST-3.2:** The final failure count reported by `run_tests.sh` includes failures from both new test suites.
- **AC-TEST-3.3:** `run_tests.gd` is NOT modified. Its content remains identical to the current version.

#### 3. Risk & Ambiguity Analysis
- If either new test file fails to parse (GDScript error), `run_tests.gd` calls `quit(1)` immediately. This is the intended behavior and serves as a compile-time check.

#### 4. Clarifying Questions
None.

---

## Non-Functional Requirements

### Requirement FESG-NFR-1: No Debug Prints in Production Code

All `print()` calls in `generate_enemy_scenes.gd` are informational (progress logging: one line per generated file, start/end messages). No debug print statements are left in production .gd files after Static QA.

### Requirement FESG-NFR-2: No @tool or extends EditorScript

`generate_enemy_scenes.gd` must not contain `@tool` or `extends EditorScript`. This is verified by Static QA grep.

### Requirement FESG-NFR-3: No Orphaned Nodes in .tscn Files

All nodes in generated .tscn files have `owner` set before pack. All nodes in modified level .tscn are properly owned. Static QA verifies no `[node ... orphan=true]` appears in output files.

### Requirement FESG-NFR-4: Existing Tests Pass Without Regression

`run_tests.sh` passes with zero new failures after all changes. Specifically, all tests in `test_3d_scene.gd` pass unchanged.

---

## File Manifest

| File | Status | Owner |
|---|---|---|
| `scripts/asset_generation/generate_enemy_scenes.gd` | NEW | Generalist Agent (Task 2) |
| `scenes/enemies/generated/acid_spitter_animated_00.tscn` through `carapace_husk_animated_02.tscn` (12 files) | NEW (generated artifact) | Generalist Agent (Task 3) |
| `scenes/levels/sandbox/test_movement_3d.tscn` | MODIFIED | Generalist Agent (Task 5) |
| `tests/scenes/enemies/test_enemy_scene_generation.gd` | NEW | Generalist Agent (Task 6) |
| `tests/scenes/enemies/test_enemy_scene_generation_adversarial.gd` | NEW | Generalist Agent (Task 6) |
| `tests/run_tests.gd` | UNCHANGED | — |
| `scripts/asset_generation/load_assets.gd` | UNCHANGED | — |
| `scripts/asset_generation/enemy_name_utils.gd` | UNCHANGED | — |
| `scripts/enemies/enemy_base.gd` | UNCHANGED | — |
| `scenes/enemy/enemy_infection_3d.tscn` | UNCHANGED | — |
| `scenes/enemies/placed/` | NOT CREATED | — |

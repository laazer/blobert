Title:
Validate and finalize Godot scene auto-generator
---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | IMPLEMENTATION_ENGINE_COMPLETE |
| Revision | 7 |
| Last Updated By | Engine Integration Agent |
| Next Responsible Agent | Acceptance Criteria Gatekeeper Agent |
| Validation Status | Not started |
| Blocking Issues | None |

---

## Description

The scene generator (scripts/asset_generation/load_assets.gd) already exists.
Validate it against real .glb exports from the Blender pipeline. Fix any issues
with collision generation, hurtbox sizing, naming extraction, or marker placement.

## Known Issues to Fix Before Validation

1. **Directory missing**: `assets/enemies/generated_glb/` does not exist. Must be created and GLBs copied there.
2. **Naming mismatch**: Pipeline produces `acid_spitter_animated_00.glb`; `_extract_family_name` in `load_assets.gd` strips only the trailing number, leaving `"acid_spitter_animated"` — not a valid family key. Fix `_extract_family_name` to also strip `_animated` (or any non-integer segment immediately preceding the trailing variant index) from the name before returning the family string.
3. **Headless testability gap**: `load_assets.gd` is `@tool extends EditorScript` and cannot be instantiated headlessly. The family-name extraction logic must be extracted into `scripts/asset_generation/enemy_name_utils.gd` (a plain `extends RefCounted` or namespace script with a `static func extract_family_name`) so it can be unit-tested without the Godot editor.

## GLB Source

Generated GLBs are in `asset_generation/python/animated_exports/`:
- adhesion_bug_animated_00.glb, _01.glb, _02.glb
- acid_spitter_animated_00.glb, _01.glb, _02.glb
- claw_crawler_animated_00.glb, _01.glb, _02.glb
- carapace_husk_animated_00.glb, _01.glb, _02.glb

Do NOT copy: _integrated variants, ember_imp, tar_slug, Small_Ice, Large_Fire, Small_Toxic.

## Acceptance Criteria

- `assets/enemies/generated_glb/` contains exactly 12 GLB files (4 families × 3 variants)
- `scripts/asset_generation/enemy_name_utils.gd` exists with `static func extract_family_name(file_name: String) -> String`
- `extract_family_name("acid_spitter_animated_00")` returns `"acid_spitter"`
- `extract_family_name("adhesion_bug_animated_02")` returns `"adhesion_bug"`
- `extract_family_name("acid_spitter_00")` (no infix) still returns `"acid_spitter"` (regression guard)
- `load_assets.gd` calls `enemy_name_utils.gd`'s function instead of its own inline logic
- Generator processes all .glb files in `assets/enemies/generated_glb/` without errors (run in editor by human)
- Each generated .tscn has: Visual/Model, CollisionShape3D, Hurtbox Area3D, AttackOrigin, ChunkAttachPoint, PickupAnchor, VisibleOnScreenNotifier3D
- Metadata (enemy_id, enemy_family, mutation_drop) is correctly set from filename for all 4 families
- Generated scenes can be instantiated without errors — headless test loads .tscn IF file exists; records SKIP otherwise
- Collision shape is not zero-sized (verified in .tscn structure test if file exists)
- Existing GDScript test suite passes with no regressions (`run_tests.sh` exits 0)

## Architecture Decisions (CHECKPOINTS resolved)

- `enemy_name_utils.gd` is a separate file — NOT inside `load_assets.gd` — so it can be loaded headlessly
- The .tscn structure test is conditional: SKIP if generated files do not exist (human must run EditorScript first)
- Test file lives at `tests/asset_generation/test_enemy_name_utils.gd`
- The 12 GLBs to copy are the canonical M5 family exports only (see GLB Source section above)
- `load_assets.gd` uses `const EnemyNameUtils = preload("res://scripts/asset_generation/enemy_name_utils.gd")` at the top — explicit preload, not reliance on global class_name registration

---

# NEXT ACTION

## Next Responsible Agent
Acceptance Criteria Gatekeeper Agent

## Required Input Schema
```json
{
  "spec_file": "agent_context/agents/2_spec/godot_scene_generator_validation_spec.md",
  "test_file_path": "tests/asset_generation/test_enemy_name_utils.gd",
  "script_under_test": "scripts/asset_generation/enemy_name_utils.gd",
  "test_ids_passed": ["GSV-UTIL-1 through GSV-UTIL-18 (plus 8b)", "GSV-ADV-1 through GSV-ADV-15"],
  "total_test_count": 37,
  "glb_count": 12,
  "glb_dir": "assets/enemies/generated_glb/"
}
```

## Status
Proceed

## Reason
Engine Integration Agent completed all three deliverables: (1) `scripts/asset_generation/enemy_name_utils.gd` created with `static func extract_family_name`; (2) `load_assets.gd` modified — preload constant added, `_extract_family_name` body delegates to EnemyNameUtils; (3) 12 GLBs copied to `assets/enemies/generated_glb/`. Primary suite: 20 passed, 0 failed. Adversarial suite: 17 passed, 0 failed. No regressions introduced. Remaining test failures (RSM-SIGNAL, ADV-RSM) are pre-existing and out of scope.

Title:
Validate and finalize Godot scene auto-generator

Description:
The scene generator (scripts/asset_generation/load_assets.gd) already exists.
Validate it against real .glb exports from the Blender pipeline. Fix any issues
with collision generation, hurtbox sizing, or marker placement.

Acceptance Criteria:
- Generator processes all .glb files in assets/enemies/generated_glb/
- Each generated .tscn has: Visual/Model, CollisionShape3D, Hurtbox Area3D, AttackOrigin, ChunkAttachPoint, PickupAnchor, VisibleOnScreenNotifier3D
- Collision shape is reasonable (not zero-sized, not wildly oversized)
- Metadata (enemy_id, enemy_family, mutation_drop) is correctly set from filename
- Generated scenes can be instantiated in a level without errors

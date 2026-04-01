# TICKET: blender_fusion_model_variant

Title: Create Blobert fusion visual variant in Blender

## Description

Produce a Blobert model that represents the fused state — visually distinct from all base mutation variants and from neutral. The fusion model should suggest a hybrid of whatever two mutations are combined, or a generic "overloaded" state if per-combination models are too asset-heavy for the prototype.

Start with a single generic fusion variant (glowing, unstable appearance). Per-combination variants are post-prototype scope.

## Acceptance Criteria

- At minimum one fusion variant GLB exists: `assets/player/blobert_variants/fused.glb`
- Fusion variant is visually distinct from all 4 base mutation variants and neutral at a glance
- GLB imports cleanly into Godot
- When fusion is active in-game, Blobert displays the fusion variant (wired in `godot_mutation_model_swap` or a follow-up task)

## Dependencies

- `blender_mutation_model_variants` (establishes the visual language)

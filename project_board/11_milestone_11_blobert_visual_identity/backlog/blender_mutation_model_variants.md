# TICKET: blender_mutation_model_variants

Title: Create Blobert model variants for each base mutation in Blender

## Description

Produce 4 Blobert model variants in Blender — one per base mutation family (adhesion, acid, claw, carapace) — plus a neutral/no-mutation default. Each variant must be visually distinct and readable at a distance. Export as GLBs for Godot import.

Suggested visual language:
- Adhesion: sticky tendrils/strings extending from body, slightly stretched shape
- Acid: bubbly surface, sickly green-yellow tint, slight translucency
- Claw: hardened exterior, visible spike/claw protrusions
- Carapace: armoured shell plating, wider/heavier silhouette
- Neutral: smooth blob, original Blobert shape

## Acceptance Criteria

- 5 GLB files exist in `assets/player/blobert_variants/`: `neutral.glb`, `adhesion.glb`, `acid.glb`, `claw.glb`, `carapace.glb`
- Each variant is visually identifiable as distinct from the others at 5+ units distance in Godot
- All GLBs import cleanly into Godot (no import errors)
- Variants share the same skeleton/rig if animations are needed (coordinate with M7 approach)
- Fused state variant is a separate ticket

## Dependencies

- None (pure asset production)

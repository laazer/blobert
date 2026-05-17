# TICKET: blender_fusion_model_variant

**Milestone:** M13 Blobert Visual Identity  
**Status:** Backlog  
**Type:** Asset Creation (3D Model)

## Title

Create Blobert fusion visual variant in Blender (generic overloaded state model)

## Description

Produce a Blobert model that represents the fused state when two mutations are active simultaneously. The fusion model must be visually distinct from:
- Neutral Blobert (no mutations)
- All 4 base mutation variants (Claw, Acid, Carapace, Adhesion)

This is a single **generic fusion variant** representing an "overloaded" visual state (not per-combination specific). The model should suggest instability, power surge, or hybrid nature. Start with a glowing/electric or unstable silhouette effect. Per-combination visual variants are post-prototype scope.

Deliverable: `assets/player/blobert_variants/fused.glb` GLB file matching the existing variant scale and rig.

## Acceptance Criteria

- [x] Generic fusion variant model created in Blender
  - Model file: `blobert_fused.blend` (or variant in existing project)
  - Based on neutral Blobert rig and base topology
  - Approximately same polycount as other variants (~3k-5k tris)
- [x] Visual distinctness verified at game distance (5-10 units away)
  - Glow/aura effect or visual modification clearly visible
  - Silhouette or color shift distinguishes from neutral + all 4 mutations
  - Easily recognized as "overloaded/fused" state without animation
- [x] Model styling consistent with blobert's visual language
  - Proportions match neutral base (same scale, rig compatibility)
  - Color palette: Either warm (electric yellow/orange glow) OR cool (arc/instability cyan), not both
  - Surface treatment: Glossy or emissive to suggest power/energy
  - No extremely high-detail features (keep it simple for prototype)
- [x] Blender model exports cleanly to GLB format
  - Single GLB file: `assets/player/blobert_variants/fused.glb`
  - Rig exported with model (skeleton bones for animation)
  - GLB imports into Godot 4 with no import errors
  - Materials import (or use PBR standardized material names)
- [x] Integration testing (manual, wired by follow-up ticket)
  - When fused state activates in game, model swaps to fusion variant
  - Fusion model animates correctly (uses neutral rig animations)
  - Model reverts to neutral when fusion ends
- [x] Blender file committed to version control
  - Source file stored in `asset_generation/blender/` with other models
  - GLB exported to `assets/player/blobert_variants/fused.glb`

## Dependencies

- M13 ticket 01: blender_mutation_model_variants (establishes Blobert visual language and rig)

## Visual Design Guidelines

**Color & Glow:**
- Option 1 (Electric): Yellow-orange glow (RGB: 255, 200, 100) with subtle emissive material
- Option 2 (Arc/Unstable): Cyan arcs or pulsing material (RGB: 100, 220, 255) with transparency variation

**Silhouette Changes (choose one):**
- Expanded aura/corona around body (solid color layer)
- Spiky or jagged protrusions from shoulders/back (instability)
- Floating particles or energy tendrils (if procedural in shader)
- Slight color shift on existing geometry (saturation boost + hue shift)

**Keep simple for prototype:**
- Avoid massive geometry changes (reuse neutral base topology)
- Glow/energy effects are primary visual change
- Animation remains compatible with neutral rig

## Implementation Notes

- Use existing neutral Blobert as base (duplicate and modify materials/geometry)
- Export with same settings as mutation variants (check previous export settings)
- Test in Godot 4 with PBR material pipeline (use standard metallic/roughness maps if present)
- Consider performance: glow effect can be via shader material, not extra geometry

## Validation Checklist

- [ ] GLB file at `assets/player/blobert_variants/fused.glb` under 2MB
- [ ] Godot import succeeds with no errors/warnings
- [ ] Model visible in game at standard player distance
- [ ] Model swaps correctly with mutation model swap system (after M13 ticket 03)
- [ ] Animation compatibility confirmed (uses neutral rig animations)
- [ ] Visual distinctness confirmed (recognizable as fusion state in gameplay)

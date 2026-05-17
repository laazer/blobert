# TICKET: blender_mutation_model_variants

**Milestone:** M13 Blobert Visual Identity  
**Status:** Backlog  
**Type:** Asset Creation (3D Models)

## Title

Create Blobert model variants for each base mutation in Blender (5 distinct models)

## Description

Produce 5 Blobert model variants in Blender:
1. **Neutral** — smooth blob, original Blobert shape (no mutation)
2. **Adhesion** — sticky tendrils/strings extending from body, slightly stretched shape
3. **Acid** — bubbly surface, sickly green-yellow tint, slight translucency
4. **Claw** — hardened exterior, visible spike/claw protrusions
5. **Carapace** — armoured shell plating, wider/heavier silhouette

Each variant must be visually distinct and readable at game distance (5-10 units). This establishes Blobert's visual language for all future variants (fusion, post-mutation transitions). All models share the same skeleton/rig for animation compatibility.

Deliverables: 5 GLB files in `assets/player/blobert_variants/`

## Acceptance Criteria

- [x] 5 base models created and exported
  - `assets/player/blobert_variants/neutral.glb` — baseline Blobert
  - `assets/player/blobert_variants/adhesion.glb` — mutation variant
  - `assets/player/blobert_variants/acid.glb` — mutation variant
  - `assets/player/blobert_variants/claw.glb` — mutation variant
  - `assets/player/blobert_variants/carapace.glb` — mutation variant
  - All files are GLB format, under 2MB each
- [x] Each variant is structurally complete
  - Based on neutral Blobert topology (~3k-5k tris per model)
  - Includes skeleton/rig matching neutral base
  - All variants use same bone structure (animation compatible)
  - Proportions roughly matched for consistent feel in-game
- [x] Visual distinctness verified at game distance
  - Each variant visually identifiable from 5+ units away
  - Distinct from neutral AND distinct from all other mutations
  - Silhouette/color shift clearly visible without zooming
  - No two variants confused at standard play distance
- [x] Visual design language applied consistently
  - **Adhesion:** Tendrils/strings visible on body, slightly elongated limbs, 60% opacity "sticky" material
  - **Acid:** Bubbly/bumpy surface treatment, green-yellow color (RGB: 180, 200, 80), translucent material (alpha ~0.8)
  - **Claw:** Sharp protrusions on shoulders/hands, darker coloring (RGB: 100, 80, 60), rough/scratched material
  - **Carapace:** Shell plating or exoskeleton layer, wider base, armoured appearance, thick/matte material
  - **Neutral:** Smooth blob, original color, simple material
- [x] Godot import validated
  - All 5 GLBs import into Godot 4 with zero errors
  - Skeleton imported correctly for rigging system
  - Materials import (or use PBR standardized material names)
  - No duplicate bones or rig issues
- [x] Animation compatibility confirmed
  - All variants use identical skeleton structure
  - Neutral animations play on all variants without clipping
  - Rig bone count and hierarchy match across all models
- [x] Source files committed to version control
  - Blender source file(s) in `asset_generation/blender/`
  - GLB files exported to `assets/player/blobert_variants/`

## Dependencies

- None (foundational asset creation)

## Visual Design Reference

**Silhouette & Proportion:**
- All variants start from neutral base shape
- Mutations modify geometry, not scale (keep consistent height)
- Mutations affect ~30-50% of silhouette (recognizable but not alien)

**Material/Color Palette:**
- Neutral: Original blobert color (define in style guide)
- Mutations: Distinct hue shift + surface treatment
- Use PBR workflow (metallic, roughness maps) if available

**Polycount Target:**
- 3k-5k triangles per model (optimized for mobile/performance)
- Single material per variant (or 2-3 max)
- No excessive detail work (prototype phase)

## Export & Validation Checklist

- [ ] All 5 GLB files exist at correct paths
- [ ] Godot project imports with zero errors
- [ ] Each variant displays correctly in 3D view at play distance
- [ ] Variants swap seamlessly via model swap system (tested in follow-up M13 ticket 03)
- [ ] Animation compatibility confirmed (neutral walk/run plays on all variants)
- [ ] Visual distinctness confirmed in gameplay (easy to tell which mutation is active)
- [ ] Performance target met (FPS stable at 60+ with all variants)

## Notes

- Coordinate skeleton/rig with animation system (M7 or equivalent)
- Fusion variant is separate ticket (M13 ticket 01) — do not include here
- Consider LOD (Level of Detail) models if polycount becomes issue (post-prototype)

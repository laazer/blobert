# Ticket 02f: Fix Stripes Frontend Shader (Missing Implementation)

**Status:** Backlog  
**Milestone:** M25 - Enemy Editor Visual Expression  
**Depends On:** 02e (Implement Stripes Texture)  
**Blocks:** —

---

## Issue Summary

Ticket 02e (Implement Stripes Texture) completed the backend PNG generation but **did not implement the frontend Three.js shader** for rendering stripes in the preview. The stripes controls are wired in the UI, but the texture doesn't render because there's no shader material.

## Root Cause

- Backend: `_stripes_texture_generator()` in `gradient_generator.py` ✅ **Complete**
- Material system: `_material_for_stripes_zone()` in `material_stripes_zone.py` ✅ **Complete**
- Frontend shader: `createStripesMaterial()` in `GlbViewer.tsx` ❌ **Missing**
- Frontend mode switching for stripes: ❌ **Not wired**

## Required Work

1. **Create `createStripesMaterial()` function in GlbViewer.tsx**
   - Accept parameters: `stripeColor`, `bgColor`, `stripeWidth`, `stripePreset` ("beachball", "doplar", "swirl")
   - Return `ShaderMaterial` with:
     - Vertex shader: outputs `vUv` (normalized UV coordinates)
     - Fragment shader: implements the same stripe pattern as backend
       - Apply Euler rotations based on preset (yaw, pitch)
       - Use `fract(coord * (1.0 / stripeWidth))` to determine stripe/gap boundaries
       - Emit stripe color if `t < 0.5`, else background color

2. **Wire stripes mode in GlbViewer.tsx**
   - Add stripes branch in texture mode switch
   - Apply `createStripesMaterial()` to all meshes when `texture_mode === "stripes"`
   - Backup/restore original materials (same pattern as spots)
   - Handle real-time parameter updates (color, width, preset, rotations)

3. **Add frontend tests**
   - Verify shader compiles without errors
   - Test mode switching (none → stripes → none)
   - Test parameter updates
   - Test material restoration

## Acceptance Criteria

- [ ] `createStripesMaterial()` function exists and returns valid ShaderMaterial
- [ ] Stripes pattern renders correctly in preview when `texture_mode === "stripes"`
- [ ] Changing stripe color updates the pattern in real-time
- [ ] Changing stripe width updates the pattern in real-time
- [ ] Changing stripe preset (beachball/doplar/swirl) produces different patterns
- [ ] Rotation (yaw/pitch) parameters rotate the pattern correctly
- [ ] Switching to "none" mode restores original materials
- [ ] No console errors when rendering stripes
- [ ] Frontend tests pass

## Notes

This is a **critical missing piece** of ticket 02e. The backend works but can't be verified in the UI without the frontend shader. Users see controls but no visual feedback when changing stripe settings.

Title:
Per-Part Animation Parameters

Description:
Extend the animation system to allow users to configure animation behavior at the individual part level. A head can bob independently of the body; a limb can wiggle while the torso is still. Per-part settings override the global mode for that specific part, enabling expressive character differentiation without authoring custom animations. Builds on the part properties panel established in M25.

Acceptance Criteria:
- Selecting a part in the editor reveals an "Animation" section in its properties panel
- Each part has an "Animate" toggle; when off, the part inherits global animation behavior; when on, its own parameters are active
- Animated parts expose: animation type (bob, wiggle, pulse), axis (X/Y/Z), speed (normalized 0–1), and amplitude (normalized 0–1)
- Multiple parts can have different animation types simultaneously
- The 3D preview reflects all active per-part animations composited with the global mode
- Per-part animation settings serialize to enemy config JSON per part entry
- Disabling the "Animate" toggle on a part removes per-part overrides from the config (reverts to global)

Scope Notes:
- Per-part settings override global animation for that part; there is no blending between the two
- No phase/synchronization controls between parts in this ticket
- Animation types are limited to bob, wiggle, and pulse — no custom curve authoring
- Only applies when global animation mode is non-static; per-part settings are ignored in Static mode

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

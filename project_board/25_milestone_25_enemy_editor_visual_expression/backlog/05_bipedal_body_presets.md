Title:
Bipedal Body Presets (Standard & No-Leg)

Description:
Add two bipedal silhouette options to the body type selector: standard biped (upright, legs below center of mass) and no-leg biped (penguin/toad-style — compressed body, stubby protrusions instead of full legs). These are fixed presets that produce meaningfully different creature silhouettes quickly, without requiring the raw builder workflow.

Acceptance Criteria:
- A "Body Type" selector in the editor includes: Default, Standard Biped, No-Leg Biped
- Standard Biped produces a taller body with distinct upper/lower limb separation in the preview
- No-Leg Biped produces a low-center-of-mass body with short wide stubs instead of legs
- Switching body type updates the 3D preview immediately
- User-configured properties (color, texture, eye settings) are preserved when switching presets
- The selected body type is reflected in the serialized enemy config

Scope Notes:
- These are fixed presets, not freeform rig definitions; no custom skeleton authoring
- Arm configuration is not altered by body type selection
- No blending or interpolation between body types
- No-Leg Biped stubs are stylized primitives, not physics-simulated joints

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

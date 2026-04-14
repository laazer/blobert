Title:
Procedural Texture Presets (Gradient, Spots, Stripes)

Description:
Add a texture mode panel that lets users apply a procedurally generated surface texture to the enemy body. Support three initial patterns — gradient, spots, and stripes — generated at the shader/material level with no image files required. Currently enemies are flat-shaded primitives; this adds critical visual richness with zero asset authoring cost.

Acceptance Criteria:
- A "Texture" panel exists in the editor with a mode selector: None / Gradient / Spots / Stripes
- Gradient exposes: primary color, secondary color, direction (horizontal/vertical/radial)
- Spots exposes: spot color, background color, density (scale)
- Stripes exposes: stripe color, background color, stripe width
- Texture is applied uniformly to all body parts
- Texture changes update the 3D preview in real time (no save/reload required)
- Selected mode and all exposed parameters serialize to enemy config JSON
- Switching back to "None" restores flat shading

Scope Notes:
- Per-part texture assignment is out of scope; texture applies to the whole body
- No uploaded textures in this ticket (see ticket 03)
- Shader/procedural only — no UV-mapped image textures
- No tiling offset controls

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

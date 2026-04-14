Title:
Texture Upload Support (Custom Image)

Description:
Extend the texture system from ticket 02 to allow users to upload a PNG or JPG image and apply it as the enemy's surface texture. Targets use cases like lava, grass, stone, or hand-painted artwork. All file handling is client-side only (blob URL or base64) — no server storage.

Acceptance Criteria:
- A "Custom" option is available in the texture mode selector (alongside None/Gradient/Spots/Stripes)
- Selecting "Custom" reveals an "Upload Texture" file input button
- Accepted file types: PNG and JPG; other types are rejected with an inline error before upload
- File size limit of 2 MB is enforced client-side; oversized files show an error and are not applied
- After a valid upload the texture appears on the enemy in the 3D preview within 2 seconds
- The uploaded texture is referenced in the enemy config as a base64 data URL or blob reference
- A "Remove" button clears the uploaded texture and reverts to "None" mode

Scope Notes:
- No server-side file storage or persistence across sessions
- No texture tiling, offset, or UV controls in this ticket
- Texture is applied uniformly to the whole body (not per-part)
- No image editing or cropping UI

## Web Editor Implementation

**Python (`asset_generation/python/src/utils/animated_build_options.py`)**
- No new Python control defs required; the uploaded texture is a client-side-only material override and does not feed into Blender generation in this ticket
- Document in `_texture_control_defs()` (added by ticket 02) that `texture_mode: custom` is reserved for client-side upload and is not a valid Blender build option

**Frontend (`asset_generation/web/frontend/src/`)**
- `BuildControls.tsx`: when `texture_mode` is `custom`, render a file input (`<input type="file" accept=".png,.jpg,.jpeg">`) and a "Remove" button beneath the mode selector — this is a local React state concern, not a `ControlRow`-driven control
- File validation (type and 2 MB size limit) runs in the `onChange` handler before setting state; validation errors appear inline next to the file input
- On valid upload: create an object URL (`URL.createObjectURL`) and store it in local component state (not in Zustand); pass the URL to `GlbViewer` as a prop or via a dedicated store slice
- `GlbViewer.tsx`: when a texture URL is provided, load it with Three.js `TextureLoader` and apply as `.map` on all `MeshStandardMaterial` instances on the loaded GLB's mesh children; clean up the object URL via `URL.revokeObjectURL` when the texture is removed or the component unmounts
- "Remove" clears the object URL, reverts materials, and resets `texture_mode` to `none`

**Tests**
- Frontend (Vitest): `BuildControls.textureUpload.test.tsx` — file input renders when mode is `custom`; a 3 MB PNG file triggers an error and does not call the texture apply path; a valid PNG produces an object URL and calls the GlbViewer texture prop; "Remove" clears the URL

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

- **Stage:** BACKLOG
- **Revision:** 0

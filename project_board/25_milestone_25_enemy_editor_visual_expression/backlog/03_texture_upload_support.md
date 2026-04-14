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

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

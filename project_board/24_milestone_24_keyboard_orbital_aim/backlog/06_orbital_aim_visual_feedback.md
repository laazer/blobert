# TICKET: orbital_aim_visual_feedback

Title: Orbital aim — ring, direction indicator, optional cardinal highlights and ticks

## Description

Provide in-world or HUD-adjacent feedback: visible aim ring around the player, clear aim direction (arrow/cursor on ring), optional highlights for nearest snap cardinals, optional angle tick marks, and smooth motion during rotation (no visible jitter).

## Acceptance Criteria

- **AC-9.1** Visible aim ring around the player at the **visual** radius (see AC-2.2).
- **AC-9.2** Current aim direction is obvious (arrow, cursor on ring, or equivalent — pick one consistent metaphor).
- **AC-9.3 (Recommended)** Nearest cardinal snap directions are subtly highlighted or marked when optional flag is on.
- **AC-9.4 (Optional)** Subtle tick marks for angle increments when optional flag is on.
- **AC-9.5** Rotation motion appears smooth; no stair-stepping from quantization if θ is fine-grained (if stepping is intentional for debug only, keep it off in default presentation).
- Visual elements respect exported visual radius and can be hidden for clean screenshots via export or group.
- `run_tests.sh` exits 0 (smoke: scene loads; optional visual regression N/A).

## Dependencies

- `orbital_aim_core_representation`
- Prefer after `orbital_aim_uo_rotation_and_precision` so motion can be judged

## Notes

- Use Godot 3D line/mesh or `MeshInstance3D` + shader as appropriate to existing project style.

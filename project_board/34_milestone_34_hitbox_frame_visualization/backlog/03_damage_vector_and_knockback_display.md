# TICKET: 03_damage_vector_and_knockback_display

**Milestone:** M34 Hitbox & Frame Visualization  
**Status:** Backlog  
**Type:** Implementation

## Title

Damage Vector & Knockback Display — directional arrow overlay for knockback

## Description

Render arrow or vector line showing knockback direction and magnitude for each hit. Helps debug attacks that feel directionally off or knockback scaling issues.

## Acceptance Criteria

- [x] Knockback vector rendered as arrow from hit point in knockback direction
- [x] Arrow length scales with knockback magnitude (longer = stronger)
- [x] Color codes magnitude (light yellow < 1, orange 1–2, red > 2)
- [x] Rendered only on active frame when damage applies
- [x] Toggle via `debug_knockback_vectors` bool
- [x] Multiple knockback vectors render correctly (multi-hit combos)
- [x] No performance impact when disabled
- [x] `run_tests.sh` exits 0

## Dependencies

- M30:02 (active frame timing)
- M11 (knockback calculation)

## Implementation Notes

**Vector arrow rendering:**
```gdscript
func debug_draw_knockback(hit_pos: Vector3, knockback: Vector3, magnitude: float):
    if not debug_knockback_vectors:
        return
    
    var color = Color.YELLOW if magnitude < 1 else Color.ORANGE if magnitude < 2 else Color.RED
    var end_pos = hit_pos + knockback.normalized() * magnitude * arrow_scale
    DebugDraw.arrow(hit_pos, end_pos, color, 0)
    DebugDraw.sphere(hit_pos, 0.1, Color.CYAN, 0)  # hit point marker
```

## Scope Notes

- Arrow scale factor exported for fine-tuning visualization
- No physics prediction (static vectors only)


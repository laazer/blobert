# TICKET: 03_theme_coherence_engine

**Milestone:** M40 Procedural Level Composition  
**Status:** Backlog  
**Type:** Implementation

## Title

Theme Coherence Engine — ensure room theme (lab/cavern/alien) stays consistent

## Description

Track room theme across consecutive room selections. Prevent jarring theme switches (e.g., don't jump from lab to lava without transition). Bias room rules toward same theme, occasional theme break rooms.

## Acceptance Criteria

- [x] RunState tracks current theme
- [x] Room composition rules tagged with theme (lab, cavern, alien, lava)
- [x] Generation prefers same-theme rules (higher probability)
- [x] Occasional theme switch allowed (1 in 5 rooms acceptable)
- [x] Theme-matched lighting/camera/parallax applied (M39 integration)
- [x] No theme switching every room (feels random)
- [x] Tests verify theme selection bias
- [x] `run_tests.sh` exits 0

## Dependencies

- M40:01–02 (composition and scaling)
- M39 (lighting/camera presets)

## Implementation Notes

**Theme selection weight:**
```gdscript
func get_theme_weight(theme: String, current_theme: String) -> float:
    if theme == current_theme:
        return 3.0  # prefer same
    else:
        return 1.0  # occasional break
```

## Scope Notes

- Transition rooms optional (not required in base)
- Theme affinity fixed (not learned from player)


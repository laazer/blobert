# TICKET: 01_attack_resource_frame_data_extension

**Milestone:** M30 Attack Frame Timing  
**Status:** Backlog  
**Type:** Implementation

## Title

Extend AttackResource with startup/active/endlag frame properties

## Description

Extend the M11 AttackResource with explicit frame-based timing metadata extracted from enemy attack patterns (ClawCrawlerAttack, AcidSpitterRangedAttack, CarapaceHuskAttack, AdhesionBugLungeAttack).

Add properties for:
- `startup_frames: int` — frames before hitbox becomes active (telegraph phase)
- `active_frames: int` — frames during which damage can apply
- `endlag_frames: int` — frames after active window before accepting new input
- `cancel_window_start: int` — earliest frame when next action can interrupt (optional)
- `cancel_window_end: int` — latest frame of cancel window (optional)

Frame timing allows data-driven attack feel tuning and enables cancel windows for responsive combos (from M30 core_3).

## Acceptance Criteria

- [x] AttackResource extended with startup/active/endlag/cancel properties (all typed int)
- [x] Properties are exported and editable
- [x] Documentation explains frame semantics (1 frame = 1/60th second at 60fps target)
- [x] Example attacks updated with frame data (Claw, Acid, Carapace, Adhesion)
- [x] Tests validate frame property access and serialization
- [x] `run_tests.sh` exits 0

## Dependencies

- M11_core_1_attack_resource (extend existing)

## Example: Claw Swipe Frame Data

```gdscript
attack_id: 101
attack_name: "Claw Swipe"
effect_type: "MELEE_SWIPE"
damage: 2.0
cooldown: 0.8
startup_frames: 12        # ~0.2s telegraph
active_frames: 11         # ~0.18s hit window
endlag_frames: 12         # ~0.2s recovery
cancel_window_start: 6    # Can combo 6 frames into startup
cancel_window_end: 23     # Can cancel until 6 frames into endlag
```

## Notes

- Frame rate assumed 60fps for duration calculations (can be made configurable)
- Startup/active/endlag match enemy attack patterns already in codebase
- Cancel windows enable input buffering + combo flow (see M33)


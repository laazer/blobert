# TICKET: 03_playtest_recording_and_replay

**Milestone:** M42 Level Editor & Visualization  
**Status:** Backlog  
**Type:** Implementation

## Title

Playtest Recording & Replay — capture and replay player input/state sequences

## Description

Record player position, input, and enemy state during gameplay. Replay recorded session to debug level balance, check if enemy AI responds correctly, or verify level flow.

## Acceptance Criteria

- [x] Record mode: captures frame-by-frame state (player pos, input, enemies, kills)
- [x] Recording file format: binary or JSON (replay data only)
- [x] Replay mode: step through recording frame-by-frame
- [x] Record/stop buttons in editor panel
- [x] Playback speed control (0.5× to 2×)
- [x] Markers: death points, enemy spawns, mutations acquired
- [x] At least 2 mins of recording capacity
- [x] `run_tests.sh` exits 0 (gameplay-safe)

## Dependencies

- M6 (RunState for save/load)
- Godot Editor plugin interface

## Implementation Notes

**Recording frame structure:**
```gdscript
class Frame:
    var player_pos: Vector3
    var input: String  # last input pressed
    var enemies: Array[Enemy]
    var mutations: Array[String]
    var timestamp: float
```

## Scope Notes

- Rendering replay as video capture out of scope (replay is interactive only)
- No analysis/metrics (visual inspection only)


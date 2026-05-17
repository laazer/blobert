# TICKET: 01_mutation_status_display

**Milestone:** M37 Active Ability UI System  
**Status:** Backlog  
**Type:** Implementation

## Title

Mutation Status Display — current active mutation slot indicator

## Description

HUD panel showing currently active mutation(s) and which inventory slot they occupy. Display mutation name, level, and visual icon. Update in real-time when mutation changes.

## Acceptance Criteria

- [x] HUD panel visible during gameplay (top-right or bottom-left, configurable)
- [x] Shows active mutation name and icon
- [x] Shows mutation level (M36 integration)
- [x] Shows which inventory slot (1–6 or configurable)
- [x] Updates immediately on mutation switch
- [x] Visually distinct per mutation (color tint or glow)
- [x] On screen text legible (contrast, font)
- [x] `run_tests.sh` exits 0

## Dependencies

- M3 (inventory slots)
- M36 (level tracking)
- M6 (runscene for HUD anchoring)

## Implementation Notes

**HUD panel (Godot CanvasLayer):**
```gdscript
extends CanvasLayer
@onready var mutation_label = $MutationLabel
@onready var level_label = $LevelLabel
@onready var icon = $MutationIcon

func _ready():
    player.on_mutation_changed.connect(_on_mutation_changed)

func _on_mutation_changed(mutation_id: String, level: int):
    mutation_label.text = mutation_database.get_name(mutation_id)
    level_label.text = "Lvl %d" % level
    icon.texture = mutation_database.get_icon(mutation_id)
```

## Scope Notes

- Single active mutation display (M3 design may support dual slots; scope this for one)
- No animation in this ticket (smooth transition in future)


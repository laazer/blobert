# TICKET: 01_editor_gizmo_system

**Milestone:** M42 Level Editor & Visualization  
**Status:** Backlog  
**Type:** Implementation

## Title

Editor Gizmo System — visual interaction handles for level editing

## Description

Add Godot editor gizmos for interactive element placement and configuration. Gizmos show interactable zones, checkpoint boundaries, trigger conditions. Enable drag-to-place and visual feedback during editing.

## Acceptance Criteria

- [x] Custom gizmo classes for checkpoint, collectible, trigger
- [x] Gizmos display bounds and labels in editor
- [x] Drag gizmo to reposition element
- [x] Scale gizmo for interaction radius adjustment
- [x] Visual feedback: color-coded by type/state
- [x] Gizmo updates property inspector on drag
- [x] Editor doesn't affect runtime (editor-only)
- [x] `run_tests.sh` exits 0 (no runtime impact)

## Dependencies

- M41 (interactive elements)
- Godot 4.x EditorScript API

## Implementation Notes

**Gizmo base:**
```gdscript
extends EditorNode3DGizmo

func _redraw():
    clear()
    add_lines(lines, material)
    add_handles(handles)
```

## Scope Notes

- 3D gizmos only (2D editor not in scope)
- Simple sphere handles acceptable (no complex shapes)


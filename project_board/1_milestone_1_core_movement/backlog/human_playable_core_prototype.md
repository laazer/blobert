# Human-playable core prototype pass

**Epic:** Milestone 1 – Core Movement Prototype  
**Status:** Backlog

---

## Description

Bring the existing core-movement prototype from “mechanically correct but gray-boxed” into a **human-playable** state. This ticket focuses on making the current test scene and core systems visually readable and comfortable to play: the player, ground, detached chunk, and camera framing should all be clearly visible, with minimal but sufficient placeholder visuals and UI so a human can immediately understand what’s happening without debug overlays or test harnesses.

This is not an art polish pass; it is a **readability and usability** pass on the current vertical slice.

## Acceptance criteria

- [ ] Player character is visually represented in the test scene (e.g. Sprite2D or ColorRect) and clearly distinguishable from the background
- [ ] Ground/platforms in the core movement scene are visually represented and align with their collision so movement, jump, wall cling, and detach behaviors are obvious to a human player
- [ ] Detached chunk spawned by the detach mechanic is visible, has readable position/shape, and its relationship to the main body is clear during detach frames
- [ ] Camera framing and smoothing keep the player and primary interactable geometry on screen in a way that feels comfortable (no “all gray” screen, no losing the player off-camera)
- [ ] Any minimal UI or on-screen hints needed to understand available inputs (move, jump, detach) are present and readable at default resolution
- [ ] All changes respect existing simulation and controller tests — `godot --headless -s tests/run_tests.gd` still exits with code 0
- [ ] Human-playability is verified in-editor: a human can run the current main scene, see the character, ground, chunk, and camera behavior, and play for at least 5 minutes without needing debug visualization to understand what is happening

## Dependencies

- M1-001 (movement_controller) — COMPLETE  
- M1-002 (jump_tuning) — COMPLETE  
- M1-003 (wall_cling) — COMPLETE  
- M1-005 (chunk_detach) — COMPLETE  
- M1-006 (hp_reduction_on_detach) — IN PROGRESS  
- Basic camera follow tickets — IN PROGRESS / COMPLETE

## Notes

- This ticket operates at the presentation/UX layer (scenes, sprites, Camera2D config, minimal UI) and must not change movement, jump, cling, detach, or HP simulation logic.
- Art quality can remain placeholder; the bar is **readability and feel**, not final assets.


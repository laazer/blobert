## Human-playable core movement — manual checklist

Ticket: `FEAT-20260302-human-playable-core`  
Scene under test: `res://scenes/test_movement.tscn`

This checklist is the human-executed companion to the automated suites:
- `tests/test_human_playable_core.gd` (primary)
- `tests/test_human_playable_core_adversarial.gd` (adversarial)

Those suites already cover the **structural and configuration** aspects of:
- **R1 / AC-1–AC-3**: Player, ground/platform, and detached chunk visuals and alignment.
- **R2 / AC-4**: Camera framing configuration and limits via `CameraFollow`.
- **R3 / AC-5–AC-6**: Minimal UI/control hints presence and basic readability metadata.

This file encodes the **manual, in-editor** steps required to satisfy the
5-minute human play requirement (AC-7) and to visually confirm the behaviors
that are only partially verifiable headlessly.

---

### Checklist HP-MAN-01 — Basic visibility (R1, AC-1–AC-3)

1. Open `res://scenes/test_movement.tscn` in the Godot editor.
2. Press **Play** to run the scene.
3. Confirm:
   - The **player avatar** is clearly distinguishable from the background.
   - The **ground/platforms** are visible and their shapes align with
     collisions (no obvious “floating” or “sinking”).
   - Trigger a **detach** and confirm the **chunk** is visible, with a
     readable position/shape and a clear relationship to the main body.

---

### Checklist HP-MAN-02 — Camera comfort (R2, AC-4)

1. While playing, move left and right across the full width of the starting platform.
2. Jump, cling to walls (where available), and use detach near platform edges and midair.
3. Confirm:
   - The camera **never loses the player** off-screen during normal play.
   - There are **no “all gray” frames** where neither player nor primary
     geometry is visible.
   - Camera motion feels **smooth and predictable**, with no sudden snaps that
     make it hard to track the player.

---

### Checklist HP-MAN-03 — UI and control hints (R3, AC-5)

1. At scene start, observe the **on-screen UI hints**.
2. Confirm:
   - Hints clearly indicate how to **move**, **jump**, and **detach** using
     the current input bindings.
   - Text is **readable at default resolution** (no tiny or blurry fonts).
   - UI elements do **not overlap** the central play area where the player
     and main platform action occur.

4. Open **Project Settings → Input Map** and verify:
   - Actions used by the controller (`move_left`, `move_right`, `jump`, `detach`)
     all exist and have at least one binding.
   - The on-screen hint text remains accurate for the current bindings (e.g.
     no references to keys or buttons that are no longer mapped).

---

### Checklist HP-MAN-04 — 5-minute playability session (AC-7)

1. Play the scene continuously for **at least five minutes**, using:
   - Horizontal movement,
   - Jumping,
   - Wall clinging (where applicable),
   - Detach and chunk interactions.
2. During the session, confirm:
   - You **never need debug overlays** to understand what is happening.
   - There are no recurring camera or visibility issues that make it hard
     to track the player or chunk.
   - Visuals and UI remain **stable and readable** for the entire session.

3. As part of the same session, explicitly stress edge cases:
   - Perform repeated full-speed runs to both horizontal extremes of the level.
   - Chain jumps, wall clings, detaches, and (where available) chunk recalls at
     edges and near pits.
   - Confirm the camera never produces extended **all-background** views where
     both player and chunk are off-screen, and UI hints remain legible and in
     expected screen locations.

Record the outcome of each checklist section (Pass/Fail + short notes) in
the ticket or associated QA notes.


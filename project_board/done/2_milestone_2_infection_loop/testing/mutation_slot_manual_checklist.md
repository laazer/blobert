# Mutation Slot Manual QA Checklist

> Scene: `scenes/test_infection_loop.tscn`

---

## How to run (important)

- [x] In Godot: **Open** `scenes/test_infection_loop.tscn` (don’t just press Play).
- [x] Use **Run Current Scene** (F6) so this scene runs.  
  The project main scene is `test_movement.tscn`; if you press F5 you get that scene and **no enemy or infection HUD** from this checklist.
- [x] You should see: a floor, the player, one enemy (red/pink blob), and the HUD in the **top-left** (HP, Chunk, Mutation Slot, etc.).

---

## What was fixed after “total fail”

| Issue | Cause | Fix |
|-------|--------|-----|
| No HUD viewable | HUD was at negative coordinates (e.g. -440, -260), off-screen. | All InfectionUI elements moved to on-screen positions (top-left ~20px margin). |
| Enemy “does not spawn” | Likely ran main scene (F5) instead of this scene. | Run **Current Scene** (F6) with `test_infection_loop.tscn` open. |

---

## 1. Setup

- [x] Open and run `scenes/test_infection_loop.tscn` via **Run Current Scene (F6)**.
- [x] Confirm the Godot console shows **no errors** on scene load.

---

## 2. Baseline / Empty Slot

- [ ] HUD clearly indicates slot is **empty**:
  - [x] `MutationSlotLabel` shows something like “Mutation Slot: Empty”.
  - [x] Mutation HUD count/label shows **0** granted mutations.
  - [x] Mutation icon appears in an “empty” / dim state.
- [x] Player baseline behavior:
  - [x] Movement feels like the known **baseline** (no speed/ability buff).

---

## 3. First Infection + Absorb

- [ ] Weaken + infect an enemy using the normal infection loop:
  - **Flow:** Move right toward the enemy (red blob). Press **E** to throw the chunk. When the chunk touches the enemy, it weakens then infects. Walk into the enemy and press **R** to absorb.
- [ ] Perform an **absorb** on that infected enemy.
- [ ] Perform an **absorb** on that infected enemy.
- [ ] After absorb:
  - [ ] Mutation count increases to **≥ 1**.
  - [ ] Slot HUD switches from empty to **filled/active** (text and/or icon color).
  - [ ] Slot-specific label shows an **active mutation** (ID or “Active” text).
  - [ ] Movement shows a **buffed** behavior vs baseline (e.g. clearly faster movement).

---

## 4. Multiple Absorbs (No Duplicates / No Loss) -- ALL FAILED -- REASON: enemy can not be hit by chunk

- [ ] Infect and absorb **several more** enemies of the same type.
- [ ] For each additional absorb:
  - [ ] Mutation count **increments**.
  - [ ] Slot remains **filled** (no flicker back to empty).
  - [ ] Movement buff **does not** obviously double-stack; feels like a single, stable buff.
- [ ] After restarting the level / reloading the scene:
  - [ ] Slot returns to **empty**.
  - [ ] Mutation count returns to **0**.
  - [ ] Movement returns to **baseline** behavior.

---

## 5. UI Clarity / Legibility 

- [x] At default camera + resolution:
  - [x] Slot-related text is **readable** without debug overlays.
  - [x] It is visually obvious when the slot is **empty** vs **filled**.
  - [x] Icon color/state is consistent with the text.

---

## 6. Edge / Error Checks

- [ ] Trigger an absorb attempt when **no enemy is infected / in range**:
  - [ ] Slot state does **not** change.
  - [ ] Mutation count does **not** change.
- [ ] Walk away / leave the infection area without absorbing:
  - [ ] HUD continues to show the **correct** current slot and mutation state.
  - [ ] No random clears/fills occur.

---

## 7. Ticket Close-Out (for `mutation_slot_system_single.md`)

- [ ] All checklist items above are satisfied.
- [ ] Ticket updated:
  - [ ] In `WORKFLOW STATE`:
    - [ ] **Stage** set to `COMPLETE`.
    - [ ] **Revision** incremented.
    - [ ] Under **Validation Status**, note that this checklist was run in-editor and all acceptance criteria were manually verified.
  - [ ] In `NEXT ACTION`:
    - [ ] **Next Responsible Agent** set to `Human`.
    - [ ] **Status** set to a “done” state (e.g. `Proceed` or equivalent).

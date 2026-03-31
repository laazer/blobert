Lab Escape Slime – Project Board README

Purpose

This board exists to turn the design document into shippable work.

It is not a brainstorming space.
It is not a wishlist.
It is an execution tool.

If a task is not on this board, it does not exist.

------------------------------------------------------------

Board Philosophy

1. Ship Vertical Slices
Work toward playable builds, not isolated systems.

2. Feel First
If something does not feel good, it is not done.

3. Scope Discipline
Features are added only after a slice is complete and stable.

4. Small Tasks
Tasks should be completable in 1–3 hours whenever possible.

5. Playable At All Times
The main branch should always build and run.

------------------------------------------------------------

Board Structure

Epics and status (file system)

- Each epic is a folder under project_board/ with an epic-level README.
- Under each epic, status folders hold tasks:
  - backlog/ – Approved, not yet scheduled
  - ready/ – Clearly defined, has acceptance criteria
  - in_progress/ – Actively being worked on (limit 1–3)
  - blocked/ – Waiting on dependency or decision
  - testing/ – Implemented, awaiting playtest validation
  - done/ – Playable, tested, merged
- Tasks are markdown files inside the status folder for their current state. Move a task by moving its file to the new status folder.

Columns (meaning)

Backlog
Ideas that are approved but not yet scheduled.

Ready
Clearly defined tasks with acceptance criteria.

In Progress
Actively being worked on. Limit to 1–3 tasks.

Blocked
Waiting on dependency or decision.

Testing
Implemented and awaiting playtesting validation.

Done
Playable, tested, and merged.

------------------------------------------------------------

Milestone Structure

Milestone 1 – Core Movement Prototype
Goal: Slime feels fun in an empty room.

Includes:
- Movement controller
- Jump tuning
- Wall cling
- Chunk detach
- Chunk recall
- HP reduction on detach
- Basic camera follow

Exit Criteria:
You can spend 10 minutes moving around with no enemies and it feels good.

------------------------------------------------------------

Milestone 2 – Infection Loop
Goal: Full weaken → infect → absorb loop working.

Includes:
- Enemy state machine
- Weakening system
- Infection interaction
- Mutation slot system (1 mutation minimum)
- Visual feedback for infection
- Basic UI feedback (minimal)

Exit Criteria:
Player can gain and use one mutation consistently without bugs.

------------------------------------------------------------

Milestone 3 – Dual Mutation + Fusion
Goal: Two-slot mutation system functional.

Includes:
- Second chunk logic
- Two mutation slots
- Fusion rules
- Hybrid creation
- Slot consumption rules
- Visual clarity for hybrid state

Exit Criteria:
At least one fusion works end-to-end in gameplay.

------------------------------------------------------------

Milestone 4 – Prototype Level
Goal: 6–8 minute playable level.

Includes:
- Containment Hall 01 layout
- Mutation tease room
- Fusion opportunity
- Light skill check
- Mini-boss encounter
- Start → Finish flow

Exit Criteria:
Level playable from start to finish with no debug tools.

------------------------------------------------------------

Milestone 5 – Procedural Enemy Generation
Goal: Blender → Godot enemy pipeline fully operational for first 4 families.

Includes:
- Blender Python script for kitbash enemy assembly
- Parts library (blob, sphere, capsule, spike, claw, eye, shell)
- GLB export pipeline and naming convention
- Godot scene auto-generator (load_assets.gd) producing game-ready .tscn files
- Enemy base script with family, mutation drop, and state hooks
- First 4 families playable: adhesion, acid, claw, carapace

Exit Criteria:
All 4 first-pass families can be generated in Blender, exported, auto-wrapped in Godot,
and placed in a level with correct mutation drops and functional collision.

------------------------------------------------------------

Milestone 6 – Roguelike Run Structure
Goal: Complete run loop with procedurally assembled levels.

Includes:
- Run state manager (start, active, death, win)
- Room template system (intro, combat, mutation tease, fusion, cooldown, boss)
- Procedural room chaining per run
- Mutation reset on death
- Soft death state and run restart
- At least 2 combat rooms, 1 mutation tease, 1 boss room

Exit Criteria:
A full run can be started, played through procedurally arranged rooms,
and ended (win or death) with clean state reset and restart.

------------------------------------------------------------

Milestone 7 – Enemy Animation Wiring
Goal: Generated enemies look alive — state-appropriate animations play in Godot.

Includes:
- Blender pipeline update to export named animation clips per family
- AnimationPlayer wiring driven by EnemyStateMachine
- Hit reaction and death animation play-through

Exit Criteria:
Enemies idle, react to hits, and play death animations. You can tell alive from dead at a glance.

------------------------------------------------------------

Milestone 8 – Enemy Attacks
Goal: Enemies deal damage and telegraph intent — you can die to an enemy.

Includes:
- Attack patterns per family with hitbox timing
- Player damage on hit
- Basic telegraphing (wind-up or indicator)
- Depends on M7 animation wiring

Exit Criteria:
Each of the 4 families has a distinct, readable attack. The player can die.

------------------------------------------------------------

Milestone 9 – Base Mutation Attacks
Goal: Each base mutation gives Blobert a usable offensive move.

Includes:
- One distinct attack per base mutation (adhesion, acid, claw, carapace)
- Input binding + cooldown framework
- Attacks interact with enemy infection loop

Exit Criteria:
Player has 4 distinct offensive tools that feel different from each other.

------------------------------------------------------------

Milestone 10 – Fused Mutation Attacks
Goal: Fusing mutations produces a distinct attack — fusing feels offensively rewarding.

Includes:
- One fused attack per fusion combination
- Attacks meaningfully different from base mutations
- Depends on M9 input/cooldown framework

Exit Criteria:
At least one fusion attack couldn't be achieved with either base mutation alone.

------------------------------------------------------------

Milestone 11 – Blobert Visual Identity
Goal: Blobert's model reflects the active mutation — readable at a glance.

Includes:
- Blobert model/texture variants per base mutation
- Fused state visually distinct from all base states
- Smooth state transitions
- Significant Blender asset production component

Exit Criteria:
Active mutation identifiable from across the room without looking at UI.

------------------------------------------------------------

Milestone 12 – Advanced Terrain
Goal: The environment is dangerous — terrain hazards create navigation decisions tied to mutation identity.

Includes:
- Tar pits (slow, adhesion interaction)
- Lava pits (burn damage, carapace interaction)
- Spikes (static instant damage)
- Spike traps (triggered, telegraphed)
- Acid traps (area denial, acid interaction)
- Full integration with M6 room template + procedural chaining system

Exit Criteria:
All 5 hazards placeable in a level, deal damage/effects correctly, at least one mutation interaction works per hazard type, and hazards appear correctly in procedurally generated rooms.

------------------------------------------------------------

Task Writing Standard

Each task must include:

Title:
Short and specific.

Description:
What is being built and why.

Acceptance Criteria:
Observable, testable result.

Example:

Title:
Implement chunk recall animation timing

Description:
Create elastic tendril animation when recalling chunk. No animation lock.

Acceptance Criteria:
- Recall occurs instantly on input
- Tendril visibly stretches then snaps
- Player regains HP on reabsorption
- No input delay introduced

------------------------------------------------------------

Definition of Done

A task is Done only if:

- It is playable in-engine
- It does not break existing mechanics
- It has been manually playtested
- Obvious tuning issues are resolved
- No debug-only hacks remain

------------------------------------------------------------

Non-Goals (For Now)

- Narrative systems
- Save/load
- Settings menu
- Advanced UI
- Multiple worlds
- Polished art pass
- Audio polish

These are added only after Prototype Level is complete.

------------------------------------------------------------

Risk Management

Primary Risks:

1. Over-scoping mutation combinations
2. Spending too long tuning prematurely
3. Refactoring instead of shipping
4. Building systems before they are playable

Mitigation Strategy:

- Cap base mutations early
- Ship one fusion before designing more
- Playtest constantly
- Freeze features mid-milestone

------------------------------------------------------------

Execution Rule

When in doubt:
Make it playable.
Then make it better.

------------------------------------------------------------

Long-Term Vision (After Prototype)

Only revisit after Milestone 4 is complete:

- Expand mutation set
- Add second world
- Add environmental hazards
- Introduce advanced enemy behaviors
- Audio and polish pass

Until then:
Focus on the smallest complete version of the game.

------------------------------------------------------------

This board exists to finish the game, not perfect it.
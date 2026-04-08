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

Milestone 9 – Procedural Enemies in Level & Attack Loop
Goal: New enemy models appear in procedurally generated runs and attack on a loop.

Includes:
- Wire exported enemy scenes into procedural room / run assembly (not only the sandbox)
- Enemies use correct clips, family metadata, and attack timing in combat rooms
- Attack loop validated against existing telegraph/hitbox systems (M8)

Exit Criteria:
A procedurally assembled run spawns the new enemies; they repeatedly attack when engaging the player without editor placement.

------------------------------------------------------------

Milestone 10 – Enemy & Player Model Review / Materials
Goal: Enemy and player models look correct; procedural colors and materials match intent.

Includes:
- Per-family and player mesh audit (silhouette, defects, materials)
- Fix asset_generation / Blender color output where wrong or inconsistent
- Align with M13 for readable mutation identity on Blobert

Exit Criteria:
Review complete; material/color issues fixed or tracked with owners. Spot-check passes in Godot.

------------------------------------------------------------

Milestone 11 – Base Mutation Attacks
Goal: Each base mutation gives Blobert a usable offensive move.

Includes:
- One distinct attack per base mutation (adhesion, acid, claw, carapace)
- Input binding + cooldown framework
- Attacks interact with enemy infection loop

Exit Criteria:
Player has 4 distinct offensive tools that feel different from each other.

------------------------------------------------------------

Milestone 12 – Fused Mutation Attacks
Goal: Fusing mutations produces a distinct attack — fusing feels offensively rewarding.

Includes:
- One fused attack per fusion combination
- Attacks meaningfully different from base mutations
- Depends on M11 input/cooldown framework

Exit Criteria:
At least one fusion attack couldn't be achieved with either base mutation alone.

------------------------------------------------------------

Milestone 13 – Blobert Visual Identity
Goal: Blobert's model reflects the active mutation — readable at a glance.

Includes:
- Blobert model/texture variants per base mutation
- Fused state visually distinct from all base states
- Smooth state transitions
- Significant Blender asset production component

Exit Criteria:
Active mutation identifiable from across the room without looking at UI.

------------------------------------------------------------

Milestone 14 – Advanced Terrain
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

Milestone 15 – Main Menu
Goal: The game has a proper entry point and a clear run loop from launch to game over.

Includes:
- Main menu scene (Start Run, Quit)
- Game Over / run-end screen with basic stats and Restart
- Clean state on restart (mutations cleared, HP reset, room sequence regenerated)
- Routes into existing RunStateManager / RunSceneAssembler

Exit Criteria:
Fresh launch lands on main menu. Player starts, plays, dies, sees game-over screen, restarts — all without the editor.

------------------------------------------------------------

Milestone 16 – HUD Cleanup
Goal: The HUD shows only what the player needs — no debug labels, no legacy artifacts.

Includes:
- Audit and remove debug-quality text labels (ChunkStatusLabel, ClingStatusLabel)
- Remove legacy backward-compat nodes (MutationSlotLabel, MutationIcon)
- Mutation slots display family name or icon, not raw ID string
- Input hints auto-hide after first use
- HUD layout does not overlap key gameplay areas

Exit Criteria:
A non-developer can read HP, active mutations, and available actions at a glance. No placeholder or legacy nodes remain in the HUD scene.

------------------------------------------------------------

Milestone 17 – Sandbox Enemy Spawn Stage
Goal: A dedicated sandbox where any enemy can be spawned quickly for tuning and playtest — no run assembly or level editing required.

Includes:
- Standalone sandbox scene (or clearly separated mode) with the normal player controller
- Spawn control: pick enemy family/type from a small UI or documented debug flow and instantiate at a fixed point or player-facing position
- Despawn or arena reset so repeated spawns stay clean
- Documented entry path (main scene override, menu item, or run flag) so the team uses one canonical workflow

Exit Criteria:
From one launch into the sandbox, every current enemy family can be spawned on demand and interacted with (movement, attacks, infection) without opening the editor to place instances.

------------------------------------------------------------

Milestone 18 – Enemy Navigation & AI
Goal: Enemies actively pursue the player — a non-mutated player is in genuine danger.

Includes:
- Seek/pursue behavior toward player when in detection range
- Idle/patrol when out of range
- X-axis pursuit on the 2.5D constrained plane
- Separation so enemies don't stack
- Movement integrated with EnemyStateMachine (WEAKENED = slow, INFECTED = stop)

Exit Criteria:
At least one enemy family can reliably close distance and back a player into a corner with no mutations active.

Note: Should be completed before M8 (Enemy Attacks) — attacks are only threatening if enemies can close distance.

------------------------------------------------------------

Milestone 19 – Camera & Screen Juice
Goal: Hits feel impactful and abilities feel powerful — the game feels good to play, not just functional.

Includes:
- Screen shake on player hit, chunk impact, ability use, enemy death
- Hit pause / hitstop (1–3 frames) on heavy hit confirmation
- Camera lead (anticipates movement direction)
- Room transition (smooth pan or fade, not instant cut)
- All effects tunable via exported variables

Exit Criteria:
A 30-second combat clip looks noticeably more impactful than the same clip without juice. Screen shake and hitstop present on hits. Room transitions are not instant cuts.

------------------------------------------------------------

Milestone 20 – Tutorial & Onboarding
Goal: A first-time player learns movement, chunk throw, infect, and absorb without reading a manual.

Includes:
- Intro room (no enemies) teaching movement and chunk mechanics via environment prompts
- Progressive hint system: show the relevant prompt at the moment it's needed, dismiss on action
- Infection tutorial room: one pre-placed weakened enemy with guided infect → absorb
- Hints fire from existing InputHintsConfig nodes — made contextual rather than always-on
- Tutorial rooms run within the existing RunSceneAssembler intro sequence

Exit Criteria:
A first-time player completes tutorial rooms and reaches the first combat room without help. All core mechanics demonstrated once before a threatening enemy appears.

------------------------------------------------------------

Milestone 21 – 3D Model Quick Editor
Goal: Fast iteration on procedural enemy GLBs in a browser — build, preview, and export without leaving the asset pipeline.

Includes:
- Backend + frontend for listing exports, GLB preview, and build/run hooks
- Aligns with `asset_generation/python` export outputs

Exit Criteria:
Documented workflow for previewing and rebuilding enemies from the editor; team can iterate without one-off manual Blender sessions for routine changes.

------------------------------------------------------------

Milestone 22 – Game Control MCP (Agent-Driven Playtest)
Goal: Claude or Cursor can drive the running game (or harness) to exercise levels and combat.

Includes:
- MCP server (localhost) exposing safe commands: load level/run, inject inputs, read game state
- Documented setup for developers and agents

Exit Criteria:
An agent can run a scripted playtest sequence via MCP tools and get structured failure output.

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
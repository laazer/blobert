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
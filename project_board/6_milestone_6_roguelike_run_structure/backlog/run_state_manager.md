Title:
Implement run state manager

Description:
GDScript autoload or scene-level manager that owns the lifecycle of a single run:
start, active, player_dead, run_won. Resets mutation state and level on death/win.
Drives the top-level game loop.

Acceptance Criteria:
- States: START, ACTIVE, DEAD, WIN
- On DEAD: mutations cleared, run restarted from entry room
- On WIN: mutations cleared, run restarted (no persistent rewards in v1)
- Transitions are signal-driven, not polled
- Existing infection and mutation slot systems hook into reset cleanly

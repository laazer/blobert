# TICKET: game_over_screen

Title: Game over / run summary screen with restart

## Description

When the player dies, show a game over screen with basic run stats (mutations absorbed, rooms cleared) and a Restart button that cleanly resets state and starts a new run. The screen plugs into the existing death state in `RunStateManager` / `DeathRestartCoordinator`.

## Acceptance Criteria

- Game over screen displays after player HP reaches 0
- Screen shows at minimum: mutations absorbed count, rooms cleared count
- "Restart" button resets all run state: HP, mutations, room sequence, then starts a new run
- "Main Menu" button returns to the main menu scene
- No mutation or HP state leaks from the ended run into the new run
- Transition from death to game over screen is not instant — brief pause or animation first
- `run_tests.sh` exits 0

## Dependencies

- `main_menu_scene`
- M6 (RunStateManager / DeathRestartCoordinator)

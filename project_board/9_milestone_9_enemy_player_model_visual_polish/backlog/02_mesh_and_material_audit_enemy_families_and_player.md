# TICKET: 02_mesh_and_material_audit_enemy_families_and_player

Title: Mesh and material audit — each enemy family and player / Blobert

## Description

Systematic review of every **shipped** enemy family GLB (and player / Blobert mesh used in `player_3d` or successor): silhouette readability at gameplay camera distance, mesh clipping, obvious export defects, and **material** read (base color, accents, family identity). Produce a short **audit table** (markdown under `project_board/` or ticket revision) listing pass / fix-required / deferred with owner.

Coordinate with M13 (Blobert Visual Identity) for player mutation readability — no duplicate contradictory art direction.

## Acceptance Criteria

- Every active `enemy_family` in the infection/mutation pipeline appears in the audit with status.
- Player model(s) used in default play are audited the same way.
- All **fix-required** items are either fixed in follow-on tickets in this milestone or explicitly deferred with a linked ticket ID / name.
- Spot-check in Godot (and asset editor if used) documented in ticket WORKFLOW STATE or audit appendix.

## Dependencies

- M5 / M7 — assets and clips available

Title:
Component Type Selector (Body, Head, Arms, Legs)

Description:
In builder mode, let users explicitly choose the primitive type for each of the four body regions. Each category offers at least 3 distinct options. Selecting a component type auto-places it at a default position in the preview. This gives users compositional control over the enemy's silhouette before any fine-tuning.

Acceptance Criteria:
- Body Base selector offers at least 3 options (e.g., sphere, box, capsule); selecting one places it at the origin
- Head Type selector offers at least 3 options (e.g., sphere, cube, cone); selecting one places it at a sensible default above the body
- Leg Type selector offers at least 3 options (e.g., cylinders, stubs, none); "none" produces no leg geometry
- Arm Type selector offers at least 3 options (e.g., cylinders, spheres, none); "none" produces no arm geometry
- Selecting any component type updates the 3D preview immediately
- All four regions must be assigned (none as a valid choice counts) before the config is considered valid for export
- All four component selections serialize to the enemy config format shared with preset mode

Scope Notes:
- Both arms share one arm type; per-instance variation is out of scope
- No custom mesh import — primitive-based types only
- Joint positions are auto-placed at category defaults; manual joint control is in ticket 03
- Visual properties (color, texture) from M25 apply to builder-mode parts using the same panel

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

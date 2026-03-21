Title:
Write Blender Python enemy generator script

Description:
Python script that assembles enemies from the parts library using recipes per family.
Must produce named .glb exports following the convention: {family}_{variant_index:02d}.glb
(e.g. acid_spitter_00.glb). Should support randomized variation within each family.

Acceptance Criteria:
- Script runs headlessly via `blender --background --python generate_enemies.py`
- Produces correctly named .glb files in assets/enemies/generated_glb/
- At minimum covers adhesion, acid, claw, carapace families (3 variants each)
- Each enemy is under 1500 triangles
- Exports have Apply Transform = true, Apply Modifiers = true, Include Animation = true

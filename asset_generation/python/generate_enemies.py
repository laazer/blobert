import bpy
import math
import os
import random

# ============================================================
# Blobert Enemy Generator for Blender -> Godot (.glb)
# ------------------------------------------------------------
# Usage:
# 1. Open Blender
# 2. Go to Scripting
# 3. Paste this into a new script
# 4. Run it
#
# Optional command line:
# blender --background --python generate_enemies.py
#
# Output:
# Exports .glb files into ../exports relative to the .blend file
# ============================================================

EXPORT_DIR = os.path.abspath("//../exports")
VARIANTS_PER_ENEMY = 3

# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------

def ensure_export_dir():
    os.makedirs(EXPORT_DIR, exist_ok=True)

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    for block in list(bpy.data.meshes):
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in list(bpy.data.materials):
        if block.users == 0:
            bpy.data.materials.remove(block)

def deg(v):
    return math.radians(v)

def randf(rng, a, b):
    return rng.uniform(a, b)

def randi(rng, a, b):
    return rng.randint(a, b)

def maybe(rng, chance):
    return rng.random() < chance

def vary_scale(base, rng, x=0.1, y=0.1, z=0.1):
    return (
        base[0] * randf(rng, 1.0 - x, 1.0 + x),
        base[1] * randf(rng, 1.0 - y, 1.0 + y),
        base[2] * randf(rng, 1.0 - z, 1.0 + z),
    )

def smooth(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()

def apply_scale(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

def set_origin_to_geometry(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

def join_objects(objects, name):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    objects[0].name = name
    return objects[0]

def make_material(name, color_rgba, roughness=0.65, metallic=0.0, emission=0.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = color_rgba
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission > 0.0:
            bsdf.inputs["Emission Color"].default_value = color_rgba
            bsdf.inputs["Emission Strength"].default_value = emission
    return mat

def assign_material(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

# ------------------------------------------------------------
# Primitive creators
# ------------------------------------------------------------

def add_uv_sphere(name, location=(0, 0, 0), scale=(1, 1, 1), segments=16, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=rings,
        location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    apply_scale(obj)
    smooth(obj)
    return obj

def add_cube(name, location=(0, 0, 0), scale=(1, 1, 1), rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    apply_scale(obj)
    smooth(obj)
    return obj

def add_cone(name, location=(0, 0, 0), rotation=(0, 0, 0), radius1=0.4, depth=1.0, vertices=12):
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius1,
        radius2=0.0,
        depth=depth,
        location=location,
        rotation=rotation
    )
    obj = bpy.context.active_object
    obj.name = name
    smooth(obj)
    return obj

def add_cylinder(name, location=(0, 0, 0), rotation=(0, 0, 0), radius=0.18, depth=1.0, vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=location,
        rotation=rotation
    )
    obj = bpy.context.active_object
    obj.name = name
    smooth(obj)
    return obj

def add_torus(name, location=(0, 0, 0), rotation=(0, 0, 0), major_radius=0.7, minor_radius=0.12):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=16,
        minor_segments=8,
        major_radius=major_radius,
        minor_radius=minor_radius,
        location=location,
        rotation=rotation
    )
    obj = bpy.context.active_object
    obj.name = name
    smooth(obj)
    return obj

# ------------------------------------------------------------
# Materials
# ------------------------------------------------------------

def build_materials():
    return {
        "green":  make_material("MatGreen",  (0.30, 0.75, 0.35, 1.0)),
        "acid":   make_material("MatAcid",   (0.55, 0.95, 0.30, 1.0)),
        "red":    make_material("MatRed",    (0.85, 0.25, 0.20, 1.0)),
        "blue":   make_material("MatBlue",   (0.35, 0.65, 0.95, 1.0)),
        "ice":    make_material("MatIce",    (0.75, 0.90, 1.00, 1.0), roughness=0.35),
        "earth":  make_material("MatEarth",  (0.45, 0.32, 0.20, 1.0)),
        "metal":  make_material("MatMetal",  (0.55, 0.58, 0.62, 1.0), roughness=0.35, metallic=0.8),
        "purple": make_material("MatPurple", (0.55, 0.35, 0.80, 1.0)),
        "yellow": make_material("MatYellow", (0.95, 0.80, 0.20, 1.0), emission=0.2),
        "black":  make_material("MatBlack",  (0.08, 0.08, 0.08, 1.0), roughness=0.9),
        "white":  make_material("MatWhite",  (0.92, 0.92, 0.92, 1.0), roughness=0.5),
        "orange": make_material("MatOrange", (0.95, 0.48, 0.10, 1.0), emission=0.25),
        "pink":   make_material("MatPink",   (0.95, 0.45, 0.70, 1.0)),
    }

# ------------------------------------------------------------
# Shared part helpers
# ------------------------------------------------------------

def add_bug_legs(parts, mats, rng, count=6, x_span=0.8, y_span=0.36, z=-0.42, radius=0.07, depth=0.45):
    per_side = count // 2
    for side in (1, -1):
        for i in range(per_side):
            t = 0 if per_side == 1 else i / (per_side - 1)
            x = -x_span / 2 + t * x_span
            y = side * randf(rng, y_span * 0.8, y_span * 1.15)
            leg = add_cylinder(
                f"Leg_{side}_{i}",
                location=(x, y, randf(rng, z - 0.04, z + 0.04)),
                rotation=(deg(90), 0, deg(randf(rng, -25, 25))),
                radius=randf(rng, radius * 0.9, radius * 1.1),
                depth=randf(rng, depth * 0.9, depth * 1.1),
                vertices=8
            )
            assign_material(leg, mats["black"])
            parts.append(leg)

def add_eyes(parts, mats, rng, count=2, front_x=0.55, y_spread=0.18, z=0.12, eye_scale=0.10):
    for i in range(count):
        y = randf(rng, -y_spread, y_spread)
        eye = add_uv_sphere(
            f"Eye_{i}",
            location=(randf(rng, front_x - 0.08, front_x + 0.08), y, randf(rng, z - 0.06, z + 0.06)),
            scale=(eye_scale, eye_scale, eye_scale),
            segments=8,
            rings=4
        )
        assign_material(eye, mats["white"])
        parts.append(eye)

def add_spikes_radial(parts, mats, rng, count=4, radius=0.55, spike_radius=0.08, spike_depth=0.45, material_key="metal"):
    for i in range(count):
        angle = (math.tau / count) * i + randf(rng, -0.12, 0.12)
        spike = add_cone(
            f"Spike_{i}",
            location=(math.cos(angle) * radius, math.sin(angle) * radius, randf(rng, -0.06, 0.06)),
            rotation=(0, deg(90), angle),
            radius1=randf(rng, spike_radius * 0.9, spike_radius * 1.1),
            depth=randf(rng, spike_depth * 0.9, spike_depth * 1.1),
            vertices=8
        )
        assign_material(spike, mats[material_key])
        parts.append(spike)

# ------------------------------------------------------------
# Enemy builders
# ------------------------------------------------------------

def build_adhesion_bug(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.80, 1.00, 0.55), rng, 0.12, 0.12, 0.10))
    assign_material(body, mats["green"])
    parts.append(body)

    add_bug_legs(parts, mats, rng, count=randi(rng, 6, 8))
    add_eyes(parts, mats, rng, count=randi(rng, 2, 3), front_x=0.55, y_spread=0.16, z=0.10, eye_scale=0.09)

    if maybe(rng, 0.6):
        pad = add_torus(
            "StickyPad",
            location=(randf(rng, -0.1, 0.1), 0, -0.52),
            rotation=(deg(90), 0, 0),
            major_radius=randf(rng, 0.18, 0.28),
            minor_radius=randf(rng, 0.03, 0.06)
        )
        assign_material(pad, mats["green"])
        parts.append(pad)

    return join_objects(parts, "adhesion_bug")

def build_tar_slug(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((1.10, 0.70, 0.42), rng, 0.18, 0.10, 0.10))
    assign_material(body, mats["black"])
    parts.append(body)

    crest = add_uv_sphere("Crest", location=(-0.35, 0, 0.05), scale=vary_scale((0.45, 0.30, 0.18), rng, 0.10, 0.10, 0.15))
    assign_material(crest, mats["green"])
    parts.append(crest)

    add_eyes(parts, mats, rng, count=2, front_x=0.75, y_spread=0.10, z=0.12, eye_scale=0.08)

    return join_objects(parts, "tar_slug")

def build_glue_drone(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.60, 0.60, 0.40), rng, 0.10, 0.10, 0.10))
    assign_material(body, mats["metal"])
    parts.append(body)

    nozzle = add_cylinder(
        "Nozzle",
        location=(0.55, 0, 0),
        rotation=(0, deg(90), 0),
        radius=randf(rng, 0.09, 0.12),
        depth=randf(rng, 0.30, 0.42),
        vertices=8
    )
    assign_material(nozzle, mats["green"])
    parts.append(nozzle)

    add_spikes_radial(parts, mats, rng, count=4, radius=0.45, spike_radius=0.05, spike_depth=0.25, material_key="metal")

    return join_objects(parts, "glue_drone")

def build_acid_spitter(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.95, 0.75, 0.55), rng, 0.12, 0.10, 0.10))
    assign_material(body, mats["acid"])
    parts.append(body)

    for i in range(randi(rng, 1, 3)):
        sac = add_uv_sphere(
            f"Sac_{i}",
            location=(randf(rng, -0.70, -0.25), randf(rng, -0.25, 0.25), randf(rng, -0.05, 0.20)),
            scale=(randf(rng, 0.18, 0.32), randf(rng, 0.18, 0.32), randf(rng, 0.18, 0.28)),
            segments=12,
            rings=6
        )
        assign_material(sac, mats["green"])
        parts.append(sac)

    mouth = add_uv_sphere(
        "Mouth",
        location=(randf(rng, 0.62, 0.80), 0, randf(rng, -0.08, 0.08)),
        scale=(randf(rng, 0.18, 0.26), randf(rng, 0.15, 0.22), randf(rng, 0.12, 0.18)),
        segments=10,
        rings=5
    )
    assign_material(mouth, mats["black"])
    parts.append(mouth)

    return join_objects(parts, "acid_spitter")

def build_melt_worm(mats, rng):
    parts = []

    segment_count = randi(rng, 4, 6)
    for i in range(segment_count):
        seg = add_uv_sphere(
            f"Seg_{i}",
            location=(-0.4 * i, 0, randf(rng, -0.03, 0.03)),
            scale=vary_scale((0.28 + i * 0.03, 0.24 + i * 0.02, 0.22), rng, 0.08, 0.08, 0.08),
            segments=12,
            rings=6
        )
        assign_material(seg, mats["acid"] if i < segment_count - 1 else mats["green"])
        parts.append(seg)

    return join_objects(parts, "melt_worm")

def build_corrosion_beetle(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.70, 0.90, 0.42), rng, 0.10, 0.10, 0.10))
    assign_material(body, mats["acid"])
    parts.append(body)

    shell = add_uv_sphere("Shell", location=(0, 0, 0.10), scale=vary_scale((0.82, 1.00, 0.36), rng, 0.08, 0.08, 0.08))
    assign_material(shell, mats["green"])
    parts.append(shell)

    add_bug_legs(parts, mats, rng, count=6, x_span=0.65, y_span=0.30, z=-0.34, radius=0.06, depth=0.36)

    return join_objects(parts, "corrosion_beetle")

def build_claw_crawler(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.75, 0.95, 0.40), rng, 0.10, 0.10, 0.10))
    assign_material(body, mats["red"])
    parts.append(body)

    add_bug_legs(parts, mats, rng, count=6, x_span=0.65, y_span=0.32, z=-0.36, radius=0.06, depth=0.34)

    for side in (1, -1):
        claw = add_cone(
            f"Claw_{side}",
            location=(0.65, side * 0.25, 0),
            rotation=(0, deg(90), deg(20 * side)),
            radius1=randf(rng, 0.14, 0.18),
            depth=randf(rng, 0.38, 0.50),
            vertices=8
        )
        assign_material(claw, mats["white"])
        parts.append(claw)

    return join_objects(parts, "claw_crawler")

def build_ripper_bat(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.45, 0.35, 0.35), rng, 0.10, 0.10, 0.10))
    assign_material(body, mats["purple"])
    parts.append(body)

    for side in (1, -1):
        wing = add_cube(
            f"Wing_{side}",
            location=(0, side * 0.42, 0.02),
            scale=(randf(rng, 0.12, 0.18), randf(rng, 0.38, 0.52), randf(rng, 0.02, 0.04)),
            rotation=(0, deg(randf(rng, -8, 8)), deg(side * randf(rng, 8, 20)))
        )
        assign_material(wing, mats["red"])
        parts.append(wing)

    for side in (1, -1):
        blade = add_cone(
            f"Blade_{side}",
            location=(0.28, side * 0.55, 0.02),
            rotation=(0, deg(90), deg(side * 30)),
            radius1=0.08,
            depth=0.28,
            vertices=8
        )
        assign_material(blade, mats["white"])
        parts.append(blade)

    return join_objects(parts, "ripper_bat")

def build_razor_lizard(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((1.00, 0.42, 0.32), rng, 0.12, 0.08, 0.08))
    assign_material(body, mats["red"])
    parts.append(body)

    head = add_cone(
        "Head",
        location=(0.72, 0, 0.02),
        rotation=(0, deg(90), 0),
        radius1=randf(rng, 0.22, 0.28),
        depth=randf(rng, 0.45, 0.60),
        vertices=10
    )
    assign_material(head, mats["white"])
    parts.append(head)

    for i in range(randi(rng, 3, 5)):
        spike = add_cone(
            f"BackSpike_{i}",
            location=(-0.30 + i * 0.28, 0, 0.25),
            rotation=(deg(-90), 0, 0),
            radius1=0.05,
            depth=randf(rng, 0.18, 0.28),
            vertices=8
        )
        assign_material(spike, mats["white"])
        parts.append(spike)

    return join_objects(parts, "razor_lizard")

def build_carapace_husk(mats, rng):
    parts = []

    body = add_uv_sphere("Body", location=(0, 0, -0.1), scale=vary_scale((0.75, 0.90, 0.42), rng, 0.10, 0.10, 0.08))
    assign_material(body, mats["earth"])
    parts.append(body)

    shell = add_uv_sphere("Shell", location=(0, 0, 0.15), scale=vary_scale((0.95, 1.05, 0.55), rng, 0.08, 0.08, 0.08))
    assign_material(shell, mats["metal"])
    parts.append(shell)

    add_bug_legs(parts, mats, rng, count=4, x_span=0.70, y_span=0.30, z=-0.35, radius=0.07, depth=0.30)

    return join_objects(parts, "carapace_husk")

def build_shell_roller(mats, rng):
    parts = []

    shell = add_uv_sphere("Shell", scale=vary_scale((0.70, 0.70, 0.70), rng, 0.10, 0.10, 0.10))
    assign_material(shell, mats["metal"])
    parts.append(shell)

    band = add_torus("Band", major_radius=randf(rng, 0.52, 0.65), minor_radius=randf(rng, 0.06, 0.10))
    assign_material(band, mats["earth"])
    parts.append(band)

    return join_objects(parts, "shell_roller")

def build_fortress_bug(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.82, 1.10, 0.38), rng, 0.08, 0.08, 0.08))
    assign_material(body, mats["earth"])
    parts.append(body)

    for i, y in enumerate((-0.28, 0, 0.28)):
        plate = add_cube(
            f"Plate_{i}",
            location=(0.10, y, 0.18),
            scale=(randf(rng, 0.40, 0.55), randf(rng, 0.10, 0.16), randf(rng, 0.10, 0.14)),
            rotation=(0, deg(randf(rng, -8, 8)), 0)
        )
        assign_material(plate, mats["metal"])
        parts.append(plate)

    add_bug_legs(parts, mats, rng, count=6, x_span=0.70, y_span=0.34, z=-0.34, radius=0.06, depth=0.32)

    return join_objects(parts, "fortress_bug")

def build_electric_node(mats, rng):
    parts = []

    core = add_uv_sphere("Core", scale=vary_scale((0.55, 0.55, 0.55), rng, 0.10, 0.10, 0.10), segments=12, rings=6)
    assign_material(core, mats["yellow"])
    parts.append(core)

    add_spikes_radial(parts, mats, rng, count=randi(rng, 4, 6), radius=randf(rng, 0.48, 0.58), spike_radius=0.08, spike_depth=0.42)

    return join_objects(parts, "electric_node")

def build_shock_jelly(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.72, 0.72, 0.58), rng, 0.10, 0.10, 0.12))
    assign_material(body, mats["blue"])
    parts.append(body)

    for i in range(randi(rng, 3, 5)):
        arc = add_cone(
            f"Arc_{i}",
            location=(randf(rng, -0.30, 0.30), randf(rng, -0.30, 0.30), randf(rng, 0.10, 0.35)),
            rotation=(deg(randf(rng, -40, 40)), deg(randf(rng, -40, 40)), deg(randf(rng, -180, 180))),
            radius1=0.04,
            depth=randf(rng, 0.18, 0.28),
            vertices=6
        )
        assign_material(arc, mats["yellow"])
        parts.append(arc)

    return join_objects(parts, "shock_jelly")

def build_tesla_wasp(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.40, 0.32, 0.28), rng, 0.10, 0.10, 0.10))
    assign_material(body, mats["yellow"])
    parts.append(body)

    for side in (1, -1):
        wing = add_cube(
            f"Wing_{side}",
            location=(-0.05, side * 0.25, 0.12),
            scale=(0.08, randf(rng, 0.24, 0.34), 0.02),
            rotation=(deg(randf(rng, -10, 10)), 0, deg(side * randf(rng, 12, 22)))
        )
        assign_material(wing, mats["white"])
        parts.append(wing)

    for side in (1, -1):
        stinger = add_cone(
            f"Stinger_{side}",
            location=(0.32, side * 0.12, 0),
            rotation=(0, deg(90), deg(side * 8)),
            radius1=0.05,
            depth=0.18,
            vertices=8
        )
        assign_material(stinger, mats["black"])
        parts.append(stinger)

    return join_objects(parts, "tesla_wasp")

def build_tendril_beast(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.72, 0.80, 0.60), rng, 0.10, 0.10, 0.12))
    assign_material(body, mats["purple"])
    parts.append(body)

    for i in range(randi(rng, 3, 5)):
        tendril = add_cylinder(
            f"Tendril_{i}",
            location=(randf(rng, -0.15, 0.15), randf(rng, -0.20, 0.20), randf(rng, -0.25, 0.05)),
            rotation=(deg(randf(rng, 65, 115)), deg(randf(rng, -20, 20)), deg(randf(rng, -180, 180))),
            radius=randf(rng, 0.05, 0.08),
            depth=randf(rng, 0.50, 0.80),
            vertices=8
        )
        assign_material(tendril, mats["purple"])
        parts.append(tendril)

    return join_objects(parts, "tendril_beast")

def build_vine_creeper(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.55, 0.55, 0.55), rng, 0.08, 0.08, 0.10))
    assign_material(body, mats["green"])
    parts.append(body)

    for i in range(randi(rng, 4, 6)):
        vine = add_cylinder(
            f"Vine_{i}",
            location=(randf(rng, -0.10, 0.10), randf(rng, -0.10, 0.10), randf(rng, -0.15, 0.05)),
            rotation=(deg(randf(rng, 50, 130)), deg(randf(rng, -30, 30)), deg(randf(rng, -180, 180))),
            radius=randf(rng, 0.04, 0.06),
            depth=randf(rng, 0.45, 0.75),
            vertices=8
        )
        assign_material(vine, mats["green"])
        parts.append(vine)

    return join_objects(parts, "vine_creeper")

def build_lash_parasite(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.35, 0.25, 0.25), rng, 0.10, 0.10, 0.10))
    assign_material(body, mats["purple"])
    parts.append(body)

    lash = add_cylinder(
        "Lash",
        location=(0.25, 0, 0),
        rotation=(0, deg(90), deg(randf(rng, -20, 20))),
        radius=0.04,
        depth=randf(rng, 0.60, 0.90),
        vertices=8
    )
    assign_material(lash, mats["purple"])
    parts.append(lash)

    hook = add_cone(
        "Hook",
        location=(0.65, 0, 0),
        rotation=(0, deg(90), 0),
        radius1=0.05,
        depth=0.18,
        vertices=8
    )
    assign_material(hook, mats["white"])
    parts.append(hook)

    return join_objects(parts, "lash_parasite")

def build_ember_imp(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.55, 0.48, 0.60), rng, 0.10, 0.10, 0.12))
    assign_material(body, mats["orange"])
    parts.append(body)

    for i in range(randi(rng, 3, 5)):
        horn = add_cone(
            f"Horn_{i}",
            location=(randf(rng, -0.18, 0.18), randf(rng, -0.18, 0.18), randf(rng, 0.20, 0.40)),
            rotation=(deg(randf(rng, -20, 20)), deg(randf(rng, -20, 20)), deg(randf(rng, -180, 180))),
            radius1=0.05,
            depth=randf(rng, 0.16, 0.24),
            vertices=8
        )
        assign_material(horn, mats["yellow"])
        parts.append(horn)

    return join_objects(parts, "ember_imp")

def build_flame_hopper(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.62, 0.55, 0.42), rng, 0.10, 0.10, 0.10))
    assign_material(body, mats["orange"])
    parts.append(body)

    for side in (1, -1):
        leg = add_cylinder(
            f"Leg_{side}",
            location=(-0.10, side * 0.16, -0.28),
            rotation=(deg(90), 0, deg(side * 10)),
            radius=0.05,
            depth=0.35,
            vertices=8
        )
        assign_material(leg, mats["black"])
        parts.append(leg)

    mouth = add_uv_sphere("Mouth", location=(0.32, 0, 0.02), scale=(0.12, 0.10, 0.08), segments=8, rings=4)
    assign_material(mouth, mats["black"])
    parts.append(mouth)

    return join_objects(parts, "flame_hopper")

def build_cinder_snake(mats, rng):
    parts = []

    seg_count = randi(rng, 5, 7)
    for i in range(seg_count):
        seg = add_uv_sphere(
            f"Seg_{i}",
            location=(-0.32 * i, 0, randf(rng, -0.03, 0.03)),
            scale=vary_scale((0.28 - i * 0.01, 0.22 - i * 0.01, 0.20), rng, 0.08, 0.08, 0.08),
            segments=12,
            rings=6
        )
        assign_material(seg, mats["orange"])
        parts.append(seg)

    flame = add_cone(
        "FlameTail",
        location=(-0.32 * seg_count, 0, 0.03),
        rotation=(0, deg(90), 0),
        radius1=0.08,
        depth=0.24,
        vertices=8
    )
    assign_material(flame, mats["yellow"])
    parts.append(flame)

    return join_objects(parts, "cinder_snake")

def build_frost_jelly(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.72, 0.72, 0.58), rng, 0.10, 0.10, 0.12))
    assign_material(body, mats["ice"])
    parts.append(body)

    for i in range(randi(rng, 3, 5)):
        crystal = add_cone(
            f"Crystal_{i}",
            location=(randf(rng, -0.20, 0.20), randf(rng, -0.20, 0.20), randf(rng, 0.05, 0.28)),
            rotation=(deg(randf(rng, -15, 15)), deg(randf(rng, -15, 15)), deg(randf(rng, -180, 180))),
            radius1=0.05,
            depth=randf(rng, 0.16, 0.28),
            vertices=6
        )
        assign_material(crystal, mats["blue"])
        parts.append(crystal)

    return join_objects(parts, "frost_jelly")

def build_glacier_crab(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.70, 0.90, 0.36), rng, 0.10, 0.10, 0.08))
    assign_material(body, mats["blue"])
    parts.append(body)

    add_bug_legs(parts, mats, rng, count=6, x_span=0.70, y_span=0.32, z=-0.30, radius=0.05, depth=0.30)

    for side in (1, -1):
        claw = add_cone(
            f"Claw_{side}",
            location=(0.58, side * 0.22, 0.02),
            rotation=(0, deg(90), deg(side * 15)),
            radius1=0.10,
            depth=0.30,
            vertices=8
        )
        assign_material(claw, mats["ice"])
        parts.append(claw)

    return join_objects(parts, "glacier_crab")

def build_snow_wisp(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.45, 0.45, 0.55), rng, 0.10, 0.10, 0.12))
    assign_material(body, mats["white"])
    parts.append(body)

    for i in range(randi(rng, 4, 6)):
        shard = add_cone(
            f"Shard_{i}",
            location=(randf(rng, -0.24, 0.24), randf(rng, -0.24, 0.24), randf(rng, -0.10, 0.20)),
            rotation=(deg(randf(rng, -40, 40)), deg(randf(rng, -40, 40)), deg(randf(rng, -180, 180))),
            radius1=0.04,
            depth=randf(rng, 0.14, 0.24),
            vertices=6
        )
        assign_material(shard, mats["ice"])
        parts.append(shard)

    return join_objects(parts, "snow_wisp")

def build_stone_burrower(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.70, 0.55, 0.40), rng, 0.10, 0.10, 0.10))
    assign_material(body, mats["earth"])
    parts.append(body)

    nose = add_cone(
        "Nose",
        location=(0.45, 0, 0.02),
        rotation=(0, deg(90), 0),
        radius1=0.14,
        depth=0.30,
        vertices=8
    )
    assign_material(nose, mats["metal"])
    parts.append(nose)

    add_eyes(parts, mats, rng, count=2, front_x=0.18, y_spread=0.10, z=0.12, eye_scale=0.06)

    return join_objects(parts, "stone_burrower")

def build_boulder_golem(mats, rng):
    parts = []

    body = add_cube(
        "Body",
        scale=vary_scale((0.45, 0.45, 0.45), rng, 0.12, 0.12, 0.12),
        rotation=(deg(randf(rng, -8, 8)), deg(randf(rng, -8, 8)), deg(randf(rng, -8, 8)))
    )
    assign_material(body, mats["earth"])
    parts.append(body)

    for side in (1, -1):
        arm = add_cube(
            f"Arm_{side}",
            location=(0, side * 0.42, -0.02),
            scale=(0.16, 0.12, 0.12),
            rotation=(0, 0, deg(side * randf(rng, 10, 25)))
        )
        assign_material(arm, mats["earth"])
        parts.append(arm)

    return join_objects(parts, "boulder_golem")

def build_mud_stomper(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.78, 0.60, 0.52), rng, 0.10, 0.10, 0.10))
    assign_material(body, mats["earth"])
    parts.append(body)

    for side in (1, -1):
        foot = add_cube(
            f"Foot_{side}",
            location=(-0.10, side * 0.18, -0.35),
            scale=(0.16, 0.12, 0.08)
        )
        assign_material(foot, mats["black"])
        parts.append(foot)

    return join_objects(parts, "mud_stomper")

def build_gale_sprite(mats, rng):
    parts = []

    body = add_torus(
        "Body",
        major_radius=randf(rng, 0.35, 0.48),
        minor_radius=randf(rng, 0.08, 0.12),
        rotation=(deg(90), 0, deg(randf(rng, -20, 20)))
    )
    assign_material(body, mats["white"])
    parts.append(body)

    core = add_uv_sphere("Core", scale=(0.14, 0.14, 0.14), segments=8, rings=4)
    assign_material(core, mats["blue"])
    parts.append(core)

    return join_objects(parts, "gale_sprite")

def build_cyclone_bird(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.40, 0.28, 0.25), rng, 0.10, 0.10, 0.10))
    assign_material(body, mats["white"])
    parts.append(body)

    for side in (1, -1):
        wing = add_cube(
            f"Wing_{side}",
            location=(0, side * 0.28, 0.02),
            scale=(0.12, randf(rng, 0.28, 0.40), 0.02),
            rotation=(0, deg(randf(rng, -8, 8)), deg(side * randf(rng, 10, 20)))
        )
        assign_material(wing, mats["blue"])
        parts.append(wing)

    beak = add_cone("Beak", location=(0.26, 0, 0), rotation=(0, deg(90), 0), radius1=0.05, depth=0.18, vertices=8)
    assign_material(beak, mats["yellow"])
    parts.append(beak)

    return join_objects(parts, "cyclone_bird")

def build_gust_hopper(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.50, 0.32, 0.28), rng, 0.10, 0.10, 0.10))
    assign_material(body, mats["green"])
    parts.append(body)

    for side in (1, -1):
        leg = add_cylinder(
            f"Leg_{side}",
            location=(-0.05, side * 0.12, -0.24),
            rotation=(deg(90), 0, deg(side * 15)),
            radius=0.04,
            depth=0.36,
            vertices=8
        )
        assign_material(leg, mats["black"])
        parts.append(leg)

    return join_objects(parts, "gust_hopper")

def build_ferro_drone(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.52, 0.52, 0.35), rng, 0.08, 0.08, 0.08))
    assign_material(body, mats["metal"])
    parts.append(body)

    for side in (1, -1):
        magnet = add_cube(
            f"Magnet_{side}",
            location=(0, side * 0.32, 0),
            scale=(0.10, 0.16, 0.08)
        )
        assign_material(magnet, mats["red"] if side == 1 else mats["blue"])
        parts.append(magnet)

    core = add_uv_sphere("Core", scale=(0.10, 0.10, 0.10), segments=8, rings=4)
    assign_material(core, mats["yellow"])
    parts.append(core)

    return join_objects(parts, "ferro_drone")

def build_iron_beetle(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.70, 0.92, 0.40), rng, 0.08, 0.08, 0.08))
    assign_material(body, mats["metal"])
    parts.append(body)

    shell = add_cube(
        "Shell",
        location=(0, 0, 0.10),
        scale=(0.44, 0.56, 0.16),
        rotation=(0, 0, deg(randf(rng, -6, 6)))
    )
    assign_material(shell, mats["black"])
    parts.append(shell)

    add_bug_legs(parts, mats, rng, count=6, x_span=0.68, y_span=0.34, z=-0.30, radius=0.05, depth=0.32)

    return join_objects(parts, "iron_beetle")

def build_scrap_slime(mats, rng):
    parts = []

    body = add_uv_sphere("Body", scale=vary_scale((0.78, 0.72, 0.55), rng, 0.10, 0.10, 0.10))
    assign_material(body, mats["metal"])
    parts.append(body)

    for i in range(randi(rng, 3, 5)):
        plate = add_cube(
            f"Plate_{i}",
            location=(randf(rng, -0.22, 0.22), randf(rng, -0.22, 0.22), randf(rng, -0.05, 0.20)),
            scale=(randf(rng, 0.10, 0.18), randf(rng, 0.08, 0.16), randf(rng, 0.04, 0.08)),
            rotation=(deg(randf(rng, -30, 30)), deg(randf(rng, -30, 30)), deg(randf(rng, -30, 30)))
        )
        assign_material(plate, mats["black"])
        parts.append(plate)

    return join_objects(parts, "scrap_slime")

def build_blade_sentinel(mats, rng):
    parts = []

    blade = add_cube(
        "Blade",
        scale=(randf(rng, 0.10, 0.16), randf(rng, 0.85, 1.10), randf(rng, 0.08, 0.12))
    )
    assign_material(blade, mats["metal"])
    parts.append(blade)

    tip = add_cone(
        "Tip",
        location=(0, randf(rng, 0.95, 1.20), 0),
        rotation=(deg(90), 0, 0),
        radius1=randf(rng, 0.10, 0.16),
        depth=randf(rng, 0.22, 0.36),
        vertices=8
    )
    assign_material(tip, mats["metal"])
    parts.append(tip)

    guard = add_cube(
        "Guard",
        location=(0, randf(rng, -0.55, -0.45), 0),
        scale=(randf(rng, 0.30, 0.48), randf(rng, 0.06, 0.10), randf(rng, 0.08, 0.12))
    )
    assign_material(guard, mats["yellow"])
    parts.append(guard)

    eye = add_uv_sphere("Eye", location=(0, randf(rng, -0.78, -0.60), 0), scale=(0.12, 0.12, 0.12), segments=8, rings=4)
    assign_material(eye, mats["purple"])
    parts.append(eye)

    return join_objects(parts, "blade_sentinel")

def build_duel_knight(mats, rng):
    parts = []

    body = add_cube(
        "Body",
        scale=vary_scale((0.26, 0.22, 0.40), rng, 0.08, 0.08, 0.08)
    )
    assign_material(body, mats["metal"])
    parts.append(body)

    head = add_uv_sphere("Head", location=(0, 0, 0.32), scale=(0.14, 0.14, 0.14), segments=8, rings=4)
    assign_material(head, mats["metal"])
    parts.append(head)

    sword = add_cube("Sword", location=(0.28, 0, 0.06), scale=(0.06, 0.34, 0.04), rotation=(0, 0, deg(15)))
    assign_material(sword, mats["white"])
    parts.append(sword)

    return join_objects(parts, "duel_knight")

def build_cutter_wisp(mats, rng):
    parts = []

    core = add_uv_sphere("Core", scale=vary_scale((0.22, 0.22, 0.22), rng, 0.08, 0.08, 0.08), segments=8, rings=4)
    assign_material(core, mats["purple"])
    parts.append(core)

    for i in range(randi(rng, 3, 4)):
        angle = i * (math.tau / 4.0)
        blade = add_cube(
            f"Blade_{i}",
            location=(math.cos(angle) * 0.34, math.sin(angle) * 0.34, 0),
            scale=(0.06, 0.22, 0.03),
            rotation=(0, 0, angle + deg(45))
        )
        assign_material(blade, mats["metal"])
        parts.append(blade)

    return join_objects(parts, "cutter_wisp")

def build_spear_wisp(mats, rng):
    parts = []

    shaft = add_cylinder(
        "Shaft",
        rotation=(0, deg(90), 0),
        radius=0.04,
        depth=randf(rng, 1.00, 1.30),
        vertices=8
    )
    assign_material(shaft, mats["earth"])
    parts.append(shaft)

    tip = add_cone(
        "Tip",
        location=(0.62, 0, 0),
        rotation=(0, deg(90), 0),
        radius1=0.10,
        depth=0.28,
        vertices=8
    )
    assign_material(tip, mats["metal"])
    parts.append(tip)

    core = add_uv_sphere("Core", location=(-0.45, 0, 0), scale=(0.10, 0.10, 0.10), segments=8, rings=4)
    assign_material(core, mats["purple"])
    parts.append(core)

    return join_objects(parts, "spear_wisp")

def build_pike_guard(mats, rng):
    parts = []

    base = add_cube("Base", scale=(0.22, 0.22, 0.22))
    assign_material(base, mats["metal"])
    parts.append(base)

    pike = add_cylinder("Pike", location=(0.40, 0, 0.10), rotation=(0, deg(90), 0), radius=0.03, depth=0.90, vertices=8)
    assign_material(pike, mats["earth"])
    parts.append(pike)

    tip = add_cone("Tip", location=(0.85, 0, 0.10), rotation=(0, deg(90), 0), radius1=0.08, depth=0.18, vertices=8)
    assign_material(tip, mats["metal"])
    parts.append(tip)

    return join_objects(parts, "pike_guard")

def build_harpoon_eel(mats, rng):
    parts = []

    seg_count = randi(rng, 4, 6)
    for i in range(seg_count):
        seg = add_uv_sphere(
            f"Seg_{i}",
            location=(-0.26 * i, 0, 0),
            scale=vary_scale((0.20 + 0.03 * i, 0.14, 0.14), rng, 0.08, 0.08, 0.08),
            segments=10,
            rings=5
        )
        assign_material(seg, mats["blue"])
        parts.append(seg)

    tip = add_cone("HarpoonTip", location=(0.25, 0, 0), rotation=(0, deg(90), 0), radius1=0.08, depth=0.24, vertices=8)
    assign_material(tip, mats["metal"])
    parts.append(tip)

    return join_objects(parts, "harpoon_eel")

def build_knuckle_sprite(mats, rng):
    parts = []

    fist = add_cube("Fist", scale=vary_scale((0.26, 0.22, 0.20), rng, 0.10, 0.10, 0.10))
    assign_material(fist, mats["red"])
    parts.append(fist)

    cuff = add_cylinder("Cuff", location=(-0.22, 0, 0), rotation=(0, deg(90), 0), radius=0.07, depth=0.20, vertices=8)
    assign_material(cuff, mats["white"])
    parts.append(cuff)

    return join_objects(parts, "knuckle_sprite")

def build_slam_golem(mats, rng):
    parts = []

    body = add_cube("Body", scale=vary_scale((0.30, 0.30, 0.34), rng, 0.08, 0.08, 0.08))
    assign_material(body, mats["earth"])
    parts.append(body)

    for side in (1, -1):
        fist = add_cube(
            f"Fist_{side}",
            location=(0, side * 0.34, -0.02),
            scale=(0.16, 0.14, 0.14)
        )
        assign_material(fist, mats["earth"])
        parts.append(fist)

    return join_objects(parts, "slam_golem")

def build_boxer_bot(mats, rng):
    parts = []

    body = add_cube("Body", scale=vary_scale((0.26, 0.22, 0.32), rng, 0.08, 0.08, 0.08))
    assign_material(body, mats["metal"])
    parts.append(body)

    for side in (1, -1):
        glove = add_cube(
            f"Glove_{side}",
            location=(0.12, side * 0.28, 0.04),
            scale=(0.12, 0.10, 0.10)
        )
        assign_material(glove, mats["red"])
        parts.append(glove)

    return join_objects(parts, "boxer_bot")

def build_ring_drone(mats, rng):
    parts = []

    ring = add_torus("Ring", major_radius=randf(rng, 0.65, 0.80), minor_radius=randf(rng, 0.09, 0.13))
    assign_material(ring, mats["metal"])
    parts.append(ring)

    core = add_uv_sphere("Core", scale=(0.20, 0.20, 0.20), segments=10, rings=5)
    assign_material(core, mats["red"])
    parts.append(core)

    return join_objects(parts, "ring_drone")

def build_orbit_wisp(mats, rng):
    parts = []

    core = add_uv_sphere("Core", scale=(0.18, 0.18, 0.18), segments=8, rings=4)
    assign_material(core, mats["purple"])
    parts.append(core)

    ring = add_torus(
        "Orbit",
        major_radius=randf(rng, 0.30, 0.42),
        minor_radius=randf(rng, 0.04, 0.07),
        rotation=(deg(randf(rng, 0, 50)), deg(randf(rng, 0, 50)), deg(randf(rng, 0, 50)))
    )
    assign_material(ring, mats["white"])
    parts.append(ring)

    return join_objects(parts, "orbit_wisp")

def build_halo_spinner(mats, rng):
    parts = []

    halo = add_torus("Halo", major_radius=randf(rng, 0.42, 0.56), minor_radius=randf(rng, 0.08, 0.10))
    assign_material(halo, mats["yellow"])
    parts.append(halo)

    for i in range(randi(rng, 3, 4)):
        angle = i * (math.tau / 4.0)
        blade = add_cone(
            f"Blade_{i}",
            location=(math.cos(angle) * 0.45, math.sin(angle) * 0.45, 0),
            rotation=(0, deg(90), angle),
            radius1=0.05,
            depth=0.18,
            vertices=8
        )
        assign_material(blade, mats["metal"])
        parts.append(blade)

    return join_objects(parts, "halo_spinner")

# ------------------------------------------------------------
# Builder registry
# ------------------------------------------------------------

BUILDERS = {
    "adhesion_bug": build_adhesion_bug,
    "tar_slug": build_tar_slug,
    "glue_drone": build_glue_drone,
    "acid_spitter": build_acid_spitter,
    "melt_worm": build_melt_worm,
    "corrosion_beetle": build_corrosion_beetle,
    "claw_crawler": build_claw_crawler,
    "ripper_bat": build_ripper_bat,
    "razor_lizard": build_razor_lizard,
    "carapace_husk": build_carapace_husk,
    "shell_roller": build_shell_roller,
    "fortress_bug": build_fortress_bug,
    "electric_node": build_electric_node,
    "shock_jelly": build_shock_jelly,
    "tesla_wasp": build_tesla_wasp,
    "tendril_beast": build_tendril_beast,
    "vine_creeper": build_vine_creeper,
    "lash_parasite": build_lash_parasite,
    "ember_imp": build_ember_imp,
    "flame_hopper": build_flame_hopper,
    "cinder_snake": build_cinder_snake,
    "frost_jelly": build_frost_jelly,
    "glacier_crab": build_glacier_crab,
    "snow_wisp": build_snow_wisp,
    "stone_burrower": build_stone_burrower,
    "boulder_golem": build_boulder_golem,
    "mud_stomper": build_mud_stomper,
    "gale_sprite": build_gale_sprite,
    "cyclone_bird": build_cyclone_bird,
    "gust_hopper": build_gust_hopper,
    "ferro_drone": build_ferro_drone,
    "iron_beetle": build_iron_beetle,
    "scrap_slime": build_scrap_slime,
    "blade_sentinel": build_blade_sentinel,
    "duel_knight": build_duel_knight,
    "cutter_wisp": build_cutter_wisp,
    "spear_wisp": build_spear_wisp,
    "pike_guard": build_pike_guard,
    "harpoon_eel": build_harpoon_eel,
    "knuckle_sprite": build_knuckle_sprite,
    "slam_golem": build_slam_golem,
    "boxer_bot": build_boxer_bot,
    "ring_drone": build_ring_drone,
    "orbit_wisp": build_orbit_wisp,
    "halo_spinner": build_halo_spinner,
}

# ------------------------------------------------------------
# Export
# ------------------------------------------------------------

def export_variant(obj, base_name, variant_index):
    ensure_export_dir()
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    filepath = os.path.join(EXPORT_DIR, f"{base_name}_{variant_index:02d}.glb")
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLB',
        use_selection=True,
        export_apply=True
    )
    print(f"Exported: {filepath}")

# ------------------------------------------------------------
# Batch generation
# ------------------------------------------------------------

def build_enemy_variant(enemy_name, builder, mats, variant_index):
    clear_scene()
    rng = random.Random(f"{enemy_name}_{variant_index}")
    obj = builder(mats, rng)
    set_origin_to_geometry(obj)
    return obj

def build_all_variants(variants_per_enemy=3):
    mats = build_materials()

    for enemy_name, builder in BUILDERS.items():
        for i in range(variants_per_enemy):
            obj = build_enemy_variant(enemy_name, builder, mats, i)
            export_variant(obj, enemy_name, i)

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

if __name__ == "__main__":
    build_all_variants(variants_per_enemy=VARIANTS_PER_ENEMY)
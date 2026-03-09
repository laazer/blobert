import bpy
import math
import os

EXPORT_DIR = os.path.abspath("//../exports")

# --------------------------------------------------
# Utilities
# --------------------------------------------------

def ensure_export_dir():
    os.makedirs(EXPORT_DIR, exist_ok=True)

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Remove orphan meshes/materials
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

def smooth(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()

def set_origin_to_geometry(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

def apply_scale(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

def make_material(name, color_rgba):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = color_rgba
        bsdf.inputs["Roughness"].default_value = 0.65
    return mat

def assign_material(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

def join_objects(objects, name):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    objects[0].name = name
    return objects[0]

# --------------------------------------------------
# Primitive creators
# --------------------------------------------------

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

def add_cube(name, location=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_cube_add(location=location)
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

# --------------------------------------------------
# Shared materials
# --------------------------------------------------

def build_materials():
    return {
        "green": make_material("MatGreen", (0.30, 0.75, 0.35, 1.0)),
        "acid": make_material("MatAcid", (0.55, 0.95, 0.30, 1.0)),
        "red": make_material("MatRed", (0.85, 0.25, 0.20, 1.0)),
        "blue": make_material("MatBlue", (0.35, 0.65, 0.95, 1.0)),
        "earth": make_material("MatEarth", (0.45, 0.32, 0.20, 1.0)),
        "metal": make_material("MatMetal", (0.55, 0.58, 0.62, 1.0)),
        "purple": make_material("MatPurple", (0.55, 0.35, 0.80, 1.0)),
        "yellow": make_material("MatYellow", (0.95, 0.80, 0.20, 1.0)),
        "black": make_material("MatBlack", (0.08, 0.08, 0.08, 1.0)),
        "white": make_material("MatWhite", (0.92, 0.92, 0.92, 1.0)),
    }

# --------------------------------------------------
# Enemy builders
# --------------------------------------------------

def build_adhesion_bug(mats):
    parts = []

    body = add_uv_sphere("Body", scale=(0.8, 1.0, 0.55))
    assign_material(body, mats["green"])
    parts.append(body)

    # 6 legs
    leg_positions = [
        (-0.45, 0.35, -0.45), (0.0, 0.4, -0.45), (0.45, 0.35, -0.45),
        (-0.45, -0.35, -0.45), (0.0, -0.4, -0.45), (0.45, -0.35, -0.45),
    ]
    for i, pos in enumerate(leg_positions):
        leg = add_cylinder(
            f"Leg_{i}",
            location=pos,
            rotation=(math.radians(90), 0, math.radians(20 if pos[1] > 0 else -20)),
            radius=0.07,
            depth=0.45,
            vertices=8
        )
        assign_material(leg, mats["black"])
        parts.append(leg)

    # eyes
    for i, y in enumerate((0.18, -0.18)):
        eye = add_uv_sphere(f"Eye_{i}", location=(0.55, y, 0.1), scale=(0.10, 0.10, 0.10), segments=8, rings=4)
        assign_material(eye, mats["white"])
        parts.append(eye)

    return join_objects(parts, "adhesion_bug")

def build_acid_spitter(mats):
    parts = []

    body = add_uv_sphere("Body", scale=(0.95, 0.75, 0.55))
    assign_material(body, mats["acid"])
    parts.append(body)

    sack = add_uv_sphere("Sack", location=(-0.55, 0, 0.05), scale=(0.35, 0.35, 0.28), segments=12, rings=6)
    assign_material(sack, mats["green"])
    parts.append(sack)

    mouth = add_uv_sphere("Mouth", location=(0.72, 0, -0.02), scale=(0.22, 0.18, 0.16), segments=10, rings=5)
    assign_material(mouth, mats["black"])
    parts.append(mouth)

    return join_objects(parts, "acid_spitter")

def build_carapace_husk(mats):
    parts = []

    body = add_uv_sphere("Body", location=(0, 0, -0.1), scale=(0.75, 0.9, 0.42))
    assign_material(body, mats["earth"])
    parts.append(body)

    shell = add_uv_sphere("Shell", location=(0, 0, 0.15), scale=(0.95, 1.05, 0.55))
    assign_material(shell, mats["metal"])
    parts.append(shell)

    leg_positions = [
        (-0.38, 0.32, -0.38), (0.38, 0.32, -0.38),
        (-0.38, -0.32, -0.38), (0.38, -0.32, -0.38),
    ]
    for i, pos in enumerate(leg_positions):
        leg = add_cylinder(
            f"Leg_{i}",
            location=pos,
            rotation=(math.radians(90), 0, 0),
            radius=0.08,
            depth=0.35,
            vertices=8
        )
        assign_material(leg, mats["black"])
        parts.append(leg)

    return join_objects(parts, "carapace_husk")

def build_electric_node(mats):
    parts = []

    core = add_uv_sphere("Core", scale=(0.55, 0.55, 0.55), segments=12, rings=6)
    assign_material(core, mats["yellow"])
    parts.append(core)

    for i, angle_deg in enumerate((0, 90, 180, 270)):
        angle = math.radians(angle_deg)
        spike = add_cone(
            f"Spike_{i}",
            location=(math.cos(angle) * 0.55, math.sin(angle) * 0.55, 0),
            rotation=(0, math.radians(90), angle),
            radius1=0.08,
            depth=0.45,
            vertices=8
        )
        assign_material(spike, mats["metal"])
        parts.append(spike)

    return join_objects(parts, "electric_node")

def build_blade_sentinel(mats):
    parts = []

    blade = add_cube("Blade", scale=(0.14, 0.95, 0.10))
    assign_material(blade, mats["metal"])
    parts.append(blade)

    tip = add_cone("Tip", location=(0, 1.1, 0), rotation=(math.radians(90), 0, 0), radius1=0.14, depth=0.32, vertices=8)
    assign_material(tip, mats["metal"])
    parts.append(tip)

    guard = add_cube("Guard", location=(0, -0.55, 0), scale=(0.42, 0.08, 0.10))
    assign_material(guard, mats["yellow"])
    parts.append(guard)

    eye = add_uv_sphere("Eye", location=(0, -0.72, 0), scale=(0.12, 0.12, 0.12), segments=8, rings=4)
    assign_material(eye, mats["purple"])
    parts.append(eye)

    return join_objects(parts, "blade_sentinel")

def build_ring_drone(mats):
    parts = []

    ring = add_torus("Ring", major_radius=0.72, minor_radius=0.11)
    assign_material(ring, mats["metal"])
    parts.append(ring)

    core = add_uv_sphere("Core", scale=(0.20, 0.20, 0.20), segments=10, rings=5)
    assign_material(core, mats["red"])
    parts.append(core)

    return join_objects(parts, "ring_drone")

# --------------------------------------------------
# Export
# --------------------------------------------------

def export_glb(obj):
    ensure_export_dir()
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    export_path = os.path.join(EXPORT_DIR, f"{obj.name}.glb")
    bpy.ops.export_scene.gltf(
        filepath=export_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True
    )
    print(f"Exported: {export_path}")

# --------------------------------------------------
# Batch build
# --------------------------------------------------

BUILDERS = {
    "adhesion_bug": build_adhesion_bug,
    "acid_spitter": build_acid_spitter,
    "carapace_husk": build_carapace_husk,
    "electric_node": build_electric_node,
    "blade_sentinel": build_blade_sentinel,
    "ring_drone": build_ring_drone,
}

def build_all():
    mats = build_materials()
    for name, builder in BUILDERS.items():
        clear_scene()
        obj = builder(mats)
        set_origin_to_geometry(obj)
        export_glb(obj)

if __name__ == "__main__":
    build_all()
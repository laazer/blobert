"""
Core Blender utilities for object creation and manipulation
"""

import bpy
from mathutils import Vector


def clear_scene():
    """Clear all objects from the current scene"""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False, confirm=False)


def create_sphere(location=(0, 0, 0), scale=(1, 1, 1), subdivisions=1):
    """Create a UV sphere with specified parameters"""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=location, scale=scale)
    obj = bpy.context.active_object

    # Add subdivision if requested
    if subdivisions > 1:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.subdivide(number_cuts=subdivisions - 1)
        bpy.ops.object.mode_set(mode="OBJECT")

    return obj


def create_cylinder(location=(0, 0, 0), scale=(1, 1, 1), vertices=8, depth=2.0):
    """Create a cylinder with specified parameters"""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, depth=depth, location=location, scale=scale
    )
    return bpy.context.active_object


def create_cone(
    location=(0, 0, 0),
    scale=(1, 1, 1),
    *,
    vertices: int = 16,
    depth: float = 2.0,
    radius1: float = 1.0,
    radius2: float = 0.0,
):
    """Create a cone mesh; use ``vertices=4`` for a pyramid."""
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius1,
        radius2=radius2,
        depth=depth,
        location=location,
        scale=scale,
    )
    return bpy.context.active_object


def create_box(location=(0, 0, 0), scale=(1, 1, 1)):
    """Create a box mesh with the specified dimensions.

    Uses Blender's unit cube (size=1.0) so scale maps directly to edge lengths:
    scale=(width, depth, height) produces a box of exactly that size.
    """
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, scale=scale)
    return bpy.context.active_object


# ---------------------------------------------------------------------------
# Eye and pupil mesh helpers (ESPS-3, ESPS-4)
# ---------------------------------------------------------------------------

# Eye shape scale constants (non-trivial tuning values must be named).
_EYE_OVAL_SCALE_X: float = 1.4  # elongate along X (forward-facing axis)
_EYE_OVAL_SCALE_Z: float = 0.85  # compress along Z slightly
_EYE_SLIT_SCALE_Y: float = 0.35  # narrow along Y for vertical-slit silhouette

# Pupil scale constants.
_PUPIL_EYE_SCALE_RATIO: float = 0.35  # pupil radius relative to eye radius
_PUPIL_DOT_Z_RATIO: float = 0.3  # Z squish for flat disc dot pupil
_PUPIL_SLIT_X_RATIO: float = 0.25  # X width for slit pupil cylinder
_PUPIL_SLIT_Z_RATIO: float = 0.05  # Z depth (thin coin)
_PUPIL_DIAMOND_X_RATIO: float = 0.6  # X width for diamond box
_PUPIL_DIAMOND_Y_RATIO: float = 0.25  # Y depth for diamond box
_PUPIL_DIAMOND_Z_RATIO: float = 0.9  # Z height for diamond box


def create_eye_mesh(shape: str, location: tuple, eye_scale: float):
    """Create an eye mesh primitive dispatched by shape.

    Args:
        shape:      One of 'circle', 'oval', 'slit', 'square'. Unknown values
                    fall back to 'circle' behaviour.
        location:   World-space (x, y, z) tuple for the eye centre.
        eye_scale:  Scalar radius / half-extent for the eye.

    Returns:
        The Blender object created.
    """
    if shape == "square":
        return create_box(location=location, scale=(eye_scale, eye_scale, eye_scale))
    if shape == "oval":
        return create_sphere(
            location=location,
            scale=(
                eye_scale * _EYE_OVAL_SCALE_X,
                eye_scale,
                eye_scale * _EYE_OVAL_SCALE_Z,
            ),
        )
    if shape == "slit":
        return create_sphere(
            location=location,
            scale=(eye_scale, eye_scale * _EYE_SLIT_SCALE_Y, eye_scale),
        )
    # Default: 'circle' (uniform sphere) — also the fallback for unknown shapes.
    return create_sphere(location=location, scale=(eye_scale, eye_scale, eye_scale))


def create_pupil_mesh(shape: str, location: tuple, pupil_scale: float):
    """Create a pupil mesh primitive dispatched by shape.

    Args:
        shape:        One of 'dot', 'slit', 'diamond'. Unknown values fall
                      back to 'dot' behaviour.
        location:     World-space (x, y, z) tuple for the pupil centre.
        pupil_scale:  Scalar radius / half-extent for the pupil.

    Returns:
        The Blender object created.
    """
    if shape == "slit":
        return create_cylinder(
            location=location,
            scale=(
                pupil_scale * _PUPIL_SLIT_X_RATIO,
                pupil_scale,
                pupil_scale * _PUPIL_SLIT_Z_RATIO,
            ),
            vertices=8,
            depth=2.0,
        )
    if shape == "diamond":
        return create_box(
            location=location,
            scale=(
                pupil_scale * _PUPIL_DIAMOND_X_RATIO,
                pupil_scale * _PUPIL_DIAMOND_Y_RATIO,
                pupil_scale * _PUPIL_DIAMOND_Z_RATIO,
            ),
        )
    # Default: 'dot' (flat disc sphere) — also the fallback for unknown shapes.
    return create_sphere(
        location=location,
        scale=(pupil_scale, pupil_scale, pupil_scale * _PUPIL_DOT_Z_RATIO),
    )


# ---------------------------------------------------------------------------
# Mouth geometry helpers (MTE-5)
# ---------------------------------------------------------------------------

_MOUTH_SMILE_X_RATIO: float = 1.2
_MOUTH_SMILE_Y_RATIO: float = 1.0
_MOUTH_SMILE_Z_RATIO: float = 0.15

_MOUTH_GRIMACE_X_RATIO: float = 1.3
_MOUTH_GRIMACE_Y_RATIO: float = 0.9
_MOUTH_GRIMACE_Z_RATIO: float = 0.12

_MOUTH_FLAT_X_RATIO: float = 1.0
_MOUTH_FLAT_Y_RATIO: float = 0.6
_MOUTH_FLAT_Z_RATIO: float = 0.1

_MOUTH_FANG_X_RATIO: float = 0.35
_MOUTH_FANG_Z_RATIO: float = 0.8

_MOUTH_BEAK_X_RATIO: float = 0.55
_MOUTH_BEAK_Z_RATIO: float = 0.9


def create_mouth_mesh(shape: str, location: tuple, head_scale: float):
    """Create a mouth mesh primitive dispatched by shape (MTE-5).

    Args:
        shape:         One of 'smile', 'grimace', 'flat', 'fang', 'beak'. Unknown values
                       fall back to 'smile' behaviour.
        location:      World-space (x, y, z) tuple for the mouth position (front surface).
        head_scale:    Scalar scale derived from head_radii.x for proportional sizing.

    Returns:
        The Blender object created.
    """
    if shape == "fang":
        return create_cone(
            location=location,
            scale=(
                head_scale * _MOUTH_FANG_X_RATIO,
                head_scale * _MOUTH_FANG_X_RATIO,
                head_scale * _MOUTH_FANG_Z_RATIO,
            ),
            vertices=8,
            depth=2.0,
            radius1=head_scale * _MOUTH_FANG_X_RATIO,
            radius2=0.0,
        )
    if shape == "beak":
        return create_cone(
            location=location,
            scale=(
                head_scale * _MOUTH_BEAK_X_RATIO,
                head_scale * _MOUTH_BEAK_X_RATIO,
                head_scale * _MOUTH_BEAK_Z_RATIO,
            ),
            vertices=8,
            depth=2.0,
            radius1=head_scale * _MOUTH_BEAK_X_RATIO,
            radius2=0.0,
        )
    if shape == "flat":
        return create_box(
            location=location,
            scale=(
                head_scale * _MOUTH_FLAT_X_RATIO,
                head_scale * _MOUTH_FLAT_Y_RATIO,
                head_scale * _MOUTH_FLAT_Z_RATIO,
            ),
        )
    if shape == "grimace":
        return create_cylinder(
            location=location,
            scale=(
                head_scale * _MOUTH_GRIMACE_X_RATIO,
                head_scale * _MOUTH_GRIMACE_Y_RATIO,
                head_scale * _MOUTH_GRIMACE_Z_RATIO,
            ),
            vertices=8,
            depth=2.0,
        )
    # Default: 'smile' (thin disc cylinder) — also the fallback for unknown shapes.
    return create_cylinder(
        location=location,
        scale=(
            head_scale * _MOUTH_SMILE_X_RATIO,
            head_scale * _MOUTH_SMILE_Y_RATIO,
            head_scale * _MOUTH_SMILE_Z_RATIO,
        ),
        vertices=8,
        depth=2.0,
    )


# ---------------------------------------------------------------------------
# Tail geometry helpers (MTE-6)
# ---------------------------------------------------------------------------

_TAIL_WHIP_XY_RATIO: float = 0.15
_TAIL_SEG_XY_RATIO: float = 0.45
_TAIL_CLUB_Z_RATIO: float = 0.7
_TAIL_CURLED_X_RATIO: float = 0.6
_TAIL_CURLED_Z_RATIO: float = 0.3


def create_tail_mesh(shape: str, length: float, location: tuple):
    """Create a tail mesh primitive dispatched by shape (MTE-6).

    Args:
        shape:       One of 'spike', 'whip', 'club', 'segmented', 'curled'. Unknown values
                     fall back to 'spike' behaviour.
        length:      Length multiplier (1.0 = normal size, 0.5 = shorter, 3.0 = longer).
        location:    World-space (x, y, z) tuple for the tail attachment point (rear surface).

    Returns:
        The Blender object created.
    """
    if shape == "spike":
        return create_cone(
            location=location,
            scale=(length * 0.25, length * 0.25, length * 1.2),
            vertices=8,
            depth=2.0,
            radius1=length * 0.25,
            radius2=0.0,
        )
    if shape == "whip":
        return create_cylinder(
            location=location,
            scale=(
                length * _TAIL_WHIP_XY_RATIO,
                length * _TAIL_WHIP_XY_RATIO,
                length * 1.5,
            ),
            vertices=8,
            depth=2.0,
        )
    if shape == "club":
        return create_sphere(
            location=location,
            scale=(length * 0.4, length * 0.4, length * _TAIL_CLUB_Z_RATIO),
        )
    if shape == "segmented":
        return create_cylinder(
            location=location,
            scale=(
                length * _TAIL_SEG_XY_RATIO,
                length * _TAIL_SEG_XY_RATIO,
                length * 1.0,
            ),
            vertices=12,
            depth=2.0,
        )
    # Default: 'curled' (flattened sphere) — also the fallback for unknown shapes.
    return create_sphere(
        location=location,
        scale=(
            length * _TAIL_CURLED_X_RATIO,
            length * _TAIL_CURLED_X_RATIO,
            length * _TAIL_CURLED_Z_RATIO,
        ),
    )


def detect_body_scale_from_mesh(mesh) -> float:
    """Estimate a body_scale value from an imported mesh's bounding box.

    Returns half the mesh height, which approximates the body_scale
    convention used throughout the enemy generation system (where body_scale
    is roughly equal to the body sphere radius).

    Falls back to 1.0 if the mesh has no vertex data.
    """
    if not mesh or not mesh.data or not mesh.data.vertices:
        return 1.0
    z_coords = [v.co.z for v in mesh.data.vertices]
    height = max(z_coords) - min(z_coords)
    return max(0.1, height * 0.5)


def apply_smooth_shading(obj):
    """Apply smooth shading to an object"""
    if obj and obj.type == "MESH":
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.faces_shade_smooth()
        bpy.ops.object.mode_set(mode="OBJECT")


def join_objects(objects):
    """Join multiple objects into one"""
    if not objects:
        return None

    # Select all objects
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        if obj:
            obj.select_set(True)

    # Set the first object as active
    bpy.context.view_layer.objects.active = objects[0]

    # Join them
    bpy.ops.object.join()

    return bpy.context.active_object


def random_variance(base_value, factor, rng):
    """Add random variance to a base value"""
    variance = base_value * factor * (rng.random() - 0.5) * 2
    return base_value + variance


def bind_mesh_to_armature(mesh_obj, armature):
    """Bind mesh to armature for animation with enhanced reliability"""
    bpy.ops.object.select_all(action="DESELECT")
    mesh_obj.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature

    # Try automatic weights first
    try:
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")

        # Verify the binding worked by checking for vertex groups
        if len(mesh_obj.vertex_groups) > 0:
            print(
                f"✅ Auto weights successful: {len(mesh_obj.vertex_groups)} vertex groups created"
            )
            return mesh_obj
        else:
            print("⚠️ Auto weights failed, using manual binding")
    except Exception as e:
        print(f"⚠️ Auto weights error: {e}, using manual binding")

    # Fallback: Manual binding with better weight distribution
    return bind_mesh_manually(mesh_obj, armature)


def bind_mesh_manually(mesh_obj, armature):
    """Manual mesh binding with proper weight assignment"""
    # Parent without automatic weights first
    bpy.ops.object.parent_set(type="ARMATURE")

    # Get mesh data
    mesh = mesh_obj.data
    vertices = mesh.vertices

    # Create vertex groups for each bone
    bone_groups = {}
    for bone in armature.data.bones:
        group = mesh_obj.vertex_groups.new(name=bone.name)
        bone_groups[bone.name] = group

    # Assign vertices to bones based on proximity
    for vertex in vertices:
        # Convert vertex position to world space
        world_pos = mesh_obj.matrix_world @ vertex.co

        # Find closest bone
        closest_bone = None
        closest_distance = float("inf")

        for bone in armature.data.bones:
            # Get bone world position (head and tail)
            bone_head = armature.matrix_world @ bone.head_local
            bone_tail = armature.matrix_world @ bone.tail_local

            # Distance to bone line segment
            bone_vec = bone_tail - bone_head
            vertex_vec = world_pos - bone_head

            # Project vertex onto bone line
            if bone_vec.length > 0:
                t = max(0, min(1, vertex_vec.dot(bone_vec) / bone_vec.length_squared))
                closest_point = bone_head + t * bone_vec
                distance = (world_pos - closest_point).length
            else:
                distance = (world_pos - bone_head).length

            if distance < closest_distance:
                closest_distance = distance
                closest_bone = bone.name

        # Assign vertex to closest bone with weight based on distance
        if closest_bone and closest_distance < 2.0:  # Max influence distance
            # Weight decreases with distance (closer = stronger influence)
            weight = max(0.1, 1.0 - (closest_distance / 2.0))
            bone_groups[closest_bone].add([vertex.index], weight, "REPLACE")

    print(f"✅ Manual binding complete: {len(bone_groups)} bone influences assigned")
    return mesh_obj


def ensure_mesh_integrity(mesh_obj, armature):
    """Ensure all mesh parts are properly bound to avoid detachment"""
    if not mesh_obj or not armature:
        return mesh_obj

    # First, fix specific body part assignments (eyes to head, etc.)
    fix_body_part_bindings(mesh_obj, armature)

    # Then check for any remaining unweighted vertices
    mesh = mesh_obj.data
    unweighted_verts = []

    for vert_index, vertex in enumerate(mesh.vertices):
        total_weight = 0.0
        for group in mesh_obj.vertex_groups:
            try:
                weight = group.weight(vert_index)
                total_weight += weight
            except RuntimeError:
                # Vertex not in this group
                pass

        if total_weight < 0.01:  # Essentially unweighted
            unweighted_verts.append(vert_index)

    # Fix unweighted vertices
    if unweighted_verts:
        print(f"⚠️ Found {len(unweighted_verts)} unweighted vertices, fixing...")

        # Find center bone (usually body or root)
        center_bone = None
        bone_names = ["body", "root", "spine", "center", "main"]
        for bone_name in bone_names:
            for bone in armature.data.bones:
                if bone_name in bone.name.lower():
                    center_bone = bone.name
                    break
            if center_bone:
                break

        # If no center bone found, use first bone
        if not center_bone and armature.data.bones:
            center_bone = armature.data.bones[0].name

        # Create vertex group for center bone if it doesn't exist
        center_group = None
        for group in mesh_obj.vertex_groups:
            if group.name == center_bone:
                center_group = group
                break

        if not center_group and center_bone:
            center_group = mesh_obj.vertex_groups.new(name=center_bone)

        # Assign unweighted vertices to center bone
        if center_group:
            center_group.add(unweighted_verts, 1.0, "REPLACE")
            print(f"✅ Assigned {len(unweighted_verts)} vertices to {center_bone}")

    return mesh_obj


def fix_body_part_bindings(mesh_obj, armature):
    """Fix specific body part bindings for natural movement"""
    if not mesh_obj or not armature:
        return

    print("🔧 Fixing body part specific bindings...")

    # Find available bones
    available_bones = {bone.name.lower(): bone.name for bone in armature.data.bones}

    # Define body part regions and their preferred bones
    body_part_rules = {
        "head": ["head", "neck", "skull"],
        "neck": ["neck", "head"],
        "eye": ["head", "neck", "skull"],
        "mouth": ["head", "neck"],
        "horn": ["head", "neck"],
        "antenna": ["head", "neck"],
        "leg": ["leg", "limb", "foot"],
        "arm": ["arm", "hand", "limb"],
        "tail": ["tail", "spine", "body"],
        "wing": ["wing", "body", "spine"],
    }

    # Get mesh vertices and their positions
    mesh = mesh_obj.data
    vertices = mesh.vertices

    # Analyze vertex positions to identify body parts
    mesh_center = sum((v.co for v in vertices), Vector()) / len(vertices)

    # Find vertices that should be bound to specific bones based on position
    for vert_index, vertex in enumerate(vertices):
        vertex_world = mesh_obj.matrix_world @ vertex.co

        # Determine which body part this vertex likely belongs to
        likely_part = identify_vertex_body_part(vertex_world, mesh_center, mesh_obj)

        if likely_part and likely_part in body_part_rules:
            # Find the best bone for this body part
            best_bone = None
            for preferred_bone in body_part_rules[likely_part]:
                for available_bone_key, available_bone_name in available_bones.items():
                    if preferred_bone in available_bone_key:
                        best_bone = available_bone_name
                        break
                if best_bone:
                    break

            if best_bone:
                # Ensure vertex group exists
                target_group = None
                for group in mesh_obj.vertex_groups:
                    if group.name == best_bone:
                        target_group = group
                        break

                if not target_group:
                    target_group = mesh_obj.vertex_groups.new(name=best_bone)

                # Assign vertex with strong weight
                try:
                    target_group.add([vert_index], 1.0, "REPLACE")
                except:
                    pass  # Vertex might already be assigned

    print("✅ Body part bindings optimized")


def identify_vertex_body_part(vertex_pos, mesh_center, mesh_obj):
    """Identify which body part a vertex belongs to based on position"""
    # Get mesh bounds
    bbox = [mesh_obj.matrix_world @ Vector(corner) for corner in mesh_obj.bound_box]

    min_x = min(v.x for v in bbox)
    max_x = max(v.x for v in bbox)
    min_y = min(v.y for v in bbox)
    max_y = max(v.y for v in bbox)
    min_z = min(v.z for v in bbox)
    max_z = max(v.z for v in bbox)

    width = max_x - min_x
    height = max_z - min_z
    depth = max_y - min_y

    # Relative position within mesh
    rel_x = (vertex_pos.x - min_x) / width if width > 0 else 0.5
    rel_y = (vertex_pos.y - min_y) / depth if depth > 0 else 0.5
    rel_z = (vertex_pos.z - min_z) / height if height > 0 else 0.5

    # Eye detection: small objects in upper front area
    if (
        rel_z > 0.6  # Upper part
        and (rel_x > 0.7 or rel_x < 0.3)  # Front area
        and vertex_pos.length < 0.3
    ):  # Small objects
        return "eye"

    # Head detection: upper/front part of creature
    if rel_z > 0.6 or rel_x > 0.6:
        return "head"

    # Tail detection: back part
    if rel_x < 0.3:
        return "tail"

    # Leg detection: lower lateral parts
    if rel_z < 0.4 and (rel_y < 0.3 or rel_y > 0.7):
        return "leg"

    return "body"  # Default

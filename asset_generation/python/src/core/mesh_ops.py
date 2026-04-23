"""Mesh operations, scene helpers, and armature binding utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import bpy
from mathutils import Vector

if TYPE_CHECKING:
    from bpy.types import Object


class SupportsRandom(Protocol):
    """Protocol for deterministic random providers used by random_variance."""

    def random(self) -> float: ...


def clear_scene() -> None:
    """Clear all objects from the current scene."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False, confirm=False)


def detect_body_scale_from_mesh(mesh: object) -> float:
    """Estimate body scale from imported mesh bounds."""
    if not mesh or not getattr(mesh, "data", None):
        return 1.0
    vertices = getattr(mesh.data, "vertices", None)
    if not vertices:
        return 1.0
    z_coords = [vertex.co.z for vertex in vertices]
    height = max(z_coords) - min(z_coords)
    return max(0.1, height * 0.5)


def apply_smooth_shading(obj: object) -> None:
    """Apply smooth shading to a mesh object."""
    if obj and obj.type == "MESH":
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.faces_shade_smooth()
        bpy.ops.object.mode_set(mode="OBJECT")


def join_objects(objects: list[object]) -> Object | None:
    """Join multiple objects into one."""
    if not objects:
        return None

    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        if obj:
            obj.select_set(True)

    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    return bpy.context.active_object


def random_variance(base_value: float, factor: float, rng: SupportsRandom) -> float:
    """Add symmetric random variance to a base value."""
    variance = base_value * factor * (rng.random() - 0.5) * 2
    return base_value + variance


def bind_mesh_to_armature(mesh_obj: object, armature: object) -> object:
    """Bind mesh to armature for animation with enhanced reliability."""
    bpy.ops.object.select_all(action="DESELECT")
    mesh_obj.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature

    try:
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        if len(mesh_obj.vertex_groups) > 0:
            print(
                f"✅ Auto weights successful: {len(mesh_obj.vertex_groups)} vertex groups created"
            )
            return mesh_obj
        print("⚠️ Auto weights failed, using manual binding")
    except Exception as error:
        print(f"⚠️ Auto weights error: {error}, using manual binding")

    return bind_mesh_manually(mesh_obj, armature)


def bind_mesh_manually(mesh_obj: object, armature: object) -> object:
    """Manual mesh binding with proper weight assignment."""
    bpy.ops.object.parent_set(type="ARMATURE")

    mesh = mesh_obj.data
    vertices = mesh.vertices

    bone_groups: dict[str, object] = {}
    for bone in armature.data.bones:
        group = mesh_obj.vertex_groups.new(name=bone.name)
        bone_groups[bone.name] = group

    for vertex in vertices:
        world_pos = mesh_obj.matrix_world @ vertex.co
        closest_bone: str | None = None
        closest_distance = float("inf")

        for bone in armature.data.bones:
            bone_head = armature.matrix_world @ bone.head_local
            bone_tail = armature.matrix_world @ bone.tail_local

            bone_vec = bone_tail - bone_head
            vertex_vec = world_pos - bone_head

            if bone_vec.length > 0:
                t = max(0, min(1, vertex_vec.dot(bone_vec) / bone_vec.length_squared))
                closest_point = bone_head + t * bone_vec
                distance = (world_pos - closest_point).length
            else:
                distance = (world_pos - bone_head).length

            if distance < closest_distance:
                closest_distance = distance
                closest_bone = bone.name

        if closest_bone and closest_distance < 2.0:
            weight = max(0.1, 1.0 - (closest_distance / 2.0))
            bone_groups[closest_bone].add([vertex.index], weight, "REPLACE")

    print(f"✅ Manual binding complete: {len(bone_groups)} bone influences assigned")
    return mesh_obj


def ensure_mesh_integrity(mesh_obj: object, armature: object) -> object:
    """Ensure all mesh parts are properly bound to avoid detachment."""
    if not mesh_obj or not armature:
        return mesh_obj

    fix_body_part_bindings(mesh_obj, armature)

    mesh = mesh_obj.data
    unweighted_verts: list[int] = []

    for vert_index, _vertex in enumerate(mesh.vertices):
        total_weight = 0.0
        for group in mesh_obj.vertex_groups:
            try:
                total_weight += group.weight(vert_index)
            except RuntimeError:
                pass
        if total_weight < 0.01:
            unweighted_verts.append(vert_index)

    if unweighted_verts:
        print(f"⚠️ Found {len(unweighted_verts)} unweighted vertices, fixing...")

        center_bone: str | None = None
        for bone_name in ["body", "root", "spine", "center", "main"]:
            for bone in armature.data.bones:
                if bone_name in bone.name.lower():
                    center_bone = bone.name
                    break
            if center_bone:
                break

        if not center_bone and armature.data.bones:
            center_bone = armature.data.bones[0].name

        center_group = None
        for group in mesh_obj.vertex_groups:
            if group.name == center_bone:
                center_group = group
                break

        if not center_group and center_bone:
            center_group = mesh_obj.vertex_groups.new(name=center_bone)

        if center_group:
            center_group.add(unweighted_verts, 1.0, "REPLACE")
            print(f"✅ Assigned {len(unweighted_verts)} vertices to {center_bone}")

    return mesh_obj


def fix_body_part_bindings(mesh_obj: object, armature: object) -> None:
    """Fix specific body part bindings for natural movement."""
    if not mesh_obj or not armature:
        return

    print("🔧 Fixing body part specific bindings...")
    available_bones = {bone.name.lower(): bone.name for bone in armature.data.bones}

    body_part_rules: dict[str, list[str]] = {
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

    mesh = mesh_obj.data
    vertices = mesh.vertices
    mesh_center = sum((v.co for v in vertices), Vector()) / len(vertices)

    for vert_index, vertex in enumerate(vertices):
        vertex_world = mesh_obj.matrix_world @ vertex.co
        likely_part = identify_vertex_body_part(vertex_world, mesh_center, mesh_obj)

        if likely_part and likely_part in body_part_rules:
            best_bone: str | None = None
            for preferred_bone in body_part_rules[likely_part]:
                for available_bone_key, available_bone_name in available_bones.items():
                    if preferred_bone in available_bone_key:
                        best_bone = available_bone_name
                        break
                if best_bone:
                    break

            if best_bone:
                target_group = None
                for group in mesh_obj.vertex_groups:
                    if group.name == best_bone:
                        target_group = group
                        break

                if not target_group:
                    target_group = mesh_obj.vertex_groups.new(name=best_bone)

                try:
                    target_group.add([vert_index], 1.0, "REPLACE")
                except Exception:
                    pass

    print("✅ Body part bindings optimized")


def identify_vertex_body_part(
    vertex_pos: Vector,
    mesh_center: Vector,
    mesh_obj: object,
) -> str:
    """Identify which body part a vertex belongs to based on position."""
    _ = mesh_center  # Compatibility: keep signature stable for existing callers.
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

    rel_x = (vertex_pos.x - min_x) / width if width > 0 else 0.5
    rel_y = (vertex_pos.y - min_y) / depth if depth > 0 else 0.5
    rel_z = (vertex_pos.z - min_z) / height if height > 0 else 0.5

    if rel_z > 0.6 and (rel_x > 0.7 or rel_x < 0.3) and vertex_pos.length < 0.3:
        return "eye"
    if rel_z > 0.6 or rel_x > 0.6:
        return "head"
    if rel_x < 0.3:
        return "tail"
    if rel_z < 0.4 and (rel_y < 0.3 or rel_y > 0.7):
        return "leg"
    return "body"


__all__ = [
    "clear_scene",
    "detect_body_scale_from_mesh",
    "apply_smooth_shading",
    "join_objects",
    "random_variance",
    "bind_mesh_to_armature",
    "bind_mesh_manually",
    "ensure_mesh_integrity",
    "fix_body_part_bindings",
    "identify_vertex_body_part",
]

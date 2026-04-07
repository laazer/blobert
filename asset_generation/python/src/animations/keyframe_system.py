"""
Keyframe system for animation creation
"""

from __future__ import annotations

import bpy

from ..core.rig_types import RigDefinition


def create_simple_armature(armature_name: str, rig: RigDefinition):
    """Create basic armature from a typed :class:`RigDefinition`."""
    bpy.ops.object.armature_add()
    armature = bpy.context.active_object
    armature.name = armature_name

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.armature.select_all(action="SELECT")
    bpy.ops.armature.delete()

    bones_created: dict[str, object] = {}
    for spec in rig.bones:
        edit_bone = armature.data.edit_bones.new(spec.name)
        edit_bone.head = spec.head
        edit_bone.tail = spec.tail
        bones_created[spec.name] = edit_bone

        if spec.parent_name and spec.parent_name in bones_created:
            edit_bone.parent = bones_created[spec.parent_name]

    bpy.ops.object.mode_set(mode="OBJECT")
    return armature


def set_bone_keyframe(armature, bone_name, frame, location=None, rotation=None, scale=None):
    """Set keyframe for bone transformation"""
    bpy.context.scene.frame_set(frame)
    
    if armature.mode != 'POSE':
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE')
    
    if bone_name in armature.pose.bones:
        bone = armature.pose.bones[bone_name]
        
        # Ensure consistent rotation mode to avoid warnings
        bone.rotation_mode = 'XYZ'
        
        if location:
            bone.location = location
            bone.keyframe_insert(data_path="location")
        
        if rotation:
            bone.rotation_euler = rotation
            bone.keyframe_insert(data_path="rotation_euler")
        
        if scale:
            bone.scale = scale
            bone.keyframe_insert(data_path="scale")
    else:
        # Bone doesn't exist - skip silently to avoid warnings
        pass
"""
Keyframe system for animation creation
"""

import bpy
from mathutils import Vector, Euler


def create_simple_armature(name, bone_positions):
    """Create basic armature with given bone layout"""
    bpy.ops.object.armature_add()
    armature = bpy.context.active_object
    armature.name = name
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='SELECT')
    bpy.ops.armature.delete()
    
    bones_created = {}
    for bone_name, (head_pos, tail_pos, parent) in bone_positions.items():
        bone = armature.data.edit_bones.new(bone_name)
        bone.head = head_pos
        bone.tail = tail_pos
        bones_created[bone_name] = bone
        
        if parent and parent in bones_created:
            bone.parent = bones_created[parent]
    
    bpy.ops.object.mode_set(mode='OBJECT')
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
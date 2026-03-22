"""
Armature builders for different enemy types
"""

import bpy
from mathutils import Vector
from .keyframe_system import create_simple_armature


def create_quadruped_armature(name, body_scale):
    """Create armature for 6-legged creatures like adhesion bugs"""
    bone_positions = {
        'root': (Vector((0, 0, 0)), Vector((0, 0, body_scale * 0.2)), None),
        'spine': (Vector((0, 0, body_scale * 0.2)), Vector((body_scale * 0.5, 0, body_scale * 0.4)), 'root'),
        'head': (Vector((body_scale * 0.5, 0, body_scale * 0.4)), Vector((body_scale * 0.8, 0, body_scale * 0.6)), 'spine'),
        
        # 6 legs for adhesion bug
        'leg_fl': (Vector((body_scale * 0.3, body_scale * 0.3, body_scale * 0.3)), Vector((body_scale * 0.3, body_scale * 0.3, 0)), 'spine'),
        'leg_fr': (Vector((body_scale * 0.3, -body_scale * 0.3, body_scale * 0.3)), Vector((body_scale * 0.3, -body_scale * 0.3, 0)), 'spine'),
        'leg_ml': (Vector((0, body_scale * 0.4, body_scale * 0.3)), Vector((0, body_scale * 0.4, 0)), 'spine'),
        'leg_mr': (Vector((0, -body_scale * 0.4, body_scale * 0.3)), Vector((0, -body_scale * 0.4, 0)), 'spine'),
        'leg_bl': (Vector((-body_scale * 0.2, body_scale * 0.3, body_scale * 0.3)), Vector((-body_scale * 0.2, body_scale * 0.3, 0)), 'root'),
        'leg_br': (Vector((-body_scale * 0.2, -body_scale * 0.3, body_scale * 0.3)), Vector((-body_scale * 0.2, -body_scale * 0.3, 0)), 'root'),
    }
    return create_simple_armature(name, bone_positions)


def create_blob_armature(name, body_scale):
    """Create armature for blob-like creatures like tar slugs"""
    bone_positions = {
        'root': (Vector((0, 0, 0)), Vector((0, 0, body_scale * 0.3)), None),
        'body': (Vector((0, 0, body_scale * 0.3)), Vector((0, 0, body_scale * 0.8)), 'root'),
        'head': (Vector((0, 0, body_scale * 0.8)), Vector((0, 0, body_scale * 1.2)), 'body'),
    }
    return create_simple_armature(name, bone_positions)


def create_humanoid_armature(name, body_height):
    """Create armature for humanoid creatures like ember imps"""
    bone_positions = {
        'root': (Vector((0, 0, 0)), Vector((0, 0, body_height * 0.2)), None),
        'spine': (Vector((0, 0, body_height * 0.2)), Vector((0, 0, body_height * 0.7)), 'root'),
        'head': (Vector((0, 0, body_height * 0.7)), Vector((0, 0, body_height * 1.0)), 'spine'),
        'arm_l': (Vector((0, body_height * 0.2, body_height * 0.6)), Vector((0, body_height * 0.5, body_height * 0.3)), 'spine'),
        'arm_r': (Vector((0, -body_height * 0.2, body_height * 0.6)), Vector((0, -body_height * 0.5, body_height * 0.3)), 'spine'),
        'leg_l': (Vector((0, body_height * 0.1, body_height * 0.2)), Vector((0, body_height * 0.1, 0)), 'root'),
        'leg_r': (Vector((0, -body_height * 0.1, body_height * 0.2)), Vector((0, -body_height * 0.1, 0)), 'root'),
    }
    return create_simple_armature(name, bone_positions)
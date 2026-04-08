"""
Core animation system for procedural enemies
"""


import bpy

from ..utils.constants import AnimationConfig, AnimationTypes
from .body_types import BodyTypeFactory


def create_all_animations(armature, enemy_body_type, rng, animation_set='core'):
    """Create animation actions for an enemy using base animation classes
    
    Args:
        armature: The armature object to animate
        enemy_body_type: Body type for animation style
        rng: Random number generator
        animation_set: 'core', 'extended', or 'all'
    """
    # Set up for pose mode
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    # Set consistent rotation mode for all bones to avoid warnings
    for bone in armature.pose.bones:
        bone.rotation_mode = 'XYZ'
    
    # Clear existing animation data
    if armature.animation_data:
        armature.animation_data.action = None
    
    # Create body type instance for this armature
    body_type = BodyTypeFactory.create_body_type(enemy_body_type, armature, rng)
    
    # Choose animation set
    if animation_set == 'core':
        animations = AnimationTypes.get_core()
    elif animation_set == 'extended':
        animations = AnimationTypes.get_extended()
    else:  # 'all'
        animations = AnimationTypes.get_all()
    
    created_actions = []

    for anim_name in animations:
        # Resolve the export name (PascalCase) for this internal animation name.
        # The internal name is kept in anim_name for dispatch and length lookups;
        # the export name is used only for naming the bpy action and NLA strip.
        export_name = AnimationTypes.get_export_name(anim_name)

        # Create new action using the export name so the GLB clip name matches
        # what EnemyAnimationController expects in Godot (BAE-2.6).
        action = bpy.data.actions.new(name=export_name)
        action.use_fake_user = True  # Prevent action from being lost
        created_actions.append(action)
        armature.animation_data_create()
        armature.animation_data.action = action

        # Set frame range for this animation (uses internal name — LENGTHS keys
        # are internal names; changing this would break AnimationConfig, BAE-2.7).
        length = AnimationConfig.get_length(anim_name)
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = length

        # Start at rest pose for perfect looping
        set_rest_pose_keyframe(armature, 1)

        # Create the specific animation using the body type
        if anim_name == AnimationTypes.IDLE:
            body_type.create_idle_animation(length)
        elif anim_name == AnimationTypes.MOVE:
            body_type.create_move_animation(length)
        elif anim_name == AnimationTypes.ATTACK:
            body_type.create_attack_animation(length)
        elif anim_name == AnimationTypes.DAMAGE:
            body_type.create_damage_animation(length)
        elif anim_name == AnimationTypes.DEATH:
            body_type.create_death_animation(length)
        # Extended animations
        elif anim_name == AnimationTypes.SPAWN:
            body_type.create_spawn_animation(length)
        elif anim_name == AnimationTypes.SPECIAL_ATTACK:
            body_type.create_special_attack_animation(length)
        elif anim_name == AnimationTypes.DAMAGE_HEAVY:
            body_type.create_damage_heavy_animation(length)
        elif anim_name == AnimationTypes.DAMAGE_FIRE:
            body_type.create_damage_fire_animation(length)
        elif anim_name == AnimationTypes.DAMAGE_ICE:
            body_type.create_damage_ice_animation(length)
        elif anim_name == AnimationTypes.STUNNED:
            body_type.create_stunned_animation(length)
        elif anim_name == AnimationTypes.CELEBRATE:
            body_type.create_celebrate_animation(length)
        elif anim_name == AnimationTypes.TAUNT:
            body_type.create_taunt_animation(length)
        else:
            print(f"Warning: Unknown animation type '{anim_name}', skipping.")

        # End at rest pose (except death) for perfect looping
        if anim_name != AnimationTypes.DEATH:
            set_rest_pose_keyframe(armature, length)

        # Set action frame range
        action.frame_range = (1, length)

        print(f"Created {export_name} animation: frames 1-{length}")

    # Push all created actions into individual NLA tracks so the GLTF exporter
    # emits all clips (BAE-1.1 through BAE-1.4).
    # NLA track creation requires OBJECT mode; switching here is explicit even if
    # the current mode is already OBJECT, to avoid context errors (Risk R1.2).
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='OBJECT')

    for action in created_actions:
        track = armature.animation_data.nla_tracks.new()
        strip = track.strips.new(action.name, 0, action)
        strip.action_frame_start = 1
        strip.action_frame_end = action.frame_range[1]

    # Set NLA-driven mode: action=None tells the GLTF exporter to export all NLA
    # strips rather than a single active action (BAE-1.4).
    armature.animation_data.action = None

    print(f"NLA: {len(created_actions)} strips wired")
    print(f"✅ {len(created_actions)} self-contained animation actions created")


def set_rest_pose_keyframe(armature, frame):
    """Set all bones to rest position at the given frame"""
    bpy.context.scene.frame_set(frame)
    
    if armature.mode != 'POSE':
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE')
    
    # Reset all bones to rest position
    for bone in armature.pose.bones:
        bone.location = (0, 0, 0)
        bone.rotation_euler = (0, 0, 0)
        bone.scale = (1, 1, 1)
        
        bone.keyframe_insert(data_path="location")
        bone.keyframe_insert(data_path="rotation_euler")
        bone.keyframe_insert(data_path="scale")

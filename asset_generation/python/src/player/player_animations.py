"""
Animation system for the player slime character

All animations are built from two techniques:
  1. Squash & stretch — scale keyframes on the body bone
     squashed  → scale (1.3, 1.3, 0.65)   wider & shorter
     stretched → scale (0.75, 0.75, 1.5)  narrower & taller
  2. Location shifts on the root/body bone for hops and knockback

Eye blinks are implemented as Z-scale on the eye bones (0.1 = closed).
Arm nubs wobble via rotation on the arm bones.
"""

import bpy
from ..animations.keyframe_system import set_bone_keyframe
from ..animations.animation_system import set_rest_pose_keyframe
from ..utils.constants import PlayerBoneNames, PlayerAnimationTypes, PlayerAnimationConfig

# ------------------------------------------------------------------
# Squash / stretch scale presets
# ------------------------------------------------------------------

_REST      = (1.00, 1.00, 1.00)
_SQUASH    = (1.30, 1.30, 0.65)
_BIG_SQUASH= (1.55, 1.55, 0.45)
_IMPACT    = (1.65, 1.65, 0.38)   # landing impact
_STRETCH   = (0.75, 0.75, 1.50)
_BIG_STRETCH=(0.68, 0.68, 1.68)   # jump peak
_LEAN_FWD  = (0.88, 1.10, 1.05)   # attack lean-forward
_LEAN_BACK = (1.12, 0.90, 0.88)   # attack wind-up lean-back

BODY  = PlayerBoneNames.BODY
ROOT  = PlayerBoneNames.ROOT
EYE_L = PlayerBoneNames.EYE_LEFT
EYE_R = PlayerBoneNames.EYE_RIGHT
ARM_L = PlayerBoneNames.ARM_LEFT
ARM_R = PlayerBoneNames.ARM_RIGHT

_BLINK_OPEN   = (1.0, 1.0, 1.00)
_BLINK_CLOSED = (1.0, 1.0, 0.08)


class PlayerSlimeAnimations:
    """Encapsulates all animation creation methods for the player slime."""

    def __init__(self, armature, rng):
        self.armature = armature
        self.rng = rng

    # ------------------------------------------------------------------
    # Public orchestrator
    # ------------------------------------------------------------------

    def create_all_animations(self):
        """Create every player animation action on the armature."""
        bpy.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode='POSE')

        for bone in self.armature.pose.bones:
            bone.rotation_mode = 'XYZ'

        if self.armature.animation_data:
            self.armature.animation_data.action = None

        created_actions = []

        for anim_name in PlayerAnimationTypes.get_all():
            action = bpy.data.actions.new(name=anim_name)
            action.use_fake_user = True
            self.armature.animation_data_create()
            self.armature.animation_data.action = action

            length = PlayerAnimationConfig.get_length(anim_name)
            bpy.context.scene.frame_start = 1
            bpy.context.scene.frame_end = length

            set_rest_pose_keyframe(self.armature, 1)
            self._dispatch_animation(anim_name, length)

            if anim_name != PlayerAnimationTypes.DEATH:
                set_rest_pose_keyframe(self.armature, length)

            action.frame_range = (1, length)
            created_actions.append(action)
            print(f"Created player animation: {anim_name} (frames 1-{length})")

        if created_actions:
            self.armature.animation_data.action = created_actions[0]

        print(f"✅ {len(created_actions)} player animations created")

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def _dispatch_animation(self, name: str, length: int):
        dispatch = {
            PlayerAnimationTypes.IDLE:      self.create_idle_animation,
            PlayerAnimationTypes.MOVE:      self.create_move_animation,
            PlayerAnimationTypes.JUMP:      self.create_jump_animation,
            PlayerAnimationTypes.LAND:      self.create_land_animation,
            PlayerAnimationTypes.ATTACK:    self.create_attack_animation,
            PlayerAnimationTypes.DAMAGE:    self.create_damage_animation,
            PlayerAnimationTypes.DEATH:     self.create_death_animation,
            PlayerAnimationTypes.CELEBRATE: self.create_celebrate_animation,
        }
        method = dispatch.get(name)
        if method:
            method(length)

    # ------------------------------------------------------------------
    # Core animations
    # ------------------------------------------------------------------

    def create_idle_animation(self, length: int):
        """Gentle vertical bob with a single mid-cycle blink."""
        quarter = length // 4

        # Body: subtle float up on quarters, settle slightly below on half
        set_bone_keyframe(self.armature, BODY, 0,        scale=_REST)
        set_bone_keyframe(self.armature, BODY, quarter,  scale=(1.0, 1.0, 1.04))
        set_bone_keyframe(self.armature, BODY, length // 2, scale=(1.0, 1.0, 0.97))
        set_bone_keyframe(self.armature, BODY, quarter * 3, scale=(1.0, 1.0, 1.04))
        set_bone_keyframe(self.armature, BODY, length,   scale=_REST)

        # Matching root lift so the whole slime floats slightly
        set_bone_keyframe(self.armature, ROOT, 0,        location=(0, 0, 0))
        set_bone_keyframe(self.armature, ROOT, quarter,  location=(0, 0, 0.05))
        set_bone_keyframe(self.armature, ROOT, length // 2, location=(0, 0, -0.02))
        set_bone_keyframe(self.armature, ROOT, quarter * 3, location=(0, 0, 0.05))
        set_bone_keyframe(self.armature, ROOT, length,   location=(0, 0, 0))

        # Blink at frame ~24 (open → closed → open over 4 frames)
        blink_frame = length // 2
        for eye in (EYE_L, EYE_R):
            set_bone_keyframe(self.armature, eye, blink_frame - 2, scale=_BLINK_OPEN)
            set_bone_keyframe(self.armature, eye, blink_frame,     scale=_BLINK_CLOSED)
            set_bone_keyframe(self.armature, eye, blink_frame + 2, scale=_BLINK_OPEN)

        # Arm nubs: slight outward droop and lift
        set_bone_keyframe(self.armature, ARM_L, 0,       rotation=(0,  0, 0))
        set_bone_keyframe(self.armature, ARM_L, quarter, rotation=(0.2, 0, 0))
        set_bone_keyframe(self.armature, ARM_L, length,  rotation=(0,  0, 0))

        set_bone_keyframe(self.armature, ARM_R, 0,       rotation=(0,   0, 0))
        set_bone_keyframe(self.armature, ARM_R, quarter, rotation=(-0.2, 0, 0))
        set_bone_keyframe(self.armature, ARM_R, length,  rotation=(0,   0, 0))

    def create_move_animation(self, length: int):
        """Two bouncing hops — squash at takeoff/landing, stretch at apex."""
        half = length // 2
        quarter = length // 4

        for hop_start in (0, half):
            apex = hop_start + quarter

            # Takeoff squash
            set_bone_keyframe(self.armature, BODY, hop_start, scale=_SQUASH)
            set_bone_keyframe(self.armature, ROOT, hop_start, location=(0, 0, 0))

            # Apex stretch
            set_bone_keyframe(self.armature, BODY, apex, scale=_STRETCH)
            set_bone_keyframe(self.armature, ROOT, apex, location=(0, 0, 0.35))

            # Land squash
            land = hop_start + half - 1
            set_bone_keyframe(self.armature, BODY, land, scale=_BIG_SQUASH)
            set_bone_keyframe(self.armature, ROOT, land, location=(0, 0, 0))

        # Bounce arms outward at each apex
        set_bone_keyframe(self.armature, ARM_L, quarter,    rotation=(0.4, 0, 0))
        set_bone_keyframe(self.armature, ARM_L, half,       rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, ARM_L, half + quarter, rotation=(0.4, 0, 0))

        set_bone_keyframe(self.armature, ARM_R, quarter,    rotation=(-0.4, 0, 0))
        set_bone_keyframe(self.armature, ARM_R, half,       rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, ARM_R, half + quarter, rotation=(-0.4, 0, 0))

    def create_jump_animation(self, length: int):
        """Charge-up crouch → explosive stretch upward.

        Frames:
          0     rest
          6     big squash (crouch)
          12    big stretch (launch)
          20    stretch at peak (held — game engine takes over from here)
        """
        crouch = 6
        launch = 12

        set_bone_keyframe(self.armature, BODY, 0,      scale=_REST)
        set_bone_keyframe(self.armature, BODY, crouch, scale=_BIG_SQUASH)
        set_bone_keyframe(self.armature, BODY, launch, scale=_BIG_STRETCH)
        set_bone_keyframe(self.armature, BODY, length, scale=_STRETCH)

        set_bone_keyframe(self.armature, ROOT, 0,      location=(0, 0, 0))
        set_bone_keyframe(self.armature, ROOT, crouch, location=(0, 0, -0.08))
        set_bone_keyframe(self.armature, ROOT, launch, location=(0, 0, 0.5))
        set_bone_keyframe(self.armature, ROOT, length, location=(0, 0, 1.2))

        # Arms fly upward on launch
        for arm, rot_dir in ((ARM_L, 1), (ARM_R, -1)):
            set_bone_keyframe(self.armature, arm, 0,      rotation=(0, 0, 0))
            set_bone_keyframe(self.armature, arm, crouch,  rotation=(rot_dir * 0.3, 0, 0))
            set_bone_keyframe(self.armature, arm, launch,  rotation=(rot_dir * -0.8, 0, 0))
            set_bone_keyframe(self.armature, arm, length,  rotation=(rot_dir * -0.5, 0, 0))

    def create_land_animation(self, length: int):
        """Heavy impact squash, single bounce, settle to rest.

        Frames:
          0     arriving stretch (starts in mid-air)
          4     IMPACT — maximum squash
          10    small bounce stretch
          16    settled rest
        """
        impact = 4
        bounce = 10

        set_bone_keyframe(self.armature, BODY, 0,      scale=_STRETCH)
        set_bone_keyframe(self.armature, BODY, impact, scale=_IMPACT)
        set_bone_keyframe(self.armature, BODY, bounce, scale=(1.05, 1.05, 1.08))
        set_bone_keyframe(self.armature, BODY, length, scale=_REST)

        set_bone_keyframe(self.armature, ROOT, 0,      location=(0, 0, 0.2))
        set_bone_keyframe(self.armature, ROOT, impact, location=(0, 0, 0))
        set_bone_keyframe(self.armature, ROOT, bounce, location=(0, 0, 0.05))
        set_bone_keyframe(self.armature, ROOT, length, location=(0, 0, 0))

        # Arms slam down on impact, spring back
        for arm, rot_dir in ((ARM_L, 1), (ARM_R, -1)):
            set_bone_keyframe(self.armature, arm, 0,      rotation=(rot_dir * -0.4, 0, 0))
            set_bone_keyframe(self.armature, arm, impact,  rotation=(rot_dir * 0.6, 0, 0))
            set_bone_keyframe(self.armature, arm, length,  rotation=(0, 0, 0))

    def create_attack_animation(self, length: int):
        """Lean back (wind-up) → lean forward (spit projectile) → recoil → rest.

        Frames:
          0     rest
          8     lean-back wind-up  (spine pitches back, arms raise)
          15    SPIT — lean forward, arms punch forward
          22    recoil bounce
          30    rest
        """
        windup = 8
        spit   = 15
        recoil = 22

        set_bone_keyframe(self.armature, BODY, 0,      scale=_REST,      rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BODY, windup, scale=_LEAN_BACK, rotation=(-0.35, 0, 0))
        set_bone_keyframe(self.armature, BODY, spit,   scale=_LEAN_FWD,  rotation=(0.45, 0, 0))
        set_bone_keyframe(self.armature, BODY, recoil, scale=(1.08, 1.0, 0.94), rotation=(-0.1, 0, 0))
        set_bone_keyframe(self.armature, BODY, length, scale=_REST,      rotation=(0, 0, 0))

        # Arms spread back on windup, thrust forward on spit
        set_bone_keyframe(self.armature, ARM_L, 0,      rotation=(0.0, 0, 0))
        set_bone_keyframe(self.armature, ARM_L, windup, rotation=(0.5, 0, 0))
        set_bone_keyframe(self.armature, ARM_L, spit,   rotation=(-0.4, 0, 0))
        set_bone_keyframe(self.armature, ARM_L, length, rotation=(0.0, 0, 0))

        set_bone_keyframe(self.armature, ARM_R, 0,      rotation=(0.0, 0, 0))
        set_bone_keyframe(self.armature, ARM_R, windup, rotation=(-0.5, 0, 0))
        set_bone_keyframe(self.armature, ARM_R, spit,   rotation=(0.4, 0, 0))
        set_bone_keyframe(self.armature, ARM_R, length, rotation=(0.0, 0, 0))

        # Eyes squint shut during spit effort, open on recoil
        for eye in (EYE_L, EYE_R):
            set_bone_keyframe(self.armature, eye, windup, scale=_BLINK_OPEN)
            set_bone_keyframe(self.armature, eye, spit,   scale=(1.0, 1.0, 0.35))  # squinting
            set_bone_keyframe(self.armature, eye, recoil, scale=_BLINK_OPEN)

    def create_damage_animation(self, length: int):
        """Side-to-side shake and body wobble — fast, chaotic squish."""
        third = length // 3

        set_bone_keyframe(self.armature, BODY, 0,           scale=_REST)
        set_bone_keyframe(self.armature, BODY, third // 2,  scale=(0.80, 1.20, 1.08))
        set_bone_keyframe(self.armature, BODY, third,       scale=(1.22, 0.82, 0.98))
        set_bone_keyframe(self.armature, BODY, third * 2,   scale=(0.90, 1.10, 1.03))
        set_bone_keyframe(self.armature, BODY, length,      scale=_REST)

        # Root rocks left-right
        set_bone_keyframe(self.armature, ROOT, 0,           location=(0, 0, 0))
        set_bone_keyframe(self.armature, ROOT, third // 2,  location=(0.25, 0, 0))
        set_bone_keyframe(self.armature, ROOT, third,       location=(-0.22, 0, 0))
        set_bone_keyframe(self.armature, ROOT, third * 2,   location=(0.12, 0, 0))
        set_bone_keyframe(self.armature, ROOT, length,      location=(0, 0, 0))

        # Eyes squish on first hit
        for eye in (EYE_L, EYE_R):
            set_bone_keyframe(self.armature, eye, 0,           scale=_BLINK_OPEN)
            set_bone_keyframe(self.armature, eye, third // 2,  scale=_BLINK_CLOSED)
            set_bone_keyframe(self.armature, eye, third,       scale=_BLINK_OPEN)

    def create_death_animation(self, length: int):
        """Slowly deflate and melt into a flat puddle."""
        quarter = length // 4

        set_bone_keyframe(self.armature, BODY, 0,           scale=_REST)
        set_bone_keyframe(self.armature, BODY, quarter,     scale=(0.95, 0.95, 0.75))
        set_bone_keyframe(self.armature, BODY, quarter * 2, scale=(1.10, 1.10, 0.45))
        set_bone_keyframe(self.armature, BODY, quarter * 3, scale=(1.35, 1.35, 0.18))
        set_bone_keyframe(self.armature, BODY, length,      scale=(1.55, 1.55, 0.05))

        # Root sinks slowly into the ground
        set_bone_keyframe(self.armature, ROOT, 0,           location=(0, 0, 0))
        set_bone_keyframe(self.armature, ROOT, quarter,     location=(0, 0, -0.08))
        set_bone_keyframe(self.armature, ROOT, quarter * 2, location=(0, 0, -0.25))
        set_bone_keyframe(self.armature, ROOT, quarter * 3, location=(0, 0, -0.45))
        set_bone_keyframe(self.armature, ROOT, length,      location=(0, 0, -0.62))

        # Eyes close slowly
        for eye in (EYE_L, EYE_R):
            set_bone_keyframe(self.armature, eye, 0,           scale=_BLINK_OPEN)
            set_bone_keyframe(self.armature, eye, quarter * 2, scale=(1.0, 1.0, 0.5))
            set_bone_keyframe(self.armature, eye, length,      scale=_BLINK_CLOSED)

        # Arms droop and flatten
        for arm, rot_dir in ((ARM_L, 1), (ARM_R, -1)):
            set_bone_keyframe(self.armature, arm, 0,           rotation=(0, 0, 0))
            set_bone_keyframe(self.armature, arm, quarter * 2, rotation=(rot_dir * 0.5, 0, 0))
            set_bone_keyframe(self.armature, arm, length,      rotation=(rot_dir * 0.9, 0, 0))

    def create_celebrate_animation(self, length: int):
        """Rapid happy bouncing with exaggerated squash/stretch."""
        sixth = length // 6

        bounces = [
            (0,          _SQUASH,     (0, 0, 0)),
            (sixth,      _BIG_STRETCH,(0, 0, 0.45)),
            (sixth * 2,  _BIG_SQUASH, (0, 0, 0)),
            (sixth * 3,  _STRETCH,    (0, 0, 0.30)),
            (sixth * 4,  _SQUASH,     (0, 0, 0)),
            (sixth * 5,  (1.0, 1.0, 1.1), (0, 0, 0.10)),
            (length,     _REST,       (0, 0, 0)),
        ]

        for frame, scale, loc in bounces:
            set_bone_keyframe(self.armature, BODY, frame, scale=scale)
            set_bone_keyframe(self.armature, ROOT, frame, location=loc)

        # Arms flail outward on each apex
        for frame, _, loc in bounces:
            if loc[2] > 0.05:  # airborne frames
                set_bone_keyframe(self.armature, ARM_L, frame, rotation=(0.7, 0, 0))
                set_bone_keyframe(self.armature, ARM_R, frame, rotation=(-0.7, 0, 0))
            else:
                set_bone_keyframe(self.armature, ARM_L, frame, rotation=(0, 0, 0))
                set_bone_keyframe(self.armature, ARM_R, frame, rotation=(0, 0, 0))

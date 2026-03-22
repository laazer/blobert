"""
Body type classes that contain their own animation logic
Much cleaner than the controller pattern!
"""

import math
from abc import ABC, abstractmethod
from ..utils.constants import AnimationTypes, AnimationConfig, BoneNames
from .keyframe_system import set_bone_keyframe


class BaseBodyType(ABC):
    """Base class for body types that know how to animate themselves"""
    
    def __init__(self, armature, rng):
        self.armature = armature
        self.rng = rng
    
    def create_all_animations(self):
        """Create all standard animations for this body type"""
        animations = AnimationTypes.get_all()
        
        for anim_name in animations:
            length = AnimationConfig.get_length(anim_name)
            
            if anim_name == AnimationTypes.IDLE:
                self.create_idle_animation(length)
            elif anim_name == AnimationTypes.MOVE:
                self.create_move_animation(length)
            elif anim_name == AnimationTypes.ATTACK:
                self.create_attack_animation(length)
            elif anim_name == AnimationTypes.DAMAGE:
                self.create_damage_animation(length)
            elif anim_name == AnimationTypes.DEATH:
                self.create_death_animation(length)
    
    @abstractmethod
    def create_idle_animation(self, length: int):
        """Create idle animation - each body type implements its own"""
        pass
    
    @abstractmethod
    def create_move_animation(self, length: int):
        """Create movement animation - each body type implements its own"""
        pass
    
    @abstractmethod
    def create_attack_animation(self, length: int):
        """Create attack animation - each body type implements its own"""
        pass
    
    @abstractmethod
    def create_damage_animation(self, length: int):
        """Create damage animation - each body type implements its own"""
        pass
    
    @abstractmethod
    def create_death_animation(self, length: int):
        """Create death animation - each body type implements its own"""
        pass
    
    # Extended animations - default implementations provided, can be overridden
    def create_spawn_animation(self, length: int):
        """Create spawn/materialize animation - default implementation"""
        # Scale from 0 to 1 with dramatic entrance
        for frame in [0, length//3, length]:
            if frame == 0:
                scale = (0.01, 0.01, 0.01)
            elif frame == length//3:
                scale = (1.2, 1.2, 1.2)  # Overshoot
            else:
                scale = (1.0, 1.0, 1.0)
            
            set_bone_keyframe(self.armature, BoneNames.ROOT, frame, scale=scale)
            
        # Add upward movement
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, -0.5))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length//2, location=(0, 0, 0.2))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))
    
    def create_special_attack_animation(self, length: int):
        """Create special attack - default is enhanced version of regular attack"""
        # Call regular attack but make it more dramatic
        windup_end = length // 3
        strike_start = windup_end
        strike_end = (length * 2) // 3
        
        # More dramatic windup with body spin
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, windup_end, rotation=(-0.8, 0, 0.5))
        set_bone_keyframe(self.armature, BoneNames.SPINE, strike_start, rotation=(1.0, 0, -0.3))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0))
    
    def create_damage_heavy_animation(self, length: int):
        """Create heavy damage reaction - longer and more dramatic than regular damage"""
        # Much bigger knockback than regular damage
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, 8, location=(-2.0, 0, 0.5))  # Bigger knockback + lift
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))
        
        # Body recoil
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, 6, rotation=(-1.2, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0))
    
    def create_damage_fire_animation(self, length: int):
        """Create fire damage - quick recoil with shaking (burning effect)"""
        # Quick knockback
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, 4, location=(-0.5, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))
        
        # Shaking/burning effect - rapid small movements
        for frame in range(4, length, 3):
            shake_x = 0.1 * self.rng.uniform(-1, 1)
            shake_z = 0.1 * self.rng.uniform(-1, 1)
            set_bone_keyframe(self.armature, BoneNames.BODY, frame, location=(shake_x, 0, shake_z))
    
    def create_damage_ice_animation(self, length: int):
        """Create ice damage - slow reaction that gets progressively slower (freezing)"""
        # Gradual slowdown effect - simulate freezing
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length//3, location=(-1.0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(-0.8, 0, 0))  # Don't fully recover
        
        # Gradual scale reduction (ice crystals forming)
        set_bone_keyframe(self.armature, BoneNames.BODY, 0, scale=(1.0, 1.0, 1.0))
        set_bone_keyframe(self.armature, BoneNames.BODY, length//2, scale=(0.9, 0.9, 1.1))
        set_bone_keyframe(self.armature, BoneNames.BODY, length, scale=(0.85, 0.85, 1.15))
    
    def create_stunned_animation(self, length: int):
        """Create stunned/dazed animation - swaying and disoriented"""
        # Swaying motion - dazed
        for frame in range(0, length + 1, 6):
            sway_amount = 0.4 * math.sin(frame * 0.2)
            wobble_z = 0.2 * math.sin(frame * 0.15)
            
            set_bone_keyframe(self.armature, BoneNames.SPINE, frame, rotation=(sway_amount, 0, wobble_z))
            
        # Slow head movement - showing disorientation
        for frame in range(0, length + 1, 8):
            head_rotation = 0.3 * math.sin(frame * 0.1)
            set_bone_keyframe(self.armature, BoneNames.HEAD, frame, rotation=(0, 0, head_rotation))
    
    def create_celebrate_animation(self, length: int):
        """Create celebration/victory animation"""
        # Rhythmic celebration - bounce up and down
        for frame in range(0, length + 1, 6):
            bounce_height = 0.3 * abs(math.sin(frame * 0.3))
            set_bone_keyframe(self.armature, BoneNames.ROOT, frame, location=(0, 0, bounce_height))
            
        # Body expression - expand with pride
        set_bone_keyframe(self.armature, BoneNames.BODY, 0, scale=(1.0, 1.0, 1.0))
        set_bone_keyframe(self.armature, BoneNames.BODY, length//2, scale=(1.1, 1.1, 0.9))
        set_bone_keyframe(self.armature, BoneNames.BODY, length, scale=(1.0, 1.0, 1.0))
    
    def create_taunt_animation(self, length: int):
        """Create taunting/provocative animation"""
        # Forward lean - aggressive posture
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length//3, rotation=(0.5, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0))
        
        # Head gesture - mockingly
        set_bone_keyframe(self.armature, BoneNames.HEAD, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length//2, location=(0.2, 0, 0.1))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length, location=(0, 0, 0))


class BlobBodyType(BaseBodyType):
    """Blob body type - squashing, stretching, pulsing creatures"""
    
    def create_idle_animation(self, length: int):
        """Gentle breathing and pulsing"""
        for frame in range(0, length + 1, 5):
            scale_factor = 1.0 + 0.3 * math.sin(frame * 0.2)
            set_bone_keyframe(self.armature, BoneNames.BODY, frame, scale=(1, 1, scale_factor))
            
            # Head bob
            head_z = 0.5 * math.sin(frame * 0.15)
            set_bone_keyframe(self.armature, BoneNames.HEAD, frame, location=(0, 0, head_z))
    
    def create_move_animation(self, length: int):
        """Dramatic squash and stretch locomotion"""
        for frame in range(0, length + 1, 2):
            progress = frame / length
            
            # Forward movement
            x_pos = 2.0 * math.sin(progress * math.pi * 2)
            
            # Squash/stretch - key characteristic of blob movement
            stretch_y = 1.0 + 1.0 * math.sin(progress * math.pi * 4)
            squash_z = 1.0 - 0.5 * math.sin(progress * math.pi * 4)
            
            set_bone_keyframe(self.armature, BoneNames.ROOT, frame, location=(x_pos, 0, 0))
            set_bone_keyframe(self.armature, BoneNames.BODY, frame, scale=(1, stretch_y, squash_z))
    
    def create_attack_animation(self, length: int):
        """Expansion/inflation attack"""
        windup_end = length // 3
        strike_end = (length * 2) // 3
        
        # Dramatic expansion - signature blob attack
        set_bone_keyframe(self.armature, BoneNames.BODY, 0, scale=(1, 1, 1))
        set_bone_keyframe(self.armature, BoneNames.BODY, windup_end, scale=(2.0, 2.0, 0.5))
        set_bone_keyframe(self.armature, BoneNames.BODY, strike_end, scale=(4.0, 4.0, 0.3))
        set_bone_keyframe(self.armature, BoneNames.BODY, length, scale=(1, 1, 1))
        
        # Head lunge
        set_bone_keyframe(self.armature, BoneNames.HEAD, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.HEAD, windup_end, location=(2.0, 0, -0.5))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length, location=(0, 0, 0))
    
    def create_damage_animation(self, length: int):
        """Compression damage reaction"""
        # Knockback
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, 5, location=(-1.0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))
        
        # Compression - blobs get squished when hit
        set_bone_keyframe(self.armature, BoneNames.BODY, 0, scale=(1, 1, 1))
        set_bone_keyframe(self.armature, BoneNames.BODY, 3, scale=(0.3, 0.3, 2.0))
        set_bone_keyframe(self.armature, BoneNames.BODY, length, scale=(1, 1, 1))
    
    def create_death_animation(self, length: int):
        """Melting/deflation death"""
        # Dramatic melt/flatten
        set_bone_keyframe(self.armature, BoneNames.BODY, 0, scale=(1, 1, 1))
        set_bone_keyframe(self.armature, BoneNames.BODY, length//2, scale=(1.5, 1.5, 0.2))
        set_bone_keyframe(self.armature, BoneNames.BODY, length, scale=(2.0, 2.0, 0.05))
        
        # Head disappears
        set_bone_keyframe(self.armature, BoneNames.HEAD, 0, scale=(1, 1, 1))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length//3, scale=(0.5, 0.5, 0.5))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length, scale=(0.01, 0.01, 0.01))
    
    # Blob-specific extended animations
    def create_spawn_animation(self, length: int):
        """Blob spawn - oozing up from the ground"""
        # Start underground, ooze upward
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, -1.0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length//2, location=(0, 0, 0.2))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))
        
        # Blob formation - start flat, become round
        set_bone_keyframe(self.armature, BoneNames.BODY, 0, scale=(2.0, 2.0, 0.1))  # Flat puddle
        set_bone_keyframe(self.armature, BoneNames.BODY, length//3, scale=(1.5, 1.5, 0.5))  # Rising
        set_bone_keyframe(self.armature, BoneNames.BODY, length, scale=(1.0, 1.0, 1.0))     # Full form
        
        # Head emerges last
        set_bone_keyframe(self.armature, BoneNames.HEAD, 0, scale=(0.01, 0.01, 0.01))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length//2, scale=(0.01, 0.01, 0.01))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length, scale=(1.0, 1.0, 1.0))
    
    def create_special_attack_animation(self, length: int):
        """Blob special attack - massive expansion slam"""
        windup_end = length // 4
        expansion_peak = length // 2
        slam_end = (length * 3) // 4
        
        # Extreme expansion attack - much bigger than regular
        set_bone_keyframe(self.armature, BoneNames.BODY, 0, scale=(1, 1, 1))
        set_bone_keyframe(self.armature, BoneNames.BODY, windup_end, scale=(0.5, 0.5, 2.0))   # Compress
        set_bone_keyframe(self.armature, BoneNames.BODY, expansion_peak, scale=(6.0, 6.0, 0.2)) # MASSIVE expansion
        set_bone_keyframe(self.armature, BoneNames.BODY, slam_end, scale=(4.0, 4.0, 0.5))      # Settle
        set_bone_keyframe(self.armature, BoneNames.BODY, length, scale=(1, 1, 1))              # Return
        
        # Ground slam effect - lift up then slam down
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, windup_end, location=(0, 0, 0.5))
        set_bone_keyframe(self.armature, BoneNames.ROOT, expansion_peak, location=(0, 0, -0.3))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))


class QuadrupedBodyType(BaseBodyType):
    """Quadruped body type - multi-legged creatures with tripod gait"""
    
    def create_idle_animation(self, length: int):
        """Body sway and occasional leg movements"""
        for frame in range(0, length + 1, 8):
            body_sway = 0.3 * math.sin(frame * 0.1)
            set_bone_keyframe(self.armature, BoneNames.SPINE, frame, rotation=(body_sway, 0, 0))
            
            # Random leg twitches - quadrupeds are restless
            if frame % 20 == 1:
                leg_names = BoneNames.get_quadruped_legs()
                for i, leg_name in enumerate(leg_names):
                    if leg_name in [bone.name for bone in self.armature.pose.bones]:
                        twitch = 0.3 * math.sin((frame + i * 10) * 0.3)
                        set_bone_keyframe(self.armature, leg_name, frame, rotation=(twitch, 0, 0))
    
    def create_move_animation(self, length: int):
        """Tripod gait - classic multi-legged locomotion"""
        for frame in range(0, length + 1, 2):
            progress = frame / length
            
            # Body forward movement
            x_movement = 1.5 * progress
            set_bone_keyframe(self.armature, BoneNames.ROOT, frame, location=(x_movement, 0, 0))
            
            # Body bob - quadrupeds bob as they walk
            body_y = 0.3 * math.sin(progress * math.pi * 6)
            set_bone_keyframe(self.armature, BoneNames.SPINE, frame, location=(0, 0, body_y))
            
            # Tripod gait - alternating sets of legs
            leg_cycle_1 = 0.8 * math.sin(progress * math.pi * 4)
            leg_cycle_2 = 0.8 * math.sin(progress * math.pi * 4 + math.pi)
            
            # Front and back legs alternate
            set_bone_keyframe(self.armature, BoneNames.LEG_FRONT_LEFT, frame, rotation=(leg_cycle_1, 0, 0))
            set_bone_keyframe(self.armature, BoneNames.LEG_BACK_RIGHT, frame, rotation=(leg_cycle_1, 0, 0))
            set_bone_keyframe(self.armature, BoneNames.LEG_FRONT_RIGHT, frame, rotation=(leg_cycle_2, 0, 0))
            set_bone_keyframe(self.armature, BoneNames.LEG_BACK_LEFT, frame, rotation=(leg_cycle_2, 0, 0))
            
            # Middle legs (for 6-legged creatures)
            if BoneNames.LEG_MIDDLE_LEFT in [bone.name for bone in self.armature.pose.bones]:
                leg_cycle_mid = 0.6 * math.sin(progress * math.pi * 4 + math.pi/2)
                set_bone_keyframe(self.armature, BoneNames.LEG_MIDDLE_LEFT, frame, rotation=(leg_cycle_mid, 0, 0))
                set_bone_keyframe(self.armature, BoneNames.LEG_MIDDLE_RIGHT, frame, rotation=(leg_cycle_mid, 0, 0))
    
    def create_attack_animation(self, length: int):
        """Pounce attack - crouch to coil all legs, then spring forward at target"""
        crouch_frame = length // 3       # frame 12 - full crouch
        leap_peak_frame = length // 2    # frame 18 - airborne peak
        land_frame = (length * 3) // 4  # frame 27 - impact landing

        # Spine: crouch low → spring high → land impact → recover
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0), location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, crouch_frame, rotation=(-0.8, 0, 0), location=(0, 0, -0.3))
        set_bone_keyframe(self.armature, BoneNames.SPINE, leap_peak_frame, rotation=(1.2, 0, 0), location=(0, 0, 0.5))
        set_bone_keyframe(self.armature, BoneNames.SPINE, land_frame, rotation=(0.3, 0, 0), location=(0, 0, 0.1))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0), location=(0, 0, 0))

        # Head follows spine
        set_bone_keyframe(self.armature, BoneNames.HEAD, crouch_frame, location=(0, 0, -0.3))
        set_bone_keyframe(self.armature, BoneNames.HEAD, leap_peak_frame, location=(0, 0, 0.5))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length, location=(0, 0, 0))

        # All legs coil on crouch, extend on leap, brace on landing
        for leg_name in BoneNames.get_quadruped_legs():
            set_bone_keyframe(self.armature, leg_name, 0, rotation=(0, 0, 0))
            set_bone_keyframe(self.armature, leg_name, crouch_frame, rotation=(-0.5, 0, 0))
            set_bone_keyframe(self.armature, leg_name, leap_peak_frame, rotation=(0.8, 0, 0))
            set_bone_keyframe(self.armature, leg_name, land_frame, rotation=(-0.3, 0, 0))
            set_bone_keyframe(self.armature, leg_name, length, rotation=(0, 0, 0))
    
    def create_special_attack_animation(self, length: int):
        """Rearing slash — rise on hind legs, front legs slash down"""
        rise_frame = length // 3         # frame 20 - fully reared
        slash_frame = (length * 2) // 3  # frame 40 - claws slam

        # Spine rears back then crashes forward
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0), location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, rise_frame, rotation=(-1.5, 0, 0), location=(0, 0, 0.8))
        set_bone_keyframe(self.armature, BoneNames.SPINE, slash_frame, rotation=(1.0, 0, 0), location=(0, 0, 0.3))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0), location=(0, 0, 0))

        # Head rises with spine
        set_bone_keyframe(self.armature, BoneNames.HEAD, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.HEAD, rise_frame, location=(0, 0, 1.0))
        set_bone_keyframe(self.armature, BoneNames.HEAD, slash_frame, location=(0, 0, 0.3))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length, location=(0, 0, 0))

        # Front legs raise then slam down (claw strike)
        for leg_name in [BoneNames.LEG_FRONT_LEFT, BoneNames.LEG_FRONT_RIGHT]:
            set_bone_keyframe(self.armature, leg_name, 0, rotation=(0, 0, 0))
            set_bone_keyframe(self.armature, leg_name, rise_frame, rotation=(-1.2, 0, 0))
            set_bone_keyframe(self.armature, leg_name, slash_frame, rotation=(1.0, 0, 0))
            set_bone_keyframe(self.armature, leg_name, length, rotation=(0, 0, 0))

        # Back and middle legs brace to support the rear-up
        for leg_name in [BoneNames.LEG_BACK_LEFT, BoneNames.LEG_BACK_RIGHT,
                         BoneNames.LEG_MIDDLE_LEFT, BoneNames.LEG_MIDDLE_RIGHT]:
            set_bone_keyframe(self.armature, leg_name, 0, rotation=(0, 0, 0))
            set_bone_keyframe(self.armature, leg_name, rise_frame, rotation=(0.6, 0, 0))
            set_bone_keyframe(self.armature, leg_name, length, rotation=(0, 0, 0))

    def create_damage_animation(self, length: int):
        """Recoil and stagger"""
        # Knockback
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, 5, location=(-1.0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))

        # Spine recoil - quadrupeds arch back when hit
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, 3, rotation=(-0.8, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0))
    
    def create_death_animation(self, length: int):
        """Collapse and curl up"""
        # Dramatic fall sequence
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length//3, rotation=(-0.5, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, (length*2)//3, rotation=(-1.2, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(-1.6, 0, 0))
        
        # Body drops to ground
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, -0.8))


class HumanoidBodyType(BaseBodyType):
    """Humanoid body type - bipedal creatures with arms"""
    
    def create_idle_animation(self, length: int):
        """Breathing and subtle swaying"""
        for frame in range(0, length + 1, 6):
            chest_rise = 0.3 * math.sin(frame * 0.12)
            set_bone_keyframe(self.armature, BoneNames.SPINE, frame, location=(0, 0, chest_rise))
            
            # Arm sway - humanoids move their arms when idle
            arm_sway = 0.3 * math.sin(frame * 0.1)
            set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, frame, rotation=(arm_sway, 0, 0))
            set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, frame, rotation=(-arm_sway, 0, 0))
    
    def create_move_animation(self, length: int):
        """Bipedal walking with arm swing"""
        for frame in range(0, length + 1, 2):
            progress = frame / length
            
            # Forward walking motion
            x_pos = 1.0 * progress
            set_bone_keyframe(self.armature, BoneNames.ROOT, frame, location=(x_pos, 0, 0))
            
            # Leg alternation - classic bipedal gait
            leg_swing = 1.0 * math.sin(progress * math.pi * 4)
            set_bone_keyframe(self.armature, BoneNames.LEG_LEFT, frame, rotation=(leg_swing, 0, 0))
            set_bone_keyframe(self.armature, BoneNames.LEG_RIGHT, frame, rotation=(-leg_swing, 0, 0))
            
            # Opposite arm swing - natural walking motion
            arm_swing = 0.6 * math.sin(progress * math.pi * 4 + math.pi)
            set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, frame, rotation=(arm_swing, 0, 0))
            set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, frame, rotation=(-arm_swing, 0, 0))
    
    def create_attack_animation(self, length: int):
        """Fire punch with body lean and guard arm"""
        windup_frame = length // 3  # frame 12 - arm cocked, spine coiled
        strike_frame = length // 2  # frame 18 - fist connects

        # Spine twists into punch on windup, uncoils and leans forward on strike
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, windup_frame, rotation=(0.2, 0, -0.4))
        set_bone_keyframe(self.armature, BoneNames.SPINE, strike_frame, rotation=(0.4, 0, 0.3))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0))

        # Right arm: pull back → punch forward → return
        set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, windup_frame, rotation=(-1.2, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, strike_frame, rotation=(1.0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, length, rotation=(0, 0, 0))

        # Left arm raises as a guard during windup, lowers after impact
        set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, windup_frame, rotation=(0.8, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, strike_frame, rotation=(0.5, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, length, rotation=(0, 0, 0))
    
    def create_special_attack_animation(self, length: int):
        """Two-handed overhead slam — raise both arms then crash down"""
        raise_frame = length // 3       # frame 20 - arms fully overhead
        slam_frame = (length * 2) // 3  # frame 40 - impact

        # Spine: lean back during raise, snap hard forward on slam
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0), location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, raise_frame, rotation=(-0.6, 0, 0), location=(0, 0, 0.2))
        set_bone_keyframe(self.armature, BoneNames.SPINE, slam_frame, rotation=(0.8, 0, 0), location=(0, 0, -0.2))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0), location=(0, 0, 0))

        # Both arms sweep overhead then slam down
        for arm_name in [BoneNames.ARM_LEFT, BoneNames.ARM_RIGHT]:
            set_bone_keyframe(self.armature, arm_name, 0, rotation=(0, 0, 0))
            set_bone_keyframe(self.armature, arm_name, raise_frame, rotation=(-1.8, 0, 0))
            set_bone_keyframe(self.armature, arm_name, slam_frame, rotation=(1.2, 0, 0))
            set_bone_keyframe(self.armature, arm_name, length, rotation=(0, 0, 0))

        # Root drops slightly on impact to sell the weight
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, slam_frame, location=(0, 0, -0.3))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))

    def create_damage_animation(self, length: int):
        """Stagger back reaction"""
        # Knockback
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, 5, location=(-1.0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))
        
        # Body recoil - humanoids lean back when hit
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, 3, rotation=(-0.8, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0))
    
    def create_death_animation(self, length: int):
        """Dramatic collapse"""
        # Fall backward sequence
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length//3, rotation=(-0.5, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, (length*2)//3, rotation=(-1.2, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(-1.6, 0, 0))
        
        # Body drops
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, -0.8))
        
        # Arms fall limp - characteristic humanoid death
        set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, length//2, rotation=(0.5, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, length//2, rotation=(0.5, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, length, rotation=(1.2, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, length, rotation=(1.2, 0, 0))


# Factory for creating body type instances
class BodyTypeFactory:
    """Factory for creating body type instances"""
    
    BODY_TYPES = {
        'blob': BlobBodyType,
        'slime': BlobBodyType,  # Same as blob
        'quadruped': QuadrupedBodyType,
        'humanoid': HumanoidBodyType,
    }
    
    @classmethod
    def create_body_type(cls, body_type_name: str, armature, rng) -> BaseBodyType:
        """Create appropriate body type instance"""
        body_class = cls.BODY_TYPES.get(body_type_name, BlobBodyType)
        return body_class(armature, rng)
    
    @classmethod
    def get_available_types(cls) -> list:
        """Get list of available body types"""
        return list(cls.BODY_TYPES.keys())
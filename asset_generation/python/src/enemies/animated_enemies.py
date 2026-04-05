"""
Animated enemy builders with enhanced materials and animations
"""

import math
from mathutils import Euler
from .animated_acid_spitter import AnimatedAcidSpitter
from .animated_adhesion_bug import AnimatedAdhesionBug
from .animated_carapace_husk import AnimatedCarapaceHusk
from .animated_claw_crawler import AnimatedClawCrawler
from .base_enemy import BaseEnemy
from ..core.blender_utils import bind_mesh_to_armature, join_objects, apply_smooth_shading, random_variance, create_sphere, create_cylinder
from ..animations.armature_builders import create_blob_armature, create_humanoid_armature
from ..animations.animation_system import create_all_animations
from ..materials.material_system import get_enemy_materials, apply_material_to_object


class AnimatedTarSlug(BaseEnemy):
    """Elongated slug with blob movement"""
    
    def create_body(self):
        """Create main slug body"""
        length = random_variance(2.0, 0.3, self.rng)
        width = random_variance(0.8, 0.2, self.rng)
        height = random_variance(0.6, 0.1, self.rng)
        
        body = create_sphere(location=(0, 0, height * 0.5), scale=(length, width, height))
        self.parts.append(body)
        
        # Store dimensions for other parts
        self.length = length
        self.width = width  
        self.height = height
        
    def create_head(self):
        """Create head bump"""
        head_scale = self.width * 0.4
        head = create_sphere(
            location=(self.length * 0.7, 0, self.height * 0.8), 
            scale=(head_scale, head_scale, head_scale)
        )
        self.parts.append(head)
        
    def create_limbs(self):
        """Create eye stalks and eyes"""
        # Eye stalks
        for side in [-1, 1]:
            stalk = create_cylinder(
                location=(self.length * 0.6, side * self.width * 0.3, self.height + 0.3), 
                scale=(0.05, 0.05, 0.3), vertices=6
            )
            self.parts.append(stalk)
            
            eye = create_sphere(
                location=(self.length * 0.6, side * self.width * 0.3, self.height + 0.6), 
                scale=(0.1, 0.1, 0.1)
            )
            self.parts.append(eye)
    
    def apply_materials(self):
        """Apply tar slug themed materials"""
        enemy_mats = get_enemy_materials('tar_slug', self.materials, self.rng)
        
        # Apply materials to individual parts for variation
        apply_material_to_object(self.parts[0], enemy_mats['body'])    # Body - tar black
        apply_material_to_object(self.parts[1], enemy_mats['head'])    # Head - slime green
        
        # Apply materials to eye stalks and eyes
        stalk_material = enemy_mats['limbs']   # Stalks - dirt brown
        eye_material = enemy_mats['extra']     # Eyes - random theme color
        
        for i, part in enumerate(self.parts[2:]):  # Skip body and head
            if i % 2 == 0:  # Eye stalks (even indices)
                apply_material_to_object(part, stalk_material)
            else:  # Eyes (odd indices)
                apply_material_to_object(part, eye_material)
    
    def create_armature(self):
        """Create blob armature for tar slug"""
        return create_blob_armature("tar_slug", self.height)
    
    def get_body_type(self):
        """Return body type for animation system"""
        from ..utils.constants import EnemyBodyTypes
        return EnemyBodyTypes.BLOB


class AnimatedEmberImp(BaseEnemy):
    """Humanoid fire creature"""
    
    def create_body(self):
        """Create cylindrical body"""
        body_height = random_variance(1.2, 0.2, self.rng)
        body_width = random_variance(0.4, 0.1, self.rng)
        body = create_cylinder(
            location=(0, 0, body_height * 0.5), 
            scale=(body_width, body_width, body_height), vertices=8
        )
        self.parts.append(body)
        
        # Store dimensions
        self.body_height = body_height
        self.body_width = body_width
        
    def create_head(self):
        """Create spherical head"""
        head_scale = self.body_width * 1.1
        head = create_sphere(
            location=(0, 0, self.body_height + head_scale * 0.7), 
            scale=(head_scale, head_scale, head_scale)
        )
        self.parts.append(head)
        
    def create_limbs(self):
        """Create arms and legs"""
        # Arms
        arm_length = random_variance(0.8, 0.2, self.rng)
        for side in [-1, 1]:
            arm = create_cylinder(
                location=(side * (self.body_width + arm_length * 0.5), 0, self.body_height * 0.7), 
                scale=(0.12, 0.12, arm_length), vertices=6
            )
            arm.rotation_euler = Euler((0, 0, math.pi/2))
            self.parts.append(arm)
            
            hand = create_sphere(
                location=(side * (self.body_width + arm_length), 0, self.body_height * 0.7), 
                scale=(0.15, 0.15, 0.15)
            )
            self.parts.append(hand)
        
        # Legs
        leg_length = random_variance(0.7, 0.1, self.rng)
        for side in [-1, 1]:
            leg = create_cylinder(
                location=(side * self.body_width * 0.3, 0, leg_length * 0.5), 
                scale=(0.12, 0.12, leg_length), vertices=6
            )
            self.parts.append(leg)
    
    def apply_materials(self):
        """Apply fire-themed materials"""
        enemy_mats = get_enemy_materials('ember_imp', self.materials, self.rng)
        
        # Apply materials to individual parts for variation
        apply_material_to_object(self.parts[0], enemy_mats['body'])    # Body - fire orange
        apply_material_to_object(self.parts[1], enemy_mats['head'])    # Head - ember red
        
        # Apply materials to limbs
        limb_material = enemy_mats['limbs']    # Arms/legs - bone white
        hand_material = enemy_mats['extra']    # Hands - random theme color
        
        part_index = 2  # Start after body and head
        # Arms
        for i in range(2):  # 2 arms
            apply_material_to_object(self.parts[part_index], limb_material)     # Arm
            apply_material_to_object(self.parts[part_index + 1], hand_material) # Hand
            part_index += 2
        
        # Legs  
        for i in range(2):  # 2 legs
            apply_material_to_object(self.parts[part_index], limb_material)
            part_index += 1
    
    def create_armature(self):
        """Create humanoid armature for ember imp"""
        return create_humanoid_armature("ember_imp", self.body_height)
    
    def get_body_type(self):
        """Return body type for animation system"""
        from ..utils.constants import EnemyBodyTypes
        return EnemyBodyTypes.HUMANOID


class AnimatedEnemyBuilder:
    """Factory for creating animated enemies"""

    ENEMY_CLASSES = {
        'adhesion_bug': AnimatedAdhesionBug,
        'tar_slug': AnimatedTarSlug,
        'ember_imp': AnimatedEmberImp,
        'acid_spitter': AnimatedAcidSpitter,
        'claw_crawler': AnimatedClawCrawler,
        'carapace_husk': AnimatedCarapaceHusk,
    }
    
    @classmethod
    def create_enemy(cls, enemy_type, materials, rng, prefab_mesh=None):
        """Create an animated enemy and return (armature, mesh, attack_profile).

        Args:
            enemy_type: Registered enemy type string.
            materials: Material system dict from setup_materials().
            rng: Random number generator for procedural variation.
            prefab_mesh: Optional pre-imported mesh to use instead of
                procedural geometry (see src/prefabs/prefab_loader.py).
        """
        if enemy_type not in cls.ENEMY_CLASSES:
            raise ValueError(f"Unknown enemy type: {enemy_type}")

        enemy_class = cls.ENEMY_CLASSES[enemy_type]
        enemy = enemy_class(enemy_type, materials, rng)
        build_result = enemy.build(prefab_mesh=prefab_mesh)
        attack_profile = enemy.get_attack_profile()

        if isinstance(build_result, tuple):
            armature, mesh = build_result
            return armature, mesh, attack_profile

        return build_result, None, attack_profile
    
    @classmethod
    def get_available_types(cls):
        """Get list of available animated enemy types"""
        return list(cls.ENEMY_CLASSES.keys())
"""
Example of how easy it is to add new enemies with the new architecture

This demonstrates the power of the base animation classes - you can create
new enemies that inherit behavior from existing body types.
"""

from .base_enemy import BaseEnemy
from ..core.blender_utils import create_sphere, create_cylinder
from ..materials.material_system import get_enemy_materials, apply_material_to_object
from ..animations.armature_builders import create_humanoid_armature
from ..utils.constants import EnemyBodyTypes


class ExampleSpider(BaseEnemy):
    """8-legged spider - uses quadruped animation but with more legs"""
    
    def create_body(self):
        """Small spherical body"""
        self.body_scale = 0.8
        body = create_sphere(location=(0, 0, 0.2), scale=(self.body_scale, self.body_scale, self.body_scale * 0.7))
        self.parts.append(body)
    
    def create_head(self):
        """Small head merged with body"""
        pass  # Spider head integrated with body
    
    def create_limbs(self):
        """8 spider legs radiating outward"""
        leg_angles = [i * 45 for i in range(8)]  # Every 45 degrees
        
        for i, angle in enumerate(leg_angles):
            import math
            x_offset = math.cos(math.radians(angle)) * self.body_scale * 0.4
            y_offset = math.sin(math.radians(angle)) * self.body_scale * 0.4
            
            leg = create_cylinder(
                location=(x_offset, y_offset, 0.1),
                scale=(0.05, 0.05, 0.4),
                vertices=6
            )
            self.parts.append(leg)
    
    def create_armature(self):
        """Use quadruped armature (will automatically get 6-legged animation)"""
        from ..animations.armature_builders import create_quadruped_armature
        return create_quadruped_armature("spider", self.body_scale)
    
    def get_body_type(self):
        """Inherits quadruped movement (6-legged gait works for 8 legs too!)"""
        return EnemyBodyTypes.QUADRUPED
    
    def apply_materials(self):
        """Apply spider-themed materials"""
        enemy_mats = get_enemy_materials('claw_crawler', self.materials, self.rng)  # Reuse theme
        
        # Body uses main material
        apply_material_to_object(self.parts[0], enemy_mats['body'])
        
        # All legs use limb material  
        for part in self.parts[1:]:
            apply_material_to_object(part, enemy_mats['limbs'])


class ExampleGhost(BaseEnemy):
    """Floating ghost - uses blob animation but floats"""
    
    def create_body(self):
        """Wispy main body"""
        body = create_sphere(location=(0, 0, 1.0), scale=(1.2, 1.2, 1.5))
        self.parts.append(body)
        self.body_scale = 1.2
    
    def create_head(self):
        """Integrated head"""
        pass  # Ghost head is part of body
        
    def create_limbs(self):
        """Wispy trailing tendrils"""
        for i in range(3):
            x_offset = (i - 1) * 0.3
            tendril = create_cylinder(
                location=(x_offset, 0, 0.3),
                scale=(0.1, 0.1, 0.8),
                vertices=6
            )
            self.parts.append(tendril)
    
    def create_armature(self):
        """Simple blob armature"""
        from ..animations.armature_builders import create_blob_armature  
        return create_blob_armature("ghost", self.body_scale)
    
    def get_body_type(self):
        """Uses blob movement (floating/pulsing)"""
        return EnemyBodyTypes.BLOB


class ExampleMech(BaseEnemy):
    """Robot mech - uses humanoid animation but bigger"""
    
    def create_body(self):
        """Large cylindrical body"""
        self.body_height = 2.0
        self.body_width = 0.8
        body = create_cylinder(
            location=(0, 0, self.body_height * 0.5),
            scale=(self.body_width, self.body_width, self.body_height),
            vertices=8
        )
        self.parts.append(body)
    
    def create_head(self):
        """Rectangular head"""
        head = create_cylinder(
            location=(0, 0, self.body_height + 0.3),
            scale=(0.4, 0.4, 0.3),
            vertices=4  # Square
        )
        self.parts.append(head)
    
    def create_limbs(self):
        """Robotic arms and legs"""
        # Arms
        for side in [-1, 1]:
            arm = create_cylinder(
                location=(side * (self.body_width + 0.4), 0, self.body_height * 0.7),
                scale=(0.15, 0.15, 0.8),
                vertices=6
            )
            self.parts.append(arm)
        
        # Legs  
        for side in [-1, 1]:
            leg = create_cylinder(
                location=(side * self.body_width * 0.3, 0, 0.6),
                scale=(0.15, 0.15, 1.2),
                vertices=6
            )
            self.parts.append(leg)
    
    def create_armature(self):
        """Humanoid armature for walking/punching"""
        from ..animations.armature_builders import create_humanoid_armature
        return create_humanoid_armature("mech", self.body_height)
    
    def get_body_type(self):
        """Uses humanoid movement (walking, punching)"""
        return EnemyBodyTypes.HUMANOID


# To add these to the system, just update the factory:
# EXAMPLE_ENEMY_CLASSES = {
#     'spider': ExampleSpider,
#     'ghost': ExampleGhost,  
#     'mech': ExampleMech,
# }

"""
✨ Benefits of this architecture:

1. **Reusable Animations**: New enemies inherit movement patterns
   - Spider gets 6-legged gait animation for free
   - Ghost gets floating/pulsing animation for free
   - Mech gets walking/punching animation for free

2. **Mix and Match**: Any enemy can use any body type
   - Want a floating robot? Give it BLOB body type
   - Want a walking slime? Give it HUMANOID body type

3. **Easy Extension**: Adding new enemies is just geometry + material choices
   - No need to rewrite animation code
   - Focus on visual design, not movement programming

4. **Consistent Behavior**: All enemies of same body type move similarly
   - Makes game feel cohesive
   - Predictable behavior for players

5. **Separation of Concerns**: 
   - Enemies define WHAT they look like
   - Body types define HOW they move
   - Materials define WHAT they're made of
   - Armatures define WHERE the bones are
"""
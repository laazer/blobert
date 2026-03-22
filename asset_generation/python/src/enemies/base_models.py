"""
Base model classes that define common enemy shapes and patterns
"""

from abc import ABC, abstractmethod
from ..core.blender_utils import create_sphere, create_cylinder, random_variance
from ..materials.material_system import get_enemy_materials, apply_material_to_object


class BaseModelType(ABC):
    """Base class for enemy model types"""
    
    def __init__(self, name, materials, rng):
        self.name = name
        self.materials = materials
        self.rng = rng
        self.parts = []
    
    @abstractmethod
    def create_geometry(self):
        """Create the enemy geometry - implemented by each model type"""
        pass
    
    def apply_themed_materials(self):
        """Apply materials based on enemy theme"""
        enemy_mats = get_enemy_materials(self.name, self.materials, self.rng)
        
        # Default material application - can be overridden
        if len(self.parts) >= 1:
            apply_material_to_object(self.parts[0], enemy_mats['body'])
        if len(self.parts) >= 2:
            apply_material_to_object(self.parts[1], enemy_mats['head'])
        
        # Apply limb materials to remaining parts
        for part in self.parts[2:]:
            apply_material_to_object(part, enemy_mats['limbs'])


class InsectoidModel(BaseModelType):
    """Multi-segment insectoid with legs and eyes"""
    
    def create_geometry(self):
        """Create segmented insect body with legs"""
        # Main body sphere
        self.body_scale = random_variance(1.0, 0.2, self.rng)
        body = create_sphere(
            location=(0, 0, 0.3), 
            scale=(self.body_scale, self.body_scale * 0.8, self.body_scale * 0.9)
        )
        self.parts.append(body)
        
        # Head sphere in front
        head_scale = self.body_scale * random_variance(0.6, 0.1, self.rng)
        head_offset = self.body_scale + head_scale * 0.5
        head = create_sphere(
            location=(head_offset, 0, 0.3), 
            scale=(head_scale, head_scale, head_scale)
        )
        self.parts.append(head)
        
        # Eyes on head
        eye_count = self.rng.choice([2, 4])
        eye_scale = head_scale * 0.15
        for i in range(eye_count):
            side = 1 if i % 2 == 0 else -1
            eye_x = head_offset + head_scale * 0.7
            eye_y = side * head_scale * 0.4
            eye_z = 0.4
            eye = create_sphere(
                location=(eye_x, eye_y, eye_z), 
                scale=(eye_scale, eye_scale, eye_scale)
            )
            self.parts.append(eye)
        
        # 6 legs in tripod arrangement
        leg_positions = [
            (self.body_scale * 0.3, self.body_scale * 0.3, 0),   # front left
            (self.body_scale * 0.3, -self.body_scale * 0.3, 0),  # front right  
            (0, self.body_scale * 0.4, 0),                        # middle left
            (0, -self.body_scale * 0.4, 0),                       # middle right
            (-self.body_scale * 0.2, self.body_scale * 0.3, 0),  # back left
            (-self.body_scale * 0.2, -self.body_scale * 0.3, 0), # back right
        ]
        
        for leg_x, leg_y, leg_z in leg_positions:
            leg_length = random_variance(0.3, 0.1, self.rng)
            leg = create_cylinder(
                location=(leg_x, leg_y, leg_z), 
                scale=(0.08, 0.08, leg_length),
                vertices=6
            )
            self.parts.append(leg)
    
    def apply_themed_materials(self):
        """Custom material application for insects"""
        enemy_mats = get_enemy_materials(self.name, self.materials, self.rng)
        
        apply_material_to_object(self.parts[0], enemy_mats['body'])    # Body
        apply_material_to_object(self.parts[1], enemy_mats['head'])    # Head
        
        # Legs and eyes get different materials
        leg_material = enemy_mats['limbs']
        eye_material = enemy_mats['extra']
        
        for i, part in enumerate(self.parts[2:]):
            if i < 6:  # Legs
                apply_material_to_object(part, leg_material)
            else:  # Eyes
                apply_material_to_object(part, eye_material)


class BlobModel(BaseModelType):
    """Stretchy blob creature with eye stalks"""
    
    def create_geometry(self):
        """Create elongated blob with eye stalks"""
        # Main blob body
        self.length = random_variance(2.0, 0.3, self.rng)
        self.width = random_variance(0.8, 0.2, self.rng)
        self.height = random_variance(0.6, 0.1, self.rng)
        
        body = create_sphere(
            location=(0, 0, self.height * 0.5), 
            scale=(self.length, self.width, self.height)
        )
        self.parts.append(body)
        
        # Head bump
        head_scale = self.width * 0.4
        head = create_sphere(
            location=(self.length * 0.7, 0, self.height * 0.8), 
            scale=(head_scale, head_scale, head_scale)
        )
        self.parts.append(head)
        
        # Eye stalks
        for side in [-1, 1]:
            stalk = create_cylinder(
                location=(self.length * 0.6, side * self.width * 0.3, self.height + 0.3), 
                scale=(0.05, 0.05, 0.3), 
                vertices=6
            )
            self.parts.append(stalk)
            
            eye = create_sphere(
                location=(self.length * 0.6, side * self.width * 0.3, self.height + 0.6), 
                scale=(0.1, 0.1, 0.1)
            )
            self.parts.append(eye)
    
    def apply_themed_materials(self):
        """Custom material application for blobs"""
        enemy_mats = get_enemy_materials(self.name, self.materials, self.rng)
        
        apply_material_to_object(self.parts[0], enemy_mats['body'])    # Body
        apply_material_to_object(self.parts[1], enemy_mats['head'])    # Head
        
        # Eye stalks and eyes alternate materials
        stalk_material = enemy_mats['limbs']
        eye_material = enemy_mats['extra']
        
        for i, part in enumerate(self.parts[2:]):
            if i % 2 == 0:  # Eye stalks (even indices)
                apply_material_to_object(part, stalk_material)
            else:  # Eyes (odd indices)
                apply_material_to_object(part, eye_material)


class HumanoidModel(BaseModelType):
    """Bipedal humanoid creature with arms and legs"""
    
    def create_geometry(self):
        """Create humanoid body with limbs"""
        # Cylindrical body
        self.body_height = random_variance(1.2, 0.2, self.rng)
        self.body_width = random_variance(0.4, 0.1, self.rng)
        body = create_cylinder(
            location=(0, 0, self.body_height * 0.5), 
            scale=(self.body_width, self.body_width, self.body_height), 
            vertices=8
        )
        self.parts.append(body)
        
        # Spherical head
        head_scale = self.body_width * 1.1
        head = create_sphere(
            location=(0, 0, self.body_height + head_scale * 0.7), 
            scale=(head_scale, head_scale, head_scale)
        )
        self.parts.append(head)
        
        # Arms
        arm_length = random_variance(0.8, 0.2, self.rng)
        for side in [-1, 1]:
            arm = create_cylinder(
                location=(side * (self.body_width + arm_length * 0.5), 0, self.body_height * 0.7), 
                scale=(0.12, 0.12, arm_length), 
                vertices=6
            )
            # Rotate arms to horizontal
            arm.rotation_euler = (0, 0, 1.57 * side)  # 90 degrees
            self.parts.append(arm)
            
            # Hands
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
                scale=(0.12, 0.12, leg_length), 
                vertices=6
            )
            self.parts.append(leg)
    
    def apply_themed_materials(self):
        """Custom material application for humanoids"""
        enemy_mats = get_enemy_materials(self.name, self.materials, self.rng)
        
        apply_material_to_object(self.parts[0], enemy_mats['body'])    # Body
        apply_material_to_object(self.parts[1], enemy_mats['head'])    # Head
        
        # Limbs and hands
        limb_material = enemy_mats['limbs']
        hand_material = enemy_mats['extra']
        
        part_index = 2
        # Arms and hands
        for i in range(2):  # 2 arms
            apply_material_to_object(self.parts[part_index], limb_material)     # Arm
            apply_material_to_object(self.parts[part_index + 1], hand_material) # Hand
            part_index += 2
        
        # Legs  
        for i in range(2):  # 2 legs
            apply_material_to_object(self.parts[part_index], limb_material)
            part_index += 1


# Factory for creating model types
class ModelTypeFactory:
    """Factory for creating appropriate model types"""
    
    MODEL_TYPES = {
        'insectoid': InsectoidModel,
        'blob': BlobModel,
        'humanoid': HumanoidModel,
    }
    
    @classmethod
    def create_model(cls, model_type: str, name: str, materials, rng) -> BaseModelType:
        """Create appropriate model type"""
        model_class = cls.MODEL_TYPES.get(model_type, InsectoidModel)
        model = model_class(name, materials, rng)
        model.create_geometry()
        model.apply_themed_materials()
        return model
    
    @classmethod
    def get_available_types(cls) -> list:
        """Get list of available model types"""
        return list(cls.MODEL_TYPES.keys())
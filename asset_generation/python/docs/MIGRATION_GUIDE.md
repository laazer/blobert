# Migration Guide

## For Users

### Current (Working)
```bash
# All functionality is available via the legacy script
./enemy.sh list
./enemy.sh animated adhesion_bug 1
./enemy.sh view adhesion_bug_animated_00 --anim move
```

### Future (Organized)
```bash
# Clean, organized CLI
python main.py list
python main.py animated adhesion_bug 1
python main.py view adhesion_bug_animated_00 --anim move
```

## For Developers

### Current Structure (Legacy)
```
animated_enemy_generator.py  # Monolithic 1000+ line file
enemy_cli.py                # CLI with embedded Blender scripts
```

### New Structure (Organized)
```
src/
├── core/blender_utils.py    # Clean Blender utilities
├── materials/               # Separate material system  
├── animations/              # Dedicated animation system
└── enemies/                 # Enemy-specific code
```

### Benefits of New Structure

1. **Modularity**: Import only what you need
2. **Testability**: Each module can be tested in isolation
3. **Extensibility**: Add new features without touching core systems
4. **Maintainability**: Clear responsibilities and boundaries

### Example: Adding a New Enemy

#### Old Way (Legacy)
```python
# Edit massive animated_enemy_generator.py file
# Add function at line 800+
# Update ANIMATED_ENEMY_BUILDERS dict
# Risk breaking existing functionality
```

#### New Way (Organized)
```python
# Create src/enemies/new_enemy.py
from src.core.blender_utils import create_sphere
from src.materials.material_system import get_enemy_materials

class NewEnemy(BaseEnemy):
    def build(self):
        # Clean, focused implementation
        pass
```

## Timeline

- **Week 1**: ✅ Infrastructure and core utilities  
- **Week 2**: ✅ Animation system extraction
- **Week 3**: ✅ Enemy system refactoring  
- **Week 4**: ✅ CLI integration and testing

## ✅ MIGRATION COMPLETE!

The organized system is now **fully functional**:

### ✅ Working Commands (Organized System)

```bash
# List available enemies
python main.py list

# Generate animated enemies  
python main.py animated adhesion_bug 1
python main.py animated tar_slug 2
python main.py animated ember_imp 3

# Quick test
python main.py test
```

### ✅ Working Commands (Legacy System)

```bash 
# All legacy functionality still works
./enemy.sh list
./enemy.sh animated adhesion_bug 1
./enemy.sh view adhesion_bug_animated_00 --anim move
./enemy.sh static glue_drone 3
```

### 🏗️ Architecture Successfully Extracted

- **src/core/** - Blender utilities (`create_sphere`, `join_objects`, etc.)
- **src/materials/** - Complete material system with 22+ materials
- **src/animations/** - Animation system (`create_all_animations`, `create_simple_armature`, body types)  
- **src/enemies/** - Enemy classes (`AnimatedAdhesionBug`, `AnimatedTarSlug`, `AnimatedEmberImp`)
- **src/generator.py** - Integrated generator using organized modules

## No Disruption Promise

- Legacy `enemy.sh` script will continue to work
- No functionality will be lost during migration
- All existing generated enemies remain compatible
- Documentation will be updated throughout the process
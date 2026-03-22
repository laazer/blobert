#!/usr/bin/env python3
"""
Animation Viewer for Generated Enemies
Loads GLB files and automatically plays specific animations
"""

import bpy
import sys
import os

def clear_scene():
    """Clear the default scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def load_glb_and_play_animation(glb_path, animation_name='idle'):
    """Load GLB file and play specified animation"""
    print(f"Loading GLB file: {glb_path}")
    print(f"Target animation: {animation_name}")
    
    # Clear the scene
    clear_scene()
    
    # Import GLB
    bpy.ops.import_scene.gltf(filepath=glb_path)
    
    # Find the armature (animated object)
    armature = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break
    
    if not armature:
        print("❌ No armature found in GLB file")
        return False
    
    print(f"Found armature: {armature.name}")
    
    # Select and make active
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    
    # Check available animations
    if not armature.animation_data:
        print("❌ No animation data found")
        return False
    
    available_actions = [action.name for action in bpy.data.actions]
    print(f"Available animations: {available_actions}")
    
    # Find and play the requested animation
    target_action = None
    for action in bpy.data.actions:
        if action.name == animation_name:
            target_action = action
            break
    
    if not target_action:
        print(f"❌ Animation '{animation_name}' not found")
        print(f"Available animations: {', '.join(available_actions)}")
        # Fall back to first available animation
        if available_actions:
            target_action = bpy.data.actions[available_actions[0]]
            print(f"Playing fallback animation: {target_action.name}")
    
    if target_action:
        # Set the action
        armature.animation_data.action = target_action
        
        # Set frame range
        bpy.context.scene.frame_start = int(target_action.frame_range[0])
        bpy.context.scene.frame_end = int(target_action.frame_range[1])
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        
        # Start playing
        bpy.ops.screen.animation_play()
        
        # Set viewport to show the object nicely
        try:
            # Try modern Blender API
            with bpy.context.temp_override(active_object=armature):
                bpy.ops.view3d.view_selected()
        except:
            # Fallback for older Blender versions
            try:
                bpy.ops.view3d.view_selected()
            except:
                print("Could not frame object in view, but animation should still play")
        
        print(f"✅ Playing animation: {target_action.name}")
        return True
    
    print("❌ No animation could be played")
    return False

def main():
    """Main function called from Blender"""
    # Get command line arguments
    argv = sys.argv
    
    # Find the -- separator
    try:
        index = argv.index("--") + 1
    except ValueError:
        print("❌ Usage: blender --background --python animation_viewer.py -- <glb_path> <animation_name>")
        return
    
    if len(argv) <= index + 1:
        print("❌ Missing arguments: GLB path and animation name required")
        return
    
    glb_path = argv[index]
    animation_name = argv[index + 1] if len(argv) > index + 1 else 'idle'
    
    # Check if file exists
    if not os.path.exists(glb_path):
        print(f"❌ GLB file not found: {glb_path}")
        return
    
    # Load and play animation
    success = load_glb_and_play_animation(glb_path, animation_name)
    
    if success:
        print("🎬 Animation viewer ready! Press SPACE to start/stop animation.")
        print("Available controls:")
        print("  - SPACE: Play/Pause animation")
        print("  - LEFT/RIGHT ARROW: Scrub timeline")
        print("  - SCROLL WHEEL: Zoom camera")
        print("  - MIDDLE MOUSE: Rotate view")
    else:
        print("❌ Failed to load animation")

if __name__ == "__main__":
    main()
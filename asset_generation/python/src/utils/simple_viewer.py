#!/usr/bin/env python3
"""
Simple Animation Viewer
Loads GLB and plays animation in a user-friendly way
"""

import os
import sys

import bpy


def main():
    # Get arguments
    argv = sys.argv
    try:
        index = argv.index("--") + 1
        glb_path = argv[index]
        animation_name = argv[index + 1] if len(argv) > index + 1 else 'idle'
    except (ValueError, IndexError):
        print("Usage: blender --python simple_viewer.py -- <glb_path> <animation_name>")
        return

    if not os.path.exists(glb_path):
        print(f"❌ GLB file not found: {glb_path}")
        return

    print(f"🎬 Loading: {os.path.basename(glb_path)}")
    print(f"🎯 Animation: {animation_name}")
    
    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Import GLB
    try:
        bpy.ops.import_scene.gltf(filepath=glb_path)
        print("✅ GLB loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load GLB: {e}")
        return
    
    # Find armature
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
    
    if not armatures:
        print("❌ No armature found - this might be a static model")
        return
    
    armature = armatures[0]
    print(f"🦴 Found armature: {armature.name}")
    
    # Make armature active
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    
    # List available animations
    if armature.animation_data and bpy.data.actions:
        actions = [action.name for action in bpy.data.actions if action.users > 0]
        print(f"🎭 Available animations: {', '.join(actions)}")
        
        # Find requested animation
        target_action = None
        for action in bpy.data.actions:
            if action.name == animation_name and action.users > 0:
                target_action = action
                break
        
        if not target_action and actions:
            # Use first available if requested not found
            target_action = bpy.data.actions[actions[0]]
            print(f"⚠️  '{animation_name}' not found, using '{target_action.name}'")
        
        if target_action:
            # Apply animation
            armature.animation_data.action = target_action
            
            # Set timeline
            frame_start = max(1, int(target_action.frame_range[0]))
            frame_end = int(target_action.frame_range[1])
            
            bpy.context.scene.frame_start = frame_start
            bpy.context.scene.frame_end = frame_end
            bpy.context.scene.frame_current = frame_start
            
            print(f"⏰ Timeline: {frame_start} - {frame_end}")
            print(f"▶️  Playing: {target_action.name}")
            
            # Start animation
            bpy.ops.screen.animation_play()
        else:
            print("❌ No valid animation found")
    else:
        print("❌ No animation data found in this file")
    
    # Center view on objects and zoom appropriately
    try:
        # Select all objects to frame them properly
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.view3d.view_selected()
        
        # Zoom out a bit to see animation movement
        bpy.ops.view3d.zoom(delta=-2)
        print("📷 View centered and zoomed for animation")
    except Exception as e:
        print(f"View adjustment failed: {e}")
        
    # Make sure we're in solid shading mode for better visibility
    try:
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'SOLID'
                        break
        print("🎨 Set solid shading for better visibility")
    except:
        pass
    
    print("\n🎮 Controls:")
    print("   SPACEBAR - Play/Pause animation")
    print("   ← → - Step through frames") 
    print("   Mouse Wheel - Zoom")
    print("   Middle Mouse - Orbit view")

if __name__ == "__main__":
    main()
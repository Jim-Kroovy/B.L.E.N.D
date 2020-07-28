import bpy
#from bpy.props import (StringProperty, BoolProperty)
#from . import _functions_, _properties_

class JK_OT_Apply_Posing(bpy.types.Operator):
    """Applies armature pose to rest with meshes. (Will apply pose to rest on ALL armature bones)"""
    bl_idname = "jk.apply_mesh_posing"
    bl_label = "Apply Mesh Pose"
    
    def execute(self, context):
        armature = bpy.context.object
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        # iterate through all objects...
        for obj in bpy.data.objects:
            # if it's a mesh...
            if obj.type == 'MESH':
                # iterate through it's modifiers...
                for modifier in obj.modifiers:
                    # if it's an armature modifier targeting the retarget target...
                    if modifier.type == 'ARMATURE' and modifier.object == armature:
                        mod_name = modifier.name
                        # apply and re-add armature modifiers...
                        bpy.context.view_layer.objects.active = obj
                        bpy.ops.object.modifier_apply(modifier=mod_name)
                        modifier = obj.modifiers.new(type='ARMATURE', name=mod_name)
                        modifier.object = armature              
        bpy.ops.object.select_all(action='DESELECT')
        # make the armature active again...
        bpy.context.view_layer.objects.active = armature
        # go into pose mode...
        bpy.ops.object.mode_set(mode='POSE')
        # apply the pose...
        bpy.ops.pose.armature_apply(selected=False)
        return {'FINISHED'}

    
import bpy
from bpy.props import (StringProperty, BoolProperty, PointerProperty, IntProperty)
from . import _functions_

class JK_OT_Apply_Posing(bpy.types.Operator):
    """Applies armature pose to rest with meshes. (Will apply pose to rest on ALL armature bones)"""
    bl_idname = "jk.apply_mesh_posing"
    bl_label = "Apply Mesh Pose"
    bl_options = {'REGISTER', 'UNDO'}

    Orient_rot: BoolProperty(name="Orient Rotation", description="Orient edit bone rotations to their targets", default=False)
    
    Orient_sca: BoolProperty(name="Orient Scale", description="Orient edit bone scales to their targets", default=False)

    Rename: BoolProperty(name="Rename Bones", description="Rename edit bones to their targets", default=False)
    
    Keep_original: BoolProperty(name="Keep Original", description="Keep original armature and meshes instead of replaceing them",
        default=False, options=set())
    
    def execute(self, context):
        armature = bpy.context.view_layer.objects.active
        _functions_.Apply_Mesh_Posing(armature)
        if 'BLEND-ArmatureActiveRetargeting' in bpy.context.preferences.addons.keys():        
            AAR = armature.data.AAR
            if self.Orient_rot or self.Orient_sca:
                _functions_.Orient_Bones(armature, AAR, self.Orient_rot, self.Orient_sca)
            if self.Rename:
                for pb in AAR.Pose_bones:
                    p_bone = armature.pose.bones[pb.name]
                    name = pb.Target
                    pb.Target = ""
                    p_bone.bone.name = name
            AAR.Target = None
        return {'FINISHED'}

    def invoke(self, context, event):
        armature = bpy.context.view_layer.objects.active
        self.Orient_rot = False
        self.Orient_sca = False
        if 'BLEND-ArmatureActiveRetargeting' in bpy.context.preferences.addons.keys() and armature.data.AAR.Target != None:
            wm = bpy.context.window_manager
            return wm.invoke_props_dialog(self)
        else:
            return self.execute(bpy.context)

    def draw(self, context):
        armature = bpy.context.object
        layout = self.layout
        if armature.data.AAR.Target != None:
            row = layout.row()
            row.prop(self, "Orient_rot")
            row = layout.row()
            row.prop(self, "Orient_sca")
            row = layout.row()
            row.prop(self, "Rename")

    
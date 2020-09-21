import bpy
from bpy.props import (StringProperty, BoolProperty, PointerProperty, IntProperty)
from . import _functions_

class JK_OT_Apply_Posing(bpy.types.Operator):
    """Applies armature pose to rest with meshes. (Will apply pose on ALL armature bones)"""
    bl_idname = "jk.apply_mesh_posing"
    bl_label = "Apply Mesh Pose"
    bl_options = {'REGISTER', 'UNDO'}

    Orient_rot: BoolProperty(name="Orient Bone Rotations", description="Orient edit bone rotations to their targets", default=False)
    
    Orient_sca: BoolProperty(name="Orient Bone Scales", description="Orient edit bone scales to their targets", default=False)

    Orient_source: BoolProperty(name="Use Source Bones", description="Orient edit bones to source bones instead of control bones. (If target uses 'Armature Control Bones')", default=False)

    Rename: BoolProperty(name="Rename Bones", description="Rename edit bones to their targets", default=False)
    
    Keep_original: BoolProperty(name="Keep Original", description="Keep original meshes instead of replacing them",
        default=False, options=set())

    def execute(self, context):
        armature = bpy.context.view_layer.objects.active
        _functions_.Apply_Mesh_Posing(armature, self.Keep_original)
        if 'BLEND-ArmatureActiveRetargeting' in bpy.context.preferences.addons.keys():        
            AAR = armature.data.AAR
            if self.Orient_rot or self.Orient_sca:
                _functions_.Orient_Bones(armature, AAR, self.Orient_rot, self.Orient_sca, self.Orient_source)
            if self.Rename:
                for pb in AAR.Pose_bones:
                    p_bone = armature.pose.bones[pb.name]
                    name = pb.Target
                    pb.Target = ""
                    p_bone.bone.name = name
            AAR.Target = None
        return {'FINISHED'}

    def invoke(self, context, event):
        self.Orient_rot = False
        self.Orient_sca = False
        self.Orient_source = False
        wm = bpy.context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        addons = bpy.context.preferences.addons.keys()
        armature = bpy.context.object
        layout = self.layout
        if 'BLEND-ArmatureActiveRetargeting' in addons and armature.data.AAR.Target != None:
            target = armature.data.AAR.Target
            
            row = layout.row()
            row.prop(self, "Orient_rot")
            row.prop(self, "Orient_sca")
            row = layout.row()
            row.prop(self, "Rename")
            col = row.column()
            col.prop(self, "Orient_source")
            col.enabled = True if 'BLEND-ArmatureControlBones' in addons and any(b.ACB.Type != 'NONE' for b in target.data.bones) else False
        layout.prop(self, "Keep_original")

    
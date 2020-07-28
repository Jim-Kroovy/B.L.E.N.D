import bpy

class JK_PT_ACB_Armature_Panel(bpy.types.Panel):
    bl_label = "Bone Controls"
    bl_idname = "JK_PT_AES_Armature_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE' and context.object.data.ACB.Has_controls

    def draw(self, context):
        layout = self.layout
        armature = bpy.context.object
        #prefs = bpy.context.preferences.addons["BLEND-AddControlBones"].preferences
        ACB = armature.data.ACB
        bone = bpy.context.active_bone
        from_bones = ACB.Edit_bones if armature.mode == 'EDIT' else ACB.Bones
        bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
        if bone != None and bone.name in bones:
            name = from_bones[bone.name].Bone_name
            row = layout.row()
            row.prop(bones[name], "name")
        row = layout.row()
        row.prop(ACB, "Con_prefix")
        row = layout.row()
        row.prop(ACB, "Mech_prefix")
        row = layout.row()
        row.prop(ACB, "Mech_show")
        row.prop(ACB, "Mech_select")
        row = layout.row()
        row.operator("jk.edit_control_bones")
       
        
        

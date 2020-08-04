import bpy

#class JK_MMT_Addon_Prefs(bpy.types.AddonPreferences):
    #bl_idname = "BLEND-ArmatureEditingStages"

    #Affixes: PointerProperty(type=_properties_.JK_ARL_Rigging_Affix_Props)

    #def draw(self, context):

class JK_PT_ARL_Armature_Panel(bpy.types.Panel):
    bl_label = "Rigging Library"
    bl_idname = "JK_PT_ARL_Armature_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE'

    def draw(self, context):
        armature = bpy.context.object
        layout = self.layout
        if armature.mode == 'POSE':
            bone = bpy.context.active_pose_bone
        else:
            bone = bpy.context.active_bone
        layout.operator("jk.add_twist")
        layout.operator("jk.add_chain")
        #is_rigged, rigging, rigging_type = _functions_.Get_Is_Bone_Rigged(bone.name)
        #if is_rigged:

#class JK_PT_ARL_Bone_Panel(bpy.types.Panel):
    #bl_label = "Stage Push Settings"
    #bl_idname = "JK_PT_ARL_Bone_Panel"
    #bl_space_type = 'PROPERTIES'
    #bl_region_type = 'WINDOW'
    #bl_context = "bone"

    #def draw(self, context):   
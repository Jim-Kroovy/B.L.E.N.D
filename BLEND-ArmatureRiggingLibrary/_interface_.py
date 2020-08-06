import bpy

#class JK_MMT_Addon_Prefs(bpy.types.AddonPreferences):
    #bl_idname = "BLEND-ArmatureEditingStages"

    #Affixes: PointerProperty(type=_properties_.JK_ARL_Rigging_Affix_Props)

    #def draw(self, context):

class JK_UL_Action_List(bpy.types.UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        slot = item
        action = slot.Action
        # draw_item must handle the three layout types... Usually 'DEFAULT' and 'COMPACT' can share the same code.
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.label(text="" if slot.Action else " ", icon='ACTION')
            if slot.Action:
                row.prop(action, "name", text="", emboss=False)
            row.prop(slot, "Use", text="", emboss=False, icon='HIDE_OFF' if slot.Use else 'HIDE_ON')
        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

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
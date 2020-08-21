import bpy

class JK_ACB_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = "BLEND-ArmatureControlBones"

    Con_prefix: bpy.props.StringProperty(name="Control Prefix", description="The prefix for control bone names", 
        default="CB_", maxlen=1024)#, update=Update_Con_Prefix)
    
    Mech_prefix: bpy.props.StringProperty(name="Mechanism Prefix", description="The prefix for mechanism bone names", 
        default="MB_", maxlen=1024)#, update=Update_Mech_Prefix)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "Con_prefix", text="")
        row.prop(self, "Mech_prefix", text="")
        row = layout.row()

class JK_PT_ACB_Armature_Panel(bpy.types.Panel):
    bl_label = "Controls"
    bl_idname = "JK_PT_ACB_Armature_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        if (context.object.type == 'MESH' and context.object.mode == 'WEIGHT_PAINT'):
            if any(mod.type == 'ARMATURE' for mod in context.object.modifiers):
                is_valid = True
            else:
                is_valid = False
        elif context.object.type == 'ARMATURE':
            is_valid = True
        else:
            is_valid = False
        return is_valid

    def draw(self, context):
        layout = self.layout
        if context.object.type == 'MESH':
            armatures = {mod.object : mod.object.data.ACB for mod in context.object.modifiers if mod.type == 'ARMATURE'}
            for armature, ACB in armatures.items():
                box = layout.box()
                box.label(text=armature.name)
                row = layout.row()
                row.prop(ACB, "Auto_hide")
                row = layout.row(align=True)
                row.prop(ACB, "Hide_source", invert_checkbox=True)
                row.prop(ACB, "Hide_mech", invert_checkbox=True)
                row.prop(ACB, "Hide_con", invert_checkbox=True)
                row.enabled = True if any(b.ACB.Type != 'NONE' for b in armature.data.bones) and not ACB.Auto_hide else False
        else:
            bone = bpy.context.object.data.bones.active
            armature = bpy.context.object
            ACB = armature.data.ACB
            row = layout.row()
            col = row.column()
            col.operator("jk.edit_control_bones", text="Add", icon='GROUP_BONE').Is_adding = True
            col.enabled = True if bone.ACB.Type == 'NONE' else False
            col = row.column()
            col.operator("jk.edit_control_bones", text="Edit", icon='TOOL_SETTINGS').Is_adding = False
            col.enabled = True if bone.ACB.Type != 'NONE' else False
            row = layout.row(align=True)
            row.prop(ACB, "Auto_hide", icon='VIS_SEL_11' if ACB.Auto_hide else 'VIS_SEL_00')
            row.prop(ACB, "Auto_sync", icon='SNAP_ON' if ACB.Auto_sync else 'SNAP_OFF')
            row = layout.row(align=True)
            row.prop(ACB, "Hide_source", text="Sources", icon='HIDE_ON' if ACB.Hide_source else 'HIDE_OFF', invert_checkbox=True)
            row.prop(ACB, "Hide_mech", text="Mechanisms", icon='HIDE_ON' if ACB.Hide_mech else 'HIDE_OFF', invert_checkbox=True)
            row.prop(ACB, "Hide_con", text="Controls", icon='HIDE_ON' if ACB.Hide_con else 'HIDE_OFF', invert_checkbox=True)
            row.enabled = True if any(b.ACB.Type != 'NONE' for b in armature.data.bones) and not ACB.Auto_hide else False
       
        
        

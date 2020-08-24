import bpy
from . import _functions_, _properties_

class JK_ACB_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = "BLEND-ArmatureControlBones"

    def Update_Prefixes(self, context):
        for armature in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
            if any(b.ACB.Type != 'NONE' for b in armature.data.bones):
                controls = _functions_.Get_Control_Bones(armature)
                bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
                for sb_name, cb_names in controls.items():
                    mb, cb = bones[cb_names['MECH']], bones[cb_names['CONT']]
                    mb.name = self.Mech_prefix + sb_name
                    cb.name = self.Cont_prefix + sb_name
    
    Cont_prefix: bpy.props.StringProperty(name="Control Prefix", description="The prefix for control bone names", 
        default="CB_", maxlen=1024, update=Update_Prefixes)
    
    Mech_prefix: bpy.props.StringProperty(name="Mechanism Prefix", description="The prefix for mechanism bone names", 
        default="MB_", maxlen=1024, update=Update_Prefixes)

    Meshes: bpy.props.CollectionProperty(type=_properties_.JK_ACB_Mesh_Props)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "Cont_prefix")
        row = layout.row()
        row.prop(self, "Mech_prefix")

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
                row = box.row(align=True)
                row.prop(ACB, "Auto_hide", icon='VIS_SEL_11' if ACB.Auto_hide else 'VIS_SEL_00')
                row.prop(ACB, "Auto_sync", icon='SNAP_ON' if ACB.Auto_sync else 'SNAP_OFF')
                row = box.row(align=True)
                row.prop(ACB, "Hide_source", text="Sources", icon='HIDE_ON' if ACB.Hide_source else 'HIDE_OFF', invert_checkbox=True)
                row.prop(ACB, "Hide_mech", text="Mechanisms", icon='HIDE_ON' if ACB.Hide_mech else 'HIDE_OFF', invert_checkbox=True)
                row.prop(ACB, "Hide_cont", text="Controls", icon='HIDE_ON' if ACB.Hide_cont else 'HIDE_OFF', invert_checkbox=True)
                row.enabled = True if any(b.ACB.Type != 'NONE' for b in armature.data.bones) and not ACB.Auto_hide else False
        else:
            armature = bpy.context.object
            ACB = armature.data.ACB
            row = layout.row()
            col = row.column()
            col.operator("jk.edit_control_bones", text="Add", icon='GROUP_BONE').Is_adding = True
            col.enabled = True if any(b.ACB.Type == 'NONE' for b in armature.data.bones) else False
            col = row.column()
            col.operator("jk.edit_control_bones", text="Edit", icon='TOOL_SETTINGS').Is_adding = False
            col.enabled = True if any(b.ACB.Type != 'NONE' for b in armature.data.bones) else False
            row = layout.row(align=True)
            row.prop(ACB, "Auto_hide", icon='VIS_SEL_11' if ACB.Auto_hide else 'VIS_SEL_00')
            row.prop(ACB, "Auto_sync", icon='SNAP_ON' if ACB.Auto_sync else 'SNAP_OFF')
            row = layout.row(align=True)
            row.prop(ACB, "Hide_source", text="Sources", icon='HIDE_ON' if ACB.Hide_source else 'HIDE_OFF', invert_checkbox=True)
            row.prop(ACB, "Hide_mech", text="Mechanisms", icon='HIDE_ON' if ACB.Hide_mech else 'HIDE_OFF', invert_checkbox=True)
            row.prop(ACB, "Hide_cont", text="Controls", icon='HIDE_ON' if ACB.Hide_cont else 'HIDE_OFF', invert_checkbox=True)
            row.enabled = True if any(b.ACB.Type != 'NONE' for b in armature.data.bones) and not ACB.Auto_hide else False
       
        
        

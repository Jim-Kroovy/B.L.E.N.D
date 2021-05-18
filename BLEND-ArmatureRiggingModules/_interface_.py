import bpy
import os
from . import (_properties_, _functions_)
from .library.chains import (_opposable_, _plantigrade_)
from bl_ui.properties_constraint import ConstraintButtonsPanel

class JK_ARM_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = "BLEND-ArmatureRiggingModules"

    disable_dependencies: bpy.props.BoolProperty(name="Disable Dependencies", description="Disables any add-ons that Mr Mannequins depends on",
        default=True)

    affixes: bpy.props.PointerProperty(type=_properties_.JK_PG_ARM_Affixes)

    auto_freq: bpy.props.FloatProperty(name="Auto Switch Frequency", description="How often we check selection for automatic IK vs FK switching. (in seconds)",
        default=0.5, min=0.25, max=1.0)

    shape_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources\\bone_shapes_default.blend")

    group_colours = {
        "Chain Bones" : 'THEME03', "Twist Bones" : 'THEME07',
        "Kinematic Targets" : 'THEME01', "Floor Targets" : 'THEME04',
        "Control Bones" : 'THEME09', "Offset Bones" : 'THEME08',
        "Gizmo Bones" : 'THEME05', "Mechanic Bones" : 'THEME06'}

    group_layers = {
        "Chain Bones" : [True] + [False] * 31, "Twist Bones" : [False] * 16 + [True] + [False] * 15,
        "Kinematic Targets" : [False] * 1 + [True] + [False] * 30, "Floor Targets" : [False] * 17 + [True] + [False] * 14,
        "Control Bones" : [False] * 2 + [True] + [False] * 29, "Offset Bones" : [False] * 18 + [True] + [False] * 13,
        "Gizmo Bones" : [False] * 3 + [True] + [False] * 28, "Mechanic Bones" : [False] * 19 + [True] + [False] * 12}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, 'auto_freq')
        props = {'Prefixes' : ['control', 'gizmo', 'offset', 'target'],
            'Affixes' : ['stretch', 'roll', 'local']}
        for title, props in props.items():
            col = layout.column()
            box = col.box()
            box.label(text=title)
            for prop in props:
                row = box.row()
                row.prop(self.affixes, prop)

class JK_UL_ARM_Rigging_List(bpy.types.UIList):

    #icons = [
        #'DECORATE_LINKED', 'DECORATE_LIBRARY_OVERRIDE',
        #'SNAP_ON', 'SNAP_OFF',
        #'LOCKED', 'UNLOCKED',
        #'PINNED', 'UNPINNED',
        #'CON_CLAMPTO', 'CON_FOLLOWPATH']

    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        slot = item
        # draw_item must handle the three layout types... Usually 'DEFAULT' and 'COMPACT' can share the same code.
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            if slot.flavour != 'NONE':
                label_text = slot.name #pointers[slot.flavour].name
                if slot.flavour in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE', 'SPLINE', 'SCALAR', 'FORWARD', 'TRACKING']:
                    label_icon = 'CON_KINEMATIC' if slot.flavour in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE', 'SCALAR'] else 'CON_SPLINEIK' if slot.flavour == 'SPLINE' else 'CON_TRANSLIKE'
                    
                elif slot.flavour in ['HEAD_HOLD', 'TAIL_FOLLOW']:
                    label_icon = 'TRACKING_BACKWARDS' if slot.flavour == 'HEAD_HOLD' else 'TRACKING_FORWARDS'
            else:
                label_icon = 'ERROR'
                label_text = "Please select a rigging type..."
            
            row.label(text=label_text, icon=label_icon)
            if slot.flavour in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE']:
                chain = slot.get_pointer()
                row.prop(chain, "use_auto_fk", text="", icon='LOCKED' if chain.use_auto_fk else 'UNLOCKED')
                col = row.column(align=True)
                col.prop(chain, "use_fk", text="", icon='CON_CLAMPTO' if chain.use_fk else 'CON_FOLLOWPATH')
                col.enabled = not chain.use_auto_fk

        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class JK_PT_ARM_Armature_Panel(bpy.types.Panel):
    bl_label = "Rigging Modules"
    bl_idname = "JK_PT_ARM_Armature_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE'
 
    def draw(self, context):
        #armature = bpy.context.object
        #ARL = armature.data.ARL
        #layout = self.layout
        #row = layout.row(align=True)
        #col = row.column(align=True)
        #col.prop(ARL, "Hide_chain", text="Chains", icon='HIDE_ON' if ARL.Hide_chain else 'HIDE_OFF', invert_checkbox=True)
        #col.prop(ARL, "Hide_target", text="Targets", icon='HIDE_ON' if ARL.Hide_target else 'HIDE_OFF', invert_checkbox=True)
        #col = row.column(align=True)
        #col.prop(ARL, "Hide_pivot", text="Pivots", icon='HIDE_ON' if ARL.Hide_pivot else 'HIDE_OFF', invert_checkbox=True)
        #col.prop(ARL, "Hide_twist", text="Twists", icon='HIDE_ON' if ARL.Hide_twist else 'HIDE_OFF', invert_checkbox=True)
        #col = row.column(align=True)
        #col.prop(ARL, "Hide_gizmo", text="Gizmos", icon='HIDE_ON' if ARL.Hide_gizmo else 'HIDE_OFF', invert_checkbox=True)
        #col.prop(ARL, "Hide_none", text="Unrigged", icon='HIDE_ON' if ARL.Hide_none else 'HIDE_OFF', invert_checkbox=True)
        #row = layout.row(align=True)
        #row.prop(ARL, "Wire_shapes", icon='SHADING_WIRE' if ARL.Wire_shapes else 'SHADING_SOLID')
        armature = bpy.context.object
        jk_arm = armature.jk_arm
        #bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.template_list("JK_UL_ARM_Rigging_List", "Rigging", armature.jk_arm, "rigging", armature.jk_arm, "active")
        col = row.column(align=True)
        add_op = col.operator("jk.arl_set_rigging", text="", icon='ADD')
        add_op.index, add_op.action = len(jk_arm.rigging), 'ADD'
        rem_op = col.operator("jk.arl_set_rigging", text="", icon='REMOVE')
        rem_op.index, rem_op.action = jk_arm.active, 'REMOVE'

class JK_PT_ARM_Edit_Panel(bpy.types.Panel):
    bl_label = "Settings"
    bl_idname = "JK_PT_ARM_Edit_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "JK_PT_ARM_Armature_Panel"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE' and context.object.jk_arm.rigging
 
    def draw(self, context):
        armature = bpy.context.object
        layout = self.layout
        if len(armature.jk_arm.rigging) > 0:
            rigging = armature.jk_arm.rigging[armature.jk_arm.active]
            if rigging.flavour in ['HEAD_HOLD', 'TAIL_FOLLOW']:
                _functions_.show_twist_settings(layout, rigging, armature)
            elif rigging.flavour != 'NONE':
                _functions_.show_chain_settings(layout, rigging, armature)
            else:
                box = layout.box()
                box.prop(rigging, "flavour")

class JK_PT_ARM_Pose_Panel(bpy.types.Panel):
    bl_label = "Controls"
    bl_idname = "JK_PT_ARM_Pose_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "JK_PT_ARM_Armature_Panel"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE' and context.object.jk_arm.rigging
    
    def draw(self, context):
        armature = bpy.context.object
        layout = self.layout
        if len(armature.jk_arm.rigging) > 0:
            rigging = armature.jk_arm.rigging[armature.jk_arm.active]
            if rigging.flavour in ['HEAD_HOLD', 'TAIL_FOLLOW']:
                _functions_.show_twist_controls(layout, rigging, armature)
            elif rigging.flavour != 'NONE':
                _functions_.show_chain_controls(layout, rigging, armature)
            else:
                box = layout.box()
                box.label(text="Pose controls appear here when rigged...")
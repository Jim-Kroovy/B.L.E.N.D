import bpy
import os
from . import (_properties_, _functions_)

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
            col = layout.column()
            col.ui_units_x = 25
            row = col.row()
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
            
            col = layout.column()
            col.ui_units_x = 25
            row = col.row(align=True)
            if slot.flavour in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE']:
                chain = slot.get_pointer()
                row.prop(chain, "ik_softness")
                col = row.column(align=True)
                col.prop(chain, "fk_influence")
                col.enabled = not chain.use_fk
                row.prop(chain, "use_auto_fk", text="", icon='AUTOMERGE_ON' if chain.use_auto_fk else 'AUTOMERGE_OFF')
                col = row.column(align=True)
                col.prop(chain, "use_fk", text="", icon='CON_CLAMPTO' if chain.use_fk else 'CON_FOLLOWPATH')
                col.enabled = not chain.use_auto_fk
            
            elif slot.flavour == 'TRACKING':
                chain = slot.get_pointer()
                row.prop(chain.target, "lock_x")
                row.prop(chain.target, "lock_z")

            elif slot.flavour == 'SPLINE':
                chain = slot.get_pointer()
                row.prop(chain, "fit_curve")

            elif slot.flavour == 'SCALAR':
                chain = slot.get_pointer()
                row.prop(chain, "ik_softness")

            elif slot.flavour == 'HEAD_HOLD':
                twist = slot.get_pointer()
                pbs = slot.id_data.pose.bones
                pb = pbs.get(twist.bone.source)
                if pb:
                    damp_track, limit_rot = pb.constraints.get("TWIST - Damped Track"), pb.constraints.get("TWIST - Limit Rotation")
                    if limit_rot:
                        row.prop(limit_rot, "influence")
                    if damp_track:
                        row.prop(damp_track, "head_tail")
            
            elif slot.flavour == 'TAIL_FOLLOW':
                twist = slot.get_pointer()
                pbs = slot.id_data.pose.bones
                pb = pbs.get(twist.bone.source)
                if pb:
                    ik = pb.constraints.get("TWIST - IK")
                    if ik:
                        row.prop(ik, "influence")

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
        ob = context.object
        return True if ob and ob.type == 'ARMATURE' else False
 
    def draw(self, context):
        armature = bpy.context.object
        jk_arm = armature.jk_arm
        layout = self.layout
        

        row = layout.row()
        row.template_list("JK_UL_ARM_Rigging_List", "Rigging", armature.jk_arm, "rigging", armature.jk_arm, "active")
        col = row.column(align=True)
        add_op = col.operator("jk.arl_set_rigging", text="", icon='ADD')
        add_op.index, add_op.action = len(jk_arm.rigging), 'ADD'
        rem_op = col.operator("jk.arl_set_rigging", text="", icon='REMOVE')
        rem_op.index, rem_op.action = jk_arm.active, 'REMOVE'
        col.separator()
        row = col.row(align=True)
        ref_op = row.operator("jk.arl_set_rigging", text="", icon='FILE_REFRESH')
        ref_op.index, ref_op.action = jk_arm.active, 'UPDATE'
        row.active = True if armature.mode == 'POSE' and not armature.jk_arm.use_edit_detection else False
        col.prop(armature.jk_arm, "use_edit_detection", text="", icon='AUTO')

        
        if len(armature.jk_arm.rigging) > 0:
            rigging = armature.jk_arm.rigging[armature.jk_arm.active]
            row = layout.row(align=True)
            col = row.column()
            col.prop(rigging, "flavour", text="")
            col.ui_units_x = 5
            col = row.column()
            col.prop(rigging, "name", text="")
            col.enabled = False
            if rigging.flavour != 'NONE':
                pointer = rigging.get_pointer()
                row.prop(pointer, "use_default_shapes", text="", icon='OBJECT_DATAMODE' if pointer.use_default_shapes else 'OBJECT_HIDDEN')
                row.prop(pointer, "use_default_groups", text="", icon='COLOR' if pointer.use_default_groups else 'MOD_TINT')
                row.prop(pointer, "use_default_layers", text="", icon='PROP_ON' if pointer.use_default_layers else 'PROP_OFF')
                row.separator()
                col = row.column()    
                col.prop(rigging, "side", text="")
                col.ui_units_x = 3

        col = layout.column(align=True)
        row = col.row(heading="Hide", align=True)
        row.prop(jk_arm.chain_bones, "edit_hide" if armature.mode == 'EDIT' else "pose_hide", text="Chains")
        row.prop(jk_arm.kinematic_targets, "edit_hide" if armature.mode == 'EDIT' else "pose_hide", text="Targets")
        row.prop(jk_arm.control_bones, "edit_hide" if armature.mode == 'EDIT' else "pose_hide", text="Controls")
        row.prop(jk_arm.gizmo_bones, "edit_hide" if armature.mode == 'EDIT' else "pose_hide", text="Gizmos")
        
        row = col.row(heading=" ", align=True)
        row.prop(jk_arm.twist_bones, "edit_hide" if armature.mode == 'EDIT' else "pose_hide", text="Twists")
        row.prop(jk_arm.floor_targets, "edit_hide" if armature.mode == 'EDIT' else "pose_hide", text="Floors")
        row.prop(jk_arm.offset_bones, "edit_hide" if armature.mode == 'EDIT' else "pose_hide", text="Offsets")
        row.prop(jk_arm.mechanic_bones, "edit_hide" if armature.mode == 'EDIT' else "pose_hide", text="Mechanics")


class JK_PT_ARM_Edit_Panel(bpy.types.Panel):
    bl_label = "Settings"
    bl_idname = "JK_PT_ARM_Edit_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "JK_PT_ARM_Armature_Panel"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob and ob.type == 'ARMATURE' and ob.jk_arm.rigging:
            active = ob.jk_arm.rigging[ob.jk_arm.active]
            if active.flavour != 'NONE':
                return True
            else:
                return False
        else:
            return False
 
    def draw(self, context):
        armature = bpy.context.object
        layout = self.layout
        if armature.jk_arm.rigging:
            rigging = armature.jk_arm.rigging[armature.jk_arm.active]
            if rigging.flavour in ['HEAD_HOLD', 'TAIL_FOLLOW']:
                _functions_.show_twist_settings(layout, rigging, armature)
            elif rigging.flavour != 'NONE':
                _functions_.show_chain_settings(layout, rigging, armature)

class JK_PT_ARM_Pose_Panel(bpy.types.Panel):
    bl_label = "Controls"
    bl_idname = "JK_PT_ARM_Pose_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "JK_PT_ARM_Armature_Panel"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob and ob.type == 'ARMATURE' and ob.jk_arm.rigging:
            active = ob.jk_arm.rigging[ob.jk_arm.active]
            if active.flavour != 'NONE':
                pointer = active.get_pointer()
                return pointer.is_rigged
            else:
                return False
        else:
            return False
            
        #return context.object.type == 'ARMATURE' and context.object.jk_arm.rigging and context.object.jk_arm.rigging[]
    
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
                layout.label(text="Animation controls appear here when rigged...")
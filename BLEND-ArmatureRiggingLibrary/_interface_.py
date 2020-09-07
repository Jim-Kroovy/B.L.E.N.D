import bpy
from . import _properties_
from bl_ui.properties_constraint import ConstraintButtonsPanel

class JK_ARL_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = "BLEND-ArmatureRiggingLibrary"

    Affixes: bpy.props.PointerProperty(type=_properties_.JK_ARL_Affix_Props)

    Auto_freq: bpy.props.FloatProperty(name="Auto Switch Frequency", description="How often we check selection for automatic IK vs FK switching. (in seconds)",
        default=0.5, min=0.25, max=1.0)

    Custom_shapes: bpy.props.BoolProperty(name="Use Default Shapes", description="Use some derpy custom shapes i coded for different bone types",
        default=True)
    
    def draw(self, context):
        addons = bpy.context.preferences.addons.keys()
        layout = self.layout
        row = layout.row()
        row.prop(self, 'Custom_shapes')
        row.prop(self, 'Auto_freq')
        props = {'General Prefixes' : ['Control', 'Gizmo', 'Pivot'],
            'Affixes' : ['Stretch', 'Roll', 'Local'],
            'Target Prefixes' : ['Target_arm', 'Target_digit', 'Target_leg', 'Target_spine', 'Target_tail', 'Target_wing', 'Target_floor']}
        for title, props in props.items():
            col = layout.column()
            box = col.box()
            box.label(text=title)
            for prop in props:
                row = box.row()
                if prop == 'Control' and 'BLEND-ArmatureControlBones' in addons:
                    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
                    row.prop(prefs, "Cont_prefix")
                    #row.enabled = False
                else:
                    row.prop(self.Affixes, prop)
                    
def Display_Bone_IK(layout, armature, cb):
    box = layout.box()
    cp_bone = armature.pose.bones[cb.name]
    row = box.row()
    row.prop(cb, "Show_expanded", text="", emboss=False, icon="DISCLOSURE_TRI_DOWN" if cb.Show_expanded else "DISCLOSURE_TRI_RIGHT")
    row.label(text="Inverse Kinematics: " + cb.name)
    if cb.Show_expanded:
        b_row = box.row()
        col = b_row.column(align=True)
        col.prop(cp_bone, "lock_ik_x", text="X", emboss=False)
        col.prop(cp_bone, "lock_ik_y", text="Y", emboss=False)
        col.prop(cp_bone, "lock_ik_z", text="Z", emboss=False)
        # ik stiffness column...
        col = b_row.column(align=True)
        row = col.row(align=True)
        row.active = not cp_bone.lock_ik_x
        row.prop(cp_bone, "ik_stiffness_x", text="")
        row.prop(cp_bone, "use_ik_limit_x", text="", icon='CON_ROTLIMIT')
        row = col.row(align=True)
        row.active = not cp_bone.lock_ik_y
        row.prop(cp_bone, "ik_stiffness_y", text="")
        row.prop(cp_bone, "use_ik_limit_y", text="", icon='CON_ROTLIMIT')
        row = col.row(align=True)
        row.active = not cp_bone.lock_ik_z
        row.prop(cp_bone, "ik_stiffness_z", text="")
        row.prop(cp_bone, "use_ik_limit_z", text="", icon='CON_ROTLIMIT')
        # ik min + max columns...
        col = b_row.column(align=True)
        row = col.row(align=True)
        row.active = cp_bone.use_ik_limit_x and not cp_bone.lock_ik_x
        row.prop(cp_bone, "ik_min_x", text="")
        row.prop(cp_bone, "ik_max_x", text="")
        row = col.row(align=True)
        row.active = cp_bone.use_ik_limit_y and not cp_bone.lock_ik_y
        row.prop(cp_bone, "ik_min_y", text="")
        row.prop(cp_bone, "ik_max_y", text="")
        row = col.row(align=True)
        row.active = cp_bone.use_ik_limit_z and not cp_bone.lock_ik_z
        row.prop(cp_bone, "ik_min_z", text="")
        row.prop(cp_bone, "ik_max_z", text="")
    if cb.Gizmo in armature.pose.bones:
        gizmo = armature.pose.bones[cb.Gizmo]
        if len(gizmo.constraints) > 0:
            copy_scale = gizmo.constraints["SOFT - Copy Scale"]
            limit_scale = gizmo.constraints["SOFT - Limit Scale"]
            row = box.row(align=True)
            row.prop(cp_bone, "ik_stretch", text="Stretch", icon='CON_STRETCHTO')
            row.prop(copy_scale, "power", text="Power", icon='CON_SIZELIKE')
            row.prop(limit_scale, "max_y", text="Max Y", icon='CON_SIZELIMIT')
    

def Display_Bone_FK(layout, armature, cb):
    box = layout.box()
    cp_bone = armature.pose.bones[cb.name]
    box.label(text="Forward Constraints: " + cb.name)
    for con_name in ["FORWARD - Copy Location", "FORWARD - Copy Rotation", "FORWARD - Copy Scale"]:
        if con_name in cp_bone.constraints:
            con_box = box.box()
            con = cp_bone.constraints[con_name]
            row = con_box.row()
            row.prop(con, "show_expanded", text="", emboss=False)
            row.label(text=con_name[10:], icon='CON_LOCLIKE' if "Loc" in con_name else 'CON_ROTLIKE' if "Rot" in con_name else 'CON_SIZELIKE')
            row.prop(con, "mute", text="", emboss=False)
            if con.show_expanded:
                row = con_box.row(align=True)
                row.prop(con, "use_x", text="Copy X", toggle=True)
                row.prop(con, "use_y", text="Copy Y", toggle=True)
                row.prop(con, "use_z", text="Copy Z", toggle=True)
                if con_name != "FORWARD - Copy Scale":
                    row = con_box.row(align=True)
                    row.prop(con, "invert_x", text="Invert X", toggle=True)
                    row.prop(con, "invert_y", text="Invert Y", toggle=True)
                    row.prop(con, "invert_z", text="Invert Z", toggle=True)
                else:
                    row = con_box.row()
                    row.prop(con, "power")
                    row = con_box.row()
                    row.prop(con, "use_make_uniform", text="Uniform", toggle=True)
                    row.prop(con, "use_offset", text="Offset", toggle=True)
                    col = row.column()
                    col.active = con.use_offset
                    col.prop(con, "use_add", toggle=True)
                if con_name == "FORWARD - Copy Rotation":
                    con_box.prop(con, "mix_mode", text="Mix")
                    con_box.prop(con, "euler_order", text="Order")
                elif con_name == "FORWARD - Copy Location":
                    con_box.prop(con, "use_offset", toggle=True)
                con_box.prop(con, "target_space")
                con_box.prop(con, "owner_space")
            row = con_box.row()
            row.prop(con, "influence")
                
class JK_UL_Rigging_List(bpy.types.UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        slot = item
        # draw_item must handle the three layout types... Usually 'DEFAULT' and 'COMPACT' can share the same code.
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if "Type" in slot.bl_rna.properties:
                # if we are displaying a chain...
                if slot.Type in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE', 'SPLINE', 'SCALAR', 'FORWARD']:
                    row = layout.row()
                    label_icon = 'CON_KINEMATIC' if slot.Type in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE', 'SCALAR'] else 'CON_SPLINEIK' if slot.Type == 'SPLINE' else 'CON_TRANSLIKE'
                    label_text = slot.Type + " - " + slot.Limb + " - " + slot.Bones[0].name
                    row.label(text=label_text, icon=label_icon)
                    if slot.Type in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE', 'SCALAR']:
                        row.prop(slot, "Auto_fk", text="", emboss=False, icon="PROP_ON" if slot.Auto_fk else "PROP_OFF")
                        row.prop(slot, "Auto_key", text="", emboss=False, icon="KEYINGSET" if slot.Auto_key else "KEY_DEHLT")
                        col = row.column()
                        col.prop(slot, "Use_fk", text="", emboss=False, icon='SNAP_ON' if slot.Use_fk else 'SNAP_OFF') #icon='LINKED' if slot.Use_fk else 'UNLINKED')
                        col.enabled = not slot.Auto_fk
                    #elif slot.Type == 'FORWARD':   
                        #row.prop(slot.Forward, "Mute_all", text="", emboss=False, icon='UNLINKED' if slot.Forward.Mute_all else 'LINKED')
                # if we are displaying a twist...
                elif slot.Type in ['HEAD_HOLD', 'TAIL_FOLLOW']:
                    row = layout.row()
                    label_icon = 'TRACKING_BACKWARDS' if slot.Type == 'HEAD_HOLD' else 'TRACKING_FORWARDS'
                    label_text = slot.Type + " - " + slot.name
                    row.label(text=label_text, icon=label_icon)
                # if we are displaying a pivot...
                elif slot.Type in ['SHARE', 'SKIP']:
                    row = layout.row()
                    label_icon = 'LOCKED' if slot.Is_forced else 'PIVOT_INDIVIDUAL' if slot.Type == 'SHARE' else 'PIVOT_ACTIVE'
                    label_text = slot.Type + " - " + slot.name
                    row.label(text=label_text, icon=label_icon)
            else:
                row = layout.row()
                label_icon = 'CON_FLOOR' #'PIVOT_INDIVIDUAL' if slot.Type == 'PARENT_SHARE' else 'PIVOT_ACTIVE'
                label_text = slot.name
                row.label(text=label_text, icon=label_icon)

        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class JK_PT_ARL_Armature_Panel(bpy.types.Panel):
    bl_label = "Rigging"
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
        ARL = armature.data.ARL
        layout = self.layout
        row = layout.row(align=True)
        col = row.column(align=True)
        col.prop(ARL, "Hide_chain", text="Chains", icon='HIDE_ON' if ARL.Hide_chain else 'HIDE_OFF', invert_checkbox=True)
        col.prop(ARL, "Hide_target", text="Targets", icon='HIDE_ON' if ARL.Hide_target else 'HIDE_OFF', invert_checkbox=True)
        col = row.column(align=True)
        col.prop(ARL, "Hide_pivot", text="Pivots", icon='HIDE_ON' if ARL.Hide_pivot else 'HIDE_OFF', invert_checkbox=True)
        col.prop(ARL, "Hide_twist", text="Twists", icon='HIDE_ON' if ARL.Hide_twist else 'HIDE_OFF', invert_checkbox=True)
        col = row.column(align=True)
        col.prop(ARL, "Hide_gizmo", text="Gizmos", icon='HIDE_ON' if ARL.Hide_gizmo else 'HIDE_OFF', invert_checkbox=True)
        col.prop(ARL, "Hide_none", text="Unrigged", icon='HIDE_ON' if ARL.Hide_none else 'HIDE_OFF', invert_checkbox=True)

class JK_PT_ARL_Chain_Panel(bpy.types.Panel):
    bl_label = "Chains"
    bl_idname = "JK_PT_ARL_Chain_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "JK_PT_ARL_Armature_Panel"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE'
 
    def draw(self, context):
        armature = bpy.context.object
        ARL = armature.ARL
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.template_list("JK_UL_Rigging_List", "chains", ARL, "Chains", ARL, "Chain")
        col = row.column(align=True)
        col.operator("jk.chain_set", text="", icon='ADD').Action = 'ADD'
        col.operator("jk.chain_set", text="", icon='REMOVE').Action = 'REMOVE'
        if ARL.Chain < len(ARL.Chains):
            chain = ARL.Chains[ARL.Chain]
            if chain.Type in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE']:
                row = box.row()
                row.prop(chain, "Auto_key", icon="KEYINGSET" if chain.Auto_key else "KEY_DEHLT")
                row.prop(chain, "Auto_fk", icon="PROP_ON" if chain.Auto_fk else "PROP_OFF")
                row = box.row()
                col = row.column()
                col.operator("jk.keyframe_chain", icon="KEY_HLT")
                col = row.column()
                col.prop(chain, "Use_fk", icon="SNAP_ON" if chain.Use_fk else "SNAP_OFF")
                col.enabled = not chain.Auto_fk  
            #elif chain.Type == 'FORWARD':
                #row = box.row()
                #row.prop(chain.Forward, "Mute_all", text="Mute Chain", icon='UNLINKED' if chain.Forward.Mute_all else 'LINKED')
            for i, tb in enumerate(ARL.Chains[ARL.Chain].Targets):
                row = box.row(align=True)
                is_active = True if armature.data.bones.active == armature.data.bones[tb.name] else False
                if chain.Type == 'SPLINE':
                    row.label(text="Target " + i + " (" + tb.name + "):")
                else:
                    row.label(text="Target (" + tb.name + "):")
                col = row.column()
                sel_row = col.row(align=True)
                sel_row.ui_units_x = 9.5
                sel_row.operator("jk.active_bone_set", text="Active", icon='PMARKER_ACT' if is_active else 'PMARKER', depress=is_active).Bone = tb.name
                sel_row.prop(armature.data.bones[tb.name], "select", text="Select", icon='RESTRICT_SELECT_OFF' if armature.data.bones[tb.name].select else 'RESTRICT_SELECT_ON')
                #row.prop(armature.data.bones[tb.name], "hide")
            if chain.Pole.name in armature.data.bones:
                row = box.row(align=True)
                is_active = True if armature.data.bones.active == armature.data.bones[chain.Pole.name] else False
                row.label(text="Pole (" + chain.Pole.name + ")")
                col = row.column()
                sel_row = col.row(align=True)
                sel_row.ui_units_x = 9.5
                sel_row.operator("jk.active_bone_set", text="Active", icon='PMARKER_ACT' if is_active else 'PMARKER', depress=is_active).Bone = chain.Pole.name
                sel_row.prop(armature.data.bones[chain.Pole.name], "select", text="Select", icon='RESTRICT_SELECT_OFF' if armature.data.bones[chain.Pole.name].select else 'RESTRICT_SELECT_ON')
                #row.prop(armature.data.bones[chain.Pole.name], "hide")
            for cb in ARL.Chains[ARL.Chain].Bones:
                row = box.row()
                if chain.Type != 'FORWARD':
                    Display_Bone_IK(box, armature, cb)
                else:
                    Display_Bone_FK(box, armature, cb)

class JK_PT_ARL_Twist_Panel(bpy.types.Panel):
    bl_label = "Twists"
    bl_idname = "JK_PT_ARL_Twist_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "JK_PT_ARL_Armature_Panel"
    bl_order = 2

    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE'
 
    def draw(self, context):
        armature = bpy.context.object
        ARL = armature.ARL
        layout = self.layout
        bone = bpy.context.active_bone
        box = layout.box()
        row = box.row()
        row.template_list("JK_UL_Rigging_List", "twists", ARL, "Twists", ARL, "Twist")
        col = row.column(align=True)
        col.operator("jk.twist_set", text="", icon='ADD').Action = 'ADD'
        col.operator("jk.twist_set", text="", icon='REMOVE').Action = 'REMOVE'
        if ARL.Twist < len(ARL.Twists):
            twist = ARL.Twists[ARL.Twist]
            row = box.row(align=True)
            is_active = True if armature.data.bones.active == armature.data.bones[twist.name] else False
            row.label(text="Twist (" + twist.name + "):")
            col = row.column()
            sel_row = col.row(align=True)
            sel_row.ui_units_x = 9.5
            sel_row.operator("jk.active_bone_set", text="Active", icon='PMARKER_ACT' if is_active else 'PMARKER', depress=is_active).Bone = twist.name
            sel_row.prop(armature.data.bones[twist.name], "select", text="Select", icon='RESTRICT_SELECT_OFF' if armature.data.bones[twist.name].select else 'RESTRICT_SELECT_ON')
            #row.prop(armature.data.bones[twist.name], "hide")
            twist_box = box.box()
            tp_bone = armature.pose.bones[twist.name]
            if twist.Type == 'HEAD_HOLD':
                damp_track = tp_bone.constraints["TWIST - Damped Track"]
                limit_rot = tp_bone.constraints["TWIST - Limit Rotation"]
                twist_box.label(text="Head Hold: " + tp_bone.name)
                row = twist_box.row()
                row.prop(damp_track, "subtarget")
                row.prop(damp_track, "head_tail")
                row = twist_box.row(align=True)
                row.prop(limit_rot, "use_limit_x", text="", icon='CON_ROTLIMIT')
                row.prop(limit_rot, "min_x", text="X Min")
                row.prop(limit_rot, "max_x", text="X Max")
                row = twist_box.row(align=True)
                row.prop(limit_rot, "use_limit_z", text="", icon='CON_ROTLIMIT')
                row.prop(limit_rot, "min_z", text="Z Min")
                row.prop(limit_rot, "max_z", text="Z Max")
            elif twist.Type == 'TAIL_FOLLOW':
                twist_box.label(text="Tail Follow: " + tp_bone.name)
                ik = tp_bone.constraints["TWIST - IK"]
                row = twist_box.row()
                row.prop(ik, "subtarget")
                row.prop(ik, "influence")
                row = twist_box.row(align=True)
                row.prop(tp_bone, "use_ik_limit_y", text="", icon='CON_ROTLIMIT')
                row.prop(tp_bone, "ik_min_y", text="Y Min")
                row.prop(tp_bone, "ik_max_y", text="Y Max")

class JK_PT_ARL_Pivot_Panel(bpy.types.Panel):
    bl_label = "Pivots"
    bl_idname = "JK_PT_ARL_Pivot_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "JK_PT_ARL_Armature_Panel"
    bl_order = 3

    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE'
 
    def draw(self, context):
        armature = bpy.context.object
        ARL = armature.ARL
        layout = self.layout
        #bone = bpy.context.active_bone
        box = layout.box()
        row = box.row()
        row.template_list("JK_UL_Rigging_List", "pivots", ARL, "Pivots", ARL, "Pivot")
        col = row.column(align=True)
        col.operator("jk.pivot_set", text="", icon='ADD').Action = 'ADD'
        col.operator("jk.pivot_set", text="", icon='REMOVE').Action = 'REMOVE'
        row = box.row()
        if ARL.Pivot < len(ARL.Pivots):
            pivot = ARL.Pivots[ARL.Pivot]
            row = box.row(align=True)
            is_active = True if armature.data.bones.active == armature.data.bones[pivot.name] else False
            row.label(text="Pivot (" + pivot.name + "):")
            col = row.column()
            sel_row = col.row(align=True)
            sel_row.ui_units_x = 9.5
            sel_row.operator("jk.active_bone_set", text="Active", icon='PMARKER_ACT' if is_active else 'PMARKER', depress=is_active).Bone = pivot.name
            sel_row.prop(armature.data.bones[pivot.name], "select", text="Select", icon='RESTRICT_SELECT_OFF' if armature.data.bones[pivot.name].select else 'RESTRICT_SELECT_ON')
            #row.prop(armature.data.bones[pivot.name], "hide")
            pivot_box = box.box()
            #tp_bone = armature.pose.bones[pivot.name]
            row = pivot_box.row()
            row.prop(pivot, "Type")
            row = pivot_box.row()
            row.prop(pivot, "Parent")
            #row.enabled = True if pivot.Type == 'PARENT_SKIP' else False
            pivot_box.enabled = False

class JK_PT_ARL_Floor_Panel(bpy.types.Panel):
    bl_label = "Floors"
    bl_idname = "JK_PT_ARL_Floor_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "JK_PT_ARL_Armature_Panel"
    bl_order = 4

    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE'
 
    def draw(self, context):
        armature = bpy.context.object
        ARL = armature.ARL
        bones = armature.data.bones
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.template_list("JK_UL_Rigging_List", "floors", ARL, "Floors", ARL, "Floor")
        col = row.column(align=True)
        col.operator("jk.floor_set", text="", icon='ADD').Action = 'ADD'
        col.operator("jk.floor_set", text="", icon='REMOVE').Action = 'REMOVE'
        
        if ARL.Floor < len(ARL.Floors):
            floor = ARL.Floors[ARL.Floor]
            row = box.row(align=True)
            is_active = True if armature.data.bones.active == armature.data.bones[floor.name] else False
            row.label(text="Floor (" + floor.name + "):")
            col = row.column()
            sel_row = col.row(align=True)
            sel_row.ui_units_x = 9.5
            sel_row.operator("jk.active_bone_set", text="Active", icon='PMARKER_ACT' if is_active else 'PMARKER', depress=is_active).Bone = floor.name
            sel_row.prop(armature.data.bones[floor.name], "select", text="Select", icon='RESTRICT_SELECT_OFF' if armature.data.bones[floor.name].select else 'RESTRICT_SELECT_ON')
            #row.prop(armature.data.bones[floor.name], "hide")
            tp_bone = armature.pose.bones[floor.Source]
            floor_con = tp_bone.constraints["FLOOR - Floor"]
            floor_box = box.box()
            row = floor_box.row()
            row.prop(floor_con, "show_expanded", text="", emboss=False)
            row.label(text="Floor Constraint: " + floor.Source)
            row.prop(floor_con, "mute", text="", emboss=False)
            if floor_con.show_expanded:
                row = floor_box.row()
                col = row.column()
                col.label(text="Min/Max:")
                col = row.column()
                col.ui_units_x = 39
                row = col.row()
                row.prop(floor_con, "floor_location", expand=True)
                row = floor_box.row()
                row.label(text="Offset:")
                row.prop(floor_con, "offset", text="")
                row.prop(floor_con, "use_rotation")
                floor_box.prop(floor_con, "target_space")
                floor_box.prop(floor_con, "owner_space")
            floor_box.prop(floor_con, "influence")



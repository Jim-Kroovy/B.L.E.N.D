import bpy

#class JK_MMT_Addon_Prefs(bpy.types.AddonPreferences):
    #bl_idname = "BLEND-ArmatureEditingStages"

    #Affixes: PointerProperty(type=_properties_.JK_ARL_Rigging_Affix_Props)

    #def draw(self, context):

def Display_Bone_IK(box, armature, cb):
    name = cb.name
    control = armature.pose.bones[name]
    box.label(text="Inverse Kinematics: " + name)
    if cb.Gizmo in armature.pose.bones:
        gizmo = armature.pose.bones[cb.Gizmo]
        if len(gizmo.constraints) > 0:
            copy_rot = control.constraints["SOFT - Copy Rotation"]
            copy_scale = gizmo.constraints["SOFT - Copy Scale"]
            limit_scale = gizmo.constraints["SOFT - Limit Scale"]
            row = box.row()
            row.prop(copy_rot, "mix_mode", text="")
            row.prop(control, "ik_stretch", text="Stretch")
            row = box.row()
            row.prop(copy_scale, "power")
            row.prop(limit_scale, "max_y", text="Max Y")
    row_top = box.row()
    col = row_top.column(align=True)
    row = col.row(align=True)
    row.prop(control, "lock_ik_x", text="")
    row.prop(control, "use_ik_limit_x", text="", icon='CON_ROTLIMIT')
    row = col.row(align=True)
    row.prop(control, "lock_ik_y", text="")
    row.prop(control, "use_ik_limit_y", text="", icon='CON_ROTLIMIT')
    row = col.row(align=True)
    row.prop(control, "lock_ik_z", text="")
    row.prop(control, "use_ik_limit_z", text="", icon='CON_ROTLIMIT')
    # ik stiffness column...
    col = row_top.column(align=True)
    col.prop(control, "ik_stiffness_x", text="")
    col.prop(control, "ik_stiffness_y", text="")
    col.prop(control, "ik_stiffness_z", text="")
    # ik min + max columns...
    col = row_top.column(align=True)
    row = col.row(align=True)
    row.prop(control, "ik_min_x", text="")
    row.prop(control, "ik_max_x", text="")
    row = col.row(align=True)
    row.prop(control, "ik_min_y", text="")
    row.prop(control, "ik_max_y", text="")
    row = col.row(align=True)
    row.prop(control, "ik_min_z", text="")
    row.prop(control, "ik_max_z", text="")


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
                        row.prop(slot, "Use_fk", text="", emboss=False, icon='SNAP_ON' if slot.Use_fk else 'SNAP_OFF') #icon='LINKED' if slot.Use_fk else 'UNLINKED')
                    elif slot.Type == 'FORWARD':   
                        row.prop(slot.Forward, "Mute_all", text="", emboss=False, icon='UNLINKED' if slot.Forward.Mute_all else 'LINKED')
                    row.prop(slot, "Auto_key", text="", emboss=False,  icon='KEYINGSET' if slot.Auto_key else 'KEY_DEHLT')
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
        ARL = armature.ARL
        layout = self.layout
        bone = bpy.context.active_bone
        layout.label(text=bone.name)

class JK_PT_ARL_Chain_Panel(bpy.types.Panel):
    bl_label = "Chain Rigging"
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
        bone = bpy.context.active_bone
        box = layout.box()
        row = box.row()
        row.template_list("JK_UL_Rigging_List", "chains", ARL, "Chains", ARL, "Chain")
        col = row.column(align=True)
        col.operator("jk.chain_action", text="", icon='ADD').Action = 'ADD'
        col.operator("jk.chain_action", text="", icon='REMOVE').Action = 'REMOVE'
        row = box.row()
        if ARL.Chain < len(ARL.Chains):
            chain = ARL.Chains[ARL.Chain]
            for tb in ARL.Chains[ARL.Chain].Targets:
                row = box.row()
                row.label(text=tb.name)
            for cb in ARL.Chains[ARL.Chain].Bones:
                row = box.row()
                if chain.Type != 'FORWARD':
                    ik_box = row.box()
                    Display_Bone_IK(ik_box, armature, cb)

class JK_PT_ARL_Twist_Panel(bpy.types.Panel):
    bl_label = "Twist Rigging"
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
        col.operator("jk.twist_action", text="", icon='ADD').Action = 'ADD'
        col.operator("jk.twist_action", text="", icon='REMOVE').Action = 'REMOVE'
        row = box.row()
        if ARL.Twist < len(ARL.Twists):
            twist = ARL.Twists[ARL.Twist]
            twist_box = row.box()
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
    bl_label = "Pivot Rigging"
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
        col.operator("jk.pivot_action", text="", icon='ADD').Action = 'ADD'
        col.operator("jk.pivot_action", text="", icon='REMOVE').Action = 'REMOVE'
        row = box.row()
        if ARL.Pivot < len(ARL.Pivots):
            pivot = ARL.Pivots[ARL.Pivot]
            pivot_box = row.box()
            #tp_bone = armature.pose.bones[pivot.name]
            row = pivot_box.row()
            row.prop(pivot, "Type")
            row = pivot_box.row()
            row.prop(pivot, "Parent")
            row.enabled = True if pivot.Type == 'PARENT_SKIP' else False

class JK_PT_ARL_Floor_Panel(bpy.types.Panel):
    bl_label = "Floor Rigging"
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
        layout = self.layout
        #bone = bpy.context.active_bone
        box = layout.box()
        row = box.row()
        row.template_list("JK_UL_Rigging_List", "floors", ARL, "Floors", ARL, "Floor")
        col = row.column(align=True)
        col.operator("jk.floor_action", text="", icon='ADD').Action = 'ADD'
        col.operator("jk.floor_action", text="", icon='REMOVE').Action = 'REMOVE'
        row = box.row()
        if ARL.Floor < len(ARL.Floors):
            floor = ARL.Floors[ARL.Floor]
            tp_bone = armature.pose.bones[floor.Target]
            floor_con = tp_bone.constraints["FLOOR - Floor"]
            floor_box = row.box()
            row = floor_box.row()
            row.prop(floor_con, "floor_location", text="", icon='CON_LOCLIKE')
            row.prop(floor_con, "offset", text="", icon='CON_LOCLIMIT')
            row.prop(floor_con, "use_rotation", text="", icon='CON_ROTLIKE')
            row = floor_box.row()
            row.prop(floor_con, "target_space", text="From")
            row.prop(floor_con, "owner_space", text="To")



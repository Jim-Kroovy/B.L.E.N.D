import bpy

from . import _properties_

class JK_ARD_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = "BLEND-ArmatureactiveRetargeting"

    copy_loc: bpy.props.PointerProperty(type=_properties_.JK_PG_ARD_Constraint)

    copy_rot: bpy.props.PointerProperty(type=_properties_.JK_PG_ARD_Constraint)

    copy_sca: bpy.props.PointerProperty(type=_properties_.JK_PG_ARD_Constraint)

    def draw(self, context):
        layout = self.layout
        for con_name in ["RETARGET - copy Location", "RETARGET - copy Rotation", "RETARGET - copy Scale"]:
            con = self.copy_loc if "Location" in con_name else self.copy_rot if "Rotation" in con_name else self.copy_sca
            label = "Location" if "Location" in con_name else "Rotation" if "Rotation" in con_name else "Scale"
            icon = 'CON_LOCLIKE' if "Location" in con_name else 'CON_ROTLIKE' if "Rotation" in con_name else 'CON_SIZELIKE'
            con_box = layout.box()
            row = con_box.row()
            row.label(text=label, icon=icon)
            col = row.column()
            row = col.row()
            row.alignment = 'RIGHT'
            row.prop(con, "mute", text=" ", emboss=False, icon='HIDE_ON' if con.mute else 'HIDE_OFF')
            row.prop(con, "use", text=" ")
            row = con_box.row()
            row.prop(con, "Influence")

class JK_UL_ARD_Action_List(bpy.types.UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        slot = item
        action = slot.action
        # draw_item must handle the three layout types... Usually 'DEFAULT' and 'COMPACT' can share the same code.
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.label(text="" if slot.action else " ", icon='ACTION')
            if slot.action:
                row.prop(action, "name", text="", emboss=False)
            row.prop(slot, "use", text="", emboss=False, icon='HIDE_OFF' if slot.use else 'HIDE_ON')
        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class JK_PT_ARD_Armature_Panel(bpy.types.Panel):
    bl_label = "Retargeting"
    bl_idname = "JK_PT_ARD_Armature_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        source = bpy.context.object
        jk_ard = source.data.jk_ard
        layout.prop(jk_ard, "Target")
        bind_box = layout.box()
        row = bind_box.row(align=True)
        row.prop_search(jk_ard, "binding", jk_ard, "bindings", text="binding")
        row.operator("jk.edit_binding", text="", icon='PLUS').Edit = 'ADD'
        row.operator("jk.edit_binding", text="", icon='TRASH').Edit = 'REMOVE'
        row = bind_box.row()
        row.prop(jk_ard, "use_offsets")
        row.operator("jk.bake_retarget_actions", text="Bake All offsets" if jk_ard.use_offsets else "Single Bake").Bake_mode = 'ALL' if jk_ard.use_offsets else 'SINGLE'
        box = bind_box.box()
        row = box.row()
        row.prop(jk_ard, "Stay_bound")
        row.prop(jk_ard, "Only_selected")
        if not jk_ard.use_offsets:
            row = box.row()
            row.prop(jk_ard, "Bake_step")
        bind_box.enabled = True if jk_ard.target != None else False
            
class JK_PT_ARD_Offset_Panel(bpy.types.Panel):
    bl_label = "Offset Slots"
    bl_idname = "JK_PT_ARD_Offset_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "JK_PT_ARD_Armature_Panel"

    @classmethod
    def poll(cls, context):
        jk_ard = context.object.data.jk_ard
        return context.object.type == 'ARMATURE' and jk_ard.target != None and jk_ard.use_offsets

    def draw(self, context):
        layout = self.layout
        source = bpy.context.object
        jk_ard = source.data.jk_ard
        offset_box = layout.box()
        row = offset_box.row()
        row.template_list("JK_UL_action_List", "offsets", jk_ard, "offsets", jk_ard, "offset")
        col = row.column(align=True)
        col.operator("jk.add_action_slot", text="", icon='ADD').Is_offset = True
        col.operator("jk.remove_action_slot", text="", icon='REMOVE').Is_offset = True
        if len(jk_ard.offsets) > 0:
            offset = jk_ard.offsets[jk_ard.offset]
            row = offset_box.row()
            row.prop(offset, "action", text="")
            col = row.column()
            col.operator("jk.bake_retarget_actions", text="offset Bake").Bake_mode = 'OFFSET'
            col.enabled = offset.use and len(offset.actions) > 0
        offset_box.enabled = True if jk_ard.target != None else False

class JK_PT_ARD_Offset_Action_Panel(bpy.types.Panel):
    bl_label = "offset action slots"
    bl_idname = "JK_PT_ARD_offset_action_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "JK_PT_ARD_offset_Panel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        jk_ard = context.object.data.jk_ard
        return context.object.type == 'ARMATURE' and len(jk_ard.offsets) > 0

    def draw(self, context):
        layout = self.layout
        source = bpy.context.object
        jk_ard = source.data.jk_ard
        offset = jk_ard.offsets[jk_ard.offset]
        action_box = layout.box()
        row = action_box.row()
        row.template_list("JK_UL_action_List", "actions", offset, "actions", offset, "active")
        col = row.column(align=True)
        col.operator("jk.add_action_slot", text="", icon='ADD').Is_offset = False
        col.operator("jk.remove_action_slot", text="", icon='REMOVE').Is_offset = False
        if len(offset.actions) > 0:
            offset_action = offset.actions[offset.active]
            row = action_box.row()
            row.prop(offset_action, "action", text="")
            #row = action_box.row()
            col = row.column()
            row.operator("jk.bake_retarget_actions", text="Single Bake").Bake_mode = 'ACTION'
            col.enabled = offset.use
            row = action_box.row()
            row.prop(offset_action, "Bake_step")
        action_box.enabled = True if jk_ard.target != None else False
                        
class JK_PT_ARD_Bone_Panel(bpy.types.Panel):
    bl_label = "binding"
    bl_idname = "JK_PT_ARD_Bone_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"

    @classmethod
    def poll(cls, context):
        jk_ard = bpy.context.object.data.jk_ard
        return bpy.context.active_bone != None and bpy.context.active_bone.name in jk_ard.pose_bones

    def draw(self, context):
        layout = self.layout
        source = bpy.context.object
        jk_ard = source.data.jk_ard
        target = jk_ard.target
        bone = bpy.context.active_bone
        if bone.name in jk_ard.pose_bones:
            pb = jk_ard.pose_bones[bone.name]
            layout.prop_search(pb, "Target", target.data, "bones") 
            p_bone = source.pose.bones[pb.name]
            rp_bone = source.pose.bones[pb.retarget]
            if pb.Is_bound:
                row = layout.row()
                row.prop(pb, "Hide_target")
                row.prop(pb, "Hide_retarget")
                for con_name in ["RETARGET - copy Location", "RETARGET - copy Rotation", "RETARGET - copy Scale"]:
                    con = p_bone.constraints[con_name]
                    label = "Location" if "Location" in con_name else "Rotation" if "Rotation" in con_name else "Scale"
                    icon = 'CON_LOCLIKE' if "Location" in con_name else 'CON_ROTLIKE' if "Rotation" in con_name else 'CON_SIZELIKE'
                    auto = 'LOCATION' if "Location" in con_name else 'ROTATION' if "Rotation" in con_name else 'SCALE'
                    extra = "head_tail" if "Location" in con_name else "euler_order" if "Rotation" in con_name else "power"
                    con_box = layout.box()
                    row = con_box.row()
                    op = row.operator("jk.auto_offset", text="", icon=icon)
                    op.auto = auto
                    op.bone = pb.name
                    op.target = pb.target
                    if "RETARGET - Child Of" in rp_bone.constraints:
                        r_op = row.operator("jk.auto_offset", text="", icon='CON_CHILDOF')
                        r_op.auto = auto
                        r_op.bone = pb.retarget
                        r_op.target = pb.target
                    row.label(text=label)#, icon=icon)
                    col = row.column()
                    row = col.row()
                    row.alignment = 'RIGHT'
                    row.prop(con, "mute", text="", emboss=False)
                    row.prop(con, "use_x", text="X")
                    row.prop(con, "use_y", text="Y")
                    row.prop(con, "use_z", text="Z")
                    row = con_box.row()
                    row.prop(con, extra, text="" if extra == "euler_order" else None)
                    row.prop(con, "influence")
        

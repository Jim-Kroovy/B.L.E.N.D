import bpy

from . import _properties_

class JK_ARD_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = "BLEND-ArmatureRetargetDynamics"

    copy_loc: bpy.props.PointerProperty(type=_properties_.JK_PG_ARD_Constraint)

    copy_rot: bpy.props.PointerProperty(type=_properties_.JK_PG_ARD_Constraint)

    copy_sca: bpy.props.PointerProperty(type=_properties_.JK_PG_ARD_Constraint)

    bone_prefix: bpy.props.StringProperty(name="Retarget Prefix", description="The prefix used for retarget bones (it's unlikely anyone needs to change this but the option is here if you do)",
        default="RB_")

    offset_affix: bpy.props.StringProperty(name="Offset Affix", description="The affix used for offset actions (it's unlikely anyone needs to change this but the option is here if you do)",
        default="_OFFSET_")

    def draw(self, context):
        layout = self.layout
        #layout.prop(self, "prefix")
        #layout.label()
        for con_name in ["RETARGET - Copy Location", "RETARGET - Copy Rotation", "RETARGET - Copy Scale"]:
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
            row.prop(con, "influence")

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
        jk_ard = source.jk_ard
        #layout.prop(jk_ard, "target")
        row = layout.row(align=True)
        row.prop(jk_ard, 'use_actions')
        row.prop(jk_ard, 'use_meshes')
        bind_box = layout.box()
        row = bind_box.row(align=True)
        row.prop_search(jk_ard, "binding", jk_ard, "bindings", text="Binding")
        row.operator("jk.edit_binding", text="", icon='PLUS').edit = 'ADD'
        row.operator("jk.edit_binding", text="", icon='TRASH').edit = 'REMOVE'
        row = bind_box.row()
        row.prop(jk_ard, "use_offsets")
        row.operator("jk.bake_retarget_actions", text="Bake All offsets" if jk_ard.use_offsets else "Single Bake").bake_mode = 'ALL' if jk_ard.use_offsets else 'SINGLE'
        box = bind_box.box()
        row = box.row()
        row.prop(jk_ard, "stay_bound")
        row.prop(jk_ard, "only_selected")
        if not jk_ard.use_offsets:
            row = box.row()
            row.prop(jk_ard, "bake_step")
        bind_box.enabled = True if (jk_ard.use_actions or jk_ard.use_meshes) else False
            
class JK_PT_ARD_Offset_Panel(bpy.types.Panel):
    bl_label = "Offset Slots"
    bl_idname = "JK_PT_ARD_Offset_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "JK_PT_ARD_Armature_Panel"

    @classmethod
    def poll(cls, context):
        jk_ard = context.object.jk_ard
        return context.object.type == 'ARMATURE' and jk_ard.use_offsets

    def draw(self, context):
        layout = self.layout
        source = bpy.context.object
        jk_ard = source.jk_ard
        offset_box = layout.box()
        row = offset_box.row()
        row.template_list("JK_UL_action_List", "offsets", jk_ard, "offsets", jk_ard, "offset")
        col = row.column(align=True)
        col.operator("jk.add_action_slot", text="", icon='ADD').is_offset = True
        col.operator("jk.remove_action_slot", text="", icon='REMOVE').is_offset = True
        if len(jk_ard.offsets) > 0:
            offset = jk_ard.offsets[jk_ard.offset]
            row = offset_box.row()
            row.prop(offset, "action", text="")
            col = row.column()
            col.operator("jk.bake_retarget_actions", text="Offset Bake").bake_mode = 'OFFSET'
            col.enabled = offset.use and len(offset.actions) > 0
        offset_box.enabled = True if (jk_ard.use_actions or jk_ard.use_meshes) else False

class JK_PT_ARD_Offset_Action_Panel(bpy.types.Panel):
    bl_label = "offset action slots"
    bl_idname = "JK_PT_ARD_Offset_Action_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "JK_PT_ARD_Offset_Panel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        jk_ard = context.object.jk_ard
        return context.object.type == 'ARMATURE' and len(jk_ard.offsets) > 0

    def draw(self, context):
        layout = self.layout
        source = bpy.context.object
        jk_ard = source.jk_ard
        offset = jk_ard.offsets[jk_ard.offset]
        action_box = layout.box()
        row = action_box.row()
        row.template_list("JK_UL_action_List", "actions", offset, "actions", offset, "active")
        col = row.column(align=True)
        col.operator("jk.add_action_slot", text="", icon='ADD').is_offset = False
        col.operator("jk.remove_action_slot", text="", icon='REMOVE').is_offset = False
        if len(offset.actions) > 0:
            offset_action = offset.actions[offset.active]
            row = action_box.row()
            row.prop(offset_action, "action", text="")
            #row = action_box.row()
            col = row.column()
            row.operator("jk.bake_retarget_actions", text="Single Bake").bake_mode = 'ACTION'
            col.enabled = offset.use
            row = action_box.row()
            row.prop(offset_action, "Bake_step")
        action_box.enabled = True if jk_ard.target != None else False
                        
class JK_PT_ARD_Bone_Panel(bpy.types.Panel):
    bl_label = "Binding"
    bl_idname = "JK_PT_ARD_Bone_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"

    @classmethod
    def poll(cls, context):
        jk_ard = bpy.context.object.jk_ard
        return bpy.context.active_bone != None and bpy.context.active_bone.name in bpy.context.object.pose.bones

    def draw(self, context):
        layout = self.layout
        source = bpy.context.object
        jk_ard = source.jk_ard
        #target = jk_ard.target
        if bpy.context.active_pose_bone and (jk_ard.use_actions or jk_ard.use_meshes):
            pb = bpy.context.active_pose_bone
            layout.prop_search(pb.jk_ard, "target", bpy.data, "objects")
            if pb.jk_ard.target:
                layout.prop_search(pb.jk_ard, "subtarget", pb.jk_ard.target.data, "bones")
            if pb.jk_ard.is_bound:
                rp_bone = source.pose.bones.get(pb.jk_ard.retarget)
                row = layout.row()
                row.prop(pb.jk_ard, "hide_target")
                row.prop(pb.jk_ard, "hide_retarget")
                for con_name in ["RETARGET - Copy Location", "RETARGET - Copy Rotation", "RETARGET - Copy Scale"]:
                    con = pb.constraints[con_name]
                    label = "Location" if "Location" in con_name else "Rotation" if "Rotation" in con_name else "Scale"
                    icon = 'CON_LOCLIKE' if "Location" in con_name else 'CON_ROTLIKE' if "Rotation" in con_name else 'CON_SIZELIKE'
                    auto = 'LOCATION' if "Location" in con_name else 'ROTATION' if "Rotation" in con_name else 'SCALE'
                    extra = "head_tail" if "Location" in con_name else "euler_order" if "Rotation" in con_name else "power"
                    con_box = layout.box()
                    row = con_box.row()
                    op = row.operator("jk.auto_offset", text="", icon=icon)
                    op.auto = auto
                    op.bone = pb.jk_ard.name
                    op.target = pb.jk_ard.target.name if pb.jk_ard.target else ""
                    if "RETARGET - Child Of" in rp_bone.constraints:
                        r_op = row.operator("jk.auto_offset", text="", icon='CON_CHILDOF')
                        r_op.auto = auto
                        r_op.bone = pb.jk_ard.retarget
                        r_op.target = pb.jk_ard.target
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
        

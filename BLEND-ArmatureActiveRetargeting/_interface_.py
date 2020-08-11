import bpy

from . import _properties_

class JK_AAR_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = "BLEND-ArmatureActiveRetargeting"

    Copy_loc: bpy.props.PointerProperty(type=_properties_.JK_AAR_Constraint_Props)

    Copy_rot: bpy.props.PointerProperty(type=_properties_.JK_AAR_Constraint_Props)

    Copy_sca: bpy.props.PointerProperty(type=_properties_.JK_AAR_Constraint_Props)

    def draw(self, context):
        layout = self.layout
        #con_row = layout.row()
        for con_name in ["RETARGET - Copy Location", "RETARGET - Copy Rotation", "RETARGET - Copy Scale"]:
            con = self.Copy_loc if "Location" in con_name else self.Copy_rot if "Rotation" in con_name else self.Copy_sca
            label = "Location" if "Location" in con_name else "Rotation" if "Rotation" in con_name else "Scale"
            icon = 'CON_LOCLIKE' if "Location" in con_name else 'CON_ROTLIKE' if "Rotation" in con_name else 'CON_SIZELIKE'
            con_box = layout.box()
            row = con_box.row()
            row.label(text=label, icon=icon)
            col = row.column()
            row = col.row()
            row.alignment = 'RIGHT'
            row.prop(con, "Mute", text=" ", emboss=False, icon='HIDE_ON' if con.Mute else 'HIDE_OFF')
            row.prop(con, "Use", text=" ")
            row = con_box.row()
            row.prop(con, "Influence")

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

class JK_PT_AAR_Armature_Panel(bpy.types.Panel):
    bl_label = "Retargeting"
    bl_idname = "JK_PT_AAR_Armature_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        source = bpy.context.object
        AAR = source.data.AAR
        layout.prop(AAR, "Target")
        row = layout.row()
        row.prop(AAR, "Binding")
        row.operator("jk.edit_binding", text="", icon='PLUS').Edit = 'ADD'
        row.operator("jk.edit_binding", text="", icon='TRASH').Edit = 'REMOVE'
        row = layout.row()
        row.prop_search(AAR, "Binding", AAR, "Bindings", text="Active Binding")
        row.enabled = True if len(AAR.Bindings) > 1 else False 

class JK_PT_AAR_Offset_Panel(bpy.types.Panel):
    bl_label = "Offset Slots"
    bl_idname = "JK_PT_AAR_Offset_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "JK_PT_AAR_Armature_Panel"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        AAR = context.object.data.AAR
        return context.object.type == 'ARMATURE' and AAR.Target != None

    def draw(self, context):
        layout = self.layout
        source = bpy.context.object
        AAR = source.data.AAR
        offset = AAR.Offsets[AAR.Offset]
        offset_box = layout.box()
        row = offset_box.row()
        row.template_list("JK_UL_Action_List", "offsets", AAR, "Offsets", AAR, "Offset")
        col = row.column(align=True)
        col.operator("jk.add_action_slot", text="", icon='ADD').Is_offset = True
        col.operator("jk.remove_action_slot", text="", icon='REMOVE').Is_offset = True
        if len(AAR.Offsets) > 0:
            offset = AAR.Offsets[AAR.Offset]
            row = offset_box.row()
            row.prop(offset, "Action", text="")
            col = row.column()
            col.operator("jk.bake_retarget_actions", text="Offset Bake").Bake_mode = 'OFFSET'
            col.enabled = offset.Use and len(offset.Actions) > 0

class JK_PT_AAR_Offset_Action_Panel(bpy.types.Panel):
    bl_label = "Offset Action Slots"
    bl_idname = "JK_PT_AAR_Offset_Action_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "JK_PT_AAR_Armature_Panel"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0

    @classmethod
    def poll(cls, context):
        AAR = context.object.data.AAR
        return context.object.type == 'ARMATURE' and len(AAR.Offsets) > 0

    def draw(self, context):
        layout = self.layout
        source = bpy.context.object
        AAR = source.data.AAR
        offset = AAR.Offsets[AAR.Offset]
        action_box = layout.box()
        row = action_box.row()
        row.template_list("JK_UL_Action_List", "actions", offset, "Actions", offset, "Active")
        col = row.column(align=True)
        col.operator("jk.add_action_slot", text="", icon='ADD').Is_offset = False
        col.operator("jk.remove_action_slot", text="", icon='REMOVE').Is_offset = False
        if len(offset.Actions) > 0:
            offset_action = offset.Actions[offset.Active]
            row = action_box.row()
            row.prop(offset_action, "Action", text="")
            col = row.column()
            col.operator("jk.bake_retarget_actions", text="Single Bake").Bake_mode = 'ACTION'
            col.enabled = offset.Use
            row = action_box.row()
            row.prop(offset_action, "Bake_step")
            row.prop(offset_action, "Selected")
                        
class JK_PT_AAR_Bone_Panel(bpy.types.Panel):
    bl_label = "Retargeting"
    bl_idname = "JK_PT_AAR_Bone_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        AAR = bpy.context.object.data.AAR
        return bpy.context.active_bone != None and bpy.context.active_bone.name in AAR.Pose_bones

    def draw(self, context):
        layout = self.layout
        source = bpy.context.object
        AAR = source.data.AAR
        target = AAR.Target
        bone = bpy.context.active_bone
        if bone.name in AAR.Pose_bones:
            pg_bone = AAR.Pose_bones[bone.name]
            layout.prop_search(pg_bone, "Target", target.data, "bones")
            #if source.mode == 'POSE': 
            p_bone = source.pose.bones[bone.name]
            if pg_bone.Is_bound:
                row = layout.row()
                row.prop(pg_bone, "Hide_target")
                row.prop(pg_bone, "Hide_retarget")
                for con_name in ["RETARGET - Copy Location", "RETARGET - Copy Rotation", "RETARGET - Copy Scale"]:
                    con = p_bone.constraints[con_name]
                    label = "Location" if "Location" in con_name else "Rotation" if "Rotation" in con_name else "Scale"
                    icon = 'CON_LOCLIKE' if "Location" in con_name else 'CON_ROTLIKE' if "Rotation" in con_name else 'CON_SIZELIKE'
                    con_box = layout.box()
                    row = con_box.row()
                    row.label(text=label, icon=icon)
                    col = row.column()
                    row = col.row()
                    row.alignment = 'RIGHT'
                    row.prop(con, "mute", text="", emboss=False)
                    row.prop(con, "use_x", text="X")
                    row.prop(con, "use_y", text="Y")
                    row.prop(con, "use_z", text="Z")
                    row = con_box.row()
                    row.prop(con, "influence")
        

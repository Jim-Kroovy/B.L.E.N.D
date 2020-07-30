import bpy

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
        if AAR.Target != None:
            if len(AAR.Offsets) > 0:
                layout.prop(AAR, "Offset")
                if AAR.Offset != None:
                    action_box = layout.box()
                    offset = AAR.Offset.AAR
                    action_box.prop(offset, "Action")
                    action_box.prop(offset, "All_actions")
                    action_box.operator("jk.bake_retarget_action")

class JK_PT_AAR_Bone_Panel(bpy.types.Panel):
    bl_label = "Retargeting"
    bl_idname = "JK_PT_AAR_Bone_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        return bpy.context.active_bone != None

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
                    row.prop(con, "use_x", text="X")
                    row.prop(con, "use_y", text="Y")
                    row.prop(con, "use_z", text="Z")
                    row = con_box.row()
                    row.prop(con, "influence")
        

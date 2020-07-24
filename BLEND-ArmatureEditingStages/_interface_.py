import bpy

#bl_label = "Socket"
    #bl_idname = "JK_PT_AES_Pose_Panel"
    #bl_space_type = 'VIEW_3D'
    #bl_context = 'posemode'
    #bl_region_type = 'UI'
    #bl_category = "B.L.E.N.D"
     
class JK_MMT_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = "BLEND-ArmatureEditingStages"

    Hierarchy_display: bpy.props.BoolProperty(name="Hierarchy Display", description="Show armature stages in a hierarchy display",
        default=True, options=set())

    def Update_Debug_Display(self, context):
        if not self.Debug_display:
            self.Developer_mode = False
    
    Debug_display: bpy.props.BoolProperty(name="Debug Display", description="Displays internal variables for debug purposes",
        default=False, options=set(), update=Update_Debug_Display)
    
    Developer_mode: bpy.props.BoolProperty(name="Dev Mode", description="Enables editing internal variables for debug purposes. (WARNING: If you break things using this i might not be able to support fixing them!)",
        default=False, options=set())

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column()
        col.prop(self, 'Hierarchy_display')
        col = row.column()
        col.prop(self, 'Debug_display')
        col = row.column()
        col.prop(self, 'Developer_mode')
        col.enabled = self.Debug_display

class JK_PT_AES_Armature_Panel(bpy.types.Panel):
    bl_label = "Armature Stages"
    bl_idname = "JK_PT_AES_Armature_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_order = -10

    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        master = bpy.context.object
        prefs = bpy.context.preferences.addons["BLEND-ArmatureEditingStages"].preferences
        if master != None:
            AES = master.data.AES
            # check if we have any stages yet...
            if len(AES.Stages) == 0:
                # if we don't then only show the add stage opertator (with empty parent name)
                layout.operator("jk.add_armature_stage", icon='PRESET_NEW')
            # else if we are using the heirarchy display...
            elif prefs.Hierarchy_display:
                # add a main column...
                main_col = layout.column()
                levels = {}
                # for each name of the stages...
                for s_name in [s.name for s in AES.Stages]:
                    # we want to iterate on that name until we are at the source...
                    i, stage, name = 0, AES.Stages[s_name], s_name
                    while name != AES.Stages[0].name:
                        i = i + 1
                        name = stage.Parent
                        stage = AES.Stages[stage.Parent]
                    # then add the distance to source and the stages name...
                    if i in levels:
                        levels[i].append(s_name)#[s_name] = [s.name for s in AES.Stages if s.Parent == s_name]
                    else:
                        levels[i] = [s_name]#{s_name : [s.name for s in AES.Stages if s.Parent == s_name]}
                # iterate on the levels sorted into numerical order...
                columns = {}
                for index in sorted(levels.keys()):
                    names = levels[index]
                    rows = {}
                    # for each of those names...
                    for name in names:
                        # if the parent doesn't have a column we need to create a row...
                        if AES.Stages[name].Parent not in columns:
                            row = main_col.row()
                        else:
                            # if the row hasn't been created yet then create it...
                            if AES.Stages[name].Parent not in rows:
                                row = columns[AES.Stages[name].Parent].row()
                                # and assign it to the parents name...
                                rows[AES.Stages[name].Parent] = row
                            else:
                                # if we have a row assigned to the parent then use it
                                row = rows[AES.Stages[name].Parent]
                        # every name get's it's own column for its children to find...
                        col = row.column()
                        columns[name] = col
                        # getting some bools...
                        is_active = True if AES.Stage == name else False
                        is_selected = AES.Stages[name].Show_details
                        # wrap with a box if the stage is selected... (showing details)
                        if is_selected:
                            switch_box = col.box()
                        else:
                            switch_box = col
                        # slap the switch to stage operator into a row with it's show details bool...
                        switch_row = switch_box.row(align=True)
                        switch_row.operator("jk.switch_armature_stage", text=name, depress=is_active).Name = name
                        switch_row.prop(AES.Stages[name], "Show_details", text="", icon='DISCLOSURE_TRI_DOWN')
                        # if we want to show details (select stage)...
                        if AES.Stages[name].Show_details:
                            # add the stage properties into a row...
                            prop_row = switch_box.row(align=False)
                            prop_row.alignment = 'CENTER'
                            prop_row.prop(AES.Stages[name], "Push_data", icon='OUTLINER_DATA_ARMATURE')
                            prop_row.prop(AES.Stages[name], "Push_object", icon='OUTLINER_OB_ARMATURE')
                            prop_row.prop(AES.Stages[name], "Push_bones", icon='BONE_DATA')
                            # and add the stage operators into another row...
                            op_row = switch_box.row(align=False)
                            op_row.alignment = 'CENTER'
                            op_row.operator("jk.add_armature_stage", icon='PRESET_NEW').Parent = name
                            op_row.operator("jk.edit_armature_stage", icon='PRESET').Stage = name
                            # we don't want to be able to remove the source stage...
                            if not name == AES.Stages[0].name:
                                op_row.operator("jk.remove_armature_stage", icon='CANCEL').Stage = name
        
            else:
                stage = AES.Stages[AES.Stage]
                op_row = layout.row()
                op_row.prop_search(AES, "Stage", AES, "Stages", text="")
                op_row.operator("jk.add_armature_stage", text="", icon='PLUS').Stage = AES.Stage
                op_row.operator("jk.add_armature_stage", text="", icon='PRESET_NEW').Parent = AES.Stage
                op_row.operator("jk.edit_armature_stage", text="", icon='PRESET').Stage = AES.Stage
                if AES.Stage != AES.Stages[0].name:
                    op_row.operator("jk.remove_armature_stage", text="", icon='CANCEL').Stage = AES.Stage
                if AES.Stage in AES.Stages:
                    prop_row = layout.row()
                    prop_row.prop(stage, "Push_data")
                    prop_row.prop(stage, "Push_object")
                    prop_row.prop(stage, "Push_bones")
                else:
                    layout.label(text="Please select a valid stage!")
            
            if prefs.Debug_display:
                debug_box = layout.box()
                debug_box.label(text="Active Stage Debug:")
                debug_box.prop(AES, "Last", text="Last Stage")
                if len(AES.Stages) != 0:
                    stage = AES.Stages[AES.Stage]
                    debug_box.prop(stage, "Armature")
                    debug_box.prop(stage, "Parent")
                    debug_box.prop(stage, "Is_source")
                    debug_box.prop(bpy.data.armatures[stage.Armature].AES, "Is_master")
                debug_box.enabled = prefs.Developer_mode
                       
class JK_PT_AES_Bone_Panel(bpy.types.Panel):
    bl_label = "Stage Push Settings"
    bl_idname = "JK_PT_AES_Bone_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"

    @classmethod
    def poll(cls, context):
        if context.object.type == 'ARMATURE':
            props = bpy.context.object.data.AES
            if props.Stages[props.Stage]:
                if props.Stages[props.Stage].Push_bones:
                    return True
            else:
                return False 
        else:
            return False

    def draw(self, context):
        layout = self.layout
        master = bpy.context.object
        props = master.data.AES
        stage = props.Stages[props.Stage]
        bone = context.active_bone
        if bone.name in stage.Bones:
            bone_props = stage.Bones[bone.name]
            row = layout.row()
            col = row.column()
            col.prop(bone_props, "Push_edit")
            col.enabled = True if master.mode == 'EDIT' else False
            col = row.column()
            col.prop(bone_props, "Push_pose")
            col.enabled = True if master.mode == 'POSE' else False
            if master.mode == 'EDIT':
                box = layout.box()
                row = box.row()
                row.prop(bone_props.Edit, "Push_transform")
                row.prop(bone_props.Edit, "Push_bendy_bones")
                row = box.row()
                row.prop(bone_props.Edit, "Push_relations")
                row.prop(bone_props.Edit, "Push_deform")
                box.operator("jk.copy_active_push_settings", text="Copy To Selected").Update = False
                box.enabled = bone_props.Push_edit
            if master.mode == 'POSE':
                box = layout.box()
                row = box.row()
                row.prop(bone_props.Pose, "Push_posing")
                row.prop(bone_props.Pose, "Push_group")
                row = box.row()
                row.prop(bone_props.Pose, "Push_ik")
                row.prop(bone_props.Pose, "Push_display")
                row = box.row()
                row.prop(bone_props.Pose, "Push_constraints")
                row.prop(bone_props.Pose, "Push_drivers")
                layout.operator("jk.copy_active_push_settings", text="Copy To Selected").Update = False
                box.enabled = bone_props.Push_pose     
        else:
            layout.label(text="Push settings not found please update them")
            layout.operator("jk.copy_active_push_settings", text="Update Push Bones").Update = True


            












            

            
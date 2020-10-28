import bpy

from bpy.props import (FloatVectorProperty, StringProperty, BoolProperty, EnumProperty, PointerProperty, IntProperty)

from . import _properties_, _functions_

class JK_OT_Add_Armature_Stage(bpy.types.Operator):
    """Adds a new armature stage"""
    bl_idname = "jk.add_armature_stage"
    bl_label = "Add Stage"
    bl_options = {'REGISTER', 'UNDO'}
    
    Stage: StringProperty(name="Stage", description="Name of the new stage that should be added", 
        default="", maxlen=1024)

    Parent: StringProperty(name="Parent", description="The stage that will be the new stages parent", 
        default="", maxlen=1024)

    Insert: BoolProperty(name="Insert", description="The children of the parent stage get reparented to this stage",
        default=False, options=set())
    
    def execute(self, context):
        master = bpy.context.object
        AES = master.data.AES
        # if the stage doesn't already exist...
        if self.Stage not in AES.Stages:
            # add to the stages collection...
            new_stage = AES.Stages.add()
            new_stage.name, new_stage.Parent = self.Stage, self.Parent
            # if this stage has no parent...
            if self.Parent == "":
                # get its properties into a json dictionary...
                _functions_.Get_Stage_Properties(master, new_stage)
                # and set the stage variables... (setting last first so as to not trigger the update)
                master.data.AES.Last = self.Stage
                master.data.AES.Stage = self.Stage
            else:
                # else if there is a parent we can just copy its json dictionary strings...
                new_stage.Object_json, new_stage.Data_json, new_stage.Addon_json = AES.Stages[self.Parent].Object_json, AES.Stages[self.Parent].Data_json, AES.Stages[self.Parent].Addon_json
                for parent_bone in AES.Stages[self.Parent].Bones:
                    new_bone = new_stage.Bones.add()
                    new_bone.name, new_bone.Edit_json, new_bone.Pose_json = parent_bone.name, parent_bone.Edit_json, parent_bone.Pose_json
            # if we are inserting the stage...
            if self.Insert:
                # iterate over all the parents children... (but not the stage we just added)
                for child in [s for s in AES.Stages if (s.Parent == self.Parent and s.name != self.Stage)]:
                    # and re-parent them to the new inserted stage...
                    child.Parent = self.Stage
        return {'FINISHED'}
        
    def invoke(self, context, event):
        wm = context.window_manager
        self.Stage = ""
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        stages = bpy.context.object.data.AES.Stages
        row = layout.row()
        row.prop(self, "Stage")
        if len(stages) > 0:
            row.prop(self, "Insert")
        
class JK_OT_Remove_Armature_Stage(bpy.types.Operator):
    """Removes armature stages from an armature"""
    bl_idname = "jk.remove_armature_stage"
    bl_label = "Remove Stage"
    bl_options = {'REGISTER', 'UNDO'}

    Stage: StringProperty(name="Stage", description="Name of the stage that should be removed", 
        default="", maxlen=1024)
        
    def execute(self, context):
        master = bpy.context.object
        stages = master.data.AES.Stages
        # always check the user has given a valid stage...
        if self.Stage in stages:
            # get it's parent...
            parent = stages[self.Stage].Parent
            # reparent all it's children...
            for child in [st for st in stages if st.Parent == self.Stage]:
                child.Parent = parent
                # and pull from them...
                _functions_.Pull_Hierarchy_Inheritance(master, stages[self.Stage])
            # if the stage we are removing is active...
            if master.data.AES.Stage == self.Stage:
                # switch to its parent if it has one...
                if stages[self.Stage].Parent != "":
                    master.data.AES.Stage = stages[self.Stage].Parent
                else:
                    # or it's first child if it has children...
                    children = _functions_.Get_Stage_Children(stages, stages[self.Stage])
                    if len(children) > 0:
                        master.data.AES.Stage = stages[children[0].name]
                    # or just the first other stage if there are any...
                    elif len(stages) > 1:
                        for st_name in [st.name for st in stages if st.name != self.Stage]:
                            master.data.AES.Stage = stages[st_name]
                            break
            # and remove the stage...
            stages.remove(stages.find(self.Stage)) 
        return {'FINISHED'}

class JK_OT_Edit_Armature_Stage(bpy.types.Operator):
    """Edits the armature stage (Change parenting, Rename)"""
    bl_idname = "jk.edit_armature_stage"
    bl_label = "Edit Stage"
    bl_options = {'REGISTER', 'UNDO'}
    
    Stage: StringProperty(name="Stage", description="Name of the stage that should be edited", 
        default="", maxlen=1024)

    Rename: BoolProperty(name="Rename", description="Rename this armature stage",
        default=False, options=set())

    Name: StringProperty(name="Name", description="New name of the stage", 
        default="", maxlen=1024)

    Reparent: BoolProperty(name="Reparent", description="Reparent this armature stage to another",
        default=False, options=set())

    Parent: StringProperty(name="Parent", description="Name of the stage that should be removed", 
        default="", maxlen=1024)
    
    def execute(self, context):
        master = bpy.context.object
        stages = master.data.AES.Stages
        # always check the user has given a valid stage...
        if self.Stage in stages:
            # get the stage we want to edit...
            stage = stages[self.Stage]
            # if we are renaming it...
            if self.Rename:
                # check the name doesn't already exist...
                if self.Name not in stages:
                    # change any child stages parents to the new name...
                    for child in [s for s in stages if s.Parent == self.Stage]:
                        child.Parent = self.Name
                    # then change the stages name...
                    stage.name = self.Name
                    # if we are renaming the active stage...
                    if self.Stage == master.data.AES.Stage:
                        # set the switching strings... (in this order so as not to trigger the update)
                        master.data.AES.Last = self.Name
                        master.data.AES.Stage = self.Name
            # if we are reparenting the stage...
            if self.Reparent:
                # check the parent is a valid stage...
                if self.Parent in stages:
                    children = _functions_.Get_Stage_Children(stages, stages[self.Stage], recursive=True)
                    # if the new parent is a child of the stage...
                    if self.Parent in [stc.name for stc in children]:
                        # then we need to reparent this stages children first...
                        for child in [s for s in stages if s.Parent == self.Stage]:
                            child.Parent = stage.Parent 
                        # pull from old parent to get changes onto it's new children...
                        _functions_.Pull_Hierarchy_Inheritance(master, stages[stage.Parent])
                    # change the parent...
                    stage.Parent = self.Parent
                    # then pull from the new parent to correct any changes this might cause...
                    _functions_.Pull_Hierarchy_Inheritance(master, stages[self.Parent])
        return {'FINISHED'}

    def invoke(self, context, event):
        AES = bpy.context.object.data.AES
        if AES.Stages.find(self.Stage) > 0:
            self.Reparent = False
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
        
    def draw(self, context):
        layout = self.layout
        AES = bpy.context.object.data.AES
        layout.prop(self, "Rename")
        row = layout.row()
        row.prop(self, "Name")
        row.enabled = self.Rename
        if AES.Stages.find(self.Stage) > 0:
            layout.prop(self, "Reparent")
            row = layout.row()
            row.prop_search(self, "Parent", AES, "Stages")
            row.enabled = self.Reparent

class JK_OT_Switch_Armature_Stage(bpy.types.Operator):
    """Switch to the labelled armature stage"""
    bl_idname = "jk.switch_armature_stage"
    bl_label = "Switch Stage"
    bl_options = {'REGISTER', 'UNDO'}
    
    Name: StringProperty(name="Name", description="Name of the stage to switch to", 
        default="", maxlen=1024)
        
    def execute(self, context):
        master = bpy.context.object
        stages = master.data.AES.Stages
        if self.Name in stages:
            master.data.AES.Stage = self.Name
        return {'FINISHED'}

class JK_OT_Copy_Active_Push_Settings(bpy.types.Operator):
    """Copys the given push settings of the active bone to all selected bones"""
    bl_idname = "jk.copy_active_push_settings"
    bl_label = "Copy To Selected"
    bl_options = {'REGISTER', 'UNDO'}
    
    Update: BoolProperty(name="Update Push Bones", description="Update the push bones of this stage. (This happens automatically when switching stages)",
        default=False, options=set())

    def execute(self, context):
        master = bpy.context.object
        props = master.data.AES
        stage = props.Stages[props.Stage]
        # if we are updating the push bones...
        if self.Update:
            _functions_.Get_Stage_Bones(stage, master.data.bones)
        # otherwise we are copying to selected...
        else:
            bones = master.data.edit_bones if master.mode == 'EDIT' else master.data.bones
            active = bones.active
            selected = {b.name : b for b in bones if b.select}
            settings = stage.Bones[active.name]
            # for each bone on this stage... (if it's selected)
            for bone in [stb for stb in stage.Bones if stb.name in selected]:
                # copy/paste the pose bone inherit settings...
                bone.Pose_inherit = settings.Pose_inherit
                for p_group in bone.Pose_groups:
                    p_group.iht = settings[p_group.name].Inherit
                    for p_iht in p_group.Inheritance:
                        p_iht.Inherit = settings[p_group.name][p_iht.name].Inherit
                # and copy/paste the edit bone push settings...
                bone.Edit_inherit = settings.Edit_inherit
                for e_group in bone.Edit_groups:
                    e_group.iht = settings[e_group.name].Inherit
                    for e_iht in e_group.Inheritance:
                        e_iht.Inherit = settings[e_group.name][e_iht.name].Inherit         
        return {'FINISHED'}

class JK_OT_Draw_Push_Settings(bpy.types.Operator):
    """Draws a window for specific push settings when shift clicked"""
    bl_idname = "jk.draw_pull_settings"
    bl_label = "Push Settings"
    bl_options = {'REGISTER', 'UNDO'}
    
    Stage: StringProperty(name="Stage", description="Name of the stage that should be edited", 
        default="", maxlen=1024)

    Settings: EnumProperty(name="Settings", description="The type of settings we are going to draw",
        items=[('OBJECT', "Object", ""), ('DATA', "Data", ""), ('BONES', "Bones", "")],
        default='OBJECT', options=set())

    def Update_Active(self, context):
        master = bpy.context.object
        AES = master.data.AES
        stage = AES.Stages[self.Stage]
        bones = master.data.edit_bones if master.mode == 'EDIT' else master.data.bones
        if len(stage.Bones) > 0:
            stage_bone = stage.Bones[self.Active]
            bones.active = bones[stage_bone.name]
            bones[stage_bone.name].select = True

    Active: IntProperty(name="Active", default=0, update=Update_Active)
    
    @classmethod
    def poll(cls, context):
        return context.object != None and context.object.type == 'ARMATURE'
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        master = bpy.context.object
        AES = master.data.AES
        stage = AES.Stages[self.Stage]
        bools = {'OBJECT' : stage.Object_inherit, 'DATA' : stage.Data_inherit, 'BONES' : stage.Bones_inherit}
        if event.shift and bools[self.Settings]:
            return context.window_manager.invoke_popup(self)
        else:
            self.Active = self.Active
            if self.Settings == 'OBJECT':
                stage.Object_inherit = False if stage.Object_inherit else True
            elif self.Settings == 'DATA':
                stage.Data_inherit = False if stage.Data_inherit else True
            else:
                stage.Bones_inherit = False if stage.Bones_inherit else True
            return self.execute(context)
    
    def draw(self, context):
        layout = self.layout
        master = bpy.context.object
        AES = master.data.AES
        stage = AES.Stages[self.Stage]
        if self.Settings == 'OBJECT':
            box = layout.box()
            row = box.row()
            row.prop(stage.Object_groups['Transform'], "Inherit", text="Transforms")
            row.prop(stage.Object_groups['Relations'], "Inherit", text="Relations")
            row = box.row()
            row.prop(stage.Object_groups['Instancing'], "Inherit", text="Instancing")
            row.prop(stage.Object_groups['Display'], "Inherit", text="Display")
        elif self.Settings == 'DATA':
            box = layout.box()
            row = box.row()
            row.prop(stage.Data_groups['Skeleton'], "Inherit", text="Skeleton")
            row.prop(stage.Data_groups['Pose'], "Inherit", text="Pose")
            row = box.row()
            row.prop(stage.Data_groups['Animation'], "Inherit", text="Animation")
            row.prop(stage.Data_groups['Display'], "Inherit", text="Display")
        elif self.Settings == 'BONES':
            bones = master.data.edit_bones if master.mode == 'EDIT' else master.data.bones
            layout.template_list("JK_UL_Push_Bones_List", "operator", stage, "Bones", self, "Active")
            bone = stage.Bones[self.Active]
            row = layout.row()
            row.operator("jk.copy_active_push_settings", text="Update Stage Bones").Update = True
            row.operator("jk.copy_active_push_settings", text="Copy To Selected").Update = False
            row.enabled = bone.name in AES.Stages[stage.Parent].Bones
            row = layout.row(align=True)
            # row.label(text=bone.name)
            row.prop(bones[bone.name], "select", text="Select", emboss=False, icon='RESTRICT_SELECT_OFF' if bones[bone.name].select else 'RESTRICT_SELECT_ON')
            row.prop(bone, "Edit_inherit", emboss=False, icon='DECORATE_KEYFRAME' if bone.Edit_inherit else 'DECORATE_ANIMATE')
            row.prop(bone, "Pose_inherit", emboss=False, icon='RADIOBUT_ON' if bone.Pose_inherit else 'RADIOBUT_OFF')
            row.enabled = bone.name in AES.Stages[stage.Parent].Bones
            if bone.Edit_inherit:
                box = layout.box()
                box.label(text="Edit Bone Inheritance")
                row = box.row()
                row.prop(bone.Edit_groups['Transform'], "Inherit", text="Transforms")
                row.prop(bone.Edit_groups['Bendy Bones'], "Inherit", text="Bendy Bones")
                row = box.row()
                row.prop(bone.Edit_groups['Relations'], "Inherit", text="Relations")
                row.prop(bone.Edit_groups['Deform'], "Inherit", text="Deform")
                box.enabled = bone.Edit_inherit
            if bone.Pose_inherit:
                box = layout.box()
                box.label(text="Pose Bone Inheritance")
                row = box.row()
                row.prop(bone.Pose_groups['Posing'], "Inherit", text="Posing")
                row.prop(bone.Pose_groups['Rigging'], "Inherit", text="Rigging")
                row = box.row()
                row.prop(bone.Pose_groups['IK Settings'], "Inherit", text="IK Settings")
                row.prop(bone.Pose_groups['Display'], "Inherit", text="Display")
                box.enabled = bone.Pose_inherit
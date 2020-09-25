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
            armature = bpy.data.objects[AES.Stages[self.Parent].Armature] if len(AES.Stages) > 0 else master
            # copy its data...
            data = armature.data.copy()
            # copy its object...
            copy = armature.copy()
            # put them together...
            copy.data = data
            # name the object and data after the master and stage we are adding...
            copy.name = master.name + " - " + self.Stage
            copy.data.name = master.name + " - " + self.Stage
            # don't want either to get deleted on save/load... (unless their master has been deleted)
            copy.use_fake_user, copy.data.use_fake_user, copy.data.AES.Is_stage = True, True, True
            # add to the stages collection...
            new_stage = AES.Stages.add()
            new_stage.name, new_stage.Parent, new_stage.Armature = self.Stage, self.Parent, copy.name
            # if this is the source stage...
            if self.Parent == "":
                # master wants its stage variables set...
                master.data.AES.Last = self.Stage
                master.data.AES.Stage = self.Stage
                # set is master true...
                master.data.AES.Is_master = True
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
            for child in [s for s in stages if s.Parent == self.Stage]:
                child.Parent = parent
            # then push from the parent and remove the parent...
            _functions_.Push_From_Stage(master, stages[parent])
            # if the stage we are removing is active...
            if master.data.AES.Stage == self.Stage:
                # get the masters name...
                master_name = master.name
                # switch to its parent...
                master.data.AES.Stage = stages[self.Stage].Parent
                # reset the master and stages variables...
                master = bpy.data.objects[master_name]
                stages = master.data.AES.Stages
            # and remove the stage and any associated objects/armatures...
            stages.remove(stages.find(self.Stage))
            if master.name + " - " + self.Stage in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects[master.name + " - " + self.Stage])
            if master.name + " - " + self.Stage in bpy.data.armatures:
                bpy.data.armatures.remove(bpy.data.armatures[master.name + " - " + self.Stage])
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
                    # change the stage object and data names...
                    stage_object = bpy.data.objects[stage.Armature]
                    stage_object.name = master.name + " - " + self.Name
                    stage_object.data.name = master.name + " - " + self.Name
                    stage.Armature = master.name + " - " + self.Name
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
                    # we need to know if we are reparenting to a child...
                    i, is_child, iterate, children = 0, False, True, [self.Stage]
                    # while the iterate bool is true...
                    while iterate:
                        # get the name and increment...
                        name, i = children[i], i + 1
                        stage = stages[name]
                        next_children = [s.name for s in stages if s.Parent == name]
                        # for each of the next children...
                        for child in next_children:
                            # check if the child is what we are trying to parent to...
                            if child == self.Parent:
                                # set is child true and break
                                is_child = True
                                break
                            else:
                                # if it isn't then append it to the children list to continue iteration...
                                children.append(child)
                        # if at any point we find a child break...
                        if is_child:
                            break
                        # finally the iterate bool, will stop iteration once we reach the length of the accumulating children...
                        iterate = True if i < len(children) else False
                    # if we are trying to parent to a child...
                    if is_child:
                        # then we need to reparent this stages children first...
                        for child in [s for s in stages if s.Parent == self.Stage]:
                            child.Parent = stage.Parent 
                        # push from old parent to get changes onto it's new children...
                        _functions_.Push_From_Stage(master, stages[stage.Parent])
                    # change the parent...
                    stage.Parent = self.Parent
                    # then push from the new parent to correct any object, data and bone changes this might cause...
                    _functions_.Push_From_Stage(master, stages[self.Parent])
        
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
    """Switches to the labelled armature stage"""
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
            _functions_.Get_Push_Bones(stage, master.data.bones)
        # otherwise we are copying to selected...
        else:
            bones = master.data.edit_bones if master.mode == 'EDIT' else master.data.bones
            active = bones.active
            selected = {b.name : b for b in bones if b.select}
            settings = stage.Bones[active.name]
            # for each bone on this stage...
            for bone in stage.Bones:
                # if it's selected...
                if bone.name in selected:
                    # copy/paste the pose bone push settings...
                    bone.Push_pose = settings.Push_pose
                    bone.Pose.Push_posing = settings.Pose.Push_posing
                    bone.Pose.Push_group = settings.Pose.Push_group
                    bone.Pose.Push_ik = settings.Pose.Push_ik
                    bone.Pose.Push_display = settings.Pose.Push_display
                    bone.Pose.Push_constraints = settings.Pose.Push_constraints
                    bone.Pose.Push_drivers = settings.Pose.Push_drivers
                    # and copy/paste the edit bone push settings...
                    bone.Push_edit = settings.Push_edit
                    bone.Edit.Push_transform = settings.Edit.Push_transform
                    bone.Edit.Push_bendy_bones = settings.Edit.Push_bendy_bones
                    bone.Edit.Push_relations = settings.Edit.Push_relations
                    bone.Edit.Push_deform = settings.Edit.Push_deform
        return {'FINISHED'}

class JK_OT_Draw_Push_Settings(bpy.types.Operator):
    """Draws a window for specific push settings when shift clicked"""
    bl_idname = "jk.draw_push_settings"
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
        bools = {'OBJECT' : stage.Push_object, 'DATA' : stage.Push_data, 'BONES' : stage.Push_bones}
        if event.shift and bools[self.Settings]:
            return context.window_manager.invoke_popup(self)
        else:
            self.Active = self.Active
            if self.Settings == 'OBJECT':
                stage.Push_object = False if stage.Push_object else True
            elif self.Settings == 'DATA':
                stage.Push_data = False if stage.Push_data else True
            else:
                stage.Push_bones = False if stage.Push_bones else True
                _functions_.Get_Push_Bones(stage, master.data.bones)
            return self.execute(context)
    
    def draw(self, context):
        layout = self.layout
        master = bpy.context.object
        AES = master.data.AES
        stage = AES.Stages[self.Stage]
        if self.Settings == 'OBJECT':
            box = layout.box()
            row = box.row()
            row.prop(stage.Object, "Push_transform")
            row.prop(stage.Object, "Push_relations")
            row = box.row()
            row.prop(stage.Object, "Push_instancing")
            row.prop(stage.Object, "Push_display")
        elif self.Settings == 'DATA':
            box = layout.box()
            row = box.row()
            row.prop(stage.Data, "Push_skeleton")
            row.prop(stage.Data, "Push_groups")
            row = box.row()
            row.prop(stage.Data, "Push_library")
            row.prop(stage.Data, "Push_display")
        elif self.Settings == 'BONES':
            bones = master.data.edit_bones if master.mode == 'EDIT' else master.data.bones
            layout.template_list("JK_UL_Push_Bones_List", "operator", stage, "Bones", self, "Active")
            bone = stage.Bones[self.Active]
            row = layout.row()
            row.operator("jk.copy_active_push_settings", text="Update Stage Bones").Update = True
            row.operator("jk.copy_active_push_settings", text="Copy To Selected").Update = False
            row = layout.row(align=True)
            # row.label(text=bone.name)
            row.prop(bones[bone.name], "select", text="Select", emboss=False, icon='RESTRICT_SELECT_OFF' if bones[bone.name].select else 'RESTRICT_SELECT_ON')
            row.prop(bone, "Push_edit", emboss=False, icon='DECORATE_KEYFRAME' if bone.Push_edit else 'DECORATE_ANIMATE')
            row.prop(bone, "Push_pose", emboss=False, icon='RADIOBUT_ON' if bone.Push_pose else 'RADIOBUT_OFF')
            box = layout.box()
            row = box.row()
            row.prop(bone.Edit, "Push_transform")
            row.prop(bone.Edit, "Push_bendy_bones")
            row = box.row()
            row.prop(bone.Edit, "Push_relations")
            row.prop(bone.Edit, "Push_deform")
            box.enabled = bone.Push_edit
            box = layout.box()
            row = box.row()
            row.prop(bone.Pose, "Push_posing")
            row.prop(bone.Pose, "Push_group")
            row = box.row()
            row.prop(bone.Pose, "Push_ik")
            row.prop(bone.Pose, "Push_display")
            row = box.row()
            row.prop(bone.Pose, "Push_constraints")
            row.prop(bone.Pose, "Push_drivers")
            box.enabled = bone.Push_pose
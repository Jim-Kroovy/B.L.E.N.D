import bpy

from bpy.props import (FloatVectorProperty, StringProperty, BoolProperty, PointerProperty)

from . import _properties_, _functions_

class JK_OT_Add_Armature_Stage(bpy.types.Operator):
    """Adds a new armature stage"""
    bl_idname = "jk.add_armature_stage"
    bl_label = "Add Stage"
    
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
            # put them together and parent to master...
            copy.data, copy.parent = data, master
            # name the object and data after the master and stage we are adding...
            copy.name = master.name + " - " + self.Stage
            copy.data.name = master.name + " - " + self.Stage
            # don't want either to get deleted on save/load... (unless their master has been deleted)
            copy.use_fake_user, copy.data.use_fake_user, copy.data.AES.Is_master = True, True, False
            # add to the stages collection...
            new_stage = AES.Stages.add()
            new_stage.name, new_stage.Parent, new_stage.Armature = self.Stage, self.Parent, copy.name
            # if this is the source stage...
            if self.Parent == "":
                # master wants its stage variables set...
                master.data.AES.Last = self.Stage
                master.data.AES.Stage = self.Stage
            # if we are inserting the stage...
            if self.Insert:
                print(self.Stage, self.Parent, [s for s in AES.Stages if (s.Parent == self.Parent and s.name != self.Stage)])
                # iterate over all the parents children... (but not the stage we just added)
                for child in [s for s in AES.Stages if (s.Parent == self.Parent and s.name != self.Stage)]:
                    # and re-parent them to the new inserted stage...
                    print(child.Parent)
                    child.Parent = self.Stage
                    print(child.Parent) 
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
            bone = context.active_bone
            settings = stage.Bones[bone.name]
            # for each bone on this stage...
            for bone in stage.Bones:
                # if it's selected...
                if bone.name in bpy.context.selected_bones:
                    # set the relevant push settings by mode...
                    if master.mode == 'POSE':
                        bone.Push_pose = settings.Push_pose
                        bone.Pose.Push_pose = settings.Pose.Push_pose
                        bone.Pose.Push_group = settings.Pose.Push_group
                        bone.Pose.Push_ik = settings.Pose.Push_ik
                        bone.Pose.Push_deform = settings.Pose.Push_deform
                        bone.Pose.Push_constraints = settings.Pose.Push_constraints
                        bone.Pose.Push_drivers = settings.Pose.Push_drivers
                    elif master.mode == 'EDIT':
                        bone.Push_edit = settings.Push_edit
                        bone.Edit.Push_transforms = settings.Edit.Push_transforms
                        bone.Edit.Push_bendy_bones = settings.Edit.Push_bendy_bones
                        bone.Edit.Push_relations = settings.Edit.Push_relations
                        bone.Edit.Push_deform = settings.Edit.Push_deform
        return {'FINISHED'}

# push operator...

# pull operator...

# add control constraints...

# add automatic control constraints...

class JK_OT_Apply_Posing(bpy.types.Operator):
    """Applies armature pose to rest with meshes"""
    bl_idname = "jk.apply_posing"
    bl_label = "Remove Stage"
    
    Bool: StringProperty(name="Name", description="Name of the stage that should be removed", 
        default="", maxlen=1024)
        
    def execute(self, context):
        armature = bpy.context.object
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        # iterate through all objects...
        for obj in bpy.data.objects:
            # if it's a mesh...
            if obj.type == 'MESH':
                # iterate through it's modifiers...
                for modifier in obj.modifiers:
                    # if it's an armature modifier targeting the retarget target...
                    if modifier.type == 'ARMATURE' and modifier.object == armature:
                        modifier.name = "Armature"
                        # apply and re-add armature modifiers...
                        bpy.context.view_layer.objects.active = obj
                        bpy.ops.object.modifier_apply(modifier="Armature")
                        modifier = obj.modifiers.new(type='ARMATURE', name="Armature")
                        modifier.object = armature              
        # make the armature active again...
        bpy.context.view_layer.objects.active = armature
        # go into pose mode...
        bpy.ops.object.mode_set(mode='POSE')
        # apply the pose...
        bpy.ops.pose.armature_apply(selected=False)
        # then iterate over the pose bones...
        for p_bone in armature.pose.bones:
            # remove all the constraints
            for constraint in p_bone.constraints:
                if constraint.name != "MECHANISM - Copy Transform":
                    p_bone.constraints.remove(constraint)
            # remove any drivers the bone might have...
            for driver in [d for d in armature.animation_data.drivers if ('"%s"' % p_bone.name) in d.data_path]:
                armature.animation_data.drivers.remove(driver)
        return {'FINISHED'}
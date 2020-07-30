import bpy
from . import _functions_
from bpy.props import (BoolProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty) 

class JK_AAR_Pose_Bone_Props(bpy.types.PropertyGroup):

    Is_bound: BoolProperty(name="Is Bound", description="Is this armature currently bound to another for retargeting",
        default=False, options=set())
    
    def Update_Hide_Binding(self, context):
        source = bpy.context.object
        target = source.data.AAR.Target
        sa_bones, ta_bones = source.data.bones, target.data.bones
        ta_bones[self.Target].hide = self.Hide_target
        sa_bones[self.Retarget].hide = self.Hide_retarget

    Hide_target: BoolProperty(name="Hide Target", description="Hide the target bone we are taking the action from",
        default=True, options=set(), update=Update_Hide_Binding)

    Hide_retarget: BoolProperty(name="Hide Binding", description="Hide the retarget bone we are binding source bones to",
        default=True, options=set(), update=Update_Hide_Binding)
    
    Retarget: StringProperty(name="Retarget Bone", description="The target bone to take animation from", default="", maxlen=1024)

    def Update_Target(self, context):
        source = bpy.context.object
        target = source.data.AAR.Target
        # if the new target exists...
        if self.Target in target.data.bones:
            # check if this bone is already bound to a target...
            if self.Is_bound:
                # if it is then rebind it to the new target...
                _functions_.Rebind_Pose_Bone(source, target, self.Retarget, self.Target)
            else:
                # else it's needs a new binding...
                _functions_.Bind_Pose_Bone(source, target, self.name, self.Target)
        else:
            # and if the target was invalid unbind it...
            _functions_.Unbind_Pose_Bone(source, self.name, self.Retarget)

    Target: StringProperty(name="Target", description="The target bone to take animation from", 
        default="", maxlen=1024, update=Update_Target)

class JK_AAR_Offset_Action_Slot_Props(bpy.types.PropertyGroup):

    Armature: PointerProperty(type=bpy.types.Armature)

    Action: PointerProperty(type=bpy.types.Action, poll=_functions_.Action_Poll)

    Use: BoolProperty(name="Use Action", description="Use this target action with this offset action",
        default=True, options=set())

    Bake_step: IntProperty(name="Bake Step", default=1, min=1)

    Selected: BoolProperty(name="Only Selected", description="Only bake selected bones",
        default=False, options=set())

class JK_AAR_Offset_Slot_Props(bpy.types.PropertyGroup):
    
    Armature: PointerProperty(type=bpy.types.Armature)
    
    Action: PointerProperty(type=bpy.types.Action)

    Use: BoolProperty(name="Use Offset", description="Use this offset",
        default=True, options=set())

    def Action_Update(self, context):
        target = bpy.context.object.data.AAR.Target
        target.animation_data.action = self.Actions[self.Active].Action
        if self.Actions[self.Active].Action:
            self.Actions[self.Active].Action.use_fake_user = True
    
    Active: IntProperty(name="Active", default=0, update=Action_Update)
    
    Actions: CollectionProperty(type=JK_AAR_Offset_Action_Slot_Props)

class JK_AAR_Armature_Props(bpy.types.PropertyGroup):
    
    Is_bound: BoolProperty(name="Is Bound", description="Is this armature currently bound to another for retargeting",
        default=False, options=set())

    Is_target: BoolProperty(name="Is Target", description="Is this armature currently the the target of another for retargeting",
        default=False, options=set())
    
    def Target_Poll(self, object):
        return object.type == 'ARMATURE' and object != bpy.context.object 

    def Target_Update(self, context):
        source = bpy.context.object
        if self.Target != None:
            if len(self.Pose_bones) > 0:
                self.Pose_bones.clear()
            # add a property group entry for every pose bone
            for sp_bone in source.pose.bones:
                gp_bone = self.Pose_bones.add()
                gp_bone.name = sp_bone.name
            # register the source as bound...
            self.Is_bound = True
        else:
            for gp_bone in self.Pose_bones:
                if gp_bone.Is_bound:
                    _functions_.Unbind_Pose_Bone(source, gp_bone.name, gp_bone.Retarget)
            self.Pose_bones.clear()
            self.Is_bound = False

    Target: PointerProperty(name="Target", type=bpy.types.Object, poll=Target_Poll, update=Target_Update)

    Mute_cons: BoolProperty(name="Mute Constraints", description="Mute existing constraints. (May increase accuracy of baking the retarget)",
        default=True, options=set())

    Hide_target_bones: BoolProperty(name="Hide Target Bones", description="Hide the target bones we are taking the action from",
        default=True, options=set())

    Hide_retarget_bones: BoolProperty(name="Hide Retarget Bones", description="Hide the retarget bones we are binding source bones to",
        default=True, options=set())

    def Offset_Update(self, context):
        source = bpy.context.object
        source.animation_data.action = self.Offsets[self.Offset].Action
        if self.Offsets[self.Offset].Action:
            self.Offsets[self.Offset].Action.use_fake_user = True
    
    Offset: IntProperty(name="Active Offset", default=0, update=Offset_Update)
    
    Offsets: CollectionProperty(type=JK_AAR_Offset_Slot_Props)

    Pose_bones: CollectionProperty(type=JK_AAR_Pose_Bone_Props)




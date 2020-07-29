import bpy
from . import _functions_
from bpy.props import (BoolProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty) 

class JK_AAR_Pose_Bone_Props(bpy.types.PropertyGroup):

    Is_bound: BoolProperty(name="Is Bound", description="Is this armature currently bound to another for retargeting",
        default=False, options=set())
    
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
            _functions_.Unbind_Pose_Bone(source, self.name)

    Target: StringProperty(name="Target Bone", description="The target bone to take animation from", 
        default="", maxlen=1024, update=Update_Target)

# because collection properties can't actually be subclasses of bpy.types.ID? (docs say they can but then they don't register)
class JK_AAR_Action_Pointer(bpy.types.PropertyGroup):
    
    Action: PointerProperty(type=bpy.types.Action)

class JK_AAR_Action_Props(bpy.types.PropertyGroup):

    Is_offset: BoolProperty(name="Is Offset", description="Is this an offset action to be used when baking retargets",
        default=False, options=set())
    
    All_actions: BoolProperty(name="All Actions", description="Bake all actions in this offsets target action list",
        default=False, options=set())
    
    def Action_Poll(self, action):
        is_valid = False
        target = bpy.context.object.data.AAR.Target
        for fc in action.fcurves:
            if any(b.name in fc.data_path for b in target.data.bones):
                is_valid = True
                break
        return is_valid

    def Action_Update(self, context):
        target = bpy.context.object.data.AAR.Target
        target.animation_data.action = self.Action
    
    Action: PointerProperty(type=bpy.types.Action, poll=Action_Poll, update=Action_Update)

    Actions: CollectionProperty(type=JK_AAR_Action_Pointer)

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
            if len(self.Offsets) == 0:
                _functions_.Add_Offset_Action(source)
        else:
            for gp_bone in self.Pose_bones:
                if gp_bone.Is_bound:
                    _functions_.Unbind_Pose_Bone(source, gp_bone.name)
            self.Pose_bones.clear()
            self.Is_bound = False

    Target: PointerProperty(name="Target", type=bpy.types.Object, poll=Target_Poll, update=Target_Update)

    Use_cons: BoolProperty(name="Use Constraints", description="Use existing constraints with retarget. (May reduce accuracy of baking the retarget)",
        default=True, options=set())

    Hide_target_bones: BoolProperty(name="Hide Target Bones", description="Hide the target bones we are taking the action from",
        default=True, options=set())

    Hide_retarget_bones: BoolProperty(name="Hide Retarget Bones", description="Hide the retarget bones we are binding source bones to",
        default=True, options=set())

    def Offset_Poll(self, action):
        return any(action == o.Action for o in self.Offsets)

    def Offset_Update(self, context):
        source = bpy.context.object
        source.animation_data.action = self.Offset
    
    Offset: PointerProperty(name="Offset", type=bpy.types.Action, poll=Offset_Poll, update=Offset_Update)
    
    Offsets: CollectionProperty(type=JK_AAR_Action_Pointer)

    Pose_bones: CollectionProperty(type=JK_AAR_Pose_Bone_Props)

class JK_AAR_Object_Props(bpy.types.PropertyGroup):

    Is_bound: BoolProperty(name="Is Bound", description="Is this object currently bound to another for retargeting",
        default=False, options=set())

    Is_target: BoolProperty(name="Is Target", description="Is this object currently the the target of another for retargeting",
        default=False, options=set())

    




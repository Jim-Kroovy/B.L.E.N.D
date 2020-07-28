import bpy
from bpy.props import (BoolProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty) 

class JK_AAR_Bone_Props(bpy.types.PropertyGroup):

    Target: StringProperty(name="Target", description="The target bone to take animation from", default="", maxlen=1024)

    Use_loc: BoolProperty(name="Use Location", description="Use location from target",
        default=True, options=set())

    Offset_loc: FloatVectorProperty(name="Head", description="Head location", size=3, default=(0.0, 0.0, 0.0))
    
    Use_rot: BoolProperty(name="Use Rotation", description="Use rotation from target",
        default=True, options=set())

    Offset_rot: FloatVectorProperty(name="Head", description="Head location", size=3, default=(0.0, 0.0, 0.0))

    Use_sca: BoolProperty(name="Use Scale", description="Use scale from target",
        default=True, options=set())

    Offset_sca: FloatVectorProperty(name="Head", description="Head location", size=3, default=(0.0, 0.0, 0.0))

class JK_AAR_Action_Props(bpy.types.PropertyGroup):

    Is_offset: BoolProperty(name="Is Offset", description="Is this an offset action to be used when baking retargets",
        default=False, options=set())
    
    All_actions: BoolProperty(name="All Actions", description="Batch retarget all actions in the target action list",
        default=False, options=set())
    
    def Action_Poll(self, action):
        return action in self.Targets

    def Action_Update(self, context):
        armature = bpy.context.object.data.AAR.Target
        armature.animation_data.action = self.Target
    
    Action: PointerProperty(type=bpy.types.Action, poll=Action_Poll, update=Action_Update)

    Actions: CollectionProperty(type=bpy.types.Action)

class JK_AAR_Armature_Props(bpy.types.PropertyGroup):

    #Retarget_type: EnumProperty()
    
    Is_bound: BoolProperty(name="Is Bound", description="Is this armature currently bound to another for retargeting",
        default=False, options=set())
    
    #Target: StringProperty(name="Target", description="The armature to making bindings with", default="", maxlen=1024)
    
    def Target_Poll(self, object):
        return object.type == 'ARMATURE'

    Target: PointerProperty(name="Target", type=bpy.types.Object, poll=Target_Poll)

    Use_cons: BoolProperty(name="Use Constraints", description="Use existing constraints with retarget. (May reduce accuracy of baking the retarget)",
        default=True, options=set())

    Hide_target_bones: BoolProperty(name="Hide Target Bones", description="Hide the target bones we are taking the action from",
        default=True, options=set())

    Hide_retarget_bones: BoolProperty(name="Hide Retarget Bones", description="Hide the retarget bones we are binding source bones to",
        default=True, options=set())

    def Offset_Poll(self, action):
        return action in self.Offsets

    def Offset_Update(self, context):
        armature = self.id_data
        armature.animation_data.action = self.Offset
    
    Offset: PointerProperty(name="Active Offset", type=bpy.types.Action, poll=Offset_Poll, update=Offset_Update)
    
    Offsets: CollectionProperty(type=bpy.types.Action)

class JK_AAR_Object_Props(bpy.types.PropertyGroup):

    Is_bound: BoolProperty(name="Is Bound", description="Is this object currently bound to another for retargeting",
        default=False, options=set())

    Is_target: BoolProperty(name="Is Source", description="Is this object currently the the target of another for retargeting",
        default=False, options=set())

    




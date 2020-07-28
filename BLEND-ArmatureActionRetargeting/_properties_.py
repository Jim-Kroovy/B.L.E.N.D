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

class JK_AAR_Armature_Props(bpy.types.PropertyGroup):

    Is_bound: BoolProperty(name="Is Bound", description="Is this armature currently bound to another for retargeting",
        default=False, options=set())
    
    Target: StringProperty(name="Target", description="The armature to making bindings with", default="", maxlen=1024)

    Use_ik: BoolProperty(name="Use Inverse Kinematics", description="Use existing IK to retarget. (May reduce accuracy of baking the retarget)",
        default=True, options=set())

    Use_cons: BoolProperty(name="Use Constraints", description="Use existing constraints with retarget. (May reduce accuracy of baking the retarget)",
        default=True, options=set())

    Hide_target_bones: BoolProperty(name="Hide Target Bones", description="Hide the target bones we are taking the action from",
        default=True, options=set())

    Hide_retarget_bones: BoolProperty(name="Hide Retarget Bones", description="Hide the retarget bones we are binding source bones to",
        default=True, options=set())




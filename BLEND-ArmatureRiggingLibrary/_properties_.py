import bpy
from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty) 
from . import _functions_

class JK_ARL_Pivot_Bone_Props(bpy.types.PropertyGroup):

    Type: EnumProperty(name="Type", description="The type of pivot bone",
        items=[('SKIP', 'Skip Parent', "Pivot bone is parented to the source bones parents parent"),
        ('SHARE', 'Share Parent', "Pivot bone is parented to the source bones parent")],
        default='SKIP')
    
    Is_parent: BoolProperty(name="Is Parent", description="Source bone is parented to the pivot", default=False)
    
    Source: StringProperty(name="Bone",description="The bone this pivot bone was created from",
        default="", maxlen=1024)

    Parent: StringProperty(name="Bone",description="The parent of the bone this pivot bone was created from",
        default="", maxlen=1024)

class JK_ARL_Floor_Bone_Props(bpy.types.PropertyGroup):

    Bone: StringProperty(name="Bone",description="The bone this floor target was created for",
        default="", maxlen=1024)

class JK_ARL_Limit_Props(bpy.types.PropertyGroup):

    Use: BoolProperty(name="Use", description="Use this limit", default=False)

    Min: FloatProperty(name="Min", description="Minimum limit", default=0.0, subtype='ANGLE', unit='ROTATION')

    Max: FloatProperty(name="Max", description="Maximum limit", default=0.0, subtype='ANGLE', unit='ROTATION')

class JK_ARL_Twist_Bone_Props(bpy.types.PropertyGroup):

    Type: EnumProperty(name="Type", description="The type of twist bone to add",
        items=[('HEAD_HOLD', 'Head Hold', "Holds deformation at the head of the bone back by tracking to the target. (eg: Upper Arm Twist)"),
        ('TAIL_FOLLOW', 'Tail Follow', "Follows deformation at the tail of the bone by copying the Y rotation of the target. (eg: Lower Arm Twist)")],
        default='HEAD_HOLD')

    Target: StringProperty(name="Target", description="The targets bones name", default="", maxlen=1024)
    
    Parent: StringProperty(name="Parent", description="The original parent of the twist bone. (if any)", default="", maxlen=1024)
    
    Float: FloatProperty(name="Float", description="Either the head vs tail or influence depending on the twist type", 
        default=1.0, min=0.0, max=1.0, subtype='FACTOR')

    Has_pivot: BoolProperty(name="Use Pivot", description="Does this twist bone have a pivot bone to define its limits?", default=False)

    Limits_x: PointerProperty(type=JK_ARL_Limit_Props)

    Limits_y: PointerProperty(type=JK_ARL_Limit_Props)

    Limits_z: PointerProperty(type=JK_ARL_Limit_Props)

class JK_ARL_Chain_Target_Bone_Props(bpy.types.PropertyGroup):

    Source: StringProperty(name="Source",description="The bone that we created the target from",
        default="", maxlen=1024)

    Target: StringProperty(name="Target", description="The actual target bone. (if parented)",
        default="", maxlen=1024)

    Local: StringProperty(name="Local",description="The local bone that controls the IK chain",
        default="", maxlen=1024)

    Control: StringProperty(name="Control", description="Name of the bone that controls the roll mechanism. (if any)", default="", maxlen=1024)

    Pivot: StringProperty(name="Pivot", description="Name of the bone used to pivot the target. (eg: bone at the ball of the foot)", 
        default="", maxlen=1024)

    Root: StringProperty(name="IK Root",description="The IK root bone. (if any)", default="", maxlen=1024)

class JK_ARL_Chain_Pole_Bone_Props(bpy.types.PropertyGroup):

    Source: StringProperty(name="Source",description="The bone that we created the pole from",
        default="", maxlen=1024)
    
    Local: StringProperty(name="Local Pole",description="The local pole bones name",default="",maxlen=1024)
    
    def Axis_Update(self, context):
        self.Angle = _functions_.Get_Pole_Angle(self.Axis)
    
    Axis: EnumProperty(name="Pole Axis", description="The local axis of the second bone that the pole target is created along. (pole angle might need to be adjusted)",
        items=[('X', 'X', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X', "", "CON_LOCLIKE", 1),
        ('Z', 'Z', "", "CON_LOCLIKE", 2),
        ('Z_NEGATIVE', '-Z', "", "CON_LOCLIKE", 3)],
        default='X', update=Axis_Update)

    Angle: FloatProperty(name="Pole Angle", description="The angle of the IK pole target. (degrees)", 
        default=0.0,subtype='ANGLE')

    Distance: FloatProperty(name="Pole Distance", description="The distance the pole target is from the IK parent. (meters)", default=0.25)

    Root: StringProperty(name="IK Root",description="The IK root bone. (if any)",default="",maxlen=1024)

class JK_ARL_Chain_Bone_Props(bpy.types.PropertyGroup):

    Gizmo: StringProperty(name="Gizmo", description="The gizmo bone that the chain bone follows", default="", maxlen=1024)

    Stretch: StringProperty(name="Stretch", description="The stretch bone that the gizmo bone follows", default="", maxlen=1024)

    Is_owner: BoolProperty(name="Is Owner",description="Is this bone the owner of the IK constraint",
        default=False)
    
    Has_target: BoolProperty(name="Has Target",description="Should this chain bone have a target. (Only used by Spline chains)",
        default=False)

class JK_ARL_Chain_Spline_Props(bpy.types.PropertyGroup):
    
    Use_divisions: BoolProperty(name="Use Divisions", description="Use a subdivsion of targets instead of creating targets from existing bones",
        default=False)
    
    Divisions: IntProperty(name="Divisions", description="The number of divisions in the curve and how many controls to create. (Not including start and end)", 
        default=1, min=1)
    
    Use_start: BoolProperty(name="Use Start",description="Include the start bone in the spline chain",
        default=True)

    Use_end: BoolProperty(name="Use End",description="Include the end bone in the spline chain",
        default=True)

class JK_ARL_Chain_Forward_Props(bpy.types.PropertyGroup):

    Loc: BoolVectorProperty(name="Location", description="Which axes are copied",
        default=(False, False, False), size=3, subtype='EULER')

    Rot: BoolVectorProperty(name="Rotation", description="Which axes are copied",
        default=(False, False, False), size=3, subtype='EULER')

    Sca: BoolVectorProperty(name="Scale", description="Which axes are copied",
        default=(False, False, False), size=3, subtype='EULER')
    
    Target: EnumProperty(name="Target Space", description="Space that target is evaluated in",
        items=[('WORLD', "World Space", ""), ('POSE', "Pose Space", ""), 
            ('LOCAL', "Local Space", ""), ('LOCAL_WITH_PARENT', "Local With Parent Space", "")],
        default='LOCAL')

    Owner: EnumProperty(name="Owner Space", description="Space that owner is evaluated in",
        items=[('WORLD', "World Space", ""), ('POSE', "Pose Space", ""), 
            ('LOCAL', "Local Space", ""), ('LOCAL_WITH_PARENT', "Local With Parent", "")],
        default='LOCAL')

class JK_ARL_Chain_Props(bpy.types.PropertyGroup):

    Parent: StringProperty(name="Parent", description="The bone at the beginning but not included in the chain. (if any)", 
        default="", maxlen=1024)

    Type: EnumProperty(name="Type", description="The type of limb IK chain",
        items=[('OPPOSABLE', 'Opposable', "A simple IK chain of 2 bones with a pole target. (Generally used by arms)"),
        ('SCALAR', 'Scalar', "An IK chain of any length controlled by scaling, rotating a parent of the target. (Generally used for fingers)"),
        ('PLANTIGRADE', 'Plantigrade', "An opposable IK chain of 2 bones with a pole target and standard foot rolling controls. (Generally used by human legs)"),
        ('DIGITIGRADE', 'Digitigrade', "A scalar IK chain of 3 bones with a pole target and special foot controls. (Generally used by animal legs)"),
        ('SPLINE', 'Spline', "A spline IK chain of any length controlled by a curve that's manipulated with target bones. (Generally used by tails/spines)"),
        ('FORWARD', 'Forward', "An FK chain of any length where the chain copies loc/rot/scale of a parent/target. (Generally an alternative used for fingers/tails)")],
        default='OPPOSABLE')

    Mode: EnumProperty(name="Mode", description="Which mode of IK is currently active",
        items=[('NONE', 'Only IK', "Only use IK"),
            ('SWITCH', 'Switchable', "IK and FK can be switched between while keyframing"),
            ('AUTO', 'Automatic', "IK and FK are switched automatically depending on bone selection")],
        default='NONE')

    Side: EnumProperty(name="Side", description="Which side of the armature is this chain on",
        items=[('NONE', 'None', "Not on any side, probably central"),
            ('LEFT', 'Left', "Chain is on the left side"),
            ('RIGHT', 'Right', "Chain is on the right side")],
        default='NONE')

    Limb: EnumProperty(name="Limb", description="What appendage this chain is for. (mostly used for naming and organisation)",
        items=[('ARM', 'Arm', "This is meant to be an arm chain"),
            ('DIGIT', 'Digit', "This is meant to be a digit chain. (Toes, Fingers and Thumbs)"),
            ('LEG', 'Leg', "This is meant to be a leg chain"),
            ('SPINE', 'Spine', "This is meant to be a spine chain"),
            ('TAIL', 'Tail', "This is meant to be a tail chain"),
            ('WING', 'Wing', "This is meant to be a wing chain")],
        default='ARM')

    Last_fk: BoolProperty(name="Last FK",description="The last 'Use FK' boolean",
        default=False)
    
    Use_fk: BoolProperty(name="Use FK",description="Switch between IK vs FK for this IK chain",
        default=False)

    Auto_key: BoolProperty(name="Auto Key FK",description="Automatically keyframe switching between IK and FK",
        default=False)
    
    Bones: CollectionProperty(type=JK_ARL_Chain_Bone_Props)
    
    Pole: PointerProperty(type=JK_ARL_Chain_Pole_Bone_Props)

    Targets: CollectionProperty(type=JK_ARL_Chain_Target_Bone_Props)

    Spline: PointerProperty(type=JK_ARL_Chain_Spline_Props)

    Forward: PointerProperty(type=JK_ARL_Chain_Forward_Props)

class JK_ARL_Affix_Props(bpy.types.PropertyGroup):

    Gizmo: StringProperty(name="Gizmo", description="The prefix of hidden bones that are used to indirectly create movement", 
        default="GB_", maxlen=1024)

    Control: StringProperty(name="Control", description="The prefix of control bones that are used to directly create movement", 
        default="CB_", maxlen=1024)

    Pivot: StringProperty(name="Pivot", description="The prefix of control bones that are used to offset constraints, inherit transforms and rotate around", 
        default="PB_", maxlen=1024)

    Target_arm: StringProperty(name="Arm Target", description="The prefix of arm chain targets", 
        default="AT_", maxlen=1024)

    Target_digit: StringProperty(name="Digit Target", description="The prefix of digit chain targets", 
        default="DT_", maxlen=1024)

    Target_leg: StringProperty(name="Arm Target", description="The prefix of leg chain targets", 
        default="LT_", maxlen=1024)

    Target_spine: StringProperty(name="Spine Target", description="The prefix of spline chain targets", 
        default="ST_", maxlen=1024)

    Target_tail: StringProperty(name="Tail Target", description="The prefix of tail chain targets", 
        default="TT_", maxlen=1024)

    Target_wing: StringProperty(name="Wing Target", description="The prefix of wing chain targets", 
        default="WT_", maxlen=1024)

    Target_floor: StringProperty(name="Floor Target", description="The prefix of floor targets", 
        default="FT_", maxlen=1024)

    Stretch: StringProperty(name="STRETCH_", description="The affix given to bones that stretch", 
        default="STRETCH_", maxlen=1024)

    Roll: StringProperty(name="ROLL_", description="The affix given to bones that roll", 
        default="ROLL_", maxlen=1024)
    
    Local: StringProperty(name="LOCAL_", description="The affix given to bones that hold local transforms", 
        default="LOCAL_", maxlen=1024)

class JK_ARL_Rigging_Library_Props(bpy.types.PropertyGroup):
    
    Pivots: CollectionProperty(type=JK_ARL_Pivot_Bone_Props)

    Floors: CollectionProperty(type=JK_ARL_Floor_Bone_Props)

    Twists: CollectionProperty(type=JK_ARL_Twist_Bone_Props)

    Chains: CollectionProperty(type=JK_ARL_Chain_Props)

    Affixes: PointerProperty(type=JK_ARL_Affix_Props)

    



    

    


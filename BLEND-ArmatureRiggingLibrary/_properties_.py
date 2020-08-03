import bpy
from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty) 
from . import _functions_
class JK_ARL_Pivot_Bone_Props(bpy.types.PropertyGroup):

    Bone: StringProperty(name="Bone",description="The bone this pivot bone was created from",
        default="", maxlen=1024)

    Parent: StringProperty(name="Bone",description="The parent of bone this pivot bone was created from",
        default="", maxlen=1024)

class JK_ARL_Camera_Bone_Props(bpy.types.PropertyGroup):

    Type: EnumProperty(name="Type", description="The type of camera bone to add",
        items=[('FP', 'First Person', "A first person camera with stabilized movement"),
        ('TP', 'Third Person', "A third person camera with stabilized movement")],
        default='HEAD_HOLD')

    #Boom:

    #Spline:

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
    
class JK_ARL_IK_Target_Bone_Props(bpy.types.PropertyGroup):

    Control: StringProperty(name="Control",description="The bone that controls the IK target. (If there isn't one this will be equal to the target)",
        default="", maxlen=1024)

    Local: StringProperty(name="Local Control",description="The local bone that controls the IK chain",
        default="", maxlen=1024)

    Root: StringProperty(name="IK Root",description="The IK root bone. (if any)",default="",maxlen=1024)

class JK_ARL_IK_Pole_Bone_Props(bpy.types.PropertyGroup):

    Local: StringProperty(name="Local Pole",description="The local IK pole target bones name",default="",maxlen=1024)
    
    Axis:  EnumProperty(name="Pole Axis", description="The local axis of the second bone that the pole target is created along. (pole angle might need to be adjusted)",
        items=[('X', 'X', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X', "", "CON_LOCLIKE", 1),
        ('Z', 'Z', "", "CON_LOCLIKE", 2),
        ('Z_NEGATIVE', '-Z', "", "CON_LOCLIKE", 3)],
        default='X')

    Angle: FloatProperty(name="Pole Angle", description="The angle of the IK pole target. (degrees)", 
        default=0.0,subtype='ANGLE')

    Distance: FloatProperty(name="Pole Distance", description="The distance the pole target is from the IK parent. (meters)", default=0.25)

    Root: StringProperty(name="IK Root",description="The IK root bone. (if any)",default="",maxlen=1024)

class JK_ARL_IK_Foot_Bone_Props(bpy.types.PropertyGroup):
    
    Main_axis:  EnumProperty(name="Main Axis", description="The main axis the foot bone rotates around. (The local axis that rotates the deformation down)",
        items=[('X', 'X', "", "CON_ROTLIKE", 0),
        ('X_NEGATIVE', '-X', "", "CON_ROTLIKE", 1),
        ('Z', 'Z', "", "CON_ROTLIKE", 2),
        ('Z_NEGATIVE', '-Z', "", "CON_ROTLIKE", 3)],
        default='X')
    
    Control: StringProperty(name="Control Name", description="Name of the bone that controls the foot roll mechanism", default="", maxlen=1024)

    Pivot: StringProperty(name="Pivot", description="Name of the bone used to pivot the end of chain. (eg: bone at the ball of the foot)", 
        default="", maxlen=1024)

    Pivot_axis:  EnumProperty(name="Pivot Axis", description="The main axis the pivot bone rotates around. (The local axis that rotates the deformation down)",
        items=[('X', 'X', "", "CON_ROTLIKE", 0),
        ('X_NEGATIVE', '-X', "", "CON_ROTLIKE", 1),
        ('Z', 'Z', "", "CON_ROTLIKE", 2),
        ('Z_NEGATIVE', '-Z', "", "CON_ROTLIKE", 3)],
        default='X')

class JK_ARL_IK_Chain_Bone_Props(bpy.types.PropertyGroup):

    Gizmo: StringProperty(name="Gizmo", description="The gizmo bone that the chain bone follows", default="", maxlen=1024)

    Stretch: StringProperty(name="Stretch", description="The stretch bone that the gizmo bone follows", default="", maxlen=1024)

    Has_target: BoolProperty(name="Has Target",description="Should this chain bone have a target",
        default=False)

    Is_start: BoolProperty(name="Is Start",description="Is this the start of the IK chain",
        default=False)

    Is_end: BoolProperty(name="Is End",description="Is this the end of the IK chain",
        default=False)

class JK_ARL_IK_Spline_Props(bpy.types.PropertyGroup):

    Divisions: IntProperty(name="Divisions", description="The number of divisions in the curve and how many controls to create. (Not including start and end. Cannot be greater than number of bones)", default=1)

    Axis: EnumProperty(name="Main Axis", description="The the local main axis of the chain",
        items=[('X', 'X', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X', "", "CON_LOCLIKE", 1),
        ('Y', 'Y', "", "CON_LOCLIKE", 2),
        ('Y_NEGATIVE', '-Y', "", "CON_LOCLIKE", 3),
        ('Z', 'Z', "", "CON_LOCLIKE", 4),
        ('Z_NEGATIVE', '-Z', "", "CON_LOCLIKE", 5)],
        default='X')
        
    Distance: FloatProperty(name="Curve Distance", description="The distance the curve and bones are from the chain. (in meters)", default=0.25)

class JK_ARL_IK_Chain_Props(bpy.types.PropertyGroup):

    Parent: StringProperty(name="Parent", description="The bone at the beginning but not included in the chain. (if any)", 
        default="", maxlen=1024)

    Type: EnumProperty(name="Type", description="The type of limb IK chain",
        items=[('SCALAR', 'Scalar', "An IK chain of any length controlled by scaling, rotating a parent of the target. (Generally used for fingers)"),
        ('OPPOSABLE', 'Opposable', "A simple IK chain of 2 bones with a pole target. (Generally used by arms)"),
        ('PLANTIGRADE', 'Plantigrade', "An IK chain of 2 bones with a pole target and standard foot rolling controls. (Generally used by human legs)"),
        ('DIGITIGRADE', 'Digitigrade', "An IK chain of 2 bones with a pole target and special foot controls. (Generally used by animal legs)"),
        ('SPLINE', 'Spline', "A spline IK chain of any length controlled by a curve that's manipulated with target bones. (Generally used by tails/spines)")],
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

    Limb: EnumProperty(name="Side", description="Which side of the armature is this chain on",
        items=[('ARM', 'Arm', "This is meant to be an arm IK chain"),
            ('LEG', 'Leg', "This is meant to be a leg IK chain"),
            ('DIGIT', 'Digit', "This is meant to be a digit IK chain. (Toes, Fingers and Thumbs)")],
        default='ARM')

    Use_fk: BoolProperty(name="Use FK",description="Switch between IK vs FK for this IK chain",
        default=False)

    Auto_key: BoolProperty(name="Auto Key FK",description="Automatically keyframe switching between IK and FK",
        default=False)
    
    Bones: CollectionProperty(type=JK_ARL_IK_Chain_Bone_Props)
    
    Pole: PointerProperty(type=JK_ARL_IK_Pole_Bone_Props)

    Targets: CollectionProperty(type=JK_ARL_IK_Target_Bone_Props)

    Foot: PointerProperty(type=JK_ARL_IK_Foot_Bone_Props)

    Spline: PointerProperty(type=JK_ARL_IK_Spline_Props)

class JK_ARL_Rigging_Affix_Props(bpy.types.PropertyGroup):

    Gizmo: StringProperty(name="Gizmo", description="The prefix of hidden bones that are used to indirectly create movement", 
        default="GB_", maxlen=1024)

    Control: StringProperty(name="Control", description="The prefix of control bones that are used to directly create movement", 
        default="CB_", maxlen=1024)

    Pivot: StringProperty(name="Pivot", description="The prefix of control bones that are used to offset constraints, inherit transforms and rotate around", 
        default="PB_", maxlen=1024)

    Target_arm: StringProperty(name="Arm Target", description="The prefix of arm IK targets", 
        default="AT_", maxlen=1024)

    Target_leg: StringProperty(name="Arm Target", description="The prefix of leg IK targets", 
        default="LT_", maxlen=1024)

    Target_spline: StringProperty(name="Spline Target", description="The prefix of spline IK targets", 
        default="ST_", maxlen=1024)

    Target_floor: StringProperty(name="Floor Target", description="The prefix of floor targets", 
        default="FT_", maxlen=1024)

    Stretch: StringProperty(name="STRETCH_", description="The affix given to bones that stretch", 
        default="STRETCH_", maxlen=1024)

    Roll: StringProperty(name="ROLL_", description="The affix given to bones that roll", 
        default="ROLL_", maxlen=1024)
    
    Local: StringProperty(name="LOCAL_", description="The affix given to bones that hold local transforms", 
        default="ROLL_", maxlen=1024)

class JK_ARL_Rigging_Library_Props(bpy.types.PropertyGroup):
    
    #Cameras: CollectionProperty(type=JK_ARL_Camera_Bone_Props)
    
    Pivots: CollectionProperty(type=JK_ARL_Pivot_Bone_Props)

    Twists: CollectionProperty(type=JK_ARL_Twist_Bone_Props)

    Chains: CollectionProperty(type=JK_ARL_IK_Chain_Props)

    Affixes: PointerProperty(type=JK_ARL_Rigging_Affix_Props)



    



    

    


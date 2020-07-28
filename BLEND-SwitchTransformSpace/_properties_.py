import bpy
from bpy.props import (EnumProperty, BoolProperty, StringProperty, CollectionProperty, FloatVectorProperty)

class JK_STS_Operator_Props(bpy.types.PropertyGroup):
    
    Mode_from: EnumProperty(name="From",description="The transform space we wish to switch from",
        items=[('LOCAL', 'Local Space', "Space from parent"),
        ('OBJECT', 'Object Space', "Space from object"),
        ('WORLD', 'World Space', "Space from world")],
        default='LOCAL')
    
    Mode_to: EnumProperty(name="To",description="The transform space we wish to switch too",
        items=[('LOCAL', 'Local Space', "Space from parent"),
        ('OBJECT', 'Object Space', "Space from object"),
        ('WORLD', 'World Space', "Space from world")],
        default='WORLD')
    
    Remove: BoolProperty(name="Remove Previous",description="Remove fcurves from previous transform space", default=False)
    
    Single: BoolProperty(name="Single Action", description="Only edit the selected action. (Edit all actions if False)", default=True)
    
    Selected: BoolProperty(name="Edit Selected Bones", description="Edit selected pose bone fcurves. (No bone fcurves will be edited if False)", default=False)
    
    Object: BoolProperty(name="Edit Object Curves", description="Edit object transform space curves. (If there are any)", default=False)

class JK_STS_Space_Props(bpy.types.PropertyGroup):

    space_mode: EnumProperty(name="From",description="The transform space we wish to switch from",
        items=[('LOCAL', 'Local Space', "Space from parent"),
        ('OBJECT', 'Object Space', "Space from object"),
        ('WORLD', 'World Space', "Space from world")],
        default='LOCAL')

    def Update_Location(self, context):
        if self.id_data.rna_type.name == "Pose Bone":
            self.id_data.matrix.Translation = self.location
        elif self.id_data.rna_type.name == "Object":
            self.id_data.matrix_world.Translation = self.location
            #exec(self.name + ".matrix.Translation = self.location")

    location: bpy.props.FloatVectorProperty(name="Location", description="", default=(0.0, 0.0, 0.0), 
        precision=3, options={'ANIMATABLE'}, subtype= 'TRANSLATION', unit='NONE', size=3, 
        update=Update_Location, get=None, set=None)

    rotation_mode: EnumProperty(name="Rotation Mode",description="The rotation mode",
        items=[('QUATERNION', 'Quaternion (WXYZ)', "No Gimbal Lock"),
        ('XYZ', 'XYZ Euler', "XYZ Rotation Order - prone to Gimbal Lock (default)"),
        ('XZY', 'XZY Euler', "XZY Rotation Order - prone to Gimbal Lock"),
        ('YXZ', 'YXZ Euler', "YXZ Rotation Order - prone to Gimbal Lock"),
        ('YZX', 'YZX Euler', "YZX Rotation Order - prone to Gimbal Lock"),
        ('ZXY', 'ZXY Euler', "ZXY Rotation Order - prone to Gimbal Lock"),
        ('ZYX', 'ZYX Euler', "ZYX Rotation Order - prone to Gimbal Lock"),
        ('AXIS_ANGLE', 'Axis Angle', "Axis Angle (W+XYZ), defines a rotation around some axis defined by 3D-Vector")],
        default='QUATERNION')

    rotation_quaternion: bpy.props.FloatVectorProperty(name="Rotation", description="", default=(1.0, 0.0, 0.0, 0.0), 
        precision=3, options={'ANIMATABLE'}, subtype= 'QUATERNION', unit='NONE', size=4, 
        update=None, get=None, set=None)

    rotation_euler: bpy.props.FloatVectorProperty(name="Rotation", description="", default=(0.0, 0.0, 0.0), 
        precision=3, options={'ANIMATABLE'}, subtype= 'EULER', unit='NONE', size=3, 
        update=None, get=None, set=None)

    rotation_axis_angle: bpy.props.FloatVectorProperty(name="Rotation", description="", default=(0.0, 0.0, 0.0, 0.0), 
        precision=3, options={'ANIMATABLE'}, subtype= 'AXIS_ANGLE', unit='NONE', size=4, 
        update=None, get=None, set=None)
    
    def Update_Scale(self, context):
        if self.id_data.rna_type.name == "Pose Bone":
            if self.space_mode == 'WORLD':
                self.id_data.matrix.Scale = self.Scale
            elif self.space_mode == 'OBJECT':
                self.id_data.matrix.Scale = self.scale
        elif self.id_data.rna_type.name == "Object":
            self.id_data.matrix_world.Scale = self.scale
    
    scale: bpy.props.FloatVectorProperty(name="Scale", description="", default=(0.0, 0.0, 0.0), 
        precision=3, options={'ANIMATABLE'}, subtype= 'XYZ', unit='NONE', size=3, 
        update=None, get=None, set=None)     
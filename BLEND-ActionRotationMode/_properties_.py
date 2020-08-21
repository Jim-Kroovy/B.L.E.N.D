import bpy

from bpy.props import (EnumProperty, BoolProperty, StringProperty, CollectionProperty)

class JK_SRM_Operator_Props(bpy.types.PropertyGroup):
    
    Mode_from: EnumProperty(name="From",description="The rotation mode we wish to switch from",
        items=[('QUATERNION', 'Quaternion (WXYZ)', "No Gimbal Lock"),
        ('XYZ', 'XYZ Euler', "XYZ Rotation Order - prone to Gimbal Lock (default)"),
        ('XZY', 'XZY Euler', "XZY Rotation Order - prone to Gimbal Lock"),
        ('YXZ', 'YXZ Euler', "YXZ Rotation Order - prone to Gimbal Lock"),
        ('YZX', 'YZX Euler', "YZX Rotation Order - prone to Gimbal Lock"),
        ('ZXY', 'ZXY Euler', "ZXY Rotation Order - prone to Gimbal Lock"),
        ('ZYX', 'ZYX Euler', "ZYX Rotation Order - prone to Gimbal Lock"),
        ('AXIS_ANGLE', 'Axis Angle', "Axis Angle (W+XYZ), defines a rotation around some axis defined by 3D-Vector")],
        default='QUATERNION')
    
    Mode_to: EnumProperty(name="To",description="The rotation mode we wish to switch too",
        items=[('QUATERNION', 'Quaternion (WXYZ)', "No Gimbal Lock"),
        ('XYZ', 'XYZ Euler', "XYZ Rotation Order - prone to Gimbal Lock (default)"),
        ('XZY', 'XZY Euler', "XZY Rotation Order - prone to Gimbal Lock"),
        ('YXZ', 'YXZ Euler', "YXZ Rotation Order - prone to Gimbal Lock"),
        ('YZX', 'YZX Euler', "YZX Rotation Order - prone to Gimbal Lock"),
        ('ZXY', 'ZXY Euler', "ZXY Rotation Order - prone to Gimbal Lock"),
        ('ZYX', 'ZYX Euler', "ZYX Rotation Order - prone to Gimbal Lock"),
        ('AXIS_ANGLE', 'Axis Angle', "Axis Angle (W+XYZ), defines a rotation around some axis defined by 3D-Vector")],
        default='XYZ')
    
    Remove: BoolProperty(name="Remove Previous",description="Remove fcurves from previous rotation mode. (Does nothing if switching between euler orders)", default=False)
    
    Single: BoolProperty(name="Single Action", description="Only edit the selected action. (Edit all actions if False)", default=True)
    
    Selected: BoolProperty(name="Edit Selected Bones", description="Edit selected pose bone fcurves. (No bone fcurves will be edited if False)", default=False)
    
    Object: BoolProperty(name="Edit Object Curves", description="Edit object rotation fcurves. (If there are any)", default=False)
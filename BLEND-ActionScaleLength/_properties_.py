import bpy
from bpy.props import (EnumProperty, BoolProperty, StringProperty, CollectionProperty, FloatProperty, IntProperty)

class JK_SAL_Operator_Props(bpy.types.PropertyGroup):
    
    Length_mode: EnumProperty(name="Mode",description="The method we are changing the action length with",
        items=[('FPS', 'Framerate', "Set action using to and from FPS values"),
        ('LENGTH', 'Playhead', "Set action to fit the given playtime")],
        default='FPS')

    Framerate_from: IntProperty(name="FPS From", description="The framerate we are changing from", default=24, min=1, 
        subtype='NONE', update=None, get=None, set=None)

    Framerate_to: IntProperty(name="FPS To", description="The framerate we are changing to", default=30, min=1, 
        subtype='NONE', update=None, get=None, set=None)

    Playhead_offset: FloatProperty(name="Offset", description="The start offset. (in keyframes)", default=0.0, min=0, step=1, 
        precision=3, subtype='TIME', unit='TIME', update=None, get=None, set=None)
    
    Playhead_length: FloatProperty(name="Length", description="The desired action length relative to the current scene FPS. (in seconds)", default=0.0, min=0, step=1, 
        precision=3, subtype='TIME', unit='TIME', update=None, get=None, set=None)

    Replace: BoolProperty(name="Replace Action",description="Replace actions or create new ones", default=False)
    
    Single: BoolProperty(name="Single Action", description="Only edit the selected action. (Edit all actions if False)", default=True)

    Selected: BoolProperty(name="Set Framerate", description="Only edit the selected keyframes. (Edit all keyframes if False)", default=True)

    Set_fps: BoolProperty(name="Set Framerate", description="Set the scenes framerate after scaling", default=True)

class JK_SAL_Action_Props(bpy.types.PropertyGroup):

    Length_mode: EnumProperty(name="",description="The method we are changing the action length with",
        items=[('FPS', 'Framerate', "Set action using to and from FPS values"),
        ('LENGTH', 'Playhead', "Set action to fit the given playtime")],
        default='FPS')

    Framerate: IntProperty(name="FPS", description="The framerate associated with this action", default=24, min=1, 
        subtype='NONE', update=None, get=None, set=None)

    Playhead: FloatProperty(name="Length", description="The current action length relative to the current scene FPS. (in seconds)", default=0.0, min=0, step=1, 
        precision=3, subtype='TIME', unit='TIME', update=None, get=None, set=None)
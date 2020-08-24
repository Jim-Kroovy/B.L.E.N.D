import bpy
from bpy.props import (EnumProperty, BoolProperty, StringProperty, CollectionProperty, FloatProperty, IntProperty, PointerProperty)
from . import _functions_

class JK_ACB_Bone_Props(bpy.types.PropertyGroup):
    
    Type: EnumProperty(name="Type", description="Type of control. (if any)",
        items=[('NONE', 'None', "No controls"), ('SOURCE', 'Source', "Has controls"),
            ('MECHANISM', 'Mechanism', "Mechanism bone"), ('CONTROL', 'Control', "Control bone")],
        default='NONE')

class JK_ACB_Mesh_Props(bpy.types.PropertyGroup):

    Armature: StringProperty(name="Armature", description="The first armature this mesh is wieghted to")
    
class JK_ACB_Armature_Props(bpy.types.PropertyGroup):
    
    Auto_sync: BoolProperty(name="Auto Sync", description="Automatically synchronize any location changes made in edit mode across control bones when leaving edit mode",
        default=False, options=set())

    Auto_hide: BoolProperty(name="Auto Hide", description="Automatically hide/show control bones depending on mode. (Show only controls in pose mode, Show only source bones in edit/weight mode",
        default=False, options=set())

    def Update_Hide(self, context):
        if not self.Auto_hide:
            _functions_.Set_Hidden_Bones(self.id_data, sb_hide=self.Hide_source, mb_hide=self.Hide_mech, cb_hide=self.Hide_cont)

    Hide_source: BoolProperty(name="Show Source", description="Hide/Show original source bones. (Deform Bones)",
        default=False, options=set(), update=Update_Hide)

    Hide_mech: BoolProperty(name="Show Mechanism", description="Hide/Show mechanism bones",
        default=False, options=set(), update=Update_Hide)

    Hide_cont: BoolProperty(name="Show Controls", description="Hide/Show control bones",
        default=False, options=set(), update=Update_Hide)

    Meshes: CollectionProperty(type=JK_ACB_Mesh_Props)
import bpy
from bpy.props import (EnumProperty, BoolProperty, StringProperty, CollectionProperty, FloatProperty, IntProperty, PointerProperty)
from . import _functions_

class JK_ACB_Bone_Props(bpy.types.PropertyGroup):
    
    Type: EnumProperty(name="Type", description="Type of control. (if any)",
        items=[('NONE', 'None', "No controls"), ('SOURCE', 'Source', "Has controls"),
            ('MECHANISM', 'Mechanism', "Mechanism bone"), ('CONTROL', 'Control', "Control bone")],
        default='NONE')
    
class JK_ACB_Armature_Props(bpy.types.PropertyGroup):
    
    Auto_sync: BoolProperty(name="Auto Sync", description="Automatically synchronize any location changes made in edit mode across control bones when leaving edit mode",
        default=False, options=set())

    Auto_hide: BoolProperty(name="Auto Hide", description="Automatically hide/show control bones depending on mode. (Show only controls in pose mode, Show only source bones in edit/weight mode",
        default=True, options=set())
    
    def Update_Con_Prefix(self, context):
        armature = bpy.context.object
        controls = _functions_.Get_Control_Bones(armature)
        bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
        for sb_name, cb_names in controls['SOURCE'].items():
            cb = bones[cb_names['CONTROL']]
            cb.name = self.Con_prefix + sb_name
    
    Con_prefix: StringProperty(name="Control Prefix", description="The prefix for control bone name", 
        default="CB_", maxlen=1024, update=Update_Con_Prefix)

    def Update_Mech_Prefix(self, context):
        armature = bpy.context.object
        controls = _functions_.Get_Control_Bones(armature)
        bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
        for sb_name, cb_names in controls['SOURCE'].items():
            mb = bones[cb_names['MECHANISM']]
            mb.name = self.Mech_prefix + sb_name
    
    Mech_prefix: StringProperty(name="Mechanism Prefix", description="The prefix for mechanism bone name", 
        default="MB_", maxlen=1024, update=Update_Mech_Prefix)

    def Update_Hide(self, context):
        if not self.Auto_hide:
            armature = bpy.context.object
            _functions_.Set_Hidden_Bones(armature, sb_hide=self.Hide_source, mb_hide=self.Hide_mech, cb_hide=self.Hide_con)

    Hide_source: BoolProperty(name="Show Source", description="Hide/Show original source bones. (Deform Bones)",
        default=False, options=set(), update=Update_Hide)

    Hide_mech: BoolProperty(name="Show Mechanism", description="Hide/Show mechanism bones",
        default=False, options=set(), update=Update_Hide)

    Hide_con: BoolProperty(name="Show Controls", description="Hide/Show control bones",
        default=False, options=set(), update=Update_Hide) 
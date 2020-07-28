import bpy
from bpy.props import (EnumProperty, BoolProperty, StringProperty, CollectionProperty, FloatProperty, IntProperty, PointerProperty)

class JK_ACB_Bone_Props(bpy.types.PropertyGroup):
    
    Bone_name: StringProperty(name="Bone Name", description="Name of the bone that has the controls", 
        default="", maxlen=1024)

    Is_con: BoolProperty(name="Is Control", description="",
        default=False, options=set())

    Is_mech: BoolProperty(name="Is Mechanism", description="",
        default=False, options=set())
    
class JK_ACB_Armature_Props(bpy.types.PropertyGroup):

    Has_controls: BoolProperty(name="If this armature has controls", description="For now we can only have one group of controls",
        default=False, options=set())
    
    Is_from_edit: BoolProperty(name="From Edit Mode", description="Need to know when we switch between edit bones and bones",
        default=False, options=set())
    
    def Update_Con_Prefix(self, context):
        bones = self.id_data.edit_bones if self.Is_from_edit else self.id_data.bones
        to_bones = self.Edit_bones if self.Is_from_edit else self.Bones
        for to_bone in [tb for tb in to_bones if tb.Is_con]:
            bone = bones[to_bone.name]
            to_bone.name = self.Con_prefix + to_bone.Bone_name
            bone.name = self.Con_prefix + to_bone.Bone_name
    
    Con_prefix: StringProperty(name="Control Prefix", description="The prefix for control bone name", 
        default="CB_", maxlen=1024, update=Update_Con_Prefix)

    def Update_Mech_Prefix(self, context):
        bones = self.id_data.edit_bones if self.Is_from_edit else self.id_data.bones
        to_bones = self.Edit_bones if self.Is_from_edit else self.Bones
        for to_bone in [tb for tb in to_bones if tb.Is_mech]:
            bone = bones[to_bone.name]
            to_bone.name = self.Mech_prefix + to_bone.Bone_name
            bone.name = self.Mech_prefix + to_bone.Bone_name
    
    Mech_prefix: StringProperty(name="Mechanism Prefix", description="The prefix for mechanism bone name", 
        default="MB_", maxlen=1024, update=Update_Mech_Prefix)
    
    def Mech_Show_Update(self, context):
        bones = self.id_data.edit_bones if self.Is_from_edit else self.id_data.bones
        to_bones = self.Edit_bones if self.Is_from_edit else self.Bones
        names = [tb.name for tb in to_bones if not tb.Is_con]
        for name in names:
            bones[name].hide = self.Mech_show

    Mech_show: BoolProperty(name="Hide Mechanism", description="Hide/show the bones manipulated by the controls",
        default=True, options=set(), update=Mech_Show_Update)

    def Mech_Select_Update(self, context):
        bones = self.id_data.edit_bones if self.Is_from_edit else self.id_data.bones
        to_bones = self.Edit_bones if self.Is_from_edit else self.Bones
        names = [tb.name for tb in to_bones if not tb.Is_con]
        for name in names:
            bones[name].hide_select = self.Mech_select
    
    Mech_select: BoolProperty(name="Lock Selection", description="Disable selection of the bones manipulated by the controls",
        default=True, options=set(), update=Mech_Select_Update)
    
    Bones: CollectionProperty(type=JK_ACB_Bone_Props)

    Edit_bones: CollectionProperty(type=JK_ACB_Bone_Props)

    


    
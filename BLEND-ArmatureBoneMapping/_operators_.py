import bpy

from . import _properties_, _functions_

from bpy.props import (IntVectorProperty, BoolProperty)

class JK_OT_Mapping_Force_Naming(bpy.types.Operator):
    """Toggle control names to use a prefix or the names within the mapping"""
    bl_idname = "jk.force_mapping_names"
    bl_label = "Force Mapping Names"

    Selected: BoolProperty(
        name="Selected",
        description="Force names on selected bones only",
        default = False
        )

    def execute(self, context):
        armature = bpy.context.object
        mapping = bpy.context.preferences.addons["BLEND-ArmatureBoneMapping"].preferences.Mapping
        if len(mapping) > 0:
            ABM = armature.data.ABM
            bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
            for to_bone in ABM.Bones:
                bone = bones[to_bone.name]
                if _functions_.Get_Mapping_Name(to_bone.Mapping_indices, mapping) != "":
                    bone.name = _functions_.Get_Mapping_Name(to_bone.Mapping_indices, mapping)     
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "Selected")
        
class JK_OT_Mapping_Write(bpy.types.Operator):
    """Write current mapping to a text file"""
    bl_idname = "jk.write_mapping"
    bl_label = "Write"

    def execute(self, context):
        mapping = bpy.context.preferences.addons["BLEND-ArmatureBoneMapping"].preferences.Mapping
        _functions_.Write_Mapping(mapping)
        return {'FINISHED'}

class JK_OT_Mapping_Reset(bpy.types.Operator):
    """Reset mapping to default"""
    bl_idname = "jk.reset_mapping"
    bl_label = "Reset"

    Mapping = _properties_.Default_mapping
    
    Clear : BoolProperty(
        name="Clear",
        description="Clear mapping first",
        default = True
        )

    def execute(self, context):
        mapping = bpy.context.preferences.addons["BLEND-ArmatureBoneMapping"].preferences.Mapping
        _functions_.Set_New_Mapping(mapping, self.Mapping, self.Clear)
        return {'FINISHED'}

class JK_OT_Mapping_Clear(bpy.types.Operator):
    """Clear all mapping"""
    bl_idname = "jk.clear_mapping"
    bl_label = "Clear"

    def execute(self, context):
        bpy.context.preferences.addons["BLEND-ArmatureBoneMapping"].preferences.Mapping.clear() 
        return {'FINISHED'}

class JK_OT_Mapping_Add(bpy.types.Operator):
    """Add Mapping Entry"""
    bl_idname = "jk.add_mapping"
    bl_label = "Add"
    
    Indices: IntVectorProperty(
        name="Indices",
        description="Indices to map to the bones name",
        default=(-1, -1, -1),
        size=3,
        )

    def execute(self, context):
        mapping = bpy.context.preferences.addons["BLEND-ArmatureBoneMapping"].preferences.Mapping
        if self.Indices[1] != -1:
            mapping[self.Indices[0]].Joints[self.Indices[1]].Sections.add()
        elif self.Indices[0] != -1:
            mapping[self.Indices[0]].Joints.add()
        elif self.Indices[0] == -1:    
            mapping.add()
        return {'FINISHED'}

class JK_OT_Mapping_Remove(bpy.types.Operator):
    """Remove Mapping Entry"""
    bl_idname = "jk.remove_mapping"
    bl_label = "Remove"
    
    Indices: IntVectorProperty(
        name="Indices",
        description="Indices to map to the bones name",
        default=(-1, -1, -1),
        size=3,
        )

    def execute(self, context):
        mapping = bpy.context.preferences.addons["BLEND-ArmatureBoneMapping"].preferences.Mapping
        if self.Indices[2] != -1:
            mapping[self.Indices[0]].Joints[self.Indices[1]].Sections.remove(self.Indices[2])
        elif self.Indices[1] != -1:
            mapping[self.Indices[0]].Joints.remove(self.Indices[1])
        elif self.Indices[0] != -1:
            mapping.remove(self.Indices[0])
        return {'FINISHED'}
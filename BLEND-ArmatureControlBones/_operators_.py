import bpy
from bpy.props import (StringProperty, BoolProperty)
from . import _functions_, _properties_

class JK_OT_Add_Controls(bpy.types.Operator):
    """Builds mechanism bones that manipulate the selected bones indirectly with control bones. (Only one set of controls allowed per armature... for now)"""
    bl_idname = "jk.add_control_bones"
    bl_label = "Add Control Bones"
    
    Con_prefix: StringProperty(name="Control Prefix", description="The prefix for control bone names", 
        default="CB_", maxlen=1024)
        
    Mech_prefix: StringProperty(name="Mechanism Prefix", description="The prefix for mechanism bone names", 
        default="MB_", maxlen=1024)

    Auto: BoolProperty(name="Automatic Orientation", description="Use automatic orientation to initially position the control bones",
        default=False, options=set())

    Selected: BoolProperty(name="Selected", description="Only add mechanism and control bones for selected bones",
        default=False, options=set())

    def execute(self, context):
        # declare active armature and mechansim dictionary...
        armature = bpy.context.object
        ACB = armature.data.ACB
        # if we are operating on selected bones...
        if self.Selected:
            # we need a list of all the selected bones that do not have selected parents...
            parents = [b for b in bpy.context.selected_bones if b.parent not in bpy.context.selected_bones]
        else:
            parents = []
        # get all the bones without parents... (or if their parents are not selected)
        parentless = [b for b in armature.data.bones if b.parent == None or b in parents]    
        # hop into edit mode and iterate on them...
        bpy.ops.object.mode_set(mode='EDIT')
        names = []
        for bone in parentless:
            # only add bones if they aren't already in the bone data...
            if bone.name not in ACB.Edit_bones:
                parent = _functions_.Get_Control_Parent(ACB, bone)
                # add the control and mechanism bones... (without giving a parent)
                _functions_.Add_Control_Bones(armature, ACB.Con_prefix, ACB.Mech_prefix, bone, parent)
                names.append(bone.name)
            # iterate on the recursive children of the parentless bone...
            for child in bone.children_recursive:
                # only add bones if they aren't already in the bone data...
                if child.name not in ACB.Edit_bones:
                    # get the control parent... (this will work because we are iterating in order of hierarchy)
                    parent = _functions_.Get_Control_Parent(ACB, child)
                    # add control and mechanism bones for the child...
                    _functions_.Add_Control_Bones(armature, ACB.Con_prefix, ACB.Mech_prefix, child, parent)
                    names.append(child.name)
        # if the armature doesn't already have some controls...
        if not ACB.Has_controls:
            # add the object mode switching callback subscription to the object...
            _functions_.Subscribe_Mode_To(bpy.context.object, "mode", _functions_.Object_Mode_Callback)
            ACB.Has_controls = True
        # then bind the original bones to the mechanism bones...     
        _functions_.Set_Mechanism(armature, names, ACB.Mech_prefix)
        if self.Auto:
            _functions_.Set_Automatic_Orientation(armature, names, ACB.Con_prefix)
        return {'FINISHED'}

    def invoke(self, context, event):
        
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
        
    def draw(self, context):
        ACB = bpy.context.object.data.ACB
        layout = self.layout
        row =  layout.row()
        row.prop(ACB, "Con_prefix")
        row.prop(ACB, "Mech_prefix")
        row.enabled = False if len(ACB.Bones) > 0 or len(ACB.Edit_bones) > 0 else True
        row =  layout.row()
        row.prop(self, "Auto")
        row.prop(self, "Selected")

class JK_OT_Edit_Controls(bpy.types.Operator):
    """Edits the current controls of the armature"""
    bl_idname = "jk.edit_control_bones"
    bl_label = "Edit Control Bones"

    Auto: BoolProperty(name="Automatic Orientation", description="Apply automatic orientation on control bones. (Requires Edit Mode)",
        default=False, options=set())
    
    Remove: BoolProperty(name="Remove", description="Remove the control and mechanism bones. (Requires Edit Mode)",
        default=False, options=set())
    
    Reset: BoolProperty(name="Reset Binding", description="Re-apply copy transform constraints on mechanism bones. (Requires Pose Mode)",
        default=False, options=set())
    
    Selected: BoolProperty(name="Selected", description="Only operate on selected bones",
        default=False, options=set())

    def execute(self, context):
        armature = bpy.context.object
        ACB = armature.data.ACB
        bones = bpy.context.selected_bones if self.Selected else bpy.armature.data.bones
        from_bones = ACB.Edit_bones if armature.mode == 'EDIT' else ACB.Bones
        # using a dictionary so we can't have multiples of the same name...
        selected = {fb.Bone_name : True for fb in from_bones if fb.name in bones}
        if self.Auto:
            _functions_.Set_Automatic_Orientation(armature, selected.keys(), ACB.Con_prefix)  
        if self.Reset:
            _functions_.Set_Mechanism(armature, selected.keys(), ACB.Mech_prefix)
        if self.Remove:
            for name in selected.keys():
                # then get and remove both control and mechanism bones...
                con_bone = bones[ACB.Con_prefix + name]
                mech_bone = bones[ACB.Mech_prefix + name]
                armature.data.edit_bones.remove(con_bone)
                armature.data.edit_bones.remove(mech_bone)
                # then remove the bones from the collection...
                from_bones.remove(from_bones.find(name))
                from_bones.remove(from_bones.find(ACB.Con_prefix + name))
                from_bones.remove(from_bones.find(ACB.Mech_prefix + name))
            # if we have removed them all then set the has controls bool...
            if len(ACB.Edit_bones) == 0:
                ACB.Has_controls = False        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.Auto = False
        self.Reset = False
        self.Remove = False
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "Auto")
        row.prop(self, "Remove")
        row.enabled = True if context.object.mode == 'EDIT' else False
        row = layout.row()
        col = row.column()
        col.prop(self, "Reset")
        col.enabled = True if context.object.mode == 'POSE' else False
        col = row.column()
        col.prop(self, "Selected")
            
            
        
        

    

    


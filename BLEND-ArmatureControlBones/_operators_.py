import bpy
from bpy.props import (StringProperty, BoolProperty, EnumProperty)
from . import _functions_, _properties_

class JK_OT_ACB_Subscribe_Object_Mode(bpy.types.Operator):
    """Subscribes the objects mode switching to the msgbus in order to auto sync editing"""
    bl_idname = "jk.acb_sub_mode"
    bl_label = "Subscribe Object"

    Object: StringProperty(name="Object", description="Name of the object to subscribe", default="")
    
    def execute(self, context):
        _functions_.Subscribe_Mode_To(bpy.data.objects[self.Object], "mode", _functions_.Object_Mode_Callback)
        return {'FINISHED'}

class JK_OT_Edit_Controls(bpy.types.Operator):
    """Edits the current controls of the armature"""
    bl_idname = "jk.edit_control_bones"
    bl_label = "Edit Control Bones"
    
    Is_adding: BoolProperty(name="Is Adding", description="If the operator should be adding or editing",
        default=False, options=set())
    
    Selected: BoolProperty(name="Only Selected", description="Only operate on selected bones",
        default=False, options=set())
    
    Orient: BoolProperty(name="Auto Orient", description="Attempt to automatically orient control bones",
        default=False, options=set())
    
    Sync: BoolProperty(name="Edit Sync", description="Synchronize changes to control bones",
        default=False, options=set())

    Remove: BoolProperty(name="Remove", description="Remove control bones",
        default=False, options=set())

    def execute(self, context):
        armature = bpy.context.object
        controls, last_mode = _functions_.Get_Control_Bones(armature), armature.mode
        # if we aren't in edit mode, go there...
        if last_mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        if self.Is_adding:
            # if we are operating on selected bones...
            if self.Selected:
                # we need a list of all the selected bones that do not have selected parents...
                parents = [b for b in bpy.context.selected_bones if b.parent not in bpy.context.selected_bones]
            else:
                parents = []
            # get all the bones without parents... (or if their parents are not selected)
            parentless, new_cons = [b for b in armature.data.bones if b.parent == None or b in parents], {}
            # hop into edit mode and iterate on them...
            bpy.ops.object.mode_set(mode='EDIT')
            for bone in parentless:
                # only add bones if they aren't already in the bone data...
                if not any(bone.name in controls[key] for key in ['SOURCE', 'MECHANISM', 'CONTROL']):
                    parent = _functions_.Get_Control_Parent(armature, new_cons, bone)
                    # add the control and mechanism bones...
                    new_cons[bone.name] = _functions_.Add_Bone_Controls(armature, bone, parent)
                # if only selected...
                if self.Selected:
                    # only get the selected recursive children...
                    children = [c for c in bone.children_recursive if c in bpy.context.selected_bones]
                else:
                    # otherwise get all recursive children...
                    children = bone.children_recursive
                # iterate on the recursive children of the parentless bone...
                for child in children:
                    # only add bones if they aren't already in the bone data...
                    if not any(child.name in controls[key] for key in ['SOURCE', 'MECHANISM', 'CONTROL']):
                        # get the control parent... (this will work because we are iterating in order of hierarchy)
                        parent = _functions_.Get_Control_Parent(armature, new_cons, child)
                        # add control and mechanism bones for the child...
                        new_cons[child.name] = _functions_.Add_Bone_Controls(armature, child, parent)
            # then toggle edit mode to update the new bones...
            bpy.ops.object.editmode_toggle()
            # and iterate through the new controls setting up the copy transform constraints...
            for sb_name, cb_names in new_cons.items():
                sp_bone = armature.pose.bones[sb_name]
                copy_trans = sp_bone.constraints.new("COPY_TRANSFORMS")
                copy_trans.name, copy_trans.show_expanded = "MECHANISM - Copy Transform", False
                copy_trans.target = armature
                copy_trans.show_expanded = False
                copy_trans.subtarget = cb_names['MECHANISM']
                mp_bone, cp_bone = armature.pose.bones[cb_names['MECHANISM']], armature.pose.bones[cb_names['CONTROL']]
                sp_bone.bone.ACB.Type, mp_bone.bone.ACB.Type, cp_bone.bone.ACB.Type = 'SOURCE', 'MECHANISM', 'CONTROL'
            # if we want to auto orient on creation...
            if self.Orient:
                bpy.ops.object.editmode_toggle()
                # iterate on collected control bone names, orienting them...
                for sb_name, cb_names in new_cons.items():
                    _functions_.Set_Automatic_Orientation(armature, cb_names['CONTROL'])     
            # if this is the first set of controls sub the armature to the msgbus...
            if len(controls['SOURCE']) == 0:
                _functions_.Subscribe_Mode_To(armature, 'mode', _functions_.Object_Mode_Callback)
        else:
            # if we aren't adding we will need to iterate over all controls...
            for sb_name, cb_names in controls['SOURCE'].items():
                # if we are only operating on selected controls...
                if self.Selected:
                    # check the controls are selected before doing anything...
                    if any(name in bpy.context.selected_bones for name in [sb_name, cb_names['MECHANISM'], cb_names['CONTROL']]):
                        # check if we are removing first...
                        if self.Remove:
                            _functions_.Remove_Control_Bones(armature, sb_name, cb_names)
                        else:
                            # if we aren't removing then we can do both other operations...
                            if self.Sync:
                                _functions_.Set_Control_Location(armature, sb_name, cb_names)
                            if self.Orient:
                                _functions_.Set_Automatic_Orientation(armature, cb_names['CONTROL'])
                else:
                    # otherwise check if we are removing first...
                    if self.Remove:
                        _functions_.Remove_Control_Bones(armature, sb_name, cb_names)
                    else:
                        # if we aren't removing then we can do both other operations...
                        if self.Sync:
                            _functions_.Set_Control_Location(armature, sb_name, cb_names)
                        if self.Orient:
                            _functions_.Set_Automatic_Orientation(armature, cb_names['CONTROL'])
        # if we changed mode, go back...
        if armature.mode != last_mode:
            bpy.ops.object.mode_set(mode=last_mode)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.Orient = False
        self.Sync = False
        self.Remove = False
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        if self.Is_adding:
            row.prop(self, "Orient")
        else:
            row.prop(self, "Sync")
            row.prop(self, "Orient")
            row = layout.row()
            row.prop(self, "Remove")
        row.prop(self, "Selected")
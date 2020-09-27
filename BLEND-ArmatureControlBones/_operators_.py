import bpy
from bpy.props import (StringProperty, BoolProperty, EnumProperty)
from . import _functions_, _properties_

class JK_OT_ACB_Subscribe_Object_Mode(bpy.types.Operator):
    """Subscribes the objects mode switching to the msgbus in order to auto sync editing"""
    bl_idname = "jk.acb_sub_mode"
    bl_label = "Subscribe Object"

    Object: StringProperty(name="Object", description="Name of the object to subscribe", default="")
    
    def execute(self, context):
        _functions_.Subscribe_Mode_To(bpy.data.objects[self.Object], _functions_.Armature_Mode_Callback)
        return {'FINISHED'}

class JK_OT_Edit_Controls(bpy.types.Operator):
    """Edits the current controls of the armature"""
    bl_idname = "jk.edit_control_bones"
    bl_label = "Control Bones"
    bl_options = {'REGISTER', 'UNDO'}
    
    Is_adding: BoolProperty(name="Is Adding", description="If the operator should be adding or editing",
        default=False, options=set())
    
    Selected: BoolProperty(name="Only Selected", description="Only operate on selected bones",
        default=False, options=set())
    
    Orient: BoolProperty(name="Auto Orient", description="Attempt to automatically orient control bones",
        default=False, options=set())
    
    Sync: BoolProperty(name="Edit Sync", description="Synchronize changes to control bones",
        default=False, options=set())

    def Remove_Update(self, context):
        if self.Remove:
            self.Orient, self.Sync = False, False

    Remove: BoolProperty(name="Remove", description="Remove control bones",
        default=False, options=set(), update=Remove_Update)

    def execute(self, context):
        armature = bpy.context.object
        controls, last_mode = _functions_.Get_Control_Bones(armature), armature.mode
        # if we are already in edit mode..
        if last_mode == 'EDIT':
            # toggle out and in to update any new bones for the selection...
            bpy.ops.object.editmode_toggle()
            selected = _functions_.Get_Selected_Bones(armature)
            bpy.ops.object.editmode_toggle()
        else:
            # otherwise go into edit mode after getting the selection...
            selected = _functions_.Get_Selected_Bones(armature)
            bpy.ops.object.mode_set(mode='EDIT')
        if self.Is_adding:
            bones = selected if self.Selected else armature.data.bones
            # if we are operating on selected bones...
            if self.Selected:
                # we need a list of all the selected bones that do not have selected parents...
                parents = [b for b in selected if b.parent not in selected]
            else:
                parents = []
            # get all the bones without parents... (or if their parents are not selected)
            parentless, new_conts = [b for b in bones if b.parent == None or b in parents], {}
            # and iterate on them...
            for bone in parentless:
                # only add bones if they aren't already part of controls...
                if bone.ACB.Type == 'NONE':
                    parent = _functions_.Get_Control_Parent(armature, new_conts, bone)
                    # add the control and mechanism bones...
                    new_conts[bone.name] = _functions_.Add_Bone_Controls(armature, bone, parent)
                # if only selected...
                if self.Selected:
                    # only get the selected recursive children... (Bug reported and fixed for next Blender release, see below)
                    children = [armature.data.bones[c.name] for c in bone.children_recursive if armature.data.bones[c.name] in selected]
                else:
                    # otherwise get all recursive children...
                    children = bone.children_recursive
                # iterate on the recursive children of the parentless bone...
                for c in children:
                    # calling "children_recursive" on a BONE in edit mode returns EDIT BONES - Bug reported and fixed for next Blender release
                    child = armature.data.bones[c.name]
                    # only add bones if they aren't already in the bone data...
                    if child.ACB.Type == 'NONE':
                        # get the control parent... (this will work because we are iterating in order of hierarchy)
                        parent = _functions_.Get_Control_Parent(armature, new_conts, child)
                        # add control and mechanism bones for the child...
                        new_conts[child.name] = _functions_.Add_Bone_Controls(armature, child, parent)
            # then toggle edit mode to update the new bones...
            bpy.ops.object.editmode_toggle()
            # and iterate through the new controls setting up the copy transform constraints...
            for sb_name, cb_names in new_conts.items():
                sp_bone = armature.pose.bones[sb_name]
                copy_trans = sp_bone.constraints.new("COPY_TRANSFORMS")
                copy_trans.name, copy_trans.show_expanded = "MECHANISM - Copy Transform", False
                copy_trans.target = armature
                copy_trans.show_expanded = False
                copy_trans.subtarget = cb_names['MECH']
                mp_bone, cp_bone = armature.pose.bones[cb_names['MECH']], armature.pose.bones[cb_names['CONT']]
                sp_bone.bone.ACB.Type, mp_bone.bone.ACB.Type, cp_bone.bone.ACB.Type = 'SOURCE', 'MECH', 'CONT'
            # if we want to auto orient on creation...
            if self.Orient:
                # toggle back to edit mode and iterate on collected control bone names, orienting them...
                bpy.ops.object.editmode_toggle()
                for sb_name, cb_names in new_conts.items():
                    _functions_.Set_Automatic_Orientation(armature, cb_names['CONT'])     
            # if this is the first set of controls sub the armature to the msgbus...
            if len(controls) == 0:
                _functions_.Subscribe_Mode_To(armature, _functions_.Armature_Mode_Callback)
        else:
            # if we aren't adding we will need to iterate over all controls...
            for sb_name, cb_names in controls.items():
                # if we are only operating on selected controls...
                if self.Selected:
                    # check the controls are selected before doing anything...
                    if any(armature.data.bones[name] in selected for name in [sb_name, cb_names['MECH'], cb_names['CONT']]):
                        # check if we are removing first...
                        if self.Remove:
                            _functions_.Remove_Bone_Controls(armature, sb_name, cb_names)
                        else:
                            # if we aren't removing then we can check both other operations...
                            if self.Sync:
                                _functions_.Set_Control_Location(armature, sb_name, cb_names)
                            if self.Orient:
                                _functions_.Set_Automatic_Orientation(armature, cb_names['CONT'])
                else:
                    # otherwise check if we are removing first...
                    if self.Remove:
                        _functions_.Remove_Bone_Controls(armature, sb_name, cb_names)
                    else:
                        # if we aren't removing then we can check both other operations...
                        if self.Sync:
                            _functions_.Set_Control_Location(armature, sb_name, cb_names)
                        if self.Orient:
                            _functions_.Set_Automatic_Orientation(armature, cb_names['CONT'])
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
            row.prop(self, "Orient", icon='PROP_ON' if self.Orient else 'PROP_OFF')
            row.prop(self, "Selected")
        else:
            row.prop(self, "Sync", icon='SNAP_ON' if self.Sync else 'SNAP_OFF')
            row.prop(self, "Orient", icon='PROP_ON' if self.Orient else 'PROP_OFF')
            row.prop(self, "Remove", icon='CANCEL' if self.Remove else 'X')
            row = layout.row()
            row.prop(self, "Selected")
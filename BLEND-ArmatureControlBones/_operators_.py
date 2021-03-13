import bpy
import json
from bpy.props import (StringProperty, BoolProperty, EnumProperty)
from . import _functions_, _properties_

class JK_OT_ACB_Subscribe_Object_Mode(bpy.types.Operator):
    """Subscribes the objects mode switching to the msgbus in order to auto sync editing"""
    bl_idname = "jk.acb_sub_mode"
    bl_label = "Subscribe Object"

    Object: StringProperty(name="Object", description="Name of the object to subscribe", default="")
    
    def execute(self, context):
        _functions_.subscribe_mode_to(bpy.data.objects[self.Object], _functions_.armature_mode_callback)
        return {'FINISHED'}

class JK_OT_Edit_Controls(bpy.types.Operator):
    """Edits the current controls of the armature"""
    bl_idname = "jk.acb_edit_controls"
    bl_label = "Control Bones"
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(name="Action", description="What this operator should do to the controls",
        items=[('ADD', 'Add', ""), ('REMOVE', 'Remove', ""), ('UPDATE', 'Update', "")],
        default='ADD')
    
    only_selected: BoolProperty(name="Only Selected", description="Only operate on selected bones",
        default=False, options=set())

    only_deforms: BoolProperty(name="Only Deforms", description="Only operate on deforming bones",
        default=False, options=set())
    
    orient: BoolProperty(name="Orient Controls", description="Attempt to automatically orient control bones. (Useful when operating on bones that are not oriented for Blender)",
        default=False, options=set())

    parent: BoolProperty(name="Parent Deforms", description="Attempt to automatically parent deform bones. (Useful when operating on a broken hierarchy)",
        default=False, options=set())

    def execute(self, context):
        controller = bpy.context.view_layer.objects.active
        deformer = controller.data.jk_acb.armature
        # make sure the operator cannot trigger any auto updates...
        is_auto_updating = controller.data.jk_acb.use_auto_update
        controller.data.jk_acb.use_auto_update = False
        # get the bones we should be operating on...
        bones = _functions_.get_bone_names(self, controller)
        # if we are adding deform bones...
        if self.action == 'ADD':
            # if there is existing deform bone data...
            if controller.data.jk_acb.deforms and controller.data.jk_acb.is_controller:
                # gather them into the bones we should be operating on...
                deforms = json.loads(controller.data.jk_acb.deforms)
                for bone in deforms:
                    control_bb = controller.data.bones.get(bone['name'])
                    # as long as they aren't already in there...
                    if control_bb and control_bb.name not in bones:
                        bones[control_bb.name] = False
            # so we can get a fresh copy of them in order of hierarchy...
            deform_bones = _functions_.get_deform_bones(controller, bones)
            controller.data.jk_acb.deforms = json.dumps(deform_bones)
            # if the armature is already a controller...
            if controller.data.jk_acb.is_controller:
                # just make sure the new deform bones get added...
                _functions_.add_deform_bones(controller, deformer)
            else:
                # if we are using combined armatures...
                if controller.data.jk_acb.use_combined:
                    # just add the deform bones to the controller...
                    _functions_.add_deform_bones(controller, deformer)
                    # and set the pointer and bools... (when combined the controller just references itself)
                    controller.data.jk_acb.is_controller = True
                    controller.data.jk_acb.armature = controller
                    controller.data.jk_acb.is_deformer = True
                    # and subscribe the mode change callback...
                    _functions_.subscribe_mode_to(controller, _functions_.armature_mode_callback)
                else:
                    # otherwise add in the deform armature...
                    _functions_.add_deform_armature(controller)
                    deformer = controller.data.jk_acb.armature
                    # and subscribe the mode change callback on both armatures...
                    _functions_.subscribe_mode_to(controller, _functions_.armature_mode_callback)
                    _functions_.subscribe_mode_to(deformer, _functions_.armature_mode_callback)
            # get a ref to the deformer... (might be None if adding for the first time)
            deformer = controller.data.jk_acb.armature
            # if we are orienting controls, orient them...
            if self.orient:
                _functions_.set_control_orientation(controller, bones)
            # if we are parenting deforms, parent them...
            if self.parent:
                _functions_.set_deform_parenting(controller, deformer, bones)
        # if we are removing deform bones...
        elif self.action == 'REMOVE':
            # if we are removing only selected or deforming bones...
            if self.only_deforms or self.only_selected or controller.data.jk_acb.use_combined:
                deform_bones = _functions_.remove_deform_bones(controller, deformer, bones)
                controller.data.jk_acb.deforms = json.dumps(deform_bones)
            else:
                # otherwise just remove the deform armature...
                _functions_.remove_deform_armature(controller)
        # if we are updating them...
        elif self.action == 'UPDATE':
            # perform and save the initial update...
            deform_bones = _functions_.update_deform_bones(controller, deformer)
            controller.data.jk_acb.deforms = json.dumps(deform_bones)
            # if we are orienting controls, orient them...
            if self.orient:
                _functions_.set_control_orientation(controller, bones)
            # if we are parenting deforms, parent them...
            if self.parent:
                _functions_.set_deform_parenting(controller, deformer, bones)
        # then always update the constraints and save any changes made to the deform bones...
        _functions_.set_deform_constraints(deformer, bones)
        deform_bones = _functions_.set_deform_bones(controller, deformer)
        controller.data.jk_acb.deforms = json.dumps(deform_bones)
        # turn auto update back on if it was on when we executed...
        controller.data.jk_acb.use_auto_update = is_auto_updating
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.orient = False
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "orient", icon='ORIENTATION_CURSOR')
        row.prop(self, "parent", icon='CON_CHILDOF')
        row.enabled = True if self.action in ['ADD', 'UPDATE'] else False
        row = layout.row()
        row.prop(self, "only_selected")
        row.prop(self, "only_deforms")
        
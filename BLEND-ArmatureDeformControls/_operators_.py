import bpy
import mathutils
from bpy.props import (StringProperty, BoolProperty, EnumProperty, IntProperty)
from . import _functions_

class JK_OT_ADC_Subscribe_Object_Mode(bpy.types.Operator):
    """Subscribes the objects mode switching to the msgbus in order to auto sync editing"""
    bl_idname = "jk.adc_sub_mode"
    bl_label = "Subscribe Object"

    Object: StringProperty(name="Object", description="Name of the object to subscribe", default="")
    
    def execute(self, context):
        _functions_.subscribe_mode_to(bpy.data.objects[self.Object], _functions_.armature_mode_callback)
        return {'FINISHED'}

class JK_OT_ADC_Edit_Controls(bpy.types.Operator):
    """Edits the current controls of the armature"""
    bl_idname = "jk.adc_edit_controls"
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
        active, controller = bpy.context.view_layer.objects.active, None
        if active and active.type == 'ARMATURE':
            controller, deformer = active.data.jk_adc.get_armatures()
            # make sure the operator cannot trigger any auto updates...
            is_auto_updating = controller.data.jk_adc.use_auto_update
            controller.data.jk_adc.use_auto_update = False
            # if we are adding deform bones...
            if self.action == 'ADD':
                names = _functions_.get_add_names(controller, self.only_selected, self.only_deforms)
                print("Adding deforms for:", names)
                # if the armature is already a controller...
                if controller.data.jk_adc.is_controller:
                    # just make sure the new deform bones get added...
                    _functions_.add_deform_bones(controller, deformer, names)
                else:
                    deformer = _functions_.add_deform_armature(controller)
                    _functions_.add_deform_bones(controller, deformer, names)
                    _functions_.subscribe_mode_to(controller, _functions_.armature_mode_callback)
                if self.orient or self.parent:
                    _functions_.update_deform_bones(controller, self.only_selected, self.only_deforms, orient_controls=self.orient, parent_deforms=self.parent)
            # if we are removing deform bones...
            elif self.action == 'REMOVE':
                names = _functions_.get_remove_names(controller, self.only_selected, self.only_deforms)
                print("Removing deforms for:", names)
                # remove all the deform bones that need removing...
                _functions_.remove_deform_bones(controller, deformer, names)
                # if this is not a combined control/deform armature...
                if not controller.data.jk_adc.use_combined:
                    # and we just deleted all the deformers bones...
                    deformer = controller.data.jk_adc.get_deformer() 
                    if not deformer.data.bones:
                        # remove the deform armature...
                        _functions_.remove_deform_armature(controller)
                else:
                    # if we removed all the deform bones, unset the controllers bool...
                    if not any(bb.jk_adc.has_deform for bb in controller.data.bones):
                        controller.data.jk_adc.is_controller = False
            # if we are updating them...
            elif self.action == 'UPDATE':
                _functions_.update_deform_bones(controller, self.only_selected, self.only_deforms, orient_controls=self.orient, parent_deforms=self.parent)
            # turn auto update back on if it was on when we executed...
            controller.data.jk_adc.use_auto_update = is_auto_updating
        else:
            print("Armature Control Bones says there is no active object?")
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

class JK_OT_ADC_Bake_Deforms(bpy.types.Operator):
    """Bakes the current deformation bones of the armature (all bones with "use_deform" set True)"""
    bl_idname = "jk.adc_bake_deforms"
    bl_label = "Bake Deforms"
    bl_options = {'REGISTER', 'UNDO'}

    armature: StringProperty(name="Armature", description="Name of the armature to bake", default="")

    bake_step: IntProperty(name="Bake Step", description="How often to evaluate keyframes when baking using 'Bake Deforms' to pre-bake keyframes", 
        default=1, min=1, options=set())

    only_active: BoolProperty(name="Only Active", description="Only bake the active action",
        default=False)

    only_selected: BoolProperty(name="Only Selected", description="Only operate on selected bones",
        default=False, options=set())

    visual_keys: BoolProperty(name="Visual Keying", description="Keyframe from the final transformation (with constraints applied)",
        default=True)

    curve_clean: BoolProperty(name="Clean Curves", description="After baking curves, remove redundant keys",
        default=False)

    fake_user: BoolProperty(name="Fake User", description="Save baked actions even if they have no users (stops them from being deleted on save/load)",
        default=True)

    def execute(self, context):
        prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
        armature = bpy.data.objects[self.armature]
        # we need have references to all the relevant armatures... (if using control/deforms)
        controller, deformer = armature.data.jk_adc.get_armatures()
        # get all the actions to bake... (and existing baked actions)
        sources, bakes = controller.data.jk_adc.get_actions(controller, self.only_active)
        # make sure we are in object mode...
        last_mode = armature.mode
        if last_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # if we have auto keying enabled, turn it off... (just incase)
        is_auto_keying = bpy.context.scene.tool_settings.use_keyframe_insert_auto
        if is_auto_keying:
            bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
        # set our meshes to use deforms... (if there are deform bones)
        if controller.data.jk_adc.is_controller:
            if controller.data.jk_adc.hide_deforms:
                controller.data.jk_adc.hide_deforms = False
            if not controller.data.jk_adc.use_deforms:
                controller.data.jk_adc.use_deforms = True
        # deselect all objects and select only the deform armature...
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = deformer
        deformer.select_set(True)
        # if the deformer doesn't have animation data, create it...
        if not deformer.animation_data:
            deformer.animation_data_create()
        # jump into pose mode...
        bpy.ops.object.mode_set(mode='POSE')
        # make sure only deforming bones are selected...
        for pb in deformer.pose.bones:
            if self.only_selected:
                if pb.bone.select:
                    pb.bone.select = pb.bone.use_deform
            else:
                pb.bone.select = pb.bone.use_deform
        # for each action...
        for source, baked in sources.items():
            # set it to the active action...
            controller.animation_data.action = source
            # clear the controllers pose transforms... (does baking already do this?)
            for pb in controller.pose.bones:
                pb.location, pb.scale, pb.rotation_euler = [0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [0.0, 0.0, 0.0]
                pb.rotation_quaternion, pb.rotation_axis_angle = [1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]
            # bake the action...
            bpy.ops.nla.bake(frame_start=int(round(source.frame_range[0], 0)), frame_end=int(round(source.frame_range[1], 0)),
                step=self.bake_step, only_selected=True, visual_keying=self.visual_keys, clear_constraints=False, clear_parents=False, 
                use_current_action=False, clean_curves=self.curve_clean, bake_types={'POSE'})
            # remove the old action if there is one...
            if baked:
                bpy.data.actions.remove(baked)
            # and name the new one, setting fake user as required...
            deformer.animation_data.action.name = prefs.deform_prefix + source.name
            deformer.animation_data.action.use_fake_user = self.fake_user
        # and mute the deform constraints so we can preview the animations... (if there are deform bones)
        if controller.data.jk_adc.is_controller:
            controller.data.jk_adc.mute_deforms = True
        # and switch auto keying back on if it got turned off...
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = is_auto_keying
        bpy.ops.object.mode_set(mode=last_mode)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.orient = False
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "only_active")
        row.prop(self, "bake_step")
        row.prop(self, "fake_user", text="", icon='FAKE_USER_ON' if self.fake_user else 'FAKE_USER_OFF')
        row = layout.row()
        row.prop(self, "visual_keys")
        row.prop(self, "curve_clean")
        row.prop(self, "only_selected")

class JK_OT_ADC_Bake_Controls(bpy.types.Operator):
    """Bakes the current control bones of the armature (all bones without "use_deform" set True)"""
    bl_idname = "jk.adc_bake_controls"
    bl_label = "Bake Controls"
    bl_options = {'REGISTER', 'UNDO'}

    armature: StringProperty(name="Armature", description="Name of the armature to bake", default="")

    bake_step: IntProperty(name="Bake Step", description="How often to evaluate keyframes when baking using 'Bake Deforms' to pre-bake keyframes", 
        default=1, min=1, options=set())

    only_active: BoolProperty(name="Only Active", description="Only bake the active action",
        default=False)

    only_selected: BoolProperty(name="Only Selected", description="Only operate on selected bones",
        default=False, options=set())

    visual_keys: BoolProperty(name="Visual Keying", description="Keyframe from the final transformation (with constraints applied)",
        default=True)

    curve_clean: BoolProperty(name="Clean Curves", description="After baking curves, remove redundant keys",
        default=False)

    fake_user: BoolProperty(name="Fake User", description="Save baked actions even if they have no users (stops them from being deleted on save/load)",
        default=True)

    def execute(self, context):
        prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
        armature = bpy.data.objects[self.armature]
        # we need have references to all the relevant armatures... (if using control/deforms)
        controller, deformer = armature.data.jk_adc.get_armatures()
        # get all the actions to bake... (and existing baked actions)
        sources, bakes = deformer.data.jk_adc.get_actions(deformer, self.only_active)
        # make sure we are in object mode...
        last_mode = armature.mode
        if last_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # if we have auto keying enabled, turn it off... (just incase)
        is_auto_keying = bpy.context.scene.tool_settings.use_keyframe_insert_auto
        if is_auto_keying:
            bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
        # set our meshes to use deforms... (if there are deform bones)
        if controller.data.jk_adc.is_controller:
            if not controller.data.jk_adc.use_deforms:
                controller.data.jk_adc.use_deforms = True
            if controller.data.jk_adc.hide_deforms:
                controller.data.jk_adc.hide_deforms = False
        # deselect all objects and select only the control armature...
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = controller
        controller.select_set(True)
        # if the deformer doesn't have animation data, create it...
        if not controller.animation_data:
            controller.animation_data_create()
        # jump into pose mode...
        bpy.ops.object.mode_set(mode='POSE')
        # make sure only control bones are selected...
        for pb in controller.pose.bones:
            if self.only_selected:
                if pb.bone.select:
                    pb.bone.select = pb.bone.jk_adc.has_deform
                else:
                    pb.bone.select = False
            else:
                pb.bone.select = pb.bone.jk_adc.has_deform
        # if rigging library is installed...
        addons = bpy.context.preferences.addons.keys()
        if 'BLEND-ArmatureRiggingModules' in addons:
            # we might want to select some IK targets...
            for rigging in controller.jk_arm.rigging:
                # turning off auto fk and set chains to use fk...
                if rigging.flavour in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE']: 
                    chain = rigging.get_pointer()
                    references = chain.get_references()
                    # select any of the chains targets and poles...
                    target = references['target']['bone'] if rigging.flavour == 'OPPOSABLE' else references['target']['parent']
                    pole = references['pole']['bone']
                    if target:
                        target.bone.select = True
                    if pole:
                        pole.bone.select = True
        # for each action...
        for baked, source in bakes.items():
            # set it to the active action...
            deformer.animation_data.action = baked
            # clear the deformers pose transforms... (does baking already do this?)
            for pb in deformer.pose.bones:
                pb.location, pb.scale, pb.rotation_euler = [0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [0.0, 0.0, 0.0]
                pb.rotation_quaternion, pb.rotation_axis_angle = [1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]
            # bake the action...
            bpy.ops.nla.bake(frame_start=int(round(baked.frame_range[0], 0)), frame_end=int(round(baked.frame_range[1], 0)),
                step=self.bake_step, only_selected=True, visual_keying=self.visual_keys, clear_constraints=False, clear_parents=False, 
                use_current_action=False, clean_curves=self.curve_clean, bake_types={'POSE'})
            # remove the old action if there is one...
            if source:
                bpy.data.actions.remove(source)
            # and name the new one, setting fake user as required...
            controller.animation_data.action.name = baked.name[len(prefs.deform_prefix):]
            controller.animation_data.action.use_fake_user = self.fake_user
        # and mute the deform constraints so we can preview the animations... (if there are deform bones)
        if controller.data.jk_adc.is_controller:
            controller.data.jk_adc.mute_deforms = True
        # and switch auto keying back on if it got turned off...
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = is_auto_keying
        bpy.ops.object.mode_set(mode=last_mode)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.orient = False
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "only_active")
        row.prop(self, "bake_step")
        row.prop(self, "fake_user", text="", icon='FAKE_USER_ON' if self.fake_user else 'FAKE_USER_OFF')
        row = layout.row()
        row.prop(self, "visual_keys")
        row.prop(self, "curve_clean")
        row.prop(self, "only_selected")

class JK_OT_ADC_Refresh_Constraints(bpy.types.Operator):
    """Refreshes the child of constraints used by control/deform bones after applying scale"""
    bl_idname = "jk.adc_refresh_constraints"
    bl_label = "Refresh Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        controller, deformer = _functions_.get_armatures()
        if controller:
            if controller.mode == 'EDIT':
                deformer.update_from_editmode()
                if not controller.data.jk_adc.is_deformer:
                    controller.update_from_editmode()
            _functions_.refresh_deform_constraints(controller, use_identity=True)
        return {'FINISHED'}

class JK_OT_ADC_Reverse_Constraints(bpy.types.Operator):
    """Reverse the deform/control constraints so the deforms follow the controls or the controls follow the deforms"""
    bl_idname = "jk.adc_reverse_constraints"
    bl_label = "Reverse Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    reverse: BoolProperty(name="Reverse Constraints", description="Reverse deform/control constraints",
        default=False)

    def execute(self, context):
        controller, deformer = _functions_.get_armatures()
        if controller:
            last_mode = controller.mode
            if last_mode != 'POSE':
                bpy.ops.object.mode_set(mode='POSE')
            deformer = controller.data.jk_adc.get_deformer()
            # copy and clear the controllers world space transforms...
            control_mat = controller.matrix_parent_inverse.copy()
            controller.matrix_parent_inverse = mathutils.Matrix()
            # if rigging library is installed...
            addons = bpy.context.preferences.addons.keys()
            if 'BLEND-ArmatureRiggingModules' in addons:
                # we need to iterate through the controllers rigging...
                for rigging in controller.jk_arm.rigging:
                    # turning off auto fk and set chains to use fk...
                    if rigging.flavour in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE']:
                        chain = rigging.get_pointer()
                        chain.use_auto_fk = False
                        chain.use_fk = True
                    # kill the influence on all the tracking constraints...
                    elif rigging.flavour == 'TRACKING':
                        chain = rigging.get_pointer()
                        for bone in chain.bones:
                            source_pb = controller.pose.bones.get(bone.source)
                            if source_pb:
                                copy_rot = source_pb.constraints.get("TRACK - Copy Rotation")
                                if copy_rot:
                                    copy_rot.influence = 0.0
            # iterate on all control/deforms and reverse their deform constraints...
            bbs = controller.data.jk_adc.get_bones()
            for bb in bbs:
                control, deform = bb.jk_adc.get_control(), bb.jk_adc.get_deform()
                if control and deform:
                    # remove the deformation constraints from one bone...
                    _functions_.remove_deform_constraints(deform if self.reverse else control)
                    # mute/un-mute all constraints on the control bone... (just in-case)
                    for con in control.constraints:
                        con.mute = self.reverse
                    # and add them to the other...
                    _functions_.add_deform_constraints(deformer, control if self.reverse else deform, deform.bone if self.reverse else control.bone, limits=True)
            if controller.mode != last_mode:
                bpy.ops.object.mode_set(mode=last_mode)
            # and return the controllers matrix...
            controller.matrix_parent_inverse = control_mat
            controller.data.jk_adc.reverse_deforms = self.reverse
            # ensuring we trigger the use location and scale updates... (to add those constraints)
            for bb in bbs:
                bb.jk_adc.use_location, bb.jk_adc.use_scale = bb.jk_adc.use_location, bb.jk_adc.use_scale
            bpy.ops.object.mode_set(mode=last_mode)
        return {'FINISHED'}

class JK_OT_ADC_Set_Selected(bpy.types.Operator):
    """Sets all selected bones pose and edit settings"""
    bl_idname = "jk.adc_set_selected"
    bl_label = "Set Selected"
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(name="Action", description="What this operator should do",
        items=[('USE_LOCATIONS', 'Use Locations', ""), ('USE_SCALES', 'Use Scales', ""), 
            ('SNAP_CONTROLS', 'Snap Controls', ""), ('SNAP_DEFORMS', 'Snap Deforms', "")],
        default='USE_LOCATIONS')
    
    use: BoolProperty(name="Use", default=True)

    def execute(self, context):
        armature = bpy.context.object
        controller = armature.data.jk_adc.get_controller()
        if controller.mode == 'EDIT':
            selected = [bb for bb in controller.data.bones if bb.jk_adc.has_deform and ((bb.jk_adc.get_control().select or bb.jk_adc.get_control().select_head or bb.jk_adc.get_control().select_tail) 
                    or (bb.jk_adc.get_deform() and (bb.jk_adc.get_deform().select or bb.jk_adc.get_deform().select_head or bb.jk_adc.get_deform().select_tail)))]
        else:
            selected = [bb for bb in controller.data.bones if bb.jk_adc.has_deform and (bb.select or (bb.jk_adc.get_deform() and bb.jk_adc.get_deform().bone.select))]
        for bb in selected:
            if self.action == 'SNAP_DEFORMS':
                bb.jk_adc.snap_deform = self.use
            elif self.action == 'SNAP_CONTROLS':
                bb.jk_adc.snap_control = self.use
            elif self.action == 'USE_LOCATIONS':
                bb.jk_adc.use_location = self.use
            elif self.action == 'USE_SCALES':
                bb.jk_adc.use_scale = self.use

        return {'FINISHED'}
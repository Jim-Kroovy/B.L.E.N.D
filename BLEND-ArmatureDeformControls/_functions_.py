import bpy
import json
import mathutils

def link_deform_armature(controller):
    # add deformer to the same collections as the controller and select it...
    deformer = controller.data.jk_adc.armature
    collections = [coll for coll in controller.users_collection if deformer.name not in coll.objects]
    for collection in collections:
        collection.objects.link(deformer)
    deformer.select_set(True)

def unlink_deform_armature(controller):
    # remove the deformer from all collections and make the controller active...
    deformer = controller.data.jk_adc.armature
    collections = [coll for coll in deformer.users_collection]
    deformer.select_set(False)
    for collection in collections:
        collection.objects.unlink(deformer)
    bpy.context.view_layer.objects.active = controller
    controller.select_set(True)

def get_armatures():
    obj, controller, deformer = bpy.context.view_layer.objects.active, None, None
    armature = obj if obj.type == 'ARMATURE' else obj.find_armature() if obj.type == 'MESH' else None
    if armature:
        if armature.data.jk_adc.is_controller:
            controller, deformer = armature, armature.data.jk_adc.armature
        elif armature.data.jk_adc.is_deformer:
            controller, deformer = armature.data.jk_adc.armature, armature
    return controller, deformer

def unset_controller_defaults(controller):
    # show deforms...
    is_hiding = controller.data.jk_adc.hide_deforms
    if is_hiding:
        controller.data.jk_adc.hide_deforms = False
    # turn off auto updates...
    is_updating = controller.data.jk_adc.use_auto_update
    if is_updating:
        controller.data.jk_adc.use_auto_update = False
    # make sure we aren't using the deforms...
    use_deforms = controller.data.jk_adc.use_deforms
    if use_deforms:
        controller.data.jk_adc.use_deforms = False
    # and if our constraints are reversed, un reverse them....
    use_reversed = controller.data.jk_adc.reverse_deforms
    if use_reversed:
        controller.data.jk_adc.reverse_deforms = False
    # return what the bools were
    return is_hiding, is_updating, use_deforms, use_reversed

def reset_controller_defaults(controller, is_hiding, is_updating, use_deforms, use_reversed):
    # if our constraints were reversed, reverse them....
    if use_reversed:
        controller.data.jk_adc.reverse_deforms = True
    # check we are using the deforms...
    if use_deforms:
        controller.data.jk_adc.use_deforms = True
    # turn auto updates back on...
    if is_updating:
        controller.data.jk_adc.use_auto_update = True
    # hide deforms...
    if is_hiding:
        controller.data.jk_adc.hide_deforms = True

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTY FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_deforms(controller):
    """Returns a dictionary of bone data, currently unused but might come in handy some day..."""
    controller.update_from_editmode()
    deforms = []
    for control in controller.pose.bones:
        deform = control.get_deform()
        # if we already have a deform bone...
        if deform:
            # append it's data...
            parent = deform.bone.parent.name if deform.bone.parent else ""
            head, tail = deform.bone.head_local, deform.bone.tail_local
            _, roll = deform.bone.AxisRollFromMatrix(deform.bone.matrix_local.to_3x3())
            deforms.append({'control' : control.name, 'head' : head, 'tail' : tail, 'roll' : roll, 'parent' : parent})
        else:
            # otherwise append the data it would initially have...
            parent = control.bone.parent.name if control.bone.parent else ""
            head, tail = control.bone.head_local, control.bone.tail_local
            _, roll = control.bone.AxisRollFromMatrix(control.bone.matrix_local.to_3x3())
            deforms.append({'control' : control.name, 'head' : head, 'tail' : tail, 'roll' : roll, 'parent' : parent})
    return deforms

def set_deforms(controller):
    last_mode = controller.mode
    if not controller.data.jk_adc.hide_deforms:
        controller.data.jk_adc.armature.select_set(True)
    if last_mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    controls = [eb for eb in controller.data.edit_bones if eb.jk_adc.has_deform]
    for control in controls:
        deform = control.jk_adc.get_deform()
        control.jk_adc.deform_head, control.jk_adc.deform_tail = deform.head, deform.tail
        control.jk_adc.deform_roll, control.jk_adc.deform_parent = deform.roll, deform.parent.name if deform.parent else ""
    bpy.ops.object.mode_set(mode=last_mode)

def hide_deforms(controller, hide):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    # if the deform/control armatures are combined into a single one...
    if controller.data.jk_adc.is_deformer:
        if controller.mode == 'EDIT':
            deforms = [eb.jk_adc.get_deform() for eb in controller.data.edit_bones if eb.jk_adc.has_deform]
            for deform in deforms:
                if deform:
                    deform.hide = hide
        else:
            deforms = [pb.jk_adc.get_deform() for pb in controller.pose.bones if pb.jk_adc.has_deform]
            for deform in deforms:
                if deform:
                    deform.bone.hide = hide
    # otherwise if we are using the dual armature method...
    else:
        last_mode = controller.mode
        deformer = controller.data.jk_adc.armature
        controller.data.jk_adc.is_editing = True
        if controller.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # if we are showing the deform armature...
        if not hide:
            # add deformer to the same collections as the controller and select it...
            link_deform_armature(controller)
            # ensuring it's name is correct...
            deformer.name, deformer.data.name = prefs.deform_prefix + controller.name, prefs.deform_prefix + controller.name
        else:
            # else we are hiding so remove deformer from all collections and make the controller active...
            unlink_deform_armature(controller)
            # ensuring it's name is correct...
            deformer.name, deformer.data.name = prefs.deform_prefix + controller.name, prefs.deform_prefix + controller.name
        bpy.ops.object.mode_set(mode=last_mode)
        controller.data.jk_adc.is_editing = False

def hide_controls(controller, hide):
    # just hide/unhide the control bones...
    if controller.mode == 'EDIT':
        controls = [eb for eb in controller.data.edit_bones if eb.jk_adc.has_deform]
        for control in controls:
            if control:
                control.hide = hide
    else:
        controls = [pb for pb in controller.pose.bones if pb.jk_adc.has_deform]
        for control in controls:
            if control:
                control.bone.hide = hide

def hide_others(controller, hide):
    # hiding bones that are not control or deform bones...
    if controller.mode == 'EDIT':
        others = [eb for eb in controller.data.edit_bones if not eb.jk_adc.has_deform]
        for other in others:
            if other:
                other.hide = hide
    else:
        others = [pb for pb in controller.pose.bones if pb.jk_adc.has_deform]
        for other in others:
            if other:
                other.bone.hide = hide

def use_deforms(controller, use):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    deformer = controller.data.jk_adc.armature
    #meshes = [ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.find_armature() == (deformer if use else controller)]
    meshes = [ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.find_armature() in [controller, deformer]]
    # get all the modifiers on the meshes that target one of the armatures...
    modifiers = [mod for mesh in meshes for mod in mesh.modifiers if mod.type == 'ARMATURE' and mod.object in [controller, deformer]]
    # remap them all to the correct armature...
    armature = deformer if use else controller
    for modifier in modifiers:
        if modifier.object != armature:
            modifier.object = armature
    # need to iterate on different bones depending on current mode...
    if controller.mode == 'EDIT':
        control_deforms = {eb : eb.jk_adc.get_deform() for eb in controller.data.edit_bones if eb.jk_adc.has_deform}
        for control, deform in control_deforms.items():
            if control and deform:
                control.use_deform, deform.use_deform = False if use else True, True if use else False
                # change any vertex groups on the meshes...
                for mesh in meshes:
                    # to relate to the deform bone instead of the control if using deforms...
                    group = mesh.vertex_groups.get(control.name if use else deform.name)
                    if group:
                        group.name = deform.name if use else control.name
    else:
        control_deforms = {pb : pb.jk_adc.get_deform() for pb in controller.pose.bones if pb.jk_adc.has_deform}
        for control, deform in control_deforms.items():
            if control and deform:
                control.bone.use_deform, deform.bone.use_deform = False if use else True, True if use else False
                # change any vertex groups on the meshes...
                for mesh in meshes:
                    # to relate to the deform bone instead of the control if using deforms...
                    group_name = control.name
                    group = mesh.vertex_groups.get(control.name if use else deform.name)
                    if group:
                        group.name = deform.name if use else control.name

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- CONSTRAINT FUNCTIONS ---------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def add_deform_constraints(armature, pb, bb, limits=True):
    if limits:
        # limit location...
        if pb.constraints.get("DEFORM - Limit Location"):
            limit_loc = pb.constraints.get("DEFORM - Limit Location")
        else:
            limit_loc = pb.constraints.new('LIMIT_LOCATION')
        limit_loc.name, limit_loc.show_expanded = "DEFORM - Limit Location", False
        limit_loc.use_min_x, limit_loc.use_min_y, limit_loc.use_min_z = True, True, True
        limit_loc.use_max_x, limit_loc.use_max_y, limit_loc.use_max_z = True, True, True
        limit_loc.owner_space = 'LOCAL_WITH_PARENT'
        # rotation...
        if pb.constraints.get("DEFORM - Limit Rotation"):
            limit_rot = pb.constraints.get("DEFORM - Limit Rotation")
        else:
            limit_rot = pb.constraints.new('LIMIT_ROTATION')
        limit_rot.name, limit_rot.show_expanded = "DEFORM - Limit Rotation", False
        limit_rot.use_limit_x, limit_rot.use_limit_y, limit_rot.use_limit_z = True, True, True
        limit_rot.owner_space = 'LOCAL_WITH_PARENT'
        # and scale, all in local with parent space...
        if pb.constraints.get("DEFORM - Limit Scale"):
            limit_sca = pb.constraints.get("DEFORM - Limit Scale")
        else:
            limit_sca = pb.constraints.new('LIMIT_SCALE')
        limit_sca.name, limit_sca.show_expanded = "DEFORM - Limit Scale", False
        limit_sca.use_min_x, limit_sca.use_min_y, limit_sca.use_min_z = True, True, True
        limit_sca.use_max_x, limit_sca.use_max_y, limit_sca.use_max_z = True, True, True
        limit_sca.min_x, limit_sca.min_y, limit_sca.min_z = 1.0, 1.0, 1.0
        limit_sca.max_x, limit_sca.max_y, limit_sca.max_z = 1.0, 1.0, 1.0
        limit_sca.owner_space = 'LOCAL_WITH_PARENT'
    # so the only transforms applied to the bone are from the child of constraint...
    if pb.constraints.get("DEFORM - Child Of"):
        child_of = pb.constraints.get("DEFORM - Child Of")
    else:
        child_of = pb.constraints.new('CHILD_OF')
    child_of.name, child_of.show_expanded = "DEFORM - Child Of", False
    child_of.target, child_of.subtarget = armature, bb.name
    child_of.inverse_matrix = bb.matrix_local.inverted() @ armature.matrix_world.inverted() #armature.matrix_parent_inverse#.inverted()#

def remove_deform_constraints(pb):
    names = ["DEFORM - Child Of", "DEFORM - Limit Scale", "DEFORM - Limit Rotation", "DEFORM - Limit Location", 
        "USE - Limit Scale", "USE - Limit Location"]
    for name in names:
        constraint = pb.constraints.get(name)
        if constraint:
            pb.constraints.remove(constraint)

def refresh_deform_constraints(controller, use_identity=False):
    if use_identity:
        # copy and clear the controllers world space transforms...
        control_mat = controller.matrix_world.copy()
        controller.matrix_world = mathutils.Matrix()
    # reset all the child of constraints... (regardless of reversal)
    controls = [pb for pb in controller.pose.bones if pb.jk_adc.has_deform]
    for control in controls:
        control.jk_adc.name = control.name
        deform = control.jk_adc.get_deform()
        if controller.data.jk_adc.reverse_deforms:
            deformer = controller.data.jk_adc.armature
            add_deform_constraints(deformer, control, deform.bone, limits=False)
        else:
            add_deform_constraints(controller, deform, control.bone, limits=False)
        control.jk_adc.use_location, control.jk_adc.use_scale = control.jk_adc.use_location, control.jk_adc.use_scale
    if use_identity:
        # and return the controllers matrix...
        controller.matrix_world = control_mat

def reverse_deform_constraints(controller, reverse):
    last_mode = controller.mode
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
    controls = [pb for pb in controller.pose.bones if pb.jk_adc.has_deform]
    armature = controller.data.jk_adc.armature if reverse else controller
    for control in controls:
        deform = control.jk_adc.get_deform()
        # remove the deformation constraints from one bone...
        remove_deform_constraints(deform if reverse else control)
        pb = control if reverse else deform
        bb = deform.bone if reverse else control.bone
        # mute/un-mute all constraints on the control bone...
        for con in control.constraints:
            con.mute = reverse
        # and add them to the other...
        add_deform_constraints(armature, pb, bb, limits=True)
        # ensuring we trigger the use location and scale updates... (to add those constraints)
        control.jk_adc.use_location, control.jk_adc.use_scale = control.jk_adc.use_location, control.jk_adc.use_scale
    
    bpy.ops.object.mode_set(mode=last_mode)
    # and return the controllers matrix...
    controller.matrix_parent_inverse = control_mat

def mute_deform_constraints(deformer, mute):
    controller = deformer.data.jk_adc.armature
    control_deforms = {pb : pb.jk_adc.get_deform() for pb in controller.pose.bones if pb.jk_adc.has_deform}
    for control, deform in control_deforms.items():
        if controller.data.jk_adc.reverse_deforms:
            pb = control
        else:
            pb = deform
        if pb:
            for con in pb.constraints:
                con.mute = mute

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- BONE FUNCTIONS ---------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_deform_parenting(deformer, control, prefix):
    bone, parent = control, ""
    # while we don't have a parent...
    while parent == "":
        # try and get the next parent in the deforming bones...
        parent = prefix + bone.parent.name if bone.parent and prefix + bone.parent.name in deformer.data.edit_bones else ""
        # always get the next parent...
        bone = bone.parent 
        # if there isn't a next parent...
        if bone == None:
            # break because we won't find one...
            break
    # return the parent...
    return parent

def set_control_orientation(control):
    has_target = False
    # if a bone has only one child...
    if len(control.children) == 1:
        child = control.children[0]
        # and as long as the childs head is not equal to the bones head...
        if child.head != control.head:
            # it's tail should probably point to it...
            control.tail = child.head
            has_target = True
    # if a bone has multiple children
    elif len(control.children) > 1:
        # iterate over the children...
        for child in control.children:
            # checking for these most likely places we will want to target...
            if any(string in child.name.upper() for string in ["NECK", "SPINE", "LOWER", "ELBOW", "KNEE", "CALF", "HAND", "WRIST", "FOOT", "ANKLE"]):
                # as long as the childs head is not equal to the bones head...
                if child.head != control.head:
                    # take the first match and break...
                    control.tail = child.head
                    has_target = True
                    break
    # if we couldn't find a suitable child target...
    if not has_target:
        # but the bone has a parent, we can align to it...
        if control.parent != None:
            control.align_orientation(control.parent)
        else:
            # otherwise let the console know that this bone couldn't be oriented...
            print("Automatic Orientation: Could not find anywhere to align", control.name, "so you are on your own with it...")

def add_deform_bone(self, deformer):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    prefix = prefs.deform_prefix if self.id_data.jk_adc.is_deformer else ""
    # controller is either going to be the deform armatures parent or the deformer... (depending on if combined or not)
    controller = deformer.parent if not self.id_data.jk_adc.is_deformer else deformer
    last_mode = controller.mode
    # create the new deform bone in edit mode...
    if last_mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    control_eb = self.id_data.edit_bones.get(self.name)
    deform_eb = deformer.data.edit_bones.new(prefix + self.name)
    deform_eb.head, deform_eb.tail, deform_eb.roll = self.deform_head, self.deform_tail, self.deform_roll
    deform_eb.parent = deformer.data.edit_bones.get(self.deform_parent)
    # the deform bone should always deform if we are not combined...
    deform_eb.use_deform = True if not self.id_data.jk_adc.is_deformer else self.id_data.jk_adc.use_deforms
    # the control bone should only deform if we are not using deforms...
    control_eb.use_deform = not self.id_data.jk_adc.use_deforms
    # update any relevant armature objects...
    deformer.update_from_editmode()
    if not self.id_data.jk_adc.is_deformer:
        controller.update_from_editmode()
    # get the deform and control pose bones and give them their constraints...
    deform_pb = deformer.pose.bones.get(prefix + self.name)
    control_pb = controller.pose.bones.get(self.name)
    control_pb.jk_adc.name = self.name
    control_bb = self.id_data.bones.get(self.name)
    add_deform_constraints(controller, deform_pb, control_bb)
    # by default we do not use scale...
    control_pb.jk_adc.use_scale = False
    # if we aren't doing this on an iteration, return the mode...
    if not self.id_data.jk_adc.is_iterating:
        bpy.ops.object.mode_set(mode=last_mode)
        # and if we are not showing deforms, hide them...
        if controller.data.jk_adc.hide_deforms:
            hide_deforms(controller, True)

def remove_deform_bone(self, deformer, deform):
    # controller is either going to be the deform armatures parent or the deformer... (depending on if combined or not)
    controller = deformer.parent if not self.id_data.jk_adc.is_deformer else deformer
    last_mode = controller.mode
    if last_mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    if deform:
        deformer.data.edit_bones.remove(deform)
    deformer.update_from_editmode()
    # if we aren't doing this on an iteration, return the mode...
    if not self.id_data.jk_adc.is_iterating:
        bpy.ops.object.mode_set(mode=last_mode)
        # and if we are not showing deforms, hide them...
        if controller.data.jk_adc.hide_deforms:
            hide_deforms(controller, True)

def add_deform_bones(controller, only_selected, only_deforms):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    last_mode = controller.mode
    if last_mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    # easier to just iterate on all pose bones that do not currently have deforms...
    controls = [eb for eb in controller.data.edit_bones if not (eb.jk_adc.has_deform or eb.name.startswith(prefs.deform_prefix))]
    controller.data.jk_adc.is_iterating = True
    controller.data.jk_adc.is_editing = True
    for control in controls:
        control.jk_adc.name, parent_name = control.name, control.parent.name if control.parent else ""
        control.jk_adc.deform_head, control.jk_adc.deform_tail = control.head, control.tail
        control.jk_adc.deform_roll, control.jk_adc.deform_parent = control.roll, parent_name
        # then check through selection and deformation bools to see if we should add it...
        if only_selected and only_deforms:
            if control.select and control.use_deform:
                control.jk_adc.has_deform = True
        elif only_selected:
            if control.select:
                control.jk_adc.has_deform = True
        elif only_deforms:
            if control.use_deform:
                control.jk_adc.has_deform = True
        else:
            control.jk_adc.has_deform = True
    controller.data.jk_adc.is_iterating = False
    controller.data.jk_adc.is_editing = False
    bpy.ops.object.mode_set(mode=last_mode)

def update_deform_bones(controller, only_selected, only_deforms, orient_controls=False, parent_deforms=False):
    last_mode, deformer = controller.mode, controller.data.jk_adc.armature
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    prefix = prefs.deform_prefix if controller.data.jk_adc.is_deformer else ""
    if last_mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    # easier to just iterate on all edit bones that currently have deforms...
    control_deforms = {eb : eb.jk_adc.get_deform() for eb in controller.data.edit_bones if eb.jk_adc.has_deform}
    controller.data.jk_adc.is_iterating = True
    controller.data.jk_adc.is_editing = True
    for control, deform in control_deforms.items():
        control.jk_adc.name, control.jk_adc.control_head = control.name, control.head
        control.jk_adc.deform_head, control.jk_adc.deform_tail = deform.head, deform.tail
        control.jk_adc.deform_roll, control.jk_adc.deform_parent = deform.roll, deform.parent.name if deform.parent else ""
        # then check through selection and deformation bools to see if we should orient controls and parent deforms...
        if only_selected and only_deforms:
            if orient_controls:
                set_control_orientation(control)
            if parent_deforms:
                parent_name = get_deform_parenting(deformer, control, prefix)
                deform.parent = deformer.data.edit_bones.get(parent_name)
                control.jk_adc.deform_parent = parent_name
        elif only_selected:
            if orient_controls:
                set_control_orientation(control)
            if parent_deforms:
                parent_name = get_deform_parenting(deformer, control, prefix)
                deform.parent = deformer.data.edit_bones.get(parent_name)
                control.jk_adc.deform_parent = parent_name
        elif only_deforms:
            if orient_controls:
                set_control_orientation(control)
            if parent_deforms:
                parent_name = get_deform_parenting(deformer, control, prefix)
                deform.parent = deformer.data.edit_bones.get(parent_name)
                control.jk_adc.deform_parent = parent_name
        else:
            if orient_controls:
                set_control_orientation(control)
            if parent_deforms:
                parent_name = get_deform_parenting(deformer, control, prefix)
                deform.parent = deformer.data.edit_bones.get(parent_name)
                control.jk_adc.deform_parent = parent_name
    # we can just always update all of the pose bone property names...
    controls = [pb for pb in controller.pose.bones if pb.jk_adc.has_deform]
    for control in controls:
        control.jk_adc.name = control.name
    bpy.ops.object.mode_set(mode=last_mode)
    controller.data.jk_adc.is_iterating = False
    controller.data.jk_adc.is_editing = False

def remove_deform_bones(controller, only_selected, only_deforms):
    last_mode = controller.mode
    if last_mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    # easier to just iterate on all pose bones that currently have deforms...
    controls = [eb for eb in controller.data.edit_bones if eb.jk_adc.has_deform]
    controller.data.jk_adc.is_iterating = True
    for control in controls:
        # setting the edit bone settings incase we are removing to combine/un-combine...
        control.jk_adc.name, parent_name = control.name, control.parent.name if control.parent else ""
        control.jk_adc.deform_head, control.jk_adc.deform_tail = control.head, control.tail
        control.jk_adc.deform_roll, control.jk_adc.deform_parent = control.roll, parent_name
        # then check through selection and deformation bools to see if we should remove it...
        if only_selected and only_deforms:
            if control.bone.select and control.bone.use_deform:
                control.jk_adc.has_deform = False
        elif only_selected:
            if control.bone.select:
                control.jk_adc.has_deform = False
        elif only_deforms:
            if control.bone.use_deform:
                control.jk_adc.has_deform = False
        else:
            control.jk_adc.has_deform = False
    controller.data.jk_adc.is_iterating = False
    bpy.ops.object.mode_set(mode=last_mode)

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- MODE FUNCTIONS ---------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def jk_adc_auto_update_timer():
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    # need to be sure this is only firing on armatures...
    armature = bpy.context.object if bpy.context.object and bpy.context.object.type == 'ARMATURE' else None
    if armature and armature.mode == 'EDIT':
        controller = armature if armature.data.jk_adc.is_controller else armature.data.jk_adc.armature
        #print("AUTO UPDATE", controller, armature)
        if not controller.data.jk_adc.is_editing:
            # for every selected control/deform edit bone in the armature...
            selected = [eb for eb in controller.data.edit_bones if eb.jk_adc.has_deform and ((eb.select or eb.select_head) or (eb.jk_adc.get_deform() and (eb.jk_adc.get_deform().select or eb.jk_adc.get_deform().select)))]
            for eb in selected:
                # set it's offset... (the get functions of control and deform locations trigger snapping)
                eb.jk_adc.offset = eb.jk_adc.control_location - eb.jk_adc.deform_location
    # check this at the users preference of frequency...
    return prefs.auto_freq

def subscribe_mode_to(obj, callback):
    # get the data path to sub and assign it to the msgbus....
    subscribe_to = obj.path_resolve('mode', False)
    bpy.msgbus.subscribe_rna(key=subscribe_to, owner=obj, args=(obj, 'mode'), notify=callback, options={"PERSISTENT"})
    

def armature_mode_callback(armature, data):
    # all pointers now get broken by Blenders undo system, so just iterate on all selected armatures...
    for armature in [ob for ob in bpy.context.selected_objects if ob.type == 'ARMATURE']:
        print("MODE", armature.name)
        if armature and armature.data.jk_adc.is_controller:
            # get controller and deformer references...
            controller = armature if armature.data.jk_adc.is_controller else armature.data.jk_adc.armature
            is_combined = controller.data.jk_adc.use_combined
            # and we are switching into edit mode...
            if controller.mode == 'EDIT' and not controller.data.jk_adc.is_editing:
                # if we aren't using combined armatures...
                if not is_combined:
                    # make sure the deformer goes into edit mode with the controller...
                    controller.data.jk_adc.hide_deforms = False
                set_deforms(controller)
                # and if the controller is auto updating...
                if controller.data.jk_adc.use_auto_update:
                    # if we are in edit mode and the update timer is not ticking...
                    if not bpy.app.timers.is_registered(jk_adc_auto_update_timer):
                        # give it a kick in the arse...
                        bpy.app.timers.register(jk_adc_auto_update_timer)
            else:
                # if we are not in edit mode and the update timer is ticking...
                if bpy.app.timers.is_registered(jk_adc_auto_update_timer):
                    # give it a kick in the face...
                    bpy.app.timers.unregister(jk_adc_auto_update_timer)
                # update all the constraints...
                refresh_deform_constraints(armature, use_identity=True)

            
"""def mesh_mode_callback(mesh, data):
    # comprehend a dictionary of the armatures we might need to edit and iterate on it...
    controllers = [mod.object for mod in mesh.modifiers if mod.type == 'ARMATURE' and mod.object and mod.object.data.jk_adc.is_controller]
    for controller in controllers:
        deforms = json.loads(controller.data.jk_adc.deforms)
        # check the armature has controls and wants to auto hide or sync locations...
        if deforms:
            # then if we are going into weight paint mode...
            if mesh.mode == 'WEIGHT_PAINT':
                # show the only the bones deforming the mesh...
                if controller.use_deforms:
                    controller.data.jk_adc.hide_deforms = False
                    controller.data.jk_adc.hide_controls = True
                else:
                    controller.data.jk_adc.hide_deforms = True
                    controller.data.jk_adc.hide_controls = False
                controller.data.jk_adc.hide_others = True
            else:
                # otherwise show the only the bones that are not deforming the mesh...
                if controller.use_deforms:
                    controller.data.jk_adc.hide_deforms = True
                    controller.data.jk_adc.hide_controls = False
                else:
                    controller.data.jk_adc.hide_deforms = False
                    controller.data.jk_adc.hide_controls = True
                controller.data.jk_adc.hide_others = False
                
def set_meshes(armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    # iterate on all meshes with armature modifiers targeting the armature...
    for mesh in [o for o in bpy.data.objects if o.type == 'MESH' and any(mod.type == 'ARMATURE' and mod.object == armature for mod in o.modifiers)]:
        # if that meshes name is not in the subscribed meshes...
        if mesh.name not in prefs.meshes:
            # sub and add it...
            subscribe_mode_to(mesh, mesh_mode_callback)
            m = prefs.meshes.add()
            m.name, m.armature = mesh.name, armature.name
    # then iterate over all subbed meshes...
    for m in prefs.meshes:
        # getting rid of any that don't exist anymore...
        if m.name not in bpy.data.objects:
            mi = prefs.meshes.find(m.name)
            prefs.meshes.remove(mi)"""

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- ARMATURE FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_deform_actions(controller, only_active):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    actions = {}
    if controller.animation_data:
        if only_active:
            action = controller.animation_data.action
            actions = {action : bpy.data.actions.get(prefs.deform_prefix + action.name)}
        else:
            actions = {act : bpy.data.actions.get(prefs.deform_prefix + act.name) for act in bpy.data.actions 
                if any(fc.data_path.partition('"')[2].split('"')[0] in controller.data.bones for fc in act.fcurves) 
                and not act.name.startswith(prefs.deform_prefix)}
    return actions

def add_deform_armature(controller):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    # create a new deformer armature that copies the transforms of the controller...
    deformer_data = bpy.data.armatures.new(prefs.deform_prefix + controller.name)
    deformer = bpy.data.objects.new(prefs.deform_prefix + controller.name, deformer_data)
    deformer.use_fake_user, deformer.parent = True, controller
    # add deformer to the same collections as the controller and select it...
    collections = [coll for coll in controller.users_collection if deformer.name not in coll.objects]
    for collection in collections:
        collection.objects.link(deformer)
    deformer.select_set(True)
    # set the pointer and bools on both armatures...
    controller.data.jk_adc.is_controller = True
    controller.data.jk_adc.is_deformer = False
    controller.data.jk_adc.armature = deformer
    deformer.data.jk_adc.is_deformer = True
    deformer.data.jk_adc.armature = controller

def remove_deform_armature(controller):
    # unlink the deforming armature and show the controls...
    hide_deforms(controller, True)
    hide_controls(controller, False)
    # and we don't want to be using deform bones during execution...
    is_using_deforms = controller.data.jk_adc.use_deforms
    if is_using_deforms:
        controller.data.jk_adc.use_deforms = False
    # remove the deformers data and object...
    deformer_data = controller.data.jk_adc.armature.data
    bpy.data.objects.remove(controller.data.jk_adc.armature)
    bpy.data.armatures.remove(deformer_data)
    # unset the controllers pointer and bool...
    controller.data.jk_adc.is_controller = False
    controller.data.jk_adc.armature = None

def set_combined(controller, combine):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    last_mode = controller.mode
    controller.data.jk_adc.is_iterating = True
    controller.data.jk_adc.is_editing = True
    # if we aren't in object mode, switch to it...
    if last_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    # get the settings the controller is currently using, and set them to default...
    is_hiding, is_updating, use_deforms, use_reversed = unset_controller_defaults(controller)
    # need to make sure all the deform bone head locations are up to date...
    set_deforms(controller)
    # if we are combining dual armature deform/controls to single armature...
    if combine:
        # kill the deform armature...
        remove_deform_armature(controller)
        # set the pointer and bools... (when combined the controller just references itself)
        controller.data.jk_adc.is_controller = True
        controller.data.jk_adc.is_deformer = True
        controller.data.jk_adc.armature = controller
        bpy.ops.object.mode_set(mode='EDIT')
        # re-add all the deform bones to the control armature...
        controls = [eb for eb in controller.data.edit_bones if eb.jk_adc.has_deform]
        for control in controls:
            # updating the parent names to have the deform prefix...
            if control.jk_adc.deform_parent:
                control.jk_adc.deform_parent = prefs.deform_prefix + control.jk_adc.deform_parent
            # but not changing the saved deform positions before triggering the add update...
            control.jk_adc.has_deform = True
        # update any relevant armature objects...
        controller.update_from_editmode()
        refresh_deform_constraints(controller, use_identity=True)
    # otherwise we want to convert single armature deform/controls to dual armature...
    else:
        # just remove all the deform bones...
        bpy.ops.object.mode_set(mode='EDIT')
        controls = [eb for eb in controller.data.edit_bones if eb.jk_adc.has_deform]
        for control in controls:
            deform = control.jk_adc.get_deform()
            controller.data.edit_bones.remove(deform)
        # create the deform armature...
        bpy.ops.object.mode_set(mode='OBJECT')
        add_deform_armature(controller)
        bpy.ops.object.mode_set(mode='EDIT')
        # and re-add all the deforms to it...
        controls = [eb for eb in controller.data.edit_bones if eb.jk_adc.has_deform]
        for control in controls:
            # updating the names to no longer have the deform prefix...
            control.jk_adc.deform_parent = control.jk_adc.deform_parent[len(prefs.deform_prefix):]
            # but not changing the saved deform positions before triggering the add update...
            control.jk_adc.has_deform = True
        controller.data.jk_adc.armature.update_from_editmode()
        controller.update_from_editmode()
        refresh_deform_constraints(controller, use_identity=True)
    # set our mode back...
    bpy.ops.object.mode_set(mode=last_mode)
    # and set the controllers settings back...
    reset_controller_defaults(controller, is_hiding, is_updating, use_deforms, use_reversed)
    controller.data.jk_adc.is_iterating = False
    controller.data.jk_adc.is_editing = False
    

    
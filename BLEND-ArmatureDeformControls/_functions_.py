import bpy
import json
import mathutils

def link_deform_armature(controller):
    # add deformer to the same collections as the controller and select it...
    deformer = controller.data.jk_adc.get_deformer()
    collections = [coll for coll in controller.users_collection if deformer.name not in coll.objects]
    for collection in collections:
        collection.objects.link(deformer)
    deformer.select_set(True)

def unlink_deform_armature(controller):
    # remove the deformer from all collections and make the controller active...
    deformer = controller.data.jk_adc.get_deformer()
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
        controller, deformer = armature.data.jk_adc.get_armatures()
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

def get_duplicate_name(new_name, old_name):
    # when bones get duplicated or mirrored we need to figure out what the new name is...
    name, suffix, prefix, is_found = new_name, "", "", False
    # first we check/get the new number affix...
    new_suffix = name.split(".")[-1]
    if new_suffix.isdigit():
        suffix = "." + new_suffix
        name = name[:-len(suffix)]
    old_suffix = ("." + old_name.split(".")[-1]) if old_name.split(".")[-1].isdigit() else ""
    # then we check through name mirror suffices and prefices...
    startswiths = {"left" : "right", "l_" : "r_", "l." : "r."}
    endswiths = {"left" : "right", "_l" : "_r", ".l" : ".r"}
    # blender prioritizes mirror suffices so check them first... (eg: "Left_Bone_L" will mirror to "Left_Bone_R")
    for ls, rs in endswiths.items():
        if (name.lower().endswith(ls) and old_name[:-len(old_suffix)].lower().endswith(rs)) or (name.lower().endswith(rs) and old_name[:-len(old_suffix)].lower().endswith(ls)):
            if name.lower().endswith(ls):
                case = name[len(name) - len(ls):]
                suffix = ((rs[0].upper() + rs[1:] if case[0].isupper() else rs) if ls[0].isalpha() else (rs[0] + rs[1].upper() if case[1].isupper() else rs)) + suffix
                name = name[:-len(ls)]
                is_found = True
                break
            elif name.lower().endswith(rs):
                case = name[len(name) - len(rs):]
                suffix = ((ls[0].upper() + ls[1:] if case[0].isupper() else ls) if rs[0].isalpha() else (ls[0] + ls[1].upper() if case[1].isupper() else ls)) + suffix
                name = name[:-len(rs)]
                is_found = True
                break
    # and if we didn't find a mirror suffix we check through mirror prefices...
    if not is_found:
        for ls, rs in startswiths.items():
            if (name.lower().startswith(ls) and old_name[:-len(old_suffix)].lower().startswith(rs)) or (name.lower().startswith(rs) and old_name[:-len(old_suffix)].lower().startswith(ls)):
                if name.lower().startswith(ls):
                    case = name[len(ls):]
                    prefix = rs[0].upper() + rs[1:] if case[0].isupper() else rs
                    name = name[len(ls):]
                    break
                elif name.lower().startswith(rs):
                    case = name[len(rs):]
                    prefix = ls[0].upper() + ls[1:] if case[0].isupper() else ls
                    name = name[len(rs):]
                    break
    return prefix + name + suffix

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTY FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def set_deforms(controller):
    last_mode = controller.mode
    controller.data.jk_adc.is_editing = True
    deforms = {}
    # if we aren't in edit mode, switch to it...
    if last_mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    # nothing bloody sticks when you set it in edit mode...
    names = [bb.name for bb in controller.data.bones if bb.jk_adc.has_deform]
    for name in names:
        # so go through the fuckery of getting all the deform data into a dictionary...
        bb = controller.data.bones.get(name)
        eb = bb.jk_adc.get_deform()
        deforms[name] = [eb.head.copy(), eb.tail.copy(), eb.roll, eb.parent.name if eb.parent else ""]
    # then swap to object mode and set it where it will stick...
    bpy.ops.object.mode_set(mode='OBJECT')
    for name in names:
        bb = controller.data.bones.get(name)
        bb.jk_adc.deform_head, bb.jk_adc.deform_tail, bb.jk_adc.deform_roll = deforms[name][0], deforms[name][1], deforms[name][2]
        bb.jk_adc.deform_parent = deforms[name][3]
    # set our mode back...
    if controller.mode != last_mode:
        bpy.ops.object.mode_set(mode=last_mode)
    controller.data.jk_adc.is_editing = False

def hide_deforms(controller, hide):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    # if the deform/control armatures are combined into a single one...
    if controller.data.jk_adc.is_deformer:
        deforms = controller.data.jk_adc.get_deforms()
        for deform in deforms.keys():
            if deform:
                if controller.mode == 'EDIT':
                    deform.hide = hide
                else:
                    deform.bone.hide = hide
    # otherwise if we are using the dual armature method...
    else:
        last_mode = controller.mode
        deformer = controller.data.jk_adc.get_deformer()
        controller.data.jk_adc.is_editing = True
        if controller.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # ensure it's name is correct...
        deformer.name, deformer.data.name = prefs.deform_prefix + controller.name, prefs.deform_prefix + controller.name
        # if we are showing the deform armature...
        if not hide:
            # add deformer to the same collections as the controller and select it...
            link_deform_armature(controller)
        else:
            # else we are hiding so remove deformer from all collections and make the controller active...
            unlink_deform_armature(controller)
        bpy.ops.object.mode_set(mode=last_mode)
        controller.data.jk_adc.is_editing = False

def hide_controls(controller, hide):
    # just hide/unhide the control bones...
    controls = controller.data.jk_adc.get_controls()
    for control in controls.keys():
        if control:
            if controller.mode == 'EDIT':
                control.hide = hide
            else:
                control.bone.hide = hide

def hide_others(controller, hide):
    # hiding bones that are not control or deform bones...
    controls = controller.data.jk_adc.get_controls()
    deforms = controller.data.jk_adc.get_deforms()
    for bb in controller.data.bones:
        other = bb.jk_adc.get_control()
        if other and not (bb in controls or bb in deforms):
            if controller.mode == 'EDIT':
                other.hide = hide
            else:
                other.bone.hide = hide

def use_deforms(controller, use):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    deformer = controller.data.jk_adc.get_deformer()
    #meshes = [ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.find_armature() == (deformer if use else controller)]
    meshes = [ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.find_armature() in [controller, deformer]]
    # get all the modifiers on the meshes that target one of the armatures...
    modifiers = [mod for mesh in meshes for mod in mesh.modifiers if mod.type == 'ARMATURE' and mod.object in [controller, deformer]]
    # remap them all to the correct armature...
    armature = deformer if use else controller
    for modifier in modifiers:
        if modifier.object != armature:
            modifier.object = armature
    # and update vertex group names...
    controls = controller.data.jk_adc.get_controls()
    for control, deform in controls.items():
        if control and deform:
            if controller.mode == 'EDIT':
                control.use_deform, deform.use_deform = False if use else True, True if use else False
            else:
                control.bone.use_deform, deform.bone.use_deform = False if use else True, True if use else False
            # change any vertex groups on the meshes...
            for mesh in meshes:
                # to relate to the deform bone instead of the control if using deforms...
                group = mesh.vertex_groups.get(control.name if use else deform.name)
                if group:
                    group.name = deform.name if use else control.name
        else:
            print("[USE DEFORMS]", "Somethings not quite right here... Control:", control, "Deform:", deform)

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
        pb.constraints.move(pb.constraints.find(limit_loc.name), 0)
        # rotation...
        if pb.constraints.get("DEFORM - Limit Rotation"):
            limit_rot = pb.constraints.get("DEFORM - Limit Rotation")
        else:
            limit_rot = pb.constraints.new('LIMIT_ROTATION')
        limit_rot.name, limit_rot.show_expanded = "DEFORM - Limit Rotation", False
        limit_rot.use_limit_x, limit_rot.use_limit_y, limit_rot.use_limit_z = True, True, True
        limit_rot.owner_space = 'LOCAL_WITH_PARENT'
        pb.constraints.move(pb.constraints.find(limit_rot.name), 1)
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
        pb.constraints.move(pb.constraints.find(limit_sca.name), 2)
    # so the only transforms applied to the bone are from the child of constraint...
    if pb.constraints.get("DEFORM - Child Of"):
        child_of = pb.constraints.get("DEFORM - Child Of")
    else:
        child_of = pb.constraints.new('CHILD_OF')
    child_of.name, child_of.show_expanded = "DEFORM - Child Of", False
    child_of.target, child_of.subtarget = armature, bb.name
    child_of.inverse_matrix = bb.matrix_local.inverted() @ armature.matrix_world.inverted() #armature.matrix_parent_inverse#.inverted()#
    pb.constraints.move(pb.constraints.find(child_of.name), 3)

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
    bbs = controller.data.jk_adc.get_bones()
    for bb in bbs:
        control, deform = bb.jk_adc.get_control(), bb.jk_adc.get_deform()
        if control and deform:
            if controller.data.jk_adc.reverse_deforms:
                deformer = controller.data.jk_adc.get_deformer()
                add_deform_constraints(deformer, control, deform.bone, limits=True)
            else:
                add_deform_constraints(controller, deform, control.bone, limits=True)
            bb.jk_adc.use_location, bb.jk_adc.use_scale = bb.jk_adc.use_location, bb.jk_adc.use_scale
        else:
            print("[REFRESH CONSTRAINTS]", "Somethings not quite right here... Control:", control, "Deform:", deform)
    if use_identity:
        # and return the controllers matrix...
        controller.matrix_world = control_mat

def mute_deform_constraints(deformer, mute):
    controller = deformer.data.jk_adc.get_controller()
    controls = controller.data.jk_adc.get_controls()
    for control, deform in controls.items():
        pb = control if controller.data.jk_adc.reverse_deforms else deform
        if pb:
            for con in pb.constraints:
                con.mute = mute

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- BONE FUNCTIONS ---------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_deform_parenting(deformer, control):
    # get the deform prefix if it's needed...
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    prefix = "" if deformer.data.jk_adc.is_controller else prefs.deform_prefix
    bone, parent = control, ""
    # while we don't have a parent...
    while parent == "":
        # try and get the next parent in the deforming bones...
        parent = prefix + bone.parent.name if bone.parent and deformer.data.edit_bones.get(prefix + bone.parent.name) else ""
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

def add_deform_bone(bb, controller, deformer):
    # get the deform prefix if it's needed...
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    prefix = prefs.deform_prefix if controller.data.jk_adc.is_deformer else ""
    # and add/return a deform bone based from the deform data held by the control bone
    eb = deformer.data.edit_bones.new(prefix + bb.jk_adc.last_name)
    eb.head, eb.tail, eb.roll = bb.jk_adc.deform_head, bb.jk_adc.deform_tail, bb.jk_adc.deform_roll

def set_deform_bone(controller, deformer, bb, eb):
    # if there is no saved parent bone...
    if not bb.jk_adc.deform_parent:
        # try to find the deforms parent the deform bones parent...
        parent = get_deform_parenting(deformer, bb)
        # using the controls parent if we didn't find one, if it even has one...
        bb.jk_adc.deform_parent = parent if parent else bb.parent.name if bb.parent else ""
    eb.parent = deformer.data.edit_bones.get(bb.jk_adc.deform_parent)
    # the deform bone should always deform if we are not combined...
    eb.use_deform = True if not controller.data.jk_adc.is_deformer else controller.data.jk_adc.use_deforms

def get_add_names(controller, only_selected, only_deforms):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    names = [bb.name for bb in controller.data.bones if not (bb.jk_adc.has_deform or bb.name.startswith(prefs.deform_prefix))]
    new_names = []
    # then check through selection and deformation bools to see if we should add it...
    for name in names:
        bb = controller.data.bones.get(name)
        if only_selected and only_deforms:
            if bb.select and bb.use_deform:
                new_names.append(name)
        elif only_selected:
            if bb.select:
                new_names.append(name)
        elif only_deforms:
            if bb.use_deform:
                new_names.append(name)
        else:
            new_names.append(name)
    return new_names

def add_deform_bones(controller, deformer, names):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    prefix = prefs.deform_prefix if controller.data.jk_adc.is_deformer else ""
    controller.data.jk_adc.is_iterating, controller.data.jk_adc.is_editing = True, True
    # create the new deform bones in edit mode...
    last_mode = controller.mode
    if last_mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    # for each bone we are adding a deform for...
    for name in names:
        bb = controller.data.bones.get(name)
        # if this bone does not have deform transforms, give it some...
        if not bb.jk_adc.last_name:
            eb = controller.data.edit_bones.get(bb.name)
            parent_name = bb.parent.name if bb.parent else ""
            bb.jk_adc.last_name = bb.name
            bb.jk_adc.deform_head, bb.jk_adc.deform_tail = eb.head, eb.tail
            bb.jk_adc.deform_roll, bb.jk_adc.deform_parent = eb.roll, parent_name
        # before adding the deform bone to deforming armature...
        add_deform_bone(bb, controller, deformer)
    # then iterate again to set parenting and deformation...
    for name in names:
        bb = controller.data.bones.get(name)
        eb = deformer.data.edit_bones.get(prefix + name)
        set_deform_bone(controller, deformer, bb, eb)
    # then hope out into pose mode and add contraints...
    bpy.ops.object.mode_set(mode='POSE')
    for name in names:
        bb = controller.data.bones.get(name)
        pb = deformer.pose.bones.get(prefix + bb.name)
        add_deform_constraints(controller, pb, bb, limits=True)
        # the control bone should only deform if we are not using deforms...
        bb.use_deform = not controller.data.jk_adc.use_deforms
        bb.jk_adc.has_deform = True
    if controller.mode != last_mode:
        bpy.ops.object.mode_set(mode=last_mode)
    controller.data.jk_adc.is_iterating, controller.data.jk_adc.is_editing = False, False

def remove_deform_bone(deformer, bb, eb):
    if eb:
        deformer.data.edit_bones.remove(eb)

def get_remove_names(controller, only_selected, only_deforms):
    names = [bb.name for bb in controller.data.bones if bb.jk_adc.has_deform]
    old_names = []
    # then check through selection and deformation bools to see if we should add it...
    for name in names:
        bb = controller.data.bones.get(name)
        if only_selected and only_deforms:
            if bb.select and bb.use_deform:
                old_names.append(name)
        elif only_selected:
            if bb.select:
                old_names.append(name)
        elif only_deforms:
            if bb.use_deform:
                old_names.append(name)
        else:
            old_names.append(name)
    return old_names

def remove_deform_bones(controller, deformer, names):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    prefix = prefs.deform_prefix if controller.data.jk_adc.is_deformer else ""
    controller.data.jk_adc.is_iterating, controller.data.jk_adc.is_editing = True, True
    last_mode = controller.mode
    if last_mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    # it is such bullshit...
    for name in names:
        bb = controller.data.bones.get(name)
        eb = deformer.data.edit_bones.get(prefix + name)
        remove_deform_bone(deformer, bb, eb)
    bpy.ops.object.mode_set(mode='OBJECT')
    # that i can't set a single bool from edit mode...
    for name in names:
        bb = controller.data.bones.get(name)
        bb.jk_adc.has_deform = False
    if controller.mode != last_mode:
        bpy.ops.object.mode_set(mode=last_mode)
    controller.data.jk_adc.is_iterating, controller.data.jk_adc.is_editing = False, False

def update_deform_bones(controller, only_selected, only_deforms, orient_controls=False, parent_deforms=False):
    last_mode, deformer = controller.mode, controller.data.jk_adc.get_deformer()
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    prefix = prefs.deform_prefix if controller.data.jk_adc.is_deformer else ""
    if last_mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    # easier to just iterate on all edit bones that currently have deforms...
    bbs = controller.data.jk_adc.get_bones()
    controller.data.jk_adc.is_iterating = True
    controller.data.jk_adc.is_editing = True
    for bb in bbs:
        control, deform = bb.jk_adc.get_control(), bb.jk_adc.get_deform()
        if control and deform:
            bb.jk_adc.control_head = control.head
            bb.jk_adc.deform_head, bb.jk_adc.deform_tail = deform.head, deform.tail
            bb.jk_adc.deform_roll, bb.jk_adc.deform_parent = deform.roll, deform.parent.name if deform.parent else ""
            # then check through selection and deformation bools to see if we should orient controls and parent deforms...
            if only_selected and only_deforms:
                if orient_controls:
                    set_control_orientation(control)
                if parent_deforms:
                    parent_name = get_deform_parenting(deformer, control, prefix)
                    deform.parent = deformer.data.edit_bones.get(parent_name)
                    bb.jk_adc.deform_parent = parent_name
            elif only_selected:
                if orient_controls:
                    set_control_orientation(control)
                if parent_deforms:
                    parent_name = get_deform_parenting(deformer, control, prefix)
                    deform.parent = deformer.data.edit_bones.get(parent_name)
                    bb.jk_adc.deform_parent = parent_name
            elif only_deforms:
                if orient_controls:
                    set_control_orientation(control)
                if parent_deforms:
                    parent_name = get_deform_parenting(deformer, control, prefix)
                    deform.parent = deformer.data.edit_bones.get(parent_name)
                    bb.jk_adc.deform_parent = parent_name
            else:
                if orient_controls:
                    set_control_orientation(control)
                if parent_deforms:
                    parent_name = get_deform_parenting(deformer, control, prefix)
                    deform.parent = deformer.data.edit_bones.get(parent_name)
                    bb.jk_adc.deform_parent = parent_name
        else:
            print("[UPDATE BONES]", "Somethings not quite right here... Control:", control, "Deform:", deform)
    bpy.ops.object.mode_set(mode=last_mode)
    controller.data.jk_adc.is_iterating = False
    controller.data.jk_adc.is_editing = False
#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- MODE FUNCTIONS ---------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def jk_adc_auto_update_timer():
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    # need to be sure this is only firing on armatures...
    armature = bpy.context.object if bpy.context.object and bpy.context.object.type == 'ARMATURE' else None
    if armature and armature.mode == 'EDIT':
        controller = armature.data.jk_adc.get_controller()
        if not controller.data.jk_adc.is_editing:
            # for every selected control/deform edit bone in the armature...
            selected = [bb for bb in controller.data.bones if bb.jk_adc.get_deform() and ((bb.get_control().select or bb.get_control().select_head) or (bb.jk_adc.get_deform() and (bb.jk_adc.get_deform().select or bb.jk_adc.get_deform().select)))]
            for bb in selected:
                # set it's offset... (the get functions of control and deform locations trigger snapping)
                bb.jk_adc.offset = bb.jk_adc.control_location - bb.jk_adc.deform_location
    # check this at the users preference of frequency...
    return prefs.auto_freq

def subscribe_mode_to(obj, callback):
    # get the data path to sub and assign it to the msgbus....
    subscribe_to = obj.path_resolve('mode', False)
    bpy.msgbus.subscribe_rna(key=subscribe_to, owner=obj, args=(obj, 'mode'), notify=callback, options={"PERSISTENT"})

def armature_mode_callback(armature, data):
    # all pointers now get broken by Blenders undo system, so just iterate on all selected armatures...
    for armature in [ob for ob in bpy.context.selected_objects if ob.type == 'ARMATURE']:
        if armature and armature.data.jk_adc.is_controller:
            # get controller and deformer references...
            controller = armature.data.jk_adc.get_controller()
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
    # set the bools on both armatures...
    controller.data.jk_adc.is_controller = True
    controller.data.jk_adc.is_deformer = False
    deformer.data.jk_adc.is_deformer = True
    return deformer

def remove_deform_armature(controller):
    # unlink the deforming armature and show the controls...
    hide_deforms(controller, True)
    hide_controls(controller, False)
    # and we don't want to be using deform bones during execution...
    is_using_deforms = controller.data.jk_adc.use_deforms
    if is_using_deforms:
        controller.data.jk_adc.use_deforms = False
    # remove the deformers data and object...
    deformer = controller.data.jk_adc.get_deformer()
    deformer_data = deformer.data
    bpy.data.objects.remove(deformer)
    bpy.data.armatures.remove(deformer_data)
    # unset the controllers bool...
    controller.data.jk_adc.is_controller = False

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
        # re-add all the deform bones to the control armature...
        names = [bb.name for bb in controller.data.bones if bb.jk_adc.has_deform]
        for name in names:
            bb = controller.data.bones.get(name)
            # updating the parent names to have the deform prefix...
            if bb.jk_adc.deform_parent:
                bb.jk_adc.deform_parent = prefs.deform_prefix + bb.jk_adc.deform_parent
        add_deform_bones(controller, controller, names)
    # otherwise we want to convert single armature deform/controls to dual armature...
    else:
        names = [bb.name for bb in controller.data.bones if bb.jk_adc.has_deform]
        # just remove all the deform bones...
        remove_deform_bones(controller, controller, names)
        # create the deform armature...
        bpy.ops.object.mode_set(mode='OBJECT')
        deformer = add_deform_armature(controller)
        bpy.ops.object.mode_set(mode='EDIT')
        # and re-add all the deforms to it...
        for name in names:
            bb = controller.data.bones.get(name)
            # updating the parent names to no longer have the deform prefix...
            bb.jk_adc.deform_parent = bb.jk_adc.deform_parent[len(prefs.deform_prefix):]
        add_deform_bones(controller, deformer, names)
    # set our mode back...
    bpy.ops.object.mode_set(mode=last_mode)
    # and set the controllers settings back...
    reset_controller_defaults(controller, is_hiding, is_updating, use_deforms, use_reversed)
    controller.data.jk_adc.is_iterating = False
    controller.data.jk_adc.is_editing = False
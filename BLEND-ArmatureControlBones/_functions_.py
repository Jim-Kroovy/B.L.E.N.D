import bpy
import json
import mathutils

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTY FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_armatures():
    obj, controller, deformer = bpy.context.view_layer.objects.active, None, None
    armature = obj if obj.type == 'ARMATURE' else obj.find_armature() if obj.type == 'MESH' else None
    if armature:
        if armature.data.jk_acb.is_controller:
            controller, deformer = armature, armature.data.jk_acb.armature
        elif armature.data.jk_acb.is_deformer:
            controller, deformer = armature.data.jk_acb.armature, armature
    return controller, deformer

def get_deform_bones(controller, bones):
    deforms, bbs = [], controller.data.bones
    # iterate on the bones in order of hierarchy...
    roots = [bbs.get(bb) for bb in bones if bbs.get(bb) and bbs.get(bb).parent == None or bbs.get(bb).parent.name not in bones]
    for root_bb in roots:
        # gather the parentless bone data... (if it hasn't already been gathered)
        if not bones[root_bb.name]:
            _, angle = root_bb.AxisRollFromMatrix(root_bb.matrix_local.to_3x3())
            bone = {'name' : root_bb.name, 'head' : root_bb.head_local[:], 'tail' : root_bb.tail_local[:], 'roll' : angle, 'offset' : [0.0, 0.0, 0.0], 'parent' : root_bb.parent.name if root_bb.parent else ""}
            deforms.append(bone)
            bones[root_bb.name] = True
        # then iterate on the parentless bones recursive children... (that haven't already been gathered)
        children = [bb for bb in root_bb.children_recursive if bb.name in bones and not bones[bb.name]]
        for child_bb in children:
            # gather their bone data...
            _, angle = child_bb.AxisRollFromMatrix(child_bb.matrix_local.to_3x3())
            bone = {'name' : child_bb.name, 'head' : child_bb.head_local[:], 'tail' : child_bb.tail_local[:], 'roll' : angle, 'offset' : [0.0, 0.0, 0.0], 'parent' : child_bb.parent.name if child_bb.parent and child_bb.parent.name in bones else ""}
            deforms.append(bone)
            bones[child_bb.name] = True
    # return the bone list...
    return deforms

def set_deform_bones(controller, deformer):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    deforms, bbs = [], deformer.data.bones
    # armatures are combined if controller is deformer...  (so this function can be called during "is_combine" update function)
    prefix = prefs.deform_prefix if controller.data.jk_acb.is_deformer else ""
    # iterate on our existing deform bones... (if there are any)
    if controller.data.jk_acb.deforms:
        deforms = json.loads(controller.data.jk_acb.deforms)
        for bone in deforms:
            # checking if they exist...
            deform_bb = bbs.get(prefix + bone['name'])
            control_bb = controller.data.bones.get(bone['name'])
            if deform_bb and control_bb:
                # before updating their saved values... (saving the parent without any prefixing)
                axis, angle = deform_bb.AxisRollFromMatrix(deform_bb.matrix_local.to_3x3())
                offset = deform_bb.head_local - mathutils.Vector((bone['head'][0], bone['head'][1], bone['head'][2]))
                bone['head'] = control_bb.head_local[:]
                bone['tail'] = deform_bb.tail_local[:]
                bone['offset'] = offset[:]
                bone['roll'] = angle
                bone['parent'] = deform_bb.parent.name[len(prefix):] if deform_bb.parent else ""
    #print(deforms)
    # return the edited bone list...
    return deforms

def hide_deforms(controller, deformer, hide):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    # if the deform/control armatures are combined into a single one...
    if controller.data.jk_acb.is_deformer:
        # just hide/unhide the deform bones...
        deforms = json.loads(controller.data.jk_acb.deforms)
        bbs = controller.data.bones
        for bone in deforms:
            deform_bb = bbs.get(prefs.deform_prefix + bone['name'])
            if deform_bb:
                deform_bb.hide = hide
    # otherwise if we are using the dual armature method...
    else:
        # if we are showing the deform armature...
        if not hide:
            # add deformer to the same collections as the controller and select it...
            collections = [coll for coll in controller.users_collection if deformer.name not in coll.objects]
            for collection in collections:
                collection.objects.link(deformer)
            deformer.select_set(True)
            # ensuring it's name is correct...
            deformer.name, deformer.data.name = prefs.deform_prefix + controller.name, prefs.deform_prefix + controller.name
        else:
            # else we are hiding so remove deformer from all collections and make the controller active...
            collections = [coll for coll in deformer.users_collection]
            for collection in collections:
                collection.objects.unlink(deformer)
            bpy.context.view_layer.objects.active = controller
            controller.select_set(True)
            # ensuring it's name is correct...
            deformer.name, deformer.data.name = prefs.deform_prefix + controller.name, prefs.deform_prefix + controller.name

def hide_controls(controller, hide):
    # just hide/unhide the control bones...
    deforms = json.loads(controller.data.jk_acb.deforms)
    bbs = controller.data.bones
    for bone in deforms:
        deform_bb = bbs.get(bone['name'])
        deform_bb.hide = hide

def hide_others(controller, hide):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    deforms = json.loads(controller.data.jk_acb.deforms)
    bbs = controller.data.bones
    # get the controls and deforms into dictionaries for fast lookups...
    controllers = {b['name'] : True for b in deforms}
    deformers = {prefs.deform_prefix + b['name'] : True for b in deforms}
    # iterate on all bones...
    for bb in bbs:
        # hiding bones that are not control or deform bones...
        if not (bb.name in controllers or bb.name in deformers):
            bb.hide = hide

def use_deforms(controller, deformer, use):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    prefix = prefs.deform_prefix if controller.data.jk_acb.is_deformer else ""
    cbbs, dbbs = controller.data.bones, deformer.data.bones
    deforms = json.loads(controller.data.jk_acb.deforms) #set_deform_bones(controller, deformer)
    # if we are switching to deform bones within the controller...
    if controller.data.jk_acb.use_combined:
        meshes = [ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.find_armature() == controller]
        # if we want to switch to using the deform bones...
        if use:
            # iterate on the deforms...
            for bone in deforms:
                control_bb, deform_bb = cbbs.get(bone['name']), dbbs.get(prefix + bone['name'])
                control_bb.use_deform, deform_bb.use_deform = False, True
                # changing any vertex groups on the meshes...
                for mesh in meshes:
                    # to relate to the deform bone instead of the control...
                    group = mesh.vertex_groups.get(bone['name'])
                    if group:
                        group.name = prefix + group.name
        else:
            # iterate on the deforms...
            for bone in deforms:
                control_bb, deform_bb = cbbs.get(bone['name']), dbbs.get(prefix + bone['name'])
                control_bb.use_deform, deform_bb.use_deform = True, False
                # changing any vertex groups on the meshes...
                for mesh in meshes:
                    # to relate to the control bone instead of the control...
                    group = mesh.vertex_groups.get(prefix + bone['name'])
                    if group:
                        group.name = bone['name']
    # otherwise we need to switch between the deform/control armatures...
    else:
        # get all the meshes associated with the armatures...
        meshes = [ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.find_armature() in [controller, deformer]]
        # get all the modifiers on the meshes that target one of the armatures...
        modifiers = [mod for mesh in meshes for mod in mesh.modifiers if mod.type == 'ARMATURE' and mod.object in [controller, deformer]]
        if use:
            # remap things to the deform armature...
            for modifier in modifiers:
                modifier.object = deformer
            for mesh in meshes:
                if mesh.parent == controller:
                    mesh.parent = deformer
            # iterate on the deforms...
            for bone in deforms:
                # to reverse their use deform setting...
                control_bb, deform_bb = cbbs.get(bone['name']), dbbs.get(prefix + bone['name'])
                control_bb.use_deform, deform_bb.use_deform = False, True
        else:
            # remap things back to the control armature...
            for modifier in modifiers:
                modifier.object = controller
            for mesh in meshes:
                if mesh.parent == deformer:
                    mesh.parent = controller
            # iterate on the deforms...
            for bone in deforms:
                # to reverse their use deform setting...
                control_bb, deform_bb = cbbs.get(bone['name']), dbbs.get(prefix + bone['name'])
                control_bb.use_deform, deform_bb.use_deform = True, False

        
#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- COSNTRAINT FUNCTIONS ---------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def add_deform_constraints(armature, deform_pb, control_bb, limits=True):
    if limits:
        # limit location...
        if deform_pb.constraints.get("DEFORM - Limit Location"):
            limit_loc = deform_pb.constraints.get("DEFORM - Limit Location")
        else:
            limit_loc = deform_pb.constraints.new('LIMIT_LOCATION')
        limit_loc.name, limit_loc.show_expanded = "DEFORM - Limit Location", False
        limit_loc.use_min_x, limit_loc.use_min_y, limit_loc.use_min_z = True, True, True
        limit_loc.use_max_x, limit_loc.use_max_y, limit_loc.use_max_z = True, True, True
        limit_loc.owner_space = 'LOCAL_WITH_PARENT'
        # rotation...
        if deform_pb.constraints.get("DEFORM - Limit Rotation"):
            limit_rot = deform_pb.constraints.get("DEFORM - Limit Rotation")
        else:
            limit_rot = deform_pb.constraints.new('LIMIT_ROTATION')
        limit_rot.name, limit_rot.show_expanded = "DEFORM - Limit Rotation", False
        limit_rot.use_limit_x, limit_rot.use_limit_y, limit_rot.use_limit_z = True, True, True
        limit_rot.owner_space = 'LOCAL_WITH_PARENT'
        # and scale, all in local with parent space...
        if deform_pb.constraints.get("DEFORM - Limit Scale"):
            limit_sca = deform_pb.constraints.get("DEFORM - Limit Scale")
        else:
            limit_sca = deform_pb.constraints.new('LIMIT_SCALE')
        limit_sca.name, limit_sca.show_expanded = "DEFORM - Limit Scale", False
        limit_sca.use_min_x, limit_sca.use_min_y, limit_sca.use_min_z = True, True, True
        limit_sca.use_max_x, limit_sca.use_max_y, limit_sca.use_max_z = True, True, True
        limit_sca.min_x, limit_sca.min_y, limit_sca.min_z = 1.0, 1.0, 1.0
        limit_sca.max_x, limit_sca.max_y, limit_sca.max_z = 1.0, 1.0, 1.0
        limit_sca.owner_space = 'LOCAL_WITH_PARENT'
    # so the only transforms applied to the bone are from the child of constraint...
    if deform_pb.constraints.get("DEFORM - Child Of"):
        child_of = deform_pb.constraints.get("DEFORM - Child Of")
    else:
        child_of = deform_pb.constraints.new('CHILD_OF')
    
    child_of.name, child_of.show_expanded = "DEFORM - Child Of", False
    child_of.target, child_of.subtarget = armature, control_bb.name
    child_of.inverse_matrix = control_bb.matrix_local.inverted() @ armature.matrix_world.inverted()
    # bones may or may not want to actually be using any inherited scale at all... (but the child of will still need to be using it)
    controller = armature if armature.data.jk_acb.is_controller else armature.data.jk_acb.armature
    use_scale = controller.data.jk_acb.use_scale
    if deform_pb.constraints.get("USE - Limit Scale"):
        limit_sca = deform_pb.constraints.get("USE - Limit Scale")
    else:
        limit_sca = deform_pb.constraints.new('LIMIT_SCALE')
    limit_sca.name, limit_sca.show_expanded = "USE - Limit Scale", False
    limit_sca.use_min_x, limit_sca.use_min_y, limit_sca.use_min_z = True, True, True
    limit_sca.use_max_x, limit_sca.use_max_y, limit_sca.use_max_z = True, True, True
    limit_sca.min_x, limit_sca.min_y, limit_sca.min_z = 1.0, 1.0, 1.0
    limit_sca.max_x, limit_sca.max_y, limit_sca.max_z = 1.0, 1.0, 1.0
    limit_sca.owner_space, limit_sca.influence = 'LOCAL', not use_scale

def remove_deform_constraints(deform_pb):
    names = ["DEFORM - Child Of", "DEFORM - Limit Scale", "DEFORM - Limit Rotation", "DEFORM - Limit Location", "USE - Limit Scale"]
    for name in names:
        constraint = deform_pb.constraints.get(name)
        if constraint:
            deform_pb.constraints.remove(constraint)

def reverse_deform_constraints(controller, deformer, reverse):
    # we don't want to be hiding the deform bones if we switching around constraints...
    is_hiding_deforms = controller.data.jk_acb.hide_deforms
    if is_hiding_deforms and reverse:
        controller.data.jk_acb.hide_deforms = False
    # copy and clear the controllers world space transforms...
    control_mat = controller.matrix_world.copy()
    controller.matrix_world = mathutils.Matrix()

    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    prefix = prefs.deform_prefix if controller.data.jk_acb.is_deformer else ""
    last_mode, last_position = controller.mode, controller.data.pose_position
    deforms = json.loads(controller.data.jk_acb.deforms)
    cpbs, dpbs = controller.pose.bones, deformer.pose.bones
    # if rigging library is installed...
    addons = bpy.context.preferences.addons.keys()
    if 'BLEND-ArmatureRiggingLibrary' in addons:
        # we need to iterate through the controllers rigging...
        for rigging in controller.jk_arl.rigging:
            # turning off auto fk and set chains to use fk...
            if rigging.flavour in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE']:
                chain = rigging.get_pointer()
                chain.use_auto_fk = False
                chain.use_fk = True
            # kill the influence on all the tracking constraints...
            elif rigging.flavour == 'TRACKING':
                chain = rigging.get_pointer()
                for bone in chain.bones:
                    source_pb = cpbs.get(bone.source)
                    if source_pb:
                        copy_rot = source_pb.get("TRACK - Copy Rotation")
                        if copy_rot:
                            copy_rot.influence = 0.0
    armature = deformer if reverse else controller
    # switch to pose mode and set the armatures to their rest pose...
    bpy.ops.object.mode_set(mode='POSE')
    bpy.context.view_layer.objects.active = deformer
    controller.data.pose_position = 'REST'
    deformer.data.pose_position = 'REST'
    # iterate on the bones...
    for bone in deforms:
        # get the pose bones...
        control_pb, deform_pb = cpbs.get(bone['name']), dpbs.get(prefix + bone['name'])
        # remove the child of and limit constraints from one bone...
        remove_deform_constraints(deform_pb if reverse else control_pb)
        # mute/un-mute all constraints on the control bone...
        for con in control_pb.constraints:
            con.mute = reverse
        # and put them on the other...
        add_deform_constraints(armature, control_pb if reverse else deform_pb, deform_pb.bone if reverse else control_pb.bone)
    # return things to their last position and mode...
    deformer.data.pose_position = 'POSE'
    controller.data.pose_position = last_position
    bpy.context.view_layer.objects.active = controller
    bpy.ops.object.mode_set(mode=last_mode)
    # and return the controllers matrix...
    controller.matrix_world = control_mat

def mute_deform_constraints(deformer, mute):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    controller = deformer.data.jk_acb.armature
    prefix = prefs.deform_prefix if controller.data.jk_acb.is_deformer else ""
    deforms, pbs = json.loads(controller.data.jk_acb.deforms), deformer.pose.bones
    for bone in deforms:
        if controller.data.jk_acb.reverse_deforms:
            pb = pbs.get(bone['name'])
        else:
            pb = pbs.get(prefix + bone['name'])
        if pb:
            for con in pb.constraints:
                con.mute = mute

def use_deform_scale(controller, deformer):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    deforms = json.loads(controller.data.jk_acb.deforms)
    prefix = prefs.deform_prefix if controller.data.jk_acb.is_deformer else ""
    # copy and clear the controllers world space transforms...
    control_mat = controller.matrix_world.copy()
    controller.matrix_world = mathutils.Matrix()
    for bone in deforms:
        control_pb = controller.pose.bones.get(bone['name'])
        deform_pb = deformer.pose.bones.get(prefix + bone['name'])
        if controller.data.jk_acb.reverse_deforms:
            add_deform_constraints(deformer, control_pb, deform_pb.bone, limits=False)
        else:
            add_deform_constraints(controller, deform_pb, control_pb.bone, limits=False)
    # and return the controllers matrix...
    controller.matrix_world = control_mat

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- BONE FUNCTIONS ---------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_deform_parent(control, deformers):
    bone, parent = control, ""
    # while we don't have a parent...
    while parent == "":
        # try and get the next parent in the deforming bones...
        parent = bone.parent.name if bone.parent and bone.parent.name in deformers else ""
        # always get the next parent...
        bone = bone.parent 
        # if there isn't a next parent...
        if bone == None:
            # break because we won't find one...
            break
    # return the parent...
    return parent

def add_deform_bones(controller, deformer):
    #print("ADD BONES")
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    last_mode, last_position = controller.mode, controller.data.pose_position
    use_deforms, is_combined = controller.data.jk_acb.use_deforms, controller.data.jk_acb.use_combined
    deforms = json.loads(controller.data.jk_acb.deforms)
    prefix = prefs.deform_prefix if is_combined else ""
    # copy and clear the controllers world space transforms...
    control_mat = controller.matrix_world.copy()
    controller.matrix_world = mathutils.Matrix()
    # make sure deforms are shown before changing mode... (if not combined will also select deform armature)
    hide_deforms(controller, deformer, False)
    # gather all the deform bones that don't already exist...
    new_deforms = [b for b in deforms if not deformer.data.bones.get(prefix + b['name'])]
    # create any new deform bones in edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    ebs = deformer.data.edit_bones
    for bone in new_deforms:
        deform_eb = ebs.new(prefix + bone['name'])
        offset = mathutils.Vector((bone['offset'][0], bone['offset'][1], bone['offset'][2]))
        head = mathutils.Vector((bone['head'][0], bone['head'][1], bone['head'][2]))
        deform_eb.head, deform_eb.tail, deform_eb.roll = head + offset, bone['tail'], bone['roll']
        # deform_eb.use_inherit_rotation, deform_eb.inherit_scale = False, 'NONE'
        deform_eb.parent = ebs.get(prefix + bone['parent'])
        
    # switch to pose mode and set the armatures to their rest pose...
    bpy.ops.object.mode_set(mode='POSE')
    bpy.context.view_layer.objects.active = deformer
    controller.data.pose_position = 'REST'
    deformer.data.pose_position = 'REST'
    # each deform bone has limits and an inverted child of constraint to its control...
    pbs, bbs = deformer.pose.bones, controller.data.bones
    for bone in deforms:
        deform_pb = pbs.get(prefix + bone['name'])
        control_bb = bbs.get(bone['name'])
        if deform_pb:
            add_deform_constraints(controller, deform_pb, control_bb)
            # the deform bone should always deform if we are not combined
            deform_pb.bone.use_deform = True if not is_combined else use_deforms
            # the control bone should only deform if we are not using deforms...
            control_bb.use_deform = not use_deforms
    # return things to their last position and mode...
    deformer.data.pose_position = 'POSE'
    controller.data.pose_position = last_position
    bpy.context.view_layer.objects.active = controller
    bpy.ops.object.mode_set(mode=last_mode)
    # if we are not showing deforms, hide them...
    if controller.data.jk_acb.hide_deforms:
        hide_deforms(controller, deformer, True)
    # and return the controllers matrix...
    controller.matrix_world = control_mat

def remove_deform_bones(controller, deformer, bones):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    last_mode = controller.mode
    deforms = json.loads(controller.data.jk_acb.deforms)
    prefix = prefs.deform_prefix if controller.data.jk_acb.is_deformer else ""
    deletes = {prefix + b['name'] : b for b in deforms if b['name'] in bones}
    # make sure deforms are shown before changing mode... (if not combined will also select deform armature)
    hide_deforms(controller, deformer, False)
    # and we don't want to be using deform bones either...
    is_using_deforms = controller.data.jk_acb.use_deforms
    if is_using_deforms:
        controller.data.jk_acb.use_deforms = False
    bpy.ops.object.mode_set(mode='EDIT')
    # remove deform bones and their data...
    ebs = deformer.data.edit_bones
    for del_name, del_bone in deletes.items():
        del_eb = ebs.get(del_name)
        if del_eb:
            ebs.remove(del_eb)
        #del_index = deforms.index(del_bone)
        deforms.remove(del_bone)
    # if there are no bones left, unset the controllers pointer and bool...
    if len(deforms) == 0:
        controller.data.jk_acb.is_controller = False
        controller.data.jk_acb.is_deformer = False
        controller.data.jk_acb.armature = None
    # then go back to the last mode and return the edited deforms dictionary...
    bpy.ops.object.mode_set(mode=last_mode)
    # if we are not showing deforms, hide them...
    if controller.data.jk_acb.hide_deforms:
        hide_deforms(controller, deformer, True)
    return deforms

def update_deform_bones(controller, deformer):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    last_mode = controller.mode
    deforms = json.loads(controller.data.jk_acb.deforms)
    prefix = prefs.deform_prefix if controller.data.jk_acb.use_combined else ""
    bbs = controller.data.bones
    updates = [b for b in deforms if bbs.get(b['name']) and mathutils.Vector((b['head'][0], b['head'][1], b['head'][2])) != bbs.get(b['name']).head_local]
    # make sure deforms are showing... (if not combined will also select deform armature)
    hide_deforms(controller, deformer, False)
    # update the deforming head locations from the control bones in edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    ebs = deformer.data.edit_bones
    for bone in updates:
        control_bb = bbs.get(bone['name'])
        deform_eb = ebs.get(prefix + bone['name'])
        if control_bb and deform_eb:
            # get the offset and old head and tail locations...
            offset = mathutils.Vector((bone['offset'][0], bone['offset'][1], bone['offset'][2]))
            old_head_loc = mathutils.Vector((bone['head'][0], bone['head'][1], bone['head'][2]))
            old_tail_loc = mathutils.Vector((bone['tail'][0], bone['tail'][1], bone['tail'][2]))
            # get the difference between the new head location and old head location...
            difference = control_bb.head_local - old_head_loc
            # apply that difference to the head and tail...
            new_head_loc = old_head_loc + difference
            new_tail_loc = old_tail_loc + difference
            # update the deform bones, adding any offsets... (also ensuring the roll doesn't change)
            deform_eb.head, deform_eb.tail, deform_eb.roll = new_head_loc + offset, new_tail_loc, bone['roll']
            # update the dictionary to have the new head and tail locations...
            bone['head'], bone['tail'] = control_bb.head_local[:], deform_eb.tail[:]
            
    # then go back to the last mode and return the edited deforms dictionary...
    bpy.ops.object.mode_set(mode=last_mode)
    # if we are not showing deforms, hide them...
    if controller.data.jk_acb.hide_deforms:
        hide_deforms(controller, deformer, True)
    return deforms

def set_deform_constraints(deformer, bones):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    controller = deformer.data.jk_acb.armature
    last_mode, last_position = controller.mode, controller.data.pose_position
    deforms = json.loads(controller.data.jk_acb.deforms)
    prefix = prefs.deform_prefix if controller.data.jk_acb.use_combined else ""
    pbs, bbs = deformer.pose.bones, controller.data.bones
    # copy and clear the controllers world space transforms...
    control_mat = controller.matrix_world.copy()
    controller.matrix_world = mathutils.Matrix()
    # if we have selected bones...
    if bones:
        # get all the bones we should be orienting...
        deformers = [b for b in deforms if bbs.get(b['name']) and b['name'] in bones]
    else:
        # otherwise just get all the deforms that exist...
        deformers = [b for b in deforms if bbs.get(b['name'])]
    # make sure deforms are shown before changing mode... (if not combined will also select deform armature)
    hide_deforms(controller, deformer, False)
    bpy.ops.object.mode_set(mode='POSE')
    bpy.context.view_layer.objects.active = deformer
    controller.data.pose_position = 'REST'
    deformer.data.pose_position = 'REST'
    # then iterate all the deform bones to reset...
    for bone in deformers:
        deform_pb = pbs.get(prefix + bone['name'])
        control_bb = bbs.get(bone['name'])
        add_deform_constraints(controller, deform_pb, control_bb)
    # return things to their last position and mode...
    bpy.context.view_layer.objects.active = controller
    deformer.data.pose_position = 'POSE'
    controller.data.pose_position = last_position
    bpy.ops.object.mode_set(mode=last_mode)
    # if we are not showing deforms, hide them...
    if controller.data.jk_acb.hide_deforms:
        hide_deforms(controller, deformer, True)
    # and return the controllers matrix...
    controller.matrix_world = control_mat

def set_control_orientation(controller, bones):
    #print("ORIENT CONTROLS")
    last_mode = controller.mode
    deforms = json.loads(controller.data.jk_acb.deforms)
    # make sure deforms are shown before changing mode... (if not combined will also select deform armature)
    hide_deforms(controller, controller.data.jk_acb.armature, False)
    bpy.ops.object.mode_set(mode='EDIT')
    ebs, bbs = controller.data.edit_bones, controller.data.bones
    # if we have selected bones...
    if bones:
        # get all the bones we should be orienting...
        orients = [ebs.get(b['name']) for b in deforms if ebs.get(b['name']) and b['name'] in bones]
    else:
        # otherwise just get all the controls that exist...
        orients = [ebs.get(b['name']) for b in deforms if ebs.get(b['name'])]
    # then iterate all the control bones to orient...
    for control_eb in orients:
        has_target = False
        # if a bone has only one child...
        if len(control_eb.children) == 1:
            child = control_eb.children[0]
            # and as long as the childs head is not equal to the bones head...
            if child.head != control_eb.head:
                # it's tail should probably point to it...
                control_eb.tail = child.head
                has_target = True
        # if a bone has multiple children
        elif len(control_eb.children) > 1:
            # iterate over the children...
            for child in control_eb.children:
                # checking for these most likely places we will want to target...
                if any(string in child.name.upper() for string in ["NECK", "SPINE", "LOWER", "ELBOW", "KNEE", "CALF", "HAND", "WRIST", "FOOT", "ANKLE"]):
                    # as long as the childs head is not equal to the bones head...
                    if child.head != control_eb.head:
                        # take the first match and break...
                        control_eb.tail = child.head
                        has_target = True
                        break
        # if we couldn't find a suitable child target...
        if not has_target:
            # but the bone has a parent, we can align to it...
            if control_eb.parent != None:
                control_eb.align_orientation(control_eb.parent)
            else:
                # otherwise let the console know that this bone couldn't be oriented...
                print("Automatic Orientation: Could not find anywhere to align", control_eb.name, "so you are on your own with it...")
    # return to the last mode...
    bpy.ops.object.mode_set(mode=last_mode)
    # if we are not showing deforms, hide them...
    if controller.data.jk_acb.hide_deforms:
        hide_deforms(controller, controller.data.jk_acb.armature, True)

def set_deform_parenting(controller, deformer, bones):
    #print("PARENT DEFORMS")
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    last_mode = controller.mode
    deforms = json.loads(controller.data.jk_acb.deforms)
    prefix = prefs.deform_prefix if controller.data.jk_acb.use_combined else ""
    # make sure deforms are shown before changing mode... (if not combined will also select deform armature)
    hide_deforms(controller, controller.data.jk_acb.armature, False)
    bpy.ops.object.mode_set(mode='EDIT')
    ebs, bbs = deformer.data.edit_bones, controller.data.bones
    # if we have selected bones...
    if bones:
        # get all the bones we should try and parent...
        parentless = [b for b in deforms if ebs.get(prefix + b['name']) and b['name'] in bones and b['parent'] == ""]
    else:
        # otherwise just get all the deforms that exist...
        parentless = [b for b in deforms if ebs.get(prefix + b['name']) and b['parent'] == ""]
    # get a dictionary of all the deform bones...
    deformers = {b['name'] : b for b in deforms}
    # then iterate all the deform bones to parent...
    for bone in parentless:
        control_bb = bbs.get(bone['name'])
        deform_eb = ebs.get(prefix + bone['name'])
        # if the control and the deform bones exist...
        if control_bb and deform_eb:
            # try and get the parent from the deformers dictionary...
            parent = get_deform_parent(control_bb, deformers)
            # if we found a parent...
            if parent:
                # set the deform bones parent to the deform of the control parent we found...
                deform_eb.parent = ebs.get(prefix + parent)
    # return to the last mode...
    bpy.ops.object.mode_set(mode=last_mode)
    # if we are not showing deforms, hide them...
    if controller.data.jk_acb.hide_deforms:
        hide_deforms(controller, controller.data.jk_acb.armature, True)

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- MODE FUNCTIONS ---------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def subscribe_mode_to(obj, callback):
    #print("SUBSCRIBE MODE", obj)
    # get the data path to sub and assign it to the msgbus....
    subscribe_to = obj.path_resolve('mode', False)
    bpy.msgbus.subscribe_rna(key=subscribe_to, owner=obj, args=(obj, 'mode'), notify=callback, options={"PERSISTENT"})

def set_meshes(armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
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
            prefs.meshes.remove(mi)

def armature_mode_callback(armature, data):
    # if the armature is a controller or deformer...
    if armature.data.jk_acb.is_controller or armature.data.jk_acb.is_deformer:
        # get controller and deformer references...
        controller = armature if armature.data.jk_acb.is_controller else armature.data.jk_acb.armature
        deformer = armature if armature.data.jk_acb.is_deformer else armature.data.jk_acb.armature
        # and if the controller is auto updating...
        if controller.data.jk_acb.use_auto_update:
            # and we are switching out of edit mode...
            if armature.mode != 'EDIT':
                #print('UPDATE ARMATURE', armature)
                # switch off auto updating so we don't don't fire this callback during the functions...
                controller.data.jk_acb.use_auto_update = False
                # update bone locations if we leave edit mode on the controller...
                if armature.data.jk_acb.is_controller:
                    deforms = update_deform_bones(controller, deformer)
                    controller.data.jk_acb.deforms = json.dumps(deforms)
                # save all deform changes if we are leaving edit mode on the deformer...
                if armature.data.jk_acb.is_deformer:
                    deforms = set_deform_bones(controller, deformer)
                    controller.data.jk_acb.deforms = json.dumps(deforms)
                # always make sure our child of constraints are behaving...
                set_deform_constraints(deformer, [])
                # then switch auto update back on so it can be used again...
                controller.data.jk_acb.use_auto_update = True

def mesh_mode_callback(mesh, data):
    # comprehend a dictionary of the armatures we might need to edit and iterate on it...
    controllers = [mod.object for mod in mesh.modifiers if mod.type == 'ARMATURE' and mod.object and mod.object.data.jk_acb.is_controller]
    for controller in controllers:
        deforms = json.loads(controller.data.jk_acb.deforms)
        # check the armature has controls and wants to auto hide or sync locations...
        if deforms:
            # then if we are going into weight paint mode...
            if mesh.mode == 'WEIGHT_PAINT':
                # show the only the bones deforming the mesh...
                if controller.use_deforms:
                    controller.data.jk_acb.hide_deforms = False
                    controller.data.jk_acb.hide_controls = True
                else:
                    controller.data.jk_acb.hide_deforms = True
                    controller.data.jk_acb.hide_controls = False
                controller.data.jk_acb.hide_others = True
            else:
                # otherwise show the only the bones that are not deforming the mesh...
                if controller.use_deforms:
                    controller.data.jk_acb.hide_deforms = True
                    controller.data.jk_acb.hide_controls = False
                else:
                    controller.data.jk_acb.hide_deforms = False
                    controller.data.jk_acb.hide_controls = True
                controller.data.jk_acb.hide_others = False

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- ARMATURE FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_deform_actions(controller, only_active):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
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

def get_bone_names(self, controller):
    # acessing bones by name preserves them through mode switching...
    if self.only_selected and self.only_deforms:
        bones = {bb.name : False for bb in controller.data.bones if bb.select and bb.use_deform}
    elif self.only_selected:
        bones = {bb.name : False for bb in controller.data.bones if bb.select}
    elif self.only_deforms:
        bones = {bb.name : False for bb in controller.data.bones if bb.use_deform}
    else:
        bones = {bb.name : False for bb in controller.data.bones}
    return bones

def add_deform_armature(controller):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    # create a new deformer armature that copies the transforms of the controller...
    deformer_data = bpy.data.armatures.new(prefs.deform_prefix + controller.name)
    deformer = bpy.data.objects.new(prefs.deform_prefix + controller.name, deformer_data)
    deformer.use_fake_user, deformer.parent = True, controller
    # set the pointer and bools on both armatures...
    controller.data.jk_acb.is_controller = True
    controller.data.jk_acb.is_deformer = False
    controller.data.jk_acb.armature = deformer
    deformer.data.jk_acb.is_deformer = True
    deformer.data.jk_acb.armature = controller
    # create the deformation bones...
    add_deform_bones(controller, deformer)

def remove_deform_armature(controller):
    # unlink the deforming armature and show the controls...
    hide_deforms(controller, controller.data.jk_acb.armature, True)
    hide_controls(controller, False)
    # and we don't want to be using deform bones during execution...
    is_using_deforms = controller.data.jk_acb.use_deforms
    if is_using_deforms:
        controller.data.jk_acb.use_deforms = False
    # remove the deformers data and object...
    deformer_data = controller.data.jk_acb.armature.data
    bpy.data.objects.remove(controller.data.jk_acb.armature)
    bpy.data.armatures.remove(deformer_data)
    # unset the controllers pointer and bool...
    controller.data.jk_acb.is_controller = False
    controller.data.jk_acb.armature = None

def set_combined(controller, deformer, combine):
    last_mode = controller.mode
    # make sure the function cannot trigger any auto updates...
    is_auto_updating = controller.data.jk_acb.use_auto_update
    if is_auto_updating:
        controller.data.jk_acb.use_auto_update = False
    # and we don't want to be using deform bones during execution...
    is_using_deforms = controller.data.jk_acb.use_deforms
    if is_using_deforms:
        controller.data.jk_acb.use_deforms = False
    # but we need to be showing deforms incase we are un-combining...
    is_hiding_deforms = controller.data.jk_acb.hide_deforms
    if is_hiding_deforms:
        controller.data.jk_acb.hide_deforms = False
    # and if our deforms are reversed we need to un reverse them....
    is_reversed_deforms = controller.data.jk_acb.reverse_deforms
    if is_reversed_deforms:
        controller.data.jk_acb.reverse_deforms = False
    # if we are combining dual armature deform/controls to single armature...
    if combine:
        # save the deform bones and remove the deform armature...
        deforms = set_deform_bones(controller, deformer)
        remove_deform_armature(controller)
        # set the pointer and bools... (when combined the controller just references itself)
        controller.data.jk_acb.is_controller = True
        controller.data.jk_acb.is_deformer = True
        controller.data.jk_acb.armature = controller
        # then add the deform bones to the controller...
        controller.data.jk_acb.deforms = json.dumps(deforms)
        add_deform_bones(controller, controller)
    # otherwise we want to convert single armature deform/controls to dual armature...
    else:
        # save and remove the deform bones from the controller...
        deforms = set_deform_bones(controller, deformer)
        bpy.ops.object.mode_set(mode='EDIT')
        remove_deform_bones(controller, deformer, [b['name'] for b in deforms])
        bpy.ops.object.mode_set(mode=last_mode)
        # and add in the seperated deformation armature...
        controller.data.jk_acb.deforms = json.dumps(deforms)
        add_deform_armature(controller)
        # and subscribe the deform armatures mdoe change callback...
        deformer = controller.data.jk_acb.armature
        subscribe_mode_to(deformer, armature_mode_callback)

    # if we were auto updating or using/hiding deforms then set them back...
    if is_auto_updating:
        controller.data.jk_acb.use_auto_update = is_auto_updating
    if is_using_deforms:
        controller.data.jk_acb.use_deforms = is_using_deforms
    if is_hiding_deforms:
        controller.data.jk_acb.hide_deforms = is_hiding_deforms
    if is_reversed_deforms:
        controller.data.jk_acb.reverse_deforms = is_reversed_deforms
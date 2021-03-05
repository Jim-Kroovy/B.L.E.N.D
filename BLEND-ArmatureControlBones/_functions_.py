import bpy
import json
import mathutils

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTY FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_armatures():
    controller, deformer = None, None
    # if the current object is an armature...
    if bpy.context.object.type == 'ARMATURE':
        if bpy.context.object.data.jk_acb.is_controller:
            controller = bpy.context.object
            deformer = controller.data.jk_acb.armature
        elif bpy.context.object.data.jk_acb.is_deformer:
            deformer = bpy.context.object
            controller = deformer.data.jk_acb.armature
    # else if the current object is a mesh...
    elif bpy.context.object.type == 'MESH':
        # find the armatures from the first armature modifier...
        for mod in bpy.context.object.modifiers:
            # if there even is one...
            if mod.type == 'ARMATURE' and mod.object:
                if mod.object.data.jk_acb.is_controller:
                    controller = mod.object
                    deformer = controller.data.jk_acb.armature
                    break
                elif bpy.context.object.data.jk_acb.is_deformer:
                    deformer = mod.object
                    controller = deformer.data.jk_acb.armature
                    break
    return controller, deformer

def get_deform_bones(controller, bones):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    deforms, bbs = [], controller.data.bones
    prefix = prefs.deform_prefix if controller.data.jk_acb.use_combined else ""
    # iterate on the bones in order of hierarchy... (need to update this to account for parenting when skipping bones!)
    roots = [bbs.get(bb) for bb in bones if bbs.get(bb) and bbs.get(bb).parent == None or bbs.get(bb).parent.name not in bones]
    for root_bb in roots:
        # gather its bone data...
        axis, angle = root_bb.AxisRollFromMatrix(root_bb.matrix_local.to_3x3())
        bone = {'name' : root_bb.name, 'head' : root_bb.head_local[:], 'tail' : root_bb.tail_local[:], 'roll' : angle, 'offset' : [0.0, 0.0, 0.0], 'parent' : ""}
        deforms.append(bone)
        children = [bb for bb in root_bb.children_recursive if bb.name in bones]
        # then iterate on the parentless bones recursive children...
        for child_bb in children:
            # gather their bone data...
            axis, angle = child_bb.AxisRollFromMatrix(child_bb.matrix_local.to_3x3())
            bone = {'name' : child_bb.name, 'head' : child_bb.head_local[:], 'tail' : child_bb.tail_local[:], 'roll' : angle, 'offset' : [0.0, 0.0, 0.0], 'parent' : prefix + child_bb.parent.name if child_bb.parent else ""}
            deforms.append(bone)
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
            # checking if they exist... (and getting the right bones if we are switching)
            deform_bb = bbs.get(prefix + bone['name'])
            control_bb = controller.data.bones.get(bone['name'])
            if deform_bb:
                # before updating their saved values... (saving the parent without any prefixing)
                axis, angle = deform_bb.AxisRollFromMatrix(deform_bb.matrix_local.to_3x3())
                offset = deform_bb.head_local - mathutils.Vector((bone['head'][0], bone['head'][1], bone['head'][2]))
                bone['head'] = control_bb.head_local[:]
                bone['tail'] = deform_bb.tail_local[:]
                bone['offset'] = offset[:]
                bone['roll'] = angle
                bone['parent'] = deform_bb.parent.name[len(prefix):] if deform_bb.parent else ""
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
    # if we are switching to deform bones within the controller...
    if controller.data.jk_acb.use_combined:
        deforms = set_deform_bones(controller, deformer)
        meshes = [ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.find_armature() == controller]
        # if we want to switch to using the deform bones...
        if use:
            # iterate on the deforms...
            for bone in deforms:
                # changing any vertex groups on the meshes...
                for mesh in meshes:
                    # to relate to the deform bone instead of the control...
                    group = mesh.vertex_groups.get(bone['name'])
                    if group:
                        group.name = prefs.deform_prefix + group.name
        else:
             # iterate on the deforms...
            for bone in deforms:
                # changing any vertex groups on the meshes...
                for mesh in meshes:
                    # to relate to the control bone instead of the control...
                    group = mesh.vertex_groups.get(prefs.deform_prefix + bone['name'])
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
        else:
            # remap things back to the control armature...
            for modifier in modifiers:
                modifier.object = controller
            for mesh in meshes:
                if mesh.parent == deformer:
                    mesh.parent = controller

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- BONE FUNCTIONS ---------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def add_deform_bones(controller, deformer):
    #print("ADD BONES")
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    last_mode, last_position = controller.mode, controller.data.pose_position
    deforms = json.loads(controller.data.jk_acb.deforms)
    prefix = prefs.deform_prefix if controller.data.jk_acb.use_combined else ""
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
        deform_eb.parent, deform_eb.use_inherit_rotation, deform_eb.inherit_scale = ebs.get(prefix + bone['parent']), False, 'NONE'
    
    # set any old bones parenting... (incase we added a new parent?)
    # old_deforms = [b for b in deforms if deformer.data.bones.get(b['name'])]
    #for bone in old_deforms:
        #deform_eb = ebs.get(bone['name'])
        #deform_eb.parent = ebs.get(bone['parent'])
    
    # switch to pose mode and set the armatures to their rest pose...
    bpy.ops.object.mode_set(mode='POSE')
    bpy.context.view_layer.objects.active = deformer
    controller.data.pose_position = 'REST'
    deformer.data.pose_position = 'REST'
    # each deform bone has an inverted child of constraint to its control...
    pbs, bbs = deformer.pose.bones, controller.data.bones
    for bone in deforms:
        deform_pb = pbs.get(prefix + bone['name'])
        control_bb = bbs.get(bone['name'])
        if deform_pb:
            # if they aren't already limited we need to limit their location...
            if deform_pb.constraints.get("DEFORM - Limit Location"):
                limit_loc = deform_pb.constraints.get("DEFORM - Limit Location")
            else:
                limit_loc = deform_pb.constraints.new('LIMIT_LOCATION')
            limit_loc.name, limit_loc.show_expanded = "DEFORM - Limit Location", False
            limit_loc.use_min_x, limit_loc.use_min_y, limit_loc.use_min_z = True, True, True
            limit_loc.use_max_x, limit_loc.use_max_y, limit_loc.use_max_z = True, True, True
            # in local with parent space, so we only inherit location from the child of constraint...
            limit_loc.owner_space = 'LOCAL_WITH_PARENT'
            # and if the child of already exists just reset it...
            if deform_pb.constraints.get("DEFORM - Child Of"):
                child_of = deform_pb.constraints.get("DEFORM - Child Of")
            else:
                # otherwise create and set it inverse...
                child_of = deform_pb.constraints.new('CHILD_OF')
            child_of.name, child_of.show_expanded = "DEFORM - Child Of", False
            child_of.target, child_of.subtarget = controller, bone['name']
            child_of.inverse_matrix = control_bb.matrix_local.inverted()
    # return things to their last position and mode...
    deformer.data.pose_position = 'POSE'
    controller.data.pose_position = last_position
    bpy.context.view_layer.objects.active = controller
    bpy.ops.object.mode_set(mode=last_mode)
    # if we are not showing deforms, hide them...
    if controller.data.jk_acb.hide_deforms:
        hide_deforms(controller, deformer, True)

def remove_deform_bones(controller, deformer, bones):
    #print("REMOVE BONES")
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    last_mode = controller.mode
    deforms = json.loads(controller.data.jk_acb.deforms)
    prefix = prefs.deform_prefix if controller.data.jk_acb.is_deformer else ""
    deletes = {prefix + b['name'] : b for b in deforms if b['name'] in bones}
    # make sure deforms are shown before changing mode... (if not combined will also select deform armature)
    hide_deforms(controller, deformer, False)
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
    print("UPDATE BONES")
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    last_mode = controller.mode
    deforms = json.loads(controller.data.jk_acb.deforms)
    prefix = prefs.deform_prefix if controller.data.jk_acb.use_combined else ""
    bbs = controller.data.bones
    #new_controls = get_deform_bones(controller, [b['name'] for b in deforms])
    #active_layers = [i for i, layer in enumerate(controller.data.layers) if layer]
    #is_active = True if any(pelvis_cb.bone.layers[index] for index in active_layers) else False
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
    #print("UPDATE CONSTRAINTS")
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    controller = deformer.data.jk_acb.armature
    last_mode, last_position = controller.mode, controller.data.pose_position
    deforms = json.loads(controller.data.jk_acb.deforms)
    prefix = prefs.deform_prefix if controller.data.jk_acb.use_combined else ""
    pbs, bbs = deformer.pose.bones, controller.data.bones
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
        # if they aren't already limited we need to limit their location...
        if deform_pb.constraints.get("DEFORM - Limit Location"):
            limit_loc = deform_pb.constraints.get("DEFORM - Limit Location")
        else:
            limit_loc = deform_pb.constraints.new('LIMIT_LOCATION')
        limit_loc.name, limit_loc.show_expanded = "DEFORM - Limit Location", False
        limit_loc.use_min_x, limit_loc.use_min_y, limit_loc.use_min_z = True, True, True
        limit_loc.use_max_x, limit_loc.use_max_y, limit_loc.use_max_z = True, True, True
        # in local with parent space, so we only inherit location from the child of constraint...
        limit_loc.owner_space = 'LOCAL_WITH_PARENT'
        # and if the child of already exists just reset it...
        if deform_pb.constraints.get("DEFORM - Child Of"):
            child_of = deform_pb.constraints.get("DEFORM - Child Of")
        else:
            # otherwise create and set it inverse...
            child_of = deform_pb.constraints.new('CHILD_OF')
        child_of.name, child_of.show_expanded = "DEFORM - Child Of", False
        child_of.target, child_of.subtarget = controller, bone['name']
        child_of.inverse_matrix = control_bb.matrix_local.inverted()
    # return things to their last position and mode...
    bpy.context.view_layer.objects.active = controller
    deformer.data.pose_position = 'POSE'
    controller.data.pose_position = last_position
    bpy.ops.object.mode_set(mode=last_mode)
    # if we are not showing deforms, hide them...
    if controller.data.jk_acb.hide_deforms:
        hide_deforms(controller, deformer, True)

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

def set_switched_names(controller):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    deforms = json.loads(controller.data.jk_acb.deforms)
    bbs = controller.data.bones
    # this should work as a toggle and just swap naming whenever it's called...
    for bone in deforms:
        control_bb = bbs.get(bone['name'])
        deform_bb = bbs.get(prefs.deform_prefix + bone['name'])
        control_bb.name = prefs.deform_prefix + bone['name']
        deform_bb.name = bone['name']

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

def get_bone_names(self, controller):
    # acessing bones by name preserves them through mode switching...
    if self.only_selected and self.only_deforms:
        bones = [bb.name for bb in controller.data.bones if bb.select and bb.use_deform]
    elif self.only_selected:
        bones = [bb.name for bb in controller.data.bones if bb.select]
    elif self.only_deforms:
        bones = [bb.name for bb in controller.data.bones if bb.use_deform]
    else:
        bones = [bb.name for bb in controller.data.bones]
    return bones

def add_deform_armature(controller):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    # create a new deformer armature that copies the transforms of the controller...
    deformer_data = bpy.data.armatures.new(prefs.deform_prefix + controller.name)
    deformer = bpy.data.objects.new(prefs.deform_prefix + controller.name, deformer_data)
    deformer.use_fake_user = True
    # the deformation armature copys the transforms of the original...
    copy_trans = deformer.constraints.new('COPY_TRANSFORMS')
    copy_trans.name, copy_trans.show_expanded, copy_trans.target = "DEFORM - Copy Transforms", False, controller
    # create the deformation bones...
    add_deform_bones(controller, deformer)
    # set the pointer and bools on both armatures...
    controller.data.jk_acb.is_controller = True
    controller.data.jk_acb.is_deformer = False
    controller.data.jk_acb.armature = deformer
    deformer.data.jk_acb.is_deformer = True
    deformer.data.jk_acb.armature = controller

def remove_deform_armature(controller):
    # unlink the deformer if it's active
    if controller.data.jk_acb.hide_deforms:
        hide_deforms(controller, controller.data.jk_acb.armature, False)
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
    # if we are combining dual armature deform/controls to single armature...
    if combine:
        # save the deform bones and remove the deform armature...
        deforms = set_deform_bones(controller, deformer)
        remove_deform_armature(controller)
        controller.data.jk_acb.is_deformer = True
        # then add the deform bones to the controller...
        controller.data.jk_acb.deforms = json.dumps(deforms)
        add_deform_bones(controller, controller)
        # set the pointer and bools... (when combined the controller just references itself)
        controller.data.jk_acb.is_controller = True
        controller.data.jk_acb.armature = controller
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
    # if we were auto updating or using deforms then set them back...
    if is_auto_updating:
        controller.data.jk_acb.use_auto_update = is_auto_updating
    if is_using_deforms:
        controller.data.jk_acb.use_deforms = is_using_deforms
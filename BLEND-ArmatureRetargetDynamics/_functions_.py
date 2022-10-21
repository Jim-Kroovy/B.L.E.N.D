import bpy

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- GENERAL FUNCTIONS ------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def add_retarget_group(armature):
    if "Retarget Bones" not in armature.pose.bone_groups:
        grp = armature.pose.bone_groups.new(name="Retarget Bones")
        grp.color_set = 'THEME14'
        for bone in armature.pose.bones:
            rpb = armature.pose.bones.get(bone.retarget)
            if rpb:
                rpb.bone_group = grp

def remove_retarget_group(armature):
    grp = armature.pose.bone_groups.get("Retarget Bones")
    if grp:
        armature.pose.bone_groups.remove(grp)

def get_is_pole(source, sb_name):
    is_pole = False
    for p_bone in [pb for pb in source.pose.bones if any(c.type == 'IK' for c in pb.constraints)]:
        if not is_pole:
            for con in [con for con in p_bone.constraints if con.type == 'IK' and con.pole_target != None]:
                if con.pole_subtarget == sb_name:
                    is_pole = True
                    break
        else:
            break
    return is_pole

def get_copied_object(source):
    # get copies of the object and data...
    copy_data, copy_object = source.data.copy(), source.copy()
    copy_object.data, copy_object.use_fake_user = copy_data, True
    # add them to the same collections as the source...
    collections = [coll for coll in source.users_collection if copy_object.name not in coll.objects]
    for collection in collections:
        collection.objects.link(copy_object)
    return copy_object

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- BONE FUNCTIONS ---------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def add_retarget_bones(source):
    last_mode = source.mode
    # go into edit mode and...
    if last_mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    ebs = [eb for eb in source.data.edit_bones]
    for source_eb in ebs:
        # create a duplicate of the source bone...
        retarget_eb = source.data.edit_bones.new("RB_" + source_eb.name)
        retarget_eb.head, retarget_eb.tail, retarget_eb.roll = source_eb.head, source_eb.tail, source_eb.roll
        retarget_eb.use_local_location, retarget_eb.use_connect = source_eb.use_local_location, source_eb.use_connect
        retarget_eb.use_inherit_rotation, retarget_eb.inherit_scale = source_eb.use_inherit_rotation, source_eb.inherit_scale
        retarget_eb.parent, retarget_eb.use_deform, retarget_eb.hide = source_eb.parent, False, True
    # update the armature from edit mode...
    source.update_from_editmode()
    # return to the last mode...
    if source.mode != last_mode:
        bpy.ops.object.mode_set(mode=last_mode)
    # and hide all the retarget pose bones, if they should be hidden...
    for pb in source.pose.bones:
        pb.jk_ard.name = pb.bone.name
        pb.jk_ard.hide_retarget = pb.jk_ard.hide_retarget

def remove_retarget_bones(source):
    last_mode = source.mode
    # go into edit mode and...
    if last_mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    # get and remove all the retarget edit bones...
    pbs = source.pose.bones
    ebs = [source.data.edit_bones.get(pb.jk_ard.retarget) for pb in pbs]
    for retarget_eb in ebs:
        if retarget_eb:
            source.data.edit_bones.remove(retarget_eb)
    # then return to the last mode...
    if source.mode != last_mode:
        bpy.ops.object.mode_set(mode=last_mode)

def set_mesh_retargeting(source):
    # find all the meshes that use the source armature and get a copy of the source...
    meshes = [ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.find_armature() == source]
    source_copy = get_copied_object(source)
    for mesh in meshes:
        mesh_copy = get_copied_object(mesh)
        armature_mods = [mo for mo in mesh_copy.modifiers if mo.type == 'ARMATURE']
        for mod in armature_mods:
            mod.object = source_copy

def set_automatic_offset(self, pb, target):
    # get the current loc rot and scale...
    pb_loc = pb.location[:]
    last_rot_mode = pb.rotation_mode
    # easier to calulate for only one rotation mode...
    if pb.rotation_mode != 'QUATERNION':
        pb.rotation_mode = 'QUATERNION'
    pb_rot = pb.rotation_quaternion[:]
    pb_sca = pb.scale[:]
    if self.auto == 'LOCATION':
        # clear the location and update view layer...
        pb.location = [0.0, 0.0, 0.0]
        bpy.context.view_layer.update()
        # then set the matrix to itself...
        pb.matrix = pb.matrix
        # negate the location we get from that...
        pb.location.negate()
        # and set the rotation and scale back incase they changed...
        pb.rotation_quaternion = pb_rot
        pb.scale = pb_sca
    elif self.auto == 'ROTATION':
        # clear the rotation and update view layer...
        pb.rotation_quaternion = [1, 0.0, 0.0, 0.0]
        bpy.context.view_layer.update()
        # then set the matrix to itself...
        pb.matrix = pb.matrix
        # invert the new rotation...
        pb.rotation_quaternion.invert()
        # and set loc and scale back in case they changed...
        pb.location = pb_loc
        pb.scale = pb_sca
    elif self.auto == 'SCALE':
        # doing the scale is so much simpler...
        t_bone = target.pose.bones[self.target]
        pb.scale = pb.scale * (t_bone.length / pb.length)
    
    # change the rotation mode back if it got changed...
    if pb.rotation_mode != last_rot_mode:
        pb.rotation_mode = last_rot_mode

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- ACTION FUNCTIONS -------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def add_offset_action(source):
    # get the offset action collection...
    offsets = source.data.jk_ard.offsets
    # if our source doesn't yet have any animation data...
    if source.animation_data == None:
        # create it...
        source.animation_data_create()
    # create a new offset action...
    new_offset = bpy.data.actions.new(source.name + "_OFFSET_" + str(len(offsets)))
    # make sure it doesn't get deleted and declare it as an offset action...
    new_offset.use_fake_user, new_offset.jk_ard.is_offset = True, True
    # set it to be the sources active action...
    source.animation_data.action = new_offset
    # and put it into the sources offsets collection...
    offset = offsets.add()
    offset.action = new_offset

def copy_offset_action(source, offset, name):
    copy = offset.action.copy()
    copy.name = name
    copy.jk_ard.is_offset = False
    source.animation_data.action = copy

def add_action_to_offset(offset, action):
    # if the action isn't already assigned to the offset...
    if not any(a.action == action for a in offset.jk_ard.actions):
        # add a new action entry to the offsets target actions...
        target_act = offset.jk_ard.actions.add()
        target_act.action = action

def remove_action_from_offset(offset, action):
    for a in offset.jk_ard.actions:
        if a.action == action:
            offset.jk_ard.actions.remove(offset.jk_ard.actions.find(a))

def get_bone_curves(source):
    bone_curves = {pb.name : 
        {'location' : True if pb.constraints["RETARGET - Copy Location"] and not pb.constraints["RETARGET - Copy Location"].mute else False,
        'rotation' : True if pb.constraints["RETARGET - Copy Rotation"] and not pb.constraints["RETARGET - Copy Rotation"].mute else False,
        'scale' : True if pb.constraints["RETARGET - Copy Scale"] and not pb.constraints["RETARGET - Copy Scale"].mute else False}
            for pb in source.pose.bones}
    return bone_curves

def action_poll(self, action):
    actions = [a for a in bpy.data.actions if any(b.name in fc.data_path for b in self.armature.data.bones for fc in a.fcurves)]
    return action in actions

#def set_retargeted_action()

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- MESH FUNCTIONS ---------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def set_oriented_bones(armature, jk_ard, rot, sca, source):
    bpy.ops.object.mode_set(mode='OBJECT')
    # make sure we bring the target armature...
    target = jk_ard.Target
    target.hide_set(False)
    target.select_set(True)
    # into edit mode with the armature...
    bpy.ops.object.mode_set(mode='EDIT')
    # iterate on AARs bound pose bone collection...
    for pb in AAR.Pose_bones:
        # if the target bone name is in the targets edit bones.. (it should be if it's bound)
        if pb.Target in target.data.edit_bones:
            # we need both source and target edit bones...
            if source and armature.data.bones[pb.name].ACB.Type == 'CONT':
                cont = armature.data.bones[pb.name]
                mech = [mb.name for mb in armature.data.bones if mb.ACB.Type == 'MECH' and mb.parent == cont]
                source = [spb.name for spb in armature.pose.bones if spb.bone.ACB.Type == 'SOURCE' 
                    and spb.constraints["MECHANISM - Copy Transform"].subtarget == mech[0]]
                se_name = source[0]
                me_bone = armature.data.edit_bones[mech[0]]
            else:
                se_name = pb.name #armature.data.edit_bones[pb.name]
                me_bone = None
            # if there are armature control bones and we want to orient to the targets source bones...
            if source and target.data.bones[pb.Target].ACB.Type == 'CONT':
                # just orient to the mech bone because it's rest pose must be the same as the source bones...
                cont = target.data.bones[pb.Target]
                mech = [mb.name for mb in target.data.bones if mb.ACB.Type == 'MECH' and mb.parent == cont]
                te_name = mech[0]
            else:
                te_name = pb.Target
            se_bone = armature.data.edit_bones[se_name]
            te_bone = target.data.edit_bones[te_name]
            # if we are orienting rotation...
            if rot:
                # do some vector math...
                y_vec = te_bone.y_axis
                se_bone.tail = se_bone.head + (y_vec * se_bone.length)
                se_bone.roll = te_bone.roll
            # and setting scale is as simple as setting the length...
            if sca:
                se_bone.length = te_bone.length
            if me_bone != None:
                me_bone.head, me_bone.tail, me_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    # back to object mode and deselect the target...
    bpy.ops.object.mode_set(mode='OBJECT')
    target.select_set(False)
    
def Apply_Mesh_Posing(armature, keep_original):
    bpy.ops.object.mode_set(mode='OBJECT')
    # get all the meshes...
    meshes = [m for m in bpy.context.scene.objects if m.type == 'MESH' and any(mod.type == 'ARMATURE' and mod.object == armature for mod in m.modifiers)]
    # if we want to keep the orignal meshes...
    if keep_original:
        # select them all...
        for mesh in meshes:
            mesh.select_set(True)
        # deselect the armature...
        bpy.context.view_layer.objects.active = meshes[0]
        armature.select_set(False)
        # duplicate all the meshes...
        bpy.ops.object.duplicate()
        # reset the meshes list to be the duped meshes...
        meshes = [m for m in bpy.context.selected_objects if m.type == 'MESH']
        # make the armature active again...
        bpy.context.view_layer.objects.active = armature
        armature.select_set(True)
    # iterate through all meshes...
    for mesh in meshes:
        # iterate through it's modifiers...
        for mod in mesh.modifiers:
            # if it's an armature modifier targeting the retarget target...
            if mod.type == 'ARMATURE' and mod.object == armature:
                # apply and re-add armature modifiers...
                mod_name = mod.name
                context = bpy.context.copy()    
                context["object"] = mesh
                bpy.ops.object.modifier_apply(context, modifier=mod_name)
                arm = mesh.modifiers.new(type='ARMATURE', name=mod_name)
                arm.object = armature
                mesh.select_set(False)
    # go into pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    # apply the pose...
    bpy.ops.pose.armature_apply(selected=False)
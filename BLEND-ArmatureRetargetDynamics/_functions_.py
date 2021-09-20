import bpy

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

def add_retarget_bones(source, names):
    last_mode, AAR = source.mode, source.data.AAR
    sb_names = [n for n in names if "RB_" + n not in source.data.bones]
    if len(sb_names) > 0:
        # go into edit mode and...
        bpy.ops.object.mode_set(mode='EDIT')
        for sb_name in sb_names:
            # create a duplicate of the source bone...
            se_bone = source.data.edit_bones[sb_name]
            re_bone = source.data.edit_bones.new("RB_" + sb_name)
            re_bone.head, re_bone.tail, re_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
            re_bone.use_local_location, re_bone.use_connect = se_bone.use_local_location, se_bone.use_connect
            re_bone.use_inherit_rotation, re_bone.inherit_scale = se_bone.use_inherit_rotation, se_bone.inherit_scale
            re_bone.parent, re_bone.use_deform = se_bone.parent, False
            AAR.pose_bones[sb_name].Retarget = "RB_" + sb_name
    if source.mode != last_mode:
        bpy.ops.object.mode_set(mode=last_mode)
    for pb in AAR.pose_bones:
        pb.hide_retarget = True

def remove_retarget_bones(source, names):
    last_mode = source.mode
    rb_names = [n for n in names if n in source.data.bones]
    if len(rb_names) > 0:
        bpy.ops.object.mode_set(mode='EDIT')
        for rb_name in rb_names:
            re_bone = source.data.edit_bones[rb_name]
            source.data.edit_bones.remove(re_bone)
    if source.mode != last_mode:
        bpy.ops.object.mode_set(mode=last_mode)

def bind_pose_bone(source, target, sb_name, tb_name):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureActiveRetargeting"].preferences
    rb_name = "RB_" + sb_name
    # then into pose mode...
    if source.mode != 'POSE':    
        bpy.ops.object.mode_set(mode='POSE')
    # to bind the bones together...
    sp_bone, rp_bone = source.pose.bones[sb_name], source.pose.bones[rb_name]
    # if the source bone is a pole target...
    if get_is_pole(source, sb_name):
        # add an inverted child of constraint to the retarget bone...
        child_of = rp_bone.constraints.new('CHILD_OF')
        child_of.name, child_of.show_expanded = "RETARGET - Child Of", False
        child_of.target, child_of.subtarget = target, tb_name
        source.data.bones.active = rp_bone.bone
        rp_bone.bone.select = True
        context = bpy.context.copy()
        context["constraint"] = child_of
        bpy.ops.constraint.childof_set_inverse(context, constraint="RETARGET - Child Of", owner='BONE')
        source.data.bones.active = sp_bone.bone
        rp_bone.bone.select = False
    else:
        # add a world space copy transforms to the retarget bone targeting the target bone...
        copy_trans = rp_bone.constraints.new('COPY_TRANSFORMS')
        copy_trans.name, copy_trans.show_expanded = "RETARGET - Copy Transform", False
        copy_trans.target, copy_trans.subtarget = target, tb_name
    # add local copy location, rotation and scale constraints to the source bone targeting the retarget bone...
    copy_loc = sp_bone.constraints.new('COPY_LOCATION')
    copy_loc.name, copy_loc.show_expanded = "RETARGET - Copy Location", False
    copy_loc.use_x, copy_loc.use_y, copy_loc.use_z = prefs.copy_loc.use[:]
    copy_loc.mute, copy_loc.influence = prefs.copy_loc.mute, prefs.copy_loc.influence
    copy_loc.target, copy_loc.subtarget = source, rb_name
    copy_loc.use_offset, copy_loc.target_space, copy_loc.owner_space = True, 'LOCAL', 'LOCAL'
    # copy rotation needs its mix mode to be "Before Orginal"...
    copy_rot = sp_bone.constraints.new('COPY_ROTATION')
    copy_rot.name, copy_rot.show_expanded = "RETARGET - Copy Rotation", False
    copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = prefs.copy_rot.use[:]
    copy_rot.mute, copy_rot.influence = prefs.copy_rot.mute, prefs.copy_rot.influence
    copy_rot.target, copy_rot.subtarget = source, rb_name
    copy_rot.mix_mode, copy_rot.target_space, copy_rot.owner_space = 'BEFORE', 'LOCAL', 'LOCAL'
    # copy scale happens to use the same constraint settings as the copy location...
    copy_sca = sp_bone.constraints.new('COPY_SCALE')
    copy_sca.name, copy_sca.show_expanded = "RETARGET - Copy Scale", False
    copy_sca.use_x, copy_sca.use_y, copy_sca.use_z = prefs.copy_sca.use[:]
    copy_sca.mute, copy_sca.influence = prefs.copy_sca.mute, prefs.copy_sca.influence
    copy_sca.target, copy_sca.subtarget = source, rb_name
    copy_sca.use_offset, copy_sca.target_space, copy_sca.owner_space = True, 'LOCAL', 'LOCAL'
    if sb_name in source.data.AAR.pose_bones:
        pb = source.data.AAR.pose_bones[sb_name]
    else:    
        pb = source.data.AAR.pose_bones.add()
    pb.name, pb.Retarget = sb_name, rb_name
    pb.is_bound, pb.hide_target, pb.hide_retarget = True, True, True

def rebind_pose_bone(source, target, sb_name, tb_name):
    unbind_pose_bone(source, sb_name, "RB_" + sb_name)
    bind_pose_bone(source, target, sb_name, tb_name)

def unbind_pose_bone(source, sb_name, rb_name):
    if rb_name != "":
        # make sure we are in pose mode and...
        if source.mode != 'POSE': 
            bpy.ops.object.mode_set(mode='POSE')
        # get the pose bones and remove the binding contsraints...
        sp_bone, rp_bone = source.pose.bones[sb_name], source.pose.bones[rb_name]
        sb_cons = [c for c in sp_bone.constraints if c.name.startswith("RETARGET - ")]
        rb_cons = [c for c in rp_bone.constraints if c.name.startswith("RETARGET - ")]
        for con in sb_cons:
            sp_bone.constraints.remove(con)
        for con in rb_cons:
            rp_bone.constraints.remove(con)
        source.data.AAR.pose_bones[sb_name].is_bound = False
    
def add_offset_action(source):
    # get the offset action collection...
    offsets = source.data.AAR.offsets
    # if our source doesn't yet have any aniamtion data...
    if source.animation_data == None:
        # create it...
        source.animation_data_create()
    # create a new offset action...
    new_offset = bpy.data.actions.new(source.name + "_OFFSET_" + str(len(offsets)))
    # make sure it doesn'nt get deleted and declare it as an offset action...
    new_offset.use_fake_user, new_offset.AAR.is_offset = True, True
    # set it to be the sources active action...
    source.animation_data.action = new_offset
    # and put it into the sources offsets collection...
    ga_offset = offsets.add()
    ga_offset.action = new_offset

def copy_offset_action(source, offset, name):
    copy = offset.action.copy()
    copy.name = name
    copy.AAR.is_offset = False
    source.animation_data.action = copy

def add_action_to_offset(offset, action):
    # if the action isn't already assigned to the offset...
    if not any(a.action == action for a in offset.AAR.actions):
        # add a new action entry to the offsets target actions...
        tg_action = offset.AAR.actions.add()
        tg_action.action = action

def remove_action_from_offset(offset, action):
    for a in offset.AAR.actions:
        if a.action == action:
            offset.AAR.actions.remove(offset.AAR.actions.find(a))

def get_bone_curves(source):
    bone_curves = {pb.name : 
        {'location' : True if pb.constraints["RETARGET - Copy Location"] and not pb.constraints["RETARGET - Copy Location"].mute else False,
        'rotation' : True if pb.constraints["RETARGET - Copy Rotation"] and not pb.constraints["RETARGET - Copy Rotation"].mute else False,
        'scale' : True if pb.constraints["RETARGET - Copy Scale"] and not pb.constraints["RETARGET - Copy Scale"].mute else False}
            for pb in source.pose.bones}
    return bone_curves

def get_binding(source, binding):
    AAR = source.data.AAR
    # clear its old data... (if any)
    binding.bindings.clear()
    # for each of our pose bones...
    for pb in AAR.pose_bones:
        # add a binding...
        bb = binding.bindings.add()
        # save the name and target...
        bb.name, bb.Target, = pb.name, pb.Target
        if pb.Target != "":
            p_bone = source.pose.bones[pb.name]
            # save the copy location settings...
            copy_loc = p_bone.constraints["RETARGET - Copy Location"]
            bb.copy_loc.use = [copy_loc.use_x, copy_loc.use_y, copy_loc.use_z]
            bb.copy_loc.influence, bb.copy_loc.mute = copy_loc.influence, copy_loc.mute
            # save the copy rotation settings...
            copy_rot = p_bone.constraints["RETARGET - Copy Rotation"]
            bb.copy_rot.use = [copy_rot.use_x, copy_rot.use_y, copy_rot.use_z]
            bb.copy_rot.influence, bb.copy_rot.mute = copy_rot.influence, copy_rot.mute
            # save the copy scale settings...
            copy_sca = p_bone.constraints["RETARGET - Copy Scale"]
            bb.copy_sca.use = [copy_sca.use_x, copy_sca.use_y, copy_sca.use_z]
            bb.copy_sca.influence, bb.copy_sca.mute = copy_sca.influence, copy_sca.mute

def set_binding(source, binding):
    AAR = source.data.AAR
    # unbind all the pose bones...
    for pb in AAR.pose_bones:
        unbind_pose_bone(source, pb.name, pb.retarget)
    # then rebind them all...
    for pb in AAR.pose_bones:   
        # if its name is in the binding...
        if pb.name in binding.bindings:
            # get the binding bone entry...
            bb = binding.bindings[pb.name]
            pb.target = bb.target
            # get the pose bone...
            p_bone = source.pose.bones[pb.name]
            #Bind_pose_Bone(source, AAR.Target, sb_name, tb_name)
            # if the target is not nothing...
            if pb.target != "":
                # load the copy location settings...
                copy_loc = p_bone.constraints["RETARGET - Copy Location"]
                copy_loc.use_x, copy_loc.use_y, copy_loc.use_z = bb.copy_loc.use[:] 
                copy_loc.influence, copy_loc.mute = bb.copy_loc.influence, bb.copy_loc.mute
                # save the copy rotation settings...
                copy_rot = p_bone.constraints["RETARGET - Copy Rotation"]
                copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = bb.copy_rot.use[:]
                copy_rot.influence, copy_rot.mute = bb.copy_rot.influence, bb.copy_rot.mute
                # load the copy scale settings...
                copy_sca = p_bone.constraints["RETARGET - Copy Scale"]
                copy_sca.use_x, copy_sca.use_y, copy_sca.use_z = bb.copy_sca.use[:]
                copy_sca.influence, copy_sca.mute = bb.copy_sca.influence, bb.copy_sca.mute
                pb.is_bound = True
        pb.is_bound = False

def action_poll(self, action):
    actions = [a for a in bpy.data.actions if any(b.name in fc.data_path for b in self.armature.data.bones for fc in a.fcurves)]
    return action in actions
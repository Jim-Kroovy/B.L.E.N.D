import bpy

def Get_Is_Pole(source, sb_name):
    is_pole = False
    for p_bone in source.pose.bones:
        if not is_pole:
            for con in p_bone.constraints:
                if con.type == 'IK' and con.pole_target != None:
                    if con.pole_subtarget == sb_name:
                        is_pole = True
                        break
        else:
            break
    return is_pole

def Bind_Pose_Bone(source, target, sb_name, tb_name):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureActiveRetargeting"].preferences
    rb_name = "RB_" + sb_name
    # go into edit mode and...
    bpy.ops.object.mode_set(mode='EDIT')
    # create a duplicate of the source bone...
    se_bone = source.data.edit_bones[sb_name]
    re_bone = source.data.edit_bones.new("RB_" + se_bone.name)
    re_bone.head, re_bone.tail, re_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    re_bone.use_local_location, re_bone.use_connect = se_bone.use_local_location, se_bone.use_connect
    re_bone.use_inherit_rotation, re_bone.inherit_scale = se_bone.use_inherit_rotation, se_bone.inherit_scale
    re_bone.parent, re_bone.use_deform = se_bone.parent, False
    # then into pose mode...    
    bpy.ops.object.mode_set(mode='POSE')
    # to bind the bones together...
    sp_bone = source.pose.bones[sb_name]
    rp_bone = source.pose.bones[rb_name]
    #is_pole = Get_Is_Pole(source, sb_name)
    # if the source bone is a pole target...
    if Get_Is_Pole(source, sb_name):
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
    copy_loc.use_x, copy_loc.use_y, copy_loc.use_z = prefs.Copy_loc.Use[:]
    copy_loc.mute, copy_loc.influence = prefs.Copy_loc.Mute, prefs.Copy_loc.Influence
    copy_loc.target, copy_loc.subtarget = source, rb_name
    copy_loc.use_offset, copy_loc.target_space, copy_loc.owner_space = True, 'LOCAL', 'LOCAL'
    # copy rotation needs its mix mode to be "Before Orginal"...
    copy_rot = sp_bone.constraints.new('COPY_ROTATION')
    copy_rot.name, copy_rot.show_expanded = "RETARGET - Copy Rotation", False
    copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = prefs.Copy_rot.Use[:]
    copy_rot.mute, copy_rot.influence = prefs.Copy_rot.Mute, prefs.Copy_rot.Influence
    copy_rot.target, copy_rot.subtarget = source, rb_name
    copy_rot.mix_mode, copy_rot.target_space, copy_rot.owner_space = 'BEFORE', 'LOCAL', 'LOCAL'
    # copy scale happens to use the same constraint settings as the copy location...
    copy_sca = sp_bone.constraints.new('COPY_SCALE')
    copy_sca.name, copy_sca.show_expanded = "RETARGET - Copy Scale", False
    copy_sca.use_x, copy_sca.use_y, copy_sca.use_z = prefs.Copy_sca.Use[:]
    copy_sca.mute, copy_sca.influence = prefs.Copy_sca.Mute, prefs.Copy_sca.Influence
    copy_sca.target, copy_sca.subtarget = source, rb_name
    copy_sca.use_offset, copy_sca.target_space, copy_sca.owner_space = True, 'LOCAL', 'LOCAL'
    if sb_name in source.data.AAR.Pose_bones:
        pb = source.data.AAR.Pose_bones[sb_name]
    else:    
        pb = source.data.AAR.Pose_bones.add()
    pb.name, pb.Retarget = sb_name, rb_name
    pb.Is_bound, pb.Hide_target, pb.Hide_retarget = True, True, True

def Rebind_Pose_Bone(source, target, rb_name, tb_name):
    # get the retarget bone and it's copy transform constraint...
    rp_bone = source.pose.bones[rb_name]
    con = rp_bone.constraints["RETARGET - Copy Transform"]
    # and tell it to follow the new target...
    con.subtarget = tb_name

def Unbind_Pose_Bone(source, sb_name, rb_name):
    # make sure we are in pose mode and...
    bpy.ops.object.mode_set(mode='POSE')
    # remove the binding contsraints...
    for con in source.pose.bones[sb_name].constraints:
        if con.name in ["RETARGET - Copy Location", "RETARGET - Copy Rotation", "RETARGET - Copy Scale"]:
            source.pose.bones[sb_name].constraints.remove(con)
    # then into edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    # get rid of the retarget bone...
    if rb_name in source.data.edit_bones:
        re_bone = source.data.edit_bones[rb_name]
        source.data.edit_bones.remove(re_bone)
    # then back to pose mode and set the bone Is Bound bool...
    bpy.ops.object.mode_set(mode='POSE')
    source.data.AAR.Pose_bones[sb_name].Is_bound = False
    
def Add_Offset_Action(source):
    # get the offset action collection...
    offsets = source.data.AAR.Offsets
    # if our source doesn't yet have any aniamtion data...
    if source.animation_data == None:
        # create it...
        source.animation_data_create()
    # create a new offset action...
    new_offset = bpy.data.actions.new(source.name + "_OFFSET_" + str(len(offsets)))
    # make sure it doesn'nt get deleted and declare it as an offset action...
    new_offset.use_fake_user, new_offset.AAR.Is_offset = True, True
    # set it to be the sources active action...
    source.animation_data.action = new_offset
    # and put it into the sources offsets collection...
    ga_offset = offsets.add()
    ga_offset.Action = new_offset

def Copy_Offset_Action(source, offset, name):
    copy = offset.Action.copy()
    copy.name = name
    copy.AAR.Is_offset = False
    source.animation_data.action = copy

def Add_Action_To_Offset(offset, action):
    # if the action isn't already assigned to the offset...
    if not any(a.Action == action for a in offset.AAR.Actions):
        # add a new action entry to the offsets target actions...
        tg_action = offset.AAR.Actions.add()
        tg_action.Action = action

def Remove_Action_From_Offset(offset, action):
    for a in offset.AAR.Actions:
        if a.Action == action:
            offset.AAR.Actions.remove(offset.AAR.Actions.find(a))

def Get_Bone_Curves(source):
    bone_curves = {pb.name : 
        {'location' : True if pb.constraints["RETARGET - Copy Location"] and not pb.constraints["RETARGET - Copy Location"].mute else False,
        'rotation' : True if pb.constraints["RETARGET - Copy Rotation"] and not pb.constraints["RETARGET - Copy Rotation"].mute else False,
        'scale' : True if pb.constraints["RETARGET - Copy Scale"] and not pb.constraints["RETARGET - Copy Scale"].mute else False}
            for pb in source.pose.bones}
    return bone_curves

def Get_Binding(source, binding):
    AAR = source.data.AAR
    # clear its old data... (if any)
    binding.Bindings.clear()
    # for each of our pose bones...
    for pb in AAR.Pose_bones:
        # add a binding...
        bb = binding.Bindings.add()
        # save the name and target...
        bb.name, bb.Target = pb.name, pb.Target
        if pb.Target != "":
            p_bone = source.pose.bones[pb.name]
            # save the copy location settings...
            copy_loc = p_bone.constraints["RETARGET - Copy Location"]
            bb.Copy_loc.Use = [copy_loc.use_x, copy_loc.use_y, copy_loc.use_z]
            bb.Copy_loc.Influence, bb.Copy_loc.Mute = copy_loc.influence, copy_loc.mute
            # save the copy rotation settings...
            copy_rot = p_bone.constraints["RETARGET - Copy Rotation"]
            bb.Copy_rot.Use = [copy_rot.use_x, copy_rot.use_y, copy_rot.use_z]
            bb.Copy_rot.Influence, bb.Copy_rot.Mute = copy_rot.influence, copy_rot.mute
            # save the copy scale settings...
            copy_sca = p_bone.constraints["RETARGET - Copy Scale"]
            bb.Copy_sca.Use = [copy_sca.use_x, copy_sca.use_y, copy_sca.use_z]
            bb.Copy_sca.Influence, bb.Copy_sca.Mute = copy_sca.influence, copy_sca.mute

def Set_Binding(source, binding):
    AAR = source.data.AAR
    # for each of our pose bones...
    for pb in AAR.Pose_bones:
        # if its name is in the binding...
        if pb.name in binding.Bindings:
            print(pb.name)
            # get the binding bone entry...
            bb = binding.Bindings[pb.name]
            # set the target...
            pb.Target = bb.Target
            print(pb.Target)
            # if the target is not nothing...
            if pb.Target != "":
                # get the pose bone...
                p_bone = source.pose.bones[pb.name]
                # load the copy location settings...
                copy_loc = p_bone.constraints["RETARGET - Copy Location"]
                copy_loc.use_x, copy_loc.use_y, copy_loc.use_z = bb.Copy_loc.Use[:] 
                copy_loc.influence, copy_loc.mute = bb.Copy_loc.Influence, bb.Copy_loc.Mute
                # save the copy rotation settings...
                copy_rot = p_bone.constraints["RETARGET - Copy Rotation"]
                copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = bb.Copy_rot.Use[:]
                copy_rot.influence, copy_rot.mute = bb.Copy_rot.Influence, bb.Copy_rot.Mute
                # load the copy scale settings...
                copy_sca = p_bone.constraints["RETARGET - Copy Scale"]
                copy_sca.use_x, copy_sca.use_y, copy_sca.use_z = bb.Copy_sca.Use[:]
                copy_sca.influence, copy_sca.mute = bb.Copy_sca.Influence, bb.Copy_sca.Mute

def Action_Poll(self, action):
    actions = [a for a in bpy.data.actions if any(b.name in fc.data_path for b in self.Armature.bones for fc in a.fcurves)]
    return action in actions
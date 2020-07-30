import bpy

def Bind_Pose_Bone(source, target, sb_name, tb_name):
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
    # add a world space copy transforms to the retarget bone targeting the target bone...
    copy_trans = rp_bone.constraints.new('COPY_TRANSFORMS')
    copy_trans.name, copy_trans.show_expanded = "RETARGET - Copy Transform", False
    copy_trans.target, copy_trans.subtarget = target, tb_name
    # add local copy location, rotation and scale constraints to the source bone targeting the retarget bone...
    copy_loc = sp_bone.constraints.new('COPY_LOCATION')
    copy_loc.name, copy_loc.show_expanded = "RETARGET - Copy Location", False
    copy_loc.target, copy_loc.subtarget = source, rb_name
    copy_loc.use_offset, copy_loc.target_space, copy_loc.owner_space = True, 'LOCAL', 'LOCAL'
    # copy rotation needs its mix mode to be "Before Orginal"...
    copy_rot = sp_bone.constraints.new('COPY_ROTATION')
    copy_rot.name, copy_rot.show_expanded = "RETARGET - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = source, rb_name
    copy_rot.mix_mode, copy_rot.target_space, copy_rot.owner_space = 'BEFORE', 'LOCAL', 'LOCAL'
    # copy scale happens to use the same constraint settings as the copy location...
    copy_sca = sp_bone.constraints.new('COPY_SCALE')
    copy_sca.name, copy_sca.show_expanded = "RETARGET - Copy Scale", False
    copy_sca.target, copy_sca.subtarget = source, rb_name
    copy_sca.use_offset, copy_sca.target_space, copy_sca.owner_space = True, 'LOCAL', 'LOCAL'
    if sb_name in source.data.AAR.Pose_bones:
        entry = source.data.AAR.Pose_bones[sb_name]
    else:    
        entry = source.data.AAR.Pose_bones.add()
    entry.name, entry.Retarget = sb_name, rb_name
    entry.Is_bound, entry.Hide_target, entry.Hide_retarget = True, True, True

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
    copy = offset.copy()
    copy.name = name
    copy.AAR.Is_offset = False
    source.animation_data.action = copy

#def Add_Action_To_Offset(offset, action):

def Get_Bone_Curves(source):
    bone_curves = {pb.name : 
        {'location' : True if pb.constraints["RETARGET - Copy Location"] and not pb.constraints["RETARGET - Copy Location"].mute else False,
        'rotation' : True if pb.constraints["RETARGET - Copy Rotation"] and not pb.constraints["RETARGET - Copy Rotation"].mute else False,
        'scale' : True if pb.constraints["RETARGET - Copy Scale"] and not pb.constraints["RETARGET - Copy Scale"].mute else False}
            for pb in source.pose.bones}
    return bone_curves

def Bake_Action_From_Offset(source, offset, action, step, selected):
    Copy_Offset_Action(source, offset, action.name + "_RETARGET")
    offset.AAR.Action = action
    bpy.ops.nla.bake(frame_start=action.frame_range[0], frame_end=action.frame_range[1], step=step, only_selected=selected, 
        visual_keying=True, clear_constraints=False, clear_parents=False, use_current_action=True, bake_types={'POSE'})

        


import bpy
import time

def Set_Use_FK_Hide_Drivers(armature, index, pb_control, pb_local, add):
    if add:
        # add a driver to the target control so it's hidden when switched to FK
        cb_driver = pb_control.driver_add("hide")
        cb_driver.driver.type = 'SCRIPTED'
        cb_var = cb_driver.driver.variables.new()
        cb_var.name, cb_var.type = "Use FK", 'SINGLE_PROP'
        cb_var.targets[0].id = armature
        cb_var.targets[0].data_path = 'ARL.Chains[' + str(index) + '].Use_fk'
        cb_driver.driver.expression = "Use FK"
        for mod in cb_driver.modifiers:
            cb_driver.modifiers.remove(mod)
        # add a driver to the local target control so it's not hidden when switched to FK
        lb_driver = pb_local.driver_add("hide")
        lb_driver.driver.type = 'SCRIPTED'
        lb_var = lb_driver.driver.variables.new()
        lb_var.name, lb_var.type = "Use FK", 'SINGLE_PROP'
        lb_var.targets[0].id = armature
        lb_var.targets[0].data_path = 'ARL.Chains[' + str(index) + '].Use_fk'
        lb_driver.driver.expression = "not Use FK"
        for mod in lb_driver.modifiers:
            lb_driver.modifiers.remove(mod)
    else:
        pb_control.driver_remove("hide")
        pb_local.driver_remove("hide")

def Set_IK_Settings_Drivers(armature, pb_gizmo, pb_control, add):
    # all the IK settings we need to drive...
    settings = ["ik_stretch", "lock_ik_x", "lock_ik_y", "lock_ik_z", 
        "ik_stiffness_x", "ik_stiffness_y", "ik_stiffness_z",
        "use_ik_limit_x", "ik_min_x", "ik_max_x",
        "use_ik_limit_y", "ik_min_y", "ik_max_y",
        "use_ik_limit_z", "ik_min_z", "ik_max_z"]
    if add:
        # iterate through and set the target setting to copy the source...
        for setting in settings:
            # add driver to setting...
            driver = pb_gizmo.driver_add(setting)
            # add variable to driver...
            var = driver.driver.variables.new()
            var.name, var.type = setting, 'SINGLE_PROP'
            var.targets[0].id = armature
            var.targets[0].data_path = 'pose.bones["' + pb_control.name + '"].' + setting
            # set the expression...
            driver.driver.expression = setting
            # remove unwanted curve modifier...
            for mod in driver.modifiers:
                driver.modifiers.remove(mod)
    else:
        for setting in settings:
            pb_gizmo.driver_remove(setting)

def Add_Pivot_Bone(armature):

def Add_Head_Hold_Twist(armature):

def Add_Tail_Follow_Twist(armature):

def Add_Opposable_IK_Target(armature, sb_name, prefix, affix):
    bpy.ops.object.mode_set(mode='EDIT')
    # get the source bone...
    se_bone = armature.data.edit_bones[sb_name]
    # add the target bone without a parent...
    te_bone = armature.data.edit_bones.new(prefix + sb_name)
    te_bone.head, te_bone.tail, te_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    te_bone.parent, te_bone.use_deform = None, False
    # add the local target bone with the source bone as parent...
    le_bone = armature.data.edit_bones.new(prefix + affix + sb_name)
    le_bone.head, le_bone.tail, le_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    le_bone.parent, le_bone.use_deform = se_bone, False

def Add_IK_Pole(armature, pole_data, sb_name, prefix, affix):
    bpy.ops.object.mode_set(mode='EDIT')
    # get some transform variables for the pole target...
    axes = [True, False] if 'X' in pole_data.Axis else [False, True]
    distance = (0 - pole_data.Distance) if "NEGATIVE" in pole_data.Axis else pole_data.Distance
    vector = (distance, 0, 0) if 'X' in pole_data.Axis else (0, 0, distance)
    # requires pivot point to be individual origins...
    bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
    # get the source and root bones...
    se_bone = armature.data.edit_bones[sb_name]
    # add the pole bone without a parent...
    pe_bone = armature.data.edit_bones.new(prefix + sb_name)
    pe_bone.head, pe_bone.tail, pe_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    pe_bone.parent, pe_bone.use_deform = None, False
    # shift the pole bone on it's local axis...
    bpy.ops.armature.select_all(action='DESELECT')
    pe_bone.select_tail = True
    pe_bone.select_head = True
    bpy.ops.transform.translate(value=vector, orient_type='NORMAL', constraint_axis=(axes[0], False, axes[1]))
    # add the local pole bone with the source bone as parent...
    le_bone = armature.data.edit_bones.new(prefix + affix + sb_name)
    le_bone.head, le_bone.tail, le_bone.roll = pe_bone.head, pe_bone.tail, pe_bone.roll
    le_bone.parent, le_bone.use_deform = se_bone, False

def Add_Plantigrade_Foot_Controls(armature, fb_name, bb_name, side):
    # first we need to set up all the names we'll need..
    ARL = armature.ARL
    # target gizmo and target local names...
    tg_name, tl_name = ARL.Prefixes.Gizmo + fb_name, ARL.Prefixes.Target_leg + 'LOCAL_' + fb_name
    # target parent and roll control names...
    tp_name, rc_name = ARL.Prefixes.Target_leg + fb_name, ARL.Prefixes.Control + fb_name
    # foot pivot and foot roll gizmo names...
    fp_name, fg_name = ARL.Prefixes.Pivot + fb_name, ARL.Prefixes.Gizmo + 'ROLL_' + fb_name
    # ball pivot and ball roll gizmo names...
    bp_name, bg_name = ARL.Prefixes.Pivot + bb_name, ARL.Prefixes.Gizmo + 'ROLL_' + bb_name
    bpy.ops.object.mode_set(mode='EDIT')
    # get the foot and ball bones...
    fe_bone = armature.data.edit_bones[fb_name]
    be_bone = armature.data.edit_bones[bb_name]
    # create a foot pivot that points straight to the floor from the ankle...
    fpe_bone = armature.data.edit_bones.new(fp_name)
    fpe_bone.head = fe_bone.head
    fpe_bone.tail = [fe_bone.head.x, fe_bone.head.y, 0.0]
    fpe_bone.roll = -180.0 if side == 'RIGHT' else 0.0
    fpe_bone.parent, fpe_bone.use_deform = fe_bone.parent, False
    # and parent the foot bone to it...
    fe_bone.parent = fpe_bone
    # create a ball pivot that points straight to the floor from the ball...
    bpe_bone = armature.data.edit_bones.new(bp_name)
    bpe_bone.head = be_bone.head
    bpe_bone.tail = [be_bone.head.x, be_bone.head.y, 0.0]
    bpe_bone.roll = -180.0 if side == 'RIGHT' else 0.0
    bpe_bone.parent, bpe_bone.use_deform = be_bone.parent, False
    # and parent the ball bone to it...
    be_bone.parent = bpe_bone
    # jump into pose mode quick...
    bpy.ops.object.mode_set(mode='POSE')
    # to give the foot pivot a locked track to the ball...
    fpp_bone = armature.pose.bones[fp_name]
    lock_track = fpp_bone.constraints.new('LOCKED_TRACK')
    lock_track.target, lock_track.subtarget = armature, bb_name
    lock_track.track_axis = 'TRACK_NEGATIVE_X'# if side != 'RIGHT' else 'TRACK_X'
    lock_track.lock_axis = 'LOCK_Y'
    # and give the ball pivot a locked track to the foot...
    bpp_bone = armature.pose.bones[bb_name]
    lock_track = bpp_bone.constraints.new('LOCKED_TRACK')
    lock_track.target, lock_track.subtarget = armature, fb_name
    lock_track.track_axis = 'TRACK_X'# if side != 'RIGHT' else 'TRACK_NEGATIVE_X'
    lock_track.lock_axis = 'LOCK_Y'
    # apply and remove the tracking so we have the right rolls...
    bpy.ops.pose.select_all(action='DESELECT')
    fpp_bone.bone.select, bpp_bone.bone.select = True, True
    bpy.ops.pose.armature_apply(selected=True)
    bpy.ops.pose.constraints_clear()
    # then back to edit mode to create the rest of the bones we need...
    bpy.ops.object.mode_set(mode='EDIT')
    # need pivot point to be individual origins...
    bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
    # parent bone is a straight bone at the tail of the pivot with 0.0 roll...
    tpe_bone = armature.data.edit_bones.new(tp_name)
    tpe_bone.head = [fpe_bone.head.x, fpe_bone.head.y, 0.0]
    tpe_bone.tail = [fpe_bone.head.x, fpe_bone.head.y, 0.0 - fpe_bone.length]
    tpe_bone.roll, tpe_bone.use_deform = 0.0, False
    # and the target local bone is a duplicate of the target parent parented to the foot pivot...
    tle_bone = armature.data.edit_bones.new(tl_name)
    tle_bone.head, tle_bone.tail, tle_bone.roll = tpe_bone.head, tpe_bone.tail, tpe_bone.roll
    tle_bone.parent, tle_bone.use_deform = fpe_bone, False
    # roll control bone is duplicate of foot pivot rotated back by 90 degrees and parented to the target parent...
    rce_bone = armature.data.edit_bones.new(rc_name)
    rce_bone.head, rce_bone.tail, rce_bone.roll = fpe_bone.head, fpe_bone.tail, fpe_bone.roll
    rce_bone.parent, rce_bone.use_deform = tpe_bone, False
    bpy.ops.armature.select_all(action='DESELECT')
    rce_bone.select_tail = True
    bpy.ops.transform.rotate(value=-1.5708, orient_axis='Z', orient_type='NORMAL')
    # ball roll gizmo is duplicate of ball bone rotated back by 90 degrees and parented to the target parent...
    bge_bone = armature.data.edit_bones.new(bg_name)
    bge_bone.head, bge_bone.tail, bge_bone.roll = bpe_bone.head, bpe_bone.tail, bpe_bone.roll
    bge_bone.parent, bge_bone.use_deform = tpe_bone, False
    bpy.ops.armature.select_all(action='DESELECT')
    bge_bone.select_tail = True
    bpy.ops.transform.rotate(value=-1.5708, orient_axis='Z', orient_type='NORMAL')
    # foot roll gizmo is duplicate of foot pivot, dropped to its tail, rotated forward 90 degrees and parented to the ball roll gizmo...
    fge_bone = armature.data.edit_bones.new(fg_name)
    fge_bone.head = [fpe_bone.head.x, fpe_bone.head.y, fpe_bone.tail.z]
    fge_bone.tail = [fpe_bone.head.x, fpe_bone.head.y, 0.0 - fpe_bone.length]
    fge_bone.parent, fge_bone.roll, fge_bone.use_deform = bge_bone, fpe_bone.roll, False
    bpy.ops.armature.select_all(action='DESELECT')
    fge_bone.select_tail = True
    bpy.ops.transform.rotate(value=1.5708, orient_axis='Z', orient_type='NORMAL')
    # then the target gizmo bone is a duplicate of the pivot parented to the foot roll gizmo...
    tge_bone = armature.data.edit_bones.new(tg_name)
    tge_bone.head, tge_bone.tail, tge_bone.roll = fpe_bone.head, fpe_bone.tail, fpe_bone.roll
    tge_bone.parent, tge_bone.use_deform = fge_bone, False
    # now the home stretch in pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    # roll control has rotation limited...
    rcp_bone = armature.pose.bones[rc_name]
    limit_rot = rcp_bone.constraints.new('LIMIT_ROTATION')
    limit_rot.name, limit_rot.show_expanded = "ROLL - Limit Rotation", False
    limit_rot.use_limit_x, limit_rot.min_x, limit_rot.max_x = True, -0.785398, 0.785398
    limit_rot.use_limit_y, limit_rot.min_y, limit_rot.max_y = True, -0.785398, 0.785398
    limit_rot.use_limit_z, limit_rot.min_z, limit_rot.max_z = True, -0.785398, 0.785398
    limit_rot.use_transform_limit, limit_rot.owner_space = True, 'LOCAL'
    # foot roll gizmo copies roll control rotation...
    fgp_bone = armature.pose.bones[fg_name]
    copy_rot = fgp_bone.constraints.new('COPY_ROTATION')
    copy_rot.name, copy_rot.show_expanded = "ROLL - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = armature, rc_name, 
    copy_rot.use_x, copy_rot.use_y = False, False
    copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
    # with limited rotation...
    limit_rot = fgp_bone.constraints.new('LIMIT_ROTATION')
    limit_rot.name, limit_rot.show_expanded = "ROLL - Limit Rotation", False
    limit_rot.use_limit_z, limit_rot.max_z = True, 0.785398
    limit_rot.use_transform_limit, limit_rot.owner_space = True, 'LOCAL'
    # and a driver to stop drifting when rolling back...

    # ball roll gizmo copies roll control rotation...
    bgp_bone = armature.pose.bones[bg_name]
    copy_rot = bgp_bone.constraints.new('COPY_ROTATION')
    copy_rot.name, copy_rot.show_expanded = "ROLL - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = armature, rc_name
    copy_rot.use_x, copy_rot.use_y = True, True
    copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
    # with limited rotation...
    limit_rot = bgp_bone.constraints.new('LIMIT_ROTATION')
    limit_rot.name, limit_rot.show_expanded = "ROLL - Limit Rotation", False
    limit_rot.use_limit_z, limit_rot.min_z = True, -0.785398
    limit_rot.use_transform_limit, limit_rot.owner_space = True, 'LOCAL'
    # ball pivot copies ball roll gizmo Z rotation inverted...
    bpp_bone = armature.pose.bones[bp_name]
    copy_rot = bpp_bone.constraints.new('COPY_ROTATION')
    copy_rot.name, copy_rot.show_expanded = "ROLL - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = armature, bg_name
    copy_rot.use_x, copy_rot.use_y, copy_rot.invert_z = False, False, True
    copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
    # foot pivot copies ik target rotation in world space...
    fpp_bone = armature.pose.bones[fp_name]
    copy_rot = fpp_bone.constraints.new('COPY_ROTATION')
    copy_rot.name, copy_rot.show_expanded = "ROLL - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = armature, tg_name
    copy_rot.target_space, copy_rot.owner_space = 'WORLD', 'WORLD'



    



















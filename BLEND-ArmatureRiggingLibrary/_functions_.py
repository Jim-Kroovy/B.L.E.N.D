import bpy
import math

# get distance between start and end...
def Get_Distance(start, end):
    x = end[0] - start[0]
    y = end[1] - start[1]
    z = end[2] - start[2]
    distance = math.sqrt((x)**2 + (y)**2 + (z)**2)
    return distance

def Set_Use_FK_Hide_Drivers(armature, index, tb_name, lb_name, add):
    tb = armature.data.bones[tb_name]
    lb = armature.data.bones[lb_name]
    if add:
        # add a driver to the target control so it's hidden when switched to FK
        cb_driver = tb.driver_add("hide")
        cb_driver.driver.type = 'SCRIPTED'
        cb_var = cb_driver.driver.variables.new()
        cb_var.name, cb_var.type = "Use FK", 'SINGLE_PROP'
        cb_var.targets[0].id = armature
        cb_var.targets[0].data_path = 'ARL.Chains[' + str(index) + '].Use_fk'
        cb_driver.driver.expression = "Use FK"
        for mod in cb_driver.modifiers:
            cb_driver.modifiers.remove(mod)
        # add a driver to the local target control so it's not hidden when switched to FK
        lb_driver = lb.driver_add("hide")
        lb_driver.driver.type = 'SCRIPTED'
        lb_var = lb_driver.driver.variables.new()
        lb_var.name, lb_var.type = "Use FK", 'SINGLE_PROP'
        lb_var.targets[0].id = armature
        lb_var.targets[0].data_path = 'ARL.Chains[' + str(index) + '].Use_fk'
        lb_driver.driver.expression = "not Use FK"
        for mod in lb_driver.modifiers:
            lb_driver.modifiers.remove(mod)
    else:
        tb.driver_remove("hide")
        lb.driver_remove("hide")

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

def Get_Is_Bone_Rigged(armature, name):
    ARL = armature.ARL
    is_rigged = False
    rigging = None
    rigging_type = ''
    return is_rigged, rigging, rigging_type

def Get_Chain_Target_Affix(affixes, appendage):
    # could of been a ternary condition, but that would be a bit long...
    if appendage == 'ARM':
        affix = affixes.Target_arm
    elif appendage == 'DIGIT':
        affix = affixes.Target_digit
    elif appendage == 'LEG':
        affix = affixes.Target_leg
    elif appendage == 'SPINE':
        affix = affixes.Target_spine
    elif appendage == 'TAIL':
        affix = affixes.Target_tail
    elif appendage == 'WING':
        affix = affixes.Target_wing
    return affix

def Add_Pivot_Bone(armature, tb_name, pb_type, is_parent):
    ARL = armature.ARL
    # get the name...
    pb_name = ARL.Affixes.Pivot + tb_name      
    bpy.ops.object.mode_set(mode='EDIT')
    # get the target edit bone...
    te_bone = armature.data.edit_bones[tb_name]
    # create the pivot bone...
    pe_bone = armature.data.edit_bones.new(pb_name)
    pe_bone.head, pe_bone.tail, pe_bone.roll = te_bone.head, te_bone.tail, te_bone.roll
    pe_bone.use_deform = False
    # if the pivot should share the targets parent...
    if pb_type == 'PARENT_SHARE':
        pe_bone.parent = te_bone.parent
    # or skip it...
    elif pb_type == 'PARENT_SKIP':
        if te_bone.parent != None:
            pe_bone.parent = te_bone.parent.parent
    # if the pivot bone is the parent of the target bone...
    if is_parent:
        te_bone.use_connect = False 
        te_bone.parent = pe_bone
    return pb_name

def Add_Head_Hold_Twist(armature, sb_name, tb_name, head_tail, limits_x, limits_z, has_pivot):
    bpy.ops.object.mode_set(mode='POSE')
    sp_bone = armature.pose.bones[sb_name]
    # give it a damped track...
    damp_track = sp_bone.constraints.new('DAMPED_TRACK')
    damp_track.name, damp_track.show_expanded = "TWIST - Damped Track", False
    damp_track.target, damp_track.subtarget, damp_track.head_tail = armature, tb_name, head_tail
    # and whatever limits might be required...
    limit_rot = sp_bone.constraints.new('LIMIT_ROTATION')
    limit_rot.name, limit_rot.show_expanded, limit_rot.owner_space = "Twist - Limit Rotation", False, 'LOCAL'
    limit_rot.use_limit_x, limit_rot.min_x, limit_rot.max_x = limits_x[0], limits_x[1], limits_x[2]
    limit_rot.use_limit_z, limit_rot.min_z, limit_rot.max_z = limits_z[0], limits_z[1], limits_z[2] 
    # give it a pivot bone if it should have one...
    if has_pivot:
        Add_Pivot_Bone(armature, sb_name, 'PARENT_SKIP', True)
    else:
        bpy.ops.object.mode_set(mode='EDIT')
        se_bone = armature.data.edit_bones[sb_name]
        se_bone.parent = se_bone.parent.parent
        bpy.ops.object.mode_set(mode='POSE')

def Add_Tail_Follow_Twist(armature, sb_name, tb_name, influence, limits_y, has_pivot):
    bpy.ops.object.mode_set(mode='POSE')
    sp_bone = armature.pose.bones[sb_name]
    # give it rotational IK limited to the Y axis...
    ik = sp_bone.constraints.new('IK')
    ik.name, ik.show_expanded = "TWIST - IK", False
    ik.target, ik.subtarget, armature, tb_name
    ik.chain_count, ik.use_location, ik.use_rotation, ik.influence = 1, False, True, influence
    sp_bone.use_ik_limt_y, sp_bone.ik_min_y, sp_bone.ik_max_y = limits_y[0], limits_y[1], limits_y[2]
    # give it a pivot bone if it should have one...
    if has_pivot:
        Add_Pivot_Bone(armature, sb_name, 'PARENT_SHARE', True)
    
def Add_Chain_Pole(armature, axes, distance, sb_name, limb):
    ARL = armature.ARL
    pb_name = Get_Chain_Target_Affix(ARL.Affixes, limb) + sb_name
    lb_name = Get_Chain_Target_Affix(ARL.Affixes, limb) + ARL.Affixes.Local + sb_name
    bpy.ops.object.mode_set(mode='EDIT')
    # get some transform variables for the pole target...
    vector = (distance, 0, 0) if axes[0] else (0, 0, distance)
    # requires pivot point to be individual origins...
    bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
    # get the source bone...
    se_bone = armature.data.edit_bones[sb_name]
    # add the pole bone without a parent...
    pe_bone = armature.data.edit_bones.new(pb_name)
    pe_bone.head, pe_bone.tail, pe_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    pe_bone.parent, pe_bone.use_deform = None, False
    # shift the pole bone on it's local axis...
    bpy.ops.armature.select_all(action='DESELECT')
    pe_bone.select_tail = True
    pe_bone.select_head = True
    bpy.ops.transform.translate(value=vector, orient_type='NORMAL', constraint_axis=(axes[0], False, axes[1]))
    # add the local pole bone with the source bone as parent...
    le_bone = armature.data.edit_bones.new(lb_name)
    le_bone.head, le_bone.tail, le_bone.roll = pe_bone.head, pe_bone.tail, pe_bone.roll
    le_bone.parent, le_bone.use_deform = se_bone, False
    # then we need to set the FK hide drivers for the target and its local bone...
    bpy.ops.object.mode_set(mode='POSE')
    Set_Use_FK_Hide_Drivers(armature, len(ARL.Chains) - 1, pb_name, lb_name, True)
    return pb_name

def Add_Opposable_Chain_Target(armature, sb_name, limb):
    ARL = armature.ARL
    bpy.ops.object.mode_set(mode='EDIT')
    # get the source bone and naming...
    se_bone = armature.data.edit_bones[sb_name]
    tb_name = Get_Chain_Target_Affix(ARL.Affixes, limb) + sb_name
    lb_name = Get_Chain_Target_Affix(ARL.Affixes, limb) + ARL.Affixes.Local + sb_name
    # add a pivot bone to offset the target rotation...
    pb_name = Add_Pivot_Bone(armature, sb_name, 'PARENT_SHARE', True)
    # add the target bone without a parent...
    te_bone = armature.data.edit_bones.new(tb_name)
    te_bone.head, te_bone.tail, te_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    te_bone.parent, te_bone.use_deform = None, False
    # add the local target bone with the source bone as parent...
    le_bone = armature.data.edit_bones.new(lb_name)
    le_bone.head, le_bone.tail, le_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    le_bone.parent, le_bone.use_deform = se_bone, False
    # jump to pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    # to give the pivot bone a world space copy rotation constraint to the target...
    pp_bone = armature.pose.bones[pb_name]
    copy_rot = pp_bone.constraints.new('COPY_ROTATION')
    copy_rot.name, copy_rot.show_expanded = "TARGET - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = armature, tb_name
    # then we need to set the FK hide drivers for the target and its local bone...
    Set_Use_FK_Hide_Drivers(armature, len(ARL.Chains) - 1, tb_name, lb_name, True)
    return tb_name

def Add_Forward_Chain_Target(armature, sb_name, eb_name, limb):
    ARL = armature.ARL
    # get the name of the control...
    tb_name = ARL.Control + limb + "_" + sb_name
    # hop into edit mode and get the start and end bones
    bpy.ops.object.mode_set(mode='EDIT')
    se_bone = armature.data.edit_bones[sb_name]
    ee_bone = armature.data.edit_bones[eb_name]
    # create the control as a copy of the start bone...
    ce_bone = armature.data.edit_bones.new(tb_name)
    ce_bone.head, ce_bone.tail, ce_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    ce_bone.parent, ce_bone.deform = se_bone.parent, False
    # then set to be as long as the chain...
    bpy.ops.armature.select_all(action='DESELECT')
    ce_bone.select_tail = True
    bpy.ops.transform.translate(value=(0, Get_Distance(ce_bone.tail, ee_bone.tail), 0), orient_type='NORMAL', constraint_axis=(False, True, False))
    return tb_name

def Add_Scalar_Chain_Target(armature, sb_name, cb_name, limb):
    ARL = armature.ARL
    # get the source bone...
    se_bone = armature.data.edit_bones[sb_name]
    ce_bone = armature.data.edit_bones[cb_name]
    tb_name = Get_Chain_Target_Affix(ARL.Affixes, limb) + sb_name
    lb_name = Get_Chain_Target_Affix(ARL.Affixes, limb) + ARL.Affixes.Local + sb_name
    # add the target bone parented to the control...
    te_bone = armature.data.edit_bones.new(tb_name)
    # add the target bone parented to the control with its head at the tail of the source bone...
    te_bone.head, te_bone.parent, te_bone.use_deform = se_bone.tail, ce_bone, False
    # and orient it to the source...
    te_bone.align_orientation(se_bone)
    # add the local target bone with the source bone as parent...
    le_bone = armature.data.edit_bones.new(lb_name)
    le_bone.head, le_bone.tail, le_bone.roll = te_bone.head, te_bone.tail, te_bone.roll
    le_bone.parent, le_bone.use_deform = se_bone, False
    # then we need to set the FK hide drivers for the target and its local bone...
    bpy.ops.object.mode_set(mode='POSE')
    Set_Use_FK_Hide_Drivers(armature, len(ARL.Chains) - 1, tb_name, lb_name, True)
    return tb_name

def Add_Forward_Chain_Bones(armature, cb_names, tb_name, loc, rot, sca, target, owner):
    # need to be in pose mode and know what constraints to add...
    bpy.ops.object.mode_set(mode='POSE')
    rotation = True if any(r == True for r in rot) else False
    location = True if any(l == True for l in loc) else False
    scale = True if any(s == True for s in sca) else False
    # for every chain bone name...
    for cb_name in cb_names:
        # we need to get the pose bone...
        cp_bone = armature.pose.bones[cb_name]
        # and give it the relevant constraints...
        if rotation:
            copy_rot = cp_bone.constraints.new('COPY_ROTATION')
            copy_rot.name, copy_rot.show_expanded = "FORWARD - Copy Rotation", False
            copy_rot.target, copy_rot.subtarget = armature, tb_name
            copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = rot[0], rot[1], rot[2]
            copy_rot.target_space, copy_rot.owner_space = target, owner
        if location:
            copy_loc = cp_bone.constraints.new('COPY_LOCATION')
            copy_loc.name, copy_loc.show_expanded = "FORWARD - Copy Location", False
            copy_loc.target, copy_loc.subtarget = armature, tb_name
            copy_loc.use_x, copy_loc.use_y, copy_loc.use_z = loc[0], rot[1], rot[2]
            copy_loc.target_space, copy_loc.owner_space = target, owner
        if scale:
            copy_sca = cp_bone.constraints.new('COPY_SCALE')
            copy_sca.name, copy_sca.show_expanded = "FORWARD - Copy Scale", False
            copy_sca.target, copy_sca.subtarget = armature, tb_name
            copy_sca.use_x, copy_sca.use_y, copy_sca.use_z = sca[0], sca[1], sca[2]
            copy_sca.target_space, copy_sca.owner_space = target, owner

def Add_Opposable_Chain_Bones(armature, cb_names, tb_name, pb_name, p_angle):
    ARL = armature.ARL
    bpy.ops.object.mode_set(mode='EDIT')
    # set the parents...
    sb_parent = armature.data.edit_bones[cb_names[-1]].parent
    gb_parent = armature.data.edit_bones[cb_names[-1]].parent
    # do the edit mode things...
    for cb_name in reversed(cb_names):
        # get the control edit bone...
        ce_bone = armature.data.edit_bones[cb_name]
        se_name = ARL.Affixes.Gizmo + "STRETCH_" + cb_name
        ge_name = ARL.Affixes.Gizmo + cb_name
        # add a copy of it that's going to do some stretching...
        se_bone = armature.data.edit_bones.new(se_name)
        se_bone.head, se_bone.tail, se_bone.roll, = ce_bone.head, ce_bone.tail, ce_bone.roll
        se_bone.inherit_scale, se_bone.use_deform, se_bone.parent = 'NONE', False, sb_parent
        sb_parent = se_bone
        # and another copy that will do limited stretching...
        ge_bone = armature.data.edit_bones.new(ge_name)
        ge_bone.head, ge_bone.tail, ge_bone.roll, = ce_bone.head, ce_bone.tail, ce_bone.roll
        ge_bone.inherit_scale, ge_bone.use_deform, ge_bone.parent = 'NONE', False, gb_parent
        gb_parent = ge_bone
    bpy.ops.object.mode_set(mode='POSE')
    # do the pose mode things...
    for i, cb_name in enumerate(cb_names):
        # get the names and pose bones...
        cp_bone = armature.pose.bones[cb_name]
        sb_name = ARL.Affixes.Gizmo + "STRETCH_" + cb_name
        gb_name = ARL.Affixes.Gizmo + cb_name
        sp_bone = armature.pose.bones[sb_name]
        gp_bone = armature.pose.bones[gb_name]
        # control bone copies local rotation of gizmo...
        copy_rot = cp_bone.constraints.new('COPY_ROTATION')
        copy_rot.name, copy_rot.show_expanded = "OPPOSABLE - Copy Rotation", False
        copy_rot.target, copy_rot.subtarget = armature, gb_name
        copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
        # and has a default a ik stretch value...
        cp_bone.ik_stretch = 0.1
        # both gizmo and stretch have their ik settings driven by the control...
        Set_IK_Settings_Drivers(armature, sp_bone, cp_bone, True)
        Set_IK_Settings_Drivers(armature, gp_bone, cp_bone, True)
        # the gizmo copies the Y scale of the stretch...
        copy_sca = gp_bone.constraints.new('COPY_SCALE')
        copy_sca.name, copy_sca.show_expanded = "OPPOSABLE - Copy Scale", False
        copy_sca.target, copy_sca.subtarget = armature, sb_name
        copy_sca.use_offset, copy_sca.use_x, copy_sca.use_z = True, False, False
        copy_sca.target_space, copy_sca.owner_space = 'LOCAL', 'LOCAL'
        # with limitations for extra animation dynamic...
        limit_sca = gp_bone.constraints.new('LIMIT_SCALE')
        limit_sca.name, limit_sca.show_expanded = "OPPOSABLE - Limit Scale", False
        limit_sca.use_min_y, limit_sca.use_max_y = True, True
        limit_sca.min_y, limit_sca.max_y, limit_sca.owner_space = 1.0, 2.0, 'LOCAL'
        # if we are on the last iteration...
        if cb_name == cb_names[0]:
            # add the IK to the stretch gizmo...
            ik = sp_bone.constraints.new("IK")
            ik.name, ik.show_expanded = "OPPOSABLE - IK", False
            ik.target, ik.subtarget = armature, tb_name
            ik.pole_target, ik.pole_subtarget = armature, pb_name
            ik.pole_angle, ik.use_stretch, ik.chain_count = p_angle, True, len(cb_names)
            # add the IK to the stretch gizmo... (no stretch)
            ik = gp_bone.constraints.new("IK")
            ik.name, ik.show_expanded = "OPPOSABLE - IK", False
            ik.target, ik.subtarget = armature, tb_name
            ik.pole_target, ik.pole_subtarget = armature, pb_name
            ik.pole_angle, ik.use_stretch, ik.chain_count = p_angle, False, len(cb_names)

def Add_Plantigrade_Foot_Controls(armature, fb_name, bb_name, side):
    # first we need to set up all the names we'll need..
    ARL = armature.ARL
    # target gizmo and target local names...
    tg_name, tl_name = ARL.Affixes.Gizmo + fb_name, ARL.Affixes.Target_leg + ARL.Affixes.Roll + fb_name
    # target parent and roll control names...
    tp_name, rc_name = ARL.Affixes.Target_leg + fb_name, ARL.Affixes.Control + ARL.Affixes.Roll + fb_name
    # foot pivot and foot roll gizmo names...
    fp_name, fg_name = ARL.Affixes.Pivot + fb_name, ARL.Affixes.Gizmo + ARL.Affixes.Roll + fb_name
    # ball pivot and ball roll gizmo names...
    bp_name, bg_name = ARL.Affixes.Pivot + bb_name, ARL.Affixes.Gizmo + ARL.Affixes.Roll + bb_name
    bpy.ops.object.mode_set(mode='EDIT')
    # get the foot and ball bones and make sure they are not connected...
    fe_bone = armature.data.edit_bones[fb_name]
    be_bone = armature.data.edit_bones[bb_name]
    fe_bone.use_connect, be_bone.use_connect = False, False
    # create a foot pivot that points straight to the floor from the ankle...
    fpe_bone = armature.data.edit_bones.new(fp_name)
    fpe_bone.head = fe_bone.head
    fpe_bone.tail = [fe_bone.head.x, fe_bone.head.y, 0.0]
    fpe_bone.roll = -180.0 if side == 'RIGHT' else 0.0
    fpe_bone.parent, fpe_bone.use_deform = fe_bone.parent, False
    # create a ball pivot that points straight to the floor from the ball...
    bpe_bone = armature.data.edit_bones.new(bp_name)
    bpe_bone.head = be_bone.head
    bpe_bone.tail = [be_bone.head.x, be_bone.head.y, 0.0]
    bpe_bone.roll = -180.0 if side == 'RIGHT' else 0.0
    bpe_bone.parent, bpe_bone.use_deform = be_bone.parent, False
    # jump into pose mode quick...
    bpy.ops.object.mode_set(mode='POSE')
    # to give the foot pivot a locked track to the ball...
    fpp_bone = armature.pose.bones[fp_name]
    lock_track = fpp_bone.constraints.new('LOCKED_TRACK')
    lock_track.target, lock_track.subtarget = armature, bb_name
    lock_track.track_axis = 'TRACK_NEGATIVE_X' if side != 'RIGHT' else 'TRACK_X'
    lock_track.lock_axis = 'LOCK_Y'
    # and give the ball pivot a locked track to the foot...
    bpp_bone = armature.pose.bones[bp_name]
    lock_track = bpp_bone.constraints.new('LOCKED_TRACK')
    lock_track.target, lock_track.subtarget = armature, fb_name
    lock_track.track_axis = 'TRACK_X' if side != 'RIGHT' else 'TRACK_NEGATIVE_X'
    lock_track.lock_axis = 'LOCK_Y'
    # apply and remove the tracking so we have the right rolls...
    bpy.ops.pose.select_all(action='DESELECT')
    fpp_bone.bone.select, bpp_bone.bone.select = True, True
    bpy.ops.pose.armature_apply(selected=True)
    bpy.ops.pose.constraints_clear()
    bpy.ops.object.mode_set(mode='EDIT')
    # get those foot and ball edit bones again because we swapped mode...
    fe_bone, be_bone = armature.data.edit_bones[fb_name], armature.data.edit_bones[bb_name]
    fpe_bone, bpe_bone = armature.data.edit_bones[fp_name], armature.data.edit_bones[bp_name]
    # parent the ball and foot to their pivots...
    be_bone.parent, fe_bone.parent = bpe_bone, fpe_bone
    # need pivot point to be individual origins fr this next bit...
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
    bpy.ops.transform.rotate(value=-1.5708 if side != 'RIGHT' else 1.5708, orient_axis='Z', orient_type='NORMAL')
    # ball roll gizmo is duplicate of ball bone rotated back by 90 degrees and parented to the target parent...
    bge_bone = armature.data.edit_bones.new(bg_name)
    bge_bone.head, bge_bone.tail, bge_bone.roll = bpe_bone.head, bpe_bone.tail, bpe_bone.roll
    bge_bone.parent, bge_bone.use_deform = tpe_bone, False
    bpy.ops.armature.select_all(action='DESELECT')
    bge_bone.select_tail = True
    bpy.ops.transform.rotate(value=-1.5708 if side != 'RIGHT' else 1.5708, orient_axis='Z', orient_type='NORMAL')
    # foot roll gizmo is duplicate of foot pivot, dropped to its tail, rotated forward 90 degrees and parented to the ball roll gizmo...
    fge_bone = armature.data.edit_bones.new(fg_name)
    fge_bone.head = [fpe_bone.head.x, fpe_bone.head.y, fpe_bone.tail.z]
    fge_bone.tail = [fpe_bone.head.x, fpe_bone.head.y, 0.0 - fpe_bone.length]
    fge_bone.parent, fge_bone.roll, fge_bone.use_deform = bge_bone, fpe_bone.roll, False
    bpy.ops.armature.select_all(action='DESELECT')
    fge_bone.select_tail = True
    bpy.ops.transform.rotate(value=1.5708 if side != 'RIGHT' else -1.5708, orient_axis='Z', orient_type='NORMAL')
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
    if side == 'RIGHT':
        limit_rot.use_limit_z, limit_rot.min_z = True, -0.785398
    else:
        limit_rot.use_limit_z, limit_rot.max_z = True, 0.785398
    limit_rot.use_transform_limit, limit_rot.owner_space = True, 'LOCAL'
    # and a driver to stop drifting when rolling back...
    driver = fgp_bone.driver_add("location", 0)       
    var = driver.driver.variables.new()
    var.name = "Z_Roll"
    var.type = 'TRANSFORMS'
    var.targets[0].id = armature
    var.targets[0].bone_target = rc_name
    var.targets[0].transform_type = 'ROT_Z'
    var.targets[0].transform_space = 'LOCAL_SPACE'
    driver.driver.expression = "Z" + "_Roll * 0.05 * -1 if " + "Z" + "_Roll " + ("<" if side == 'RIGHT' else ">") + " 0 else 0"
    for mod in driver.modifiers:
        driver.modifiers.remove(mod)
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
    if side == 'RIGHT':
        limit_rot.use_limit_z, limit_rot.max_z = True, 0.785398
    else:
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
    # return the ik target name...
    return tg_name

def Add_Digitigrade_Foot_Controls(armature, fb_name, bb_name, side):
    # first we need to set up all the names we'll need..
    ARL = armature.ARL

def Add_Spline_Chain_Bones(armature, cb_names, tb_names):
    ARL = armature.ARL
    bpy.ops.object.mode_set(mode='EDIT')
    # iterate on target chain bones...
    parent = armature.data.edit_bones[cb_names[0]].parent
    for cb_name in cb_names:
        # get the target edit bone...
        ce_bone = armature.data.edit_bones[cb_name]
        se_name = ARL.Affixes.Gizmo + cb_name
        # add a copy of it with forward axis at zero so we get a straight chain...
        se_bone = armature.data.edit_bones.new(se_name)
        se_bone.head, se_bone.tail = [0.0, 0.0, ce_bone.head.z], [0.0, 0.0, ce_bone.tail.z]
        se_bone.roll, se_bone.use_deform, se_bone.parent = ce_bone.roll, False, parent
        # set the parent for the next iteration...
        parent = se_bone
        if cb_name in tb_names: # should i just pass the whole property group into here?
            te_name = ARL.Affixes.Target_spline + cb_name
            te_bone = armature.data.edit_bones.new(te_name)
            te_bone.head, te_bone.tail = [0.0, 0.0, ce_bone.head.z], [0.0, 0.0, ce_bone.tail.z]
            te_bone.roll, te_bone.use_deform, te_bone.parent = ce_bone.roll, False, None

def Add_Spline_Chain_Curve(armature, tb_names, sc_name):
    # in object mode...
    bpy.ops.object.mode_set(mode='OBJECT')
    # let's create a new curve and object for it with some basic display settings...
    curve = bpy.data.curves.new(name=sc_name, type='CURVE')
    curve.dimensions, curve.extrude, curve.bevel_depth = '3D', 0.01, 0.05
    obj = bpy.data.objects.new(name=sc_name, object_data=curve)
    obj.display_type = 'WIRE'
    # parent to the armature and link to the same collections...
    obj.parent = armature
    for collection in armature.users_collection:
        bpy.data.collections[collection.name].objects.link(obj)
    # set it to active, hope into edit mode and give it a bezier spline...
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    spline = curve.splines.new('BEZIER')
    # then for each bone in the spline targets...
    for i, tb_name in enumerate(tb_names):
        # we get the pose bone...
        tp_bone = armature.pose.bones[tb_name]
        # add a control point...
        if i > 0:
            spline.bezier_points.add(count=1)
        index = len(spline.bezier_points) - 1
        # get the control point and set its coordinates and handles relative to the bone...
        tb_point = spline.bezier_points[index]
        tb_point.co = tp_bone.head
        tb_point.handle_left = [tp_bone.head.x, tp_bone.head.y, tp_bone.head.z - 0.01]
        tb_point.handle_right = tp_bone.tail  
    # need a seperate iteration for hooking... (otherwise only the last hook applies?)
    for i, tb_name in enumerate(tb_names):
        bpy.ops.object.mode_set(mode='OBJECT')
        hook = obj.modifiers.new(name=tb_name + " - Hook", type='HOOK')
        hook.object, hook.subtarget = armature, tb_name
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='DESELECT')
        tb_point = curve.splines[0].bezier_points[i]
        tb_point.select_control_point = True
        tb_point.select_left_handle = True
        tb_point.select_right_handle = True
        bpy.ops.object.hook_assign(modifier=tb_name + " - Hook")
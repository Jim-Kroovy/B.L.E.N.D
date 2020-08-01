import bpy

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

def Add_IK_Target(armature, sb_name, prefix, affix):
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

# incrementally adjusts an edit bone around a normal axis to reach the target location channel...
def Set_Bone_Rotation_By_Step(bone, axis, c_int, t_loc):
    # declare some variables...
    increment = 0.01
    step = False
    direction = Get_Rot_Direction_Shortest(bone, axis[0], c_int, t_loc)
    last = bone.tail[c_int]
    # going to put a limit on how long this can run...
    time_start = time.time()
    # while loop on increment size...
    while increment > 0.00000001:
        # switch bool on positive vs negative step over...
        if (bone.tail[c_int] > t_loc and last < t_loc) or (bone.tail[c_int] < t_loc and last > t_loc):
            direction = axis[0] + ('' if 'NEGATIVE' in direction else '_NEGATIVE') 
            step = True
        # on step over make increment smaller...    
        if step == True:
            increment = (increment * 0.1)
            step = False
        last = bone.tail[c_int]
        # value gets negated depending on direction and step...
        val = (increment * 1) if 'NEGATIVE' in direction else (increment * -1)
        print(val)
        bpy.ops.transform.rotate(value=val, orient_axis=direction[0], orient_type='NORMAL')
        # safety precaution...
        if increment < 0.0000001 or time.time() >= (time_start + 5):
            print(time.time() - time_start)
            break
    bone.select = True
    bpy.ops.armature.calculate_roll(type='ACTIVE')

def Add_Foot_Controls(armature, sb_name, pb_name, prefix, affix):
    # get the foot and ball bones...
    se_bone = armature.data.edit_bones[sb_name]
    pe_bone = armature.data.edit_bones[pb_name]
    # create foot roll system pointing straight forward at 0, 0, 0...
















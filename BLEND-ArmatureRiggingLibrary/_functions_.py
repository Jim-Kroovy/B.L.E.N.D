import bpy
import math
import mathutils

def Get_Distance(start, end):
    x, y, z = end[0] - start[0], end[1] - start[1], end[2] - start[2]
    distance = math.sqrt((x)**2 + (y)**2 + (z)**2)
    return distance

def Get_Chain_Target_Affix(affixes, limb):
    tb_affixes = {'ARM' : affixes.Target_arm, 'DIGIT': affixes.Target_digit, 'LEG' : affixes.Target_leg,
        'SPINE' : affixes.Target_spine, 'TAIL' : affixes.Target_tail, 'WING' : affixes.Target_wing}
    return tb_affixes[limb]

def Get_Pole_Angle(axis):
    angle = -3.141593 if axis == 'X_NEGATIVE' else 1.570796 if axis == 'Z' else -1.570796 if axis == 'Z_NEGATIVE' else 0.0
    return angle
    
def Get_Bone_Side(name):
    n_up = name.upper()
    side = 'LEFT' if n_up.endswith(".L") or n_up.endswith("_L") else 'RIGHT' if n_up.endswith(".R") or n_up.endswith("_R") else 'NONE'
    return side

def Get_Bone_Limb(name):
    limbs = {'ARM' : ["HUMERUS", "ULNA", "SHOULDER", "ELBOW", "WRIST"], 'LEG' : ["FEMUR", "TIBIA", "THIGH", "CALF", "KNEE", "ANKLE"],
    'DIGIT' : ["FINGER", "TOE", "THUMB", "INDEX", "MIDDLE", "RING", "LITTLE", "PINKY"], 'SPINE' : ["LUMBAR", "THORACIC", "CERVICAL", "VERTEBRA", "NECK", "HEAD"],
    'TAIL' : ["CAUDAL", "COCCYX"], 'WING' : ["CARPUS", "TIP"]}
    limb = 'ARM'
    for l, strings in limbs.items():
        if l in name.upper():
            limb = l
            break
        elif any(string in name.upper() for string in strings):
            limb = l
            break
    return limb

# yes i'm slacking for the default shapes and cba to import the bmesh module lol...
def Get_Default_Bone_Shape(armature, bone_type):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingLibrary"].preferences
    # if we aren't using custom shapes just return shape as None...
    if not prefs.Custom_shapes:
        shape = None
    # if the shape already exists we can just return it...
    elif "Bone_Shape_" + bone_type in bpy.data.objects:
        shape = bpy.data.objects["Bone_Shape_" + bone_type]
    # otherwise...
    else:
        # we need to hop into object mode, deselect everything...
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        # and create and transform the right shape...
        if bone_type == 'CHAIN':
            bpy.ops.mesh.primitive_cone_add(vertices=8, calc_uvs=False, enter_editmode=False, align='WORLD', location=(0, 0, 0))
            shape = bpy.context.view_layer.objects.active
            shape.location, shape.rotation_euler, shape.scale = [0.0, 0.5, 0.0], [-1.570796, 0.0, 0.0], [0.25, 0.25, 0.05]
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.transform.translate(value=(0, 0.05, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False))
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            for vert in [v for v in shape.data.vertices if v.co.z < 0.001]:
                vert.select = True
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.delete(type='ONLY_FACE')
            bpy.ops.object.mode_set(mode='OBJECT')
            mirror = shape.modifiers.new(name="Mirror", type='MIRROR')
            mirror.use_axis = [False, False, True]
            bpy.ops.object.convert(target='MESH')
        elif bone_type == 'TARGET':
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, calc_uvs=False, enter_editmode=False, align='WORLD', location=(0, 0, 0))
            shape = bpy.context.view_layer.objects.active
            shape.location, shape.rotation_euler, shape.scale = [0.0, 0.0, 0.0], [-1.570796, 0.0, 0.0], [0.5, 0.5, 0.1]
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.transform.translate(value=(0, 0.1, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            for vert in [v for v in shape.data.vertices if v.co.z > 0.001]:
                vert.select = True
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.transform.resize(value=(0.75, 0.75, 0.75), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), 
                orient_matrix_type='GLOBAL')
            bpy.ops.mesh.inset(thickness=0.25, depth=-1.5, use_select_inset=True)
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='ONLY_FACE')
            bpy.ops.object.mode_set(mode='OBJECT')
            mirror = shape.modifiers.new(name="Mirror", type='MIRROR')
            mirror.use_axis = [False, False, True]
            bpy.ops.object.convert(target='MESH')
        elif bone_type == 'TWIST':
            bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(0, 0, 0), rotation=(0, 0, 0), major_segments=8, minor_segments=3, major_radius=1, 
                minor_radius=0.15, abso_major_rad=1.25, abso_minor_rad=0.75, generate_uvs=False)
            shape = bpy.context.view_layer.objects.active
            shape.location, shape.rotation_euler, shape.scale = [0.0, 0.5, 0.0], [-1.570796, 0.0, 0.0], [0.25, 0.25, 0.25]
        elif bone_type == 'PIVOT' or bone_type == 'POLE':
            bpy.ops.mesh.primitive_cube_add(calc_uvs=False, enter_editmode=False, align='WORLD', location=(0, 0, 0))
            shape = bpy.context.view_layer.objects.active
            shape.modifiers.new(name="Subdivision", type='SUBSURF')
            bpy.ops.object.convert(target='MESH')
            # pole shape is as pivots but on the tail instead of head...
            if bone_type == 'POLE':
                shape.location = [0.0, 1.0, 0.0]
            shape.scale = [0.25, 0.25, 0.25]
        elif bone_type == 'FLOOR':
            bpy.ops.mesh.primitive_plane_add(calc_uvs=False, enter_editmode=False, align='WORLD', location=(0, 0, 0))
            shape = bpy.context.view_layer.objects.active
            shape.rotation_euler, shape.scale = [1.570796, 0.0, 0.0], [0.5, 0.5, 0.5]
        elif bone_type == 'ROLL':
            bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(0, 0, 0), rotation=(0, 0, 0), major_segments=8, minor_segments=3, major_radius=1, minor_radius=0.15, abso_major_rad=1.25, abso_minor_rad=0.75, generate_uvs=False)
            shape = bpy.context.view_layer.objects.active
            shape.location, shape.rotation_euler, shape.scale = [0.0, 0.0, 0.0], [-1.570796, 0.0, 1.570796], [0.5, 0.5, 0.5]
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            for vert in [v for v in shape.data.vertices if v.co.x <= 0.001]:
                vert.select = True
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.delete(type='VERT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.edge_face_add()
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.duplicate()
            bpy.context.view_layer.objects.active.rotation_euler = [0.0, 0.0, 1.570796]
            bpy.context.view_layer.objects.active = shape
            shape.select_set(True)
            bpy.ops.object.join()
        # apply the transforms and name the shape and its data and remove it from the active collection...
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        shape.name, shape.data.name = "Bone_Shape_" + bone_type, "Bone_Shape_" + bone_type
        #bpy.context.collection.objects.unlink(shape)
        bpy.ops.object.select_all(action='DESELECT')
        # go back to the armature in pose mode...
        bpy.context.view_layer.objects.active = armature
        armature.select_set(True)
        bpy.ops.object.mode_set(mode='POSE')
    # return whatever shape we created/found...
    return shape

def Set_Bone_Type(armature, name, enum, shape):
    last_mode, ARL = armature.mode, armature.ARL
    # might need to switch to pose mode...
    if last_mode != 'POSE':      
        bpy.ops.object.mode_set(mode='POSE')
    pb = armature.pose.bones[name]
    pb.bone.ARL.Type = enum
    if shape == 'NONE':
        pb.custom_shape = None
    else:
        pb.custom_shape = Get_Default_Bone_Shape(armature, shape)
    pb.bone.show_wire = armature.data.ARL.Wire_shapes
    # might need to go back to last mode...
    if last_mode != armature.mode:
        bpy.ops.object.mode_set(mode=last_mode)

# unused, wasn't needed but i want to save this function for future projects...
def Set_Use_FK_Hide_Drivers(armature, index, tb_name, lb_name, add):
    tb = armature.data.bones[tb_name]
    lb = armature.data.bones[lb_name]
    if add:
        # add a driver to the target control so it's hidden when switched to FK
        cb_driver = tb.driver_add("hide")
        cb_driver.driver.type = 'SCRIPTED'
        cb_var = cb_driver.driver.variables.new()
        cb_var.name, cb_var.type = "Use_FK", 'SINGLE_PROP'
        cb_var.targets[0].id = armature
        cb_var.targets[0].data_path = 'ARL.Chains[' + str(index) + '].Use_fk'
        cb_driver.driver.expression = "Use_FK"
        for mod in cb_driver.modifiers:
            cb_driver.modifiers.remove(mod)
        # add a driver to the local target control so it's not hidden when switched to FK
        lb_driver = lb.driver_add("hide")
        lb_driver.driver.type = 'SCRIPTED'
        lb_var = lb_driver.driver.variables.new()
        lb_var.name, lb_var.type = "Use_FK", 'SINGLE_PROP'
        lb_var.targets[0].id = armature
        lb_var.targets[0].data_path = 'ARL.Chains[' + str(index) + '].Use_fk'
        lb_driver.driver.expression = "not Use_FK"
        for mod in lb_driver.modifiers:
            lb_driver.modifiers.remove(mod)
    else:
        tb.driver_remove("hide")
        lb.driver_remove("hide")

def Set_IK_Settings_Drivers(armature, tp_bone, sp_bone, add):
    # all the IK settings we need to drive...
    settings = ["ik_stretch", "lock_ik_x", "lock_ik_y", "lock_ik_z", 
        "ik_stiffness_x", "ik_stiffness_y", "ik_stiffness_z",
        "use_ik_limit_x", "ik_min_x", "ik_max_x",
        "use_ik_limit_y", "ik_min_y", "ik_max_y",
        "use_ik_limit_z", "ik_min_z", "ik_max_z"]
    if add:
        # iterate through adding a driver to each setting...
        for setting in settings:
            # add driver to target pose bone setting...
            driver = tp_bone.driver_add(setting)
            # add variable to driver...
            var = driver.driver.variables.new()
            var.name, var.type = setting, 'SINGLE_PROP'
            var.targets[0].id = armature
            # set variable to point to the source bones name...
            var.targets[0].data_path = 'pose.bones["' + sp_bone.name + '"].' + setting
            # set the expression...
            driver.driver.expression = setting
            # remove any automatic curve modifier...
            for mod in driver.modifiers:
                driver.modifiers.remove(mod)
    else:
        for setting in settings:
            tp_bone.driver_remove(setting)

def Add_Pivot_Bone(armature, sb_name, pb_type, is_parent, is_forced):
    ARL, prefs = armature.ARL, bpy.context.preferences.addons["BLEND-ArmatureRiggingLibrary"].preferences
    # get the name...
    pb_name = prefs.Affixes.Pivot + sb_name
    # create the data...
    pb = ARL.Pivots.add()
    pb.name, pb.Source, pb.Is_parent, pb.Type = pb_name, sb_name, is_parent, pb_type
    if armature.data.bones[sb_name].parent != None:
        pb.Parent = armature.data.bones[sb_name].parent.name
    # when the pivot is added as part of a chain it is forced and gets removed with the IK chain...
    pb.Is_forced = is_forced
    last_mode = armature.mode
    # might need to switch to edit mode...
    if last_mode != 'EDIT':      
        bpy.ops.object.mode_set(mode='EDIT')
    # get the target edit bone...
    se_bone = armature.data.edit_bones[sb_name]
    # create the pivot bone...
    pe_bone = armature.data.edit_bones.new(pb_name)
    pe_bone.head, pe_bone.tail, pe_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    pe_bone.use_deform = False
    # if the pivot should share the targets parent...
    if pb_type == 'SHARE':
        pe_bone.parent = se_bone.parent
    # or skip it...
    elif pb_type == 'SKIP':
        if se_bone.parent != None:
            pe_bone.parent = se_bone.parent.parent
    # if the pivot bone is the parent of the target bone...
    if is_parent:
        se_bone.use_connect = False
        if se_bone.parent != None:
            pb.Parent = se_bone.parent.name  
        se_bone.parent = pe_bone 
    # might need to go back to last mode...
    if last_mode != armature.mode:
        bpy.ops.object.mode_set(mode=last_mode)
    return pb_name

def Remove_Pivot_Bone(armature, pivot):
    last_mode = armature.mode
    # might need to switch to edit mode...
    if last_mode != 'EDIT':      
        bpy.ops.object.mode_set(mode='EDIT')
    se_bone = armature.data.edit_bones[pivot.Source]
    pe_bone = armature.data.edit_bones[pivot.name]
    if pivot.Parent in armature.data.edit_bones:
        se_bone.parent = armature.data.edit_bones[pivot.Parent]
    armature.data.edit_bones.remove(pe_bone)
    # might need to go back to last mode...
    if last_mode != armature.mode:
        bpy.ops.object.mode_set(mode=last_mode)

def Add_Head_Hold_Twist(armature, twist, head_tail, limits_x, limits_z):
    bpy.ops.object.mode_set(mode='POSE')
    sp_bone = armature.pose.bones[twist.name]
    sp_bone.custom_shape = Get_Default_Bone_Shape(armature, 'TWIST')
    sp_bone.bone.ARL.Type = 'TWIST'
    # give it a damped track...
    damp_track = sp_bone.constraints.new('DAMPED_TRACK')
    damp_track.name, damp_track.show_expanded = "TWIST - Damped Track", False
    damp_track.target, damp_track.subtarget, damp_track.head_tail = armature, twist.Target, head_tail
    # and whatever limits might be required...
    limit_rot = sp_bone.constraints.new('LIMIT_ROTATION')
    limit_rot.name, limit_rot.show_expanded, limit_rot.owner_space = "TWIST - Limit Rotation", False, 'LOCAL'
    limit_rot.use_limit_x, limit_rot.min_x, limit_rot.max_x = limits_x[0], limits_x[1], limits_x[2]
    limit_rot.use_limit_z, limit_rot.min_z, limit_rot.max_z = limits_z[0], limits_z[1], limits_z[2]
    # give it a pivot bone if it should have one...
    if twist.Has_pivot:
        pb_name = Add_Pivot_Bone(armature, twist.name, 'SKIP', True, True)
        Set_Bone_Type(armature, pb_name, 'PIVOT', 'ROLL')
    # if it doesn't have a pivot...
    else:
        # go into edit mode to set it's parent...
        bpy.ops.object.mode_set(mode='EDIT')
        se_bone = armature.data.edit_bones[twist.name]
        # saving original parent name first...
        twist.Parent = se_bone.parent.name
        # set parent to parents parent to stop flipping...
        se_bone.parent = se_bone.parent.parent
        bpy.ops.object.mode_set(mode='POSE')

def Add_Tail_Follow_Twist(armature, twist, influence, limits_y):
    bpy.ops.object.mode_set(mode='POSE')
    sp_bone = armature.pose.bones[twist.name]
    sp_bone.custom_shape = Get_Default_Bone_Shape(armature, 'TWIST')
    sp_bone.lock_ik_x, sp_bone.lock_ik_z = True, True
    sp_bone.bone.ARL.Type = 'TWIST'
    # give it rotational IK limited to the Y axis...
    ik = sp_bone.constraints.new('IK')
    ik.name, ik.show_expanded = "TWIST - IK", False
    ik.target, ik.subtarget, ik.use_stretch = armature, twist.Target, False
    ik.chain_count, ik.use_location, ik.use_rotation, ik.influence = 1, False, True, influence 
    sp_bone.use_ik_limit_y, sp_bone.ik_min_y, sp_bone.ik_max_y = limits_y[0], limits_y[1], limits_y[2]
    # give it a pivot bone if it should have one...
    if twist.Has_pivot:
        pb_name = Add_Pivot_Bone(armature, twist.name, 'SHARE', True, True)
        Set_Bone_Type(armature, pb_name, 'PIVOT', 'ROLL')

def Remove_Twist_Rigging(armature, twist):
    if twist.Has_pivot:
        for pivot in [p for p in armature.ARL.Pivots if p.Source == twist.name]:
            Remove_Pivot_Bone(armature, pivot)
            armature.ARL.Pivots.remove(armature.ARL.Pivots.find(pivot.name))
    tp_bone = armature.pose.bones[twist.name]
    tp_bone.custom_shape = None
    for con in [c for c in tp_bone.constraints if c.name in ["TWIST - Limit Rotation", 'TWIST - Damped Track', "TWIST - IK"]]:
        tp_bone.constraints.remove(con)

def Add_Floor_Bone(armature, sb_name, pb_name):
    ARL, prefs = armature.ARL, bpy.context.preferences.addons["BLEND-ArmatureRiggingLibrary"].preferences
    # add the data...
    fb = ARL.Floors.add()
    fb.name, fb.Source = prefs.Affixes.Target_floor + sb_name, sb_name
    # might need to switch to edit mode...
    last_mode = armature.mode
    if last_mode != 'EDIT':      
        bpy.ops.object.mode_set(mode='EDIT')
    # to create the floor bone, on the floor...
    te_bone = armature.data.edit_bones[fb.Source]
    pe_bone = armature.data.edit_bones[pb_name] if pb_name in armature.data.edit_bones else None
    fe_bone = armature.data.edit_bones.new(fb.name)
    fe_bone.head, fe_bone.tail = [te_bone.head.x, te_bone.head.y, 0.0], [te_bone.head.x, te_bone.head.y, 0.0 - te_bone.length]
    fe_bone.roll, fe_bone.use_deform, fe_bone.parent = 0.0, False, pe_bone
    # go into pose mode and add the floor constraint to the target...
    bpy.ops.object.mode_set(mode='POSE')
    tp_bone = armature.pose.bones[fb.Source]
    con = tp_bone.constraints.new('FLOOR')
    con.name, con.show_expanded = "FLOOR - Floor", False
    con.target, con.subtarget = armature, fb.name
    con.use_rotation, con.offset, con.floor_location = True, 0.0, 'FLOOR_NEGATIVE_Y'
    Set_Bone_Type(armature, fb.name, 'TARGET', 'FLOOR')
    # might need to go back to last mode...
    if last_mode != armature.mode:
        bpy.ops.object.mode_set(mode=last_mode)
    return fb.name

def Remove_Floor_Bone(armature, floor):
    last_mode = armature.mode
    # might need to switch to edit mode...
    if last_mode != 'EDIT':      
        bpy.ops.object.mode_set(mode='EDIT')
    fe_bone = armature.data.edit_bones[floor.name]
    armature.data.edit_bones.remove(fe_bone)
    sp_bone = armature.pose.bones[floor.Source]
    sp_bone.constraints.remove(sp_bone.constraints["FLOOR - Floor"])
    # might need to go back to last mode...
    if last_mode != armature.mode:
        bpy.ops.object.mode_set(mode=last_mode)

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- TARGET FUNCTIONS -------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def Add_Opposable_Chain_Target(armature, target):
    sb_name, tb_name, lb_name = target.Source, target.name, target.Local
    # add a pivot bone to offset the target rotation...
    pb_name = Add_Pivot_Bone(armature, sb_name, 'SHARE', True, True)
    type_shapes = {tb_name : ['TARGET', 'TARGET'], lb_name : ['GIZMO', 'NONE'], pb_name : ['PIVOT', 'PIVOT'], sb_name : ['NONE', 'ROLL']}
    # get the source edit bone...
    bpy.ops.object.mode_set(mode='EDIT')
    se_bone = armature.data.edit_bones[sb_name]
    re_bone = armature.data.edit_bones[target.Root] if target.Root in armature.data.edit_bones else None
    # add the target bone without a parent...
    te_bone = armature.data.edit_bones.new(tb_name)
    te_bone.head, te_bone.tail, te_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    te_bone.parent, te_bone.use_deform = re_bone, False
    # add the local target bone with the pivot bone as parent...
    le_bone = armature.data.edit_bones.new(lb_name)
    le_bone.head, le_bone.tail, le_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    le_bone.parent, le_bone.use_deform = armature.data.edit_bones[pb_name], False
    # jump to pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    # to give the pivot bone a world space copy rotation constraint to the target...
    pp_bone = armature.pose.bones[pb_name]
    copy_rot = pp_bone.constraints.new('COPY_ROTATION')
    copy_rot.name, copy_rot.show_expanded = "TARGET - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = armature, tb_name
    # set all the bone types and shapes...
    for name, ts in type_shapes.items():
        Set_Bone_Type(armature, name, ts[0], ts[1])

def Add_Forward_Chain_Target(armature, target, end):
    # hop into edit mode and get the start and end bones
    bpy.ops.object.mode_set(mode='EDIT')
    se_bone = armature.data.edit_bones[target.Source]
    ee_bone = armature.data.edit_bones[end.name]
    # create the control as a copy of the start bone...
    ce_bone = armature.data.edit_bones.new(target.name)
    ce_bone.head, ce_bone.tail, ce_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    ce_bone.parent, ce_bone.use_deform = se_bone.parent, False
    # then set to be as long as the chain...
    bpy.ops.armature.select_all(action='DESELECT')
    ce_bone.select_tail = True
    bpy.ops.transform.translate(value=(0, Get_Distance(ce_bone.tail, ee_bone.tail), 0), orient_type='NORMAL', constraint_axis=(False, True, False),
        orient_matrix=ce_bone.matrix.to_3x3(), orient_matrix_type='NORMAL')
    # then add the custom shape and bone type...
    Set_Bone_Type(armature, target.name, 'TARGET', 'PIVOT')

def Add_Scalar_Chain_Target(armature, target):
    type_shapes = {target.name : ['TARGET', 'PIVOT'], target.Target : ['TARGET', 'TARGET'], target.Local : ['GIZMO', 'NONE']}
    # hop into edit mode and get the start and end bones
    bpy.ops.object.mode_set(mode='EDIT')
    # get the source and pivot bone...
    se_bone = armature.data.edit_bones[target.Source]
    pe_bone = armature.data.edit_bones[target.Pivot]
    # the control is a copy of the last bone in the chain...
    ce_bone = armature.data.edit_bones.new(target.name)
    ce_bone.head, ce_bone.tail, ce_bone.roll = pe_bone.head, pe_bone.tail, pe_bone.roll
    ce_bone.parent, ce_bone.use_deform = pe_bone.parent, False
    # set to be as long as the chain...
    bpy.ops.armature.select_all(action='DESELECT')
    ce_bone.select_tail = True
    bpy.ops.transform.translate(value=(0, Get_Distance(ce_bone.tail, se_bone.tail), 0), orient_type='NORMAL', constraint_axis=(False, True, False), 
        orient_matrix=ce_bone.matrix.to_3x3(), orient_matrix_type='NORMAL')
    # add the target bone parented to the control with its head at the tail of the source bone...
    te_bone = armature.data.edit_bones.new(target.Target)
    te_bone.head, te_bone.tail, te_bone.roll = se_bone.tail, se_bone.head, se_bone.roll
    te_bone.parent, te_bone.use_deform, te_bone.inherit_scale = ce_bone, False, 'NONE'
    # and orient it to the source...
    te_bone.align_orientation(se_bone)
    # add the local target bone with the source bone as parent...
    le_bone = armature.data.edit_bones.new(target.Local)
    le_bone.head, le_bone.tail, le_bone.roll = te_bone.head, te_bone.tail, te_bone.roll
    le_bone.parent, le_bone.use_deform = se_bone, False
    # then we need to set the FK hide drivers for the target and its local bone...
    bpy.ops.object.mode_set(mode='POSE')
    # Set_Use_FK_Hide_Drivers(armature, len(armature.ARL.Chains) - 1, target.Target, target.Local, True)
    for name, ts in type_shapes.items():
        Set_Bone_Type(armature, name, ts[0], ts[1])

def Add_Plantigrade_Target(armature, target, side):
    # first we need to set up all the names we'll need..
    ARL, prefs = armature.ARL, bpy.context.preferences.addons["BLEND-ArmatureRiggingLibrary"].preferences
    fb_name, bb_name = target.Source, target.Pivot
    # target gizmo and target local and parent and roll names...
    tg_name, tl_name, tp_name, rc_name = target.Target, target.Local, target.name, target.Control
    # foot pivot and foot roll gizmo names...
    fp_name, fg_name = Add_Pivot_Bone(armature, fb_name, 'SHARE', False, True), prefs.Affixes.Gizmo + prefs.Affixes.Roll + fb_name
    # ball pivot and ball roll gizmo names...
    bp_name, bg_name = Add_Pivot_Bone(armature, bb_name, 'SHARE', False, True), prefs.Affixes.Gizmo + prefs.Affixes.Roll + bb_name
    type_shapes = {tg_name : ['GIZMO', 'NONE'], tl_name : ['GIZMO', 'NONE'], tp_name : ['TARGET', 'TARGET'], rc_name : ['NONE', 'ROLL'], 
        fb_name : ['NONE', 'ROLL'], fp_name : ['PIVOT', 'PIVOT'], fg_name : ['GIZMO', 'NONE'], 
        bb_name : ['NONE', 'ROLL'], bp_name : ['PIVOT', 'PIVOT'], bg_name : ['GIZMO', 'NONE']}
    bpy.ops.object.mode_set(mode='EDIT')
    # get the foot and ball bones and make sure they are not connected...
    fe_bone = armature.data.edit_bones[fb_name]
    be_bone = armature.data.edit_bones[bb_name]
    fe_bone.use_connect, be_bone.use_connect = False, False
    # create a foot pivot that points straight to the floor from the ankle...
    fpe_bone = armature.data.edit_bones[fp_name]
    fpe_bone.head = fe_bone.head
    fpe_bone.tail = [fe_bone.head.x, fe_bone.head.y, 0.0]
    fpe_bone.roll = -180.0 if side == 'RIGHT' else 0.0
    fpe_bone.parent, fpe_bone.use_deform = fe_bone.parent, False
    # create a ball pivot that points straight to the floor from the ball...
    bpe_bone = armature.data.edit_bones[bp_name]
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
    lock_track.track_axis = 'TRACK_NEGATIVE_X' if side == 'RIGHT' else 'TRACK_X'
    lock_track.lock_axis = 'LOCK_Y'
    # and give the ball pivot a locked track to the foot...
    bpp_bone = armature.pose.bones[bp_name]
    lock_track = bpp_bone.constraints.new('LOCKED_TRACK')
    lock_track.target, lock_track.subtarget = armature, fb_name
    lock_track.track_axis = 'TRACK_X' if side == 'RIGHT' else 'TRACK_NEGATIVE_X'
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
    re_bone = armature.data.edit_bones[target.Root] if target.Root in armature.data.edit_bones else None
    # parent the ball and foot to their pivots...
    be_bone.parent, fe_bone.parent = bpe_bone, fpe_bone
    # parent bone is a straight bone at the tail of the pivot with 0.0 roll...
    tpe_bone = armature.data.edit_bones.new(tp_name)
    tpe_bone.head = [fpe_bone.head.x, fpe_bone.head.y, 0.0]
    tpe_bone.tail = [fpe_bone.head.x, fpe_bone.head.y, 0.0 - fpe_bone.length]
    tpe_bone.roll, tpe_bone.use_deform, tpe_bone.parent = 0.0, False, re_bone
    # and the target local bone is a duplicate of the target parent parented to the foot pivot...
    tle_bone = armature.data.edit_bones.new(tl_name)
    tle_bone.head, tle_bone.tail, tle_bone.roll = tpe_bone.head, tpe_bone.tail, tpe_bone.roll
    tle_bone.parent, tle_bone.use_deform = fpe_bone, False
    # roll control bone is duplicate of foot pivot rotated back by 90 degrees and parented to the target parent...
    rce_bone = armature.data.edit_bones.new(rc_name)
    rce_bone.head, rce_bone.tail, rce_bone.roll = fpe_bone.head, fpe_bone.tail, fpe_bone.roll
    rce_bone.parent, rce_bone.use_deform, rce_bone.length = tpe_bone, False, fe_bone.length
    bpy.ops.armature.select_all(action='DESELECT')
    rce_bone.select_tail = True
    bpy.ops.transform.rotate(value=-1.5708 if side != 'RIGHT' else 1.5708, orient_axis='Z', orient_type='NORMAL',
        orient_matrix=rce_bone.matrix.to_3x3(), orient_matrix_type='NORMAL')
    # ball roll gizmo is duplicate of ball bone rotated back by 90 degrees and parented to the target parent...
    bge_bone = armature.data.edit_bones.new(bg_name)
    bge_bone.head, bge_bone.tail, bge_bone.roll = bpe_bone.head, bpe_bone.tail, bpe_bone.roll
    bge_bone.parent, bge_bone.use_deform = tpe_bone, False
    bpy.ops.armature.select_all(action='DESELECT')
    bge_bone.select_tail = True
    bpy.ops.transform.rotate(value=-1.5708 if side != 'RIGHT' else 1.5708, orient_axis='Z', orient_type='NORMAL',
        orient_matrix=bge_bone.matrix.to_3x3(), orient_matrix_type='NORMAL')
    # foot roll gizmo is duplicate of foot pivot, dropped to its tail, rotated forward 90 degrees and parented to the ball roll gizmo...
    fge_bone = armature.data.edit_bones.new(fg_name)
    fge_bone.head = [fpe_bone.head.x, fpe_bone.head.y, fpe_bone.tail.z]
    fge_bone.tail = [fpe_bone.head.x, fpe_bone.head.y, 0.0 - fpe_bone.length]
    fge_bone.parent, fge_bone.roll, fge_bone.use_deform = bge_bone, fpe_bone.roll, False
    bpy.ops.armature.select_all(action='DESELECT')
    fge_bone.select_tail = True
    bpy.ops.transform.rotate(value=1.5708 if side != 'RIGHT' else -1.5708, orient_axis='Z', orient_type='NORMAL', 
        orient_matrix=fge_bone.matrix.to_3x3(), orient_matrix_type='NORMAL')
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
    fgp_bone.bone.hide = True
    copy_rot = fgp_bone.constraints.new('COPY_ROTATION')
    copy_rot.name, copy_rot.show_expanded = "ROLL - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = armature, rc_name, 
    copy_rot.use_x, copy_rot.use_y = False, False
    copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
    # with limited rotation...
    limit_rot = fgp_bone.constraints.new('LIMIT_ROTATION')
    limit_rot.name, limit_rot.show_expanded = "ROLL - Limit Rotation", False
    if side == 'RIGHT':
        limit_rot.use_limit_z, limit_rot.max_z = True, 0.785398
    else:
        limit_rot.use_limit_z, limit_rot.min_z = True, -0.785398
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
    driver.driver.expression = "Z" + "_Roll * 0.05 * -1 if " + "Z" + "_Roll " + ("<" if side != 'RIGHT' else ">") + " 0 else 0"
    for mod in driver.modifiers:
        driver.modifiers.remove(mod)
    # ball roll gizmo copies roll control rotation...
    bgp_bone = armature.pose.bones[bg_name]
    bgp_bone.bone.hide = True
    copy_rot = bgp_bone.constraints.new('COPY_ROTATION')
    copy_rot.name, copy_rot.show_expanded = "ROLL - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = armature, rc_name
    copy_rot.use_x, copy_rot.use_y = True, True
    copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
    # with limited rotation...
    limit_rot = bgp_bone.constraints.new('LIMIT_ROTATION')
    limit_rot.name, limit_rot.show_expanded = "ROLL - Limit Rotation", False
    if side == 'RIGHT':
        limit_rot.use_limit_z, limit_rot.min_z = True, -0.785398
    else:
        limit_rot.use_limit_z, limit_rot.max_z = True, 0.785398
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
    copy_rot.name, copy_rot.show_expanded = "TARGET - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = armature, tg_name
    copy_rot.target_space, copy_rot.owner_space = 'WORLD', 'WORLD'
    # and the local target bones copies the transform of the target parent...
    tlp_bone = armature.pose.bones[tl_name]
    copy_trans = tlp_bone.constraints.new("COPY_TRANSFORMS")
    copy_trans.name, copy_trans.show_expanded = "TARGET - Copy Transforms", False
    copy_trans.target, copy_trans.subtarget = armature, tp_name
    # do the shapes and types...
    for name, ts in type_shapes.items():
        Set_Bone_Type(armature, name, ts[0], ts[1])

def Add_Digitigrade_Target(armature, target, chain):
    side = chain.Side
    ARL, prefs = armature.ARL, bpy.context.preferences.addons["BLEND-ArmatureRiggingLibrary"].preferences
    # get all the names we need...
    pb_name, bb_name, fb_name = target.Pivot, target.Source, chain.Bones[0].Stretch 
    bp_name, pg_name, ps_name = Add_Pivot_Bone(armature, bb_name, 'SHARE', True, True), chain.Bones[pb_name].Gizmo, chain.Bones[pb_name].Stretch
    # target gizmo and target local and parent and roll names...
    tg_name, tl_name, tp_name, rc_name, rg_name = target.Target, target.Local, target.name, target.Control, prefs.Affixes.Gizmo + prefs.Affixes.Roll + pb_name
    type_shapes = {tg_name : ['GIZMO', 'NONE'], tl_name : ['GIZMO', 'NONE'], tp_name : ['TARGET', 'TARGET'], 
        rc_name : ['NONE', 'ROLL'], rg_name : ['GIZMO', 'NONE'], bp_name : ['PIVOT', 'PIVOT']}
    # then into edit mode to build things...
    bpy.ops.object.mode_set(mode='EDIT')
    # get the foot and ball bones and make sure they are not connected...
    be_bone = armature.data.edit_bones[bb_name]
    fe_bone = armature.data.edit_bones[fb_name]
    pe_bone = armature.data.edit_bones[pb_name]
    fe_bone.use_connect, be_bone.use_connect = False, False
    # create a foot control that points straight to the floor from the ankle...
    rce_bone = armature.data.edit_bones.new(rc_name)
    rce_bone.head = fe_bone.head
    rce_bone.tail = [fe_bone.head.x, fe_bone.head.y, 0.0]
    rce_bone.roll = -180.0 if side == 'RIGHT' else 0.0
    rce_bone.parent, rce_bone.use_deform = fe_bone.parent, False
    rce_bone.use_inherit_rotation, rce_bone.inherit_scale = False, 'NONE'
    # roll gizmo is a duplicate of the roll control oriented to the thigh...
    rge_bone = armature.data.edit_bones.new(rg_name)
    rge_bone.head, rge_bone.tail, rge_bone.roll = rce_bone.head, rce_bone.tail, pe_bone.roll 
    rge_bone.align_orientation(pe_bone)
    # jump into pose mode quick...
    bpy.ops.object.mode_set(mode='POSE')
    # to give the foot pivot a locked track to the ball...
    rcp_bone = armature.pose.bones[rc_name]
    lock_track = rcp_bone.constraints.new('LOCKED_TRACK')
    lock_track.target, lock_track.subtarget = armature, rg_name
    lock_track.track_axis = 'TRACK_NEGATIVE_X' if side == 'RIGHT' else 'TRACK_X'
    lock_track.lock_axis, lock_track.head_tail = 'LOCK_Y', 1.0
    # apply and remove the tracking so we have the right rolls...
    bpy.ops.pose.select_all(action='DESELECT')
    rcp_bone.bone.select = True#, bpp_bone.bone.select = True, True
    bpy.ops.pose.armature_apply(selected=True)
    bpy.ops.pose.constraints_clear()
    bpy.ops.object.mode_set(mode='EDIT')
    # get the edit bones we need...
    rce_bone = armature.data.edit_bones[rc_name]
    rge_bone = armature.data.edit_bones[rg_name]
    pe_bone = armature.data.edit_bones[pb_name]
    be_bone = armature.data.edit_bones[bb_name]
    re_bone = armature.data.edit_bones[target.Root] if target.Root in armature.data.edit_bones else None
    # roll control gets rotated back by 90 degrees and...
    bpy.ops.armature.select_all(action='DESELECT')
    rce_bone.select_tail = True
    bpy.ops.transform.rotate(value=-1.5708 if side != 'RIGHT' else 1.5708, orient_axis='Z', orient_type='NORMAL',
        orient_matrix=rce_bone.matrix.to_3x3(), orient_matrix_type='NORMAL')
    rce_bone.length = pe_bone.length
    # has the control gizmo parented to it...
    rge_bone.parent, rge_bone.use_deform = rce_bone, False
    # target parent is a straight down bone from the ball at 0...
    tpe_bone = armature.data.edit_bones.new(tp_name)
    tpe_bone.head = [be_bone.head.x, be_bone.head.y, 0.0]
    tpe_bone.tail = [be_bone.head.x, be_bone.head.y, be_bone.head.z - be_bone.length]
    tpe_bone.roll = -180.0 if side == 'RIGHT' else 0.0
    tpe_bone.parent, tpe_bone.use_deform = re_bone, False, 
    # actual target (gizmo) is a duplicate of the ball parented to the target parent...
    tge_bone = armature.data.edit_bones.new(tg_name)
    tge_bone.head, tge_bone.tail, tge_bone.roll = be_bone.head, be_bone.tail, be_bone.roll
    tge_bone.parent, tge_bone.use_deform = tpe_bone, False
    # ball pivot is a duplicate of the ball bone...
    bpe_bone = armature.data.edit_bones[bp_name]
    bpe_bone.head, bpe_bone.tail, bpe_bone.roll = be_bone.head, be_bone.tail, be_bone.roll
    bpe_bone.parent, bpe_bone.use_deform = be_bone.parent, False
    # with the ball bone parented to it...
    be_bone.use_connect, be_bone.parent = False, bpe_bone
    # local target is a duplicate of the target parent parented to the pivot...
    tle_bone = armature.data.edit_bones.new(tl_name)
    tle_bone.head, tle_bone.tail, tle_bone.roll = tpe_bone.head, tpe_bone.tail, tpe_bone.roll
    tle_bone.parent, tle_bone.use_deform = bpe_bone, False
    # then into pose mode for some constraints...
    bpy.ops.object.mode_set(mode='POSE')
    # the ball pivot copies the world space rotation of the target gizmo...
    bpp_bone = armature.pose.bones[bp_name]
    copy_rot = bpp_bone.constraints.new('COPY_ROTATION')
    copy_rot.name, copy_rot.show_expanded = "TARGET - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = armature, tg_name
    # and the thigh gizmo copies local rotation from roll gizmo...
    pgp_bone = armature.pose.bones[pg_name]
    copy_rot = pgp_bone.constraints.new('COPY_ROTATION')
    copy_rot.name, copy_rot.show_expanded = "DIGITIGRADE - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget, copy_rot.mix_mode = armature, rg_name, 'AFTER'
    copy_rot.target_space, copy_rot.owner_space = 'LOCAL_WITH_PARENT', 'LOCAL_WITH_PARENT'
    # do the shapes and types...
    for name, ts in type_shapes.items():
        Set_Bone_Type(armature, name, ts[0], ts[1])

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- CHAIN FUNCTIONS --------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def Add_Chain_Pole(armature, pole):
    axes = [True, False] if 'X' in pole.Axis else [False, True]
    distance = (pole.Distance * -1) if 'NEGATIVE' in pole.Axis else (pole.Distance)
    sb_name, pb_name, lb_name = pole.Source, pole.name, pole.Local
    bpy.ops.object.mode_set(mode='EDIT')
    # get some transform variables for the pole target...
    vector = (distance, 0, 0) if axes[0] else (0, 0, distance)
    # get the source bone...
    se_bone = armature.data.edit_bones[sb_name]
    re_bone = armature.data.edit_bones[pole.Root] if pole.Root in armature.data.edit_bones else None
    # add the pole bone without parent if any...
    pe_bone = armature.data.edit_bones.new(pb_name)
    pe_bone.head, pe_bone.tail, pe_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    pe_bone.parent, pe_bone.use_deform = re_bone, False
    # shift the pole bone on it's local axis...
    bpy.ops.armature.select_all(action='DESELECT')
    pe_bone.select_tail = True
    pe_bone.select_head = True
    bpy.ops.transform.translate(value=vector, orient_type='NORMAL', 
        orient_matrix=pe_bone.matrix.to_3x3(), orient_matrix_type='NORMAL', constraint_axis=(axes[0], False, axes[1]))
    # add the local pole bone with the source bone as parent...
    le_bone = armature.data.edit_bones.new(lb_name)
    le_bone.head, le_bone.tail, le_bone.roll = pe_bone.head, pe_bone.tail, pe_bone.roll
    le_bone.parent, le_bone.use_deform = se_bone, False
    # then we need to set the FK hide drivers for the target and its local bone...
    bpy.ops.object.mode_set(mode='POSE')
    #Set_Use_FK_Hide_Drivers(armature, len(armature.ARL.Chains) - 1, pb_name, lb_name, True)
    # do the shapes and types...
    Set_Bone_Type(armature, pb_name, 'TARGET', 'POLE')
    Set_Bone_Type(armature, lb_name, 'GIZMO', 'NONE')

def Add_Soft_Chain_Bones(armature, bones):
    bpy.ops.object.mode_set(mode='EDIT')
    # set the parents...
    sb_parent = armature.data.edit_bones[bones[-1].name].parent
    gb_parent = armature.data.edit_bones[bones[-1].name].parent
    # do the edit mode things...
    for cb in reversed(bones):
        # get the control edit bone...
        ce_bone = armature.data.edit_bones[cb.name]
        # add a copy of it that's going to do some stretching...
        se_bone = armature.data.edit_bones.new(cb.Stretch)
        se_bone.head, se_bone.tail, se_bone.roll, = ce_bone.head, ce_bone.tail, ce_bone.roll
        se_bone.inherit_scale, se_bone.use_deform, se_bone.parent = 'NONE', False, sb_parent
        sb_parent = se_bone
        # and another copy that will do limited stretching...
        ge_bone = armature.data.edit_bones.new(cb.Gizmo)
        ge_bone.head, ge_bone.tail, ge_bone.roll, = ce_bone.head, ce_bone.tail, ce_bone.roll
        ge_bone.inherit_scale, ge_bone.use_deform, ge_bone.parent = 'NONE', False, gb_parent
        gb_parent = ge_bone
    bpy.ops.object.mode_set(mode='POSE')
    # do the pose mode things...
    for i, cb in enumerate(bones):
        # get the names and pose bones...
        cp_bone = armature.pose.bones[cb.name]
        Set_Bone_Type(armature, cb.name, 'CHAIN', 'CHAIN')
        sp_bone = armature.pose.bones[cb.Stretch]
        Set_Bone_Type(armature, cb.Stretch, 'GIZMO', 'NONE')
        gp_bone = armature.pose.bones[cb.Gizmo]
        Set_Bone_Type(armature, cb.Gizmo, 'GIZMO', 'NONE')
        # control bone copies local rotation of gizmo...
        copy_rot = cp_bone.constraints.new('COPY_ROTATION')
        copy_rot.name, copy_rot.show_expanded = "SOFT - Copy Rotation", False
        copy_rot.target, copy_rot.subtarget = armature, cb.Gizmo
        copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
        # and has a default a ik stretch value...
        cp_bone.ik_stretch = 0.1
        # both gizmo and stretch have their ik settings driven by the control...
        Set_IK_Settings_Drivers(armature, sp_bone, cp_bone, True)
        Set_IK_Settings_Drivers(armature, gp_bone, cp_bone, True)
        # the gizmo copies the Y scale of the stretch...
        copy_sca = gp_bone.constraints.new('COPY_SCALE')
        copy_sca.name, copy_sca.show_expanded = "SOFT - Copy Scale", False
        copy_sca.target, copy_sca.subtarget = armature, cb.Stretch
        copy_sca.use_offset, copy_sca.use_x, copy_sca.use_z = True, False, False
        copy_sca.target_space, copy_sca.owner_space = 'LOCAL', 'LOCAL'
        # with limitations for extra animation dynamic...
        limit_sca = gp_bone.constraints.new('LIMIT_SCALE')
        limit_sca.name, limit_sca.show_expanded = "SOFT - Limit Scale", False
        limit_sca.use_min_y, limit_sca.use_max_y = True, True
        limit_sca.min_y, limit_sca.max_y, limit_sca.owner_space = 1.0, 2.0, 'LOCAL'

def Add_Soft_Chain_IK(armature, target, bones, pole):           
    bpy.ops.object.mode_set(mode='POSE')
    owner = bones[0]
    sp_bone = armature.pose.bones[owner.Stretch]
    gp_bone = armature.pose.bones[owner.Gizmo]
    # add the IK to the stretch gizmo...
    ik = sp_bone.constraints.new("IK")
    ik.name, ik.show_expanded = "SOFT - IK", False
    ik.target, ik.subtarget, ik.chain_count = armature, target.Target, len(bones)
    if pole != None:
        ik.pole_target, ik.pole_subtarget = armature, pole.name
        ik.pole_angle, ik.use_stretch = pole.Angle, True
    # add the IK to the gizmo... (no stretch)
    ik = gp_bone.constraints.new("IK")
    ik.name, ik.show_expanded, ik.use_stretch = "SOFT - IK", False, False
    ik.target, ik.subtarget, ik.chain_count = armature, target.Target, len(bones)
    if pole != None:
        ik.pole_target, ik.pole_subtarget = armature, pole.name
        ik.pole_angle, ik.use_stretch = pole.Angle, False

def Add_Forward_Chain_Constraints(armature, bones, target, forward):
    # need to be in pose mode and know what constraints to add...
    bpy.ops.object.mode_set(mode='POSE')
    # for every chain bone name...
    for cb in bones:
        # we need to get the pose bone and constraint settings...
        cp_bone, copy = armature.pose.bones[cb.name], forward[cb.name]
        Set_Bone_Type(armature, cb.name, 'CHAIN', 'CHAIN')
        # and give it the relevant constraints...
        copy_rot = cp_bone.constraints.new('COPY_ROTATION')
        copy_rot.name, copy_rot.show_expanded = "FORWARD - Copy Rotation", False
        copy_rot.target, copy_rot.subtarget = armature, target.name
        copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = copy.Rot[0], copy.Rot[1], copy.Rot[2]
        copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
        copy_loc = cp_bone.constraints.new('COPY_LOCATION')
        copy_loc.name, copy_loc.show_expanded = "FORWARD - Copy Location", False
        copy_loc.target, copy_loc.subtarget = armature, target.name
        copy_loc.use_x, copy_loc.use_y, copy_loc.use_z = copy.Loc[0], copy.Loc[1], copy.Loc[2]
        copy_loc.target_space, copy_loc.owner_space = 'LOCAL', 'LOCAL'
        copy_loc.mute = True if not any(s == True for s in copy.Loc) else False
        copy_sca = cp_bone.constraints.new('COPY_SCALE')
        copy_sca.name, copy_sca.show_expanded = "FORWARD - Copy Scale", False
        copy_sca.target, copy_sca.subtarget = armature, target.name
        copy_sca.use_x, copy_sca.use_y, copy_sca.use_z = copy.Sca[0], copy.Sca[1], copy.Sca[2]
        copy_sca.target_space, copy_sca.owner_space = 'LOCAL', 'LOCAL'
        copy_sca.mute = True if not any(s == True for s in copy.Sca) else False

def Add_Spline_Chain_Bones(armature, bones, targets):
    # get the start and end...
    start, end = bones[0].name, bones[-1].name
    # hop into pose mode and clear transforms... (otherwise we might get twisted curves?)
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode='EDIT')
    gpe_bone = armature.data.edit_bones[end].parent
    tpe_bone = armature.data.edit_bones[end].parent
    line_start = armature.data.edit_bones[start].tail
    line_end = armature.data.edit_bones[end].head
    for cb in reversed(bones):
        # get the chain edit bone...
        ce_bone = armature.data.edit_bones[cb.name]
        # and the head/tail locations... (maybe i'll find a use for the distance?)
        h_loc, h_dis = mathutils.geometry.intersect_point_line(ce_bone.head, line_start, line_end)
        t_loc, t_dis = mathutils.geometry.intersect_point_line(ce_bone.tail, line_start, line_end)
        # add the the spline bone with the same roll as the chain bone...
        ge_bone = armature.data.edit_bones.new(cb.Stretch)
        ge_bone.head, ge_bone.tail, ge_bone.roll = h_loc, t_loc, ce_bone.roll
        ge_bone.use_deform, ge_bone.parent = False,  gpe_bone
        # set the parent for the next iteration...
        gpe_bone = ge_bone
        # if the chain has a target...
        if cb.Has_target:
            # find it... (there should only be one? this will do until i do chains by divisions)    
            for tb in [t for t in targets if t.Source == cb.Stretch]:
                # and add it in the same as the spline bone...
                te_bone = armature.data.edit_bones.new(tb.name)
                te_bone.head, te_bone.tail, te_bone.roll = h_loc, t_loc, ce_bone.roll
                te_bone.roll, te_bone.use_deform, te_bone.parent = ce_bone.roll, False, tpe_bone  
    # then into pose mode...    
    bpy.ops.object.mode_set(mode='POSE')
    # iterate over the names again...
    for cb in bones:
        # getting and hiding the spline gizmo bone...
        Set_Bone_Type(armature, cb.Stretch, 'GIZMO', 'NONE')
        # and telling the chain bone to copy its local rotation before its own...
        cp_bone = armature.pose.bones[cb.name]
        copy_rot = cp_bone.constraints.new('COPY_ROTATION')
        copy_rot.name, copy_rot.show_expanded = "SPLINE - Copy Rotation", False
        copy_rot.target, copy_rot.subtarget, copy_rot.mix_mode = armature, cb.Stretch, 'BEFORE'
        copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
        # and set the custom shape and type...
        Set_Bone_Type(armature, cb.name, 'CHAIN', 'CHAIN')
    # then do a quick iteration over targets to set their shapes as well...
    tb_shape = Get_Default_Bone_Shape(armature, 'TARGET')
    for tb in targets:
        tp_bone = armature.pose.bones[tb.name]
        tp_bone.custom_shape = tb_shape
 
def Add_Spline_Chain_Curve(armature, bones, targets, spline):
    # go into edit mode and get target edit data needed...
    bpy.ops.object.mode_set(mode='EDIT')
    te_bones = []
    for tb in targets:
        te_bone = armature.data.edit_bones[tb.name]
        te_bones.append([tb.name, te_bone.y_axis, te_bone.head, te_bone.tail])
    start, end = te_bones[0][0], te_bones[-1][0]
    te_bones.reverse()
    # in object mode...
    bpy.ops.object.mode_set(mode='OBJECT')
    sc_name = spline.name
    # let's create a new curve and object for it with some basic display settings...
    curve = bpy.data.curves.new(name=sc_name, type='CURVE')
    curve.dimensions, curve.extrude, curve.bevel_depth = '3D', 0.01, 0.025
    obj = bpy.data.objects.new(name=sc_name, object_data=curve)
    obj.display_type = 'WIRE'
    # parent to the armature and link to the same collections...
    obj.parent = armature
    for collection in armature.users_collection:
        bpy.data.collections[collection.name].objects.link(obj)
    # set it to active, hope into edit mode and give it a bezier spline...
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bezier = curve.splines.new('BEZIER')
    # then for each bone in the spline targets...
    for i, te in enumerate(te_bones):
        te_name, te_y, te_head, te_tail = te[:]
        # add a bezier point if we need to...
        if i > 0:
            bezier.bezier_points.add(count=1)
        index = len(bezier.bezier_points) - 1
        # and get it...
        tb_point = bezier.bezier_points[index]
        # and set its coordinates and handles relative to the bone...
        co_loc = te_tail if (te_name == start and spline.Use_start) or (te_name == end and not spline.Use_end) else te_head
        lh_loc, rh_loc = co_loc + (te_y * (1 * -0.1)), co_loc + (te_y * (1 * 0.1)) 
        tb_point.co = co_loc
        tb_point.handle_left = lh_loc # - handle
        tb_point.handle_right = rh_loc # + handle
    # need a seperate iteration for hooking... (otherwise only the last hook applies)
    for i, te in enumerate(te_bones):
        bpy.ops.object.mode_set(mode='OBJECT')
        hook = obj.modifiers.new(name=te[0] + " - Hook", type='HOOK')
        hook.object, hook.subtarget = armature, te[0]
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='DESELECT')
        tb_point = curve.splines[0].bezier_points[i]
        tb_point.select_control_point = True
        tb_point.select_left_handle = True
        tb_point.select_right_handle = True
        bpy.ops.object.hook_assign(modifier=te[0] + " - Hook")
    # swap back to the armature
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    # and add the spline ik constraint to the start bone or its parent... (accounting for use start and end)
    count = len(bones) if spline.Use_start and spline.Use_end else len(bones) - 2 if not (spline.Use_start or spline.Use_end) else len(bones) - 1
    cb = bones[0] if spline.Use_start else bones[1]
    cb.Is_owner = True
    gp_bone = armature.pose.bones[cb.Stretch]
    spline_ik = gp_bone.constraints.new('SPLINE_IK')
    spline_ik.name, spline_ik.show_expanded = "SPLINE - Spline IK", False
    spline_ik.target, spline_ik.chain_count = obj, count

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- OPERATOR FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def Get_Chain_Target_Data(self, affixes, chain, cb):
    tb = chain.Targets.add()
    if self.Type == 'OPPOSABLE':
        tb.Source = self.Targets[0].Source
        tb.name = Get_Chain_Target_Affix(affixes, self.Limb) + tb.Source
        tb.Local = Get_Chain_Target_Affix(affixes, self.Limb) + affixes.Local + tb.Source
        tb.Target, tb.Root = tb.name, self.Pole.Root
    elif self.Type in ['PLANTIGRADE', 'DIGITIGRADE']:
        tb.Source = self.Targets[0].Source
        tb.name = Get_Chain_Target_Affix(affixes, self.Limb) + tb.Source
        tb.Local = Get_Chain_Target_Affix(affixes, self.Limb) + affixes.Local + tb.Source
        tb.Target, tb.Root = affixes.Gizmo + tb.Source, self.Pole.Root
        tb.Control = affixes.Control + affixes.Roll + (tb.Source if self.Type == 'PLANTIGRADE' else self.Targets[0].Pivot)
        tb.Pivot = self.Targets[0].Pivot
    elif self.Type == 'SCALAR':
        tb.Source = self.Bones[0].name
        tb.name = affixes.Control + self.Limb + "_" + self.Bones[-1].name
        tb.Target = Get_Chain_Target_Affix(affixes, self.Limb) + tb.Source
        tb.Pivot, tb.Local = self.Bones[-1].name, Get_Chain_Target_Affix(affixes, self.Limb) + affixes.Local + tb.Source
    elif self.Type == 'FORWARD':
        tb.name = affixes.Control + self.Limb + "_" + cb.name
        tb.Source = cb.name
    elif self.Type == 'SPLINE':
        tb.name = Get_Chain_Target_Affix(affixes, self.Limb) + cb.name
        tb.Source = cb.Stretch
    return tb

def Get_Chain_Pole_Data(self, affixes, chain):
    pb = chain.Pole
    pb.Source = self.Pole.Source
    pb.name = Get_Chain_Target_Affix(affixes, self.Limb) + pb.Source
    pb.Local = Get_Chain_Target_Affix(affixes, self.Limb) + affixes.Local + pb.Source
    pb.Axis, pb.Distance, pb.Angle = self.Pole.Axis, self.Pole.Distance, self.Pole.Angle
    pb.Root = self.Pole.Root
    return pb

def Get_Chain_Bone_Data(self, b, affixes, chain):
    cb = chain.Bones.add()
    cb.name = b.name
    if self.Type != 'FORWARD':
        if self.Type != 'SPLINE':
            cb.Gizmo = affixes.Gizmo + b.name
        cb.Stretch = affixes.Gizmo + affixes.Stretch + b.name
        cb.Is_owner = True if b == self.Bones[0] else False
    return cb
    
def Set_Chain(self, armature):
    ARL, prefs = armature.ARL, bpy.context.preferences.addons["BLEND-ArmatureRiggingLibrary"].preferences
    last_mode = armature.mode
    # if we are adding a chain...
    if self.Action == 'ADD':
        # add the chain with it's data...
        chain = ARL.Chains.add()
        chain.Type, chain.Side, chain.Limb = self.Type, self.Side, self.Limb
        if armature.data.bones[self.Bones[-1].name].parent != None:
            chain.Parent = armature.data.bones[self.Bones[-1].name].parent.name
        # in rare cases snapping being on can cause problems?...
        bpy.context.scene.tool_settings.use_snap = False
        # and we don't want to be keying anything in pose mode...
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
        # some of the functions need pivot point to be individual origins...
        bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
        # get all the chain bone data...
        for b in self.Bones:
            cb = Get_Chain_Bone_Data(self, b, prefs.Affixes, chain)
            # get the target if it has one... (only used by spline and forward chains)
            if b.Has_target:
                cb.Has_target = True
                Get_Chain_Target_Data(self, prefs.Affixes, chain, cb)
        # only opposable and plantigrade chains have pole targets...
        pb = Get_Chain_Pole_Data(self, prefs.Affixes, chain) if self.Type in ['OPPOSABLE', 'PLANTIGRADE'] else None
        # the forward and spline chains get their targets when getting bones...
        tb = Get_Chain_Target_Data(self, prefs.Affixes, chain, None) if self.Type not in ['FORWARD', 'SPLINE'] else None
        # if it's a spline chain...
        if chain.Type == 'SPLINE':
            # get the spline data...
            chain.Spline.name = "IK_SPLINE_" + armature.name + chain.Targets[0].name
            chain.Spline.Use_start, chain.Spline.Use_end = self.Spline.Use_start, self.Spline.Use_end
        # if this is not a forward or spline chain...
        if tb != None:
            # add the soft chain bones...
            Add_Soft_Chain_Bones(armature, chain.Bones)
            # if we need a pole target, add one...
            if pb != None:
                Add_Chain_Pole(armature, chain.Pole)
            # add target with any controls required by chain type...
            if chain.Type == 'OPPOSABLE':
                Add_Opposable_Chain_Target(armature, chain.Targets[0])
            elif chain.Type == 'PLANTIGRADE':
                Add_Plantigrade_Target(armature, chain.Targets[0], chain.Side)
            elif chain.Type == 'DIGITIGRADE':
                Add_Digitigrade_Target(armature, chain.Targets[0], chain)
            elif chain.Type == 'SCALAR':
                Add_Scalar_Chain_Target(armature, chain.Targets[0])
            # then add the soft chain IK constraints...
            Add_Soft_Chain_IK(armature, chain.Targets[0], chain.Bones, pb)
        # otherwise it's a spline or forward chain and...
        else:
            # each of those types have no shared functions...
            if chain.Type == 'SPLINE':
                Add_Spline_Chain_Bones(armature, chain.Bones, chain.Targets)
                Add_Spline_Chain_Curve(armature, chain.Bones, chain.Targets, chain.Spline)
            elif chain.Type == 'FORWARD':
                Add_Forward_Chain_Target(armature, chain.Targets[0], chain.Bones[0])
                Add_Forward_Chain_Constraints(armature, chain.Bones, chain.Targets[0], self.Forward)    
        # finally trigger the hide bools update so things get hidden if they should be...
        armature.data.ARL.Hide_gizmo = armature.data.ARL.Hide_gizmo
    if self.Action == 'REMOVE':
        chain = ARL.Chains[ARL.Chain]
        if chain.Use_fk:
            chain.Use_fk = False
        rb_names = []
        for cb in chain.Bones:
            rb_names.append(cb.Gizmo)
            rb_names.append(cb.Stretch)
            cb_bone = armature.pose.bones[cb.name]
            cb_bone.custom_shape = None
            cb_bone.bone.ARL.Type = 'NONE'
            for con in cb_bone.constraints:
                if any(con.name.startswith(prefix) for prefix in ["SOFT", "FORWARD", "SPLINE", "DIGITIGRADE"]):
                    cb_bone.constraints.remove(con)
        for tb in chain.Targets:
            rb_names.append(tb.name)
            rb_names.append(tb.Local)
            rb_names.append(tb.Control)
            rb_names.append(tb.Target)
            pivots = [p.name for p in armature.ARL.Pivots if p.Source in [tb.Source, tb.Pivot]]
            for pb_name in pivots:
                pb = armature.ARL.Pivots[pb_name]
                sp_bone = armature.pose.bones[pb.Source]
                sp_bone.custom_shape = None
                sp_bone.bone.ARL.Type = 'NONE'
                print("PIVOT REMOVE", pb.name, pb.Source)
                Remove_Pivot_Bone(armature, pb)
                index = armature.ARL.Pivots.find(pb.name)
                armature.ARL.Pivots.remove(index)
            for con in sp_bone.constraints:
                if any(con.name.startswith(prefix) for prefix in ["DIGITIGRADE", "PLANTIGRADE"]):
                    sp_bone.constraints.remove(con)
            if chain.Type in ['PLANTIGRADE', 'DIGITIGRADE']:
                for child in armature.pose.bones[tb.name].children_recursive:
                    rb_names.append(child.name)
                if chain.Type == 'DIGITIGRADE':
                    for child in armature.pose.bones[tb.Control].children_recursive:
                        rb_names.append(child.name)
        rb_names.append(chain.Pole.name)
        rb_names.append(chain.Pole.Local)
        bpy.ops.object.mode_set(mode='EDIT')
        for rb_name in rb_names:
            if rb_name != "" and rb_name in armature.data.edit_bones:
                e_bone = armature.data.edit_bones[rb_name]
                armature.data.edit_bones.remove(e_bone)
        ARL.Chains.remove(ARL.Chain)
    # might need to go back to last mode...
    if last_mode != armature.mode:
        bpy.ops.object.mode_set(mode=last_mode)

def Set_Twist(self, armature):
    ARL = armature.ARL
    if self.Action == 'ADD':
        twist = ARL.Twists.add()
        twist.name, twist.Has_pivot, twist.Target, twist.Type = self.Source, self.Has_pivot, self.Target, self.Type
        if self.Type == 'HEAD_HOLD':
            Add_Head_Hold_Twist(armature, twist, self.Float, [self.Use_a, self.Min_a, self.Max_a], [self.Use_b, self.Min_b, self.Max_b])
        elif self.Type == 'TAIL_FOLLOW':
            Add_Tail_Follow_Twist(armature, twist, self.Float, [self.Use_a, self.Min_a, self.Max_a])
    else:
        Remove_Twist_Rigging(armature, ARL.Twists[ARL.Twist])
        ARL.Twists.remove(ARL.Twist)

def Set_Floor(self, armature):
    ARL = armature.ARL
    if self.Action == 'ADD':
        Add_Floor_Bone(armature, self.Source, self.Parent)
    else:
        Remove_Floor_Bone(armature, ARL.Floors[ARL.Floor])
        ARL.Floors.remove(ARL.Floor)

def Set_Pivot(self, armature):
    ARL = armature.ARL
    if self.Action == 'ADD':
        pb_name = Add_Pivot_Bone(armature, self.Source, self.Type, self.Is_parent, False)
        Set_Bone_Type(armature, pb_name, 'PIVOT', 'PIVOT')
    else:
        Remove_Pivot_Bone(armature, ARL.Pivots[ARL.Pivot])
        ARL.Pivots.remove(ARL.Pivot)

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- UPDATE FUNCTIONS -------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def Set_IK_to_FK(self, armature):
    # get the matrices of the chain bones then iterate on them
    cb_mats = {cb.name : armature.pose.bones[cb.name].matrix.copy() for cb in self.Bones}
    for cb in self.Bones:
        cp_bone = armature.pose.bones[cb.name]
        cg_bone = armature.pose.bones[cb.Gizmo]
        cs_bone = armature.pose.bones[cb.Stretch]
        cp_bone.constraints.remove(cp_bone.constraints["SOFT - Copy Rotation"])
        cp_bone.matrix = cb_mats[cb.name]
        # if this is the contraint owner...
        if cb.Is_owner:
            # give the gizmo bone a copy rot to the FK bone...
            copy_rot = cg_bone.constraints.new("COPY_ROTATION")
            copy_rot.name, copy_rot.show_expanded = "FK - Copy Rotation", False
            copy_rot.target, copy_rot.subtarget = armature, cb.name
            copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
            # and give the stretch bone a copy rot to the FK bone...
            copy_rot = cs_bone.constraints.new("COPY_ROTATION")
            copy_rot.name, copy_rot.show_expanded = "FK - Copy Rotation", False
            copy_rot.target, copy_rot.subtarget = armature, cb.name
            copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
    # iterate over targets...
    for tb in self.Targets:
        tp_bone = armature.pose.bones[tb.name]
        tlp_bone = armature.pose.bones[tb.Local]
        tpp_bone = tlp_bone.parent
        # if it's a plantigrade chain...
        if self.Type == 'PLANTIGRADE':
            # get any difference between the target gizmo and the target parent locations...
            tgp_bone = armature.pose.bones[tb.Target]
            diff = tp_bone.matrix.to_translation() - tgp_bone.matrix.to_translation()
            # and get the local bones matrix...
            tl_mat = tlp_bone.matrix.copy()
            # before removing it's copy transforms and returning its position...
            tlp_bone.constraints.remove(tlp_bone.constraints["TARGET - Copy Transforms"])
            tlp_bone.matrix = tl_mat
        tlp_mat = tpp_bone.matrix.copy()
        # kill the copy rotation on the offset pivot bone...
        tpp_bone.constraints.remove(tpp_bone.constraints["TARGET - Copy Rotation"])
        # and set its matrix to what it was...
        tpp_bone.matrix = tlp_mat
        # if it's a leg chain...
        if self.Type == 'PLANTIGRADE':
            # apply any location difference between the target gizmo and the target parent...
            tlp_bone.matrix.translation = tpp_bone.matrix.to_translation() + diff
            # lock the control so the user can't edit it and break the chain position...
            tcp_bone = armature.pose.bones[tb.Control]
            tcp_bone.lock_rotation = [True, True, True]
        # and tell the target to copy it...
        copy_trans = tp_bone.constraints.new("COPY_TRANSFORMS")
        copy_trans.name, copy_trans.show_expanded = "FK - Copy Transforms", False
        copy_trans.target, copy_trans.subtarget = armature, tb.Local
    if self.Type != 'DIGITIGRADE':
        # get the pole...
        pp_bone = armature.pose.bones[self.Pole.name]
        # and tell tell it copy its local bone...
        copy_trans = pp_bone.constraints.new("COPY_TRANSFORMS")
        copy_trans.name, copy_trans.show_expanded = "FK - Copy Transforms", False
        copy_trans.target, copy_trans.subtarget = armature, self.Pole.Local

def Set_FK_to_IK(self, armature):
    if self.Type != 'DIGITIGRADE':
        # get the pole and a copy of its matrix...
        pp_bone = armature.pose.bones[self.Pole.name]
        pp_mat = pp_bone.matrix.copy()
        pp_bone.constraints.remove(pp_bone.constraints["FK - Copy Transforms"])
        pp_bone.matrix = pp_mat
    # iterate over targets...
    for tb in self.Targets:
        tlp_bone = armature.pose.bones[tb.Local]
        tp_bone = armature.pose.bones[tb.name]
        tpp_bone = tlp_bone.parent
        # remove the FK copy constraint while keeping transform...
        tp_mat = tp_bone.matrix.copy()
        tp_bone.constraints.remove(tp_bone.constraints["FK - Copy Transforms"])
        tp_bone.matrix = tp_mat
        # give the offset pivot back its copy rotation...
        copy_rot = tpp_bone.constraints.new(type='COPY_ROTATION')
        copy_rot.name, copy_rot.show_expanded = "TARGET - Copy Rotation", False
        copy_rot.target, copy_rot.subtarget = armature, tb.Target
        # if this is a plantigrade leg chain...
        if self.Type == 'PLANTIGRADE':
            # give the local target back its copy transform...
            copy_trans = tlp_bone.constraints.new("COPY_TRANSFORMS")
            copy_trans.name, copy_trans.show_expanded = "TARGET - Copy Transforms", False
            copy_trans.target, copy_trans.subtarget = armature, tb.name
            # and unlock the control so the user can edit it again...
            tcp_bone = armature.pose.bones[tb.Control]
            tcp_bone.lock_rotation = [False, False, False]
    # iterate on the chain bones...
    for cb in self.Bones:
        cp_bone = armature.pose.bones[cb.name]
        cg_bone = armature.pose.bones[cb.Gizmo]
        cs_bone = armature.pose.bones[cb.Stretch]
        # if this is the contraint owner...
        if cb.Is_owner:
            cg_mat, cs_mat = cg_bone.matrix.copy(), cs_bone.matrix.copy()
            cg_bone.constraints.remove(cg_bone.constraints["FK - Copy Rotation"])
            cs_bone.constraints.remove(cs_bone.constraints["FK - Copy Rotation"])
            cg_bone.matrix, cs_bone.matrix = cg_mat, cs_mat
        copy_rot = cp_bone.constraints.new("COPY_ROTATION")
        copy_rot.name, copy_rot.show_expanded = "SOFT - Copy Rotation", False
        copy_rot.target, copy_rot.subtarget = armature, cb.Gizmo
        copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'

# currently unused because i cant figure out how to restrict keying set context to selected objects... 
def Get_Chain_Keying_Set(armature, chain):
    keyset_name = "Chain - " + chain.type + " - " + chain.Bones[0].name
    keyset = bpy.context.scene.keying_sets.new(idname=keyset_name, name=keyset_name)
    keyset.bl_description = "Visually keyframe all bones in the active chain"
    keyset.use_insert_key_needed = False
    keyset.use_insertkey_override_visual = True
    keyset.use_insertkey_visual = True
    # get all the bones that need to be keyed visually...
    kp_bones = [armature.pose.bones[cb.name] for cb in chain.Bones]
    for tb in chain.Targets:
        kp_bones.append(armature.pose.bones[tb.name])
        kp_bones.append(armature.pose.bones[tb.Source].parent)
    if chain.Pole.name != "":
        kp_bones.append(armature.pose.bones[chain.Pole.name])
    rot_paths = {'EULER' : 'rotation_euler', 'QUATERNION' : 'rotation_quaternion', 'AXIS_ANGLE' : 'rotation_axis_angle'}
    for kp_bone in kp_bones:
        keyset.paths.add(armature, "pose.bones[" + kp_bone.name + "].location", index=-1)
        keyset.paths.add(armature, "pose.bones[" + kp_bone.name + "]." + rot_paths[kp_bone.rotation_mode], index=-1)
        keyset.paths.add(armature, "pose.bones[" + kp_bone.name + "].scale", index=-1)

def Set_Chain_Keyframe(chain, armature):
    # make sure the chain is up to date...
    bpy.context.view_layer.update()
    # and there needs to be animation data and an active action...
    if armature.animation_data and armature.animation_data.action:
        # more readable to define rotation path from a dictionary than do a ternary...
        rot_paths = {'EULER' : 'rotation_euler', 'QUATERNION' : 'rotation_quaternion', 'AXIS_ANGLE' : 'rotation_axis_angle'}
        # get all the bones that need to be keyed visually...
        kp_bones = [armature.pose.bones[cb.name] for cb in chain.Bones]
        for tb in chain.Targets:
            kp_bones.append(armature.pose.bones[tb.name])
            kp_bones.append(armature.pose.bones[tb.Source].parent)
        if chain.Pole.name != "":
            kp_bones.append(armature.pose.bones[chain.Pole.name])
        # for each bone that needs keying...
        for kp_bone in kp_bones:
            # replace location keyframes...
            kp_bone.keyframe_delete('location', index=-1, frame=bpy.context.scene.frame_current)
            kp_bone.keyframe_insert('location', index=-1, frame=bpy.context.scene.frame_current, options={'INSERTKEY_VISUAL'})
            # replace rotation keyframes from rotation mode...
            kp_bone.keyframe_delete(rot_paths[kp_bone.rotation_mode], index=-1, frame=bpy.context.scene.frame_current)
            kp_bone.keyframe_insert(rot_paths[kp_bone.rotation_mode], index=-1, frame=bpy.context.scene.frame_current, options={'INSERTKEY_VISUAL'})
            # replace scale keyframes...
            kp_bone.keyframe_delete('scale', index=-1, frame=bpy.context.scene.frame_current)
            kp_bone.keyframe_insert('scale', index=-1, frame=bpy.context.scene.frame_current, options={'INSERTKEY_VISUAL'})
        # return the default keyframe interpolation...
        # bpy.context.user_preferences.edit.keyframe_new_interpolation_type = last_interp    
        chain.keyframe_insert('Use_fk', index=-1, frame=bpy.context.scene.frame_current)
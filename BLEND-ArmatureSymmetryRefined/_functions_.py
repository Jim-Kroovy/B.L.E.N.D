import bpy
import copy
import mathutils

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- GENERAL FUNCTIONS ------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def add_to_edit_menu(self, context):
    self.layout.operator("jk.asr_set_edit_bone_symmetry")

def add_to_pose_menu(self, context):
    self.layout.operator("jk.asr_set_pose_bone_symmetry")

def add_to_key_menu(self, context):
    self.layout.operator("jk.asr_set_action_symmetry")

def get_string_difference(source, target):
    # keeping this as a dictionary so if i need to access index logic in the future i can...
    difference = {i : s if i < len(target) and target[i] != s else "" for i, s in enumerate(source)}
    return "".join(str(c) for c in difference.values())

def get_symmetrical_name(self, from_name, to_names):
    "Wrote this to work out the list comprehension that actually gets used"
    name, to_difference = "", get_string_difference(self.to_string, self.from_string)
    valid_names = [n for n in to_names if self.to_string in n and len(n) - len(self.to_string) == len(from_name) - len(self.from_string)]
    for valid_name in valid_names:
        # get the difference between the valid string the from string...
        difference = get_string_difference(valid_name, from_name)
        # if the difference is what we are looking for...
        if difference == to_difference:
            # then we have found the name we need...
            #print("TEST", valid_name)
            name = valid_name
            break
    return name

def get_new_symmetrical_name(from_name, from_string, to_string):
    name, indices = "", [i for i in range(len(from_name)) if from_name.startswith(from_string, i)]
    # if we only detect one occurance of the from string...
    if len(indices) == 1:
        # getting the new name is a piece of cake...
        name = from_name[:indices[0]] + to_string + from_name[indices[0] + len(from_string):]
    else:
        # otherwise we can only make assumptions by...
        for index in indices:
            # checking what comes after each detected from string...
            if index + len(from_string) < len(from_name):
                # if the next character is capitalised or simply is not a letter...
                if from_name[index + len(from_string)].isupper() or not from_name[index + len(from_string)].isalpha():
                    # then replace the from string with the to string and break...
                    name = from_name[:index] + to_string + from_name[index + len(from_string):]
                    break
            else:
                # else if there is no letter after the detected string then we probably have a suffix?..
                name = from_name[:index] + to_string + from_name[index + len(from_string):]
                break
    # if we can't get a name then just return the from name for the user to deal with...
    return name if name else from_name

def get_symmetrical_names(self, bones):
    # get all the potentially valid symmetry bones that have the to string in their names...
    valid_names = [b.name for b in bones if self.to_string in b.name]
    # get only selected or all armature edit bones...ADD HEAD AND TAIL SELECTION FOR EDIT BONES!!!
    selected = [b.name for b in bones if b.select and self.from_string in b.name] if self.only_selected else [b.name for b in bones if self.from_string in b.name]
    # get the symmtrical map of names...
    symmetrical_names = { 
        # to do this we need get a list of valid names... (should only end up with one entry?)
        from_name : [to_name for to_name in valid_names
            # the to name can only be valid it's length minus the to string is the same as the from names length minus the from string...
            if len(to_name) - len(self.to_string) == len(from_name) - len(self.from_string)
            # and the difference between the to name and the from name is equal to the difference between the to string and the from string...
            and get_string_difference(to_name, from_name) == get_string_difference(self.to_string, self.from_string)]
        # for each from name in selected...
        for from_name in selected}
    # quickly reiterate on the names in order to pull out the to names from their list...
    names = {from_name : to_names[0] if len(to_names) == 1 else "" for from_name, to_names in symmetrical_names.items()}
    return names

def get_matrix(location, euler, scale):
    # create a location matrix
    loc_mat = mathutils.Matrix.Translation((location))
    # create and combine scale matrices by axis...
    sca_mat_x = mathutils.Matrix.Scale(scale.x, 4, (1, 0, 0))
    sca_mat_y = mathutils.Matrix.Scale(scale.y, 4, (0, 1, 0))
    sca_mat_z = mathutils.Matrix.Scale(scale.z, 4, (0, 0, 1))
    sca_mat = sca_mat_x @ sca_mat_y @ sca_mat_z
    # create and combine rotation matrices by axis...
    rot_mat_x = mathutils.Matrix.Rotation(euler.x, 4, 'X')
    rot_mat_y = mathutils.Matrix.Rotation(euler.y, 4, 'Y')
    rot_mat_z = mathutils.Matrix.Rotation(euler.z, 4, 'Z')
    rot_mat = rot_mat_z @ rot_mat_y @ rot_mat_x
    # combine and return transformations
    return loc_mat @ rot_mat @ sca_mat

def get_symmetrical_matrix(self, matrix):
    # get a copy of the matrix...
    symmetrical_matrix = matrix.copy()
    # and iterate over the axes of symmetry...
    axes = {'X' : self.axes[0], 'Y' : self.axes[1], 'Z' : self.axes[2]}
    for axis, use_axis in axes.items():
        # accumulating symmetry if the axis get used...
        if use_axis:
            # by applying a diagonal matrix based on the axis we are mirroring across...
            diagonal_mat = matrix.Diagonal((-1 if axis == 'X' else 1, -1 if axis == 'Y' else 1, -1 if axis == 'Z' else 1, 0))
            symmetrical_matrix = diagonal_mat @ symmetrical_matrix
            # and slapping a dirty euler that rotates 180 on the Y and Z axes... (probably not a good method?)
            euler = mathutils.Euler((0.0, 3.141592653589793, 3.141592653589793)).to_matrix().to_4x4()
            symmetrical_matrix = symmetrical_matrix @ euler
    # return the fully transformed matrix...
    return symmetrical_matrix

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- EDIT BONE FUNCTIONS ----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_edit_bone_symmetry(self, from_eb):
    # get the symmetrical head, tail and roll from operator variables...
    head = mathutils.Vector((
        from_eb.head.x * -1 if self.axes[0] and self.use_head else from_eb.head.x, 
        from_eb.head.y * -1 if self.axes[1] and self.use_head else from_eb.head.y,
        from_eb.head.z * -1 if self.axes[2] and self.use_head else from_eb.head.z))
    tail = mathutils.Vector((
        from_eb.tail.x * -1 if self.axes[0] and self.use_tail else from_eb.tail.x, 
        from_eb.tail.y * -1 if self.axes[1] and self.use_tail else from_eb.tail.y,
        from_eb.tail.z * -1 if self.axes[2] and self.use_tail else from_eb.tail.z))
    roll = from_eb.roll * -1 if self.use_roll else from_eb.roll
    # and return them...
    return head, tail, roll

def set_edit_bone_symmetry(self, armature):
    ebs = armature.data.edit_bones
    # get the symmtrical map of names...
    symmetrical_names = get_symmetrical_names(self, ebs)
    # for each bone name and symmetrical bone name...
    for from_name, to_name in symmetrical_names.items():
        # get the from bone and attempt to get the to bone...
        from_eb, to_eb = ebs.get(from_name), ebs.get(to_name)
        # if we want to create the to bone, if it does not exist, do so...
        if self.create and not to_eb:
            to_eb = ebs.new(get_new_symmetrical_name(from_name, self.from_string, self.to_string))
        # check we have a symmetrical bone...
        if to_eb:
            # get the symmetrical head, tail and roll...
            head, tail, roll = get_edit_bone_symmetry(self, from_eb)
            # then set what should be set...
            if self.use_head:
                to_eb.head = head
            if self.use_tail:
                to_eb.tail = tail
            if self.use_roll:
                to_eb.roll = roll
    # if we want to mirror parenting...
    if self.use_parent:
        # iterate over each pair of names again...
        for from_name, to_name in symmetrical_names.items():
            # getting the from bone and attempting to get the to bone again...
            from_eb, to_eb = ebs.get(from_name), ebs.get(to_name)
            # if the to bone exists and the from bone has a parent...
            if to_eb and from_eb.parent:
                # set what the symmetrical parent bone should be... (will return None if not existing)
                parent_eb = ebs.get(from_eb.parent.name.split(self.from_string)[0] + self.to_string + from_eb.parent.name.split(self.from_string)[1])
                to_eb.parent = parent_eb

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- POSE BONE FUNCTIONS ----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def set_pose_bone_symmetry(self, armature):
    pbs, bbs = armature.pose.bones, armature.data.bones
    # get the symmtrical map of names...
    symmetrical_names = get_symmetrical_names(self, bbs)
    # for each bone name and symmetrical bone name...
    for from_name, to_name in symmetrical_names.items():
        # get the from bone and attempt to get the to bone...
        from_pb, to_pb = pbs.get(from_name), pbs.get(to_name)
        # check we have a symmetrical bone...
        if to_pb:
            # if we are mirroring rotation mode, do so...
            if self.use_mode:
                to_pb.rotation_mode = from_pb.rotation_mode
            # then get copies of the to bones current location, rotations and scale...
            to_location, to_scale = to_pb.location.copy(), to_pb.scale.copy()
            to_quaternion, to_euler = to_pb.rotation_quaternion.copy(), to_pb.rotation_euler.copy(),
            to_axis_angle = to_pb.rotation_axis_angle[:]
            # and copies of the from bones current location, rotations and scale...
            from_location, from_scale = from_pb.location.copy(), from_pb.scale.copy()
            from_quaternion, from_euler = from_pb.rotation_quaternion.copy(), from_pb.rotation_euler.copy(),
            from_axis_angle = from_pb.rotation_axis_angle[:]
            # get and set the fully symmetrical matrix...
            from_matrix = get_symmetrical_matrix(self, from_pb.matrix)
            to_matrix = get_symmetrical_matrix(self, to_pb.matrix)
            to_pb.matrix = from_matrix
            # also setting the from bone if using mirror...
            if self.use_mirror:
                from_pb.matrix = to_matrix
            # set location and rotation back if they are not being used...
            if not self.use_location:
                to_pb.location = to_location
                # also setting the from bone back if using mirror...
                if self.use_mirror:
                    from_pb.location = from_location
            if not self.use_rotation:
                to_pb.rotation_quaternion = to_quaternion
                to_pb.rotation_axis_angle = to_axis_angle
                to_pb.rotation_euler = to_euler
                # also setting the from bone back if using mirror...
                if self.use_mirror:
                    from_pb.rotation_quaternion = from_quaternion
                    from_pb.rotation_axis_angle = from_axis_angle
                    from_pb.rotation_euler = from_euler
            # scale always gets inverted by matrix so either set it back or set it from the from bone...
            to_pb.scale = from_scale if self.use_scale else to_scale
            if self.use_mirror:
                # and again, do the from bone if using mirror...
                from_pb.scale = to_scale if self.use_scale else from_scale
            # if we want to mirror constraints... (if the from bone has them an lets not try to do bi-directional constraints atm lol)
            if self.use_constraints and from_pb.constraints and not self.use_mirror:
                # iterate over the from bones constraints...
                for from_con in from_pb.constraints:
                    # adding a constraint of the same type to the to bone...
                    to_con = to_pb.constraints.new(type=from_con.type)
                    # get all the constraints properties... (that aren't readonly)
                    con_props = {p.identifier : getattr(from_con, p.identifer) for p in from_con.bl_rna.properties if not p.is_readonly}
                    # then iterate over them...
                    for prop, value in con_props:
                        # checking the property type and if the constraint has...
                        if prop.type == 'STRING' and any(p in con_props for p in ['target', 'pole_subtarget']):
                            # to see if we can find symmetrical names for them...
                            target = con_props['target' if prop == 'subtarget' else 'pole_subtarget']
                            search = target.pose.bones if target.type == 'ARMATURE' else target.vertex_groups if target.type == 'MESH' else None
                            name = get_new_symmetrical_name(value, self.from_string, self.to_string)
                            # if we have a searchable pointer and found a new name...
                            if search and name != value:
                                # see if we can get a symmetrical reference...
                                symmetrical_ref = search.get(name)
                                # setting the value if we find one...
                                if symmetrical_ref:
                                    value = name
                        # then set that property from the value...
                        setattr(to_con, prop, value)

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- ACTION FUNCTIONS -------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_curve_identifier(fcurve):
    identifier = ""
    transforms = ["location", "rotation_quaternion", "rotation_euler", "rotation_axis_angle", "scale"]
    for transform in transforms:
        if fcurve.data_path.endswith(transform):
            identifier = transform
            break
    return identifier

def get_keyframe_properties(keyframe):
    # we might not want to be setting all properties so instead using of a getattr() iteration...
    keyframe_properties = {
        'co' : keyframe.co.copy(), 'interpolation' : keyframe.interpolation, 'type' : keyframe.type,
        'handle_left' : keyframe.handle_left.copy(), 'handle_right' : keyframe.handle_right.copy(),
        'handle_left_type' : keyframe.handle_left_type, 'handle_right_type' : keyframe.handle_right_type
        }
    # return a dictionary of properties i know we will need...
    return keyframe_properties

def get_curve_properties(action, bones):
    curves = {}
    # iterate over fcurves to organise keyframes...
    for fcurve in action.fcurves:
        # by name and identifier...
        name = fcurve.data_path.partition('"')[2].split('"')[0]
        identifier = get_curve_identifier(fcurve)
        # if we have a bone name and a valid identifier...
        if identifier and bones.get(name):
            # so we can iterate over bones, their transforms...
            bone = curves[name] if name in curves else {'rotation_mode' : bones.get(name).rotation_mode, 'matrix_local' : bones.get(name).bone.matrix_local}
            curves = bone[identifier] if identifier in bone else {}
            # 'auto_smoothing', 'extrapolation' ? 
            curve = {'curve' : fcurve, 'keys' : [get_keyframe_properties(k) for k in fcurve.keyframe_points if k.select_control_point]}
            # and selected keyframes, with easy access to to other properties so as to mirror them by matrix...
            curves[fcurve.array_index] = curve
            bone[identifier] = curves
            curves[name] = bone
    return curves

def get_curve_transforms(self, curves, name, frame):
    # get the evaluated location and rotation at the frame...
    location = mathutils.Vector((
        curves[name]['location'][0]['curve'].evaluate(frame),
        curves[name]['location'][1]['curve'].evaluate(frame),
        curves[name]['location'][2]['curve'].evaluate(frame)))
    # if the rotation mode is not euler, convert to it...
    if curves[name]['rotation_mode'] == 'QUATERNION':
        quaternion = mathutils.Quaternion((
            curves[name]['rotation_quaternion'][0]['curve'].evaluate(frame),
            curves[name]['rotation_quaternion'][1]['curve'].evaluate(frame),
            curves[name]['rotation_quaternion'][2]['curve'].evaluate(frame),
            curves[name]['rotation_quaternion'][4]['curve'].evaluate(frame)))
        euler = quaternion.to_euler()
    elif curves[name]['rotation_mode'] == 'AXIS_ANGLE':
        quaternion = mathutils.Quaternion((
            curves[name]['rotation_axis_angle'][1]['curve'].evaluate(frame),
            curves[name]['rotation_axis_angle'][2]['curve'].evaluate(frame),
            curves[name]['rotation_axis_angle'][3]['curve'].evaluate(frame)),
            curves[name]['rotation_axis_angle'][0]['curve'].evaluate(frame))
        euler = quaternion.to_euler()
    else:
        euler = mathutils.Euler((
            curves[name]['rotation_euler'][0]['curve'].evaluate(frame),
            curves[name]['rotation_euler'][1]['curve'].evaluate(frame),
            curves[name]['rotation_euler'][2]['curve'].evaluate(frame)),
            'XYZ')
    # and the evaluated scale...
    scale = mathutils.Vector((
        curves[name]['scale'][0]['curve'].evaluate(frame),
        curves[name]['scale'][1]['curve'].evaluate(frame),
        curves[name]['scale'][2]['curve'].evaluate(frame)))
    # return the transforms...
    return location, euler, scale

def set_symmetrical_curves(self, armature, action, curves):
    pbs, bbs = armature.pose.bones, armature.data.bones
    symmetrical_names = get_symmetrical_names(self, bbs)
    bone_path = ['pose.bones["', '"].']
    # get a deep copy of the curve dictionary so we can edit it...
    symmetrical_curves = copy.deepcopy(curves)
    # iterate over the bone dictionairies...
    for name, bone in symmetrical_curves.items():
        # and over the curves within them...
        for identifier, curves in bone.items():
            # aaaaand the individual curves...
            for index, curve in curves.items():
                to_name = symmetrical_names[name] if name in symmetrical_names else ""
                if to_name != name:
                    to_path = bone_path[0] + to_name + bone_path[1] + identifier
                    to_curve = action.fcurves.new(data_path=to_path, index=index, action_group=to_name)
                    for keyframe in curve['keys']:
                        frame, local_matrix = keyframe['co'][0], bone['matrix_local']
                        location, euler, scale = get_curve_transforms(self, curves, name, frame)
                        # get the transform matrix from the bone to armature space...
                        from_matrix = local_matrix @ get_matrix(location, euler, scale)
                        # apply the symmetry to the now local matrix
                        symmetrical_matrix = local_matrix @ get_symmetrical_matrix(self, from_matrix)
                        # then pull it back into bone space...
                        to_matrix = local_matrix.inverted() @ symmetrical_matrix
                        # and set the new values...
                        if identifier == 'location':
                            #keyframe['co'][1] = to_matrix.to_translation()[index]
                            value = to_matrix.to_translation()[index]
                        elif identifier == 'scale':
                            #keyframe['co'][1] = to_matrix.to_scale()[index]
                            value = to_matrix.to_scale()[index]
                        elif identifier.startswith('rotation'):
                            if bone['rotation_mode'] == 'QUATERNION':
                                # keyframe['co'][1] = to_matrix.to_quaternion()[index]
                                value = to_matrix.to_quaternion()[index]
                            elif bone['rotation_mode'] == 'AXIS_ANGLE':
                                #keyframe['co'][1] = to_matrix.to_quaternion().to_axis_angle[index]
                                value = to_matrix.to_quaternion().to_axis_angle[index]
                            else:
                                #keyframe['co'][1] = to_matrix.to_euler()[index]
                                value = to_matrix.to_euler()[index]
                            new_key = to_curve.keyframe_points.insert(frame, value, keyframe_type=keyframe['type'])
                            new_key.interpolation = keyframe['interpolation']
                            new_key.left_handle, new_key.right_handle = keyframe['left_handle'], keyframe['right_handle']
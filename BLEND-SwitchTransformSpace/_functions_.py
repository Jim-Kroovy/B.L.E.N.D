import bpy
import mathutils

# adds operator to menu...
def Add_To_Menu(self, context):
    self.layout.operator("jk.switch_transform_space", text="Switch Transform Space")

def Get_Space_Location(matrix):
    return matrix.to_translation()

def Get_Space_Rotation(matrix, mode):
    # get quaternion from the space matrix...
    quat = matrix.to_quaternion()
    # get euler from the space matrix with mode order...
    euler = matrix.to_euler('XYZ' if mode in ['QUATERNION', 'AXIS_ANGLE'] else mode)
    # get axis angle from quaternion...
    axis_angle = [quat.to_axis_angle()[1], quat.to_axis_angle()[0][0], quat.to_axis_angle()[0][1], quat.to_axis_angle()[0][2]]
    # set and return the correct rotation...
    rotation = quat if mode == 'QUATERNION' else axis_angle if mode == 'AXIS_ANGLE' else euler
    return rotation

def Get_Space_Scale(matrix):
    return matrix.to_scale()

def Get_Space_Matrix(item, space):
    # if we need to get matrix from a pose bone...
    if item.rna_type.name == "Pose Bone":
        # world space is object world matrix combined with pose bone matrix and object space is the pose bones matrix...
        matrix = item.id_data.matrix_world @ item.matrix if space == 'WORLD' else item.matrix if space == 'OBJECT' else None
    # or if we are getting it from an object...
    elif item.rna_type.name == "Object":
        # world space and object space are already accessible matrices...
        matrix = item.matrix_world if space == 'WORLD' else item.matrix_local if space == 'OBJECT' else None
    return matrix





def Get_Rotation_Curves(action, rot_path_from, selection, object_curves):
    rotation_curves = []
    # if we have a pose bone selection to process...
    if len(selection) > 0:
        rotation_curves = rotation_curves + [fcurve for fcurve in action.fcurves 
            if any(p_bone.name in fcurve.data_path for p_bone in selection) 
            and any(fcurve.data_path.endswith(mode) for mode in ['rotation_euler', 'rotation_quaternion', 'rotation_axis_angle'])]
    # if we want to edit the object rotation curves...
    if object_curves:
        rotation_curves = rotation_curves + [fcurve for fcurve in action.fcurves 
            if any(fcurve.data_path == mode for mode in ['rotation_euler', 'rotation_quaternion', 'rotation_axis_angle'])]
    # organise fcurves by their data paths...
    curves_by_mode = {mode : {fcurve.data_path : {fc.array_index : fc for fc in rotation_curves if fc.data_path == fcurve.data_path} 
        for fcurve in rotation_curves if fcurve.data_path.endswith(mode)} 
        for mode in ['rotation_euler', 'rotation_quaternion', 'rotation_axis_angle']}  
    
    return curves_by_mode

def Set_Rotation_Curves(action, mode_from, mode_to, remove, selection, object_curves):
    # copy the action so we can remove curves and re-add them...
    action_copy = action.copy()
    # these two bool conditions would be annoying to keep calling on...
    is_from_euler = True if mode_from in ['XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'] else False
    is_to_euler = True if mode_to in ['XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'] else False
    # get the strings we need for the to and from data paths...
    rot_path_to = "rotation_quaternion" if mode_to == 'QUATERNION' else "rotation_axis_angle" if mode_to == 'AXIS_ANGLE' else "rotation_euler"
    rot_path_from = "rotation_quaternion" if mode_from == 'QUATERNION' else "rotation_axis_angle" if mode_from == 'AXIS_ANGLE' else "rotation_euler"
    # get the original rotation fcurves...
    rot_curves = Get_Rotation_Curves(action, rot_path_from, selection, object_curves)
    # then we want to operate on the copy...
    rot_curves_copy = Get_Rotation_Curves(action_copy, rot_path_from, selection, object_curves)
    rot_curves_from = rot_curves_copy[rot_path_from]
    # iterate over data path and channel index dictionary...
    for d_path, indices in rot_curves_from.items():
        # if the data_path is the one we wish to change from...
        if d_path.endswith(rot_path_from):
            # get the base path without rotation string...
            b_path = d_path[:-19] if mode_from in ['QUATERNION', 'AXIS_ANGLE'] else d_path[:-14]
            # if we are coming from eulers to quat/axis angle...
            if (is_from_euler and not is_to_euler):
                # and there is already a w curve...
                if (b_path + rot_path_to in rot_curves[rot_path_to] and 0 in rot_curves[rot_path_to][b_path + rot_path_to]):
                    # remove it...
                    action.fcurves.remove(rot_curves[rot_path_to][b_path + rot_path_to][new_index])
                # add a w curve...
                w_curve = action.fcurves.new(data_path=b_path + rot_path_to, index=0, action_group=b_path.partition('"')[2].split('"')[0])
            # iterate over the index and channel dictionary...
            for index, fcurve in indices.items():
                if not (index == 0 and (is_to_euler and not is_from_euler)):
                    # new index is subtracted by 1 if we are switching to euler from quat/axis angle and + 1 if we are switching to quat/axis angle from euler...
                    new_index = index + (-1 if (is_to_euler and not is_from_euler) else 1 if (is_from_euler and not is_to_euler) else 0)
                    # if the new curve already exists...
                    if b_path + rot_path_to in rot_curves[rot_path_to] and new_index in rot_curves[rot_path_to][b_path + rot_path_to]:
                        # remove it...
                        action.fcurves.remove(rot_curves[rot_path_to][b_path + rot_path_to][new_index])
                    # add the new curve by adding the the base data path to the desired data path...
                    new_curve = action.fcurves.new(data_path=b_path + rot_path_to, index=new_index, action_group=fcurve.group.name)
                    new_curve.auto_smoothing = fcurve.auto_smoothing
                    new_curve.extrapolation = fcurve.extrapolation
                    # for each keyframe in the fcurve...
                    for key in fcurve.keyframe_points:
                        # get the rotation as evaluated floats from the curves of the same data path...
                        w = rot_curves_from[d_path][0].evaluate(key.co[0])
                        x = rot_curves_from[d_path][1].evaluate(key.co[0]) if not is_from_euler else rot_curves_from[d_path][0].evaluate(key.co[0])
                        y = rot_curves_from[d_path][2].evaluate(key.co[0]) if not is_from_euler else rot_curves_from[d_path][1].evaluate(key.co[0])
                        z = rot_curves_from[d_path][3].evaluate(key.co[0]) if not is_from_euler else rot_curves_from[d_path][2].evaluate(key.co[0])
                        # create a quaternion from the evaluated floats...
                        quat = (mathutils.Quaternion((w, x, y, z)) if mode_from == 'QUATERNION' else 
                            # axis angle wants to be a quaternion created a little different...
                            mathutils.Quaternion((x, y, z), w) if mode_from == 'AXIS_ANGLE' else 
                            # euler wants to be converted to quaternion...
                            mathutils.Euler((x, y, z), mode_from).to_quaternion())
                        # set that rotation to what we want it to be...
                        new_rot = (quat if mode_to == 'QUATERNION' else
                            # rotation needs to be unpacked for axis angle...
                            [quat.to_axis_angle()[1], quat.to_axis_angle()[0][0], quat.to_axis_angle()[0][1], quat.to_axis_angle()[0][2]] if mode_to == 'AXIS_ANGLE' else 
                            # rotation needs converting for euler...
                            quat.to_euler(mode_to))
                        # add a new key in the same place...
                        new_key = new_curve.keyframe_points.insert(key.co[0], new_rot[new_index], keyframe_type='KEYFRAME')
                        # set that keyframes curve coordinates and settings...
                        new_key.co[0] = key.co[0]
                        new_key.co[1] = new_rot[new_index]
                        new_key.handle_left_type = key.handle_left_type
                        new_key.handle_right_type = key.handle_right_type
                        # custom curve handles will be close approximations until i can figured out a better way to calculate them...
                        new_key.handle_left[0] = key.handle_left[0]
                        new_key.handle_left[1] = new_key.co[1] * (key.handle_left[1] / (key.co[1] + (1 if key.co[1] == 0 else 0)))
                        new_key.handle_right[0] = key.handle_right[0]
                        new_key.handle_right[1] = new_key.co[1] * (key.handle_right[1] / (key.co[1] + (1 if key.co[1] == 0 else 0)))
                        # and the rest of the keyframe settings...
                        new_key.interpolation = key.interpolation
                        new_key.period = key.period
                        new_key.easing = key.easing
                        new_key.amplitude = key.amplitude
                        new_key.back = key.back
                        if key.type in ['KEYFRAME', 'BREAKDOWN', 'MOVING_HOLD', 'EXTREME', 'JITTER']:
                            new_key.type = key.type
                        # if we came from eulers...
                        if (is_from_euler and not is_to_euler):
                            if w_curve != None:
                                # we need to key w everytime any channel is keyed... (unable to support interpolation and custom handles on a curve that doesn't exist)
                                w_key = w_curve.keyframe_points.insert(key.co[0], new_rot[0], keyframe_type='KEYFRAME')
                                w_key.co[1] = new_rot[0]
                                w_key.handle_left[1] = new_rot[0]
                                w_key.handle_right[1] = new_rot[0]
            # if we want to remove the old fcurves...
            if remove and not (is_from_euler and is_to_euler):
                for fcurve in [fc for fc in action.fcurves if fc.data_path == d_path]:
                    action.fcurves.remove(fcurve)
    # get rid of the copy we operated on...
    bpy.data.actions.remove(action_copy)
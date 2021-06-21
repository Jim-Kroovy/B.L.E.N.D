import bpy
import json
import math
import mathutils

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- GENERAL FUNCTIONS ------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_active_bone(armature):
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    return bones.active

def set_active_bone(armature, bone):
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    bones.active = bone

def get_distance(start, end):
    x, y, z = end[0] - start[0], end[1] - start[1], end[2] - start[2]
    distance = math.sqrt((x)**2 + (y)**2 + (z)**2)
    return distance

def get_pole_angle(self):
    # this method is NOT working 100% of the time, and isn't necessery as poles are currently created along axes...
    armature = self.id_data
    bbs, rigging = armature.data.bones, armature.jk_arm.rigging[armature.jk_arm.active].opposable
    # if all the bone bones we need to calculate the pole angle exist...
    pole, owner, start = bbs.get(self.bone), bbs.get(rigging.bones[1].source), bbs.get(self.source)
    if pole and owner and start:
        # get what the pole normal and projected pole axis should be...
        pole_normal = (owner.tail_local - start.head_local).cross(pole.head_local - start.head_local)
        pole_axis = pole_normal.cross(start.tail_local - start.head_local)
        # calculate the angle, making it negative if needs to be...
        angle = start.x_axis.angle(pole_axis) * (-1 if start.x_axis.cross(pole_axis).angle(start.tail_local - start.head_local) < 1 else 1)
        return angle
    else:
        # if any bone bones didn't exsist just return 0.0... (they will exist if this function is being called though?)
        return 0.0
    #angle = -3.141593 if axis == 'X_NEGATIVE' else 1.570796 if axis == 'Z' else -1.570796 if axis == 'Z_NEGATIVE' else 0.0
    
def get_bone_side(name):
    n_up = name.upper()
    side = 'LEFT' if n_up.endswith(".L") or n_up.endswith("_L") else 'RIGHT' if n_up.endswith(".R") or n_up.endswith("_R") else 'NONE'
    return side

def get_bone_limb(name):
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

def get_chain_rigging(armature, filters={'OPPOSABLE' : True, 'PLANTIGRADE' : True}):
    chains = [r.opposable if r.flavour == 'OPPOSABLE' else r.plantigrade if r.flavour == 'PLANTIGRADE' else r.digitigrade
        for r in armature.jk_arm.rigging if r.flavour in filters]# and any(c.is_rigged for c in [r.opposable, r.plantigrade, r.digitigrade])]
    return chains

def get_chain_armatures():
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE' and len(get_chain_rigging(obj)) > 0]
    return armatures

def get_rigging_pointer(self):
    pointers = {'HEAD_HOLD' : self.headhold, 'TAIL_FOLLOW' : self.tailfollow, 
            'OPPOSABLE' : self.opposable, 'PLANTIGRADE' : self.plantigrade}
    return pointers[self.flavour]

def get_bone_string(armature, bone):
    string = 'bpy.data.objects["' + armature.name + '"].data.bones["' + bone.name + '"]'
    return string

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- MODE CHANGE FUNCTIONS --------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def subscribe_mode_to(obj, callback):
    # get the data path to sub and assign it to the msgbus....
    subscribe_to = obj.path_resolve('mode', False)
    bpy.msgbus.subscribe_rna(key=subscribe_to, owner=obj, args=(obj, 'mode'), notify=callback, options={"PERSISTENT"})
    obj.jk_arm.is_mode_subbed = True

def armature_mode_callback(armature, data):
    # if the armature has any rigging... (and we are using automatic rigging updates)
    if armature and armature.jk_arm.rigging and armature.jk_arm.use_edit_detection:
        # if we are switching to edit mode... 
        if armature.mode == 'EDIT':
                # hide all bones that are not sources...
                ebs = armature.data.edit_bones
                for rigging in armature.jk_arm.rigging:
                    pointer = rigging.get_pointer()
                    sources, groups = pointer.get_sources(), pointer.get_groups()
                    for _, names in groups.items():
                        for name in names:
                            eb = ebs.get(name)
                            if eb:
                                eb.hide = False if name in sources else True
        # if we are switching out of edit mode...
        else:
            # check if any of the riggings source bones have changed...
            for rigging in armature.jk_arm.rigging:
                detected = rigging.check_sources()
                # if they have, update it...
                if detected:
                    pointer = rigging.get_pointer()
                    pointer.update_rigging(bpy.context)

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- EDIT INTERFACE FUNCTIONS -----------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def show_cosmetic_settings(box, pointer):
    row = box.row()
    row.prop(pointer, "use_default_shapes")
    row.prop(pointer, "use_default_groups")
    row.prop(pointer, "use_default_layers")

def show_twist_settings(layout, rigging, armature):
    twist, box = rigging.get_pointer(), layout.box()
    # show cosmetic settings and rigging flavour... 
    show_cosmetic_settings(box, twist)
    row = box.row()
    row.prop(rigging, "flavour")
    row = box.row()
    row.prop_search(twist.bone, "source", armature.data, "bones")
    row.prop(twist, "use_offset")
    row = box.row()
    row.prop_search(twist.constraints[0], "subtarget", armature.data, "bones")

def show_chain_settings(layout, rigging, armature):
    chain, box = rigging.get_pointer(), layout.box()
    # show cosmetic settings and rigging flavour... (and side if planti/digiti)
    show_cosmetic_settings(box, chain)
    row = box.row()
    row.prop(rigging, "flavour")
    if rigging.flavour in ['PLANTIGRADE', 'DIGITIGRADE']:
        row.prop(rigging, "side")
    # if this one of the chains with a pole...
    if rigging.flavour in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE']:
        row = box.row()
        row.prop_search(chain.target, "source", armature.data, "bones", text="Source")
        # only plantigrade and digitigrade chains have a pivot...
        if rigging.flavour in ['PLANTIGRADE', 'DIGITIGRADE']:
            row = box.row()
            row.prop_search(chain.target, "pivot", armature.data, "bones", text="Pivot")
        row = box.row()
        row.prop(chain.pole, "axis", text="")
        row.prop(chain.pole, "distance", text="Pole Distance:")
        row = box.row()
        row.prop(chain, "use_floor")
        if rigging.flavour in ['OPPOSABLE', 'PLANTIGRADE']:
            row.prop(chain, "use_stretch")
        if chain.use_floor:
            row = box.row()
            row.prop_search(chain.floor, "root", armature.data, "bones", text="Floor Root")
            row.enabled = chain.is_rigged
        row = box.row()
        row.prop_search(chain.target, "root", armature.data, "bones", text="Target Root")
        row.enabled = chain.is_rigged
        row = box.row()
        row.prop_search(chain.pole, "root", armature.data, "bones", text="Pole Root")
        row.enabled = chain.is_rigged
    # else if this is a spline chain...
    elif rigging.flavour == 'SPLINE':
        row = box.row()
        row.prop_search(chain.spline, "end", armature.data, "bones", text="From")
        row.prop(chain.spline, "length")
        row = box.row()
        row.prop(chain.spline, "axis")
        row.prop(chain.spline, "distance")
        if chain.is_rigged:
            curve = chain.spline.curve#bpy.data.objects[chain.spline.curve]
            row.prop(curve.data, "bevel_depth")
        else:
            row.prop(chain.spline, "bevel_depth")
        for i in range(len(chain.targets)):
            target, bone = chain.targets[i], chain.bones[i]
            row = box.row()
            row.label(text=target.source)
            col = row.column()
            col.prop(target, "use", text="Create Target")
            col.enabled = False if i == 0 or i == len(chain.targets) - 1 else True
            col = row.column()
            col.prop(bone, "axis", text="Shape Axis")
            col.enabled = chain.use_default_shapes
    # else if this is a tracking chain...
    elif rigging.flavour == 'TRACKING':
        row = box.row()
        row.prop_search(chain.target, "source", armature.data, "bones", text="From")
        row.prop(chain, "length")
        row = box.row()
        row.prop(chain.target, "axis")
        row.prop(chain.target, "distance")
        row = box.row()
        row.prop_search(chain.target, "root", armature.data, "bones", text="Target Root")
        row.enabled = chain.is_rigged
        for i in range(len(chain.bones)):
            bone = chain.bones[i]
            row = box.row()
            row.label(text=bone.source)
            col = row.column()
            col.prop(bone, "axis", text="Shape Axis")
            col.enabled = chain.use_default_shapes
    # else if this is a forward or scalar chain...
    elif rigging.flavour in ['SCALAR', 'FORWARD']:
        row = box.row()
        # both have the end and length properties...
        row.prop_search(chain.target, "end", armature.data, "bones", text="From")
        row.prop(chain.target, "length")
        # but only scalar chains can have floor bones...
        if rigging.flavour == 'SCALAR':
            row.prop(chain, "use_floor")
            if chain.use_floor:
                row = box.row()
                row.prop_search(chain.floor, "root", armature.data, "bones", text="Floor Root")
                row.enabled = chain.is_rigged
    

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- POSE INTERFACE FUNCTIONS -----------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

# Not currently in add to interface at some point...
def show_bone_selection(row, bones, bone):
    is_active = True if bones.active == bones.get(bone.name) else False
    row.operator("jk.active_bone_set", text="Active", icon='PMARKER_ACT' if is_active else 'PMARKER', depress=is_active).Bone = bone.name
    row.prop(bones[bone.name], "select", text="Select", icon='RESTRICT_SELECT_OFF' if bones[bone.name].select else 'RESTRICT_SELECT_ON')

def show_limit_rotation(box, limit_rot):
    # X row....
    x_row = box.row(align=True)
    col = x_row.column(align=True)
    col.prop(limit_rot, "use_limit_x", icon='CON_ROTLIMIT')
    col = x_row.column(align=True)
    col.prop(limit_rot, "min_x")
    col.enabled = limit_rot.use_limit_x
    col = x_row.column(align=True)
    col.prop(limit_rot, "max_x")
    col.enabled = limit_rot.use_limit_x
    # Y row...
    y_row = box.row(align=True)
    col = y_row.column(align=True)
    col.prop(limit_rot, "use_limit_y", icon='CON_ROTLIMIT')
    col = y_row.column(align=True)
    col.prop(limit_rot, "min_y")
    col.enabled = limit_rot.use_limit_x
    col = y_row.column(align=True)
    col.prop(limit_rot, "max_y")
    col.enabled = limit_rot.use_limit_x
    # Z row...
    z_row = box.row(align=True)
    col = z_row.column(align=True)
    col.prop(limit_rot, "use_limit_z", icon='CON_ROTLIMIT')
    col = z_row.column(align=True)
    col.prop(limit_rot, "min_z")
    col.enabled = limit_rot.use_limit_x
    col = z_row.column(align=True)
    col.prop(limit_rot, "max_z")
    col.enabled = limit_rot.use_limit_x
    # influence...
    row = box.row()
    row.prop(limit_rot, "influence")
    #row.prop(limit_rot, "owner_space")

def show_copy_rotation(box, copy_rot):
    col = box.column(align=True)
    row = col.row(align=True)
    #row.prop(copy_rot, "mute", text="", invert_checkbox=True)
    row.prop(copy_rot, "influence", text="Rotation")
    row = col.row(align=True)
    row.prop(copy_rot, "mix_mode", text="")
    row.prop(copy_rot, "euler_order", text="")
    row.enabled = True if copy_rot.influence > 0.0 else False#not copy_rot.mute
    row = col.row(align=True)
    row.prop(copy_rot, "use_x", text="X", toggle=True)
    row.prop(copy_rot, "use_y", text="Y", toggle=True)
    row.prop(copy_rot, "use_z", text="Z", toggle=True)
    row.enabled = True if copy_rot.influence > 0.0 else False#not copy_rot.mute

def show_copy_location(box, copy_loc):
    col = box.column(align=True)
    row = col.row(align=True)
    #row.prop(copy_loc, "mute", text="", invert_checkbox=True)
    row.prop(copy_loc, "influence", text="Location")
    row = col.row(align=True)
    row.prop(copy_loc, "use_offset", text="", icon='ORIENTATION_LOCAL')
    row.prop(copy_loc, "head_tail", text="Head/Tail")
    row.enabled = True if copy_loc.influence > 0.0 else False#not copy_loc.mute
    row = col.row(align=True)
    row.prop(copy_loc, "use_x", text="X", toggle=True)
    row.prop(copy_loc, "use_y", text="Y", toggle=True)
    row.prop(copy_loc, "use_z", text="Z", toggle=True)
    row.enabled = True if copy_loc.influence > 0.0 else False#not copy_loc.mute

def show_copy_scale(box, copy_sca):
    col = box.column(align=True)
    row = col.row(align=True)
    #row.prop(copy_sca, "mute", text="", invert_checkbox=True)
    row.prop(copy_sca, "influence", text="Scale")
    row = col.row(align=True)
    row.prop(copy_sca, "use_offset", text="", icon='ORIENTATION_LOCAL')
    row.prop(copy_sca, "power", text="Power")
    row.enabled = True if copy_sca.influence > 0.0 else False#not copy_sca.mute
    row = col.row(align=True)
    row.prop(copy_sca, "use_x", text="X", toggle=True)
    row.prop(copy_sca, "use_y", text="Y", toggle=True)
    row.prop(copy_sca, "use_z", text="Z", toggle=True)
    row.enabled = True if copy_sca.influence > 0.0 else False#not copy_sca.mute

def show_bone_kinematics(box, pb, show_stretch=False):
    # if we want to display the IK stretching, show it...
    if show_stretch:
        row = box.row()
        row.prop(pb, "ik_stretch", icon='CON_STRETCHTO')
    # make a row for the columns...
    row = box.row()
    # lock column...
    lock_col = row.column(align=True)
    lock_col.prop(pb, "lock_ik_x", text="X", emboss=False)
    lock_col.prop(pb, "lock_ik_y", text="Y", emboss=False)
    lock_col.prop(pb, "lock_ik_z", text="Z", emboss=False)
    # stiffness column...
    stiff_col = row.column(align=True)
    x_row = stiff_col.row(align=True)
    x_row.prop(pb, "ik_stiffness_x", text="")
    x_row.prop(pb, "use_ik_limit_x", text="", icon='CON_ROTLIMIT')
    x_row.active = not pb.lock_ik_x
    y_row = stiff_col.row(align=True)
    y_row.prop(pb, "ik_stiffness_y", text="")
    y_row.prop(pb, "use_ik_limit_y", text="", icon='CON_ROTLIMIT')
    y_row.active = not pb.lock_ik_y
    z_row = stiff_col.row(align=True)
    z_row.prop(pb, "ik_stiffness_z", text="")
    z_row.prop(pb, "use_ik_limit_z", text="", icon='CON_ROTLIMIT')
    z_row.active = not pb.lock_ik_z
    # limit column...
    limit_col = row.column(align=True)
    x_row = limit_col.row(align=True)
    x_row.prop(pb, "ik_min_x", text="")
    x_row.prop(pb, "ik_max_x", text="")
    x_row.active = pb.use_ik_limit_x and not pb.lock_ik_x
    y_row = limit_col.row(align=True)
    y_row.prop(pb, "ik_min_y", text="")
    y_row.prop(pb, "ik_max_y", text="")
    y_row.active = pb.use_ik_limit_y and not pb.lock_ik_y
    z_row = limit_col.row(align=True)
    z_row.prop(pb, "ik_min_z", text="")
    z_row.prop(pb, "ik_max_z", text="")
    z_row.active = pb.use_ik_limit_z and not pb.lock_ik_z

def show_track_kinematics(box, pb, bone):
    # make a row for the columns...
    row = box.row()
    con_col = row.column(align=True)
    con_col.ui_units_x = 20
    lean_row = con_col.row(align=True)
    lean_row.prop(bone, "lean")
    turn_row = con_col.row(align=True)
    turn_row.prop(bone, "turn")
    stretch_row = con_col.row(align=True)
    stretch_row.prop(pb, "ik_stretch", text="Stretch")
    # limit column...
    limit_col = row.column(align=True)
    x_row = limit_col.row(align=True)
    x_row.prop(pb, "ik_stiffness_x", text="X")
    x_row.prop(pb, "ik_min_x", text="")
    x_row.prop(pb, "ik_max_x", text="")
    y_row = limit_col.row(align=True)
    y_row.prop(pb, "ik_stiffness_y", text="Y")
    y_row.prop(pb, "ik_min_y", text="")
    y_row.prop(pb, "ik_max_y", text="")
    z_row = limit_col.row(align=True)
    z_row.prop(pb, "ik_stiffness_z", text="Z")
    z_row.prop(pb, "ik_min_z", text="")
    z_row.prop(pb, "ik_max_z", text="")

def show_soft_kinematics(box, pb, copy, limit):
    row = box.row()
    row.label(text="Inverse Kinematics: " + pb.name)
    # show the bones IK stretching, copy scale power and limit scale Y limit...
    row = box.row(align=True)
    # all in one row...
    row.prop(pb, "ik_stretch", text="Stretch", icon='CON_STRETCHTO')
    row.prop(copy, "power", text="Power", icon='CON_SIZELIKE')
    row.prop(limit, "max_y", text="Max Y", icon='CON_SIZELIMIT')

def show_twist_controls(layout, rigging, armature):
    pbs, twist = armature.pose.bones, rigging.get_pointer()
    pb, box = pbs.get(twist.bone.source), layout.box()
    if pb and twist.is_rigged and twist.has_properties:
        if rigging.flavour == 'HEAD_HOLD':
            damp_track, limit_rot = pb.constraints.get("TWIST - Damped Track"), pb.constraints.get("TWIST - Limit Rotation")
            show_limit_rotation(box, limit_rot)
        elif rigging.flavour == 'TAIL_FOLLOW':
            show_bone_kinematics(box, pb, show_stretch=False)
    else:
        box.label(text="Animation controls appear here once rigged...")

def show_chain_controls(layout, rigging, armature):
    pbs, chain = armature.pose.bones, rigging.get_pointer()
    if chain.is_rigged and chain.has_properties:
        # show the IK/FK switching properties... (on chains with switching)
        if rigging.flavour in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE']:
            box = layout.box()
            row = box.row()
            row.prop(chain, "use_auto_fk")
            row.prop(chain, "use_fk")
            #snap_col = row.column()
            row = box.row()
            row.prop(chain, "ik_softness")
            row.prop(chain, "fk_influence")
            row.enabled = not chain.use_fk
            row = box.row()
            snap_name = chain.target.bone if rigging.flavour == 'OPPOSABLE' else chain.target.parent
            snap_floor = row.operator("jk.arl_snap_bones", text="Floor > Target", icon='SNAP_ON')
            snap_floor.source, snap_floor.target = chain.floor.bone, snap_name
            snap_target = row.operator("jk.arl_snap_bones", text="Target > Floor", icon='SNAP_ON')
            snap_target.source, snap_target.target = snap_name, chain.floor.bone
            row.enabled = chain.use_floor and not chain.use_fk
        # spline chains have the fit curve property...
        elif rigging.flavour == 'SPLINE':
            box = layout.box()
            row = box.row()
            row.prop(chain, "fit_curve")
            row = box.row()
            snap_parent = row.operator("jk.arl_snap_bones", text="Parent > Start", icon='SNAP_ON')
            snap_parent.source, snap_parent.target = chain.spline.parent, chain.bones[0].source
            snap_start = row.operator("jk.arl_snap_bones", text="Start > Parent", icon='SNAP_ON')
            snap_start.source, snap_start.target = chain.bones[0].source, chain.spline.parent
        # scalar chains only have IK softness... (for now)
        elif rigging.flavour == 'SCALAR':
            box = layout.box()
            row = box.row()
            row.prop(chain, "ik_softness")
         # else if this is a tracking chain...
        elif rigging.flavour == 'TRACKING':
            box = layout.box()
            row = box.row()
            control_pb = pbs.get(chain.target.control)
            if control_pb:
                row.prop(chain.target, "lock_x")
                row.prop(chain.target, "lock_z")
            box = layout.box()
            for bone in chain.bones:
                source_pb = pbs.get(bone.source)
                row = box.row()
                row.label(text="Tracking: " + bone.source)
                if source_pb:
                    copy = source_pb.constraints.get('TRACK - Copy Rotation')
                    if copy:
                        row = box.row()
                        row.prop(copy, "influence")
                show_track_kinematics(box, source_pb, bone)
        # if the chain has soft IK display the bone kinematics...
        if rigging.flavour in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE', 'SCALAR']:
            box = layout.box()
            for bone in chain.bones:
                source_pb, gizmo_pb = pbs.get(bone.source), pbs.get(bone.gizmo)
                if source_pb and gizmo_pb:
                    copy, limit = gizmo_pb.constraints.get("SOFT - Copy Scale"), gizmo_pb.constraints.get("SOFT - Limit Scale")
                    if copy and limit:
                        show_soft_kinematics(box, source_pb, copy, limit)
                    show_bone_kinematics(box, source_pb, show_stretch=False)

        elif rigging.flavour == 'FORWARD':
            
            for bone in chain.bones:
                box = layout.box()
                source_pb = pbs.get(bone.source)
                row = box.row()
                row.label(text="Forward Kinematics: " + bone.source)
                con_row = box.row()
                for name in ["FORWARD - Copy Location", "FORWARD - Copy Rotation", "FORWARD - Copy Scale"]: 
                    if name in source_pb.constraints:
                        constraint = source_pb.constraints.get(name)
                        if name == "FORWARD - Copy Rotation":
                            show_copy_rotation(con_row, constraint)
                        elif name == "FORWARD - Copy Location":
                            show_copy_location(con_row, constraint)
                        elif name == "FORWARD - Copy Scale":
                            show_copy_scale(con_row, constraint)




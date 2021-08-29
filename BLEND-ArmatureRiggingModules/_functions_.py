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
    # all pointers now get broken by Blenders undo system, so just iterate on all selected armatures...
    for armature in [ob for ob in bpy.context.selected_objects if ob.type == 'ARMATURE']:
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
                # check if any of the riggings source bones have changed... (saving the last active rigging)
                last_mode = armature.mode
                last_active = armature.jk_arm.active
                for i, rigging in enumerate(armature.jk_arm.rigging):
                    armature.jk_arm.active = i
                    detected = rigging.check_sources()
                    # if they have, update it...
                    if detected:
                        pointer = rigging.get_pointer()
                        pointer.update_rigging(bpy.context)
                # then return the active rigging and mode to what it was before we updated...
                armature.jk_arm.active = last_active
                bpy.ops.object.mode_set(mode=last_mode)

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- EDIT INTERFACE FUNCTIONS -----------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def show_cosmetic_settings(box, pointer):
    row = box.row()
    row.prop(pointer, "use_default_shapes")
    row.prop(pointer, "use_default_groups")
    row.prop(pointer, "use_default_layers")

def show_twist_settings(layout, rigging, armature):
    twist = rigging.get_pointer()
    row = layout.row()
    col = row.column()
    col.alignment = 'RIGHT'
    col.label(text="Twist Source")
    col.label(text="Twist Target")
    col.separator()
    col.label(text="Use")
    
    col = row.column()
    col.prop_search(twist.bone, "source", armature.data, "bones", text="")
    col.prop_search(twist.constraints[0], "subtarget", armature.data, "bones", text="", icon='BONE_DATA' if twist.constraints[0].subtarget in armature.data.bones else 'ERROR')
    col.separator()
    col.prop(twist, "use_offset", text="Offset Parenting")

def show_chain_settings(layout, rigging, armature):
    chain = rigging.get_pointer()
    row = layout.row()
    # if this one of the chains with a pole...
    if rigging.flavour in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE']:
        col = row.column()
        col.alignment = 'RIGHT'
        col.label(text="Target Source")
        if rigging.flavour in ['PLANTIGRADE', 'DIGITIGRADE']:
            col.label(text="Target Pivot")
        col.label(text="Target Root")
        col.separator()
        col.label(text="Pole Position")
        col.label(text="Pole Root")
        col.separator()
        col.label(text="Use")
        col.label(text="")
        if chain.use_floor:
            col.label(text="Floor Root")
        
        col = row.column()
        col.prop_search(chain.target, "source", armature.data, "bones", text="", icon='BONE_DATA' if chain.target.source in armature.data.bones else 'ERROR')
        if rigging.flavour in ['PLANTIGRADE', 'DIGITIGRADE']:
            #row = layout.row(heading="Target Pivot:")
            col.prop_search(chain.target, "pivot", armature.data, "bones", text="", icon='BONE_DATA' if chain.target.pivot in armature.data.bones else 'ERROR')
        col.prop_search(chain.target, "root", armature.data, "bones", text="")
        col.separator()
        row = col.row(align=False)
        row.prop(chain.pole, "axis", text="")
        row.prop(chain.pole, "distance", text="Distance")
        col.prop_search(chain.pole, "root", armature.data, "bones", text="")
        col.separator()
        col.prop(chain, "use_stretch", text="Stretching")
        col.prop(chain, "use_floor", text="Floor Target")
        if chain.use_floor:
            col.prop_search(chain.floor, "root", armature.data, "bones", text="")

    # else if this is a spline chain...
    elif rigging.flavour == 'SPLINE':
        col = row.column()
        col.alignment = 'RIGHT'
        col.label(text="Chain End")
        col.label(text="Chain Size")
        col.separator()
        for i, target in enumerate(chain.targets):
            col.label(text=target.source)
        col.separator()
        col.label(text="Target Position")
        
        col = row.column()
        col.prop_search(chain.spline, "end", armature.data, "bones", text="")
        row = col.row(align=False)
        row.prop(chain.spline, "length", text="Bone Length")
        if chain.is_rigged:
            curve = chain.spline.curve #bpy.data.objects[chain.spline.curve]
            row.prop(curve.data, "bevel_depth", text="Curve Depth")
        else:
            row.prop(chain.spline, "bevel_depth", text="Curve Depth")
        
        col.separator()
        for i, target in enumerate(chain.targets):
            bone = chain.bones[i]
            row = col.row()
            row.alignment = 'LEFT'
            tcol = row.column()
            tcol.prop(target, "use", text="Target Point")
            tcol.enabled = False if i == 0 or i == len(chain.targets) - 1 else True
            if chain.use_default_shapes:
                row.label(text="Shape")
                scol = row.column()
                scol.prop(bone, "axis", text="")

        col.separator()
        row = col.row(align=False)
        row.prop(chain.spline, "axis", text="")
        row.prop(chain.spline, "distance", text="Distance")
    
    # else if this is a tracking chain...
    elif rigging.flavour == 'TRACKING':
        col = row.column()
        col.alignment = 'RIGHT'
        col.label(text="Target Source")
        col.label(text="Target Root")
        col.label(text="Chain Size")
        if chain.use_default_shapes:
            col.separator()
            for i, target in enumerate(chain.bones):
                col.label(text=target.source)
        col.separator()
        col.label(text="Chain Position")
        
        col = row.column()
        col.prop_search(chain.target, "source", armature.data, "bones", text="")
        col.prop_search(chain.target, "root", armature.data, "bones", text="")
        row = col.row(align=False)
        row.prop(chain, "length", text="Bone Length")
        if chain.use_default_shapes:
            col.separator()
            for i, bone in enumerate(chain.bones):
                row = col.row()
                row.alignment = 'RIGHT'
                if chain.use_default_shapes:
                    row.label(text="Shape")
                    scol = row.column()
                    scol.prop(bone, "axis", text="")
                
        col.separator()
        row = col.row(align=False)
        row.prop(chain.target, "axis", text="")
        row.prop(chain.target, "distance", text="Distance")
        
    # else if this is a forward or scalar chain...
    elif rigging.flavour in ['SCALAR', 'FORWARD']:
        col = row.column()
        col.alignment = 'RIGHT'
        col.label(text="Chain End")
        col.label(text="Chain Size")
        if rigging.flavour == 'SCALAR':
            col.separator()
            col.label(text="Use")
            if chain.use_floor:
                col.label(text="Floor Root")
        
        col = row.column()
        col.prop_search(chain.target, "end", armature.data, "bones", text="")
        row = col.row(align=False)
        row.prop(chain.target, "length", text="Bone Length")
        if rigging.flavour == 'SCALAR':
            col.separator()
            col.prop(chain, "use_floor", text="Floor Target")
            if chain.use_floor:
                col.prop_search(chain.floor, "root", armature.data, "bones", text="")
    

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- POSE INTERFACE FUNCTIONS -----------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

# Not currently used, add to interface at some point...
def show_bone_selection(row, bones, bone):
    is_active = True if bones.active == bones.get(bone.name) else False
    row.operator("jk.active_bone_set", text="Active", icon='PMARKER_ACT' if is_active else 'PMARKER', depress=is_active).Bone = bone.name
    row.prop(bones[bone.name], "select", text="Select", icon='RESTRICT_SELECT_OFF' if bones[bone.name].select else 'RESTRICT_SELECT_ON')

def show_limit_rotation(layout, limit_rot):
    # X row....
    x_row = layout.row(align=True)
    col = x_row.column(align=True)
    col.prop(limit_rot, "use_limit_x", text="X", icon='CON_ROTLIMIT')
    col.ui_units_x = 2
    col = x_row.column(align=True)
    col.prop(limit_rot, "min_x", text="Min")
    col.enabled = limit_rot.use_limit_x
    col = x_row.column(align=True)
    col.prop(limit_rot, "max_x", text="Max")
    col.enabled = limit_rot.use_limit_x
    # Y row...
    y_row = layout.row(align=True)
    col = y_row.column(align=True)
    col.prop(limit_rot, "use_limit_y", text="Y", icon='CON_ROTLIMIT')
    col.ui_units_x = 2
    col = y_row.column(align=True)
    col.prop(limit_rot, "min_y", text="Min")
    col.enabled = limit_rot.use_limit_y
    col = y_row.column(align=True)
    col.prop(limit_rot, "max_y", text="Max")
    col.enabled = limit_rot.use_limit_y
    # Z row...
    z_row = layout.row(align=True)
    col = z_row.column(align=True)
    col.prop(limit_rot, "use_limit_z", text="Z", icon='CON_ROTLIMIT')
    col.ui_units_x = 2
    col = z_row.column(align=True)
    col.prop(limit_rot, "min_z", text="Min")
    col.enabled = limit_rot.use_limit_z
    col = z_row.column(align=True)
    col.prop(limit_rot, "max_z", text="Max")
    col.enabled = limit_rot.use_limit_z
    # influence...
    row = layout.row()
    row.prop(limit_rot, "influence")
    #row.prop(limit_rot, "owner_space")

def show_copy_rotation(layout, copy_rot):
    col = layout.column(align=True)
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

def show_copy_location(layout, copy_loc):
    col = layout.column(align=True)
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

def show_copy_scale(layout, copy_sca):
    col = layout.column(align=True)
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

def show_bone_kinematics(layout, pb, show_stretch=False):
    # if we want to display the IK stretching, show it...
    if show_stretch:
        row = layout.row()
        row.prop(pb, "ik_stretch", icon='CON_STRETCHTO')
    # make a row for the columns...
    row = layout.row()
    axis_col = row.column(align=True)
    axis_col.label(text="X")
    axis_col.label(text="Y")
    axis_col.label(text="Z")
    axis_col.ui_units_x = 1
    # lock / stiffness column...
    stiff_col = row.column(align=True)
    x_row = stiff_col.row(align=True)
    x_row.prop(pb, "lock_ik_x", text="")
    x_col = x_row.column(align=True)
    x_col.prop(pb, "ik_stiffness_x", text="")
    x_col.active = not pb.lock_ik_x
    y_row = stiff_col.row(align=True)
    y_row.prop(pb, "lock_ik_y", text="")
    y_col = y_row.column(align=True)
    y_col.prop(pb, "ik_stiffness_y", text="")
    y_col.active = not pb.lock_ik_y
    z_row = stiff_col.row(align=True)
    z_row.prop(pb, "lock_ik_z", text="")
    z_col = z_row.column(align=True)
    z_col.prop(pb, "ik_stiffness_z", text="")
    z_col.active = not pb.lock_ik_z
    # limit column...
    limit_col = row.column(align=True)
    x_row = limit_col.row(align=True)
    x_row.active = not pb.lock_ik_x
    x_col = x_row.column(align=True)
    x_col.prop(pb, "use_ik_limit_x", text="", icon='CON_ROTLIMIT')
    x_col = x_row.column(align=True)
    x_row = x_col.row(align=True)
    x_row.prop(pb, "ik_min_x", text="")
    x_row.prop(pb, "ik_max_x", text="")
    x_row.active = pb.use_ik_limit_x and not pb.lock_ik_x
    y_row = limit_col.row(align=True)
    y_row.active = not pb.lock_ik_y
    y_col = y_row.column(align=True)
    y_col.prop(pb, "use_ik_limit_y", text="", icon='CON_ROTLIMIT')
    y_col = y_row.column(align=True)
    y_row = y_col.row(align=True)
    y_row.prop(pb, "ik_min_y", text="")
    y_row.prop(pb, "ik_max_y", text="")
    y_row.active = pb.use_ik_limit_y and not pb.lock_ik_y
    z_row = limit_col.row(align=True)
    z_row.active = not pb.lock_ik_z
    z_col = z_row.column(align=True)
    z_col.prop(pb, "use_ik_limit_z", text="", icon='CON_ROTLIMIT')
    z_col = z_row.column(align=True)
    z_row = z_col.row(align=True)
    z_row.prop(pb, "ik_min_z", text="")
    z_row.prop(pb, "ik_max_z", text="")
    z_row.active = pb.use_ik_limit_z and not pb.lock_ik_z

def show_track_kinematics(layout, pb, bone):
    row = layout.row()
    axis_col = row.column(align=True)
    axis_col.label(text="X")
    axis_col.label(text="Y")
    axis_col.label(text="Z")
    axis_col.ui_units_x = 1
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

def show_soft_kinematics(layout, pb, copy, limit):
    # show the bones IK stretching, copy scale power and limit scale Y limit...
    row = layout.row(align=True)
    # all in one row...
    row.prop(pb, "ik_stretch", text="Stretch", icon='CON_STRETCHTO')
    row.prop(copy, "power", text="Power", icon='CON_SIZELIKE')
    row.prop(limit, "max_y", text="Max Y", icon='CON_SIZELIMIT')

def show_track_kinematics(layout, pb, bone):
    row = layout.row(align=True)
    row.prop(pb, "ik_stretch", text="Stretch")
    row.prop(bone, "lean")
    row.prop(bone, "turn")
    row = layout.row()
    axis_col = row.column(align=True)
    axis_col.label(text="X")
    axis_col.label(text="Y")
    axis_col.label(text="Z")
    axis_col.ui_units_x = 1
    # stiffness column...
    stiff_col = row.column(align=True)
    x_row = stiff_col.row(align=True)
    x_row.prop(pb, "ik_stiffness_x", text="")
    x_row.active = not pb.lock_ik_x
    y_row = stiff_col.row(align=True)
    y_row.prop(pb, "ik_stiffness_y", text="")
    y_row.active = not pb.lock_ik_y
    z_row = stiff_col.row(align=True)
    z_row.prop(pb, "ik_stiffness_z", text="")
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

def show_twist_controls(layout, rigging, armature):
    pbs, twist = armature.pose.bones, rigging.get_pointer()
    pb = pbs.get(twist.bone.source)
    row = layout.row()
    if pb and twist.is_rigged and twist.has_properties:
        col = row.column()
        col.alignment = "RIGHT"
        if rigging.flavour == 'HEAD_HOLD':
            col.label(text="Limits")
            col.label(text="")
            col.label(text="")
            col.label(text="")
            col.separator()
            col.label(text="Track")
            col = row.column()
            damp_track, limit_rot = pb.constraints.get("TWIST - Damped Track"), pb.constraints.get("TWIST - Limit Rotation")
            show_limit_rotation(col, limit_rot)
            col.separator()
            col.prop(damp_track, "head_tail")
        elif rigging.flavour == 'TAIL_FOLLOW':
            col.label(text="Kinematics")
            col = row.column()
            ik = pb.constraints.get("TWIST - IK")
            col.prop(ik, "influence")
            show_bone_kinematics(col, pb, show_stretch=False)
    else:
        layout.label(text="Animation controls appear here once rigged...")

def show_chain_controls(layout, rigging, armature):
    pbs, chain = armature.pose.bones, rigging.get_pointer()
    if chain.is_rigged and chain.has_properties:
        row = layout.row()
        # show the IK/FK switching properties... (on chains with switching)
        if rigging.flavour in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE']:
            col = row.column()
            col.alignment = 'RIGHT'
            col.label(text="Kinematics")
            col.label(text="")
            
            for i, bone in enumerate(chain.bones):
                col.separator()
                source_pb, gizmo_pb = pbs.get(bone.source), pbs.get(bone.gizmo)
                if source_pb and gizmo_pb:
                    copy, limit = gizmo_pb.constraints.get("SOFT - Copy Scale"), gizmo_pb.constraints.get("SOFT - Limit Scale")
                    if copy and limit:
                        col.label(text=source_pb.name)
                    ocol = col.column(align=True)
                    ocol.alignment = 'RIGHT'
                    ocol.label(text="")
                    ocol.label(text="")
                    ocol.label(text="")
                    
            col.separator()
            col.label(text="Snapping")

            col = row.column()
            row = col.row(align=True)
            #row.prop(chain, "use_auto_fk", text="Automatic Switching" if chain.use_auto_fk else "Manual Switching", emboss=True, icon='AUTOMERGE_ON' if chain.use_auto_fk else 'AUTOMERGE_OFF')
            row.prop(chain, "use_auto_fk", text="", emboss=True, icon='AUTOMERGE_ON' if chain.use_auto_fk else 'AUTOMERGE_OFF')
            string = ("Using FK " if chain.use_fk else "Using IK ") + ("(Automatic Switching)" if chain.use_auto_fk else "(Manual Switching)")
            #row.prop(chain, "use_fk", text="Using FK" if chain.use_fk else "Using IK", emboss=True, icon='CON_CLAMPTO' if chain.use_fk else 'CON_FOLLOWPATH')
            fcol = row.column(align=True)
            fcol.prop(chain, "use_fk", text=string, emboss=True, icon='CON_CLAMPTO' if chain.use_fk else 'CON_FOLLOWPATH')
            fcol.enabled = not chain.use_auto_fk
            
            row = col.row()
            row.prop(chain, "ik_softness")
            row.prop(chain, "fk_influence")
            row.enabled = not chain.use_fk
            
            #col.separator()
            for bone in chain.bones:
                col.separator()
                source_pb, gizmo_pb = pbs.get(bone.source), pbs.get(bone.gizmo)
                if source_pb and gizmo_pb:
                    copy, limit = gizmo_pb.constraints.get("SOFT - Copy Scale"), gizmo_pb.constraints.get("SOFT - Limit Scale")
                    if copy and limit:
                        show_soft_kinematics(col, source_pb, copy, limit)
                    show_bone_kinematics(col, source_pb, show_stretch=False)
            
            if chain.use_floor:
                col.separator()
                row = col.row()
                snap_name = chain.target.bone if rigging.flavour == 'OPPOSABLE' else chain.target.parent
                snap_floor = row.operator("jk.arl_snap_bones", text="Floor to Target", icon='SNAP_ON')
                snap_floor.source, snap_floor.target = chain.floor.bone, snap_name
                snap_target = row.operator("jk.arl_snap_bones", text="Target to Floor", icon='SNAP_ON')
                snap_target.source, snap_target.target = snap_name, chain.floor.bone
                row.enabled = not chain.use_fk
                    

        # spline chains have the fit curve property...
        elif rigging.flavour == 'SPLINE':
            col = row.column()
            col.alignment = 'RIGHT'
            col.label(text="Kinematics")
            col.separator()
            col.label(text="Snapping")
            
            col = row.column()
            col.prop(chain, "fit_curve")
            col.separator()
            row = col.row()
            snap_parent = row.operator("jk.arl_snap_bones", text="Parent > Start", icon='SNAP_ON')
            snap_parent.source, snap_parent.target = chain.spline.parent, chain.bones[0].source
            snap_start = row.operator("jk.arl_snap_bones", text="Start > Parent", icon='SNAP_ON')
            snap_start.source, snap_start.target = chain.bones[0].source, chain.spline.parent
        
        # scalar chains only have IK softness... (for now)
        elif rigging.flavour == 'SCALAR':
            col = row.column()
            col.alignment = 'RIGHT'
            col.label(text="Kinematics")
            for bone in chain.bones:
                col.separator()
                source_pb, gizmo_pb = pbs.get(bone.source), pbs.get(bone.gizmo)
                if source_pb and gizmo_pb:
                    copy, limit = gizmo_pb.constraints.get("SOFT - Copy Scale"), gizmo_pb.constraints.get("SOFT - Limit Scale")
                    if copy and limit:
                        col.label(text=source_pb.name)
                    ocol = col.column(align=True)
                    ocol.alignment = 'RIGHT'
                    ocol.label(text="")
                    ocol.label(text="")
                    ocol.label(text="")
            
            col = row.column()
            col.prop(chain, "ik_softness")     
            for bone in chain.bones:
                col.separator()
                source_pb, gizmo_pb = pbs.get(bone.source), pbs.get(bone.gizmo)
                if source_pb and gizmo_pb:
                    copy, limit = gizmo_pb.constraints.get("SOFT - Copy Scale"), gizmo_pb.constraints.get("SOFT - Limit Scale")
                    if copy and limit:
                        show_soft_kinematics(col, source_pb, copy, limit)
                    show_bone_kinematics(col, source_pb, show_stretch=False)
        
        # else if this is a tracking chain...
        elif rigging.flavour == 'TRACKING':
            col = row.column()
            col.alignment = 'RIGHT'
            col.label(text="Kinematics")
            
            for bone in chain.bones:
                col.separator()
                source_pb = pbs.get(bone.source)
                if source_pb:
                    copy = source_pb.constraints.get('TRACK - Copy Rotation')
                    if copy:
                        col.label(text=source_pb.name)
                    ocol = col.column(align=True)
                    ocol.alignment = 'RIGHT'
                    ocol.label(text="")
                    ocol.label(text="")
                    ocol.label(text="")
                    col.label(text="")
                    #orow = ocol.row()
                    #orow.label(text="")
            
            col = row.column()
            row = col.row()
            row.prop(chain.target, "lock_x")
            row.prop(chain.target, "lock_z")
            row.enabled = True if pbs.get(chain.target.control) else False
            
            for bone in chain.bones:
                col.separator()
                source_pb = pbs.get(bone.source)
                if source_pb:
                    copy = source_pb.constraints.get('TRACK - Copy Rotation')
                    show_track_kinematics(col, source_pb, bone)
                    if copy:
                        col.prop(copy, "influence")

        elif rigging.flavour == 'FORWARD':
            col = row.column()
            col.alignment = 'RIGHT'
            for bone in chain.bones:
                col.separator()
                orow = col.row(align=True)
                source_pb = pbs.get(bone.source)
                if source_pb:
                    ocol = orow.column(align=True)
                    ocol.alignment = 'RIGHT'
                    ocol.label(text=source_pb.name)
                    ocol.label(text="")
                    ocol.label(text="")
             
            col = row.column()
            for bone in chain.bones:
                col.separator()
                source_pb = pbs.get(bone.source)
                if source_pb:
                    row = col.row()
                    for name in ["FORWARD - Copy Location", "FORWARD - Copy Rotation", "FORWARD - Copy Scale"]: 
                        if name in source_pb.constraints:
                            constraint = source_pb.constraints.get(name)
                            if name == "FORWARD - Copy Rotation":
                                show_copy_rotation(row, constraint)
                            elif name == "FORWARD - Copy Location":
                                show_copy_location(row, constraint)
                            elif name == "FORWARD - Copy Scale":
                                show_copy_scale(row, constraint)




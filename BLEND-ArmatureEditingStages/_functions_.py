import bpy

def Get_Armatures_From_Stages(master, stages):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    for stage in stages:
        stage_object = bpy.data.objects[stage.Armature]
        for collection in master.users_collection:
            bpy.data.collections[collection.name].objects.link(stage_object)
        stage_object.select_set(True)
        bpy.context.view_layer.objects.active = stage_object

def Set_Armatures_To_Stages(master, stages):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    for stage in stages:
        stage_object = bpy.data.objects[stage.Armature]
        for collection in master.users_collection:
            bpy.data.collections[collection.name].objects.unlink(stage_object)
        master.select_set(True)
        bpy.context.view_layer.objects.active = master

def Get_Push_Bones(stage, bones):
    last_mode = bpy.context.object.mode
    bpy.ops.object.mode_set(mode='OBJECT')
    # if this stage is pushing bones...    
    if stage.Push_bones:
        # iterate over the armatures bones...
        for bone in bones:
            # adding settings for any new bones...
            if bone.name not in stage.Bones:
                new_bone = stage.Bones.add()
                new_bone.name = bone.name
        # then removing any bone settings...
        for bone in stage.Bones:
            # that are not in the armature anymore...
            if bone.name not in bones:
                stage.Bones.remove(stage.Bones.find(bone.name))
    # else the stage is not pushing bones...
    else:
        # and we should clear the collection...
        stage.Bones.clear()
    bpy.ops.object.mode_set(mode=last_mode)
    
def Push_Edit_Bone(from_edit, from_bone, to_bone):
    # if we are pushing transforms...        
    if from_edit.Push_transform:
        # we gotta iterate on these settings...
        for prop in ['head', 'tail', 'roll', 'lock']:
            # setting them close to the bone... lul
            exec("to_bone." + prop + " =  from_bone." + prop)
    # if we are pushing bendy bones...
    if from_edit.Push_bendy_bones:
        # heckin much lots of flex...
        bb_props = ['bbone_segments', 'bbone_x', 'bbone_z', 'bbone_handle_type_start', 'bbone_custom_handle_start', 
        'bbone_handle_type_end', 'bbone_custom_handle_end', 'bbone_rollin', 'bbone_rollout', 'use_endroll_as_inroll',
        'bbone_curveinx', 'bbone_curveiny', 'bbone_curveoutx', 'bbone_curveouty', 'bbone_easein', 
        'bbone_easeout', 'bbone_scaleinx', 'bbone_scaleiny', 'bbone_scaleoutx', 'bbone_scaleouty']
        for prop in bb_props:
            # to be bent into position...
            exec("to_bone." + prop + " =  from_bone." + prop)
    # if we are pushing relations...
    if from_edit.Push_relations:
        # this family...
        for prop in ['layers', 'parent', 'use_connect', 'use_inherit_rotation', 'inherit_scale']:
            # is coming over for the holidays...
            exec("to_bone." + prop + " =  from_bone." + prop)
    # and if we are pushing deform settings...
    if from_edit.Push_deform:
        # don't let these deformities fool you...
        for prop in ['use_deform', 'envelope_distance', 'envelope_weight', 'use_envelope_multiply', 'head_radius', 'tail_radius']:
            # it's whats on the inside that counts...
            exec("to_bone." + prop + " =  from_bone." + prop)

def Push_Pose_Bone(from_pose, from_bone, to_bone, from_object, to_object):
    # if we are pushing transforms...  
    if from_pose.Push_posing:
        rot_props = ['location', 'lock_location', 'rotation_mode', 'rotation_quaternion', 'rotation_euler', 
            'rotation_axis_angle', 'lock_rotation_w', 'lock_rotation', 'scale', 'lock_scale']
        for prop in rot_props:
            exec("to_bone." + prop + " =  from_bone." + prop)
    # if we are pushing the bone group...  
    if from_pose.Push_group:
        from_group = from_bone.bone_group
        if from_group != None:
            # if the group exists use it...
            if from_group.name in to_object.pose.bone_groups:
                to_bone.bone_group = to_object.pose.bone_groups[from_group.name]
            # otherwise copy it over...
            else:
                to_group = to_object.pose.bone_groups.new(name=from_group.name)
                # using the good old rna property trick...
                for g_prop in to_group.bl_rna.properties:
                    if not g_prop.is_readonly:
                        exec("to_group." + g_prop.identifier + " =  from_group." + g_prop.identifier)   
    # if we are pushing IK settings...
    if from_pose.Push_ik:
        ik_props = ['lock_ik_x', 'lock_ik_y', 'lock_ik_z', 'use_ik_limit_x', 'use_ik_limit_y', 'use_ik_limit_z', 
        'use_ik_rotation_control', 'use_ik_linear_control','ik_min_x', 'ik_max_x', 'ik_min_y', 'ik_max_y', 'ik_min_z', 'ik_max_z', 
        'ik_stiffness_x', 'ik_stiffness_y', 'ik_stiffness_z', 'ik_stretch', 'ik_rotation_weight', 'ik_linear_weight']
        for prop in ik_props:
            exec("to_bone." + prop + " =  from_bone." + prop)
    # and if we are pushing the display...
    if from_pose.Push_display:
        for prop in ['custom_shape', 'custom_shape_scale', 'use_custom_shape_bone_size', 'custom_shape_transform']:
            exec("to_bone." + prop + " =  from_bone." + prop)
    # also if we are pushing constraints... (always clears existing)
    if from_pose.Push_constraints:
        # if the bone we are pushing from doesn't have constraints, kill all constraints on the bone we push to...
        if len(from_bone.constraints) == 0:
            for constraint in to_bone.constraints:
                to_bone.constraints.remove(constraint)
        # else it does have constraints...
        else:
            # and we can do a quick bit of selection and copy the constraints across... (this way should preserve child of space?)
            bpy.ops.pose.select_all(action='DESELECT')
            to_bone.bone.select = True
            from_object.data.bones.active = from_bone.bone
            from_bone.bone.select = True
            bpy.ops.pose.constraints_copy()
    # and if we want to push drivers... 
    if from_pose.Push_drivers:
        # kill any existing drivers on the bone we are pushing to...
        if to_object.animation_data and to_object.animation_data.drivers:
            for driver in [d for d in to_object.animation_data.drivers if ('"%s"' % to_bone.name) in d.data_path]:
                to_object.animation_data.drivers.remove(driver)
        # now the fun really begins when we iterate over the bone we push froms drivers...
        for from_driver in [d for d in from_object.animation_data.drivers if ('"%s"' % to_bone.name) in d.data_path]:
            # adding a new driver for the bone we are pushing to...
            if to_object.animation_data == None:
                to_object.animation_data_create()
            to_driver = to_object.animation_data.drivers.new(from_driver.data_path, index=from_driver.array_index)
            # for each driver property on the from driver that isn't read only...
            for d_prop in from_driver.bl_rna.properties:
                if not d_prop.is_readonly:
                    # set the same to driver property to it...
                    exec("to_driver." + d_prop.identifier + " =  from_driver." + d_prop.identifier)
            # then we need to do the same for the drivers driver property... (where the expression actually is)
            for dd_prop in from_driver.driver.bl_rna.properties:
                if not dd_prop.is_readonly:
                    exec("to_driver.driver." + dd_prop.identifier + " =  from_driver.driver." + dd_prop.identifier)
            # then for each variable on the push from driver we add a variable to the push to driver...
            for from_var in from_driver.driver.variables:
                to_var = to_driver.driver.variables.new()
                # iterate over the variables properties setting them like before...
                for ddv_prop in from_var.bl_rna.properties:
                    if not ddv_prop.is_readonly:
                        exec("to_var." + ddv_prop.identifier + " = from_var." + ddv_prop.identifier)
                # then for each target of the from variables targets we do almost the same again but...
                for i, from_tar in enumerate(from_var.targets):
                    # enumerating to use the index to get the to target of from vars target...
                    to_tar = to_var.targets[i]
                    for ddvt_prop in from_tar.bl_rna.properties:
                        # id type is read only when the variable is not a single property so we need to check that...
                        id_type_bool = True if ddvt_prop.identifier != 'id_type' else True if from_var.type == 'SINGLE_PROPERTY' else False
                        if not ddvt_prop.is_readonly and id_type_bool:
                            exec("to_tar." + ddvt_prop.identifier + " = from_tar." + ddvt_prop.identifier)
            # then we can remove any modifiers that might of been auto-created... (drivers have done this to me before)
            for sneaky_mod in to_driver.modifiers:
                to_driver.modifiers.remove(sneaky_mod)
            # aaaaand finally... we push... modifiers...
            for from_mod in from_driver.modifiers:
                to_mod = to_driver.modifiers.new(from_mod.type)
                for m_prop in from_mod.bl_rna.properties:
                    if not m_prop.is_readonly:
                        exec("to_mod." + m_prop.identifier + " = from_mod." + m_prop.identifier)

def Push_Bones(master, stage_from, stage_to):
    # get the stage objects and pull them out of the bpy.data void...
    from_object = bpy.data.objects[stage_from.Armature]
    to_object = bpy.data.objects[stage_to.Armature]
    Get_Armatures_From_Stages(master, [stage_to, stage_from])
    # update the push bone settings on the stage we are pushing...
    Get_Push_Bones(stage_from, from_object.data.bones)
    # get the bones we need to push...
    push_edit_bones = [bone for bone in stage_from.Bones if bone.Push_edit]
    push_pose_bones = [bone for bone in stage_from.Bones if bone.Push_pose]
    print(push_edit_bones, push_pose_bones)
    # if we are pushing edit bones hop into edit mode...
    if len(push_edit_bones) > 0:
        bpy.ops.object.mode_set(mode='EDIT')
        for bone in push_edit_bones:
            # grab the edit bone and edit push settings...
            from_bone = from_object.data.edit_bones[bone.name]
            from_edit = bone.Edit
            # if the bone exists in the stage we are heading to grab a reference to it...
            if from_bone.name in to_object.data.edit_bones:
                to_bone = to_object.data.edit_bones[from_bone.name]
            # else if it doesn't exist create a new bone...
            else:
                to_bone = to_object.data.edit_bones.new(from_bone.name)
            Push_Edit_Bone(from_edit, from_bone, to_bone)
    # if we are pushing pose bones hop into pose mode...
    if len(push_pose_bones) > 0:
        bpy.ops.object.mode_set(mode='POSE')
        for bone in push_pose_bones:
            # grab the pose bone and edit push settings...
            from_bone = from_object.pose.bones[bone.name]
            from_pose = bone.Pose
            # if the bone exists in the stage we are heading to grab a reference to it, and push the posers...
            if from_bone.name in to_object.pose.bones:
                to_bone = to_object.pose.bones[from_bone.name]
                Push_Pose_Bone(from_pose, from_bone, to_bone, from_object, to_object)
    # update the push bone settings on the stage we are pushing...
    Get_Push_Bones(stage_from, to_object.data.bones)
    # and then we can send the stage armatures back to the abyss...                
    Set_Armatures_To_Stages(master, [stage_from, stage_to])

def Push_Data(master, stage_from, stage_to):
    # get the datas and objects we need...
    from_object = bpy.data.objects[stage_from.Armature]
    from_data = bpy.data.armatures[stage_from.Armature]
    to_object = bpy.data.objects[stage_to.Armature]
    to_data = bpy.data.armatures[stage_to.Armature]
    # if we want to push dat oesteology...
    if stage_from.Data.Push_skeleton:
        to_data.pose_position = from_data.pose_position
        to_data.layers = from_data.layers
        to_data.layers_protected = from_data.layers_protected
    # if we to push dem bone colours...
    if stage_from.Data.Push_groups:
        # for each bone group in
        for from_group in from_object.pose.bone_groups:
            # get the group if it already exists...
            if from_group.name not in to_object.pose.bone_groups:
                to_group = to_object.pose.bone_groups[from_group.name]
            else:
                # otherwise make a create one with it's name...
                to_group = to_object.pose.bone_groups.new(name=from_group.name)
            # set all the settings using the good old rna property trick...
            for g_prop in to_group.bl_rna.properties:
                if not g_prop.is_readonly:
                    exec("to_group." + g_prop.identifier + " =  from_group." + g_prop.identifier)
    # if we want to push our selfies...
    if stage_from.Data.Push_library:
        to_object.pose_library = from_object.pose_library
    # and finally if we want to slap in some style...
    if stage_from.Data.Push_display:
        d_props = ['display_type', 'show_names', 'show_bone_custom_shapes', 'show_axes', 'show_group_colors']
        for d_prop in d_props:
            exec("to_data." + d_prop + " =  from_data." + d_prop)
    # copy and push the data...
    #copy_data = from_data.copy()
    #to_object.data = copy_data
    # remove the old data...
    #bpy.data.armatures.remove(to_data)
    # return stage data name...
    #copy_data.name = stage_to.Armature

def Push_Object(master, stage_from, stage_to):
    # get the objects and data we need...
    from_object = bpy.data.objects[stage_from.Armature]
    #from_data = bpy.data.armatures[stage_from.Armature]
    to_object = bpy.data.objects[stage_to.Armature]
    #to_data = bpy.data.armatures[stage_to.Armature]

    if stage_from.Object.Push_transform:
        t_props = ['location', 'rotation_euler', 'rotation_quaternion', 'rotation_axis_angle', 'rotation_mode', 'scale', 
            'delta_location', 'delta_rotation_quaternion', 'delta_rotation_euler', 'delta_scale']
        for t_prop in t_props:
            exec("to_object." + t_prop + " =  from_object." + t_prop)

    if stage_from.Object.Push_relations:
        r_props = ['parent', 'parent_type', 'parent_bone', 'track_axis', 'up_axis', 'pass_index']
        for r_prop in r_props:
            exec("to_object." + r_prop + " =  from_object." + r_prop)

    if stage_from.Object.Push_instancing:
        i_props = ['instance_type', 'show_instancer_for_viewport', 'show_instancer_for_render', 
            'use_instance_vertices_rotation', 'use_instance_faces_scale', 'instance_faces_scale']
        for i_prop in i_props:
            exec("to_object." + i_prop + " =  from_object." + i_prop)

    if stage_from.Object.Push_display:
        d_props = ['show_name', 'show_axis', 'show_in_front', 'show_axis', 'display_type', 'show_bounds', 'display_bounds_type']
        for d_prop in d_props:
            exec("to_object." + d_prop + " =  from_object." + d_prop)
        



    # push the object...
    #copy_object = from_object.copy()
    #bpy.data.objects.remove(to_object)
    #copy_object.name = stage_to.Armature
    #copy_object.data = to_data
    # return stage data name...
    #copy_object.name = stage_to.Armature

def Push_To_Stage(master, stage_from, stage_to):
    # if both data and object exist, push them and return true...
    if bpy.data.armatures[stage_from.Armature] and bpy.data.objects[stage_from.Armature]:
        if stage_from.Push_object:
            Push_Object(master, stage_from, stage_to)
        if stage_from.Push_data:
            Push_Data(master, stage_from, stage_to)
        if stage_from.Push_bones:
            Push_Bones(master, stage_from, stage_to)
        return True
    else:
        return False

def Push_From_Stage(master, stage_from):
    # get all the stages...
    stages = master.data.AES.Stages
    # if a stage doesn't push anything none of it's children will need changing...
    if (stage_from.Push_data or stage_from.Push_object or stage_from.Push_bones):
        # kick off iteration by dunmping the stage from into the list of children...
        children = [stage_from.name] #[stage.name for stage in stages if stage.Parent == stage_from]
        # we should iterate through all children...
        i, iterate, success = 0, True, True
        # while the iterate bool is true...
        while iterate:
            # get the name and increment...
            name, i = children[i], i + 1
            # get the stage from the name...
            stage = stages[name]
            # get any children of the stage...
            next_children = [c for c in stages if c.Parent == name]
            # if the stage should push to it's children... (and has any)
            if (stage.Push_data or stage.Push_object or stage.Push_bones) and len(next_children) > 0:
                # iterate over them backwards...
                next_children.reverse()
                for child in next_children:
                    # push then check if the push was successful...
                    success = Push_To_Stage(master, stage, child)
                    # success means we extend the list of children by inserting moar name... 
                    if success:
                        # inserting at the next index to maintain order
                        children.insert(i, child.name)
                    # if it wasn't break from this loop...
                    else:
                        break
            # if not successful, break on through to the other side...
            if not success:
                break
            # finally the iterate bool, will stop iteration once we reach the length of the accumulating children...
            iterate = True if i < len(children) else False
        # if we were not successful...
        if not success:
            # rage at user error...
            print("A stage armature has been deleted!? ... WTF, Don't break my !£$%^&* add-ons... smacked bottoms all round! Maybe i can fix this...")
            # if the source exists, we can make try to fix as much as possible by pushing from the source...
            if master.data.AES.Stages[0].Armature in bpy.data.objects:
                Push_From_Source(master.data.AES.Stages[0], master)
                print("So... i just disciplined every stage... they might not be the same anymore though...")
            # else you're screwed...
            else:
                print("Nope... you have some how killed the source armature... *sighs* i knew i should of made a backup...")

def Push_From_Source(master, source):
    stages = master.data.AES.Stages
    # so you will only be heading into this if you broke something...
    children = [source.name] #[stage.name for stage in stages if stage.Parent == stage_from]
    # and i can iterate through all stages to try and fix it...
    i, iterate = 0, True
    # while the iterate bool is true...
    while iterate:
        # get the name and increment...
        name, i = children[i], i + 1
        # get the stage from the name...
        stage = stages[name]
        # get any children of the stage...
        next_children = [c for c in stages if c.Parent == name]
        # if the stage should push to it's children... (and has any)
        if len(next_children) > 0:
            # iterate over them backwards...
            next_children.reverse()
            for child in next_children:
                # push and extend the list of children by inserting moar names
                Push_To_Stage(master, stage, child)
                children.insert(i, child.name)
        # finally the iterate bool, will stop iteration once we reach the length of the accumulating children...
        iterate = True if i < len(children) else False

def Push_To_Master(master, stage):
    stage.Is_pushing = True
    # get the stages armature object...
    stage_armature = bpy.data.objects[stage.Armature]
    # get the master data we need...
    master_name = master.name[:]
    master_data = master.data
    master_props = master_data.AES
    # get the stage data we need...
    stage_copy = stage_armature.copy()
    stage_data = stage_armature.data.copy()
    stage_props = stage_data.AES
    # link the copied object to every collection the master is in...
    for collection in master.users_collection:
        bpy.data.collections[collection.name].objects.link(stage_copy)
    # set the data settings for the master...
    stage_props.Is_master = master_props.Is_master
    stage_props.Master = None
    stage_props.Last = master_props.Last
    stage_props.Stage = master_props.Stage
    # set all the stage settings...
    for m_stage in master_props.Stages:
        n_stage = stage_props.Stages.add()
        n_stage.name, n_stage.Is_pushing = m_stage.name, True
        # push stage settings...
        n_stage.Armature, n_stage.Is_source = m_stage.Armature, m_stage.Is_source
        n_stage.Show_details, n_stage.Parent = m_stage.Show_details, m_stage.Parent
        # push data settings... 
        n_stage.Data.Push_skeleton, n_stage.Data.Push_groups = m_stage.Data.Push_skeleton, m_stage.Data.Push_groups
        n_stage.Data.Push_library, n_stage.Data.Push_display = m_stage.Data.Push_library, m_stage.Data.Push_display
        # push object settings...
        n_stage.Object.Push_transform, n_stage.Object.Push_relations = m_stage.Object.Push_transform, m_stage.Object.Push_relations
        n_stage.Object.Push_instancing, n_stage.Object.Push_display = m_stage.Object.Push_instancing, m_stage.Object.Push_display
        # iterate on stage bones...
        for m_bone in m_stage.Bones:
            n_bone = n_stage.Bones.add()
            n_bone.name, n_bone.Push_edit, n_bone.Push_pose = m_bone.name, m_bone.Push_edit, m_bone.Push_pose
            # push pose bone settings...
            n_bone.Pose.Push_posing, n_bone.Pose.Push_group = m_bone.Pose.Push_posing, m_bone.Pose.Push_group
            n_bone.Pose.Push_ik, n_bone.Pose.Push_display = m_bone.Pose.Push_ik, m_bone.Pose.Push_display
            n_bone.Pose.Push_constraints, n_bone.Pose.Push_drivers = m_bone.Pose.Push_constraints, m_bone.Pose.Push_drivers
            # push edit bone settings...
            n_bone.Edit.Push_transform, n_bone.Edit.Push_bendy_bones = m_bone.Edit.Push_transform, m_bone.Edit.Push_bendy_bones
            n_bone.Edit.Push_relations, n_bone.Edit.Push_deform = m_bone.Edit.Push_relations, m_bone.Edit.Push_deform
        # set stage push settings and return is pushing to false...
        n_stage.Push_data, n_stage.Push_object, n_stage.Push_bones = m_stage.Push_data, m_stage.Push_object, m_stage.Push_bones
        n_stage.Is_pushing = False
    # assign the copied data to the copied object...
    stage_copy.data = stage_data
    # stage_copy.parent = master.parent
    # move all the children from the master to the copy...
    for child in master.children:
        #print(master.name, child.name)
        child.parent = stage_copy    
    # remove the master object and data...
    bpy.data.objects.remove(master)
    bpy.data.armatures.remove(master_data)
    # rename the copied object and data to the masters name...
    stage_copy.name = master_name
    stage_copy.data.name = master_name
    bpy.context.view_layer.objects.active = stage_copy
    stage_copy.select_set(True)
    if 'BLEND-ArmatureControlBones' in bpy.context.preferences.addons.keys():
        if stage_copy.data.ACB.Has_controls:
            bpy.ops.jk.acb_sub_mode(Object=master_name)
        
def Pull_From_Master(master, stage):
    # get the stages armature object...
    stage_object = bpy.data.objects[stage.Armature]
    # get the stage data we need...
    stage_name = stage_object.name
    stage_data = stage_object.data
    # copy the master object and data...
    master_copy = master.copy()
    master_data = master.data.copy()
    # remove the old stage object...
    bpy.data.objects.remove(stage_object)
    # set the copied object name...
    master_copy.name = stage_name
    # remove the old stage data...
    bpy.data.armatures.remove(stage_data)
    # set the copied data name...
    master_data.name = stage_name
    # set is master false... (so the stage will get cleaned up if the master gets deleted)
    master_data.AES.Is_master = False
    master_data.AES.Master = master
    master_data.AES.Stages.clear()
    # assign the data...
    master_copy.data = master_data
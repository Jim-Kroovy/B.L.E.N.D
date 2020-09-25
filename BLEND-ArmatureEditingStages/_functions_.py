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

def Set_RNA_Properties(source, target, override=[], exclude=[]):
    # if we are excluding any transforms then we need to add all matrix properties to the exclusion list...
    if any(e in ["location", "rotation_euler", "rotation_quaternion", "rotation_axis_angle", "scale"] for e in exclude):
        exclude = exclude + [tp.identifier for tp in target.bl_rna.properties if "matrix" in tp.identifier]
    # just get all the from data blocks RNA property identifiers if the override list is empty...
    from_rna_ids = [sp.identifier for sp in source.bl_rna.properties] if len(override) == 0 else override
    # get the properties that are in both data blocks and are not in the exclude list or read only...
    to_rna_ids = [fi for fi in from_rna_ids if fi in [tp.identifier for tp in target.bl_rna.properties if not (tp.is_readonly or tp.identifier in exclude)]]
    # then iterate on them...
    for rna_id in to_rna_ids:
        # use a neat little execute to format and run the code that will set the data block settings...
        exec("target." + rna_id + " =  source." + rna_id)

def Get_Is_Armature_Valid(data):
    is_valid = False
    if data.AES.Is_stage:
        for armature in [a for a in bpy.data.armatures if a.AES.Is_master]:
            if not is_valid:
                for stage in armature.AES.Stages:
                    if stage.Armature == data.name:
                        is_valid = True
                        break
            else:
                break
    else:
        is_valid = True
    return is_valid

def Get_Push_Bones(stage, bones):
    last_mode = bpy.context.object.mode
    if last_mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')
    # iterate over the armatures bones...
    for bone in bones:
        # adding settings for any new bones...
        if bone.name not in stage.Bones:
            new_bone = stage.Bones.add()
            new_bone.name = bone.name
    # get all the names of the stage bones...
    stage_bones = {b.name : index for index, b in enumerate(stage.Bones)}
    # then remove any bone settings...
    for name, index in stage_bones.items():
        # that are not in the armature anymore...
        if name not in bones:
            stage.Bones.remove(index)
    if last_mode == 'EDIT':
        bpy.ops.object.mode_set(mode=last_mode)

def Get_Stage_Bone_Hierarchy(stage, bones):
    hierarchy = []
    parentless = [b for b in bones if b.parent == None]
    for parent in parentless:
        hierarchy.append(stage.Bones[parent.name])
        for child in parent.children_recursive:
            hierarchy.append(stage.Bones[child.name])
    return hierarchy

def Get_Installed_Addons():
    addons = bpy.context.preferences.addons.keys()
    installed = {'BLEND-ArmatureControlBones' : True if 'BLEND-ArmatureControlBones' in addons else False, 
        'BLEND-ArmatureRiggingLibrary' : True if 'BLEND-ArmatureRiggingLibrary' in addons else False}
    return installed

def Push_Edit_Bone(from_edit, from_bone, to_bone):
    # if we are pushing transforms...        
    if from_edit.Push_transform:
        # set them close to the bone... lul
        Set_RNA_Properties(from_bone, to_bone, override=['head', 'tail', 'roll', 'lock'])
    # if we are pushing bendy bones...
    if from_edit.Push_bendy_bones:
        # heckin much lots of flex...
        bb_props = ['bbone_segments', 'bbone_x', 'bbone_z', 'bbone_handle_type_start', 'bbone_custom_handle_start', 
            'bbone_handle_type_end', 'bbone_custom_handle_end', 'bbone_rollin', 'bbone_rollout', 'use_endroll_as_inroll',
            'bbone_curveinx', 'bbone_curveiny', 'bbone_curveoutx', 'bbone_curveouty', 'bbone_easein', 
            'bbone_easeout', 'bbone_scaleinx', 'bbone_scaleiny', 'bbone_scaleoutx', 'bbone_scaleouty']
        # to be bent into position...
        Set_RNA_Properties(from_bone, to_bone, override=bb_props)
    # if we are pushing relations...
    if from_edit.Push_relations:
        # this family...
        r_props = ['layers', 'use_connect', 'use_inherit_rotation', 'inherit_scale']
        # is coming over for the holidays...
        Set_RNA_Properties(from_bone, to_bone, override=r_props)
        # so make sure the parents are ready...
        parent = None if from_bone.parent == None else to_bone.id_data.edit_bones[from_bone.parent.name]
        to_bone.parent = parent
    # and if we are pushing deform settings...
    if from_edit.Push_deform:
        # don't let these deformities fool you...
        d_props = ['use_deform', 'envelope_distance', 'envelope_weight', 'use_envelope_multiply', 'head_radius', 'tail_radius']
        # it's whats on the inside that counts...
        Set_RNA_Properties(from_bone, to_bone, override=d_props)

def Push_Pose_Bone(from_pose, from_bone, to_bone, from_object, to_object):
    # if we are pushing transforms...  
    if from_pose.Push_posing:
        p_props = ['location', 'lock_location', 'rotation_mode', 'rotation_quaternion', 'rotation_euler', 
            'rotation_axis_angle', 'lock_rotation_w', 'lock_rotation', 'scale', 'lock_scale']
        Set_RNA_Properties(from_bone, to_bone, override=p_props)
    # if we are pushing the bone group...  
    if from_pose.Push_group:
        from_group = from_bone.bone_group
        if from_group != None:
            # if the group exists use it...
            if from_group.name in to_object.pose.bone_groups:
                to_bone.bone_group = to_object.pose.bone_groups[from_group.name]
    # if we are pushing IK settings...
    if from_pose.Push_ik:
        ik_props = ['lock_ik_x', 'lock_ik_y', 'lock_ik_z', 'use_ik_limit_x', 'use_ik_limit_y', 'use_ik_limit_z', 
        'use_ik_rotation_control', 'use_ik_linear_control','ik_min_x', 'ik_max_x', 'ik_min_y', 'ik_max_y', 'ik_min_z', 'ik_max_z', 
        'ik_stiffness_x', 'ik_stiffness_y', 'ik_stiffness_z', 'ik_stretch', 'ik_rotation_weight', 'ik_linear_weight']
        Set_RNA_Properties(from_bone, to_bone, override=ik_props)
    # and if we are pushing the display...
    if from_pose.Push_display:
        d_props = ['custom_shape', 'custom_shape_scale', 'use_custom_shape_bone_size', 'custom_shape_transform']
        Set_RNA_Properties(from_bone, to_bone, override=d_props)
    # also if we are pushing constraints...
    if from_pose.Push_constraints:
        # remove all existing constraints on the to bone...
        for constraint in to_bone.constraints:
            to_bone.constraints.remove(constraint)
        for from_con in from_bone.constraints:
            to_con = to_bone.constraints.new(type=from_con.type)
            # to_con.name = from_con.name
            Set_RNA_Properties(from_con, to_con)
    # and if we want to push drivers... 
    if from_pose.Push_drivers:
        # kill any existing drivers on the bone we are pushing to...
        if to_object.animation_data and to_object.animation_data.drivers:
            for driver in [d for d in to_object.animation_data.drivers if ('"%s"' % to_bone.name) in d.data_path]:
                to_object.animation_data.drivers.remove(driver)
        # if there is even from_object animation data...
        if from_object.animation_data:
            # now the fun really begins when we iterate over the bone we push froms drivers...
            for from_driver in [d for d in from_object.animation_data.drivers if ('"%s"' % to_bone.name) in d.data_path]:
                # adding a new driver for the bone we are pushing to...
                if to_object.animation_data == None:
                    to_object.animation_data_create()
                to_driver = to_object.animation_data.drivers.new(from_driver.data_path, index=from_driver.array_index)
                # for each driver property on the from driver that isn't read only...
                Set_RNA_Properties(from_driver, to_driver)
                # then we need to do the same for the drivers driver property... (where the expression actually is)
                Set_RNA_Properties(from_driver.driver, to_driver.driver)
                # then for each variable on the push from driver we add a variable to the push to driver...
                for from_var in from_driver.driver.variables:
                    to_var = to_driver.driver.variables.new()
                    # iterate over the variables properties setting them like before...
                    Set_RNA_Properties(from_var, to_var)
                    # then for each target of the from variables targets we do almost the same again but...
                    for i, from_tar in enumerate(from_var.targets):
                        # enumerating to use the index to get the to target of from vars target...
                        to_tar = to_var.targets[i]
                        Set_RNA_Properties(from_tar, to_tar)
                # then we can remove any modifiers that might of been auto-created... (drivers have done this to me before)
                for sneaky_mod in to_driver.modifiers:
                    to_driver.modifiers.remove(sneaky_mod)
                # aaaaand finally... we push... modifiers...
                for from_mod in from_driver.modifiers:
                    to_mod = to_driver.modifiers.new(from_mod.type)
                    Set_RNA_Properties(from_mod, to_mod)

def Push_Bones(master, stage_from, stage_to):
    # get certain other BLEND addons if they are installed...
    addons = Get_Installed_Addons()
    # get the stage objects and pull them out of the bpy.data void...
    from_object = bpy.data.objects[stage_from.Armature]
    to_object = bpy.data.objects[stage_to.Armature]
    Get_Armatures_From_Stages(master, [stage_from, stage_to])
    # update the push bone settings on the stage we are pushing...
    Get_Push_Bones(stage_from, from_object.data.bones)
    # we should probably process this in order of hierachy...
    bones = from_object.data.edit_bones if from_object.mode == 'EDIT' else from_object.data.bones
    stage_bones = Get_Stage_Bone_Hierarchy(stage_from, bones)
    # get the bones we need to push...
    push_edit_bones = [bone for bone in stage_bones if bone.Push_edit]
    push_pose_bones = [bone for bone in stage_bones if bone.Push_pose]
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
        bpy.ops.object.mode_set(mode='OBJECT')
        # if my rigging library add-on is installed...
        if addons['BLEND-ArmatureRiggingLibrary']:
            # force updates of any rigging on the to stage armature...
            for i, chain in enumerate(to_object.ARL.Chains):
                to_object.ARL.Chain = i
                bpy.ops.jk.chain_set(Action='UPDATE')
            for i, twist in enumerate(to_object.ARL.Twists):
                to_object.ARL.Twist = i
                bpy.ops.jk.twist_set(Action='UPDATE')
            for i, pivot in enumerate(to_object.ARL.Pivots):
                if not pivot.Is_forced:
                    to_object.ARL.Pivots = i
                    bpy.ops.jk.pivot_set(Action='UPDATE')
            for i, floor in enumerate(to_object.ARL.Floors):
                to_object.ARL.Floor = i
                bpy.ops.jk.floor_set(Action='UPDATE')
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
    # if there are installed add-ons...
    if any(val for val in addons.values()):
        # we have some bone properties to set for certain ones...
        for bone in stage_bones:
            from_bone = from_object.data.bones[bone.name]
            to_bone = to_object.data.bones[bone.name]
            if addons['BLEND-ArmatureControlBones']:
                Set_RNA_Properties(from_bone.ACB, to_bone.ACB)
            if addons['BLEND-ArmatureRiggingLibrary']:
                Set_RNA_Properties(from_bone.ARL, to_bone.ARL)
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
            Set_RNA_Properties(from_group, to_group)
    # if we want to push our selfies...
    if stage_from.Data.Push_library:
        to_object.pose_library = from_object.pose_library
    # and finally if we want to slap in some style...
    if stage_from.Data.Push_display:
        dis_props = ['display_type', 'show_names', 'show_bone_custom_shapes', 'show_axes', 'show_group_colors']
        Set_RNA_Properties(from_data, to_data, override=dis_props)

def Push_Object(master, stage_from, stage_to):
    # get the objects and data we need...
    from_object = bpy.data.objects[stage_from.Armature]
    to_object = bpy.data.objects[stage_to.Armature]
    # maybe do some orientation...
    if stage_from.Object.Push_transform:
        t_props = ['location', 'rotation_euler', 'rotation_quaternion', 'rotation_axis_angle', 'rotation_mode', 'scale', 
            'delta_location', 'delta_rotation_quaternion', 'delta_rotation_euler', 'delta_scale']
        Set_RNA_Properties(from_object, to_object, override=t_props)
    # if there are more of those pesky relatives...
    if stage_from.Object.Push_relations:
        r_props = ['parent', 'parent_type', 'parent_bone', 'track_axis', 'up_axis', 'pass_index']
        Set_RNA_Properties(from_object, to_object, override=r_props)
    # and if there be instances...
    if stage_from.Object.Push_instancing:
        i_props = ['instance_type', 'show_instancer_for_viewport', 'show_instancer_for_render', 
            'use_instance_vertices_rotation', 'use_instance_faces_scale', 'instance_faces_scale']
        Set_RNA_Properties(from_object, to_object, override=i_props)
    # also might even gussy up...
    if stage_from.Object.Push_display:
        d_props = ['show_name', 'show_axis', 'show_in_front', 'show_axis', 'display_type', 'show_bounds', 'display_bounds_type']
        Set_RNA_Properties(from_object, to_object, override=d_props)

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
                print("Nope... you have some how killed the source armature... *sighs* i knew i should of made you a backup...")

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
    master_name = master.data.name[:]
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
    stage_props.Is_master = True
    stage_props.Is_stage = False
    stage_props.Last = master_props.Last
    stage_props.Stage = master_props.Stage
    # set all the stage settings...
    for m_stage in master_props.Stages:
        n_stage = stage_props.Stages.add()
        # set is pushing true so we don't fire the update functions...
        n_stage.Is_pushing = True
        Set_RNA_Properties(m_stage, n_stage, exclude=["Is_pushing"])
        Set_RNA_Properties(m_stage.Data, n_stage.Data)
        Set_RNA_Properties(m_stage.Object, n_stage.Object)
        # iterate on stage bones after clearing the new stages bone collection...
        n_stage.Bones.clear()
        for m_bone in m_stage.Bones:
            n_bone = n_stage.Bones.add()
            Set_RNA_Properties(m_bone, n_bone)
            Set_RNA_Properties(m_bone.Edit, n_bone.Edit)
            Set_RNA_Properties(m_bone.Pose, n_bone.Pose)
        # set is pushing to false after the stage has been set...
        n_stage.Is_pushing = False
    # assign the copied data to the copied object...
    stage_copy.data = stage_data
    # move all the children from the master to the copy...
    for child in master.children:
        child.parent = stage_copy    
    # remove the master object and data...
    bpy.data.objects.remove(master)
    bpy.data.armatures.remove(master_data)
    # rename the copied object and data to the masters name...
    stage_copy.name = master_name
    stage_copy.data.name = master_name
    # selct it and set it to active...
    bpy.context.view_layer.objects.active = stage_copy
    stage_copy.select_set(True)
    # get certain other BLEND addons if they are installed...
    addons = Get_Installed_Addons()
    if addons['BLEND-ArmatureControlBones']:
        if any(b.ACB.Type != 'NONE' for b in stage_copy.data.bones):
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
    # set is master false and is stage true... (so the stage will get cleaned up if the master gets deleted)
    master_data.AES.Is_master = False
    master_data.AES.Is_stage = True
    master_data.AES.Stages.clear()
    # assign the data...
    master_copy.data = master_data
    master_copy.use_fake_user, master_copy.data.use_fake_user = True, True
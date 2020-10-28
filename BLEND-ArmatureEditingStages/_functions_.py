import bpy
import json

from . import _properties_

def Get_Stage_Parenting(stages, stage, recursive=False):
    if recursive:
        parents, parent = [], stage.Parent
        while parent != "":
            next_stage = stages[parent]
            parents.append(next_stage)
            parent = next_stage.Parent
        return parents
    else:
        return None if stage.Parent == "" else stages[stage.Parent] 

def Get_Stage_Children(stages, stage, recursive=False):
    children = [st for st in stages if st.Parent == stage.name]
    # if we are getting recursive children...
    if recursive:
        # set off a while loop to gather all the children...
        next_children = [st for st in stages if st.Parent == stage.name]
        while len(next_children) > 0:
            child = next_children.pop()
            for next_child in [st for st in stages if st.Parent == child.name]:
                children.append(next_child)
    # otherwise just return the immediate children...
    return children

def Set_Pointer_String(pointer):
    if pointer == None:
        return None
    else:
        # print(pointer.rna_type.name)
        path = _properties_.Pathing[pointer.rna_type.name]
        return "{p_path}['{p_name}']".format(p_name=pointer.name, p_path=path)

def Get_Stage_Bones(stage, bones):
    # add in any new bone entries...
    for add_bone in [b for b in bones if b.name not in stage.Bones]:
        add = stage.Bones.add()
        add.name = add_bone.name
    # remove any bones that no longer exist...
    for rem_bone in [sb for sb in stage.Bones if sb.name not in bones]:
        stage.Bones.remove(stage.Bones.find(rem_bone.name))

def Get_Stage_Bone_Hierarchy(stage, bones):
    # declare a couple of lists...
    hierarchy, parentless = [], [b for b in bones if b.parent == None]
    # iterate on bones without parents...
    for parent in parentless:
        # appending their names first...
        hierarchy.append(stage.Bones[parent.name])
        # then appending each of their recursive childrens names...
        for child in parent.children_recursive:
            hierarchy.append(stage.Bones[child.name])
    return hierarchy

def Get_Installed_Addons():
    # just a function that returns a dictionary of my own add-ons if they are installed...
    addons = bpy.context.preferences.addons.keys()
    installed = {'BLEND-ArmatureControlBones' : True if 'BLEND-ArmatureControlBones' in addons else False, 
        'BLEND-ArmatureRiggingLibrary' : True if 'BLEND-ArmatureRiggingLibrary' in addons else False}
    return installed

def Get_Property(source, identifier, type):
    # if we have int, float or bool it could be a vector...
    if type in ['INT', 'FLOAT', 'BOOLEAN']:
        try:
            # if it's a matrix, break it down into a list of lists...
            if identifier.startswith('matrix') or identifier.endswith('matrix'):
                value = [vec[:] for vec in getattr(source, identifier)]
            else:
                # otherwise try to comprehend it like a vector...
                value = getattr(source, identifier)[:]
        except:
            # if we can't then get it normally...
            value = getattr(source, identifier)
    # if it's a pointer then we need to format a data path...
    elif type == 'POINTER':
        value = Set_Pointer_String(getattr(source, identifier))
    # if it's a collection we may need to iterate again so just declare a dictionary...
    elif type == 'COLLECTION':
        # can we add all names and information here?
        value = {}
    else:
        value = getattr(source, identifier)
    # then return the value to be added...
    return value

def Get_Properties(source, props=[]):
    dictionary = {}
    # use the user defined property strings if they exists, if not use the source datas rna properties...
    identifiers = props if props else [p.identifier for p in source.bl_rna.properties]
    # iterate on the identifiers...
    for identifier in identifiers:
        # getting the properties...
        prop = source.bl_rna.properties[identifier]
        # if the property is not read only...
        if not prop.is_readonly:
            # format the value of it and add it to the dictionary we are going to return...
            dictionary[prop.identifier] = Get_Property(source, identifier, prop.type)
    return dictionary
            
def Set_Property(target, dictionary, identifier, type):
    has_changed = True if Get_Property(target, identifier, type) != dictionary[identifier] else False
    if has_changed:
        # if it's a pointer...
        if target.bl_rna.properties[identifier].type == 'POINTER':
            try:
                # then try to execute setting the formatted data path...
                exec("target." + identifier + " = " + dictionary[identifier])
            except:
                # if we can't execute the data path then set it to None...
                setattr(target, identifier, None)
        # if it's a collection...
        elif target.bl_rna.properties[identifier].type == 'COLLECTION':
            # just skip it for now... (i can't think of a clever way to handle this at the moment)
            pass
        else:
            # we could set these up to be handled but for now i'm just leaving them alone...
            if not identifier.startswith("matrix") and not identifier.startswith("dimensions"):
                # otherwise we should be able to just set the property normally...
                setattr(target, identifier, dictionary[identifier])
    return has_changed

def Set_Properties(target, dictionary):
    # declare changes list and get all the identifiers that exist in the dictionary data...
    changes, identifiers = [], [p.identifier for p in target.bl_rna.properties if p.identifier in dictionary]
    for identifier in identifiers:
        prop = target.bl_rna.properties[identifier]
        has_changed = Set_Property(target, dictionary, identifier, prop.type)
        if has_changed:
            changes.append(has_changed)
    return True if len(changes) > 0 else False

def Get_Rigging_Library_Properties(armature):
    rigging = {}
    # we need to gather all the bone properties...
    rigging['Bones'] = {bb.name : Get_Properties(bb.ARL, props=['Type', 'Subtype', 'Edit_matrix']) for bb in armature.data.bones}
    # getting the chains is a little more fiddley as they have collection properties...
    rigging['Chains'] = {}
    for ci, chain in enumerate(armature.ARL.Chains):
        # get all the properties that aren't pointers...
        ch_props = Get_Properties(chain, props=[p.identifier for p in chain.bl_rna.properties if p.type != 'POINTER'])
        # then get the pole and spline pointer settings...
        ch_props['Pole'] = Get_Properties(chain.Pole)
        ch_props['Spline'] = Get_Properties(chain.Spline)
        # then get all the collection properties...
        ch_props['Bones'] = {cb.name : Get_Properties(cb) for cb in chain.Bones}
        ch_props['Targets'] = {ct.name : Get_Properties(ct) for ct in chain.Targets}
        ch_props['Forward'] = {cf.name : Get_Properties(cf) for cf in chain.Forward}
        # and add them to the rigging library entry in the add-ons dictionary by the chain index...
        rigging['Chains'][ci] = ch_props
    # get all the twist properties...
    rigging['Twists'] = {ti : Get_Properties(twist) for ti, twist in enumerate(armature.ARL.Twists)}
    # and all the pivot properties...
    rigging['Pivots'] = {pi : Get_Properties(pivot) for pi, pivot in enumerate(armature.ARL.Pivots)}
    # aaaaand all the floor properties...
    rigging['Floors'] = {fi : Get_Properties(floor) for fi, floor in enumerate(armature.ARL.Floors)}
    return rigging

def Get_Rigging_Entry_Exists(armature, props, type):
    # get a the essential bone names depending on rigging type...
    if type == 'CHAIN':
        names = [ck for ck in props['Bones'].keys()] + [tv['Source'] for tv in props['Targets'].values()] + [tv['Pivot'] for tv in props['Targets'].values()] + [props['Parent']]
    elif type == 'TWIST':
        names = [props['name'], props['Target'], props['Parent']]
    elif type == 'PIVOT':
        names = [props['Source'], props['Parent']]
    elif type == 'FLOOR':
        names = [props['Source']]
    # this rigging can exist if all the valid bone names exist in the armature...
    exists = False if any(name not in armature.data.bones for name in [n for n in names if n != ""]) else True
    # also need to know if this bone has inherited any changes and needs updating...
    changed = True if exists and any(armature.data.bones[name].ARL.Has_changes for name in names if name in armature.data.bones) else False
    return exists, changed

def Set_Rigging_Entry_Collections(coll, props, changes):
    # for each name, property in the collection...
    for cn, cps in props.items():
        # if it exists use it...
        if cn in coll:
            cb = coll[cn]
        else:
            # otherwise add a new one...
            cb = coll.add()
        changed = Set_Properties(cb, cps)
        # if any properties have changed...
        if changed:
            # append to the changes list...
            changes.append(changed)

def Set_Rigging_Entries(armature, coll, rigging, flavour, del_list):
    # for each rigging index, properties in the given rigging...
    for index, props in rigging.items():
        # check if it exists and has edit mode changes...
        exists, changed = Get_Rigging_Entry_Exists(armature, props, flavour)
        # if the rigging can exist...
        if exists:
            # use an existing entry if there is one...
            if int(index) < len(coll):
                entry = coll[int(index)]
            else:
                # otherwise add a new one...
                entry = coll.add()
            # set is adding false so we don't trigger any update functions...
            entry.Is_adding = True
            # if this a chain entry we need to set some collection and pointer properties...
            if flavour == 'CHAIN':
                # set the chain, pole and spline properties...
                ch_changed = Set_Properties(entry, {key : val for key, val in props.items() if key not in ['Pole', 'Spline', 'Bones', 'Targets', 'Forward', 'Is_adding']})
                cp_changed = Set_Properties(entry.Pole, props['Pole'])
                cs_changed = Set_Properties(entry.Spline, props['Spline'])
                # gather any changes so far...
                changes = [cng for cng in [changed, ch_changed, cp_changed, cs_changed] if cng]
                # iterate over the bones, targets and forwards setting properties and appending changes...
                Set_Rigging_Entry_Collections(entry.Bones, props['Bones'], changes)
                Set_Rigging_Entry_Collections(entry.Targets, props['Targets'], changes)
                Set_Rigging_Entry_Collections(entry.Forward, props['Forward'], changes)
                # and set the changed bool by the length of the accumulated changes...
                entry_changed = True if len(changes) > 0 else False
            else:
                # set the riggin entry properties... (excluding the is adding bool)
                entry_changed = Set_Properties(entry, {key : val for key, val in props.items() if key != 'Is_adding'})
            # then return is adding so the user can edit it...
            entry.Is_adding = False
            # if there are changes we need to fire the specific update operator...
            if entry_changed or changed:
                if flavour == 'CHAIN':
                    armature.ARL.Chain = int(index)
                    bpy.ops.jk.chain_set(Action='UPDATE')
                elif flavour == 'TWIST':
                    armature.ARL.Twist = int(index)
                    bpy.ops.jk.twist_set(Action='UPDATE')
                elif flavour == 'PIVOT':
                    armature.ARL.Pivot = int(index)
                    bpy.ops.jk.pivot_set(Action='UPDATE')
                elif flavour == 'FLOOR':
                    armature.ARL.Floor = int(index)
                    bpy.ops.jk.floor_set(Action='UPDATE')
        # else append the index if the rigging can't exist and there is an entry for it...
        elif int(index) < len(coll):
            del_list.append(coll[int(index)])
    # then get rid of any entries that need removing...
    for del_index in reversed(sorted(del_list)):
        coll.remove(del_index)

def Set_Rigging_Library_Properties(armature, rigging):
    # make sure everything is up to date...
    bpy.context.view_layer.update()
    # get the current rigging...
    chains, twists, pivots, floors = armature.ARL.Chains, armature.ARL.Twists, armature.ARL.Pivots, armature.ARL.Floors
    # and all the rigging indices that will need to be removed...
    del_chains, del_twists = [i for i in range(len(chains)) if i >= len(rigging['Chains'])], [i for i in range(len(twists)) if i >= len(rigging['Twists'])]
    del_pivots, del_floors = [i for i in range(len(pivots)) if i >= len(rigging['Pivots'])], [i for i in range(len(floors)) if i >= len(rigging['Floors'])]
    # then we can set the chains, twists, pivots and floors...
    Set_Rigging_Entries(armature, chains, rigging['Chains'], 'CHAIN', del_chains)
    Set_Rigging_Entries(armature, twists, rigging['Twists'], 'TWIST', del_twists)
    Set_Rigging_Entries(armature, pivots, rigging['Pivots'], 'PIVOT', del_pivots)
    Set_Rigging_Entries(armature, floors, rigging['Floors'], 'FLOOR', del_floors)
    # then finally iterate on all the bone properties in the armature... 
    for b_name, b_props in rigging['Bones'].items():
        if b_name in armature.data.bones:
            for identifier, value in b_props.items():
                if identifier.endswith('matrix'):
                    # we don't set the last matrix these because it sets itself?
                    continue
                    #setattr(armature.data.bones[b_name].ARL, identifier, [f for v in value for f in v])
                else:
                    setattr(armature.data.bones[b_name].ARL, identifier, value)

def Get_Stage_Properties(armature, stage):
    # get the object properties... (can just save them all?)
    stage.Object_json = json.dumps(Get_Properties(armature))
    # get the data properties...
    data_props = Get_Properties(armature.data)
    data_props.update(Get_Properties(armature.pose))
    # adding in all the bone groups...
    data_props['bone_groups'] = {}
    for grp in armature.pose.bone_groups:
        data_props['bone_groups'][grp.name] = Get_Properties(grp)
    stage.Data_json = json.dumps(data_props)
    # then we need to update the bones...
    Get_Stage_Bones(stage, armature.data.bones)
    
    # gather all the pose bone properties...
    for pb in armature.pose.bones:
        pose_props = Get_Properties(pb)
        # but constraints need to be accumulated...
        pose_props['constraints'] = {}
        for con in pb.constraints:
            pose_props['constraints'][con.name] = Get_Properties(con)
            pose_props['constraints'][con.name]['type'] = con.type
        # and drivers are even more fiddly...
        pose_props['drivers'] = {}
        if armature.animation_data:
            for drv in [d for d in armature.animation_data.drivers if ('"%s"' % pb.name) in d.data_path]:
                pose_props['drivers'][drv.data_path] = Get_Properties(drv)
        # but that's all the pose bone data dumped to its dictionary...
        stage.Bones[pb.name].Pose_json = json.dumps(pose_props)
    
    bpy.ops.object.mode_set(mode='EDIT')
    # edit bones should be saved in order of hierarchy...
    parentless = [eb for eb in armature.data.edit_bones if eb.parent == None]
    for peb in parentless:
        peb_props = Get_Properties(peb)
        stage.Bones[peb.name].Edit_json = json.dumps(peb_props)
        for ceb in peb.children_recursive:
            ceb_props = Get_Properties(ceb)
            stage.Bones[ceb.name].Edit_json = json.dumps(ceb_props)

    # if we have any other BLEND add-ons installed we need to do some specific things...
    addons = Get_Installed_Addons()
    if any(val for val in addons.values()):
        addon_props = {}
        # if armature control bones is installed...
        if addons['BLEND-ArmatureControlBones']:
            # get all the bone types of this stage...
            addon_props['BLEND-ArmatureControlBones'] = {bb.name : bb.ACB.Type for bb in armature.data.bones}
        # if armature rigging library is installed...
        if addons['BLEND-ArmatureRiggingLibrary']:
            # we need to do some fiddly business so i made a function for it...
            addon_props['BLEND-ArmatureRiggingLibrary'] = Get_Rigging_Library_Properties(armature)
        # then dump all the add-on properties into its json string...
        stage.Addon_json = json.dumps(addon_props)
        #print("GET ADDON PROPS", json.loads(stage.Addon_json))

    bpy.ops.object.mode_set(mode='OBJECT')

def Set_Stage_Properties(armature, stage):
    # get all the property dictionaries...
    obj, data = json.loads(stage.Object_json), json.loads(stage.Data_json)
    # just set the object all the object properties...
    Set_Properties(armature, obj)
    # and set the data and pose properties we can...
    Set_Properties(armature.data, data)
    Set_Properties(armature.pose, data)
    # need to do an iteration on bone groups...
    for bg_name, bg_props in data['bone_groups'].items():
        # to add in bone groups that need adding...
        if bg_name in armature.pose.bone_groups:
            b_group = armature.pose.bone_groups[bg_name]
        else:
            b_group = armature.pose.bone_groups.new(bg_name)
        # and set their properties...
        Set_Properties(b_group, bg_props)
    # then iterate on bone groups again removing any that should be removed...
    remove_groups = [bg for bg in armature.pose.bone_groups if bg.name not in data['bone_groups']]
    for r_group in remove_groups:
        armature.pose.bone_groups.remove(r_group)
    
    bpy.ops.object.mode_set(mode='EDIT')
    # then we need to iterate on edit bones...
    for sb in stage.Bones:
        edit = json.loads(sb.Edit_json)
        # to add bones that need adding...
        if sb.name in armature.data.edit_bones:
            e_bone = armature.data.edit_bones[sb.name]
        else:
            e_bone = armature.data.edit_bones.new(sb.name)
        # and set the properties...
        Set_Properties(e_bone, edit)
        #print("SET EDIT BONE", edit)
    # then we need to iterate on edit bones again to remove bones that need removing...
    remove_bones = [eb for eb in armature.data.edit_bones if eb.name not in stage.Bones]
    for re_bone in remove_bones:
        armature.data.edit_bones.remove(re_bone)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    # if we have any other BLEND add-ons installed we need to do some specific things...
    installed = Get_Installed_Addons()
    if any(val for val in installed.values()):
        # print("SET ADDON PROPS", stage.Addon_json)
        addons = json.loads(stage.Addon_json)
        # if armature control bones is installed...
        if installed['BLEND-ArmatureControlBones']:
            # set all the bone types back up...
            for b_name, b_type in addons['BLEND-ArmatureControlBones'].items():
                if b_name in armature.data.bones:
                    armature.data.bones[b_name].ACB.Type = b_type
        # if armature rigging library is installed...
        if installed['BLEND-ArmatureRiggingLibrary']:
            # this gets a bit long so i made a setting function for less clutter...
            Set_Rigging_Library_Properties(armature, addons['BLEND-ArmatureRiggingLibrary'])

    bpy.ops.object.mode_set(mode='POSE')
    # then iterate on pose bones and set all their constraints, drivers and things back up...
    for sb in stage.Bones:
        pose = json.loads(sb.Pose_json)
        p_bone = armature.pose.bones[sb.name]
        Set_Properties(p_bone, pose)
        # remove constraints that we need to remove...
        remove_cons = [co for co in p_bone.constraints if co.name not in pose['constraints']]
        for r_con in remove_cons:
            p_bone.constraints.remove(r_con)
        # then add all the constraints that need adding...
        for con_name, con_props in pose['constraints'].items():
            if con_name not in p_bone.constraints:
                con = p_bone.constraints.new(con_props['type'])
            else:
                con = p_bone.constraints[con_name]
            # and set their properties...
            Set_Properties(con, con_props)
    
            #### set drivers...

def Pull_Stage_Inheritance(armature, stage_from, stage_to):
    # if we are inheriting object properties...
    if stage_to.Object_inherit:
        # get the object dictionaries...
        obj_from, obj_to = json.loads(stage_from.Object_json), json.loads(stage_to.Object_json)
        # iterate on the property groupings that should inherit...
        for group in [grp for grp in stage_to.Object_groups if grp.Inherit]:
            # and on the properties that should be inherited... (and even need to be changed)
            for inherit in [iht for iht in group.Inheritance if iht.Inherit and obj_to[iht.name] != obj_from[iht.name]]:
                # to update all the dictionary settings...
                obj_to[inherit.name] = obj_from[inherit.name]
        # then dump the dictionary back into it's string...
        stage_to.Object_json = json.dumps(obj_to)
    
    # if we are inheriting data properties...
    if stage_to.Data_inherit:
        # get the data dictionaries...
        dat_from, dat_to = json.loads(stage_from.Data_json), json.loads(stage_to.Data_json)
        # iterate on the property groupings that should inherit...
        for group in [grp for grp in stage_to.Data_groups if grp.Inherit]:
            # and on the properties that should be inherited... (and even need to be changed)
            for inherit in [iht for iht in group.Inheritance if iht.Inherit and dat_to[iht.name] != dat_from[iht.name]]:
                # to update all the dictionary settings...
                dat_to[inherit.name] = dat_from[inherit.name]
        # then dump the dictionary back into it's string...
        stage_to.Data_json = json.dumps(dat_to)
    
    # if we are inheriting per bone properties...
    if stage_to.Bones_inherit:
        # iterate on bones that exist in the from stage...
        for bone_to in [sb for sb in stage_to.Bones if sb.name in stage_from.Bones]:
            bone_from = stage_from.Bones[bone_to.name]
            
            # if we are inheriting edit bone properties...
            if bone_to.Edit_inherit:
                # get the edit bone dictionaries...
                eb_from, eb_to = json.loads(bone_from.Edit_json), json.loads(bone_to.Edit_json)
                # iterate on the property groupings that should inherit...
                for group in [grp for grp in bone_to.Edit_groups if grp.Inherit]:
                    # and on the properties that should be inherited... (and even need to be changed)
                    for inherit in [iht for iht in group.Inheritance if iht.Inherit and eb_to[iht.name] != eb_from[iht.name]]:
                        # to update all the dictionary settings...
                        eb_to[inherit.name] = eb_from[inherit.name]
                # then dump the dictionary back into it's string...
                bone_to.Edit_json = json.dumps(eb_to)
            
            # if we are inheriting pose bone properties...
            if bone_to.Pose_inherit:
                # get the pose bone dictionary...
                pb_from, pb_to = json.loads(bone_from.Pose_json), json.loads(bone_to.Pose_json)
                # iterate on the property groupings that should inherit...
                for group in [grp for grp in bone_to.Pose_groups if grp.Inherit]:
                    # and on the properties that should be inherited... (and even need to be changed)
                    for inherit in [iht for iht in group.Inheritance if iht.Inherit and pb_to[iht.name] != pb_from[iht.name]]:
                        # to update all the dictionary settings...
                        pb_to[inherit.name] = pb_from[inherit.name]
                # then dump the dictionary back into it's string...
                bone_to.Pose_json = json.dumps(pb_to)
        # then get rid of any entries that shouldn't be there any more... (if they inherit and don't exist they should be removed?) 
        for check in [sb for sb in stage_to.Bones if sb.name not in stage_from.Bones]:    
            if check.Edit_inherit or check.Pose_inherit:
                stage_to.Bones.remove(stage_to.Bones.find(bone_to.name))
                    
def Pull_Hierarchy_Inheritance(armature, stage):
    # get our stages...
    stages = armature.data.AES.Stages
    # if the stage has any parents, get them...
    if stage.Parent != "":
        parents = Get_Stage_Parenting(stages, stage, recursive=True)
        # and iterate on the recursive children of last parent... 
        for child in Get_Stage_Children(stages, parents[-1], recursive=True):
            Pull_Stage_Inheritance(armature, stages[child.Parent], child)
    else:
        # else iterate on the recursive children of this stage... 
        for child in Get_Stage_Children(stages, stage, recursive=True):
            Pull_Stage_Inheritance(armature, stages[child.Parent], child)






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
        exec("target." + rna_id + " = source." + rna_id)
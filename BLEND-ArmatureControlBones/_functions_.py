import bpy

def Get_Bone_Controls(armature, sb_name):
    sp_bone = armature.pose.bones[sb_name]
    copy_trans = sp_bone.constraints["MECHANISM - Copy Transform"]
    mb_name = copy_trans.subtarget
    mb_bone = armature.pose.bones[mb_name]
    cb_name = mb_bone.parent.name
    return {'MECH' : mb_name, 'CONT' : cb_name}

def Get_Control_Bones(armature):
    controls = {sb.name : Get_Bone_Controls(armature, sb.name) for sb in armature.data.bones if sb.ACB.Type == 'SOURCE'}
    return controls

def Get_Selected_Bones(armature):
    if armature.mode == 'EDIT':
        bones = [armature.data.bones[eb.name] for eb in bpy.context.selected_bones]
    elif armature.mode == 'POSE':
        bones = [armature.data.bones[pb.name] for pb in bpy.context.selected_pose_bones]
    else:
        bones = [b for b in armature.data.bones if b.select]
    return bones

def Set_Selected_Bones(data, controls):
    obj = bpy.context.object
    bones = data.edit_bones if obj.mode == 'EDIT' and obj.type == 'ARMATURE' else data.bones
    selected = [b.name for b in data.bones if b.select]
    for sb_name, cb_names in controls.items():
        sb, cb = bones[sb_name], bones[cb_names['CONT']]
        if obj.mode == 'EDIT':
            if cb_names['CONT'] in selected:
                sb.select, sb.select_head, sb.select_tail = True, True, True
                cb.select, cb.select_head, cb.select_tail = False, False, False
            if cb == bones.active:
                bones.active = sb
        else:
            if sb_name in selected:
                cb.select = True
                sb.select = False
            if sb == bones.active:
                bones.active = cb

def Get_Control_Parent(armature, controls, bone):
    parent = None
    if bone.parent != None:
        if bone.parent.name in controls:
            p_name = controls[bone.parent.name]['CONT']
            parent = armature.data.edit_bones[p_name]
        else:
            parent = armature.data.edit_bones[bone.parent.name]
    return parent

def Set_Hidden_Bones(data, sb_hide=True, mb_hide=True, cb_hide=True):
    obj = bpy.context.object
    bones = data.edit_bones if obj.mode == 'EDIT' and obj.type == 'ARMATURE' else data.bones
    for b in data.bones:
        if b.ACB.Type != 'NONE':
            bone = bones[b.name]
            bone.hide = sb_hide if b.ACB.Type == 'SOURCE' else mb_hide if b.ACB.Type == 'MECH' else cb_hide

def Set_Control_Location(armature, sb_name, cb_names):
    se_bone = armature.data.edit_bones[sb_name]
    me_bone = armature.data.edit_bones[cb_names['MECH']]
    ce_bone = armature.data.edit_bones[cb_names['CONT']]
    # if the control bone doesn't have the same head location as the source...
    if ce_bone.head != se_bone.head:
        # get the length and y direction vector of the control bone...
        ce_length, ce_vec = ce_bone.length, ce_bone.y_axis
        # and set it's head and it's tail relative to the source bone...
        ce_bone.head, ce_bone.tail = se_bone.head, se_bone.head + (ce_vec * ce_length)
    # if the mech bone isn't oriented to the source...
    if me_bone.head != se_bone.head or me_bone.tail != se_bone.tail or me_bone.roll != se_bone.roll:
        # then orient the mechanism bone to the source bone...
        me_bone.head, me_bone.tail, me_bone.roll = se_bone.head, se_bone.tail, se_bone.roll

def Subscribe_Mode_To(obj, callback):
    # get the data path to sub and assign it to the msgbus....
    subscribe_to = obj.path_resolve('mode', False)
    bpy.msgbus.subscribe_rna(key=subscribe_to, owner=obj, args=(obj, 'mode'), notify=callback, options={"PERSISTENT"})

def Set_Meshes(armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    # iterate on all meshes with armature modifiers targeting the armature...
    for mesh in [o for o in bpy.data.objects if o.type == 'MESH' and any(mod.type == 'ARMATURE' and mod.object == armature for mod in o.modifiers)]:
        # if that meshes name is not in the subscribed meshes...
        if mesh.name not in prefs.Meshes:
            # sub and add it...
            Subscribe_Mode_To(mesh, Mesh_Mode_Callback)
            m = prefs.Meshes.add()
            m.name, m.Armature = mesh.name, armature.name
    # then iterate over all subbed meshes...
    for m in prefs.Meshes:
        # getting rid of any that don't exist anymore...
        if m.name not in bpy.data.objects:
            mi = prefs.Meshes.find(m.name)
            prefs.Meshes.remove(mi)
    #print(obj.mode, "ACB")
    
def Armature_Mode_Callback(armature, data):
    if armature in {o : o.name for o in bpy.data.objects}:
        ACB = armature.data.ACB
        # if we are auto hiding...
        if ACB.Auto_hide:
            # check the armature has controls...
            if any(b.ACB.Type != 'NONE' for b in armature.data.bones):
                # that's gone into edit mode...
                if armature.mode == 'EDIT':
                    # show the source bones and hide the others...
                    Set_Hidden_Bones(armature.data, sb_hide=False)
                    ACB.Hide_source, ACB.Hide_mech, ACB.Hide_cont = False, True, True
                    Set_Selected_Bones(armature.data, Get_Control_Bones(armature))
                else:
                    # otherwise show the controls and the others...
                    Set_Hidden_Bones(armature.data, cb_hide=False)
                    ACB.Hide_source, ACB.Hide_mech, ACB.Hide_cont = True, True, False
                    Set_Selected_Bones(armature.data, Get_Control_Bones(armature))
        else:
            # otherwise just set hidden by user...
            Set_Hidden_Bones(armature.data, sb_hide=ACB.Hide_source, mb_hide=ACB.Hide_mech, cb_hide=ACB.Hide_cont)
        # if we want to auto sync bone locations when leaving edit mode...
        if ACB.Auto_sync and armature.mode != 'EDIT':
            ACB.Auto_sync = False
            # get the controls and go to edit mode...
            controls = Get_Control_Bones(armature)
            last_mode = armature.mode
            bpy.ops.object.mode_set(mode='EDIT')
            # for each control set the location of controls and mechanisms...
            for sb_name, cb_names in controls.items():
                Set_Control_Location(armature, sb_name, cb_names)
            # then hop back out of edit mode...
            bpy.ops.object.mode_set(mode=last_mode)
            ACB.Auto_sync = True
        # putting this here for now to try and avoid a persistant timer to check it...
        Set_Meshes(armature)
        # so this should fire whenever we add controls and change the armatures mode keeping meshes up to date?

def Mesh_Mode_Callback(mesh, data):
    # comprehend a dictionary of the armatures we might need to edit and iterate on it...
    armatures = {mod.object : mod.object.data.ACB for mod in mesh.modifiers if mod.type == 'ARMATURE'}
    for armature, ACB in armatures.items():
        # check the armature has controls and wants to auto hide or sync locations...
        if any(b.ACB.Type != 'NONE' for b in armature.data.bones) and ACB.Auto_hide:
            # then if we are going into weight paint mode...
            if mesh.mode == 'WEIGHT_PAINT':
                # show the source bones and hide the others...
                Set_Hidden_Bones(armature.data, sb_hide=False)
                ACB.Hide_source, ACB.Hide_mech, ACB.Hide_cont = False, True, True
                Set_Selected_Bones(armature.data, Get_Control_Bones(armature))
            else:
                # otherwise show the controls and hide the others...
                Set_Hidden_Bones(armature.data, cb_hide=False)
                ACB.Hide_source, ACB.Hide_mech, ACB.Hide_cont = True, True, False
                Set_Selected_Bones(armature.data, Get_Control_Bones(armature))

def Set_Automatic_Orientation(armature, cb_name):
    cd_bone = armature.data.bones[cb_name]
    ce_bone = armature.data.edit_bones[cb_name]
    children = [armature.data.edit_bones[c.name] for c in cd_bone.children if c.ACB.Type != 'MECH']
    has_target = False
    # if a bone has only one child...
    if len(children) == 1:
        child = children[0]
        # and as long as the childs head is not equal to the bones head...
        if child.head != ce_bone.head:
            # it's tail should probably point to it...
            ce_bone.tail = child.head
            has_target = True
    # if a bone has multiple children
    elif len(children) > 1:
        # iterate over the children...
        for child in children:
            # checking for these most likely places we will want to target...
            if any(string in child.name.upper() for string in ["NECK", "SPINE", "LOWER", "ELBOW", "KNEE", "CALF", "HAND", "WRIST", "FOOT", "ANKLE"]):
                # as long as the childs head is not equal to the bones head...
                if child.head != ce_bone.head:
                    # take the first match and break...
                    ce_bone.tail = child.head
                    has_target = True
                    break  
    # if we couldn't find a suitable child target...
    if not has_target:
        # but the bone has a parent, we can align to it...
        if ce_bone.parent != None:
            ce_bone.align_orientation(ce_bone.parent)
        else:
            print("Automatic Orientation: Could not find anywhere to align", ce_bone.name, "so you are on your own with it...")  

def Add_Bone_Controls(armature, bone, parent):
    #ACB = armature.data.ACB
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    # get the edit bone...
    se_bone = armature.data.edit_bones[bone.name]
    # add the control and mechanism bones with their prefixes...
    me_bone = armature.data.edit_bones.new(prefs.Mech_prefix + bone.name)
    ce_bone = armature.data.edit_bones.new(prefs.Cont_prefix + bone.name)
    # set their transforms...
    ce_bone.head, ce_bone.tail, ce_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    me_bone.head, me_bone.tail, me_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    # niether bone should deform... (if you want them to then you're doing this wrong lol)
    ce_bone.use_deform, me_bone.use_deform = False, False
    # parent control bone to input parent and parent mechanism bone to the control bone...
    ce_bone.parent, me_bone.parent = parent, ce_bone
    # return the name of the control...
    return {'MECH' : prefs.Mech_prefix + bone.name, 'CONT' : prefs.Cont_prefix + bone.name}

def Remove_Bone_Controls(armature, sb_name, cb_names):
    se_bone = armature.data.edit_bones[sb_name]
    se_bone.hide = False
    # we need to kill the mechanism and control bones...
    me_bone = armature.data.edit_bones[cb_names['MECH']]
    ce_bone = armature.data.edit_bones[cb_names['CONT']]
    armature.data.edit_bones.remove(me_bone)
    armature.data.edit_bones.remove(ce_bone)
    # make sure the source pose bone isn't hidden and kill its constraint and type...
    bpy.ops.object.mode_set(mode='POSE')
    sp_bone = armature.pose.bones[sb_name]
    copy_trans = sp_bone.constraints["MECHANISM - Copy Transform"]
    sp_bone.constraints.remove(copy_trans)
    sp_bone.bone.hide = False
    sp_bone.bone.ACB.Type = 'NONE'
    bpy.ops.object.mode_set(mode='EDIT')
    

    

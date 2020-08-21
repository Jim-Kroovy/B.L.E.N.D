import bpy

def Add_To_Edit_Menu(self, context):
    row = self.layout.row()
    row.operator("jk.edit_control_bones", icon='GROUP_BONE').Edit = 'ADD'

def Add_to_Pose_Menu(self, context):
    self.layout.operator("jk.edit_control_bones", icon='GROUP_BONE').Edit = 'ADD'

def Get_Bone_Controls(armature, sb_name):
    sp_bone = armature.pose.bones[sb_name]
    copy_trans = sp_bone.constraints["MECHANISM - Copy Transform"]
    mb_name = copy_trans.subtarget
    mb_bone = armature.pose.bones[mb_name]
    cb_name = mb_bone.parent.name
    return {'MECHANISM' : mb_name, 'CONTROL' : cb_name}

def Get_Control_Bones(armature):
    ACB = armature.data.ACB
    #last_mode = armature.mode
    #if last_mode != 'POSE':
        #bpy.ops.object.mode_set(mode='POSE')
    sources = {sb.name : Get_Bone_Controls(armature, sb.name) for sb in armature.data.bones if sb.ACB.Type == 'SOURCE'}
    mechs = {cb_names['MECHANISM'] : {'SOURCE' : name, 'CONTROL' : cb_names['CONTROL']} for name, cb_names in sources.items()}
    conts = {cb_names['CONTROL'] : {'SOURCE' : name, 'MECHANISM' : cb_names['MECHANISM']} for name, cb_names in sources.items()}
    #if armature.mode != last_mode:
        #bpy.ops.object.mode_set(mode=last_mode)
    return {'SOURCE' : sources, 'MECHANISM' : mechs, 'CONTROL' : conts}

def Get_Control_Parent(armature, controls, bone):
    parent = None
    if bone.parent != None:
        if bone.parent.name in controls:
            p_name = controls[bone.parent.name]['CONTROL']
            parent = armature.data.edit_bones[p_name]
        else:
            parent = bone.parent
    return parent

def Set_Hidden_Bones(armature, sb_hide=True, mb_hide=True, cb_hide=True):
    controls = Get_Control_Bones(armature)
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    for sb_name, cb_names in controls['SOURCE'].items():
        sb, mb, cb = bones[sb_name], bones[cb_names['MECHANISM']], bones[cb_names['CONTROL']]
        sb.hide, mb.hide, cb.hide = sb_hide, mb_hide, cb_hide

def Object_Mode_Callback(obj, data):
    print(obj.mode, "ACB")
    # if the message is coming from the active object...
    if obj == bpy.context.object:
        armature = obj
        ACB = armature.data.ACB
        # if we are auto hiding...
        if ACB.Auto_hide:
            # check the armature has controls...
            if any(b.ACB.Type != 'NONE' for b in armature.data.bones):
                # that's gone into edit mode...
                if armature.mode == 'EDIT':
                    # show the source bones and hide the others...
                    Set_Hidden_Bones(armature, sb_hide=False)
                    ACB.Hide_source, ACB.Hide_mech, ACB.Hide_con = False, True, True
                else:
                    # otherwise show the controls and the others...
                    Set_Hidden_Bones(armature, cb_hide=False)
                    ACB.Hide_source, ACB.Hide_mech, ACB.Hide_con = True, True, False
        else:
            # otherwise just set hidden by user...
            Set_Hidden_Bones(armature, sb_hide=ACB.Hide_source, mb_hide=ACB.Hide_mech, cb_hide=ACB.Hide_con)
    # else if it's a mesh...
    elif bpy.context.object.type == 'MESH':
        mesh = bpy.context.object
        # get it's armature modifiers... (if any)
        armatures = {mod.object : mod.object.data.ACB for mod in mesh.modifiers if mod.type == 'ARMATURE'}
        for armature, ACB in armatures.items():
            # check the armature has controls and wants to auto hide...
            if any(b.ACB.Type != 'NONE' for b in armature.data.bones) and ACB.Auto_hide:
                # then if we are going into weight paint mode...
                if mesh.mode == 'WEIGHT_PAINT':
                    # show the source bones and hide the others...
                    Set_Hidden_Bones(armature, sb_hide=False)
                    ACB.Hide_source, ACB.Hide_mech, ACB.Hide_con = False, True, True
                else:
                    # otherwise show the controls and hide the others...
                    Set_Hidden_Bones(armature, cb_hide=False)
                    ACB.Hide_source, ACB.Hide_mech, ACB.Hide_con = True, True, False
                                        
def Subscribe_Mode_To(obj, data_path, callback):
    # get the data path to sub and assign it to the msgbus....
    subscribe_to = obj.path_resolve(data_path, False)
    bpy.msgbus.subscribe_rna(key=subscribe_to, owner=obj, args=(obj, data_path), notify=callback, options={"PERSISTENT"})

def Subscribe_Objects():
    # for all armatures...
    for armature in [a for a in bpy.data.objects if a.type == 'ARMATURE']:
        # if they have any controls...
        if any(b.ACB.Type != 'NONE' for b in armature.data.bones):
            # subscribe them to the msgbus...
            Subscribe_Mode_To(armature, 'mode', Object_Mode_Callback)

def Set_Automatic_Orientation(armature, cb_name):
    cd_bone = armature.data.bones[cb_name]
    ce_bone = armature.data.edit_bones[cb_name]
    children = [armature.data.edit_bones[c.name] for c in cd_bone.children if c.ACB.Type != 'MECHANISM']
    # if a bone has only one child...
    if len(children) == 1:
        child = children[0]
        # it's tail should probably point to it...
        ce_bone.tail = child.head
    # if a bone has multiple children
    elif len(children) > 1:
        # iterate over the children...
        for child in children:
            # checking for these most likely places we will want to target...
            if any(string in child.name.upper() for string in ["NECK", "SPINE", "LOWER", "ELBOW", "KNEE", "CALF", "HAND", "WRIST", "FOOT", "ANKLE"]):
                # take the first match and break...
                ce_bone.tail = child.head
                break
    # otherwise the bone has no children...
    elif ce_bone.parent != None:
        # but if it has a parent we can align to it...
        ce_bone.align_orientation(ce_bone.parent)
    else:
        print("Automatic Orientation: Could not find anywhere to align", ce_bone.name, "so you are on your own with it...")  

def Add_Bone_Controls(armature, bone, parent):
    ACB = armature.data.ACB
    # get the edit bone...
    se_bone = armature.data.edit_bones[bone.name]
    # add the control and mechanism bones with their prefixes...
    me_bone = armature.data.edit_bones.new(ACB.Mech_prefix + bone.name)
    ce_bone = armature.data.edit_bones.new(ACB.Con_prefix + bone.name)
    # set their transforms...
    ce_bone.head, ce_bone.tail, ce_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    me_bone.head, me_bone.tail, me_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    # niether bone should deform... (if you want them to then you're doing this wrong lol)
    ce_bone.use_deform, me_bone.use_deform = False, False
    # parent control bone to input parent and parent mechanism bone to the control bone...
    ce_bone.parent, me_bone.parent = parent, ce_bone
    # return the name of the control...
    return {'MECHANISM' : ACB.Mech_prefix + bone.name, 'CONTROL' : ACB.Con_prefix + bone.name}

def Remove_Control_Bones(armature, sb_name, cb_names):
    # we need to kill the mechanism and control bones...
    me_bone = armature.data.edit_bones[cb_names['MECHANISM']]
    ce_bone = armature.data.edit_bones[cb_names['CONTROL']]
    armature.data.edit_bones.remove(me_bone)
    armature.data.edit_bones.remove(ce_bone)
    # and kill the constraint on the source bone...
    sp_bone = armature.pose.bones[sb_name]
    copy_trans = sp_bone.constraints["MECHANISM - Copy Transform"]
    sp_bone.constraints.remove(copy_trans)
    armature.data.bones[sb_name].ACB.Type == 'NONE'

def Set_Control_Location(armature, sb_name, cb_names):
    se_bone = armature.data.edit_bones[sb_name]
    me_bone = armature.data.edit_bones[cb_names['MECHANISM']]
    ce_bone = armature.data.edit_bones[cb_names['CONTROL']]
    # get the length and y direction vector of the control bone...
    ce_length, ce_vec = ce_bone.length, ce_bone.y_axis
    # and set it's head and it's tail relative to the source bone...
    ce_bone.head, ce_bone.tail = se_bone.head, se_bone.head + (ce_vec * ce_length)
    # then orient the mechanism bone to the source bone...
    me_bone.head, me_bone.tail, me_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
    

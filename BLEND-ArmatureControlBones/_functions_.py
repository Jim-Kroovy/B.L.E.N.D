import bpy

def Add_To_Edit_Menu(self, context):
    row = self.layout.row()
    row.operator("jk.add_control_bones", icon='GROUP_BONE')

def Add_to_Pose_Menu(self, context):
    self.layout.operator("jk.edit_control_bones", icon='GROUP_BONE')

def Get_Control_Parent(ACB, bone):
    parent = None
    if bone.parent != None:
        if bone.parent.name in ACB.Edit_bones:
            parent = ACB.id_data.edit_bones[ACB.Con_prefix + bone.parent.name]
        else:
            parent = bone.parent
    print(parent)
    return parent

def Get_Selected_Bones(bones, settings):
    selected = {setting.Bone_name : True for setting in settings if setting.name in bones}
    for setting in settings:
        if setting.name in bones:
            selected[setting.Bone_name] = True

def Bone_Name_Callback(bone, props):
    #print(bone.name, props.Bone_name, props.Is_con, props.Is_mech)
    ACB = bone.id_data.ACB
    mode = bpy.context.object.mode
    bones = bone.id_data.edit_bones if mode == 'EDIT' else bone.id_data.bones
    to_bones = ACB.Edit_bones if mode == 'EDIT' else ACB.Bones
    # get the governing bone name...
    bone_name = props.Bone_name
    # get the control and mechanism prefixes...
    con_prefix, mech_prefix = ACB.Con_prefix, ACB.Mech_prefix
    # if we are calling from a control or mechanism bone...
    if props.Is_con:
        con_bone = bone
        con_bone.name = con_prefix + bone_name
        props.name = con_prefix + bone_name
    elif props.Is_mech:
        mech_bone = bone
        mech_bone.name = mech_prefix + bone_name
        props.name = mech_prefix + bone_name
    # if we aren't calling from a control or mechanism bone...
    else:
        # then get both control and mechanism
        con_bone = bones[con_prefix + bone_name]
        mech_bone = bones[mech_prefix + bone_name]
        # and change all the relevant data names for them...
        con_props = to_bones[con_prefix + bone_name]
        mech_props = to_bones[mech_prefix + bone_name]
        con_props.Bone_name = bone.name
        con_props.name = con_prefix + bone_name
        mech_props.Bone_name = bone.name
        mech_props.name = mech_prefix + bone_name
        # then rename the relvant bone data...
        props.Bone_name = bone.name
        props.name = bone.name
        # before renaming the control and mechanism bones themselves... (this will trigger the callback for them)
        con_bone.name = con_prefix + bone.name
        mech_bone.name = mech_prefix + bone.name
    
def Subscribe_Bone_To(bone, props, data_path, callback):
    # get the data path to sub and assign it to the msgbus....
    subscribe_to = bone.path_resolve(data_path, False)
    bpy.msgbus.subscribe_rna(key=subscribe_to, owner=bone, args=(bone, props), notify=callback, options={"PERSISTENT"})

# switching in and out of edit mode kills all msgbus subscriptions on bones... (edit bones are kind of their own thing)
def Object_Mode_Callback(obj, data):
    print(obj.mode)
    ACB = obj.data.ACB
    if ACB.Is_from_edit or obj.mode == 'EDIT':
        bones = obj.data.edit_bones if obj.mode == 'EDIT' else obj.data.bones
        from_bones = ACB.Bones if obj.mode == 'EDIT' else ACB.Edit_bones
        to_bones = ACB.Edit_bones if obj.mode == 'EDIT' else ACB.Bones
        for from_bone in from_bones:
            to_bone = to_bones.add()
            to_bone.name = from_bone.name
            to_bone.Bone_name = from_bone.Bone_name
            to_bone.Is_con = from_bone.Is_con
            to_bone.Is_mech = from_bone.Is_mech
        from_bones.clear()
        for bone in bones:
            # if this bone has something to do with controls it will be in there...
            if bone.name in to_bones:
                # we need to resub all the edit bones everytime we switch...
                Subscribe_Bone_To(bone, to_bones[bone.name], "name", Bone_Name_Callback)      
    # then toggle the bool for next time if we are now in edit mode or not...
    ACB.Is_from_edit = True if obj.mode == 'EDIT' else False
    # trigger the hide and lock updates... (i want to avoid driving these)
    ACB.Mech_show, ACB.Mech_select = ACB.Mech_show, ACB.Mech_select
    # CHECK LOCATION CHANGES HERE IN FUTURE?
                                        
def Subscribe_Mode_To(obj, data_path, callback):
    # get the data path to sub and assign it to the msgbus....
    subscribe_to = obj.path_resolve(data_path, False)
    bpy.msgbus.subscribe_rna(key=subscribe_to, owner=obj, args=(obj, data_path), notify=callback, options={"PERSISTENT"})

def Add_Control_Bones(armature, con_prefix, mech_prefix, bone, parent):
    # get the edit bone...
    e_bone = armature.data.edit_bones[bone.name]
    # add the control and mechanism bones with their prefixes...
    control_bone = armature.data.edit_bones.new(con_prefix + bone.name)
    mech_bone = armature.data.edit_bones.new(mech_prefix + bone.name)
    # set their transforms...
    control_bone.head, control_bone.tail, control_bone.roll = e_bone.head, e_bone.tail, e_bone.roll
    mech_bone.head, mech_bone.tail, mech_bone.roll = e_bone.head, e_bone.tail, e_bone.roll
    # niether bone should deform... (if you want them to then you're doing this wrong lol)
    control_bone.use_deform, mech_bone.use_deform = False, False
    # parent control bone to input parent and parent mechanism bone to the control bone...
    control_bone.parent, mech_bone.parent = parent, control_bone
    # set the bone data properties for all three bones...
    ACB = armature.data.ACB
    ACB.Is_from_edit = True
    bone_props = ACB.Edit_bones.add()
    bone_props.name = e_bone.name
    bone_props.Bone_name, bone_props.Is_con, bone_props.Is_mech = e_bone.name, False, False
    bone_props = ACB.Edit_bones.add()
    bone_props.name = control_bone.name
    bone_props.Bone_name, bone_props.Is_con, bone_props.Is_mech = e_bone.name, True, False
    bone_props = ACB.Edit_bones.add()
    bone_props.name = mech_bone.name
    bone_props.Bone_name, bone_props.Is_con, bone_props.Is_mech = e_bone.name, False, True

def Set_Mechanism(armature, names, mech_prefix):
    bpy.ops.object.mode_set(mode='POSE')
    for name in names:
        p_bone = armature.pose.bones[name]
        if "MECHANISM - Copy Transform" not in p_bone.constraints:
            copy_trans = p_bone.constraints.new("COPY_TRANSFORMS")
            copy_trans.name = "MECHANISM - Copy Transform"
        else:
            copy_trans = p_bone.constraints["MECHANISM - Copy Transform"]
        copy_trans.target = armature
        copy_trans.show_expanded = False
        copy_trans.subtarget = mech_prefix + name

def Set_Automatic_Orientation(armature, names, con_prefix):
    ACB = armature.data.ACB
    bpy.ops.object.mode_set(mode='EDIT')
    for name in names:
        e_bone = armature.data.edit_bones[ACB.Con_prefix + name]
        children = [c for c in e_bone.children if not c.name.startswith(ACB.Mech_prefix)]
        # if a bone has only one child...
        if len(children) == 1:
            child = children[0]
            print("CHILD SINGLE", child.name)
            # it's tail should probably point to it...
            e_bone.tail = child.head
        # if a bone has multiple children
        elif len(children) > 1:
            # iterate over the children...
            for child in children:
                # checking for these most likely places we will want to target...
                if any(string in child.name.upper() for string in ["NECK", "SPINE", "LOWER", "ELBOW", "KNEE", "CALF", "HAND", "WRIST", "FOOT", "ANKLE"]):
                    # take the first match and break...
                    e_bone.tail = child.head
                    break
            print("CHILD MULTIPLE", child.name)
        # otherwise the bone has no children...
        elif e_bone.parent != None:
            # but if it has a parent we can align to it...
            e_bone.align_orientation(e_bone.parent)
        else:
            print("Automatic Orientation: Could not find anywhere to align", name, "so you are on your own with it...")  
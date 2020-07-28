import bpy

def Add_Armature_Bindings(source, target):
    re_bones = {}
    # go into edit mode and...
    bpy.ops.object.mode_set(mode='EDIT')
    # create duplicates of all the source armatures bones...
    for se_bone in source.data.edit_bones:
        re_bone = source.data.edit_bones.new("RB_" + se_bone.name)
        re_bone.head, re_bone.tail, re_bone.roll = se_bone.head, se_bone.tail, se_bone.roll
        re_bone.parent = se_bone.parent
        re_bones[se_bone.name] = "RB_" + se_bone.name
    # then into pose mode...    
    bpy.ops.object.mode_set(mode='POSE')
    # to bind the bones together...
    for sp_name, rp_name in re_bones.items():
        sp_bone = source.pose.bones[sp_name]
        rp_bone = source.pose.bones[rp_name]
        # add a world space copy transforms to the retarget bone targeting the target bone...
        copy_trans = rp_bone.constraints.new('COPY_TRANSFORMS')
        copy_trans.name, copy_trans.show_expanded = "RETARGET - Copy Transform", False
        copy_trans.target, copy_trans.subtarget = target, target_bone_name
        # add local copy location, rotation and scale constraints to the source bone targeting the retarget bone...
        copy_loc = sp_bone.constraints.new('COPY_LOCATION')
        copy_loc.name, copy_loc.show_expanded = "RETARGET - Copy Location", False
        copy_loc.target, copy_loc.subtarget = source, rp_name
        copy_loc.use_offset, copy_loc.target_space, copy_loc.owner_space = True, 'LOCAL', 'LOCAL'
        # copy rotation needs its mix mode to be "Before Orginal"...
        copy_rot = sp_bone.constraints.new('COPY_ROTATION')
        copy_rot.name, copy_rot.show_expanded = "RETARGET - Copy Rotation", False
        copy_rot.target, copy_rot.subtarget = source, rp_name
        copy_rot.mix_mode, copy_rot.target_space, copy_rot.owner_space = 'BEFORE' 'LOCAL', 'LOCAL'
        # copy scale happens to use the same constraint settings as the copy location...
        copy_sca = sp_bone.constraints.new('COPY_SCALE')
        copy_sca.name, copy_sca.show_expanded = "RETARGET - Copy Scale", False
        copy_sca.target, copy_sca.subtarget = source, rp_name
        copy_sca.use_offset, copy_sca.target_space, copy_sca.owner_space = True, 'LOCAL', 'LOCAL'

def Add_Retarget_Action(source, action):
    if source.animation_data == None:
        source.animation_data_create()
    new_action = bpy.data.actions.new(action.name + "OFFSETS")
    new_action.use_fake_user = True
    source.animation_data.action = new_action
    action_pg = source.data.AAR.Actions.add()
    action_pg.Source = new_action

def Copy_Retarget_Action(source, action):
    copy = action.copy()
    copy.name = 
    source.animation_data.action = copy

def Get_Next_Action(source, action):


def Get_Bone_Curves(source):
    bone_curves = {pb.name : 
        {'location' : True if pb.constraints["RETARGET - Copy Location"] and not pb.constraints["RETARGET - Copy Location"].mute,
        'rotation' : True if pb.constraints["RETARGET - Copy Rotation"] and not pb.constraints["RETARGET - Copy Rotation"].mute,
        'scale' : True if pb.constraints["RETARGET - Copy Scale"] and not pb.constraints["RETARGET - Copy Scale"].mute}
            for pb in source.pose.bones}
    return bone_curves

        


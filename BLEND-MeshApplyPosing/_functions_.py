import bpy

def Add_To_Pose_Menu(self, context):
    self.layout.operator("jk.apply_mesh_posing", icon='MESH_DATA')

def Orient_Bones(armature, AAR, rot, sca):
    bpy.ops.object.mode_set(mode='OBJECT')
    # make sure we bring the target armature...
    target = AAR.Target
    target.select_set(True)
    # into edit mode with the armature...
    bpy.ops.object.mode_set(mode='EDIT')
    # iterate on AARs bound pose bone collection...
    for pb in AAR.Pose_bones:
        # if the target bone name is in the targets edit bones.. (it should be if it's bound)
        if pb.Target in target.data.edit_bones:
            # get both source and target edit bones...
            sp_bone = armature.data.edit_bones[pb.name]
            tp_bone = target.data.edit_bones[pb.Target]
            # if we are orienting rotation...
            if rot:
                # do some vector math...
                y_vec = tp_bone.y_axis
                sp_bone.tail = sp_bone.head + (y_vec * sp_bone.length)
                sp_bone.roll = tp_bone.roll
            # and setting scale is as simple as setting the length...
            if sca:
                sp_bone.length = tp_bone.length
    # back to object mode and deselct the target...
    bpy.ops.object.mode_set(mode='OBJECT')
    target.select_set(False)
    
def Apply_Mesh_Posing(armature):
    bpy.ops.object.mode_set(mode='OBJECT')
    # iterate through all objects...
    for mesh in [m for m in bpy.context.scene.objects if m.type == 'MESH']:
        # iterate through it's modifiers...
        for mod in mesh.modifiers:
            # if it's an armature modifier targeting the retarget target...
            if mod.type == 'ARMATURE' and mod.object == armature:
                # apply and re-add armature modifiers...
                context = bpy.context.copy()    
                context["object"] = mesh
                bpy.ops.object.modifier_apply(context, apply_as='DATA', modifier=mod.name)
                arm = mesh.modifiers.new(type='ARMATURE', name=mod.name)
                arm.object = armature
                mesh.select_set(False)
    # go into pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    # apply the pose...
    bpy.ops.pose.armature_apply(selected=False)
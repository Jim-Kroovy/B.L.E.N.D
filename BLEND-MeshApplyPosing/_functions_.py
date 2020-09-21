import bpy

def Add_To_Pose_Menu(self, context):
    self.layout.operator("jk.apply_mesh_posing", icon='MESH_DATA')

def Orient_Bones(armature, AAR, rot, sca, source):
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
            # we need both source and target edit bones...
            se_bone = armature.data.edit_bones[pb.name]
            # if there are armature control bones and we want to orient to the targets source bones...
            if source and target.data.bones[pb.Target].ACB.Type == 'CONT':
                # just orient to the mech bone because it's rest pose must be the same as the source bones...
                cont = target.data.bones[pb.Target]
                mech = [mpb.name for mpb in target.pose.bones if mpb.bone.ACB.Type == 'MECH' and mpb.bone.parent == cont]
                te_name = mech[0]
            else:
                te_name = pb.Target
            te_bone = target.data.edit_bones[te_name]
            # if we are orienting rotation...
            if rot:
                # do some vector math...
                y_vec = te_bone.y_axis
                se_bone.tail = se_bone.head + (y_vec * se_bone.length)
                se_bone.roll = te_bone.roll
            # and setting scale is as simple as setting the length...
            if sca:
                se_bone.length = te_bone.length
    # back to object mode and deselect the target...
    bpy.ops.object.mode_set(mode='OBJECT')
    target.select_set(False)
    
def Apply_Mesh_Posing(armature, keep_original):
    bpy.ops.object.mode_set(mode='OBJECT')
    # get all the meshes...
    meshes = [m for m in bpy.context.scene.objects if m.type == 'MESH' and any(mod.type == 'ARMATURE' and mod.object == armature for mod in m.modifiers)]
    # if we want to keep the orignal meshes...
    if keep_original:
        # select them all...
        for mesh in meshes:
            mesh.select_set(True)
        # deselect the armature...
        bpy.context.view_layer.objects.active = meshes[0]
        armature.select_set(False)
        # duplicate all the meshes...
        bpy.ops.object.duplicate()
        # reset the meshes list to be the duped meshes...
        meshes = [m for m in bpy.context.selected_objects if m.type == 'MESH']
        # make the armature active again...
        bpy.context.view_layer.objects.active = armature
        armature.select_set(True)
    # iterate through all meshes...
    for mesh in meshes:
        # iterate through it's modifiers...
        for mod in mesh.modifiers:
            # if it's an armature modifier targeting the retarget target...
            if mod.type == 'ARMATURE' and mod.object == armature:
                # apply and re-add armature modifiers...
                mod_name = mod.name
                context = bpy.context.copy()    
                context["object"] = mesh
                bpy.ops.object.modifier_apply(context, modifier=mod_name)
                arm = mesh.modifiers.new(type='ARMATURE', name=mod_name)
                arm.object = armature
                mesh.select_set(False)
    # go into pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    # apply the pose...
    bpy.ops.pose.armature_apply(selected=False)
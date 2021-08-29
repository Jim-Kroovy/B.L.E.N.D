import bpy

from bpy.props import (PointerProperty, CollectionProperty, IntProperty, EnumProperty, StringProperty, BoolProperty, FloatProperty)

from . import _properties_, _functions_

#from .modules.chains import _opposable_

#from .modules.twists import (_headhold_, _tailfollow_)

class JK_OT_ARM_Set_Rigging(bpy.types.Operator):
    """Adds/removes modular rigging"""
    bl_idname = "jk.arl_set_rigging"
    bl_label = "Add Rigging"
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(name="Action", description="",
        items=[('ADD', 'Add', ""), ('REMOVE', 'Remove', ""), ('UPDATE', 'Update', "")],
        default='ADD')
    
    index: IntProperty(name="Index", description="The rigging to add, edit or remove", default=0)

    flavour: EnumProperty(name="Type", description="The type of limb IK chain",
        items=[('NONE', 'Select rigging type...', ""),
            # chains...
            ('OPPOSABLE', 'Opposable', "A simple IK chain of 2 bones with a pole target. (Generally used by arms)"),
            ('PLANTIGRADE', 'Plantigrade', "An opposable IK chain of 2 bones with a pole target and standard foot rolling controls. (Generally used by human legs)"),
            ('DIGITIGRADE', 'Digitigrade', "A scalar IK chain of 3 bones with a pole target and special foot controls. (Generally used by animal legs)"),
            ('SPLINE', 'Spline', "A spline IK chain of any length controlled by a curve that's manipulated with target bones. (Generally used by tails/spines)"),
            ('SCALAR', 'Scalar', "An IK chain of any length controlled by scaling and rotating a parent of the target. (Generally used for fingers)"),
            ('FORWARD', 'Forward', "An FK chain of any length where the chain copies loc/rot/scale of a parent/target. (Generally an alternative used for fingers/tails)"),
            # twists...
            ('HEAD_HOLD', 'Head Hold', "A twist bone that holds deformation at the head of the bone back by tracking to a target. (eg: Upper Arm Twist)"),
            ('TAIL_FOLLOW', 'Tail Follow', "A twist bone that follows deformation at the tail of the bone by copying the local Y rotation of a target. (eg: Lower Arm Twist)")],
        default='NONE')#, update=update_flavour)

    def execute(self, context):
        armature = bpy.context.view_layer.objects.active
        if self.action == 'ADD':
            rigging = armature.jk_arm.rigging.add()
            rigging.name = "No rigging type selected..."
            armature.jk_arm.active = self.index
        elif self.action == 'REMOVE':
            if self.index == len(armature.jk_arm.rigging) - 1:
                armature.jk_arm.active = armature.jk_arm.active - 1
            rigging = armature.jk_arm.rigging[self.index]
            rigging.flavour = 'NONE'
            armature.jk_arm.rigging.remove(self.index)
        elif self.action == 'UPDATE':
            # check if any of the riggings source bones have changed... (saving the last active rigging)
            last_active = armature.jk_arm.active
            for i, rigging in enumerate(armature.jk_arm.rigging):
                armature.jk_arm.active = i
                detected = rigging.check_sources()
                # if they have, update it...
                if detected:
                    pointer = rigging.get_pointer()
                    pointer.update_rigging(bpy.context)
            # then return the active rigging to what it was before we updated...
            armature.jk_arm.active = last_active

        if not armature.jk_arm.is_mode_subbed:
            _functions_.subscribe_mode_to(armature, _functions_.armature_mode_callback)
        return {'FINISHED'}

class JK_OT_Hide_Bones(bpy.types.Operator):
    """Selects the given bone"""
    bl_idname = "jk.arl_hide_bones"
    bl_label = "Hide Bones"
    bl_options = {'REGISTER', 'UNDO'}

    armature: StringProperty(name="Armature", description="The armature to hide the bones of", default="", maxlen=1024)
    group: StringProperty(name="Group", description="The group of bones to hide", default="", maxlen=1024)
    
    def execute(self, context):
        armature = bpy.data.objects[self.armature]
        bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
        
        armature.data.bones.active = bone
        bone.select = True
        return {'FINISHED'}

class JK_OT_Select_Bone(bpy.types.Operator):
    """Selects the given bone"""
    bl_idname = "jk.active_bone_set"
    bl_label = "Active"
    bl_options = {'REGISTER', 'UNDO'}

    bone: StringProperty(name="Bone", description="The bone to make active", default="", maxlen=1024)
    
    def execute(self, context):
        armature = bpy.context.object
        bone = armature.data.bones[self.bone]
        armature.data.bones.active = bone
        bone.select = True
        return {'FINISHED'}

"""class JK_OT_Key_Chain(bpy.types.Operator):
    
    bl_idname = "jk.keyframe_chain"
    bl_label = "Keyframe Chain"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = bpy.context.object
        chain = armature.ARL.Chains[armature.ARL.chain]
        #_functions_.Set_Chain_Keyframe(chain, armature)
        return {'FINISHED'}"""

class JK_OT_ARM_Snap_Bones(bpy.types.Operator):
    """Snaps one pose bone to another"""
    bl_idname = "jk.arl_snap_bones"
    bl_label = "Snap Bones"
    bl_options = {'REGISTER', 'UNDO'}

    source: StringProperty(name="Source", description="The bone to snap from", default="", maxlen=1024)

    target: StringProperty(name="Target", description="The bone to snap to", default="", maxlen=1024)

    def execute(self, context):
        armature = bpy.context.object
        pbs = armature.pose.bones
        source_pb, target_pb = pbs.get(self.source), pbs.get(self.target)
        # get a copy of the target bones matrix...
        target_mat = target_pb.matrix.copy()
        # snap the parent and start bone to it...
        source_pb.matrix = target_mat
        # then snap the target to source... (incase we snapped to a child)
        if target_pb in source_pb.children_recursive:
            target_pb.matrix = source_pb.matrix.copy() #target_mat.copy()
        return {'FINISHED'}
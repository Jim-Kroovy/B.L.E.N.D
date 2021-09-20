import bpy
from . import _functions_
from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty) 

class JK_PG_ARD_Constraint(bpy.types.PropertyGroup):
    
    use: BoolVectorProperty(name="Use", description="Which axes are copied",
        default=(True, True, True), size=3, subtype='EULER')

    mute: BoolProperty(name="Mute", description="Is this copy constraint muted",
        default=True, options=set())
    
    influence: FloatProperty(name="Influence", description="Influence of the copy constraint", 
        default=1.0, min=0.0, max=1.0, subtype='FACTOR')

class JK_PG_ARD_Binding_Bone(bpy.types.PropertyGroup):

    target: StringProperty(name="Target Bone", description="The target bone to take animation from", default="", maxlen=1024)

    copy_loc: PointerProperty(type=JK_PG_ARD_Constraint)

    copy_rot: PointerProperty(type=JK_PG_ARD_Constraint)

    copy_sca: PointerProperty(type=JK_PG_ARD_Constraint)

class JK_PG_ARD_Pose_Bone(bpy.types.PropertyGroup):

    is_bound: BoolProperty(name="Is Bound", description="Is this bone currently bound to another for retargeting",
        default=False, options=set())
    
    def update_hide(self, context):
        source = bpy.context.object
        target = source.data.AAR.target
        sa_bones, ta_bones = source.data.bones, target.data.bones
        if self.target in ta_bones:
            ta_bones[self.target].hide = self.hide_target
        if self.retarget in sa_bones:
            sa_bones[self.retarget].hide = self.hide_retarget

    hide_target: BoolProperty(name="Hide Target", description="Hide the target bone we are taking the action from",
        default=True, options=set(), update=update_hide)

    hide_retarget: BoolProperty(name="Hide Binding", description="Hide the retarget bone we are binding source bones to",
        default=True, options=set(), update=update_hide)
    
    retarget: StringProperty(name="Retarget Bone", description="The retarget bone to follow", default="", maxlen=1024)

    def update_target(self, context):
        source = bpy.context.object
        target = source.data.AAR.target
        # if the new target exists...
        if target != None and self.target in target.data.bones:
                # check if this bone is already bound to a target...
                if self.is_bound:
                    _functions_.unbind_pose_bone(source, self.name, self.retarget)
                _functions_.bind_pose_bone(source, target, self.name, self.target)
        else:
            # and if the target was invalid unbind it...
            _functions_.unbind_pose_bone(source, self.name, self.retarget)

    target: StringProperty(name="Target", description="The target bone to take animation from", 
        default="", maxlen=1024, update=update_target)


class JK_PG_ARD_Action_Slot(bpy.types.PropertyGroup):

    armature: PointerProperty(type=bpy.types.Object)

    action: PointerProperty(type=bpy.types.Action, poll=_functions_.Action_Poll)

    use: BoolProperty(name="Use Action", description="Use this target action with this offset action",
        default=True, options=set())

    bake_step: IntProperty(name="Bake Step", default=1, min=1)

class JK_PG_ARD_Offset_Slot(bpy.types.PropertyGroup):
    
    armature: PointerProperty(type=bpy.types.Object)
    
    action: PointerProperty(type=bpy.types.Action)

    use: BoolProperty(name="Use Offset", description="Use this offset",
        default=True, options=set())

    def action_update(self, context):
        target = bpy.context.object.data.AAR.Target
        target.animation_data.action = self.Actions[self.Active].Action
        if self.Actions[self.Active].Action:
            self.Actions[self.Active].Action.use_fake_user = True
    
    Active: IntProperty(name="Active", default=0, update=action_update)
    
    Actions: CollectionProperty(type=JK_PG_ARD_Action_Slot)

class JK_PG_ARD_Binding(bpy.types.PropertyGroup):

    Bindings: CollectionProperty(type=JK_PG_ARD_Binding_Bone)

class JK_PG_ARD_Armature(bpy.types.PropertyGroup):
    
    is_bound: BoolProperty(name="Is Bound", description="Is this armature currently bound to another for retargeting",
        default=False, options=set())

    is_target: BoolProperty(name="Is Target", description="Is this armature currently the the target of another for retargeting",
        default=False, options=set())
    
    use_offsets: BoolProperty(name="Use Offsets", description="Enables offset actions for more advanced batch baking of retarget animations",
        default=False, options=set())

    apply_to_copy: BoolProperty(name="Apply to copy", description="Bakes retargets to a copy of the armature",
        default=False, options=set())

    def target_poll(self, object):
        return object.type == 'ARMATURE' and object != bpy.context.object and not object.data.AAR.Is_bound

    def target_update(self, context):
        source = bpy.context.object
        self.binding = ""
        if self.target != None:
            if len(self.pose_bones) > 0:
                self.pose_bones.clear()
            # add a property group entry for every pose bone
            for sp_bone in source.pose.bones:
                pb = self.pose_bones.add()
                pb.name = sp_bone.name
            _functions_.Add_Retarget_Bones(source, [pb.name for pb in self.pose_bones])
            # register the source as bound...
            self.Is_bound = True
        else:
            for pb in self.pose_bones:
                if pb.is_bound:
                    _functions_.unbind_pose_bone(source, pb.name, pb.Retarget)
            _functions_.Remove_Retarget_Bones(source, [p.Retarget for p in self.pose_bones])
            self.pose_bones.clear()
            self.is_bound = False

    target: PointerProperty(name="Target", type=bpy.types.Object, poll=target_poll, update=target_update)

    mute_cons: BoolProperty(name="Mute Constraints", description="Mute existing constraints. (May increase accuracy of baking the retarget)",
        default=True, options=set())

    hide_target_bones: BoolProperty(name="Hide Target Bones", description="Hide the target bones we are taking the action from",
        default=True, options=set())

    hide_retarget_bones: BoolProperty(name="Hide Retarget Bones", description="Hide the retarget bones we are binding source bones to",
        default=True, options=set())

    def update_offset(self, context):
        source = bpy.context.object
        source.animation_data.action = self.Offsets[self.Offset].Action
        if self.Offsets[self.Offset].Action:
            self.Offsets[self.Offset].Action.use_fake_user = True
    
    offset: IntProperty(name="Active Offset", default=0, update=update_offset)
    
    offsets: CollectionProperty(type=JK_PG_ARD_Offset_Slot)

    pose_bones: CollectionProperty(type=JK_PG_ARD_Pose_Bone)

    def update_binding(self, context):
        source = bpy.context.object
        # if it's being changed...
        if self.binding_last != self.binding:
            # if the last binding exists...
            if self.binding_last in self.bindings:
                # get and save it...
                last = self.bindings[self.binding_last]
                _functions_.get_binding(source, last)
            # if the new binding exists...
            if self.binding in self.bindings:
                # get and load it...
                binding = self.bindings[self.binding]
                _functions_.set_binding(source, binding)
            # else if the new binding is nothing...
            elif self.binding == "":
                # just clear all the bindings...
                for pb in self.pose_bones:
                    pb.Target = ""
            # then set our last binding to the new binding...
            self.binding_last = self.binding

    binding: StringProperty(name="Binding", default="", update=update_binding)

    binding_last: StringProperty(name="Last Binding", default="")
    
    bindings: CollectionProperty(type=JK_PG_ARD_Binding)

    retarget_meshes: BoolProperty(name="Retarget Meshes", description="If the target has meshes should we retarget them as well",
        default=True, options=set())

    use_offsets: BoolProperty(name="Use Offsets", description="Use offset slots to batch bake actions. (with different settings if needed)",
        default=False, options=set())
    
    bake_step: IntProperty(name="Bake Step", default=1, min=1)

    only_selected: BoolProperty(name="Only Selected", description="Only bake selected bones",
        default=False, options=set())

    stay_bound: BoolProperty(name="Stay Bound", description="Keep armature bound after baking actions",
        default=False, options=set())
    

    
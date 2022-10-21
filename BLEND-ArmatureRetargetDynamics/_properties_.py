import bpy
import json
from . import _functions_
from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty) 

class JK_PG_ARD_Constraint(bpy.types.PropertyGroup):
    
    use: BoolVectorProperty(name="Use", description="Which axes are copied",
        default=(True, True, True), size=3, subtype='EULER')

    mute: BoolProperty(name="Mute", description="Is this copy constraint muted",
        default=False, options=set())
    
    influence: FloatProperty(name="Influence", description="Influence of the copy constraint", 
        default=1.0, min=0.0, max=1.0, subtype='FACTOR')

class JK_PG_ARD_PoseBone(bpy.types.PropertyGroup):

    def bind(self):
        pbs = self.id_data.pose.bones
        source_pb, retarget_pb = pbs.get(self.name), pbs.get(self.retarget)
        bind = self.id_data.jk_ard.bindings.get(self.id_data.jk_ard.binding)
        binding = bind.get_binding() if bind else None
        # there should always be a retarget bone but check it just in case...
        if retarget_pb:
            # the retarget bone has a world space copy transform to the subtarget...
            copy_trans = retarget_pb.constraints.new(type='COPY_TRANSFORMS')
            copy_trans.name, copy_trans.show_expanded = "RETARGET - Copy Transform", False
            copy_trans.target, copy_trans.subtarget = self.target, self.subtarget
            # and the source bone has copy location, rotation and scale constraints to the retarget...
            if binding and self.name in binding:
                constraints = binding[self.name]['constraints']
            else:
                # if we didn't have the binding json or this bone wasn't in it, use constraint settings from the prefs...
                prefs = bpy.context.preferences.addons["BLEND-ArmatureRetargetDynamics"].preferences
                constraints = [
                    {'name' : "RETARGET - Copy Location", 'type' : 'COPY_LOCATION',
                        'mute' : prefs.copy_loc.mute, 'influence' : prefs.copy_loc.influence, 'use' : prefs.copy_loc.use[:]},
                    {'name' : "RETARGET - Copy Rotation", 'type' : 'COPY_ROTATION',
                        'mute' : prefs.copy_rot.mute, 'influence' : prefs.copy_rot.influence, 'use' : prefs.copy_rot.use[:]},
                    {'name' : "RETARGET - Copy Scale", 'type' : 'COPY_SCALE',
                        'mute' : prefs.copy_sca.mute, 'influence' : prefs.copy_sca.influence, 'use' : prefs.copy_sca.use[:]}]
            for con in constraints:
                constraint = source_pb.constraints.new(type=con['type'])
                constraint.name, constraint.show_expanded = con['name'], False
                constraint.use_x, constraint.use_y, constraint.use_z = con['use']
                constraint.mute, constraint.influence = con['mute'], con['influence']
                constraint.owner_space, constraint.target_space = 'LOCAL', 'LOCAL'
                constraint.target, constraint.subtarget = self.id_data, self.retarget
                # the copy rotation uses before original mix mode...
                if con['type'] == 'COPY_ROTATION':
                    constraint.mix_mode = 'BEFORE'
                else:
                    # the copy location and scale use offset...
                    constraint.use_offset = True
        # always update the current binding...
        if bind:
            bind.set_binding()

    def unbind(self):
        pbs = self.id_data.pose.bones
        # get the source and retarget bones...
        source_pb, retarget_pb = pbs.get(self.name), pbs.get(self.retarget)
        if retarget_pb:
            # kill all their retargeting constraints... (if the bone was found)
            retarget_cons = [c for c in retarget_pb.constraints if c.name.startswith("RETARGET - ")]
            for con in retarget_cons:
                retarget_pb.constraints.remove(con)
        if source_pb:
            # kill all their retargeting constraints... (if the bone was found)
            source_cons = [c for c in source_pb.constraints if c.name.startswith("RETARGET - ")]
            for con in source_cons:
                retarget_pb.constraints.remove(con)
        # always update the current binding...
        bind = self.id_data.jk_ard.bindings.get(self.id_data.jk_ard.binding)
        if bind:
            bind.set_binding()

    def update_is_bound(self, context):
        if self.is_bound:
            self.bind()
        else:
            self.unbind()

    is_bound: BoolProperty(name="Is Bound", description="Is this bone currently bound to another for retargeting",
        default=False, update=update_is_bound)

    is_binding: BoolProperty(name="Is Binding", description="Are we currently editing the binding elsewhere?",
        default=False)

    def update_target(self, context):
        # if we are not editing the binding elsewhere...
        if not self.is_binding:
            # kill the binding when the target/subtarget changes
            self.is_bound = False
            if self.target:
                # get the subtarget if the target exists...
                target_bbs = self.target.data.bones
                target_bb = target_bbs.get(self.subtarget)
                # and if the subtarget exists in the target...
                if target_bb:
                    # rebind to it...
                    self.is_bound = True

    def target_poll(self, object):
        return object.type == 'ARMATURE' and object != bpy.context.object

    target: PointerProperty(name="Target", description="The target armature to retarget animation from", 
        type=bpy.types.Object, poll=target_poll, update=update_target)

    subtarget: StringProperty(name="Subtarget", description="The subtarget bone to retarget animation from", 
        default="", maxlen=1024, update=update_target)

    def get_retarget(self):
        prefs = bpy.context.preferences.addons["BLEND-ArmatureRetargetDynamics"].preferences
        return "RB_" + self.name

    retarget: StringProperty(name="Retarget", description="The retarget bone to follow", 
        get=get_retarget)

    def update_hide(self, context):
        source, target = self.id_data, self.target
        if self.target:
            source_bbs, target_bbs = source.data.bones, target.data.bones
            retarget_bb, target_bb = source_bbs.get(self.retarget), target_bbs.get(self.subtarget)
            if retarget_bb:
                retarget_bb.hide = self.hide_retarget
            if target_bb:
                target_bb.hide = self.hide_target

    hide_target: BoolProperty(name="Hide Target", description="Hide the target bone we are taking the action from",
        default=False, options=set(), update=update_hide)

    hide_retarget: BoolProperty(name="Hide Binding", description="Hide the retarget bone we are binding source bones to",
        default=True, options=set(), update=update_hide)

class JK_PG_ARD_Action_Slot(bpy.types.PropertyGroup):

    armature: PointerProperty(type=bpy.types.Object)

    action: PointerProperty(type=bpy.types.Action, poll=_functions_.action_poll)

    use: BoolProperty(name="Use Action", description="Retarget this target action with this offset action",
        default=True, options=set())

    bake_step: IntProperty(name="Bake Step", default=1, min=1)

"""class JK_PG_ARD_Mesh_Slot(bpy.types.PropertyGroup):

    armature: PointerProperty(type=bpy.types.Object)

    mesh: PointerProperty(type=bpy.types.Object, poll=_functions_.object_poll)

    use: BoolProperty(name="Use Mesh", description="Retarget this mesh with this offset pose",
        default=True, options=set())"""

class JK_PG_ARD_Offset_Slot(bpy.types.PropertyGroup):
    
    armature: PointerProperty(type=bpy.types.Object)
    
    action: PointerProperty(type=bpy.types.Action)

    offset_json: StringProperty(name="Offset Json", description="This offsets pose/curves stored as a dictionary",
        default="")

    use: BoolProperty(name="Use Offset", description="Retarget using this offset",
        default=True, options=set())

    def action_update(self, context):
        target = bpy.context.object.data.jk_ard.target
        target.animation_data.action = self.actions[self.active].action
        if self.actions[self.active].action:
            self.actions[self.active].action.use_fake_user = True
    
    active: IntProperty(name="Active", default=0, update=action_update)
    
    actions: CollectionProperty(type=JK_PG_ARD_Action_Slot)

    #meshes: CollectionProperty(type=JK_PG_ARD_Mesh_Slot)

class JK_PG_ARD_Binding(bpy.types.PropertyGroup):

    def get_binding(self):
        return json.loads(self.binding)
    
    def set_binding(self):
        pbs = self.id_data.pose.bones
        binding = {}
        for pb in pbs:
            if pb.jk_ard.is_bound:
                binding['target'] = pb.jk_ard.target.name
                binding['subtarget'] = pb.jk_ard.subtarget
                binding['constraints'] = []
                for con in [c for c in pb.constraints if c.name.startswith("RETARGET - ")]:
                    constraint = {}
                    constraint['name'], constraint['type'] = con.name, con.type
                    constraint['use'] = [con.use_x, con.use_y, con.use_z]
                    constraint['mute'], constraint['influence'] = con.mute, con.influence
                    binding['constraints'].append(constraint)
        self.binding_json = json.dumps(binding)

    binding_json: StringProperty(name="Binding Json", description="", default="")

class JK_PG_ARD_Object(bpy.types.PropertyGroup):

    is_retargeting: BoolProperty(name="Is Retargeting", description="Is this armature currently retargeting",
        default=False)

    def update_use_meshes(self, context):
        if self.use_meshes:
            if self.use_actions:
                self.use_actions = False
            else:
                _functions_.add_retarget_bones(self.id_data)
                self.is_retargeting = True
        else:
            if not self.use_actions:
                _functions_.remove_retarget_bones(self.id_data)
            self.is_retargeting = self.use_actions

    def update_use_actions(self, context):
        if self.use_actions:
            if self.use_meshes:
                self.use_meshes = False
            else:
                _functions_.add_retarget_bones(self.id_data)
            self.is_retargeting = True
        else:
            _functions_.remove_retarget_bones(self.id_data)
            self.is_retargeting = self.use_meshes

    use_meshes: BoolProperty(name="Meshes", description="Is this armature currently retargeting meshes to another",
        default=False, update=update_use_meshes)

    use_actions: BoolProperty(name="Actions", description="Is this armature currently retargeting actions from another",
        default=False, update=update_use_actions)
    
    use_offsets: BoolProperty(name="Use Offsets", description="Enables offset actions for animated baking of retarget animations",
        default=False)

    apply_to_copy: BoolProperty(name="Keep Original", description="Operate on copies of armature/meshes to preserve the originals",
        default=False)

    mute_cons: BoolProperty(name="Mute Constraints", description="Mute existing constraints. (May increase accuracy of baking the retarget)",
        default=True, options=set())

    hide_target_bones: BoolProperty(name="Hide Target Bones", description="Hide the target bones we are taking the action from",
        default=True, options=set())

    hide_retarget_bones: BoolProperty(name="Hide Retarget Bones", description="Hide the retarget bones we are binding source bones to",
        default=True, options=set())

    def update_offset(self, context):
        source = bpy.context.object
        source.animation_data.action = self.offsets[self.offset].action
        if self.offsets[self.offset].action:
            self.offsets[self.offset].action.use_fake_user = True
    
    offset: IntProperty(name="Active Offset", default=0, update=update_offset)
    
    offsets: CollectionProperty(type=JK_PG_ARD_Offset_Slot)

    def update_binding(self, context):
        source = self.id_data
        source_pbs = source.pose.bones
        # if it's being changed...
        if self.binding_last != self.binding:
            # if the last binding exists...
            if self.binding_last in self.bindings:
                # get it and auto save...
                last = self.bindings[self.binding_last]
                last.set_binding()
            # if the new binding exists...
            if self.binding in self.bindings:
                # get and load the new binding...
                binding = self.bindings[self.binding].get_binding()
                for pb in source_pbs:
                    # clear any current pose bone bindings
                    pb.jk_ard.is_bound = False
                    # if the bone name is in the new binding...
                    if pb.bone.name in binding:
                        bind = binding[pb.bone.name]
                        pb.jk_ard.is_binding = True
                        # set it's target and subtarget and trigger the bind update...
                        pb.jk_ard.target = bpy.data.objects[bind['target']]
                        pb.jk_ard.subtarget = bind['subtarget']
                        pb.jk_ard.is_binding = False
                        pb.jk_ard.is_bound = True
            # else if the new binding is nothing...
            elif self.binding == "":
                # just clear all the bindings...
                for pb in source_pbs:
                    pb.jk_ard.is_bound = False
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
    

    
import bpy

from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty)

from ... import _functions_, _properties_ 

# Much of this code is copy/pasted between the various flavours of rigging, while a little long winded it makes adding new things and updating and troubleshooting a whole lot easier...
# and everyone wants me to do so much i decided it's better that things are easy to edit/create and not as dynamic as they could be...

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTY FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_forward_refs(self):
    armature, references = self.id_data, {}
    pbs, bbs = armature.pose.bones, armature.data.bones
    references['target'] = {
        'source' : pbs.get(self.target.source), 'origin' : pbs.get(self.target.origin),
        'end' : pbs.get(self.target.end), 'bone' : pbs.get(self.target.bone)}
    references['bones'] = [{
        'source' : pbs.get(bone.source), 'origin' : pbs.get(bone.origin)} for bone in self.bones]
    references['constraints'] = [{
        'constraint' : pbs.get(con.source).constraints.get(con.constraint) if pbs.get(con.source) else None,
        'source' : pbs.get(con.source)} for con in self.constraints]
    return references

def get_forward_parents(self, bones):
    # get recursive parents from the source to the length of the chain...
    parent, parents = bones.get(self.target.end), []
    while len(parents) < self.target.length:# and parent != None:
        parents.append(parent)
        parent = parent.parent if parent else None
    return parents

def get_forward_props(self, armature):
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    self.is_editing = True
    self.bones.clear()
    self.constraints.clear()
    #if bones.active:
    # target could be set now... (unless it's already been set by combo rigging?)
    if not self.target.end:
        print("NOT SET")
        self.target.end = bones.active.name
    # get recursive parents...
    parents = _functions_.get_parents(bones, self.target.end, self.target.length)
    constraints = {'COPY_LOCATION' : "FORWARD - Copy Location", 
        'COPY_ROTATION' : "FORWARD - Copy Rotation", 
        'COPY_SCALE' : "FORWARD - Copy Scale"}
    for parent in reversed(parents):
        bone = self.bones.add()
        if parent:
            bone.source = parent.name
        for flavour, name in constraints.items():
            constraint = self.constraints.add()
            constraint.source, constraint.flavour, constraint.constraint = bone.source, flavour, name
            constraint.owner_space, constraint.target_space = 'LOCAL', 'LOCAL'
            if flavour == 'COPY_ROTATION':
                # copy rotations use mix mode instead of offset...
                constraint.mix_mode, constraint.influence = 'BEFORE', 1.0
            else:
                # usually these chains will be for rotation so default the other constraint influences to 0.0
                constraint.use_offset, constraint.influence = True, 0.0
    self.is_editing = False

def set_forward_props(self, armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingModules"].preferences
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    rigging = armature.jk_arm.rigging[armature.jk_arm.active]
    self.is_editing = True
    # set the name of the rigging based on the bones... (needed for drivers)
    rigging.name = "Chain (Forward) - " + self.bones[0].source + " - " + self.target.end
    # get recursive parents...
    parents = _functions_.get_parents(bones, self.target.end, self.target.length)
    parents.reverse()
    self.target.source = parents[0].name
    self.target.bone = prefs.affixes.target + self.target.source
    constraints = {'COPY_LOCATION' : "FORWARD - Copy Location", 
            'COPY_ROTATION' : "FORWARD - Copy Rotation", 
            'COPY_SCALE' : "FORWARD - Copy Scale"}
    ci = 0
    for bi in range(0, self.target.length):
        # if we don't have a bone already create one...
        bone = self.bones.add() if len(self.bones) <= bi else self.bones[bi]
        parent = parents[bi]
        if parent:
            bone.source = parent.name
            bone.origin = parent.parent.name if parent.parent else ""
        for flavour, name in constraints.items():
            constraint = self.constraints.add() if len(self.constraints) <= ci else self.constraints[ci]
            constraint.source, constraint.flavour, constraint.constraint = bone.source, flavour, name
            constraint.owner_space, constraint.target_space = 'LOCAL', 'LOCAL'
            constraint.subtarget = self.target.bone
            if flavour == 'COPY_ROTATION':
                # copy rotations use mix mode instead of offset...
                constraint.mix_mode, constraint.influence = 'BEFORE', 1.0
            else:
                # usually these chains will be for rotation so default the other constraint influences to 0.0
                constraint.use_offset, constraint.influence = True, 0.0
            ci = ci + 1
        # might need to clean up bones when reducing chain length...
        if len(self.bones) > self.target.length:
            while len(self.bones) != self.target.length:
                self.bones.remove(self.target.length)
        # might need to clean up constraints when reducing chain length...
        if len(self.constraints) > (self.target.length * 3):
            while len(self.constraints) != (self.target.length * 3):
                self.constraints.remove((self.target.length * 3))
    print(rigging.flavour)
    self.is_editing = False
    # then clear the riggings source bone data...
    rigging.sources.clear()
    # and refresh it for the auto update functionality...
    rigging.get_sources()

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- RIGGING FUNCTIONS ------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def add_forward_target(self, armature):
    ebs = armature.data.edit_bones
    # get the targets source...
    source_eb = ebs.get(self.bones[0].source)
    # create a target from the source bone pointing in the user defined direction...
    target_eb = ebs.new(self.target.bone)
    target_eb.head, target_eb.tail = source_eb.head, source_eb.tail #source_eb.head + (direction * (distance * 0.01))
    target_eb.roll = source_eb.roll
    target_eb.parent, target_eb.use_deform = source_eb.parent, False
    # none of the bones in the chain should be connected...
    for bone in self.bones:
        eb = ebs.get(bone.source)
        if eb:
            eb.use_connect = False

def add_forward_rolls(self, armature):
    ebs = armature.data.edit_bones
    # deselect everything...
    bpy.ops.armature.select_all(action='DESELECT')
    # then select all the bones in the chain...
    for bone in self.bones:
        eb = ebs.get(bone.source)
        if eb:
            # saving their original bone roll as we go...
            bone.roll = eb.roll
            eb.select = True
    # then make all their rolls relative to the control...
    ebs.active = ebs.get(self.target.bone)
    bpy.ops.armature.calculate_roll(type='ACTIVE')

def add_forward_chain(self, armature):
    # don't touch the symmetry! (Thanks Jon V.D, you are a star)
    is_mirror_x = armature.data.use_mirror_x
    if is_mirror_x:
        armature.data.use_mirror_x = False
    # don't want to trigger the mode callback during setup...
    is_detecting = armature.jk_arm.use_edit_detection
    if is_detecting:
        armature.jk_arm.use_edit_detection = False
    # need to add bones in edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    add_forward_target(self, armature)
    if self.auto_roll:
        add_forward_rolls(self, armature)
    # and add constraints and drivers in pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    _functions_.add_constraints(self, armature)
    # if we are using default shapes or groups, add them...
    if self.use_default_shapes:
        _functions_.add_shapes(self, armature)
    if self.use_default_groups:
        _functions_.add_groups(self, armature)
    if self.use_default_layers:
        _functions_.add_layers(self, armature)
    # give x mirror back... (if it was turned on)
    armature.data.use_mirror_x = is_mirror_x
    # give edit detection back... (if it was turned on)
    armature.jk_arm.use_edit_detection = is_detecting

def remove_forward_chain(self, armature):
    references = self.get_references()
    # first we should get rid of anything in pose mode...
    if armature.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    # constraints need removing, we aren't removing any bones that have them...
    for con_refs in references['constraints']:
        if con_refs['source'] and con_refs['constraint']:
            con_refs['source'].constraints.remove(con_refs['constraint'])
    # clear shapes/groups from source bones... (what should i do about layers?)
    for bone_refs in references['bones']:
        if bone_refs['source']:
            bone_refs['source'].custom_shape, bone_refs['source'].bone_group = None, None
    # then we need to kill the target bone in edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    ebs = armature.data.edit_bones
    target_eb = ebs.get(self.target.bone)
    for child in target_eb.children:
        child.parent = ebs.get(self.target.source)
    if target_eb:
        ebs.remove(target_eb)
    # then return to pose mode like nothing ever happened...
    bpy.ops.object.mode_set(mode='POSE')

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTIES -------------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

class JK_PG_ARM_Forward_Chain(bpy.types.PropertyGroup):

    target: PointerProperty(type=_properties_.JK_PG_ARM_Target)

    bones: CollectionProperty(type=_properties_.JK_PG_ARM_Bone)

    constraints: CollectionProperty(type=_properties_.JK_PG_ARM_Constraint)

    def get_references(self):
        return get_forward_refs(self)

    def get_sources(self):
        sources = [bone.source for bone in self.bones]
        return sources

    def get_groups(self):
        groups = {
            "Chain Bones" : [bone.source for bone in self.bones],
            "Kinematic Targets": [self.target.bone]}
        return groups

    def get_shapes(self):
        shapes = {
            "Bone_Shape_Default_Head_Flare" : [self.target.bone],
            "Bone_Shape_Default_Medial_Ring" : [bone.source for bone in self.bones]}
        return shapes

    def get_is_riggable(self):
        # we are going to need to know if the rigging in the properties is riggable...
        armature, is_riggable = self.id_data, True
        bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
        # for this rigging we iterate on some names...
        for name in [bone.source for bone in self.bones]:
            bone = bones.get(name)
            # if those names are not existing bones...
            if bone == None:
                # this riggin' ain't riggable...
                is_riggable = False
                break
        return is_riggable

    is_riggable: BoolProperty(name="Is Riggable", description="Can this chain have it's rigging applied?",
        get=get_is_riggable)

    def update_is_rigged(self, context):
        # whenever we set "is_rigged" to false, kill the rigging...
        if not self.is_rigged:
            remove_forward_chain(self, self.id_data)

    is_rigged: BoolProperty(name="Is Rigged", description="Is this chain currently rigged?",
        default=False, update=update_is_rigged)

    is_editing: BoolProperty(name="Is Editing", description="Is this rigging being edited internally? (if it is we need to stop update functions from firing)",
        default=False)

    has_properties: BoolProperty(name="Has Properties", description="Have we added all the needed properties for this rigging?",
        default=False)

    def update_rigging(self, context):
        if not self.is_editing:
            # if this rigging is currently rigged, unrig it...
            if self.is_rigged:
                self.is_rigged = False
            # if it hasn't had properties created for it...
            if not self.has_properties:
                # try to get the essentials...
                get_forward_props(self, self.id_data)
                self.has_properties = True
            # always set the properties that get calculated from the essentials...
            set_forward_props(self, self.id_data)
            # if we can rig from the properties...
            if self.is_riggable:
                # add the rigging...
                add_forward_chain(self, self.id_data)
                self.is_rigged = True

    auto_roll: BoolProperty(name="Auto Roll", description="Automatically align bone rolls so all bones in the chain transform to the orientation of the target",
        default=False, update=update_rigging)

    use_default_groups: BoolProperty(name="Use Default Groups", description="Do you want this rigging to use some default bone groups?",
        default=False, update=update_rigging)

    use_default_shapes: BoolProperty(name="Use Default Shapes", description="Do you want this rigging to use some default bone shapes?",
        default=False, update=update_rigging)

    use_default_layers: BoolProperty(name="Use Default Layers", description="Do you want this rigging to use some default armature layers?",
        default=False, update=update_rigging)



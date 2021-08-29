import bpy

from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty)

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
    if bones.active:
        # target could be set now...
        self.target.end = bones.active.name
        self.target.bone = "TB_" + bones.active.name
        # get recursive parents...
        parents = get_forward_parents(self, bones)
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

def set_forward_props(self, armature):
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    rigging = armature.jk_arm.rigging[armature.jk_arm.active]
    # set the name of the rigging based on the bones... (needed for drivers)
    rigging.name = "Chain (Forward) - " + self.bones[0].source + " - " + str(self.target.length)
    #end = bones.get(self.target.end)
    #if end and self.target.length > 0:
    # get recursive parents...
    parents = get_forward_parents(self, bones)
    parents.reverse()
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
            constraint.subtarget = self.target.bone
            ci = ci + 1
        # might need to clean up bones when reducing chain length...
        if len(self.bones) > self.target.length:
            while len(self.bones) != self.target.length:
                self.bones.remove(self.target.length)
        # might need to clean up constraints when reducing chain length...
        if len(self.constraints) > (self.target.length * 3):
            while len(self.constraints) != (self.target.length * 3):
                self.constraints.remove((self.target.length * 3))
    # then clear the riggings source bone data...
    rigging.sources.clear()
    # and refresh it for the auto update functionality...
    rigging.get_sources()

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- RIGGING FUNCTIONS ------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def add_forward_target(self, armature):
    ebs = armature.data.edit_bones
    # get the targets source and end bones...
    source_eb, end_eb = ebs.get(self.bones[0].source), ebs.get(self.target.end)
    # and the defined local axis and distance...
    #direction = source_eb.x_axis if self.target.axis.startswith('X') else source_eb.z_axis
    #distance = (self.target.distance * -1) if 'NEGATIVE' in self.target.axis else (self.target.distance)
    # create a target from the source bone pointing in the user defined direction...
    target_eb = ebs.new(self.target.bone)
    target_eb.head, target_eb.tail = source_eb.head, source_eb.tail #source_eb.head + (direction * (distance * 0.01))
    target_eb.roll = source_eb.roll
    target_eb.parent, target_eb.use_deform = source_eb.parent, False
    # deselect everything, select the target bone and make the end bone active...
    #bpy.ops.armature.select_all(action='DESELECT')
    #target_eb.select = True
    #end_eb.select = True
    #ebs.active = end_eb
    # then make the targets roll relative to the end bone
    #bpy.ops.armature.calculate_roll(type='ACTIVE')

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

def add_forward_constraints(self, armature):
    pbs = armature.pose.bones
    for constraint in self.constraints:
        pb = pbs.get(constraint.source)
        if pb and constraint.flavour != 'NONE':
            con = pb.constraints.new(type=constraint.flavour)
            con_props = {cp.identifier : getattr(constraint, cp.identifier) for cp in constraint.bl_rna.properties if not cp.is_readonly}
            # for each of the constraints settings...
            for cp in con.bl_rna.properties:
                if cp.identifier == 'target':
                    con.target = armature
                # so constraints are stupid af, not all constraints with 'target_space' even HAVE a 'target' property...
                elif cp.identifier == 'target_space' and con_props['target_space'] in ['LOCAL_WITH_PARENT', 'POSE']:
                    # but can only set target space to 'local with parent' or 'pose' on those that do if the target has been set...
                    con.target, con.target_space = armature, con_props['target_space']
                # my collections are indexed, so to avoid my own confusion, name is constraint...
                elif cp.identifier == 'name':
                    setattr(con, cp.identifier, con_props['constraint'])
                # use offset overrides copy rotations mix mode...
                elif cp.identifier == 'use_offset':
                    # so only set it if this constraint is not a copy rotation...
                    if constraint.flavour != 'COPY_ROTATION' and cp.identifier in con_props:
                        setattr(con, cp.identifier, con_props[cp.identifier])
                # if they are in our settings dictionary... (and are not read only?)
                elif cp.identifier in con_props and not cp.is_readonly:
                    setattr(con, cp.identifier, con_props[cp.identifier])
            con.show_expanded = False

def add_forward_shapes(self, armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingModules"].preferences
    pbs = armature.pose.bones
    bone_shapes = self.get_shapes()
    # get the names of any shapes that do not already exists in the .blend...
    load_shapes = [sh for sh in bone_shapes.keys() if sh not in bpy.data.objects]
    # if we have shapes to load...
    if load_shapes:
        # load the them from their library.blend...
        with bpy.data.libraries.load(prefs.shape_path, link=False) as (data_from, data_to):
            data_to.objects = [shape for shape in data_from.objects if shape in load_shapes]
    # then iterate on the bone shapes dictionary...
    for shape, bones in bone_shapes.items():
        for bone in bones:
            # setting all existing pose bones...
            pb = pbs.get(bone)
            if pb:
                # to use their designated shape...
                pb.custom_shape = bpy.data.objects[shape]

def add_forward_groups(self, armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingModules"].preferences
    pbs = armature.pose.bones
    bone_groups = self.get_groups()
    # get the names of any groups that do not already exist on the armature...
    load_groups = [gr for gr in bone_groups.keys() if gr not in armature.pose.bone_groups]
     # if we have any groups to load...
    if load_groups:
        # create them and set their colour...
        for load_group in load_groups:
            grp = armature.pose.bone_groups.new(name=load_group)
            grp.color_set = prefs.group_colours[load_group]
    # then iterate on the bone groups dictionary...
    for group, bones in bone_groups.items():
        for bone in bones:
            # setting all existing pose bones...
            pb = pbs.get(bone)
            if pb:
                # to use their designated group...
                pb.bone_group = armature.pose.bone_groups[group]

def add_forward_layers(self, armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingModules"].preferences
    pbs = armature.pose.bones
    bone_layers = self.get_groups()
    # then iterate on the bone layers dictionary...
    for layer, bones in bone_layers.items():
        for bone in bones:
            # setting all existing pose bones...
            pb = pbs.get(bone)
            if pb:
                # to use their designated layer...
                pb.bone.layers = prefs.group_layers[layer]

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
    add_forward_constraints(self, armature)
    # if we are using default shapes or groups, add them...
    if self.use_default_shapes:
        add_forward_shapes(self, armature)
    if self.use_default_groups:
        add_forward_groups(self, armature)
    if self.use_default_layers:
        add_forward_layers(self, armature)
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

class JK_PG_ARM_Forward_Constraint(bpy.types.PropertyGroup):
    
    def update_constraint(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].forward
        if not rigging.is_editing:
            rigging.update_rigging(context)

    source: StringProperty(name="Source", description="Name of the bone the constraint is on",
        default="", maxlen=63)

    constraint: StringProperty(name="Constraint", description="Name of the actual constraint",
        default="", maxlen=63)

    flavour: EnumProperty(name="Flavour", description="The type of constraint",
        items=[('COPY_ROTATION', 'Copy Rotation', ""), ('COPY_LOCATION', 'Copy Location', ""), ('COPY_SCALE', 'Copy Location', "")],
        default='COPY_ROTATION')
    
    subtarget: StringProperty(name="Subtarget", description="Name of the subtarget. (if any)",
        default="", maxlen=1024, update=update_constraint)

    use_x: BoolProperty(name="Use X", description="Use X", default=True)
    invert_x: BoolProperty(name="Invert X", description="Invert X", default=False)

    use_y: BoolProperty(name="Use Y", description="Use Y", default=True)
    invert_y: BoolProperty(name="Invert Y", description="Invert Y", default=False)

    use_z: BoolProperty(name="Use Z", description="Use Z limit", default=True)
    invert_z: BoolProperty(name="Invert Z", description="Invert Z", default=False)

    use_offset: BoolProperty(name="Use Offset", description="Add original transform into copied transform. (location/scale copy constraint)", default=True)

    mix_mode: EnumProperty(name="Mix Mode", description="Specify how the copied and existing rotations are combined",
        items=[('REPLACE', "Replace", "Replace original rotation with copied"), 
            ('ADD', "Add", "Add euler component values together"),
            ('BEFORE', "Before Original", "Apply copied rotation before original, as if the constraint target is a parent"),
            ('AFTER', "After Original", "Apply copied rotation after original, as if the constraint target is a child"),
            ('OFFSET', "Fit Curve", "Combine rotations like the original offset checkbox. Does not work well for multiple axis rotations")],
        default='BEFORE')

    target_space: EnumProperty(name="Target Space", description="Space that target is evaluated in",
        items=[('WORLD', "World Space", ""), ('POSE', "Pose Space", ""), 
            ('LOCAL', "local Space", ""), ('LOCAL_WITH_PARENT', "local With Parent Space", "")],
        default='LOCAL')

    owner_space: EnumProperty(name="owner Space", description="Space that owner is evaluated in",
        items=[('WORLD', "World Space", ""), ('POSE', "Pose Space", ""), 
            ('LOCAL', "local Space", ""), ('LOCAL_WITH_PARENT', "local With Parent", "")],
        default='LOCAL')

    influence: FloatProperty(name="Influence", description="influence of this constraint", default=1.0, min=0.0, max=1.0, subtype='FACTOR')

class JK_PG_ARM_Forward_Bone(bpy.types.PropertyGroup):

    def update_bone(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].forward
        if not rigging.is_editing:
            # changing the source is a little complicated because we need it to remove/update rigging...
            bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
            # deselect everything depending on mode...
            if armature.mode == 'EDIT':
                bpy.ops.armature.select_all(action='DESELECT')
            elif armature.mode == 'POSE':
                bpy.ops.pose.select_all(action='DESELECT')
            # make the new source active and save a reference of it...
            bones.active = bones.get(self.source)
            new_source = self.source
            # remove the rigging and set "is_editing" true...
            rigging.is_rigged, rigging.is_editing = False, True
            # while is_editing is false set the new source to what we want it to be...
            self.source, rigging.is_editing = new_source, False
            # then we can update the rigging...
            rigging.update_rigging(context)

    source: StringProperty(name="Source", description="Name of the source bone that copies transforms",
        default="", maxlen=63)#, update=update_bone)

    origin: StringProperty(name="Origin", description="Name of the source bones original parent",
        default="", maxlen=63)

    roll: FloatProperty(name="Roll", description="The source bones roll before rigging", 
        default=0.0, subtype='ANGLE', unit='ROTATION')

class JK_PG_ARM_Forward_Target(bpy.types.PropertyGroup):
    
    def update_target(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].forward
        if rigging.is_rigged and not rigging.is_editing:
            # changing the source is a little complicated because we need it to remove/update rigging...
            bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
            # deselect everything depending on mode...
            if armature.mode == 'EDIT':
                bpy.ops.armature.select_all(action='DESELECT')
            elif armature.mode == 'POSE':
                bpy.ops.pose.select_all(action='DESELECT')
            # make the new end active and save a reference of it...
            bones.active = bones.get(self.source)
            new_end = self.end
            # if the new end exists...
            if bones.get(new_end):
                # remove the rigging and set "is_editing" true...
                rigging.is_rigged, rigging.is_editing = False, True
                # while "is_editing" is false set the new end to what we actually want it to be...
                self.end, rigging.is_editing = new_end, False
                # then we can update the rigging...
                rigging.update_rigging(context)
            else:
                rigging.update_rigging(context)
        elif not rigging.is_editing:
            rigging.update_rigging(context)

    source: StringProperty(name="Source", description="Name of the source bone that does the twisting",
        default="", maxlen=63)

    origin: StringProperty(name="Origin", description="Name of the source bones original parent",
        default="", maxlen=63)

    bone: StringProperty(name="Bone", description="Name of the actual target",
        default="", maxlen=63)

    end: StringProperty(name="End", description="Name of the bone at the end of the chain",
        default="", maxlen=63, update=update_target)

    length: IntProperty(name="Chain Length", description="How many bones are included in this FK chain",
        default=3, min=2, update=update_target)

    distance: FloatProperty(name="Distance", description="The distance the targets and curve are from the source bones. (in metres)", 
        default=0.25, update=update_target)
    
    axis: EnumProperty(name="Shape Axis", description="The local axis of the bone that defines which custom shape to use",
        items=[('X', 'X axis', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X axis', "", "CON_LOCLIKE", 1),
        ('Z', 'Z axis', "", "CON_LOCLIKE", 4),
        ('Z_NEGATIVE', '-Z axis', "", "CON_LOCLIKE", 5)],
        default='Z_NEGATIVE')

class JK_PG_ARM_Forward_Chain(bpy.types.PropertyGroup):

    target: PointerProperty(type=JK_PG_ARM_Forward_Target)

    bones: CollectionProperty(type=JK_PG_ARM_Forward_Bone)

    constraints: CollectionProperty(type=JK_PG_ARM_Forward_Constraint)

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



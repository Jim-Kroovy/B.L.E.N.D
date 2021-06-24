import bpy

from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty)

# Much of this code is copy/pasted between the various flavours of rigging, while a little long winded it makes adding new things and updating and troubleshooting a whole lot easier...
# and everyone wants me to do so much i decided it's better that things are easy to edit/create and not as dynamic as they could be...

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTY FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_tailfollow_refs(self):
    pbs, references = self.id_data.pose.bones, {}
    references['bone'] = {
        'source' : pbs.get(self.bone.source), 'origin' : pbs.get(self.bone.origin), 'offset' : pbs.get(self.bone.offset)}
    references['constraints'] = [{
        'constraint' : pbs.get(con.source).constraints.get(con.constraint) if pbs.get(con.source) else None,
        'source' : pbs.get(con.source)} for con in self.constraints]
    return references

def get_tailfollow_props(self, armature):
    # try and get a few properties when the rigging is added/refreshed...
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    self.is_editing = True
    if bones.active:
        # all we need is the source bone, it's parent and an optional offset...
        self.bone.source = bones.active.name
    # make sure the constraints have been cleared...
    self.constraints.clear()
    # just a rotational ik constraint... (to the parents first child by default)
    ik = self.constraints.add()
    ik.constraint, ik.source, ik.flavour = "TWIST - IK", self.bone.source, 'IK'
    ik.use_stretch, ik.use_location, ik.use_rotation = False, False, True
    self.is_editing = False

def set_tailfollow_props(self, armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingModules"].preferences
    bbs = armature.data.bones
    rigging = armature.jk_arm.rigging[armature.jk_arm.active]
    rigging.name = "Twist (Tail Follow) - " + self.bone.source
    source_bb = bbs.get(self.bone.source)
    if source_bb:
        self.bone.origin = source_bb.parent.name if source_bb.parent else ""
        self.bone.offset = prefs.affixes.offset + source_bb.name
        # save the original tail and roll of the source...
        self.bone.tail = source_bb.tail_local
        _, angle = source_bb.AxisRollFromMatrix(source_bb.matrix_local.to_3x3())
        self.bone.roll, self.bone.length = angle, source_bb.length
    # just a rotational ik constraint...
    ik = self.constraints[0]
    ik.source = self.bone.source
    # then clear the riggings source bone data...
    rigging.sources.clear()
    # and refresh it for the auto update functionality...
    rigging.get_sources()

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- RIGGING FUNCTIONS ------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def add_tailfollow_bones(self, armature):
    ebs = armature.data.edit_bones
    # get the source, it's parent and the parents parent...
    source_eb, origin_eb = ebs.get(self.bone.source), ebs.get(self.bone.origin)
    # if we are using an offset...
    if self.use_offset:
        # it's a duplicate of the source, parented to the parents parent...
        offset_eb = ebs.new(self.bone.offset)
        offset_eb.head, offset_eb.tail, offset_eb.roll = source_eb.head, source_eb.tail, source_eb.roll
        offset_eb.parent, offset_eb.use_deform = origin_eb, False
        # with the source bone parented to it...
        source_eb.use_connect, source_eb.parent = False, offset_eb

def add_tailfollow_constraints(self, armature):
    pbs = armature.pose.bones
    for constraint in self.constraints:
        pb = pbs.get(constraint.source) # should i check if the pose bone exists? i know it does...
        con = pb.constraints.new(type=constraint.flavour)
        con_props = {cp.identifier : getattr(constraint, cp.identifier) for cp in constraint.bl_rna.properties if not cp.is_readonly}
        # for each of the constraints settings...
        for cp in con.bl_rna.properties:
            if cp.identifier == 'target':
                con.target = armature
            # my collections are indexed, so to avoid my own confusion, name is constraint...
            elif cp.identifier == 'name':
                setattr(con, cp.identifier, con_props['constraint'])
            # if they are in our settings dictionary... (and are not read only?)
            elif cp.identifier in con_props and not cp.is_readonly:
                setattr(con, cp.identifier, con_props[cp.identifier])
        # lock the source bones ik on x and z by default...
        pb.lock_ik_x, pb.lock_ik_y, pb.lock_ik_z = True, False, True
        # and apply the rotation the twist needs to maintain rest consistency...
        bpy.ops.pose.select_all(action='DESELECT')
        pb.bone.select = True
        armature.data.bones.active = pb.bone
        influence = pb.constraints[0].influence
        pb.constraints[0].influence = 1.0
        bpy.ops.pose.armature_apply(selected=True)
        pb.constraints[0].influence = influence
        # if we are using an offset...
        if self.use_offset:
            # jump into edit mode...
            bpy.ops.object.mode_set(mode='EDIT')
            ebs = armature.data.edit_bones
            # to apply any source changes to the offset... (it should stay a duplicate?)
            offset_eb, source_eb = ebs.get(self.bone.offset), ebs.get(self.bone.source)
            offset_eb.head, offset_eb.tail, offset_eb.roll = source_eb.head, source_eb.tail, source_eb.roll
            bpy.ops.object.mode_set(mode='POSE')

def add_tailfollow_shapes(self, armature):
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

def add_tailfollow_groups(self, armature):
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

def add_tailfollow_layers(self, armature):
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

def add_tailfollow_twist(self, armature):
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
    add_tailfollow_bones(self, armature)
    # and add constraints in pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    add_tailfollow_constraints(self, armature)
    # if we are using default shapes or groups, add them...
    if self.use_default_shapes:
        add_tailfollow_shapes(self, armature)
    if self.use_default_groups:
        add_tailfollow_groups(self, armature)
    if self.use_default_layers:
        add_tailfollow_layers(self, armature)
    # give x mirror back... (if it was turned on)
    armature.data.use_mirror_x = is_mirror_x
    # give edit detection back... (if it was turned on)
    armature.jk_arm.use_edit_detection = is_detecting

def remove_tailfollow_twist(self, armature):
    # don't touch the symmetry! (Thanks Jon V.D, you are a star)
    is_mirror_x = armature.data.use_mirror_x
    if is_mirror_x:
        armature.data.use_mirror_x = False
    # first we should get rid of anything in pose mode...
    if armature.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    references = self.get_references()
    # constraints do get removed with bones, but this is just simpler...
    for con_refs in references['constraints']:
        if con_refs['source'] and con_refs['constraint']:
            con_refs['source'].constraints.remove(con_refs['constraint'])
            # conveniently the shapes/groups we need to remove are only on bones with constraints...
            con_refs['source'].custom_shape, con_refs['source'].bone_group = None, None
    # then we might need to kill bones in edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    ebs = armature.data.edit_bones
    # sort out parenting first and return the sources tail and roll...
    source_eb, origin_eb = ebs.get(self.bone.source), ebs.get(self.bone.origin)
    source_eb.tail, source_eb.roll, source_eb.parent = self.bone.tail, self.bone.roll, origin_eb
    # then get rid of the offset if there is one...
    offset_eb = ebs.get(self.bone.offset)
    if offset_eb:
        ebs.remove(offset_eb)
    # then back to pose mode like nothing happened...
    bpy.ops.object.mode_set(mode='POSE')
    # give x mirror back... (if it was turned on)
    armature.data.use_mirror_x = is_mirror_x

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTIES -------------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

class JK_PG_ARM_TailFollow_Constraint(bpy.types.PropertyGroup):
    
    def update_constraint(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].tailfollow
        if not rigging.is_editing:
            rigging.update_rigging(context)

    source: StringProperty(name="Source", description="Name of the bone the constraint is on",
        default="", maxlen=63)

    constraint: StringProperty(name="Constraint", description="Name of the actual constraint",
        default="", maxlen=63)

    flavour: EnumProperty(name="Flavour", description="The type of constraint",
        items=[('COPY_ROTATION', 'Copy Rotation', ""), ('LIMIT_ROTATION', 'Limit Rotation', ""), 
            ('FLOOR', 'Floor', ""), ('IK', 'Inverse Kinematics', ""), ('DAMPED_TRACK', 'Damped Track', "")],
        default='COPY_ROTATION')
    
    subtarget: StringProperty(name="Subtarget", description="Name of the subtarget",
        default="", maxlen=1024, update=update_constraint)

    chain_count: IntProperty(name="Chain Length", description="How many bones are included in the IK effect",
        default=1, min=0)

    use_stretch: BoolProperty(name="Use stretch", description="Use IK stretching", default=False)
    use_location: BoolProperty(name="Use Location", description="Use IK location", default=False)
    use_rotation: BoolProperty(name="Use Rotation", description="Use IK rotation", default=True)

    influence: FloatProperty(name="Influence", description="influence of this constraint", default=0.5, min=0.0, max=1.0, subtype='FACTOR')

class JK_PG_ARM_TailFollow_Bone(bpy.types.PropertyGroup):

    def update_bone(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].tailfollow
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

    source: StringProperty(name="Source", description="Name of the source bone that does the twisting",
        default="", maxlen=63, update=update_bone)

    origin: StringProperty(name="Origin", description="Name of the source bones original parent",
        default="", maxlen=63)

    offset: StringProperty(name="Offset", description="Name of the bone that offsets the sources rotation from its origin",
        default="", maxlen=63)

    length: FloatProperty(name="Length", description="The source bones length before rigging", 
        default=0.0)

    head: FloatVectorProperty(name="Head", description="The source bones head location before rigging",
        default=(0.0, 0.0, 0.0), size=3, subtype='TRANSLATION')

    tail: FloatVectorProperty(name="Tail", description="The source bones tail location before rigging",
        default=(0.0, 0.0, 0.0), size=3, subtype='TRANSLATION')

    roll: FloatProperty(name="Roll", description="The source bones roll before rigging", 
        default=0.0, subtype='ANGLE', unit='ROTATION')

class JK_PG_ARM_TailFollow_Twist(bpy.types.PropertyGroup):
        
    def apply_transforms(self):
        bbs = self.id_data.data.bones
        source_bb = bbs.get(self.bone.source)
        # get the scale from the difference in bone length...
        scale = source_bb.length / self.bone.length
        # then apply that scaling to the saved tail location and length...
        self.bone.tail = self.bone.tail * scale
        self.bone.length = source_bb.length

    bone: PointerProperty(type=JK_PG_ARM_TailFollow_Bone)

    constraints: CollectionProperty(type=JK_PG_ARM_TailFollow_Constraint)

    def get_references(self):
        return get_tailfollow_refs(self)

    def get_sources(self):
        sources = [self.bone.source]
        return sources

    def get_groups(self):
        groups = {
            "Twist Bones" : [self.bone.source], 
            "Offset Bones" : [self.bone.offset]}
        return groups

    def get_shapes(self):
        shapes = {
            "Bone_Shape_Default_Tail_Twist" : [self.bone.source], 
            "Bone_Shape_Default_Tail_Socket" : [self.bone.offset]}
        return shapes


    def get_is_riggable(self):
        # we are going to need to know if the rigging in the properties is riggable...
        armature, is_riggable = self.id_data, True
        bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
        # for this rigging we iterate on some names...
        for name in [self.bone.source, self.constraints[0].subtarget]:
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
            remove_tailfollow_twist(self, self.id_data)

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
            get_tailfollow_props(self, self.id_data)
            self.has_properties = True
        # always set the properties that get calculated from the essentials...
        set_tailfollow_props(self, self.id_data)
        # if we can rig from the properties...
        if self.is_riggable:
            # add the rigging...
            add_tailfollow_twist(self, self.id_data)
            self.is_rigged = True

    use_offset: BoolProperty(name="Use Offset", description="Use an offset bone to inherit limitations and parenting",
        default=False, update=update_rigging)

    use_default_groups: BoolProperty(name="Use Default Groups", description="Do you want this rigging to use Jims default bone groups?",
        default=False, update=update_rigging)

    use_default_shapes: BoolProperty(name="Use Default Shapes", description="Do you want this rigging to use Jims default bone shapes?",
        default=False, update=update_rigging)

    use_default_layers: BoolProperty(name="Use Default Layers", description="Do you want this rigging to use some default armature layers?",
        default=False, update=update_rigging)

import bpy

from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty)

from ... import _functions_, _properties_

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
    ik.chain_count = 1
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
    ebs, pbs = armature.data.edit_bones, armature.pose.bones
    # seems odd but we need to do some pose mode tricks first...
    bpy.ops.object.mode_set(mode='POSE')
    source_pb = pbs.get(self.bone.source)
    # to lock the source bones ik on x and z by default...
    source_pb.lock_ik_x, source_pb.lock_ik_y, source_pb.lock_ik_z = True, False, True
    # and apply the rotation the twist needs to maintain rest consistency...
    bpy.ops.pose.select_all(action='DESELECT')
    source_pb.bone.select = True
    ik = source_pb.constraints.new(type='IK')
    ik.target, ik.subtarget = armature, self.constraints[0].subtarget
    ik.use_stretch, ik.use_location, ik.use_rotation = False, False, True
    bpy.ops.pose.armature_apply(selected=True)
    bpy.ops.pose.constraints_clear()
    bpy.ops.object.mode_set(mode='EDIT')
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

class JK_PG_ARM_TailFollow_Twist(bpy.types.PropertyGroup):
        
    def apply_transforms(self):
        bbs = self.id_data.data.bones
        source_bb = bbs.get(self.bone.source)
        # get the scale from the difference in bone length...
        scale = source_bb.length / self.bone.length
        # then apply that scaling to the saved tail location and length...
        self.bone.tail = self.bone.tail * scale
        self.bone.length = source_bb.length

    bone: PointerProperty(type=_properties_.JK_PG_ARM_Bone)

    constraints: CollectionProperty(type=_properties_.JK_PG_ARM_Constraint)

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

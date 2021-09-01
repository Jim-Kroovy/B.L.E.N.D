import bpy

from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty)

# Much of this code is copy/pasted between the various flavours of rigging, while a little long winded it makes adding new things and updating and troubleshooting a whole lot easier...
# and everyone wants me to do so much i decided it's better that things are easy to edit/create and not as dynamic as they could be...

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTY FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_scalar_refs(self):
    armature, references = self.id_data, {}
    pbs, bbs = armature.pose.bones, armature.data.bones
    references['target'] = {
        'source' : pbs.get(self.target.source), 'origin' : pbs.get(self.target.origin),
        'end' : pbs.get(self.target.end), 'bone' : pbs.get(self.target.bone)}
    references['floor'] = {
        'source' : pbs.get(self.floor.source), 'root' : pbs.get(self.floor.root), 'bone' : pbs.get(self.floor.bone)}
    references['bones'] = [{
        'source' : pbs.get(bone.source), 'origin' : pbs.get(bone.origin)} for bone in self.bones]
    references['constraints'] = [{
        'constraint' : pbs.get(con.source).constraints.get(con.constraint) if pbs.get(con.source) else None,
        'source' : pbs.get(con.source)} for con in self.constraints]
    references['drivers'] = [{
        'source' : pbs.get(drv.source) if drv.is_pose_bone else bbs.get(drv.source),
        'constraint' : pbs.get(drv.source).constraints.get(drv.constraint) if drv.constraint and pbs.get(drv.source) else "",
        'setting' : drv.setting} for drv in self.drivers]
    return references

def get_scalar_parents(self, bones):
    # get recursive parents from the source to the length of the chain...
    parent, parents = bones.get(self.target.end), []
    while len(parents) < self.target.length:# and parent != None:
        parents.append(parent)
        parent = parent.parent if parent else None
    return parents

def get_scalar_deps(self):
    # these are bone names that cannot be roots or have anything relevent parented to them...
    dependents = [self.target.source, self.target.bone, self.target.parent]
    dependents = dependents + [b.source for b in self.bones] + [b.gizmo for b in self.bones] + [b.stretch for b in self.bones]
    return dependents

def get_scalar_props(self, armature):
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    self.is_editing = True
    self.bones.clear()
    self.constraints.clear()
    self.drivers.clear()
    if bones.active:
        # target could be set now...
        self.target.end = bones.active.name
    # get recursive parents...
    parents = get_scalar_parents(self, bones)
    # iterate on them backwards...
    for parent in reversed(parents):
        bone = self.bones.add()
        if parent:
            bone.source = parent.name
        # each source bone has a copy rotation to its gizmo...
        copy_rot = self.constraints.add()
        copy_rot.flavour = 'COPY_ROTATION'
        # gizmo bones copy the stretch bones Y scale...
        copy_sca = self.constraints.add()
        copy_sca.flavour = 'COPY_SCALE'
        # with a limit...
        limit_sca = self.constraints.add()
        limit_sca.flavour = 'LIMIT_SCALE'
        # gizmo bone has a limit rotation to cancel any FK influence...
        limit_rot = self.constraints.add()
        limit_rot.flavour = 'LIMIT_ROTATION'
        # and so does the stretch bone...
        limit_rot = self.constraints.add()
        limit_rot.flavour = 'LIMIT_ROTATION'
    # then iterate on the owners gizmo and stretch...
    for _ in [self.bones[-1].gizmo, self.bones[-1].stretch]:
        # owner gizmo and stretch bones have an ik constraint... (gizmo doesn't stretch)
        self.constraints.add()
        # and copy the targets rotation...
        self.constraints.add()
    # then iterate on the starts gizmo and stretch...
    for _ in [self.bones[0].gizmo, self.bones[0].stretch]:
        # each of them copies the rotation of the control...
        self.constraints.add()
    # add one extra constraint for the floor...
    self.constraints.add()
    # add drivers for all the IK settings we need to drive on the stretch/gizmo bones...
    ik_settings = ["ik_stretch", "lock_ik_x", "lock_ik_y", "lock_ik_z", "ik_stiffness_x", "ik_stiffness_y", "ik_stiffness_z",
        "use_ik_limit_x", "ik_min_x", "ik_max_x","use_ik_limit_y", "ik_min_y", "ik_max_y", "use_ik_limit_z", "ik_min_z", "ik_max_z"]
    for bone in self.bones:
        for _ in [bone.gizmo, bone.stretch]:
            for _ in ik_settings:
                self.drivers.add()
    # aaaand the soft ik drivers on the copy Y scale gizmo constraints...
    for _ in [b.gizmo for b in self.bones]:
        self.drivers.add()
    self.is_editing = False

def set_scalar_props(self, armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingModules"].preferences
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    rigging = armature.jk_arm.rigging[armature.jk_arm.active]
    # get recursive parents...
    parents, self.is_editing = get_scalar_parents(self, bones), True
    parents.reverse()
    ci, di = 0, 0
    for bi in range(0, self.target.length):
        # if we don't have a bone already create one...
        bone = self.bones.add() if len(self.bones) <= bi else self.bones[bi]
        parent = parents[bi]
        if parent:
            bone.source = parent.name
            bone.origin = parent.parent.name if parent.parent else ""
            bone.gizmo = prefs.affixes.gizmo + parent.name
            bone.stretch = prefs.affixes.mech + prefs.affixes.stretch + parent.name
        # each source bone has a copy rotation to its gizmo...
        copy_rot = self.constraints.add() if len(self.constraints) <= ci else self.constraints[ci]
        copy_rot.constraint, copy_rot.flavour = "GIZMO - Copy Rotation", 'COPY_ROTATION'
        copy_rot.source, copy_rot.subtarget = bone.source, bone.gizmo
        copy_rot.target_space, copy_rot.owner_space, copy_rot.mix_mode = 'LOCAL', 'LOCAL', 'BEFORE'
        ci = ci + 1
        # gizmo bones copy the stretch bones Y scale...
        copy_sca = self.constraints.add() if len(self.constraints) <= ci else self.constraints[ci]
        copy_sca.constraint, copy_sca.flavour = "SOFT - Copy Scale", 'COPY_SCALE'
        copy_sca.source, copy_sca.subtarget = bone.gizmo, bone.stretch
        copy_sca.use_x, copy_sca.use_y, copy_sca.use_z = False, True, False
        copy_sca.target_space, copy_sca.owner_space = 'LOCAL', 'LOCAL'
        ci = ci + 1
        # with a limit...
        limit_sca = self.constraints.add() if len(self.constraints) <= ci else self.constraints[ci]
        limit_sca.constraint, limit_sca.flavour = "SOFT - Limit Scale", 'LIMIT_SCALE'
        limit_sca.source, limit_sca.use_min_y, limit_sca.use_max_y = bone.gizmo, True, True
        limit_sca.min_y, limit_sca.max_y, limit_sca.owner_space = 1.0, 2.0, 'LOCAL'
        ci = ci + 1
        # gizmo bone has a limit rotation to cancel any FK influence...
        limit_rot = self.constraints.add() if len(self.constraints) <= ci else self.constraints[ci]
        limit_rot.constraint, limit_rot.flavour = "FK - Limit Rotation", 'LIMIT_ROTATION'
        limit_rot.source, limit_rot.owner_space, limit_rot.influence = bone.gizmo, 'LOCAL', 0.0
        ci = ci + 1
        # and so does the stretch bone...
        limit_rot = self.constraints.add() if len(self.constraints) <= ci else self.constraints[ci]
        limit_rot.constraint, limit_rot.flavour = "FK - Limit Rotation", 'LIMIT_ROTATION'
        limit_rot.source, limit_rot.owner_space, limit_rot.influence = bone.stretch, 'LOCAL', 0.0
        ci = ci + 1
    # set the name of the rigging based on the bones... (needed for drivers)
    rigging.name = "Chain (Scalar) - " + self.bones[0].source + " - " + str(self.target.length)
    # set up the names for the target...
    self.target.source = self.bones[0].source
    self.target.parent = prefs.affixes.target + self.target.source
    self.target.bone = prefs.affixes.target + self.target.end
    self.floor.bone = prefs.affixes.floor + self.target.end
    # then iterate on the owners gizmo and stretch...
    for ni, name in enumerate([self.bones[-1].gizmo, self.bones[-1].stretch]):
        # owner gizmo and stretch bones have an ik constraint... (gizmo doesn't stretch)
        ik = self.constraints.add() if len(self.constraints) <= ci else self.constraints[ci]
        ik.constraint, ik.flavour, ik.source = "SOFT - IK", 'IK', name
        ik.use_stretch, ik.chain_length, ik.subtarget = False if ni == 0 else True, 3, self.target.bone
        ci = ci + 1
        # and copy the targets rotation...
        copy_rot = self.constraints.add() if len(self.constraints) <= ci else self.constraints[ci]
        copy_rot.constraint, copy_rot.flavour, copy_rot.mix_mode = "TARGET - Copy Rotation", 'COPY_ROTATION', 'BEFORE'
        copy_rot.source, copy_rot.subtarget = name, self.target.bone
        copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
        ci = ci + 1
    # then iterate on the starts gizmo and stretch...
    for name in [self.bones[0].gizmo, self.bones[0].stretch]:
        # each of them copies the rotation of the control...
        copy_rot = self.constraints.add() if len(self.constraints) <= ci else self.constraints[ci]
        copy_rot.constraint, copy_rot.flavour, copy_rot.mix_mode = "CONTROL - Copy Rotation", 'COPY_ROTATION', 'BEFORE'
        copy_rot.source, copy_rot.subtarget = name, self.target.parent
        copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
        ci = ci + 1
    # if this chain has a floor for the target...
    floor = self.constraints.add() if len(self.constraints) <= ci else self.constraints[ci]
    floor.constraint, floor.flavour = "FLOOR- Floor", 'FLOOR' if self.use_floor else 'NONE'
    floor.flor_location, floor.use_rotation = 'FLOOR_NEGATIVE_Y', True
    floor.source, floor.subtarget = self.target.bone, self.floor.bone
    self.is_editing = False
    # add drivers for all the IK settings we need to drive on the stretch/gizmo bones...
    ik_settings = ["ik_stretch", "lock_ik_x", "lock_ik_y", "lock_ik_z", "ik_stiffness_x", "ik_stiffness_y", "ik_stiffness_z",
        "use_ik_limit_x", "ik_min_x", "ik_max_x","use_ik_limit_y", "ik_min_y", "ik_max_y", "use_ik_limit_z", "ik_min_z", "ik_max_z"]
    for bone in self.bones:
        for name in [bone.gizmo, bone.stretch]:
            for setting in ik_settings:
                driver = self.drivers.add() if len(self.drivers) <= di else self.drivers[di]
                driver.setting, driver.expression, driver.source = setting, setting, name
                variable = driver.variables.add() if len(driver.variables) == 0 else driver.variables[0]
                variable.name, variable.flavour = setting, 'SINGLE_PROP'
                variable.data_path = 'pose.bones["' + bone.source + '"].' + setting
                di = di + 1
    # aaaand the soft ik drivers on the copy Y scale gizmo constraints...
    for name in [b.gizmo for b in self.bones]:
        driver = self.drivers.add() if len(self.drivers) <= di else self.drivers[di]
        driver.source, driver.constraint = name, "SOFT - Copy Scale"
        driver.setting, driver.expression = 'influence', "ik_softness"
        variable = driver.variables.add() if len(driver.variables) == 0 else driver.variables[0]
        variable.name, variable.flavour = "ik_softness", 'SINGLE_PROP'
        variable.data_path = 'jk_arm.rigging["' + rigging.name + '"].scalar.ik_softness'
        di = di + 1
    # might need to clean up bones when reducing chain length...
    if len(self.bones) > self.target.length:
        while len(self.bones) != self.target.length:
            self.bones.remove(self.target.length)
    # might need to clean up constraints when reducing chain length...
    if len(self.constraints) > ((self.target.length * 5) + 7):
        while len(self.constraints) != ((self.target.length * 5) + 7):
            self.constraints.remove(((self.target.length * 5) + 7))
    # aaand might need to clean up drivers when reducing length...
    if len(self.drivers) > (self.target.length * (len(ik_settings) * 2 + 1)):
        while len(self.drivers) != (self.target.length * (len(ik_settings) * 2 + 1)):
            self.drivers.remove((self.target.length * (len(ik_settings) * 2 + 1)))
    # then clear the riggings source bone data...
    rigging.sources.clear()
    # and refresh it for the auto update functionality...
    rigging.get_sources()

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- RIGGING FUNCTIONS ------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def add_scalar_target(self, armature):
    ebs = armature.data.edit_bones
    # get the targets source and end bones...
    source_eb, end_eb = ebs.get(self.target.source), ebs.get(self.target.end)
    # parent bone is a duplicate of the source...
    parent_eb = ebs.new(self.target.parent)
    parent_eb.head, parent_eb.tail, parent_eb.roll = source_eb.head, source_eb.tail, source_eb.roll
    parent_eb.parent, parent_eb.use_deform = source_eb.parent, False
    # target is created from the end of the chain, parented to the parent...
    target_eb = ebs.new(self.target.bone)
    target_eb.head, target_eb.tail = end_eb.head + (end_eb.y_axis * end_eb.length), end_eb.tail + (end_eb.y_axis * end_eb.length)
    target_eb.roll, target_eb.parent, target_eb.use_deform, target_eb.inherit_scale = end_eb.roll, parent_eb, False, 'NONE'
    # if this target should have a floor bone...
    if self.use_floor:
        # create it on the ground beneath the target with zeroed roll...
        floor_eb = ebs.new(self.floor.bone)
        floor_eb.head = [end_eb.head.x, end_eb.head.y, 0.0]
        floor_eb.tail = [end_eb.head.x, end_eb.head.y, 0.0 - end_eb.length]
        floor_eb.use_deform, floor_eb.roll, floor_eb.parent = False, 0.0, ebs.get(self.floor.root)

def add_scalar_rolls(self, armature):
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

def add_scalar_bones(self, armature):
    ebs = armature.data.edit_bones
    stretch_parent, gizmo_parent = ebs.get(self.bones[0].origin), ebs.get(self.bones[0].origin)
    # add in stretch bones for every bone in the chain...
    for bone in self.bones:
        source_eb = ebs.get(bone.source)
        stretch_eb = ebs.new(bone.stretch)
        stretch_eb.head, stretch_eb.tail, stretch_eb.roll = source_eb.head, source_eb.tail, source_eb.roll
        stretch_eb.parent, stretch_eb.use_deform = stretch_parent, False
        stretch_parent = stretch_eb
        gizmo_eb = ebs.new(bone.gizmo)
        gizmo_eb.head, gizmo_eb.tail, gizmo_eb.roll = source_eb.head, source_eb.tail, source_eb.roll
        gizmo_eb.parent, gizmo_eb.use_deform, gizmo_eb.inherit_scale = gizmo_parent, False, 'ALIGNED'
        gizmo_parent = gizmo_eb

def add_scalar_constraints(self, armature):
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

def add_scalar_drivers(self, armature):
    pbs, bbs = armature.pose.bones, armature.data.bones
    for driver in self.drivers:
        # get the source bone of the driver, if it exists... (from the relevant bones)
        source_b = pbs.get(driver.source) if driver.is_pose_bone else bbs.get(driver.source)
        if source_b:
            # add a driver to the setting...
            if driver.constraint:
                drv = source_b.constraints[driver.constraint].driver_add(driver.setting)
            else:
                drv = source_b.driver_add(driver.setting)
            # and iterate on the variables...
            for variable in driver.variables:
                # adding them, setting their names and types...
                var = drv.driver.variables.new()
                var.name, var.type = variable.name, variable.flavour
                # scalar drivers use all single property variables
                var.targets[0].id = armature
                var.targets[0].data_path = variable.data_path
            # set the drivers expression...
            drv.driver.expression = driver.expression
            # and remove any sneaky curve modifiers...
            for mod in drv.modifiers:
                drv.modifiers.remove(mod)

def add_scalar_shapes(self, armature):
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

def add_scalar_groups(self, armature):
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

def add_scalar_layers(self, armature):
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

def add_scalar_chain(self, armature):
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
    add_scalar_target(self, armature)
    add_scalar_bones(self, armature)
    if self.auto_roll:
        add_scalar_rolls(self, armature)
    # and add constraints and drivers in pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    add_scalar_constraints(self, armature)
    add_scalar_drivers(self, armature)
    # if we are using default shapes or groups, add them...
    if self.use_default_shapes:
        add_scalar_shapes(self, armature)
    if self.use_default_groups:
        add_scalar_groups(self, armature)
    if self.use_default_layers:
        add_scalar_layers(self, armature)
    pbs = armature.pose.bones
    parent_pb = pbs.get(self.target.parent)
    parent_pb.lock_scale = [True, False, True]
    for bone in self.bones:
        source_pb = pbs.get(bone.source)
        if source_pb:
            source_pb.ik_stretch = 0.1
    # give x mirror back... (if it was turned on)
    armature.data.use_mirror_x = is_mirror_x
    # give edit detection back... (if it was turned on)
    armature.jk_arm.use_edit_detection = is_detecting

def remove_scalar_chain(self, armature):
    references = self.get_references()
    # first we should get rid of anything in pose mode...
    if armature.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    # drivers do not get removed when bones/constraints get removed so get rid of them...
    for drv_refs in references['drivers']:
        if drv_refs['constraint']:
            drv_refs['constraint'].driver_remove(drv_refs['setting'])
        elif drv_refs['source']:
            drv_refs['source'].driver_remove(drv_refs['setting'])
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
    ebs, remove_bones = armature.data.edit_bones, []
    target_eb = ebs.get(self.target.bone)
    if target_eb:
        for child in target_eb.children:
            child.parent = ebs.get(self.target.source)
    remove_bones.append(self.target.bone)
    remove_bones.append(self.target.parent)
    remove_bones.append(self.floor.bone)
    for bone in self.bones:
        remove_bones.append(bone.gizmo)
        remove_bones.append(bone.stretch)
    for name in remove_bones:
        remove_eb = ebs.get(name)
        if remove_eb:
            ebs.remove(remove_eb)
    # then return to pose mode like nothing ever happened...
    bpy.ops.object.mode_set(mode='POSE')

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTIES -------------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

class JK_PG_ARM_Scalar_Constraint(bpy.types.PropertyGroup):
    
    def update_constraint(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].scalar
        if not rigging.is_editing:
            rigging.update_rigging(context)

    source: StringProperty(name="Source", description="Name of the bone the constraint is on",
        default="", maxlen=63)

    constraint: StringProperty(name="Constraint", description="Name of the actual constraint",
        default="", maxlen=63)

    flavour: EnumProperty(name="Flavour", description="The type of constraint",
        items=[('NONE', 'None', ""), ('COPY_ROTATION', 'Copy Rotation', ""), ('LIMIT_ROTATION', 'Limit Rotation', ""), 
            ('FLOOR', 'Floor', ""), ('IK', 'Inverse Kinematics', ""), ('DAMPED_TRACK', 'Damped Track', ""),
            ('COPY_SCALE', 'Copy Scale', ""), ('LIMIT_SCALE', 'Limit Scale', ""), ('COPY_TRANSFORMS', 'Copy Transforms', "")],
        default='NONE')
    
    subtarget: StringProperty(name="Subtarget", description="Name of the subtarget. (if any)",
        default="", maxlen=1024)#, update=update_constraint)

    chain_count: IntProperty(name="Chain Length", description="How many bones are included in the IK effect",
        default=3, min=2)

    influence: FloatProperty(name="Influence", description="influence of this constraint", default=1.0, min=0.0, max=1.0, subtype='FACTOR')

    use_x: BoolProperty(name="Use X", description="Use X", default=True)
    invert_x: BoolProperty(name="Invert X", description="Invert X", default=False)
    
    use_limit_x: BoolProperty(name="Use Limit X", description="Use X limit", default=True)
    use_min_x: BoolProperty(name="Use Min X", description="Use minimum X limit", default=False)
    use_max_x: BoolProperty(name="Use Min X", description="Use maximum X limit", default=False)
    
    min_x: FloatProperty(name="Min X", description="Minimum X limit", default=0.0, subtype='ANGLE', unit='ROTATION')
    max_x: FloatProperty(name="Max X", description="Maximum X limit", default=0.0, subtype='ANGLE', unit='ROTATION')

    use_y: BoolProperty(name="Use Y", description="Use Y", default=True)
    invert_y: BoolProperty(name="Invert Y", description="Invert Y", default=False)

    use_limit_y: BoolProperty(name="Use Limit Y", description="Use Y limit", default=True)
    use_min_y: BoolProperty(name="Use Min Y", description="Use minimum Y limit", default=False)
    use_max_y: BoolProperty(name="Use Min Y", description="Use maximum Y limit", default=False)
    
    min_y: FloatProperty(name="Min Y", description="Minimum Y limit", default=0.0, subtype='ANGLE', unit='ROTATION')
    max_y: FloatProperty(name="Max Y", description="Maximum Y limit", default=0.0, subtype='ANGLE', unit='ROTATION')

    use_z: BoolProperty(name="Use Z", description="Use Z limit", default=True)
    invert_z: BoolProperty(name="Invert Z", description="Invert Z", default=False)
    
    use_limit_z: BoolProperty(name="Use Limit Z", description="Use Z limit", default=True)
    use_min_z: BoolProperty(name="Use Min Z", description="Use minimum Z limit", default=False)
    use_max_z: BoolProperty(name="Use Min Z", description="Use maximum Z limit", default=False)

    min_z: FloatProperty(name="Min Z", description="Minimum Z limit", default=0.0, subtype='ANGLE', unit='ROTATION')
    max_z: FloatProperty(name="Max Z", description="Maximum Z limit", default=0.0, subtype='ANGLE', unit='ROTATION')

    use_stretch: BoolProperty(name="Use stretch", description="Use IK stretching", default=False)
    use_location: BoolProperty(name="Use Location", description="Use IK location", default=True)
    use_rotation: BoolProperty(name="Use Rotation", description="Use IK rotation", default=False)

    use_transform_limit: BoolProperty(name="Use Transform", description="Limit transforms to constraint", default=False)

    offset: FloatProperty(name="Offset", description="Offset of floor from target. (in metres)", default=0.0)

    mix_mode: EnumProperty(name="Mix Mode", description="Specify how the copied and existing rotations are combined",
        items=[('REPLACE', "Replace", "Replace original rotation with copied"), 
            ('ADD', "Add", "Add euler component values together"),
            ('BEFORE', "Before Original", "Apply copied rotation before original, as if the constraint target is a parent"),
            ('AFTER', "After Original", "Apply copied rotation after original, as if the constraint target is a child"),
            ('OFFSET', "Fit Curve", "Combine rotations like the original offset checkbox. Does not work well for multiple axis rotations")],
        default='REPLACE')

    floor_location: EnumProperty(name="Floor Location", description="The type of constraint",
        items=[('FLOOR_X', 'X', ""), ('FLOOR_Y', 'Y', ""), ('FLOOR_Z', 'Z', ""), 
            ('FLOOR_NEGATIVE_X', '-X', ""), ('FLOOR_NEGATIVE_Y', '-Y', ""), ('FLOOR_NEGATIVE_Z', '-Z', "")],
        default='FLOOR_NEGATIVE_Y')

    target_space: EnumProperty(name="Target Space", description="Space that target is evaluated in",
        items=[('WORLD', "World Space", ""), ('POSE', "Pose Space", ""), 
            ('LOCAL', "local Space", ""), ('LOCAL_WITH_PARENT', "local With Parent Space", "")],
        default='WORLD')

    owner_space: EnumProperty(name="owner Space", description="Space that owner is evaluated in",
        items=[('WORLD', "World Space", ""), ('POSE', "Pose Space", ""), 
            ('LOCAL', "local Space", ""), ('LOCAL_WITH_PARENT', "local With Parent", "")],
        default='WORLD')

class JK_PG_ARM_Scalar_Variable(bpy.types.PropertyGroup):

    flavour: EnumProperty(name="Type", description="What kind of driver variable is this?",
        items=[('SINGLE_PROP', "Single Property", ""), ('TRANSFORMS', "Transforms", ""),
            ('ROTATION_DIFF', "Rotation Difference", ""), ('LOC_DIFF', "Location Difference", "")])

    data_path: StringProperty(name="Data Path", description="The data path if single property",
        default="")

class JK_PG_ARM_Scalar_Driver(bpy.types.PropertyGroup):

    is_pose_bone: BoolProperty(name="Is Pose Bone", description="Is this drivers source a pose bone or a bone bone?",
        default=True)

    source: StringProperty(name="Source", description="Name of the bone the driver is on",
        default="", maxlen=63)

    constraint: StringProperty(name="Constraint", description="Name of constraint on the bone the driver is on",
        default="", maxlen=63)

    setting: StringProperty(name="Source", description="Name of the bone setting the driver is on",
        default="")

    expression: StringProperty(name="Expression", description="The expression of the driver",
        default="")

    variables: CollectionProperty(type=JK_PG_ARM_Scalar_Variable)

class JK_PG_ARM_Scalar_Floor(bpy.types.PropertyGroup):

    def update_floor(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].scalar
        if rigging.is_rigged and not rigging.is_editing:
            new_root = self.root
            # if the new root is not a bone that would cause dependency issue...
            dep_bones = get_scalar_deps(rigging)
            if new_root not in dep_bones:
                rigging.is_rigged, rigging.is_editing = False, True
                self.root, rigging.is_editing = new_root, False
            rigging.update_rigging(context)

    source: StringProperty(name="Source", description="Name of the source bone the floor is created for",
        default="", maxlen=63)

    bone: StringProperty(name="Bone", description="Name of the actual floor bone",
        default="", maxlen=63)

    root: StringProperty(name="Root", description="Name of the floor bones root. (if any)",
        default="", maxlen=63, update=update_floor)

class JK_PG_ARM_Scalar_Bone(bpy.types.PropertyGroup):

    def update_bone(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].scalar
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
        default="", maxlen=63)#, update=update_bone)

    origin: StringProperty(name="Origin", description="Name of the source bones original parent",
        default="", maxlen=63)

    gizmo: StringProperty(name="Gizmo", description="Name of the gizmo bone that copies the stretch with limits",
        default="", maxlen=63)

    stretch: StringProperty(name="Stretch",description="Name of the stretch bone that smooths kinematics", 
        default="", maxlen=63)

    roll: FloatProperty(name="Roll", description="The source bones roll before rigging", 
        default=0.0, subtype='ANGLE', unit='ROTATION')

class JK_PG_ARM_Scalar_Target(bpy.types.PropertyGroup):
    
    def update_target(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].scalar
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

    end: StringProperty(name="End", description="Name of the bone at the end of the chain",
        default="", maxlen=63, update=update_target)

    bone: StringProperty(name="Bone", description="Name of the actual target",
        default="", maxlen=63)

    parent: StringProperty(name="Parent", description="Name of the targets parent",
        default="", maxlen=63)

    length: IntProperty(name="Chain Length", description="How many bones are included in this IK chain",
        default=3, min=2, update=update_target)

class JK_PG_ARM_Scalar_Chain(bpy.types.PropertyGroup):

    target: PointerProperty(type=JK_PG_ARM_Scalar_Target)

    floor: PointerProperty(type=JK_PG_ARM_Scalar_Floor)

    bones: CollectionProperty(type=JK_PG_ARM_Scalar_Bone)

    constraints: CollectionProperty(type=JK_PG_ARM_Scalar_Constraint)

    drivers: CollectionProperty(type=JK_PG_ARM_Scalar_Driver)

    def get_references(self):
        return get_scalar_refs(self)

    def get_sources(self):
        sources = [bone.source for bone in self.bones]
        return sources

    def get_groups(self):
        groups = {
            "Chain Bones" : [bone.source for bone in self.bones],
            "Gizmo Bones" : [bone.gizmo for bone in self.bones],
            "Mechanic Bones" : [bone.stretch for bone in self.bones],
            "Floor Targets" : [self.floor.bone],
            "Kinematic Targets": [self.target.bone, self.target.parent]}
        return groups

    def get_shapes(self):
        shapes = {
            "Bone_Shape_Default_Head_Button" : [self.floor.bone],
            "Bone_Shape_Default_Head_Flare" : [self.target.parent],
            "Bone_Shape_Default_Head_Socket" : [self.target.bone],
            "Bone_Shape_Default_Medial_Ring_Even" : [bone.gizmo for bone in self.bones],
            "Bone_Shape_Default_Medial_Ring_Odd" : [bone.stretch for bone in self.bones],
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
            remove_scalar_chain(self, self.id_data)

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
            get_scalar_props(self, self.id_data)
            self.has_properties = True
        # always set the properties that get calculated from the essentials...
        set_scalar_props(self, self.id_data)
        # if we can rig from the properties...
        if self.is_riggable:
            # add the rigging...
            add_scalar_chain(self, self.id_data)
            self.is_rigged = True

    auto_roll: BoolProperty(name="Auto Roll", description="Automatically align bone rolls so all bones in the chain transform to the orientation of the target",
        default=False, update=update_rigging)

    use_floor: BoolProperty(name="Use Floor", description="Use a floor bone to prevent the target from passing through the floor",
        default=False, update=update_rigging)

    use_default_groups: BoolProperty(name="Use Default Groups", description="Do you want this rigging to use some default bone groups?",
        default=False, update=update_rigging)

    use_default_shapes: BoolProperty(name="Use Default Shapes", description="Do you want this rigging to use some default bone shapes?",
        default=False, update=update_rigging)

    use_default_layers: BoolProperty(name="Use Default Layers", description="Do you want this rigging to use some default armature layers?",
        default=False, update=update_rigging)

    ik_softness: FloatProperty(name="IK Softness", description="Influence of this chains soft IK. (if not using FK)", 
        default=1.0, min=0.0, max=1.0, subtype='FACTOR')



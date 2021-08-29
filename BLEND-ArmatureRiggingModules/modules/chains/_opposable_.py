import bpy
import math
import mathutils

from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty)

# Much of this code is copy/pasted between the various flavours of rigging, while a little long winded it makes adding new things and updating and troubleshooting a whole lot easier...
# and everyone wants me to do so much i decided it's better that things are easy to edit/create and not as dynamic as they could be...

# STRETCHING = Local Copy Scale Y constraints, IK vs FK remove constraints, offset bone inherit scale

# BETTER IK vs FK = Kill all local bones, Target/pole use child ofs instead of transforms (driver forces FK influence on during FK ???)

# AUTO UPDATE = add get sources function to set props, switch edit detection off during add/remove, clear sources on set props

# HIDING = Copy/paste group and shape functions into rigging props, add group hiding function to rigging properties (also update the add layers, groups and shapes functions)

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTY FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_opposable_refs(self):
    armature, references = self.id_data, {}
    pbs, bbs = armature.pose.bones, armature.data.bones
    references['target'] = {
        'source' : pbs.get(self.target.source), 'origin' : pbs.get(self.target.origin), 'bone' : pbs.get(self.target.bone),
        'offset' : pbs.get(self.target.offset), 'root' : pbs.get(self.target.root)}
    references['floor'] = {
        'source' : pbs.get(self.floor.source), 'root' : pbs.get(self.floor.root), 'bone' : pbs.get(self.floor.bone)}
    references['pole'] = {
        'source' : pbs.get(self.pole.source), 'origin' : pbs.get(self.pole.origin), 'bone' : pbs.get(self.pole.bone), 'root' : pbs.get(self.pole.root)}
    references['bones'] = [{
        'source' : pbs.get(bone.source), 'origin' : pbs.get(bone.origin), 'gizmo' : pbs.get(bone.gizmo),
        'stretch' : pbs.get(bone.stretch), 'offset' : pbs.get(bone.offset)} for bone in self.bones]
    references['constraints'] = [{
        'constraint' : pbs.get(con.source).constraints.get(con.constraint) if pbs.get(con.source) else None,
        'source' : pbs.get(con.source)} for con in self.constraints]
    references['drivers'] = [{
        'source' : pbs.get(drv.source) if drv.is_pose_bone else bbs.get(drv.source),
        'constraint' : pbs.get(drv.source).constraints.get(drv.constraint) if drv.constraint and pbs.get(drv.source) else "",
        'setting' : drv.setting} for drv in self.drivers]
    return references

def get_opposable_deps(self):
    # these are bone names that cannot be roots or have anything relevent parented to them...
    dependents = [self.pole.bone, self.floor.bone,
        self.target.source, self.target.offset, self.target.bone,
        self.bones[0].source, self.bones[0].gizmo, self.bones[0].stretch, self.bones[0].offset,
        self.bones[1].source, self.bones[1].gizmo, self.bones[1].stretch, self.bones[1].offset]
    return dependents

def get_opposable_props(self, armature):
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    self.is_editing = True
    # add two bones, this is a two bone chain...
    self.bones.clear()
    self.bones.add()
    self.bones.add()
    if bones.active:
        # target could be set now...
        self.target.source = bones.active.name
    # if we are getting properties we need clear any existing constraints...
    self.constraints.clear()
    # target offset copies the targets world space rotation... 0
    copy_rot = self.constraints.add()
    copy_rot.constraint, copy_rot.flavour = "TARGET - Copy Rotation", 'COPY_ROTATION'
    # start source bones copy gizmo rotations... 1
    copy_rot = self.constraints.add()
    copy_rot.constraint, copy_rot.flavour = "SOFT - Copy Rotation", 'COPY_ROTATION'
    copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
    # owner source bones copy gizmo rotations... 2
    copy_rot = self.constraints.add()
    copy_rot.constraint, copy_rot.flavour = "SOFT - Copy Rotation", 'COPY_ROTATION'
    copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
    # start gizmo bones copy the start stretch bones Y scale... 3
    copy_sca = self.constraints.add()
    copy_sca.constraint, copy_sca.flavour = "SOFT - Copy Scale", 'COPY_SCALE'
    copy_sca.use_x, copy_sca.use_y, copy_sca.use_z = False, True, False
    copy_sca.target_space, copy_sca.owner_space = 'LOCAL', 'LOCAL'
    # with a limit... 4
    limit_sca = self.constraints.add()
    limit_sca.constraint, limit_sca.flavour = "SOFT - Limit Scale", 'LIMIT_SCALE'
    limit_sca.use_min_y, limit_sca.use_max_y = True, True
    limit_sca.min_y, limit_sca.max_y, limit_sca.owner_space = 1.0, 2.0, 'LOCAL'
    # owner gizmo bones copy the owner stretch bones Y scale... 5
    copy_sca = self.constraints.add()
    copy_sca.constraint, copy_sca.flavour = "SOFT - Copy Scale", 'COPY_SCALE'
    copy_sca.use_x, copy_sca.use_y, copy_sca.use_z = False, True, False
    copy_sca.target_space, copy_sca.owner_space = 'LOCAL', 'LOCAL'
    # with a limit... 6
    limit_sca = self.constraints.add()
    limit_sca.constraint, limit_sca.flavour = "SOFT - Limit Scale", 'LIMIT_SCALE'
    limit_sca.use_min_y, limit_sca.use_max_y = True, True
    limit_sca.min_y, limit_sca.max_y, limit_sca.owner_space = 1.0, 2.0, 'LOCAL'
    # owner gizmo has an ik constraint without stretching... 7
    ik = self.constraints.add()
    ik.constraint, ik.flavour, ik.use_stretch, ik.chain_length = "SOFT - IK", 'IK', False, 2
    # owner gizmo bone has a limit rotation to cancel any FK influence... 8 
    limit_rot = self.constraints.add()
    limit_rot.constraint, limit_rot.flavour = "FK - Limit Rotation", 'LIMIT_ROTATION'
    limit_rot.owner_space, limit_rot.influence = 'LOCAL', 0.0
    # owner stretch bone has an ik constraint with stretching... 9
    ik = self.constraints.add()
    ik.constraint, ik.flavour, ik.use_stretch, ik.chain_length = "SOFT - IK", 'IK', True, 2
    # stretch bone has a limit rotation to cancel any FK influence... 10
    limit_rot = self.constraints.add()
    limit_rot.constraint, limit_rot.flavour = "FK - Limit Rotation", 'LIMIT_ROTATION'
    limit_rot.owner_space, limit_rot.influence = 'LOCAL', 0.0
    # if this chain has a floor for the target, we need a constraint entry for it... 11
    floor = self.constraints.add()
    floor.constraint, floor.flavour = "TARGET - Floor", 'FLOOR' if self.use_floor else 'NONE'
    floor.use_rotation, floor.floor_location = True, 'FLOOR_NEGATIVE_Y'
    floor.target_space, floor.owner_space = 'WORLD', 'WORLD'
    # if this chain is going to use stretch for more than just soft IK... 12
    copy_sca = self.constraints.add()
    copy_sca.constraint, copy_sca.flavour = "STRETCH - Copy Scale", 'COPY_SCALE' if self.use_stretch else 'NONE'
    copy_sca.use_x, copy_sca.use_y, copy_sca.use_z = False, True, False
    copy_sca.target_space, copy_sca.owner_space = 'LOCAL', 'LOCAL'
    # we'll need a couple of copy scale constraints... 13
    copy_sca = self.constraints.add()
    copy_sca.constraint, copy_sca.flavour = "STRETCH - Copy Scale", 'COPY_SCALE' if self.use_stretch else 'NONE'
    copy_sca.use_x, copy_sca.use_y, copy_sca.use_z = False, True, False
    copy_sca.target_space, copy_sca.owner_space = 'LOCAL', 'LOCAL'
    # clear any drivers we might have saved...
    self.drivers.clear()
    ik_settings = ["ik_stretch", "lock_ik_x", "lock_ik_y", "lock_ik_z", "ik_stiffness_x", "ik_stiffness_y", "ik_stiffness_z",
        "use_ik_limit_x", "ik_min_x", "ik_max_x","use_ik_limit_y", "ik_min_y", "ik_max_y", "use_ik_limit_z", "ik_min_z", "ik_max_z"]
    for bone in self.bones:
        for name in [bone.gizmo, bone.stretch]:
            for setting in ik_settings:
                driver = self.drivers.add()
                driver.setting, driver.expression = setting, setting
                variable = driver.variables.add()
                variable.name, variable.flavour = setting, 'SINGLE_PROP'
    # aaaand the soft ik drivers on the copy Y scale gizmo constraints...
    for name in [self.bones[0].gizmo, self.bones[1].gizmo]:
        driver = self.drivers.add()
        driver.setting, driver.expression = 'influence', "ik_softness"
        variable = driver.variables.add()
        variable.name, variable.flavour = "ik_softness", 'SINGLE_PROP'
    # aaaaaaaaaand the fk influence drivers on the owners gizmo and stretch bones...
    for name in [self.bones[1].gizmo, self.bones[1].stretch]:
        driver = self.drivers.add()
        driver.setting, driver.expression = 'influence', "1 - fk_influence"
        variable = driver.variables.add()
        variable.name, variable.flavour = "fk_influence", 'SINGLE_PROP'
    # return is editing to false...
    self.is_editing = False

def set_opposable_props(self, armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingModules"].preferences
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    rigging = armature.jk_arm.rigging[armature.jk_arm.active]
    target = bones.get(self.target.source)
    if target:
        if target.parent:
            self.bones[1].source = target.parent.name
            if target.parent.parent:
                self.bones[0].source = target.parent.parent.name
        self.target.origin = target.parent.name if target.parent else ""
        self.target.offset = prefs.affixes.offset + self.target.source
        self.target.bone = prefs.affixes.target + self.target.source
        self.floor.source = self.target.bone
        self.floor.bone = prefs.affixes.floor + self.target.source
    start = bones.get(self.bones[0].source)
    if start:
        self.bones[0].origin = start.parent.name if start.parent else ""
        self.bones[0].offset = prefs.affixes.offset + self.bones[0].source
        self.bones[0].gizmo = prefs.affixes.gizmo + self.bones[0].source
        self.bones[0].stretch = prefs.affixes.gizmo + prefs.affixes.stretch + self.bones[0].source
        # pole source is the same as the start bone...
        self.pole.source = self.bones[0].source
        self.pole.origin = self.bones[0].origin
        self.pole.bone = prefs.affixes.target + self.pole.source
    owner = bones.get(self.bones[1].source)
    if owner:
        self.bones[1].origin = owner.parent.name if owner.parent else ""
        self.bones[1].offset = prefs.affixes.offset + self.bones[1].source
        self.bones[1].gizmo = prefs.affixes.gizmo + self.bones[1].source
        self.bones[1].stretch = prefs.affixes.gizmo + prefs.affixes.stretch + self.bones[1].source
    # set the name of the rigging based on the bones... (needed for drivers)
    rigging.name = "Chain (Opposable) - " + self.bones[0].source + " - " + self.bones[1].source
    # target offset copies the targets rotation...
    copy_rot = self.constraints[0]
    copy_rot.source, copy_rot.subtarget = self.target.offset, self.target.bone
    # start source bones copy gizmo rotations...
    copy_rot = self.constraints[1]
    copy_rot.source, copy_rot.subtarget = self.bones[0].source, self.bones[0].gizmo
    # owner source bones copy gizmo rotations...
    copy_rot = self.constraints[2]
    copy_rot.source, copy_rot.subtarget = self.bones[1].source, self.bones[1].gizmo
    # start gizmo bones copy the start stretch bones Y scale...
    copy_sca = self.constraints[3]
    copy_sca.source, copy_sca.subtarget = self.bones[0].gizmo, self.bones[0].stretch
    # with a limit...
    limit_sca = self.constraints[4]
    limit_sca.source = self.bones[0].gizmo
    # owner gizmo bones copy the owner stretch bones Y scale...
    copy_sca = self.constraints[5]
    copy_sca.source, copy_sca.subtarget = self.bones[1].gizmo, self.bones[1].stretch
    # with a limit...
    limit_sca = self.constraints[6]
    limit_sca.source = self.bones[1].gizmo
    # owner gizmo has an ik constraint without stretching...
    ik = self.constraints[7]
    ik.source, ik.subtarget, ik.pole_subtarget = self.bones[1].gizmo, self.target.bone, self.pole.bone
    # owner gizmo bone has a limit rotation to cancel any FK influence...
    limit_rot = self.constraints[8]
    limit_rot.source = self.bones[1].gizmo
    # owner stretch bone has an ik constraint with stretching...
    ik = self.constraints[9]
    ik.source, ik.subtarget, ik.pole_subtarget = self.bones[1].stretch, self.target.bone, self.pole.bone
    # owner stretch bone has a limit rotation to cancel any FK influence...
    limit_rot = self.constraints[10]
    limit_rot.source = self.bones[1].stretch
    # if this chain has a floor for the target...
    floor = self.constraints[11]
    floor.flavour = 'FLOOR' if self.use_floor else 'NONE'
    floor.source, floor.subtarget = self.floor.source, self.floor.bone
    # if this chain is going to use stretch for more than just soft IK...
    copy_sca = self.constraints[12]
    copy_sca.flavour = 'COPY_SCALE' if self.use_stretch else 'NONE'
    copy_sca.source, copy_sca.subtarget = self.bones[0].source, self.bones[0].gizmo
    # we'll need a couple of copy scale constraints...
    copy_sca = self.constraints[13]
    copy_sca.flavour = 'COPY_SCALE' if self.use_stretch else 'NONE'
    copy_sca.source, copy_sca.subtarget = self.bones[1].source, self.bones[1].gizmo
    di = 0
    # and all the IK settings we need to drive on the stretch/gizmo bones...
    ik_settings = ["ik_stretch", "lock_ik_x", "lock_ik_y", "lock_ik_z", "ik_stiffness_x", "ik_stiffness_y", "ik_stiffness_z",
        "use_ik_limit_x", "ik_min_x", "ik_max_x","use_ik_limit_y", "ik_min_y", "ik_max_y", "use_ik_limit_z", "ik_min_z", "ik_max_z"]
    for bone in self.bones:
        for name in [bone.gizmo, bone.stretch]:
            for setting in ik_settings:
                driver = self.drivers[di]
                driver.source = name
                driver.variables[0].data_path = 'pose.bones["' + bone.source + '"].' + setting
                di = di + 1
    # aaaand the soft ik drivers on the copy Y scale gizmo constraints...
    for name in [self.bones[0].gizmo, self.bones[1].gizmo]:
        driver = self.drivers[di]
        driver.source, driver.constraint = name, "SOFT - Copy Scale"
        driver.variables[0].data_path = 'jk_arm.rigging["' + rigging.name + '"].opposable.ik_softness'
        di = di + 1
    # aaaaaaaaaand the fk influence drivers on the owners gizmo and stretch bones...
    for name in [self.bones[1].gizmo, self.bones[1].stretch]:
        driver = self.drivers[di]
        driver.source, driver.constraint = name, "FK - Limit Rotation"
        driver.variables[0].data_path = 'jk_arm.rigging["' + rigging.name + '"].opposable.fk_influence'
        di = di + 1
    # then clear the riggings source bone data...
    rigging.sources.clear()
    # and refresh it for the auto update functionality...
    rigging.get_sources()

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- RIGGING FUNCTIONS ------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def add_opposable_target(self, armature):
    ebs = armature.data.edit_bones
    # get the source of the target and pivot bone...
    source_eb = ebs.get(self.target.source)
    # get the targets root (if any)
    root_eb = ebs.get(self.target.root)
    # we are always going to need to create a target bone... (it just gets setup differently depending on subtype)
    target_eb = ebs.new(self.target.bone)
    # create an offset bone and parent the source bone to it...
    offset_eb = ebs.new(self.target.offset)
    offset_eb.head, offset_eb.tail, offset_eb.roll = source_eb.head, source_eb.tail, source_eb.roll
    offset_eb.parent, offset_eb.use_deform = source_eb.parent, False
    source_eb.use_connect, source_eb.parent = False, offset_eb
    if self.use_stretch:
        offset_eb.inherit_scale = 'NONE'
    # if this target should have a floor bone...
    if self.use_floor:
        # create it on the ground beneath the target with zeroed roll...
        floor_eb = ebs.new(self.floor.bone)
        floor_eb.head = [source_eb.head.x, source_eb.head.y, 0.0]
        floor_eb.tail = [source_eb.head.x, source_eb.head.y, 0.0 - source_eb.length]
        floor_eb.use_deform, floor_eb.roll, floor_eb.parent = False, 0.0, ebs.get(self.floor.root)
    # the target has the same orientation as the source...
    target_eb.head, target_eb.tail, target_eb.roll = source_eb.head, source_eb.tail, source_eb.roll
    # but parent it to the root... (if any, it doesn't directly deform)
    target_eb.parent, target_eb.use_deform = root_eb, False

def add_opposable_pole(self, armature):
    #side = armature.jk_arm.rigging[armature.jk_arm.active].side
    source_eb, root_eb = armature.data.edit_bones[self.pole.source], armature.data.edit_bones.get(self.pole.root)
    # get the axis and distance to shift the pole on from it's source bone...
    source_axis = source_eb.x_axis if self.pole.axis.startswith('X') else source_eb.z_axis
    distance = (self.pole.distance * -1) if 'NEGATIVE' in self.pole.axis else (self.pole.distance)
    # create the pole from the head of the start bone along the desired axis...
    pole_eb = armature.data.edit_bones.new(self.pole.bone)
    pole_eb.head = source_eb.head + (source_axis * distance)
    pole_eb.tail = source_eb.tail + (source_axis * distance)
    pole_eb.roll = source_eb.roll #-180.0 if side == 'RIGHT' else 0.0
    pole_eb.parent, pole_eb.use_deform = root_eb, False

def add_opposable_bones(self, armature):
    ebs = armature.data.edit_bones
    # iterate on the bone entries...
    for bi, bone in enumerate(self.bones):
        # get the source bone...
        source_eb = ebs.get(bone.source)
        # if this is the first bone it's the start of the chain...
        if bi == 0:
            # so set the parents to the sources parent...
            gizmo_parent, stretch_parent = source_eb.parent, source_eb.parent
        # add the gizmo bone...
        gizmo_eb = armature.data.edit_bones.new(bone.gizmo)
        gizmo_eb.head, gizmo_eb.tail, gizmo_eb.roll = source_eb.head, source_eb.tail, source_eb.roll
        gizmo_eb.parent, gizmo_eb.use_deform, gizmo_eb.inherit_scale = gizmo_parent, False, 'ALIGNED'
        # set the next gizmos parent to be this gizmo...
        gizmo_parent = gizmo_eb
        # and the stretch bone...
        stretch_eb = armature.data.edit_bones.new(bone.stretch)
        stretch_eb.head, stretch_eb.tail, stretch_eb.roll = source_eb.head, source_eb.tail, source_eb.roll
        stretch_eb.parent, stretch_eb.use_deform = stretch_parent, False
        # set the next stretch parent to be this stretch...
        stretch_parent = stretch_eb

def add_opposable_constraints(self, armature):
    pbs = armature.pose.bones
    for constraint in self.constraints:
        if constraint.flavour != 'NONE':
            pb = pbs.get(constraint.source) # should i check if the pose bone exists? i know it does...
            con = pb.constraints.new(type=constraint.flavour)
            con_props = {cp.identifier : getattr(constraint, cp.identifier) for cp in constraint.bl_rna.properties if not cp.is_readonly}
            # for each of the constraints settings...
            for cp in con.bl_rna.properties:
                if cp.identifier == 'target':
                    con.target = armature
                elif cp.identifier == 'pole_target':
                    con.pole_target = armature
                elif cp.identifier == 'pole_angle':
                    con.pole_angle = self.pole.angle
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

def add_opposable_drivers(self, armature):
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
                # opposable drivers use all single property variables
                var.targets[0].id = armature
                var.targets[0].data_path = variable.data_path
            # set the drivers expression...
            drv.driver.expression = driver.expression
            # and remove any sneaky curve modifiers...
            for mod in drv.modifiers:
                drv.modifiers.remove(mod)

def add_opposable_shapes(self, armature):
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

def add_opposable_groups(self, armature):
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

def add_opposable_layers(self, armature):
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

def add_opposable_chain(self, armature):
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
    add_opposable_target(self, armature)
    add_opposable_pole(self, armature)
    add_opposable_bones(self, armature)
    # and add constraints and drivers in pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    add_opposable_constraints(self, armature)
    add_opposable_drivers(self, armature)
    # if we are using default shapes or groups, add them...
    if self.use_default_shapes:
        add_opposable_shapes(self, armature)
    if self.use_default_groups:
        add_opposable_groups(self, armature)
    if self.use_default_layers:
        add_opposable_layers(self, armature)
    pbs = armature.pose.bones
    # set the default ik stretching of the source bones...
    source_pbs = {pbs.get(self.bones[1].source) : 0.15, pbs.get(self.bones[0].source) : 0.1}
    for source_pb, stretch in source_pbs.items():
        if source_pb:
            source_pb.ik_stretch = stretch
    # give x mirror back... (if it was turned on)
    armature.data.use_mirror_x = is_mirror_x
    # give edit detection back... (if it was turned on)
    armature.jk_arm.use_edit_detection = is_detecting

def remove_opposable_chain(self, armature):
    # we don't want to be removing with "use_fk" enabled... (more of a headache than it's worth lol)
    self.use_auto_fk, self.use_fk = False, False
    references = self.get_references()
    # first we should get rid of anything in pose mode...
    if armature.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    # drivers do not get removed when bones get removed so get rid of them...
    for drv_refs in references['drivers']:
        if drv_refs['constraint']:
            drv_refs['constraint'].driver_remove(drv_refs['setting'])
        elif drv_refs['source']:
            drv_refs['source'].driver_remove(drv_refs['setting'])
    # constraints do get removed with bones, but this is just simpler...
    for con_refs in references['constraints']:
        if con_refs['source'] and con_refs['constraint']:
            con_refs['source'].constraints.remove(con_refs['constraint'])
    # clear shapes/groups from source bones...
    source_pb = references['target']['source']
    source_pb.custom_shape, source_pb.bone_group = None, None
    source_pb = references['bones'][0]['source']
    source_pb.custom_shape, source_pb.bone_group = None, None
    source_pb = references['bones'][1]['source']
    source_pb.custom_shape, source_pb.bone_group = None, None
    # then we need to kill all the chains bones in edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    ebs, remove_bones = armature.data.edit_bones, []
    # so sort out any children of the target bones...
    target_eb = ebs.get(self.target.bone)
    offset_eb = ebs.get(self.target.offset)
    for child in target_eb.children:
        child.parent = ebs.get(self.target.source)
    for child in offset_eb.children:
        child.parent = ebs.get(self.target.origin)
    # and append the target bones for removal...
    remove_bones.append(self.target.bone)
    remove_bones.append(self.target.offset)
    remove_bones.append(self.floor.bone)
    # sort out any children of the pole bones...
    pole_eb = ebs.get(self.pole.bone)
    for child in pole_eb.children:
        child.parent = ebs.get(self.pole.source)
    # and append the pole bone to be removed...
    remove_bones.append(self.pole.bone)
    # append the gizmo and stretch bones...
    remove_bones.append(self.bones[0].gizmo)
    remove_bones.append(self.bones[0].stretch)
    remove_bones.append(self.bones[1].gizmo)
    remove_bones.append(self.bones[1].stretch)
    # iterate on the names of the bones to be removed...
    for name in remove_bones:
        # if they exist...
        eb = ebs.get(name)
        if eb:
            # remove them...
            ebs.remove(eb)
    # hop back to pose mode...
    bpy.ops.object.mode_set(mode='POSE')

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- ANIMATION FUNCTIONS ----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def set_opposable_fk_constraints(armature, target_pb, source_pb=None):
    # save and clear any armature transforms... (quick fix for world transform issue?)
    armature_matrix = armature.matrix_world.copy()
    armature.matrix_world = mathutils.Matrix()
    if source_pb:
        limit_loc = target_pb.constraints.new('LIMIT_LOCATION')
        limit_loc.name, limit_loc.show_expanded = "FK - Limit Location", False
        limit_loc.use_min_x, limit_loc.use_min_y, limit_loc.use_min_z = True, True, True
        limit_loc.use_max_x, limit_loc.use_max_y, limit_loc.use_max_z = True, True, True
        limit_loc.owner_space = 'LOCAL_WITH_PARENT'

        limit_rot = target_pb.constraints.new('LIMIT_ROTATION')
        limit_rot.name, limit_rot.show_expanded = "FK - Limit Rotation", False
        limit_rot.use_limit_x, limit_rot.use_limit_y, limit_rot.use_limit_z = True, True, True
        limit_rot.owner_space = 'LOCAL_WITH_PARENT'

        limit_sca = target_pb.constraints.new('LIMIT_SCALE')
        limit_sca.name, limit_sca.show_expanded = "FK - Limit Scale", False
        limit_sca.use_min_x, limit_sca.use_min_y, limit_sca.use_min_z = True, True, True
        limit_sca.use_max_x, limit_sca.use_max_y, limit_sca.use_max_z = True, True, True
        limit_sca.min_x, limit_sca.min_y, limit_sca.min_z = 1.0, 1.0, 1.0
        limit_sca.max_x, limit_sca.max_y, limit_sca.max_z = 1.0, 1.0, 1.0
        limit_sca.owner_space = 'LOCAL_WITH_PARENT'

        child_of = target_pb.constraints.new("CHILD_OF")
        child_of.name, child_of.show_expanded = "FK - Child Of", False
        child_of.target, child_of.subtarget = armature, source_pb.name
        child_of.inverse_matrix = source_pb.bone.matrix_local.inverted() @ armature.matrix_world.inverted()
        # and lock the targets transforms so the user can't mess them up...
        target_pb.lock_location, target_pb.lock_rotation = [True, True, True], [True, True, True]
        target_pb.lock_rotation_w, target_pb.lock_scale = True, [True, True, True]
    
    else:
        cons = [target_pb.constraints.get("FK - Limit Location"), target_pb.constraints.get("FK - Limit Rotation"),
            target_pb.constraints.get("FK - Limit Scale"), target_pb.constraints.get("FK - Child Of")]
        for con in cons:
            if con:
                target_pb.constraints.remove(con)

        target_pb.lock_location, target_pb.lock_rotation = [False, False, False], [False, False, False]
        target_pb.lock_rotation_w, target_pb.lock_scale = False, [False, False, False]
    
    # set back any armature transforms... (quick fix for world transform issue?)
    armature.matrix_world = armature_matrix

def set_opposable_ik_to_fk(self, armature):
    references = self.get_references()
    # get the references and matrices of the chain bones...
    start, owner = references['bones'][0], references['bones'][1]
    target, pole = references['target'], references['pole']
    
    # remove the start and owner bones constraints while keeping transforms...
    start_mat, owner_mat = start['source'].matrix.copy(), owner['source'].matrix.copy()
    start['source'].constraints.remove(references['constraints'][1]['constraint'])
    owner['source'].constraints.remove(references['constraints'][2]['constraint'])
    # if this is a stretchy chain....
    if self.use_stretch:
        # need to get rid of the stretch constraints as well...
        start['source'].constraints.remove(references['constraints'][12]['constraint'])
        owner['source'].constraints.remove(references['constraints'][13]['constraint'])
    start['source'].matrix, owner['source'].matrix = start_mat, owner_mat
    
    # give the owners gizmo bone a copy rot to the source bone...
    copy_rot = owner['gizmo'].constraints.new("COPY_ROTATION")
    copy_rot.name, copy_rot.show_expanded = "FK - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = armature, owner['source'].name
    copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
    
    # and give the stretch bone a copy rot to the source bone...
    copy_rot = owner['stretch'].constraints.new("COPY_ROTATION")
    copy_rot.name, copy_rot.show_expanded = "FK - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = armature, owner['source'].name
    copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
    
    # kill the copy rotation on the targets offset bone and set its matrix to what it was...
    offset_mat = target['offset'].matrix.copy()
    target['offset'].constraints.remove(references['constraints'][0]['constraint'])
    target['offset'].matrix = offset_mat
    # then give the target bone a child of to the offset...
    set_opposable_fk_constraints(armature, target['bone'], source_pb=target['offset'])
    # and the pole a child of to its source...
    set_opposable_fk_constraints(armature, pole['bone'], source_pb=pole['source'])

def set_opposable_fk_to_ik(self, armature):
    references = self.get_references()
    start, owner = references['bones'][0], references['bones'][1]
    target, pole = references['target'], references['pole']
    # remove the target and poles FK child of constraints while keeping transforms...
    target_mat, pole_mat = target['bone'].matrix.copy(), pole['bone'].matrix.copy()
    set_opposable_fk_constraints(armature, target['bone'])
    set_opposable_fk_constraints(armature, pole['bone'])
    target['bone'].matrix, pole['bone'].matrix = target_mat, pole_mat

    # give the offset back its copy rotation to the target...
    copy_rot = target['offset'].constraints.new(type='COPY_ROTATION')
    copy_rot.name, copy_rot.show_expanded = "TARGET - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = armature, target['bone'].name

    # remove the owners gizmo and stretch constraints while keeping transforms...
    gizmo_mat, stretch_mat = owner['gizmo'].matrix.copy(), owner['stretch'].matrix.copy()
    owner['gizmo'].constraints.remove(owner['gizmo'].constraints.get("FK - Copy Rotation"))
    owner['stretch'].constraints.remove(owner['stretch'].constraints.get("FK - Copy Rotation"))
    owner['gizmo'].matrix, owner['stretch'].matrix = gizmo_mat, stretch_mat
    
    # give the start source bone back its copy rotation to its gizmo...
    copy_rot = start['source'].constraints.new("COPY_ROTATION")
    copy_rot.name, copy_rot.show_expanded = "SOFT - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = armature, start['gizmo'].name
    copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
    # if this is a stretchy chain....
    if self.use_stretch:
        # give the start bone back it's copy scale...
        copy_sca = start['source'].constraints.new("COPY_SCALE")
        copy_sca.name, copy_sca.show_expanded = "STRETCH - Copy Scale", False
        copy_sca.target, copy_sca.subtarget = armature, start['gizmo'].name
        copy_sca.use_x, copy_sca.use_y, copy_sca.use_z = False, True, False
        copy_sca.target_space, copy_sca.owner_space = 'LOCAL', 'LOCAL'
    
    # give the owner source bone back its copy rotation to its gizmo...
    copy_rot = owner['source'].constraints.new("COPY_ROTATION")
    copy_rot.name, copy_rot.show_expanded = "SOFT - Copy Rotation", False
    copy_rot.target, copy_rot.subtarget = armature, owner['gizmo'].name
    copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
    # if this is a stretchy chain....
    if self.use_stretch:
        # also give the owner bone back it's copy scale...
        copy_sca = owner['source'].constraints.new("COPY_SCALE")
        copy_sca.name, copy_sca.show_expanded = "STRETCH - Copy Scale", False
        copy_sca.target, copy_sca.subtarget = armature, owner['gizmo'].name
        copy_sca.use_x, copy_sca.use_y, copy_sca.use_z = False, True, False
        copy_sca.target_space, copy_sca.owner_space = 'LOCAL', 'LOCAL'

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTIES -------------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

class JK_PG_ARM_Opposable_Constraint(bpy.types.PropertyGroup):

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
        default="", maxlen=1024)

    pole_subtarget: StringProperty(name="Pole Target", description="Name of the pole target. (if any)",
        default="", maxlen=1024)

    chain_count: IntProperty(name="Chain Length", description="How many bones are included in the IK effect",
        default=2, min=0)

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

class JK_PG_ARM_Opposable_Variable(bpy.types.PropertyGroup):

    flavour: EnumProperty(name="Type", description="What kind of driver variable is this?",
        items=[('SINGLE_PROP', "Single Property", ""), ('TRANSFORMS', "Transforms", ""),
            ('ROTATION_DIFF', "Rotation Difference", ""), ('LOC_DIFF', "Location Difference", "")])

    data_path: StringProperty(name="Data Path", description="The data path if single property",
        default="")

class JK_PG_ARM_Opposable_Driver(bpy.types.PropertyGroup):

    is_pose_bone: BoolProperty(name="Is Pose Bone", description="Is this drivers source a pose bone or a bone bone?",
        default=True)

    source: StringProperty(name="Source", description="Name of the bone the driver is on",
        default="", maxlen=63)

    constraint: StringProperty(name="Constraint", description="Name of constraint on the bone the driver is on",
        default="", maxlen=63)

    setting: StringProperty(name="Setting", description="Name of the setting the driver is on",
        default="")

    expression: StringProperty(name="Expression", description="The expression of the driver",
        default="")

    variables: CollectionProperty(type=JK_PG_ARM_Opposable_Variable)

class JK_PG_ARM_Opposable_Floor(bpy.types.PropertyGroup):

    def update_floor(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].opposable
        if rigging.is_rigged and not rigging.is_editing:
            new_root = self.root
            # if the new root is not a bone that would cause dependency issue...
            dep_bones = get_opposable_deps(rigging)
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

class JK_PG_ARM_Opposable_Target(bpy.types.PropertyGroup):
    
    def update_target(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].opposable
        if rigging.is_rigged and not rigging.is_editing:
            # changing the source is a little complicated because we need it to remove/update rigging...
            bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
            # deselect everything depending on mode...
            if armature.mode == 'EDIT':
                bpy.ops.armature.select_all(action='DESELECT')
            elif armature.mode == 'POSE':
                bpy.ops.pose.select_all(action='DESELECT')
            # make the new source active and save a reference of it...
            bones.active = bones.get(self.source)
            new_source, new_root = self.source, self.root
            # if the new source exists, has a parent and that parent has a parent...
            if bones.get(new_source) and bones.get(new_source).parent and bones.get(new_source).parent.parent:
                # remove the rigging and set "is_editing" true (removing sets self.source back to what it was from saved refs)
                rigging.is_rigged, rigging.is_editing = False, True
                # while "is_editing" is false set the new source to what we actually want it to be...
                self.source, rigging.is_editing = new_source, False
                # then we can update the rigging...
                rigging.update_rigging(context)
                # if the new root is not a bone that would cause dependency issue...
                dep_bones = get_opposable_deps(rigging)
                if rigging.is_rigged and new_root not in dep_bones:
                    # do the same thing for the root that we just did for the source...
                    rigging.is_rigged, rigging.is_editing = False, True
                    self.root, rigging.is_editing = new_root, False
                    # i don't really want to the update again but the source needs to be set...
                    rigging.update_rigging(context)
            else:
                rigging.update_rigging(context)
        elif not rigging.is_editing:
            rigging.update_rigging(context)

    source: StringProperty(name="Source", description="Name of the source bone the target is created from",
        default="", maxlen=63, update=update_target)

    origin: StringProperty(name="Origin", description="Name of the source bones original parent",
        default="", maxlen=63)

    bone: StringProperty(name="Bone", description="Name of the actual target",
        default="", maxlen=63)

    root: StringProperty(name="Root",description="The targets root bone. (if any)", 
        default="", maxlen=63, update=update_target)

    offset: StringProperty(name="Offset", description="Name of the bone that offsets the targets rotation from its source bone",
        default="", maxlen=63)

class JK_PG_ARM_Opposable_Pole(bpy.types.PropertyGroup):

    def update_pole(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].opposable
        if rigging.is_rigged and not rigging.is_editing:
            new_root = self.root
            # if the new root is not a bone that would cause dependency issue...
            dep_bones = get_opposable_deps(rigging)
            if new_root not in dep_bones:
                rigging.is_rigged, rigging.is_editing = False, True
                self.root, rigging.is_editing = new_root, False
            rigging.update_rigging(context)

    source: StringProperty(name="Source", description="Name of the source bone the target is created from",
        default="", maxlen=63)

    origin: StringProperty(name="Origin", description="Name of the source bones original parent",
        default="", maxlen=63)

    bone: StringProperty(name="Bone", description="Name of the actual target",
        default="", maxlen=63)

    root: StringProperty(name="Root",description="The targets root bone. (if any)", 
        default="", maxlen=63)

    axis: EnumProperty(name="Axis", description="The local axis of the start bone that the pole target is created from",
        items=[('X', 'X axis', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X axis', "", "CON_LOCLIKE", 1),
        #('Y', 'Y axis', "", "CON_LOCLIKE", 2),
        #('Y_NEGATIVE', '-Y axis', "", "CON_LOCLIKE", 3),
        ('Z', 'Z axis', "", "CON_LOCLIKE", 4),
        ('Z_NEGATIVE', '-Z axis', "", "CON_LOCLIKE", 5)],
        default='X', update=update_pole)

    def get_pole_angle(self):
        angle = -3.141593 if self.axis == 'X_NEGATIVE' else 1.570796 if self.axis == 'Z' else -1.570796 if self.axis == 'Z_NEGATIVE' else 0.0
        return angle

    angle: FloatProperty(name="Angle", description="The angle of the IK pole target. (degrees)", 
        default=0.0, subtype='ANGLE', get=get_pole_angle)

    distance: FloatProperty(name="distance", description="The distance the pole target is from the IK parent. (in metres)", 
        default=0.25, update=update_pole)

class JK_PG_ARM_Opposable_Bone(bpy.types.PropertyGroup):

    def update_bone(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].opposable
        if rigging.is_rigged and not rigging.is_editing:
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
            # remove the rigging and set "is_editing" true (removing sets the source back to what it was from saved refs)
            rigging.is_rigged, rigging.is_editing = False, True
            # while is_editing is false set the new source to what we want it to be...
            self.source, rigging.is_editing = new_source, False
            # then we can update the rigging...
            rigging.update_rigging(context)

    source: StringProperty(name="Source", description="Name of the source bone",
        default="", maxlen=63, update=update_bone)

    origin: StringProperty(name="Origin", description="Name of the source bones original parent",
        default="", maxlen=63)

    gizmo: StringProperty(name="Gizmo", description="Name of the gizmo bone that copies the stretch with limits",
        default="", maxlen=63)

    stretch: StringProperty(name="Stretch",description="Name of the stretch bone that smooths kinematics", 
        default="", maxlen=63)

    use_offset: BoolProperty(name="Use Offset", description="Use an offset bone to provide an independent pivot from the inverse kinematics",
        default=False, update=update_bone)

    offset: StringProperty(name="Offset", description="Name of the bone that offsets the targets rotation from its source bone",
        default="", maxlen=63)

class JK_PG_ARM_Opposable_Chain(bpy.types.PropertyGroup):

    def apply_transforms(self):
        # when applying transforms we need to reset the pole distance...
        armature = self.id_data
        bbs = armature.data.bones
        # this will trigger a full update of the rigging and should apply all transform differences...
        source_bb, pole_bb = bbs.get(self.pole.source), bbs.get(self.pole.bone)
        start, end = source_bb.head_local, pole_bb.head_local
        distance = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2 + (end[2] - start[2])**2)
        self.pole.distance = abs(distance)

    def hide_groups(self, group, hide):
        bone_groups = self.get_groups()
        bones = self.id_data.data.edit_bones if self.id_data.mode == 'EDIT' else self.id_data.data.bones
        # if we are hiding a group this rigging uses...
        if group in bone_groups:
            # iterate on all the bones in that group...
            for name in bone_groups[group]:
                bone = bones.get(name)
                # and show/hide them...
                if bone:
                    bone.hide = hide

    target: PointerProperty(type=JK_PG_ARM_Opposable_Target)

    pole: PointerProperty(type=JK_PG_ARM_Opposable_Pole)

    bones: CollectionProperty(type=JK_PG_ARM_Opposable_Bone)

    constraints: CollectionProperty(type=JK_PG_ARM_Opposable_Constraint)

    drivers: CollectionProperty(type=JK_PG_ARM_Opposable_Driver)

    floor: PointerProperty(type=JK_PG_ARM_Opposable_Floor)

    def get_references(self):
        return get_opposable_refs(self)

    def get_sources(self):
        sources = [self.bones[0].source, self.bones[1].source, self.target.source]
        return sources

    def get_groups(self):
        groups = {
                "Chain Bones" : [self.bones[0].source, self.bones[1].source],
                "Gizmo Bones" : [self.bones[0].gizmo, self.bones[1].gizmo],
                "Mechanic Bones" : [self.bones[0].stretch, self.bones[1].stretch],
                "Offset Bones" : [self.target.offset],
                "Control Bones" : [self.target.source],
                "Floor Targets" : [self.floor.bone],
                "Kinematic Targets": [self.target.bone, self.pole.bone]}
        return groups

    def get_shapes(self):
        shapes = {
            "Bone_Shape_Default_Head_Button" : [self.floor.bone],
            "Bone_Shape_Default_Tail_Sphere" : [self.pole.bone],
            "Bone_Shape_Default_Medial_Ring" : [self.bones[0].source, self.bones[1].source],
            "Bone_Shape_Default_Head_Ring" : [self.target.source],
            "Bone_Shape_Default_Medial_Ring_Even" : [self.bones[0].gizmo, self.bones[1].gizmo],
            "Bone_Shape_Default_Medial_Ring_Odd" : [self.bones[0].stretch, self.bones[1].stretch],
            "Bone_Shape_Default_Head_Flare" : [self.target.bone],
            "Bone_Shape_Default_Head_Socket" : [self.target.offset]}
        return shapes

    def get_is_riggable(self):
        # we are going to need to know if the rigging in the properties is riggable...
        armature, is_riggable = self.id_data, True
        bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
        # for this rigging we iterate on some names...
        for name in [self.target.source, self.bones[0].source, self.bones[1].source]:
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
            remove_opposable_chain(self, self.id_data)

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
            get_opposable_props(self, self.id_data)
            self.has_properties = True
        # always set the properties that get calculated from the essentials...
        set_opposable_props(self, self.id_data)
        # if we can rig from the properties...
        if self.is_riggable:
            # add the rigging...
            add_opposable_chain(self, self.id_data)
            self.is_rigged = True

    use_stretch: BoolProperty(name="Use Stretch", description="Use stretching on the source bones",
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

    fk_influence: FloatProperty(name="FK Influence", description="Influence of the FK transforms forced onto the IK when switching. (if any)", 
        default=1.0, min=0.0, max=1.0, subtype='FACTOR')

    last_fk: BoolProperty(name="Last FK", description="The last 'Use FK' boolean",
        default=False)

    def update_use_fk(self, context):
        if self.use_fk != self.last_fk:
            self.fk_influence = 1.0
            if self.use_fk:
                #print("IK TO FK")
                set_opposable_ik_to_fk(self, self.id_data)
            else:
                #print("FK TO IK")
                set_opposable_fk_to_ik(self, self.id_data)
            self.last_fk = self.use_fk
            # add in auto keying logic here???
            # if self.id_data.jk_arm.last_frame == bpy.context.scene.frame_float:

    use_fk: BoolProperty(name="Use FK",description="Switch between IK vs FK for this IK chain",
        default=False, update=update_use_fk)
    
    use_auto_fk: BoolProperty(name="Auto Switch", description="Automatically switch between IK and FK depending on bone selection. (Defaults to IK)",
        default=False)

    def get_is_auto_fk(self):
        bbs = self.id_data.data.bones
        names = [self.target.offset, self.bones[0].source, self.bones[1].source]
        selected = [name for name in names if bbs.get(name) and bbs.get(name).select]
        return True if selected else False

    is_auto_fk: BoolProperty(name="Is Auto FK", description="Should we automatically switch to and from FK?",
        get=get_is_auto_fk)
    
    use_auto_key: BoolProperty(name="Auto Key Switch",description="Automatically keyframe switching between IK and FK",
        default=False)
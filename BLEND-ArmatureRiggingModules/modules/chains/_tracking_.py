import bpy
import math
from mathutils import Vector

from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty)

# Much of this code is copy/pasted between the various flavours of rigging, while a little long winded it makes adding new things and updating and troubleshooting a whole lot easier...
# and everyone wants me to do so much i decided it's better that things are easy to edit/create and not as dynamic as they could be...

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTY FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_tracking_refs(self):
    armature, references = self.id_data, {}
    pbs, bbs = armature.pose.bones, armature.data.bones
    references['target'] = {
        'source' : pbs.get(self.target.source), 'origin' : pbs.get(self.target.origin), 'bone' : pbs.get(self.target.bone),
        'offset' : pbs.get(self.target.offset), 'control' : pbs.get(self.target.control), 'root' : pbs.get(self.target.root)}
    references['bones'] = [{
        'source' : pbs.get(bone.source), 'origin' : pbs.get(bone.origin), 'gizmo' : pbs.get(bone.gizmo), 'stretch' : pbs.get(bone.gizmo)} for bone in self.bones]
    references['constraints'] = [{
        'constraint' : pbs.get(con.source).constraints.get(con.constraint) if pbs.get(con.source) else None,
        'source' : pbs.get(con.source)} for con in self.constraints]
    references['drivers'] = [{
        'source' : pbs.get(drv.source) if drv.is_pose_bone else bbs.get(drv.source),
        'constraint' : pbs.get(drv.source).constraints.get(drv.constraint) if drv.constraint and pbs.get(drv.source) else "",
        'setting' : drv.setting} for drv in self.drivers]
    return references

def get_tracking_parents(self, bones):
    # get recursive parents from the source to the length of the chain...
    parent, parents = bones.get(self.target.source), []
    while len(parents) < self.length:# and parent != None:
        parents.append(parent)
        parent = parent.parent if parent else None
    return parents

def get_tracking_props(self, armature):
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    self.is_editing = True
    self.bones.clear()
    for _ in range(self.length - 1):
        self.bones.add()
    self.constraints.clear()
    self.drivers.clear()
    if bones.active:
        # target could be set now...
        self.target.source = bones.active.name
    # if we are getting properties we need to clear any existing constraints and drivers...
    self.constraints.clear()
    # the control has an IK constraint...
    ik = self.constraints.add()
    ik.source, ik.flavour, ik.constraint = self.target.control, 'IK', "TRACKING - IK"
    # and a locked track for X...
    lock_track = self.constraints.add()
    lock_track.source, lock_track.flavour, lock_track.constraint = self.target.control, 'LOCKED_TRACK', "LOCK X - Locked Track"
    # and a locked track for the Z...
    lock_track = self.constraints.add()
    lock_track.source, lock_track.flavour, lock_track.constraint = self.target.control, 'LOCKED_TRACK', "LOCK Z - Locked Track"
    # the offset has it's own IK to keep the end tracking independently...
    ik = self.constraints.add()
    ik.source, ik.flavour, ik.constraint = self.target.offset, 'IK', "TRACKING - IK"
    # and a copy rotation to the control to pick up the locked rotations... (if used)
    copy_rot = self.constraints.add()
    copy_rot.source, copy_rot.flavour, copy_rot.constraint = self.target.offset, 'COPY_ROTATION', "TRACK - Copy Rotation"
    # the controls IK limit X can only be true when not lock tracking Z
    driver = self.drivers.add()
    driver.setting = "use_ik_limit_x"
    variable = driver.variables.add()
    variable.name, variable.flavour = "lock_z", 'SINGLE_PROP'
    # the controls IK limit Z can only be true when not lock tracking X
    driver = self.drivers.add()
    driver.setting = "use_ik_limit_z"
    variable = driver.variables.add()
    variable.name, variable.flavour = "lock_x", 'SINGLE_PROP'
    # the controls IK limit Z can only be true when not lock tracking X
    driver = self.drivers.add()
    driver.setting = "influence"
    variable = driver.variables.add()
    variable.name, variable.flavour = "lock_z", 'SINGLE_PROP'
    # the controls IK limit Z can only be true when not lock tracking X
    driver = self.drivers.add()
    driver.setting = "influence"
    variable = driver.variables.add()
    variable.name, variable.flavour = "lock_x", 'SINGLE_PROP'
    # then get recursive parents...
    parents = get_tracking_parents(self, bones)
    ik_settings = ["ik_stretch", "ik_min_x", "ik_max_x","ik_min_y", "ik_max_y", "ik_min_z", "ik_max_z", "ik_stiffness_x", "ik_stiffness_y", "ik_stiffness_z"]
    # and iterate on them backwards...
    for parent in reversed(parents):
        bone = self.bones.add()
        if parent:
            bone.source = parent.name
        # every source has a copy rotation to it's gizmo...
        copy_rot = self.constraints.add()
        copy_rot.source, copy_rot.flavour, copy_rot.constraint = bone.source, 'COPY_ROTATION', "TRACK - Copy Rotation"
        # each gizmo in the chain has an IK constraint...
        ik = self.constraints.add()
        ik.source, ik.flavour, ik.constraint = bone.gizmo, 'IK', "TRACKING - IK"
        # and a copy Y rotation... (unless it's the end of the chain)
        if parent != bones.active:
            copy_rot = self.constraints.add()
            copy_rot.source, copy_rot.flavour, copy_rot.constraint = bone.gizmo, 'COPY_ROTATION', "TRACK - Copy Rotation"
    # we need drivers for all the gizmo and stretch bones...
    for bone in self.bones:
        for name in [bone.gizmo, bone.stretch]:
            # as their ik settings are driven from the sources...
            for setting in ik_settings:
                driver = self.drivers.add()
                driver.setting = setting
                if setting in ["ik_stretch", "ik_stiffness_x", "ik_stiffness_y", "ik_stiffness_z"]:
                    # one variable for the ik stretch setting...
                    variable = driver.variables.add()
                    variable.name, variable.flavour = setting, 'SINGLE_PROP'
                else:
                    # one variable for the lean/turn property...
                    variable = driver.variables.add()
                    variable.name, variable.flavour = 'turn' if setting.endswith("_y") else 'lean', 'SINGLE_PROP'
                    # and another for the sources min/max ik setting...
                    variable = driver.variables.add()
                    variable.name, variable.flavour = setting, 'SINGLE_PROP'
    
    self.is_editing = False

def set_tracking_props(self, armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingModules"].preferences
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    rigging = armature.jk_arm.rigging[armature.jk_arm.active]
    self.is_editing = True
    # set the targets bone names...
    self.target.bone = prefs.affixes.target + "TRACK_" + self.target.source
    self.target.control = prefs.affixes.control + "TRACK_" + self.target.source
    self.target.offset = prefs.affixes.offset + "TRACK_" + self.target.source
    # the control has an IK constraint...
    ik = self.constraints[0]
    ik.source, ik.flavour, ik.constraint = self.target.control, 'IK', "TRACK - IK"
    ik.subtarget, ik.chain_count = self.target.bone, self.length
    # and a locked track for X...
    lock_track = self.constraints[1]
    lock_track.source, lock_track.flavour, lock_track.constraint = self.target.control, 'LOCKED_TRACK', "LOCK X - Locked Track"
    lock_track.subtarget, lock_track.track_axis, lock_track.lock_axis, lock_track.influence = self.target.bone, 'TRACK_Y', 'LOCK_X', 0.0
    # and a locked track for the Z...
    lock_track = self.constraints[2]
    lock_track.source, lock_track.flavour, lock_track.constraint = self.target.control, 'LOCKED_TRACK', "LOCK Z - Locked Track"
    lock_track.subtarget, lock_track.track_axis, lock_track.lock_axis, lock_track.influence = self.target.bone, 'TRACK_Y', 'LOCK_Z', 0.0
    # the offset has it's own IK to keep the end tracking independently...
    ik = self.constraints[3]
    ik.source, ik.flavour, ik.constraint = self.target.offset, 'IK', "TRACK - IK"
    ik.subtarget, ik.use_stretch, ik.chain_count = self.target.bone, False, 1
    # and a copy rotation to the control to pick up the locked rotations... (if used)
    copy_rot = self.constraints[4]
    copy_rot.source, copy_rot.flavour, copy_rot.constraint = self.target.offset, 'COPY_ROTATION', "TRACK - Copy Rotation"
    copy_rot.subtarget, copy_rot.target_space, copy_rot.owner_space, copy_rot.mix_mode = self.target.control, 'LOCAL', 'LOCAL', 'AFTER'
    
    # the controls IK limit X can only be true when not lock tracking Z...
    driver = self.drivers[0]
    driver.source, driver.setting = self.target.control, "use_ik_limit_x"
    driver.expression = "True if lock_z == 0.0 else False"
    variable = driver.variables[0]
    variable.name, variable.flavour = "lock_z", 'SINGLE_PROP'
    #variable.data_path = 'pose.bones["' + self.target.control + '"].constraints["LOCK Z - Locked Track"].mute'
    variable.data_path = 'jk_arm.rigging["' + rigging.name + '"].tracking.target.lock_z'
    
    # the controls IK limit Z can only be true when not lock tracking X...
    driver = self.drivers[1]
    driver.source, driver.setting = self.target.control, "use_ik_limit_z"
    driver.expression = "True if lock_x == 0.0 else False"
    variable = driver.variables[0]
    variable.name, variable.flavour = "lock_x", 'SINGLE_PROP'
    #variable.data_path = 'pose.bones["' + self.target.control + '"].constraints["LOCK X - Locked Track"].mute'
    variable.data_path = 'jk_arm.rigging["' + rigging.name + '"].tracking.target.lock_x'
    
    # drive the Locked Track Z constraints influence from the lock_z float...
    driver = self.drivers[2]
    driver.source, driver.setting = self.target.control, "influence"
    driver.constraint, driver.expression = "LOCK Z - Locked Track", "lock_z"
    variable = driver.variables[0]
    variable.name, variable.flavour = "lock_z", 'SINGLE_PROP'
    variable.data_path = 'jk_arm.rigging["' + rigging.name + '"].tracking.target.lock_z'
    
    # drive the Locked Track X constraints influence from the lock_x float...
    driver = self.drivers[3]
    driver.source, driver.setting = self.target.control, "influence"
    driver.constraint, driver.expression = "LOCK X - Locked Track", "lock_x"
    variable = driver.variables[0]
    variable.name, variable.flavour = "lock_x", 'SINGLE_PROP'
    variable.data_path = 'jk_arm.rigging["' + rigging.name + '"].tracking.target.lock_x'

    # get recursive parents...
    parents = get_tracking_parents(self, bones)
    ik_settings = ["ik_stretch", "ik_min_x", "ik_max_x","ik_min_y", "ik_max_y", "ik_min_z", "ik_max_z", "ik_stiffness_x", "ik_stiffness_y", "ik_stiffness_z"]
    parents.reverse()
    ci, di = 5, 4
    # we need all the bone names setup first...
    for bi in range(0, self.length):
        # if we don't have a bone already create one...
        bone = self.bones.add() if len(self.bones) <= bi else self.bones[bi]
        parent = parents[bi]
        if parent:
            bone.source = parent.name
            bone.origin = parent.parent.name if parent.parent else ""
            bone.gizmo = prefs.affixes.gizmo + "TRACK_" + parent.name
            bone.stretch = prefs.affixes.mech + "TRACK_" + parent.name
    # to set the name of the rigging based on the bones... (needed for drivers)
    rigging.name = "Chain (Tracking) - " + self.bones[0].source + " - " + self.bones[-1].source
    # before we add the constraints...
    for bi in range(0, self.length):
        parent = parents[bi]
        bone = self.bones[bi]
        # every source has a copy rotation to it's gizmo...
        copy_rot = self.constraints.add() if len(self.constraints) <= ci else self.constraints[ci]
        copy_rot.flavour, copy_rot.constraint = 'COPY_ROTATION', "TRACK - Copy Rotation"
        copy_rot.source, copy_rot.subtarget = bone.source, bone.gizmo
        copy_rot.target_space, copy_rot.owner_space, copy_rot.mix_mode = 'LOCAL', 'LOCAL', 'AFTER'
        ci = ci + 1
        # each gizmo in the chain has an IK constraint...
        ik = self.constraints.add() if len(self.constraints) <= ci else self.constraints[ci]
        ik.flavour, ik.constraint, ik.use_stretch = 'IK', "TRACK - IK", False
        # if this is the end of the chain...
        if bi == (self.length - 1):
            # the ik is rotational to the stretch...
            ik.source, ik.subtarget, ik.chain_count = bone.gizmo, bone.stretch, 1
            ik.use_location, ik.use_rotation = False, True
            ci = ci + 1
        else:
            # otherwise it's single bone ik to the next stretch...
            ik.source, ik.chain_count = bone.gizmo, 1
            # and the subtarget is the next stretch bone... (second to last bone targets the control)
            ik.subtarget = self.bones[bi + 1].stretch if bi < (self.length - 2) else self.target.control
            ci = ci + 1
            # and a copy rotation constraint...
            copy_rot = self.constraints.add() if len(self.constraints) <= ci else self.constraints[ci]
            copy_rot.flavour, copy_rot.constraint = 'COPY_ROTATION', "TRACK - Copy Rotation"
            copy_rot.source, copy_rot.subtarget = bone.gizmo, bone.stretch
            copy_rot.target_space, copy_rot.owner_space, copy_rot.mix_mode = 'LOCAL', 'LOCAL', 'AFTER'
            copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = False, True, False
            ci = ci + 1
    # we need drivers for all the gizmo and stretch bones...
    for bi, bone in enumerate(self.bones):
        for name in [bone.gizmo, bone.stretch]:
            # as their ik settings are driven from the sources...
            for setting in ik_settings:
                driver = self.drivers.add() if len(self.drivers) <= di else self.drivers[di]
                # if this is the last bone...
                if bi == (self.length - 1):
                    # switch the drivers over to the targets control and offset bones... (also switch the turn axis over to Z)
                    driver.source, driver.setting, turn_suffix = self.target.control if name == bone.gizmo else self.target.offset, setting, "_z"
                else:
                    driver.source, driver.setting, turn_suffix = name, setting, "_y"
                # if this is the stretch or stiffness ik settings...
                if setting in ["ik_stretch", "ik_stiffness_x", "ik_stiffness_y", "ik_stiffness_z"]:
                    driver.expression = setting
                    # we only need one variable for the stretch ik setting...
                    variable = driver.variables[0] if driver.variables else driver.variables.add()
                    variable.name, variable.flavour = setting, 'SINGLE_PROP'
                    variable.data_path = 'pose.bones["' + bone.source + '"].' + setting
                    if len(driver.variables) > 1:
                        driver.variables.remove(1)
                else:
                    driver.expression = setting + ' * ' + ('turn' if setting.endswith(turn_suffix) else 'lean')
                    # otherwise one variable for the lean/turn property...
                    variable = driver.variables[0] if driver.variables else driver.variables.add()
                    variable.name, variable.flavour = 'turn' if setting.endswith(turn_suffix) else 'lean', 'SINGLE_PROP'
                    variable.data_path = 'jk_arm.rigging["' + rigging.name + '"].tracking.bones[' + str(bi) + '].' + variable.name
                    # and another for the sources min/max ik setting...
                    variable = driver.variables[1] if len(driver.variables) > 1 else driver.variables.add()
                    variable.name, variable.flavour = setting, 'SINGLE_PROP'
                    variable.data_path = 'pose.bones["' + bone.source + '"].' + setting
                di = di + 1
    # might need to clean up bones when reducing chain length...
    if len(self.bones) > self.length:
        while len(self.bones) != self.length:
            self.bones.remove(self.length)
    # might need to clean up constraints when reducing chain length...
    if len(self.constraints) > ((self.length * 2) + (self.length - 1) + 5):
        while len(self.constraints) != ((self.length * 2) + (self.length - 1) + 5):
            self.constraints.remove(((self.length * 2) + (self.length - 1) + 5))
    # aaand might need to clean up drivers when reducing length...
    if len(self.drivers) > (4 + (self.length * 20)):
        while len(self.drivers) != (4 + (self.length * 20)):
            self.drivers.remove((4 + (self.length * 20)))

    self.is_editing = False

    # then clear the riggings source bone data...
    rigging.sources.clear()
    # and refresh it for the auto update functionality...
    rigging.get_sources()

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- RIGGING FUNCTIONS ------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def add_tracking_target(self, armature):
    ebs = armature.data.edit_bones
    direction = Vector((1.0, 0.0, 0.0)) if self.target.axis.startswith('X') else Vector((0.0, 1.0, 0.0)) if self.target.axis.startswith('Y') else Vector((0.0, 0.0, 1.0))
    distance = (self.target.distance * -1) if 'NEGATIVE' in self.target.axis else (self.target.distance)
    source_eb, end_eb, root_eb = ebs.get(self.target.source), ebs.get(self.bones[-1].stretch), ebs.get(self.target.root)
    # add the target down the user defined axis of the armature...
    target_eb = ebs.new(self.target.bone)
    target_eb.head, target_eb.tail = source_eb.head + (direction * distance), source_eb.tail + (direction * distance)
    target_eb.roll, target_eb.parent, target_eb.use_deform = 0.0, root_eb, False
    # add the stretchy twisty control that tracks to the target, inserted into the stretch hierarchy...
    control_eb = ebs.new(self.target.control)
    control_eb.head, control_eb.tail, control_eb.roll = source_eb.head, target_eb.head, 0.0
    control_eb.parent, control_eb.use_deform = end_eb.parent, False
    # add the offset bone as a duplicate of the control parented to the sources parent...
    offset_eb = ebs.new(self.target.offset)
    offset_eb.head, offset_eb.tail, offset_eb.roll = control_eb.head, control_eb.tail, control_eb.roll
    offset_eb.parent, offset_eb.use_deform = source_eb.parent, False
    # and parent the end stretch to it...
    end_eb.parent = offset_eb

def add_tracking_bones(self, armature):
    ebs = armature.data.edit_bones
    # iterate on the bone entries...
    for bi, bone in enumerate(self.bones):
        # get the source bone...
        source_eb = ebs.get(bone.source)
        # if this is the first bone...
        if bi == 0:
            # the stretch parent is the sources parent...
            stretch_parent = source_eb.parent
        # add the gizmo bone parented to the sources parent...
        gizmo_eb = armature.data.edit_bones.new(bone.gizmo)
        gizmo_eb.head, gizmo_eb.tail, gizmo_eb.roll = source_eb.head, source_eb.tail, source_eb.roll
        gizmo_eb.parent, gizmo_eb.use_deform, gizmo_eb.inherit_scale = source_eb.parent, False, 'ALIGNED'
        # and the stretch bone is another duplicate...
        stretch_eb = armature.data.edit_bones.new(bone.stretch)
        stretch_eb.head, stretch_eb.tail, stretch_eb.roll = source_eb.head, source_eb.tail, source_eb.roll
        stretch_eb.parent, stretch_eb.use_deform = stretch_parent, False
        # set the next stretchs parent to be this stretch...
        stretch_parent = stretch_eb

def add_tracking_constraints(self, armature):
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

def add_tracking_drivers(self, armature):
    pbs, bbs = armature.pose.bones, armature.data.bones
    for driver in self.drivers:
        # get the source bone of the driver, if it exists... (from the relevant bones)
        source_b = pbs.get(driver.source) if driver.is_pose_bone else bbs.get(driver.source)
        if source_b:
            if driver.constraint:
                drv = source_b.constraints[driver.constraint].driver_add(driver.setting)
            else:
                drv = source_b.driver_add(driver.setting)
            # and iterate on the variables...
            for variable in driver.variables:
                # adding them, setting their names and types...
                var = drv.driver.variables.new()
                var.name, var.type = variable.name, variable.flavour
                var.targets[0].id = armature
                var.targets[0].data_path = variable.data_path
            # set the drivers expression...
            drv.driver.expression = driver.expression
            # and remove any sneaky curve modifiers...
            for mod in drv.modifiers:
                drv.modifiers.remove(mod)

def add_tracking_shapes(self, armature):
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

def add_tracking_groups(self, armature):
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

def add_tracking_layers(self, armature):
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

def add_tracking_chain(self, armature):
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
    add_tracking_bones(self, armature)
    add_tracking_target(self, armature)
    #if self.auto_roll:
        #add_tracking_rolls(self, armature)
    # and add constraints and drivers in pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    add_tracking_constraints(self, armature)
    add_tracking_drivers(self, armature)
    # if we are using default shapes or groups, add them...
    if self.use_default_shapes:
        add_tracking_shapes(self, armature)
    if self.use_default_groups:
        add_tracking_groups(self, armature)
    if self.use_default_layers:
        add_tracking_layers(self, armature)
    # then we need to set some default ik settings...
    pbs = armature.pose.bones
    for bi, bone in enumerate(self.bones):
        source_pb = pbs.get(bone.source)
        # switching to offset/control if this is the last bone in the chain...
        stretch_pb = pbs.get(self.target.control if bi == (self.length - 1) else bone.stretch)
        gizmo_pb = pbs.get(self.target.offset if bi == (self.length - 1) else bone.gizmo)
        if source_pb:
            # set all the stretch values...
            source_pb.ik_stretch = 0.5
        # and the stretch/gizmo/control/offset bones need their ik limits on for lean/turn to work...
        if stretch_pb:
            stretch_pb.use_ik_limit_x, stretch_pb.use_ik_limit_y, stretch_pb.use_ik_limit_z = True, True, True
        if gizmo_pb:
            gizmo_pb.use_ik_limit_x, gizmo_pb.use_ik_limit_y, gizmo_pb.use_ik_limit_z = True, True, True
    # give x mirror back... (if it was turned on)
    armature.data.use_mirror_x = is_mirror_x
    # give edit detection back... (if it was turned on)
    armature.jk_arm.use_edit_detection = is_detecting

def remove_tracking_chain(self, armature):
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
    # constraints need removing, we are, only removing the bone of one...
    for con_refs in references['constraints']:
        if con_refs['source'] and con_refs['constraint']:
            con_refs['source'].constraints.remove(con_refs['constraint'])
    # clear shapes/groups from source bones... (what should i do about layers?)
    for bone_refs in references['bones']:
        if bone_refs['source']:
            bone_refs['source'].custom_shape, bone_refs['source'].bone_group = None, None
    # then we need to kill any added bones in edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    ebs, remove_bones = armature.data.edit_bones, []
    remove_bones.append(self.target.bone)
    remove_bones.append(self.target.control)
    remove_bones.append(self.target.offset)
    for bone in self.bones:
        source_eb = ebs.get(bone.source)
        if source_eb:
            source_eb.parent = ebs.get(bone.origin)
        remove_bones.append(bone.gizmo)
        remove_bones.append(bone.stretch)
    # iterate on the names of the bones to be removed...
    for name in remove_bones:
        # if they exist...
        eb = ebs.get(name)
        if eb:
            # remove them...
            ebs.remove(eb)
    # then return to pose mode like nothing ever happened...
    bpy.ops.object.mode_set(mode='POSE')

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTIES -------------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

class JK_PG_ARM_Tracking_Constraint(bpy.types.PropertyGroup):

    source: StringProperty(name="Source", description="Name of the bone the constraint is on",
        default="", maxlen=63)

    constraint: StringProperty(name="Constraint", description="Name of the actual constraint",
        default="", maxlen=63)

    flavour: EnumProperty(name="Flavour", description="The type of constraint",
        items=[('NONE', 'None', ""), ('COPY_ROTATION', 'Copy Rotation', ""), ('LIMIT_ROTATION', 'Limit Rotation', ""), 
            ('LOCKED_TRACK', 'Locked Track', ""), ('IK', 'Inverse Kinematics', ""), ('DAMPED_TRACK', 'Damped Track', ""),
            ('COPY_SCALE', 'Copy Scale', ""), ('LIMIT_SCALE', 'Limit Scale', ""), ('COPY_TRANSFORMS', 'Copy Transforms', "")],
        default='NONE')
    
    subtarget: StringProperty(name="Subtarget", description="Name of the subtarget. (if any)",
        default="", maxlen=1024)

    pole_subtarget: StringProperty(name="Pole Target", description="Name of the pole target. (if any)",
        default="", maxlen=1024)

    chain_count: IntProperty(name="Chain Length", description="How many bones are included in the IK effect",
        default=2, min=0)

    influence: FloatProperty(name="Influence", description="influence of this constraint", default=1.0, min=0.0, max=1.0, subtype='FACTOR')

    track_axis: EnumProperty(name="Track Axis", description="Axis that points to the target object",
        items=[('TRACK_X', 'X', ""), ('TRACK_Y', 'Y', ""), ('TRACK_Z', 'Z', ""), 
            ('TRACK_NEGATIVE_X', '-X', ""), ('TRACK_NEGATIVE_Y', '-Y', ""), ('TRACK_NEGATIVE_Z', '-Z', "")],
        default='TRACK_Y')

    lock_axis: EnumProperty(name="Lock Axis", description="Axis that points upward",
        items=[('LOCK_X', 'X', ""), ('LOCK_Y', 'Y', ""), ('LOCK_Z', 'Z', "")],
        default='LOCK_X')

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

    use_stretch: BoolProperty(name="Use stretch", description="Use IK stretching", default=True)
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

class JK_PG_ARM_Tracking_Variable(bpy.types.PropertyGroup):

    flavour: EnumProperty(name="Type", description="What kind of driver variable is this?",
        items=[('SINGLE_PROP', "Single Property", ""), ('TRANSFORMS', "Transforms", ""),
            ('ROTATION_DIFF', "Rotation Difference", ""), ('LOC_DIFF', "Location Difference", "")])

    transform_type: StringProperty(name="Transform Type", description="The data path if single property",
        default="")
    
    transform_space: StringProperty(name="Transform Space", description="The data path if single property",
        default="")

    data_path: StringProperty(name="Data Path", description="The data path if single property",
        default="")

    bone_target: StringProperty(name="Bone Target", description="The first bone target if transforms/difference",
        default="")

class JK_PG_ARM_Tracking_Driver(bpy.types.PropertyGroup):

    is_pose_bone: BoolProperty(name="Is Pose Bone", description="Is this drivers source a pose bone or a bone bone?",
        default=True)

    source: StringProperty(name="Source", description="Name of the bone the driver is on",
        default="", maxlen=63)

    constraint: StringProperty(name="Constraint", description="Name of constraint on the bone the driver is on",
        default="", maxlen=63)

    setting: StringProperty(name="Setting", description="Name of the bone setting the driver is on",
        default="")

    array_index: IntProperty(name="Array Index", description="Index of the setting if it's an array",
        default=0)

    expression: StringProperty(name="Expression", description="The expression of the driver",
        default="")

    variables: CollectionProperty(type=JK_PG_ARM_Tracking_Variable)

class JK_PG_ARM_Tracking_Target(bpy.types.PropertyGroup):
    
    def update_target(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].tracking
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
            # remove the rigging and set "is_editing" true (removing sets the source back to what it was from saved refs)
            rigging.is_rigged, rigging.is_editing = False, True
            # while is_editing is false set the new source to what we want it to be...
            self.source, self.root, rigging.is_editing = new_source, new_root, False
            # then we can update the rigging...
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

    control: StringProperty(name="Control", description="Name of the bone that controls the roll mechanism. (if any)", 
        default="", maxlen=1024)

    axis: EnumProperty(name="Axis", description="The local axis of the armature that the target is created away from the source bones",
        items=[('X', 'X axis', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X axis', "", "CON_LOCLIKE", 1),
        ('Y', 'Y axis', "", "CON_LOCLIKE", 2),
        ('Y_NEGATIVE', '-Y axis', "", "CON_LOCLIKE", 3),
        ('Z', 'Z axis', "", "CON_LOCLIKE", 4),
        ('Z_NEGATIVE', '-Z axis', "", "CON_LOCLIKE", 5)],
        default='Y', update=update_target)

    distance: FloatProperty(name="Distance", description="The distance the target is created from the source bones. (in metres)", 
        default=0.25, update=update_target)

    lock_x: FloatProperty(name="Lock X", description="Influence of the locked tracking around the stretchy controllers X Axis. (Only needed during 360 X rotations)", 
        default=0.0, min=0.0, max=1.0, subtype='FACTOR')

    lock_z: FloatProperty(name="Lock Z", description="Influence of the locked tracking around the stretchy controllers Z Axis. (Only needed during 360 Z rotations)", 
        default=0.0, min=0.0, max=1.0, subtype='FACTOR')

class JK_PG_ARM_Tracking_Bone(bpy.types.PropertyGroup):

    def update_bone(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].tracking
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
        default="", maxlen=63)#, update=update_bone)

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

    axis: EnumProperty(name="Shape Axis", description="The local axis of the bone that defines which custom shape to use",
        items=[('X', 'X axis', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X axis', "", "CON_LOCLIKE", 1),
        ('Z', 'Z axis', "", "CON_LOCLIKE", 4),
        ('Z_NEGATIVE', '-Z axis', "", "CON_LOCLIKE", 5)],
        default='Z_NEGATIVE')

    lean: FloatProperty(name="Lean", description="Influence of leaning towards the target", 
        default=1.0, min=0.0, max=1.0, subtype='FACTOR')

    turn: FloatProperty(name="Turn", description="Influence of turning towards the target", 
        default=1.0, min=0.0, max=1.0, subtype='FACTOR')

class JK_PG_ARM_Tracking_Chain(bpy.types.PropertyGroup):

    def apply_transforms(self):
        # when applying transforms we need to reset the pole distance...
        armature = self.id_data
        bbs = armature.data.bones
        # this will trigger a full update of the rigging and should apply all transform differences...
        source_bb, target_bb = bbs.get(self.target.source), bbs.get(self.target.bone)
        start, end = source_bb.head_local, target_bb.head_local
        distance = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2 + (end[2] - start[2])**2)
        self.target.distance = abs(distance)

    target: PointerProperty(type=JK_PG_ARM_Tracking_Target)

    bones: CollectionProperty(type=JK_PG_ARM_Tracking_Bone)

    constraints: CollectionProperty(type=JK_PG_ARM_Tracking_Constraint)

    drivers: CollectionProperty(type=JK_PG_ARM_Tracking_Driver)

    def get_references(self):
        return get_tracking_refs(self)

    def get_sources(self):
        sources = [bone.source for bone in self.bones] + [self.target.source]
        return sources

    def get_groups(self):
        groups = {
            "Chain Bones" : [bone.source for bone in self.bones],
            "Gizmo Bones" : [bone.gizmo for bone in self.bones],
            "Mechanic Bones" : [bone.stretch for bone in self.bones],
            "Control Bones" : [self.target.control],
            "Offset Bones" : [self.target.offset],
            "Kinematic Targets": [self.target.bone]}
        return groups

    def get_shapes(self):
        shapes = {
            "Bone_Shape_Default_Tail_Fan" : [self.target.control],
            "Bone_Shape_Default_Tail_Socket" : [self.target.offset],
            "Bone_Shape_Default_Head_Sphere" : [self.target.bone],
            "Bone_Shape_Default_Medial_Ring_Even" : [bone.gizmo for bone in self.bones],
            "Bone_Shape_Default_Medial_Ring_Odd" : [bone.stretch for bone in self.bones]}
        # iterate on the bones to get the source bones axis based shapes...
        brackets = {'X' : "Bone_Shape_Default_Medial_Bracket_X_Positive", 'X_NEGATIVE' : "Bone_Shape_Default_Medial_Bracket_X_Negative",
            'Z' : "Bone_Shape_Default_Medial_Bracket_Z_Positive", 'Z_NEGATIVE' : "Bone_Shape_Default_Medial_Bracket_Z_Negative"}
        for bone in self.bones:
            bracket = brackets[bone.axis]
            # and append or add them into the bone shapes dictionary...
            if bracket in shapes:
                shapes[bracket].append(bone.source)
            else:
                shapes[bracket] = [bone.source]
        return shapes

    def get_is_riggable(self):
        # we are going to need to know if the rigging in the properties is riggable...
        armature, is_riggable = self.id_data, True
        bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
        # for this rigging we iterate on some names...
        for name in [self.target.source] + [b.source for b in self.bones]:
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
            remove_tracking_chain(self, self.id_data)

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
            get_tracking_props(self, self.id_data)
            self.has_properties = True
        # always set the properties that get calculated from the essentials...
        set_tracking_props(self, self.id_data)
        # if we can rig from the properties...
        if self.is_riggable:
            # add the rigging...
            add_tracking_chain(self, self.id_data)
            self.is_rigged = True

    length: IntProperty(name="Chain Length", description="How many bones are included in this IK chain",
        default=3, min=2, update=update_rigging)

    use_default_groups: BoolProperty(name="Use Default Groups", description="Do you want this rigging to use some default bone groups?",
        default=False, update=update_rigging)

    use_default_shapes: BoolProperty(name="Use Default Shapes", description="Do you want this rigging to use some default bone shapes?",
        default=False, update=update_rigging)

    use_default_layers: BoolProperty(name="Use Default Layers", description="Do you want this rigging to use some default armature layers?",
        default=False, update=update_rigging)

    #ik_softness: FloatProperty(name="IK Softness", description="Influence of this chains soft IK. (if not using FK)", 
        #default=1.0, min=0.0, max=1.0, subtype='FACTOR')

    influence: FloatProperty(name="Influence", description="Influence of the tracking", 
        default=1.0, min=0.0, max=1.0, subtype='FACTOR')

    lean: FloatProperty(name="Lean", description="Influence of leaning towards the target", 
        default=1.0, min=0.0, max=1.0, subtype='FACTOR')

    turn: FloatProperty(name="Lean", description="Influence of turning towards the target", 
        default=1.0, min=0.0, max=1.0, subtype='FACTOR')

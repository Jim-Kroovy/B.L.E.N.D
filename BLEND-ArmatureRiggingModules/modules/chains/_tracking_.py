import bpy
import math
from mathutils import Vector

from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty)

from ... import _functions_, _properties_

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
    _functions_.add_constraints(self, armature)
    _functions_.add_drivers(self, armature)
    # if we are using default shapes or groups, add them...
    if self.use_default_shapes:
        _functions_.add_shapes(self, armature)
    if self.use_default_groups:
        _functions_.add_groups(self, armature)
    if self.use_default_layers:
        _functions_.add_layers(self, armature)
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

    target: PointerProperty(type=_properties_.JK_PG_ARM_Target)

    bones: CollectionProperty(type=_properties_.JK_PG_ARM_Bone)

    constraints: CollectionProperty(type=_properties_.JK_PG_ARM_Constraint)

    drivers: CollectionProperty(type=_properties_.JK_PG_ARM_Driver)

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
            "Bone_Shape_Default_Medial_Ring_Odd" : [bone.stretch for bone in self.bones],
            "Bone_Shape_Default_Medial_Bracket" : [bone.source for bone in self.bones]}
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

    #lean: FloatProperty(name="Lean", description="Influence of leaning towards the target", 
        #default=1.0, min=0.0, max=1.0, subtype='FACTOR')

    #turn: FloatProperty(name="Lean", description="Influence of turning towards the target", 
        #default=1.0, min=0.0, max=1.0, subtype='FACTOR')

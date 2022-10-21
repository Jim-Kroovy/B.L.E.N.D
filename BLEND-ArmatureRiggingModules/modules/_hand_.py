import bpy

from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty)

from .. import _functions_, _properties_

#forward: PointerProperty(type=_forward_.JK_PG_ARM_Forward_Chain)
#scalar: PointerProperty(type=_scalar_.JK_PG_ARM_Scalar_Chain)

# Much of this code is copy/pasted between the various flavours of rigging, while a little long winded it makes adding new things and updating and troubleshooting a whole lot easier...
# and everyone wants me to do so much i decided it's better that things are easy to edit/create and not as dynamic as they could be...

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTY FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_hand_refs(self):
    armature, references = self.id_data, {}
    pbs, bbs = armature.pose.bones, armature.data.bones
    references['target'] = {
        'source' : pbs.get(self.target.source), 'origin' : pbs.get(self.target.origin),
        'root' : pbs.get(self.target.root),
        'pivot' : pbs.get(self.target.pivot), 'control' : pbs.get(self.target.control)}
    references['digits'] = [{
        'roll' : pbs.get(digit.roll), 'track' : pbs.get(digit.track)} for digit in self.digits]
    references['constraints'] = [{
        'constraint' : pbs.get(con.source).constraints.get(con.constraint) if pbs.get(con.source) else None,
        'source' : pbs.get(con.source)} for con in self.constraints]
    references['drivers'] = [{
        'source' : pbs.get(drv.source) if drv.is_pose_bone else bbs.get(drv.source),
        'constraint' : pbs.get(drv.source).constraints.get(drv.constraint) if drv.constraint and pbs.get(drv.source) else "",
        'setting' : drv.setting} for drv in self.drivers]
    return references

def get_hand_deps(self):
    # these are bone names that cannot be roots or have anything relevent parented to them...
    dependents = [self.target.source, self.target.pivot, self.target.control]
    return dependents

def get_hand_props(self, armature):
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    self.is_editing = True
    self.digits.clear()
    self.constraints.clear()
    self.drivers.clear()
    active, selected = bones.active, [b for b in bones if b.select]
    self.target.source = active.name
    # add digits for each selected bone... (but not the active)
    for i, bone in enumerate(selected):
        if bone != active:
            digit = self.digits.add()
            digit.end = bone.name
            digit.flavour = 'FORWARD'

    # the pivot bones scale is driven on all axes by the local Z scale of the control...
    for i in range(0, 3):
        driver = self.drivers.add()
        driver.setting, driver.array_index, driver.expression = 'scale', i, "z_sca"
        variable = driver.variables.add()
        variable.name, variable.flavour = "z_sca", 'TRANSFORMS', #variable.bone_target
        variable.transform_type, variable.transform_space = 'SCALE_Z', 'LOCAL_SPACE'
    # then create variables for each digit to the controls...
    for digit in self.digits:
        # each digit roll bone has it's rotation driven from the Z rotation of the control... (must be euler?)
        driver = self.drivers.add()
        driver.setting, driver.array_index, driver.expression = 'rotation_euler', 0 if digit.roll_axis == 'X' else 2, "z_rot"
        variable = driver.variables.add()
        variable.name, variable.flavour = "z_rot", 'TRANSFORMS', #variable.bone_target
        variable.transform_type, variable.transform_space = 'ROT_Z', 'LOCAL_SPACE'
        # each digit track bone has a damped track constraint...
        damp_track = self.constraints.add()
        damp_track.constraint = "TRACK - Damped Track"
        damp_track.flavour, damp_track.head_tail = 'DAMPED_TRACK', 1.0 
        # and that damped track has a driver on its head/tail to the Y scale of the pivot...
        driver = self.drivers.add()
        driver.setting, driver.expression = 'head_tail', "y_scale"
        variable = driver.variables.add()
        variable.name, variable.flavour = "y_scale", 'TRANSFORMS'
        variable.transform_type, variable.transform_space = 'SCALE_Y', 'LOCAL_SPACE'
        # the digit control itself has a copy rotation to the track... (including Y?)
        copy_rot = self.constraints.add()
        copy_rot.constraint, copy_rot.flavour = "TRACK - Copy Rotation", 'COPY_ROTATION'
        copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = True if digit.track_axis == 'X' else False, True, True if digit.track_axis == 'Z' else False
        copy_rot.target_space, copy_rot.owner_space, copy_rot.mix_mode = 'LOCAL', 'LOCAL', 'BEFORE'
        # and a copy rotation to the roll...
        copy_rot = self.constraints.add()
        copy_rot.constraint, copy_rot.flavour = "ROLL - Copy Rotation", 'COPY_ROTATION'
        copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = True if digit.roll_axis == 'X' else False, False, True if digit.roll_axis == 'Z' else False
        copy_rot.target_space, copy_rot.owner_space, copy_rot.mix_mode = 'LOCAL', 'LOCAL', 'BEFORE'
        # aaaand if this digit is scalar it has a copy Y scale to the pivot...
        copy_sca = self.constraints.add()
        copy_sca.constraint, copy_sca.flavour = "STRETCH - Copy Scale", 'COPY_SCALE' if digit.flavour == 'SCALAR' else 'NONE'
        copy_sca.use_x, copy_sca.use_y, copy_sca.use_z = False, True, False
        copy_sca.target_space, copy_sca.owner_space, copy_sca.use_offset = 'LOCAL', 'LOCAL', True

    self.is_editing = False

def set_hand_props(self, armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingModules"].preferences
    side = armature.jk_arm.rigging[armature.jk_arm.active].side
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    armature.jk_arm.rigging[armature.jk_arm.active].name = "Merged (Hand) - " + self.target.source
    self.is_editing = True
    self.target.control = prefs.affixes.control + self.target.source
    self.target.pivot = prefs.affixes.mech + self.target.source
    di, ci = 0, 0
    # the pivot bones scale is driven on all axes by the local Z scale of the control...
    for i in range(0, 3):
        driver = self.drivers[di]
        driver.source, driver.variables[0].bone_target = self.target.pivot, self.target.control
        di = di + 1
    # and the digits need all their things set...
    last_active = armature.jk_arm.active
    for i, digit in enumerate(self.digits):
        armature.jk_arm.active = armature.jk_arm.active + (i + 1)
        is_existing = False
        if digit.rigging:
            rigging = armature.jk_arm.rigging[digit.rigging]
            is_existing = True
        else:
            rigging = armature.jk_arm.rigging.add()
            rigging.is_merged = True
        chain = rigging.forward if digit.flavour == 'FORWARD' else rigging.scalar
        chain.is_editing = True
        chain.target.end = digit.end
        chain.use_default_shapes = self.use_default_shapes
        chain.use_default_groups = self.use_default_groups
        chain.use_default_layers = self.use_default_layers
        chain.is_editing = False
        if is_existing:
            chain.update_rigging(bpy.context)
        else:
            rigging.flavour = digit.flavour
        # return active so update functions reference the correct rigging...
        armature.jk_arm.active = last_active
        control = chain.target.bone if digit.flavour == 'FORWARD' else chain.target.parent
        if chain.is_rigged:
            # so we can get at it's targets and set up our drivers and constraints...
            digit.roll = prefs.affixes.gizmo + prefs.affixes.roll + chain.target.source
            digit.track = prefs.affixes.mech + prefs.affixes.track + chain.target.source
            # each digit roll bone has it's rotation driven from the Z rotation of the control... (must be euler?)
            driver = self.drivers[di]
            driver.source, driver.variables[0].bone_target = digit.roll, self.target.control
            driver.setting, driver.array_index, driver.expression = 'rotation_euler', 0 if digit.roll_axis == 'X' else 2, "z_rot"
            di = di + 1
            # each digit track bone has a damped track constraint...
            damp_track = self.constraints[ci]
            damp_track.source, damp_track.subtarget = digit.track, digit.roll
            ci = ci + 1
            # and that damped track has a driver on its head/tail to the Y scale of the pivot...
            driver = self.drivers[di]
            driver.source, driver.constraint = digit.track, "TRACK - Damped Track"
            driver.variables[0].bone_target = self.target.pivot
            di = di + 1
            # the digit control itself has a to the track... (including Y?)
            copy_rot = self.constraints[ci]
            copy_rot.source, copy_rot.subtarget = control, digit.track
            copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = True if digit.track_axis == 'X' else False, True, True if digit.track_axis == 'Z' else False
            ci = ci + 1
            # and a copy rotation to the roll...
            copy_rot = self.constraints[ci]
            copy_rot.source, copy_rot.subtarget = control, digit.roll
            copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = True if digit.roll_axis == 'X' else False, False, True if digit.roll_axis == 'Z' else False
            ci = ci + 1
            # aaaand if this digit is scalar it has a copy Y scale to the pivot...
            copy_sca = self.constraints[ci]
            copy_sca.source, copy_sca.subtarget = control, self.target.pivot
            ci = ci + 1
    #armature.jk_arm.active = last_active
    self.is_editing = False

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- RIGGING FUNCTIONS ------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def add_hand_target(self, armature):
    ebs = armature.data.edit_bones
    side = armature.jk_arm.rigging[armature.jk_arm.active].side
    source_eb = ebs.get(self.target.source)
    source_axis = source_eb.x_axis if self.target.axis.startswith('X') else source_eb.y_axis if self.target.axis.startswith('Y') else source_eb.z_axis
    direction = source_eb.x_axis if self.target.direction.startswith('X') else source_eb.y_axis if self.target.direction.startswith('Y') else source_eb.z_axis
    distance = (self.target.distance * -1) if 'NEGATIVE' in self.target.axis else (self.target.distance)
    length = (source_eb.length * -1) if 'NEGATIVE' in self.target.direction else (source_eb.length)
    # create control as dupe of hand...
    control_eb = ebs.new(self.target.control)
    # place between hand and finger median... # damp track X to hand and apply rest pose?
    control_eb.head = source_eb.head + (source_axis * distance)
    control_eb.tail = control_eb.head + (direction * length)
    # create parent as control
    pivot_eb = ebs.new(self.target.pivot)
    pivot_eb.head, pivot_eb.tail, pivot_eb.roll = control_eb.head, control_eb.tail, control_eb.roll
    # now we should hop into pose mode and use constraints to ensure these controls always use the Z axis...
    bpy.ops.object.mode_set(mode='POSE')
    # give control a lock track X if left -X if right around Y...
    control_pb = armature.pose.bones[self.target.control]
    lock_track = control_pb.constraints.new('LOCKED_TRACK')
    lock_track.target, lock_track.subtarget = armature, self.target.source
    lock_track.track_axis = 'TRACK_NEGATIVE_X' if side == 'RIGHT' else 'TRACK_X'
    lock_track.lock_axis = 'LOCK_Y'
    # give the parent a copy rot to control and a damp track to source...
    pivot_pb = armature.pose.bones[self.target.pivot]
    copy_rot = pivot_pb.constraints.new('COPY_ROTATION')
    copy_rot.target, copy_rot.subtarget = armature, self.target.control
    damp_track = pivot_pb.constraints.new('DAMPED_TRACK')
    damp_track.target, damp_track.subtarget = armature, self.target.source
    # apply and remove the constraints then hop back to edit mode...
    bpy.ops.pose.select_all(action='DESELECT')
    control_pb.bone.select, pivot_pb.bone.select = True, True
    bpy.ops.pose.armature_apply(selected=True)
    bpy.ops.pose.constraints_clear()
    bpy.ops.object.mode_set(mode='EDIT')
    # so we can add in the digit roll and track targets...
    pivot_eb = ebs.get(self.target.pivot)
    root_eb = ebs.get(self.target.root)
    for digit in self.digits:
        if digit.flavour != 'NONE':
            chain = armature.jk_arm.rigging[digit.rigging].get_pointer()
            if chain.is_rigged:
                source_eb = ebs.get(chain.bones[0].source)
                roll_eb = ebs.new(digit.roll)
                roll_eb.head, roll_eb.tail, roll_eb.roll = source_eb.head, source_eb.tail, source_eb.roll
                roll_eb.parent = root_eb
                track_eb = ebs.new(digit.track)
                track_eb.head, track_eb.tail, track_eb.roll = source_eb.head, source_eb.tail, source_eb.roll
                track_eb.parent = pivot_eb

    # pivot has drivers to copy Z scale from control across all axes...

    # if scalar need additional roll control bone? 
    # or maybe just copy Y scale from control with power of 2 and drive the influence of an additional copy rotation to the roll (driven from the Y scale of the control * 2)

def add_hand_controls(self, armature):
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
    add_hand_target(self, armature)
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
    # we need to set all the digit roll bones...
    pbs = armature.pose.bones
    for digit in self.digits:
        # to use euler rotation...
        roll_pb = pbs.get(digit.roll)
        if roll_pb:
            roll_pb.rotation_mode = 'XYZ'
    # give x mirror back... (if it was turned on)
    armature.data.use_mirror_x = is_mirror_x
    # give edit detection back... (if it was turned on)
    armature.jk_arm.use_edit_detection = is_detecting

def remove_hand_controls(self, armature):
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
    #for bone_refs in references['digits']:
        #if bone_refs['source']:
            #bone_refs['source'].custom_shape, bone_refs['source'].bone_group = None, None
    # then we need to kill the target bone in edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    ebs = armature.data.edit_bones
    target_eb, pivot_eb = ebs.get(self.target.control), ebs.get(self.target.pivot)
    if target_eb:
        for child in target_eb.children:
            child.parent = ebs.get(self.target.source)
        ebs.remove(target_eb)
    if pivot_eb:
        ebs.remove(pivot_eb)
    for digit in self.digits:
        roll_eb, track_eb = ebs.get(digit.roll), ebs.get(digit.track)
        if roll_eb:
            ebs.remove(roll_eb)
        if track_eb:
            ebs.remove(track_eb)
    
    # then return to pose mode like nothing ever happened...
    bpy.ops.object.mode_set(mode='POSE')
    # and unrig all the digits?...
    for digit in self.digits:
        rigging = armature.jk_arm.rigging[digit.rigging]
        chain = rigging.get_pointer()
        if chain.is_rigged:
            chain.is_rigged = False

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTIES -------------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

class JK_PG_ARM_Hand_Digit(bpy.types.PropertyGroup):

    is_thumb: BoolProperty(name="Is Thumb", description="Is this digit a thumb",
        default=False, update=_functions_.update_properties)

    flavour: EnumProperty(name="Type", description="What kind of chain should this digit use",
        items = [('NONE', 'Select rigging type...', ""), ('SCALAR', "Scalar (Chain)", ""), ('FORWARD', "Forward (Chain)", "")],
        default='NONE', update=_functions_.update_properties)

    def get_rigging(self):
        name = ""
        for rigging in self.id_data.jk_arm.rigging:
            if rigging.flavour == self.flavour:
                chain = rigging.forward if self.flavour == 'FORWARD' else rigging.scalar
                if chain.target.end == self.end:
                    name = rigging.name
                    break
        return name

    rigging: StringProperty(name="Rigging", description="The rigging associated with this digit", 
        get=get_rigging)

    end: StringProperty(name="End", description="Name of the bone at the end of the digit chain", 
        default="", update=_functions_.update_properties)

    length: IntProperty(name="Length", description="How many bones are included in this digit chain",
        default=3, min=2, update=_functions_.update_properties)

    roll: StringProperty(name="Curl", description="Name of the roll bone once created")

    roll_axis: EnumProperty(name="Roll Axis", description="The local axis the first digit bone rolls around",
        items=[('X', 'X axis', "", "CON_ROTLIKE", 0),
        #('Y', 'Y axis', "", "CON_ROTLIKE", 2),
        ('Z', 'Z axis', "", "CON_ROTLIKE", 4)],
        default='X', update=_functions_.update_properties)

    track: StringProperty(name="Spread", description="Name of the track bone once created")

    track_axis: EnumProperty(name="Track Axis", description="The local axis the first digit bone tracks over",
        items=[('X', 'X axis', "", "CON_TRACKTO", 0),
        #('Y', 'Y axis', "", "CON_TRACKTO", 2),
        ('Z', 'Z axis', "", "CON_TRACKTO", 4)],
        default='X', update=_functions_.update_properties)

class JK_PG_ARM_Hand_Metacarpal(bpy.types.PropertyGroup):
    
    show_metacarpal: BoolProperty()

    source: StringProperty()

    origin: StringProperty()

    target: StringProperty()

class JK_PG_ARM_Hand_Controls(bpy.types.PropertyGroup):

    digits: CollectionProperty(type=JK_PG_ARM_Hand_Digit)

    #metacarpals: CollectionProperty(type=JK_PG_ARM_Hand_Metacarpal)

    target: PointerProperty(type=_properties_.JK_PG_ARM_Target)

    constraints: CollectionProperty(type=_properties_.JK_PG_ARM_Constraint)

    drivers: CollectionProperty(type=_properties_.JK_PG_ARM_Driver)

    def get_references(self):
        return get_hand_refs(self)

    def get_sources(self):
        sources = [digit.end for digit in self.digits]
        return sources

    def get_groups(self):
        groups = {
            "Mechanic Bones" : [digit.track for digit in self.digits] + [self.target.pivot],
            "Gizmo Bones" : [digit.roll for digit in self.digits],
            "Control Bones": [self.target.control]}
        return groups

    def get_shapes(self):
        shapes = {
            "Bone_Shape_Default_Tail_Fan" : [self.target.control],
            "Bone_Shape_Default_Head_Sphere" : [self.target.pivot],
            "Bone_Shape_Default_Tail_Socket" : [digit.track for digit in self.digits],
            "Bone_Shape_Default_Tail_Sphere" : [digit.roll for digit in self.digits]}
        return shapes

    def get_is_riggable(self):
        # we are going to need to know if the rigging in the properties is riggable...
        armature, is_riggable = self.id_data, True
        bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
        # for this rigging we iterate on some names...
        for digit in self.digits:
            bone = bones.get(digit.end)
            chain = armature.jk_arm.rigging[digit.rigging].get_pointer()
            # if those names are not existing bones or the digit chain isn't riggable...
            if bone == None or not chain.is_riggable:
                # this riggin' ain't riggable...
                is_riggable = False
                break
        return is_riggable

    is_riggable: BoolProperty(name="Is Riggable", description="Can this chain have it's rigging applied?",
        get=get_is_riggable)

    def update_is_rigged(self, context):
        # whenever we set "is_rigged" to false, kill the rigging...
        if not self.is_rigged:
            remove_hand_controls(self, self.id_data)

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
            get_hand_props(self, self.id_data)
            self.has_properties = True
        # always set the properties that get calculated from the essentials...
        set_hand_props(self, self.id_data)
        # if we can rig from the properties...
        if self.is_riggable:
            # add the rigging...
            add_hand_controls(self, self.id_data)
            self.is_rigged = True

    use_default_groups: BoolProperty(name="Use Default Groups", description="Do you want this rigging to use some default bone groups?",
        default=False, update=update_rigging)

    use_default_shapes: BoolProperty(name="Use Default Shapes", description="Do you want this rigging to use some default bone shapes?",
        default=False, update=update_rigging)

    use_default_layers: BoolProperty(name="Use Default Layers", description="Do you want this rigging to use some default armature layers?",
        default=False, update=update_rigging)

    show_digits: BoolProperty()

    show_metacarpals: BoolProperty()

    use_chain: BoolProperty()

    chain: StringProperty()


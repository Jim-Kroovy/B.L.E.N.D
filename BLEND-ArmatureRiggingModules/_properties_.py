import bpy

from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty) 

from . import _functions_

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- RIGGING PROPERTIES -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

class JK_PG_ARM_Constraint(bpy.types.PropertyGroup):

    source: StringProperty(name="Source", description="Name of the bone the constraint is on",
        default="", maxlen=63)

    constraint: StringProperty(name="Constraint", description="Name of the actual constraint",
        default="", maxlen=63)

    flavour: EnumProperty(name="Flavour", description="The type of constraint",
        items=[('NONE', 'None', ""), ('COPY_TRANSFORMS', 'Copy Transforms', ""),
            ('COPY_ROTATION', 'Copy Rotation', ""), ('COPY_LOCATION', 'Copy Location', ""), ('COPY_SCALE', 'Copy Scale', ""),
            ('LIMIT_ROTATION', 'Limit Rotation', ""), ('LIMIT_SCALE', 'Limit Scale', ""),
            ('FLOOR', 'Floor', ""), ('IK', 'Inverse Kinematics', ""), ('DAMPED_TRACK', 'Damped Track', "")],
        default='NONE')
    
    subtarget: StringProperty(name="Subtarget", description="Name of the subtarget. (if any)",
        default="", maxlen=1024, update=_functions_.update_properties)

    pole_subtarget: StringProperty(name="Pole Target", description="Name of the pole target. (if any)",
        default="", maxlen=1024)

    chain_count: IntProperty(name="Chain Length", description="How many bones are included in the IK effect",
        default=2, min=0)

    influence: FloatProperty(name="Influence", description="influence of this constraint", default=1.0, min=0.0, max=1.0, subtype='FACTOR')
    
    power: FloatProperty(name="Power", description="Raise the targets scale to the specified power", default=1.0)

    head_tail: FloatProperty(name="Head/Tail", description="target along length of bone", default=0.0, min=0.0, max=1.0, subtype='FACTOR')

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

    use_offset: BoolProperty(name="Use Offset", description="Combine original transform with copied (Scale/Location)", default=False)

    mix_mode: EnumProperty(name="Mix Mode", description="Specify how the copied and existing rotations are combined",
        items=[('REPLACE', "Replace", "Replace original rotation with copied"), 
            ('ADD', "Add", "Add euler component values together"),
            ('BEFORE', "Before Original", "Apply copied rotation before original, as if the constraint target is a parent"),
            ('AFTER', "After Original", "Apply copied rotation after original, as if the constraint target is a child"),
            ('OFFSET', "Fit Curve", "Combine rotations like the original offset checkbox. Does not work well for multiple axis rotations")],
        default='REPLACE')

    y_scale_mode: EnumProperty(name="Y Scale Mode", description="Method used for determining the scaling of the Y axis of the bones, on top of the shape and scaling of the curve itself",
        items=[('NONE', "None", "Don't scale on the Y axis"), 
            ('BONE_ORIGINAL', "Bone Original", "Use original Y scale"), 
            ('FIT_CURVE', "Fit Curve", "Scale bones to fit the entire length of the curve")],
        default='BONE_ORIGINAL')

    track_axis: EnumProperty(name="Track Axis", description="Axis that points to the target object",
        items=[('TRACK_X', 'X', ""), ('TRACK_Y', 'Y', ""), ('TRACK_Z', 'Z', ""), 
            ('TRACK_NEGATIVE_X', '-X', ""), ('TRACK_NEGATIVE_Y', '-Y', ""), ('TRACK_NEGATIVE_Z', '-Z', "")],
        default='TRACK_Y')

    lock_axis: EnumProperty(name="Lock Axis", description="Axis that points upward",
        items=[('LOCK_X', 'X', ""), ('LOCK_Y', 'Y', ""), ('LOCK_Z', 'Z', "")],
        default='LOCK_X')

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

class JK_PG_ARM_Variable(bpy.types.PropertyGroup):

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

class JK_PG_ARM_Driver(bpy.types.PropertyGroup):

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

    variables: CollectionProperty(type=JK_PG_ARM_Variable)

class JK_PG_ARM_Target(bpy.types.PropertyGroup):

    source: StringProperty(name="Source", description="Name of the source bone the target is created from",
        default="", maxlen=63, update=_functions_.update_properties)

    origin: StringProperty(name="Origin", description="Name of the source bones original parent",
        default="", maxlen=63)

    bone: StringProperty(name="Bone", description="Name of the actual target",
        default="", maxlen=63)

    parent: StringProperty(name="Parent", description="Name of the targets control parent (if any)",
        default="", maxlen=63)

    root: StringProperty(name="Root",description="The targets root bone (if any)", 
        default="", maxlen=63, update=_functions_.update_properties)

    offset: StringProperty(name="Offset", description="Name of the bone that offsets the targets rotation from its source bone",
        default="", maxlen=63)

    control: StringProperty(name="Control", description="Name of the bone that controls the target mechanism",
        default="", maxlen=1024)

    roll: StringProperty(name="Roll", description="Name of the rolling bone in the target mechanism",
        default="", maxlen=1024)

    pivot: StringProperty(name="Pivot", description="Name of the bone used to create a pivot for controls. (eg: bone at the ball of the foot)", 
        default="", maxlen=1024, update=_functions_.update_properties)
    
    pivot_roll: StringProperty(name="Pivot Roll", description="Name of the bone in the roll mechanism for the pivot",
        default="", maxlen=1024)

    pivot_offset: StringProperty(name="Pivot Offset", description="Name of the bone used to offset the pivot",
        default="", maxlen=1024)

    end: StringProperty(name="End", description="Name of the bone at the end of the chain (if any)",
        default="", maxlen=63, update=_functions_.update_properties)

    length: IntProperty(name="Chain Length", description="How many bones are included in this chain",
        default=3, min=2, update=_functions_.update_properties)

    use: BoolProperty(name="Use", description="Use the source bone to create a target", default=False, update=_functions_.update_properties)

    use_edited: BoolProperty(name="Use Edited", description="The user set this source bone to create a target", default=False)

    co: FloatVectorProperty(name="Co", description="The target bones head/tail location. (used to set up curves)",
        default=(0.0, 0.0, 0.0), size=3, subtype='TRANSLATION')

    axis: EnumProperty(name="Axis", description="The local axis the target is created away from the source bones (of the armature for tracking chains, of the bone for hands)",
        items=[('X', 'X axis', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X axis', "", "CON_LOCLIKE", 1),
        ('Y', 'Y axis', "", "CON_LOCLIKE", 2),
        ('Y_NEGATIVE', '-Y axis', "", "CON_LOCLIKE", 3),
        ('Z', 'Z axis', "", "CON_LOCLIKE", 4),
        ('Z_NEGATIVE', '-Z axis', "", "CON_LOCLIKE", 5)],
        default='Y', update=_functions_.update_properties)

    distance: FloatProperty(name="Distance", description="The distance the target is created from the source bones. (in metres)", 
        default=0.25, update=_functions_.update_properties)

    direction: EnumProperty(name="Direction", description="The local axis of the source bone that the target is oriented along (which axis points to the out of the top of the hand?)",
        items=[('X', 'X axis', "", "CON_ROTLIKE", 0),
        ('X_NEGATIVE', '-X axis', "", "CON_ROTLIKE", 1),
        ('Y', 'Y axis', "", "CON_ROTLIKE", 2),
        ('Y_NEGATIVE', '-Y axis', "", "CON_ROTLIKE", 3),
        ('Z', 'Z axis', "", "CON_ROTLIKE", 4),
        ('Z_NEGATIVE', '-Z axis', "", "CON_ROTLIKE", 5)],
        default='X', update=_functions_.update_properties)

    lock_x: FloatProperty(name="Lock X", description="Influence of the locked tracking around the stretchy controllers X Axis. (Only needed during 360 X rotations)", 
        default=0.0, min=0.0, max=1.0, subtype='FACTOR')

    lock_z: FloatProperty(name="Lock Z", description="Influence of the locked tracking around the stretchy controllers Z Axis. (Only needed during 360 Z rotations)", 
        default=0.0, min=0.0, max=1.0, subtype='FACTOR')

class JK_PG_ARM_Pole(bpy.types.PropertyGroup):

    source: StringProperty(name="Source", description="Name of the source bone the target is created from",
        default="", maxlen=63)

    origin: StringProperty(name="Origin", description="Name of the source bones original parent",
        default="", maxlen=63)

    bone: StringProperty(name="Bone", description="Name of the actual target",
        default="", maxlen=63)

    root: StringProperty(name="Root",description="The targets root bone. (if any)", 
        default="", maxlen=63)

    axis: EnumProperty(name="Axis", description="The local axis of the start bone that the pole target is created along",
        items=[('X', 'X axis', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X axis', "", "CON_LOCLIKE", 1),
        ('Z', 'Z axis', "", "CON_LOCLIKE", 2),
        ('Z_NEGATIVE', '-Z axis', "", "CON_LOCLIKE", 3)],
        default='X', update=_functions_.update_properties)

    def get_pole_angle(self):
        angle = -3.141593 if self.axis == 'X_NEGATIVE' else 1.570796 if self.axis == 'Z' else -1.570796 if self.axis == 'Z_NEGATIVE' else 0.0
        return angle

    angle: FloatProperty(name="Angle", description="The angle of the IK pole target. (degrees)", 
        default=0.0, subtype='ANGLE', get=get_pole_angle)

    distance: FloatProperty(name="distance", description="The distance the pole target is from the IK parent. (in metres)", 
        default=0.25, update=_functions_.update_properties)

class JK_PG_ARM_Floor(bpy.types.PropertyGroup):

    source: StringProperty(name="Source", description="Name of the source bone the floor is created for",
        default="", maxlen=63)

    bone: StringProperty(name="Bone", description="Name of the actual floor bone",
        default="", maxlen=63)

    root: StringProperty(name="Root", description="Name of the floor bones root. (if any)",
        default="", maxlen=63, update=_functions_.update_properties)

class JK_PG_ARM_Bone(bpy.types.PropertyGroup):

    source: StringProperty(name="Source", description="Name of the source bone",
        default="", maxlen=63)

    origin: StringProperty(name="Origin", description="Name of the source bones original parent",
        default="", maxlen=63)

    gizmo: StringProperty(name="Gizmo", description="Name of the gizmo bone that copies the stretch with limits",
        default="", maxlen=63)

    stretch: StringProperty(name="Stretch",description="Name of the stretch bone that smooths kinematics", 
        default="", maxlen=63)

    use_offset: BoolProperty(name="Use Offset", description="Use an offset bone to provide an independent pivot from the rigging",
        default=False, update=_functions_.update_properties)

    offset: StringProperty(name="Offset", description="Name of the bone that offsets the targets rotation from its source bone",
        default="", maxlen=63)

    length: FloatProperty(name="Length", description="The source bones length before rigging", 
        default=0.0)

    head: FloatVectorProperty(name="Head", description="The source bones head location before rigging",
        default=(0.0, 0.0, 0.0), size=3, subtype='TRANSLATION')

    tail: FloatVectorProperty(name="Tail", description="The source bones tail location before rigging",
        default=(0.0, 0.0, 0.0), size=3, subtype='TRANSLATION')

    roll: FloatProperty(name="Roll", description="The source bones roll before rigging", 
        default=0.0, subtype='ANGLE', unit='ROTATION')

    axis: EnumProperty(name="Shape Axis", description="The local axis of the bone that defines which custom shape to use",
        items=[('X', 'X axis', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X axis', "", "CON_LOCLIKE", 1),
        ('Z', 'Z axis', "", "CON_LOCLIKE", 4),
        ('Z_NEGATIVE', '-Z axis', "", "CON_LOCLIKE", 5)],
        default='Z_NEGATIVE', update=_functions_.update_properties)

    lean: FloatProperty(name="Lean", description="Influence of leaning towards the target", 
        default=1.0, min=0.0, max=1.0, subtype='FACTOR')

    turn: FloatProperty(name="Turn", description="Influence of turning towards the target", 
        default=1.0, min=0.0, max=1.0, subtype='FACTOR')

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- GENERAL PROPERTIES -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

class JK_PG_ARM_Source(bpy.types.PropertyGroup):

    head: FloatVectorProperty(name="Source Head", description="The head of the source bone",
        size=3, subtype='TRANSLATION', default=[0.0, 0.0, 0.0])

    tail: FloatVectorProperty(name="Source Tail", description="The tail of the source bone",
        size=3, subtype='TRANSLATION', default=[0.0, 0.0, 0.0])

    roll: FloatProperty(name="Source Roll", description="The roll of the source bone", 
        default=0.0, subtype='ANGLE', unit='ROTATION')

class JK_PG_ARM_Rigging(bpy.types.PropertyGroup):

    from .modules.chains import (_opposable_, _plantigrade_, _digitigrade_, _forward_, _spline_, _scalar_, _tracking_)
    from .modules.twists import (_headhold_, _tailfollow_)
    from .modules import _hand_

    def get_pointer(self):
        pointers = {'HAND' : self.hand, #'FACE' : self.face,
            'HEAD_HOLD' : self.headhold, 'TAIL_FOLLOW' : self.tailfollow, 
            'OPPOSABLE' : self.opposable, 'PLANTIGRADE' : self.plantigrade, 'DIGITIGRADE' : self.digitigrade,
            'FORWARD' : self.forward, 'SPLINE' : self.spline, 'SCALAR' : self.scalar, 'TRACKING' : self.tracking}
        return pointers[self.flavour]

    def update_flavour(self, context):
        self.is_editing = True
        if self.id_data.data.bones.active:
            self.side = _functions_.get_bone_side(self.id_data.data.bones.active.name)
        self.is_editing = False
        # whenever we change the flavour of rigging...
        pointers = {'HAND' : self.hand, #'FACE' : self.face,
            'HEAD_HOLD' : self.headhold, 'TAIL_FOLLOW' : self.tailfollow, 
            'OPPOSABLE' : self.opposable, 'PLANTIGRADE' : self.plantigrade, 'DIGITIGRADE' : self.digitigrade,
            'FORWARD' : self.forward, 'SPLINE' : self.spline, 'SCALAR' : self.scalar, 'TRACKING' : self.tracking}
        # iterate on the dictionary of flavours to pointers...
        for flavour, pointer in pointers.items():
            # if a pointer is rigged...
            if pointer.is_rigged:
                # trigger the update that removes it...
                pointer.is_rigged = False
            # if it's the new flavour...
            if flavour == self.flavour:
                # make sure the pointers properties get refreshed... (if it had any)
                pointer.has_properties = False
                # when we trigger the pointers rigging update...
                pointer.update_rigging(context)

    def check_sources(self):
        detected = []
        # for each of the saved source transforms...
        for sb in self.sources:
            # try to get the source bone bone...
            bb = self.id_data.data.bones.get(sb.name)
            if bb:
                # check if the bone bones head, tail or roll have changed...
                head, tail = bb.head_local, bb.tail_local
                _, roll = bb.AxisRollFromMatrix(bb.matrix_local.to_3x3())
                if sb.head != head or sb.tail != tail or round(sb.roll, 2) != round(roll, 2):
                    # if a change is detected then append the name and break...
                    detected.append(sb.name)
                    break
            # if we didn't get the bone...
            else:
                # then just detect a change and break iteration...
                detected.append(sb.name)
                break
        return True if detected else False

    def get_sources(self):
        pointer = self.get_pointer()
        names = pointer.get_sources()
        for name in names:
            bb = self.id_data.data.bones.get(name)
            if bb:
                head, tail = bb.head_local, bb.tail_local
                _, roll = bb.AxisRollFromMatrix(bb.matrix_local.to_3x3())
                source = self.sources.add()
                source.name, source.head, source.tail, source.roll = name, head, tail, roll

    def subscribe_mode(self):
        _functions_.subscribe_mode_to(self.id_data, _functions_.armature_mode_callback)

    sources: CollectionProperty(type=JK_PG_ARM_Source)

    flavour: EnumProperty(name="Type", description="The type of rigging",
        items=[('NONE', 'Select rigging type...', ""),
            ('HAND', 'Hand (Merged)', "A combination of digit controls and optionally metacarpal and hand controls"),
            # chains...
            ('OPPOSABLE', 'Opposable (Chain)', "A simple IK chain of 2 bones with a pole target. (Generally used by arms)"),
            ('PLANTIGRADE', 'Plantigrade (Chain)', "An opposable IK chain of 2 bones with a pole target and standard foot rolling controls. (Generally used by human legs)"),
            ('DIGITIGRADE', 'Digitigrade (Chain)', "A scalar IK chain of 3 bones with a pole target and special foot controls. (Generally used by animal legs)"),
            ('SPLINE', 'Spline (Chain)', "A spline IK chain of 3 or more bones controlled by a curve that's manipulated with target bones. (Generally used by tails/spines)"),
            ('SCALAR', 'Scalar (Chain)', "An IK chain of 3 or more bones controlled by scaling and rotating a parent of the target. (Generally used for fingers)"),
            ('FORWARD', 'Forward (Chain)', "An FK chain of 1 or more bones where the chain copies loc/rot/scale of a parent/target. (Generally an alternative used for fingers/tails)"),
            ('TRACKING', 'Tracking (Chain)', "An IK chain of 2 or more bones where a target is used for tracking. (Generally used for head tracking that influences the neck/shoulders)"),
            # twists...
            ('HEAD_HOLD', 'Head Hold (Twist)', "A twist bone that holds deformation at the head of the bone back by tracking to a target. (eg: Upper Arm Twist)"),
            ('TAIL_FOLLOW', 'Tail Follow (Twist)', "A twist bone that follows deformation at the tail of the bone by copying the local Y rotation of a target. (eg: Lower Arm Twist)")],
        default='NONE', update=update_flavour)

    def update_side(self, context):
        if not self.is_editing:
            # some rigging types need updating if the side changes...
            if self.flavour == 'PLANTIGRADE':
                self.plantigrade.update_rigging(context)
            elif self.flavour == 'DIGITGRADE':
                self.digitigrade.update_rigging(context)
    
    side: EnumProperty(name="Side", description="Which side of the armature is this chain on. (if any)",
        items=[('NONE', 'None', "Not on any side, probably central"),
            ('LEFT', 'Left', "Chain is on the left side"),
            ('RIGHT', 'Right', "Chain is on the right side")],
        default='NONE', update=update_side)

    opposable: PointerProperty(type=_opposable_.JK_PG_ARM_Opposable_Chain)

    plantigrade: PointerProperty(type=_plantigrade_.JK_PG_ARM_Plantigrade_Chain)
    
    digitigrade: PointerProperty(type=_digitigrade_.JK_PG_ARM_Digitigrade_Chain)

    forward: PointerProperty(type=_forward_.JK_PG_ARM_Forward_Chain)

    spline: PointerProperty(type=_spline_.JK_PG_ARM_Spline_Chain)

    scalar: PointerProperty(type=_scalar_.JK_PG_ARM_Scalar_Chain)

    tracking: PointerProperty(type=_tracking_.JK_PG_ARM_Tracking_Chain)

    headhold: PointerProperty(type=_headhold_.JK_PG_ARM_HeadHold_Twist)

    tailfollow: PointerProperty(type=_tailfollow_.JK_PG_ARM_TailFollow_Twist)

    is_merged: BoolProperty(name="Is Merged", description="Is this rigging merged with a combination module?",
        default=False)

    hand: PointerProperty(type=_hand_.JK_PG_ARM_Hand_Controls)

    is_editing: BoolProperty(name="Is Editing", description="Is this rigging being edited internally? (if it is we need to stop update functions from firing)",
        default=False)

class JK_PG_ARM_Affixes(bpy.types.PropertyGroup):

    target: StringProperty(name="Target", description="The prefix of target bones", 
        default="TB_", maxlen=1024)

    floor: StringProperty(name="Floor", description="The prefix of floor target bones", 
        default="FB_", maxlen=1024)

    control: StringProperty(name="Control", description="The prefix of controller bones. (Uses 'Armature Control Bones' control prefix if it's installed? i think lol)", 
        default="CB_", maxlen=1024)

    offset: StringProperty(name="Offset", description="The prefix of bones that are used to offset constraints, inherited transforms and limitations", 
        default="OB_", maxlen=1024)

    gizmo: StringProperty(name="Gizmo", description="The prefix of hidden bones that are used to indirectly create movement", 
        default="GB_", maxlen=1024)

    mech: StringProperty(name="Mech", description="The prefix of hidden bones that are used to create mechanisms", 
        default="MB_", maxlen=1024)

    stretch: StringProperty(name="Stretch", description="The affix given to hidden bones that stretch to create soft kinematics",
        default="STRETCH_", maxlen=1024)

    roll: StringProperty(name="Roll", description="The affix given to hidden bones used in rolling mechanisms", 
        default="ROLL_", maxlen=1024)

    track: StringProperty(name="Track", description="The affix given to hidden bones used in tracking mechanisms",
        default="TRACK_", maxlen=1024)
    
    local: StringProperty(name="Local", description="The affix given to bones that hold local transforms", 
        default="LOCAL_", maxlen=1024)

class JK_PG_ARM_Bones(bpy.types.PropertyGroup):

    theme: StringProperty(name='Theme', description="The theme for this bone group",
        default="")

    layers: BoolVectorProperty(name="Layers", description="The layers this group of bones belongs too",
        size=32)

    def update_hide(self, context):
        armature = self.id_data
        armature.jk_arm.update_hidden_bones()

    edit_hide: BoolProperty(name="Hide", description="Show/hide edit bones in this group",
        default=False)

    pose_hide: BoolProperty(name="Hide", description="Show/hide pose bones in this group",
        default=False, update=update_hide)

class JK_PG_ARM_Object(bpy.types.PropertyGroup):

    def subscribe_mode(self):
        _functions_.subscribe_mode_to(self.id_data, _functions_.armature_mode_callback)

    active: IntProperty(name='Active', default=0, min=0)

    rigging: CollectionProperty(type=JK_PG_ARM_Rigging)

    forward_axis: EnumProperty(name="Forward Axis", description="The local forward axis of the armature",
        items=[('X', 'X axis', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X axis', "", "CON_LOCLIKE", 1),
        ('Y', 'Y axis', "", "CON_LOCLIKE", 2),
        ('Y_NEGATIVE', '-Y axis', "", "CON_LOCLIKE", 3),
        ('Z', 'Z axis', "", "CON_LOCLIKE", 4),
        ('Z_NEGATIVE', '-Z axis', "", "CON_LOCLIKE", 5)],
        default='X')

    upward_axis: EnumProperty(name="Up Axis", description="The local upward axis of the armature",
        items=[('X', 'X axis', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X axis', "", "CON_LOCLIKE", 1),
        ('Y', 'Y axis', "", "CON_LOCLIKE", 2),
        ('Y_NEGATIVE', '-Y axis', "", "CON_LOCLIKE", 3),
        ('Z', 'Z axis', "", "CON_LOCLIKE", 4),
        ('Z_NEGATIVE', '-Z axis', "", "CON_LOCLIKE", 5)],
        default='X')

    is_mode_subbed: BoolProperty(name="Is Subbed", description="Does this armature object have its mode subscribed to msgbus",
        default=False)

    use_edit_detection: BoolProperty(name="Auto Update", description="Do you want this armature to automatically regenerate it's rigging when changes to source bones in edit mode are detected?",
        default=False)

    def update_hidden_bones(self):
        bones = self.id_data.data.edit_bones if self.id_data.mode == 'EDIT' else self.id_data.data.bones
        hide_groups = {'Chain Bones' : self.chain_bones.edit_hide if self.id_data.mode == 'EDIT' else self.chain_bones.pose_hide,
            'Twist Bones' : self.twist_bones.edit_hide if self.id_data.mode == 'EDIT' else self.twist_bones.pose_hide,
            'Gizmo Bones' : self.gizmo_bones.edit_hide if self.id_data.mode == 'EDIT' else self.gizmo_bones.pose_hide,
            'Mechanic Bones' : self.mechanic_bones.edit_hide if self.id_data.mode == 'EDIT' else self.mechanic_bones.pose_hide,
            'Control Bones' : self.control_bones.edit_hide if self.id_data.mode == 'EDIT' else self.control_bones.pose_hide,
            'Offset Bones' : self.offset_bones.edit_hide if self.id_data.mode == 'EDIT' else self.offset_bones.pose_hide,
            'Kinematic Targets' : self.kinematic_targets.edit_hide if self.id_data.mode == 'EDIT' else self.kinematic_targets.pose_hide,
            'Floor Targets' : self.floor_targets.edit_hide if self.id_data.mode == 'EDIT' else self.floor_targets.pose_hide}
        
        for rigging in self.rigging:
            if rigging.flavour != 'NONE':
                pointer = rigging.get_pointer()
                bone_groups = pointer.get_groups()
                for group, names in bone_groups.items():
                    if group in hide_groups:
                        for name in names:
                            bone = bones.get(name)
                            if bone:
                                bone.hide = hide_groups[group]

    chain_bones: PointerProperty(type=JK_PG_ARM_Bones)
    twist_bones: PointerProperty(type=JK_PG_ARM_Bones)
    
    gizmo_bones: PointerProperty(type=JK_PG_ARM_Bones)
    mechanic_bones: PointerProperty(type=JK_PG_ARM_Bones)
    
    control_bones: PointerProperty(type=JK_PG_ARM_Bones)
    offset_bones: PointerProperty(type=JK_PG_ARM_Bones)

    kinematic_targets: PointerProperty(type=JK_PG_ARM_Bones)
    floor_targets: PointerProperty(type=JK_PG_ARM_Bones)

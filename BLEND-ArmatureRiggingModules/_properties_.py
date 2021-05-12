import bpy
from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty) 
from . import _functions_

from .library.chains import (_opposable_, _plantigrade_, _digitigrade_, _forward_, _spline_, _scalar_, _tracking_)
from .library.twists import (_headhold_, _tailfollow_)

class JK_PG_ARM_Rigging(bpy.types.PropertyGroup):

    def get_pointer(self):
        pointers = {'HEAD_HOLD' : self.headhold, 'TAIL_FOLLOW' : self.tailfollow, 
            'OPPOSABLE' : self.opposable, 'PLANTIGRADE' : self.plantigrade, 'DIGITIGRADE' : self.digitigrade,
            'FORWARD' : self.forward, 'SPLINE' : self.spline, 'SCALAR' : self.scalar, 'TRACKING' : self.tracking}
        return pointers[self.flavour]

    def update_flavour(self, context):
        self.is_editing = True
        self.side = _functions_.get_bone_side(self.id_data.data.bones.active.name)
        self.is_editing = False
        # whenever we change the flavour of rigging...
        pointers = {'HEAD_HOLD' : self.headhold, 'TAIL_FOLLOW' : self.tailfollow, 
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

    flavour: EnumProperty(name="Type", description="The type of rigging",
        items=[('NONE', 'Select rigging type...', ""),
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
    
    local: StringProperty(name="Local", description="The affix given to bones that hold local transforms", 
        default="LOCAL_", maxlen=1024)

class JK_PG_ARM_Object(bpy.types.PropertyGroup):

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
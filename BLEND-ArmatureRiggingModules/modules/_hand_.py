import bpy

from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty)

from .chains import _scalar_, _spline_, _forward_

# Much of this code is copy/pasted between the various flavours of rigging, while a little long winded it makes adding new things and updating and troubleshooting a whole lot easier...
# and everyone wants me to do so much i decided it's better that things are easy to edit/create and not as dynamic as they could be...

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTIES -------------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

class JK_PG_ARM_Digit(bpy.types.PropertyGroup):

    flavour: EnumProperty()

    scalar: PointerProperty()

    spline: PointerProperty()

    forward: PointerProperty()

class JK_PG_ARM_Metacarpal(bpy.types.PropertyGroup):

    source: StringProperty

    origin: StringProperty

    target: StringProperty

class JK_PG_ARM_Hand_Combo(bpy.types.PropertyGroup):

    source: StringProperty

    origin: StringProperty


    show_digits: BoolProperty()

    digits: CollectionProperty(type=JK_PG_ARM_Digit)

    show_metacarpals: BoolProperty()

    metacarpals: CollectionProperty(type=JK_PG_ARM_Metacarpal)


    use_palm: BoolProperty()

    rigging: StringProperty()


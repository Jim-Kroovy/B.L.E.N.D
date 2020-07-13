# Contributor(s): James Goldsworthy (Jim Kroovy)

# Support: https://twitter.com/JimKroovy
#          https://www.facebook.com/JimKroovy
#          http://youtube.com/c/JimKroovy
#          https://www.patreon.com/JimKroovy

# This code is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "B.L.E.N.D - Switch Rotation Mode",
    "author": "James Goldsworthy (Jim Kroovy)",
    "version": (1, 0),
    "blender": (2, 83, 0),
    "location": "Dope Sheet > Key",
    "description": "Enables switching the rotation mode of fcurves keyed into actions",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Animation",
    }

##### NOTES #####

# This is the first part of a series of modular add-ons that i hope can increase the quality of life within Blender.
# Who knows i might put forward some of them to the Blender devs to become built in!
#
# SRM provides what i (and Brad) feel should be some built in functionality for rotation mode switching on bones and objects...
# and it does it with support for keys that is not possible with duped armatures and baked constraints/drivers.
#
# It just doesn't make sense that we should have to re-keyframe all rotations after switching mode!
#
# Currently SRM does not support fcurve modifiers and drivers, it simply swaps fcurves and keyframes between rotation modes...
# I have not tested this with NLA strips so it might not work on those either and key handles are being swapped as close as possible.

import bpy

from bpy.utils import (register_class, unregister_class)

from . import (_functions_, _properties_, _operators_)

JK_ARMS_classes = (_properties_.JK_ARMS_Operator_Props, _operators_.JK_OT_Set_Action_Rotation_Mode)

def register():
    for cls in JK_ARMS_classes:
        register_class(cls)

    bpy.types.DOPESHEET_MT_key.append(_functions_.Add_To_Menu)
        
def unregister():
    for cls in reversed(JK_ARMS_classes):
        unregister_class(cls)
    
    bpy.types.DOPESHEET_MT_key.remove(_functions_.Add_To_Menu)
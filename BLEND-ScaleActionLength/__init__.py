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
    "name": "B.L.E.N.D - Scale Action Length",
    "author": "James Goldsworthy (Jim Kroovy)",
    "version": (1, 0),
    "blender": (2, 83, 0),
    "location": "Dope Sheet > Key",
    "description": "Enables scaling the playhead of actions to the desired FPS or Time",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Animation",
    }

##### NOTES #####

# This is the third part of a series of modular add-ons that i hope can increase the quality of life within Blender.
# Who knows i might put forward some of them to the Blender devs to become built in!
#
# SAL provides what i feel should be some built in functionality for scaling the length of actions bpy framerate and time...
#
# It just doesn't make sense that we can't simply specify a framerate or time frame and switch an action to it!

import bpy

from bpy.utils import (register_class, unregister_class)

from . import (_functions_, _properties_, _operators_)

JK_SAL_classes = (_properties_.JK_SAL_Operator_Props, _operators_.JK_OT_Set_Action_Length)

def register():
    for cls in JK_SAL_classes:
        register_class(cls)

    bpy.types.DOPESHEET_MT_key.append(_functions_.Add_To_Menu)
        
def unregister():
    for cls in reversed(JK_SAL_classes):
        unregister_class(cls)
    
    bpy.types.DOPESHEET_MT_key.remove(_functions_.Add_To_Menu)
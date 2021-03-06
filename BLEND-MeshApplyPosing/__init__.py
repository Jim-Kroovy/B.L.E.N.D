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
    "name": "B.L.E.N.D - Mesh Apply Posing",
    "author": "James Goldsworthy (Jim Kroovy)",
    "version": (1, 0),
    "blender": (2, 90, 0),
    "location": "3D View > Pose",
    "description": "Apply/Re-apply the armature modifier on meshes and applies the armature pose to rest pose",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Armatures",
    }

import bpy

from bpy.utils import (register_class, unregister_class)

from . import _operators_, _functions_

def register():
    print("REGISTER: ['B.L.E.N.D - Mesh Apply Posing']")
    register_class(_operators_.JK_OT_Apply_Posing)
    print("Classes registered...")
    bpy.types.VIEW3D_MT_pose.append(_functions_.Add_To_Pose_Menu)
    print("Operator appended...")

def unregister():
    print("UNREGISTER: ['B.L.E.N.D - Mesh Apply Posing']")
    unregister_class(_operators_.JK_OT_Apply_Posing)
    print("Classes unregistered...")
    bpy.types.VIEW3D_MT_pose.remove(_functions_.Add_To_Pose_Menu)
    print("Operator removed...")
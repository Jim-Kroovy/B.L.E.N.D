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
    "name": "B.L.E.N.D - Armature Bone Mapping",
    "author": "James Goldsworthy (Jim Kroovy)",
    "version": (1, 0),
    "blender": (2, 83, 0),
    "location": "Armature > Pose",
    "description": "Maps armature bones to a three dimensional array of naming conventions",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Armatures",
    }

import bpy

from bpy.utils import (register_class, unregister_class)

from . import _properties_, _operators_, _interface_

JK_ACB_classes = (_operators_.JK_OT_Apply_Posing)

def Add_To_Pose_Menu(self, context):
    self.layout.operator("jk.apply_mesh_posing")

def register():
    #for cls in JK_ACB_classes:
    register_class(_operators_.JK_OT_Apply_Posing)

    bpy.types.VIEW3D_MT_pose.append(Add_To_Pose_Menu)

def unregister():
    #for cls in reversed(JK_ACB_classes):
    unregister_class(_operators_.JK_OT_Apply_Posing)
    
    bpy.types.VIEW3D_MT_pose.remove(Add_To_Pose_Menu)
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

# By downloading these files you agree to the above licenses where they are applicable.

bl_info = {
    "name": "B.L.E.N.D - Armature Better Symmetrize",
    "author": "James Goldsworthy (Jim Kroovy)",
    "version": (1, 0),
    "blender": (2, 90, 0),
    "location": "3D View > Armature",
    "description": "Symmetrize edit bones with more options than the default symmetrize",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Armatures",
    }
    
import bpy

from . import _operators_, _functions_

from bpy.utils import (register_class, unregister_class)

def register():
    #for cls in JK_SRM_classes:
        #register_class(cls)
    register_class(_operators_.JK_OT_Set_Armature_Symmetry)

    bpy.types.VIEW3D_MT_edit_armature.append(_functions_.Add_To_Edit_Menu)
        
def unregister():
    #for cls in reversed(JK_SRM_classes):
        #unregister_class(cls)
    
    bpy.types.VIEW3D_MT_edit_armature.remove(_functions_.Add_To_Edit_Menu)

    unregister_class(_operators_.JK_OT_Set_Armature_Symmetry)

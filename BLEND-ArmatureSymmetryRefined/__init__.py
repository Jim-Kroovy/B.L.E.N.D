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
    "name": "B.L.E.N.D - Armature Symmetry Refined",
    "author": "James Goldsworthy (Jim Kroovy)",
    "version": (1, 0, 0),
    "blender": (2, 93, 0),
    "location": "3D View > Armature",
    "description": "Symmetrize edit and pose bones with more options than the default symmetry/mirror operators",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Armatures",
    }
    
import bpy

from . import _operators_, _functions_

from bpy.utils import (register_class, unregister_class)

def register():
    print("REGISTER: ['B.L.E.N.D - Armature Better Symmetrize']")
    register_class(_operators_.JK_OT_ASR_Set_Armature_Symmetry)
    print("Classes registered...")

    bpy.types.VIEW3D_MT_edit_armature.append(_functions_.add_to_edit_menu)
    print("Operator appended...")
        
def unregister():
    print("UNREGISTER: ['B.L.E.N.D - Armature Better Symmetrize']")
    bpy.types.VIEW3D_MT_edit_armature.remove(_functions_.add_to_edit_menu)
    print("Operator removed...")

    unregister_class(_operators_.JK_OT_ASR_Set_Armature_Symmetry)
    print("Classes unregistered...")

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

# By downloading these files you agree to the above license where applicable.

bl_info = {
    "name": "B.L.E.N.D - Armature Retarget Dynamics",
    "author": "James Goldsworthy (Jim Kroovy)",
    "version": (1, 0, 0),
    "blender": (2, 93, 0),
    "location": "Armature > Pose",
    "description": "Retargets actions and meshes between armatures with realtime offset tweaking",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Armatures",
    }
    
import bpy

from bpy.utils import (register_class, unregister_class)

from . import (_properties_, _operators_, _interface_)

JK_ARD_classes = (
    # properties...
    _properties_.JK_PG_ARD_Constraint, 
    _properties_.JK_PG_ARD_Binding_Bone, 
    _properties_.JK_PG_ARD_Binding,
    _properties_.JK_PG_ARD_Pose_Bone, 
    _properties_.JK_PG_ARD_Offset_Action_Slot, 
    _properties_.JK_PG_ARD_Offset_Slot, 
    _properties_.JK_PG_ARD_Armature,
    # operators...
    _operators_.JK_OT_ARD_Bake_Retarget_Actions, 
    _operators_.JK_OT_ARD_Add_Action_Slot, 
    _operators_.JK_OT_ARD_Remove_Action_Slot,
    _operators_.JK_OT_ARD_Edit_Binding,
    _operators_.JK_OT_ARD_Auto_Offset,
    # interface...
    _interface_.JK_ARD_Addon_Prefs,
    _interface_.JK_UL_ARD_Action_List, 
    _interface_.JK_PT_ARD_Armature_Panel, 
    _interface_.JK_PT_ARD_Bone_Panel,
    _interface_.JK_PT_ARD_Offset_Panel, 
    _interface_.JK_PT_ARD_Offset_Action_Panel
    )

def register():
    print("REGISTER: ['B.L.E.N.D - Armature Active Retargeting']")
    for cls in JK_ARD_classes:
        register_class(cls)
    print("Classes registered...")   
    # register the armature type properties...
    bpy.types.Armature.jk_ard = bpy.props.PointerProperty(type=_properties_.JK_ARD_Armature_Props)
    print("Properties assigned...")

def unregister():
    print("UNREGISTER: ['B.L.E.N.D - Armature Active Retargeting']")
    for cls in reversed(JK_ARD_classes):
        unregister_class(cls)
    print("Classes unregistered...")   
    del bpy.types.Armature.ARD
    print("Properties deleted...")
    
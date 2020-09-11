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
    "name": "B.L.E.N.D - Armature Control Bones",
    "author": "James Goldsworthy (Jim Kroovy)",
    "version": (1, 0),
    "blender": (2, 90, 0),
    "location": "Armature > Add",
    "description": "Builds mechanism bones that manipulate deformation bones indirectly via control bones",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Armatures",
    }

import bpy

from bpy.utils import (register_class, unregister_class)

from . import _functions_, _properties_, _operators_, _interface_

JK_ACB_classes = (_properties_.JK_ACB_Bone_Props,
    _properties_.JK_ACB_Mesh_Props, 
    _properties_.JK_ACB_Armature_Props,
    _operators_.JK_OT_Edit_Controls, 
    _operators_.JK_OT_ACB_Subscribe_Object_Mode,
    _interface_.JK_ACB_Addon_Prefs, 
    _interface_.JK_PT_ACB_Armature_Panel)

from bpy.app.handlers import persistent

@persistent
def ACB_Subscription_Handler(dummy):
    # iterate on all armature objects...
    for armature in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
        # if they have any controls...
        if any(b.ACB.Type != 'NONE' for b in armature.data.bones):
            # re-sub them and any/all their meshes to the msgbus...
            _functions_.Subscribe_Mode_To(armature, _functions_.Armature_Mode_Callback)
            _functions_.Set_Meshes(armature)
    # then set the mech/cont prefix to themselves to fire update on bone names...
    prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
    prefs.Cont_prefix, prefs.Mech_prefix = prefs.Cont_prefix, prefs.Mech_prefix
                          
# do this on load to re-subscribe callbacks and keep everything up to date...
bpy.app.handlers.load_post.append(ACB_Subscription_Handler)

def register():
    for cls in JK_ACB_classes:
        register_class(cls)
    
    bpy.types.Armature.ACB = bpy.props.PointerProperty(type=_properties_.JK_ACB_Armature_Props)
    bpy.types.Bone.ACB = bpy.props.PointerProperty(type=_properties_.JK_ACB_Bone_Props)
        
def unregister():
    for cls in reversed(JK_ACB_classes):
        unregister_class(cls)
    
    del bpy.types.Bone.ACB
    del bpy.types.Armature.ACB
    
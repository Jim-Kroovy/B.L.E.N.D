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
    "blender": (2, 83, 0),
    "location": "Armature > Add",
    "description": "Builds mechanism bones that manipulate the selected bones indirectly via control bones",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Armatures",
    }

import bpy

from bpy.utils import (register_class, unregister_class)

from . import _functions_, _properties_, _operators_, _interface_

JK_ACB_classes = (_properties_.JK_ACB_Bone_Props, _properties_.JK_ACB_Armature_Props, 
    _operators_.JK_OT_Add_Controls, _operators_.JK_OT_Edit_Controls, 
    _interface_.JK_PT_ACB_Armature_Panel)

from bpy.app.handlers import persistent

@persistent
def ACB_Subscription_Handler(dummy):
    armatures = {}
    # iterate on all armature objects...
    for obj in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
        data = obj.data
        # if the there are any controls...
        if data.ACB.Has_controls:
            # resub the object mode callback...
            _functions_.Subscribe_Mode_To(obj, 'mode', _functions_.Object_Mode_Callback)
            # if we haven't already processed this armature...
            if data.name not in armatures:
                # get the bones we need to resub...
                bones = data.edit_bones if obj.mode == 'EDIT' else data.bones
                to_bones = data.ACB.Edit_bones if obj.mode == 'EDIT' else data.ACB.Bones
                # iterate on the bones...
                for bone in bones:
                    # if the bones name is in the controls...
                    if bone.name in to_bones:
                        # resub it...
                        _functions_.Subscribe_Bone_To(bone, to_bones[bone.name], "name", _functions_.Bone_Name_Callback)
                # then add it to the armature dictionary so it doesn't get processed again... 
                armatures[data.name] = True
                          
# do this on load to re-subscribe callbacks...
bpy.app.handlers.load_post.append(ACB_Subscription_Handler)

def register():
    for cls in JK_ACB_classes:
        register_class(cls)
    
    bpy.types.Armature.ACB = bpy.props.PointerProperty(type=_properties_.JK_ACB_Armature_Props)

    bpy.types.TOPBAR_MT_edit_armature_add.append(_functions_.Add_To_Edit_Menu)
        
def unregister():
    for cls in reversed(JK_ACB_classes):
        unregister_class(cls)
    
    bpy.types.TOPBAR_MT_edit_armature_add.remove(_functions_.Add_To_Edit_Menu)

    del bpy.types.Armature.ACB
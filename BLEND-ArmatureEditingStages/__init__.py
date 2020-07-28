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

#### NOTES ####

# So! Welcome to armature editing stages (AES) and i hope you find it useful... i know i do! ;)
#
# As the name suggests whole point of this add-on is to easily revert/progress through stages of armature editing...
# as it can be very frustrating getting half way through animating to then realise you need to change some crucial rigging.
#
# AES started as a simple stage hierarchy for my other add-on Mr Mannequins Tools and then evolved into its own thing because...
# Mr Mannes was getting to big and i wanted to break out its functionality into seperate add-ons.
#
# I plan to work on keyframing the change of stage so that it's much easier to switch between rigging during animation...
# and at some point there might also be a node tree to better visualise the stage heirarchy.

bl_info = {
    "name": "B.L.E.N.D - Armature Editing Stages",
    "author": "James Goldsworthy (Jim Kroovy)",
    "version": (1, 0),
    "blender": (2, 83, 0),
    "location": "3D View > Tools",
    "description": "Enables saving and switching the state of the armature through created stages",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Armatures",
    }
    
import bpy

from bpy.utils import (register_class, unregister_class)

from . import (_properties_, _operators_, _interface_)

from bpy.app.handlers import persistent

@persistent
def AES_Clean_Handler(dummy):
    # iterate on all armature objects...
    for obj in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
        # get the armature data...
        data = obj.data
        # if it's a stage and it's parent no longer exists...
        if not data.AES.Is_master:
            if obj.parent == None:
                # remove the object and data...
                bpy.data.objects.remove(obj)
                bpy.data.armatures.remove(data)
# do this on load to keep things clean after deleting master armatures...
bpy.app.handlers.load_post.append(AES_Clean_Handler)

JK_AES_classes = (
    # properties...
    _properties_.JK_AES_Edit_Bone_Props, _properties_.JK_AES_Pose_Bone_Props, _properties_.JK_AES_Bone_Props,
    _properties_.JK_AES_Stage_Props, _properties_.JK_AES_Armature_Props, 
    # operators...
    _operators_.JK_OT_Add_Armature_Stage, _operators_.JK_OT_Remove_Armature_Stage, _operators_.JK_OT_Edit_Armature_Stage,
    _operators_.JK_OT_Switch_Armature_Stage, _operators_.JK_OT_Copy_Active_Push_Settings,
    # interface...
    _interface_.JK_MMT_Addon_Prefs, _interface_.JK_PT_AES_Armature_Panel, _interface_.JK_PT_AES_Bone_Panel
    )

def register():
    for cls in JK_AES_classes:
        register_class(cls)   
    
    bpy.types.Armature.AES = bpy.props.PointerProperty(type=_properties_.JK_AES_Armature_Props)
        
def unregister():
    for cls in reversed(JK_AES_classes):
        unregister_class(cls)
    
    del bpy.types.Armature.AES
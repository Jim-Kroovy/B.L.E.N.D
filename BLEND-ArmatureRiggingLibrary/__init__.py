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
    "name": "B.L.E.N.D - Armature Rigging Library",
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

#@persistent
#def ARL_Keyframe_Handler(dummy):
    # iterate on all armature objects...
    #for obj in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
        
# do this on load to keep things clean after deleting master armatures...
#bpy.app.handlers.load_post.append(AES_Clean_Handler)

JK_ARL_classes = (
    # properties...
    _properties_.JK_ARL_Pivot_Bone_Props,
    _properties_.JK_ARL_Floor_Bone_Props,
    _properties_.JK_ARL_Limit_Props, 
    _properties_.JK_ARL_Twist_Bone_Props, 
    _properties_.JK_ARL_Chain_Target_Bone_Props,
    _properties_.JK_ARL_Chain_Pole_Bone_Props, 
    _properties_.JK_ARL_Chain_Bone_Props, 
    _properties_.JK_ARL_Chain_Spline_Props, 
    _properties_.JK_ARL_Chain_Forward_Props, 
    _properties_.JK_ARL_Chain_Props, 
    _properties_.JK_ARL_Affix_Props, 
    _properties_.JK_ARL_Rigging_Library_Props,
    # operators...
    _operators_.JK_OT_Add_Twist, 
    _operators_.JK_OT_Add_Chain,
    # interface...
    _interface_.JK_UL_Rigging_List,
    _interface_.JK_PT_ARL_Armature_Panel
    )

def register():
    for cls in JK_ARL_classes:
        register_class(cls)   
    
    bpy.types.Object.ARL = bpy.props.PointerProperty(type=_properties_.JK_ARL_Rigging_Library_Props)
        
def unregister():
    for cls in reversed(JK_ARL_classes):
        unregister_class(cls)
    
    del bpy.types.Object.ARL
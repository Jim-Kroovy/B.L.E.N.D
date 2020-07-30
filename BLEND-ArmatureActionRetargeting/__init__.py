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
    "name": "B.L.E.N.D - Armature Action Retargeting",
    "author": "James Goldsworthy (Jim Kroovy)",
    "version": (1, 0),
    "blender": (2, 83, 0),
    "location": "Armature > Pose",
    "description": "Retargets actions between armatures with realtime offset tweaking",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Animation",
    }
    
import bpy

from bpy.utils import (register_class, unregister_class)

from . import (_properties_, _operators_, _interface_)

JK_AAR_classes = (
    # properties...
    _properties_.JK_AAR_Pose_Bone_Props, _properties_.JK_AAR_Action_Pointer, _properties_.JK_AAR_Action_Props, _properties_.JK_AAR_Armature_Props,
    # operators...
    _operators_.JK_OT_Bake_Action,
    # interface...
    _interface_.JK_PT_AAR_Armature_Panel, _interface_.JK_PT_AAR_Bone_Panel
    )

def register():
    for cls in JK_AAR_classes:
        register_class(cls)   
    
    bpy.types.Armature.AAR = bpy.props.PointerProperty(type=_properties_.JK_AAR_Armature_Props)
    bpy.types.Action.AAR = bpy.props.PointerProperty(type=_properties_.JK_AAR_Action_Props)    

def unregister():
    for cls in reversed(JK_AAR_classes):
        unregister_class(cls)
    
    del bpy.types.Action.AAR
    del bpy.types.Armature.AAR
    
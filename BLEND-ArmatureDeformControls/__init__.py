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
    "name": "B.L.E.N.D - Armature Deform Controls",
    "author": "James Goldsworthy (Jim Kroovy)",
    "version": (1, 1, 0),
    "blender": (2, 93, 0),
    "location": "Properties > Data > Deform Controls",
    "description": "Builds control bones that manipulate deformation bones indirectly to maintain compatibility between other applications.",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Armatures",
    }

import bpy

from bpy.utils import (register_class, unregister_class)

from . import _functions_, _properties_, _operators_, _interface_

jk_adc_classes = (
    _properties_.JK_PG_ADC_EditBone,
    _properties_.JK_PG_ADC_PoseBone,
    _properties_.JK_PG_ADC_Armature,
    _operators_.JK_OT_ADC_Edit_Controls,
    _operators_.JK_OT_ADC_Bake_Deforms,
    _operators_.JK_OT_ADC_Bake_Controls,
    _operators_.JK_OT_ADC_Refresh_Constraints,
    _operators_.JK_OT_ADC_Subscribe_Object_Mode,
    _operators_.JK_OT_ADC_Set_Selected,
    _interface_.JK_ADC_Addon_Prefs, 
    _interface_.JK_PT_ADC_Armature_Panel,
    _interface_.JK_PT_ADC_Bone_Panel)

from bpy.app.handlers import persistent

@persistent
def jk_adc_on_load_post(dummy):
    # iterate on all armature objects...
    for armature in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
        # if they have any controls...
        if armature.data.jk_adc.is_controller:
            # re-sub them to the msgbus... (add mesh function in here for auto-hiding?)
            _functions_.subscribe_mode_to(armature, _functions_.armature_mode_callback)
    # then set the deform prefix to itself to fire update on bone/armature names...
    prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
    prefs.deform_prefix = prefs.deform_prefix

def register():
    print("REGISTER: ['B.L.E.N.D - Armature Deform Controls']")
    
    for cls in jk_adc_classes:
        register_class(cls)
    print("Classes registered...")
    
    bpy.types.Armature.jk_adc = bpy.props.PointerProperty(type=_properties_.JK_PG_ADC_Armature)
    bpy.types.EditBone.jk_adc = bpy.props.PointerProperty(type=_properties_.JK_PG_ADC_EditBone)
    bpy.types.PoseBone.jk_adc = bpy.props.PointerProperty(type=_properties_.JK_PG_ADC_PoseBone)
    print("Properties assigned...")
    
    if jk_adc_on_load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(jk_adc_on_load_post)
        print("Load post handler appended...")
        
def unregister():
    print("UNREGISTER: ['B.L.E.N.D - Armature Deform Controls']")
    
    if jk_adc_on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(jk_adc_on_load_post)
        print("Load post handler removed...")
    
    del bpy.types.PoseBone.jk_adc
    del bpy.types.EditBone.jk_adc
    del bpy.types.Armature.jk_adc
    print("Properties deleted...")
    
    for cls in reversed(jk_adc_classes):
        unregister_class(cls)
    print("Classes unregistered...")
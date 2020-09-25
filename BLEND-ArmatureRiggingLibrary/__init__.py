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
    "name": "B.L.E.N.D - Armature Rigging Library",
    "author": "James Goldsworthy (Jim Kroovy)",
    "version": (1, 0),
    "blender": (2, 90, 0),
    "location": "3D View > Tools",
    "description": "Enables saving and switching the state of the armature through created stages",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Armatures",
    }
    
import bpy

from bpy.utils import (register_class, unregister_class)

from . import (_properties_, _operators_, _interface_, _functions_)

from bpy.app.handlers import persistent

# this is probably the best way to achieve auto IK vs FK...
def ARL_Auto_FK_Timer():
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingLibrary"].preferences
    # get all valid armature objects and iterate on them...
    objs = [o for o in bpy.data.objects if o.type == 'ARMATURE' and any(ch.Auto_fk for ch in o.ARL.Chains)]
    for obj in objs:
        # if it's in pose mode...
        if obj.mode == 'POSE' and (not obj.ARL.Is_playing):
            # get it's active bone name and all the chains that are using auto FK...
            chains = [ch for ch in obj.ARL.Chains if ch.Auto_fk]
            print(len(chains))
            # if there are actually any chains to check...
            if len(chains) > 0:
                # iterate over them...
                for chain in chains:
                    # if any chain bones are selected, set use FK to true...
                    if any(obj.data.bones[cb.name].select for cb in chain.Bones):
                        chain.Use_fk = True
                    else:
                        # otherwise just set it false...
                        chain.Use_fk = False
    # check this at the users preference of frequency...
    return prefs.Auto_freq
# while not the most performant, it's alot more stable than hacking the msgbus system...

@persistent
def ARL_Load_Timers_Handler(dummy):
    # timers can't be persistant so if the Auto FK timer isn't registered...
    if not bpy.app.timers.is_registered(ARL_Auto_FK_Timer):
        # give it a kick in the arse...
        bpy.app.timers.register(ARL_Auto_FK_Timer)

@persistent
def ARL_Keyframe_Handler(dummy):
    # iterate on all armature objects...
    for obj in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
        # for each chain that has inequal fk bools and is not using auto fk...
        for chain in [ch for ch in obj.ARL.Chains if ch.Last_fk != ch.Use_fk]:
            # set use fk to itself to trigger the update...
            chain.Use_fk = chain.Use_fk
            # if the chain is using auto switching and auto keyframing...
            if chain.Auto_fk and chain.Auto_key:
                # we should match selection...
                for cb in chain.Bones:
                    # to stop auto keying on the next switch update...
                    obj.data.bones[cb.name].select = chain.Use_fk
        # set the last frame so we can auto-key on switch again...
        obj.ARL.Last_frame = bpy.context.scene.frame_float   
# do this after each frame updates to force the use fk boolean update function...

JK_ARL_classes = (
    # properties...
    _properties_.JK_ARL_Pivot_Bone_Props,
    _properties_.JK_ARL_Floor_Bone_Props,
    _properties_.JK_ARL_Twist_Bone_Props, 
    _properties_.JK_ARL_Chain_Target_Bone_Props,
    _properties_.JK_ARL_Chain_Pole_Bone_Props, 
    _properties_.JK_ARL_Chain_Bone_Props, 
    _properties_.JK_ARL_Chain_Spline_Props, 
    _properties_.JK_ARL_Chain_Forward_Props, 
    _properties_.JK_ARL_Chain_Props, 
    _properties_.JK_ARL_Affix_Props,
    _properties_.JK_ARL_Bone_Props,
    _properties_.JK_ARL_Armature_Props, 
    _properties_.JK_ARL_Object_Props,
    # operators...
    _operators_.JK_OT_Set_Pivot,
    _operators_.JK_OT_Set_Floor,
    _operators_.JK_OT_Set_Twist, 
    _operators_.JK_OT_Set_Chain,
    _operators_.JK_OT_Select_Bone,
    _operators_.JK_OT_Key_Chain,
    # interface...
    _interface_.JK_ARL_Addon_Prefs,
    _interface_.JK_UL_Rigging_List,
    _interface_.JK_PT_ARL_Armature_Panel,
    _interface_.JK_PT_ARL_Chain_Panel,
    _interface_.JK_PT_ARL_Twist_Panel,
    _interface_.JK_PT_ARL_Pivot_Panel,
    _interface_.JK_PT_ARL_Floor_Panel)

def register():
    print("REGISTER: ['B.L.E.N.D - Armature Rigging Library']")
    
    for cls in JK_ARL_classes:
        register_class(cls)
    print("Classes registered...")    
    
    bpy.types.Bone.ARL = bpy.props.PointerProperty(type=_properties_.JK_ARL_Bone_Props)
    bpy.types.Armature.ARL = bpy.props.PointerProperty(type=_properties_.JK_ARL_Armature_Props)
    bpy.types.Object.ARL = bpy.props.PointerProperty(type=_properties_.JK_ARL_Object_Props)
    print("Properties assigned...")

    if ARL_Keyframe_Handler not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(ARL_Keyframe_Handler)
        print("Keyframe Handler appended...")

    if ARL_Load_Timers_Handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(ARL_Load_Timers_Handler)
        print("Load Timers appended...")
        
def unregister():
    print("UNREGISTER: ['B.L.E.N.D - Armature Rigging Library']")
    
    if ARL_Keyframe_Handler in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(ARL_Keyframe_Handler)
        print("Keyframe Handler removed...")

    if ARL_Load_Timers_Handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(ARL_Load_Timers_Handler)
        print("Load Timers removed...")
    
    del bpy.types.Object.ARL
    del bpy.types.Armature.ARL
    del bpy.types.Bone.ARL
    print("Properties deleted...")
    
    for cls in reversed(JK_ARL_classes):
        unregister_class(cls)
    print("Classes unregistered...")
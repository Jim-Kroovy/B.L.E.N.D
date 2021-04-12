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
    "version": (1, 0, 0),
    "blender": (2, 90, 0),
    "location": "Properties > Data > Rigging",
    "description": "Enables saving and switching the state of the armature through created stages",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Armatures",
    }
    
import bpy

from bpy.utils import (register_class, unregister_class)

from . import (_properties_, _operators_, _interface_, _functions_)

from .library.chains import (_opposable_, _plantigrade_, _digitigrade_, _forward_, _spline_, _scalar_, _tracking_)
from .library.twists import (_headhold_, _tailfollow_)

from bpy.app.handlers import persistent

# while not the most performant, this is alot more stable than hacking the msgbus system...
def jk_arl_auto_fk_timer():
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingLibrary"].preferences
    is_playing, selected = bpy.context.screen.is_animation_playing, bpy.context.selected_objects
    # if we have selected objects and are in pose mode and not playing any animation...
    if selected and (bpy.context.object and bpy.context.object.mode == 'POSE') and not is_playing:
        # get all potentially valid armature objects and iterate on them...
        armatures = [ob for ob in selected if ob.type == 'ARMATURE' and len(ob.jk_arl.rigging) > 0]
        for armature in armatures:
            # get the chains using auto fk...
            auto_chains = [ch.digitigrade if ch.flavour == 'DIGITIGRADE' else ch.plantigrade if ch.flavour == 'PLANTIGRADE' else ch.opposable 
                for ch in armature.jk_arl.rigging if (ch.digitigrade.use_auto_fk or ch.plantigrade.use_auto_fk or ch.opposable.use_auto_fk)]
            if auto_chains:
                # if we have any chains iterate on them...
                for auto_chain in auto_chains:
                    # toggle the switch based on their fk selection bool return...
                    if auto_chain.is_auto_fk and not auto_chain.use_fk:
                        auto_chain.use_fk = True
                    elif auto_chain.use_fk and not auto_chain.is_auto_fk:
                        auto_chain.use_fk = False
    # check this at the users preference of frequency...
    return prefs.auto_freq

# do this after each frame updates to force the use fk boolean update function...
@persistent
def jk_arl_on_frame_change_post(dummy):
    # iterate on all armatures with chains...
    armatures = _functions_.get_chain_armatures()
    for arma in armatures:
        # get all the chains with inequal last_fk and use fk bools...
        chains = _functions_.get_chain_rigging(arma)
        switch_chains = [ch for ch in chains if ch.last_fk != ch.use_fk]
        # if there are any...
        if switch_chains:
            # iterate on them and trigger the "use_fk" update function...
            for chain in switch_chains:
                chain.use_fk = chain.use_fk

@persistent
def jk_arl_on_load_post(dummy):
    # timers can't be persistent so if the Auto FK timer isn't registered...
    if not bpy.app.timers.is_registered(jk_arl_auto_fk_timer):
        # give it a kick in the arse...
        bpy.app.timers.register(jk_arl_auto_fk_timer)
    # then iterate on all valid armature objects... (we might have invalid drivers after updating?)
    for armature in [o for o in bpy.data.objects if o.type == 'ARMATURE' and len(o.jk_arl.rigging) > 0]: 
        # if they have any drivers...
        if armature.animation_data and armature.animation_data.drivers:
            # iterate on them checking if they are valid...
            for drv in armature.animation_data.drivers:
                #if not drv.driver.is_valid:
                # if they are invalid reset their expression to trigger dependency update...
                drv.driver.expression = drv.driver.expression

jk_arl_classes = (
    # head hold twist properties...
    _headhold_.JK_PG_ARL_HeadHold_Constraint, _headhold_.JK_PG_ARL_HeadHold_Bone, _headhold_.JK_PG_ARL_HeadHold_Twist,
    # tail follow twist properties...
    _tailfollow_.JK_PG_ARL_TailFollow_Constraint, _tailfollow_.JK_PG_ARL_TailFollow_Bone, _tailfollow_.JK_PG_ARL_TailFollow_Twist,
    # opposable chain properties...
    _opposable_.JK_PG_ARL_Opposable_Variable, _opposable_.JK_PG_ARL_Opposable_Driver, 
    _opposable_.JK_PG_ARL_Opposable_Constraint, _opposable_.JK_PG_ARL_Opposable_Floor, 
    _opposable_.JK_PG_ARL_Opposable_Target, _opposable_.JK_PG_ARL_Opposable_Pole, 
    _opposable_.JK_PG_ARL_Opposable_Bone, _opposable_.JK_PG_ARL_Opposable_Chain,
    # plantigrade chain properties...
    _plantigrade_.JK_PG_ARL_Plantigrade_Variable, _plantigrade_.JK_PG_ARL_Plantigrade_Driver, 
    _plantigrade_.JK_PG_ARL_Plantigrade_Constraint, _plantigrade_.JK_PG_ARL_Plantigrade_Floor, 
    _plantigrade_.JK_PG_ARL_Plantigrade_Target, _plantigrade_.JK_PG_ARL_Plantigrade_Pole, 
    _plantigrade_.JK_PG_ARL_Plantigrade_Bone, _plantigrade_.JK_PG_ARL_Plantigrade_Chain,
    # digitigrade chain properties...
    _digitigrade_.JK_PG_ARL_Digitigrade_Variable, _digitigrade_.JK_PG_ARL_Digitigrade_Driver, 
    _digitigrade_.JK_PG_ARL_Digitigrade_Constraint, _digitigrade_.JK_PG_ARL_Digitigrade_Floor, 
    _digitigrade_.JK_PG_ARL_Digitigrade_Target, _digitigrade_.JK_PG_ARL_Digitigrade_Pole, 
    _digitigrade_.JK_PG_ARL_Digitigrade_Bone, _digitigrade_.JK_PG_ARL_Digitigrade_Chain,
    # spline chain properties...
    _spline_.JK_PG_ARL_Spline_Variable, _spline_.JK_PG_ARL_Spline_Driver,
    _spline_.JK_PG_ARL_Spline_Constraint, _spline_.JK_PG_ARL_Spline_Bone, _spline_.JK_PG_ARL_Spline_Curve,
    _spline_.JK_PG_ARL_Spline_Target, _spline_.JK_PG_ARL_Spline_Chain,
    # scalar properties...
    _scalar_.JK_PG_ARL_Scalar_Variable, _scalar_.JK_PG_ARL_Scalar_Driver,
    _scalar_.JK_PG_ARL_Scalar_Constraint, _scalar_.JK_PG_ARL_Scalar_Bone, _scalar_.JK_PG_ARL_Scalar_Floor,
    _scalar_.JK_PG_ARL_Scalar_Target, _scalar_.JK_PG_ARL_Scalar_Chain,
    # tracking chain properties...
    _tracking_.JK_PG_ARL_Tracking_Variable, _tracking_.JK_PG_ARL_Tracking_Driver,
    _tracking_.JK_PG_ARL_Tracking_Constraint, _tracking_.JK_PG_ARL_Tracking_Bone,
    _tracking_.JK_PG_ARL_Tracking_Target, _tracking_.JK_PG_ARL_Tracking_Chain,
    # forward chain properties...
    _forward_.JK_PG_ARL_Forward_Constraint, _forward_.JK_PG_ARL_Forward_Bone, 
    _forward_.JK_PG_ARL_Forward_Target, _forward_.JK_PG_ARL_Forward_Chain,
    # general properties...
    _properties_.JK_PG_ARL_Rigging, _properties_.JK_PG_ARL_Affixes, _properties_.JK_PG_ARL_Object,
    # operators...
    _operators_.JK_OT_ARL_Set_Rigging, _operators_.JK_OT_ARL_Snap_Bones,
    # interface...
    _interface_.JK_ARL_Addon_Prefs, _interface_.JK_UL_ARL_Rigging_List, _interface_.JK_PT_ARL_Armature_Panel, _interface_.JK_PT_ARL_Edit_Panel, _interface_.JK_PT_ARL_Pose_Panel
)

def register():
    print("REGISTER: ['B.L.E.N.D - Armature Rigging Library']")
    
    for cls in jk_arl_classes:
        register_class(cls)
    print("Classes registered...")

    bpy.types.Object.jk_arl = bpy.props.PointerProperty(type=_properties_.JK_PG_ARL_Object)
    print("Properties assigned...")
    
    if jk_arl_on_frame_change_post not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(jk_arl_on_frame_change_post)
        print("Keyframe change handler appended...")

    if jk_arl_on_load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(jk_arl_on_load_post)
        if not bpy.app.timers.is_registered(jk_arl_auto_fk_timer):
            bpy.app.timers.register(jk_arl_auto_fk_timer)
        print("Load post handler appended...")

def unregister():
    print("UNREGISTER: ['B.L.E.N.D - Armature Rigging Library']")
    
    if jk_arl_on_frame_change_post in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(jk_arl_on_frame_change_post)
        print("Keyframe handler removed...")

    if jk_arl_on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(jk_arl_on_load_post)
        if bpy.app.timers.is_registered(jk_arl_auto_fk_timer):
            bpy.app.timers.unregister(jk_arl_auto_fk_timer)
        print("Load handler removed...")

    del bpy.types.Object.jk_arl
    print("Properties deleted...")
    
    for cls in reversed(jk_arl_classes):
        unregister_class(cls)
    print("Classes unregistered...")
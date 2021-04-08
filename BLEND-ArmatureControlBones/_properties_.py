import bpy
import json
from bpy.props import (EnumProperty, BoolProperty, StringProperty, CollectionProperty, FloatProperty, IntProperty, PointerProperty)
from . import _functions_

class JK_PG_ACB_Mesh(bpy.types.PropertyGroup):

    armature: StringProperty(name="Armature", description="The first armature this mesh is weighted to")
    
class JK_PG_ACB_Armature(bpy.types.PropertyGroup):

    def apply_transforms(self, controller, deformer):
        prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
        prefix = prefs.deform_prefix if controller.data.jk_acb.use_combined else ""
        pbs, bbs = deformer.pose.bones, controller.data.bones
        # if the armatures have transforms applied, we need to update the deform .json...
        deforms = _functions_.set_deform_bones(controller, deformer)
        controller.data.jk_acb.deforms = json.dumps(deforms)
        # and all the constraints should be reset...
        for bone in deforms:
            deform_pb = pbs.get(prefix + bone['name'])
            control_bb = bbs.get(bone['name'])
            if deform_pb and control_bb:
                _functions_.add_deform_constraints(controller, deform_pb, control_bb, limits=False)

    def get_actions(self, armature, only_active=False, reverse=False):
        prefs = bpy.context.preferences.addons["BLEND-ArmatureControlBones"].preferences
        source, baked = {}, {}
        # only use the active action...
        if only_active and armature.animation_data:
            # if the armature has animation data and an active action...
            action = armature.animation_data.action
            if action:
                source = {action : bpy.data.actions.get(prefs.deform_prefix + action.name)}
                baked = {action : bpy.data.actions.get(action.name[len(prefs.deform_prefix):])}
        else:
            # get a dictionary of all control actions to their baked deform counterparts...
            source = {act : bpy.data.actions.get(prefs.deform_prefix + act.name) for act in bpy.data.actions 
                if any(fc.data_path.partition('"')[2].split('"')[0] in armature.data.bones for fc in act.fcurves) 
                and not act.name.startswith(prefs.deform_prefix)}
            # get a dictionary of all deform actions to their baked control counterparts...
            baked = {act : bpy.data.actions.get(action.name[len(prefs.deform_prefix):]) for act in bpy.data.actions 
                if any(fc.data_path.partition('"')[2].split('"')[0] in armature.data.bones for fc in act.fcurves) 
                and act.name.startswith(prefs.deform_prefix)}
        return source, baked

    use_auto_update: BoolProperty(name="Auto Update", description="Automatically update any changes made to control/deform bones when leaving edit mode",
        default=False, options=set())

    auto_hide: BoolProperty(name="Auto Hide", description="Automatically hide/show deform bones depending on mode. (Shows only controls in pose mode and only deform bones in edit/weight mode",
        default=False, options=set())

    def update_use_deforms(self, context):
        controller, deformer = _functions_.get_armatures()
        _functions_.use_deforms(controller, deformer, self.use_deforms)

    use_deforms: BoolProperty(name="Use Deforms", description="Use deform/control bones to deform the mesh",
        default=False, options=set(), update=update_use_deforms)

    def update_use_combined(self, context):
        controller, deformer = _functions_.get_armatures()
        _functions_.set_combined(controller, deformer, self.use_combined)

    use_combined: BoolProperty(name="Combine Armatures", description="Deformation bones are combined into the control armature",
        default=False, options=set(), update=update_use_combined)

    def update_mute_deforms(self, context):
        _, deformer = _functions_.get_armatures()
        _functions_.mute_deform_constraints(deformer, self.mute_deforms)
    
    mute_deforms: BoolProperty(name="Mute Constraints", description="Mute deform bone constraints (deform bones are unaffected by the controls)",
        default=False, options=set(), update=update_mute_deforms)

    def update_reverse_deforms(self, context):
        controller, deformer = _functions_.get_armatures()
        _functions_.reverse_deform_constraints(controller, deformer, self.reverse_deforms)

    reverse_deforms: BoolProperty(name="Reverse Constraints", description="Reverse deform bone constraints so control bones follow deform bones (WARNING! Constraints on controls get muted but drivers stay enabled and may cause problems)",
        default=False, options=set(), update=update_reverse_deforms)

    def update_use_scale(self, context):
        controller, deformer = _functions_.get_armatures()
        _functions_.use_deform_scale(controller, deformer)
    
    use_scale: BoolProperty(name="Use Scale", description="Child of constraints use scale (Useful to not use scale to export stretching to Unreal Engine)",
        default=False, options=set(), update=update_use_scale)

    def update_hide_deforms(self, context):
        controller, deformer = _functions_.get_armatures()
        _functions_.hide_deforms(controller, deformer, self.hide_deforms)

    hide_deforms: BoolProperty(name="Hide Deforms", description="Hide/Show deform bones",
        default=False, options=set(), update=update_hide_deforms)

    def update_hide_controls(self, context):
        controller, _ = _functions_.get_armatures()
        _functions_.hide_controls(controller, self.hide_controls)

    hide_controls: BoolProperty(name="Hide Controls", description="Hide/Show control bones",
        default=False, options=set(), update=update_hide_controls)

    def update_hide_others(self, context):
        controller, _ = _functions_.get_armatures()
        _functions_.hide_others(controller, self.hide_others)

    hide_others: BoolProperty(name="Hide Others", description="Hide/Show bones that are not control or deform bones",
        default=False, options=set(), update=update_hide_others)
    
    is_deformer:  BoolProperty(name="Is Deform Armature", description="Is this a deformation armature",
        default=False, options=set())

    is_controller:  BoolProperty(name="Is Control Armature", description="Is this an animation control armature",
        default=False, options=set())

    armature: PointerProperty(type=bpy.types.Object)

    deforms: StringProperty(name="Deform Bones", description="The .json list that stores the deform bones")

    #action: StringProperty(name="Action", description="When set this ")
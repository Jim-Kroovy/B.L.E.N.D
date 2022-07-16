import bpy
from bpy.props import (EnumProperty, BoolProperty, StringProperty, CollectionProperty, FloatProperty, FloatVectorProperty, IntProperty, PointerProperty)
from . import _functions_
import random

class JK_PG_ADC_Bone(bpy.types.PropertyGroup):

    def get_armature(self):
        return self.id_data.jk_adc.get_armature()

    def get_control(self):
        # always operating through controls...
        controller = self.id_data.jk_adc.get_controller()
        deformer = self.id_data.jk_adc.get_deformer()
        for bb in controller.data.bones:
            # will mean always knowing...
            if bb.jk_adc == self:
                # what this function returns...
                if controller.mode == 'EDIT':
                    return controller.data.edit_bones.get(bb.name)
                else:
                    return controller.pose.bones.get(bb.name)
        #if controller.mode == 'EDIT':
            #controller.update_from_editmode()
            #if deformer:
                #deformer.update_from_editmode()

    def get_deform(self):
        # always operating through controls...
        controller, deformer = self.id_data.jk_adc.get_armatures()
        prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
        prefix = prefs.deform_prefix if self.id_data.jk_adc.is_deformer else ""
        # also means we can always find the deforms...
        if controller and deformer:
            control = self.get_control()
            # this is especially easy if we have reversed constraints...
            if controller.data.jk_adc.reverse_deforms:
                # as the control bone itself now has them...
                pb = controller.pose.bones.get(control.name)
                if pb:
                    con = pb.constraints.get("DEFORM - Child Of")
                    if con:
                        # so we can just pull the deform from the subtarget...
                        return deformer.data.edit_bones.get(con.subtarget) if deformer.mode == 'EDIT' else deformer.pose.bones.get(con.subtarget)
            else:
                # though having reversed constraints isn't common, we can also attempt to find them from the controls name first...
                deform = deformer.pose.bones.get(prefix + self.last_name)
                # if we do find a bone though...
                if deform:
                    # it could of been duplicated and is holding an old reference...
                    con = deform.constraints.get("DEFORM - Child Of")
                    # so checking the constraints subtarget...
                    if con and con.subtarget == control.name:
                        # ensures returning the correct bone...
                        return deformer.data.edit_bones.get(deform.name) if deformer.mode == 'EDIT' else deform
                    else:
                        # else if it was the wrong bone, we better go find the right one...
                        for pb in deformer.pose.bones:
                            # by searching every nook and cranny on the deformers pose bones...
                            con = pb.constraints.get("DEFORM - Child Of")
                            if con:
                                # and if we still can't find it then it must of been deleted....
                                if con.subtarget == control.name:
                                    # or possibly consumed by a rogue driver in the middle of an fcurve sometime last thursday night...
                                    return deformer.data.edit_bones.get(pb.name) if deformer.mode == 'EDIT' else pb
                else:
                    # else if we can't find the damn thing at all...
                    for pb in deformer.pose.bones:
                        # we can go have a crawl around...
                        con = pb.constraints.get("DEFORM - Child Of")
                        if con:
                            # because if it's a deform it should be constrained somewhere...
                            if con.subtarget == control.name:
                                # in the dungeon guarded by the skeletons...
                                return deformer.data.edit_bones.get(pb.name) if deformer.mode == 'EDIT' else pb
        else:
            # if we can't even get the armatures then somethings gone terribly wrong...
            return None

    def get_name(self):
        control = self.get_control()
        # ensure deform name is always up to date with control...
        if control and control.name != self.last_name:
            # by trying to get the deform bone...
            db = self.get_deform()
            if db:
                prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
                prefix = prefs.deform_prefix if self.id_data.jk_adc.is_deformer else ""
                # if we find one update it's name...
                db.name = prefix + control.name
            self.last_name = control.name
        return control.name if control else ""

    name: StringProperty(get=get_name)

    last_name: StringProperty()

    def update_snap_deform(self, context):
        if self.snap_deform:
            control = self.get_control()
            self.control_head = control.head
            self.snap_control = False

    snap_deform: BoolProperty(name="Snap Deform", description="Snap the deform bone to the control when it's edited",
        default=False, update=update_snap_deform)

    def update_snap_control(self, context):
        if self.snap_control:
            deform = self.get_deform()
            self.deform_head, self.deform_tail = deform.head, deform.tail
            self.snap_deform = False

    snap_control: BoolProperty(name="Snap Control", description="Snap the control bone to the deform bone when it's edited",
        default=False, update=update_snap_control)

    has_deform: BoolProperty(name="Has Deform", description="Does this control have a deform bone?",
        default=False)

    offset: FloatVectorProperty(name="Offset", description="The offset between control and deform bone heads",
        size=3, subtype='TRANSLATION', default=[0.0, 0.0, 0.0])

    def get_control_location(self):
        control, deform = self.get_control(), self.get_deform()
        if self.snap_deform:
            # get the controls location difference...
            difference = control.head - self.control_head
            # apply that difference to the deform bone...
            deform.head, deform.tail = deform.head + difference, deform.tail + difference
            self.deform_head, self.deform_tail = deform.head.copy(), deform.tail.copy()
        self.control_head = control.head.copy()
        return control.head
    
    control_location: FloatVectorProperty(name="Control", description="The current head of this bone",
        size=3, subtype='TRANSLATION', default=[0.0, 0.0, 0.0], get=get_control_location)
    
    control_head: FloatVectorProperty(name="Control Head", description="The head of the control bone",
        size=3, subtype='TRANSLATION', default=[0.0, 0.0, 0.0])

    control_parent: StringProperty(name="Control Parent", description="Name of parent bone (Without prefixing)", 
        default="")
        
    def get_deform_location(self):
        control, deform = self.get_control(), self.get_deform()
        # if we should be auto_snapping the control...
        if self.snap_control:
            # get the deforms location difference...
            difference = deform.head - self.deform_head
            # apply that difference to the deform bone...
            control.head, control.tail = control.head + difference, control.tail + difference
            self.control_head = control.head.copy()
        # otherwise just set and return our new head location...
        self.deform_head = deform.head.copy()
        return deform.head
    
    deform_location: FloatVectorProperty(name="Deform", description="The current head of the deform bone",
        size=3, subtype='TRANSLATION', default=[0.0, 0.0, 0.0], get=get_deform_location)
    
    deform_head: FloatVectorProperty(name="Deform Head", description="The head of the deform bone",
        size=3, subtype='TRANSLATION', default=[0.0, 0.0, 0.0])

    deform_tail: FloatVectorProperty(name="Deform Tail", description="The tail of the deform bone",
        size=3, subtype='TRANSLATION', default=[0.0, 0.0, 0.0])

    deform_roll: FloatProperty(name="Roll", description="The roll of the deform bone", 
        default=0.0, subtype='ANGLE', unit='ROTATION')

    deform_parent: StringProperty(name="Deform Parent", description="Name of deforms parent bone", 
        default="")
    
    def update_use_location(self, context):
        pb = self.get_control() if self.id_data.jk_adc.reverse_deforms else self.get_deform()
        if self.use_location:
            limit_loc = pb.constraints.get("USE - Limit Location")
            if limit_loc:
                pb.constraints.remove(limit_loc)
        else:
            if pb.constraints.get("USE - Limit Location"):
                limit_loc = pb.constraints.get("USE - Limit Location")
            else:
                limit_loc = pb.constraints.new('LIMIT_LOCATION')
            limit_loc.name, limit_loc.show_expanded = "USE - Limit Location", False
            limit_loc.use_min_x, limit_loc.use_min_y, limit_loc.use_min_z = True, True, True
            limit_loc.use_max_x, limit_loc.use_max_y, limit_loc.use_max_z = True, True, True
            limit_loc.owner_space = 'LOCAL'

    use_location: BoolProperty(name="Use Location", description="Should the deform bone use location from the control or inherit it from it's parent", 
        default=True, update=update_use_location)

    def update_use_scale(self, context):
        pb = self.get_control() if self.id_data.jk_adc.reverse_deforms else self.get_deform()
        if self.use_scale:
            limit_sca = pb.constraints.get("USE - Limit Scale")
            if limit_sca:
                pb.constraints.remove(limit_sca)
        else:
            if pb.constraints.get("USE - Limit Scale"):
                limit_sca = pb.constraints.get("USE - Limit Scale")
            else:
                limit_sca = pb.constraints.new('LIMIT_SCALE')
            limit_sca.name, limit_sca.show_expanded = "USE - Limit Scale", False
            limit_sca.use_min_x, limit_sca.use_min_y, limit_sca.use_min_z = True, True, True
            limit_sca.use_max_x, limit_sca.use_max_y, limit_sca.use_max_z = True, True, True
            limit_sca.min_x, limit_sca.min_y, limit_sca.min_z = 1.0, 1.0, 1.0
            limit_sca.max_x, limit_sca.max_y, limit_sca.max_z = 1.0, 1.0, 1.0
            limit_sca.owner_space = 'LOCAL'

    use_scale: BoolProperty(name="Use Scale", description="Should the deform bone use scale from the control", 
        default=False, update=update_use_scale)

class JK_PG_ADC_Armature(bpy.types.PropertyGroup):

    def subscribe_mode(self, controller):
        _functions_.subscribe_mode_to(controller, _functions_.armature_mode_callback)

    def apply_transforms(self, use_identity=False):
        # when applying transforms all the constraints should be reset...
        _functions_.refresh_deform_constraints(self.get_controller(), use_identity=use_identity)

    is_iterating: BoolProperty(name="Is Iterating", description="Is this armature currently iterating on bones?", 
        default=False)

    is_editing: BoolProperty(name="Is Editing", description="Is this armature currently being edited?", 
        default=False)

    is_deformer:  BoolProperty(name="Is Deform Armature", description="Is this a deformation armature",
        default=False, options=set())

    is_controller:  BoolProperty(name="Is Control Armature", description="Is this an animation control armature",
        default=False, options=set())

    def get_armature(self):
        armatures = [ob for ob in bpy.data.objects if ob.type == 'ARMATURE']
        for arm in armatures:
            if arm.type == 'ARMATURE' and arm.data == self.id_data:
                return arm
    
    def get_deformer(self):
        armature = self.get_armature()
        # if armatures are separated and we call this from the controller there should only ever be one valid deformer child...
        if self.is_controller and not self.is_deformer:
            for ob in armature.children:
                if ob.type == 'ARMATURE' and ob.data.jk_adc.get_controller() == armature:
                    return ob
        else:
            # else we return self object if we are deformer and controller...
            return armature if self.is_deformer else None

    def get_controller(self):
        armature = self.get_armature()
        # if we call this from a deformer that is not a controller...
        if self.is_deformer and not self.is_controller:
            # return the self objects parent... (WARNING: Will break if people reparent seperated deform armatures!)
            return armature.parent
        else:
            # else we return self object if we are both or neither...
            return armature

    def get_armatures(self):
        # should get both armatures no which one we call from... (might come in handy)
        return self.get_controller(), self.get_deformer()

    def get_bones(self):
        controller = self.get_controller()
        if controller:
            return [bb for bb in controller.data.bones if bb.jk_adc.has_deform]
        else:
            return []

    def get_controls(self):
        controller = self.get_controller()
        if controller:
            return {bb.jk_adc.get_control() : bb.jk_adc.get_deform() for bb in controller.data.bones if bb.jk_adc.has_deform}
        else:
            return {}

    def get_deforms(self):
        controller = self.get_controller()
        if controller:
            return {bb.jk_adc.get_deform() : bb.jk_adc.get_control() for bb in controller.data.bones if bb.jk_adc.has_deform}
        else:
            return {}

    def get_actions(self, armature, only_active=False):
        prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
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
            baked = {act : bpy.data.actions.get(act.name[len(prefs.deform_prefix):]) for act in bpy.data.actions 
                if any(fc.data_path.partition('"')[2].split('"')[0] in armature.data.bones for fc in act.fcurves) 
                and act.name.startswith(prefs.deform_prefix)}
        return source, baked

    def update_use_auto_update(self, context):
        controller, deformer = self.get_armatures()
        if controller and controller.mode == 'EDIT':
            # need to make sure the saved edit bone locations stay updated...
            controls = [bb for bb in controller.data.edit_bones if bb.jk_adc.has_deform]
            for control in controls:
                deform = control.jk_adc.get_deform()
                control.jk_adc.last_name = control.name
                control.jk_adc.deform_head, control.jk_adc.deform_tail = deform.head, deform.tail
                control.jk_adc.control_head = control.head
            if controller.data.jk_adc.use_auto_update:
                # if we are in edit mode and the update timer is not ticking...
                if not bpy.app.timers.is_registered(_functions_.jk_adc_auto_update_timer):
                    # give it a kick in the arse...
                    bpy.app.timers.register(_functions_.jk_adc_auto_update_timer)
        else:
            # if we are not in edit mode and the update timer is ticking...
            if bpy.app.timers.is_registered(_functions_.jk_adc_auto_update_timer):
                # give it a kick in the face...
                bpy.app.timers.unregister(_functions_.jk_adc_auto_update_timer)
            #deformer.update_from_editmode()
            #if not controller.data.jk_adc.is_deformer:
                #controller.update_from_editmode()
            # update all the constraints...
            _functions_.refresh_deform_constraints(controller, use_identity=True)
        
    use_auto_update: BoolProperty(name="Auto Snap", description="Automatically apply any location changes made to control/deform bones while in edit mode (based on the per bone snap settings)",
        default=False, options=set(), update=update_use_auto_update)

    auto_hide: BoolProperty(name="Auto Hide", description="Automatically hide/show deform/control bones depending on mode",
        default=False, options=set())

    def update_use_deforms(self, context):
        controller = self.get_controller()
        _functions_.use_deforms(controller, self.use_deforms)

    use_deforms: BoolProperty(name="Use Deforms", description="Use deform/control bones to deform the mesh",
        default=False, options=set(), update=update_use_deforms)

    def update_use_combined(self, context):
        controller = self.get_controller()
        _functions_.set_combined(controller, self.use_combined)

    use_combined: BoolProperty(name="Combine Armatures", description="Deformation bones are combined into the control armature",
        default=False, options=set(), update=update_use_combined)

    def update_mute_deforms(self, context):
        deformer = self.get_deformer()
        _functions_.mute_deform_constraints(deformer, self.mute_deforms)
    
    mute_deforms: BoolProperty(name="Mute Constraints", description="Mute deform bone constraints (deform bones are unaffected by the controls)",
        default=False, options=set(), update=update_mute_deforms)

    reverse_deforms: BoolProperty(name="Reverse Constraints", description="Reverse deform bone constraints so control bones follow deform bones (WARNING! Constraints on controls get muted but drivers stay enabled and may cause problems)",
        default=False, options=set())

    def update_hide_deforms(self, context):
        controller = self.get_controller()
        _functions_.hide_deforms(controller, self.hide_deforms)

    hide_deforms: BoolProperty(name="Hide Deforms", description="Hide/Show deform bones",
        default=False, options=set(), update=update_hide_deforms)

    def update_hide_controls(self, context):
        controller = self.get_controller()
        _functions_.hide_controls(controller, self.hide_controls)

    hide_controls: BoolProperty(name="Hide Controls", description="Hide/Show control bones",
        default=False, options=set(), update=update_hide_controls)

    def update_hide_others(self, context):
        controller = self.get_controller()
        _functions_.hide_others(controller, self.hide_others)

    hide_others: BoolProperty(name="Hide Others", description="Hide/Show bones that are not control or deform bones",
        default=False, options=set(), update=update_hide_others)
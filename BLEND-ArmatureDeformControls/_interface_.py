import bpy
from . import _functions_

class JK_ADC_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = "BLEND-ArmatureDeformControls"

    def update_deform_prefix(self, context):
        # no point executing anything if the prefix hasn't changed...
        if self.last_prefix != self.deform_prefix:
            for armature in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
                # if the armatures are combined...
                if armature.data.jk_adc.use_combined:
                    bones = armature.data.bones
                    deforms = [db for db in bones if db.name.startswith(self.last_prefix)]
                    # then iterate through them finding the controls...
                    for deform in deforms:
                        # and setting the saved parent name
                        control = bones.get(deform.name[len(self.last_prefix):])
                        if control and control.jk_adc.deform_parent:
                            control.jk_adc.deform_parent = self.deform_prefix + control.deform_parent[len(self.last_prefix):]
                        deform.name = self.last_prefix + deform.name[len(self.last_prefix):]
                else:
                    # if the armatures are not combined...
                    if armature.data.jk_adc.is_deformer:
                        # we just rename the deformation armature...
                        armature.name = self.deform_prefix + armature.name[len(self.last_prefix):]
            
            for action in [a for a in bpy.data.actions if a.name.startswith(self.last_prefix)]:
                action.name = self.deform_prefix + action.name[len(self.last_prefix):]
            
            self.last_prefix = self.deform_prefix

    last_prefix: bpy.props.StringProperty(name="Last Prefix", description="The last used prefix for the deform armature when using dual armature method. (Bones can have the same names between armatures)", 
        default="DEF_", maxlen=1024)
    
    deform_prefix: bpy.props.StringProperty(name="Deform Prefix", description="The prefix for the deform armature when using dual armature method. (Bones can have the same names between armatures)", 
        default="DEF_", maxlen=1024, update=update_deform_prefix)

    auto_freq: bpy.props.FloatProperty(name="Auto Update Frequency", description="How often we check selection for automatic control/deform location snapping in edit mode. (in seconds)",
        default=0.5, min=0.1, max=1.0)
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "deform_prefix")
        row.prop(self, "auto_freq")

class JK_PT_ADC_Armature_Panel(bpy.types.Panel):
    bl_label = "Deform Controls"
    bl_idname = "JK_PT_ADC_Armature_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        if (context.object.type == 'MESH' and context.object.mode == 'WEIGHT_PAINT'):
            if any(mod.type == 'ARMATURE' for mod in context.object.modifiers):
                is_valid = True
            else:
                is_valid = False
        elif context.object.type == 'ARMATURE':
            is_valid = True
        else:
            is_valid = False
        return is_valid

    def draw(self, context):
        layout = self.layout
        if bpy.context.object:
            controller = bpy.context.object.data.jk_adc.get_controller() 
            row = layout.row()
            row.enabled = True if context.object.type != 'MESH' else False
            row.operator("jk.adc_edit_controls", text='Add Deforms', icon='GROUP_BONE').action = 'ADD'
            row.operator("jk.adc_edit_controls", text='Remove Deforms', icon='CANCEL').action = 'REMOVE'
            row.operator("jk.adc_edit_controls", text='Update Deforms', icon='FILE_REFRESH').action = 'UPDATE'
            
            row = layout.row()
            bake_col = row.column()
            bake_row = bake_col.row(align=True)
            col = bake_row.column(align=True)
            if controller:
                col.operator("jk.adc_reverse_constraints", text="", icon='ARROW_LEFTRIGHT', depress=controller.data.jk_adc.reverse_deforms).reverse = not controller.data.jk_adc.reverse_deforms
                #col.prop(controller.data.jk_adc, "reverse_deforms", text="", icon='ARROW_LEFTRIGHT')
            #else:
                #col.operator("jk.adc_bake_deforms", text="", icon='ARROW_LEFTRIGHT')
                #col.enabled = False
            col = bake_row.column(align=True)
            if controller and controller.data.jk_adc.reverse_deforms:
                col.operator("jk.adc_bake_controls", text='Bake Controls').armature = bpy.context.object.name
            else:
                col.operator("jk.adc_bake_deforms", text='Bake Deforms').armature = bpy.context.object.name
            row.enabled = True if bpy.context.object.type == 'ARMATURE' else False
            
            #split = row.split()
            refresh_col = row.column()
            refresh_row = refresh_col.row(align=True)
            col = refresh_row.column(align=True)
            if controller and controller.data.jk_adc.is_controller:
                col.prop(controller.data.jk_adc, "mute_deforms", text="", icon='HIDE_ON' if controller.data.jk_adc.mute_deforms else 'HIDE_OFF')
            else:
                col.operator("jk.adc_refresh_constraints", text="", icon='HIDE_OFF')
                col.enabled = False
            col = refresh_row.column(align=True)
            col.operator("jk.adc_refresh_constraints", text='Refresh Constraints')
            col.enabled = True if controller and not controller.data.jk_adc.mute_deforms else False
            row.enabled = True if controller else False

            if controller:
                row = layout.row()
                row.prop(controller.data.jk_adc, "use_combined", icon='LINKED' if controller.data.jk_adc.use_combined else 'UNLINKED')#, emboss=False)
                row.prop(controller.data.jk_adc, "use_deforms", icon='MODIFIER_ON' if controller.data.jk_adc.use_deforms else 'MODIFIER_OFF')#, emboss=False)
                row.prop(controller.data.jk_adc, "use_auto_update", icon='SNAP_ON' if controller.data.jk_adc.use_auto_update else 'SNAP_OFF')
                #row.enabled = True if context.object.type != 'MESH' else False
                row = layout.row(align=True)
                row.prop(controller.data.jk_adc, "hide_controls")#, text="Controls", icon='HIDE_OFF' if controller.data.jk_adc.hide_controls else 'HIDE_ON')#, emboss=False)
                row.prop(controller.data.jk_adc, "hide_deforms")#, text="Deforms", icon='HIDE_OFF' if controller.data.jk_adc.hide_deforms else 'HIDE_ON')#, emboss=False)
                row.prop(controller.data.jk_adc, "hide_others")

class JK_PT_ADC_Bone_Panel(bpy.types.Panel):
    bl_label = "Selected"
    bl_idname = "JK_PT_ADC_Bone_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "JK_PT_ADC_Armature_Panel"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        is_valid = False
        if context.object and context.object.type == 'ARMATURE':
            if any(bb.jk_adc.has_deform for bb in bpy.context.object.data.bones):
                if context.object.mode == 'EDIT':
                    if any(eb.select for eb in context.object.data.edit_bones):
                        is_valid = True
                else:
                    if any(bb.select for bb in context.object.data.bones):
                        is_valid = True
        return is_valid

    def draw(self, context):
        layout = self.layout
        armature = bpy.context.object
        controller = armature.data.jk_adc.get_controller()
        row = layout.row(align=True)
        row.alignment = 'RIGHT'
        row.label(text="Set All Selected")
        row.separator()
        if controller:
            if controller.mode == 'EDIT':
                snap_col = row.column()
                snap_row = snap_col.row(align=True)
                snap_con = snap_row.operator("jk.adc_set_selected", text='', icon='TRACKING_CLEAR_FORWARDS')
                snap_con.action, snap_con.use = 'SNAP_CONTROLS', False
                snap_con = snap_row.operator("jk.adc_set_selected", text='', icon='TRACKING_FORWARDS')
                snap_con.action, snap_con.use = 'SNAP_CONTROLS', True
                row.separator()
                snap_col = row.column()
                snap_row = snap_col.row(align=True)
                snap_def = snap_row.operator("jk.adc_set_selected", text='', icon='TRACKING_CLEAR_BACKWARDS')
                snap_def.action, snap_def.use = 'SNAP_DEFORMS', False
                snap_def = snap_row.operator("jk.adc_set_selected", text='', icon='TRACKING_BACKWARDS')
                snap_def.action, snap_def.use = 'SNAP_DEFORMS', True
                layout.separator()
                selected = [bb for bb in controller.data.bones if bb.jk_adc.has_deform and ((bb.jk_adc.get_control().select or bb.jk_adc.get_control().select_head or bb.jk_adc.get_control().select_tail) 
                    or (bb.jk_adc.get_deform() and (bb.jk_adc.get_deform().select or bb.jk_adc.get_deform().select_head or bb.jk_adc.get_deform().select_tail)))]
                for bb in selected:
                    control, deform = bb.jk_adc.get_control(), bb.jk_adc.get_deform()
                    if control and deform:
                        row = layout.row(align=True)
                        row.alignment = 'RIGHT'
                        row.label(text=control.name + " | " + deform.name)
                        row.separator()
                        row.prop(bb.jk_adc, "snap_control", text="", icon='TRACKING_FORWARDS' if bb.jk_adc.snap_control else 'TRACKING_CLEAR_FORWARDS')
                        row.prop(bb.jk_adc, "snap_deform", text="", icon='TRACKING_BACKWARDS' if bb.jk_adc.snap_deform else 'TRACKING_CLEAR_BACKWARDS')
            else:
                loc_col = row.column()
                loc_row = loc_col.row(align=True)
                use_loc = loc_row.operator("jk.adc_set_selected", text='', icon='CON_LOCLIMIT')
                use_loc.action, use_loc.use = 'USE_LOCATIONS', False
                use_loc = loc_row.operator("jk.adc_set_selected", text='', icon='CON_LOCLIKE')
                use_loc.action, use_loc.use = 'USE_LOCATIONS', True
                row.separator()
                sca_col = row.column()
                sca_row = sca_col.row(align=True)
                use_sca = sca_row.operator("jk.adc_set_selected", text='', icon='CON_SIZELIMIT')
                use_sca.action, use_sca.use = 'USE_SCALES', False
                use_sca = sca_row.operator("jk.adc_set_selected", text='', icon='CON_SIZELIKE')
                use_sca.action, use_sca.use = 'USE_SCALES', True
                layout.separator()
                selected = [bb for bb in controller.data.bones if bb.jk_adc.has_deform and (bb.select or (bb.jk_adc.get_deform() and bb.jk_adc.get_deform().bone.select))]
                for bb in selected:
                    control, deform = bb.jk_adc.get_control(), bb.jk_adc.get_deform()
                    if control and deform:
                        row = layout.row(align=True)
                        row.alignment = 'RIGHT'
                        row.label(text=control.name + " | " + deform.name)
                        row.separator()
                        row.prop(bb.jk_adc, "use_location", text="", icon='CON_LOCLIKE' if bb.jk_adc.use_location else 'CON_LOCLIMIT')
                        row.prop(bb.jk_adc, "use_scale", text="", icon='CON_SIZELIKE' if bb.jk_adc.use_scale else 'CON_SIZELIMIT')
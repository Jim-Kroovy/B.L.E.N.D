import bpy
import json
from . import _functions_, _properties_

class JK_ACB_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = "BLEND-ArmatureControlBones"

    def update_deform_prefix(self, context):
        if self.last_prefix != self.deform_prefix:
            
            for armature in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
                if armature.data.jk_acb.use_combined:
                    bbs = armature.data.bones
                    deforms = json.loads(armature.data.jk_acb.deforms)
                    for bone in deforms:
                        deform_bb = bbs.get(self.last_prefix + bone['name'])
                        if deform_bb:
                            deform_bb.name = self.deform_prefix + bone['name']
                else:
                    if armature.data.jk_acb.is_deformer:
                        armature.name = self.deform_prefix + armature.name[len(self.last_prefix):]
            
            for action in [a for a in bpy.data.actions if a.name.startswith(self.last_prefix)]:
                action.name = self.deform_prefix + action.name[len(self.last_prefix):]
            
            self.last_prefix = self.deform_prefix

    last_prefix: bpy.props.StringProperty(name="Last Prefix", description="The last used prefix for the deform armature when using dual armature method. (Bones can have the same names between armatures)", 
        default="DEF_", maxlen=1024, update=update_deform_prefix)
    
    deform_prefix: bpy.props.StringProperty(name="Deform Prefix", description="The prefix for the deform armature when using dual armature method. (Bones can have the same names between armatures)", 
        default="DEF_", maxlen=1024, update=update_deform_prefix)

    meshes: bpy.props.CollectionProperty(type=_properties_.JK_PG_ACB_Mesh)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "deform_prefix")

class JK_PT_ACB_Armature_Panel(bpy.types.Panel):
    bl_label = "Deform Controls"
    bl_idname = "JK_PT_ACB_Armature_Panel"
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
            controller, _ = _functions_.get_armatures()
            row = layout.row()
            row.enabled = True if context.object.type != 'MESH' else False
            row.operator("jk.acb_edit_controls", text='Add Deforms', icon='GROUP_BONE').action = 'ADD'
            row.operator("jk.acb_edit_controls", text='Remove Deforms', icon='CANCEL').action = 'REMOVE'
            col = row.column()
            row = col.row(align=True)
            col = row.column(align=True)
            if controller:
                col.prop(controller.data.jk_acb, "use_auto_update", text="", icon='SNAP_ON' if controller.data.jk_acb.use_auto_update else 'SNAP_OFF')
            else:
                col.operator("jk.acb_edit_controls", text="", icon='SNAP_OFF').action = 'UPDATE'
            col = row.column(align=True)
            col.operator("jk.acb_edit_controls", text='Update Deforms').action = 'UPDATE'#, icon='FILE_REFRESH').action = 'UPDATE'
            col.enabled = True if controller and not controller.data.jk_acb.use_auto_update else False
            row.enabled = True if controller else False
            row = layout.row()
            bake_col = row.column()
            bake_row = bake_col.row(align=True)
            col = bake_row.column(align=True)
            if controller and controller.data.jk_acb.is_controller:
                
                col.prop(controller.data.jk_acb, "reverse_deforms", text="", icon='ARROW_LEFTRIGHT')
            else:
                col.operator("jk.acb_bake_deforms", text="", icon='ARROW_LEFTRIGHT')
                col.enabled = False
            col = bake_row.column(align=True)
            if controller and controller.data.jk_acb.reverse_deforms:
                col.operator("jk.acb_bake_controls", text='Bake Controls').armature = bpy.context.object.name
            else:
                col.operator("jk.acb_bake_deforms", text='Bake Deforms').armature = bpy.context.object.name
            row.enabled = True if bpy.context.object.type == 'ARMATURE' else False
            
            #split = row.split()
            refresh_col = row.column()
            refresh_row = refresh_col.row(align=True)
            col = refresh_row.column(align=True)
            if controller and controller.data.jk_acb.is_controller:
                col.prop(controller.data.jk_acb, "mute_deforms", text="", icon='HIDE_ON' if controller.data.jk_acb.mute_deforms else 'HIDE_OFF')
            else:
                col.operator("jk.acb_refresh_constraints", text="", icon='HIDE_OFF')
                col.enabled = False
            col = refresh_row.column(align=True)
            col.operator("jk.acb_refresh_constraints", text='Refresh Constraints')
            col.enabled = True if controller and not controller.data.jk_acb.mute_deforms else False
            row.enabled = True if controller else False

            if controller:

                row = layout.row()
                row.prop(controller.data.jk_acb, "use_combined", icon='LINKED' if controller.data.jk_acb.use_combined else 'UNLINKED')#, emboss=False)
                row.prop(controller.data.jk_acb, "use_deforms", icon='MODIFIER_ON' if controller.data.jk_acb.use_deforms else 'MODIFIER_OFF')#, emboss=False)
                row.prop(controller.data.jk_acb, "use_scale", icon='CON_SIZELIKE' if controller.data.jk_acb.use_scale else 'CON_SIZELIMIT')
                
                row.enabled = True if context.object.type != 'MESH' else False
                row = layout.row(align=True)
                row.prop(controller.data.jk_acb, "hide_controls")#, text="Controls", icon='HIDE_OFF' if controller.data.jk_acb.hide_controls else 'HIDE_ON')#, emboss=False)
                row.prop(controller.data.jk_acb, "hide_deforms")#, text="Deforms", icon='HIDE_OFF' if controller.data.jk_acb.hide_deforms else 'HIDE_ON')#, emboss=False)
                row.prop(controller.data.jk_acb, "hide_others")
        # disable the whole layout if we are in edit mode... (for now at least)
        layout.enabled = True if context.object.mode != 'EDIT' else False


                
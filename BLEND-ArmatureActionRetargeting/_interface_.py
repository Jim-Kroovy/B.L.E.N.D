import bpy

class JK_PT_AAR_Armature_Panel(bpy.types.Panel):
    bl_label = "Retargeting"
    bl_idname = "JK_PT_AAR_Armature_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        source = bpy.context.object
        AAR = bpy.context.object.data.AAR
        layout.prop(AAR, "Target")
        if AAR.Target != None:
            layout.prop(AAR, "Offset")
            if AAR.Offset != None:
                action_box = layout.box
                offset = AAR.Offset.AAR
                action_box.prop(offset, "Action")
                action_box.prop(offset, "All_actions")

        

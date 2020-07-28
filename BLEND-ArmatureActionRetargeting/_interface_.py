import bpy

class JK_PT_AAR_Armature_Panel(bpy.types.Panel):
    bl_label = "Armature Stages"
    bl_idname = "JK_PT_AES_Armature_Panel"
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
        

import bpy
from . import _functions_
from bpy.props import (IntVectorProperty, BoolProperty, StringProperty, PointerProperty, IntProperty)

class JK_OT_Bake_Action(bpy.types.Operator):
    """Binds source armature to the target armature"""
    bl_idname = "jk.bake_retarget_action"
    bl_label = "Bake Action"

    Bake_from_curves: BoolProperty(name="Bake From Curves", description="Use rotation from target",
        default=False, options=set())

    Bake_all: BoolProperty(name="Bake All", description="Bake all actions used by each offset",
        default=False, options=set())

    Bake_step: IntProperty(name="Bake Step", description="How often to evaluate keyframes when baking", 
        default=1, options=set())
    
    Selected: BoolProperty(name="Only Selected", description="Only bake selected pose bones",
        default=False, options=set())

    def execute(self, context):
        source = bpy.context.object
        AAR = source.data.AAR
        if not self.Bake_from_curves:
            if self.Bake_all:
                for offset in AAR.Offsets:
                    if offset.AAR.All_actions:
                        for action in offset.Actions:
                            _functions_.Bake_Action_From_Offset(source, offset, action, self.Bake_step, self.Selected)
                    else:
                        action = offset.AAR.Action
                        _functions_.Bake_Action_From_Offset(source, offset, action, self.Bake_step, self.Selected)
            else:
                offset = AAR.Offset 
                action = offset.AAR.Action
                _functions_.Bake_Action_From_Offset(source, offset, action, self.Bake_step, self.Selected)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        #row.prop_search(self, "Parent", bpy.data.objects, "Stages")
        row.prop(self, "Bake_all")
        row.prop(self, "Bake_step")

class JK_OT_Add_Action(bpy.types.Operator):
    """Adds an action to the list"""
    bl_idname = "jk.add_retarget_action"
    bl_label = "Add Action"
    
    Is_offset: BoolProperty(name="Is Offset", description="Is this an offset action to be used when baking retargets",
        default=False, options=set())
    
    All: BoolProperty(name="All Actions", description="Add all the targets possible actions to this offsets target action list",
        default=False, options=set())
    
    def execute(self, context):
        source = bpy.context.object
        AAR = source.data.AAR
        target = AAR.Target
        if self.Is_offset:
            _functions_.Add_Offset_Action(source)
        elif self.All:
            actions = [a for a in bpy.data.actions if any(b.name in fc.data_path for b in target.data.bones for fc in a.fcurves)]
            for action in actions:
                _functions_.Add_Action_To_Offset(AAR.Offset, action)
        else:
            _functions_.Add_Action_To_Offset(AAR.Offset, AAR.Offset.AAR.Action)
        return {'FINISHED'}




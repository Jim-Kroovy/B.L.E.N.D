import bpy
from . import _functions_
from bpy.props import (IntVectorProperty, BoolProperty, StringProperty, PointerProperty, IntProperty)

class JK_OT_Bind_Retarget(bpy.types.Operator):
    """Binds source armature to the target armature"""
    bl_idname = "jk.bind_retarget"
    bl_label = "Retarget Armature"

    def Target_Poll(self, object):
        return object.type == 'ARMATURE'
    
    Target: PointerProperty(type=bpy.types.Object, poll=Target_Poll)
    
    #Props: PointerProperty(type=_properties_.JK_AAR_Armature_Props)

    def execute(self, context):
        source = bpy.context.object
        target = source.data.AAR.Target
        #mapping = bpy.context.preferences.addons["BLEND-ArmatureBoneMapping"].preferences.Mapping
        _functions_.Add_Armature_Bindings(source, target)
        source.AAR.Is_bound = True
        source.AAR.Target = target.name   
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        #row.prop_search(self, "Parent", bpy.data.objects, "Stages")
        row.prop(self, "Target")

class JK_OT_Bake_Action(bpy.types.Operator):
    """Binds source armature to the target armature"""
    bl_idname = "jk.bake_retarget_action"
    bl_label = "Bake Action"

    Bake_from_curves: BoolProperty(name="Bake From Curves", description="Use rotation from target",
        default=True, options=set())

    Bake_all: BoolProperty(name="Bake All", description="Bake all actions used by each offset",
        default=True, options=set())

    Bake_step: IntProperty(name="Bake Step", description="How often to evaluate keyframes when baking", 
        default=1)
    
    Selected: BoolProperty(name="Only Selected", description="Only bake selected pose bones",
        default=True, options=set())

    def execute(self, context):
        source = bpy.context.object
        AAR = source.data.AAR
        target = AAR.Target
        #mapping = bpy.context.preferences.addons["BLEND-ArmatureBoneMapping"].preferences.Mapping
        if not self.Bake_from_curves:
            if self.Bake_all:
                for offset in AAR.Offsets:
                    action = offset.Action
                    for curve in action.fcurves:
                        if any(b.name in curve.data_path for b in target.data.bones):
                            target.animation_data.action = action
                            _functions_.Add_Retarget_Action(source, action)
                            bpy.ops.nla.bake(frame_start=action.frame_range[0], frame_end=action.frame_range[1], step=self.Bake_step, only_selected=self.Selected, 
                                visual_keying=True, clear_constraints=False, clear_parents=False, use_current_action=True, bake_types={'POSE'})
                            break
            else: 
                if self.Action != None:
                    action = self.Action
                    target.animation_data.action = action
                    _functions_.Add_Retarget_Action(source, action)
                    bpy.ops.nla.bake(frame_start=action.frame_range[0], frame_end=action.frame_range[1], step=self.Bake_step, only_selected=self.Selected, 
                        visual_keying=True, clear_constraints=False, clear_parents=False, use_current_action=True, bake_types={'POSE'})
        return {'FINISHED'}
import bpy
from bpy.props import PointerProperty
from . import (_functions_, _properties_)

class JK_OT_Scale_Action_Length(bpy.types.Operator):
    """Scales actions to a framerate or length in seconds"""
    bl_idname = "jk.scale_action_length"
    bl_label = "Scale Action Length"
    
    Props: PointerProperty(type=_properties_.JK_SAL_Operator_Props)
    
    def execute(self, context):
        # get the actions...
        actions = [bpy.data.actions[self.Props.name]] if self.Props.Single else [action for action in bpy.data.actions]
        # check which scaling method to use...
        if self.Props.Length_mode == 'FPS':
            # check if we can execute correctly...
            if self.Props.FPS_from != self.Props.FPS_to:
                # run scaling on those actions...
                for action in actions:
                    Scale_By_Framerate(action, self.Props.FPS_from, self.Props.FPS_to, False)
                # maybe set the render fps...
                if self.Props.Set_fps:
                    bpy.context.scene.render.fps = self.Props.FPS_to
            # if that condition failed i hope you misclicked lol
            else:
                print("'Scale_Action_Length' cannot execute as there's no need to scale to the same FPS...")
        elif self.Props.Length_mode == 'LENGTH':
            # get the actions...
            actions = [bpy.data.actions[self.Props.name]] if self.Props.Single else [action for action in bpy.data.actions]
            # run scaling on those actions...
            for action in actions:
                Scale_By_Length(action, self.Props., offset, seconds, selection)
        # job done!
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        # if selected pose bones is not valid...
        if not bpy.context.selected_pose_bones:
            # make sure the selected bool is false...
            self.Props.Selected = False
            # and set the object bool to be true...
            self.Props.Object = True
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self.Props, "Single")
        row.prop(self.Props, "Remove")
        row = layout.row()
        row.prop_search(self.Props, "name", bpy.data, "actions", text="Action")
        # disable the action selection if we aren't doing a single action...
        row.enabled = self.Props.Single
        row = layout.row()
        row.prop(self.Props, "Mode_from")
        row.prop(self.Props, "Mode_to")
        row = layout.row()
        row.prop(self.Props, "Object")
        col = row.column()
        col.prop(self.Props, "Selected")
        # disable selected bool if there are no selected pose bones...
        col.enabled = True if bpy.context.selected_pose_bones else False
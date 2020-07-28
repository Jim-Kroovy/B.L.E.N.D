import bpy
from bpy.props import PointerProperty
from . import (_functions_, _properties_)

class JK_OT_Set_Action_Transform_Space(bpy.types.Operator):
    """Switch the rotation mode of keyframed fcurves on selected bones. (and optionally object rotations)"""
    bl_idname = "jk.switch_rotation_mode"
    bl_label = "Switch Rotation Mode"
    
    Props: PointerProperty(type=_properties_.JK_STS_Operator_Props)
    
    def execute(self, context):
        # check if we can execute correctly...
        if self.Props.Mode_from != self.Props.Mode_to and (self.Props.name in bpy.data.actions if self.Props.Single else True):
            # get the actions...
            actions = [bpy.data.actions[self.Props.name]] if self.Props.Single else [action for action in bpy.data.actions]
            # get the selected pose bones if possible...
            selection = [p_bone for p_bone in bpy.context.selected_pose_bones] if self.Props.Selected else []
            # get objects that have active actions that will be edited...
            objects = [ob for ob in bpy.data.objects if ob.animation_data and any(ob.animation_data.action == action for action in actions)]  
            # set the selected pose bones rotation modes to the mode we are switching from...
            for selected in selection:
                selected.rotation_mode = self.Props.Mode_from
            # if we are editing object fcurves... 
            if self.Props.Object:
                # set object rotation modes to the mode we are switching from...
                for obj in objects:
                    obj.rotation_mode = self.Props.Mode_from
            # iterate over actions switching their rotation mode...
            for action in actions:
                _functions_.Set_Rotation_Curves(action, self.Props.Mode_from, self.Props.Mode_to, self.Props.Remove, selection, self.Props.Object)
            # set the selected pose bones rotation modes to the mode we are switching to...
            for selected in selection:
                selected.rotation_mode = self.Props.Mode_to
            # if we are editing object fcurves... 
            if self.Props.Object:
                # set object rotation modes to the mode we are switching to...  
                for obj in objects:
                    obj.rotation_mode = self.Props.Mode_to
        # if we can't execute...
        else:
            # explain why...
            if self.Props.Mode_from == self.Props.Mode_to:
                print("'Set Action Rotation Mode' can't execute if 'Mode to' is the same as the 'Mode from'...")
            if self.Props.name not in bpy.data.actions:
                print("'Set Action Rotation Mode' can't execute without a valid action...")
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